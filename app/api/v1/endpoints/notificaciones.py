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
    ResponderInvitacion,
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

# Cómo se muestra el remitente cuando la notificación se envía desde un rol
# (el estudiante ve la dimensión, no el nombre de quien la mandó).
ETIQUETA_REMITENTE_ROL = {
    UserRole.CAPELLAN.value: "Profesional de Psicología Positiva",
    UserRole.ACTIVIDAD_FISICA.value: "Profesional de Actividad Física",
    UserRole.RESPONSABILIDAD_SALUD.value: "Profesional de Responsabilidad en Salud",
    UserRole.RELACIONES_INTERPERSONALES.value: "Profesional de Relaciones Interpersonales",
    UserRole.MANEJO_ESTRES.value: "Profesional de Manejo del Estrés",
    UserRole.NUTRICION.value: "Profesional de Nutrición",
}


def _puede_responder(n) -> bool:
    """Una invitación a cita (dirigida a un estudiante desde un rol) que el
    estudiante todavía no ha respondido."""
    return bool(n.remitente_rol and n.destinatario_id and not n.respuesta)


RUTA_POR_ROL = {
    UserRole.ACTIVIDAD_FISICA.value: "/dashboard/actividad-fisica",
    UserRole.NUTRICION.value: "/dashboard/nutricion",
    UserRole.RESPONSABILIDAD_SALUD.value: "/dashboard/responsabilidad-salud",
    UserRole.RELACIONES_INTERPERSONALES.value: "/dashboard/relaciones-interpersonales",
    UserRole.MANEJO_ESTRES.value: "/dashboard/manejo-estres",
    UserRole.CAPELLAN.value: "/dashboard/capellan",
}


def _enlace_historial(rol: str | None, alumno_id) -> str:
    # Hoy lleva a la persona dentro de la vista de la dimensión; cuando exista el
    # historial individual descargable (en desarrollo por Ana), se repunta aquí.
    ruta = RUTA_POR_ROL.get(rol, "/dashboard")
    return f"{ruta}?alerta={alumno_id}"


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

    # El admin actúa como el rol de la vista en la que está (data.rol); un
    # profesional real siempre usa su propio rol, sin importar lo que envíe.
    if current_user.role == UserRole.ADMIN.value:
        remitente_rol = data.rol if data.rol in ETIQUETA_REMITENTE_ROL else None
    else:
        remitente_rol = current_user.role if current_user.role in ETIQUETA_REMITENTE_ROL else None

    notificacion = repo.crear(
        db, current_user.id, destinatario_uuid, data.mensaje, remitente_rol=remitente_rol
    )
    return NotificacionResponse(
        id=notificacion.id,
        remitente_nombre=ETIQUETA_REMITENTE_ROL.get(remitente_rol, current_user.full_name),
        mensaje=notificacion.mensaje,
        enlace=notificacion.enlace,
        tipo=notificacion.tipo,
        puede_responder=_puede_responder(notificacion),
        respuesta=notificacion.respuesta,
        leida=notificacion.leida,
        created_at=notificacion.created_at,
    )


@router.get("", response_model=list[NotificacionResponse])
def mis_notificaciones(
    rol: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Notificaciones de la campana del usuario, más recientes primero. Incluye
    las alertas del rol que se está viendo: un profesional ve las de su
    dimensión; el administrador ve las de la vista en la que entró (`rol`)."""
    notificaciones = repo.listar_para(db, current_user, rol)

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
            remitente_nombre=ETIQUETA_REMITENTE_ROL.get(n.remitente_rol, nombre_de(n.remitente_id)),
            mensaje=n.mensaje,
            enlace=n.enlace,
            tipo=n.tipo,
            puede_responder=_puede_responder(n),
            respuesta=n.respuesta,
            leida=n.leida,
            created_at=n.created_at,
        )
        for n in notificaciones
    ]


@router.get("/notificados", response_model=dict[str, str])
def estudiantes_notificados(
    rol: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Estado de la invitación a cita de cada estudiante en una dimensión:
    `pendiente`, `aceptada` o `rechazada`, indexado por id.

    La vista lo usa para distinguir a quien todavía no contesta de quien rechazó
    —a ese se le puede volver a invitar— y que el estado sobreviva a recargar.
    Admin o el profesional del rol.
    """
    if current_user.role != UserRole.ADMIN.value and current_user.role != rol:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    return repo.estados_invitacion_por_rol(db, rol)


@router.patch("/{notificacion_id}/leida", response_model=NotificacionResponse)
def marcar_como_leida(
    notificacion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Descarta la notificación una vez la vio quien puede verla."""
    notificacion = repo.marcar_leida(db, notificacion_id, current_user)
    if notificacion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificación no encontrada")

    remitente = UserRepository(db).get_by_id(notificacion.remitente_id)
    nombre = remitente.full_name if remitente else "Equipo Vitalis"
    return NotificacionResponse(
        id=notificacion.id,
        remitente_nombre=ETIQUETA_REMITENTE_ROL.get(notificacion.remitente_rol, nombre),
        mensaje=notificacion.mensaje,
        enlace=notificacion.enlace,
        tipo=notificacion.tipo,
        puede_responder=_puede_responder(notificacion),
        respuesta=notificacion.respuesta,
        leida=notificacion.leida,
        created_at=notificacion.created_at,
    )


@router.post("/{notificacion_id}/responder", response_model=NotificacionResponse)
def responder_invitacion(
    notificacion_id: int,
    data: ResponderInvitacion,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """El estudiante acepta o rechaza una invitación a cita. Le avisa de vuelta
    al rol que lo invitó (lo ve ese profesional y el admin en su vista)."""
    notificacion = repo.obtener(db, notificacion_id)
    if notificacion is None or notificacion.destinatario_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificación no encontrada")
    if not notificacion.remitente_rol:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Esta notificación no admite respuesta")
    if notificacion.respuesta is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya respondiste esta invitación")

    notificacion.respuesta = "aceptada" if data.acepta else "rechazada"
    notificacion.leida = True
    db.commit()
    db.refresh(notificacion)

    # Ambas respuestas llevan a la persona en la vista: aceptada, a su historial
    # (repunta cuando exista); rechazada, para poder volver a invitarla.
    verbo = "Aceptó" if data.acepta else "Rechazó"
    repo.crear(
        db,
        remitente_id=current_user.id,
        destinatario_id=None,
        mensaje=f"{verbo} la invitación a agendar una cita.",
        rol_destinatario=notificacion.remitente_rol,
        enlace=_enlace_historial(notificacion.remitente_rol, current_user.id),
        tipo="cita_aceptada" if data.acepta else "cita_rechazada",
    )

    return NotificacionResponse(
        id=notificacion.id,
        remitente_nombre=ETIQUETA_REMITENTE_ROL.get(notificacion.remitente_rol, "Equipo Vitalis"),
        mensaje=notificacion.mensaje,
        enlace=notificacion.enlace,
        tipo=notificacion.tipo,
        puede_responder=_puede_responder(notificacion),
        respuesta=notificacion.respuesta,
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
