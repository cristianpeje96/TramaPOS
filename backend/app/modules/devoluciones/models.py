"""
TramaPos · Modelo SQLAlchemy del módulo devoluciones.
Mapea la tabla devoluciones del schema.sql.

Por diseño, una devolución es TOTAL (anula la venta completa), no
parcial por línea — es la versión más simple y menos propensa a
confundir al cajero. Si más adelante se necesita devolución parcial,
este modelo es el punto de partida para agregarle detalle_devolucion.
"""

from datetime import datetime

from sqlalchemy import ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Devolucion(Base):
    __tablename__ = "devoluciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    venta_id: Mapped[int] = mapped_column(
        ForeignKey("ventas.id"), nullable=False, unique=True
    )
    motivo: Mapped[str] = mapped_column(String(255), nullable=False)
    monto_devuelto: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())