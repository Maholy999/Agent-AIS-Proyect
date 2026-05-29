-- ============================================================
-- FraudIA Claims — Schema PostgreSQL
-- ============================================================

-- Extensiones
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================
-- TABLA: usuarios
-- ============================================================
CREATE TABLE IF NOT EXISTS usuarios (
    id            UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    username      VARCHAR(50)  UNIQUE NOT NULL,
    email         VARCHAR(120) UNIQUE NOT NULL,
    nombre        VARCHAR(100) NOT NULL,
    rol           VARCHAR(20)  NOT NULL DEFAULT 'analista'
                               CHECK (rol IN ('admin', 'analista', 'supervisor')),
    password_hash VARCHAR(255) NOT NULL,
    activo        BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLA: asegurados
-- ============================================================
CREATE TABLE IF NOT EXISTS asegurados (
    id_asegurado               VARCHAR(50) PRIMARY KEY,
    nombre                     VARCHAR(150) NOT NULL,
    segmento                   VARCHAR(50), -- VIP, Estándar, Corporativo, etc.
    antiguedad                 INT, -- en años
    ciudad                     VARCHAR(80),
    numero_polizas             INT NOT NULL DEFAULT 1,
    reclamos_ultimos_12_meses  INT NOT NULL DEFAULT 0,
    mora_actual                BOOLEAN NOT NULL DEFAULT FALSE,
    score_cliente_simulado     INT CHECK (score_cliente_simulado BETWEEN 0 AND 100),
    created_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLA: polizas
-- ============================================================
CREATE TABLE IF NOT EXISTS polizas (
    id_poliza         VARCHAR(50) PRIMARY KEY,
    id_asegurado      VARCHAR(50) NOT NULL REFERENCES asegurados(id_asegurado) ON DELETE CASCADE,
    ramo              VARCHAR(50) NOT NULL CHECK (ramo IN ('Vehículos', 'Salud', 'Vida', 'Hogar', 'Generales', 'Otro')),
    fecha_inicio      DATE NOT NULL,
    fecha_fin         DATE NOT NULL,
    prima             NUMERIC(12, 2) NOT NULL CHECK (prima >= 0),
    suma_asegurada    NUMERIC(12, 2) NOT NULL CHECK (suma_asegurada >= 0),
    deducible         NUMERIC(12, 2) NOT NULL CHECK (deducible >= 0),
    canal_venta       VARCHAR(80),
    ciudad            VARCHAR(80),
    estado_poliza     VARCHAR(50),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLA: proveedores
-- ============================================================
CREATE TABLE IF NOT EXISTS proveedores (
    id                          SERIAL PRIMARY KEY,
    id_proveedor                VARCHAR(50) UNIQUE NOT NULL,
    nombre                      VARCHAR(150) UNIQUE NOT NULL,
    tipo                        VARCHAR(80),
    ciudad                      VARCHAR(80),
    reclamos_asociados          INT NOT NULL DEFAULT 0,
    monto_promedio_reclamado    NUMERIC(12, 2) DEFAULT 0 CHECK (monto_promedio_reclamado >= 0),
    porcentaje_casos_observados NUMERIC(5, 2) DEFAULT 0 CHECK (porcentaje_casos_observados BETWEEN 0 AND 100),
    antiguedad                  INT, -- en años
    total_siniestros            INT NOT NULL DEFAULT 0, -- compatibilidad
    alertas_activas             INT NOT NULL DEFAULT 0, -- compatibilidad
    score_riesgo                SMALLINT NOT NULL DEFAULT 0 CHECK (score_riesgo BETWEEN 0 AND 100), -- compatibilidad
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLA: siniestros
-- ============================================================
CREATE TABLE IF NOT EXISTS siniestros (
    id                              SERIAL PRIMARY KEY,
    id_siniestro                    VARCHAR(30) UNIQUE NOT NULL,
    id_poliza                       VARCHAR(50) REFERENCES polizas(id_poliza) ON DELETE SET NULL,
    id_asegurado                    VARCHAR(50) REFERENCES asegurados(id_asegurado) ON DELETE SET NULL,
    ramo                            VARCHAR(50) NOT NULL CHECK (ramo IN ('Vehículos', 'Salud', 'Vida', 'Hogar', 'Generales', 'Otro')),
    cobertura                       VARCHAR(80) NOT NULL CHECK (cobertura IN ('Choque', 'Robo', 'Atención médica', 'Incendio', 'Daño', 'Otro')),
    fecha_ocurrencia                DATE NOT NULL,
    fecha_reporte                   DATE NOT NULL,
    monto_reclamado                 NUMERIC(12, 2) NOT NULL CHECK (monto_reclamado >= 0),
    monto_estimado                  NUMERIC(12, 2) NOT NULL CHECK (monto_estimado >= 0),
    monto_pagado                    NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (monto_pagado >= 0),
    estado                          VARCHAR(50) NOT NULL DEFAULT 'Reserva'
                                    CHECK (estado IN ('Reserva', 'Pago Total', 'Pago Parcial', 'Anticipo', 'Negativa', 'Cierre Sin Consecuencia', 'Liquidado', 'pendiente', 'en_revision', 'cerrado', 'aprobado', 'rechazado')),
    sucursal                        VARCHAR(80),
    descripcion                     TEXT,
    documentos_completos            BOOLEAN NOT NULL DEFAULT TRUE,
    beneficiario                    VARCHAR(100), -- Taller, clínica, perito, Asegurado, etc.
    dias_desde_inicio_poliza        INT,
    dias_desde_fin_poliza           INT,
    dias_entre_ocurrencia_reporte   INT,
    historial_siniestros_asegurado  INT NOT NULL DEFAULT 0,
    etiqueta_fraude_simulada        SMALLINT DEFAULT 0 CHECK (etiqueta_fraude_simulada IN (0, 1)),
    
    -- Campos de Compatibilidad (Frontend y Modelos ML/NLP preexistentes)
    cliente                         VARCHAR(150) NOT NULL,
    tipo_siniestro                  VARCHAR(80) NOT NULL,
    fecha_incidente                 DATE NOT NULL,
    fecha_poliza                    DATE NOT NULL,
    ciudad                          VARCHAR(80),
    proveedor                       VARCHAR(150),
    proveedor_id                    INT REFERENCES proveedores(id) ON DELETE SET NULL,
    historial_reclamos              SMALLINT NOT NULL DEFAULT 0 CHECK (historial_reclamos >= 0),
    narrativa                       TEXT,

    -- Resultados del análisis
    score_riesgo                    SMALLINT NOT NULL DEFAULT 0 CHECK (score_riesgo BETWEEN 0 AND 100),
    nivel_riesgo                    VARCHAR(10) NOT NULL DEFAULT 'Bajo'
                                    CHECK (nivel_riesgo IN ('Bajo', 'Medio', 'Alto')),
    alertas                         JSONB NOT NULL DEFAULT '[]',
    score_reglas                    SMALLINT DEFAULT 0,
    score_ml                        SMALLINT DEFAULT 0,
    score_nlp                       SMALLINT DEFAULT 0,
    similitud_max                   NUMERIC(4,3) DEFAULT 0,
    es_anomalia                     BOOLEAN DEFAULT FALSE,
    explicacion_ia                  TEXT,

    -- Auditoría
    analista_id                     UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    fecha_registro                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLA: documentos
-- ============================================================
CREATE TABLE IF NOT EXISTS documentos (
    id_documento             SERIAL PRIMARY KEY,
    id_siniestro             VARCHAR(30) NOT NULL REFERENCES siniestros(id_siniestro) ON DELETE CASCADE,
    tipo_documento           VARCHAR(100) NOT NULL, -- Factura, Cédula, Informe Policial, etc.
    entregado                BOOLEAN NOT NULL DEFAULT TRUE,
    legible                  BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_emision            DATE,
    inconsistencia_detectada BOOLEAN NOT NULL DEFAULT FALSE,
    observacion              TEXT,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLA: historial_alertas
-- ============================================================
CREATE TABLE IF NOT EXISTS historial_alertas (
    id             SERIAL PRIMARY KEY,
    siniestro_id   INT NOT NULL REFERENCES siniestros(id) ON DELETE CASCADE,
    tipo_alerta    VARCHAR(60)  NOT NULL,
    descripcion    TEXT         NOT NULL,
    peso           SMALLINT     NOT NULL DEFAULT 0,
    activa         BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLA: conversaciones_ia
-- ============================================================
CREATE TABLE IF NOT EXISTS conversaciones_ia (
    id             SERIAL PRIMARY KEY,
    usuario_id     UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    titulo         VARCHAR(200),
    mensajes       JSONB NOT NULL DEFAULT '[]',
    siniestro_id   INT REFERENCES siniestros(id) ON DELETE SET NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLA: reportes
-- ============================================================
CREATE TABLE IF NOT EXISTS reportes (
    id             SERIAL PRIMARY KEY,
    titulo         VARCHAR(200) NOT NULL,
    tipo           VARCHAR(50)  NOT NULL CHECK (tipo IN ('individual', 'ejecutivo', 'alertas', 'proveedor')),
    siniestro_id   INT REFERENCES siniestros(id) ON DELETE SET NULL,
    generado_por   UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    ruta_archivo   VARCHAR(500),
    contenido_json JSONB,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- ÍNDICES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_siniestros_nivel_riesgo  ON siniestros(nivel_riesgo);
CREATE INDEX IF NOT EXISTS idx_siniestros_score         ON siniestros(score_riesgo DESC);
CREATE INDEX IF NOT EXISTS idx_siniestros_fecha         ON siniestros(fecha_registro DESC);
CREATE INDEX IF NOT EXISTS idx_siniestros_proveedor     ON siniestros(proveedor);
CREATE INDEX IF NOT EXISTS idx_siniestros_cliente       ON siniestros USING gin (to_tsvector('spanish', cliente));
CREATE INDEX IF NOT EXISTS idx_siniestros_narrativa     ON siniestros USING gin (to_tsvector('spanish', narrativa));
CREATE INDEX IF NOT EXISTS idx_alertas_siniestro        ON historial_alertas(siniestro_id);
CREATE INDEX IF NOT EXISTS idx_conv_usuario             ON conversaciones_ia(usuario_id);

-- ============================================================
-- TRIGGER: updated_at automático
-- ============================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_siniestros_updated
    BEFORE UPDATE ON siniestros
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE OR REPLACE TRIGGER trg_usuarios_updated
    BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- DATOS INICIALES: usuario admin demo
-- ============================================================
INSERT INTO usuarios (username, email, nombre, rol, password_hash)
VALUES ('admin', 'admin@fraudia.com', 'Administrador FraudIA', 'admin',
        '$2b$12$demo_hash_replace_in_production')
ON CONFLICT (username) DO NOTHING;

-- ============================================================
-- SEGURIDAD: ROW LEVEL SECURITY (RLS)
-- ============================================================
-- Se habilita RLS en todas las tablas para cerrar el acceso público no autorizado (API anon).
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE asegurados ENABLE ROW LEVEL SECURITY;
ALTER TABLE polizas ENABLE ROW LEVEL SECURITY;
ALTER TABLE proveedores ENABLE ROW LEVEL SECURITY;
ALTER TABLE siniestros ENABLE ROW LEVEL SECURITY;
ALTER TABLE documentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE historial_alertas ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversaciones_ia ENABLE ROW LEVEL SECURITY;
ALTER TABLE reportes ENABLE ROW LEVEL SECURITY;

-- IMPORTANTE PARA FUNCIONALIDAD:
-- Como el sistema gestiona su propia autenticación (Streamlit login en main.py),
-- por defecto estas reglas bloquean a cualquier persona que use la clave "anon".
-- Para que el sistema siga funcionando normalmente, debes usar la clave
-- SUPABASE_SERVICE_ROLE_KEY en lugar de SUPABASE_ANON_KEY dentro de tu .env
-- La service_role_key se salta el RLS y permite al backend operar correctamente.
