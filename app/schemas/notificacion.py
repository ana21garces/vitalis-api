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


class DifusionRequest(BaseModel):
    """Un anuncio del administrador a un segmento de usuarios."""

    mensaje: str
    # todos | facultad | programa | tipo | nivel | sin_responder
    segmento: str
    # El valor del segmento (una facultad, un programa, un tipo o un nivel).
    # No aplica a «todos» ni a «sin_responder».
    valor: str | None = None

    @field_validator("mensaje")
    @classmethod
    def mensaje_no_vacio(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 5:
            raise ValueError("El mensaje debe tener al menos 5 caracteres")
        return v


class DifusionResponse(BaseModel):
    enviados: int


class PreviewResponse(BaseModel):
    destinatarios: int


class MedicionAbiertaInfo(BaseModel):
    nombre: str
    faltantes: int


class SegmentosResponse(BaseModel):
    """Catálogos para armar un anuncio en el panel del administrador."""

    total_estudiantes: int
    facultades: list[str]
    programas: list[str]
    tipos: list[str]
    niveles: list[str]
    medicion_abierta: MedicionAbiertaInfo | None


class EnvioResumen(BaseModel):
    """Una línea del historial: un anuncio o una notificación individual,
    agrupando todos los destinatarios que recibieron el mismo mensaje."""

    remitente_nombre: str
    mensaje: str
    total: int
    leidas: int
    created_at: datetime
