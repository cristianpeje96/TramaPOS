"""
TramaPos · Schemas del módulo finanzas.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.finanzas.models import TipoCategoriaFinanciera


class CategoriaFinancieraCrear(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    tipo: TipoCategoriaFinanciera


class CategoriaFinancieraOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    tipo: TipoCategoriaFinanciera
    activo: bool


class MovimientoFinancieroCrear(BaseModel):
    categoria_id: int
    fecha: date | None = None  # si no se manda, usa hoy
    descripcion: str | None = Field(default=None, max_length=255)
    monto: float = Field(gt=0)


class MovimientoFinancieroOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    categoria_id: int
    categoria_nombre: str
    categoria_tipo: TipoCategoriaFinanciera
    fecha: date
    descripcion: str | None
    monto: float
    creado_en: datetime


# --- Reporte de Pérdidas y Ganancias ---
class FilaPyG(BaseModel):
    nombre: str
    valores_por_mes: list[float]  # 12 posiciones, Ene..Dic
    total: float


class PerdidasGananciasOut(BaseModel):
    anio: int
    ingresos: list[FilaPyG]
    total_ingresos: list[float]
    costo_ventas: list[FilaPyG]
    total_costo_ventas: list[float]
    margen_bruto: list[float]
    gastos: list[FilaPyG]
    total_gastos: list[float]
    ganancia_neta: list[float]