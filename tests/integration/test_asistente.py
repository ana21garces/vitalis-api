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


def test_el_plan_trae_el_avance_del_seguimiento(client, auth_headers):
    """El asistente no puede quedarse en los nombres de las dimensiones: cada
    una viene con cuántas recomendaciones lleva completadas de cuántas."""
    from tests.conftest import ENCUESTA_PAYLOAD

    client.post("/api/v1/encuesta", json=ENCUESTA_PAYLOAD, headers=auth_headers)

    plan = client.get("/api/v1/asistente/mensaje", headers=auth_headers).json()["plan"]
    assert plan
    for dimension in plan:
        assert dimension["label"]
        assert dimension["total"] > 0
        assert dimension["completadas"] <= dimension["total"]


def test_el_plan_va_en_el_mismo_orden_que_el_dashboard(client, auth_headers):
    """De peor a mejor índice, igual que "Dimensiones prioritarias": si el orden
    difiere entre las dos vistas la persona se pierde."""
    from tests.conftest import ENCUESTA_PAYLOAD

    payload = {
        k: (1 if k.startswith("n_item_") else 2) if "_item_" in k else v
        for k, v in ENCUESTA_PAYLOAD.items()
    }
    client.post("/api/v1/encuesta", json=payload, headers=auth_headers)

    plan = client.get("/api/v1/asistente/mensaje", headers=auth_headers).json()["plan"]
    assert plan[0]["label"] == "Nutrición"
    assert [d["label"] for d in plan[1:]] == [
        "Responsabilidad en salud",
        "Psicología positiva",
        "Actividad física",
        "Relaciones interpersonales",
        "Manejo del estrés",
    ]


def test_el_plan_cuenta_lo_registrado_hoy(client, auth_headers):
    """El registro del día tiene que verse en el asistente: la persona marca
    "lo hice hoy" y la barra se mueve, sin esperar a completar nada."""
    from tests.conftest import ENCUESTA_PAYLOAD

    client.post("/api/v1/encuesta", json=ENCUESTA_PAYLOAD, headers=auth_headers)
    plan = client.get("/api/v1/asistente/mensaje", headers=auth_headers).json()["plan"]
    dimension = plan[0]["dimension"]
    assert plan[0]["registradas_hoy"] == 0

    tarjetas = client.get(
        f"/api/v1/seguimiento-recomendaciones/{dimension.replace('_', '-')}/tarjetas",
        headers=auth_headers,
    ).json()
    seguimiento_id = tarjetas["tarjetas"][0]["seguimiento"]["id"]
    client.post(
        f"/api/v1/seguimiento-recomendaciones/{seguimiento_id}/registrar-dia",
        json={},
        headers=auth_headers,
    )

    despues = client.get("/api/v1/asistente/mensaje", headers=auth_headers).json()["plan"]
    registradas = {d["dimension"]: d["registradas_hoy"] for d in despues}
    assert registradas[dimension] == 1


def test_el_plan_refleja_una_recomendacion_completada(client, auth_headers):
    from tests.conftest import ENCUESTA_PAYLOAD

    client.post("/api/v1/encuesta", json=ENCUESTA_PAYLOAD, headers=auth_headers)
    antes = client.get("/api/v1/asistente/mensaje", headers=auth_headers).json()["plan"]

    dimension = antes[0]["dimension"]
    tarjetas = client.get(
        f"/api/v1/seguimiento-recomendaciones/{dimension.replace('_', '-')}/tarjetas",
        headers=auth_headers,
    ).json()
    seguimiento_id = tarjetas["tarjetas"][0]["seguimiento"]["id"]
    client.post(
        f"/api/v1/seguimiento-recomendaciones/{seguimiento_id}/registrar-dia",
        json={},
        headers=auth_headers,
    )
    client.post(
        f"/api/v1/seguimiento-recomendaciones/{seguimiento_id}/completar", headers=auth_headers
    )

    despues = client.get("/api/v1/asistente/mensaje", headers=auth_headers).json()["plan"]
    avance = {d["dimension"]: d["completadas"] for d in despues}
    assert avance[dimension] == 1


def test_no_estudiante_recibe_mensaje_vacio(client, capellan_headers):
    res = client.get("/api/v1/asistente/mensaje", headers=capellan_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["mensaje"] == ""
    assert data["pendientes"] == 0
    assert data["todo_hecho"] is True
