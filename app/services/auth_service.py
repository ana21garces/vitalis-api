from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.schemas.user import UserResponse
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token


class AuthService:

    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def register(self, data: RegisterRequest) -> UserResponse:
        # Verificar si el email ya existe
        existing_user = self.repo.get_by_email(data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo ya está registrado"
            )

        # Crear el nuevo usuario
        new_user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
        )

        created_user = self.repo.create(new_user)
        return UserResponse.model_validate(created_user)

    def login(self, data: LoginRequest) -> TokenResponse:
        # Verificar que el usuario existe
        user = self.repo.get_by_email(data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas"
            )

        # Verificar contraseña
        if not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas"
            )

        # Verificar que la cuenta esté activa
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cuenta inactiva, contacta al administrador"
            )

        # Actualizar último login
        user.last_login_at = datetime.now(timezone.utc)
        self.repo.update(user)

        # Generar tokens
        token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
        )