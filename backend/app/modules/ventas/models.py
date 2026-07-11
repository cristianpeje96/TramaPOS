"""
TramaPos · Modelos SQLAlchemy del módulo ventas.
Mapea ventas y detalles_venta del schema.sql, incluyendo los ENUMs
de canal, estado y método de pago.

Importante: el trigger `trg_descontar_stock` (definido en schema.sql,
no en Python) es el que realmente descuenta variantes_producto.stock_actual
al insertar en detalles_venta. Esto es deliberado: así el stock queda
protegido incluso si algún día otra app distinta a este backend escribe
directo en la base de datos.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.modules.productos.models import VarianteProducto


class CanalVenta(str, PyEnum):
    POS = "POS"
    WEB = "WEB"


class EstadoVenta(str, PyEnum):
    COMPLETADA = "COMPLETADA"
    ANULADA = "ANULADA"
    PENDIENTE_PAGO = "PENDIENTE_PAGO"


class MetodoPago(str, PyEnum):
    EFECTIVO = "EFECTIVO"
    DATAFONO = "DATAFONO"
    TRANSFERENCIA = "TRANSFERENCIA"
    PASARELA_WEB = "PASARELA_WEB"
    MIXTO = "MIXTO"


class EstadoFacturaDian(str, PyEnum):
    NO_APLICA = "NO_APLICA"
    PENDIENTE = "PENDIENTE"
    ENVIADA = "ENVIADA"
    ACEPTADA = "ACEPTADA"
    RECHAZADA = "RECHAZADA"


class Venta(Base):
    __tablename__ = "ventas"
    __table_args__ = (
        CheckConstraint(
            "(canal = 'POS' AND sesion_caja_id IS NOT NULL) OR "
            "(canal = 'WEB' AND sesion_caja_id IS NULL)",
            name="chk_pos_requiere_sesion",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid_publico: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True
    )
    canal: Mapped[CanalVenta] = mapped_column(SAEnum(CanalVenta, name="canal_venta"))
    sesion_caja_id: Mapped[int | None] = mapped_column(ForeignKey("sesiones_caja.id"))
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.id"))
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    descuento_puntos: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    descuento_manual: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    motivo_descuento_manual: Mapped[str | None] = mapped_column(String(255))
    descuento_fidelizacion: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    rango_fidelizacion_aplicado: Mapped[str | None] = mapped_column(String(50))
    total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    metodo_pago: Mapped[MetodoPago] = mapped_column(SAEnum(MetodoPago, name="metodo_pago"))
    estado: Mapped[EstadoVenta] = mapped_column(
        SAEnum(EstadoVenta, name="estado_venta"), default=EstadoVenta.COMPLETADA
    )
    estado_factura_dian: Mapped[EstadoFacturaDian] = mapped_column(
        SAEnum(EstadoFacturaDian, name="estado_factura_dian"),
        default=EstadoFacturaDian.NO_APLICA,
    )
    puntos_ganados: Mapped[int] = mapped_column(default=0)
    puntos_redimidos: Mapped[int] = mapped_column(default=0)
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())

    detalles: Mapped[list["DetalleVenta"]] = relationship(
        back_populates="venta", cascade="all, delete-orphan"
    )


class DetalleVenta(Base):
    __tablename__ = "detalles_venta"

    id: Mapped[int] = mapped_column(primary_key=True)
    venta_id: Mapped[int] = mapped_column(
        ForeignKey("ventas.id", ondelete="CASCADE"), nullable=False
    )
    variante_id: Mapped[int] = mapped_column(
        ForeignKey("variantes_producto.id"), nullable=False
    )
    cantidad: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    precio_unitario: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    venta: Mapped[Venta] = relationship(back_populates="detalles")
    variante: Mapped["VarianteProducto"] = relationship()

    # Propiedades de solo lectura: la línea de venta nunca "copia" el
    # nombre/color del producto a su propia tabla (evita duplicación e
    # inconsistencia si el producto se renombra después) — simplemente
    # los expone leyendo la variante relacionada, para que el frontend
    # (recibos, historial, devoluciones) no tenga que hacer una consulta
    # aparte solo para saber qué se vendió.
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