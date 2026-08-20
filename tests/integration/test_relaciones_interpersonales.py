from tests.conftest import ENCUESTA_PAYLOAD

ENCUESTA_URL = "/api/v1/encuesta"
RI_URL = f"{ENCUESTA_URL}/relaciones-interpersonales/resultados"
RI_REC_URL = f"{ENCUESTA_URL}/recomendaciones/relaciones-interpersonales"


def test_ri_sin_auth(client):
    res = client.get(RI_URL)
    assert res.status_code == 401


def test_ri_acceso_denegado_sin_rol(client, auth_headers):
    res = client.get(RI_URL, headers=auth_headers)
    assert res.status_code == 403


def test_ri_estructura_respuesta(client, ri_headers):
    res = client.get(RI_URL, headers=ri_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_usuarios" in data
    assert "facultades" in data
    assert isinstance(data["facultades"], list)


def test_ri_con_encuestas(client, auth_headers, ri_headers):
    client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)
    res = client.get(RI_URL, headers=ri_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_usuarios"] >= 1
    facultad = data["facultades"][0]
    assert "facultad" in facultad
    assert "total" in facultad
    carrera = facultad["carreras"][0]
    assert "carrera" in carrera
    assert "total" in carrera
    ri = carrera["usuarios"][0]["relaciones_interpersonales"]
    for campo in [
        "ri_item_01", "ri_item_07", "ri_item_13", "ri_item_20", "ri_item_26",
        "ri_item_32", "ri_item_38", "ri_item_45", "ri_item_50",
        "ri_indice", "ri_nivel",
    ]:
        assert campo in ri


def test_ri_recomendaciones_sin_encuesta(client, auth_headers):
    res = client.get(RI_REC_URL, headers=auth_headers)
    assert res.status_code == 404


def test_ri_recomendaciones_ok(client, auth_headers):
    client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)
    res = client.get(RI_REC_URL, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "ri_nivel" in data
    assert "ri_indice" in data
    assert "total_tarjetas" in data
    assert "tarjetas" in data
    assert isinstance(data["tarjetas"], list)
    if data["tarjetas"]:
        t = data["tarjetas"][0]
        for campo in ["pregunta_num", "pregunta_texto", "nivel", "puntaje", "tecnica", "objetivo", "instrucciones"]:
            assert campo in t


def test_ri_recomendaciones_solo_pobre_moderado(client, auth_headers):
    """Preguntas con puntaje BUENO (3) o EXCELENTE (4) no deben generar tarjeta."""
    client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)
    res = client.get(RI_REC_URL, headers=auth_headers)
    data = res.json()
    for t in data["tarjetas"]:
        assert t["nivel"] in ("POBRE", "MODERADO"), f"Nivel inesperado: {t['nivel']}"


def test_ri_pregunta_50_nunca_genera_tarjeta(client, auth_headers):
    """El objetivo de la técnica de la pregunta 50 no está diligenciado en el
    documento fuente: aunque el puntaje sea POBRE o MODERADO, no debe
    aparecer ninguna tarjeta para esa pregunta."""
    payload = dict(ENCUESTA_PAYLOAD, ri_item_50=1)  # POBRE
    client.post(ENCUESTA_URL, json=payload, headers=auth_headers)
    res = client.get(RI_REC_URL, headers=auth_headers)
    data = res.json()
    numeros = [t["pregunta_num"] for t in data["tarjetas"]]
    assert 50 not in numeros


def test_ri_recomendaciones_sin_auth(client):
    res = client.get(RI_REC_URL)
    assert res.status_code == 401
