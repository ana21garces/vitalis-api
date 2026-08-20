from tests.conftest import ENCUESTA_PAYLOAD

ENCUESTA_URL = "/api/v1/encuesta"
ME_URL = f"{ENCUESTA_URL}/manejo-estres/resultados"
ME_REC_URL = f"{ENCUESTA_URL}/recomendaciones/manejo-estres"


def test_me_sin_auth(client):
    res = client.get(ME_URL)
    assert res.status_code == 401


def test_me_acceso_denegado_sin_rol(client, auth_headers):
    res = client.get(ME_URL, headers=auth_headers)
    assert res.status_code == 403


def test_me_estructura_respuesta(client, manejo_estres_headers):
    res = client.get(ME_URL, headers=manejo_estres_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_usuarios" in data
    assert "facultades" in data
    assert isinstance(data["facultades"], list)


def test_me_con_encuestas(client, auth_headers, manejo_estres_headers):
    client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)
    res = client.get(ME_URL, headers=manejo_estres_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_usuarios"] >= 1
    facultad = data["facultades"][0]
    assert "facultad" in facultad
    assert "total" in facultad
    carrera = facultad["carreras"][0]
    assert "carrera" in carrera
    assert "total" in carrera
    me = carrera["usuarios"][0]["manejo_estres"]
    for campo in [
        "me_item_05", "me_item_11", "me_item_18", "me_item_24",
        "me_item_30", "me_item_36", "me_item_43", "me_item_48",
        "me_indice", "me_nivel",
    ]:
        assert campo in me


def test_me_recomendaciones_sin_encuesta(client, auth_headers):
    res = client.get(ME_REC_URL, headers=auth_headers)
    assert res.status_code == 404


def test_me_recomendaciones_ok(client, auth_headers):
    client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)
    res = client.get(ME_REC_URL, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "me_nivel" in data
    assert "me_indice" in data
    assert "total_tarjetas" in data
    assert "tarjetas" in data
    assert isinstance(data["tarjetas"], list)
    if data["tarjetas"]:
        t = data["tarjetas"][0]
        for campo in ["pregunta_num", "pregunta_texto", "nivel", "puntaje", "tecnica", "objetivo", "instrucciones"]:
            assert campo in t


def test_me_recomendaciones_solo_pobre_moderado(client, auth_headers):
    """Preguntas con puntaje BUENO (3) o EXCELENTE (4) no deben generar tarjeta."""
    client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)
    res = client.get(ME_REC_URL, headers=auth_headers)
    data = res.json()
    for t in data["tarjetas"]:
        assert t["nivel"] in ("POBRE", "MODERADO"), f"Nivel inesperado: {t['nivel']}"


def test_me_recomendaciones_incluye_nota_de_nivel(client, auth_headers):
    """La guía distingue el alcance por nivel (Pobre/Moderado) dentro de la
    misma técnica; esa nota debe llegar como el último paso de instrucciones."""
    client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)
    res = client.get(ME_REC_URL, headers=auth_headers)
    data = res.json()
    for t in data["tarjetas"]:
        ultima = t["instrucciones"][-1]
        assert ultima.startswith(f"Para tu nivel ({t['nivel'].capitalize()})")


def test_me_recomendaciones_sin_auth(client):
    res = client.get(ME_REC_URL)
    assert res.status_code == 401
