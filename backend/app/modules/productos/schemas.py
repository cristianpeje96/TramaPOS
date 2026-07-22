"""
TramaPos · Schemas Pydantic del módulo productos.
Separados de los modelos SQLAlchemy a propósito: la API nunca expone
directamente el modelo de base de datos (principio API-first).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# --- Categoría ---
class CategoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    categoria_padre_id: int | None = None


# --- Variante de producto ---
class VarianteProductoBase(BaseModel):
    sku: str
    codigo_barras: str | None = None
    color: str | None = None
    grosor: str | None = None
    precio_venta: float = Field(ge=0)
    costo_unitario: float | None = Field(default=None, ge=0)
    porcentaje_iva: float = Field(default=19.00, ge=0, le=100)
    stock_actual: float = Field(default=0, ge=0)
    stock_minimo: float = Field(default=0, ge=0)


class VarianteProductoCrear(VarianteProductoBase):
    pass


class VarianteProductoOut(VarianteProductoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    producto_id: int
    activo: bool


# --- Producto ---
class ProductoBase(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    descripcion: str | None = None
    categoria_id: int | None = None
    unidad_medida: str = "unidad"
    visible_web: bool = False
    favorito: bool = False


class ProductoCrear(ProductoBase):
    variantes: list[VarianteProductoCrear] = Field(
        default_factory=list,
        description="Variantes iniciales (ej: colores/grosores de Hilo Guajira)",
    )


class ProductoActualizar(BaseModel):
    """Todos los campos opcionales — solo se actualiza lo que venga en el body (PATCH)."""

    nombre: str | None = Field(default=None, min_length=2, max_length=150)
    descripcion: str | None = None
    categoria_id: int | None = None
    unidad_medida: str | None = None
    visible_web: bool | None = None
    favorito: bool | None = None
    activo: bool | None = None


class VarianteProductoActualizar(BaseModel):
    sku: str | None = None
    codigo_barras: str | None = None
    color: str | None = None
    grosor: str | None = None
    precio_venta: float | None = Field(default=None, ge=0)
    costo_unitario: float | None = Field(default=None, ge=0)
    porcentaje_iva: float | None = Field(default=None, ge=0, le=100)
    stock_actual: float | None = Field(default=None, ge=0)
    stock_minimo: float | None = Field(default=None, ge=0)
    activo: bool | None = None


class ProductoOut(ProductoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    activo: bool
    creado_en: datetime
    variantes: list[VarianteProductoOut] = []


# --- Alta rápida: para productos pequeños descubiertos sobre la marcha
# (botones, agujas, etc.) — mínima fricción, máximos valores por defecto.
class ProductoAltaRapidaIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    precio_venta: float = Field(ge=0)
    stock_inicial: float = Field(default=1, ge=0)
    categoria_id: int | None = None
    categoria_nombre: str | None = Field(
        default=None, description="Si no existe, se crea; ignorado si se manda categoria_id"
    )


# --- Alertas de stock ---
class StockBajoOut(BaseModel):
    producto: str
    sku: str
    color: str | None
    grosor: str | None
    stock_actual: float
    stock_minimo: float


# --- Productos destacados (favoritos / más vendidos) para el POS ---
class ProductoDestacadoOut(BaseModel):
    variante_id: int
    producto_nombre: str
    color: str | None
    grosor: str | None
    sku: str
    precio_venta: float
    stock_actual: float
    unidad_medida: str
    cantidad_vendida: float | None = None  # solo se llena en "más vendidos"