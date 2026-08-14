from app.schemas.encuesta_hplp import EncuestaCreate

# ──────────────────────────────────────────────────────────────────────────────
# Mapeo PEPS II correcto por número de ítem.
#
# Los prefijos (ri_, n_, af_…) en los nombres de campo del frontend NO coinciden
# con las subescalas reales del instrumento HPLP-II ASD.  Se usa el número del
# ítem para asignarlo a la dimensión que corresponde según el instrumento.
#
#  RI (9): ítems  1, 7,13,19,25,31,37,43,49
#  N  (9): ítems  2, 8,14,20,26,32,38,44,50
#  RS (9): ítems  3, 9,15,21,27,33,39,45,51
#  AF (8): ítems  4,10,16,22,28,34,40,46
#  ME (8): ítems  5,11,17,23,29,35,41,47
#  PP (9): ítems  6,12,18,24,30,36,42,48,52
# ──────────────────────────────────────────────────────────────────────────────

SUBSCALES_PEPS2: dict[str, list[str]] = {
    "relaciones_interpersonales": [   # ítems 1,7,13,19,25,31,37,43,49
        "ri_item_01", "ri_item_07", "ri_item_13",
        "pp_item_19", "pp_item_25", "pp_item_31", "pp_item_37",
        "me_item_43", "pp_item_49",
    ],
    "nutricion": [                    # ítems 2,8,14,20,26,32,38,44,50
        "n_item_02",  "n_item_08",  "n_item_14",
        "ri_item_20", "ri_item_26", "ri_item_32", "ri_item_38",
        "pp_item_44", "ri_item_50",
    ],
    "responsabilidad_salud": [        # ítems 3,9,15,21,27,33,39,45,51
        "rs_item_03", "rs_item_09", "rs_item_15",
        "n_item_21",  "n_item_27",  "n_item_33",  "n_item_39",
        "ri_item_45", "n_item_51",
    ],
    "actividad_fisica": [             # ítems 4,10,16,22,28,34,40,46
        "af_item_04", "af_item_10", "af_item_16",
        "rs_item_22", "rs_item_28", "rs_item_34",
        "n_item_40",  "n_item_46",
    ],
    "manejo_estres": [                # ítems 5,11,17,23,29,35,41,47
        "me_item_05", "me_item_11",
        "af_item_17", "af_item_23", "af_item_29", "af_item_35",
        "rs_item_41", "af_item_47",
    ],
    "psicologia_positiva": [          # ítems 6,12,18,24,30,36,42,48,52
        "pp_item_06", "pp_item_12",
        "me_item_18", "me_item_24", "me_item_30", "me_item_36",
        "af_item_42", "me_item_48",
        "pp_item_52",
    ],
}

# Los 52 campos de ítem. Se derivan del mapeo para que no puedan
# desincronizarse, y para excluir los campos de perfil (facultad, program,
# tipo_usuario) que EncuestaCreate también trae.
ITEM_FIELDS: list[str] = [
    campo for campos in SUBSCALES_PEPS2.values() for campo in campos
]

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
    Calcula índices PEPS II para cada dimensión y el puntaje global.
    Retorna un dict listo para guardar en el modelo EncuestaHplp.
    """
    data = payload.model_dump()

    resultados: dict = {}

    for dim, campos in SUBSCALES_PEPS2.items():
        valores = [data[c] for c in campos]
        promedio = sum(valores) / len(valores)
        indice = _indice(promedio)
        nivel = _nivel_por_indice(indice)

        # Prefijo de columna en BD (ri, n, rs, af, me, pp)
        prefijo = {
            "relaciones_interpersonales": "ri",
            "nutricion":                  "n",
            "responsabilidad_salud":      "rs",
            "actividad_fisica":           "af",
            "manejo_estres":              "me",
            "psicologia_positiva":        "pp",
        }[dim]

        resultados[f"{prefijo}_indice"] = indice
        resultados[f"{prefijo}_nivel"]  = nivel

    # Global
    puntaje_crudo = sum(data[c] for c in ITEM_FIELDS)   # suma de los 52 ítems
    promedio_global = puntaje_crudo / 52
    resultados["puntaje_crudo"] = puntaje_crudo
    resultados["indice_global"] = _indice(promedio_global)
    resultados["nivel_global"]  = _nivel_global(puntaje_crudo)

    return resultados
