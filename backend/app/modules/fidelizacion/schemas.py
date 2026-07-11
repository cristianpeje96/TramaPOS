"""
TramaPos · Schemas Pydantic del módulo fidelizacion.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.fidelizacion.models import TipoMovimientoPuntos


class ConfiguracionFidelizacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    pesos_por_punto: float
    valor_punto_redimido: float


class ConfiguracionFidelizacionActualizar(BaseModel):
    pesos_por_punto: float = Field(gt=0)
    valor_punto_redimido: float = Field(gt=0)


class HistorialPuntosOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    cliente_id: int
    venta_id: int | None
    tipo_movimiento: TipoMovimientoPuntos
    puntos: int
    saldo_resultante: int
    nota: str | None
    creado_en: datetime


class AjusteManualCrear(BaseModel):
    cliente_id: int
    puntos: int = Field(description="Positivo para sumar, negativo para restar")
    nota: str = Field(min_length=3, max_length=255)


class SimulacionRedencionOut(BaseModel):
    """Usado por el POS al presionar F9: muestra el descuento antes de confirmar."""

    puntos_disponibles: int
    puntos_a_redimir: int
    valor_descuento: float


# --- Rangos de descuento por fidelización (niveles Bronce/Plata/Oro) ---
class RangoDescuentoBase(BaseModel):
    nombre: str = Field(min_length=2, max_length=50)
    puntos_minimo: int = Field(ge=0)
    puntos_maximo: int | None = Field(default=None, ge=0)
    porcentaje_descuento: float = Field(ge=0, le=100)


class RangoDescuentoCrear(RangoDescuentoBase):
    pass


class RangoDescuentoActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=50)
    puntos_minimo: int | None = Field(default=None, ge=0)
    puntos_maximo: int | None = Field(default=None, ge=0)
    porcentaje_descuento: float | None = Field(default=None, ge=0, le=100)
    activo: bool | None = None


class RangoDescuentoOut(RangoDescuentoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    activo: bool


class RangoClienteOut(BaseModel):
    """Lo que el CheckoutPanel consulta para mostrar el descuento automático."""

    rango: str | None
    porcentaje_descuento: float
    puntos_totales_historicos: int