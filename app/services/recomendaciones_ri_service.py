"""
Servicio de recomendaciones de Relaciones Interpersonales.
Tabla estática de fichas por pregunta y nivel (POBRE y MODERADO). BUENO y
EXCELENTE no reciben recomendación.

Contenido tomado de "Compendio de Guías de Recomendaciones por Área de
Bienestar", Parte VI — Relaciones Interpersonales (autora: Hellen Buendía,
Profesional en Psicología), verificado contra "Guía requerimientos
Relaciones Interpersonales.docx". A diferencia de Manejo del Estrés, aquí
el documento sí diferencia técnica y objetivo por nivel en la mayoría de
las preguntas; cuando el documento marca "Ambos" (7, 20, 26, 45, 50) se usa
la misma ficha para POBRE y MODERADO.

Los campos "Recursos necesarios" y "Notas adicionales" del documento se
incorporan como pasos finales de las instrucciones (el esquema de tarjeta
no tiene campos propios para ellos), solo cuando el documento trae
contenido real y no "No aplica". Los anexos gráficos que el documento
referencia (D.1 "semáforo relacional", D.2 "árbol/red de apoyo") son
plantillas físicas para imprimir y no están implementados como imagen en
la app; las instrucciones los mencionan por nombre tal como el documento.

La Pregunta 50 ("Comprometerte a encontrar puntos en común...") NO genera
tarjeta: el campo "Objetivo" de su ficha está vacío en el documento fuente
(tanto en la guía original como en el compendio) y Ana pidió no inventar
contenido clínico. Pendiente de que el objetivo real llegue de la autora.
"""
from app.models.encuesta_hplp import EncuestaHplp


def puntaje_a_nivel(valor: int) -> str:
    return {1: "POBRE", 2: "MODERADO", 3: "BUENO", 4: "EXCELENTE"}[valor]


PREGUNTAS = {
    1:  "Dialogar tus problemas o preocupaciones con personas muy allegadas a ti.",
    7:  "Elogiar a otras personas por sus éxitos.",
    13: "Mantener relaciones sociales positivas.",
    20: "Dedicar tiempo para estar con tus amistades más cercanas.",
    26: "Expresar amor o cariño a otros.",
    32: "Utilizar el toque físico con las personas importantes para ti.",
    38: "Buscar maneras respetuosas de llenar tus necesidades afectivas.",
    45: "Buscar apoyo en las personas que se preocupan por ti.",
    50: "Comprometerte a encontrar puntos en común, por medio del diálogo, con otras personas.",
}

ITEM_FIELDS = {
    1:  "ri_item_01",
    7:  "ri_item_07",
    13: "ri_item_13",
    20: "ri_item_20",
    26: "ri_item_26",
    32: "ri_item_32",
    38: "ri_item_38",
    45: "ri_item_45",
    50: "ri_item_50",
}

RECOMENDACIONES: dict[int, dict[str, dict]] = {
    1: {
        "POBRE": {
            "tecnica": "Hablemos de la Vulnerabilidad",
            "objetivo": "Reconocer mi vulnerabilidad y expresar emociones.",
            "instrucciones": [
                "Lee el libro «El poder de la vulnerabilidad».",
                "En un cuaderno o agenda escribe cuáles son tus vulnerabilidades, esas que te hacen pensar que no puedes confiar en las personas. Ejemplo: «siento que me van a juzgar».",
                "Dale un valor de 1 a 5 según cuánto afecta cada vulnerabilidad a tu vida personal.",
                "Después, en el cuaderno, escribe una carta o texto sobre qué te gustaría que tu círculo más cercano conozca de ti, aun cuando te sientas inseguro.",
                "Escoge a una persona de tu círculo más cercano y léele algo de lo que escribiste.",
                "Identifica cómo te sentiste al hablar con alguien y por qué es importante hablar con las personas a nuestro alrededor.",
                "Recursos necesarios: cuaderno o agenda; dedica 15 minutos diarios.",
            ],
        },
        "MODERADO": {
            "tecnica": "Diario de Conversaciones",
            "objetivo": "Crear el hábito de reconocer y expresar emociones.",
            "instrucciones": [
                "Escribe en un diario (cuaderno o agenda) lo que te preocupa o sientes.",
                "Practica cómo lo dirías en voz alta.",
                "Elige un momento tranquilo para compartirlo con una persona cercana.",
                "Recursos necesarios: cuaderno o agenda.",
            ],
        },
    },
    7: {
        "tecnica": "El Reto del Elogio Diario",
        "objetivo": "Crear el hábito de reconocer y expresar admiración.",
        "instrucciones": [
            "Escribe en unos post-it elogios (un logro, una habilidad o una característica positiva) que te gustaría decir, o que te gustaría escuchar.",
            "Cada día, elige un post-it y una persona a la cual le quieras dedicar ese elogio.",
            "Inicia con frases o elogios pequeños, por ejemplo: «Eres una persona importante». Ve cambiando las frases haciéndolas más personales, pero siempre en positivo.",
            "Recursos necesarios: tarjetas post-it.",
        ],
    },
    13: {
        "POBRE": {
            "tecnica": "Semáforo relacional",
            "objetivo": "Identificar relaciones saludables y dañinas.",
            "instrucciones": [
                "En la hoja del semáforo (Anexo D.1) describe, en el color verde, a las personas que generan tranquilidad y respeto, y qué buscas en las personas a tu alrededor.",
                "En el color amarillo, describe qué personas o relaciones te pueden afectar, aquellas que se sienten inestables o agotadoras.",
                "En el color rojo, describe y califica qué relaciones o personas pueden generar daño emocional, hacerte sentir rechazo, abandono o no sentirte suficiente.",
                "Después del análisis anterior, identifica si en tu círculo más cercano tienes personas o relaciones sanas que te ayuden.",
                "Recursos necesarios: hoja con la forma de un semáforo, en blanco y negro, para colorear y escribir dentro (Anexo D.1).",
            ],
        },
        "MODERADO": {
            "tecnica": "Agenda de Relaciones Positivas",
            "objetivo": "Facilitar la organización y el seguimiento de interacciones saludables.",
            "instrucciones": [
                "En una hoja, escribe cuáles relaciones interpersonales (amistades) han sido significativas para ti.",
                "Anota cómo te hicieron sentir, qué emociones experimentaste y cuál es el recuerdo más bonito o positivo.",
                "Planifica una acción sencilla para mantener o mejorar esas relaciones. Ejemplo: enviar un mensaje, proponer un encuentro.",
                "Recursos necesarios: hojas (en blanco o de colores).",
            ],
        },
    },
    20: {
        "tecnica": "El Banco de Afecto",
        "objetivo": "Practicar y fortalecer la expresión de afecto de forma cómoda.",
        "instrucciones": [
            "Identifica diferentes formas de mostrar cariño (palabras amables, gestos, actos de servicio).",
            "En una lista personal decide qué actividad te gusta realizar y compartir con personas de tu círculo más cercano.",
            "Escoge un día a la semana, o cada día, y realiza una acción de esa lista con personas importantes para ti.",
        ],
    },
    26: {
        "tecnica": "El Banco de Afecto",
        "objetivo": "Practicar y fortalecer la expresión de afecto de forma cómoda.",
        "instrucciones": [
            "Elige una forma cómoda de expresión: palabras (cualidades, afectos positivos, elogios), actos (servicio en algo que las personas necesiten) o detalles (pequeños regalos, como un post-it).",
            "Cuando elijas la forma de expresión, intenta expresar palabras de afecto, cariño o cercanía en tu círculo más cercano, de manera gradual.",
            "Registra en tu diario emocional las emociones que sentiste al expresar una muestra de cariño.",
        ],
    },
    32: {
        "POBRE": {
            "tecnica": "Contacto Seguro",
            "objetivo": "Incrementar gradualmente el uso de contacto físico respetuoso y recíproco.",
            "instrucciones": [
                "Observa e identifica, en tu círculo más cercano, a la persona o amistad con la que sientes un grado de seguridad o que pueda brindarte apoyo emocional.",
                "Conversa con esa persona en relación con el contacto físico, iniciando con contacto breve: palmada de mano o de hombro, tomar del brazo en forma de abrazo, abrazo corto.",
                "Amplía poco a poco la cercanía y el contacto con otras personas a tu alrededor.",
                "Identifica tus límites, para expresarlos a las personas a tu alrededor y también para comprender los límites de los demás.",
            ],
        },
        "MODERADO": {
            "tecnica": "Contacto Seguro",
            "objetivo": "El contacto físico seguro reduce el cortisol y aumenta la sensación de conexión.",
            "instrucciones": [
                "Observa y aprende el nivel de comodidad de la otra persona.",
                "Prueba con gestos simples, como un apretón de mano, un choque de palma o un abrazo breve.",
            ],
        },
    },
    38: {
        "POBRE": {
            "tecnica": "Necesidades Sin Culpa",
            "objetivo": "Identificar qué necesitas afectivamente y cómo puedes cubrirlo adecuadamente.",
            "instrucciones": [
                "Identifica qué apoyo emocional necesitas: compañía en momentos difíciles o cuando te sientes triste; escucha, donde puedas sentir comprensión de tu problemática, sin juzgamientos ni reproches; apoyo en momentos difíciles o en la toma de decisiones.",
                "Expresa estas necesidades a personas que puedan apoyarte: dentro de tu círculo más cercano, aquellas con las que sientas seguridad al expresar tus luchas y necesidades. Ejemplo: «Hoy necesito hablar con alguien».",
                "Importante: procura que, al solicitar apoyo, puedas sentir seguridad para explorar tu vulnerabilidad, y evalúa si puedes generar dependencia emocional.",
            ],
        },
        "MODERADO": {
            "tecnica": "Mapa de Necesidades y Recursos",
            "objetivo": "Reconocer y expresar necesidades afectivas de manera respetuosa.",
            "instrucciones": [
                "Haz una lista de tus necesidades afectivas (por ejemplo, sentirte escuchado o valorado).",
                "Al lado de cada necesidad anota personas o actividades que puedan ayudarte a cubrirla de manera respetuosa y saludable.",
                "Empieza por esa actividad que te trae felicidad, tranquilidad o satisfacción: que sea tu «punto de luz».",
            ],
        },
    },
    45: {
        "tecnica": "Red de Apoyo Visible",
        "objetivo": "Reconocer y fortalecer la red de personas dispuestas a apoyarte.",
        "instrucciones": [
            "En la imagen de apoyo (Anexo D.2), coloca en cada rama del árbol los nombres de las personas que te apoyan.",
            "Piensa en cómo y cuándo pedirles ayuda, y practica pequeños pedidos para crear confianza en buscar apoyo.",
            "Recursos necesarios: impresión de la imagen (Anexo D.2), colores, esfero negro.",
        ],
    },
    # Pregunta 50: el documento fuente no trae el objetivo de la técnica.
    # Sin ficha hasta que la autora lo entregue — ver docstring del módulo.
    50: {},
}

# Preguntas 7, 20, 26, 45 traen una sola ficha ("Ambos") en vez de una por
# nivel: se replica para POBRE y MODERADO antes de exponer RECOMENDACIONES.
for _num_q, _ficha in list(RECOMENDACIONES.items()):
    if _ficha and "POBRE" not in _ficha and "MODERADO" not in _ficha:
        RECOMENDACIONES[_num_q] = {"POBRE": _ficha, "MODERADO": _ficha}

NIVELES_CON_RECOMENDACION = {"POBRE", "MODERADO"}
PRIORIDAD_NIVEL = {"POBRE": 0, "MODERADO": 1}


def obtener_recomendaciones_ri(encuesta: EncuestaHplp) -> list[dict]:
    """
    Devuelve tarjetas de recomendación de Relaciones Interpersonales.
    Solo para POBRE y MODERADO. Orden: POBRE → MODERADO.
    La pregunta 50 no genera tarjeta (ver RECOMENDACIONES[50]).
    """
    tarjetas = []
    for num_q, campo in ITEM_FIELDS.items():
        valor = getattr(encuesta, campo)
        nivel = puntaje_a_nivel(valor)
        if nivel not in NIVELES_CON_RECOMENDACION:
            continue
        rec = RECOMENDACIONES[num_q].get(nivel)
        if rec is None:
            continue
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
