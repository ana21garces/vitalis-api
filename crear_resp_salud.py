from app.db.session import engine
from app.core.security import hash_password
from sqlalchemy import text

with engine.connect() as conn:
    existe = conn.execute(
        text("SELECT id FROM users WHERE email = 'respsalud@vitalis.com'")
    ).fetchone()

    if existe:
        print("El usuario de Responsabilidad en Salud ya existe, nada que hacer.")
    else:
        conn.execute(
            text("""
                INSERT INTO users (id, email, password_hash, full_name, role,
                                   is_active, is_verified, total_xp, current_level,
                                   streak_days, created_at, updated_at)
                VALUES (gen_random_uuid(), 'respsalud@vitalis.com', :pwd,
                        'Profesional Responsabilidad en Salud', 'responsabilidad_salud',
                        true, true, 0, 1, 0, now(), now())
            """),
            {"pwd": hash_password("RespSalud1234")},
        )
        conn.commit()
        print("Usuario Responsabilidad en Salud creado")
        print("Email:    respsalud@vitalis.com")
        print("Password: RespSalud1234")
