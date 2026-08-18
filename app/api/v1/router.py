from fastapi import APIRouter

from app.api.v1.endpoints import auth, encuesta_hplp, estadisticas, users

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(encuesta_hplp.router)
api_router.include_router(estadisticas.router)
api_router.include_router(users.router)
