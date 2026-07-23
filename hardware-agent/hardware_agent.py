"""
TramaPos · Agente Local de Hardware
Escucha comandos vía WebSocket desde el frontend React y los traduce
a comandos ESC/POS enviados a la ticketera térmica.

Corre como proceso local en el PC de cada caja (nunca en el servidor).
Pensado para empaquetarse como .exe con PyInstaller — ver build_exe.bat
y README.md en esta misma carpeta.

Soporta DOS formas de conectar con la impresora (se elige en config.json
con "modo_conexion"):
  - "windows" (recomendado si la impresora YA aparece instalada en
    Windows, en "Dispositivos e impresoras") — imprime a través del
    controlador de Windows, usando el NOMBRE exacto de la impresora.
    Requiere pywin32.
  - "usb" (para impresoras que Windows detecta como dispositivo USB
    genérico, no como impresora instalada) — habla USB directo,
    usando vendor_id/product_id.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("tramapos_agente")

# -----------------------------------------------------------------------
# CONFIGURACIÓN — se lee de config.json (al lado del .exe). Si no existe,
# se crea uno con valores de ejemplo la primera vez que corre.
# -----------------------------------------------------------------------
CARPETA_CONFIG = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
RUTA_CONFIG = CARPETA_CONFIG / "config.json"

CONFIG_POR_DEFECTO = {
    "modo_conexion": "windows",
    "impresora_nombre_windows": "BIXOLON SRP-330II",
    "impresora_vendor_id": "0x04b8",
    "impresora_product_id": "0x0202",
    "ws_host": "localhost",
    "ws_port": 9100,
}


def cargar_configuracion() -> dict:
    if not RUTA_CONFIG.exists():
        RUTA_CONFIG.write_text(
            json.dumps(CONFIG_POR_DEFECTO, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        logger.warning(
            f"No existía config.json — se creó uno con valores de ejemplo en {RUTA_CONFIG}. "
            "Revisa 'impresora_nombre_windows' (debe ser EXACTO al nombre en Windows) y "
            "vuelve a abrir el agente."
        )
        return CONFIG_POR_DEFECTO

    try:
        datos = json.loads(RUTA_CONFIG.read_text(encoding="utf-8"))
        return {**CONFIG_POR_DEFECTO, **datos}
    except json.JSONDecodeError:
        logger.error("config.json tiene un error de formato — usando valores por defecto.")
        return CONFIG_POR_DEFECTO


CONFIG = cargar_configuracion()
MODO_CONEXION = CONFIG["modo_conexion"]
IMPRESORA_NOMBRE_WINDOWS = CONFIG["impresora_nombre_windows"]
IMPRESORA_VENDOR_ID = int(CONFIG["impresora_vendor_id"], 16)
IMPRESORA_PRODUCT_ID = int(CONFIG["impresora_product_id"], 16)
WS_HOST = CONFIG["ws_host"]
WS_PORT = int(CONFIG["ws_port"])

# Secuencia ESC/POS estándar para pulso al cajón monedero
CMD_ABRIR_CAJON = bytes([0x1B, 0x70, 0x00, 0x19, 0xFA])


def get_printer():
    """Devuelve una instancia conectada a la ticketera física, según el modo configurado."""
    if MODO_CONEXION == "windows":
        try:
            from escpos.printer import Win32Raw

            impresora = Win32Raw(printer_name=IMPRESORA_NOMBRE_WINDOWS)
            impresora.open()
            return impresora
        except Exception as exc:
            logger.error(
                f"No se pudo conectar a la impresora de Windows '{IMPRESORA_NOMBRE_WINDOWS}': {exc}. "
                "Revisa que el nombre en config.json sea EXACTO al que aparece en "
                "'Dispositivos e impresoras' de Windows, y que pywin32 esté instalado "
                "(pip install pywin32)."
            )
            return None
    else:
        try:
            from escpos.printer import Usb

            return Usb(IMPRESORA_VENDOR_ID, IMPRESORA_PRODUCT_ID)
        except Exception as exc:
            logger.error(
                f"No se pudo conectar a la impresora por USB (vendor={hex(IMPRESORA_VENDOR_ID)}, "
                f"product={hex(IMPRESORA_PRODUCT_ID)}): {exc}. "
                "Revisa que esté encendida, conectada por USB, y que el vendor_id/product_id "
                "en config.json sean los correctos para tu modelo."
            )
            return None


def abrir_cajon(imprimir_ticket: bool = False, contenido_ticket: str | None = None):
    printer = get_printer()
    if printer is None:
        return {"ok": False, "error": "impresora_no_disponible"}

    try:
        if imprimir_ticket and contenido_ticket:
            printer.text(contenido_ticket)
            printer.cut()

        printer._raw(CMD_ABRIR_CAJON)
        logger.info("Cajón monedero abierto correctamente")
        return {"ok": True}
    except Exception as exc:
        logger.error(f"Error abriendo el cajón: {exc}")
        return {"ok": False, "error": str(exc)}
    finally:
        printer.close()


async def manejar_conexion(websocket):
    logger.info("✅ POS conectado al agente de hardware")
    try:
        async for mensaje_raw in websocket:
            try:
                mensaje = json.loads(mensaje_raw)
                accion = mensaje.get("accion")

                if accion == "abrir_cajon_manual":
                    resultado = abrir_cajon(imprimir_ticket=False)
                elif accion == "procesar_venta":
                    ticket = mensaje.get("ticket_texto", "")
                    resultado = abrir_cajon(imprimir_ticket=True, contenido_ticket=ticket)
                else:
                    resultado = {"ok": False, "error": f"accion_desconocida:{accion}"}

                await websocket.send(json.dumps(resultado))

            except json.JSONDecodeError:
                await websocket.send(json.dumps({"ok": False, "error": "json_invalido"}))
            except Exception as exc:
                logger.exception("Error procesando mensaje del frontend")
                await websocket.send(json.dumps({"ok": False, "error": str(exc)}))
    finally:
        logger.info("POS desconectado del agente de hardware")


async def main():
    import websockets

    logger.info("=" * 60)
    logger.info("  TramaPos · Agente de Hardware")
    logger.info("=" * 60)
    logger.info(f"Modo de conexión: {MODO_CONEXION}")
    if MODO_CONEXION == "windows":
        logger.info(f"Impresora de Windows: {IMPRESORA_NOMBRE_WINDOWS}")
    logger.info(f"Escuchando en ws://{WS_HOST}:{WS_PORT}")
    logger.info(f"Configuración cargada de: {RUTA_CONFIG}")
    logger.info("Deja esta ventana abierta mientras uses el POS.")
    logger.info("Para cerrar el agente, cierra esta ventana o presiona Ctrl+C.")
    logger.info("=" * 60)

    async with websockets.serve(manejar_conexion, WS_HOST, WS_PORT):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Agente de hardware detenido.")
    except Exception as exc:
        logger.exception(f"Error inesperado: {exc}")
        input("Presiona Enter para cerrar...")  # evita que el .exe se cierre solo en un crash