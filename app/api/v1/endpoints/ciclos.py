from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, requiere_admin
from app.models.ciclo_medicion import CicloMedicion, LINEA_BASE, como_utc
from app.models.user import User
from app.repositories import ciclo_repository as repo
from app.schemas.ciclo import (
    ActualizarCicloRequest,
    CiclosResponse,
    CicloResponse,
    ComparacionResponse,
    CrearCicloRequest,
    RenombrarCicloRequest,
)
from app.services import comparacion_service

router = APIRouter(prefix="/ciclos", tags=["Mediciones"])


def _a_response(db: Session, ciclo: CicloMedicion) -> CicloResponse:
    elegibles = repo.contar_elegibles(db, ciclo)
    respondieron = repo.contar_respuestas(db, ciclo.id)
    return CicloResponse(
        id=ciclo.id,
        numero=ciclo.numero,
        nombre=ciclo.nombre,
        tipo=ciclo.tipo,
        estado=ciclo.estado(),
        fecha_apertura=ciclo.fecha_apertura,
        fecha_cierre=ciclo.fecha_cierre,
        elegibles=elegibles,
        respondieron=respondieron,
        participacion=round(respondieron / elegibles * 100, 1) if elegibles else 0.0,
        editable=ciclo.tipo != LINEA_BASE and repo.es_el_mas_reciente(db, ciclo),
    )


@router.get("", response_model=CiclosResponse)
def listar_ciclos(
    _admin: User = Depends(requiere_admin),
    db: Session = Depends(get_db),
):
    """Todas las mediciones con su participación. Solo el administrador."""
    repo.obtener_linea_base(db)  # la crea si es la primera vez
    ciclos = repo.listar(db)
    return CiclosResponse(
        total=len(ciclos),
        ciclos=[_a_response(db, c) for c in ciclos],
    )


@router.get("/comparar", response_model=ComparacionResponse)
def comparar_mediciones(
    base: int,
    seguimiento: int,
    _admin: User = Depends(requiere_admin),
    db: Session = Depends(get_db),
):
    """Compara dos mediciones entre sí. Solo el administrador.

    Se declara antes de las rutas con `/{ciclo_id}` a propósito: si fuera
    después, FastAPI intentaría leer "comparar" como un id.
    """
    ciclo_base = repo.obtener(db, base)
    ciclo_seguimiento = repo.obtener(db, seguimiento)
    if ciclo_base is None or ciclo_seguimiento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medición no encontrada",
        )
    if ciclo_base.id == ciclo_seguimiento.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Elige dos mediciones distintas para comparar",
        )
    if ciclo_base.numero > ciclo_seguimiento.numero:
        # Se ordenan solas: comparar "hacia atrás" invertiría el signo de todos
        # los cambios y se leería como que la gente empeoró.
        ciclo_base, ciclo_seguimiento = ciclo_seguimiento, ciclo_base

    return comparacion_service.comparar(db, ciclo_base, ciclo_seguimiento)


@router.post("", response_model=CicloResponse, status_code=status.HTTP_201_CREATED)
def programar_seguimiento(
    data: CrearCicloRequest,
    admin: User = Depends(requiere_admin),
    db: Session = Depends(get_db),
):
    """Programa una nueva medición de seguimiento. Solo el administrador.

    Las reglas evitan rondas que no se puedan interpretar después: no puede
    haber dos seguimientos vivos a la vez, y no tiene sentido un seguimiento sin
    una línea base con la que comparar.
    """
    # Las fechas se normalizan a UTC con zona: el cliente puede mandarlas sin
    # ella, y compararlas con fechas de la base reventaría.
    apertura = como_utc(data.fecha_apertura)
    cierre = como_utc(data.fecha_cierre) if data.fecha_cierre is not None else None

    if cierre is not None and cierre <= apertura:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de cierre debe ser posterior a la de apertura",
        )

    linea_base = repo.obtener_linea_base(db)
    if repo.contar_respuestas(db, linea_base.id) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Todavía nadie ha respondido la encuesta inicial, no hay con qué comparar",
        )

    vigente = repo.obtener_seguimiento_vigente(db)
    if vigente is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Ya hay una medición {vigente.estado()}: «{vigente.nombre}». "
                "Ciérrala antes de programar otra."
            ),
        )

    ciclo = repo.crear_seguimiento(
        db,
        nombre=data.nombre,
        fecha_apertura=apertura,
        fecha_cierre=cierre,
        creado_por=admin.id,
    )
    return _a_response(db, ciclo)


@router.patch("/{ciclo_id}", response_model=CicloResponse)
def mover_cierre(
    ciclo_id: int,
    data: ActualizarCicloRequest,
    _admin: User = Depends(requiere_admin),
    db: Session = Depends(get_db),
):
    """Extiende una medición abierta o reabre la última que se cerró.

    Es la misma operación en los dos casos: mover la fecha de cierre. Solo se
    permite sobre la medición más reciente (ver `es_el_mas_reciente`).
    """
    ciclo = repo.obtener(db, ciclo_id)
    if ciclo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medición no encontrada",
        )
    if ciclo.tipo == LINEA_BASE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La línea base está siempre abierta: no tiene fecha de cierre",
        )
    if not repo.es_el_mas_reciente(db, ciclo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Solo se puede modificar la medición más reciente. "
                "Si necesitas volver a medir, programa una nueva."
            ),
        )
    cierre = como_utc(data.fecha_cierre) if data.fecha_cierre is not None else None
    if cierre is not None and cierre <= como_utc(ciclo.fecha_apertura):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de cierre debe ser posterior a la de apertura",
        )

    ciclo.fecha_cierre = cierre
    return _a_response(db, repo.guardar(db, ciclo))


@router.post("/{ciclo_id}/cerrar", response_model=CicloResponse)
def cerrar_ahora(
    ciclo_id: int,
    _admin: User = Depends(requiere_admin),
    db: Session = Depends(get_db),
):
    """Cierra una medición en este momento, antes de su fecha prevista."""
    ciclo = repo.obtener(db, ciclo_id)
    if ciclo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medición no encontrada",
        )
    if ciclo.tipo == LINEA_BASE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La línea base no se cierra: es la puerta de entrada de cada usuario nuevo",
        )
    if ciclo.estado() == "cerrado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta medición ya está cerrada",
        )

    ciclo.fecha_cierre = datetime.now(timezone.utc)
    return _a_response(db, repo.guardar(db, ciclo))


@router.patch("/{ciclo_id}/nombre", response_model=CicloResponse)
def renombrar(
    ciclo_id: int,
    data: RenombrarCicloRequest,
    _admin: User = Depends(requiere_admin),
    db: Session = Depends(get_db),
):
    """Cambia el nombre de una medición. Es seguro en cualquier seguimiento: el
    nombre es solo una etiqueta, no cambia a qué ronda pertenece cada respuesta."""
    ciclo = repo.obtener(db, ciclo_id)
    if ciclo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medición no encontrada",
        )
    if ciclo.tipo == LINEA_BASE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de la línea base no se cambia",
        )
    ciclo.nombre = data.nombre
    return _a_response(db, repo.guardar(db, ciclo))


@router.delete("/{ciclo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(
    ciclo_id: int,
    _admin: User = Depends(requiere_admin),
    db: Session = Depends(get_db),
):
    """Elimina una medición SIN respuestas (p. ej. una programada por error).

    No se puede borrar la línea base ni una medición con respuestas: esas son
    datos de la investigación. Al borrar una, la anterior vuelve a ser la más
    reciente y por tanto editable/reabrible.
    """
    ciclo = repo.obtener(db, ciclo_id)
    if ciclo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medición no encontrada",
        )
    if ciclo.tipo == LINEA_BASE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La línea base no se puede eliminar",
        )
    if repo.contar_respuestas(db, ciclo.id) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar una medición que ya tiene respuestas",
        )
    repo.eliminar(db, ciclo)
    return None
