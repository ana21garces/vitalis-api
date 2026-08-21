"""
Cubre el endpoint de reportes descargables: los formatos y los filtros.

Del CSV se verifica el contenido (encabezado y filas), que es lo que se lleva a
un programa de estadística; de Excel y PDF solo que el archivo salga con su tipo
correcto, porque su contenido es binario.
"""
from tests.conftest import ENCUESTA_PAYLOAD

REPORTES_URL = "/api/v1/reportes"
ENCUESTA_URL = "/api/v1/encuesta"


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
