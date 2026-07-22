"""
TramaPos · Lógica de negocio del módulo productos.
El router NUNCA arma queries directamente: siempre pasa por aquí,
para que esta misma lógica sea reutilizable por el futuro e-commerce.
"""

from datetime import datetime, timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.categorias import service as categorias_service
from app.modules.productos.models import Producto, VarianteProducto
from app.modules.productos.schemas import (
    ProductoActualizar,
    ProductoAltaRapidaIn,
    ProductoCrear,
    VarianteProductoActualizar,
)


async def crear_producto(db: AsyncSession, datos: ProductoCrear) -> Producto:
    """Crea un producto junto con sus variantes iniciales en una sola transacción."""
    producto = Producto(
        nombre=datos.nombre,
        descripcion=datos.descripcion,
        categoria_id=datos.categoria_id,
        unidad_medida=datos.unidad_medida,
        visible_web=datos.visible_web,
    )
    producto.variantes = [
        VarianteProducto(**variante.model_dump()) for variante in datos.variantes
    ]

    db.add(producto)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        detalle = str(exc.orig).lower()
        if "sku" in detalle:
            raise ValueError("Uno de los SKU ya está en uso por otra variante") from exc
        if "codigo_barras" in detalle:
            raise ValueError("Uno de los códigos de barras ya está en uso") from exc
        raise ValueError("No se pudo guardar: ya existe un registro con esos datos") from exc

    await db.refresh(producto, attribute_names=["variantes"])
    return producto


async def listar_productos(db: AsyncSession, incluir_inactivos: bool = False, limite: int = 200) -> list[Producto]:
    """Listado completo para la pantalla de administración (no el buscador ágil de F2)."""
    query = select(Producto).options(selectinload(Producto.variantes))
    if not incluir_inactivos:
        query = query.where(Producto.activo.is_(True))
    query = query.order_by(Producto.nombre).limit(limite)
    resultado = await db.execute(query)
    return list(resultado.scalars().unique().all())


async def buscar_productos(db: AsyncSession, texto: str, limite: int = 15) -> list[Producto]:
    """
    Búsqueda ágil para el buscador del POS (atajo F2).
    Usa ILIKE sobre el índice GIN trigram creado en el schema.sql.
    """
    query = (
        select(Producto)
        .options(selectinload(Producto.variantes))
        .where(Producto.nombre.ilike(f"%{texto}%"), Producto.activo.is_(True))
        .limit(limite)
    )
    resultado = await db.execute(query)
    return list(resultado.scalars().unique().all())


async def obtener_variante_por_codigo(
    db: AsyncSession, codigo: str
) -> VarianteProducto | None:
    """Busca por SKU o código de barras (lector de código de barras en caja)."""
    query = (
        select(VarianteProducto)
        .options(selectinload(VarianteProducto.producto).selectinload(Producto.variantes))
        .where(
            (VarianteProducto.sku == codigo) | (VarianteProducto.codigo_barras == codigo)
        )
    )
    resultado = await db.execute(query)
    return resultado.scalar_one_or_none()


async def listar_stock_bajo(db: AsyncSession) -> list[VarianteProducto]:
    """Espejo de la vista vw_stock_bajo del schema.sql, vía ORM."""
    query = (
        select(VarianteProducto)
        .options(selectinload(VarianteProducto.producto))
        .where(
            VarianteProducto.stock_actual <= VarianteProducto.stock_minimo,
            VarianteProducto.activo.is_(True),
        )
    )
    resultado = await db.execute(query)
    return list(resultado.scalars().all())


async def actualizar_producto(
    db: AsyncSession, producto_id: int, datos: ProductoActualizar
) -> Producto:
    query = (
        select(Producto)
        .options(selectinload(Producto.variantes))
        .where(Producto.id == producto_id)
    )
    resultado = await db.execute(query)
    producto = resultado.scalar_one_or_none()
    if producto is None:
        raise ValueError(f"Producto {producto_id} no encontrado")

    # exclude_unset=True: solo toca los campos que el cliente realmente envió
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(producto, campo, valor)

    await db.commit()
    await db.refresh(producto, attribute_names=["variantes"])
    return producto


async def actualizar_variante(
    db: AsyncSession, variante_id: int, datos: VarianteProductoActualizar
) -> VarianteProducto:
    variante = await db.get(VarianteProducto, variante_id)
    if variante is None:
        raise ValueError(f"Variante {variante_id} no encontrada")

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(variante, campo, valor)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        # El mensaje crudo de Postgres distingue qué columna violó el unique
        detalle = str(exc.orig).lower()
        if "sku" in detalle:
            raise ValueError(f"El SKU '{datos.sku}' ya está en uso por otra variante") from exc
        if "codigo_barras" in detalle:
            raise ValueError(
                f"El código de barras '{datos.codigo_barras}' ya está en uso por otra variante"
            ) from exc
        raise ValueError("No se pudo guardar: ya existe un registro con esos datos") from exc

    await db.refresh(variante)
    return variante


async def listar_favoritos(db: AsyncSession) -> list[VarianteProducto]:
    """Productos marcados por el cajero — acceso rápido en el POS."""
    query = (
        select(VarianteProducto)
        .join(Producto, Producto.id == VarianteProducto.producto_id)
        .options(selectinload(VarianteProducto.producto))
        .where(
            Producto.favorito.is_(True),
            Producto.activo.is_(True),
            VarianteProducto.activo.is_(True),
        )
        .order_by(Producto.nombre)
    )
    resultado = await db.execute(query)
    return list(resultado.scalars().unique().all())


async def listar_mas_vendidos(
    db: AsyncSession, limite: int = 6, dias: int = 30
) -> list[tuple[VarianteProducto, float]]:
    """Top variantes por cantidad vendida en los últimos `dias` días."""
    # Import local: evita que productos/service.py dependa de ventas a
    # nivel de módulo — solo se necesita dentro de esta función puntual.
    from app.modules.ventas.models import DetalleVenta, EstadoVenta, Venta

    fecha_desde = datetime.utcnow() - timedelta(days=dias)
    query = (
        select(DetalleVenta.variante_id, func.sum(DetalleVenta.cantidad).label("total"))
        .join(Venta, Venta.id == DetalleVenta.venta_id)
        .where(Venta.estado == EstadoVenta.COMPLETADA, Venta.creado_en >= fecha_desde)
        .group_by(DetalleVenta.variante_id)
        .order_by(desc("total"))
        .limit(limite)
    )
    resultado = await db.execute(query)
    filas = resultado.all()
    if not filas:
        return []

    variante_ids = [fila.variante_id for fila in filas]
    cantidades = {fila.variante_id: float(fila.total) for fila in filas}

    query_variantes = (
        select(VarianteProducto)
        .options(selectinload(VarianteProducto.producto))
        .where(VarianteProducto.id.in_(variante_ids))
    )
    resultado_variantes = await db.execute(query_variantes)
    variantes_por_id = {v.id: v for v in resultado_variantes.scalars().all()}

    # Preserva el orden de más vendido a menos vendido
    return [
        (variantes_por_id[vid], cantidades[vid])
        for vid in variante_ids
        if vid in variantes_por_id
    ]


async def _generar_siguiente_sku_varios(db: AsyncSession) -> str:
    """
    SKU automático tipo VAR-0001, VAR-0002... para productos de alta
    rápida que no traen código de barras ni SKU propio (botones,
    agujas, y demás artículos pequeños).
    """
    query = select(VarianteProducto.sku).where(VarianteProducto.sku.like("VAR-%"))
    resultado = await db.execute(query)
    numeros = []
    for (sku,) in resultado.all():
        sufijo = sku.replace("VAR-", "")
        if sufijo.isdigit():
            numeros.append(int(sufijo))
    siguiente = (max(numeros) + 1) if numeros else 1
    return f"VAR-{siguiente:04d}"


async def crear_producto_alta_rapida(
    db: AsyncSession, datos: ProductoAltaRapidaIn
) -> Producto:
    """
    Registro mínimo para artículos pequeños descubiertos sobre la marcha
    (botones, agujas, cierres...) — solo pide nombre, precio y cantidad.
    Todo lo demás se completa con valores por defecto sensatos, para que
    nunca terminen vendiéndose como "genérico" sin quedar en el inventario.
    """
    categoria_id = datos.categoria_id
    if categoria_id is None and datos.categoria_nombre:
        categoria = await categorias_service.obtener_o_crear_por_nombre(
            db, datos.categoria_nombre
        )
        categoria_id = categoria.id

    sku = await _generar_siguiente_sku_varios(db)

    producto = Producto(
        nombre=datos.nombre,
        categoria_id=categoria_id,
        unidad_medida="unidad",
    )
    producto.variantes = [
        VarianteProducto(
            sku=sku,
            precio_venta=datos.precio_venta,
            stock_actual=datos.stock_inicial,
            stock_minimo=0,
        )
    ]
    db.add(producto)
    await db.commit()
    await db.refresh(producto, attribute_names=["variantes"])
    return producto