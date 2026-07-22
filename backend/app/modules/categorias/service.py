"""
TramaPos · Lógica de categorías.
"""

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.categorias.models import Categoria
from app.modules.categorias.schemas import CategoriaActualizar, CategoriaCrear


async def listar_categorias(db: AsyncSession, solo_activas: bool = True) -> list[Categoria]:
    query = select(Categoria).order_by(Categoria.nombre)
    if solo_activas:
        query = query.where(Categoria.activo.is_(True))
    resultado = await db.execute(query)
    return list(resultado.scalars().all())


async def crear_categoria(db: AsyncSession, datos: CategoriaCrear) -> Categoria:
    categoria = Categoria(**datos.model_dump())
    db.add(categoria)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ValueError(f"Ya existe una categoría llamada '{datos.nombre}'") from exc
    await db.refresh(categoria)
    return categoria


async def obtener_o_crear_por_nombre(db: AsyncSession, nombre: str) -> Categoria:
    """
    Usado por alta rápida y carga masiva: si la categoría ya existe (por
    nombre, sin distinguir mayúsculas), la reutiliza; si no, la crea.
    """
    resultado = await db.execute(
        select(Categoria).where(func.lower(Categoria.nombre) == nombre.lower())
    )
    categoria = resultado.scalar_one_or_none()
    if categoria is None:
        categoria = Categoria(nombre=nombre)
        db.add(categoria)
        await db.flush()
    return categoria


async def actualizar_categoria(
    db: AsyncSession, categoria_id: int, datos: CategoriaActualizar
) -> Categoria:
    categoria = await db.get(Categoria, categoria_id)
    if categoria is None:
        raise ValueError(f"Categoría {categoria_id} no encontrada")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(categoria, campo, valor)
    await db.commit()
    await db.refresh(categoria)
    return categoria