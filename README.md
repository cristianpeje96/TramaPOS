# TramaPos

**Sistema de punto de venta e inventario para negocios de venta al detal**, construido a la medida para Surthilanas (tienda de lanas e hilos), pero pensado desde el día 1 para crecer con el negocio.

---

## ¿Qué es TramaPos?

Es la aplicación que usa el negocio todos los días para vender, controlar el inventario, cerrar caja, fidelizar clientes y entender cómo va el negocio — todo en un solo lugar, sin depender de cuadernos, hojas de Excel sueltas, o memoria.

No es un producto genérico comprado por internet: cada decisión de diseño responde a cómo trabaja realmente el negocio — desde los atajos de teclado del cajero hasta cómo se calculan los puntos de fidelización.

---

## ¿Cómo ayuda al día a día del negocio?

### 🧾 Vender más rápido, con menos errores

El punto de venta está diseñado para operarse casi sin tocar el mouse — buscar un producto, escanear un código de barras, elegir cliente, aplicar puntos, cobrar y cerrar la venta, todo con atajos de teclado (`F2`, `F4`, `F7`, `F9`, `F10`). Los productos favoritos y los más vendidos aparecen a un click, así que no hay que buscarlos cada vez. Hasta la calculadora de cambio en efectivo está pensada para que el cajero no tenga que hacer cuentas de cabeza.

### 💰 Nunca perder el control del dinero

Cada turno de caja se abre con un monto inicial y se cierra con un arqueo que le dice al cajero exactamente cuánto debería haber en el cajón — comparado contra lo que realmente cuenta. Si el negocio crece a dos o más cajas registradoras, cada una lleva su propio control, sin mezclarse.

### 🎁 Clientes que vuelven, sin esfuerzo extra

Cada compra suma puntos automáticamente. Los clientes frecuentes (Bronce, Plata, Oro — los nombres y los montos los define el dueño) reciben descuentos automáticos sin que el cajero tenga que acordarse de aplicarlos. Todo queda registrado, así que nunca se pierde el historial de un cliente.

### 📦 Inventario que se cuida solo

El stock baja solo cuando se vende y sube solo cuando llega mercancía nueva de un proveedor — nadie tiene que actualizar un Excel a mano. El sistema avisa cuándo un producto está por agotarse, antes de que sea demasiado tarde para reordenar.

### 📊 Saber qué está funcionando y qué no

Un panel de reportes muestra, con gráficas, cuánto se vendió cada día, cada mes, y cuáles son los productos que más mueven el negocio — información que antes solo vivía en la cabeza del dueño, ahora está a un click.

### 🤖 Un asistente que entiende el negocio

Se le puede preguntar en lenguaje normal — _"¿cuánto vendí la semana pasada?"_, _"¿qué productos se me están agotando?"_ — y responde con datos reales del negocio, no con inventos. Nunca toma decisiones por su cuenta; solo informa y sugiere.

### 🔄 Errores que se pueden corregir sin dolores de cabeza

Si una venta se hizo mal o el cliente devuelve algo, hay una pantalla separada — a propósito, para que nunca se confunda con una venta nueva — que revierte el stock y los puntos automáticamente, con doble confirmación para que nadie lo haga sin querer.

### 🔒 Cada quien ve lo que le corresponde

Los cajeros pueden vender, abrir/cerrar caja y hacer devoluciones. Solo los administradores pueden ver reportes financieros, cambiar precios, o configurar el negocio. Cada acción queda registrada con el nombre de quién la hizo.

### 🌱 Listo para cuando el negocio crezca

El sistema de IVA está preparado y **apagado** — el día que el negocio se constituya formalmente y quede obligado a declarar IVA, se activa con un interruptor, sin tener que reconstruir nada. Lo mismo pasa con soportar varias cajas registradoras, o eventualmente conectar una tienda en línea: la base ya está puesta.

---

## Tecnologías utilizadas

No hace falta entender esto para usar el sistema — es solo referencia para quien vaya a mantenerlo técnicamente.

| Parte                                | Tecnología                      |
| ------------------------------------ | ------------------------------- |
| Backend (el "cerebro" del sistema)   | Python + FastAPI                |
| Base de datos                        | PostgreSQL                      |
| Frontend (lo que se ve y se usa)     | React + Vite                    |
| Autenticación                        | JWT (tokens de sesión)          |
| Agente de hardware (ticketera/cajón) | Python, empaquetado como `.exe` |
| Asistente de IA                      | Claude (API de Anthropic)       |
| Gráficas de reportes                 | Recharts                        |

---

## Estructura del proyecto

```
TramaPOS/
├── backend/           # La lógica de negocio y la API
├── frontend/          # El punto de venta y el panel de administración
├── hardware-agent/    # El programa que conecta con la ticketera/cajón
└── schema.sql         # El diseño completo de la base de datos
```

## Cómo ponerlo en marcha

Instrucciones técnicas detalladas de instalación están en los archivos `README.md` de cada carpeta (`hardware-agent/README.md`, por ejemplo). En resumen, hacen falta 3 partes corriendo al mismo tiempo:

1. **El backend** (`uvicorn app.main:app`) — el servidor que guarda y procesa todo.
2. **El frontend** (`npm run dev`) — lo que se ve en pantalla.
3. **El agente de hardware** (`TramaPos-Agente.exe`) — solo en el PC de cada caja, para la ticketera.

---

_TramaPos — construido a la medida, no comprado de una estantería._
