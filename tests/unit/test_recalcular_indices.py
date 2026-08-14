"""
Tests de scripts/recalcular_indices.recalcular().

Esa función es la que va a reescribir datos reales, así que conviene tenerla
cubierta: se ejecuta sobre las encuestas ya guardadas, cuyas columnas derivadas
se calcularon con el mapeo de subescalas anterior.

No tocan la base de datos: recalcular() solo lee atributos de la fila, así que
basta con una instancia de EncuestaHplp sin persistir.
"""
import pytest

from app.models.encuesta_hplp import EncuestaHplp
from app.services.encuesta_hplp_service import ITEM_FIELDS, SUBSCALES_HPLP2
from scripts.recalcular_indices import CAMPOS_DERIVADOS, recalcular


def _fila(**valores_por_campo: int) -> EncuestaHplp:
    """Fila en memoria con todos los ítems en 1, salvo los que se pasen."""
    return EncuestaHplp(**({c: 1 for c in ITEM_FIELDS} | valores_por_campo))


def test_recalcula_todas_las_columnas_derivadas():
    nuevos = recalcular(_fila())
    assert set(nuevos) == set(CAMPOS_DERIVADOS)


def test_corrige_una_fila_guardada_con_el_mapeo_viejo():
    """
    Caso real: solo Psicología Positiva respondida en 4, el resto en 1.
    El mapeo viejo repartía los pp_ entre RI, N y RS, así que dejaba a PP con un
    índice bajo y contaminaba tres dimensiones que debían estar en cero.
    """
    _, campos_pp = SUBSCALES_HPLP2["psicologia_positiva"]
    fila = _fila(**{c: 4 for c in campos_pp})

    # Valores derivados heredados del mapeo viejo.
    fila.pp_indice, fila.pp_nivel = 33.33, "Moderado"
    fila.ri_indice, fila.ri_nivel = 44.44, "Moderado"
    fila.n_indice, fila.n_nivel = 11.11, "Pobre"

    nuevos = recalcular(fila)

    assert nuevos["pp_indice"] == 100.0
    assert nuevos["pp_nivel"] == "Excelente"
    for prefijo in ("ri", "n", "rs", "af", "me"):
        assert nuevos[f"{prefijo}_indice"] == 0.0
        assert nuevos[f"{prefijo}_nivel"] == "Pobre"


def test_puntaje_crudo_se_deriva_de_los_items():
    _, campos_pp = SUBSCALES_HPLP2["psicologia_positiva"]
    nuevos = recalcular(_fila(**{c: 4 for c in campos_pp}))

    # 43 ítems en 1 + 9 ítems de PP en 4
    assert nuevos["puntaje_crudo"] == 43 + 9 * 4
    assert nuevos["nivel_global"] == "Pobre"


@pytest.mark.parametrize("valor,indice", [(1, 0.0), (2, 33.33), (3, 66.67), (4, 100.0)])
def test_fila_uniforme_da_el_mismo_indice_en_todas_las_dimensiones(valor, indice):
    nuevos = recalcular(_fila(**{c: valor for c in ITEM_FIELDS}))

    assert nuevos["indice_global"] == indice
    for prefijo, _ in SUBSCALES_HPLP2.values():
        assert nuevos[f"{prefijo}_indice"] == indice


def test_una_fila_ya_correcta_no_produce_cambios():
    """Correr el script dos veces seguidas debe ser idempotente."""
    fila = _fila(**{c: 3 for c in ITEM_FIELDS})
    primera = recalcular(fila)

    for campo, valor in primera.items():
        setattr(fila, campo, valor)

    assert recalcular(fila) == primera
