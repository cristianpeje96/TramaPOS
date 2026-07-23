"""
TramaPos · Lógica de negocio de cotizaciones.
"""

from io import BytesIO

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.cotizaciones.models import Cotizacion, DetalleCotizacion, EstadoCotizacion
from app.modules.cotizaciones.schemas import CotizacionCrear, FacturarCotizacionIn
from app.modules.productos.models import VarianteProducto
from app.modules.ventas.models import CanalVenta
from app.modules.ventas.schemas import LineaVentaCrear, VentaCrear
from app.modules.ventas.service import procesar_venta


def _con_detalles_completos():
    return (
        selectinload(Cotizacion.detalles)
        .selectinload(DetalleCotizacion.variante)
        .selectinload(VarianteProducto.producto),
        selectinload(Cotizacion.cliente),
    )


async def _generar_siguiente_numero(db: AsyncSession) -> str:
    query = select(Cotizacion.numero).where(Cotizacion.numero.like("COT-%"))
    resultado = await db.execute(query)
    numeros = []
    for (numero,) in resultado.all():
        sufijo = numero.replace("COT-", "")
        if sufijo.isdigit():
            numeros.append(int(sufijo))
    siguiente = (max(numeros) + 1) if numeros else 1
    return f"COT-{siguiente:04d}"


async def crear_cotizacion(
    db: AsyncSession, datos: CotizacionCrear, usuario_id: int | None
) -> Cotizacion:
    variante_ids = [l.variante_id for l in datos.lineas]
    query_variantes = select(VarianteProducto).where(VarianteProducto.id.in_(variante_ids))
    resultado = await db.execute(query_variantes)
    variantes = {v.id: v for v in resultado.scalars().all()}
    faltantes = set(variante_ids) - set(variantes.keys())
    if faltantes:
        raise ValueError(f"Variantes inexistentes: {faltantes}")

    subtotal = sum(
        l.cantidad * (l.precio_unitario if l.precio_unitario is not None else float(variantes[l.variante_id].precio_venta))
        for l in datos.lineas
    )
    total = max(subtotal - datos.descuento_manual, 0.0)
    numero = await _generar_siguiente_numero(db)

    cotizacion = Cotizacion(
        numero=numero,
        cliente_id=datos.cliente_id,
        cliente_nombre=datos.cliente_nombre,
        cliente_telefono=datos.cliente_telefono,
        cliente_email=datos.cliente_email,
        fecha_vencimiento=datos.fecha_vencimiento,
        notas=datos.notas,
        subtotal=subtotal,
        descuento_manual=datos.descuento_manual,
        total=total,
        usuario_id=usuario_id,
    )
    db.add(cotizacion)
    await db.flush()

    for linea in datos.lineas:
        variante = variantes[linea.variante_id]
        precio = linea.precio_unitario if linea.precio_unitario is not None else variante.precio_venta
        db.add(
            DetalleCotizacion(
                cotizacion_id=cotizacion.id,
                variante_id=linea.variante_id,
                cantidad=linea.cantidad,
                precio_unitario=precio,
            )
        )

    await db.commit()
    return await obtener_cotizacion(db, cotizacion.id)


async def listar_cotizaciones(
    db: AsyncSession, estado: EstadoCotizacion | None = None, limite: int = 100
) -> list[Cotizacion]:
    query = (
        select(Cotizacion).options(*_con_detalles_completos()).order_by(Cotizacion.creado_en.desc())
    )
    if estado is not None:
        query = query.where(Cotizacion.estado == estado)
    query = query.limit(limite)
    resultado = await db.execute(query)
    return list(resultado.scalars().unique().all())


async def obtener_cotizacion(db: AsyncSession, cotizacion_id: int) -> Cotizacion | None:
    query = (
        select(Cotizacion)
        .options(*_con_detalles_completos())
        .where(Cotizacion.id == cotizacion_id)
    )
    resultado = await db.execute(query)
    return resultado.scalar_one_or_none()


async def cambiar_estado(
    db: AsyncSession, cotizacion_id: int, nuevo_estado: EstadoCotizacion
) -> Cotizacion:
    cotizacion = await obtener_cotizacion(db, cotizacion_id)
    if cotizacion is None:
        raise ValueError(f"Cotización {cotizacion_id} no encontrada")
    if cotizacion.estado == EstadoCotizacion.FACTURADA:
        raise ValueError("Esta cotización ya fue facturada, no se puede cambiar su estado")
    cotizacion.estado = nuevo_estado
    await db.commit()
    return await obtener_cotizacion(db, cotizacion_id)


async def facturar_cotizacion(
    db: AsyncSession, cotizacion_id: int, datos: FacturarCotizacionIn, usuario_id: int
):
    """
    Convierte una cotización APROBADA en una venta real, respetando
    EXACTAMENTE los precios que se cotizaron (aunque el catálogo haya
    cambiado de precio desde entonces) — nadie vuelve a digitar nada.
    """
    cotizacion = await obtener_cotizacion(db, cotizacion_id)
    if cotizacion is None:
        raise ValueError(f"Cotización {cotizacion_id} no encontrada")
    if cotizacion.estado == EstadoCotizacion.FACTURADA:
        raise ValueError("Esta cotización ya fue facturada anteriormente")
    if cotizacion.estado != EstadoCotizacion.APROBADA:
        raise ValueError("Solo se puede facturar una cotización en estado APROBADA")

    porcentaje_descuento = (
        (cotizacion.descuento_manual / cotizacion.subtotal * 100) if cotizacion.subtotal > 0 else 0
    )

    venta_datos = VentaCrear(
        canal=CanalVenta.POS,
        sesion_caja_id=datos.sesion_caja_id,
        cliente_id=cotizacion.cliente_id,
        metodo_pago=datos.metodo_pago,
        lineas=[
            LineaVentaCrear(
                variante_id=d.variante_id, cantidad=d.cantidad, precio_unitario=d.precio_unitario
            )
            for d in cotizacion.detalles
        ],
        descuento_manual_porcentaje=round(porcentaje_descuento, 2) if porcentaje_descuento > 0 else None,
        motivo_descuento_manual=f"Cotización {cotizacion.numero}" if porcentaje_descuento > 0 else None,
    )
    venta = await procesar_venta(db, venta_datos, vendedor_id=usuario_id)

    cotizacion.estado = EstadoCotizacion.FACTURADA
    cotizacion.venta_id = venta.id
    await db.commit()

    return await obtener_cotizacion(db, cotizacion_id), venta


def generar_pdf(cotizacion: Cotizacion, nombre_empresa: str = "TramaPos") -> bytes:
    """Genera el PDF descargable/enviable de la cotización con reportlab."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=2 * cm, bottomMargin=2 * cm)
    estilos = getSampleStyleSheet()
    titulo_style = ParagraphStyle("Titulo", parent=estilos["Heading1"], textColor=colors.HexColor("#1d3557"))

    elementos = [
        Paragraph(nombre_empresa, titulo_style),
        Paragraph(f"Cotización {cotizacion.numero}", estilos["Heading2"]),
        Spacer(1, 0.3 * cm),
        Paragraph(f"Fecha: {cotizacion.fecha_emision.strftime('%d/%m/%Y')}", estilos["Normal"]),
    ]
    if cotizacion.fecha_vencimiento:
        elementos.append(
            Paragraph(f"Válida hasta: {cotizacion.fecha_vencimiento.strftime('%d/%m/%Y')}", estilos["Normal"])
        )
    nombre_cliente = (cotizacion.cliente.nombre_completo if cotizacion.cliente_id and getattr(cotizacion, "cliente", None) else cotizacion.cliente_nombre) or "Cliente de mostrador"
    elementos.append(Paragraph(f"Cliente: {nombre_cliente}", estilos["Normal"]))
    elementos.append(Spacer(1, 0.6 * cm))

    filas = [["Producto", "Cantidad", "Precio unit.", "Subtotal"]]
    for d in cotizacion.detalles:
        nombre = d.producto_nombre + (f" · {d.color}" if d.color else "")
        filas.append(
            [
                nombre,
                f"{d.cantidad:g}",
                f"${d.precio_unitario:,.0f}",
                f"${d.cantidad * d.precio_unitario:,.0f}",
            ]
        )
    tabla = Table(filas, colWidths=[8 * cm, 2.5 * cm, 3 * cm, 3 * cm])
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d3557")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ]
        )
    )
    elementos.append(tabla)
    elementos.append(Spacer(1, 0.4 * cm))

    if cotizacion.descuento_manual > 0:
        elementos.append(Paragraph(f"Subtotal: ${cotizacion.subtotal:,.0f}", estilos["Normal"]))
        elementos.append(Paragraph(f"Descuento: -${cotizacion.descuento_manual:,.0f}", estilos["Normal"]))
    elementos.append(Paragraph(f"<b>Total: ${cotizacion.total:,.0f}</b>", estilos["Heading3"]))

    if cotizacion.notas:
        elementos.append(Spacer(1, 0.4 * cm))
        elementos.append(Paragraph(f"Notas: {cotizacion.notas}", estilos["Normal"]))

    doc.build(elementos)
    return buffer.getvalue()