"""
TramaPos · Modelo de cajas físicas (terminales).
Cada registradora física de la tienda es una fila acá — permite que
2+ cajas operen simultáneamente, cada una con su propia sesión.
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CajaFisica(Base):
    __tablename__ = "cajas_fisicas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    activo: Mapped[bool] = mapped_column(default=True)