"""
Cubre el endpoint de reportes descargables: los formatos y los filtros.

Del CSV se verifica el contenido (encabezado y filas), que es lo que se lleva a
un programa de estadística; de Excel y PDF solo que el archivo salga con su tipo
correcto, porque su contenido es binario.
"""
from datetime import date, timedelta

from tests.conftest import ENCUESTA_PAYLOAD

REPORTES_URL = "/api/v1/reportes"
ENCUESTA_URL = "/api/v1/encuesta"
SEG_URL = "/api/v1/seguimiento-recomendaciones"
GAMI_URL = "/api/v1/gamificacion"


def _registrar_una_actividad(client, auth_headers):
    """Deja al estudiante con una actividad de AF registrada hoy."""
    client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)
    tarjetas = client.get(f"{SEG_URL}/actividad-fisica/tarjetas", headers=auth_headers).json()
    seguimiento_id = tarjetas["tarjetas"][0]["seguimiento"]["id"]
    client.post(f"{SEG_URL}/{seguimiento_id}/registrar-dia", json={}, headers=auth_headers)


def test_cumplimiento_registra_lo_hecho(client, auth_headers, admin_headers):
    _registrar_una_actividad(client, auth_headers)

    res = client.get(
        f"{REPORTES_URL}/cumplimiento",
        params={"formato": "csv", "dimension": "actividad_fisica"},
        headers=admin_headers,
    )
    assert res.status_code == 200
    texto = res.content.decode("utf-8-sig")
    encabezado = texto.splitlines()[0].split(";")
    assert encabezado[0] == "Nombre"
    assert "¿La hizo?" in encabezado
    assert "Fechas" in encabezado

    hoy = date.today().strftime("%Y-%m-%d")
    assert hoy in texto
    filas = [f for f in texto.splitlines()[1:] if f]
    assert any(f.split(";")[8] == "Sí" for f in filas)


def test_cumplimiento_periodo_excluye_lo_de_fuera(client, auth_headers, admin_headers):
    _registrar_una_actividad(client, auth_headers)

    manana = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    res = client.get(
        f"{REPORTES_URL}/cumplimiento",
        params={"formato": "csv", "dimension": "actividad_fisica", "desde": manana},
        headers=admin_headers,
    )
    assert res.status_code == 200
    texto = res.content.decode("utf-8-sig")
    assert date.today().strftime("%Y-%m-%d") not in texto


def test_misiones_registra_lo_completado(client, auth_headers, admin_headers):
    client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)
    hoy = client.get(f"{GAMI_URL}/misiones/hoy", headers=auth_headers).json()
    assert hoy["misiones"]
    mision_id = hoy["misiones"][0]["id"]
    client.post(f"{GAMI_URL}/misiones/{mision_id}/completar", headers=auth_headers)

    res = client.get(f"{REPORTES_URL}/misiones", params={"formato": "csv"}, headers=admin_headers)
    assert res.status_code == 200
    texto = res.content.decode("utf-8-sig")
    encabezado = texto.splitlines()[0].split(";")
    assert encabezado[0] == "Nombre"
    assert "Misión" in encabezado
    assert "Veces" in encabezado
    assert date.today().strftime("%Y-%m-%d") in texto


def test_requiere_admin(client, auth_headers):
    res = client.get(f"{REPORTES_URL}/usuarios", headers=auth_headers)
    assert res.status_code == 403


def test_tipo_desconocido(client, admin_headers):
    res = client.get(f"{REPORTES_URL}/inventado", headers=admin_headers)
    assert res.status_code == 404


def test_formato_invalido(client, admin_headers):
    res = client.get(
        f"{REPORTES_URL}/usuarios", params={"formato": "word"}, headers=admin_headers
    )
    assert res.status_code == 400


def test_csv_trae_encabezado_y_filas(client, auth_headers, admin_headers):
    client.post(
        ENCUESTA_URL, json={**ENCUESTA_PAYLOAD, "sexo": "femenino"}, headers=auth_headers
    )
    res = client.get(
        f"{REPORTES_URL}/usuarios", params={"formato": "csv"}, headers=admin_headers
    )
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    assert ".csv" in res.headers["content-disposition"]

    texto = res.content.decode("utf-8-sig")
    lineas = [l for l in texto.splitlines() if l]
    encabezado = lineas[0].split(";")
    assert encabezado[0] == "Nombre"
    assert "Sexo" in encabezado
    # El usuario de la encuesta y el admin que pide el reporte.
    assert len(lineas) == 3
    assert "femenino" in texto


def test_csv_de_progresion_compara_primera_y_ultima(client, auth_headers, admin_headers):
    client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)
    res = client.get(
        f"{REPORTES_URL}/progresion",
        params={"formato": "csv", "dimension": "todas"},
        headers=admin_headers,
    )
    assert res.status_code == 200
    encabezado = res.content.decode("utf-8-sig").splitlines()[0]
    assert "Sexo" in encabezado
    assert "nivel inicial" in encabezado
    assert "tendencia" in encabezado


def test_excel_y_pdf_siguen_saliendo(client, auth_headers, admin_headers):
    client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)
    excel = client.get(
        f"{REPORTES_URL}/participacion", params={"formato": "excel"}, headers=admin_headers
    )
    assert excel.status_code == 200
    assert "spreadsheet" in excel.headers["content-type"]

    pdf = client.get(
        f"{REPORTES_URL}/distribucion", params={"formato": "pdf"}, headers=admin_headers
    )
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
