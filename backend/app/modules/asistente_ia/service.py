"""
TramaPos · Asistente de IA — administrador de inventario y finanzas.
Usa la API de OpenAI directamente.

Principio de diseño clave: el modelo NUNCA inventa cifras. Antes de
responder cualquier pregunta sobre ventas, inventario o dinero, tiene
que usar una de las "herramientas" de abajo, que consultan la base de
datos real a través de los mismos service.py que ya usa el resto de
TramaPos (reportes, productos). Y el asistente es de SOLO LECTURA — no
tiene ninguna herramienta para crear, modificar o borrar nada. Puede
sugerir una compra, pero nunca la registra él mismo.
"""

import json
from datetime import date, datetime

from openai import AsyncOpenAI

from app.core.config import settings
from app.modules.productos import service as productos_service
from app.modules.reportes import service as reportes_service

_cliente = AsyncOpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = """Eres el asistente de administración de TramaPos, un sistema de punto de \
venta para un negocio de lanas e hilos en Colombia (los montos siempre están en pesos \
colombianos, COP).

Tu función es actuar como un administrador de inventario y un asesor financiero para el \
dueño del negocio. Reglas que debes seguir siempre:

1. SIEMPRE usa las herramientas disponibles para consultar datos reales antes de responder \
cualquier pregunta sobre ventas, inventario, stock o finanzas. Nunca inventes ni estimes \
cifras — si no tienes una herramienta para algo, dilo claramente en vez de adivinar.
2. Eres de SOLO LECTURA. No puedes crear compras, cambiar precios, ni modificar nada del \
sistema. Si el usuario te pide "hacer" algo (ej. "reordena este producto"), dale tu \
recomendación concreta (qué, cuánto, por qué) y explícale que debe registrarlo él mismo \
desde el panel de Compras — nunca digas que ya lo hiciste.
3. Responde en español, de forma concisa y práctica — como un administrador con experiencia \
real, no como un reporte académico. Usa cifras concretas de las herramientas, no vaguedades.
4. Si los datos muestran algo preocupante (stock crítico, caída de ventas), dilo directamente \
pero sin alarmismo — con una recomendación clara de qué hacer.
"""

# Formato de herramientas estilo OpenAI/Kimi (distinto al de Anthropic:
# aquí cada una va envuelta en {"type": "function", "function": {...}})
HERRAMIENTAS = [
    {
        "type": "function",
        "function": {
            "name": "resumen_ventas",
            "description": (
                "Total vendido, número de ventas y ticket promedio en un rango de fechas. "
                "Si no se dan fechas, usa los últimos 30 días."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha_desde": {"type": "string", "description": "Formato YYYY-MM-DD"},
                    "fecha_hasta": {"type": "string", "description": "Formato YYYY-MM-DD"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ventas_por_dia",
            "description": "Ventas día por día en un rango de fechas, para ver tendencias o picos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha_desde": {"type": "string", "description": "Formato YYYY-MM-DD"},
                    "fecha_hasta": {"type": "string", "description": "Formato YYYY-MM-DD"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ventas_por_mes",
            "description": "Ventas agrupadas por mes, para comparar meses o ver tendencia anual.",
            "parameters": {
                "type": "object",
                "properties": {
                    "meses": {
                        "type": "integer",
                        "description": "Cuántos meses atrás, por defecto 12",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "productos_mas_vendidos",
            "description": "Ranking de productos por cantidad e ingresos vendidos en un rango de fechas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha_desde": {"type": "string", "description": "Formato YYYY-MM-DD"},
                    "fecha_hasta": {"type": "string", "description": "Formato YYYY-MM-DD"},
                    "limite": {
                        "type": "integer",
                        "description": "Cuántos productos traer, por defecto 10",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stock_bajo",
            "description": "Lista de variantes de producto cuyo stock actual está en o por debajo del mínimo definido — candidatos a reordenar.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_producto",
            "description": "Busca productos por nombre y trae sus variantes con precio, costo y stock actual.",
            "parameters": {
                "type": "object",
                "properties": {
                    "texto": {
                        "type": "string",
                        "description": "Nombre o parte del nombre a buscar",
                    },
                },
                "required": ["texto"],
            },
        },
    },
]


def _parsear_fecha(valor: str | None) -> date | None:
    if not valor:
        return None
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except ValueError:
        return None


async def _ejecutar_herramienta(db, nombre: str, argumentos: dict) -> object:
    fecha_desde = _parsear_fecha(argumentos.get("fecha_desde"))
    fecha_hasta = _parsear_fecha(argumentos.get("fecha_hasta"))

    if nombre == "resumen_ventas":
        return await reportes_service.obtener_resumen(db, fecha_desde, fecha_hasta)

    if nombre == "ventas_por_dia":
        return await reportes_service.ventas_por_dia(db, fecha_desde, fecha_hasta)

    if nombre == "ventas_por_mes":
        return await reportes_service.ventas_por_mes(db, meses_atras=argumentos.get("meses", 12))

    if nombre == "productos_mas_vendidos":
        return await reportes_service.productos_mas_vendidos_reporte(
            db, fecha_desde, fecha_hasta, limite=argumentos.get("limite", 10)
        )

    if nombre == "stock_bajo":
        variantes = await productos_service.listar_stock_bajo(db)
        return [
            {
                "producto": v.producto.nombre,
                "sku": v.sku,
                "color": v.color,
                "grosor": v.grosor,
                "stock_actual": v.stock_actual,
                "stock_minimo": v.stock_minimo,
            }
            for v in variantes
        ]

    if nombre == "buscar_producto":
        productos = await productos_service.buscar_productos(db, argumentos.get("texto", ""))
        return [
            {
                "nombre": p.nombre,
                "variantes": [
                    {
                        "sku": v.sku,
                        "color": v.color,
                        "grosor": v.grosor,
                        "precio_venta": float(v.precio_venta),
                        "costo_unitario": float(v.costo_unitario) if v.costo_unitario else None,
                        "stock_actual": float(v.stock_actual),
                    }
                    for v in p.variantes
                ],
            }
            for p in productos
        ]

    return {"error": f"Herramienta desconocida: {nombre}"}


async def conversar(db, mensaje: str, historial: list[dict]) -> str:
    """
    Ciclo de conversación con tool use (formato OpenAI/Kimi): le manda
    el mensaje a Kimi, y si pide usar una herramienta, la ejecuta contra
    la base de datos real y le devuelve el resultado, hasta que da una
    respuesta final en texto (máximo 5 vueltas, por seguridad).
    """
    if not settings.openai_api_key:
        return (
            "El asistente de IA todavía no está configurado — falta la API key de OpenAI "
            "en el .env del backend (OPENAI_API_KEY)."
        )

    mensajes = [{"role": "system", "content": SYSTEM_PROMPT}]
    mensajes += [{"role": h["rol"], "content": h["contenido"]} for h in historial]
    mensajes.append({"role": "user", "content": mensaje})

    for _ in range(5):
        respuesta = await _cliente.chat.completions.create(
            model=settings.openai_model,
            max_tokens=1024,
            tools=HERRAMIENTAS,
            messages=mensajes,
        )
        mensaje_respuesta = respuesta.choices[0].message

        if not mensaje_respuesta.tool_calls:
            return mensaje_respuesta.content or ""

        # El mensaje del asistente con los tool_calls hay que reenviarlo
        # tal cual, para que Kimi sepa a qué llamada corresponde cada
        # resultado que le mandemos después.
        mensajes.append(mensaje_respuesta.model_dump(exclude_unset=True))

        for tool_call in mensaje_respuesta.tool_calls:
            nombre_herramienta = tool_call.function.name
            try:
                argumentos = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                argumentos = {}

            resultado = await _ejecutar_herramienta(db, nombre_herramienta, argumentos)
            mensajes.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(resultado, default=str, ensure_ascii=False),
                }
            )

    return "No pude completar la consulta — intenta reformular la pregunta."