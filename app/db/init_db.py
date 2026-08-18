from sqlalchemy import text

from app.db.base import Base
from app.db.session import engine

# Importar todos los modelos aquí es lo que registra sus tablas en Base.metadata.
# Sin estos imports, create_all() no crearía nada.
from app.models.encuesta_hplp import EncuestaHplp  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.notificacion import Notificacion  # noqa: F401


def init_db() -> None:
    print("Creando tablas...", flush=True)
    print(f"Tablas detectadas: {list(Base.metadata.tables.keys())}", flush=True)
    Base.metadata.create_all(bind=engine)
    print("[OK] Tablas creadas correctamente", flush=True)

    # Migración: convierte la columna role de enum nativo a VARCHAR(50)
    try:
        with engine.begin() as conn:
            conn.execute(text(
                "ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(50)"
            ))
        print("[OK] Columna role migrada a VARCHAR(50)", flush=True)
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
    print("[OK] Columnas facultad y tipo_usuario verificadas", flush=True)

    # Migración: normaliza role a minúsculas.
    # El SAEnum original guardaba el nombre del miembro ("STUDENT") en vez de su
    # valor ("student"). Al pasar la columna a VARCHAR esos valores quedaron tal
    # cual, y los usuarios creados después nacen en minúscula: la tabla termina
    # con los dos formatos. Hoy no rompe nada porque todos los guardas comparan
    # con != contra roles profesionales, pero cualquier comparación por igualdad
    # con UserRole.STUDENT fallaria en silencio.
    with engine.begin() as conn:
        resultado = conn.execute(text(
            "UPDATE users SET role = lower(role) WHERE role <> lower(role)"
        ))
    if resultado.rowcount:
        print(f"[OK] {resultado.rowcount} valores de role normalizados a minusculas", flush=True)
