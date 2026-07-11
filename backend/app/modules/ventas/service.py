"""
TramaPos · Lógica de negocio del módulo ventas.

Este es el corazón transaccional del sistema: una venta exitosa tiene que
descontar stock, ganar/redimir puntos y quedar registrada — todo junto,
o nada. Por eso todo el flujo vive en una sola función y un solo commit.

Orden de la transacción:
  1. Bloquear (SELECT ... FOR UPDATE) las variantes y el cliente involucrados,
     para que dos ventas simultáneas del mismo producto/cliente no se pisen.
  2. Validar stock disponible ANTES de escribir nada (mejor error, más claro
     que el que lanzaría el trigger de la base de datos como último resorte).
  3. Crear la venta (flush para obtener su id).
  4. Crear las líneas — el trigger trg_descontar_stock del schema.sql
     descuenta variantes_producto.stock_actual automáticamente al insertar.
  5. Calcular los tres descuentos posibles (puntos redimidos, manual,
     y automático por rango de fidelización) y aplicarlos al total.
  6. Redimir puntos (si aplica) y luego ganar puntos sobre el total ya
     descontado — en ese orden, porque los puntos ganados son sobre lo que
     el cliente realmente pagó, no sobre el subtotal antes del descuento.
  7. Commit único.
"""

from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.clientes.models import Cliente
from app.modules.fidelizacion import service as fidelizacion_service
from app.modules.productos.models import VarianteProducto
from app.modules.ventas.models import CanalVenta, DetalleVenta, EstadoFacturaDian, Venta
from app.modules.ventas.schemas import VentaCrear


def _con_detalles_completos():
    """
    Cadena de eager loading reutilizada en procesar_venta/listar_ventas/
    obtener_venta: trae detalles -> variante -> producto en la misma
    consulta, para que el frontend reciba producto_nombre/color/sku sin
    que cada endpoint tenga que acordarse de repetir el .options(...).
    """
    return selectinload(Venta.detalles).selectinload(DetalleVenta.variante).selectinload(
        VarianteProducto.producto
    )


async def _bloquear_variantes(
    db: AsyncSession, variante_ids: list[int]
) -> dict[int, VarianteProducto]:
    query = (
        select(VarianteProducto)
        .where(VarianteProducto.id.in_(variante_ids))
        .with_for_update()
    )
    resultado = await db.execute(query)
    variantes = {v.id: v for v in resultado.scalars().all()}

    faltantes = set(variante_ids) - set(variantes.keys())
    if faltantes:
        raise ValueError(f"Variantes inexistentes: {faltantes}")
    return variantes


async def _bloquear_cliente(db: AsyncSession, cliente_id: int) -> Cliente:
    query = select(Cliente).where(Cliente.id == cliente_id).with_for_update()
    resultado = await db.execute(query)
    cliente = resultado.scalar_one_or_none()
    if cliente is None:
        raise ValueError(f"Cliente {cliente_id} no encontrado")
    return cliente


async def procesar_venta(db: AsyncSession, datos: VentaCrear) -> Venta:
    try:
        variantes = await _bloquear_variantes(
            db, [linea.variante_id for linea in datos.lineas]
        )

        # --- Validación de stock, antes de escribir nada ---
        for linea in datos.lineas:
            variante = variantes[linea.variante_id]
            if variante.stock_actual < linea.cantidad:
                raise ValueError(
                    f"Stock insuficiente para {variante.sku} "
                    f"(disponible: {variante.stock_actual}, solicitado: {linea.cantidad})"
                )

        subtotal = sum(
            linea.cantidad * float(variantes[linea.variante_id].precio_venta)
            for linea in datos.lineas
        )

        cliente: Cliente | None = None
        if datos.cliente_id is not None:
            cliente = await _bloquear_cliente(db, datos.cliente_id)

        # --- Descuento por redención de puntos ---
        descuento_puntos = 0.0
        if datos.puntos_a_redimir > 0:
            config = await fidelizacion_service.obtener_configuracion(db)
            descuento_puntos = fidelizacion_service.calcular_valor_descuento(
                datos.puntos_a_redimir, config
            )

        # --- Descuento manual (porcentaje o monto fijo, con motivo obligatorio) ---
        descuento_manual = 0.0
        if datos.descuento_manual_porcentaje is not None:
            descuento_manual = subtotal * (datos.descuento_manual_porcentaje / 100)
        elif datos.descuento_manual_monto is not None:
            descuento_manual = min(datos.descuento_manual_monto, subtotal)

        # --- Descuento automático por rango de fidelización (Bronce/Plata/Oro) ---
        # Se calcula con el histórico ANTES de sumar los puntos de esta venta —
        # el nivel del cliente es el que ya tenía al llegar a caja, no el que
        # tendría después de comprar.
        descuento_fidelizacion = 0.0
        rango_aplicado: str | None = None
        if cliente is not None:
            rango = await fidelizacion_service.obtener_rango_para_puntos(
                db, cliente.puntos_totales_historicos
            )
            if rango is not None:
                rango_aplicado = rango.nombre
                descuento_fidelizacion = subtotal * (float(rango.porcentaje_descuento) / 100)

        total = max(
            subtotal - descuento_puntos - descuento_manual - descuento_fidelizacion, 0.0
        )

        venta = Venta(
            canal=datos.canal,
            sesion_caja_id=datos.sesion_caja_id,
            cliente_id=datos.cliente_id,
            subtotal=subtotal,
            descuento_puntos=descuento_puntos,
            descuento_manual=descuento_manual,
            motivo_descuento_manual=datos.motivo_descuento_manual,
            descuento_fidelizacion=descuento_fidelizacion,
            rango_fidelizacion_aplicado=rango_aplicado,
            total=total,
            metodo_pago=datos.metodo_pago,
            estado_factura_dian=EstadoFacturaDian.PENDIENTE,
        )
        db.add(venta)
        await db.flush()  # necesitamos venta.id para las líneas y el historial de puntos

        for linea in datos.lineas:
            variante = variantes[linea.variante_id]
            db.add(
                DetalleVenta(
                    venta_id=venta.id,
                    variante_id=variante.id,
                    cantidad=linea.cantidad,
                    precio_unitario=variante.precio_venta,
                )
            )
        await db.flush()  # dispara trg_descontar_stock en PostgreSQL

        if cliente is not None:
            if datos.puntos_a_redimir > 0:
                await fidelizacion_service.redimir_puntos(
                    db, cliente, datos.puntos_a_redimir, venta.id
                )
                venta.puntos_redimidos = datos.puntos_a_redimir

            movimiento_ganado = await fidelizacion_service.ganar_puntos(
                db, cliente, total, venta.id
            )
            venta.puntos_ganados = movimiento_ganado.puntos

        await db.commit()

    except Exception:
        await db.rollback()
        raise

    return await obtener_venta(db, venta.id)


async def listar_ventas(
    db: AsyncSession,
    canal: CanalVenta | None = None,
    sesion_caja_id: int | None = None,
    fecha: date | None = None,
    limite: int = 100,
) -> list[Venta]:
    """Historial de ventas para administración y para el buscador de devoluciones."""
    query = select(Venta).options(_con_detalles_completos()).order_by(Venta.creado_en.desc())

    if canal is not None:
        query = query.where(Venta.canal == canal)
    if sesion_caja_id is not None:
        query = query.where(Venta.sesion_caja_id == sesion_caja_id)
    if fecha is not None:
        inicio_dia = datetime.combine(fecha, datetime.min.time())
        fin_dia = inicio_dia + timedelta(days=1)
        query = query.where(Venta.creado_en >= inicio_dia, Venta.creado_en < fin_dia)

    query = query.limit(limite)
    resultado = await db.execute(query)
    return list(resultado.scalars().unique().all())


async def obtener_venta(db: AsyncSession, venta_id: int) -> Venta | None:
    query = select(Venta).options(_con_detalles_completos()).where(Venta.id == venta_id)
    resultado = await db.execute(query)
    return resultado.scalar_one_or_none()