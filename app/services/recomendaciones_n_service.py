"""
Servicio de recomendaciones de Nutrición.
Tabla estática de 10 fichas (una por pregunta). BUENO y EXCELENTE no
reciben recomendación.

El documento fuente ("Guía requerimientos Nutrición.docx", equipo de
Nutrición y Dietética: Diana Marcela Morales Carpio y Adriana Carolina
Daza Albor) solo traía, para cada una de las 10 preguntas, una
recomendación en texto libre — la tabla estructurada de técnica/objetivo/
instrucciones/nivel de aplicación estaba sin diligenciar (plantilla
vacía), y así se confirmó también en el "Compendio de Guías de
Recomendaciones por Área de Bienestar", que la marca explícitamente como
"Campos pendientes por diligenciar".

Ana pidió (2026-08-19) completar esa tabla a partir del texto libre ya
escrito por las profesionales, en vez de esperar la versión diligenciada:
revisó y aprobó el documento resultante antes de construir este servicio.
Por eso, a diferencia de manejo del estrés o relaciones interpersonales,
aquí la técnica/objetivo/instrucciones de cada pregunta no son una cita
textual de las autoras sino una estructuración de su recomendación
original. El documento no distingue Pobre de Moderado para ninguna
pregunta, así que las 10 aplican igual en ambos niveles.
"""
from app.models.encuesta_hplp import EncuestaHplp


def puntaje_a_nivel(valor: int) -> str:
    return {1: "POBRE", 2: "MODERADO", 3: "BUENO", 4: "EXCELENTE"}[valor]


PREGUNTAS = {
    2:  "Consumir alimentos reducidos en grasas, grasas saturadas o calorías.",
    8:  "Limitar el consumo de alimentos con azúcares añadidos (dulces, pasteles/panes, refrescos, entre otros).",
    14: "Comer diariamente de 6 a 11 porciones (1 porción = ½ taza) de carbohidratos (pan, tortilla, arroz, avena, pasta, fideos, amaranto, entre otros).",
    21: "Comer diariamente de 2 a 4 porciones de frutas (1 porción = 1 pieza o 1 taza).",
    27: "Comer diariamente de 3 a 5 porciones de vegetales (1 porción de vegetales crudos = 1 taza y 1 porción de vegetales cocidos = ½ taza).",
    33: "Comer diariamente de 2 a 3 porciones de lácteos (1 porción de leche = 1 taza, 1 porción de yogurt = ½ taza y 1 porción de queso = 40 g).",
    39: "Comer diariamente de 2 a 3 porciones (1 porción = ½ taza) de proteína de origen vegetal (frijol, garbanzo, lenteja, soya, nueces, almendras, cacahuates, entre otras).",
    40: "Comer diariamente de 2 a 3 porciones (1 porción = 90 gramos) de proteína de origen animal (carne, aves, pescado, huevos, entre otras).",
    46: "Observar los sellos de advertencia (hexágonos negros) que tienen los productos alimenticios ultraprocesados (empacados).",
    51: "Desayunar diariamente.",
}

ITEM_FIELDS = {
    2:  "n_item_02",
    8:  "n_item_08",
    14: "n_item_14",
    21: "n_item_21",
    27: "n_item_27",
    33: "n_item_33",
    39: "n_item_39",
    40: "n_item_40",
    46: "n_item_46",
    51: "n_item_51",
}

_FICHAS = {
    2: {
        "tecnica": "Sustitución progresiva de frituras",
        "objetivo": "Reducir el consumo de grasas y calorías provenientes de frituras, disminuyendo la acumulación de grasa abdominal y visceral.",
        "instrucciones": [
            "Durante un fin de semana, anota cuántas veces consumes alimentos fritos.",
            "Reemplaza una fritura a la semana por una preparación al horno, a la plancha o al vapor.",
            "Si fríes en casa, no reutilices el aceite más de una o dos veces: reutilizarlo daña sus componentes y aumenta el daño metabólico.",
            "Aumenta gradualmente el número de comidas no fritas hasta que sean la mayoría de tu semana.",
        ],
        "tipo_actividad": "registro_numerico",
        "config_actividad": {"unidad": "comidas fritas hoy"},
    },
    8: {
        "tecnica": "Reducción progresiva de azúcares añadidos",
        "objetivo": "Disminuir el consumo diario de azúcares añadidos para prevenir alteraciones en la glucosa y la acumulación de grasa.",
        "instrucciones": [
            "Durante una semana, registra cuántas porciones de dulces, panes/pasteles o bebidas azucaradas consumes al día.",
            "Si superas 3 porciones diarias, reduce una porción cada semana hasta llegar a un consumo ocasional.",
            "Reserva los alimentos con azúcar añadida para ocasiones especiales, no para el consumo diario.",
            "Sustituye una bebida azucarada al día por agua o una infusión sin azúcar.",
        ],
        "tipo_actividad": "registro_numerico",
        "config_actividad": {"unidad": "porciones con azúcar añadida hoy"},
    },
    14: {
        "tecnica": "Plato balanceado: carbohidratos integrales",
        "objetivo": "Incorporar la porción adecuada de carbohidratos, priorizando los integrales, en las comidas principales.",
        "instrucciones": [
            "En cada comida principal, sirve los carbohidratos (pan, arroz, pasta, avena, tortilla) ocupando un cuarto de tu plato.",
            "Prioriza las versiones integrales (arroz integral, pan integral, avena) sobre las refinadas cuando sea posible.",
            "Ajusta la cantidad según tu nivel de actividad física y tus objetivos; si tienes una condición de salud, consulta con un profesional para adaptar la porción.",
        ],
        "tipo_actividad": "registro_numerico",
        "config_actividad": {"unidad": "porciones de carbohidratos hoy"},
    },
    21: {
        "tecnica": "Frutas como primera opción para la saciedad",
        "objetivo": "Aumentar el consumo diario de frutas para mejorar la saciedad y apoyar el control de colesterol y triglicéridos.",
        "instrucciones": [
            "Ten siempre frutas a la mano (bolso, nevera o escritorio) para los momentos de ansiedad por comer.",
            "Varía el tipo de fruta: intenta consumir al menos 3 frutas diferentes a lo largo de la semana.",
            "Prefiere comer la fruta entera en vez de en jugo, para conservar la fibra y la saciedad.",
            "Acompaña una comida principal al día con una porción de fruta.",
        ],
        "tipo_actividad": "registro_numerico",
        "config_actividad": {"unidad": "porciones de fruta hoy"},
    },
    27: {
        "tecnica": "Vegetales en cada comida",
        "objetivo": "Aumentar el consumo diario de vegetales para favorecer la saciedad y el aporte de antioxidantes, vitaminas, minerales y fibra.",
        "instrucciones": [
            "Incluye una porción de vegetales, crudos o cocidos, en al menos dos comidas principales del día.",
            "Varía la preparación (ensaladas, salteados, sopas) para no perder la costumbre.",
            "Aprovecha los vegetales como opción de snack entre comidas.",
        ],
        "tipo_actividad": "registro_numerico",
        "config_actividad": {"unidad": "porciones de vegetales hoy"},
    },
    33: {
        "tecnica": "Lácteos como refrigerio saludable",
        "objetivo": "Asegurar el aporte diario de calcio a través de lácteos, priorizando opciones sin azúcares añadidas.",
        "instrucciones": [
            "Incluye una porción de lácteo (leche, yogur o queso) como parte de un refrigerio o comida principal.",
            "Al elegir yogur, prefiere uno sin azúcar añadida y, si es posible, con probióticos.",
            "Combina los lácteos con otros alimentos (frutas, cereales) para variar su consumo.",
        ],
        "tipo_actividad": "registro_numerico",
        "config_actividad": {"unidad": "porciones de lácteos hoy"},
    },
    39: {
        "tecnica": "Combinación de leguminosas con otros grupos",
        "objetivo": "Incorporar proteína de origen vegetal de forma que se aproveche mejor su absorción.",
        "instrucciones": [
            "Incluye leguminosas (fríjol, garbanzo, lenteja, soya) de 2 a 3 veces por semana.",
            "Combina siempre la leguminosa con un carbohidrato y, cuando sea posible, con un alimento de origen animal, para mejorar la absorción de la proteína.",
            "Recuerda que las leguminosas por sí solas no cubren el requerimiento proteico completo del día.",
        ],
        "tipo_actividad": "registro_numerico",
        "config_actividad": {"unidad": "porciones de proteína vegetal hoy"},
    },
    40: {
        "tecnica": "Porción diaria de proteína animal",
        "objetivo": "Asegurar el consumo diario de proteína de origen animal en la cantidad recomendada para apoyar procesos metabólicos y hormonales.",
        "instrucciones": [
            "Incluye una porción de proteína animal (carne, aves, pescado, huevo) en tus comidas principales todos los días.",
            "Ajusta la porción entre 50 y 90 gramos según tu objetivo o necesidad nutricional.",
            "Varía la fuente de proteína animal a lo largo de la semana (pescado, pollo, huevo, carnes rojas magras) en vez de repetir siempre la misma.",
        ],
        "tipo_actividad": "registro_numerico",
        "config_actividad": {"unidad": "porciones de proteína animal hoy"},
    },
    46: {
        "tecnica": "Lectura del etiquetado y los sellos de advertencia",
        "objetivo": "Desarrollar el hábito de revisar los sellos de advertencia y la información nutricional antes de consumir productos ultraprocesados.",
        "instrucciones": [
            "Antes de comprar un producto empacado, revisa cuántos sellos de advertencia (hexágonos negros) trae.",
            "Entre dos productos similares, prefiere el que tenga menos sellos de advertencia.",
            "No te quedes solo con los sellos: revisa también la lista de ingredientes y la información nutricional en letra pequeña.",
            "Si tienes una enfermedad crónica no transmisible, ten especial cuidado con los productos que traen varios sellos.",
        ],
        "tipo_actividad": "lista",
        "config_actividad": {"placeholder": "Producto empacado que revisaste hoy..."},
    },
    51: {
        "tecnica": "Desayuno balanceado diario",
        "objetivo": "Consolidar el hábito de desayunar todos los días con una combinación balanceada de grupos de alimentos.",
        "instrucciones": [
            "Arma tu desayuno combinando al menos tres grupos: un cereal o tubérculo, una fruta, un lácteo y/o una fuente de proteína.",
            "Si el estrés te quita el apetito en las mañanas, empieza con una porción pequeña (por ejemplo, una fruta con yogur) en vez de saltarte la comida.",
            "Evita saltarte el desayuno con fines de bajar de peso: alterar así el metabolismo tiende a generar más ganancia de peso, no menos.",
            "Prepara la noche anterior algo simple (avena remojada, fruta picada) si las mañanas son apuradas.",
        ],
        "tipo_actividad": "diario",
        "config_actividad": {
            "prompt": "¿Qué desayunaste hoy? Menciona los grupos de alimentos que incluiste (cereal/tubérculo, fruta, lácteo, proteína).",
        },
    },
}

# El documento no distingue Pobre de Moderado: la misma ficha aplica a
# ambos niveles para las 10 preguntas.
RECOMENDACIONES: dict[int, dict[str, dict]] = {
    num_q: {"POBRE": ficha, "MODERADO": ficha} for num_q, ficha in _FICHAS.items()
}

NIVELES_CON_RECOMENDACION = {"POBRE", "MODERADO"}
PRIORIDAD_NIVEL = {"POBRE": 0, "MODERADO": 1}


def obtener_recomendaciones_n(encuesta: EncuestaHplp) -> list[dict]:
    """
    Devuelve tarjetas de recomendación de Nutrición.
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
