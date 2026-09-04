"""Tests del servicio de gamificación: generación de las misiones del día.
Usa el mismo SQLite de pruebas que el resto de la suite (tests/conftest.py)
porque las misiones se persisten en BD real."""
from datetime import timedelta

import pytest

from app.models.gamificacion import MisionDiaria
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
