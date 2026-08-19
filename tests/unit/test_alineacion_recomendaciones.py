"""
Cada vista de rol muestra un índice de dimensión (pp_indice, af_indice,
rs_indice) junto a las tarjetas de recomendación de esa dimensión. Si el
servicio de cálculo y el de recomendaciones no usan el mismo conjunto de ítems,
el índice describe una cosa y las tarjetas otra.

Estos tests amarran los dos servicios entre sí.
"""
import pytest

from app.services import (
    recomendaciones_af_service,
    recomendaciones_pp_service,
    recomendaciones_rs_service,
    recomendaciones_ri_service,
)
from app.services.encuesta_hplp_service import SUBSCALES_HPLP2

SERVICIOS_POR_DIMENSION = [
    ("psicologia_positiva", recomendaciones_pp_service),
    ("actividad_fisica", recomendaciones_af_service),
    ("responsabilidad_salud", recomendaciones_rs_service),
    ("relaciones_interpersonales", recomendaciones_ri_service),
]


@pytest.mark.parametrize("dimension,servicio", SERVICIOS_POR_DIMENSION)
def test_las_tarjetas_usan_los_mismos_items_que_el_indice(dimension, servicio):
    _, campos_del_indice = SUBSCALES_HPLP2[dimension]

    assert set(servicio.ITEM_FIELDS.values()) == set(campos_del_indice), (
        f"{dimension}: las recomendaciones se generan sobre ítems distintos a "
        f"los que promedia el índice."
    )


@pytest.mark.parametrize("dimension,servicio", SERVICIOS_POR_DIMENSION)
def test_el_numero_de_pregunta_coincide_con_el_sufijo_del_campo(dimension, servicio):
    """La pregunta 19 debe leerse de pp_item_19, no de otro campo."""
    for num_pregunta, campo in servicio.ITEM_FIELDS.items():
        assert campo.endswith(f"_item_{num_pregunta:02d}"), (
            f"{dimension}: la pregunta {num_pregunta} lee el campo {campo}"
        )


@pytest.mark.parametrize("dimension,servicio", SERVICIOS_POR_DIMENSION)
def test_hay_texto_y_recomendacion_para_cada_item(dimension, servicio):
    for num_pregunta in servicio.ITEM_FIELDS:
        assert num_pregunta in servicio.PREGUNTAS, (
            f"{dimension}: falta el texto de la pregunta {num_pregunta}"
        )
        assert num_pregunta in servicio.RECOMENDACIONES, (
            f"{dimension}: falta la tarjeta de la pregunta {num_pregunta}"
        )
