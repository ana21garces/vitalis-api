"""
Crea los usuarios profesionales (uno por rol) y rota sus contraseñas.

    python -m scripts.seed_roles              # crea los que falten
    python -m scripts.seed_roles capellan     # crea solo ese rol
    python -m scripts.seed_roles --rotar      # nueva contraseña a los que existen
    python -m scripts.seed_roles --rotar admin capellan

La contraseña se genera al azar y se imprime UNA sola vez: no queda escrita en
el código ni en la base de datos, solo su hash. Guárdala en un gestor de
contraseñas en cuanto la veas.
"""
import argparse
import secrets
import sys
import uuid
from datetime import datetime, timezone

from sqlalchemy import text

from app.core.security import hash_password
from app.db.session import engine
from app.models.user import UserRole

# rol -> (email, nombre completo)
USUARIOS_PROFESIONALES = {
    UserRole.ADMIN.value: ("admin@vitalis.com", "Administrador Vitalis"),
    UserRole.CAPELLAN.value: ("capellan@vitalis.com", "Capellan Vitalis"),
    UserRole.ACTIVIDAD_FISICA.value: (
        "actfisica@vitalis.com", "Profesional Actividad Fisica",
    ),
    UserRole.RESPONSABILIDAD_SALUD.value: (
        "respsalud@vitalis.com", "Profesional Responsabilidad en Salud",
    ),
    UserRole.RELACIONES_INTERPERSONALES.value: (
        "relinterpersonales@vitalis.com", "Profesional Relaciones Interpersonales",
    ),
    UserRole.MANEJO_ESTRES.value: (
        "manejoestres@vitalis.com", "Profesional Manejo del Estres",
    ),
}

# El id y las fechas se generan en Python a proposito, no con gen_random_uuid()
# ni now(): la primera solo es nativa desde PostgreSQL 13 (antes exige pgcrypto,
# que instalar requiere superusuario) y la segunda no existe en SQLite. Asi el
# script no depende del motor ni de su version, y se puede probar.
INSERT_SQL = text("""
    INSERT INTO users (id, email, password_hash, full_name, role,
                       is_active, is_verified, total_xp, current_level,
                       streak_days, created_at, updated_at)
    VALUES (:id, :email, :pwd, :nombre, :rol,
            true, true, 0, 1, 0, :ahora, :ahora)
""")

UPDATE_PWD_SQL = text("""
    UPDATE users SET password_hash = :pwd, updated_at = :ahora
    WHERE email = :email
""")


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def generar_password() -> str:
    """Contraseña aleatoria de ~22 caracteres, apta para copiar y pegar."""
    return secrets.token_urlsafe(16)


def _existe(conn, email: str) -> bool:
    return conn.execute(
        text("SELECT 1 FROM users WHERE email = :email"), {"email": email}
    ).fetchone() is not None


def crear_usuario(conn, rol: str, email: str, nombre: str) -> str | None:
    if _existe(conn, email):
        print(f"[--] {rol}: ya existe ({email}). Usa --rotar para cambiar su clave.")
        return None

    password = generar_password()
    conn.execute(INSERT_SQL, {
        "id": uuid.uuid4(), "email": email, "pwd": hash_password(password),
        "nombre": nombre, "rol": rol, "ahora": _ahora(),
    })
    conn.commit()
    return password


def rotar_password(conn, rol: str, email: str) -> str | None:
    if not _existe(conn, email):
        print(f"[--] {rol}: no existe ({email}). Correlo sin --rotar para crearlo.")
        return None

    password = generar_password()
    conn.execute(UPDATE_PWD_SQL, {
        "pwd": hash_password(password), "email": email, "ahora": _ahora(),
    })
    conn.commit()
    return password


def main(roles: list[str], rotar: bool) -> None:
    desconocidos = [r for r in roles if r not in USUARIOS_PROFESIONALES]
    if desconocidos:
        print(f"Rol(es) desconocido(s): {', '.join(desconocidos)}")
        print(f"Disponibles: {', '.join(USUARIOS_PROFESIONALES)}")
        sys.exit(1)

    credenciales: list[tuple[str, str, str]] = []

    with engine.connect() as conn:
        for rol in roles:
            email, nombre = USUARIOS_PROFESIONALES[rol]
            password = (
                rotar_password(conn, rol, email) if rotar
                else crear_usuario(conn, rol, email, nombre)
            )
            if password:
                credenciales.append((rol, email, password))

    if not credenciales:
        return

    verbo = "rotada" if rotar else "creada"
    print()
    print("=" * 68)
    print(f"  CONTRASENA {verbo.upper()} - se muestra UNA sola vez")
    print("  Guardala ahora en un gestor de contrasenas. No queda en el codigo")
    print("  ni en la base de datos: solo se almacena su hash.")
    print("=" * 68)
    for rol, email, password in credenciales:
        print(f"  {rol:<24} {email:<28} {password}")
    print("=" * 68)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "roles", nargs="*", metavar="ROL",
        help="roles a procesar; por defecto, todos",
    )
    parser.add_argument(
        "--rotar", action="store_true",
        help="genera una contrasena nueva para usuarios que ya existen",
    )
    args = parser.parse_args()
    main(args.roles or list(USUARIOS_PROFESIONALES), args.rotar)
