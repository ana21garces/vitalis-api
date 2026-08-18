ME_URL = "/api/v1/users/me"


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
