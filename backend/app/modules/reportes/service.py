"""
TramaPos · Lógica de reportes.
Todo se calcula sobre ventas COMPLETADA únicamente — una venta ANULADA
(devuelta) no debe inflar las estadísticas de lo que realmente se vendió.
"""

from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.productos.models import VarianteProducto
from app.modules.ventas.models import DetalleVenta, EstadoVenta, Venta


def _rango_fechas(fecha_desde: date | None, fecha_hasta: date | None):
    """Por defecto, últimos 30 días si no se especifica nada."""
    hasta = fecha_hasta or date.today()
    desde = fecha_desde or (hasta - timedelta(days=30))
    inicio = datetime.combine(desde, datetime.min.time())
    fin = datetime.combine(hasta, datetime.min.time()) + timedelta(days=1)
    return inicio, fin


async def obtener_resumen(
    db: AsyncSession, fecha_desde: date | None, fecha_hasta: date | None
) -> dict:
    inicio, fin = _rango_fechas(fecha_desde, fecha_hasta)
    query = select(
        func.coalesce(func.sum(Venta.total), 0),
        func.count(Venta.id),
    ).where(
        Venta.estado == EstadoVenta.COMPLETADA,
        Venta.creado_en >= inicio,
        Venta.creado_en < fin,
    )
    resultado = await db.execute(query)
    total, cantidad = resultado.one()
    total = float(total)
    return {
        "total_ventas": total,
        "cantidad_ventas": cantidad,
        "ticket_promedio": round(total / cantidad, 2) if cantidad > 0 else 0.0,
    }


async def ventas_por_dia(
    db: AsyncSession, fecha_desde: date | None, fecha_hasta: date | None
) -> list[dict]:
    inicio, fin = _rango_fechas(fecha_desde, fecha_hasta)
    dia = func.date(Venta.creado_en)
    query = (
        select(dia.label("fecha"), func.sum(Venta.total).label("total"), func.count(Venta.id).label("cantidad"))
        .where(
            Venta.estado == EstadoVenta.COMPLETADA,
            Venta.creado_en >= inicio,
            Venta.creado_en < fin,
        )
        .group_by(dia)
        .order_by(dia)
    )
    resultado = await db.execute(query)
    return [
        {"fecha": fila.fecha, "total": float(fila.total), "cantidad_ventas": fila.cantidad}
        for fila in resultado.all()
    ]


async def ventas_por_mes(db: AsyncSession, meses_atras: int = 12) -> list[dict]:
    """Últimos N meses (incluye el actual), agrupados por año-mes."""
    hoy = date.today()
    inicio = datetime.combine(hoy.replace(day=1), datetime.min.time()) - timedelta(
        days=31 * (meses_atras - 1)
    )
    inicio = inicio.replace(day=1)

    anio = func.extract("year", Venta.creado_en)
    mes = func.extract("month", Venta.creado_en)
    query = (
        select(
            anio.label("anio"),
            mes.label("mes"),
            func.sum(Venta.total).label("total"),
            func.count(Venta.id).label("cantidad"),
        )
        .where(Venta.estado == EstadoVenta.COMPLETADA, Venta.creado_en >= inicio)
        .group_by(anio, mes)
        .order_by(anio, mes)
    )
    resultado = await db.execute(query)
    return [
        {
            "anio": int(fila.anio),
            "mes": int(fila.mes),
            "total": float(fila.total),
            "cantidad_ventas": fila.cantidad,
        }
        for fila in resultado.all()
    ]


async def productos_mas_vendidos_reporte(
    db: AsyncSession,
    fecha_desde: date | None,
    fecha_hasta: date | None,
    limite: int = 15,
) -> list[dict]:
    inicio, fin = _rango_fechas(fecha_desde, fecha_hasta)
    query = (
        select(
            DetalleVenta.variante_id,
            func.sum(DetalleVenta.cantidad).label("cantidad_vendida"),
            func.sum(DetalleVenta.cantidad * DetalleVenta.precio_unitario).label("total_vendido"),
        )
        .join(Venta, Venta.id == DetalleVenta.venta_id)
        .where(
            Venta.estado == EstadoVenta.COMPLETADA,
            Venta.creado_en >= inicio,
            Venta.creado_en < fin,
        )
        .group_by(DetalleVenta.variante_id)
        .order_by(func.sum(DetalleVenta.cantidad).desc())
        .limit(limite)
    )
    resultado = await db.execute(query)
    filas = resultado.all()
    if not filas:
        return []

    variante_ids = [f.variante_id for f in filas]
    query_variantes = (
        select(VarianteProducto)
        .options(selectinload(VarianteProducto.producto))
        .where(VarianteProducto.id.in_(variante_ids))
    )
    resultado_variantes = await db.execute(query_variantes)
    variantes = {v.id: v for v in resultado_variantes.scalars().all()}

    reporte = []
    for fila in filas:
        variante = variantes.get(fila.variante_id)
        if variante is None:
            continue
        reporte.append(
            {
                "variante_id": variante.id,
                "producto_nombre": variante.producto.nombre,
                "color": variante.color,
                "grosor": variante.grosor,
                "sku": variante.sku,
                "cantidad_vendida": float(fila.cantidad_vendida),
                "total_vendido": float(fila.total_vendido),
            }
        )
    return reporte