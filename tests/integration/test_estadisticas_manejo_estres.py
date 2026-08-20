from tests.conftest import ENCUESTA_PAYLOAD

ENCUESTA_URL = "/api/v1/encuesta"
ESTADISTICAS_URL = f"{ENCUESTA_URL}/manejo-estres/resultados/estadisticas"


def test_estadisticas_sin_auth(client):
    res = client.get(ESTADISTICAS_URL)
    assert res.status_code == 401


def test_estadisticas_acceso_denegado_sin_rol(client, auth_headers):
    res = client.get(ESTADISTICAS_URL, headers=auth_headers)
    assert res.status_code == 403


def test_estadisticas_sin_encuestas(client, manejo_estres_headers):
    res = client.get(ESTADISTICAS_URL, headers=manejo_estres_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["poblacion_general"]["total"] == 0
    assert data["por_facultad"] == []


def test_estadisticas_con_una_encuesta(client, auth_headers, manejo_estres_headers):
    client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)

    res = client.get(ESTADISTICAS_URL, headers=manejo_estres_headers)
    assert res.status_code == 200
    data = res.json()

    general = data["poblacion_general"]
    assert general["total"] == 1
    assert general["pobre"] + general["moderado"] + general["bueno"] + general["excelente"] == 1

    facultad = data["por_facultad"][0]
    assert facultad["facultad"] == "Ingenieria"
    assert facultad["conteo"]["total"] == 1


def test_estadisticas_ordena_peor_facultad_primero(client, manejo_estres_headers):
    peor = {
        **ENCUESTA_PAYLOAD,
        "facultad": "Facultad Baja",
        **{k: 1 for k in ENCUESTA_PAYLOAD if k.startswith("me_item_")},
    }
    mejor = {
        **ENCUESTA_PAYLOAD,
        "facultad": "Facultad Alta",
        **{k: 4 for k in ENCUESTA_PAYLOAD if k.startswith("me_item_")},
    }

    for payload, correo in [(peor, "baja_me@vitalis.com"), (mejor, "alta_me@vitalis.com")]:
        client.post("/api/v1/auth/register", json={
            "full_name": "Estudiante Test", "email": correo,
            "password": "password123", "confirm_password": "password123",
        })
        login = client.post("/api/v1/auth/login", json={"email": correo, "password": "password123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        client.post(ENCUESTA_URL, json=payload, headers=headers)

    res = client.get(ESTADISTICAS_URL, headers=manejo_estres_headers)
    facultades = res.json()["por_facultad"]
    nombres = [f["facultad"] for f in facultades]
    assert nombres.index("Facultad Baja") < nombres.index("Facultad Alta")
