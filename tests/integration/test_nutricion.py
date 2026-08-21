from tests.conftest import ENCUESTA_PAYLOAD

ENCUESTA_URL = "/api/v1/encuesta"
N_URL = f"{ENCUESTA_URL}/nutricion/resultados"
N_REC_URL = f"{ENCUESTA_URL}/recomendaciones/nutricion"


def test_n_sin_auth(client):
    res = client.get(N_URL)
    assert res.status_code == 401


def test_n_acceso_denegado_sin_rol(client, auth_headers):
    res = client.get(N_URL, headers=auth_headers)
    assert res.status_code == 403


def test_n_estructura_respuesta(client, n_headers):
    res = client.get(N_URL, headers=n_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_usuarios" in data
    assert "facultades" in data
    assert isinstance(data["facultades"], list)


def test_n_con_encuestas(client, auth_headers, n_headers):
    client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)
    res = client.get(N_URL, headers=n_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_usuarios"] >= 1
    facultad = data["facultades"][0]
    assert "facultad" in facultad
    assert "total" in facultad
    carrera = facultad["carreras"][0]
    assert "carrera" in carrera
    assert "total" in carrera
    n = carrera["usuarios"][0]["nutricion"]
    for campo in [
        "n_item_02", "n_item_08", "n_item_14", "n_item_21", "n_item_27",
        "n_item_33", "n_item_39", "n_item_40", "n_item_46", "n_item_51",
        "n_indice", "n_nivel",
    ]:
        assert campo in n


def test_n_recomendaciones_sin_encuesta(client, auth_headers):
    res = client.get(N_REC_URL, headers=auth_headers)
    assert res.status_code == 404


def test_n_recomendaciones_ok(client, auth_headers):
    client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)
    res = client.get(N_REC_URL, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "n_nivel" in data
    assert "n_indice" in data
    assert "total_tarjetas" in data
    assert "tarjetas" in data
    assert isinstance(data["tarjetas"], list)
    if data["tarjetas"]:
        t = data["tarjetas"][0]
        for campo in ["pregunta_num", "pregunta_texto", "nivel", "puntaje", "tecnica", "objetivo", "instrucciones"]:
            assert campo in t


def test_n_recomendaciones_solo_pobre_moderado(client, auth_headers):
    """Preguntas con puntaje BUENO (3) o EXCELENTE (4) no deben generar tarjeta."""
    client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)
    res = client.get(N_REC_URL, headers=auth_headers)
    data = res.json()
    for t in data["tarjetas"]:
        assert t["nivel"] in ("POBRE", "MODERADO"), f"Nivel inesperado: {t['nivel']}"


def test_n_recomendaciones_sin_auth(client):
    res = client.get(N_REC_URL)
    assert res.status_code == 401
