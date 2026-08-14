from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Literal, Optional

Val = Literal[1, 2, 3, 4]

TipoUsuario = Literal["estudiante", "docente", "administrativo"]


class EncuestaCreate(BaseModel):
    # Datos de perfil universitario (se guardan en el usuario)
    facultad: str
    program: str
    tipo_usuario: TipoUsuario

    # Relaciones Interpersonales — 9 ítems (campo: ri_)
    ri_item_01: Val
    ri_item_07: Val
    ri_item_13: Val
    ri_item_20: Val
    ri_item_26: Val
    ri_item_32: Val
    ri_item_38: Val
    ri_item_45: Val
    ri_item_50: Val

    # Nutrición — 10 ítems (campo: n_)
    n_item_02: Val
    n_item_08: Val
    n_item_14: Val
    n_item_21: Val
    n_item_27: Val
    n_item_33: Val
    n_item_39: Val
    n_item_40: Val
    n_item_46: Val
    n_item_51: Val

    # Responsabilidad en Salud — 7 ítems (campo: rs_)
    rs_item_03: Val
    rs_item_09: Val
    rs_item_15: Val
    rs_item_22: Val
    rs_item_28: Val
    rs_item_34: Val
    rs_item_41: Val

    # Actividad Física — 9 ítems (campo: af_)
    af_item_04: Val
    af_item_10: Val
    af_item_16: Val
    af_item_17: Val
    af_item_23: Val
    af_item_29: Val
    af_item_35: Val
    af_item_42: Val
    af_item_47: Val

    # Manejo del Estrés — 8 ítems (campo: me_)
    me_item_05: Val
    me_item_11: Val
    me_item_18: Val
    me_item_24: Val
    me_item_30: Val
    me_item_36: Val
    me_item_43: Val
    me_item_48: Val

    # Psicología Positiva — 9 ítems (campo: pp_)
    pp_item_06: Val
    pp_item_12: Val
    pp_item_19: Val
    pp_item_25: Val
    pp_item_31: Val
    pp_item_37: Val
    pp_item_44: Val
    pp_item_49: Val
    pp_item_52: Val


class DimensionResultado(BaseModel):
    indice: float   # 0 – 100  →  (promedio - 1) / 3 × 100
    nivel: str      # Pobre | Moderado | Bueno | Excelente


class ResultadosEncuesta(BaseModel):
    # Puntaje crudo global (suma de los 52 ítems, rango 52–208)
    puntaje_crudo: int
    indice_global: float    # 0 – 100
    nivel_global: str       # Pobre | Moderado | Bueno | Excelente

    # Las 6 dimensiones PEPS II
    relaciones_interpersonales: DimensionResultado
    nutricion: DimensionResultado
    responsabilidad_salud: DimensionResultado
    actividad_fisica: DimensionResultado
    manejo_estres: DimensionResultado
    psicologia_positiva: DimensionResultado


class EncuestaResponse(BaseModel):
    encuesta_id: int
    usuario_id: str
    fecha: datetime
    resultados: ResultadosEncuesta


class EncuestaHistorialItem(BaseModel):
    encuesta_id: int
    fecha: datetime
    resultados: ResultadosEncuesta


class EncuestaHistorialResponse(BaseModel):
    usuario_id: str
    total: int
    encuestas: List[EncuestaHistorialItem]


class EstadoEncuesta(BaseModel):
    completada: bool
    encuesta_id: int | None = None


class ResetearResponse(BaseModel):
    message: str


class OpcionesFiltrosResponse(BaseModel):
    facultades: List[str]
    carreras: List[str]
    tipos_usuario: List[str]


class ResumenAdminResponse(BaseModel):
    total_usuarios: int
    completaron_encuesta: int
    sin_completar: int
    tasa_participacion: float


# ── Schemas compartidos por los tres roles ───────────────────────────────────

class TarjetaRecomendacion(BaseModel):
    pregunta_num: int
    pregunta_texto: str
    nivel: str
    puntaje: int
    tecnica: str
    objetivo: str
    instrucciones: List[str]


# ── Vista Capellán: Psicología Positiva ──────────────────────────────────────

class PsicologiaPositivaItems(BaseModel):
    pp_item_06: int
    pp_item_12: int
    pp_item_19: int
    pp_item_25: int
    pp_item_31: int
    pp_item_37: int
    pp_item_44: int
    pp_item_49: int
    pp_item_52: int
    pp_indice: float
    pp_nivel: str


class ResultadoCapellanItem(BaseModel):
    encuesta_id: int
    usuario_id: str
    nombre: str
    facultad: str | None
    programa: str | None
    tipo_usuario: str | None
    universidad: str | None
    fecha: datetime
    psicologia_positiva: PsicologiaPositivaItems


class CarreraGroupPP(BaseModel):
    carrera: str | None
    total: int
    usuarios: List[ResultadoCapellanItem]


class FacultadGroupPP(BaseModel):
    facultad: str | None
    total: int
    carreras: List[CarreraGroupPP]


# Alias de compatibilidad
ProgramaGroup = CarreraGroupPP


class ResultadosCapellanResponse(BaseModel):
    total_usuarios: int
    facultades: List[FacultadGroupPP]


class RecomendacionesPPResponse(BaseModel):
    usuario_id: str
    nombre: str | None
    pp_nivel: str
    pp_indice: float
    total_tarjetas: int
    tarjetas: List[TarjetaRecomendacion]


# ── Vista Actividad Física ────────────────────────────────────────────────────

class ActividadFisicaItems(BaseModel):
    af_item_04: int
    af_item_10: int
    af_item_16: int
    af_item_17: int
    af_item_23: int
    af_item_29: int
    af_item_35: int
    af_item_42: int
    af_item_47: int
    af_indice: float
    af_nivel: str


class ResultadoActFisicaItem(BaseModel):
    encuesta_id: int
    usuario_id: str
    nombre: str
    facultad: str | None
    programa: str | None
    tipo_usuario: str | None
    universidad: str | None
    fecha: datetime
    actividad_fisica: ActividadFisicaItems


class CarreraGroupAF(BaseModel):
    carrera: str | None
    total: int
    usuarios: List[ResultadoActFisicaItem]


class FacultadGroupAF(BaseModel):
    facultad: str | None
    total: int
    carreras: List[CarreraGroupAF]


# Alias de compatibilidad
ProgramaGroupAF = CarreraGroupAF


class ResultadosActFisicaResponse(BaseModel):
    total_usuarios: int
    facultades: List[FacultadGroupAF]


class RecomendacionesAFResponse(BaseModel):
    usuario_id: str
    nombre: str | None
    af_nivel: str
    af_indice: float
    total_tarjetas: int
    tarjetas: List[TarjetaRecomendacion]


# ── Vista Responsabilidad en Salud ────────────────────────────────────────────

class ResponsabilidadSaludItems(BaseModel):
    rs_item_03: int
    rs_item_09: int
    rs_item_15: int
    rs_item_22: int
    rs_item_28: int
    rs_item_34: int
    rs_item_41: int
    rs_indice: float
    rs_nivel: str


class ResultadoRespSaludItem(BaseModel):
    encuesta_id: int
    usuario_id: str
    nombre: str
    facultad: str | None
    programa: str | None
    tipo_usuario: str | None
    universidad: str | None
    fecha: datetime
    responsabilidad_salud: ResponsabilidadSaludItems


class CarreraGroupRS(BaseModel):
    carrera: str | None
    total: int
    usuarios: List[ResultadoRespSaludItem]


class FacultadGroupRS(BaseModel):
    facultad: str | None
    total: int
    carreras: List[CarreraGroupRS]


# Alias de compatibilidad
ProgramaGroupRS = CarreraGroupRS


class ResultadosRespSaludResponse(BaseModel):
    total_usuarios: int
    facultades: List[FacultadGroupRS]


class RecomendacionesRSResponse(BaseModel):
    usuario_id: str
    nombre: str | None
    rs_nivel: str
    rs_indice: float
    total_tarjetas: int
    tarjetas: List[TarjetaRecomendacion]
