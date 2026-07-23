-- =====================================================================
-- SURTHILANAS · MODELO DE DATOS RELACIONAL (PostgreSQL 15+)
-- Arquitectura multicanal (POS físico + futuro E-commerce)
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- búsqueda ágil por nombre/SKU (F2)

-- ---------------------------------------------------------------------
-- ENUMS: modelan estados de negocio como tipos, no strings mágicos
-- ---------------------------------------------------------------------
CREATE TYPE canal_venta AS ENUM ('POS', 'WEB');
CREATE TYPE estado_venta AS ENUM ('COMPLETADA', 'ANULADA', 'PENDIENTE_PAGO');
CREATE TYPE metodo_pago AS ENUM ('EFECTIVO', 'DATAFONO', 'TRANSFERENCIA', 'PASARELA_WEB', 'MIXTO');
CREATE TYPE tipo_movimiento_puntos AS ENUM ('GANADO', 'REDIMIDO', 'AJUSTE_MANUAL', 'EXPIRADO');
CREATE TYPE estado_sesion_caja AS ENUM ('ABIERTA', 'CERRADA');
CREATE TYPE estado_factura_dian AS ENUM ('NO_APLICA', 'PENDIENTE', 'ENVIADA', 'ACEPTADA', 'RECHAZADA');

-- ---------------------------------------------------------------------
-- CATEGORÍAS (jerarquía simple: Lanas > Hilo Guajira, Herramientas, etc.)
-- ---------------------------------------------------------------------
CREATE TABLE categorias (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(80) NOT NULL UNIQUE,
    categoria_padre_id INTEGER REFERENCES categorias(id) ON DELETE SET NULL,
    activo          BOOLEAN NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- PRODUCTOS (concepto general: "Hilo Guajira") -> no tiene precio/stock
-- ---------------------------------------------------------------------
CREATE TABLE productos (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(150) NOT NULL,
    descripcion     TEXT,
    categoria_id    INTEGER REFERENCES categorias(id) ON DELETE SET NULL,
    unidad_medida   VARCHAR(20) NOT NULL DEFAULT 'unidad', -- unidad, madeja, metro, kg
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    visible_web     BOOLEAN NOT NULL DEFAULT FALSE, -- flag de escalabilidad e-commerce
    favorito        BOOLEAN NOT NULL DEFAULT FALSE, -- marcado por el cajero, acceso rápido en el POS
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_en  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_productos_nombre_trgm ON productos USING gin (nombre gin_trgm_ops);
CREATE INDEX idx_productos_categoria ON productos(categoria_id);

-- ---------------------------------------------------------------------
-- VARIANTES DE PRODUCTO (color, grosor) -> aquí SÍ viven precio y stock
-- Evita redundancia: N variantes por 1 producto, sin duplicar descripción
-- ---------------------------------------------------------------------
CREATE TABLE variantes_producto (
    id              SERIAL PRIMARY KEY,
    producto_id     INTEGER NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    sku             VARCHAR(50) NOT NULL UNIQUE,
    codigo_barras   VARCHAR(50) UNIQUE,
    color           VARCHAR(60),
    grosor          VARCHAR(40),          -- ej: "Grueso", "Fino", "4mm"
    atributos_extra JSONB DEFAULT '{}',   -- para variantes futuras sin migrar schema
    precio_venta    NUMERIC(12,2) NOT NULL CHECK (precio_venta >= 0),
    costo_unitario  NUMERIC(12,2) CHECK (costo_unitario >= 0),
    porcentaje_iva  NUMERIC(5,2) NOT NULL DEFAULT 19.00 CHECK (porcentaje_iva >= 0),
    stock_actual    NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (stock_actual >= 0),
    stock_minimo    NUMERIC(12,2) NOT NULL DEFAULT 0,
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_en  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_variantes_producto_id ON variantes_producto(producto_id);
CREATE INDEX idx_variantes_sku ON variantes_producto(sku);
CREATE INDEX idx_variantes_codigo_barras ON variantes_producto(codigo_barras);
-- Alerta de stock mínimo: consulta directa, sin trigger obligatorio
CREATE INDEX idx_variantes_stock_bajo ON variantes_producto(stock_actual)
    WHERE stock_actual <= stock_minimo;

-- ---------------------------------------------------------------------
-- CLIENTES (comunidad artesanal + datos DIAN)
-- ---------------------------------------------------------------------
CREATE TABLE clientes (
    id                  SERIAL PRIMARY KEY,
    tipo_documento      VARCHAR(10) NOT NULL DEFAULT 'CC', -- CC, NIT, CE, PAS
    numero_documento    VARCHAR(30) NOT NULL,
    nombre_completo     VARCHAR(150) NOT NULL,
    email               VARCHAR(150),
    telefono            VARCHAR(30),
    direccion           TEXT,
    puntos_balance      INTEGER NOT NULL DEFAULT 0 CHECK (puntos_balance >= 0),
    puntos_totales_historicos INTEGER NOT NULL DEFAULT 0, -- NUNCA baja al redimir; define el rango de fidelización
    creado_en           TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tipo_documento, numero_documento)
);
CREATE INDEX idx_clientes_documento ON clientes(numero_documento);
CREATE INDEX idx_clientes_nombre_trgm ON clientes USING gin (nombre_completo gin_trgm_ops);

-- ---------------------------------------------------------------------
-- RANGOS DE DESCUENTO POR FIDELIZACIÓN (niveles: Bronce/Plata/Oro...)
-- Se calculan sobre puntos_totales_historicos, NO sobre el saldo
-- redimible — así un cliente no "baja de nivel" solo por canjear puntos.
-- ---------------------------------------------------------------------
CREATE TABLE rangos_descuento_fidelizacion (
    id                  SERIAL PRIMARY KEY,
    nombre              VARCHAR(50) NOT NULL UNIQUE,
    puntos_minimo       INTEGER NOT NULL CHECK (puntos_minimo >= 0),
    puntos_maximo       INTEGER,  -- NULL = sin techo (el rango más alto)
    porcentaje_descuento NUMERIC(5,2) NOT NULL CHECK (porcentaje_descuento BETWEEN 0 AND 100),
    activo              BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT chk_rango_valido CHECK (puntos_maximo IS NULL OR puntos_maximo > puntos_minimo)
);

-- ---------------------------------------------------------------------
-- USUARIOS — cuentas de acceso (cajero/admin). Va antes de cajas_fisicas
-- y ventas porque ambas la referencian como FK.
-- ---------------------------------------------------------------------
CREATE TABLE usuarios (
    id              SERIAL PRIMARY KEY,
    nombre_completo VARCHAR(150) NOT NULL,
    username        VARCHAR(50) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    rol             VARCHAR(20) NOT NULL DEFAULT 'CAJERO',
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- CAJAS FÍSICAS (terminales) — necesarias para permitir varias
-- registradoras abiertas al mismo tiempo, cada una con su propia sesión.
-- ---------------------------------------------------------------------
CREATE TABLE cajas_fisicas (
    id      SERIAL PRIMARY KEY,
    nombre  VARCHAR(50) NOT NULL UNIQUE,
    activo  BOOLEAN NOT NULL DEFAULT TRUE
);
INSERT INTO cajas_fisicas (nombre) VALUES ('Caja 1');

-- ---------------------------------------------------------------------
-- SESIONES DE CAJA (arqueo diario) — SOLO ventas POS se atan aquí
-- ---------------------------------------------------------------------
CREATE TABLE sesiones_caja (
    id                  SERIAL PRIMARY KEY,
    caja_fisica_id      INTEGER NOT NULL REFERENCES cajas_fisicas(id),
    usuario_apertura_id INTEGER NOT NULL REFERENCES usuarios(id),
    usuario_cierre_id   INTEGER REFERENCES usuarios(id),
    monto_apertura      NUMERIC(12,2) NOT NULL DEFAULT 0,
    monto_cierre_esperado NUMERIC(12,2),
    monto_cierre_real   NUMERIC(12,2),
    diferencia          NUMERIC(12,2) GENERATED ALWAYS AS (monto_cierre_real - monto_cierre_esperado) STORED,
    estado              estado_sesion_caja NOT NULL DEFAULT 'ABIERTA',
    abierta_en          TIMESTAMPTZ NOT NULL DEFAULT now(),
    cerrada_en          TIMESTAMPTZ
);
CREATE INDEX idx_sesiones_caja_estado ON sesiones_caja(estado);
-- Garantiza una sola sesión abierta POR CAJA FÍSICA (no global) — así
-- 2+ registradoras pueden operar simultáneamente, cada una con la suya.
CREATE UNIQUE INDEX idx_una_sesion_abierta_por_caja ON sesiones_caja (caja_fisica_id)
    WHERE estado = 'ABIERTA';

-- ---------------------------------------------------------------------
-- VENTAS (cabecera) — canal distingue POS vs WEB sin mezclar flujos
-- ---------------------------------------------------------------------
CREATE TABLE ventas (
    id                  BIGSERIAL PRIMARY KEY,
    uuid_publico        UUID NOT NULL DEFAULT uuid_generate_v4(), -- id seguro para exponer a la web/DIAN
    canal               canal_venta NOT NULL,
    sesion_caja_id      INTEGER REFERENCES sesiones_caja(id),     -- NULL obligatorio si canal = WEB
    cliente_id          INTEGER REFERENCES clientes(id),
    vendedor_id         INTEGER REFERENCES usuarios(id),
    subtotal            NUMERIC(12,2) NOT NULL CHECK (subtotal >= 0),
    descuento_puntos    NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (descuento_puntos >= 0),
    descuento_manual    NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (descuento_manual >= 0),
    motivo_descuento_manual VARCHAR(255),
    descuento_fidelizacion NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (descuento_fidelizacion >= 0),
    rango_fidelizacion_aplicado VARCHAR(50),
    total_iva           NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (total_iva >= 0), -- 0 mientras aplica_iva=false
    total                NUMERIC(12,2) NOT NULL CHECK (total >= 0),
    metodo_pago         metodo_pago NOT NULL,
    estado              estado_venta NOT NULL DEFAULT 'COMPLETADA',
    estado_factura_dian estado_factura_dian NOT NULL DEFAULT 'NO_APLICA',
    puntos_ganados      INTEGER NOT NULL DEFAULT 0,
    puntos_redimidos    INTEGER NOT NULL DEFAULT 0,
    creado_en           TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Regla dura a nivel de BD: una venta POS siempre tiene sesión de caja
    CONSTRAINT chk_pos_requiere_sesion CHECK (
        (canal = 'POS' AND sesion_caja_id IS NOT NULL) OR
        (canal = 'WEB' AND sesion_caja_id IS NULL)
    )
);
CREATE INDEX idx_ventas_canal_fecha ON ventas(canal, creado_en DESC);
CREATE INDEX idx_ventas_sesion_caja ON ventas(sesion_caja_id);
CREATE INDEX idx_ventas_cliente ON ventas(cliente_id);
CREATE INDEX idx_ventas_estado_dian ON ventas(estado_factura_dian) WHERE estado_factura_dian IN ('PENDIENTE');

-- ---------------------------------------------------------------------
-- DETALLE DE VENTA (líneas) — descuenta la MISMA tabla de stock
-- sin importar si la venta vino del POS o de la web
-- ---------------------------------------------------------------------
CREATE TABLE detalles_venta (
    id              BIGSERIAL PRIMARY KEY,
    venta_id        BIGINT NOT NULL REFERENCES ventas(id) ON DELETE CASCADE,
    variante_id     INTEGER NOT NULL REFERENCES variantes_producto(id),
    cantidad        NUMERIC(12,2) NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(12,2) NOT NULL CHECK (precio_unitario >= 0),
    porcentaje_iva_aplicado NUMERIC(5,2) NOT NULL DEFAULT 0, -- snapshot: el % vigente AL MOMENTO de la venta
    iva_linea       NUMERIC(12,2) NOT NULL DEFAULT 0,
    subtotal_linea  NUMERIC(12,2) GENERATED ALWAYS AS (cantidad * precio_unitario) STORED
);
CREATE INDEX idx_detalles_venta_id ON detalles_venta(venta_id);
CREATE INDEX idx_detalles_variante_id ON detalles_venta(variante_id);

-- ---------------------------------------------------------------------
-- HISTORIAL DE PUNTOS (auditoría completa de fidelización)
-- ---------------------------------------------------------------------
CREATE TABLE historial_puntos (
    id              BIGSERIAL PRIMARY KEY,
    cliente_id      INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    venta_id        BIGINT REFERENCES ventas(id),   -- NULL si es ajuste manual
    tipo_movimiento tipo_movimiento_puntos NOT NULL,
    puntos          INTEGER NOT NULL,               -- positivo=ganado, negativo=redimido
    saldo_resultante INTEGER NOT NULL,
    nota            VARCHAR(255),
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_historial_puntos_cliente ON historial_puntos(cliente_id, creado_en DESC);
CREATE INDEX idx_historial_puntos_venta ON historial_puntos(venta_id);

-- ---------------------------------------------------------------------
-- PARÁMETROS DE FIDELIZACIÓN (configurable sin tocar código)
-- ---------------------------------------------------------------------
CREATE TABLE configuracion_fidelizacion (
    id                      SMALLINT PRIMARY KEY DEFAULT 1,
    pesos_por_punto         NUMERIC(12,2) NOT NULL DEFAULT 1000, -- 1 punto c/ $1.000 COP
    valor_punto_redimido    NUMERIC(12,2) NOT NULL DEFAULT 1,    -- $ que vale 1 punto al redimir
    CONSTRAINT chk_singleton CHECK (id = 1)
);
INSERT INTO configuracion_fidelizacion (id) VALUES (1);

INSERT INTO rangos_descuento_fidelizacion (nombre, puntos_minimo, puntos_maximo, porcentaje_descuento) VALUES
    ('Bronce', 0, 99, 0),
    ('Plata', 100, 299, 5),
    ('Oro', 300, NULL, 10);

-- ---------------------------------------------------------------------
-- CONFIGURACIÓN DE EMPRESA — interruptor maestro de IVA.
-- Apagado por defecto: mientras el negocio sea persona natural no
-- obligada a declarar IVA, el sistema opera exactamente igual que sin
-- esta tabla. El día que se constituyan como empresa y queden
-- obligados, se prende desde Administración sin tocar código.
-- ---------------------------------------------------------------------
CREATE TABLE configuracion_empresa (
    id                      SMALLINT PRIMARY KEY DEFAULT 1,
    aplica_iva              BOOLEAN NOT NULL DEFAULT FALSE,
    porcentaje_iva_default  NUMERIC(5,2) NOT NULL DEFAULT 19.00,
    CONSTRAINT chk_singleton_empresa CHECK (id = 1)
);
INSERT INTO configuracion_empresa (id) VALUES (1);

-- ---------------------------------------------------------------------
-- DEVOLUCIONES — anulación total de una venta (sección separada del POS,
-- nunca se mezcla con el flujo de cobro para evitar confusión del cajero)
-- ---------------------------------------------------------------------
CREATE TABLE devoluciones (
    id              BIGSERIAL PRIMARY KEY,
    venta_id        BIGINT NOT NULL UNIQUE REFERENCES ventas(id),
    motivo          VARCHAR(255) NOT NULL,
    monto_devuelto  NUMERIC(12,2) NOT NULL,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_devoluciones_venta ON devoluciones(venta_id);

-- ---------------------------------------------------------------------
-- PROVEEDORES Y COMPRAS — registrar mercancía que llega a la tienda,
-- simétrico al flujo de ventas: sube el stock en vez de bajarlo.
-- ---------------------------------------------------------------------
CREATE TABLE proveedores (
    id                  SERIAL PRIMARY KEY,
    nombre_comercial    VARCHAR(150) NOT NULL,
    nit_o_documento     VARCHAR(30),
    telefono            VARCHAR(30),
    email               VARCHAR(150),
    direccion           TEXT,
    activo              BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en           TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_proveedores_nombre_trgm ON proveedores USING gin (nombre_comercial gin_trgm_ops);

CREATE TABLE compras (
    id                          BIGSERIAL PRIMARY KEY,
    proveedor_id                INTEGER NOT NULL REFERENCES proveedores(id),
    numero_factura_proveedor    VARCHAR(50),
    fecha_compra                DATE NOT NULL DEFAULT CURRENT_DATE,
    subtotal                    NUMERIC(12,2) NOT NULL CHECK (subtotal >= 0),
    total                       NUMERIC(12,2) NOT NULL CHECK (total >= 0),
    estado                      VARCHAR(20) NOT NULL DEFAULT 'RECIBIDA', -- RECIBIDA | ANULADA
    usuario_id                  INTEGER REFERENCES usuarios(id),
    creado_en                   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_compras_proveedor ON compras(proveedor_id);
CREATE INDEX idx_compras_fecha ON compras(fecha_compra);

CREATE TABLE detalles_compra (
    id              BIGSERIAL PRIMARY KEY,
    compra_id       BIGINT NOT NULL REFERENCES compras(id) ON DELETE CASCADE,
    variante_id     INTEGER NOT NULL REFERENCES variantes_producto(id),
    cantidad        NUMERIC(12,2) NOT NULL CHECK (cantidad > 0),
    costo_unitario  NUMERIC(12,2) NOT NULL CHECK (costo_unitario >= 0),
    subtotal_linea  NUMERIC(12,2) GENERATED ALWAYS AS (cantidad * costo_unitario) STORED
);
CREATE INDEX idx_detalles_compra_id ON detalles_compra(compra_id);
CREATE INDEX idx_detalles_compra_variante ON detalles_compra(variante_id);

-- Trigger simétrico al de ventas: AUMENTA stock al recibir mercancía.
CREATE OR REPLACE FUNCTION fn_incrementar_stock_compra() RETURNS TRIGGER AS $$
BEGIN
    UPDATE variantes_producto
    SET stock_actual = stock_actual + NEW.cantidad,
        actualizado_en = now()
    WHERE id = NEW.variante_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_incrementar_stock_compra
    AFTER INSERT ON detalles_compra
    FOR EACH ROW EXECUTE FUNCTION fn_incrementar_stock_compra();

-- ---------------------------------------------------------------------
-- FINANZAS GENERALES DEL NEGOCIO — movimientos que NO son ventas ni
-- compras de mercancía (arriendo, servicios, retiros de socios, etc.).
-- El reporte de Pérdidas y Ganancias combina esto con ventas/compras
-- reales — nadie tiene que volver a escribir una venta a mano aquí.
-- ---------------------------------------------------------------------
CREATE TABLE categorias_financieras (
    id      SERIAL PRIMARY KEY,
    nombre  VARCHAR(80) NOT NULL UNIQUE,
    tipo    VARCHAR(20) NOT NULL, -- INGRESO | GASTO
    activo  BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE movimientos_financieros (
    id              BIGSERIAL PRIMARY KEY,
    categoria_id    INTEGER NOT NULL REFERENCES categorias_financieras(id),
    fecha           DATE NOT NULL DEFAULT CURRENT_DATE,
    descripcion     VARCHAR(255),
    monto           NUMERIC(12,2) NOT NULL CHECK (monto > 0), -- siempre positivo; el signo lo da categoria.tipo
    usuario_id      INTEGER REFERENCES usuarios(id),
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_movimientos_financieros_fecha ON movimientos_financieros(fecha);
CREATE INDEX idx_movimientos_financieros_categoria ON movimientos_financieros(categoria_id);

-- ---------------------------------------------------------------------
-- COTIZACIONES — se pueden descargar/enviar, y si el cliente aprueba,
-- se convierten en una venta real de un solo paso (sin volver a
-- digitar los productos).
-- ---------------------------------------------------------------------
CREATE TABLE cotizaciones (
    id                  SERIAL PRIMARY KEY,
    numero              VARCHAR(20) NOT NULL UNIQUE, -- COT-0001, COT-0002...
    cliente_id          INTEGER REFERENCES clientes(id),
    cliente_nombre      VARCHAR(150), -- para cotizar a alguien aún no registrado
    cliente_telefono    VARCHAR(30),
    cliente_email       VARCHAR(150),
    fecha_emision       DATE NOT NULL DEFAULT CURRENT_DATE,
    fecha_vencimiento   DATE,
    estado              VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE', -- PENDIENTE|APROBADA|RECHAZADA|FACTURADA
    subtotal            NUMERIC(12,2) NOT NULL DEFAULT 0,
    descuento_manual    NUMERIC(12,2) NOT NULL DEFAULT 0,
    total               NUMERIC(12,2) NOT NULL DEFAULT 0,
    notas               TEXT,
    usuario_id          INTEGER REFERENCES usuarios(id),
    venta_id            INTEGER REFERENCES ventas(id), -- se llena al facturar
    creado_en           TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_cotizaciones_estado ON cotizaciones(estado);
CREATE INDEX idx_cotizaciones_cliente ON cotizaciones(cliente_id);

CREATE TABLE detalles_cotizacion (
    id              SERIAL PRIMARY KEY,
    cotizacion_id   INTEGER NOT NULL REFERENCES cotizaciones(id) ON DELETE CASCADE,
    variante_id     INTEGER NOT NULL REFERENCES variantes_producto(id),
    cantidad        NUMERIC(12,2) NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(12,2) NOT NULL CHECK (precio_unitario >= 0)
);
CREATE INDEX idx_detalles_cotizacion_cotizacion ON detalles_cotizacion(cotizacion_id);

-- =====================================================================
-- TRIGGER: descuenta stock automáticamente al insertar detalle_venta
-- (garantiza consistencia stock POS/WEB sin depender solo del backend)
-- =====================================================================
CREATE OR REPLACE FUNCTION fn_descontar_stock() RETURNS TRIGGER AS $$
BEGIN
    UPDATE variantes_producto
    SET stock_actual = stock_actual - NEW.cantidad,
        actualizado_en = now()
    WHERE id = NEW.variante_id;

    IF (SELECT stock_actual FROM variantes_producto WHERE id = NEW.variante_id) < 0 THEN
        RAISE EXCEPTION 'Stock insuficiente para variante_id=%', NEW.variante_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_descontar_stock
    AFTER INSERT ON detalles_venta
    FOR EACH ROW EXECUTE FUNCTION fn_descontar_stock();

-- =====================================================================
-- VISTA: productos con stock bajo (para dashboard de alertas)
-- =====================================================================
CREATE VIEW vw_stock_bajo AS
SELECT p.nombre AS producto, v.sku, v.color, v.grosor, v.stock_actual, v.stock_minimo
FROM variantes_producto v
JOIN productos p ON p.id = v.producto_id
WHERE v.stock_actual <= v.stock_minimo AND v.activo = TRUE;
