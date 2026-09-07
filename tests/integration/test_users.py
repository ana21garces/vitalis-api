from tests.conftest import ENCUESTA_PAYLOAD

ME_URL = "/api/v1/users/me"
USERS_URL = "/api/v1/users"
ENCUESTA_URL = "/api/v1/encuesta"
SEG_URL = "/api/v1/seguimiento-recomendaciones"


def test_me_devuelve_el_perfil(client, auth_headers, registered_user):
    res = client.get(ME_URL, headers=auth_headers)
    assert res.status_code == 200

    data = res.json()
    assert data["email"] == registered_user["email"]
    assert data["full_name"] == registered_user["full_name"]
    assert data["role"] == "student"
    assert data["is_active"] is True


def test_me_sin_token(client):
    res = client.get(ME_URL)
    assert res.status_code == 401


def test_me_token_invalido(client):
    res = client.get(ME_URL, headers={"Authorization": "Bearer no.es.un.jwt"})
    assert res.status_code == 401


def test_me_no_expone_la_contrasena(client, auth_headers):
    """El perfil sale por UserResponse, que no incluye el hash. Vale la pena
    fijarlo con un test: añadir un campo al schema es fácil de hacer sin
    pensar."""
    data = client.get(ME_URL, headers=auth_headers).json()
    assert "password_hash" not in data
    assert "password" not in data


def test_me_incluye_el_perfil_academico(client, auth_headers):
    """Facultad, programa y tipo de usuario llegan vacíos hasta que se
    responde la encuesta, pero el contrato tiene que exponerlos: son lo que
    el frontend necesita para mostrar el perfil."""
    data = client.get(ME_URL, headers=auth_headers).json()
    for campo in ("facultad", "program", "tipo_usuario", "university"):
        assert campo in data


def test_cambiar_correo_exige_la_contrasena_actual(client, auth_headers, registered_user):
    """Cambiar solo el nombre no pide contraseña; cambiar el correo (el
    identificador de acceso) sí, y tiene que ser la correcta."""
    solo_nombre = {"full_name": "Nombre Cambiado", "email": registered_user["email"]}
    assert client.patch(ME_URL, json=solo_nombre, headers=auth_headers).status_code == 200

    nuevo_correo = {"full_name": "Nombre Cambiado", "email": "cambiado@vitalis.com"}
    assert client.patch(ME_URL, json=nuevo_correo, headers=auth_headers).status_code == 400
    assert client.patch(
        ME_URL, json={**nuevo_correo, "current_password": "incorrecta"}, headers=auth_headers
    ).status_code == 400

    ok = client.patch(
        ME_URL,
        json={**nuevo_correo, "current_password": registered_user["password"]},
        headers=auth_headers,
    )
    assert ok.status_code == 200
    assert ok.json()["email"] == "cambiado@vitalis.com"


def test_eliminar_estudiante_con_datos_de_gamificacion_y_seguimiento(
    client, auth_headers, admin_headers, registered_user
):
    """Un estudiante que ya respondió la encuesta y registró un seguimiento
    tiene filas en encuestas_hplp, xp_eventos, seguimientos_recomendacion,
    registros_diarios_seguimiento y sesiones. Borrarlo no debe romper por las
    llaves foráneas: tiene que responder 204 y desaparecer."""
    client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=auth_headers)
    tarjetas = client.get(
        f"{SEG_URL}/actividad-fisica/tarjetas", headers=auth_headers
    ).json()
    seg_id = tarjetas["tarjetas"][0]["seguimiento"]["id"]
    assert client.post(
        f"{SEG_URL}/{seg_id}/registrar-dia", json={}, headers=auth_headers
    ).status_code == 200

    lista = client.get(USERS_URL, headers=admin_headers).json()
    uid = next(u["id"] for u in lista if u["email"] == registered_user["email"])

    assert client.delete(f"{USERS_URL}/{uid}", headers=admin_headers).status_code == 204

    restantes = client.get(USERS_URL, headers=admin_headers).json()
    assert all(u["email"] != registered_user["email"] for u in restantes)


# ── Completar datos demográficos ──────────────────────────────────────────

DEMOGRAFICOS_URL = f"{ME_URL}/datos-demograficos"


def test_completar_datos_demograficos_persiste(client, auth_headers):
    antes = client.get(ME_URL, headers=auth_headers).json()
    assert antes["tipo_usuario"] is None
    assert antes["facultad"] is None

    res = client.patch(
        DEMOGRAFICOS_URL,
        headers=auth_headers,
        json={
            "tipo_usuario": "estudiante",
            "sexo": "femenino",
            "facultad": "Ingeniería",
            "program": "Ingeniería de Sistemas",
        },
    )
    assert res.status_code == 200

    despues = client.get(ME_URL, headers=auth_headers).json()
    assert despues["tipo_usuario"] == "estudiante"
    assert despues["sexo"] == "femenino"
    assert despues["facultad"] == "Ingeniería"
    assert despues["program"] == "Ingeniería de Sistemas"


def test_completar_datos_demograficos_no_borra_lo_que_ya_estaba(client, auth_headers):
    client.patch(
        DEMOGRAFICOS_URL,
        headers=auth_headers,
        json={"tipo_usuario": "docente", "facultad": "Teología"},
    )

    client.patch(DEMOGRAFICOS_URL, headers=auth_headers, json={"sexo": "masculino"})

    data = client.get(ME_URL, headers=auth_headers).json()
    assert data["tipo_usuario"] == "docente"
    assert data["facultad"] == "Teología"
    assert data["sexo"] == "masculino"
