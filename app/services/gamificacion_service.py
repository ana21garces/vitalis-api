"""Lógica de gamificación: misiones diarias, XP, niveles y rangos."""

from __future__ import annotations

import random
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

try:
    from zoneinfo import ZoneInfo
    COLOMBIA_TZ = ZoneInfo("America/Bogota")
except Exception:
    # Windows sin paquete tzdata: Colombia usa UTC-5 fijo (sin horario de verano).
    COLOMBIA_TZ = timezone(timedelta(hours=-5))

from app.data.tareas_catalogo import (
    DIMENSION_LABELS,
    DIMENSIONES,
    TAREAS_CATALOGO,
    TAREAS_POR_DIMENSION,
    TAREAS_POR_ID,
    TareaDef,
)
from app.models.gamificacion import MisionDiaria, XpEvento
from app.models.user import User, UserRole
from app.repositories import encuesta_hplp_repository as encuesta_repo
from app.repositories.gamificacion_repository import GamificacionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.gamificacion import (
    CompletarMisionResponse,
    MisionResponse,
    MisionesHoyResponse,
    ProgresoGamificacion,
    XpEventoResponse,
)

BOGOTA = COLOMBIA_TZ
BONUS_DIA_XP = 25
BONUS_ENCUESTA_XP = 100
RACHA_3_BONUS = 10
RACHA_7_BONUS = 50

RANK_TIERS = [
    (0, "bronce"),
    (500, "plata"),
    (1500, "oro"),
    (4000, "platino"),
]


def hoy_bogota() -> date:
    return datetime.now(BOGOTA).date()


def xp_umbral_nivel(level: int) -> int:
    if level <= 1:
        return 0
    total = 0
    for i in range(1, level):
        total += 100 + (i - 1) * 50
    return total


def nivel_desde_xp(total_xp: int) -> int:
    level = 1
    while xp_umbral_nivel(level + 1) <= total_xp:
        level += 1
    return level


def rank_desde_xp(total_xp: int) -> str:
    rank = "bronce"
    for umbral, nombre in RANK_TIERS:
        if total_xp >= umbral:
            rank = nombre
    return rank


def progreso_de_usuario(user: User) -> ProgresoGamificacion:
    level = nivel_desde_xp(user.total_xp)
    xp_en_nivel = user.total_xp - xp_umbral_nivel(level)
    xp_para_siguiente = xp_umbral_nivel(level + 1) - xp_umbral_nivel(level)
    return ProgresoGamificacion(
        total_xp=user.total_xp,
        current_level=level,
        rank_tier=rank_desde_xp(user.total_xp),
        streak_days=user.streak_days,
        xp_en_nivel=xp_en_nivel,
        xp_para_siguiente=xp_para_siguiente,
        avatar_url=user.avatar_url,
    )


def _dimensiones_ordenadas(db: Session, user_id: uuid.UUID) -> list[str]:
    encuesta = encuesta_repo.obtener_ultimo(db, user_id)
    if not encuesta:
        return DIMENSIONES.copy()

    pares = [
        ("relaciones_interpersonales", encuesta.ri_indice or 0),
        ("nutricion", encuesta.n_indice or 0),
        ("responsabilidad_salud", encuesta.rs_indice or 0),
        ("actividad_fisica", encuesta.af_indice or 0),
        ("manejo_estres", encuesta.me_indice or 0),
        ("psicologia_positiva", encuesta.pp_indice or 0),
    ]
    pares.sort(key=lambda p: p[1])
    return [p[0] for p in pares]


def _elegir_tarea(
    dimension: str,
    excluir: set[str],
    rng: random.Random,
) -> TareaDef:
    candidatas = [t for t in TAREAS_POR_DIMENSION[dimension] if t.id not in excluir]
    if not candidatas:
        candidatas = TAREAS_POR_DIMENSION[dimension]
    return rng.choice(candidatas)


def _generar_misiones(user_id: uuid.UUID, db: Session, fecha: date) -> list[MisionDiaria]:
    repo = GamificacionRepository(db)
    recientes = repo.tareas_recientes(user_id, dias=2)
    rng = random.Random(f"{user_id}-{fecha.isoformat()}")

    orden = _dimensiones_ordenadas(db, user_id)
    debiles = orden[:3]
    fuertes = orden[3:] or orden
    dimension_equilibrio = rng.choice(fuertes)

    seleccionadas: list[TareaDef] = []
    usadas: set[str] = set()

    for dim in debiles:
        tarea = _elegir_tarea(dim, recientes | usadas, rng)
        seleccionadas.append(tarea)
        usadas.add(tarea.id)

    tarea_eq = _elegir_tarea(dimension_equilibrio, recientes | usadas, rng)
    seleccionadas.append(tarea_eq)

    return [
        MisionDiaria(
            user_id=user_id,
            fecha=fecha,
            tarea_id=t.id,
            dimension=t.dimension,
            xp_otorgado=t.xp,
        )
        for t in seleccionadas
    ]


def _mision_a_response(mision: MisionDiaria) -> MisionResponse:
    tarea = TAREAS_POR_ID[mision.tarea_id]
    return MisionResponse(
        id=mision.id,
        tarea_id=mision.tarea_id,
        dimension=mision.dimension,
        dimension_label=DIMENSION_LABELS[mision.dimension],
        titulo=tarea.titulo,
        descripcion=tarea.descripcion,
        xp=mision.xp_otorgado,
        duracion_min=tarea.duracion_min,
        completada=mision.completada_at is not None,
        completada_at=mision.completada_at,
    )


def es_usuario(user: User) -> bool:
    """La gamificación es solo para el rol usuario (student)."""
    return user.role == UserRole.STUDENT.value


class GamificacionService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = GamificacionRepository(db)
        self.users = UserRepository(db)

    def obtener_misiones_hoy(self, user: User) -> MisionesHoyResponse:
        if not es_usuario(user):
            return MisionesHoyResponse(
                fecha=hoy_bogota(),
                misiones=[],
                completadas_hoy=0,
                total_hoy=0,
                bonus_disponible=0,
                progreso=progreso_de_usuario(user),
            )
        fecha = hoy_bogota()
        misiones = self.repo.obtener_misiones_dia(user.id, fecha)
        if not misiones:
            misiones = self.repo.crear_misiones(_generar_misiones(user.id, self.db, fecha))

        completadas = sum(1 for m in misiones if m.completada_at)
        return MisionesHoyResponse(
            fecha=fecha,
            misiones=[_mision_a_response(m) for m in misiones],
            completadas_hoy=completadas,
            total_hoy=len(misiones),
            bonus_disponible=BONUS_DIA_XP if completadas < len(misiones) else 0,
            progreso=progreso_de_usuario(user),
        )

    def _otorgar_xp(
        self,
        user: User,
        xp: int,
        motivo: str,
        referencia_id: str | None = None,
    ) -> None:
        if not es_usuario(user):
            return
        if xp <= 0:
            return
        user.total_xp += xp
        user.current_level = nivel_desde_xp(user.total_xp)
        self.repo.registrar_xp(
            XpEvento(
                user_id=user.id,
                xp=xp,
                motivo=motivo,
                referencia_id=referencia_id,
            )
        )
        self.users.update(user)

    def _actualizar_racha(self, user: User, fecha: date) -> int:
        if user.last_streak_date == fecha:
            return 0

        ayer = fecha - timedelta(days=1)
        if user.last_streak_date == ayer:
            user.streak_days += 1
        else:
            user.streak_days = 1

        user.last_streak_date = fecha
        bonus = 0

        if user.streak_days == 3 and not self.repo.ya_otorgo_motivo(user.id, "racha_3"):
            bonus += RACHA_3_BONUS
            self._otorgar_xp(user, RACHA_3_BONUS, "racha_3")
        if user.streak_days == 7 and not self.repo.ya_otorgo_motivo(user.id, "racha_7"):
            bonus += RACHA_7_BONUS
            self._otorgar_xp(user, RACHA_7_BONUS, "racha_7")

        self.users.update(user)
        return bonus

    def completar_mision(self, user: User, mision_id: uuid.UUID) -> CompletarMisionResponse:
        if not es_usuario(user):
            raise ValueError("La gamificación es solo para usuarios")
        mision = self.repo.obtener_mision(mision_id, user.id)
        if not mision:
            raise ValueError("Misión no encontrada")
        if mision.completada_at:
            raise ValueError("La misión ya fue completada")

        rank_anterior = rank_desde_xp(user.total_xp)
        nivel_anterior = nivel_desde_xp(user.total_xp)

        mision.completada_at = datetime.now(timezone.utc)
        self.repo.guardar_mision(mision)

        xp_ganado = mision.xp_otorgado
        self._otorgar_xp(user, xp_ganado, "tarea_completada", str(mision.id))

        bonus_dia = 0
        bonus_racha = self._actualizar_racha(user, mision.fecha)

        misiones_dia = self.repo.obtener_misiones_dia(user.id, mision.fecha)
        completadas = [m for m in misiones_dia if m.completada_at]

        if len(completadas) == len(misiones_dia):
            ref = f"bonus-{mision.fecha.isoformat()}"
            if not self.repo.ya_otorgo_motivo(user.id, "bonus_dia", ref):
                bonus_dia = BONUS_DIA_XP
                self._otorgar_xp(user, bonus_dia, "bonus_dia", ref)

        subio_nivel = nivel_desde_xp(user.total_xp) > nivel_anterior
        rank_nuevo = rank_desde_xp(user.total_xp)
        nuevo_rank = rank_nuevo if rank_nuevo != rank_anterior else None

        return CompletarMisionResponse(
            mision=_mision_a_response(mision),
            xp_ganado=xp_ganado + bonus_dia + bonus_racha,
            bonus_dia=bonus_dia,
            subio_nivel=subio_nivel,
            nuevo_rank=nuevo_rank,
            progreso=progreso_de_usuario(user),
        )

    def otorgar_xp_externo(
        self,
        user: User,
        xp: int,
        motivo: str,
        referencia_id: str | None = None,
    ) -> None:
        """Punto de entrada público para que otros servicios (fuera del flujo
        de misiones/racha) otorguen XP reutilizando el mismo mecanismo."""
        self._otorgar_xp(user, xp, motivo, referencia_id)

    def otorgar_bonus_encuesta(self, user: User, encuesta_id: int) -> bool:
        ref = str(encuesta_id)
        if self.repo.ya_otorgo_motivo(user.id, "encuesta", ref):
            return False
        self._otorgar_xp(user, BONUS_ENCUESTA_XP, "encuesta", ref)
        return True

    def historial(self, user: User, limite: int = 20) -> list[XpEventoResponse]:
        eventos = self.repo.historial(user.id, limite)
        return [XpEventoResponse.model_validate(e) for e in eventos]

    def progreso(self, user: User) -> ProgresoGamificacion:
        return progreso_de_usuario(user)
