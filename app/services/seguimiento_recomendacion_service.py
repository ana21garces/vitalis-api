"""Seguimiento diario (con racha) de las recomendaciones profesionales de las
6 dimensiones HPLP-II. Reutiliza el contenido ya existente en
`app/services/recomendaciones_*_service.py` (no lo reimplementa) y el mismo
algoritmo de racha que usa `GamificacionService._actualizar_racha`, aplicado
aquí a una tabla propia en vez de al usuario."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.data.tareas_catalogo import DIMENSION_LABELS
from app.models.encuesta_hplp import EncuestaHplp
from app.models.seguimiento_recomendacion import RegistroDiarioSeguimiento, SeguimientoRecomendacion
from app.models.user import User, UserRole
from app.repositories import notificacion_repository
from app.repositories.seguimiento_recomendacion_repository import SeguimientoRecomendacionRepository
from app.schemas.encuesta_hplp import TarjetaRecomendacion
from app.schemas.seguimiento_recomendacion import (
    ProgresoDimension,
    ProgresoSeguimientoResponse,
    RegistrarDiaResponse,
    RegistroDiarioResponse,
    SeguimientoResponse,
    TarjetaConSeguimiento,
    TarjetasSeguimientoResponse,
)
from app.services.gamificacion_service import GamificacionService, hoy_bogota
from app.services.recomendaciones_af_service import (
    PREGUNTAS as PREGUNTAS_AF,
    RECOMENDACIONES as RECOMENDACIONES_AF,
    obtener_recomendaciones_af,
)
from app.services.recomendaciones_me_service import (
    PREGUNTAS as PREGUNTAS_ME,
    RECOMENDACIONES as RECOMENDACIONES_ME,
    obtener_recomendaciones_me,
)
from app.services.recomendaciones_n_service import (
    PREGUNTAS as PREGUNTAS_N,
    RECOMENDACIONES as RECOMENDACIONES_N,
    obtener_recomendaciones_n,
)
from app.services.recomendaciones_pp_service import (
    PREGUNTAS as PREGUNTAS_PP,
    RECOMENDACIONES as RECOMENDACIONES_PP,
    obtener_recomendaciones_pp,
)
from app.services.recomendaciones_ri_service import (
    PREGUNTAS as PREGUNTAS_RI,
    RECOMENDACIONES as RECOMENDACIONES_RI,
    obtener_recomendaciones_ri,
)
from app.services.recomendaciones_rs_service import (
    PREGUNTAS as PREGUNTAS_RS,
    RECOMENDACIONES as RECOMENDACIONES_RS,
    obtener_recomendaciones_rs,
)

XP_POR_DIA = 15
XP_POR_COMPLETAR = 50

DIAS_MINIMOS_PARA_COMPLETAR = 1

MENSAJE_CIERRE = "Completaste tu mejora de hábitos en esta dimensión por este momento."

DIMENSION_A_FUNCION = {
    "actividad_fisica": obtener_recomendaciones_af,
    "nutricion": obtener_recomendaciones_n,
    "responsabilidad_salud": obtener_recomendaciones_rs,
    "manejo_estres": obtener_recomendaciones_me,
    "relaciones_interpersonales": obtener_recomendaciones_ri,
    "psicologia_positiva": obtener_recomendaciones_pp,
}

DIMENSION_A_PREGUNTAS = {
    "actividad_fisica": PREGUNTAS_AF,
    "nutricion": PREGUNTAS_N,
    "responsabilidad_salud": PREGUNTAS_RS,
    "manejo_estres": PREGUNTAS_ME,
    "relaciones_interpersonales": PREGUNTAS_RI,
    "psicologia_positiva": PREGUNTAS_PP,
}

DIMENSION_A_FICHAS = {
    "actividad_fisica": RECOMENDACIONES_AF,
    "nutricion": RECOMENDACIONES_N,
    "responsabilidad_salud": RECOMENDACIONES_RS,
    "manejo_estres": RECOMENDACIONES_ME,
    "relaciones_interpersonales": RECOMENDACIONES_RI,
    "psicologia_positiva": RECOMENDACIONES_PP,
}

DIMENSION_A_PREFIJO = {
    "actividad_fisica": "af",
    "nutricion": "n",
    "responsabilidad_salud": "rs",
    "manejo_estres": "me",
    "relaciones_interpersonales": "ri",
    "psicologia_positiva": "pp",
}

DIMENSION_A_ROL = {
    "actividad_fisica": UserRole.ACTIVIDAD_FISICA,
    "nutricion": UserRole.NUTRICION,
    "responsabilidad_salud": UserRole.RESPONSABILIDAD_SALUD,
    "manejo_estres": UserRole.MANEJO_ESTRES,
    "relaciones_interpersonales": UserRole.RELACIONES_INTERPERSONALES,
    "psicologia_positiva": UserRole.CAPELLAN,
}


class SeguimientoRecomendacionService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = SeguimientoRecomendacionRepository(db)

    def _obtener_o_crear(
        self, user_id, dimension: str, pregunta_num: int, nivel: str,
    ) -> SeguimientoRecomendacion:
        existente = self.repo.obtener_seguimiento(user_id, dimension, pregunta_num, nivel)
        if existente:
            return existente
        try:
            return self.repo.crear_seguimiento(
                SeguimientoRecomendacion(
                    user_id=user_id,
                    dimension=dimension,
                    pregunta_num=pregunta_num,
                    nivel=nivel,
                )
            )
        except IntegrityError:
            # Otra petición simultánea ya lo creó (la vista se abre y dispara
            # dos veces): se recupera el que quedó en vez de fallar.
            self.db.rollback()
            creado = self.repo.obtener_seguimiento(user_id, dimension, pregunta_num, nivel)
            if creado is None:
                raise
            return creado

    def obtener_tarjetas_con_seguimiento(
        self, user: User, dimension: str, encuesta: EncuestaHplp,
    ) -> TarjetasSeguimientoResponse:
        tarjetas_data = DIMENSION_A_FUNCION[dimension](encuesta)
        tarjetas = []
        for t in tarjetas_data:
            seguimiento = self._obtener_o_crear(user.id, dimension, t["pregunta_num"], t["nivel"])
            tarjetas.append(
                TarjetaConSeguimiento(
                    tarjeta=TarjetaRecomendacion(**t),
                    seguimiento=SeguimientoResponse.model_validate(seguimiento),
                )
            )
        prefijo = DIMENSION_A_PREFIJO[dimension]
        return TarjetasSeguimientoResponse(
            dimension=dimension,
            nivel_dimension=getattr(encuesta, f"{prefijo}_nivel"),
            indice_dimension=getattr(encuesta, f"{prefijo}_indice"),
            total=len(tarjetas),
            tarjetas=tarjetas,
        )

    def _actualizar_racha(self, seguimiento: SeguimientoRecomendacion, fecha: date) -> bool:
        ayer = fecha - timedelta(days=1)
        if seguimiento.ultima_fecha_registro == ayer:
            seguimiento.racha_actual += 1
            aumento = True
        else:
            seguimiento.racha_actual = 1
            aumento = False
        seguimiento.mejor_racha = max(seguimiento.mejor_racha, seguimiento.racha_actual)
        seguimiento.ultima_fecha_registro = fecha
        return aumento

    def registrar_dia(self, user: User, seguimiento_id, notas: str | None = None) -> RegistrarDiaResponse:
        seguimiento = self.repo.obtener_seguimiento_por_id(seguimiento_id, user.id)
        if not seguimiento:
            raise ValueError("Seguimiento no encontrado")
        if seguimiento.estado == "completada":
            raise ValueError("Esta recomendación ya fue marcada como completada")

        hoy = hoy_bogota()
        if self.repo.obtener_registro_dia(seguimiento.id, hoy):
            raise ValueError("Ya registraste esta recomendación hoy")

        try:
            registro = self.repo.crear_registro(
                RegistroDiarioSeguimiento(seguimiento_id=seguimiento.id, fecha=hoy, notas=notas)
            )
        except IntegrityError:
            # Doble clic en "Lo hice hoy": el aviso de arriba no alcanza a ver
            # el registro de la otra petición, así que se traduce el choque al
            # mismo mensaje en vez de dejar un 500.
            self.db.rollback()
            raise ValueError("Ya registraste esta recomendación hoy")

        racha_aumento = self._actualizar_racha(seguimiento, hoy)
        seguimiento.total_dias_registrados += 1
        self.repo.guardar_seguimiento(seguimiento)

        GamificacionService(self.db).otorgar_xp_externo(
            user, XP_POR_DIA, "recomendacion_dia", str(registro.id)
        )

        return RegistrarDiaResponse(
            seguimiento=SeguimientoResponse.model_validate(seguimiento),
            registro=RegistroDiarioResponse.model_validate(registro),
            racha_aumento=racha_aumento,
        )

    def _notificar_profesionales(self, user: User, seguimiento: SeguimientoRecomendacion) -> None:
        rol = DIMENSION_A_ROL[seguimiento.dimension]
        pregunta_texto = DIMENSION_A_PREGUNTAS[seguimiento.dimension][seguimiento.pregunta_num]
        tecnica = DIMENSION_A_FICHAS[seguimiento.dimension][seguimiento.pregunta_num][seguimiento.nivel]["tecnica"]
        dimension_label = DIMENSION_LABELS[seguimiento.dimension]

        mensaje = (
            f"{user.full_name} avanzó: completó el seguimiento de la recomendación "
            f"\"{tecnica}\" (pregunta {seguimiento.pregunta_num}: {pregunta_texto}) "
            f"en {dimension_label}, nivel {seguimiento.nivel.capitalize()}, por este momento."
        )

        profesionales = (
            self.db.query(User)
            .filter(User.role == rol.value, User.is_active.is_(True))
            .all()
        )
        for profesional in profesionales:
            notificacion_repository.crear(
                self.db,
                remitente_id=user.id,
                destinatario_id=profesional.id,
                mensaje=mensaje,
            )

    def completar_manualmente(self, user: User, seguimiento_id) -> SeguimientoResponse:
        seguimiento = self.repo.obtener_seguimiento_por_id(seguimiento_id, user.id)
        if not seguimiento:
            raise ValueError("Seguimiento no encontrado")
        if seguimiento.estado == "completada":
            raise ValueError("Esta recomendación ya fue marcada como completada")
        if seguimiento.total_dias_registrados < DIAS_MINIMOS_PARA_COMPLETAR:
            raise ValueError(
                f"Registra al menos {DIAS_MINIMOS_PARA_COMPLETAR} día antes de marcarla "
                "como completada"
            )

        seguimiento.estado = "completada"
        seguimiento.completada_at = datetime.now(timezone.utc)
        self.repo.guardar_seguimiento(seguimiento)

        GamificacionService(self.db).otorgar_xp_externo(
            user, XP_POR_COMPLETAR, "recomendacion_completada", str(seguimiento.id)
        )
        self._notificar_profesionales(user, seguimiento)

        return SeguimientoResponse.model_validate(seguimiento)

    def historial(self, user: User, seguimiento_id, limite: int = 60) -> list[RegistroDiarioResponse]:
        seguimiento = self.repo.obtener_seguimiento_por_id(seguimiento_id, user.id)
        if not seguimiento:
            raise ValueError("Seguimiento no encontrado")
        registros = self.repo.historial_registros(seguimiento.id, limite)
        return [RegistroDiarioResponse.model_validate(r) for r in registros]

    def progreso_general(self, user: User, encuesta: EncuestaHplp) -> ProgresoSeguimientoResponse:
        dimensiones = []
        for dimension, funcion in DIMENSION_A_FUNCION.items():
            tarjetas = funcion(encuesta)
            total = len(tarjetas)

            seguimientos = self.repo.obtener_seguimientos_dimension(user.id, dimension)
            por_clave = {(s.pregunta_num, s.nivel): s for s in seguimientos}
            completadas = 0
            registradas_hoy = 0
            hoy = hoy_bogota()
            for tarjeta in tarjetas:
                seguimiento = por_clave.get((tarjeta["pregunta_num"], tarjeta["nivel"]))
                if seguimiento is None:
                    continue
                if seguimiento.estado == "completada":
                    completadas += 1
                elif seguimiento.ultima_fecha_registro == hoy:
                    registradas_hoy += 1
            activas = total - completadas

            mensaje_cierre = MENSAJE_CIERRE if total > 0 and completadas == total else None

            dimensiones.append(
                ProgresoDimension(
                    dimension=dimension,
                    dimension_label=DIMENSION_LABELS[dimension],
                    total=total,
                    activas=activas,
                    completadas=completadas,
                    registradas_hoy=registradas_hoy,
                    mensaje_cierre=mensaje_cierre,
                )
            )
        return ProgresoSeguimientoResponse(dimensiones=dimensiones)
