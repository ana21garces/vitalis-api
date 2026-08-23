from tests.conftest import ENCUESTA_PAYLOAD

ENCUESTA_URL = "/api/v1/encuesta"
SEG_URL = "/api/v1/seguimiento-recomendaciones"


def test_tarjetas_sin_encuesta(client, auth_headers):
    res = client.get(f"{SEG_URL}/actividad-fisica/tarjetas", headers=auth_headers)
    assert res.status_code == 404


def test_dimension_invalida(client, auth_headers):
    client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)
    res = client.get(f"{SEG_URL}/inventada/tarjetas", headers=auth_headers)
    assert res.status_code == 422


def test_flujo_completo_registrar_dia_y_completar(client, auth_headers, act_fisica_headers):
    client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)

    res = client.get(f"{SEG_URL}/actividad-fisica/tarjetas", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["dimension"] == "actividad_fisica"
    assert data["total"] > 0
    primera = data["tarjetas"][0]
    for campo in ["pregunta_num", "pregunta_texto", "nivel", "puntaje", "tecnica", "objetivo", "instrucciones"]:
        assert campo in primera["tarjeta"]
    seguimiento_id = primera["seguimiento"]["id"]
    assert primera["seguimiento"]["estado"] == "en_progreso"
    assert primera["seguimiento"]["racha_actual"] == 0

    res = client.post(
        f"{SEG_URL}/{seguimiento_id}/registrar-dia",
        json={"notas": "hoy hice la caminata"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["seguimiento"]["racha_actual"] == 1
    assert body["registro"]["notas"] == "hoy hice la caminata"

    # Mismo día no se puede registrar de nuevo.
    res = client.post(f"{SEG_URL}/{seguimiento_id}/registrar-dia", json={}, headers=auth_headers)
    assert res.status_code == 400

    res = client.get(f"{SEG_URL}/{seguimiento_id}/historial", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) == 1

    res = client.post(f"{SEG_URL}/{seguimiento_id}/completar", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["estado"] == "completada"

    # No se puede completar dos veces.
    res = client.post(f"{SEG_URL}/{seguimiento_id}/completar", headers=auth_headers)
    assert res.status_code == 400

    res = client.get(f"{SEG_URL}/progreso", headers=auth_headers)
    assert res.status_code == 200
    af = next(d for d in res.json()["dimensiones"] if d["dimension"] == "actividad_fisica")
    assert af["completadas"] == 1

    # El profesional de actividad física recibió la notificación de avance.
    res = client.get("/api/v1/notificaciones", headers=act_fisica_headers)
    assert res.status_code == 200
    mensajes = [n["mensaje"] for n in res.json()]
    assert any("Estudiante" in m or "Test User" in m for m in mensajes)


def test_progreso_sin_encuesta(client, auth_headers):
    res = client.get(f"{SEG_URL}/progreso", headers=auth_headers)
    assert res.status_code == 404


def test_sin_auth(client):
    res = client.get(f"{SEG_URL}/actividad-fisica/tarjetas")
    assert res.status_code == 401
