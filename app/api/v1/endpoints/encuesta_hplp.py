from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.encuesta_hplp import (
    EncuestaCreate,
    EncuestaResponse,
    EncuestaHistorialResponse,
    EncuestaHistorialItem,
    ResultadosEncuesta,
    DimensionResultado,
    EstadoEncuesta,
    ResetearResponse,
)
from app.models.user import UserRole
from app.services.encuesta_hplp_service import calcular_puntajes
from app.repositories import encuesta_hplp_repository as repo

router = APIRouter(prefix="/encuesta", tags=["Encuesta HPLP-II ASD"])


def _build_resultados(row) -> ResultadosEncuesta:
    """Construye ResultadosEncuesta desde una fila del modelo (para historial)."""
    return ResultadosEncuesta(
        puntaje_crudo=row.puntaje_crudo,
        indice_global=row.indice_global,
        nivel_global=row.nivel_global,
        relaciones_interpersonales=DimensionResultado(
            indice=row.ri_indice, nivel=row.ri_nivel
        ),
        nutricion=DimensionResultado(
            indice=row.n_indice, nivel=row.n_nivel
        ),
        responsabilidad_salud=DimensionResultado(
            indice=row.rs_indice, nivel=row.rs_nivel
        ),
        actividad_fisica=DimensionResultado(
            indice=row.af_indice, nivel=row.af_nivel
        ),
        manejo_estres=DimensionResultado(
            indice=row.me_indice, nivel=row.me_nivel
        ),
        psicologia_positiva=DimensionResultado(
            indice=row.pp_indice, nivel=row.pp_nivel
        ),
    )


def _build_resultados_from_puntajes(puntajes: dict) -> ResultadosEncuesta:
    """Construye ResultadosEncuesta desde el dict devuelto por calcular_puntajes."""
    return ResultadosEncuesta(
        puntaje_crudo=puntajes["puntaje_crudo"],
        indice_global=puntajes["indice_global"],
        nivel_global=puntajes["nivel_global"],
        relaciones_interpersonales=DimensionResultado(
            indice=puntajes["ri_indice"], nivel=puntajes["ri_nivel"]
        ),
        nutricion=DimensionResultado(
            indice=puntajes["n_indice"], nivel=puntajes["n_nivel"]
        ),
        responsabilidad_salud=DimensionResultado(
            indice=puntajes["rs_indice"], nivel=puntajes["rs_nivel"]
        ),
        actividad_fisica=DimensionResultado(
            indice=puntajes["af_indice"], nivel=puntajes["af_nivel"]
        ),
        manejo_estres=DimensionResultado(
            indice=puntajes["me_indice"], nivel=puntajes["me_nivel"]
        ),
        psicologia_positiva=DimensionResultado(
            indice=puntajes["pp_indice"], nivel=puntajes["pp_nivel"]
        ),
    )


@router.post("", response_model=EncuestaResponse, status_code=status.HTTP_201_CREATED)
def guardar_encuesta(
    payload: EncuestaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recibe las 52 respuestas Likert (1–4), calcula los índices PEPS II
    y guarda el resultado.  Cada usuario solo puede responder una vez.
    """
    if repo.ya_respondio(db, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El usuario ya completó la encuesta",
        )

    puntajes = calcular_puntajes(payload)
    encuesta = repo.crear_encuesta(db, payload, puntajes, current_user.id)

    return EncuestaResponse(
        encuesta_id=encuesta.id,
        usuario_id=str(current_user.id),
        fecha=encuesta.fecha_respuesta,
        resultados=_build_resultados_from_puntajes(puntajes),
    )


@router.get("/estado", response_model=EstadoEncuesta)
def estado_encuesta(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Indica si el usuario ya completó la encuesta.
    El frontend lo llama al iniciar sesión para decidir si mostrar
    la encuesta o redirigir directo al dashboard.
    """
    ultimo = repo.obtener_ultimo(db, current_user.id)
    if ultimo:
        return EstadoEncuesta(completada=True, encuesta_id=ultimo.id)
    return EstadoEncuesta(completada=False)


@router.get("/resultado", response_model=EncuestaResponse)
def resultado_encuesta(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Devuelve el resultado más reciente del usuario autenticado.
    Usado por el dashboard para mostrar el puntaje al hacer login.
    """
    ultimo = repo.obtener_ultimo(db, current_user.id)
    if not ultimo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario aún no ha completado la encuesta",
        )
    return EncuestaResponse(
        encuesta_id=ultimo.id,
        usuario_id=str(current_user.id),
        fecha=ultimo.fecha_respuesta,
        resultados=_build_resultados(ultimo),
    )


@router.patch("/{encuesta_id}/resetear", response_model=ResetearResponse)
def resetear_encuesta(
    encuesta_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Solo administradores pueden resetear la encuesta de un usuario
    para que pueda volver a completarla.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden resetear encuestas",
        )
    eliminada = repo.eliminar(db, encuesta_id)
    if not eliminada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró la encuesta con id {encuesta_id}",
        )
    return ResetearResponse(message=f"Encuesta {encuesta_id} eliminada. El usuario puede volver a completarla.")


@router.get("/historial", response_model=EncuestaHistorialResponse)
def historial_encuestas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna el historial de encuestas del usuario autenticado."""
    encuestas = repo.obtener_por_usuario(db, current_user.id)

    if not encuestas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron encuestas para este usuario",
        )

    return EncuestaHistorialResponse(
        usuario_id=str(current_user.id),
        total=len(encuestas),
        encuestas=[
            EncuestaHistorialItem(
                encuesta_id=e.id,
                fecha=e.fecha_respuesta,
                resultados=_build_resultados(e),
            )
            for e in encuestas
        ],
    )
