-- =============================================================
-- SCHEMA: Tabla encuestas_hplp
-- Instrumento: HPLP-II ASD (52 ítems, 6 dimensiones)
-- Metodología: PEPS II  →  índice = (promedio - 1) / 3 × 100
-- Niveles globales por puntaje crudo:
--   Pobre 52–90 | Moderado 91–129 | Bueno 130–168 | Excelente 169–208
-- Correr: psql -d nombre_bd -f schema.sql
-- =============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================
-- MIGRACIÓN: Agregar facultad y tipo_usuario a la tabla users
-- Ejecutar solo si las columnas no existen aún.
-- =============================================================
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS facultad     VARCHAR(200),
    ADD COLUMN IF NOT EXISTS tipo_usuario VARCHAR(50);
-- tipo_usuario: 'estudiante' | 'docente' | 'administrativo'

CREATE TABLE IF NOT EXISTS encuestas_hplp (
    id              SERIAL PRIMARY KEY,
    usuario_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fecha_respuesta TIMESTAMPTZ DEFAULT NOW(),

    -- ─────────────────────────────────────────────────────────
    -- DIMENSIÓN 1: Relaciones Interpersonales (RI) — 9 ítems
    -- PEPS II ítems: 1, 7, 13, 19, 25, 31, 37, 43, 49
    -- ─────────────────────────────────────────────────────────
    ri_item_01  SMALLINT NOT NULL CHECK (ri_item_01  BETWEEN 1 AND 4),
    ri_item_07  SMALLINT NOT NULL CHECK (ri_item_07  BETWEEN 1 AND 4),
    ri_item_13  SMALLINT NOT NULL CHECK (ri_item_13  BETWEEN 1 AND 4),
    ri_item_20  SMALLINT NOT NULL CHECK (ri_item_20  BETWEEN 1 AND 4),
    ri_item_26  SMALLINT NOT NULL CHECK (ri_item_26  BETWEEN 1 AND 4),
    ri_item_32  SMALLINT NOT NULL CHECK (ri_item_32  BETWEEN 1 AND 4),
    ri_item_38  SMALLINT NOT NULL CHECK (ri_item_38  BETWEEN 1 AND 4),
    ri_item_45  SMALLINT NOT NULL CHECK (ri_item_45  BETWEEN 1 AND 4),
    ri_item_50  SMALLINT NOT NULL CHECK (ri_item_50  BETWEEN 1 AND 4),
    ri_indice   NUMERIC(6,2),   -- 0 – 100
    ri_nivel    VARCHAR(20),    -- Pobre | Moderado | Bueno | Excelente

    -- ─────────────────────────────────────────────────────────
    -- DIMENSIÓN 2: Nutrición (N) — 10 ítems
    -- PEPS II ítems: 2, 8, 14, 20, 26, 32, 38, 44, 50
    -- ─────────────────────────────────────────────────────────
    n_item_02  SMALLINT NOT NULL CHECK (n_item_02  BETWEEN 1 AND 4),
    n_item_08  SMALLINT NOT NULL CHECK (n_item_08  BETWEEN 1 AND 4),
    n_item_14  SMALLINT NOT NULL CHECK (n_item_14  BETWEEN 1 AND 4),
    n_item_21  SMALLINT NOT NULL CHECK (n_item_21  BETWEEN 1 AND 4),
    n_item_27  SMALLINT NOT NULL CHECK (n_item_27  BETWEEN 1 AND 4),
    n_item_33  SMALLINT NOT NULL CHECK (n_item_33  BETWEEN 1 AND 4),
    n_item_39  SMALLINT NOT NULL CHECK (n_item_39  BETWEEN 1 AND 4),
    n_item_40  SMALLINT NOT NULL CHECK (n_item_40  BETWEEN 1 AND 4),
    n_item_46  SMALLINT NOT NULL CHECK (n_item_46  BETWEEN 1 AND 4),
    n_item_51  SMALLINT NOT NULL CHECK (n_item_51  BETWEEN 1 AND 4),
    n_indice   NUMERIC(6,2),
    n_nivel    VARCHAR(20),

    -- ─────────────────────────────────────────────────────────
    -- DIMENSIÓN 3: Responsabilidad en Salud (RS) — 7 ítems
    -- PEPS II ítems: 3, 9, 15, 21, 27, 33, 39, 45, 51
    -- ─────────────────────────────────────────────────────────
    rs_item_03  SMALLINT NOT NULL CHECK (rs_item_03  BETWEEN 1 AND 4),
    rs_item_09  SMALLINT NOT NULL CHECK (rs_item_09  BETWEEN 1 AND 4),
    rs_item_15  SMALLINT NOT NULL CHECK (rs_item_15  BETWEEN 1 AND 4),
    rs_item_22  SMALLINT NOT NULL CHECK (rs_item_22  BETWEEN 1 AND 4),
    rs_item_28  SMALLINT NOT NULL CHECK (rs_item_28  BETWEEN 1 AND 4),
    rs_item_34  SMALLINT NOT NULL CHECK (rs_item_34  BETWEEN 1 AND 4),
    rs_item_41  SMALLINT NOT NULL CHECK (rs_item_41  BETWEEN 1 AND 4),
    rs_indice   NUMERIC(6,2),
    rs_nivel    VARCHAR(20),

    -- ─────────────────────────────────────────────────────────
    -- DIMENSIÓN 4: Actividad Física (AF) — 9 ítems
    -- PEPS II ítems: 4, 10, 16, 22, 28, 34, 40, 46
    -- ─────────────────────────────────────────────────────────
    af_item_04  SMALLINT NOT NULL CHECK (af_item_04  BETWEEN 1 AND 4),
    af_item_10  SMALLINT NOT NULL CHECK (af_item_10  BETWEEN 1 AND 4),
    af_item_16  SMALLINT NOT NULL CHECK (af_item_16  BETWEEN 1 AND 4),
    af_item_17  SMALLINT NOT NULL CHECK (af_item_17  BETWEEN 1 AND 4),
    af_item_23  SMALLINT NOT NULL CHECK (af_item_23  BETWEEN 1 AND 4),
    af_item_29  SMALLINT NOT NULL CHECK (af_item_29  BETWEEN 1 AND 4),
    af_item_35  SMALLINT NOT NULL CHECK (af_item_35  BETWEEN 1 AND 4),
    af_item_42  SMALLINT NOT NULL CHECK (af_item_42  BETWEEN 1 AND 4),
    af_item_47  SMALLINT NOT NULL CHECK (af_item_47  BETWEEN 1 AND 4),
    af_indice   NUMERIC(6,2),
    af_nivel    VARCHAR(20),

    -- ─────────────────────────────────────────────────────────
    -- DIMENSIÓN 5: Manejo del Estrés (ME) — 8 ítems
    -- PEPS II ítems: 5, 11, 17, 23, 29, 35, 41, 47
    -- ─────────────────────────────────────────────────────────
    me_item_05  SMALLINT NOT NULL CHECK (me_item_05  BETWEEN 1 AND 4),
    me_item_11  SMALLINT NOT NULL CHECK (me_item_11  BETWEEN 1 AND 4),
    me_item_18  SMALLINT NOT NULL CHECK (me_item_18  BETWEEN 1 AND 4),
    me_item_24  SMALLINT NOT NULL CHECK (me_item_24  BETWEEN 1 AND 4),
    me_item_30  SMALLINT NOT NULL CHECK (me_item_30  BETWEEN 1 AND 4),
    me_item_36  SMALLINT NOT NULL CHECK (me_item_36  BETWEEN 1 AND 4),
    me_item_43  SMALLINT NOT NULL CHECK (me_item_43  BETWEEN 1 AND 4),
    me_item_48  SMALLINT NOT NULL CHECK (me_item_48  BETWEEN 1 AND 4),
    me_indice   NUMERIC(6,2),
    me_nivel    VARCHAR(20),

    -- ─────────────────────────────────────────────────────────
    -- DIMENSIÓN 6: Psicología Positiva (PP) — 9 ítems
    -- PEPS II ítems: 6, 12, 18, 24, 30, 36, 42, 48, 52
    -- ─────────────────────────────────────────────────────────
    pp_item_06  SMALLINT NOT NULL CHECK (pp_item_06  BETWEEN 1 AND 4),
    pp_item_12  SMALLINT NOT NULL CHECK (pp_item_12  BETWEEN 1 AND 4),
    pp_item_19  SMALLINT NOT NULL CHECK (pp_item_19  BETWEEN 1 AND 4),
    pp_item_25  SMALLINT NOT NULL CHECK (pp_item_25  BETWEEN 1 AND 4),
    pp_item_31  SMALLINT NOT NULL CHECK (pp_item_31  BETWEEN 1 AND 4),
    pp_item_37  SMALLINT NOT NULL CHECK (pp_item_37  BETWEEN 1 AND 4),
    pp_item_44  SMALLINT NOT NULL CHECK (pp_item_44  BETWEEN 1 AND 4),
    pp_item_49  SMALLINT NOT NULL CHECK (pp_item_49  BETWEEN 1 AND 4),
    pp_item_52  SMALLINT NOT NULL CHECK (pp_item_52  BETWEEN 1 AND 4),
    pp_indice   NUMERIC(6,2),
    pp_nivel    VARCHAR(20),

    -- ─────────────────────────────────────────────────────────
    -- GLOBAL
    -- ─────────────────────────────────────────────────────────
    puntaje_crudo  SMALLINT,        -- suma 52 ítems → rango 52–208
    indice_global  NUMERIC(6,2),    -- 0 – 100
    nivel_global   VARCHAR(20)      -- Pobre | Moderado | Bueno | Excelente
);

CREATE INDEX IF NOT EXISTS idx_encuesta_usuario ON encuestas_hplp (usuario_id);
CREATE INDEX IF NOT EXISTS idx_encuesta_fecha   ON encuestas_hplp (fecha_respuesta);
