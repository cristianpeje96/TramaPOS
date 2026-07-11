"""
TramaPos · Hub de WebSocket del backend.

OJO: esto NO es el agente de hardware (hardware_agent.py) — ese corre
local en cada PC y habla con la ticketera/cajón. Este hub vive en el
BACKEND y sirve para sincronizar en tiempo real varios terminales POS
de la misma tienda entre sí. Ejemplo real: si Surthilanas tiene 2 cajas
y en la caja 1 se vende la última unidad de un color de Hilo Guajira,
la caja 2 se entera al instante sin tener que refrescar ni hacer polling.

Conexión desde el frontend: ws://<backend>/ws/notificaciones
"""

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("websockets_hub")

router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self._conexiones_activas: set[WebSocket] = set()

    async def conectar(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._conexiones_activas.add(websocket)
        logger.info(f"Terminal POS conectado. Total activos: {len(self._conexiones_activas)}")

    def desconectar(self, websocket: WebSocket) -> None:
        self._conexiones_activas.discard(websocket)
        logger.info(f"Terminal POS desconectado. Total activos: {len(self._conexiones_activas)}")

    async def difundir(self, evento: str, datos: dict) -> None:
        """Envía un evento a TODOS los terminales POS conectados."""
        mensaje = json.dumps({"evento": evento, "datos": datos})
        muertos = []
        for conexion in self._conexiones_activas:
            try:
                await conexion.send_text(mensaje)
            except Exception:
                muertos.append(conexion)
        for conexion in muertos:
            self.desconectar(conexion)


# Instancia única compartida por toda la app (importar desde otros módulos)
connection_manager = ConnectionManager()


@router.websocket("/ws/notificaciones")
async def endpoint_notificaciones(websocket: WebSocket):
    await connection_manager.conectar(websocket)
    try:
        while True:
            # No esperamos mensajes del cliente por ahora, solo mantenemos
            # la conexión viva; si el POS manda algo, se ignora o se loguea.
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.desconectar(websocket)


# --- Helpers para disparar eventos desde otros módulos ---


async def notificar_stock_actualizado(variante_id: int, stock_actual: float) -> None:
    await connection_manager.difundir(
        "stock_actualizado", {"variante_id": variante_id, "stock_actual": stock_actual}
    )


async def notificar_venta_creada(venta_id: int, canal: str) -> None:
    await connection_manager.difundir("venta_creada", {"venta_id": venta_id, "canal": canal})