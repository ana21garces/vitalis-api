import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user, requiere_admin
from app.models.ciclo_medicion import como_utc
from app.models.encuesta_hplp import EncuestaHplp
from app.models.user import User, UserRole
from app.repositories import ciclo_repository as ciclo_repo
from app.repositories import notificacion_repository as repo
from app.repositories.user_repository import UserRepository
from app.schemas.notificacion import (
    DifusionRequest,
    DifusionResponse,
    EnvioResumen,
    MedicionAbiertaInfo,
    NotificacionCreate,
    NotificacionResponse,
    PreviewResponse,
    SegmentosResponse,
)

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])

NIVELES = ["Pobre", "Moderado", "Bueno", "Excelente"]
SEGMENTOS_CON_VALOR = {"facultad", "programa", "tipo", "nivel"}
SEGMENTOS_VALIDOS = SEGMENTOS_CON_VALOR | {"todos", "sin_responder"}

# Roles que pueden invitar a un estudiante a agendar una cita desde su vista
# de resultados.
ROLES_QUE_NOTIFICAN = {
    UserRole.ADMIN,
    UserRole.CAPELLAN,
    UserRole.ACTIVIDAD_FISICA,
    UserRole.RESPONSABILIDAD_SALUD,
    UserRole.RELACIONES_INTERPERSONALES,
    UserRole.MANEJO_ESTRES,
    UserRole.NUTRICION,
}


@router.post("", response_model=NotificacionResponse, status_code=status.HTTP_201_CREATED)
def enviar_notificacion(
    data: NotificacionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Un profesional invita a un estudiante a agendar una cita."""
    if current_user.role not in {r.value for r in ROLES_QUE_NOTIFICAN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu rol no puede enviar notificaciones",
        )

    try:
        destinatario_uuid = uuid.UUID(data.destinatario_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="destinatario_id inválido")

    destinatario = UserRepository(db).get_by_id(destinatario_uuid)
    if destinatario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El destinatario no existe")
    if destinatario.role != UserRole.STUDENT.value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Solo se puede notificar a estudiantes",
        )

    notificacion = repo.crear(db, current_user.id, destinatario_uuid, data.mensaje)
    return NotificacionResponse(
        id=notificacion.id,
        remitente_nombre=current_user.full_name,
        mensaje=notificacion.mensaje,
        leida=notificacion.leida,
        created_at=notificacion.created_at,
    )


@router.get("", response_model=list[NotificacionResponse])
def mis_notificaciones(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Notificaciones recibidas por el usuario autenticado, más recientes primero."""
    notificaciones = repo.listar_por_destinatario(db, current_user.id)

    user_repo = UserRepository(db)
    nombres_por_remitente: dict[uuid.UUID, str] = {}

    def nombre_de(remitente_id: uuid.UUID) -> str:
        if remitente_id not in nombres_por_remitente:
            remitente = user_repo.get_by_id(remitente_id)
            nombres_por_remitente[remitente_id] = remitente.full_name if remitente else "Equipo Vitalis"
        return nombres_por_remitente[remitente_id]

    return [
        NotificacionResponse(
            id=n.id,
            remitente_nombre=nombre_de(n.remitente_id),
            mensaje=n.mensaje,
            leida=n.leida,
            created_at=n.created_at,
        )
        for n in notificaciones
    ]


@router.patch("/{notificacion_id}/leida", response_model=NotificacionResponse)
def marcar_como_leida(
    notificacion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """El destinatario descarta la notificación una vez la vio."""
    notificacion = repo.marcar_leida(db, notificacion_id, current_user.id)
    if notificacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificación no encontrada")

    remitente = UserRepository(db).get_by_id(notificacion.remitente_id)
    return NotificacionResponse(
        id=notificacion.id,
        remitente_nombre=remitente.full_name if remitente else "Equipo Vitalis",
        mensaje=notificacion.mensaje,
        leida=notificacion.leida,
        created_at=notificacion.created_at,
    )


# ── Centro de anuncios (solo administrador) ───────────────────────────────────
#
# Los anuncios van solo a cuentas con rol `student` (los profesionales no reciben
# notificaciones) y activas. Un anuncio se guarda como una notificación por
# destinatario, así el usuario lo ve en su campana igual que las individuales.


def _base_estudiantes(db: Session):
    """Query de los ids de estudiantes activos: la audiencia de cualquier anuncio."""
    return db.query(User.id).filter(
        User.role == UserRole.STUDENT.value, User.is_active.is_(True)
    )


def _ultima_encuesta_por_usuario(db: Session) -> dict:
    sub = (
        db.query(EncuestaHplp.usuario_id, func.max(EncuestaHplp.id).label("eid"))
        .group_by(EncuestaHplp.usuario_id)
        .subquery()
    )
    filas = db.query(EncuestaHplp).join(sub, EncuestaHplp.id == sub.c.eid).all()
    return {e.usuario_id: e for e in filas}


def _sin_responder_medicion_abierta(db: Session) -> list[uuid.UUID]:
    """Estudiantes elegibles para la medición abierta que aún no la respondieron."""
    ciclo = ciclo_repo.obtener_seguimiento_abierto(db)
    if ciclo is None:
        return []
    elegibles = {
        r[0]
        for r in _base_estudiantes(db)
        .join(EncuestaHplp, EncuestaHplp.usuario_id == User.id)
        .filter(EncuestaHplp.fecha_respuesta < como_utc(ciclo.fecha_apertura))
        .distinct()
        .all()
    }
    respondieron = {
        r[0]
        for r in db.query(EncuestaHplp.usuario_id)
        .filter(EncuestaHplp.ciclo_id == ciclo.id)
        .distinct()
        .all()
    }
    return list(elegibles - respondieron)


def _resolver_destinatarios(db: Session, segmento: str, valor: str | None) -> list[uuid.UUID]:
    if segmento == "todos":
        return [r[0] for r in _base_estudiantes(db).all()]
    if segmento == "facultad":
        return [r[0] for r in _base_estudiantes(db).filter(User.facultad == valor).all()]
    if segmento == "programa":
        return [r[0] for r in _base_estudiantes(db).filter(User.program == valor).all()]
    if segmento == "tipo":
        return [r[0] for r in _base_estudiantes(db).filter(User.tipo_usuario == valor).all()]
    if segmento == "nivel":
        ids = {r[0] for r in _base_estudiantes(db).all()}
        ultimas = _ultima_encuesta_por_usuario(db)
        return [uid for uid, enc in ultimas.items() if uid in ids and enc.nivel_global == valor]
    if segmento == "sin_responder":
        return _sin_responder_medicion_abierta(db)
    return []


def _validar_segmento(segmento: str, valor: str | None) -> None:
    if segmento not in SEGMENTOS_VALIDOS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Segmento no válido")
    if segmento in SEGMENTOS_CON_VALOR and not valor:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Este segmento necesita que elijas un valor",
        )
    if segmento == "nivel" and valor not in NIVELES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Nivel no válido")


@router.get("/segmentos", response_model=SegmentosResponse)
def segmentos(
    _admin: User = Depends(requiere_admin),
    db: Session = Depends(get_db),
):
    """Catálogos para armar un anuncio: facultades, programas, tipos, niveles y
    el estado de la medición abierta."""

    def distintos(columna):
        filas = (
            db.query(columna)
            .filter(User.role == UserRole.STUDENT.value, columna.isnot(None), columna != "")
            .distinct()
            .all()
        )
        return sorted(r[0] for r in filas)

    total = _base_estudiantes(db).count()

    ciclo = ciclo_repo.obtener_seguimiento_abierto(db)
    medicion = None
    if ciclo is not None:
        medicion = MedicionAbiertaInfo(
            nombre=ciclo.nombre,
            faltantes=len(_sin_responder_medicion_abierta(db)),
        )

    return SegmentosResponse(
        total_estudiantes=total,
        facultades=distintos(User.facultad),
        programas=distintos(User.program),
        tipos=distintos(User.tipo_usuario),
        niveles=NIVELES,
        medicion_abierta=medicion,
    )


@router.get("/difusion/preview", response_model=PreviewResponse)
def preview_difusion(
    segmento: str = Query(...),
    valor: str | None = Query(None),
    _admin: User = Depends(requiere_admin),
    db: Session = Depends(get_db),
):
    """Cuántas personas recibirían el anuncio, para mostrarlo antes de enviar."""
    _validar_segmento(segmento, valor)
    return PreviewResponse(destinatarios=len(_resolver_destinatarios(db, segmento, valor)))


@router.post("/difusion", response_model=DifusionResponse, status_code=status.HTTP_201_CREATED)
def enviar_difusion(
    data: DifusionRequest,
    admin: User = Depends(requiere_admin),
    db: Session = Depends(get_db),
):
    """Envía un anuncio a un segmento de estudiantes. Solo el administrador."""
    _validar_segmento(data.segmento, data.valor)
    destinatarios = _resolver_destinatarios(db, data.segmento, data.valor)
    if not destinatarios:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="No hay destinatarios para ese segmento",
        )
    enviados = repo.crear_difusion(db, admin.id, destinatarios, data.mensaje)
    return DifusionResponse(enviados=enviados)


@router.get("/enviadas", response_model=list[EnvioResumen])
def historial_enviadas(
    _admin: User = Depends(requiere_admin),
    db: Session = Depends(get_db),
):
    """Historial de anuncios y notificaciones enviadas en la plataforma."""
    filas = repo.listar_enviadas(db)

    user_repo = UserRepository(db)
    nombres: dict[uuid.UUID, str] = {}

    def nombre_de(remitente_id: uuid.UUID) -> str:
        if remitente_id not in nombres:
            u = user_repo.get_by_id(remitente_id)
            nombres[remitente_id] = u.full_name if u else "Equipo Vitalis"
        return nombres[remitente_id]

    return [
        EnvioResumen(
            remitente_nombre=nombre_de(f.remitente_id),
            mensaje=f.mensaje,
            total=f.total,
            leidas=int(f.leidas or 0),
            created_at=f.created_at,
        )
        for f in filas
    ]
