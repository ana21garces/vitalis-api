from pydantic import BaseModel


class PlanDimension(BaseModel):
    dimension: str
    label: str
    completadas: int
    total: int
    activas: int = 0
    registradas_hoy: int = 0


class AsistenteMensajeResponse(BaseModel):
    mensaje: str
    misiones: list[str]
    plan: list[PlanDimension]
    pendientes: int
    todo_hecho: bool
