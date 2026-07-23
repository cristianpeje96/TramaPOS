"""
TramaPos · Modelo de configuración de empresa.
Singleton: una sola fila, id=1. `aplica_iva` es el interruptor maestro —
apagado por defecto, para negocios (como persona natural) que todavía
no están obligados a declarar IVA. También guarda los datos de
membrete (nombre, NIT, dirección) para las facturas formales en PDF.
"""

from sqlalchemy import CheckConstraint, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ConfiguracionEmpresa(Base):
    __tablename__ = "configuracion_empresa"
    __table_args__ = (CheckConstraint("id = 1", name="chk_singleton_empresa"),)

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    aplica_iva: Mapped[bool] = mapped_column(default=False)
    porcentaje_iva_default: Mapped[float] = mapped_column(Numeric(5, 2), default=19.00)

    # --- Membrete (para facturas/cotizaciones en PDF y el ticket) ---
    razon_social: Mapped[str | None] = mapped_column(String(150))
    nit: Mapped[str | None] = mapped_column(String(30))
    direccion: Mapped[str | None] = mapped_column(String(255))
    telefono: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(150))