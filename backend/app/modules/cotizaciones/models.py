"""
TramaPos · Modelos de cotizaciones.
Una cotización aprobada se convierte en una Venta real de un solo paso
(ver service.facturar_cotizacion) — nadie vuelve a digitar los productos.
"""

from datetime import date, datetime
from enum import Enum as PyEnum

from sqlalchemy import Date, ForeignKey, Numeric, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.modules.clientes.models import Cliente
from app.modules.productos.models import VarianteProducto


class EstadoCotizacion(str, PyEnum):
    PENDIENTE = "PENDIENTE"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"
    FACTURADA = "FACTURADA"


class Cotizacion(Base):
    __tablename__ = "cotizaciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.id"))
    cliente_nombre: Mapped[str | None] = mapped_column(String(150))
    cliente_telefono: Mapped[str | None] = mapped_column(String(30))
    cliente_email: Mapped[str | None] = mapped_column(String(150))
    fecha_emision: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    fecha_vencimiento: Mapped[date | None] = mapped_column(Date)
    estado: Mapped[EstadoCotizacion] = mapped_column(
        SAEnum(EstadoCotizacion, name="estado_cotizacion", native_enum=False, length=20),
        default=EstadoCotizacion.PENDIENTE,
    )
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    descuento_manual: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    notas: Mapped[str | None] = mapped_column(Text)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    venta_id: Mapped[int | None] = mapped_column(ForeignKey("ventas.id"))
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())

    detalles: Mapped[list["DetalleCotizacion"]] = relationship(
        back_populates="cotizacion", cascade="all, delete-orphan"
    )
    cliente: Mapped["Cliente | None"] = relationship()


class DetalleCotizacion(Base):
    __tablename__ = "detalles_cotizacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    cotizacion_id: Mapped[int] = mapped_column(
        ForeignKey("cotizaciones.id", ondelete="CASCADE"), nullable=False
    )
    variante_id: Mapped[int] = mapped_column(ForeignKey("variantes_producto.id"), nullable=False)
    cantidad: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    precio_unitario: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    cotizacion: Mapped[Cotizacion] = relationship(back_populates="detalles")
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