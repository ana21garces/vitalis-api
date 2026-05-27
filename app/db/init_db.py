from sqlalchemy import text
from app.db.base import Base
from app.db.session import engine
from app.models.user import User  # noqa: F401


def init_db() -> None:
    print("Creando tablas...")
    print(f"Tablas detectadas: {list(Base.metadata.tables.keys())}")
    Base.metadata.create_all(bind=engine)
    print("[OK] Tablas creadas correctamente")

    # Migración: convierte la columna role de enum nativo a VARCHAR(50)
    # si aún no se ha hecho. Es idempotente: no falla si ya es VARCHAR.
    try:
        with engine.begin() as conn:
            conn.execute(text(
                "ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(50)"
            ))
        print("[OK] Columna role migrada a VARCHAR(50)")
    except Exception:
        pass