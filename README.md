# TaxiCab Bitácora

Envío automático de la bitácora diaria y el recap semanal por correo.

Cada persona del equipo genera su bitácora del día con Claude (di **"cerrar el día"**,
ver `skill/cerrar-dia/`, que se instala una vez (paso 0)) y su propio equipo la manda por correo al día
siguiente: la diaria todos los días, el recap semanal los lunes. Si no hay archivo
nuevo, no manda nada; si el archivo ya se envió, no lo repite.

Necesitas: **Python 3.8 o más nuevo** y **Chrome o Edge** (para el PDF adjunto). Windows
trae Edge. No hay que instalar paquetes de Python.

## 0. Instalar la instrucción "cerrar el día" (una vez)

Copia `skill/cerrar-dia` a la carpeta de skills de tu usuario, para que Claude la conozca
en cualquier proyecto (por ejemplo en TaxiCab):

```bash
mkdir -p ~/.claude/skills && cp -R skill/cerrar-dia ~/.claude/skills/        # Mac / Linux
```
```powershell
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null; Copy-Item -Recurse skill\cerrar-dia "$HOME\.claude\skills\"   # Windows
```

Después abre `SKILL.md` en esa carpeta y escribe en la línea `RUTA_BITACORA:` la carpeta
donde clonaste este repo.

## 1. Contraseña de aplicación de Google

Gmail no deja entrar a un script con tu contraseña normal.

1. Activa la verificación en 2 pasos en tu cuenta de Google.
2. Entra a <https://myaccount.google.com/apppasswords>, nómbrala **TaxiCab Bitácora**.
3. Copia la clave de 16 caracteres: Google no la vuelve a mostrar.

## 2. Tus datos

```bash
cp .env.example .env        # en Windows: copy .env.example .env
```

Llena `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `DESTINATARIO`, `DESTINATARIO_NOMBRE` y
`REMITENTE_NOMBRE` (tu nombre). El `.env` no se sube a git y **no se comparte**: con él
se pueden mandar correos como tú.

## 3. Probar antes de programar

Genera una bitácora de prueba (o copia `plantilla-bitacora.html` a la carpeta de reportes
como `2026-01-01-bitacora.html`), pon tu propio correo en `DESTINATARIO` y corre:

```bash
python3 enviar_bitacora.py diaria        # Windows: py enviar_bitacora.py diaria
```

Debe terminar con `Enviado a …`. Cuando funcione, pon el destinatario real.

## 4. Programarlo

### Windows (Programador de tareas)

En PowerShell, dentro de esta carpeta:

```powershell
powershell -ExecutionPolicy Bypass -File .\instalar_windows.ps1
```

Copia el script y tu `.env` a `%LOCALAPPDATA%\TaxiCab-Bitacora` (así sigue funcionando si
cambias de rama) y crea dos tareas: diaria a las 08:20 y semanal los lunes. Si el equipo
estaba apagado o dormido a esa hora, la tarea corre al encenderse. Otra hora:
`-Hora 07:30`. Quitar: `-Desinstalar`.

Importante: si después cambias el `.env` de esta carpeta, vuelve a correr el instalador o
edita el de `%LOCALAPPDATA%\TaxiCab-Bitacora`, que es el que usa la tarea.

> Probado en Mac. El instalador de Windows se escribió sin poder ejecutarlo en Windows:
> si algo falla, avisa y se ajusta.

### Mac (launchd)

El equipo debe estar despierto a la hora del envío. Usa dos archivos `.plist` en
`~/Library/LaunchAgents/` que llamen a `python3 enviar_bitacora.py diaria` y `semanal`
(`StartCalendarInterval` a las 8:20; en el semanal, `Weekday` 1). Ojo: macOS bloquea a
launchd en `~/Documents`, así que deja el script y su `.env` en
`~/Library/Application Support/TaxiCab-Bitacora/`. Se activan con
`launchctl load ~/Library/LaunchAgents/<archivo>.plist`.

## Problemas comunes

| Síntoma | Qué hacer |
|---|---|
| `SMTPAuthenticationError` | La contraseña de aplicación está mal o Google la revocó: genera otra y actualiza `.env`. |
| `No encontré Chrome ni Edge` | Instala Chrome o pon la ruta del navegador en `NAVEGADOR` dentro de `.env`. |
| No llegó el correo | Mira Spam la primera vez, corre el script a mano y lee el error. Para reenviar un archivo, borra su línea de `.enviados.log`. |
| Windows: la tarea no corre | En el Programador de tareas, revisa "Resultado de la última ejecución" de las tareas *TaxiCab Bitacora*. |

## Pruebas

```bash
python3 -m unittest -v
```
