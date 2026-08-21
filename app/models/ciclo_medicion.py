from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

LINEA_BASE = "linea_base"
SEGUIMIENTO = "seguimiento"


def como_utc(valor: datetime) -> datetime:
    """Devuelve la fecha con zona horaria, asumiendo UTC si no la trae.

    SQLite (el motor de los tests) no guarda la zona, así que al releer una
    fecha vuelve sin `tzinfo` y compararla con `now(timezone.utc)` reventaría.
    """
    return valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)


class CicloMedicion(Base):
    """Una aplicación de la encuesta en el tiempo.

    La **línea base** es un ciclo permanente y sin fecha de cierre: ahí cae la
    primera encuesta de cada persona, incluida la de quien se registre dentro de
    un año. Los **seguimientos** son ventanas con fecha y solo aplican a quien ya
    tiene una encuesta anterior, que es lo que los vuelve comparables.

    El estado (programado, abierto, cerrado) no se guarda en una columna: se
    deduce de las fechas. Así el cierre no depende de ningún proceso agendado,
    que el proyecto no tiene, y basta con mover `fecha_cierre` para extender,
    cerrar antes o reabrir una medición.
    """

    __tablename__ = "ciclos_medicion"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    numero = Column(Integer, nullable=False)
    nombre = Column(String(100), nullable=False)
    tipo = Column(String(20), nullable=False, default=SEGUIMIENTO)
    fecha_apertura = Column(DateTime(timezone=True), nullable=False)
    # NULL = sin cierre previsto. La línea base siempre queda así.
    fecha_cierre = Column(DateTime(timezone=True), nullable=True)
    creado_por = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def estado(self, ahora: datetime | None = None) -> str:
        """`programado` | `abierto` | `cerrado`, según las fechas."""
        ahora = ahora or datetime.now(timezone.utc)
        if como_utc(self.fecha_apertura) > ahora:
            return "programado"
        if self.fecha_cierre is not None and como_utc(self.fecha_cierre) <= ahora:
            return "cerrado"
        return "abierto"

    @property
    def esta_abierto(self) -> bool:
        return self.estado() == "abierto"

    def __repr__(self):
        return f"<CicloMedicion {self.numero} {self.nombre} ({self.tipo})>"
