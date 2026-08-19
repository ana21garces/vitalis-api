NOTIF_URL = "/api/v1/notificaciones"


def _mi_id(client, headers) -> str:
    return client.get("/api/v1/users/me", headers=headers).json()["id"]


def test_capellan_notifica_a_un_estudiante(client, capellan_headers, auth_headers):
    res = client.post(
        NOTIF_URL,
        json={"destinatario_id": _mi_id(client, auth_headers), "mensaje": "Te invitamos a agendar una cita."},
        headers=capellan_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["mensaje"] == "Te invitamos a agendar una cita."
    assert data["remitente_nombre"] == "Capellan Test"
    assert data["leida"] is False


def test_estudiante_ve_su_notificacion(client, capellan_headers, auth_headers):
    client.post(
        NOTIF_URL,
        json={"destinatario_id": _mi_id(client, auth_headers), "mensaje": "Agenda una cita"},
        headers=capellan_headers,
    )
    res = client.get(NOTIF_URL, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["mensaje"] == "Agenda una cita"


def test_estudiante_no_puede_notificar(client, auth_headers):
    """Solo los roles profesionales con vista de resultados pueden notificar."""
    res = client.post(
        NOTIF_URL,
        json={"destinatario_id": "00000000-0000-0000-0000-000000000000", "mensaje": "hola"},
        headers=auth_headers,
    )
    assert res.status_code == 403


def test_actividad_fisica_notifica_a_un_estudiante(client, act_fisica_headers, auth_headers):
    res = client.post(
        NOTIF_URL,
        json={"destinatario_id": _mi_id(client, auth_headers), "mensaje": "Agenda una cita con actividad física."},
        headers=act_fisica_headers,
    )
    assert res.status_code == 201
    assert res.json()["remitente_nombre"] == "Act Fisica Test"


def test_responsabilidad_salud_notifica_a_un_estudiante(client, resp_salud_headers, auth_headers):
    res = client.post(
        NOTIF_URL,
        json={"destinatario_id": _mi_id(client, auth_headers), "mensaje": "Agenda una cita con responsabilidad en salud."},
        headers=resp_salud_headers,
    )
    assert res.status_code == 201
    assert res.json()["remitente_nombre"] == "Resp Salud Test"


def test_relaciones_interpersonales_notifica_a_un_estudiante(client, ri_headers, auth_headers):
    res = client.post(
        NOTIF_URL,
        json={"destinatario_id": _mi_id(client, auth_headers), "mensaje": "Agenda una cita con relaciones interpersonales."},
        headers=ri_headers,
    )
    assert res.status_code == 201
    assert res.json()["remitente_nombre"] == "Relaciones Interpersonales Test"


def test_no_se_puede_notificar_a_un_profesional(client, capellan_headers, act_fisica_headers):
    """La notificación es para invitar a la población encuestable, no a colegas."""
    destinatario_id = _mi_id(client, act_fisica_headers)
    res = client.post(
        NOTIF_URL,
        json={"destinatario_id": destinatario_id, "mensaje": "hola"},
        headers=capellan_headers,
    )
    assert res.status_code == 422


def test_notificar_a_usuario_inexistente(client, capellan_headers):
    res = client.post(
        NOTIF_URL,
        json={"destinatario_id": "00000000-0000-0000-0000-000000000000", "mensaje": "hola"},
        headers=capellan_headers,
    )
    assert res.status_code == 404


def test_mensaje_vacio_rechazado(client, capellan_headers, auth_headers):
    res = client.post(
        NOTIF_URL,
        json={"destinatario_id": _mi_id(client, auth_headers), "mensaje": "   "},
        headers=capellan_headers,
    )
    assert res.status_code == 422


def test_marcar_como_leida(client, capellan_headers, auth_headers):
    creada = client.post(
        NOTIF_URL,
        json={"destinatario_id": _mi_id(client, auth_headers), "mensaje": "hola"},
        headers=capellan_headers,
    ).json()

    res = client.patch(f"{NOTIF_URL}/{creada['id']}/leida", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["leida"] is True


def test_no_se_puede_marcar_leida_la_de_otro(client, capellan_headers, auth_headers, act_fisica_headers):
    creada = client.post(
        NOTIF_URL,
        json={"destinatario_id": _mi_id(client, auth_headers), "mensaje": "hola"},
        headers=capellan_headers,
    ).json()

    res = client.patch(f"{NOTIF_URL}/{creada['id']}/leida", headers=act_fisica_headers)
    assert res.status_code == 404
