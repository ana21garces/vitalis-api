def test_estudiante_recibe_mensaje_del_asistente(client, auth_headers):
    res = client.get("/api/v1/asistente/mensaje", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["mensaje"].strip() != ""
    assert isinstance(data["pendientes"], int)
    assert isinstance(data["todo_hecho"], bool)


def test_saludo_se_cachea_una_vez_al_dia(client, auth_headers, monkeypatch):
    import app.services.asistente_service as svc

    llamadas = {"n": 0}

    def fake_gen(datos, nombre):
        llamadas["n"] += 1
        return f"Saludo IA para {nombre}"

    monkeypatch.setattr(svc, "_generar_con_gemini", fake_gen)

    r1 = client.get("/api/v1/asistente/mensaje", headers=auth_headers)
    r2 = client.get("/api/v1/asistente/mensaje", headers=auth_headers)

    assert r1.json()["mensaje"].startswith("Saludo IA")
    assert r2.json()["mensaje"] == r1.json()["mensaje"]
    assert llamadas["n"] == 1


def test_no_estudiante_recibe_mensaje_vacio(client, capellan_headers):
    res = client.get("/api/v1/asistente/mensaje", headers=capellan_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["mensaje"] == ""
    assert data["pendientes"] == 0
    assert data["todo_hecho"] is True
