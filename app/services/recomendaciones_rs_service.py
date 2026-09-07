"""
Servicio de recomendaciones de Responsabilidad en Salud.
Tabla estática de 14 tarjetas (7 preguntas × 2 niveles: POBRE y MODERADO).
BUENO y EXCELENTE no reciben recomendación (el profesional así lo indicó).
"""
from app.models.encuesta_hplp import EncuestaHplp


def puntaje_a_nivel(valor: int) -> str:
    return {1: "POBRE", 2: "MODERADO", 3: "BUENO", 4: "EXCELENTE"}[valor]


PREGUNTAS = {
    3:  "Informar a los profesionales de la salud cualquier señal inusual o síntoma extraño en tu salud o cuerpo.",
    9:  "Procurar mantenerte informado acerca del mejoramiento de la salud.",
    15: "Hacer preguntas a los profesionales de la salud para poder entender sus instrucciones.",
    22: "Buscar una segunda opinión cuando tengas dudas de las recomendaciones de tu proveedor de servicios de salud.",
    28: "Dialogar tus puntos de vista acerca de la salud con los profesionales en este campo.",
    34: "Examinar mensualmente tu cuerpo para detectar cambios físicos o señales diferentes en él.",
    41: "Pedir orientación de los profesionales de la salud sobre cómo mantenerte en buen estado de salud.",
}

ITEM_FIELDS = {
    3:  "rs_item_03",
    9:  "rs_item_09",
    15: "rs_item_15",
    22: "rs_item_22",
    28: "rs_item_28",
    34: "rs_item_34",
    41: "rs_item_41",
}

# La misma técnica aplica para POBRE y MODERADO en cada pregunta.
_REC = {
    3: {
        "tecnica": "Bitácora de síntomas",
        "objetivo": "Desarrollar la capacidad de detectar signos y síntomas de alarma inusuales y consultar a tiempo.",
        "instrucciones": [
            "Toma 1 minuto cada noche para realizar un escaneo mental de pies a cabeza y determinar si hubo una señal inusual durante el día (algún dolor, fatiga, cambio).",
            "Registra el síntoma en tu diario de señales de alerta de la app: describe el síntoma, la duración y la intensidad.",
            "Ubica los síntomas en el semáforo de síntomas para definir si requieres atención inmediata: Verde (estado óptimo), Amarillo/Naranja (alerta temprana) o Rojo (urgencia).",
            "Lleva la bitácora de escaneo a tu consulta médica e informa al médico los registros que hiciste.",
        ],
        "tipo_actividad": "matriz",
        "config_actividad": {
            "cuadrantes": ["Verde (estado óptimo)", "Amarillo/Naranja (alerta temprana)", "Rojo (urgencia)"],
            "campos": ["Síntoma", "Duración", "Intensidad"],
        },
    },
    9: {
        "tecnica": "Alfabetización en salud",
        "objetivo": "Incrementar el conocimiento sobre estilo de vida saludable.",
        "instrucciones": [
            "Cada semana escoge un tema sobre estilo de vida saludable que desees aprender (nutrición, ejercicio, sueño, etc.).",
            "Busca información sobre el tema en fuentes oficiales (OMS, revistas científicas, boletines informativos). Puedes leer un artículo, aprender una receta saludable o realizar una rutina de ejercicio nueva.",
            "Pon en práctica lo aprendido y regístralo en la app.",
        ],
        "tipo_actividad": "matriz",
        "config_actividad": {
            "campos": ["Tema de esta semana", "Qué aprendiste o hiciste"],
        },
    },
    15: {
        "tecnica": "Pregunta – Respuesta – Confirmación",
        "objetivo": "Comprender de forma clara las recomendaciones e indicaciones dadas por el profesional de salud para garantizar un adecuado cumplimiento del tratamiento.",
        "instrucciones": [
            "Anota las dudas que tengas antes de ir a tu consulta médica para no olvidarlas cuando estés frente al médico. Puedes guiarte de las preguntas inteligentes que sugiere la app.",
            "Utiliza la técnica de feedback: explícale a tu médico lo que entendiste de las indicaciones para que pueda corregir errores.",
            "No te retires de la consulta hasta tener todas las dudas claras y las indicaciones entendidas.",
        ],
        "tipo_actividad": "lista",
        "config_actividad": {"placeholder": "Duda o pregunta para tu próxima consulta"},
    },
    22: {
        "tecnica": "Triangulación de criterio médico",
        "objetivo": "Empoderar al usuario en la seguridad sobre su tratamiento y la certeza en la toma de decisiones.",
        "instrucciones": [
            "Cuando tengas dudas sobre las recomendaciones médicas, no tengas miedo de preguntar; si es necesario, solicita evidencia científica.",
            "Si aún tienes dudas o no estás seguro con las recomendaciones, solicita una segunda cita con otro profesional diferente y exprésale tu caso y tus dudas.",
            "Contrasta ambas informaciones para poder tomar una decisión final sobre tu tratamiento.",
        ],
    },
    28: {
        "tecnica": "Negociación conductual en la consulta médica",
        "objetivo": "Fomentar la integración de las creencias personales con las recomendaciones médicas.",
        "instrucciones": [
            "Identifica creencias o hábitos que no van acorde con las sugerencias médicas.",
            "Expresa tu punto de vista o creencia al médico de forma respetuosa.",
            "Llega a un acuerdo con el médico y diseña un plan de tratamiento en que converjan ambos puntos de vista, que sea realista y ajustable a tu vida.",
        ],
    },
    34: {
        "tecnica": "Autoexamen corporal",
        "objetivo": "Crear el hábito de realizar los autoexámenes para detectar alguna alteración a tiempo.",
        "instrucciones": [
            "Configura en la app una alarma mensual para realizarte el autoexamen (de mama en mujeres, testicular en hombres).",
            "Sigue los pasos de la imagen o del video para realizarte el autoexamen.",
            "Reporta en la app si encuentras un hallazgo anormal o si no encuentras cambios.",
            "Si encuentras algo fuera de lo normal, consulta al médico y reporta el hallazgo.",
        ],
        "tipo_actividad": "autoexamen_corporal",
    },
    41: {
        "tecnica": "Control médico preventivo",
        "objetivo": "Promover la salud antes de que llegue un proceso de enfermedad.",
        "instrucciones": [
            "Agenda una cita de revisión y promoción de la salud sin necesidad de tener algún signo de enfermedad.",
            "Solicita un análisis de tu estilo de vida para detectar los factores de riesgo a desarrollar enfermedades.",
            "Trabaja en los factores de riesgo detectados haciendo cambios en tu estilo de vida que busquen disminuir el riesgo de desarrollar una enfermedad.",
        ],
    },
}

RECOMENDACIONES: dict[int, dict[str, dict]] = {
    num_q: {"POBRE": rec, "MODERADO": rec}
    for num_q, rec in _REC.items()
}

NIVELES_CON_RECOMENDACION = {"POBRE", "MODERADO"}
PRIORIDAD_NIVEL = {"POBRE": 0, "MODERADO": 1}


def obtener_recomendaciones_rs(encuesta: EncuestaHplp) -> list[dict]:
    """
    Devuelve tarjetas de recomendación de Responsabilidad en Salud.
    Solo para POBRE y MODERADO. Orden: POBRE → MODERADO.
    """
    tarjetas = []
    for num_q, campo in ITEM_FIELDS.items():
        valor = getattr(encuesta, campo)
        nivel = puntaje_a_nivel(valor)
        if nivel not in NIVELES_CON_RECOMENDACION:
            continue
        rec = RECOMENDACIONES[num_q][nivel]
        tarjetas.append({
            "pregunta_num": num_q,
            "pregunta_texto": PREGUNTAS[num_q],
            "nivel": nivel,
            "puntaje": valor,
            "tecnica": rec["tecnica"],
            "objetivo": rec["objetivo"],
            "instrucciones": rec["instrucciones"],
            "tipo_actividad": rec.get("tipo_actividad", "checklist_simple"),
            "config_actividad": rec.get("config_actividad"),
        })
    tarjetas.sort(key=lambda t: PRIORIDAD_NIVEL[t["nivel"]])
    return tarjetas
