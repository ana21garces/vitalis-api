from app.models.encuesta_hplp import EncuestaHplp

# Mapeo: puntaje de ítem (1-4) → nivel
def puntaje_a_nivel(valor: int) -> str:
    return {1: "POBRE", 2: "MODERADO", 3: "BUENO", 4: "EXCELENTE"}[valor]


# Preguntas del indicador
PREGUNTAS = {
    6:  "Cambiar tus comportamientos habituales de una forma positiva.",
    12: "Aceptar que tu vida tiene un propósito.",
    19: "Mirar hacia el futuro de forma positiva.",
    25: "Sentir satisfacción hacia tu persona.",
    31: "Establecer metas a largo plazo para tu vida.",
    37: "Hacer que tu día sea interesante y retador (estimulante).",
    44: "Enfocarte en lo que es importante para ti en la vida.",
    49: "Sentirte unido a Dios.",
    52: "Exponerte a nuevas experiencias y retos constructivos.",
}

# Campo del modelo EncuestaHplp para cada pregunta PP
ITEM_FIELDS = {
    6:  "pp_item_06",
    12: "pp_item_12",
    19: "pp_item_19",
    25: "pp_item_25",
    31: "pp_item_31",
    37: "pp_item_37",
    44: "pp_item_44",
    49: "pp_item_49",
    52: "pp_item_52",
}

# Tabla de recomendaciones elaboradas por el profesional — una por pregunta × nivel
RECOMENDACIONES: dict[int, dict[str, dict]] = {
    6: {
        "POBRE": {
            "tecnica": "Matriz de Eisenhower + Cuadro de Hábitos",
            "objetivo": "Ayudar al usuario a identificar qué comportamientos está priorizando mal y establecer un hábito positivo concreto con seguimiento diario.",
            "instrucciones": [
                "Cada mañana clasifica tus tareas del día en los 4 cuadrantes: Urgente+Importante (hazlo ya), Importante+No urgente (planifícalo), Urgente+No importante (delégalo), Ni urgente ni importante (elimínalo).",
                "Elige UN comportamiento positivo que quieras adoptar esta semana (ej: leer 15 minutos, tomar agua al despertar).",
                "Crea una tabla semanal sencilla y marca con X cada día que cumples ese comportamiento. No rompas la cadena.",
                "Al final de la semana reflexiona: ¿qué hábitos te suman? ¿cuáles te restan? ¿qué creencias limitantes aparecieron?",
            ],
        },
        "MODERADO": {
            "tecnica": "Cuadro de Hábitos con Identidad",
            "objetivo": "Consolidar el cambio de comportamiento conectándolo con la identidad que el usuario quiere construir.",
            "instrucciones": [
                "Escribe cómo te gustaría que las personas te describieran en un año (valores, carácter, metas).",
                "Lista tus hábitos actuales y clasifícalos en 'me suman' o 'me restan' respecto a esa identidad.",
                "Elige 2 hábitos que quieras reforzar y 1 que quieras eliminar. Lleva registro semanal con el cuadro de hábitos.",
                "Revisa el avance cada domingo: ¿estoy actuando como la persona que quiero ser?",
            ],
        },
        "BUENO": {
            "tecnica": "Reflexión de Mantenimiento",
            "objetivo": "Mantener y profundizar los buenos hábitos ya establecidos.",
            "instrucciones": [
                "Continúa con tu cuadro de hábitos actual y añade un reto nuevo cada mes.",
                "Comparte tus avances con alguien de confianza para reforzar el compromiso.",
            ],
        },
    },
    12: {
        "POBRE": {
            "tecnica": "Diario de Gratitud + Propósito",
            "objetivo": "Despertar el sentido de propósito en el usuario mediante el reconocimiento diario de momentos significativos.",
            "instrucciones": [
                "Antes de dormir, escribe en un cuaderno 3 cosas específicas por las que estás agradecido hoy (evita respuestas genéricas; sé concreto: 'mi hija me abrazó esta mañana').",
                "Debajo de cada una escribe: ¿cómo conecta esto con lo que creo que es mi propósito o misión de vida?",
                "Si no tienes claro tu propósito, escribe una frase provisional: 'Creo que estoy aquí para...' y ajústala con el tiempo.",
                "Hazlo durante 21 días consecutivos y revisa si tu percepción de sentido ha cambiado.",
            ],
        },
        "MODERADO": {
            "tecnica": "Diario de Gratitud con Vinculación de Propósito",
            "objetivo": "Fortalecer la conexión entre experiencias cotidianas y el sentido de vida ya parcialmente reconocido.",
            "instrucciones": [
                "Escribe 3 gratitudes específicas cada noche.",
                "Para cada una, responde: ¿qué dice esto sobre quién soy o hacia dónde voy?",
                "Una vez a la semana relee entradas anteriores e identifica patrones: ¿qué te da más sentido consistentemente?",
            ],
        },
        "BUENO": {
            "tecnica": "Gratitud Express",
            "objetivo": "Mantener el hábito de gratitud como ancla de propósito.",
            "instrucciones": [
                "Continúa el diario de gratitud con al menos 3 entradas semanales.",
                "Cada mes escribe una reflexión sobre cómo tu propósito ha evolucionado.",
            ],
        },
    },
    19: {
        "POBRE": {
            "tecnica": "Cuadro de Hábitos para el Optimismo — Nivel Básico",
            "objetivo": "Entrenar al cerebro del usuario a buscar activamente aspectos positivos del futuro, contrarrestando el sesgo negativo.",
            "instrucciones": [
                "Al despertar, escribe UNA afirmación sobre algo bueno que esperas que ocurra hoy (no tiene que ser grande: 'Hoy voy a disfrutar mi café de la mañana').",
                "Al terminar el día, revisa: ¿ocurrió algo positivo? ¿tu enfoque optimista cambió cómo viviste el día?",
                "En tu cuadro de hábitos, añade la columna 'Pensamiento Positivo del Día' y marca si lo cumpliste.",
                "Si el pensamiento negativo domina, escríbelo y al lado escribe una perspectiva alternativa posible.",
            ],
        },
        "MODERADO": {
            "tecnica": "Cuadro de Hábitos para el Optimismo — Nivel Intermedio",
            "objetivo": "Expandir la visión positiva hacia metas de mediano y largo plazo.",
            "instrucciones": [
                "Escribe cada mañana 1 cosa positiva que esperas para hoy y 1 meta positiva para esta semana.",
                "Al final de la semana evalúa: ¿qué salió bien? ¿qué aprendiste de lo que no salió como esperabas?",
                "Lleva registro en el cuadro de hábitos y celebra las rachas de pensamiento positivo.",
            ],
        },
        "BUENO": {
            "tecnica": "Visión a Futuro",
            "objetivo": "Proyectar el optimismo hacia metas de vida concretas.",
            "instrucciones": [
                "Escribe una carta a ti mismo desde el futuro (1 año) describiendo cómo es tu vida.",
                "Léela cada mes y ajusta tu perspectiva actual.",
            ],
        },
    },
    25: {
        "POBRE": {
            "tecnica": "Reconocimiento frente al Espejo",
            "objetivo": "Activar la autocompasión y el reconocimiento del valor propio mediante un ejercicio corporal y verbal diario.",
            "instrucciones": [
                "Busca un espejo en un lugar tranquilo y reserva 5 minutos sin interrupciones.",
                "Mírate a los ojos y reconoce en voz alta algo que valoras de ti mismo hoy (puede ser una actitud, un esfuerzo, una decisión).",
                "Toca suavemente tus hombros como gesto de autocuidado. Da gracias por algo que tu cuerpo te permite hacer.",
                "Si surge autocrítica, nómbrala sin juzgarla: 'Noto que me cuesta aceptar esto' y continúa de todas formas.",
                "Practica diariamente por 2 semanas y registra cómo te sientes antes y después.",
            ],
        },
        "MODERADO": {
            "tecnica": "Carta de Autoaceptación",
            "objetivo": "Profundizar en el reconocimiento propio mediante la escritura reflexiva.",
            "instrucciones": [
                "Escribe una carta de una página dirigida a ti mismo reconociendo tus fortalezas, tus esfuerzos y lo que has superado.",
                "Incluye al menos 3 cualidades que otros valoran de ti y 1 logro reciente del que te sientas orgulloso.",
                "Léela en voz alta frente al espejo 1 vez por semana.",
            ],
        },
        "BUENO": {
            "tecnica": "Afirmaciones de Mantenimiento",
            "objetivo": "Sostener la autosatisfacción con un ritual breve diario.",
            "instrucciones": [
                "Elige 3 afirmaciones sobre ti mismo y repítelas cada mañana.",
                "Actualiza las afirmaciones mensualmente según tu crecimiento.",
            ],
        },
    },
    31: {
        "POBRE": {
            "tecnica": "Metas SMART desde los Sueños",
            "objetivo": "Ayudar al usuario a transformar deseos vagos en objetivos concretos y alcanzables en distintas áreas de su vida.",
            "instrucciones": [
                "Escribe UN sueño (deseo general) para cada área: Académica, Personal, Laboral, Espiritual, Social/emocional.",
                "Para cada sueño, define 2 metas SMART: una a corto plazo (1–3 meses) y una a mediano plazo (6–12 meses). Cada meta debe ser Específica, Medible, Alcanzable, Relevante y con Tiempo definido.",
                "Ejemplo: Sueño 'quiero ser más espiritual' → Meta SMART: 'Voy a leer 20 minutos cada mañana durante los próximos 3 meses'.",
                "Pega tus metas en un lugar visible y revísalas cada semana.",
            ],
        },
        "MODERADO": {
            "tecnica": "Metas SMART a Largo Plazo",
            "objetivo": "Ampliar el horizonte de planificación hacia metas de largo plazo (1–3 años) en todas las áreas de vida.",
            "instrucciones": [
                "Revisa las metas a corto y mediano plazo que ya tienes (o defínelas si no las tienes).",
                "Añade UNA meta a largo plazo (1–3 años) por área de vida, siguiendo el formato SMART.",
                "Crea un tablero o mapa visual con tus sueños y metas. Actualízalo trimestralmente.",
            ],
        },
        "BUENO": {
            "tecnica": "Revisión Trimestral de Metas",
            "objetivo": "Mantener el enfoque en metas de largo plazo mediante revisiones periódicas.",
            "instrucciones": [
                "Revisa tus metas cada 3 meses: ¿qué avanzaste? ¿qué ajustas? ¿qué celebras?",
                "Añade nuevas metas según el crecimiento personal que estás experimentando.",
            ],
        },
    },
    37: {
        "POBRE": {
            "tecnica": "Rutina de Meditación, Lectura y Oración con los Sentidos",
            "objetivo": "Dotar al usuario de una rutina matutina estructurada que transforme sus días en experiencias significativas y estimulantes.",
            "instrucciones": [
                "Meditación Terapéutica (10 min): En un lugar tranquilo, respira profundo y suelta el aire lentamente como si fueras a silbar. Repite durante 10 minutos.",
                "Lectura y Expresión (10–15 min): Lee un pasaje de un libro significativo para ti. Luego dibuja la escena, escribe las ideas principales o usa recortes que reflejen lo que entendiste aplicado a tu vida hoy.",
                "Oración/Reflexión con los Sentidos (5–10 min): Percibe el entorno: el silencio, la luz, el aroma del aire. Escribe y da gracias por lo que has visto, oído y sentido.",
                "Hazlo cada mañana por 21 días y anota cómo cambia tu energía y actitud durante el día.",
            ],
        },
        "MODERADO": {
            "tecnica": "Desafío Diario Pequeño",
            "objetivo": "Introducir micro-retos cotidianos que generen sensación de logro y estimulación.",
            "instrucciones": [
                "Cada mañana elige UN micro-reto para el día (aprender algo nuevo, hacer algo diferente, conectar con alguien).",
                "Al final del día evalúa: ¿cómo me hizo sentir? ¿qué aprendí?",
                "Mantén el registro en tu cuadro de hábitos.",
            ],
        },
        "BUENO": {
            "tecnica": "Reto Semanal de Crecimiento",
            "objetivo": "Sostener la estimulación con retos de mayor alcance.",
            "instrucciones": [
                "Elige un reto semanal que esté fuera de tu zona de confort.",
                "Documenta qué aprendiste de ti mismo al completarlo.",
            ],
        },
    },
    44: {
        "POBRE": {
            "tecnica": "Servicio Activo + Clarificación de Valores",
            "objetivo": "Ayudar al usuario a identificar lo que realmente importa en su vida a través de la acción concreta hacia otros.",
            "instrucciones": [
                "Haz una lista de personas a quienes te gustaría ayudar. Para cada una escribe: ¿cómo las ayudarías? ¿qué necesitas para hacerlo?",
                "Elige UNA persona y UNA acción concreta esta semana. Hazlo sin esperar nada a cambio.",
                "Después de hacerlo, reflexiona: ¿qué sentí? ¿esto refleja lo que es importante para mí?",
                "Repite semanalmente y observa cómo van apareciendo tus valores más claros.",
            ],
        },
        "MODERADO": {
            "tecnica": "Mapa de Valores",
            "objetivo": "Hacer explícitos los valores del usuario y alinear sus acciones diarias con ellos.",
            "instrucciones": [
                "Escribe tus 5 valores más importantes (ej: familia, honestidad, crecimiento, fe, salud).",
                "Revisa tu semana pasada: ¿actuaste coherente con esos valores? ¿dónde no?",
                "Define 1 acción concreta esta semana que refleje cada uno de tus valores principales.",
            ],
        },
        "BUENO": {
            "tecnica": "Auditoría de Valores",
            "objetivo": "Verificar periódicamente la alineación entre valores, metas y acciones.",
            "instrucciones": [
                "Una vez al mes, revisa si tus actividades y decisiones recientes reflejan lo que declaras que es importante para ti.",
                "Ajusta donde haya desalineación.",
            ],
        },
    },
    49: {
        "POBRE": {
            "tecnica": "Rutina de Conexión Espiritual con los Sentidos",
            "objetivo": "Facilitar una experiencia de conexión espiritual concreta y accesible, comenzando con la percepción sensorial del entorno.",
            "instrucciones": [
                "Meditación de apertura (10 min): Siéntate en silencio, respira profundo. Percibe deliberadamente lo que puedes ver, oír, oler y sentir. Reconoce cada sensación como parte de la creación.",
                "Lectura y Dibujo (10–15 min): Lee un pasaje bíblico o de un libro espiritual. Dibuja la escena o escribe las ideas más importantes aplicadas a tu situación actual.",
                "Oración con los sentidos (5–10 min): Ora percibiendo el entorno. Da gracias por aquello que puedes ver, tocar y oír. Si quieres, escríbelo como una carta a Dios.",
                "Practica esta rutina 5 días a la semana y lleva un registro simple de cómo te sentiste después.",
            ],
        },
        "MODERADO": {
            "tecnica": "Diario Espiritual",
            "objetivo": "Profundizar la conexión espiritual mediante la reflexión escrita y la oración intencional.",
            "instrucciones": [
                "Cada día escribe: ¿dónde sentí la presencia de Dios hoy? Puede ser en algo pequeño.",
                "Añade una petición y una acción de gracias específica.",
                "Una vez a la semana relee tus anotaciones y reflexiona sobre cómo ha evolucionado tu conexión.",
            ],
        },
        "BUENO": {
            "tecnica": "Profundización Espiritual",
            "objetivo": "Llevar la conexión espiritual a nuevos niveles de profundidad.",
            "instrucciones": [
                "Incorpora un estudio bíblico o espiritual más profundo (libro, comunidad, retiro).",
                "Comparte tu fe o práctica espiritual con alguien cercano.",
            ],
        },
    },
    52: {
        "POBRE": {
            "tecnica": "Retos Constructivos Graduales",
            "objetivo": "Guiar al usuario a salir progresivamente de su zona de confort con retos pequeños y seguros que generen autoconfianza.",
            "instrucciones": [
                "Haz una lista de 5 actividades que siempre te han generado curiosidad pero también temor o incomodidad.",
                "Ordénalas de menor a mayor dificultad percibida.",
                "Comprométete a hacer la más pequeña esta semana: puede ser algo muy sencillo (probar una comida nueva, hablar con un desconocido, tomar una ruta diferente).",
                "Después de hacerla, responde: ¿qué aprendí de mí mismo? ¿fue tan difícil como pensaba?",
                "Avanza al siguiente reto la semana siguiente. Documenta el proceso.",
            ],
        },
        "MODERADO": {
            "tecnica": "Reto Mensual de Zona de Confort",
            "objetivo": "Establecer un hábito mensual de exponerse a experiencias nuevas de mayor envergadura.",
            "instrucciones": [
                "Cada mes comprométete con UNA actividad nueva que siempre te haya causado curiosidad: un curso, deporte, viaje corto, actividad artística, voluntariado.",
                "Al completarla, evalúa: ¿qué aprendí de mí mismo? ¿cómo cambió mi perspectiva?",
                "Lleva un diario de retos completados para evidenciar tu crecimiento.",
            ],
        },
        "BUENO": {
            "tecnica": "Proyecto de Crecimiento Personal",
            "objetivo": "Dirigir la apertura a experiencias hacia un proyecto de vida más ambicioso.",
            "instrucciones": [
                "Define UN proyecto de crecimiento personal para los próximos 6 meses (aprender un idioma, emprender, viajar, estudiar algo nuevo).",
                "Establece metas SMART para ese proyecto y haz seguimiento mensual.",
            ],
        },
    },
}

PRIORIDAD_NIVEL = {"POBRE": 0, "MODERADO": 1, "BUENO": 2, "EXCELENTE": 3}


def obtener_recomendaciones_pp(encuesta: EncuestaHplp) -> list[dict]:
    """
    Para cada ítem PP de la encuesta, determina el nivel y retorna
    la tarjeta de recomendación correspondiente del documento profesional.
    Las tarjetas se ordenan por prioridad: POBRE primero, luego MODERADO, luego BUENO.
    EXCELENTE no genera tarjeta.
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
        })
    tarjetas.sort(key=lambda t: PRIORIDAD_NIVEL[t["nivel"]])
    return tarjetas
