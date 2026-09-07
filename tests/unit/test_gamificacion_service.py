"""Tests del servicio de gamificación: generación de las misiones del día.
Usa el mismo SQLite de pruebas que el resto de la suite (tests/conftest.py)
porque las misiones se persisten en BD real."""
from datetime import timedelta

import pytest

from app.models.gamificacion import MisionDiaria, XpEvento
from app.models.user import User, UserRole
from app.repositories.gamificacion_repository import GamificacionRepository
from app.services.gamificacion_service import (
    GamificacionService,
    _generar_misiones,
    hoy_bogota,
)
from tests.conftest import TestingSessionLocal


@pytest.fixture()
def db():
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture()
def estudiante(db):
    user = User(
        email="estudiante@test.com",
        password_hash="x",
        full_name="Estudiante Test",
        role=UserRole.STUDENT.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def service(db):
    return GamificacionService(db)


def test_misiones_hoy_crea_cuatro(db, estudiante, service):
    respuesta = service.obtener_misiones_hoy(estudiante)

    assert respuesta.total_hoy == 4
    assert respuesta.fecha == hoy_bogota()


def test_misiones_hoy_no_duplica_al_pedirlas_otra_vez(db, estudiante, service):
    primera = service.obtener_misiones_hoy(estudiante)
    segunda = service.obtener_misiones_hoy(estudiante)

    assert {m.id for m in primera.misiones} == {m.id for m in segunda.misiones}
    assert db.query(MisionDiaria).filter(MisionDiaria.user_id == estudiante.id).count() == 4


def test_misiones_hoy_tolera_dos_peticiones_a_la_vez(db, estudiante, service):
    """En el primer acceso del día el dashboard y la burbuja del asistente
    piden a la vez: las dos ven la tabla vacía y las dos insertan. La segunda
    chocaba contra la restricción única, respondía 500 y la tarjeta de
    misiones desaparecía sin mensaje hasta que se recargaba la página."""
    original = service.repo.obtener_misiones_dia
    llamadas = {"n": 0}

    def simula_carrera(user_id, fecha):
        llamadas["n"] += 1
        if llamadas["n"] == 1:
            GamificacionRepository(TestingSessionLocal()).crear_misiones(
                _generar_misiones(user_id, db, fecha)
            )
            return []
        return original(user_id, fecha)

    service.repo.obtener_misiones_dia = simula_carrera
    try:
        respuesta = service.obtener_misiones_hoy(estudiante)
    finally:
        service.repo.obtener_misiones_dia = original

    assert respuesta.total_hoy == 4
    assert db.query(MisionDiaria).filter(MisionDiaria.user_id == estudiante.id).count() == 4


def test_tareas_recientes_ignora_el_dia_que_se_genera(db, estudiante):
    """Si las misiones de hoy contaran como "recientes", dos peticiones
    simultáneas podrían generar juegos distintos y el usuario terminaría con
    ocho misiones en vez de cuatro."""
    hoy = hoy_bogota()
    repo = GamificacionRepository(db)
    repo.crear_misiones(_generar_misiones(estudiante.id, db, hoy))
    ayer = repo.crear_misiones(_generar_misiones(estudiante.id, db, hoy - timedelta(days=1)))

    recientes = repo.tareas_recientes(estudiante.id, hoy)

    assert recientes == {m.tarea_id for m in ayer}


# ── Bonus por racha de misiones (chequeo 6.4) ────────────────────────────────


def _xp_de(db, estudiante, motivo):
    return [
        e
        for e in db.query(XpEvento)
        .filter(XpEvento.user_id == estudiante.id, XpEvento.motivo == motivo)
        .all()
    ]


def test_racha_de_3_dias_da_el_bonus_una_sola_vez(db, estudiante, service):
    """Al llegar la racha de misiones a 3 días se otorga RACHA_3_BONUS una vez.
    Si la racha se rompe y vuelve a 3, no se otorga otra vez."""
    hoy = hoy_bogota()

    # Racha de 2 -> completar hoy la sube a 3 y dispara el bonus.
    estudiante.streak_days = 2
    estudiante.last_streak_date = hoy - timedelta(days=1)
    db.commit()
    service.completar_mision(
        estudiante,
        GamificacionRepository(db).crear_misiones(
            _generar_misiones(estudiante.id, db, hoy)
        )[0].id,
    )
    db.refresh(estudiante)
    assert estudiante.streak_days == 3
    racha_3 = _xp_de(db, estudiante, "racha_3")
    assert len(racha_3) == 1
    assert racha_3[0].xp == 10

    # La racha se rompe y otro día vuelve a 3: el bonus NO se repite.
    otro_dia = hoy + timedelta(days=5)
    estudiante.streak_days = 2
    estudiante.last_streak_date = otro_dia - timedelta(days=1)
    db.commit()
    service.completar_mision(
        estudiante,
        GamificacionRepository(db).crear_misiones(
            _generar_misiones(estudiante.id, db, otro_dia)
        )[0].id,
    )
    db.refresh(estudiante)
    assert estudiante.streak_days == 3
    assert len(_xp_de(db, estudiante, "racha_3")) == 1  # sigue siendo una sola


def test_racha_de_7_dias_da_el_bonus_una_sola_vez(db, estudiante, service):
    hoy = hoy_bogota()

    estudiante.streak_days = 6
    estudiante.last_streak_date = hoy - timedelta(days=1)
    db.commit()
    service.completar_mision(
        estudiante,
        GamificacionRepository(db).crear_misiones(
            _generar_misiones(estudiante.id, db, hoy)
        )[0].id,
    )
    db.refresh(estudiante)
    assert estudiante.streak_days == 7
    racha_7 = _xp_de(db, estudiante, "racha_7")
    assert len(racha_7) == 1
    assert racha_7[0].xp == 50


def test_completar_otra_mision_el_mismo_dia_no_repite_el_bonus_de_racha(
    db, estudiante, service
):
    """Dos misiones completadas el mismo día cuentan como un solo día de racha:
    la segunda no vuelve a dar el bonus."""
    hoy = hoy_bogota()
    estudiante.streak_days = 2
    estudiante.last_streak_date = hoy - timedelta(days=1)
    db.commit()

    misiones = GamificacionRepository(db).crear_misiones(
        _generar_misiones(estudiante.id, db, hoy)
    )
    r1 = service.completar_mision(estudiante, misiones[0].id)
    r2 = service.completar_mision(estudiante, misiones[1].id)

    db.refresh(estudiante)
    assert estudiante.streak_days == 3
    # La 1ª completada del día llevó el bonus de racha; la 2ª solo la XP de
    # su misión (aún no se completan las 4, así que tampoco hay bonus de día).
    assert r1.xp_ganado == misiones[0].xp_otorgado + 10
    assert r2.xp_ganado == misiones[1].xp_otorgado
    # Y el bonus de racha_3 quedó registrado una sola vez.
    assert len(_xp_de(db, estudiante, "racha_3")) == 1
