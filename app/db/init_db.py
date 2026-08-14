from sqlalchemy import text

from app.db.base import Base
from app.db.session import engine

# Importar todos los modelos aquí es lo que registra sus tablas en Base.metadata.
# Sin estos imports, create_all() no crearía nada.
from app.models.encuesta_hplp import EncuestaHplp  # noqa: F401
from app.models.user import User  # noqa: F401


def init_db() -> None:
    print("Creando tablas...")
    print(f"Tablas detectadas: {list(Base.metadata.tables.keys())}")
    Base.metadata.create_all(bind=engine)
    print("[OK] Tablas creadas correctamente")

    # Migración: convierte la columna role de enum nativo a VARCHAR(50)
    try:
        with engine.begin() as conn:
            conn.execute(text(
                "ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(50)"
            ))
        print("[OK] Columna role migrada a VARCHAR(50)")
    except Exception:
        pass

    # Migración: agrega facultad y tipo_usuario si no existen
    with engine.begin() as conn:
        conn.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS facultad VARCHAR(200)"
        ))
        conn.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS tipo_usuario VARCHAR(50)"
        ))
    print("[OK] Columnas facultad y tipo_usuario verificadas")
