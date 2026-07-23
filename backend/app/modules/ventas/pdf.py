"""
TramaPos · Factura formal en PDF (hoja carta), con membrete de la
empresa — para clientes que necesitan un comprobante más formal que
la tirilla térmica del POS.
"""

from io import BytesIO


def generar_factura_pdf(venta, config_empresa) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=2 * cm, bottomMargin=2 * cm)
    estilos = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        "Titulo", parent=estilos["Heading1"], textColor=colors.HexColor("#1d3557")
    )
    subtitulo_style = ParagraphStyle(
        "Subtitulo", parent=estilos["Normal"], textColor=colors.HexColor("#555555"), fontSize=9
    )

    # --- Membrete ---
    elementos = [Paragraph(config_empresa.razon_social or "TramaPos", titulo_style)]
    datos_membrete = []
    if config_empresa.nit:
        datos_membrete.append(f"NIT: {config_empresa.nit}")
    if config_empresa.direccion:
        datos_membrete.append(config_empresa.direccion)
    if config_empresa.telefono:
        datos_membrete.append(f"Tel: {config_empresa.telefono}")
    if config_empresa.email:
        datos_membrete.append(config_empresa.email)
    if datos_membrete:
        elementos.append(Paragraph(" · ".join(datos_membrete), subtitulo_style))

    elementos.append(Spacer(1, 0.5 * cm))
    elementos.append(Paragraph(f"Factura de venta #{venta.id}", estilos["Heading2"]))
    elementos.append(
        Paragraph(f"Fecha: {venta.creado_en.strftime('%d/%m/%Y %H:%M')}", estilos["Normal"])
    )

    nombre_cliente = venta.cliente.nombre_completo if venta.cliente else "Cliente de mostrador"
    elementos.append(Paragraph(f"Cliente: {nombre_cliente}", estilos["Normal"]))
    if venta.vendedor:
        elementos.append(Paragraph(f"Atendido por: {venta.vendedor.nombre_completo}", estilos["Normal"]))
    elementos.append(Spacer(1, 0.6 * cm))

    # --- Líneas ---
    filas = [["Producto", "Cantidad", "Precio unit.", "Subtotal"]]
    for d in venta.detalles:
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

    # --- Totales ---
    elementos.append(Paragraph(f"Subtotal: ${venta.subtotal:,.0f}", estilos["Normal"]))
    if venta.descuento_manual > 0:
        elementos.append(
            Paragraph(
                f"Descuento{' (' + venta.motivo_descuento_manual + ')' if venta.motivo_descuento_manual else ''}: "
                f"-${venta.descuento_manual:,.0f}",
                estilos["Normal"],
            )
        )
    if venta.descuento_puntos > 0:
        elementos.append(Paragraph(f"Descuento por puntos: -${venta.descuento_puntos:,.0f}", estilos["Normal"]))
    if venta.descuento_fidelizacion > 0:
        elementos.append(
            Paragraph(
                f"Descuento {venta.rango_fidelizacion_aplicado or 'fidelización'}: "
                f"-${venta.descuento_fidelizacion:,.0f}",
                estilos["Normal"],
            )
        )
    if venta.total_iva > 0:
        elementos.append(Paragraph(f"IVA incluido: ${venta.total_iva:,.0f}", estilos["Normal"]))

    elementos.append(Spacer(1, 0.2 * cm))
    elementos.append(Paragraph(f"<b>TOTAL: ${venta.total:,.0f}</b>", estilos["Heading3"]))
    elementos.append(Spacer(1, 0.2 * cm))
    elementos.append(Paragraph(f"Método de pago: {venta.metodo_pago.value.title()}", estilos["Normal"]))

    if venta.puntos_ganados > 0:
        elementos.append(
            Paragraph(f"Puntos ganados en esta compra: {venta.puntos_ganados}", subtitulo_style)
        )

    elementos.append(Spacer(1, 1 * cm))
    elementos.append(
        Paragraph("Gracias por su compra.", ParagraphStyle("Footer", parent=estilos["Normal"], alignment=1))
    )

    doc.build(elementos)
    return buffer.getvalue()