"""
TramaPos · Modelos de compras.
Simétrico al módulo ventas: el trigger trg_incrementar_stock_compra
(definido en schema.sql) sube variantes_producto.stock_actual al
insertar en detalles_compra — la app nunca toca el stock directamente.
"""

from datetime import date, datetime
from enum import Enum as PyEnum

from sqlalchemy import Date, ForeignKey, Numeric, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.modules.productos.models import VarianteProducto


class EstadoCompra(str, PyEnum):
    RECIBIDA = "RECIBIDA"
    ANULADA = "ANULADA"


class Compra(Base):
    __tablename__ = "compras"

    id: Mapped[int] = mapped_column(primary_key=True)
    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedores.id"), nullable=False)
    numero_factura_proveedor: Mapped[str | None] = mapped_column(String(50))
    fecha_compra: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    estado: Mapped[EstadoCompra] = mapped_column(
        SAEnum(EstadoCompra, name="estado_compra", native_enum=False, length=20),
        default=EstadoCompra.RECIBIDA,
    )
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())

    detalles: Mapped[list["DetalleCompra"]] = relationship(
        back_populates="compra", cascade="all, delete-orphan"
    )


class DetalleCompra(Base):
    __tablename__ = "detalles_compra"

    id: Mapped[int] = mapped_column(primary_key=True)
    compra_id: Mapped[int] = mapped_column(
        ForeignKey("compras.id", ondelete="CASCADE"), nullable=False
    )
    variante_id: Mapped[int] = mapped_column(ForeignKey("variantes_producto.id"), nullable=False)
    cantidad: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    costo_unitario: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    compra: Mapped[Compra] = relationship(back_populates="detalles")
    variante: Mapped["VarianteProducto"] = relationship()

    @property
    def producto_nombre(self) -> str:
        return self.variante.producto.nombre if self.variante and self.variante.producto else ""

    @property
    def color(self) -> str | None:
        return self.variante.color if self.variante else None

    @property
    def grosor(self) -> str | None:
        return self.variante.grosor if self.variante else None

    @property
    def sku(self) -> str | None:
        return self.variante.sku if self.variante else None