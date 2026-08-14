"""
Tests del cálculo de índices PEPS II.

El punto crítico que cubren: cada dimensión debe puntuarse con los ítems de SU
propio prefijo. En esta adaptación (HPLP-II ASD) el prefijo del campo indica la
dimensión y el número es la posición de la pregunta, así que aplicar la
numeración del HPLP-II original mezclaría los ítems entre dimensiones.
"""
import pytest

from app.schemas.encuesta_hplp import EncuestaCreate
from app.services.encuesta_hplp_service import (
    ITEM_FIELDS,
    SUBSCALES_HPLP2,
    calcular_puntajes,
)

PERFIL = {
    "facultad": "Ingenieria",
    "program": "Ingenieria de Sistemas",
    "tipo_usuario": "estudiante",
}


def _payload(**valores_por_campo: int) -> EncuestaCreate:
    """Encuesta con todos los ítems en 1, salvo los que se pasen explícitos."""
    return EncuestaCreate(**PERFIL, **{c: 1 for c in ITEM_FIELDS} | valores_por_campo)


# ── Estructura del mapeo ──────────────────────────────────────────────────────

def test_mapeo_cubre_los_52_items_sin_repetir():
    assert len(ITEM_FIELDS) == 52
    assert len(set(ITEM_FIELDS)) == 52


def test_cada_dimension_solo_agrupa_campos_de_su_prefijo():
    """Blindaje contra volver a repartir ítems entre dimensiones por número."""
    for dimension, (prefijo, campos) in SUBSCALES_HPLP2.items():
        for campo in campos:
            assert campo.startswith(f"{prefijo}_item_"), (
                f"{dimension}: el campo {campo} no pertenece al prefijo {prefijo}_"
            )


def test_conteo_de_items_de_la_adaptacion():
    """Nutrición 10 y Responsabilidad en Salud 7 — no 9 y 9 como el HPLP-II original."""
    conteos = {dim: len(campos) for dim, (_, campos) in SUBSCALES_HPLP2.items()}
    assert conteos == {
        "relaciones_interpersonales": 9,
        "nutricion": 10,
        "responsabilidad_salud": 7,
        "actividad_fisica": 9,
        "manejo_estres": 8,
        "psicologia_positiva": 9,
    }


# ── Cálculo ───────────────────────────────────────────────────────────────────

def test_todo_en_uno_da_indice_cero():
    r = calcular_puntajes(_payload())
    assert r["puntaje_crudo"] == 52
    assert r["indice_global"] == 0.0
    assert r["nivel_global"] == "Pobre"
    for prefijo, _ in SUBSCALES_HPLP2.values():
        assert r[f"{prefijo}_indice"] == 0.0


def test_todo_en_cuatro_da_indice_cien():
    r = calcular_puntajes(_payload(**{c: 4 for c in ITEM_FIELDS}))
    assert r["puntaje_crudo"] == 208
    assert r["indice_global"] == 100.0
    assert r["nivel_global"] == "Excelente"
    for prefijo, _ in SUBSCALES_HPLP2.values():
        assert r[f"{prefijo}_indice"] == 100.0


@pytest.mark.parametrize("dimension", list(SUBSCALES_HPLP2))
def test_subir_una_dimension_no_mueve_a_las_demas(dimension):
    """
    Si solo suben los ítems de una dimensión, únicamente su índice cambia.
    Con el mapeo viejo (por número de ítem del HPLP-II original) este test
    fallaba: subir los pp_ movía también ri_, n_ y rs_.
    """
    prefijo, campos = SUBSCALES_HPLP2[dimension]
    r = calcular_puntajes(_payload(**{c: 4 for c in campos}))

    assert r[f"{prefijo}_indice"] == 100.0
    for otro_prefijo, _ in SUBSCALES_HPLP2.values():
        if otro_prefijo != prefijo:
            assert r[f"{otro_prefijo}_indice"] == 0.0, (
                f"subir {dimension} contaminó la dimensión {otro_prefijo}_"
            )


def test_items_de_perfil_no_entran_al_puntaje_crudo():
    """facultad/program/tipo_usuario son strings: no deben sumarse."""
    r = calcular_puntajes(_payload(**{c: 2 for c in ITEM_FIELDS}))
    assert r["puntaje_crudo"] == 104


def test_niveles_por_indice():
    # Un ítem en 2 sobre el resto en 1 mantiene la dimensión en "Pobre";
    # todos en 3 la dejan en "Bueno" (índice 66.67).
    r = calcular_puntajes(_payload(**{c: 3 for c in ITEM_FIELDS}))
    assert r["indice_global"] == 66.67
    assert r["nivel_global"] == "Bueno"
    for prefijo, _ in SUBSCALES_HPLP2.values():
        assert r[f"{prefijo}_nivel"] == "Bueno"
