import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.gamificacion import MisionDiaria, XpEvento


class GamificacionRepository:

    def __init__(self, db: Session):
        self.db = db

    def obtener_misiones_dia(self, user_id: uuid.UUID, fecha: date) -> list[MisionDiaria]:
        return (
            self.db.query(MisionDiaria)
            .filter(MisionDiaria.user_id == user_id, MisionDiaria.fecha == fecha)
            .order_by(MisionDiaria.created_at)
            .all()
        )

    def obtener_mision(self, mision_id: uuid.UUID, user_id: uuid.UUID) -> MisionDiaria | None:
        return (
            self.db.query(MisionDiaria)
            .filter(MisionDiaria.id == mision_id, MisionDiaria.user_id == user_id)
            .first()
        )

    def crear_misiones(self, misiones: list[MisionDiaria]) -> list[MisionDiaria]:
        self.db.add_all(misiones)
        self.db.commit()
        for mision in misiones:
            self.db.refresh(mision)
        return misiones

    def guardar_mision(self, mision: MisionDiaria) -> MisionDiaria:
        self.db.commit()
        self.db.refresh(mision)
        return mision

    def tareas_recientes(self, user_id: uuid.UUID, dias: int = 2) -> set[str]:
        from datetime import timedelta

        desde = date.today() - timedelta(days=dias)
        filas = (
            self.db.query(MisionDiaria.tarea_id)
            .filter(MisionDiaria.user_id == user_id, MisionDiaria.fecha >= desde)
            .all()
        )
        return {fila[0] for fila in filas}

    def registrar_xp(self, evento: XpEvento) -> XpEvento:
        self.db.add(evento)
        self.db.commit()
        self.db.refresh(evento)
        return evento

    def ya_otorgo_motivo(self, user_id: uuid.UUID, motivo: str, referencia_id: str | None = None) -> bool:
        q = self.db.query(XpEvento).filter(
            XpEvento.user_id == user_id,
            XpEvento.motivo == motivo,
        )
        if referencia_id is not None:
            q = q.filter(XpEvento.referencia_id == referencia_id)
        return q.first() is not None

    def historial(self, user_id: uuid.UUID, limite: int = 20) -> list[XpEvento]:
        return (
            self.db.query(XpEvento)
            .filter(XpEvento.user_id == user_id)
            .order_by(XpEvento.created_at.desc())
            .limit(limite)
            .all()
        )
