from sqlalchemy import text
from app.db.base import Base
from app.db.session import engine
from app.models.user import User  # noqa: F401


def _agregar_valores_enum() -> None:
    """Agrega valores nuevos al tipo enum de PostgreSQL si aún no existen.
    ALTER TYPE ... ADD VALUE no puede ejecutarse dentro de una transacción,
    por eso se usa AUTOCOMMIT."""
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'capellan'"))


def init_db() -> None:
    print("Creando tablas...")
    _agregar_valores_enum()
    print(f"Tablas detectadas: {list(Base.metadata.tables.keys())}")
    Base.metadata.create_all(bind=engine)
    print("[OK] Tablas creadas correctamente")