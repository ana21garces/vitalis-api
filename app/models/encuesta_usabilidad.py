from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class EncuestaUsabilidad(Base):
    __tablename__ = "encuestas_usabilidad"
    # Una respuesta por (usuario, rol): el admin puede responder una vez por cada
    # área de bienestar que administra, y cada respuesta queda con ese rol.
    __table_args__ = (UniqueConstraint("usuario_id", "rol", name="uq_usabilidad_usuario_rol"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    rol = Column(String(50))
    fecha_respuesta = Column(DateTime(timezone=True), server_default=func.now())

    item_01 = Column(SmallInteger, nullable=False)
    item_02 = Column(SmallInteger, nullable=False)
    item_03 = Column(SmallInteger, nullable=False)
    item_04 = Column(SmallInteger, nullable=False)
    item_05 = Column(SmallInteger, nullable=False)
    item_06 = Column(SmallInteger, nullable=False)
    item_07 = Column(SmallInteger, nullable=False)
    item_08 = Column(SmallInteger, nullable=False)
    item_09 = Column(SmallInteger, nullable=False)
    item_10 = Column(SmallInteger, nullable=False)
    item_11 = Column(SmallInteger, nullable=False)
    item_12 = Column(SmallInteger, nullable=False)
    item_13 = Column(SmallInteger, nullable=False)
    item_14 = Column(SmallInteger, nullable=False)
    item_15 = Column(SmallInteger, nullable=False)
    item_16 = Column(SmallInteger, nullable=False)

    sysuse = Column(Float)
    infoqual = Column(Float)
    interqual = Column(Float)
    puntaje_global = Column(Float)
