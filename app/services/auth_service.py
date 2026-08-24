import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    RestablecerClaveRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.repositories.user_repository import UserRepository
from app.repositories import sesion_repository
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

REFRESH_INVALIDO = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token de refresco inválido o expirado",
)


class AuthService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)

    def register(self, data: RegisterRequest) -> UserResponse:
        # Verificar si el email ya existe
        existing_user = self.repo.get_by_email(data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
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

    def login(self, data: LoginRequest, ip: str | None = None) -> TokenResponse:
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

        # Abrir una sesión para la auditoría de accesos.
        sesion_repository.crear(self.db, user.id, ip)

        # Generar tokens
        token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
        )

    def refresh(self, data: RefreshRequest) -> TokenResponse:
        """Canjea un refresh token por un access token nuevo.

        El refresh token **no se renueva**: se devuelve el mismo que llegó. Así
        el límite de REFRESH_TOKEN_EXPIRE_DAYS es absoluto y la sesión no se
        puede estirar indefinidamente encadenando renovaciones. Pasados esos
        días hay que volver a autenticarse con contraseña.
        """
        payload = decode_token(data.refresh_token)

        # Un access token enviado aquí no sirve: el tipo tiene que ser refresh.
        # Es la contraparte de la comprobación que hace get_current_user.
        if not payload or payload.get("type") != "refresh":
            raise REFRESH_INVALIDO

        try:
            uid = uuid.UUID(payload.get("sub"))
        except (ValueError, AttributeError, TypeError):
            raise REFRESH_INVALIDO

        # Se relee el usuario en vez de confiar en lo que dice el token: si lo
        # desactivaron o le cambiaron el rol después de iniciar sesión, tiene
        # que notarse en la siguiente renovación y no dentro de siete días.
        user = self.repo.get_by_id(uid)
        if user is None:
            raise REFRESH_INVALIDO

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cuenta inactiva, contacta al administrador",
            )

        token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=data.refresh_token,
        )

    def verificar_correo(self, email: str) -> bool:
        """Indica si existe una cuenta con ese correo (paso 1 de la recuperación)."""
        return self.repo.get_by_email(email) is not None

    def restablecer_clave(self, data: RestablecerClaveRequest) -> None:
        """Restablece la contraseña de una cuenta existente por su correo.

        Flujo simplificado (sin verificación por correo): valida que la cuenta
        exista y guarda el nuevo hash. Queda preparado para sustituirse por un
        esquema con código enviado al correo como mejora posterior.
        """
        user = self.repo.get_by_email(data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No existe una cuenta con ese correo",
            )
        user.password_hash = hash_password(data.new_password)
        self.repo.update(user)
