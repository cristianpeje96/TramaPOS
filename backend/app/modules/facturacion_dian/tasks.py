"""
TramaPos · Background task de facturación electrónica DIAN.

Se ejecuta DESPUÉS de que la respuesta HTTP de POST /ventas ya volvió
al frontend (ver app/modules/ventas/router.py). Por eso abre su PROPIA
sesión de base de datos — la sesión original de la request ya se cerró
para cuando esta función corre.

Nota de producción: FastAPI BackgroundTasks es "fire and forget" — si el
servidor se reinicia a mitad del envío, la tarea se pierde sin reintento
automático. Para volumen alto/soporte de reintentos robustos, migrar esta
función a un worker de Celery (ya está en requirements.txt) es el siguiente
paso natural; la firma de la función no cambiaría.

El payload exacto que espera el proveedor tecnológico (Factus, Alegra,
Siigo, etc.) varía según cuál se contrate — aquí se deja la estructura
genérica; ajustar `_construir_payload_dian` al conectar el proveedor real.
"""

import logging

import httpx
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.session import SessionLocal
from app.modules.clientes.models import Cliente
from app.modules.ventas.models import EstadoFacturaDian, Venta

logger = logging.getLogger("facturacion_dian")


def _construir_payload_dian(venta: Venta, cliente: Cliente | None) -> dict:
    return {
        "nit_emisor": settings.dian_nit_emisor,
        "ambiente": settings.dian_ambiente,
        "uuid_venta": str(venta.uuid_publico),
        "cliente": {
            "tipo_documento": cliente.tipo_documento if cliente else "CC",
            "numero_documento": cliente.numero_documento if cliente else "222222222222",
            "nombre": cliente.nombre_completo if cliente else "Consumidor final",
        },
        "items": [
            {
                "variante_id": detalle.variante_id,
                "cantidad": float(detalle.cantidad),
                "precio_unitario": float(detalle.precio_unitario),
            }
            for detalle in venta.detalles
        ],
        "subtotal": float(venta.subtotal),
        "descuento": float(venta.descuento_puntos),
        "total": float(venta.total),
    }


async def enviar_factura_dian(venta_id: int) -> None:
    async with SessionLocal() as db:
        venta = await db.get(Venta, venta_id, options=[selectinload(Venta.detalles)])
        if venta is None:
            logger.error(f"enviar_factura_dian: venta {venta_id} no encontrada")
            return

        cliente = None
        if venta.cliente_id is not None:
            cliente = await db.get(Cliente, venta.cliente_id)

        payload = _construir_payload_dian(venta, cliente)

        try:
            async with httpx.AsyncClient(
                base_url=settings.dian_provider_base_url, timeout=30.0
            ) as client:
                respuesta = await client.post(
                    "/facturas",
                    json=payload,
                    headers={"Authorization": f"Bearer {settings.dian_provider_api_key}"},
                )
                respuesta.raise_for_status()

            venta.estado_factura_dian = EstadoFacturaDian.ENVIADA
            logger.info(f"Factura DIAN enviada correctamente para venta {venta_id}")

        except httpx.HTTPError as exc:
            venta.estado_factura_dian = EstadoFacturaDian.RECHAZADA
            logger.error(f"Error enviando factura DIAN para venta {venta_id}: {exc}")

        await db.commit()


async def reintentar_factura_dian(venta_id: int) -> None:
    """Permite reintentar manualmente una factura que quedó RECHAZADA."""
    await enviar_factura_dian(venta_id)
