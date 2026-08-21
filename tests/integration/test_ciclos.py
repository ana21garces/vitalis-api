from datetime import datetime, timedelta, timezone

from tests.conftest import ENCUESTA_PAYLOAD

CICLOS_URL = "/api/v1/ciclos"
ENCUESTA_URL = "/api/v1/encuesta"


def _iso(momento: datetime) -> str:
    return momento.isoformat()


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def _responder(client, headers):
    return client.post(ENCUESTA_URL, json=ENCUESTA_PAYLOAD, headers=headers)


def _programar(client, admin_headers, nombre="Seguimiento 1", cierre_en_dias=30):
    return client.post(
        CICLOS_URL,
        json={
            "nombre": nombre,
            "fecha_apertura": _iso(_ahora()),
            "fecha_cierre": _iso(_ahora() + timedelta(days=cierre_en_dias)),
        },
        headers=admin_headers,
    )


def test_listar_requiere_admin(client, auth_headers):
    res = client.get(CICLOS_URL, headers=auth_headers)
    assert res.status_code == 403


def test_listar_crea_la_linea_base(client, admin_headers):
    """La línea base no se siembra en una migración: aparece la primera vez
    que se consulta."""
    res = client.get(CICLOS_URL, headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    linea_base = data["ciclos"][0]
    assert linea_base["tipo"] == "linea_base"
    assert linea_base["estado"] == "abierto"
    assert linea_base["fecha_cierre"] is None
    assert linea_base["editable"] is False


def test_no_se_programa_sin_linea_base_respondida(client, admin_headers):
    res = _programar(client, admin_headers)
    assert res.status_code == 400


def test_programar_seguimiento(client, auth_headers, admin_headers):
    _responder(client, auth_headers)
    res = _programar(client, admin_headers)
    assert res.status_code == 201
    ciclo = res.json()
    assert ciclo["numero"] == 2
    assert ciclo["tipo"] == "seguimiento"
    assert ciclo["estado"] == "abierto"
    assert ciclo["elegibles"] == 1  # quien ya tenía encuesta
    assert ciclo["respondieron"] == 0
    assert ciclo["editable"] is True


def test_no_hay_dos_seguimientos_vivos(client, auth_headers, admin_headers):
    _responder(client, auth_headers)
    _programar(client, admin_headers)
    res = _programar(client, admin_headers, nombre="Seguimiento 2")
    assert res.status_code == 409


def test_cierre_debe_ser_posterior_a_la_apertura(client, auth_headers, admin_headers):
    _responder(client, auth_headers)
    res = client.post(
        CICLOS_URL,
        json={
            "nombre": "Seguimiento raro",
            "fecha_apertura": _iso(_ahora()),
            "fecha_cierre": _iso(_ahora() - timedelta(days=1)),
        },
        headers=admin_headers,
    )
    assert res.status_code == 400


def test_segunda_encuesta_solo_con_seguimiento_abierto(client, auth_headers, admin_headers):
    """Sin medición abierta la segunda respuesta sigue rechazándose; con una
    abierta se acepta y queda etiquetada aparte."""
    assert _responder(client, auth_headers).status_code == 201
    assert _responder(client, auth_headers).status_code == 409

    _programar(client, admin_headers)
    assert _responder(client, auth_headers).status_code == 201

    historial = client.get(f"{ENCUESTA_URL}/historial", headers=auth_headers).json()
    assert historial["total"] == 2
    nombres = {e["ciclo"] for e in historial["encuestas"]}
    assert nombres == {"Línea base", "Seguimiento 1"}


def test_el_seguimiento_conserva_el_sexo(client, auth_headers, admin_headers):
    """En un seguimiento no se vuelven a pedir los demográficos, así que la
    respuesta llega sin sexo: el que ya tenía la persona no debe borrarse."""
    client.post(ENCUESTA_URL, json={**ENCUESTA_PAYLOAD, "sexo": "masculino"}, headers=auth_headers)
    _programar(client, admin_headers)
    assert _responder(client, auth_headers).status_code == 201

    perfil = client.get("/api/v1/users/me", headers=auth_headers).json()
    assert perfil["sexo"] == "masculino"


def test_no_se_responde_dos_veces_la_misma_medicion(client, auth_headers, admin_headers):
    _responder(client, auth_headers)
    _programar(client, admin_headers)
    assert _responder(client, auth_headers).status_code == 201
    assert _responder(client, auth_headers).status_code == 409


def test_estado_avisa_del_seguimiento_pendiente(client, auth_headers, admin_headers):
    _responder(client, auth_headers)
    _programar(client, admin_headers)

    estado = client.get(f"{ENCUESTA_URL}/estado", headers=auth_headers).json()
    assert estado["completada"] is True
    assert estado["seguimiento_pendiente"]["nombre"] == "Seguimiento 1"

    _responder(client, auth_headers)
    estado = client.get(f"{ENCUESTA_URL}/estado", headers=auth_headers).json()
    assert estado["seguimiento_pendiente"] is None


def test_cerrar_ahora_y_reabrir(client, auth_headers, admin_headers):
    _responder(client, auth_headers)
    ciclo_id = _programar(client, admin_headers).json()["id"]

    cerrado = client.post(f"{CICLOS_URL}/{ciclo_id}/cerrar", headers=admin_headers)
    assert cerrado.status_code == 200
    assert cerrado.json()["estado"] == "cerrado"

    # Con la medición cerrada, la persona ya no puede responder.
    assert _responder(client, auth_headers).status_code == 409

    reabierto = client.patch(
        f"{CICLOS_URL}/{ciclo_id}",
        json={"fecha_cierre": _iso(_ahora() + timedelta(days=7))},
        headers=admin_headers,
    )
    assert reabierto.status_code == 200
    assert reabierto.json()["estado"] == "abierto"
    assert _responder(client, auth_headers).status_code == 201


def test_no_se_modifica_una_medicion_vieja(client, auth_headers, admin_headers):
    """Solo la más reciente se puede mover: reabrir una vieja dejaría
    respuestas nuevas etiquetadas en una ronda anterior."""
    _responder(client, auth_headers)
    primero = _programar(client, admin_headers).json()["id"]
    client.post(f"{CICLOS_URL}/{primero}/cerrar", headers=admin_headers)
    _programar(client, admin_headers, nombre="Seguimiento 2")

    res = client.patch(
        f"{CICLOS_URL}/{primero}",
        json={"fecha_cierre": _iso(_ahora() + timedelta(days=7))},
        headers=admin_headers,
    )
    assert res.status_code == 400


def test_la_linea_base_no_se_cierra(client, admin_headers):
    linea_base = client.get(CICLOS_URL, headers=admin_headers).json()["ciclos"][0]
    res = client.post(f"{CICLOS_URL}/{linea_base['id']}/cerrar", headers=admin_headers)
    assert res.status_code == 400


def test_programar_requiere_admin(client, auth_headers):
    res = _programar(client, auth_headers)
    assert res.status_code == 403


# ── Comparación entre mediciones ─────────────────────────────────────────────

COMPARAR_URL = f"{CICLOS_URL}/comparar"


def test_comparar_requiere_admin(client, auth_headers):
    res = client.get(COMPARAR_URL, params={"base": 1, "seguimiento": 2}, headers=auth_headers)
    assert res.status_code == 403


def test_comparar_dos_mediciones(client, auth_headers, admin_headers):
    """Con la misma persona en las dos rondas, la comparación la cuenta una vez
    y el cambio de nivel queda registrado."""
    _responder(client, auth_headers)
    ciclos = client.get(CICLOS_URL, headers=admin_headers).json()["ciclos"]
    base_id = next(c["id"] for c in ciclos if c["tipo"] == "linea_base")
    seguimiento_id = _programar(client, admin_headers).json()["id"]

    # Segunda respuesta con puntajes altos: el índice tiene que subir.
    mejor = {**ENCUESTA_PAYLOAD, **{k: 4 for k in ENCUESTA_PAYLOAD if "_item_" in k}}
    assert client.post(ENCUESTA_URL, json=mejor, headers=auth_headers).status_code == 201

    res = client.get(
        COMPARAR_URL,
        params={"base": base_id, "seguimiento": seguimiento_id},
        headers=admin_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["usuarios_comparados"] == 1
    assert data["base"]["nombre"] == "Línea base"

    global_ = data["dimensiones"][0]
    assert global_["clave"] == "indice_global"
    assert global_["promedio_seguimiento"] > global_["promedio_base"]
    assert global_["delta"] > 0
    assert global_["mejoraron"] == 1

    facultad = data["facultades"][0]
    assert facultad["total"] == 1
    assert facultad["delta"] > 0


def test_comparar_solo_cuenta_a_quien_respondio_ambas(client, auth_headers, admin_headers):
    """Quien respondió solo la línea base no entra en la comparación."""
    _responder(client, auth_headers)
    ciclos = client.get(CICLOS_URL, headers=admin_headers).json()["ciclos"]
    base_id = next(c["id"] for c in ciclos if c["tipo"] == "linea_base")
    seguimiento_id = _programar(client, admin_headers).json()["id"]

    data = client.get(
        COMPARAR_URL,
        params={"base": base_id, "seguimiento": seguimiento_id},
        headers=admin_headers,
    ).json()
    assert data["respondieron_base"] == 1
    assert data["respondieron_seguimiento"] == 0
    assert data["usuarios_comparados"] == 0
    assert data["dimensiones"][0]["promedio_base"] == 0.0


def test_comparar_la_misma_medicion_falla(client, admin_headers):
    linea_base = client.get(CICLOS_URL, headers=admin_headers).json()["ciclos"][0]
    res = client.get(
        COMPARAR_URL,
        params={"base": linea_base["id"], "seguimiento": linea_base["id"]},
        headers=admin_headers,
    )
    assert res.status_code == 400


def test_comparar_se_ordena_sola(client, auth_headers, admin_headers):
    """Pasar las mediciones al revés no invierte el signo del cambio."""
    _responder(client, auth_headers)
    ciclos = client.get(CICLOS_URL, headers=admin_headers).json()["ciclos"]
    base_id = next(c["id"] for c in ciclos if c["tipo"] == "linea_base")
    seguimiento_id = _programar(client, admin_headers).json()["id"]

    data = client.get(
        COMPARAR_URL,
        params={"base": seguimiento_id, "seguimiento": base_id},
        headers=admin_headers,
    ).json()
    assert data["base"]["id"] == base_id
    assert data["seguimiento"]["id"] == seguimiento_id
