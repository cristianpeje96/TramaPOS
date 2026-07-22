"""
TramaPos · Modelos del módulo finanzas.
Movimientos que NO son ventas ni compras de mercancía (esos ya se
llevan solos vía ventas/ y compras/) — arriendo, servicios, retiros de
socios, préstamos, y cualquier otro dinero que entra o sale del negocio.
"""

from datetime import date, datetime
from enum import Enum as PyEnum

from sqlalchemy import Date, ForeignKey, Numeric, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TipoCategoriaFinanciera(str, PyEnum):
    INGRESO = "INGRESO"
    GASTO = "GASTO"


class CategoriaFinanciera(Base):
    __tablename__ = "categorias_financieras"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    tipo: Mapped[TipoCategoriaFinanciera] = mapped_column(
        SAEnum(TipoCategoriaFinanciera, name="tipo_categoria_financiera", native_enum=False, length=20)
    )
    activo: Mapped[bool] = mapped_column(default=True)


class MovimientoFinanciero(Base):
    __tablename__ = "movimientos_financieros"

    id: Mapped[int] = mapped_column(primary_key=True)
    categoria_id: Mapped[int] = mapped_column(
        ForeignKey("categorias_financieras.id"), nullable=False
    )
    fecha: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    descripcion: Mapped[str | None] = mapped_column(String(255))
    monto: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())

    categoria: Mapped[CategoriaFinanciera] = relationship()

    @property
    def categoria_nombre(self) -> str:
        return self.categoria.nombre if self.categoria else ""

    @property
    def categoria_tipo(self) -> TipoCategoriaFinanciera:
        return self.categoria.tipo if self.categoria else None