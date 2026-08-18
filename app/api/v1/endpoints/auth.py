from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, RefreshRequest, TokenResponse
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

    Hasta ahora el login entregaba un refresh token que no se podía canjear en
    ninguna parte: a los 30 minutos la sesión moría y había que escribir la
    contraseña otra vez, aunque fuera en mitad de la encuesta de 52 ítems.
    """
    service = AuthService(db)
    return service.refresh(data)