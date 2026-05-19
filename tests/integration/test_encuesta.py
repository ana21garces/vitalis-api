import pytest
from tests.conftest import ENCUESTA_PAYLOAD

ENCUESTA_URL = "/api/v1/encuesta"


def test_guardar_encuesta_ok(client, auth_headers):
    res = client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert "encuesta_id" in data
    assert "resultados" in data
    r = data["resultados"]
    assert "puntaje_crudo" in r
    assert "indice_global" in r
    assert "nivel_global" in r
    for dim in ["relaciones_interpersonales", "nutricion", "responsabilidad_salud",
                "actividad_fisica", "manejo_estres", "psicologia_positiva"]:
        assert dim in r
        assert "indice" in r[dim]
        assert "nivel" in r[dim]


def test_guardar_encuesta_sin_auth(client):
    res = client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD)
    assert res.status_code == 401


def test_guardar_encuesta_duplicada(client, auth_headers):
    client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)
    res = client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)
    assert res.status_code == 409


def test_guardar_encuesta_respuesta_invalida(client, auth_headers):
    payload_invalido = {**ENCUESTA_PAYLOAD, "ri_item_01": 5}
    res = client.post(ENCUESTA_URL, json=payload_invalido, headers=auth_headers)
    assert res.status_code == 422


def test_estado_no_completada(client, auth_headers):
    res = client.get(f"{ENCUESTA_URL}/estado", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["completada"] is False


def test_estado_completada(client, auth_headers):
    client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)
    res = client.get(f"{ENCUESTA_URL}/estado", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["completada"] is True
    assert "encuesta_id" in data


def test_estado_sin_auth(client):
    res = client.get(f"{ENCUESTA_URL}/estado")
    assert res.status_code == 401


def test_resultado_ok(client, auth_headers):
    client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)
    res = client.get(f"{ENCUESTA_URL}/resultado", headers=auth_headers)
    assert res.status_code == 200
    assert "resultados" in res.json()


def test_resultado_sin_encuesta(client, auth_headers):
    res = client.get(f"{ENCUESTA_URL}/resultado", headers=auth_headers)
    assert res.status_code == 404


def test_historial_ok(client, auth_headers):
    client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)
    res = client.get(f"{ENCUESTA_URL}/historial", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert len(data["encuestas"]) >= 1


def test_historial_sin_encuestas(client, auth_headers):
    res = client.get(f"{ENCUESTA_URL}/historial", headers=auth_headers)
    assert res.status_code == 404


def test_resetear_sin_admin(client, auth_headers):
    r = client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)
    encuesta_id = r.json()["encuesta_id"]
    res = client.patch(f"{ENCUESTA_URL}/{encuesta_id}/resetear", headers=auth_headers)
    assert res.status_code == 403


# ── Tests Capellán: Psicología Positiva ──────────────────────────────────────

CAPELLAN_URL = f"{ENCUESTA_URL}/capellan/psicologia-positiva"


def test_capellan_sin_auth(client):
    res = client.get(CAPELLAN_URL)
    assert res.status_code == 401


def test_capellan_acceso_denegado_sin_rol(client, auth_headers):
    res = client.get(CAPELLAN_URL, headers=auth_headers)
    assert res.status_code == 403


def test_capellan_estructura_respuesta(client, capellan_headers):
    res = client.get(CAPELLAN_URL, headers=capellan_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_estudiantes" in data
    assert "grupos" in data
    assert isinstance(data["grupos"], list)


def test_capellan_con_encuestas(client, auth_headers, capellan_headers):
    client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)
    res = client.get(CAPELLAN_URL, headers=capellan_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_estudiantes"] >= 1
    grupo = data["grupos"][0]
    assert "programa" in grupo
    assert "total" in grupo
    assert "estudiantes" in grupo
    pp = grupo["estudiantes"][0]["psicologia_positiva"]
    for campo in [
        "pp_item_06", "pp_item_12", "pp_item_19", "pp_item_25",
        "pp_item_31", "pp_item_37", "pp_item_44", "pp_item_49", "pp_item_52",
        "pp_indice", "pp_nivel",
    ]:
        assert campo in pp
