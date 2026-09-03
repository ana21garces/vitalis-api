from pydantic import BaseModel


class AsistenteMensajeResponse(BaseModel):
    mensaje: str
    misiones: list[str]
    plan: list[str]
    pendientes: int
    todo_hecho: bool
