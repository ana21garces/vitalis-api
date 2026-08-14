from app.schemas.encuesta_hplp import EncuestaCreate

# ──────────────────────────────────────────────────────────────────────────────
# Subescalas del instrumento HPLP-II ASD (adaptación, 52 ítems).
#
# El prefijo del campo (ri_, n_, rs_, af_, me_, pp_) YA indica la dimensión a la
# que pertenece el ítem: el número del campo es la posición de la pregunta en el
# cuestionario, y el prefijo su dimensión.  Ambos vienen de QUESTION_KEY_MAP en
# el frontend y coinciden con el texto que se le muestra al usuario.
#
# OJO — no aplicar aquí la numeración del HPLP-II original (1,7,13,19… por
# módulo 6).  Esta adaptación reordenó y redistribuyó los ítems: Nutrición tiene
# 10 (separa proteína vegetal, ítem 39, de animal, ítem 40) y Responsabilidad en
# Salud tiene 7, en vez de 9 y 9.  Verificable contra el texto de las preguntas:
# la 17 es "actividades físicas moderadas" (AF), la 19 "mirar hacia el futuro de
# forma positiva" (PP) y la 22 "buscar una segunda opinión" (RS).
#
# Este mismo criterio es el que usan los servicios recomendaciones_*_service.
# ──────────────────────────────────────────────────────────────────────────────

# dimensión -> (prefijo de columna en BD, campos de ítem)
SUBSCALES_HPLP2: dict[str, tuple[str, list[str]]] = {
    "relaciones_interpersonales": ("ri", [   # ítems 1,7,13,20,26,32,38,45,50
        "ri_item_01", "ri_item_07", "ri_item_13", "ri_item_20", "ri_item_26",
        "ri_item_32", "ri_item_38", "ri_item_45", "ri_item_50",
    ]),
    "nutricion": ("n", [                     # ítems 2,8,14,21,27,33,39,40,46,51
        "n_item_02", "n_item_08", "n_item_14", "n_item_21", "n_item_27",
        "n_item_33", "n_item_39", "n_item_40", "n_item_46", "n_item_51",
    ]),
    "responsabilidad_salud": ("rs", [        # ítems 3,9,15,22,28,34,41
        "rs_item_03", "rs_item_09", "rs_item_15", "rs_item_22", "rs_item_28",
        "rs_item_34", "rs_item_41",
    ]),
    "actividad_fisica": ("af", [             # ítems 4,10,16,17,23,29,35,42,47
        "af_item_04", "af_item_10", "af_item_16", "af_item_17", "af_item_23",
        "af_item_29", "af_item_35", "af_item_42", "af_item_47",
    ]),
    "manejo_estres": ("me", [                # ítems 5,11,18,24,30,36,43,48
        "me_item_05", "me_item_11", "me_item_18", "me_item_24", "me_item_30",
        "me_item_36", "me_item_43", "me_item_48",
    ]),
    "psicologia_positiva": ("pp", [          # ítems 6,12,19,25,31,37,44,49,52
        "pp_item_06", "pp_item_12", "pp_item_19", "pp_item_25", "pp_item_31",
        "pp_item_37", "pp_item_44", "pp_item_49", "pp_item_52",
    ]),
}

# Los 52 campos de ítem. Se derivan del mapeo para que no puedan desincronizarse,
# y para excluir los campos de perfil (facultad, program, tipo_usuario) que
# EncuestaCreate también trae.
ITEM_FIELDS: list[str] = [
    campo for _, campos in SUBSCALES_HPLP2.values() for campo in campos
]

assert len(ITEM_FIELDS) == len(set(ITEM_FIELDS)) == 52, (
    f"El mapeo de subescalas debe cubrir los 52 ítems sin repetir; "
    f"tiene {len(ITEM_FIELDS)} ({len(set(ITEM_FIELDS))} únicos)."
)

NIVELES_CRUDO = [
    (52,  90,  "Pobre"),
    (91,  129, "Moderado"),
    (130, 168, "Bueno"),
    (169, 208, "Excelente"),
]


def _indice(promedio: float) -> float:
    """Convierte el promedio 1–4 al índice 0–100 del PEPS II."""
    return round((promedio - 1) / 3 * 100, 2)


def _nivel_por_indice(indice: float) -> str:
    if indice <= 25:
        return "Pobre"
    elif indice <= 50:
        return "Moderado"
    elif indice <= 75:
        return "Bueno"
    else:
        return "Excelente"


def _nivel_global(puntaje_crudo: int) -> str:
    for lo, hi, nivel in NIVELES_CRUDO:
        if lo <= puntaje_crudo <= hi:
            return nivel
    return "Excelente"


def calcular_puntajes(payload: EncuestaCreate) -> dict:
    """
    Calcula el índice PEPS II de cada dimensión y el puntaje global.
    Retorna un dict listo para guardar en el modelo EncuestaHplp.
    """
    data = payload.model_dump()

    resultados: dict = {}

    for prefijo, campos in SUBSCALES_HPLP2.values():
        promedio = sum(data[c] for c in campos) / len(campos)
        indice = _indice(promedio)

        resultados[f"{prefijo}_indice"] = indice
        resultados[f"{prefijo}_nivel"]  = _nivel_por_indice(indice)

    # Global
    puntaje_crudo = sum(data[c] for c in ITEM_FIELDS)   # suma de los 52 ítems
    promedio_global = puntaje_crudo / 52
    resultados["puntaje_crudo"] = puntaje_crudo
    resultados["indice_global"] = _indice(promedio_global)
    resultados["nivel_global"]  = _nivel_global(puntaje_crudo)

    return resultados
