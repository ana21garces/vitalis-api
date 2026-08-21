from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, requiere_admin
from app.models.user import User
from app.services import reportes_service as svc

router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get("/{tipo}")
def generar_reporte(
    tipo: str,
    formato: str = Query("excel", description="excel | pdf | csv"),
    rol: str = Query("todos", description="todos | usuarios | profesionales"),
    segmento: str = Query("todas"),
    dimension: str = Query("global", description="global | todas | <clave de dimensión>"),
    nivel: str | None = Query(None, description="Pobre | Moderado | Bueno | Excelente"),
    _admin: User = Depends(requiere_admin),
    db: Session = Depends(get_db),
):
    """Genera un reporte descargable (Excel o PDF). Solo el administrador.

    Los reportes son cuatro (`tipo`): usuarios, participacion, progresion y
    distribucion. Cada uno usa los filtros que le aplican e ignora el resto.
    """
    if tipo not in svc.TIPOS_VALIDOS:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Reporte no encontrado")
    if formato not in svc.FORMATOS_VALIDOS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="El formato debe ser excel, pdf o csv"
        )
    if dimension not in ("global", "todas") and dimension not in svc.DIM_POR_CLAVE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Dimensión no válida")
    if nivel is not None and nivel not in svc.NIVELES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Nivel no válido")

    tabla = svc.generar(
        db, tipo, rol=rol, segmento=segmento, dimension=dimension, nivel=nivel,
    )
    contenido, media_type, ext = svc.render(tabla, formato)

    nombre = f"reporte_{tipo}.{ext}"
    # filename* permite acentos; filename plano como respaldo.
    disposition = f"attachment; filename=\"{nombre}\"; filename*=UTF-8''{quote(nombre)}"
    return Response(
        content=contenido,
        media_type=media_type,
        headers={"Content-Disposition": disposition},
    )
