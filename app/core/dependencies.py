import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.security import decode_token
from app.repositories.user_repository import UserRepository
from collections.abc import Generator

bearer_scheme = HTTPBearer()

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token inválido o expirado",
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

    return user