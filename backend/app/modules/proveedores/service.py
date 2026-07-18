"""
TramaPos · Lógica de negocio de proveedores.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.proveedores.models import Proveedor
from app.modules.proveedores.schemas import ProveedorActualizar, ProveedorCrear


async def crear_proveedor(db: AsyncSession, datos: ProveedorCrear) -> Proveedor:
    proveedor = Proveedor(**datos.model_dump())
    db.add(proveedor)
    await db.commit()
    await db.refresh(proveedor)
    return proveedor


async def listar_proveedores(db: AsyncSession, solo_activos: bool = True) -> list[Proveedor]:
    query = select(Proveedor).order_by(Proveedor.nombre_comercial)
    if solo_activos:
        query = query.where(Proveedor.activo.is_(True))
    resultado = await db.execute(query)
    return list(resultado.scalars().all())


async def buscar_proveedores(db: AsyncSession, texto: str) -> list[Proveedor]:
    query = (
        select(Proveedor)
        .where(Proveedor.nombre_comercial.ilike(f"%{texto}%"), Proveedor.activo.is_(True))
        .limit(15)
    )
    resultado = await db.execute(query)
    return list(resultado.scalars().all())


async def actualizar_proveedor(
    db: AsyncSession, proveedor_id: int, datos: ProveedorActualizar
) -> Proveedor:
    proveedor = await db.get(Proveedor, proveedor_id)
    if proveedor is None:
        raise ValueError(f"Proveedor {proveedor_id} no encontrado")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(proveedor, campo, valor)
    await db.commit()
    await db.refresh(proveedor)
    return proveedor