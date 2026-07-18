# TramaPos · Agente de Hardware

Programa que corre en el PC de cada caja física y habla directamente
con la ticketera térmica/cajón monedero por USB. El navegador nunca
puede hacer esto por sí solo (por seguridad), así que este agente hace
de puente entre el POS (en el navegador) y el hardware real.

## 1. Compilarlo como .exe (una sola vez, en un PC con Python)

```cmd
cd hardware-agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
build_exe.bat
```

Esto genera `dist\TramaPos-Agente.exe` — un archivo único que **no
necesita tener Python instalado** para correr. Cópialo a cualquier PC
de caja (ej. en una carpeta `C:\TramaPos\`).

## 2. Configurar la impresora (primera vez en cada PC)

1. Corre `TramaPos-Agente.exe` una vez (doble click). Va a crear un
   archivo `config.json` al lado del `.exe`, con valores de ejemplo, y
   te va a avisar que la impresora no se encontró — es normal la
   primera vez.
2. Necesitas el **vendor_id** y **product_id** reales de tu ticketera:
   - Abre el **Administrador de dispositivos** de Windows (`Windows + X` → "Administrador de dispositivos").
   - Busca tu impresora (usualmente bajo "Dispositivos USB" o "Controladoras de bus USB").
   - Click derecho → Propiedades → pestaña "Detalles" → selecciona "ID de hardware".
   - Vas a ver algo como `USB\VID_04B8&PID_0202...` — `VID_04B8` es el vendor_id (`0x04b8`) y `PID_0202` es el product_id (`0x0202`).
3. Abre `config.json` con el Bloc de notas y reemplaza esos dos valores:
   ```json
   {
     "impresora_vendor_id": "0x04b8",
     "impresora_product_id": "0x0202",
     "ws_host": "localhost",
     "ws_port": 9100
   }
   ```
4. Vuelve a correr `TramaPos-Agente.exe`. Debería decir que está escuchando, sin el error de impresora.

## 3. Hacer que arranque solo al prender el PC (recomendado)

Así el cajero nunca tiene que acordarse de abrirlo manualmente:

1. Presiona `Windows + R`, escribe `shell:startup` y Enter — se abre una carpeta.
2. Copia un **acceso directo** de `TramaPos-Agente.exe` dentro de esa carpeta (click derecho sobre el .exe → "Crear acceso directo", y mueve el acceso directo a la carpeta de inicio).
3. Listo — desde el próximo reinicio, el agente arranca solo (aparece una ventana negra de consola; el cajero solo debe dejarla abierta, minimizada).

## 4. Probarlo

Con el agente corriendo y el POS abierto en el navegador (`npm run dev` o la versión de producción), presiona `Ctrl+Shift+O` en el POS — el cajón debería abrirse sin imprimir nada. Si haces una venta completa (F10), debería imprimir el ticket y abrir el cajón.

## Notas

- Si cambias de ticketera, solo edita `config.json` — no hace falta volver a compilar el `.exe`.
- El agente solo acepta conexiones desde `localhost` (el mismo PC) — no es accesible desde la red, por seguridad.
- Si ves la ventana cerrarse sola con un error, vuelve a abrir el `.exe` desde una consola (`cmd`, navega a la carpeta y escribe `TramaPos-Agente.exe`) para ver el mensaje de error completo en vez de que la ventana se cierre antes de poder leerlo.
