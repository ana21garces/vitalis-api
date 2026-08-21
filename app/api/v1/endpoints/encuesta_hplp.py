from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.dependencies import get_db, get_current_user, requiere_admin
from app.models.user import User
from app.schemas.encuesta_hplp import (
    EncuestaCreate,
    EncuestaResponse,
    EncuestaHistorialResponse,
    EncuestaHistorialItem,
    ResultadosEncuesta,
    DimensionResultado,
    EstadoEncuesta,
    OpcionesFiltrosResponse,
    ResumenAdminResponse,
    PerfilSaludItem,
    PerfilesSaludResponse,
    PsicologiaPositivaItems,
    ResultadoCapellanItem,
    CarreraGroupPP,
    FacultadGroupPP,
    ResultadosCapellanResponse,
    EstadisticasDimensionResponse,
    RecomendacionesPPResponse,
    TarjetaRecomendacion,
    ActividadFisicaItems,
    ResultadoActFisicaItem,
    CarreraGroupAF,
    FacultadGroupAF,
    ResultadosActFisicaResponse,
    RecomendacionesAFResponse,
    ResponsabilidadSaludItems,
    ResultadoRespSaludItem,
    CarreraGroupRS,
    FacultadGroupRS,
    ResultadosRespSaludResponse,
    RecomendacionesRSResponse,
    RelacionesInterpersonalesItems,
    ResultadoRIItem,
    CarreraGroupRI,
    FacultadGroupRI,
    ResultadosRIResponse,
    RecomendacionesRIResponse,
    ManejoEstresItems,
    ResultadoMEItem,
    CarreraGroupME,
    FacultadGroupME,
    ResultadosMEResponse,
    RecomendacionesMEResponse,
    NutricionItems,
    ResultadoNutricionItem,
    CarreraGroupN,
    FacultadGroupN,
    ResultadosNutricionResponse,
    RecomendacionesNResponse,
)
from app.services.recomendaciones_pp_service import obtener_recomendaciones_pp
from app.services.recomendaciones_af_service import obtener_recomendaciones_af
from app.services.recomendaciones_rs_service import obtener_recomendaciones_rs
from app.services.recomendaciones_ri_service import obtener_recomendaciones_ri
from app.services.recomendaciones_me_service import obtener_recomendaciones_me
from app.services.recomendaciones_n_service import obtener_recomendaciones_n
from app.models.user import UserRole
from app.services.encuesta_hplp_service import calcular_puntajes
from app.repositories import encuesta_hplp_repository as repo
from app.repositories import ciclo_repository as ciclos
from app.schemas.ciclo import SeguimientoPendiente

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
    y guarda el resultado.

    La respuesta se etiqueta con la medición que le corresponde: la línea base
    si es su primera vez, o el seguimiento que esté abierto si ya tenía una
    encuesta. Una respuesta por persona por medición, así que sin seguimiento
    abierto la segunda vez sigue dando 409 como antes.
    """
    primera_vez = not repo.ya_respondio(db, current_user.id)

    if primera_vez:
        ciclo = ciclos.obtener_linea_base(db)
    else:
        ciclo = ciclos.obtener_seguimiento_abierto(db)
        if ciclo is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El usuario ya completó la encuesta",
            )

    if repo.ya_respondio(db, current_user.id, ciclo.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya respondiste la medición «{ciclo.nombre}»",
        )

    # Actualizar perfil universitario del usuario con los datos de la encuesta
    current_user.facultad = payload.facultad
    current_user.program = payload.program
    current_user.tipo_usuario = payload.tipo_usuario
    db.add(current_user)

    puntajes = calcular_puntajes(payload)
    encuesta = repo.crear_encuesta(db, payload, puntajes, current_user.id, ciclo.id)

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

    Si además hay un seguimiento abierto que le toca responder, lo devuelve en
    `seguimiento_pendiente` para que el dashboard le muestre el aviso. Es
    opcional: no bloquea nada, solo invita.
    """
    ultimo = repo.obtener_ultimo(db, current_user.id)
    if not ultimo:
        return EstadoEncuesta(completada=False)

    pendiente = None
    abierto = ciclos.obtener_seguimiento_abierto(db)
    if (
        abierto is not None
        and ciclos.es_elegible(db, abierto, current_user.id)
        and not repo.ya_respondio(db, current_user.id, abierto.id)
    ):
        pendiente = SeguimientoPendiente(
            ciclo_id=abierto.id,
            nombre=abierto.nombre,
            fecha_cierre=abierto.fecha_cierre,
        )

    return EstadoEncuesta(
        completada=True,
        encuesta_id=ultimo.id,
        seguimiento_pendiente=pendiente,
    )


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


@router.get("/capellan/psicologia-positiva", response_model=ResultadosCapellanResponse)
def resultados_psicologia_positiva(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    facultad: Optional[str] = Query(None, description="Filtrar por facultad"),
    carrera: Optional[str] = Query(None, description="Filtrar por carrera/programa"),
    tipo_usuario: Optional[str] = Query(None, description="Filtrar por tipo: estudiante, docente, administrativo"),
):
    """
    Vista exclusiva para el capellán.
    Devuelve resultados de Psicología Positiva agrupados por facultad y carrera.
    Acepta filtros opcionales: facultad, carrera, tipo_usuario.
    """
    if current_user.role not in (UserRole.CAPELLAN, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el capellán puede acceder a esta vista",
        )

    filas = repo.obtener_resultados_pp_todos(db, facultad=facultad, carrera=carrera, tipo_usuario=tipo_usuario)

    # Agrupación: facultad → carrera → usuarios
    por_facultad: dict[str | None, dict[str | None, list[ResultadoCapellanItem]]] = {}
    for encuesta, usuario in filas:
        item = ResultadoCapellanItem(
            encuesta_id=encuesta.id,
            usuario_id=str(usuario.id),
            nombre=usuario.full_name,
            facultad=usuario.facultad,
            programa=usuario.program,
            tipo_usuario=usuario.tipo_usuario,
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
        por_facultad.setdefault(usuario.facultad, {}).setdefault(usuario.program, []).append(item)

    facultades_list = [
        FacultadGroupPP(
            facultad=fac,
            total=sum(len(v) for v in carreras.values()),
            carreras=[
                CarreraGroupPP(carrera=car, total=len(usuarios), usuarios=usuarios)
                for car, usuarios in carreras.items()
            ],
        )
        for fac, carreras in por_facultad.items()
    ]

    return ResultadosCapellanResponse(
        total_usuarios=len(filas),
        facultades=facultades_list,
    )


@router.get("/capellan/psicologia-positiva/estadisticas", response_model=EstadisticasDimensionResponse)
def estadisticas_psicologia_positiva(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Vista exclusiva para el capellán.
    Población general y por facultad en Psicología Positiva, para los
    gráficos de qué facultades necesitan más atención y cómo está la
    universidad en conjunto. No admite filtros: es la foto completa.
    """
    if current_user.role not in (UserRole.CAPELLAN, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el capellán puede acceder a esta vista",
        )

    general, facultades = repo.obtener_estadisticas_pp(db)
    return EstadisticasDimensionResponse(poblacion_general=general, por_facultad=facultades)


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
    facultad: Optional[str] = Query(None, description="Filtrar por facultad"),
    carrera: Optional[str] = Query(None, description="Filtrar por carrera/programa"),
    tipo_usuario: Optional[str] = Query(None, description="Filtrar por tipo: estudiante, docente, administrativo"),
):
    """
    Vista exclusiva para el rol de Actividad Física.
    Devuelve resultados agrupados por facultad y carrera.
    Acepta filtros opcionales: facultad, carrera, tipo_usuario.
    """
    if current_user.role not in (UserRole.ACTIVIDAD_FISICA, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el profesional de Actividad Física puede acceder a esta vista",
        )

    filas = repo.obtener_resultados_af_todos(db, facultad=facultad, carrera=carrera, tipo_usuario=tipo_usuario)

    por_facultad: dict[str | None, dict[str | None, list[ResultadoActFisicaItem]]] = {}
    for encuesta, usuario in filas:
        item = ResultadoActFisicaItem(
            encuesta_id=encuesta.id,
            usuario_id=str(usuario.id),
            nombre=usuario.full_name,
            facultad=usuario.facultad,
            programa=usuario.program,
            tipo_usuario=usuario.tipo_usuario,
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
        por_facultad.setdefault(usuario.facultad, {}).setdefault(usuario.program, []).append(item)

    facultades_list = [
        FacultadGroupAF(
            facultad=fac,
            total=sum(len(v) for v in carreras.values()),
            carreras=[
                CarreraGroupAF(carrera=car, total=len(usuarios), usuarios=usuarios)
                for car, usuarios in carreras.items()
            ],
        )
        for fac, carreras in por_facultad.items()
    ]

    return ResultadosActFisicaResponse(
        total_usuarios=len(filas),
        facultades=facultades_list,
    )


@router.get("/actividad-fisica/resultados/estadisticas", response_model=EstadisticasDimensionResponse)
def estadisticas_actividad_fisica(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Vista exclusiva para el rol de Actividad Física.
    Población general y por facultad en Actividad Física, para los
    gráficos de qué facultades necesitan más atención y cómo está la
    universidad en conjunto. No admite filtros: es la foto completa.
    """
    if current_user.role not in (UserRole.ACTIVIDAD_FISICA, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el profesional de Actividad Física puede acceder a esta vista",
        )

    general, facultades = repo.obtener_estadisticas_af(db)
    return EstadisticasDimensionResponse(poblacion_general=general, por_facultad=facultades)


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


@router.get("/responsabilidad-salud/resultados", response_model=ResultadosRespSaludResponse)
def resultados_responsabilidad_salud(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    facultad: Optional[str] = Query(None, description="Filtrar por facultad"),
    carrera: Optional[str] = Query(None, description="Filtrar por carrera/programa"),
    tipo_usuario: Optional[str] = Query(None, description="Filtrar por tipo: estudiante, docente, administrativo"),
):
    """
    Vista exclusiva para el rol de Responsabilidad en Salud.
    Devuelve resultados agrupados por facultad y carrera.
    Acepta filtros opcionales: facultad, carrera, tipo_usuario.
    """
    if current_user.role not in (UserRole.RESPONSABILIDAD_SALUD, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el profesional de Responsabilidad en Salud puede acceder a esta vista",
        )

    filas = repo.obtener_resultados_rs_todos(db, facultad=facultad, carrera=carrera, tipo_usuario=tipo_usuario)

    por_facultad: dict[str | None, dict[str | None, list[ResultadoRespSaludItem]]] = {}
    for encuesta, usuario in filas:
        item = ResultadoRespSaludItem(
            encuesta_id=encuesta.id,
            usuario_id=str(usuario.id),
            nombre=usuario.full_name,
            facultad=usuario.facultad,
            programa=usuario.program,
            tipo_usuario=usuario.tipo_usuario,
            universidad=usuario.university,
            fecha=encuesta.fecha_respuesta,
            responsabilidad_salud=ResponsabilidadSaludItems(
                rs_item_03=encuesta.rs_item_03,
                rs_item_09=encuesta.rs_item_09,
                rs_item_15=encuesta.rs_item_15,
                rs_item_22=encuesta.rs_item_22,
                rs_item_28=encuesta.rs_item_28,
                rs_item_34=encuesta.rs_item_34,
                rs_item_41=encuesta.rs_item_41,
                rs_indice=encuesta.rs_indice,
                rs_nivel=encuesta.rs_nivel,
            ),
        )
        por_facultad.setdefault(usuario.facultad, {}).setdefault(usuario.program, []).append(item)

    facultades_list = [
        FacultadGroupRS(
            facultad=fac,
            total=sum(len(v) for v in carreras.values()),
            carreras=[
                CarreraGroupRS(carrera=car, total=len(usuarios), usuarios=usuarios)
                for car, usuarios in carreras.items()
            ],
        )
        for fac, carreras in por_facultad.items()
    ]

    return ResultadosRespSaludResponse(
        total_usuarios=len(filas),
        facultades=facultades_list,
    )


@router.get("/responsabilidad-salud/resultados/estadisticas", response_model=EstadisticasDimensionResponse)
def estadisticas_responsabilidad_salud(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Vista exclusiva para el rol de Responsabilidad en Salud.
    Población general y por facultad en Responsabilidad en Salud, para los
    gráficos de qué facultades necesitan más atención y cómo está la
    universidad en conjunto. No admite filtros: es la foto completa.
    """
    if current_user.role not in (UserRole.RESPONSABILIDAD_SALUD, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el profesional de Responsabilidad en Salud puede acceder a esta vista",
        )

    general, facultades = repo.obtener_estadisticas_rs(db)
    return EstadisticasDimensionResponse(poblacion_general=general, por_facultad=facultades)


@router.get("/recomendaciones/responsabilidad-salud", response_model=RecomendacionesRSResponse)
def recomendaciones_responsabilidad_salud(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Devuelve el plan de recomendaciones de Responsabilidad en Salud para el usuario autenticado.
    Solo genera tarjetas para niveles POBRE y MODERADO (el profesional así lo indicó).
    Requiere haber completado la encuesta.
    """
    ultimo = repo.obtener_ultimo(db, current_user.id)
    if not ultimo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario aún no ha completado la encuesta",
        )

    tarjetas = obtener_recomendaciones_rs(ultimo)

    return RecomendacionesRSResponse(
        usuario_id=str(current_user.id),
        nombre=current_user.full_name,
        rs_nivel=ultimo.rs_nivel,
        rs_indice=ultimo.rs_indice,
        total_tarjetas=len(tarjetas),
        tarjetas=[TarjetaRecomendacion(**t) for t in tarjetas],
    )


@router.get("/relaciones-interpersonales/resultados", response_model=ResultadosRIResponse)
def resultados_relaciones_interpersonales(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    facultad: Optional[str] = Query(None, description="Filtrar por facultad"),
    carrera: Optional[str] = Query(None, description="Filtrar por carrera/programa"),
    tipo_usuario: Optional[str] = Query(None, description="Filtrar por tipo: estudiante, docente, administrativo"),
):
    """
    Vista exclusiva para el rol de Relaciones Interpersonales.
    Devuelve resultados agrupados por facultad y carrera.
    Acepta filtros opcionales: facultad, carrera, tipo_usuario.
    """
    if current_user.role not in (UserRole.RELACIONES_INTERPERSONALES, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el profesional de Relaciones Interpersonales puede acceder a esta vista",
        )

    filas = repo.obtener_resultados_ri_todos(db, facultad=facultad, carrera=carrera, tipo_usuario=tipo_usuario)

    por_facultad: dict[str | None, dict[str | None, list[ResultadoRIItem]]] = {}
    for encuesta, usuario in filas:
        item = ResultadoRIItem(
            encuesta_id=encuesta.id,
            usuario_id=str(usuario.id),
            nombre=usuario.full_name,
            facultad=usuario.facultad,
            programa=usuario.program,
            tipo_usuario=usuario.tipo_usuario,
            universidad=usuario.university,
            fecha=encuesta.fecha_respuesta,
            relaciones_interpersonales=RelacionesInterpersonalesItems(
                ri_item_01=encuesta.ri_item_01,
                ri_item_07=encuesta.ri_item_07,
                ri_item_13=encuesta.ri_item_13,
                ri_item_20=encuesta.ri_item_20,
                ri_item_26=encuesta.ri_item_26,
                ri_item_32=encuesta.ri_item_32,
                ri_item_38=encuesta.ri_item_38,
                ri_item_45=encuesta.ri_item_45,
                ri_item_50=encuesta.ri_item_50,
                ri_indice=encuesta.ri_indice,
                ri_nivel=encuesta.ri_nivel,
            ),
        )
        por_facultad.setdefault(usuario.facultad, {}).setdefault(usuario.program, []).append(item)

    facultades_list = [
        FacultadGroupRI(
            facultad=fac,
            total=sum(len(v) for v in carreras.values()),
            carreras=[
                CarreraGroupRI(carrera=car, total=len(usuarios), usuarios=usuarios)
                for car, usuarios in carreras.items()
            ],
        )
        for fac, carreras in por_facultad.items()
    ]

    return ResultadosRIResponse(
        total_usuarios=len(filas),
        facultades=facultades_list,
    )


@router.get("/relaciones-interpersonales/resultados/estadisticas", response_model=EstadisticasDimensionResponse)
def estadisticas_relaciones_interpersonales(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Vista exclusiva para el rol de Relaciones Interpersonales.
    Población general y por facultad en Relaciones Interpersonales, para
    los gráficos de qué facultades necesitan más atención y cómo está la
    universidad en conjunto. No admite filtros: es la foto completa.
    """
    if current_user.role not in (UserRole.RELACIONES_INTERPERSONALES, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el profesional de Relaciones Interpersonales puede acceder a esta vista",
        )

    general, facultades = repo.obtener_estadisticas_ri(db)
    return EstadisticasDimensionResponse(poblacion_general=general, por_facultad=facultades)


@router.get("/recomendaciones/relaciones-interpersonales", response_model=RecomendacionesRIResponse)
def recomendaciones_relaciones_interpersonales(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Devuelve el plan de recomendaciones de Relaciones Interpersonales para
    el usuario autenticado. Solo genera tarjetas para niveles POBRE y
    MODERADO. Requiere haber completado la encuesta.

    La pregunta 50 no genera tarjeta: falta el objetivo real de la técnica
    en el documento fuente (ver app/services/recomendaciones_ri_service.py).
    """
    ultimo = repo.obtener_ultimo(db, current_user.id)
    if not ultimo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario aún no ha completado la encuesta",
        )

    tarjetas = obtener_recomendaciones_ri(ultimo)

    return RecomendacionesRIResponse(
        usuario_id=str(current_user.id),
        nombre=current_user.full_name,
        ri_nivel=ultimo.ri_nivel,
        ri_indice=ultimo.ri_indice,
        total_tarjetas=len(tarjetas),
        tarjetas=[TarjetaRecomendacion(**t) for t in tarjetas],
    )


@router.get("/manejo-estres/resultados", response_model=ResultadosMEResponse)
def resultados_manejo_estres(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    facultad: Optional[str] = Query(None, description="Filtrar por facultad"),
    carrera: Optional[str] = Query(None, description="Filtrar por carrera/programa"),
    tipo_usuario: Optional[str] = Query(None, description="Filtrar por tipo: estudiante, docente, administrativo"),
):
    """
    Vista exclusiva para el rol de Manejo del Estrés.
    Devuelve resultados agrupados por facultad y carrera.
    Acepta filtros opcionales: facultad, carrera, tipo_usuario.
    """
    if current_user.role not in (UserRole.MANEJO_ESTRES, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el profesional de Manejo del Estrés puede acceder a esta vista",
        )

    filas = repo.obtener_resultados_me_todos(db, facultad=facultad, carrera=carrera, tipo_usuario=tipo_usuario)

    por_facultad: dict[str | None, dict[str | None, list[ResultadoMEItem]]] = {}
    for encuesta, usuario in filas:
        item = ResultadoMEItem(
            encuesta_id=encuesta.id,
            usuario_id=str(usuario.id),
            nombre=usuario.full_name,
            facultad=usuario.facultad,
            programa=usuario.program,
            tipo_usuario=usuario.tipo_usuario,
            universidad=usuario.university,
            fecha=encuesta.fecha_respuesta,
            manejo_estres=ManejoEstresItems(
                me_item_05=encuesta.me_item_05,
                me_item_11=encuesta.me_item_11,
                me_item_18=encuesta.me_item_18,
                me_item_24=encuesta.me_item_24,
                me_item_30=encuesta.me_item_30,
                me_item_36=encuesta.me_item_36,
                me_item_43=encuesta.me_item_43,
                me_item_48=encuesta.me_item_48,
                me_indice=encuesta.me_indice,
                me_nivel=encuesta.me_nivel,
            ),
        )
        por_facultad.setdefault(usuario.facultad, {}).setdefault(usuario.program, []).append(item)

    facultades_list = [
        FacultadGroupME(
            facultad=fac,
            total=sum(len(v) for v in carreras.values()),
            carreras=[
                CarreraGroupME(carrera=car, total=len(usuarios), usuarios=usuarios)
                for car, usuarios in carreras.items()
            ],
        )
        for fac, carreras in por_facultad.items()
    ]

    return ResultadosMEResponse(
        total_usuarios=len(filas),
        facultades=facultades_list,
    )


@router.get("/manejo-estres/resultados/estadisticas", response_model=EstadisticasDimensionResponse)
def estadisticas_manejo_estres(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Vista exclusiva para el rol de Manejo del Estrés.
    Población general y por facultad en Manejo del Estrés, para los
    gráficos de qué facultades necesitan más atención y cómo está la
    universidad en conjunto. No admite filtros: es la foto completa.
    """
    if current_user.role not in (UserRole.MANEJO_ESTRES, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el profesional de Manejo del Estrés puede acceder a esta vista",
        )

    general, facultades = repo.obtener_estadisticas_me(db)
    return EstadisticasDimensionResponse(poblacion_general=general, por_facultad=facultades)


@router.get("/recomendaciones/manejo-estres", response_model=RecomendacionesMEResponse)
def recomendaciones_manejo_estres(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Devuelve el plan de recomendaciones de Manejo del Estrés para el usuario autenticado.
    Solo genera tarjetas para niveles POBRE y MODERADO. Requiere haber completado la encuesta.

    Contenido pendiente de validación por el equipo de psicología (ver
    app/services/recomendaciones_me_service.py).
    """
    ultimo = repo.obtener_ultimo(db, current_user.id)
    if not ultimo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario aún no ha completado la encuesta",
        )

    tarjetas = obtener_recomendaciones_me(ultimo)

    return RecomendacionesMEResponse(
        usuario_id=str(current_user.id),
        nombre=current_user.full_name,
        me_nivel=ultimo.me_nivel,
        me_indice=ultimo.me_indice,
        total_tarjetas=len(tarjetas),
        tarjetas=[TarjetaRecomendacion(**t) for t in tarjetas],
    )


@router.get("/nutricion/resultados", response_model=ResultadosNutricionResponse)
def resultados_nutricion(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    facultad: Optional[str] = Query(None, description="Filtrar por facultad"),
    carrera: Optional[str] = Query(None, description="Filtrar por carrera/programa"),
    tipo_usuario: Optional[str] = Query(None, description="Filtrar por tipo: estudiante, docente, administrativo"),
):
    """
    Vista exclusiva para el rol de Nutrición.
    Devuelve resultados agrupados por facultad y carrera.
    Acepta filtros opcionales: facultad, carrera, tipo_usuario.
    """
    if current_user.role not in (UserRole.NUTRICION, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el profesional de Nutrición puede acceder a esta vista",
        )

    filas = repo.obtener_resultados_n_todos(db, facultad=facultad, carrera=carrera, tipo_usuario=tipo_usuario)

    por_facultad: dict[str | None, dict[str | None, list[ResultadoNutricionItem]]] = {}
    for encuesta, usuario in filas:
        item = ResultadoNutricionItem(
            encuesta_id=encuesta.id,
            usuario_id=str(usuario.id),
            nombre=usuario.full_name,
            facultad=usuario.facultad,
            programa=usuario.program,
            tipo_usuario=usuario.tipo_usuario,
            universidad=usuario.university,
            fecha=encuesta.fecha_respuesta,
            nutricion=NutricionItems(
                n_item_02=encuesta.n_item_02,
                n_item_08=encuesta.n_item_08,
                n_item_14=encuesta.n_item_14,
                n_item_21=encuesta.n_item_21,
                n_item_27=encuesta.n_item_27,
                n_item_33=encuesta.n_item_33,
                n_item_39=encuesta.n_item_39,
                n_item_40=encuesta.n_item_40,
                n_item_46=encuesta.n_item_46,
                n_item_51=encuesta.n_item_51,
                n_indice=encuesta.n_indice,
                n_nivel=encuesta.n_nivel,
            ),
        )
        por_facultad.setdefault(usuario.facultad, {}).setdefault(usuario.program, []).append(item)

    facultades_list = [
        FacultadGroupN(
            facultad=fac,
            total=sum(len(v) for v in carreras.values()),
            carreras=[
                CarreraGroupN(carrera=car, total=len(usuarios), usuarios=usuarios)
                for car, usuarios in carreras.items()
            ],
        )
        for fac, carreras in por_facultad.items()
    ]

    return ResultadosNutricionResponse(
        total_usuarios=len(filas),
        facultades=facultades_list,
    )


@router.get("/nutricion/resultados/estadisticas", response_model=EstadisticasDimensionResponse)
def estadisticas_nutricion(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Vista exclusiva para el rol de Nutrición.
    Población general y por facultad en Nutrición, para los gráficos de
    qué facultades necesitan más atención y cómo está la universidad en
    conjunto. No admite filtros: es la foto completa.
    """
    if current_user.role not in (UserRole.NUTRICION, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el profesional de Nutrición puede acceder a esta vista",
        )

    general, facultades = repo.obtener_estadisticas_n(db)
    return EstadisticasDimensionResponse(poblacion_general=general, por_facultad=facultades)


@router.get("/recomendaciones/nutricion", response_model=RecomendacionesNResponse)
def recomendaciones_nutricion(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Devuelve el plan de recomendaciones de Nutrición para el usuario
    autenticado. Solo genera tarjetas para niveles POBRE y MODERADO.
    Requiere haber completado la encuesta.
    """
    ultimo = repo.obtener_ultimo(db, current_user.id)
    if not ultimo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario aún no ha completado la encuesta",
        )

    tarjetas = obtener_recomendaciones_n(ultimo)

    return RecomendacionesNResponse(
        usuario_id=str(current_user.id),
        nombre=current_user.full_name,
        n_nivel=ultimo.n_nivel,
        n_indice=ultimo.n_indice,
        total_tarjetas=len(tarjetas),
        tarjetas=[TarjetaRecomendacion(**t) for t in tarjetas],
    )


@router.get("/admin/resumen", response_model=ResumenAdminResponse)
def resumen_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Vista exclusiva para el administrador.
    Devuelve totales: usuarios registrados, que completaron la encuesta HPLP,
    sin completar y tasa de participación.
    Solo cuenta usuarios con rol student (excluye cuentas profesionales y admin).
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden acceder a este resumen",
        )
    return repo.obtener_resumen_admin(db)


@router.get("/perfiles", response_model=PerfilesSaludResponse)
def perfiles_salud(
    db: Session = Depends(get_db),
    _admin: User = Depends(requiere_admin),
    facultad: Optional[str] = Query(None, description="Filtrar por facultad"),
    tipo_usuario: Optional[str] = Query(None, description="Filtrar por tipo de usuario"),
):
    """Perfiles de bienestar de todos los usuarios que respondieron la encuesta.

    Vista del administrador: por cada usuario, su última encuesta con las 6
    dimensiones PEPS II y el índice/nivel global. Reutiliza la misma consulta
    base que las vistas por rol (última encuesta de cada usuario).
    """
    filas = repo.obtener_perfiles_todos(db, facultad=facultad, tipo_usuario=tipo_usuario)
    perfiles = [
        PerfilSaludItem(
            usuario_id=str(usuario.id),
            nombre=usuario.full_name,
            email=usuario.email,
            facultad=usuario.facultad,
            programa=usuario.program,
            tipo_usuario=usuario.tipo_usuario,
            fecha=encuesta.fecha_respuesta,
            resultados=_build_resultados(encuesta),
        )
        for encuesta, usuario in filas
    ]
    return PerfilesSaludResponse(total=len(perfiles), perfiles=perfiles)


@router.get("/filtros/opciones", response_model=OpcionesFiltrosResponse)
def opciones_filtros(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Devuelve los valores únicos de facultad, carrera y tipo_usuario
    presentes en los resultados de la encuesta HPLP.
    Úsalo para poblar los dropdowns de filtros en el frontend.
    Accesible por cualquier rol profesional o admin.
    """
    roles_permitidos = {
        UserRole.ADMIN,
        UserRole.CAPELLAN,
        UserRole.ACTIVIDAD_FISICA,
        UserRole.RESPONSABILIDAD_SALUD,
        UserRole.RELACIONES_INTERPERSONALES,
        UserRole.MANEJO_ESTRES,
        UserRole.NUTRICION,
    }
    if current_user.role not in roles_permitidos:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para acceder a las opciones de filtros",
        )
    return repo.obtener_opciones_filtros(db)


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

    # Nombre de cada medición en una sola consulta, para no pedirla por fila.
    nombres = {c.id: c for c in ciclos.listar(db)}

    return EncuestaHistorialResponse(
        usuario_id=str(current_user.id),
        total=len(encuestas),
        encuestas=[
            EncuestaHistorialItem(
                encuesta_id=e.id,
                fecha=e.fecha_respuesta,
                resultados=_build_resultados(e),
                ciclo=nombres[e.ciclo_id].nombre if e.ciclo_id in nombres else None,
                ciclo_numero=nombres[e.ciclo_id].numero if e.ciclo_id in nombres else None,
            )
            for e in encuestas
        ],
    )
