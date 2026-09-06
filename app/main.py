import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
from sqlalchemy.exc import IntegrityError
from app.core.config import settings
from app.db.session import check_database_connection
from app.db.init_db import init_db
from app.api.v1.router import api_router

logger = logging.getLogger("app")

Path("uploads/avatars").mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):

    check_database_connection()
    init_db()

    yield
    


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    # Nunca en modo debug: con debug=True Starlette devuelve el traceback completo
    # (rutas del servidor, versiones, SQL) en la respuesta HTTP. El detalle de los
    # errores va al log; ver el manejador de excepciones más abajo.
    debug=False,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.exception_handler(IntegrityError)
def _integridad(request: Request, exc: IntegrityError):
    """Un choque de integridad (llave foránea, único…) es culpa del dato que
    entró, no del servidor. Se responde 409 con un mensaje neutro y el detalle
    queda solo en el log."""
    logger.warning("IntegrityError en %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=409,
        content={"detail": "La operación choca con datos existentes y no se pudo completar."},
    )


@app.exception_handler(Exception)
def _error_no_controlado(request: Request, exc: Exception):
    """Cualquier error no previsto. Nunca se devuelve el traceback al cliente
    (exponía rutas del servidor, versiones y SQL); se registra completo en el
    log y el cliente recibe un 500 genérico."""
    logger.exception("Error no controlado en %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocurrió un error interno. Inténtalo de nuevo más tarde."},
    )


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }