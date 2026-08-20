from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    VerificarCorreoRequest,
    VerificarCorreoResponse,
    RestablecerClaveRequest,
    RestablecerClaveResponse,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.register(data)


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.login(data)


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    """Devuelve un access token nuevo a partir del refresh token del login.

    El refresh token se devuelve sin cambios: su caducidad es un límite
    absoluto y no se extiende al renovar. Responde 401 si el token no es de
    tipo refresh, es ilegible o ha caducado, y 403 si la cuenta está inactiva.
    """
    service = AuthService(db)
    return service.refresh(data)


@router.post("/verificar-correo", response_model=VerificarCorreoResponse, status_code=status.HTTP_200_OK)
def verificar_correo(data: VerificarCorreoRequest, db: Session = Depends(get_db)):
    """Indica si existe una cuenta con el correo dado (paso 1 de la recuperación)."""
    existe = AuthService(db).verificar_correo(data.email)
    return VerificarCorreoResponse(existe=existe)


@router.post("/restablecer-clave", response_model=RestablecerClaveResponse, status_code=status.HTTP_200_OK)
def restablecer_clave(data: RestablecerClaveRequest, db: Session = Depends(get_db)):
    """Restablece la contraseña de una cuenta existente (paso 2 de la recuperación)."""
    AuthService(db).restablecer_clave(data)
    return RestablecerClaveResponse(message="Contraseña actualizada correctamente")
