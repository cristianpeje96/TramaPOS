"""
TramaPos · Modelo SQLAlchemy del módulo usuarios.
Cada persona que opera el sistema (cajero o administrador) tiene una
cuenta acá — esto es lo que hacía falta para saber QUIÉN abrió una caja,
QUIÉN aplicó un descuento manual, o QUIÉN hizo una devolución.
"""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RolUsuario(str, PyEnum):
    CAJERO = "CAJERO"
    ADMIN = "ADMIN"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre_completo: Mapped[str] = mapped_column(String(150), nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[RolUsuario] = mapped_column(
        SAEnum(RolUsuario, name="rol_usuario", native_enum=False, length=20),
        default=RolUsuario.CAJERO,
    )
    activo: Mapped[bool] = mapped_column(default=True)
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())