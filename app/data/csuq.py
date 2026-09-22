"""Cuestionario de Usabilidad de Sistemas Informáticos (CSUQ), adaptación al
español de Hedlefs et al. (2015) del instrumento de Lewis. 16 ítems positivos
en escala Likert 1–7 (1 = totalmente en desacuerdo, 7 = totalmente de acuerdo);
mayor puntaje = mejor usabilidad. Se reporta un promedio global y tres
subescalas."""

CSUQ_ITEMS: list[str] = [
    "En general, estoy satisfecho con lo fácil que es utilizar este sitio web.",
    "Fue simple usar este sitio web.",
    "Soy capaz de completar mi trabajo rápidamente utilizando este sitio web.",
    "Me siento cómodo utilizando este sitio web.",
    "Fue fácil aprender a utilizar este sitio web.",
    "Creo que me volví experto rápidamente utilizando este sitio web.",
    "El sitio web muestra mensajes de error que me dicen claramente cómo resolver los problemas.",
    "Cada vez que cometo un error utilizando el sitio web, lo resuelvo fácil y rápidamente.",
    "La información (como ayuda en línea, mensajes en pantalla y otra documentación) que provee este sitio web es clara.",
    "Es fácil encontrar en el sitio web la información que necesito.",
    "La información que proporciona el sitio web fue efectiva ayudándome a completar las tareas.",
    "La organización de la información del sitio web en la pantalla fue clara.",
    "La interfaz del sitio web fue placentera.",
    "Me gustó utilizar el sitio web.",
    "El sitio web tuvo todas las herramientas que esperaba que tuviera.",
    "En general, estuve satisfecho con el sitio web.",
]

# Subescalas del CSUQ por rango de ítem (1-indexado, inclusivo).
SUBESCALAS: dict[str, tuple[str, int, int]] = {
    "sysuse": ("Utilidad del sistema", 1, 6),
    "infoqual": ("Calidad de la información", 7, 12),
    "interqual": ("Calidad de la interfaz", 13, 15),
}

ESCALA_MIN = 1
ESCALA_MAX = 7
TOTAL_ITEMS = len(CSUQ_ITEMS)


def calcular_puntajes(respuestas: list[int]) -> dict[str, float]:
    """respuestas: 16 valores 1–7 en orden de ítem. Devuelve las 3 subescalas
    y el promedio global, redondeados a 2 decimales."""
    def promedio(desde: int, hasta: int) -> float:
        tramo = respuestas[desde - 1:hasta]
        return round(sum(tramo) / len(tramo), 2)

    puntajes = {clave: promedio(ini, fin) for clave, (_, ini, fin) in SUBESCALAS.items()}
    puntajes["puntaje_global"] = round(sum(respuestas) / len(respuestas), 2)
    return puntajes
