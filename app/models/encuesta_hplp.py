from sqlalchemy import Column, Integer, String, Float, DateTime, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base


class EncuestaHplp(Base):
    __tablename__ = "encuestas_hplp"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    fecha_respuesta = Column(DateTime(timezone=True), server_default=func.now())
    # Medición a la que pertenece la respuesta (ciclos_medicion.id). Es lo que
    # permite comparar la línea base con cada seguimiento.
    ciclo_id = Column(Integer, nullable=True, index=True)
    consentimiento_aceptado_en = Column(DateTime(timezone=True), nullable=True)

    # ── Relaciones Interpersonales (9 ítems, prefijo ri_) ──────────────────
    ri_item_01 = Column(SmallInteger, nullable=False)
    ri_item_07 = Column(SmallInteger, nullable=False)
    ri_item_13 = Column(SmallInteger, nullable=False)
    ri_item_20 = Column(SmallInteger, nullable=False)
    ri_item_26 = Column(SmallInteger, nullable=False)
    ri_item_32 = Column(SmallInteger, nullable=False)
    ri_item_38 = Column(SmallInteger, nullable=False)
    ri_item_45 = Column(SmallInteger, nullable=False)
    ri_item_50 = Column(SmallInteger, nullable=False)
    ri_indice = Column(Float)   # 0 – 100
    ri_nivel  = Column(String(20))

    # ── Nutrición (10 ítems, prefijo n_) ───────────────────────────────────
    n_item_02 = Column(SmallInteger, nullable=False)
    n_item_08 = Column(SmallInteger, nullable=False)
    n_item_14 = Column(SmallInteger, nullable=False)
    n_item_21 = Column(SmallInteger, nullable=False)
    n_item_27 = Column(SmallInteger, nullable=False)
    n_item_33 = Column(SmallInteger, nullable=False)
    n_item_39 = Column(SmallInteger, nullable=False)
    n_item_40 = Column(SmallInteger, nullable=False)
    n_item_46 = Column(SmallInteger, nullable=False)
    n_item_51 = Column(SmallInteger, nullable=False)
    n_indice = Column(Float)
    n_nivel  = Column(String(20))

    # ── Responsabilidad en Salud (7 ítems, prefijo rs_) ────────────────────
    rs_item_03 = Column(SmallInteger, nullable=False)
    rs_item_09 = Column(SmallInteger, nullable=False)
    rs_item_15 = Column(SmallInteger, nullable=False)
    rs_item_22 = Column(SmallInteger, nullable=False)
    rs_item_28 = Column(SmallInteger, nullable=False)
    rs_item_34 = Column(SmallInteger, nullable=False)
    rs_item_41 = Column(SmallInteger, nullable=False)
    rs_indice = Column(Float)
    rs_nivel  = Column(String(20))

    # ── Actividad Física (9 ítems, prefijo af_) ────────────────────────────
    af_item_04 = Column(SmallInteger, nullable=False)
    af_item_10 = Column(SmallInteger, nullable=False)
    af_item_16 = Column(SmallInteger, nullable=False)
    af_item_17 = Column(SmallInteger, nullable=False)
    af_item_23 = Column(SmallInteger, nullable=False)
    af_item_29 = Column(SmallInteger, nullable=False)
    af_item_35 = Column(SmallInteger, nullable=False)
    af_item_42 = Column(SmallInteger, nullable=False)
    af_item_47 = Column(SmallInteger, nullable=False)
    af_indice = Column(Float)
    af_nivel  = Column(String(20))

    # ── Manejo del Estrés (8 ítems, prefijo me_) ───────────────────────────
    me_item_05 = Column(SmallInteger, nullable=False)
    me_item_11 = Column(SmallInteger, nullable=False)
    me_item_18 = Column(SmallInteger, nullable=False)
    me_item_24 = Column(SmallInteger, nullable=False)
    me_item_30 = Column(SmallInteger, nullable=False)
    me_item_36 = Column(SmallInteger, nullable=False)
    me_item_43 = Column(SmallInteger, nullable=False)
    me_item_48 = Column(SmallInteger, nullable=False)
    me_indice = Column(Float)
    me_nivel  = Column(String(20))

    # ── Psicología Positiva (9 ítems, prefijo pp_) ─────────────────────────
    pp_item_06 = Column(SmallInteger, nullable=False)
    pp_item_12 = Column(SmallInteger, nullable=False)
    pp_item_19 = Column(SmallInteger, nullable=False)
    pp_item_25 = Column(SmallInteger, nullable=False)
    pp_item_31 = Column(SmallInteger, nullable=False)
    pp_item_37 = Column(SmallInteger, nullable=False)
    pp_item_44 = Column(SmallInteger, nullable=False)
    pp_item_49 = Column(SmallInteger, nullable=False)
    pp_item_52 = Column(SmallInteger, nullable=False)
    pp_indice = Column(Float)
    pp_nivel  = Column(String(20))

    # ── Global ─────────────────────────────────────────────────────────────
    puntaje_crudo = Column(Integer)     # suma 52 ítems → rango 52–208
    indice_global = Column(Float)       # 0 – 100
    nivel_global  = Column(String(20))  # Pobre | Moderado | Bueno | Excelente
