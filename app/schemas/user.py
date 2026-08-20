from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID
from datetime import datetime
from app.models.user import UserRole


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    university: str | None
    facultad: str | None
    program: str | None
    tipo_usuario: str | None
    role: UserRole
    is_active: bool
    is_verified: bool
    total_xp: int
    current_level: int
    streak_days: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CambiarRolRequest(BaseModel):
    role: UserRole


class CambiarEstadoRequest(BaseModel):
    is_active: bool


class CrearUsuarioRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.STUDENT

    @field_validator("full_name")
    @classmethod
    def name_must_not_be_empty(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("La contraseña debe tener mínimo 8 caracteres")
        return v