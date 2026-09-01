"""Catálogo de insignias del estudiante.

`icono` es un nombre de ícono de lucide-react que el frontend mapea.
`rareza` define el estilo visual (comun / rara / epica).
`xp` es el bonus que se otorga al ganarla (reutiliza el XP de Duvan).
Las de `dimension` no nula son "Plan cumplido" de esa dimensión.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class InsigniaDef:
    id: str
    nombre: str
    descripcion: str
    criterio: str          # texto que ve el usuario mientras está bloqueada
    icono: str
    rareza: str
    xp: int
    dimension: str | None = None


INSIGNIAS: list[InsigniaDef] = [
    InsigniaDef(
        "primer_paso", "Primer paso",
        "Completaste tu primera encuesta de salud.",
        "Diste el primer paso: responde la encuesta.",
        "Footprints", "comun", 20,
    ),
    InsigniaDef(
        "constancia_7", "Constancia",
        "Mantuviste una actividad 7 días seguidos.",
        "Registra una actividad 7 días seguidos.",
        "Flame", "rara", 30,
    ),
    InsigniaDef(
        "imparable_21", "Imparable",
        "Mantuviste una actividad 21 días seguidos.",
        "Registra una actividad 21 días seguidos.",
        "Zap", "epica", 100,
    ),
    InsigniaDef(
        "explorador", "Explorador del bienestar",
        "Registraste al menos un día en las 6 dimensiones.",
        "Registra un día en cada una de las 6 dimensiones.",
        "Compass", "rara", 40,
    ),
    InsigniaDef(
        "semana_perfecta", "Semana perfecta",
        "Completaste todas tus misiones diarias 7 días seguidos.",
        "Completa las misiones del día, 7 días seguidos.",
        "CalendarCheck", "epica", 60,
    ),
    InsigniaDef(
        "evolucion", "Evolución",
        "Subiste de nivel global entre la primera encuesta y un seguimiento.",
        "Mejora tu nivel global en el siguiente seguimiento.",
        "TrendingUp", "epica", 60,
    ),
    InsigniaDef(
        "plan_actividad_fisica", "Plan cumplido: Actividad Física",
        "Completaste todas tus recomendaciones de Actividad Física.",
        "Completa todas las recomendaciones de Actividad Física.",
        "Dumbbell", "rara", 50, dimension="actividad_fisica",
    ),
    InsigniaDef(
        "plan_nutricion", "Plan cumplido: Nutrición",
        "Completaste todas tus recomendaciones de Nutrición.",
        "Completa todas las recomendaciones de Nutrición.",
        "Salad", "rara", 50, dimension="nutricion",
    ),
    InsigniaDef(
        "plan_responsabilidad_salud", "Plan cumplido: Responsabilidad en Salud",
        "Completaste todas tus recomendaciones de Responsabilidad en Salud.",
        "Completa todas las recomendaciones de Responsabilidad en Salud.",
        "Stethoscope", "rara", 50, dimension="responsabilidad_salud",
    ),
    InsigniaDef(
        "plan_relaciones_interpersonales", "Plan cumplido: Relaciones Interpersonales",
        "Completaste todas tus recomendaciones de Relaciones Interpersonales.",
        "Completa todas las recomendaciones de Relaciones Interpersonales.",
        "HeartHandshake", "rara", 50, dimension="relaciones_interpersonales",
    ),
    InsigniaDef(
        "plan_manejo_estres", "Plan cumplido: Manejo del Estrés",
        "Completaste todas tus recomendaciones de Manejo del Estrés.",
        "Completa todas las recomendaciones de Manejo del Estrés.",
        "Brain", "rara", 50, dimension="manejo_estres",
    ),
    InsigniaDef(
        "plan_psicologia_positiva", "Plan cumplido: Psicología Positiva",
        "Completaste todas tus recomendaciones de Psicología Positiva.",
        "Completa todas las recomendaciones de Psicología Positiva.",
        "Sparkles", "rara", 50, dimension="psicologia_positiva",
    ),
]

INSIGNIAS_POR_ID: dict[str, InsigniaDef] = {i.id: i for i in INSIGNIAS}
