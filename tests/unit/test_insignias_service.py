"""Tests del servicio de insignias. Interesa sobre todo que la evaluación al
leer (`obtener`) no falle si dos peticiones la hacen a la vez, porque otorga
filas con restricción única y además reparte XP."""
import pytest

from app.data.insignias_catalogo import INSIGNIAS
from app.models.insignia import InsigniaUsuario
from app.models.user import User, UserRole
from app.services.insignias_service import InsigniasService
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
    return InsigniasService(db)


def test_otorga_la_insignia_cumplida(db, estudiante, service):
    objetivo = INSIGNIAS[0]
    service._cumple = lambda insignia, uid: insignia.id == objetivo.id

    respuesta = service.obtener(estudiante)

    estado = next(e for e in respuesta.insignias if e.id == objetivo.id)
    assert estado.ganada is True
    assert estado.nueva is True
    assert respuesta.ganadas == 1


def test_insignias_toleran_dos_peticiones_a_la_vez(db, estudiante, service):
    """El contador del panel y la rejilla del perfil piden lo mismo: si las dos
    evalúan antes de que cualquiera guarde, ambas intentan otorgar la misma
    insignia y la segunda chocaba contra la restricción única."""
    objetivo = INSIGNIAS[0]
    service._cumple = lambda insignia, uid: insignia.id == objetivo.id
    original = service._ganadas
    llamadas = {"n": 0}

    def simula_carrera(user_id):
        llamadas["n"] += 1
        if llamadas["n"] == 1:
            otra = TestingSessionLocal()
            otra.add(InsigniaUsuario(user_id=user_id, insignia_id=objetivo.id))
            otra.commit()
            otra.close()
            return {}
        return original(user_id)

    service._ganadas = simula_carrera
    respuesta = service.obtener(estudiante)

    estado = next(e for e in respuesta.insignias if e.id == objetivo.id)
    assert estado.ganada is True
    assert (
        db.query(InsigniaUsuario)
        .filter(InsigniaUsuario.user_id == estudiante.id, InsigniaUsuario.insignia_id == objetivo.id)
        .count()
        == 1
    )
