from datetime import datetime

from pydantic import BaseModel, field_validator


class NotificacionCreate(BaseModel):
    destinatario_id: str
    mensaje: str

    @field_validator("mensaje")
    @classmethod
    def mensaje_no_vacio(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El mensaje no puede estar vacío")
        return v


class NotificacionResponse(BaseModel):
    id: int
    remitente_nombre: str
    mensaje: str
    leida: bool
    created_at: datetime
