from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,   # Verifica conexión antes de usarla
    pool_size=10,         # Conexiones simultáneas
    max_overflow=20,      # Conexiones extra en picos
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def check_database_connection() -> None:
    """Verifica que la BD esté disponible al iniciar la app.
    Lanza un error claro si no se puede conectar."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("✅ Conexión a base de datos exitosa")
    except Exception as e:
        raise RuntimeError(f"❌ No se pudo conectar a la base de datos: {e}")