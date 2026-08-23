import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.seguimiento_recomendacion import RegistroDiarioSeguimiento, SeguimientoRecomendacion


class SeguimientoRecomendacionRepository:

    def __init__(self, db: Session):
        self.db = db

    def obtener_seguimiento(
        self, user_id: uuid.UUID, dimension: str, pregunta_num: int, nivel: str,
    ) -> SeguimientoRecomendacion | None:
        return (
            self.db.query(SeguimientoRecomendacion)
            .filter(
                SeguimientoRecomendacion.user_id == user_id,
                SeguimientoRecomendacion.dimension == dimension,
                SeguimientoRecomendacion.pregunta_num == pregunta_num,
                SeguimientoRecomendacion.nivel == nivel,
            )
            .first()
        )

    def obtener_seguimiento_por_id(
        self, seguimiento_id: uuid.UUID, user_id: uuid.UUID,
    ) -> SeguimientoRecomendacion | None:
        return (
            self.db.query(SeguimientoRecomendacion)
            .filter(
                SeguimientoRecomendacion.id == seguimiento_id,
                SeguimientoRecomendacion.user_id == user_id,
            )
            .first()
        )

    def obtener_seguimientos_dimension(
        self, user_id: uuid.UUID, dimension: str,
    ) -> list[SeguimientoRecomendacion]:
        return (
            self.db.query(SeguimientoRecomendacion)
            .filter(
                SeguimientoRecomendacion.user_id == user_id,
                SeguimientoRecomendacion.dimension == dimension,
            )
            .all()
        )

    def crear_seguimiento(self, seguimiento: SeguimientoRecomendacion) -> SeguimientoRecomendacion:
        self.db.add(seguimiento)
        self.db.commit()
        self.db.refresh(seguimiento)
        return seguimiento

    def guardar_seguimiento(self, seguimiento: SeguimientoRecomendacion) -> SeguimientoRecomendacion:
        self.db.commit()
        self.db.refresh(seguimiento)
        return seguimiento

    def obtener_registro_dia(
        self, seguimiento_id: uuid.UUID, fecha: date,
    ) -> RegistroDiarioSeguimiento | None:
        return (
            self.db.query(RegistroDiarioSeguimiento)
            .filter(
                RegistroDiarioSeguimiento.seguimiento_id == seguimiento_id,
                RegistroDiarioSeguimiento.fecha == fecha,
            )
            .first()
        )

    def crear_registro(self, registro: RegistroDiarioSeguimiento) -> RegistroDiarioSeguimiento:
        self.db.add(registro)
        self.db.commit()
        self.db.refresh(registro)
        return registro

    def historial_registros(
        self, seguimiento_id: uuid.UUID, limite: int = 60,
    ) -> list[RegistroDiarioSeguimiento]:
        return (
            self.db.query(RegistroDiarioSeguimiento)
            .filter(RegistroDiarioSeguimiento.seguimiento_id == seguimiento_id)
            .order_by(RegistroDiarioSeguimiento.fecha.desc())
            .limit(limite)
            .all()
        )
