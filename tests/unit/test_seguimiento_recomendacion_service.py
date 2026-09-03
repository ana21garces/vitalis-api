"""Tests del servicio de seguimiento diario de recomendaciones: racha,
idempotencia, XP y notificación al profesional. Usa el mismo SQLite de
pruebas que el resto de la suite (tests/conftest.py) porque el servicio
persiste en BD real (no son cálculos puros en memoria)."""
from datetime import timedelta

import pytest

from app.models.gamificacion import XpEvento
from app.models.notificacion import Notificacion
from app.models.encuesta_hplp import EncuestaHplp
from app.models.seguimiento_recomendacion import (
    RegistroDiarioSeguimiento,
    SeguimientoRecomendacion,
)
from app.models.user import User, UserRole
from app.services.encuesta_hplp_service import ITEM_FIELDS
from app.services.gamificacion_service import hoy_bogota
from app.services.seguimiento_recomendacion_service import (
    MENSAJE_CIERRE,
    XP_POR_COMPLETAR,
    XP_POR_DIA,
    SeguimientoRecomendacionService,
)
from tests.conftest import TestingSessionLocal


_NIVEL_INDICE_POR_DEFECTO = {
    f"{prefijo}_{campo}": valor
    for prefijo in ("af", "n", "rs", "me", "ri", "pp")
    for campo, valor in (("nivel", "Pobre"), ("indice", 0.0))
}


def _encuesta(**overrides) -> EncuestaHplp:
    """Fila en memoria (no persistida): todos los ítems en 1 salvo overrides.
    También fija nivel/índice por dimensión en "Pobre"/0.0 (coherente con
    todos los ítems en 1), ya que estos campos derivados no se calculan solos
    en un objeto sin persistir — el servicio de seguimiento los necesita para
    nivel_dimension/indice_dimension."""
    return EncuestaHplp(**({c: 1 for c in ITEM_FIELDS} | _NIVEL_INDICE_POR_DEFECTO | overrides))


@pytest.fixture()
def db():
    session = TestingSessionLocal()
    yield session
    session.close()


def _crear_usuario(db, email="estudiante@test.com", role=UserRole.STUDENT) -> User:
    user = User(email=email, password_hash="x", full_name="Estudiante Test", role=role.value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def estudiante(db):
    return _crear_usuario(db)


@pytest.fixture()
def service(db):
    return SeguimientoRecomendacionService(db)


# ── Racha e idempotencia ──────────────────────────────────────────────────

def test_primer_registro_racha_uno(db, estudiante, service):
    seguimiento = service._obtener_o_crear(estudiante.id, "actividad_fisica", 4, "POBRE")

    resultado = service.registrar_dia(estudiante, seguimiento.id, notas=None)

    assert resultado.seguimiento.racha_actual == 1
    assert resultado.seguimiento.mejor_racha == 1
    assert resultado.seguimiento.total_dias_registrados == 1
    assert resultado.racha_aumento is False


def test_dia_consecutivo_incrementa_racha(db, estudiante, service):
    seguimiento = service._obtener_o_crear(estudiante.id, "actividad_fisica", 4, "POBRE")

    ayer = hoy_bogota() - timedelta(days=1)
    db.add(RegistroDiarioSeguimiento(seguimiento_id=seguimiento.id, fecha=ayer, notas=None))
    seguimiento.ultima_fecha_registro = ayer
    seguimiento.racha_actual = 1
    seguimiento.mejor_racha = 1
    seguimiento.total_dias_registrados = 1
    db.commit()

    resultado = service.registrar_dia(estudiante, seguimiento.id, notas="hoy también")

    assert resultado.seguimiento.racha_actual == 2
    assert resultado.seguimiento.mejor_racha == 2
    assert resultado.racha_aumento is True


def test_salto_de_racha_reinicia_pero_conserva_mejor_racha(db, estudiante, service):
    seguimiento = service._obtener_o_crear(estudiante.id, "actividad_fisica", 4, "POBRE")

    hace_3_dias = hoy_bogota() - timedelta(days=3)
    seguimiento.ultima_fecha_registro = hace_3_dias
    seguimiento.racha_actual = 5
    seguimiento.mejor_racha = 5
    seguimiento.total_dias_registrados = 5
    db.commit()

    resultado = service.registrar_dia(estudiante, seguimiento.id, notas=None)

    assert resultado.seguimiento.racha_actual == 1
    assert resultado.seguimiento.mejor_racha == 5
    assert resultado.racha_aumento is False


def test_registro_duplicado_mismo_dia_falla(db, estudiante, service):
    seguimiento = service._obtener_o_crear(estudiante.id, "actividad_fisica", 4, "POBRE")
    service.registrar_dia(estudiante, seguimiento.id, notas=None)

    with pytest.raises(ValueError):
        service.registrar_dia(estudiante, seguimiento.id, notas=None)


def test_obtener_o_crear_tolera_dos_peticiones_a_la_vez(db, estudiante, service):
    """Abrir el plan dispara la petición dos veces (el efecto se ejecuta doble
    en desarrollo, y en producción pasa con dos pestañas): la segunda chocaba
    contra la restricción única y la pantalla quedaba en error."""
    original = service.repo.obtener_seguimiento
    llamadas = {"n": 0}

    def simula_carrera(*args, **kwargs):
        llamadas["n"] += 1
        if llamadas["n"] == 1:
            service.repo.crear_seguimiento(
                SeguimientoRecomendacion(
                    user_id=estudiante.id,
                    dimension="actividad_fisica",
                    pregunta_num=4,
                    nivel="POBRE",
                )
            )
            return None
        return original(*args, **kwargs)

    service.repo.obtener_seguimiento = simula_carrera
    try:
        seguimiento = service._obtener_o_crear(estudiante.id, "actividad_fisica", 4, "POBRE")
    finally:
        service.repo.obtener_seguimiento = original

    assert seguimiento is not None
    assert seguimiento.pregunta_num == 4


def test_completar_dos_veces_falla(db, estudiante, service):
    seguimiento = service._obtener_o_crear(estudiante.id, "actividad_fisica", 4, "POBRE")
    service.registrar_dia(estudiante, seguimiento.id, notas=None)
    service.completar_manualmente(estudiante, seguimiento.id)

    with pytest.raises(ValueError):
        service.completar_manualmente(estudiante, seguimiento.id)


def test_registrar_dia_sobre_completada_falla(db, estudiante, service):
    seguimiento = service._obtener_o_crear(estudiante.id, "actividad_fisica", 4, "POBRE")
    service.registrar_dia(estudiante, seguimiento.id, notas=None)
    service.completar_manualmente(estudiante, seguimiento.id)

    with pytest.raises(ValueError):
        service.registrar_dia(estudiante, seguimiento.id, notas=None)


# ── Tarjetas y progreso ──────────────────────────────────────────────────

def test_obtener_tarjetas_no_duplica_seguimientos(db, estudiante, service):
    encuesta = _encuesta()

    service.obtener_tarjetas_con_seguimiento(estudiante, "actividad_fisica", encuesta)
    service.obtener_tarjetas_con_seguimiento(estudiante, "actividad_fisica", encuesta)

    total = len(service.repo.obtener_seguimientos_dimension(estudiante.id, "actividad_fisica"))
    # 9 preguntas AF, todas con nivel POBRE (item=1) generan 9 seguimientos únicos.
    assert total == 9


def test_progreso_general_activas_y_completadas(db, estudiante, service):
    encuesta = _encuesta()

    progreso_inicial = service.progreso_general(estudiante, encuesta)
    af_inicial = next(d for d in progreso_inicial.dimensiones if d.dimension == "actividad_fisica")
    assert af_inicial.total == 9
    assert af_inicial.activas == 9
    assert af_inicial.completadas == 0
    assert af_inicial.mensaje_cierre is None

    seguimiento = service._obtener_o_crear(estudiante.id, "actividad_fisica", 4, "POBRE")
    service.registrar_dia(estudiante, seguimiento.id, notas=None)
    service.completar_manualmente(estudiante, seguimiento.id)

    progreso_final = service.progreso_general(estudiante, encuesta)
    af_final = next(d for d in progreso_final.dimensiones if d.dimension == "actividad_fisica")
    assert af_final.completadas == 1
    assert af_final.activas == 8
    assert af_final.mensaje_cierre is None  # todavía no están todas completas


def test_progreso_general_mensaje_cierre_al_completar_todo(db, estudiante, service):
    """Dimensión con una sola pregunta activa (responsabilidad_salud con la
    encuesta uniforme en 1 solo tiene nivel POBRE en las 7 preguntas); se
    completan todas para forzar el mensaje de cierre."""
    encuesta = _encuesta()
    inicial = service.progreso_general(estudiante, encuesta)
    rs = next(d for d in inicial.dimensiones if d.dimension == "responsabilidad_salud")
    assert rs.total == 7

    for pregunta_num in (3, 9, 15, 22, 28, 34, 41):
        seguimiento = service._obtener_o_crear(estudiante.id, "responsabilidad_salud", pregunta_num, "POBRE")
        service.registrar_dia(estudiante, seguimiento.id, notas=None)
        service.completar_manualmente(estudiante, seguimiento.id)

    final = service.progreso_general(estudiante, encuesta)
    rs_final = next(d for d in final.dimensiones if d.dimension == "responsabilidad_salud")
    assert rs_final.completadas == 7
    assert rs_final.mensaje_cierre == MENSAJE_CIERRE


# ── XP ──────────────────────────────────────────────────────────────────

def test_registrar_dia_otorga_xp(db, estudiante, service):
    seguimiento = service._obtener_o_crear(estudiante.id, "actividad_fisica", 4, "POBRE")
    xp_previo = estudiante.total_xp

    service.registrar_dia(estudiante, seguimiento.id, notas=None)
    db.refresh(estudiante)

    assert estudiante.total_xp == xp_previo + XP_POR_DIA
    evento = (
        db.query(XpEvento)
        .filter(XpEvento.user_id == estudiante.id, XpEvento.motivo == "recomendacion_dia")
        .first()
    )
    assert evento is not None
    assert evento.xp == XP_POR_DIA


def test_completar_otorga_xp(db, estudiante, service):
    seguimiento = service._obtener_o_crear(estudiante.id, "actividad_fisica", 4, "POBRE")
    service.registrar_dia(estudiante, seguimiento.id, notas=None)
    db.refresh(estudiante)
    xp_previo = estudiante.total_xp

    service.completar_manualmente(estudiante, seguimiento.id)
    db.refresh(estudiante)

    assert estudiante.total_xp == xp_previo + XP_POR_COMPLETAR
    evento = (
        db.query(XpEvento)
        .filter(XpEvento.user_id == estudiante.id, XpEvento.motivo == "recomendacion_completada")
        .first()
    )
    assert evento is not None


# ── Notificación al profesional ──────────────────────────────────────────

def test_completar_notifica_a_un_profesional_activo(db, estudiante, service):
    profesional = _crear_usuario(db, email="af@test.com", role=UserRole.ACTIVIDAD_FISICA)
    seguimiento = service._obtener_o_crear(estudiante.id, "actividad_fisica", 4, "POBRE")
    service.registrar_dia(estudiante, seguimiento.id, notas=None)

    service.completar_manualmente(estudiante, seguimiento.id)

    notificaciones = (
        db.query(Notificacion)
        .filter(Notificacion.destinatario_id == profesional.id)
        .all()
    )
    assert len(notificaciones) == 1
    assert notificaciones[0].remitente_id == estudiante.id
    assert "Estudiante Test" in notificaciones[0].mensaje


def test_completar_notifica_a_varios_profesionales_del_mismo_rol(db, estudiante, service):
    p1 = _crear_usuario(db, email="af1@test.com", role=UserRole.ACTIVIDAD_FISICA)
    p2 = _crear_usuario(db, email="af2@test.com", role=UserRole.ACTIVIDAD_FISICA)
    seguimiento = service._obtener_o_crear(estudiante.id, "actividad_fisica", 4, "POBRE")
    service.registrar_dia(estudiante, seguimiento.id, notas=None)

    service.completar_manualmente(estudiante, seguimiento.id)

    total = db.query(Notificacion).filter(
        Notificacion.destinatario_id.in_([p1.id, p2.id])
    ).count()
    assert total == 2


def test_completar_sin_profesionales_no_falla(db, estudiante, service):
    seguimiento = service._obtener_o_crear(estudiante.id, "actividad_fisica", 4, "POBRE")

    # No debe lanzar excepción aunque no haya ningún usuario con rol actividad_fisica.
    service.registrar_dia(estudiante, seguimiento.id, notas=None)
    resultado = service.completar_manualmente(estudiante, seguimiento.id)

    assert resultado.estado == "completada"
    assert db.query(Notificacion).count() == 0
