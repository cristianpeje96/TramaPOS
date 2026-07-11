"""
TramaPos · Modelo SQLAlchemy del módulo clientes.
Mapea la tabla clientes del schema.sql.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Cliente(Base):
    __tablename__ = "clientes"
    __table_args__ = (
        UniqueConstraint("tipo_documento", "numero_documento", name="uq_cliente_documento"),
        CheckConstraint("puntos_balance >= 0", name="chk_puntos_balance_positivo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo_documento: Mapped[str] = mapped_column(String(10), default="CC")
    numero_documento: Mapped[str] = mapped_column(String(30), nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str | None] = mapped_column(String(150))
    telefono: Mapped[str | None] = mapped_column(String(30))
    direccion: Mapped[str | None] = mapped_column(Text)
    puntos_balance: Mapped[int] = mapped_column(default=0)
    puntos_totales_historicos: Mapped[int] = mapped_column(default=0)
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())