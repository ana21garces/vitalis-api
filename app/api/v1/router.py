from fastapi import APIRouter

from app.api.v1.endpoints import (
    asistente,
    auditoria,
    auth,
    ciclos,
    encuesta_hplp,
    estadisticas,
    gamificacion,
    notificaciones,
    reportes,
    seguimiento_recomendaciones,
    users,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(encuesta_hplp.router)
api_router.include_router(estadisticas.router)
api_router.include_router(users.router)
api_router.include_router(notificaciones.router)
api_router.include_router(ciclos.router)
api_router.include_router(reportes.router)
api_router.include_router(auditoria.router)
api_router.include_router(gamificacion.router)
api_router.include_router(seguimiento_recomendaciones.router)
api_router.include_router(asistente.router)
