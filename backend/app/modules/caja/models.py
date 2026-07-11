"""
TramaPos · Modelo SQLAlchemy del módulo caja.
Mapea sesiones_caja del schema.sql.

`diferencia` es una columna GENERATED ALWAYS AS en PostgreSQL (ver schema.sql).
Se mapea con `Computed(...)` para que SQLAlchemy sepa que NUNCA debe
incluirla en INSERT/UPDATE — Postgres la calcula sola.
"""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Computed, DateTime, Numeric, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EstadoSesionCaja(str, PyEnum):
    ABIERTA = "ABIERTA"
    CERRADA = "CERRADA"


class SesionCaja(Base):
    __tablename__ = "sesiones_caja"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_apertura_id: Mapped[int] = mapped_column(nullable=False)
    usuario_cierre_id: Mapped[int | None] = mapped_column()
    monto_apertura: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    monto_cierre_esperado: Mapped[float | None] = mapped_column(Numeric(12, 2))
    monto_cierre_real: Mapped[float | None] = mapped_column(Numeric(12, 2))
    diferencia: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        Computed("monto_cierre_real - monto_cierre_esperado"),
        nullable=True,
    )
    estado: Mapped[EstadoSesionCaja] = mapped_column(
        SAEnum(EstadoSesionCaja, name="estado_sesion_caja"), default=EstadoSesionCaja.ABIERTA
    )
    abierta_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    cerrada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))