import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from collections.abc import Generator

bearer_scheme = HTTPBearer()

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token inválido o expirado",
)

CUENTA_INACTIVA = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Cuenta inactiva, contacta al administrador",
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    payload = decode_token(credentials.credentials)

    if not payload or payload.get("type") != "access":
        raise CREDENTIALS_EXCEPTION

    user_id = payload.get("sub")
    if not user_id:
        raise CREDENTIALS_EXCEPTION

    try:
        uid = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        raise CREDENTIALS_EXCEPTION

    user = UserRepository(db).get_by_id(uid)
    if user is None:
        raise CREDENTIALS_EXCEPTION

    # La cuenta pudo suspenderse después de emitir el token. Se comprueba en
    # cada petición para que la suspensión sea inmediata y no espere a que
    # expire el access token. Se responde 401 y no 403 a propósito: así el
    # cliente limpia la sesión y vuelve al acceso, donde el intento de entrar
    # explica que la cuenta está inactiva.
    if not user.is_active:
        raise CUENTA_INACTIVA

    return user


def requiere_roles(*roles_permitidos: UserRole):
    """Dependencia que exige que el usuario tenga alguno de los roles dados.

    Centraliza el control de acceso por rol: en vez de repetir en cada endpoint
    `if current_user.role != UserRole.X: raise 403`, se declara
    `Depends(requiere_roles(UserRole.ADMIN, ...))`.
    """
    permitidos = {rol.value for rol in roles_permitidos}

    def verificador(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para realizar esta acción",
            )
        return current_user

    return verificador


def requiere_admin(current_user: User = Depends(get_current_user)) -> User:
    """Atajo para exigir el rol de administrador."""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede realizar esta acción",
        )
    return current_user