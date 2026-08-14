"""
Crea los usuarios profesionales (uno por rol) si no existen todavía.

Uso:
    python -m scripts.seed_roles              # crea todos los que falten
    python -m scripts.seed_roles capellan     # crea solo uno

Las contraseñas son de arranque: cámbialas después del primer login.
"""
import sys

from sqlalchemy import text

from app.core.security import hash_password
from app.db.session import engine
from app.models.user import UserRole

# rol -> (email, nombre completo, contraseña inicial)
USUARIOS_PROFESIONALES = {
    UserRole.CAPELLAN.value: (
        "capellan@vitalis.com", "Capellan Vitalis", "Capellan1234",
    ),
    UserRole.ACTIVIDAD_FISICA.value: (
        "actfisica@vitalis.com", "Profesional Actividad Fisica", "ActFisica1234",
    ),
    UserRole.RESPONSABILIDAD_SALUD.value: (
        "respsalud@vitalis.com", "Profesional Responsabilidad en Salud", "RespSalud1234",
    ),
}

INSERT_SQL = text("""
    INSERT INTO users (id, email, password_hash, full_name, role,
                       is_active, is_verified, total_xp, current_level,
                       streak_days, created_at, updated_at)
    VALUES (gen_random_uuid(), :email, :pwd, :nombre, :rol,
            true, true, 0, 1, 0, now(), now())
""")


def crear_usuario(conn, rol: str, email: str, nombre: str, password: str) -> None:
    ya_existe = conn.execute(
        text("SELECT id FROM users WHERE email = :email"), {"email": email}
    ).fetchone()

    if ya_existe:
        print(f"[--] {rol}: ya existe ({email}), nada que hacer.")
        return

    conn.execute(INSERT_SQL, {
        "email": email, "pwd": hash_password(password),
        "nombre": nombre, "rol": rol,
    })
    conn.commit()
    print(f"[OK] {rol} creado -> {email} / {password}")


def main(roles: list[str]) -> None:
    desconocidos = [r for r in roles if r not in USUARIOS_PROFESIONALES]
    if desconocidos:
        print(f"Rol(es) desconocido(s): {', '.join(desconocidos)}")
        print(f"Disponibles: {', '.join(USUARIOS_PROFESIONALES)}")
        sys.exit(1)

    with engine.connect() as conn:
        for rol in roles:
            crear_usuario(conn, rol, *USUARIOS_PROFESIONALES[rol])


if __name__ == "__main__":
    main(sys.argv[1:] or list(USUARIOS_PROFESIONALES))
