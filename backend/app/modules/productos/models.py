"""
TramaPos · Modelos SQLAlchemy del módulo productos.
Mapean 1:1 las tablas categorias, productos y variantes_producto del schema.sql.
"""

from datetime import datetime

from sqlalchemy import ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Categoria(Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    categoria_padre_id: Mapped[int | None] = mapped_column(
        ForeignKey("categorias.id", ondelete="SET NULL")
    )
    activo: Mapped[bool] = mapped_column(default=True)

    productos: Mapped[list["Producto"]] = relationship(back_populates="categoria")


class Producto(Base):
    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    categoria_id: Mapped[int | None] = mapped_column(
        ForeignKey("categorias.id", ondelete="SET NULL")
    )
    unidad_medida: Mapped[str] = mapped_column(String(20), default="unidad")
    activo: Mapped[bool] = mapped_column(default=True)
    visible_web: Mapped[bool] = mapped_column(default=False)
    favorito: Mapped[bool] = mapped_column(default=False)
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    categoria: Mapped[Categoria | None] = relationship(back_populates="productos")
    variantes: Mapped[list["VarianteProducto"]] = relationship(
        back_populates="producto", cascade="all, delete-orphan"
    )


class VarianteProducto(Base):
    __tablename__ = "variantes_producto"

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(
        ForeignKey("productos.id", ondelete="CASCADE"), nullable=False
    )
    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    codigo_barras: Mapped[str | None] = mapped_column(String(50), unique=True)
    color: Mapped[str | None] = mapped_column(String(60))
    grosor: Mapped[str | None] = mapped_column(String(40))
    atributos_extra: Mapped[dict] = mapped_column(JSONB, default=dict)
    precio_venta: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    costo_unitario: Mapped[float | None] = mapped_column(Numeric(12, 2))
    stock_actual: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    stock_minimo: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    activo: Mapped[bool] = mapped_column(default=True)
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    producto: Mapped[Producto] = relationship(back_populates="variantes")