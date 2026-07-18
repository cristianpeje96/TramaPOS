"""
TramaPos · Lógica de negocio de compras.

Simétrico a ventas/service.py: una compra sube stock y (opcionalmente)
actualiza el costo del producto — todo en una sola transacción.
"""

from datetime import date as date_type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.compras.models import Compra, DetalleCompra, EstadoCompra
from app.modules.compras.schemas import CompraCrear
from app.modules.productos.models import VarianteProducto


def _con_detalles_completos():
    return selectinload(Compra.detalles).selectinload(DetalleCompra.variante).selectinload(
        VarianteProducto.producto
    )


async def _bloquear_variantes(
    db: AsyncSession, variante_ids: list[int]
) -> dict[int, VarianteProducto]:
    query = (
        select(VarianteProducto).where(VarianteProducto.id.in_(variante_ids)).with_for_update()
    )
    resultado = await db.execute(query)
    variantes = {v.id: v for v in resultado.scalars().all()}
    faltantes = set(variante_ids) - set(variantes.keys())
    if faltantes:
        raise ValueError(f"Variantes inexistentes: {faltantes}")
    return variantes


async def procesar_compra(db: AsyncSession, datos: CompraCrear, usuario_id: int | None) -> Compra:
    try:
        variantes = await _bloquear_variantes(db, [l.variante_id for l in datos.lineas])

        subtotal = sum(l.cantidad * l.costo_unitario for l in datos.lineas)

        compra = Compra(
            proveedor_id=datos.proveedor_id,
            numero_factura_proveedor=datos.numero_factura_proveedor,
            fecha_compra=datos.fecha_compra or date_type.today(),
            subtotal=subtotal,
            total=subtotal,  # sin descuentos/impuestos por ahora — igual que el subtotal
            usuario_id=usuario_id,
        )
        db.add(compra)
        await db.flush()

        for linea in datos.lineas:
            db.add(
                DetalleCompra(
                    compra_id=compra.id,
                    variante_id=linea.variante_id,
                    cantidad=linea.cantidad,
                    costo_unitario=linea.costo_unitario,
                )
            )
            if datos.actualizar_costo_producto:
                variantes[linea.variante_id].costo_unitario = linea.costo_unitario
        await db.flush()  # dispara trg_incrementar_stock_compra en PostgreSQL

        await db.commit()

    except Exception:
        await db.rollback()
        raise

    return await obtener_compra(db, compra.id)


async def listar_compras(
    db: AsyncSession,
    proveedor_id: int | None = None,
    fecha: date_type | None = None,
    limite: int = 100,
) -> list[Compra]:
    query = select(Compra).options(_con_detalles_completos()).order_by(Compra.creado_en.desc())
    if proveedor_id is not None:
        query = query.where(Compra.proveedor_id == proveedor_id)
    if fecha is not None:
        query = query.where(Compra.fecha_compra == fecha)
    query = query.limit(limite)
    resultado = await db.execute(query)
    return list(resultado.scalars().unique().all())


async def obtener_compra(db: AsyncSession, compra_id: int) -> Compra | None:
    query = select(Compra).options(_con_detalles_completos()).where(Compra.id == compra_id)
    resultado = await db.execute(query)
    return resultado.scalar_one_or_none()


async def anular_compra(db: AsyncSession, compra_id: int, motivo: str) -> Compra:
    """
    Revierte una compra mal registrada: baja el stock que había subido.
    Si ya se vendió parte de esa mercancía y el stock no alcanza para
    revertir, lanza error — no deja el stock en negativo.
    """
    try:
        query = (
            select(Compra)
            .options(selectinload(Compra.detalles))
            .where(Compra.id == compra_id)
            .with_for_update()
        )
        resultado = await db.execute(query)
        compra = resultado.scalar_one_or_none()

        if compra is None:
            raise ValueError(f"Compra {compra_id} no encontrada")
        if compra.estado == EstadoCompra.ANULADA:
            raise ValueError(f"La compra {compra_id} ya fue anulada anteriormente")

        variante_ids = [d.variante_id for d in compra.detalles]
        query_variantes = (
            select(VarianteProducto).where(VarianteProducto.id.in_(variante_ids)).with_for_update()
        )
        resultado_variantes = await db.execute(query_variantes)
        variantes = {v.id: v for v in resultado_variantes.scalars().all()}

        for detalle in compra.detalles:
            variante = variantes.get(detalle.variante_id)
            if variante is None:
                continue
            if variante.stock_actual < detalle.cantidad:
                raise ValueError(
                    f"No se puede anular: el stock de {variante.sku} ya bajó de lo que "
                    "esta compra había agregado (probablemente ya se vendió)."
                )
            variante.stock_actual -= detalle.cantidad

        compra.estado = EstadoCompra.ANULADA
        await db.commit()

    except Exception:
        await db.rollback()
        raise

    return await obtener_compra(db, compra_id)