-- =====================================================================
-- TRAMAPOS · Migración: cotizaciones
-- Ejecutar UNA vez contra la base 'tramapos' que ya tienes corriendo.
--   psql -U postgres -d tramapos -f migracion_cotizaciones.sql
-- =====================================================================

CREATE TABLE IF NOT EXISTS cotizaciones (
    id                  SERIAL PRIMARY KEY,
    numero              VARCHAR(20) NOT NULL UNIQUE,
    cliente_id          INTEGER REFERENCES clientes(id),
    cliente_nombre      VARCHAR(150),
    cliente_telefono    VARCHAR(30),
    cliente_email       VARCHAR(150),
    fecha_emision       DATE NOT NULL DEFAULT CURRENT_DATE,
    fecha_vencimiento   DATE,
    estado              VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    subtotal            NUMERIC(12,2) NOT NULL DEFAULT 0,
    descuento_manual    NUMERIC(12,2) NOT NULL DEFAULT 0,
    total               NUMERIC(12,2) NOT NULL DEFAULT 0,
    notas               TEXT,
    usuario_id          INTEGER REFERENCES usuarios(id),
    venta_id            INTEGER REFERENCES ventas(id),
    creado_en           TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_cotizaciones_estado ON cotizaciones(estado);
CREATE INDEX IF NOT EXISTS idx_cotizaciones_cliente ON cotizaciones(cliente_id);

CREATE TABLE IF NOT EXISTS detalles_cotizacion (
    id              SERIAL PRIMARY KEY,
    cotizacion_id   INTEGER NOT NULL REFERENCES cotizaciones(id) ON DELETE CASCADE,
    variante_id     INTEGER NOT NULL REFERENCES variantes_producto(id),
    cantidad        NUMERIC(12,2) NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(12,2) NOT NULL CHECK (precio_unitario >= 0)
);
CREATE INDEX IF NOT EXISTS idx_detalles_cotizacion_cotizacion ON detalles_cotizacion(cotizacion_id);
