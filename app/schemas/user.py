from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID
from datetime import date, datetime
from app.models.user import UserRole


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    university: str | None
    facultad: str | None
    program: str | None
    tipo_usuario: str | None
    sexo: str | None
    role: UserRole
    is_active: bool
    is_verified: bool
    total_xp: int
    current_level: int
    streak_days: int
    avatar_url: str | None = None
    rank_tier: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CambiarRolRequest(BaseModel):
    role: UserRole


class CambiarEstadoRequest(BaseModel):
    is_active: bool


class ActualizarPerfilRequest(BaseModel):
    full_name: str
    email: EmailStr

    @field_validator("full_name")
    @classmethod
    def name_must_not_be_empty(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres")
        return v.strip()


class CompletarDatosDemograficosRequest(BaseModel):
    """Datos demográficos que a algunas cuentas les quedaron sin guardar.
    Todos opcionales: la pantalla que bloquea el dashboard manda solo los que
    falten, y el endpoint solo escribe lo que llega (no borra lo que ya está).
    """

    facultad: str | None = None
    program: str | None = None
    tipo_usuario: str | None = None
    sexo: str | None = None

    @field_validator("facultad", "program")
    @classmethod
    def _texto_o_none(cls, v):
        if v is None:
            return None
        v = v.strip()
        return v or None

    @field_validator("tipo_usuario")
    @classmethod
    def _tipo_valido(cls, v):
        if v is None:
            return None
        v = v.strip().lower()
        if v not in {"estudiante", "docente", "administrativo"}:
            raise ValueError("tipo_usuario inválido")
        return v

    @field_validator("sexo")
    @classmethod
    def _sexo_valido(cls, v):
        if v is None:
            return None
        v = v.strip().lower()
        if v not in {"masculino", "femenino"}:
            raise ValueError("sexo inválido")
        return v


class CambiarPasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("La contraseña debe tener mínimo 8 caracteres")
        return v


class MensajeResponse(BaseModel):
    message: str


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