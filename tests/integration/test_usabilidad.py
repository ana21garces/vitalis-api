RESPUESTAS_OK = [7, 6, 7, 6, 7, 6, 5, 5, 5, 5, 5, 5, 6, 7, 6, 7]


def test_flujo_responder_usabilidad(client, auth_headers):
    inicial = client.get("/api/v1/usabilidad/estado", headers=auth_headers)
    assert inicial.status_code == 200
    assert inicial.json()["respondida"] is False

    envio = client.post(
        "/api/v1/usabilidad", json={"respuestas": RESPUESTAS_OK}, headers=auth_headers
    )
    assert envio.status_code == 201
    data = envio.json()
    assert data["sysuse"] == round(sum(RESPUESTAS_OK[0:6]) / 6, 2)
    assert data["infoqual"] == round(sum(RESPUESTAS_OK[6:12]) / 6, 2)
    assert data["interqual"] == round(sum(RESPUESTAS_OK[12:15]) / 3, 2)
    assert data["puntaje_global"] == round(sum(RESPUESTAS_OK) / 16, 2)

    despues = client.get("/api/v1/usabilidad/estado", headers=auth_headers)
    assert despues.json()["respondida"] is True

    duplicado = client.post(
        "/api/v1/usabilidad", json={"respuestas": RESPUESTAS_OK}, headers=auth_headers
    )
    assert duplicado.status_code == 409


def test_usabilidad_valida_cantidad_de_respuestas(client, auth_headers):
    r = client.post(
        "/api/v1/usabilidad", json={"respuestas": [7, 7, 7]}, headers=auth_headers
    )
    assert r.status_code == 422


def test_usabilidad_valida_rango(client, auth_headers):
    fuera = [9] + [5] * 15
    r = client.post("/api/v1/usabilidad", json={"respuestas": fuera}, headers=auth_headers)
    assert r.status_code == 422


def test_campana_hace_obligatoria_la_encuesta(client, auth_headers, admin_headers):
    def requerida(headers):
        return client.get("/api/v1/usabilidad/estado", headers=headers).json()["requerida"]

    assert requerida(auth_headers) is False

    activar = client.put("/api/v1/usabilidad/campana", json={"activa": True}, headers=admin_headers)
    assert activar.status_code == 200
    assert activar.json()["abierta"] is True

    assert requerida(auth_headers) is True
    assert requerida(admin_headers) is False  # el admin no queda bloqueado

    client.post("/api/v1/usabilidad", json={"respuestas": RESPUESTAS_OK}, headers=auth_headers)
    assert requerida(auth_headers) is False


def test_admin_responde_una_vez_por_area(client, admin_headers):
    client.put("/api/v1/usabilidad/campana", json={"activa": True}, headers=admin_headers)

    r1 = client.post(
        "/api/v1/usabilidad", json={"respuestas": RESPUESTAS_OK, "rol": "capellan"}, headers=admin_headers
    )
    assert r1.status_code == 201

    cap = client.get("/api/v1/usabilidad/estado?rol=capellan", headers=admin_headers).json()
    assert cap["respondida"] is True
    nut = client.get("/api/v1/usabilidad/estado?rol=nutricion", headers=admin_headers).json()
    assert nut["respondida"] is False

    r2 = client.post(
        "/api/v1/usabilidad", json={"respuestas": RESPUESTAS_OK, "rol": "nutricion"}, headers=admin_headers
    )
    assert r2.status_code == 201

    repetido = client.post(
        "/api/v1/usabilidad", json={"respuestas": RESPUESTAS_OK, "rol": "capellan"}, headers=admin_headers
    )
    assert repetido.status_code == 409


def test_reporte_detalle_de_usabilidad(client, auth_headers, admin_headers):
    client.post("/api/v1/usabilidad", json={"respuestas": RESPUESTAS_OK}, headers=auth_headers)
    r = client.get("/api/v1/reportes/usabilidad_detalle?formato=csv", headers=admin_headers)
    assert r.status_code == 200


def test_campana_rechaza_rango_invertido(client, admin_headers):
    r = client.put(
        "/api/v1/usabilidad/campana",
        json={"activa": True, "fecha_inicio": "2026-10-10", "fecha_fin": "2026-10-01"},
        headers=admin_headers,
    )
    assert r.status_code == 422


def test_solo_admin_maneja_la_campana(client, auth_headers):
    assert client.get("/api/v1/usabilidad/campana", headers=auth_headers).status_code in (401, 403)
    assert (
        client.put("/api/v1/usabilidad/campana", json={"activa": True}, headers=auth_headers).status_code
        in (401, 403)
    )
