"""
Ejercita la consulta de scripts.reporte_usuarios contra la BD de pruebas.

Los tests unitarios cubren el armado de las filas; esto cubre el SQL: el
outerjoin con la subconsulta de "ultima encuesta por usuario" tiene que
devolver tambien a quienes no han respondido.
"""
from tests.conftest import ENCUESTA_PAYLOAD, TestingSessionLocal
from scripts.reporte_usuarios import consultar, fila


def _reporte():
    db = TestingSessionLocal()
    try:
        return [(u, e) for u, e in consultar(db)]
    finally:
        db.close()


def test_incluye_a_quien_no_ha_respondido(client, registered_user):
    filas = _reporte()

    assert len(filas) == 1
    usuario, encuesta = filas[0]
    assert usuario.email == registered_user["email"]
    assert encuesta is None
    assert fila(usuario, encuesta)["hizo_hplp"] == "NO"


def test_incluye_los_resultados_de_quien_si_respondio(client, auth_headers):
    client.post("/api/v1/encuesta", json=ENCUESTA_PAYLOAD, headers=auth_headers)

    filas = _reporte()

    assert len(filas) == 1
    usuario, encuesta = filas[0]
    assert encuesta is not None

    f = fila(usuario, encuesta)
    assert f["hizo_hplp"] == "SI"
    assert f["facultad"] == ENCUESTA_PAYLOAD["facultad"]
    assert f["programa"] == ENCUESTA_PAYLOAD["program"]
    assert isinstance(f["indice_global"], float)
    assert f["nivel_global"] in {"Pobre", "Moderado", "Bueno", "Excelente"}


def test_excluye_las_cuentas_profesionales(client, capellan_user, registered_user):
    """El capellan no responde la encuesta: no debe aparecer en el reporte."""
    emails = {usuario.email for usuario, _ in _reporte()}

    assert registered_user["email"] in emails
    assert capellan_user["email"] not in emails


def test_toma_la_encuesta_mas_reciente(client, auth_headers):
    """Con varias encuestas del mismo usuario, el reporte trae una sola fila."""
    client.post("/api/v1/encuesta", json=ENCUESTA_PAYLOAD, headers=auth_headers)

    db = TestingSessionLocal()
    try:
        from app.models.encuesta_hplp import EncuestaHplp
        primera = db.query(EncuestaHplp).first()
        # Segunda encuesta del mismo usuario, saltandose el guard del endpoint
        # para simular el escenario de reasignacion que se quiere soportar.
        copia = EncuestaHplp(**{
            c.name: getattr(primera, c.name)
            for c in EncuestaHplp.__table__.columns
            if c.name not in ("id", "fecha_respuesta")
        })
        copia.indice_global = 99.0
        db.add(copia)
        db.commit()
    finally:
        db.close()

    filas = _reporte()

    assert len(filas) == 1
    _, encuesta = filas[0]
    assert encuesta.indice_global == 99.0
