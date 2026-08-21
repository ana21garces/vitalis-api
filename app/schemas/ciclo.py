from datetime import datetime

from pydantic import BaseModel, field_validator


class CicloResponse(BaseModel):
    id: int
    numero: int
    nombre: str
    tipo: str  # linea_base | seguimiento
    estado: str  # programado | abierto | cerrado
    fecha_apertura: datetime
    fecha_cierre: datetime | None
    elegibles: int
    respondieron: int
    participacion: float  # 0 – 100
    editable: bool  # solo la medición más reciente se puede modificar


class CiclosResponse(BaseModel):
    total: int
    ciclos: list[CicloResponse]


class CrearCicloRequest(BaseModel):
    """Programa un seguimiento.

    `fecha_cierre` es opcional: sin ella la ventana queda abierta hasta que se
    cierre a mano.
    """

    nombre: str
    fecha_apertura: datetime
    fecha_cierre: datetime | None = None

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, v: str) -> str:
        if len(v.strip()) < 3:
            raise ValueError("El nombre debe tener al menos 3 caracteres")
        return v.strip()


class ActualizarCicloRequest(BaseModel):
    """Mueve la fecha de cierre: extiende una medición abierta o reabre la
    última que se cerró. `null` la deja sin cierre previsto."""

    fecha_cierre: datetime | None = None


class RenombrarCicloRequest(BaseModel):
    """Cambia solo el nombre de una medición. Es una etiqueta: no afecta a qué
    ronda pertenece cada respuesta, así que se permite en cualquier seguimiento."""

    nombre: str

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, v: str) -> str:
        if len(v.strip()) < 3:
            raise ValueError("El nombre debe tener al menos 3 caracteres")
        return v.strip()


class SeguimientoPendiente(BaseModel):
    """Lo que necesita el frontend para avisarle a la persona."""

    ciclo_id: int
    nombre: str
    fecha_cierre: datetime | None
