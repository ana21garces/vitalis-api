def test_estudiante_recibe_mensaje_del_asistente(client, auth_headers):
    res = client.get("/api/v1/asistente/mensaje", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["mensaje"].strip() != ""
    assert isinstance(data["pendientes"], int)
    assert isinstance(data["todo_hecho"], bool)


def test_no_estudiante_recibe_mensaje_vacio(client, capellan_headers):
    res = client.get("/api/v1/asistente/mensaje", headers=capellan_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["mensaje"] == ""
    assert data["pendientes"] == 0
    assert data["todo_hecho"] is True
