"""
Servicio de recomendaciones de Actividad Física.
Tabla estática de 27 tarjetas (9 preguntas × 3 niveles) elaboradas por el profesional.
EXCELENTE no recibe recomendación.

Todas las fichas usan "tipo_actividad": "registro_numerico" (duración,
esfuerzo percibido, pasos o frecuencia cardíaca según la pregunta) — ver
"config_actividad.unidad" para lo que el frontend debe pedir.
"""
from app.models.encuesta_hplp import EncuestaHplp


def puntaje_a_nivel(valor: int) -> str:
    return {1: "POBRE", 2: "MODERADO", 3: "BUENO", 4: "EXCELENTE"}[valor]


PREGUNTAS = {
    4:  "Seguir un programa de ejercicio físico planificado por un profesional en este campo.",
    10: "Practicar semanalmente ejercicios vigorosos (≥ 3 días y ≥ 20 minutos por sesión).",
    16: "Practicar semanalmente actividades físicas de caminata (≥ 5 días y ≥ 30 minutos por sesión).",
    17: "Practicar semanalmente actividades físicas moderadas (≥ 5 días y ≥ 30 minutos por sesión).",
    23: "Practicar, en tus tiempos libres, actividades físicas de recreación (nadar, andar en bicicleta, escalar montañas, entre otras).",
    29: "Practicar ejercicios de estiramiento que involucren grandes grupos musculares (espaldas, pectorales, cadera, piernas) 3 veces por semana.",
    35: "Tratar de mejorar tu nivel de actividad física diaria a través de comportamientos como caminar a la hora del almuerzo, utilizar escaleras en vez de elevadores, estacionar el carro lejos del lugar de destino, entre otros.",
    42: "Medir tu frecuencia cardíaca cuando estás haciendo ejercicio.",
    47: "Alcanzar tu pulso cardíaco objetivo cuando haces ejercicios aeróbicos (caminar rápido, correr, pedalear, remar y nadar).",
}

ITEM_FIELDS = {
    4:  "af_item_04",
    10: "af_item_10",
    16: "af_item_16",
    17: "af_item_17",
    23: "af_item_23",
    29: "af_item_29",
    35: "af_item_35",
    42: "af_item_42",
    47: "af_item_47",
}

# Unidad de registro por pregunta (misma para los 3 niveles).
_UNIDAD_POR_PREGUNTA = {
    4:  "minutos",
    10: "minutos",
    16: "minutos",
    17: "minutos",
    23: "minutos",
    29: "repeticiones",
    35: "pasos",
    42: "pulsaciones por minuto",
    47: "minutos en zona objetivo",
}

RECOMENDACIONES: dict[int, dict[str, dict]] = {
    # ── Pregunta 4 ──────────────────────────────────────────────────────────
    4: {
        "POBRE": {
            "tecnica": "Programa de inicio seguro — Arquetipo L1 Clínico / L2 Principiante",
            "objetivo": "Crear el hábito de ejercicio con sesiones cortas, seguras y alcanzables para un usuario sedentario o con condición de riesgo.",
            "instrucciones": [
                "Completar el onboarding de la app: datos físicos, condición de salud, experiencia, días disponibles y equipo.",
                "Recibir el arquetipo asignado (L1 o L2) con explicación simple de qué significa y qué tipo de sesión recibirá.",
                "Iniciar con 2–3 sesiones semanales de 20–30 minutos, priorizando movilidad, fuerza básica y bajo impacto.",
                "Al finalizar cada sesión, reportar en la app qué tan difícil fue (escala 1–5). El sistema ajusta la siguiente sesión con base en esa respuesta.",
                "Si aparece dolor durante la sesión, usar el botón 'me duele' en el player para que la app sustituya el ejercicio automáticamente.",
            ],
        },
        "MODERADO": {
            "tecnica": "Programa estructurado con progresión — Arquetipo L2 / L3",
            "objetivo": "Consolidar el hábito de ejercicio con sesiones variadas que incluyan fuerza, cardio y flexibilidad, avanzando de arquetipo L2 a L3.",
            "instrucciones": [
                "Revisar el arquetipo actual del usuario y confirmar que está en L2 (principiante con base física) o avanzando a L3.",
                "Diseñar semanas con bloques de movimiento variados: 1 sesión de fuerza, 1 de cardio moderado, 1 de movilidad.",
                "Incrementar progresivamente la carga o duración cada 2 semanas si el feedback de sesión indica facilidad (RPE < 5).",
                "Registrar la asistencia semanal y felicitar rachas de cumplimiento desde la app.",
                "Revisión del programa cada 4 semanas para ajustar nivel, tipo de sesión y objetivo.",
            ],
        },
        "BUENO": {
            "tecnica": "Optimización de programa — Arquetipo L3 / L4",
            "objetivo": "Mantener y mejorar el rendimiento con sesiones de mayor complejidad, variedad y progresión controlada.",
            "instrucciones": [
                "Confirmar arquetipo L3 o L4 según historial de sesiones y feedback acumulado.",
                "Estructurar semanas con periodización básica: días de fuerza, cardio vigoroso y recuperación activa.",
                "Controlar la fatiga: si el feedback de 3 sesiones consecutivas indica RPE > 8, reducir intensidad o incluir semana de descarga.",
                "Revisar y actualizar el programa cada 4 semanas con nuevos objetivos.",
            ],
        },
    },
    # ── Pregunta 10 ─────────────────────────────────────────────────────────
    10: {
        "POBRE": {
            "tecnica": "Introducción gradual a la intensidad — Arquetipos L1/L2",
            "objetivo": "Llevar al usuario desde el reposo hacia niveles de esfuerzo moderado-vigoroso de forma segura y progresiva, sin riesgo de lesión o abandono.",
            "instrucciones": [
                "Iniciar con sesiones de intensidad leve (RPE 3–4), verificando tolerancia en las primeras 2 semanas.",
                "En la semana 3, incorporar intervalos cortos de mayor esfuerzo: 30 segundos de caminata rápida o troteo suave alternados con 90 segundos de recuperación. Repetir 5–8 veces.",
                "Evaluar respuesta mediante feedback al finalizar la sesión. Si RPE < 5 dos sesiones consecutivas, aumentar el intervalo de esfuerzo a 45 segundos.",
                "Objetivo de 8 semanas: alcanzar 20 minutos continuos a RPE 6–7 en al menos 2 sesiones semanales.",
                "Si hay mareo, dolor en el pecho o dificultad respiratoria anormal, detener y activar flujo de seguridad en la app.",
            ],
        },
        "MODERADO": {
            "tecnica": "Entrenamiento vigoroso por intervalos — Arquetipo L2/L3",
            "objetivo": "Alcanzar y sostener la frecuencia y duración recomendada de ejercicio vigoroso (≥ 3 días, ≥ 20 min) mediante sesiones de intervalos estructuradas.",
            "instrucciones": [
                "Calentar 5 minutos a paso suave o movilidad articular.",
                "Realizar intervalos de alta intensidad: 1 minuto de esfuerzo vigoroso (RPE 7–8) seguido de 1–2 minutos de recuperación activa. Completar 8–10 ciclos (20–25 minutos totales).",
                "Enfriar 5 minutos con caminata suave y estiramientos.",
                "Registrar la sesión en la app indicando duración, percepción de esfuerzo y si hubo dolor.",
                "Meta semanal: 3 sesiones completadas. La app muestra una barra de progreso para motivar.",
            ],
        },
        "BUENO": {
            "tecnica": "Entrenamiento vigoroso continuo — Arquetipo L3/L4",
            "objetivo": "Mantener y optimizar el rendimiento en ejercicio vigoroso con sesiones continuas y variadas.",
            "instrucciones": [
                "Alternar entre sesiones de cardio continuo (correr, pedalear, nadar) y sesiones de HIIT estructurado.",
                "Mantener al menos 3 sesiones vigorosas por semana, con duración de 25–40 minutos.",
                "Monitorear FC durante las sesiones para mantenerse en zona 75–85% FCmax.",
                "Incluir una semana de descarga (menor intensidad) cada 4 semanas para evitar sobreentrenamiento.",
            ],
        },
    },
    # ── Pregunta 16 ─────────────────────────────────────────────────────────
    16: {
        "POBRE": {
            "tecnica": "Protocolo de Caminata Progresiva — Arquetipo L1/L2",
            "objetivo": "Construir el hábito de caminata diaria desde cero, alcanzando gradualmente los 30 minutos diarios en 5 días a la semana.",
            "instrucciones": [
                "Semana 1–2: Caminar 15–20 minutos al día, 3 días a la semana, a paso cómodo (RPE 3–4).",
                "Semana 3–4: Aumentar a 25 minutos, 4 días a la semana. Mantener ritmo conversacional.",
                "Semana 5–6: Alcanzar 30 minutos, 5 días a la semana. Incluir 5 minutos de caminata rápida en el tramo central.",
                "Registrar cada caminata en la app (duración y cómo se sintió). La app muestra racha de días cumplidos.",
                "Usar las estrategias NEAT sugeridas: caminar a la hora del almuerzo, usar escaleras, estacionar lejos.",
            ],
        },
        "MODERADO": {
            "tecnica": "Caminata estructurada con variaciones — Arquetipo L2/L3",
            "objetivo": "Alcanzar de forma consistente los 5 días y 30 minutos semanales de caminata, incorporando variaciones que aumenten el beneficio cardiovascular.",
            "instrucciones": [
                "Establecer 5 días fijos de caminata en el calendario semanal (la app puede enviar recordatorios).",
                "Alternar días de caminata suave (30 min, RPE 4) con días de caminata con tramos rápidos (30 min, con 10 min a RPE 6).",
                "Una vez por semana, hacer una caminata más larga (40–45 min) en terreno variado o con desnivel leve.",
                "Registrar distancia y duración. Celebrar rachas de 5 días completados.",
            ],
        },
        "BUENO": {
            "tecnica": "Caminata activa y progresión a cardio — Arquetipo L3",
            "objetivo": "Mantener el hábito de caminata diaria y progresar hacia modalidades más exigentes como el troteo intermitente.",
            "instrucciones": [
                "Mantener 5 días de caminata/semana como base.",
                "En 2 de esos días, incorporar intervalos de troteo: 2 min troteo + 3 min caminata, durante 30 min.",
                "Una vez por semana, hacer una caminata larga de 50–60 minutos a ritmo moderado.",
                "Controlar FC para mantenerse en zona 60–75% FCmax.",
            ],
        },
    },
    # ── Pregunta 17 ─────────────────────────────────────────────────────────
    17: {
        "POBRE": {
            "tecnica": "Introducción a la actividad moderada — Arquetipo L1/L2",
            "objetivo": "Establecer el hábito de actividad física moderada diaria en un usuario que actualmente es sedentario o muy poco activo.",
            "instrucciones": [
                "Identificar 1–2 actividades de intensidad moderada que sean accesibles: bicicleta estática, baile, natación suave, caminata rápida.",
                "Iniciar con 20 minutos diarios, 3 días a la semana. La actividad debe permitir hablar con algo de dificultad (RPE 4–5).",
                "Semana 3: añadir un cuarto día. Semana 5: llegar a 5 días, 30 minutos.",
                "Registrar cada sesión en la app y marcar el nivel de esfuerzo percibido.",
                "La app ajusta la duración o intensidad siguiente con base en el feedback.",
            ],
        },
        "MODERADO": {
            "tecnica": "Consolidación de actividad moderada — Arquetipo L2/L3",
            "objetivo": "Cumplir consistentemente los 5 días y 30 minutos de actividad moderada semanal con variedad de modalidades.",
            "instrucciones": [
                "Planificar la semana con 5 actividades moderadas de tipo diferente: 2 días de caminata rápida, 1 día de bicicleta, 1 día de natación o baile, 1 día de actividad moderada libre.",
                "Mantener RPE 5–6 durante las sesiones. Si baja a RPE 3–4, aumentar el ritmo.",
                "Registrar asistencia semanal. La app celebra cuando se completan los 5 días.",
                "Cada 4 semanas, explorar una nueva actividad moderada para mantener la motivación.",
            ],
        },
        "BUENO": {
            "tecnica": "Variedad y mantenimiento de actividad moderada — Arquetipo L3",
            "objetivo": "Sostener el nivel de actividad moderada e incorporar progresiones hacia actividades más exigentes.",
            "instrucciones": [
                "Mantener 5 días de actividad moderada como base mínima.",
                "Incorporar 1–2 sesiones de mayor intensidad (RPE 7) para estimular adaptación cardiovascular.",
                "Variar las modalidades mensualmente para prevenir adaptación y mantener motivación.",
            ],
        },
    },
    # ── Pregunta 23 ─────────────────────────────────────────────────────────
    23: {
        "POBRE": {
            "tecnica": "Exploración de actividades recreativas — Arquetipo L1/L2",
            "objetivo": "Motivar al usuario a descubrir y probar actividades físicas recreativas accesibles y placenteras que generen adherencia a largo plazo.",
            "instrucciones": [
                "Mostrar en la app un menú de actividades recreativas con descripción breve e intensidad aproximada (caminata en parque, bicicleta, natación recreativa, baile, senderismo suave).",
                "Invitar al usuario a elegir 1 actividad que le genere curiosidad y planificarla una vez en la semana siguiente.",
                "Facilitar recursos simples en la app: dónde hacerla, qué necesita, cuánto dura una sesión típica.",
                "Al completarla, el usuario responde: ¿la disfrutaste? ¿la repetirías? La app aprende sus preferencias para futuras sugerencias.",
                "Objetivo del primer mes: 1 actividad recreativa por semana.",
            ],
        },
        "MODERADO": {
            "tecnica": "Planificación de recreación activa regular — Arquetipo L2/L3",
            "objetivo": "Estructurar la práctica de actividades recreativas como parte habitual del estilo de vida, con al menos 1–2 sesiones semanales.",
            "instrucciones": [
                "Revisar las actividades recreativas que el usuario ya disfruta o ha probado.",
                "Planificar en el calendario de la app 1–2 sesiones semanales de recreación activa.",
                "Combinar actividades: una de baja intensidad (caminata en parque, ciclismo suave) y una de intensidad moderada (natación, senderismo, deportes recreativos).",
                "Registrar la sesión y compartir el logro (si la app tiene función social).",
            ],
        },
        "BUENO": {
            "tecnica": "Expansión del repertorio recreativo — Arquetipo L3/L4",
            "objetivo": "Enriquecer el estilo de vida activo con variedad de actividades recreativas desafiantes.",
            "instrucciones": [
                "Mantener 2 sesiones recreativas semanales.",
                "Explorar actividades de mayor exigencia: ciclismo de montaña, natación en aguas abiertas, escalada, deportes colectivos.",
                "Documentar nuevas experiencias en la app como parte del historial de actividades.",
            ],
        },
    },
    # ── Pregunta 29 ─────────────────────────────────────────────────────────
    29: {
        "POBRE": {
            "tecnica": "Rutina de Movilidad y Estiramientos Básicos — Arquetipo L1/L2",
            "objetivo": "Introducir el hábito de estiramiento con una rutina corta, segura y efectiva que cubra los grandes grupos musculares.",
            "instrucciones": [
                "Realizar la rutina al finalizar cualquier actividad física o de forma independiente (mañana o noche).",
                "Espalda baja: postura del niño 30 seg × 2. Rotación de tronco acostado 20 seg cada lado × 2.",
                "Pectorales: estiramiento de pecho en esquina o con brazos abiertos 30 seg × 2.",
                "Cadera y glúteos: piriforme (figura 4 acostado) 30 seg × 2 por lado. Flexor de cadera en estocada baja 30 seg × 2 por lado.",
                "Isquiotibiales: estiramiento sentado o de pie con apoyo 30 seg × 2 por pierna.",
                "Mantener cada posición sin dolor. No forzar el rango de movimiento. Respirar profundo durante el estiramiento.",
            ],
        },
        "MODERADO": {
            "tecnica": "Rutina de Flexibilidad Progresiva — Arquetipo L2/L3",
            "objetivo": "Estructurar sesiones de estiramiento regulares con mayor variedad y profundidad para mejorar la movilidad funcional.",
            "instrucciones": [
                "Combinar estiramientos estáticos (al final de sesiones de fuerza/cardio) y estiramientos dinámicos (como calentamiento).",
                "Estiramientos estáticos: mantener 20–30 seg, 2–3 repeticiones por grupo muscular.",
                "Estiramientos dinámicos: círculos de cadera, balanceos de pierna, rotaciones de tronco — 10–15 repeticiones controladas.",
                "Incluir los 5 grupos principales: espalda, pectorales, cadera, cuádriceps/isquiotibiales, hombros.",
                "Registrar en la app los días de estiramiento completados.",
            ],
        },
        "BUENO": {
            "tecnica": "Movilidad avanzada y yoga/pilates — Arquetipo L3/L4",
            "objetivo": "Mantener y profundizar la flexibilidad funcional incorporando prácticas de movilidad más completas.",
            "instrucciones": [
                "Mantener 3 sesiones semanales de flexibilidad como parte del plan de entrenamiento.",
                "Una sesión dedicada a yoga o pilates (20–30 min) para trabajar movilidad, respiración y estabilidad simultáneamente.",
                "Las otras dos sesiones: estiramientos post-entrenamiento específicos según los grupos trabajados en esa sesión.",
            ],
        },
    },
    # ── Pregunta 35 ─────────────────────────────────────────────────────────
    35: {
        "POBRE": {
            "tecnica": "Estrategia NEAT — Actividad Física No Estructurada del Día",
            "objetivo": "Aumentar el gasto energético cotidiano del usuario sedentario mediante pequeños cambios de comportamiento que no requieren tiempo extra dedicado al ejercicio.",
            "instrucciones": [
                "Presentar al usuario una lista de 8–10 comportamientos NEAT en la app (usar escaleras, parquear lejos, caminar al almuerzo, reuniones de pie, etc.).",
                "Pedir al usuario que elija 2–3 comportamientos que pueda implementar esta semana en su rutina real.",
                "Registrar diariamente cuáles cumplió. La app muestra un contador semanal de comportamientos activos completados.",
                "Cada semana, añadir 1 comportamiento nuevo a la lista personal.",
                "Celebrar cuando el usuario completa más del 80% de sus comportamientos NEAT semanales.",
            ],
        },
        "MODERADO": {
            "tecnica": "NEAT + Metas de Pasos Diarios",
            "objetivo": "Consolidar los comportamientos NEAT con una meta cuantificable de pasos diarios como indicador de actividad cotidiana.",
            "instrucciones": [
                "Establecer una meta inicial de pasos diarios según el nivel actual: si el usuario promedia 3.000 pasos, la meta es 5.000; si ya hace 5.000, la meta es 7.500.",
                "Usar el teléfono o smartwatch para registrar los pasos diarios.",
                "La app muestra el progreso diario de pasos y alerta si el usuario va por debajo de la meta a mitad del día.",
                "Cada 2 semanas, revisar el promedio y aumentar la meta en 500–1.000 pasos.",
                "Meta a 3 meses: alcanzar 8.000–10.000 pasos diarios de forma consistente.",
            ],
        },
        "BUENO": {
            "tecnica": "NEAT optimizado + Actividad física activa en desplazamientos",
            "objetivo": "Maximizar la actividad física integrada en el estilo de vida usando el desplazamiento activo como medio de ejercicio.",
            "instrucciones": [
                "Sustituir desplazamientos cortos (< 3 km) en vehículo por caminata o bicicleta cuando sea posible.",
                "Mantener el hábito de escaleras, pausas activas y caminata al almuerzo.",
                "Registrar la actividad de desplazamiento como parte del plan de la app.",
            ],
        },
    },
    # ── Pregunta 42 ─────────────────────────────────────────────────────────
    42: {
        "POBRE": {
            "tecnica": "Introducción a la Escala de Esfuerzo Percibido (RPE) y medición manual de FC",
            "objetivo": "Enseñar al usuario a monitorear su intensidad de ejercicio de forma sencilla, sin necesidad de dispositivos especiales, para ejercitarse de manera segura.",
            "instrucciones": [
                "Explicar en la app la Escala de Borg simplificada (0–10): 0 = reposo, 5 = moderado (puedes hablar con dificultad), 7–8 = vigoroso, 10 = máximo esfuerzo.",
                "Durante las primeras sesiones, pedir al usuario que evalúe su esfuerzo percibido al terminar cada bloque de ejercicio.",
                "Enseñar medición manual de FC: colocar dedos en la muñeca (arteria radial) o cuello (carótida), contar los latidos durante 15 segundos y multiplicar por 4.",
                "Mostrar en la app la fórmula de FCmax = 220 − edad y la zona objetivo (60–75% para esfuerzo moderado).",
                "Practicar la medición al finalizar un bloque de ejercicio y registrar el valor en la app.",
            ],
        },
        "MODERADO": {
            "tecnica": "Entrenamiento por Zonas de Frecuencia Cardíaca",
            "objetivo": "Usar la FC como herramienta activa para controlar la intensidad del ejercicio y mejorar la eficiencia cardiovascular.",
            "instrucciones": [
                "Calcular FCmax = 220 − edad del usuario.",
                "Definir las zonas de trabajo: Zona 1 (50–60%): recuperación activa. Zona 2 (60–70%): base aeróbica. Zona 3 (70–80%): mejora cardiovascular. Zona 4 (80–90%): umbral anaeróbico.",
                "Asignar una zona objetivo a cada tipo de sesión: sesiones fáciles → Zona 2, sesiones moderadas → Zona 3, sesiones duras → Zona 4.",
                "El usuario mide o registra su FC durante la sesión y verifica si está en la zona correcta.",
                "Si la FC supera la zona objetivo, reducir intensidad. Si está muy por debajo, aumentarla.",
            ],
        },
        "BUENO": {
            "tecnica": "Monitoreo avanzado de FC y variabilidad cardíaca (HRV)",
            "objetivo": "Optimizar el entrenamiento usando FC y HRV para ajustar cargas de forma inteligente.",
            "instrucciones": [
                "Usar smartwatch o pulsómetro para monitoreo continuo de FC durante las sesiones.",
                "Revisar la HRV (variabilidad de la frecuencia cardíaca) matutina como indicador de recuperación. Si la HRV está baja, el día corresponde a una sesión suave.",
                "Ajustar el plan semanal según los datos de FC y HRV.",
            ],
        },
    },
    # ── Pregunta 47 ─────────────────────────────────────────────────────────
    47: {
        "POBRE": {
            "tecnica": "Alcanzar la Zona Aeróbica Base — Protocolo Progresivo",
            "objetivo": "Guiar al usuario para que, por primera vez, alcance y mantenga su pulso cardíaco objetivo durante el ejercicio aeróbico de forma segura.",
            "instrucciones": [
                "Calcular el pulso objetivo del usuario: FCmax = 220 − edad. Zona base: 60–70% FCmax.",
                "Ejemplo: usuario de 35 años → FCmax = 185. Zona base = 111–130 lpm.",
                "Iniciar con caminata rápida. Aumentar el ritmo gradualmente hasta sentir que la respiración es más exigente (RPE 5–6).",
                "Medir la FC en ese punto (manual o con dispositivo). Si está en la zona objetivo, mantener ese ritmo 10–15 minutos.",
                "Si no llega a la zona, aumentar levemente la velocidad o incluir un tramo con pendiente.",
                "Al finalizar, registrar el tiempo que mantuvo el pulso en zona objetivo. Aumentar ese tiempo cada semana.",
            ],
        },
        "MODERADO": {
            "tecnica": "Entrenamiento Aeróbico en Zona 3 — FC Objetivo Consistente",
            "objetivo": "Alcanzar el pulso cardíaco objetivo de forma consistente en sesiones aeróbicas de modalidades variadas.",
            "instrucciones": [
                "Seleccionar la modalidad aeróbica preferida: caminata rápida, troteo, bicicleta, natación o remo.",
                "Calentar 5 min a baja intensidad. Luego aumentar progresivamente hasta alcanzar el 70–80% FCmax.",
                "Mantener esa zona durante 20–25 minutos. Si la FC sube demasiado, reducir el ritmo.",
                "Enfriar 5 min con actividad suave.",
                "Registrar en la app: duración total en zona objetivo vs. duración total de la sesión. Meta: 80% del tiempo en zona.",
            ],
        },
        "BUENO": {
            "tecnica": "Entrenamiento Polarizado — Zonas 2 y 4",
            "objetivo": "Optimizar la capacidad aeróbica combinando sesiones de base aeróbica (baja intensidad) con sesiones de umbral (alta intensidad).",
            "instrucciones": [
                "Distribuir el volumen semanal: 80% de las sesiones en Zona 2 (60–70% FCmax) y 20% en Zona 4 (80–90% FCmax).",
                "Sesiones Zona 2: largas, cómodas, conversacionales. Duración 40–60 min.",
                "Sesiones Zona 4: intervalos de 3–5 min a alta intensidad con recuperación completa. Duración 30–35 min totales.",
                "Monitorear FC en todas las sesiones para verificar las zonas.",
            ],
        },
    },
}

# Agrega tipo_actividad/config_actividad a las 27 fichas sin repetirlo a mano.
for _num_q, _por_nivel in RECOMENDACIONES.items():
    for _ficha in _por_nivel.values():
        _ficha["tipo_actividad"] = "registro_numerico"
        _ficha["config_actividad"] = {"unidad": _UNIDAD_POR_PREGUNTA[_num_q]}

PRIORIDAD_NIVEL = {"POBRE": 0, "MODERADO": 1, "BUENO": 2, "EXCELENTE": 3}


def obtener_recomendaciones_af(encuesta: EncuestaHplp) -> list[dict]:
    """
    Devuelve las tarjetas de recomendación de Actividad Física para la encuesta dada.
    No incluye tarjetas para preguntas con nivel EXCELENTE.
    Orden: POBRE → MODERADO → BUENO.
    """
    tarjetas = []
    for num_q, campo in ITEM_FIELDS.items():
        valor = getattr(encuesta, campo)
        nivel = puntaje_a_nivel(valor)
        if nivel == "EXCELENTE":
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
