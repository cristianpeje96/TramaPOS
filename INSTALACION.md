# TramaPos · Guía de instalación desde cero

Esta guía asume un PC con Windows nuevo (o "limpio"), sin nada de esto instalado todavía. Sigue los pasos en orden — cada uno depende del anterior.

---

## 1. Instalar los programas base

Descarga e instala, en este orden:

1. **Python 3.12** — [python.org/downloads](https://www.python.org/downloads/). Al instalar, marca la casilla **"Add python.exe to PATH"**.
2. **PostgreSQL 16 (o 17)** — [postgresql.org/download/windows](https://www.postgresql.org/download/windows/). Durante la instalación te va a pedir una contraseña para el usuario `postgres` — **anótala**, la vas a necesitar todo el tiempo.
3. **Node.js LTS** (v20 o superior) — [nodejs.org](https://nodejs.org/).
4. **Git** — [git-scm.com](https://git-scm.com/) (instala también "Git Bash", la terminal que hemos usado).
5. *(Opcional, solo si vas a compilar el agente de hardware en este PC)* nada extra — ya viene con Python.

Reinicia el PC después de instalar todo, para que las rutas (`PATH`) queden bien registradas.

> **Nota sobre Git Bash:** en toda esta guía las rutas usan `/` (como `venv/Scripts/activate`), no `\` — Git Bash es una terminal de estilo Unix, y las barras invertidas no funcionan igual que en CMD/PowerShell. Si copias un comando de otro lado con `\`, cámbialo a `/` antes de correrlo aquí.

---

## 2. Clonar el proyecto desde GitHub

Abre Git Bash donde quieras guardar el proyecto (ej. `C:\TramaPOS`) y corre:

```bash
git clone https://github.com/cristianpeje96/TramaPOS.git
cd TramaPOS
```

---

## 3. Crear la base de datos

Con PostgreSQL instalado, abre Git Bash **dentro de la carpeta del proyecto** (`TramaPOS/`) y corre (ajusta la ruta de `psql.exe` si tu versión de PostgreSQL es distinta a la 16):

```bash
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -c "CREATE DATABASE tramapos"
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d tramapos -f schema.sql
```

Te va a pedir la contraseña de `postgres` cada vez (no se ve al escribirla, es normal).

> **Nota:** `schema.sql` ya tiene TODO lo que hemos construido hasta ahora — usuarios, IVA, cajas físicas, compras, categorías, finanzas, cotizaciones, etc. No hace falta correr ningún archivo `migracion_*.sql` aparte en una instalación nueva; esos son solo para actualizar una base que ya existía antes de cada función.

---

## 4. Configurar y levantar el backend

```bash
cd backend
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
```

### Crea tu archivo `.env`

Copia `backend/.env.example` a `backend/.env` (mismo nombre, sin `.example`), y complétalo:

```env
# --- Entorno ---
ENV=production
DEBUG=False
APP_NOMBRE=TramaPos

# --- Base de datos ---
DATABASE_URL=postgresql+asyncpg://postgres:TU_PASSWORD_DE_POSTGRES@localhost:5432/tramapos

# --- Seguridad ---
SECRET_KEY=genera-una-clave-larga-y-aleatoria-aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# --- CORS (el navegador desde donde se usa el POS) ---
CORS_ORIGINS=http://localhost:5173

# --- Facturación electrónica (cuando tengas las credenciales de Factus) ---
DIAN_PROVIDER_BASE_URL=
DIAN_PROVIDER_API_KEY=
DIAN_NIT_EMISOR=
DIAN_AMBIENTE=habilitacion

# --- Agente de hardware ---
HARDWARE_AGENT_WS_URL=ws://localhost:9100

# --- Asistente de IA (opcional) ---
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
```

**`SECRET_KEY`**: no uses cualquier texto — genera una clave real así:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Copia lo que imprima y pégalo como valor de `SECRET_KEY`.

### Crea el primer usuario administrador

```bash
python scripts/crear_usuario_inicial.py
```

### Levanta el backend

```bash
uvicorn app.main:app --reload
```

Debe quedar corriendo en `http://127.0.0.1:8000` — déjalo abierto en esa terminal.

---

## 5. Compilar el frontend (una sola vez, o cada vez que actualicemos el código)

En el computador de la tienda (el que se queda prendido todos los días),
el frontend **no** corre con `npm run dev` — se compila una vez a
archivos estáticos, y el backend los sirve directamente. Así solo hay
**un programa** que mantener corriendo, no dos.

```bash
cd TramaPOS/frontend
npm install
npm run build
```

Esto crea la carpeta `frontend/dist/` — el backend la detecta sola la
próxima vez que arranque.

> **Nota para cuando sigamos desarrollando/agregando funciones:** en tu
> propio PC de trabajo (no el de la tienda), seguimos usando
> `npm run dev` como siempre para ver los cambios al instante — eso no
> cambia. Lo de compilar (`npm run build`) es solo para el computador
> donde va a quedar TramaPos funcionando de verdad, día a día.

---

## 6. El agente de hardware (solo en el PC de cada caja física)

Si este PC va a tener conectada una ticketera/cajón monedero:

```bash
cd TramaPOS/hardware-agent
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
build_exe.bat
```

Sigue el resto de instrucciones en `hardware-agent/README.md` (configurar `config.json` con el nombre de la impresora o su `vendor_id`/`product_id`).

---

## 7. Que todo arranque solo, sin que nadie tenga que abrir una terminal

Con el frontend ya compilado (paso 5), el backend es el único programa
que hay que dejar corriendo — y lo hacemos arrancar solo cuando se
prende el PC, sin ninguna ventana visible para el vendedor.

### 7.1. Prueba que funcione manualmente primero

```bash
cd TramaPOS
./iniciar_backend.bat
```

Abre `http://localhost:8000` en el navegador — deberías ver el POS
completo (ya no hace falta el puerto 5173, todo vive en el 8000 ahora).
Si funciona, ciérralo (`Ctrl+C`) y sigue con el arranque automático.

### 7.2. Arranque automático, sin ventanas

1. Presiona `Windows + R`, escribe `shell:startup` y Enter — se abre una carpeta.
2. Dentro de `TramaPOS/`, click derecho sobre `iniciar_backend_oculto.vbs` → **"Crear acceso directo"**.
3. Mueve ese acceso directo a la carpeta que se abrió en el paso 1.
4. Si este PC también tiene la ticketera conectada: repite lo mismo con `hardware-agent/iniciar_agente_oculto.vbs` (después de haber corrido `build_exe.bat` en el paso 6) — otro acceso directo, a la misma carpeta de inicio.

Desde el próximo reinicio, TramaPos arranca solo — **sin ninguna ventana de consola visible**.

### 7.3. Acceso directo para el vendedor

Crea un acceso directo en el escritorio hacia `http://localhost:8000`
(en el navegador, arrastra el ícono de la URL desde la barra de
direcciones hasta el escritorio) — así el vendedor solo hace doble
click ahí, sin saber que por debajo hay un backend, una base de datos,
etc.

### 7.4. Si algo no arranca

Como el `.vbs` corre todo oculto, si algo falla no vas a ver el error
en pantalla. Para diagnosticar, corre `iniciar_backend.bat` (doble
click normal, sin el `.vbs`) — ahí sí se queda la ventana abierta
mostrando cualquier error.

---

## Resumen de lo que necesitas tener a la mano

| Cosa | Dónde conseguirla |
|---|---|
| Contraseña de PostgreSQL (`postgres`) | La que pusiste al instalar PostgreSQL |
| `SECRET_KEY` | La generas tú mismo (paso 4) |
| Usuario admin de TramaPos | Lo creas tú mismo (paso 4) |
| API key de OpenAI (opcional) | platform.openai.com |
| Credenciales de Factus (cuando estén listas) | Te las da Factus al aprobar tu cuenta |
| `vendor_id`/`product_id` de la ticketera | Administrador de dispositivos de Windows |
