"""Ajusta XP de un usuario para previsualizar rangos en local."""

from __future__ import annotations

import argparse

from app.db.session import SessionLocal
from app.repositories.user_repository import UserRepository
from app.services.gamificacion_service import nivel_desde_xp, rank_desde_xp

RANK_XP = {
    "bronce": 0,
    "plata": 500,
    "oro": 1500,
    "platino": 4500,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Previsualizar rango de gamificación")
    parser.add_argument("--email", required=True, help="Correo del usuario")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--rank", choices=list(RANK_XP.keys()))
    group.add_argument("--xp", type=int)
    args = parser.parse_args()

    xp = RANK_XP[args.rank] if args.rank else args.xp
    db = SessionLocal()
    try:
        user = UserRepository(db).get_by_email(args.email.strip().lower())
        if not user:
            raise SystemExit(f"No existe usuario con email: {args.email}")

        user.total_xp = xp
        user.current_level = nivel_desde_xp(xp)
        user.streak_days = 7 if xp >= 500 else 0
        UserRepository(db).update(user)

        print(f"[OK] {user.full_name} ({user.email})")
        print(f"     total_xp={user.total_xp} | nivel={user.current_level} | rango={rank_desde_xp(xp)}")
        print("     Recarga el dashboard o /dashboard/perfil en el navegador.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
