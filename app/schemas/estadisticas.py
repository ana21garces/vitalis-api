from pydantic import BaseModel


class EstadisticasPublicas(BaseModel):
    usuarios_registrados: int
