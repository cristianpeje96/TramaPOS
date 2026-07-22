"""
TramaPos · Modelo de categorías.
La tabla ya existía desde el schema.sql original (productos.categoria_id
la referencia desde el día 1), pero nunca se construyó el CRUD — hasta
ahora productos se creaban sin categoría.
"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Categoria(Base):
    __tablename__ = "categorias"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    categoria_padre_id: Mapped[int | None] = mapped_column(
        ForeignKey("categorias.id", ondelete="SET NULL")
    )
    activo: Mapped[bool] = mapped_column(default=True)