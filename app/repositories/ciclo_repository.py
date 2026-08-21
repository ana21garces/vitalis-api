import uuid
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ciclo_medicion import LINEA_BASE, SEGUIMIENTO, CicloMedicion, como_utc
from app.models.encuesta_hplp import EncuestaHplp
from app.models.user import User, UserRole

# Los roles profesionales no responden la encuesta, así que no cuentan como
# elegibles al medir la participación.
ROLES_PROFESIONALES = [
    UserRole.ADMIN.value,
    UserRole.CAPELLAN.value,
    UserRole.ACTIVIDAD_FISICA.value,
    UserRole.RESPONSABILIDAD_SALUD.value,
    UserRole.RELACIONES_INTERPERSONALES.value,
    UserRole.MANEJO_ESTRES.value,
    UserRole.NUTRICION.value,
]


def obtener(db: Session, ciclo_id: int) -> CicloMedicion | None:
    return db.query(CicloMedicion).filter(CicloMedicion.id == ciclo_id).first()


def listar(db: Session) -> list[CicloMedicion]:
    """Todas las mediciones, la más reciente primero."""
    return db.query(CicloMedicion).order_by(CicloMedicion.numero.desc()).all()


def obtener_linea_base(db: Session) -> CicloMedicion:
    """La línea base, creándola la primera vez que se necesita.

    Se crea al vuelo en vez de en una migración para que una base recién hecha
    (o la de los tests) funcione sin ningún paso previo.
    """
    ciclo = db.query(CicloMedicion).filter(CicloMedicion.tipo == LINEA_BASE).first()
    if ciclo is not None:
        return ciclo

    ciclo = CicloMedicion(
        numero=1,
        nombre="Línea base",
        tipo=LINEA_BASE,
        fecha_apertura=datetime.now(timezone.utc),
        fecha_cierre=None,
    )
    db.add(ciclo)
    db.commit()
    db.refresh(ciclo)
    return ciclo


def obtener_seguimiento_abierto(db: Session) -> CicloMedicion | None:
    """El seguimiento cuya ventana está abierta ahora, si hay alguno."""
    for ciclo in db.query(CicloMedicion).filter(CicloMedicion.tipo == SEGUIMIENTO).all():
        if ciclo.esta_abierto:
            return ciclo
    return None


def obtener_seguimiento_vigente(db: Session) -> CicloMedicion | None:
    """El seguimiento abierto o aún por abrir: el que impide programar otro."""
    for ciclo in db.query(CicloMedicion).filter(CicloMedicion.tipo == SEGUIMIENTO).all():
        if ciclo.estado() in ("abierto", "programado"):
            return ciclo
    return None


def es_el_mas_reciente(db: Session, ciclo: CicloMedicion) -> bool:
    """Si no existe ninguna medición posterior a esta.

    Solo la más reciente se puede extender, cerrar o reabrir: si se reabriera
    una vieja, las respuestas que llegaran hoy serían las más nuevas de esa
    persona pero quedarían etiquetadas en una ronda anterior, y los promedios
    por ronda dejarían de significar lo que dicen.
    """
    maximo = db.query(func.max(CicloMedicion.numero)).scalar() or 0
    return ciclo.numero >= maximo


def siguiente_numero(db: Session) -> int:
    return (db.query(func.max(CicloMedicion.numero)).scalar() or 0) + 1


def crear_seguimiento(
    db: Session,
    nombre: str,
    fecha_apertura: datetime,
    fecha_cierre: datetime | None,
    creado_por: uuid.UUID | None,
) -> CicloMedicion:
    ciclo = CicloMedicion(
        numero=siguiente_numero(db),
        nombre=nombre,
        tipo=SEGUIMIENTO,
        fecha_apertura=fecha_apertura,
        fecha_cierre=fecha_cierre,
        creado_por=creado_por,
    )
    db.add(ciclo)
    db.commit()
    db.refresh(ciclo)
    return ciclo


def guardar(db: Session, ciclo: CicloMedicion) -> CicloMedicion:
    db.add(ciclo)
    db.commit()
    db.refresh(ciclo)
    return ciclo


def eliminar(db: Session, ciclo: CicloMedicion) -> None:
    db.delete(ciclo)
    db.commit()


def contar_respuestas(db: Session, ciclo_id: int) -> int:
    return (
        db.query(func.count(func.distinct(EncuestaHplp.usuario_id)))
        .filter(EncuestaHplp.ciclo_id == ciclo_id)
        .scalar()
        or 0
    )


def contar_elegibles(db: Session, ciclo: CicloMedicion) -> int:
    """A cuánta gente le aplica esta medición.

    Para la línea base son todos los usuarios que responden encuestas. Para un
    seguimiento, solo quienes ya tenían una encuesta cuando se abrió: medir la
    participación contra el total de usuarios daría un número injusto.
    """
    if ciclo.tipo == LINEA_BASE:
        return (
            db.query(func.count(User.id))
            .filter(User.role.notin_(ROLES_PROFESIONALES))
            .scalar()
            or 0
        )

    return (
        db.query(func.count(func.distinct(EncuestaHplp.usuario_id)))
        .join(User, User.id == EncuestaHplp.usuario_id)
        .filter(User.role.notin_(ROLES_PROFESIONALES))
        .filter(EncuestaHplp.fecha_respuesta < como_utc(ciclo.fecha_apertura))
        .scalar()
        or 0
    )


def es_elegible(db: Session, ciclo: CicloMedicion, usuario_id: uuid.UUID) -> bool:
    """Si a esta persona le toca responder la medición.

    La línea base le toca a quien no ha respondido nunca; un seguimiento, a
    quien ya tiene una encuesta anterior a la apertura de esa ventana.
    """
    anteriores = (
        db.query(EncuestaHplp)
        .filter(EncuestaHplp.usuario_id == usuario_id)
        .filter(EncuestaHplp.fecha_respuesta < como_utc(ciclo.fecha_apertura))
        .first()
    )
    if ciclo.tipo == LINEA_BASE:
        return anteriores is None
    return anteriores is not None
