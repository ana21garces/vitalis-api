from sqlalchemy import text

from app.db.base import Base
from app.db.session import engine

# Importar todos los modelos aquí es lo que registra sus tablas en Base.metadata.
# Sin estos imports, create_all() no crearía nada.
from app.models.encuesta_hplp import EncuestaHplp  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.notificacion import Notificacion  # noqa: F401
from app.models.ciclo_medicion import CicloMedicion  # noqa: F401
from app.models.sesion import Sesion  # noqa: F401


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
        # El sexo se pedía en la encuesta pero no se guardaba en ninguna parte.
        # Queda NULL en quienes respondieron antes de esta columna.
        conn.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS sexo VARCHAR(20)"
        ))
    print("[OK] Columnas facultad, tipo_usuario y sexo verificadas", flush=True)

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

    # Migración: mediciones. create_all() crea la tabla ciclos_medicion nueva,
    # pero no agrega la columna a encuestas_hplp, que ya existía.
    with engine.begin() as conn:
        conn.execute(text(
            "ALTER TABLE encuestas_hplp ADD COLUMN IF NOT EXISTS ciclo_id INTEGER"
        ))
    print("[OK] Columna ciclo_id verificada", flush=True)

    # Las encuestas que ya existían son la línea base: se crea el ciclo si hace
    # falta y se les asigna. Sin esto quedarían sin medición y no entrarían en
    # ninguna comparación.
    with engine.begin() as conn:
        pendientes = conn.execute(text(
            "SELECT count(*) FROM encuestas_hplp WHERE ciclo_id IS NULL"
        )).scalar()
        if pendientes:
            linea_base = conn.execute(text(
                "SELECT id FROM ciclos_medicion WHERE tipo = 'linea_base' LIMIT 1"
            )).scalar()
            if linea_base is None:
                linea_base = conn.execute(text(
                    "INSERT INTO ciclos_medicion "
                    "(numero, nombre, tipo, fecha_apertura, fecha_cierre, created_at) "
                    "VALUES (1, 'Línea base', 'linea_base', "
                    "COALESCE((SELECT min(fecha_respuesta) FROM encuestas_hplp), now()), "
                    "NULL, now()) RETURNING id"
                )).scalar()
            conn.execute(
                text("UPDATE encuestas_hplp SET ciclo_id = :cid WHERE ciclo_id IS NULL"),
                {"cid": linea_base},
            )
            print(f"[OK] {pendientes} encuestas asignadas a la linea base", flush=True)

    # Una sola respuesta por persona y medición. Si la tabla ya tuviera un
    # duplicado, el índice no se crea y se avisa: hay que revisarlo a mano
    # antes de confiar en las comparaciones por ronda.
    try:
        with engine.begin() as conn:
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_encuesta_usuario_ciclo "
                "ON encuestas_hplp (usuario_id, ciclo_id)"
            ))
        print("[OK] Indice unico (usuario_id, ciclo_id) verificado", flush=True)
    except Exception as exc:
        print(f"[AVISO] No se pudo crear el indice unico de mediciones: {exc}", flush=True)
