from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.estadisticas import EstadisticasPublicas

router = APIRouter(prefix="/estadisticas", tags=["Estadísticas"])


@router.get("/publicas", response_model=EstadisticasPublicas)
def estadisticas_publicas(db: Session = Depends(get_db)):
    """Métricas públicas para la landing/registro (sin autenticación)."""
    usuarios = UserRepository(db).count()
    return {"usuarios_registrados": usuarios}
