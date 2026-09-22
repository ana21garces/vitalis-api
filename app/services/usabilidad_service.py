from datetime import date

from sqlalchemy.orm import Session

from app.data.csuq import TOTAL_ITEMS, calcular_puntajes
from app.models.encuesta_usabilidad import EncuestaUsabilidad
from app.models.usabilidad_campana import UsabilidadCampana
from app.models.user import User, UserRole
from app.services.gamificacion_service import hoy_bogota

# Áreas de bienestar que el admin puede responder impersonando el rol.
ROLES_AREA = {
    UserRole.CAPELLAN.value,
    UserRole.ACTIVIDAD_FISICA.value,
    UserRole.RESPONSABILIDAD_SALUD.value,
    UserRole.RELACIONES_INTERPERSONALES.value,
    UserRole.MANEJO_ESTRES.value,
    UserRole.NUTRICION.value,
}


def rol_efectivo(user: User, rol: str | None) -> str:
    """El admin puede guardar bajo el rol del área que administra; los demás
    siempre quedan con su propio rol."""
    if user.role == UserRole.ADMIN.value and rol in ROLES_AREA:
        return rol
    return user.role


def obtener_campana(db: Session) -> UsabilidadCampana:
    campana = db.get(UsabilidadCampana, 1)
    if campana is None:
        campana = UsabilidadCampana(id=1, activa=False)
        db.add(campana)
        db.commit()
        db.refresh(campana)
    return campana


def guardar_campana(
    db: Session, activa: bool, fecha_inicio: date | None, fecha_fin: date | None
) -> UsabilidadCampana:
    campana = obtener_campana(db)
    campana.activa = activa
    campana.fecha_inicio = fecha_inicio
    campana.fecha_fin = fecha_fin
    db.commit()
    db.refresh(campana)
    return campana


def campana_abierta(db: Session) -> bool:
    campana = obtener_campana(db)
    if not campana.activa:
        return False
    hoy = hoy_bogota()
    if campana.fecha_inicio and hoy < campana.fecha_inicio:
        return False
    if campana.fecha_fin and hoy > campana.fecha_fin:
        return False
    return True


def total_respuestas(db: Session) -> int:
    return db.query(EncuestaUsabilidad.id).count()


def ya_respondio(db: Session, usuario_id, rol: str) -> bool:
    return (
        db.query(EncuestaUsabilidad.id)
        .filter(EncuestaUsabilidad.usuario_id == usuario_id, EncuestaUsabilidad.rol == rol)
        .first()
        is not None
    )


def guardar(db: Session, user: User, respuestas: list[int], rol: str) -> EncuestaUsabilidad:
    puntajes = calcular_puntajes(respuestas)
    fila = EncuestaUsabilidad(
        usuario_id=user.id,
        rol=rol,
        **{f"item_{i:02d}": respuestas[i - 1] for i in range(1, TOTAL_ITEMS + 1)},
        **puntajes,
    )
    db.add(fila)
    db.commit()
    db.refresh(fila)
    return fila
