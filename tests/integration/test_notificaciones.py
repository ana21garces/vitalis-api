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
    assert data["remitente_nombre"] == "Profesional de Psicología Positiva"
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
    assert res.json()["remitente_nombre"] == "Profesional de Actividad Física"


def test_responsabilidad_salud_notifica_a_un_estudiante(client, resp_salud_headers, auth_headers):
    res = client.post(
        NOTIF_URL,
        json={"destinatario_id": _mi_id(client, auth_headers), "mensaje": "Agenda una cita con responsabilidad en salud."},
        headers=resp_salud_headers,
    )
    assert res.status_code == 201
    assert res.json()["remitente_nombre"] == "Profesional de Responsabilidad en Salud"


def test_relaciones_interpersonales_notifica_a_un_estudiante(client, ri_headers, auth_headers):
    res = client.post(
        NOTIF_URL,
        json={"destinatario_id": _mi_id(client, auth_headers), "mensaje": "Agenda una cita con relaciones interpersonales."},
        headers=ri_headers,
    )
    assert res.status_code == 201
    assert res.json()["remitente_nombre"] == "Profesional de Relaciones Interpersonales"


def test_manejo_estres_notifica_a_un_estudiante(client, manejo_estres_headers, auth_headers):
    res = client.post(
        NOTIF_URL,
        json={"destinatario_id": _mi_id(client, auth_headers), "mensaje": "Agenda una cita con manejo del estrés."},
        headers=manejo_estres_headers,
    )
    assert res.status_code == 201
    assert res.json()["remitente_nombre"] == "Profesional de Manejo del Estrés"


def test_nutricion_notifica_a_un_estudiante(client, n_headers, auth_headers):
    res = client.post(
        NOTIF_URL,
        json={"destinatario_id": _mi_id(client, auth_headers), "mensaje": "Agenda una cita con nutrición."},
        headers=n_headers,
    )
    assert res.status_code == 201
    assert res.json()["remitente_nombre"] == "Profesional de Nutrición"


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


def _crear_invitacion(client, capellan_headers, auth_headers):
    return client.post(
        NOTIF_URL,
        json={"destinatario_id": _mi_id(client, auth_headers), "mensaje": "Agenda una cita"},
        headers=capellan_headers,
    ).json()


def test_estudiante_acepta_invitacion_y_avisa_al_rol(client, capellan_headers, auth_headers):
    creada = _crear_invitacion(client, capellan_headers, auth_headers)

    lista = client.get(NOTIF_URL, headers=auth_headers).json()
    invitacion = next(n for n in lista if n["id"] == creada["id"])
    assert invitacion["puede_responder"] is True

    res = client.post(f"{NOTIF_URL}/{creada['id']}/responder", json={"acepta": True}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["respuesta"] == "aceptada"
    assert res.json()["puede_responder"] is False

    del_capellan = client.get(NOTIF_URL, headers=capellan_headers).json()
    avisos = [n for n in del_capellan if "Aceptó la invitación" in n["mensaje"]]
    assert len(avisos) == 1
    assert avisos[0]["tipo"] == "cita_aceptada"
    assert avisos[0]["enlace"].startswith("/dashboard/capellan?alerta=")


def test_estudiante_rechaza_y_permite_reinvitar(client, capellan_headers, auth_headers):
    creada = _crear_invitacion(client, capellan_headers, auth_headers)

    res = client.post(f"{NOTIF_URL}/{creada['id']}/responder", json={"acepta": False}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["respuesta"] == "rechazada"

    del_capellan = client.get(NOTIF_URL, headers=capellan_headers).json()
    avisos = [n for n in del_capellan if "Rechazó la invitación" in n["mensaje"]]
    assert len(avisos) == 1
    assert avisos[0]["tipo"] == "cita_rechazada"
    assert avisos[0]["enlace"].startswith("/dashboard/capellan?alerta=")


def test_no_se_puede_responder_dos_veces(client, capellan_headers, auth_headers):
    creada = _crear_invitacion(client, capellan_headers, auth_headers)
    client.post(f"{NOTIF_URL}/{creada['id']}/responder", json={"acepta": False}, headers=auth_headers)
    res = client.post(f"{NOTIF_URL}/{creada['id']}/responder", json={"acepta": True}, headers=auth_headers)
    assert res.status_code == 409


def test_otro_no_puede_responder_invitacion_ajena(client, capellan_headers, auth_headers, act_fisica_headers):
    creada = _crear_invitacion(client, capellan_headers, auth_headers)
    res = client.post(f"{NOTIF_URL}/{creada['id']}/responder", json={"acepta": True}, headers=act_fisica_headers)
    assert res.status_code == 404


def _estado_invitacion(client, headers, rol, est_id):
    return client.get(f"{NOTIF_URL}/notificados?rol={rol}", headers=headers).json().get(est_id)


def test_estado_de_la_invitacion_segun_la_respuesta(client, capellan_headers, auth_headers):
    """La vista necesita distinguir a quien no ha contestado de quien rechazó."""
    creada = _crear_invitacion(client, capellan_headers, auth_headers)
    est_id = _mi_id(client, auth_headers)
    assert _estado_invitacion(client, capellan_headers, "capellan", est_id) == "pendiente"

    client.post(f"{NOTIF_URL}/{creada['id']}/responder", json={"acepta": False}, headers=auth_headers)
    assert _estado_invitacion(client, capellan_headers, "capellan", est_id) == "rechazada"


def test_se_puede_volver_a_invitar_a_quien_rechazo(client, capellan_headers, auth_headers):
    """Tras un rechazo, una invitación nueva deja el estado en pendiente otra vez
    y el estudiante puede volver a responder."""
    primera = _crear_invitacion(client, capellan_headers, auth_headers)
    est_id = _mi_id(client, auth_headers)
    client.post(f"{NOTIF_URL}/{primera['id']}/responder", json={"acepta": False}, headers=auth_headers)

    segunda = _crear_invitacion(client, capellan_headers, auth_headers)
    assert _estado_invitacion(client, capellan_headers, "capellan", est_id) == "pendiente"

    acepta = client.post(
        f"{NOTIF_URL}/{segunda['id']}/responder", json={"acepta": True}, headers=auth_headers
    )
    assert acepta.status_code == 200
    assert _estado_invitacion(client, capellan_headers, "capellan", est_id) == "aceptada"


def test_lista_de_notificados_persiste(client, capellan_headers, auth_headers, admin_headers):
    _crear_invitacion(client, capellan_headers, auth_headers)
    est_id = _mi_id(client, auth_headers)

    # El profesional del rol ve al estudiante como ya notificado.
    propia = client.get(f"{NOTIF_URL}/notificados?rol=capellan", headers=capellan_headers)
    assert propia.status_code == 200
    assert est_id in propia.json()

    # El admin también puede consultarlo (entra a esa vista).
    del_admin = client.get(f"{NOTIF_URL}/notificados?rol=capellan", headers=admin_headers)
    assert del_admin.status_code == 200
    assert est_id in del_admin.json()

    # Un profesional de otra dimensión no puede consultar un rol ajeno.
    ajeno = client.get(f"{NOTIF_URL}/notificados?rol=nutricion", headers=capellan_headers)
    assert ajeno.status_code == 403
