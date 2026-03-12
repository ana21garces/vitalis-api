from app.db.base import Base
from app.db.session import engine
from app.models.user import User  # noqa: F401


def init_db() -> None:
    print("🔄 Creando tablas...")
    print(f"📋 Tablas detectadas: {list(Base.metadata.tables.keys())}")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas correctamente")