"""
TramaPos · Modelo de configuración de empresa.
Singleton: una sola fila, id=1. `aplica_iva` es el interruptor maestro —
apagado por defecto, para negocios (como persona natural) que todavía
no están obligados a declarar IVA.
"""

from sqlalchemy import CheckConstraint, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ConfiguracionEmpresa(Base):
    __tablename__ = "configuracion_empresa"
    __table_args__ = (CheckConstraint("id = 1", name="chk_singleton_empresa"),)

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    aplica_iva: Mapped[bool] = mapped_column(default=False)
    porcentaje_iva_default: Mapped[float] = mapped_column(Numeric(5, 2), default=19.00)