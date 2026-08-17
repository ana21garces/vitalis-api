"""
Tests de scripts/reporte_usuarios.

No tocan la base de datos: fila() y columnas() solo leen atributos, asi que
basta con instancias de los modelos sin persistir.
"""
from app.models.encuesta_hplp import EncuestaHplp
from app.models.user import User
from app.services.encuesta_hplp_service import SUBSCALES_HPLP2
from scripts.reporte_usuarios import CAMPOS_BASE, columnas, fila


def _usuario(**kwargs) -> User:
    base = {
        "full_name": "Ana Garces", "email": "ana@unac.edu.co",
        "facultad": "Ingenieria", "program": "Sistemas",
        "tipo_usuario": "estudiante", "is_verified": True,
    }
    return User(**(base | kwargs))


def _encuesta() -> EncuestaHplp:
    valores = {"puntaje_crudo": 150, "indice_global": 62.82, "nivel_global": "Bueno"}
    for prefijo, _ in SUBSCALES_HPLP2.values():
        valores[f"{prefijo}_indice"] = 60.0
        valores[f"{prefijo}_nivel"] = "Bueno"
    return EncuestaHplp(**valores)


def test_columnas_incluyen_las_seis_dimensiones():
    cols = columnas()
    assert cols[:len(CAMPOS_BASE)] == CAMPOS_BASE
    # dos columnas (indice y nivel) por cada dimension
    assert len(cols) == len(CAMPOS_BASE) + 2 * len(SUBSCALES_HPLP2)
    assert "psicologia_positiva_indice" in cols
    assert "manejo_estres_nivel" in cols


def test_fila_cubre_exactamente_las_columnas():
    assert set(fila(_usuario(), _encuesta())) == set(columnas())
    assert set(fila(_usuario(), None)) == set(columnas())


def test_usuario_con_encuesta():
    f = fila(_usuario(), _encuesta())
    assert f["hizo_hplp"] == "SI"
    assert f["indice_global"] == 62.82
    assert f["psicologia_positiva_nivel"] == "Bueno"


def test_usuario_sin_encuesta_deja_las_metricas_vacias():
    f = fila(_usuario(), None)
    assert f["hizo_hplp"] == "NO"
    assert f["nombre"] == "Ana Garces"
    for campo in ("indice_global", "nivel_global", "puntaje_crudo", "fecha_respuesta"):
        assert f[campo] == ""
    assert f["actividad_fisica_indice"] == ""
    assert f["actividad_fisica_nivel"] == ""


def test_campos_de_perfil_ausentes_salen_vacios_no_none():
    """Los 48 encuestados historicos no tienen facultad ni programa."""
    f = fila(_usuario(facultad=None, program=None, tipo_usuario=None), _encuesta())
    assert f["facultad"] == ""
    assert f["programa"] == ""
    assert f["tipo_usuario"] == ""


def test_verificado_se_traduce_a_si_no():
    assert fila(_usuario(is_verified=True), None)["verificado"] == "SI"
    assert fila(_usuario(is_verified=False), None)["verificado"] == "NO"
