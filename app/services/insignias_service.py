"""Evalúa y otorga las insignias del estudiante.

Se calcula todo al leer (`obtener`), a partir de datos que la gamificación de
Duvan y el seguimiento de recomendaciones ya guardan. Cuando una insignia pasa
a ganada se registra en `insignias_usuario` y se otorga su bonus de XP con el
mismo mecanismo de Duvan (`otorgar_xp_externo`).
"""
from __future__ import annotations

from sqlalchemy import distinct, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.data.insignias_catalogo import INSIGNIAS, InsigniaDef
from app.models.encuesta_hplp import EncuestaHplp
from app.models.gamificacion import MisionDiaria
from app.models.insignia import InsigniaUsuario
from app.models.seguimiento_recomendacion import SeguimientoRecomendacion
from app.models.user import User
from app.schemas.insignia import InsigniaEstado, InsigniasResponse
from app.services.gamificacion_service import GamificacionService
from app.services.seguimiento_recomendacion_service import DIMENSION_A_FUNCION

_ORDEN_NIVEL = {"Pobre": 0, "Moderado": 1, "Bueno": 2, "Excelente": 3}


class InsigniasService:
    def __init__(self, db: Session):
        self.db = db

    # ── criterios ─────────────────────────────────────────────────────────
    def _primer_paso(self, uid) -> bool:
        return self.db.query(EncuestaHplp).filter(EncuestaHplp.usuario_id == uid).count() >= 1

    def _mejor_racha_min(self, uid, minimo: int) -> bool:
        return (
            self.db.query(SeguimientoRecomendacion)
            .filter(
                SeguimientoRecomendacion.user_id == uid,
                SeguimientoRecomendacion.mejor_racha >= minimo,
            )
            .count()
            >= 1
        )

    def _explorador(self, uid) -> bool:
        n = (
            self.db.query(func.count(distinct(SeguimientoRecomendacion.dimension)))
            .filter(
                SeguimientoRecomendacion.user_id == uid,
                SeguimientoRecomendacion.total_dias_registrados > 0,
            )
            .scalar()
        )
        return (n or 0) >= 6

    def _semana_perfecta(self, uid) -> bool:
        filas = (
            self.db.query(
                MisionDiaria.fecha,
                func.count(MisionDiaria.id),
                func.count(MisionDiaria.completada_at),
            )
            .filter(MisionDiaria.user_id == uid)
            .group_by(MisionDiaria.fecha)
            .order_by(MisionDiaria.fecha)
            .all()
        )
        perfectas = sorted(f for f, total, hechas in filas if total > 0 and total == hechas)
        seguidas = 1
        for i in range(1, len(perfectas)):
            if (perfectas[i] - perfectas[i - 1]).days == 1:
                seguidas += 1
                if seguidas >= 7:
                    return True
            else:
                seguidas = 1
        return False

    def _evolucion(self, uid) -> bool:
        encuestas = (
            self.db.query(EncuestaHplp)
            .filter(EncuestaHplp.usuario_id == uid)
            .order_by(EncuestaHplp.fecha_respuesta.asc())
            .all()
        )
        if len(encuestas) < 2:
            return False
        base = _ORDEN_NIVEL.get(encuestas[0].nivel_global, -1)
        ultimo = _ORDEN_NIVEL.get(encuestas[-1].nivel_global, -1)
        return ultimo > base

    def _plan_cumplido(self, uid, dimension: str) -> bool:
        encuesta = (
            self.db.query(EncuestaHplp)
            .filter(EncuestaHplp.usuario_id == uid)
            .order_by(EncuestaHplp.fecha_respuesta.desc())
            .first()
        )
        if encuesta is None:
            return False
        tarjetas = DIMENSION_A_FUNCION[dimension](encuesta)
        if not tarjetas:
            return False
        pares = {(t["pregunta_num"], t["nivel"]) for t in tarjetas}
        completadas = {
            (s.pregunta_num, s.nivel)
            for s in self.db.query(SeguimientoRecomendacion)
            .filter(
                SeguimientoRecomendacion.user_id == uid,
                SeguimientoRecomendacion.dimension == dimension,
                SeguimientoRecomendacion.estado == "completada",
            )
            .all()
        }
        return pares.issubset(completadas)

    def _cumple(self, insignia: InsigniaDef, uid) -> bool:
        if insignia.dimension:
            return self._plan_cumplido(uid, insignia.dimension)
        return {
            "primer_paso": lambda: self._primer_paso(uid),
            "constancia_7": lambda: self._mejor_racha_min(uid, 7),
            "imparable_21": lambda: self._mejor_racha_min(uid, 21),
            "explorador": lambda: self._explorador(uid),
            "semana_perfecta": lambda: self._semana_perfecta(uid),
            "evolucion": lambda: self._evolucion(uid),
        }.get(insignia.id, lambda: False)()

    # ── API ───────────────────────────────────────────────────────────────
    def _ganadas(self, user_id) -> dict[str, InsigniaUsuario]:
        return {
            row.insignia_id: row
            for row in self.db.query(InsigniaUsuario).filter(InsigniaUsuario.user_id == user_id).all()
        }

    def obtener(self, user: User) -> InsigniasResponse:
        ganadas = self._ganadas(user.id)
        gamificacion = GamificacionService(self.db)
        nuevas: set[str] = set()
        relectura = False

        try:
            for insignia in INSIGNIAS:
                if insignia.id in ganadas:
                    continue
                if self._cumple(insignia, user.id):
                    self.db.add(InsigniaUsuario(user_id=user.id, insignia_id=insignia.id))
                    gamificacion.otorgar_xp_externo(user, insignia.xp, "insignia", insignia.id)
                    nuevas.add(insignia.id)

            if nuevas:
                self.db.commit()
                relectura = True
        except IntegrityError:
            # Dos peticiones a la vez (dos pestañas, o entrar al perfil con la
            # del panel todavía en vuelo) evalúan lo mismo y las dos intentan
            # otorgar la misma insignia. La que pierde se queda con lo que
            # alcanzó a guardar la otra en vez de responder 500.
            self.db.rollback()
            nuevas = set()
            relectura = True

        if relectura:
            ganadas = self._ganadas(user.id)

        estados = [
            InsigniaEstado(
                id=i.id,
                nombre=i.nombre,
                descripcion=i.descripcion,
                criterio=i.criterio,
                icono=i.icono,
                rareza=i.rareza,
                xp=i.xp,
                ganada=i.id in ganadas,
                otorgada_at=ganadas[i.id].otorgada_at if i.id in ganadas else None,
                nueva=i.id in nuevas,
            )
            for i in INSIGNIAS
        ]
        return InsigniasResponse(
            total=len(INSIGNIAS),
            ganadas=sum(1 for e in estados if e.ganada),
            insignias=estados,
        )
