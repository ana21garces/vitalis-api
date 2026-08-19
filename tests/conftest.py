import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.core.dependencies import get_db
from app.models import user as _user_model          # noqa: F401 — registra tabla users
from app.models import encuesta_hplp as _enc_model  # noqa: F401 — registra tabla encuestas_hplp
from app.models import notificacion as _notif_model # noqa: F401 — registra tabla notificaciones

_SQLITE_TABLES = ["users", "encuestas_hplp", "notificaciones"]

SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    tables = [Base.metadata.tables[t] for t in _SQLITE_TABLES]
    Base.metadata.create_all(bind=engine, tables=tables)
    yield
    Base.metadata.drop_all(bind=engine, tables=tables)


@pytest.fixture(autouse=True)
def limpiar_tablas():
    """Limpia las tablas antes de cada test para garantizar aislamiento."""
    db = TestingSessionLocal()
    db.execute(text("DELETE FROM notificaciones"))
    db.execute(text("DELETE FROM encuestas_hplp"))
    db.execute(text("DELETE FROM users"))
    db.commit()
    db.close()
    yield


@pytest.fixture()
def client():
    # Ojo: se instancia SIN "with" a propósito. El context manager dispara el
    # lifespan de la app, que conecta a la BD real (Supabase) y corre init_db.
    # Los tests deben correr solo contra el SQLite de arriba.
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app, raise_server_exceptions=True)
    app.dependency_overrides.clear()


@pytest.fixture()
def registered_user(client):
    payload = {
        "full_name": "Test User",
        "email": "test@vitalis.com",
        "password": "password123",
        "confirm_password": "password123",
    }
    client.post("/api/v1/auth/register", json=payload)
    return payload


@pytest.fixture()
def auth_headers(client, registered_user):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def capellan_user(client):
    payload = {
        "full_name": "Capellan Test",
        "email": "capellan@vitalis.com",
        "password": "password123",
        "confirm_password": "password123",
    }
    client.post("/api/v1/auth/register", json=payload)
    db = TestingSessionLocal()
    from app.models.user import User, UserRole
    user = db.query(User).filter(User.email == payload["email"]).first()
    user.role = UserRole.CAPELLAN
    db.commit()
    db.close()
    return payload


@pytest.fixture()
def capellan_headers(client, capellan_user):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": capellan_user["email"], "password": capellan_user["password"]},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def act_fisica_user(client):
    payload = {
        "full_name": "Act Fisica Test",
        "email": "actfisica@vitalis.com",
        "password": "password123",
        "confirm_password": "password123",
    }
    client.post("/api/v1/auth/register", json=payload)
    db = TestingSessionLocal()
    from app.models.user import User, UserRole
    user = db.query(User).filter(User.email == payload["email"]).first()
    user.role = UserRole.ACTIVIDAD_FISICA
    db.commit()
    db.close()
    return payload


@pytest.fixture()
def act_fisica_headers(client, act_fisica_user):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": act_fisica_user["email"], "password": act_fisica_user["password"]},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def resp_salud_user(client):
    payload = {
        "full_name": "Resp Salud Test",
        "email": "respsalud@vitalis.com",
        "password": "password123",
        "confirm_password": "password123",
    }
    client.post("/api/v1/auth/register", json=payload)
    db = TestingSessionLocal()
    from app.models.user import User, UserRole
    user = db.query(User).filter(User.email == payload["email"]).first()
    user.role = UserRole.RESPONSABILIDAD_SALUD
    db.commit()
    db.close()
    return payload


@pytest.fixture()
def resp_salud_headers(client, resp_salud_user):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": resp_salud_user["email"], "password": resp_salud_user["password"]},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def n_user(client):
    payload = {
        "full_name": "Nutricion Test",
        "email": "nutricion@vitalis.com",
        "password": "password123",
        "confirm_password": "password123",
    }
    client.post("/api/v1/auth/register", json=payload)
    db = TestingSessionLocal()
    from app.models.user import User, UserRole
    user = db.query(User).filter(User.email == payload["email"]).first()
    user.role = UserRole.NUTRICION
    db.commit()
    db.close()
    return payload


@pytest.fixture()
def n_headers(client, n_user):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": n_user["email"], "password": n_user["password"]},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


ENCUESTA_PAYLOAD = {
    # Perfil universitario (se guarda en el usuario, no en la encuesta)
    "facultad": "Ingenieria",
    "program": "Ingenieria de Sistemas",
    "tipo_usuario": "estudiante",

    "ri_item_01": 3, "ri_item_07": 2, "ri_item_13": 4, "ri_item_20": 1,
    "ri_item_26": 3, "ri_item_32": 2, "ri_item_38": 4, "ri_item_45": 3, "ri_item_50": 2,
    "n_item_02": 4, "n_item_08": 3, "n_item_14": 2, "n_item_21": 1,
    "n_item_27": 4, "n_item_33": 3, "n_item_39": 2, "n_item_40": 4, "n_item_46": 1, "n_item_51": 3,
    "rs_item_03": 2, "rs_item_09": 3, "rs_item_15": 4, "rs_item_22": 1,
    "rs_item_28": 2, "rs_item_34": 3, "rs_item_41": 4,
    "af_item_04": 1, "af_item_10": 2, "af_item_16": 3, "af_item_17": 4,
    "af_item_23": 1, "af_item_29": 2, "af_item_35": 3, "af_item_42": 4, "af_item_47": 1,
    "me_item_05": 3, "me_item_11": 2, "me_item_18": 4, "me_item_24": 1,
    "me_item_30": 3, "me_item_36": 2, "me_item_43": 4, "me_item_48": 3,
    "pp_item_06": 2, "pp_item_12": 4, "pp_item_19": 1, "pp_item_25": 3,
    "pp_item_31": 2, "pp_item_37": 4, "pp_item_44": 1, "pp_item_49": 3, "pp_item_52": 2,
}
