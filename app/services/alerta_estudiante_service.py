"""Avisa a la dimensión cuando un estudiante queda en nivel crítico (Pobre o
Moderado) al responder la encuesta. La alerta se dirige al ROL de la dimensión,
no a una persona: la ve el profesional de esa dimensión y también el
administrador cuando entra a su vista.

El enlace apunta hoy al listado de la vista profesional con la persona
resaltada; cuando exista la ficha individual por persona (tarea aparte), basta
cambiar `_enlace_persona` para repuntarlo."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.encuesta_hplp import EncuestaHplp
from app.models.user import User, UserRole
from app.repositories import notificacion_repository

NIVELES_CRITICOS = {"Pobre", "Moderado"}
ORDEN_NIVEL = {"pobre": 0, "moderado": 1, "bueno": 2, "excelente": 3}

# prefijo de columna en encuestas_hplp → (etiqueta, rol profesional, ruta de su vista)
DIMENSIONES = [
    ("af", "Actividad física", UserRole.ACTIVIDAD_FISICA, "/dashboard/actividad-fisica"),
    ("n", "Nutrición", UserRole.NUTRICION, "/dashboard/nutricion"),
    ("rs", "Responsabilidad en salud", UserRole.RESPONSABILIDAD_SALUD, "/dashboard/responsabilidad-salud"),
    ("ri", "Relaciones interpersonales", UserRole.RELACIONES_INTERPERSONALES, "/dashboard/relaciones-interpersonales"),
    ("me", "Manejo del estrés", UserRole.MANEJO_ESTRES, "/dashboard/manejo-estres"),
    ("pp", "Psicología positiva", UserRole.CAPELLAN, "/dashboard/capellan"),
]


def _enlace_persona(ruta_vista: str, alumno_id) -> str:
    return f"{ruta_vista}?alerta={alumno_id}"


def notificar_alertas(db: Session, alumno: User, encuesta: EncuestaHplp) -> int:
    """Crea una alerta por cada dimensión en la que el alumno quedó en nivel
    crítico, dirigida al rol de esa dimensión. Devuelve cuántas se crearon."""
    creadas = 0
    for prefijo, etiqueta, rol, ruta_vista in DIMENSIONES:
        nivel = getattr(encuesta, f"{prefijo}_nivel", None)
        if nivel not in NIVELES_CRITICOS:
            continue

        mensaje = (
            f"🔴 {alumno.full_name} quedó en nivel {nivel} en {etiqueta}. "
            f"Requiere atención."
        )
        notificacion_repository.crear(
            db,
            remitente_id=alumno.id,
            destinatario_id=None,
            mensaje=mensaje,
            enlace=_enlace_persona(ruta_vista, alumno.id),
            rol_destinatario=rol.value,
            tipo="alerta",
        )
        creadas += 1
    return creadas


def notificar_retrocesos(db: Session, alumno: User, actual: EncuestaHplp, base: EncuestaHplp) -> int:
    """Avisa al rol de cada dimensión en la que el alumno BAJÓ de nivel respecto
    a su línea base (retrocedió en vez de avanzar). Devuelve cuántas se crearon."""
    creadas = 0
    for prefijo, etiqueta, rol, ruta_vista in DIMENSIONES:
        nivel_actual = getattr(actual, f"{prefijo}_nivel", None)
        nivel_base = getattr(base, f"{prefijo}_nivel", None)
        pos_base = ORDEN_NIVEL.get((nivel_base or "").lower())
        pos_actual = ORDEN_NIVEL.get((nivel_actual or "").lower())
        if pos_base is None or pos_actual is None or pos_actual >= pos_base:
            continue

        mensaje = (
            f"🔻 {alumno.full_name} retrocedió en {etiqueta}: "
            f"bajó de {nivel_base} a {nivel_actual}."
        )
        notificacion_repository.crear(
            db,
            remitente_id=alumno.id,
            destinatario_id=None,
            mensaje=mensaje,
            enlace=_enlace_persona(ruta_vista, alumno.id),
            rol_destinatario=rol.value,
            tipo="alerta",
        )
        creadas += 1
    return creadas
