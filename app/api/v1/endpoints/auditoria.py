from datetime import date, datetime, timezone
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, requiere_admin
from app.models.user import User, UserRole
from app.repositories import sesion_repository
from app.schemas.auditoria import AuditoriaItem, AuditoriaResponse, AuditoriaResumen
from app.services import reportes_service as rep

router = APIRouter(prefix="/auditoria", tags=["Auditoría"])

TAM_PAGINA = 15


def _tipo(role: str) -> str:
    """Bucket para la columna Tipo: usuario final vs. cuenta profesional."""
    return "Usuario" if role == UserRole.STUDENT.value else "Profesional"


def _fecha(valor: str | None) -> date | None:
    if not valor:
        return None
    try:
        return date.fromisoformat(valor)
    except ValueError:
        return None


def _entradas(db: Session) -> list[dict]:
    """Expande cada sesión en entradas de bitácora: un `login` (al inicio) y,
    si se cerró, un `logout` (al fin). Ordenadas de más reciente a más antigua."""
    sesiones = sesion_repository.listar(db)
    usuarios = {u.id: u for u in db.query(User).all()}
    entradas: list[dict] = []
    for s in sesiones:
        u = usuarios.get(s.usuario_id)
        if u is None:
            continue
        base = {"usuario": u.full_name, "email": u.email, "tipo": _tipo(u.role), "ip": s.ip}
        entradas.append({**base, "evento": "login", "fecha": s.inicio})
        if s.fin is not None:
            entradas.append({**base, "evento": "logout", "fecha": s.fin})
    entradas.sort(key=lambda e: e["fecha"], reverse=True)
    return entradas


def _filtrar(entradas, q, evento, desde, hasta):
    ql = (q or "").lower()

    def ok(e) -> bool:
        if ql and ql not in e["usuario"].lower() and ql not in e["email"].lower():
            return False
        if evento in ("login", "logout") and e["evento"] != evento:
            return False
        f = e["fecha"].date()
        if desde and f < desde:
            return False
        if hasta and f > hasta:
            return False
        return True

    return [e for e in entradas if ok(e)]


@router.get("", response_model=AuditoriaResponse)
def bitacora(
    q: str | None = Query(None),
    evento: str = Query("todos"),
    desde: str | None = Query(None),
    hasta: str | None = Query(None),
    page: int = Query(1, ge=1),
    _admin: User = Depends(requiere_admin),
    db: Session = Depends(get_db),
):
    """Bitácora de accesos (login/logout) con filtros. Solo el administrador."""
    entradas = _filtrar(_entradas(db), q, evento, _fecha(desde), _fecha(hasta))
    total = len(entradas)
    inicio = (page - 1) * TAM_PAGINA
    items = [AuditoriaItem(**e) for e in entradas[inicio : inicio + TAM_PAGINA]]
    return AuditoriaResponse(total=total, items=items)


@router.get("/resumen", response_model=AuditoriaResumen)
def resumen(
    _admin: User = Depends(requiere_admin),
    db: Session = Depends(get_db),
):
    """Métricas del día y tiempo promedio de sesión (con el latido, fiel aunque
    no den logout)."""
    sesiones = sesion_repository.listar(db)
    hoy = datetime.now(timezone.utc).date()

    logins_hoy = sum(1 for s in sesiones if s.inicio.date() == hoy)
    logouts_hoy = sum(1 for s in sesiones if s.fin is not None and s.fin.date() == hoy)
    activos = {
        s.usuario_id
        for s in sesiones
        if s.inicio.date() == hoy or s.ultima_actividad.date() == hoy
    }

    duraciones = []
    for s in sesiones:
        fin = s.fin or s.ultima_actividad
        minutos = (fin - s.inicio).total_seconds() / 60
        if minutos > 0:
            duraciones.append(minutos)
    promedio = round(sum(duraciones) / len(duraciones), 1) if duraciones else 0.0

    return AuditoriaResumen(
        logins_hoy=logins_hoy,
        logouts_hoy=logouts_hoy,
        activos_hoy=len(activos),
        duracion_promedio_min=promedio,
    )


@router.get("/export")
def exportar(
    q: str | None = Query(None),
    evento: str = Query("todos"),
    desde: str | None = Query(None),
    hasta: str | None = Query(None),
    _admin: User = Depends(requiere_admin),
    db: Session = Depends(get_db),
):
    """Descarga la bitácora filtrada en Excel. Reutiliza el renderizador de reportes."""
    entradas = _filtrar(_entradas(db), q, evento, _fecha(desde), _fecha(hasta))
    tabla = rep.Tabla(
        titulo="Auditoría de accesos",
        subtitulo=f"{len(entradas)} eventos · generado el {datetime.now().strftime('%Y-%m-%d')}",
        columnas=["Usuario", "Email", "Tipo", "Evento", "IP", "Fecha y hora"],
        filas=[
            [
                e["usuario"],
                e["email"],
                e["tipo"],
                "Login" if e["evento"] == "login" else "Logout",
                e["ip"] or "",
                e["fecha"].strftime("%Y-%m-%d %H:%M:%S"),
            ]
            for e in entradas
        ],
    )
    contenido = rep.render_excel(tabla)
    nombre = "auditoria_accesos.xlsx"
    disposition = f"attachment; filename=\"{nombre}\"; filename*=UTF-8''{quote(nombre)}"
    return Response(
        content=contenido,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": disposition},
    )
