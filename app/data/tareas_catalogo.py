"""Catálogo estático de tareas diarias por dimensión PEPS II."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TareaDef:
    id: str
    dimension: str
    titulo: str
    descripcion: str
    xp: int
    duracion_min: int | None
    dificultad: str


TAREAS_CATALOGO: list[TareaDef] = [
    # Psicología positiva
    TareaDef("PP-01", "psicologia_positiva", "Gratitud del día", "Escribe 3 cosas por las que estás agradecido hoy.", 25, 5, "facil"),
    TareaDef("PP-02", "psicologia_positiva", "Lectura inspiradora", "Lee algo inspirador y anota una idea aplicable a tu día.", 25, 10, "facil"),
    TareaDef("PP-03", "psicologia_positiva", "Gratitud express", "Nombra en voz alta algo positivo que ocurrió hoy.", 20, 3, "facil"),
    TareaDef("PP-04", "psicologia_positiva", "Meta significativa", "Escribe una meta significativa para esta semana.", 30, 10, "media"),
    TareaDef("PP-05", "psicologia_positiva", "Tiempo de disfrute", "Dedica 10 minutos a una actividad que disfrutes sin pantallas.", 25, 10, "facil"),
    # Actividad física
    TareaDef("AF-01", "actividad_fisica", "Caminata activa", "Realiza una caminata de 20–30 minutos al aire libre.", 30, 25, "media"),
    TareaDef("AF-02", "actividad_fisica", "Estiramientos matutinos", "Haz una rutina de estiramientos de 10 minutos.", 25, 10, "facil"),
    TareaDef("AF-03", "actividad_fisica", "Escaleras activas", "Sube escaleras en lugar del ascensor cuando puedas.", 20, None, "facil"),
    TareaDef("AF-04", "actividad_fisica", "Registro de movimiento", "Registra tu actividad física del día (tipo y duración).", 20, 5, "facil"),
    TareaDef("AF-05", "actividad_fisica", "Sesión moderada", "Realiza 30 minutos de movimiento moderado.", 35, 30, "dificil"),
    # Responsabilidad en salud
    TareaDef("RS-01", "responsabilidad_salud", "Chequeo personal", "Registra tu estado de salud hoy: sueño, energía y síntomas.", 20, 5, "facil"),
    TareaDef("RS-02", "responsabilidad_salud", "Rutina de salud", "Cumple con tu rutina de medicamentos o suplementos indicados.", 25, None, "facil"),
    TareaDef("RS-03", "responsabilidad_salud", "Hidratación", "Bebe al menos 6 vasos de agua hoy.", 20, None, "facil"),
    TareaDef("RS-04", "responsabilidad_salud", "Lectura de salud", "Lee una recomendación de salud de tu plan durante 5 minutos.", 25, 5, "facil"),
    TareaDef("RS-05", "responsabilidad_salud", "Cita preventiva", "Programa o confirma una cita médica preventiva.", 35, 10, "dificil"),
    # Relaciones interpersonales
    TareaDef("RI-01", "relaciones_interpersonales", "Mensaje de afecto", "Envía un mensaje de afecto a alguien cercano.", 25, 5, "facil"),
    TareaDef("RI-02", "relaciones_interpersonales", "Conexión social", "Llama o escribe a un amigo o familiar.", 30, 15, "media"),
    TareaDef("RI-03", "relaciones_interpersonales", "Escucha activa", "Practica escucha activa en una conversación hoy.", 25, None, "facil"),
    TareaDef("RI-04", "relaciones_interpersonales", "Aprecio concreto", "Expresa aprecio específico a alguien de tu entorno.", 25, 5, "facil"),
    TareaDef("RI-05", "relaciones_interpersonales", "Momento compartido", "Comparte un momento positivo con alguien de tu círculo.", 30, 20, "media"),
    # Nutrición
    TareaDef("N-01", "nutricion", "Frutas y verduras", "Incluye una fruta o verdura en cada comida principal.", 25, None, "facil"),
    TareaDef("N-02", "nutricion", "Diario alimentario", "Registra lo que comiste hoy (desayuno, almuerzo y cena).", 20, 10, "facil"),
    TareaDef("N-03", "nutricion", "Snack saludable", "Elige un snack saludable en lugar de ultraprocesado.", 20, None, "facil"),
    TareaDef("N-04", "nutricion", "Agua antes de comer", "Bebe agua antes de cada comida principal.", 20, None, "facil"),
    TareaDef("N-05", "nutricion", "Comida balanceada", "Prepara una comida balanceada en casa.", 30, 30, "media"),
    # Manejo del estrés
    TareaDef("ME-01", "manejo_estres", "Respiración 4-7-8", "Practica respiración 4-7-8 durante 3 ciclos.", 20, 5, "facil"),
    TareaDef("ME-02", "manejo_estres", "Desconexión nocturna", "Pasa 15 minutos sin pantallas antes de dormir.", 25, 15, "facil"),
    TareaDef("ME-03", "manejo_estres", "Pausa consciente", "Toma una pausa consciente de 5 minutos durante el día.", 20, 5, "facil"),
    TareaDef("ME-04", "manejo_estres", "Diario emocional", "Escribe en un diario emocional cómo te sentiste hoy.", 25, 10, "facil"),
    TareaDef("ME-05", "manejo_estres", "Relajación muscular", "Practica relajación muscular progresiva durante 10 minutos.", 30, 10, "media"),
]

TAREAS_POR_ID: dict[str, TareaDef] = {t.id: t for t in TAREAS_CATALOGO}

TAREAS_POR_DIMENSION: dict[str, list[TareaDef]] = {}
for _tarea in TAREAS_CATALOGO:
    TAREAS_POR_DIMENSION.setdefault(_tarea.dimension, []).append(_tarea)

DIMENSIONES = list(TAREAS_POR_DIMENSION.keys())

DIMENSION_LABELS: dict[str, str] = {
    "psicologia_positiva": "Psicología positiva",
    "actividad_fisica": "Actividad física",
    "responsabilidad_salud": "Responsabilidad en salud",
    "relaciones_interpersonales": "Relaciones interpersonales",
    "nutricion": "Nutrición",
    "manejo_estres": "Manejo del estrés",
}
