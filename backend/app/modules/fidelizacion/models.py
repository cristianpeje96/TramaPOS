"""
TramaPos · Modelos SQLAlchemy del módulo fidelizacion.
Mapea historial_puntos y configuracion_fidelizacion del schema.sql.

Nota: venta_id referencia la tabla "ventas" por nombre (string), no por
relationship a la clase Venta, para evitar import circular entre módulos
(fidelizacion se usa DESDE ventas, no al revés).
"""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TipoMovimientoPuntos(str, PyEnum):
    GANADO = "GANADO"
    REDIMIDO = "REDIMIDO"
    AJUSTE_MANUAL = "AJUSTE_MANUAL"
    EXPIRADO = "EXPIRADO"


class HistorialPuntos(Base):
    __tablename__ = "historial_puntos"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False
    )
    venta_id: Mapped[int | None] = mapped_column(ForeignKey("ventas.id"))
    tipo_movimiento: Mapped[TipoMovimientoPuntos] = mapped_column(
        SAEnum(TipoMovimientoPuntos, name="tipo_movimiento_puntos"), nullable=False
    )
    puntos: Mapped[int] = mapped_column(nullable=False)  # positivo=ganado, negativo=redimido
    saldo_resultante: Mapped[int] = mapped_column(nullable=False)
    nota: Mapped[str | None] = mapped_column(String(255))
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())


class ConfiguracionFidelizacion(Base):
    __tablename__ = "configuracion_fidelizacion"
    __table_args__ = (CheckConstraint("id = 1", name="chk_singleton"),)

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    pesos_por_punto: Mapped[float] = mapped_column(Numeric(12, 2), default=1000)
    valor_punto_redimido: Mapped[float] = mapped_column(Numeric(12, 2), default=1)


class RangoDescuentoFidelizacion(Base):
    """
    Niveles tipo Bronce/Plata/Oro. Se calculan sobre
    clientes.puntos_totales_historicos (nunca baja al redimir), NO sobre
    el saldo redimible — un cliente no pierde su nivel solo por canjear.
    """

    __tablename__ = "rangos_descuento_fidelizacion"
    __table_args__ = (
        CheckConstraint("puntos_minimo >= 0", name="chk_puntos_minimo_positivo"),
        CheckConstraint(
            "porcentaje_descuento BETWEEN 0 AND 100", name="chk_porcentaje_valido"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    puntos_minimo: Mapped[int] = mapped_column(nullable=False)
    puntos_maximo: Mapped[int | None] = mapped_column()  # NULL = sin techo
    porcentaje_descuento: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    activo: Mapped[bool] = mapped_column(default=True)