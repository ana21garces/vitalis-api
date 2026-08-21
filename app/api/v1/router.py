from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    ciclos,
    encuesta_hplp,
    estadisticas,
    notificaciones,
    users,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(encuesta_hplp.router)
api_router.include_router(estadisticas.router)
api_router.include_router(users.router)
api_router.include_router(notificaciones.router)
api_router.include_router(ciclos.router)
