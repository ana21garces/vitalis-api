import pytest


REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"

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
