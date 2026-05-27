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
    PsicologiaPositivaItems,
    ResultadoCapellanItem,
    ProgramaGroup,
    ResultadosCapellanResponse,
    RecomendacionesPPResponse,
    TarjetaRecomendacion,
    ActividadFisicaItems,
    ResultadoActFisicaItem,
    ProgramaGroupAF,
    ResultadosActFisicaResponse,
    RecomendacionesAFResponse,
)
from app.services.recomendaciones_pp_service import obtener_recomendaciones_pp
from app.services.recomendaciones_af_service import obtener_recomendaciones_af
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


@router.get("/capellan/psicologia-positiva", response_model=ResultadosCapellanResponse)
def resultados_psicologia_positiva(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Vista exclusiva para el capellán.
    Devuelve los resultados de Psicología Positiva (ítems 6,12,19,25,31,37,44,49,52)
    de todos los estudiantes que completaron la encuesta, agrupados por programa/facultad.
    """
    if current_user.role != UserRole.CAPELLAN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el capellán puede acceder a esta vista",
        )

    filas = repo.obtener_resultados_pp_todos(db)

    grupos: dict[str | None, list[ResultadoCapellanItem]] = {}
    for encuesta, usuario in filas:
        item = ResultadoCapellanItem(
            encuesta_id=encuesta.id,
            usuario_id=str(usuario.id),
            nombre=usuario.full_name,
            programa=usuario.program,
            universidad=usuario.university,
            fecha=encuesta.fecha_respuesta,
            psicologia_positiva=PsicologiaPositivaItems(
                pp_item_06=encuesta.pp_item_06,
                pp_item_12=encuesta.pp_item_12,
                pp_item_19=encuesta.pp_item_19,
                pp_item_25=encuesta.pp_item_25,
                pp_item_31=encuesta.pp_item_31,
                pp_item_37=encuesta.pp_item_37,
                pp_item_44=encuesta.pp_item_44,
                pp_item_49=encuesta.pp_item_49,
                pp_item_52=encuesta.pp_item_52,
                pp_indice=encuesta.pp_indice,
                pp_nivel=encuesta.pp_nivel,
            ),
        )
        grupos.setdefault(usuario.program, []).append(item)

    grupos_list = [
        ProgramaGroup(programa=prog, total=len(estudiantes), estudiantes=estudiantes)
        for prog, estudiantes in grupos.items()
    ]

    return ResultadosCapellanResponse(
        total_estudiantes=len(filas),
        grupos=grupos_list,
    )


@router.get("/recomendaciones/psicologia-positiva", response_model=RecomendacionesPPResponse)
def recomendaciones_psicologia_positiva(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Devuelve el plan de recomendaciones de Psicología Positiva para el usuario autenticado.
    Las recomendaciones son las elaboradas por el profesional, seleccionadas según
    el puntaje de cada ítem PP. Requiere haber completado la encuesta.
    """
    ultimo = repo.obtener_ultimo(db, current_user.id)
    if not ultimo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario aún no ha completado la encuesta",
        )

    tarjetas = obtener_recomendaciones_pp(ultimo)

    return RecomendacionesPPResponse(
        usuario_id=str(current_user.id),
        nombre=current_user.full_name,
        pp_nivel=ultimo.pp_nivel,
        pp_indice=ultimo.pp_indice,
        total_tarjetas=len(tarjetas),
        tarjetas=[TarjetaRecomendacion(**t) for t in tarjetas],
    )


@router.get("/actividad-fisica/resultados", response_model=ResultadosActFisicaResponse)
def resultados_actividad_fisica(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Vista exclusiva para el rol de Actividad Física.
    Devuelve los resultados de Actividad Física (ítems 4,10,16,17,23,29,35,42,47)
    de todos los estudiantes que completaron la encuesta, agrupados por programa/facultad.
    """
    if current_user.role != UserRole.ACTIVIDAD_FISICA:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el profesional de Actividad Física puede acceder a esta vista",
        )

    filas = repo.obtener_resultados_af_todos(db)

    grupos: dict[str | None, list[ResultadoActFisicaItem]] = {}
    for encuesta, usuario in filas:
        item = ResultadoActFisicaItem(
            encuesta_id=encuesta.id,
            usuario_id=str(usuario.id),
            nombre=usuario.full_name,
            programa=usuario.program,
            universidad=usuario.university,
            fecha=encuesta.fecha_respuesta,
            actividad_fisica=ActividadFisicaItems(
                af_item_04=encuesta.af_item_04,
                af_item_10=encuesta.af_item_10,
                af_item_16=encuesta.af_item_16,
                af_item_17=encuesta.af_item_17,
                af_item_23=encuesta.af_item_23,
                af_item_29=encuesta.af_item_29,
                af_item_35=encuesta.af_item_35,
                af_item_42=encuesta.af_item_42,
                af_item_47=encuesta.af_item_47,
                af_indice=encuesta.af_indice,
                af_nivel=encuesta.af_nivel,
            ),
        )
        grupos.setdefault(usuario.program, []).append(item)

    grupos_list = [
        ProgramaGroupAF(programa=prog, total=len(estudiantes), estudiantes=estudiantes)
        for prog, estudiantes in grupos.items()
    ]

    return ResultadosActFisicaResponse(
        total_estudiantes=len(filas),
        grupos=grupos_list,
    )


@router.get("/recomendaciones/actividad-fisica", response_model=RecomendacionesAFResponse)
def recomendaciones_actividad_fisica(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Devuelve el plan de recomendaciones de Actividad Física para el usuario autenticado.
    Las recomendaciones son las elaboradas por el profesional, seleccionadas según
    el puntaje de cada ítem AF. Requiere haber completado la encuesta.
    """
    ultimo = repo.obtener_ultimo(db, current_user.id)
    if not ultimo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario aún no ha completado la encuesta",
        )

    tarjetas = obtener_recomendaciones_af(ultimo)

    return RecomendacionesAFResponse(
        usuario_id=str(current_user.id),
        nombre=current_user.full_name,
        af_nivel=ultimo.af_nivel,
        af_indice=ultimo.af_indice,
        total_tarjetas=len(tarjetas),
        tarjetas=[TarjetaRecomendacion(**t) for t in tarjetas],
    )


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
