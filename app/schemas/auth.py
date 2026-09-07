from pydantic import BaseModel, field_validator

from app.schemas.comunes import CorreoNormalizado


class RegisterRequest(BaseModel):
    full_name: str
    email: CorreoNormalizado
    password: str
    confirm_password: str

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

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Las contraseñas no coinciden")
        return v


class LoginRequest(BaseModel):
    email: CorreoNormalizado
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class VerificarCorreoRequest(BaseModel):
    email: CorreoNormalizado


class VerificarCorreoResponse(BaseModel):
    existe: bool


class RestablecerClaveRequest(BaseModel):
    email: CorreoNormalizado
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("La contraseña debe tener mínimo 8 caracteres")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Las contraseñas no coinciden")
        return v


class RestablecerClaveResponse(BaseModel):
    message: str