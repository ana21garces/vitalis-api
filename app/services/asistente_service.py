import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.data.tareas_catalogo import DIMENSION_LABELS
from app.models.asistente import AsistenteSaludo
from app.models.user import User
from app.repositories import encuesta_hplp_repository as encuesta_repo
from app.services.gamificacion_service import GamificacionService, hoy_bogota
from app.services.seguimiento_recomendacion_service import SeguimientoRecomendacionService

logger = logging.getLogger(__name__)

PREFIJO_A_DIMENSION = {
    "af": "actividad_fisica",
    "n": "nutricion",
    "rs": "responsabilidad_salud",
    "ri": "relaciones_interpersonales",
    "me": "manejo_estres",
    "pp": "psicologia_positiva",
}

# Mismo orden que la sección "Dimensiones prioritarias" del dashboard: por índice
# de menor a mayor, y los empates en este orden.
ORDEN_DASHBOARD = ["rs", "pp", "af", "ri", "n", "me"]

DATOS_VACIOS = {
    "misiones_pendientes": [],
    "plan": [],
    "racha": 0,
}


def _dimensiones_prioritarias(encuesta) -> list[str]:
    if encuesta is None or getattr(encuesta, "nivel_global", None) == "Excelente":
        return []
    indices = [(p, getattr(encuesta, f"{p}_indice", None) or 0.0) for p in ORDEN_DASHBOARD]
    ordenadas = sorted(indices, key=lambda par: par[1])
    corte = ordenadas[min(2, len(ordenadas) - 1)][1]
    return [PREFIJO_A_DIMENSION[p] for p, idx in ordenadas if idx <= corte]


def _plan_con_progreso(db: Session, user: User, encuesta) -> list[dict]:
    prioritarias = _dimensiones_prioritarias(encuesta)
    if not prioritarias:
        return []

    progreso = SeguimientoRecomendacionService(db).progreso_general(user, encuesta)
    por_dimension = {d.dimension: d for d in progreso.dimensiones}

    plan = []
    for dimension in prioritarias:
        avance = por_dimension.get(dimension)
        plan.append({
            "dimension": dimension,
            "label": DIMENSION_LABELS[dimension],
            "completadas": avance.completadas if avance else 0,
            "total": avance.total if avance else 0,
            "activas": avance.activas if avance else 0,
            "registradas_hoy": avance.registradas_hoy if avance else 0,
        })
    return plan


def _datos_del_dia(db: Session, user: User) -> dict:
    misiones = GamificacionService(db).obtener_misiones_hoy(user)
    misiones_pendientes = [m.titulo for m in misiones.misiones if not m.completada]
    encuesta = encuesta_repo.obtener_ultimo(db, user.id)
    return {
        "misiones_pendientes": misiones_pendientes,
        "plan": _plan_con_progreso(db, user, encuesta),
        "racha": user.streak_days or 0,
    }


def _mensaje_respaldo(datos: dict, nombre: str) -> str:
    if not datos["misiones_pendientes"]:
        return f"¡Bien hecho, {nombre}! 🎉 Completaste tus misiones de hoy."
    return f"¡Hola, {nombre}! 👋 Estos son tus retos de hoy. ¡Un ratico y los sacas! 💪"


def _prompt(datos: dict) -> str:
    pendientes = len(datos["misiones_pendientes"])
    foco = datos["plan"][0]["label"] if datos["plan"] else "su bienestar general"
    racha = datos["racha"]
    return (
        'Eres "Asistente UnacHealth", un asistente breve y motivador de una '
        "plataforma universitaria de bienestar. Escribe un saludo MUY corto (1 o 2 "
        "líneas), cálido, en español, tuteando al estudiante y llamándolo {nombre}.\n"
        f"- Misiones diarias que le faltan hoy: {pendientes}\n"
        f"- Dimensión en la que está más bajo: {foco}\n"
        f"- Días seguidos registrando actividades: {racha}\n"
        f"Menciona «{foco}» por su nombre para que sepa dónde poner el foco hoy"
        + (
            f", y felicítalo por llevar {racha} días seguidos.\n"
            if racha > 1
            else ".\n"
        )
        + "NO enumeres las misiones ni las recomendaciones (se muestran aparte en una "
        "lista). No des consejos médicos ni diagnósticos, no inventes datos ni cifras "
        "que no te di, y usa uno o dos emojis como mucho. Devuelve SOLO el saludo, sin "
        "comillas ni títulos, y escribe {nombre} tal cual donde quieras poner el nombre."
    )


def _generar_con_gemini(datos: dict, nombre: str) -> str | None:
    if not settings.GEMINI_API_KEY:
        return None
    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        modelo = genai.GenerativeModel(settings.GEMINI_MODEL)
        texto = modelo.generate_content(
            _prompt(datos),
            request_options={"timeout": 8, "retry": None},
        ).text
        if texto and texto.strip():
            return texto.strip().replace("{nombre}", nombre)
    except Exception:
        logger.exception("Falló Gemini en el asistente; se usa el mensaje de respaldo")
    return None


def _saludo_del_dia(db: Session, user: User, datos: dict, nombre: str) -> str:
    if not datos["misiones_pendientes"]:
        return _mensaje_respaldo(datos, nombre)

    hoy = hoy_bogota()
    try:
        cacheado = (
            db.query(AsistenteSaludo.mensaje)
            .filter(AsistenteSaludo.user_id == user.id, AsistenteSaludo.fecha == hoy)
            .scalar()
        )
    except Exception:
        db.rollback()
        cacheado = None
    if cacheado:
        return cacheado

    # Se guarda el resultado incluso cuando Gemini falla: si no, un límite de
    # cuota hacía que cada apertura de la burbuja reintentara y quemara el resto.
    saludo = _generar_con_gemini(datos, nombre) or _mensaje_respaldo(datos, nombre)
    try:
        db.add(AsistenteSaludo(user_id=user.id, fecha=hoy, mensaje=saludo))
        db.commit()
    except Exception:
        db.rollback()
    return saludo


def generar_mensaje(db: Session, user: User) -> dict:
    try:
        datos = _datos_del_dia(db, user)
    except Exception:
        logger.exception("No se pudieron leer los retos del día para el asistente")
        datos = DATOS_VACIOS

    primer_nombre = (user.full_name or "").strip().split(" ")[0] or "estudiante"
    pendientes = len(datos["misiones_pendientes"])

    mensaje = _saludo_del_dia(db, user, datos, primer_nombre)

    return {
        "mensaje": mensaje,
        "misiones": datos["misiones_pendientes"],
        "plan": datos["plan"],
        "pendientes": pendientes,
        "todo_hecho": pendientes == 0,
    }
