import pytest


REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
ESTADO_URL = "/api/v1/encuesta/estado"

VALID_USER = {
    "full_name": "Ana Garcia",
    "email": "ana@vitalis.com",
    "password": "segura123",
    "confirm_password": "segura123",
}


def test_register_ok(client):
    res = client.post(REGISTER_URL, json=VALID_USER)
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == VALID_USER["email"]
    assert "id" in data


def test_register_email_duplicado(client):
    client.post(REGISTER_URL, json=VALID_USER)
    res = client.post(REGISTER_URL, json=VALID_USER)
    assert res.status_code == 409


def test_register_contrasenas_no_coinciden(client):
    payload = {**VALID_USER, "email": "otro@vitalis.com", "confirm_password": "diferente"}
    res = client.post(REGISTER_URL, json=payload)
    assert res.status_code == 422


def test_register_contrasena_corta(client):
    payload = {**VALID_USER, "email": "corta@vitalis.com", "password": "123", "confirm_password": "123"}
    res = client.post(REGISTER_URL, json=payload)
    assert res.status_code == 422


def test_register_nombre_muy_corto(client):
    payload = {**VALID_USER, "email": "x@vitalis.com", "full_name": "A"}
    res = client.post(REGISTER_URL, json=payload)
    assert res.status_code == 422


def test_register_email_invalido(client):
    payload = {**VALID_USER, "email": "no-es-un-email"}
    res = client.post(REGISTER_URL, json=payload)
    assert res.status_code == 422


def test_login_ok(client):
    client.post(REGISTER_URL, json=VALID_USER)
    res = client.post(LOGIN_URL, json={"email": VALID_USER["email"], "password": VALID_USER["password"]})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_contrasena_incorrecta(client):
    client.post(REGISTER_URL, json=VALID_USER)
    res = client.post(LOGIN_URL, json={"email": VALID_USER["email"], "password": "incorrecta"})
    assert res.status_code == 401


def test_login_usuario_no_existe(client):
    res = client.post(LOGIN_URL, json={"email": "noexiste@vitalis.com", "password": "cualquiera"})
    assert res.status_code == 401


def _tokens(client):
    """Registra al usuario de prueba e inicia sesion. Devuelve los dos tokens."""
    client.post(REGISTER_URL, json=VALID_USER)
    res = client.post(LOGIN_URL, json={
        "email": VALID_USER["email"],
        "password": VALID_USER["password"],
    })
    return res.json()


def test_refresh_devuelve_access_token_nuevo(client):
    tokens = _tokens(client)
    res = client.post(REFRESH_URL, json={"refresh_token": tokens["refresh_token"]})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_refresh_el_access_token_nuevo_sirve(client):
    tokens = _tokens(client)
    nuevo = client.post(REFRESH_URL, json={"refresh_token": tokens["refresh_token"]})
    access = nuevo.json()["access_token"]

    res = client.get(ESTADO_URL, headers={"Authorization": f"Bearer {access}"})
    assert res.status_code == 200


def test_refresh_no_renueva_el_refresh_token(client):
    """El limite de dias es absoluto: encadenar renovaciones no lo estira."""
    tokens = _tokens(client)
    res = client.post(REFRESH_URL, json={"refresh_token": tokens["refresh_token"]})
    assert res.json()["refresh_token"] == tokens["refresh_token"]


def test_refresh_rechaza_un_access_token(client):
    tokens = _tokens(client)
    res = client.post(REFRESH_URL, json={"refresh_token": tokens["access_token"]})
    assert res.status_code == 401


def test_refresh_token_ilegible(client):
    res = client.post(REFRESH_URL, json={"refresh_token": "esto.no.es-un-jwt"})
    assert res.status_code == 401


def test_refresh_usuario_desactivado(client):
    """Desactivar una cuenta corta la renovacion, no solo el login."""
    from tests.conftest import TestingSessionLocal
    from app.models.user import User

    tokens = _tokens(client)

    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == VALID_USER["email"]).first()
    user.is_active = False
    db.commit()
    db.close()

    res = client.post(REFRESH_URL, json={"refresh_token": tokens["refresh_token"]})
    assert res.status_code == 403
