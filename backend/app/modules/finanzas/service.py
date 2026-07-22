"""
TramaPos · Lógica del módulo finanzas.
La pieza central es generar_perdidas_ganancias: arma el reporte P&G
combinando VENTAS y COMPRAS reales (ya registradas en sus propios
módulos) con los movimientos financieros manuales de este módulo —
nadie tiene que volver a escribir una venta a mano.
"""

from datetime import date

from sqlalchemy import extract, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.compras.models import Compra, EstadoCompra
from app.modules.finanzas.models import CategoriaFinanciera, MovimientoFinanciero, TipoCategoriaFinanciera
from app.modules.finanzas.schemas import (
    CategoriaFinancieraCrear,
    FilaPyG,
    MovimientoFinancieroCrear,
)
from app.modules.ventas.models import EstadoVenta, Venta

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


# --- Categorías ---
async def listar_categorias_financieras(
    db: AsyncSession, solo_activas: bool = True
) -> list[CategoriaFinanciera]:
    query = select(CategoriaFinanciera).order_by(CategoriaFinanciera.nombre)
    if solo_activas:
        query = query.where(CategoriaFinanciera.activo.is_(True))
    resultado = await db.execute(query)
    return list(resultado.scalars().all())


async def crear_categoria_financiera(
    db: AsyncSession, datos: CategoriaFinancieraCrear
) -> CategoriaFinanciera:
    categoria = CategoriaFinanciera(**datos.model_dump())
    db.add(categoria)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ValueError(f"Ya existe una categoría financiera llamada '{datos.nombre}'") from exc
    await db.refresh(categoria)
    return categoria


# --- Movimientos ---
async def crear_movimiento(
    db: AsyncSession, datos: MovimientoFinancieroCrear, usuario_id: int | None
) -> MovimientoFinanciero:
    movimiento = MovimientoFinanciero(
        categoria_id=datos.categoria_id,
        fecha=datos.fecha or date.today(),
        descripcion=datos.descripcion,
        monto=datos.monto,
        usuario_id=usuario_id,
    )
    db.add(movimiento)
    await db.commit()
    await db.refresh(movimiento, attribute_names=["categoria"])
    return movimiento


async def listar_movimientos(
    db: AsyncSession,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    categoria_id: int | None = None,
    limite: int = 200,
) -> list[MovimientoFinanciero]:
    query = (
        select(MovimientoFinanciero)
        .options(selectinload(MovimientoFinanciero.categoria))
        .order_by(MovimientoFinanciero.fecha.desc(), MovimientoFinanciero.id.desc())
    )
    if fecha_desde:
        query = query.where(MovimientoFinanciero.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.where(MovimientoFinanciero.fecha <= fecha_hasta)
    if categoria_id:
        query = query.where(MovimientoFinanciero.categoria_id == categoria_id)
    query = query.limit(limite)
    resultado = await db.execute(query)
    return list(resultado.scalars().all())


async def eliminar_movimiento(db: AsyncSession, movimiento_id: int) -> None:
    movimiento = await db.get(MovimientoFinanciero, movimiento_id)
    if movimiento is None:
        raise ValueError(f"Movimiento {movimiento_id} no encontrado")
    await db.delete(movimiento)
    await db.commit()


# --- Pérdidas y Ganancias ---
def _array_mensual(filas: dict[int, float]) -> list[float]:
    return [round(filas.get(mes, 0.0), 2) for mes in range(1, 13)]


def _sumar_arrays(arrays: list[list[float]]) -> list[float]:
    if not arrays:
        return [0.0] * 12
    return [round(sum(a[i] for a in arrays), 2) for i in range(12)]


async def generar_perdidas_ganancias(db: AsyncSession, anio: int):
    # --- Ventas reales del POS, por mes ---
    query_ventas = (
        select(extract("month", Venta.creado_en), func.sum(Venta.total))
        .where(Venta.estado == EstadoVenta.COMPLETADA, extract("year", Venta.creado_en) == anio)
        .group_by(extract("month", Venta.creado_en))
    )
    resultado_ventas = await db.execute(query_ventas)
    ventas_por_mes = _array_mensual({int(m): float(t) for m, t in resultado_ventas.all()})
    fila_ventas = FilaPyG(nombre="Ventas", valores_por_mes=ventas_por_mes, total=round(sum(ventas_por_mes), 2))

    # --- Ingresos manuales (categorías tipo INGRESO), por categoría y mes ---
    query_ingresos_manuales = (
        select(
            CategoriaFinanciera.nombre,
            extract("month", MovimientoFinanciero.fecha),
            func.sum(MovimientoFinanciero.monto),
        )
        .join(CategoriaFinanciera, CategoriaFinanciera.id == MovimientoFinanciero.categoria_id)
        .where(
            CategoriaFinanciera.tipo == TipoCategoriaFinanciera.INGRESO,
            extract("year", MovimientoFinanciero.fecha) == anio,
        )
        .group_by(CategoriaFinanciera.nombre, extract("month", MovimientoFinanciero.fecha))
    )
    resultado_ingresos = await db.execute(query_ingresos_manuales)
    ingresos_por_categoria: dict[str, dict[int, float]] = {}
    for nombre, mes, total in resultado_ingresos.all():
        ingresos_por_categoria.setdefault(nombre, {})[int(mes)] = float(total)

    filas_ingresos = [fila_ventas] + [
        FilaPyG(
            nombre=nombre,
            valores_por_mes=_array_mensual(valores),
            total=round(sum(valores.values()), 2),
        )
        for nombre, valores in sorted(ingresos_por_categoria.items())
    ]
    total_ingresos = _sumar_arrays([f.valores_por_mes for f in filas_ingresos])

    # --- Costo de ventas: compras reales de mercancía, por mes ---
    query_compras = (
        select(extract("month", Compra.fecha_compra), func.sum(Compra.total))
        .where(Compra.estado == EstadoCompra.RECIBIDA, extract("year", Compra.fecha_compra) == anio)
        .group_by(extract("month", Compra.fecha_compra))
    )
    resultado_compras = await db.execute(query_compras)
    compras_por_mes = _array_mensual({int(m): float(t) for m, t in resultado_compras.all()})
    fila_compras = FilaPyG(
        nombre="Costo de mercancía",
        valores_por_mes=compras_por_mes,
        total=round(sum(compras_por_mes), 2),
    )
    filas_costo_ventas = [fila_compras]
    total_costo_ventas = _sumar_arrays([f.valores_por_mes for f in filas_costo_ventas])

    margen_bruto = [round(total_ingresos[i] - total_costo_ventas[i], 2) for i in range(12)]

    # --- Gastos manuales (categorías tipo GASTO), por categoría y mes ---
    query_gastos = (
        select(
            CategoriaFinanciera.nombre,
            extract("month", MovimientoFinanciero.fecha),
            func.sum(MovimientoFinanciero.monto),
        )
        .join(CategoriaFinanciera, CategoriaFinanciera.id == MovimientoFinanciero.categoria_id)
        .where(
            CategoriaFinanciera.tipo == TipoCategoriaFinanciera.GASTO,
            extract("year", MovimientoFinanciero.fecha) == anio,
        )
        .group_by(CategoriaFinanciera.nombre, extract("month", MovimientoFinanciero.fecha))
    )
    resultado_gastos = await db.execute(query_gastos)
    gastos_por_categoria: dict[str, dict[int, float]] = {}
    for nombre, mes, total in resultado_gastos.all():
        gastos_por_categoria.setdefault(nombre, {})[int(mes)] = float(total)

    filas_gastos = [
        FilaPyG(
            nombre=nombre,
            valores_por_mes=_array_mensual(valores),
            total=round(sum(valores.values()), 2),
        )
        for nombre, valores in sorted(gastos_por_categoria.items())
    ]
    total_gastos = _sumar_arrays([f.valores_por_mes for f in filas_gastos])

    ganancia_neta = [round(margen_bruto[i] - total_gastos[i], 2) for i in range(12)]

    return {
        "anio": anio,
        "ingresos": filas_ingresos,
        "total_ingresos": total_ingresos,
        "costo_ventas": filas_costo_ventas,
        "total_costo_ventas": total_costo_ventas,
        "margen_bruto": margen_bruto,
        "gastos": filas_gastos,
        "total_gastos": total_gastos,
        "ganancia_neta": ganancia_neta,
    }