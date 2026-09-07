from datetime import datetime, timedelta, timezone

from tests.conftest import ENCUESTA_PAYLOAD

ENCUESTA_URL = "/api/v1/encuesta"
NOTIF_URL = "/api/v1/notificaciones"
CICLOS_URL = "/api/v1/ciclos"


def _payload_todo(valor):
    return {k: (valor if "_item_" in k else v) for k, v in ENCUESTA_PAYLOAD.items()}


def _programar_seguimiento(client, admin_headers):
    ahora = datetime.now(timezone.utc)
    return client.post(
        CICLOS_URL,
        json={
            "nombre": "Seguimiento 1",
            "fecha_apertura": ahora.isoformat(),
            "fecha_cierre": (ahora + timedelta(days=30)).isoformat(),
        },
        headers=admin_headers,
    )

AF_ITEMS = [
    "af_item_04", "af_item_10", "af_item_16", "af_item_17", "af_item_23",
    "af_item_29", "af_item_35", "af_item_42", "af_item_47",
]
PP_ITEMS = [
    "pp_item_06", "pp_item_12", "pp_item_19", "pp_item_25", "pp_item_31",
    "pp_item_37", "pp_item_44", "pp_item_49", "pp_item_52",
]


def _payload(af_valor, pp_valor):
    p = {**ENCUESTA_PAYLOAD}
    for k in AF_ITEMS:
        p[k] = af_valor
    for k in PP_ITEMS:
        p[k] = pp_valor
    return p


def _alertas_af(notis):
    return [n for n in notis if "Actividad física" in n["mensaje"]]


def test_profesional_ve_la_alerta_de_su_dimension(client, auth_headers, act_fisica_headers):
    res = client.post(ENCUESTA_URL, json=_payload(1, 4), headers=auth_headers)
    assert res.status_code == 201

    alertas = _alertas_af(client.get(NOTIF_URL, headers=act_fisica_headers).json())
    assert len(alertas) == 1
    assert "Pobre" in alertas[0]["mensaje"]
    assert alertas[0]["enlace"].startswith("/dashboard/actividad-fisica?alerta=")


def test_admin_ve_la_alerta_al_entrar_a_la_vista(client, auth_headers, admin_headers):
    res = client.post(ENCUESTA_URL, json=_payload(1, 4), headers=auth_headers)
    assert res.status_code == 201

    # Sin entrar a la dimensión, su campana personal no la trae.
    assert _alertas_af(client.get(NOTIF_URL, headers=admin_headers).json()) == []

    # Al entrar a la vista de Actividad Física (rol), sí la ve.
    con_rol = client.get(f"{NOTIF_URL}?rol=actividad_fisica", headers=admin_headers).json()
    assert len(_alertas_af(con_rol)) == 1


def test_otro_profesional_no_ve_la_alerta_ajena(client, auth_headers, n_headers):
    res = client.post(ENCUESTA_URL, json=_payload(1, 4), headers=auth_headers)
    assert res.status_code == 201

    assert _alertas_af(client.get(NOTIF_URL, headers=n_headers).json()) == []


def test_sin_alerta_cuando_nivel_no_es_critico(client, auth_headers, capellan_headers):
    res = client.post(ENCUESTA_URL, json=_payload(1, 4), headers=auth_headers)
    assert res.status_code == 201

    notis = client.get(NOTIF_URL, headers=capellan_headers).json()
    assert [n for n in notis if "Psicología positiva" in n["mensaje"]] == []


def test_notifica_retroceso_vs_linea_base(client, auth_headers, admin_headers, act_fisica_headers):
    assert client.post(ENCUESTA_URL, json=_payload_todo(4), headers=auth_headers).status_code == 201
    _programar_seguimiento(client, admin_headers)
    assert client.post(ENCUESTA_URL, json=_payload_todo(1), headers=auth_headers).status_code == 201

    notis = client.get(NOTIF_URL, headers=act_fisica_headers).json()
    retrocesos = [n for n in notis if "retrocedió en Actividad física" in n["mensaje"]]
    assert len(retrocesos) == 1
    assert "de Excelente a Pobre" in retrocesos[0]["mensaje"]


def test_sin_retroceso_si_mejora(client, auth_headers, admin_headers, act_fisica_headers):
    assert client.post(ENCUESTA_URL, json=_payload_todo(1), headers=auth_headers).status_code == 201
    _programar_seguimiento(client, admin_headers)
    assert client.post(ENCUESTA_URL, json=_payload_todo(4), headers=auth_headers).status_code == 201

    notis = client.get(NOTIF_URL, headers=act_fisica_headers).json()
    assert [n for n in notis if "retrocedió" in n["mensaje"]] == []
