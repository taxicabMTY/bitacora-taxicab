#!/usr/bin/env python3
# Compatibilidad con Python 3.7+: las anotaciones tipo `Path | None` y
# `tuple[str, str]` sólo funcionan en 3.10+ / 3.9+, esto las convierte
# a strings para que Python no las evalúe.
from __future__ import annotations

"""
Envía por Gmail la última bitácora generada del proyecto TaxiCab.

Uso:
    python3 enviar_bitacora.py diaria      (en Windows: py enviar_bitacora.py diaria)
    python3 enviar_bitacora.py semanal

Modo `diaria`:
    Toma el archivo `YYYY-MM-DD-bitacora.html` MÁS RECIENTE de REPORTES_DIR
    (por defecto Documents/TaxiCab-Notas/Reportes dentro de tu carpeta de usuario)
    y lo envía por correo (inline + PDF adjunto).

Modo `semanal`:
    Toma el archivo `YYYY-MM-DD-semanal.html` MÁS RECIENTE.

Requiere un archivo `.env` en la misma carpeta con:
    GMAIL_USER=tu.correo@gmail.com
    GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx   # contraseña de aplicación (16 chars)
    DESTINATARIO=jefe@empresa.com
    DESTINATARIO_NOMBRE=Nombre del Jefe
    REMITENTE_NOMBRE=Luis
    REPORTES_DIR=              (opcional)
    ULTIMOS_ENVIOS_LOG=        (opcional)
    NAVEGADOR=                 (opcional: ruta de Chrome/Edge si no lo encuentra)

Registra en `ULTIMOS_ENVIOS_LOG` cada envío para evitar duplicados y
no envía nada si el archivo más reciente ya fue enviado.
"""
import os
import sys
import re
import ssl
import glob
import shutil
import platform
import smtplib
import subprocess
import tempfile
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

# En Windows la consola usa cp1252 y no imprime «·» ni acentos: sin esto el
# script se cae al escribir su propio log.
for _flujo in (sys.stdout, sys.stderr):
    try:
        _flujo.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def cargar_env(path: Path) -> dict:
    if not path.exists():
        die(f"No encontré {path}. Copia .env.template como .env y llénalo.")
    env = {}
    # utf-8-sig: el Bloc de notas de Windows guarda un BOM al inicio.
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def die(msg: str) -> None:
    print(f"[bitacora] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[bitacora] {ts} · {msg}")


def buscar_ultima_bitacora(reportes_dir: Path, tipo: str) -> Path | None:
    """
    tipo = "diaria" → busca YYYY-MM-DD-bitacora.html
    tipo = "semanal" → busca YYYY-MM-DD-semanal.html
    """
    sufijo = "bitacora" if tipo == "diaria" else "semanal"
    patron = str(reportes_dir / f"*-{sufijo}.html")
    candidatos = sorted(glob.glob(patron))
    if not candidatos:
        return None
    return Path(candidatos[-1])


def ya_enviado(log_path: Path, archivo: Path) -> bool:
    if not log_path.exists():
        return False
    return archivo.name in log_path.read_text(encoding="utf-8").splitlines()


def marcar_enviado(log_path: Path, archivo: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"{archivo.name}\n")


def reportes_por_defecto(home: Path) -> Path:
    return home / "Documents" / "TaxiCab-Notas" / "Reportes"


def url_de_archivo(path: Path) -> str:
    """`file:///…` válido en Windows y Mac (con espacios y letras de unidad)."""
    return path.resolve().as_uri()


def buscar_navegador(sistema=None, existe=None, which=None, env=None) -> str | None:
    """
    Ruta de un navegador Chromium para imprimir el PDF, o None.
    Orden: NAVEGADOR del entorno, Chrome, Edge (viene con Windows), Chromium.
    Los parámetros existen para poder probarlo sin tocar el disco.
    """
    sistema = sistema or platform.system()
    existe = existe or (lambda p: Path(p).exists())
    which = which or shutil.which
    env = os.environ if env is None else env

    if env.get("NAVEGADOR"):
        return env["NAVEGADOR"]

    if sistema == "Darwin":
        candidatos = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        ]
    elif sistema == "Windows":
        carpetas = [env.get(k) for k in ("ProgramFiles", "ProgramFiles(x86)", "LocalAppData")]
        carpetas = [Path(c) for c in carpetas if c]
        candidatos = [
            str(c / sub)
            for sub in ("Google/Chrome/Application/chrome.exe", "Microsoft/Edge/Application/msedge.exe")
            for c in carpetas
        ]
    else:
        candidatos = []

    for c in candidatos:
        if existe(c):
            return c
    for nombre in ("google-chrome", "chromium", "chromium-browser", "chrome", "msedge"):
        encontrado = which(nombre)
        if encontrado:
            return encontrado
    return None


def html_a_pdf(html_path: Path) -> Path:
    """
    Renderiza el HTML a PDF con Chrome o Edge en modo headless.
    Devuelve la ruta al PDF generado en un tempfile.
    """
    navegador = buscar_navegador()
    if not navegador:
        die(
            "No encontré Chrome ni Edge. Instala Chrome o pon la ruta de tu navegador "
            "en NAVEGADOR dentro del .env."
        )

    fd, nombre = tempfile.mkstemp(suffix=".pdf", prefix="bitacora-")
    os.close(fd)  # en Windows el navegador no puede escribir un archivo que sigue abierto
    pdf_path = Path(nombre)
    result = subprocess.run(
        [
            navegador,
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}",
            url_de_archivo(html_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not pdf_path.exists() or pdf_path.stat().st_size < 500:
        die(f"El navegador falló al generar el PDF:\n{result.stderr}")
    return pdf_path


def extraer_titulo_y_body(html: str) -> tuple[str, str]:
    """Devuelve (título de la página, HTML del <body> o del bloque .page)."""
    title_match = re.search(r"<title>([^<]+)</title>", html, flags=re.IGNORECASE)
    titulo = title_match.group(1).strip() if title_match else "Bitácora TaxiCab"

    body_match = re.search(
        r'<div class="page">(.*?)</div>\s*(?=<script|$)',
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if body_match:
        return titulo, body_match.group(1)

    body_match = re.search(r"<body[^>]*>(.*?)</body>", html, flags=re.DOTALL | re.IGNORECASE)
    if body_match:
        return titulo, body_match.group(1)

    return titulo, html


def construir_correo_html(titulo: str, body_html: str, env: dict) -> str:
    """
    Envuelve el body del reporte en un HTML compatible con clientes de correo:
    estilos inline, sin dependencias externas, fuentes de sistema.
    """
    css_email = """
    <style>
      body {
        margin: 0; padding: 24px;
        background: #ffffff;
        color: #1E1E1E;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        font-size: 15px;
        line-height: 1.55;
      }
      .wrapper { max-width: 640px; margin: 0 auto; }
      .aviso {
        background: #FBF7EE;
        border-left: 3px solid #7B3F00;
        padding: 12px 16px;
        margin-bottom: 24px;
        font-size: 13px;
        color: #4B4744;
      }
      h1, h2, h3 { font-family: Georgia, "Times New Roman", serif; font-weight: 500; margin: 0 0 12px; }
      h1 { font-size: 28px; letter-spacing: -0.01em; }
      h2.section { font-size: 20px; margin-top: 32px; margin-bottom: 16px; color: #1E1E1E; }
      h3 { font-size: 17px; }
      p { margin: 0 0 10px; }
      .tldr {
        background: #FBF7EE;
        border-left: 3px solid #7B3F00;
        padding: 16px 20px;
        margin: 24px 0;
      }
      .tldr h2 {
        font-family: Menlo, Consolas, monospace;
        font-size: 11px; text-transform: uppercase; letter-spacing: 0.14em;
        color: #7A7570; margin: 0 0 8px;
      }
      .tldr p { font-family: Georgia, serif; font-size: 17px; margin: 0; color: #1E1E1E; }
      .change {
        border: 1px solid #D6CDBC;
        border-radius: 6px;
        padding: 18px 20px;
        margin: 0 0 18px;
        background: #FBF7EE;
      }
      .change-head { margin-bottom: 12px; }
      .status {
        display: inline-block;
        font-family: Menlo, monospace;
        font-size: 10px; letter-spacing: 0.09em;
        text-transform: uppercase; font-weight: 600;
        padding: 3px 9px; border-radius: 999px;
        margin-left: 8px;
      }
      .status.done { background: #E4EDE5; color: #275640; }
      .status.progress { background: #F1E4CA; color: #7C5000; }
      .status.deployed { background: #E1E6F1; color: #2C4478; }
      .facts { margin: 12px 0; padding: 10px 0; border-top: 1px dashed #D6CDBC; border-bottom: 1px dashed #D6CDBC; }
      .facts > div { margin: 6px 0; }
      .facts dt {
        display: inline-block;
        font-family: Menlo, monospace; font-size: 10px;
        text-transform: uppercase; letter-spacing: 0.12em;
        color: #7A7570; margin-right: 8px;
      }
      .facts dd { display: inline; margin: 0; font-size: 14px; }
      .role {
        display: inline-block; font-family: Menlo, monospace; font-size: 11px;
        padding: 1px 6px; border: 1px solid #B9AF9B; border-radius: 3px;
        margin-right: 4px; color: #4B4744;
      }
      .what .label {
        font-family: Menlo, monospace; font-size: 10px; letter-spacing: 0.12em;
        text-transform: uppercase; color: #7A7570;
        display: block; margin-bottom: 3px;
      }
      .note {
        font-size: 13px; color: #4B4744; background: #ffffff;
        border: 1px solid #D6CDBC; border-radius: 4px;
        padding: 8px 12px; font-style: italic; margin-top: 10px;
      }
      .eyebrow { display: none; }
      .masthead-meta { display: none; }
      .print-btn { display: none; }
      footer {
        margin-top: 32px; padding-top: 16px;
        border-top: 1px solid #D6CDBC;
        font-family: Menlo, monospace; font-size: 11px;
        color: #7A7570; text-transform: uppercase; letter-spacing: 0.08em;
      }
    </style>
    """.strip()

    aviso = (
        f'<div class="aviso">Reporte del proyecto <b>TaxiCab</b> enviado automáticamente por '
        f'{env.get("REMITENTE_NOMBRE") or "el equipo"}. También se adjunta como PDF.</div>'
    )
    return f"""<!doctype html>
<html lang="es"><head>
<meta charset="utf-8">
<title>{titulo}</title>
{css_email}
</head>
<body>
<div class="wrapper">
{aviso}
{body_html}
</div>
</body></html>"""


def enviar_correo(env: dict, asunto: str, cuerpo_html: str, pdf_path: Path, nombre_pdf: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = f'{env.get("REMITENTE_NOMBRE", "TaxiCab")} <{env["GMAIL_USER"]}>'
    dest_nombre = env.get("DESTINATARIO_NOMBRE", "").strip()
    if dest_nombre:
        msg["To"] = f'{dest_nombre} <{env["DESTINATARIO"]}>'
    else:
        msg["To"] = env["DESTINATARIO"]
    msg["Reply-To"] = env["GMAIL_USER"]

    msg.set_content(
        "Este correo contiene HTML. Si no puedes verlo, abre el PDF adjunto.",
        subtype="plain",
        charset="utf-8",
    )
    msg.add_alternative(cuerpo_html, subtype="html")

    with pdf_path.open("rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename=nombre_pdf,
        )

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=30) as smtp:
        smtp.login(env["GMAIL_USER"], env["GMAIL_APP_PASSWORD"].replace(" ", ""))
        smtp.send_message(msg)


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("diaria", "semanal"):
        die("Uso: enviar_bitacora.py [diaria|semanal]")
    tipo = sys.argv[1]

    script_dir = Path(__file__).resolve().parent
    env = cargar_env(script_dir / ".env")

    reportes_dir = Path(env.get("REPORTES_DIR") or reportes_por_defecto(Path.home())).expanduser()
    log_path = Path(env.get("ULTIMOS_ENVIOS_LOG") or script_dir / ".enviados.log").expanduser()

    archivo = buscar_ultima_bitacora(reportes_dir, tipo)
    if archivo is None:
        log(f"No hay bitácora {tipo} en {reportes_dir}. Nada que enviar.")
        return

    if ya_enviado(log_path, archivo):
        log(f"{archivo.name} ya fue enviado. Nada que hacer.")
        return

    log(f"Enviando {archivo.name} …")
    html = archivo.read_text(encoding="utf-8")
    titulo, body = extraer_titulo_y_body(html)
    cuerpo_html = construir_correo_html(titulo, body, env)

    log("Generando PDF …")
    pdf_path = html_a_pdf(archivo)

    asunto_prefijo = "Bitácora diaria" if tipo == "diaria" else "Recap semanal"
    fecha_titulo = archivo.stem.split("-bitacora")[0].split("-semanal")[0]
    asunto = f"{asunto_prefijo} · TaxiCab · {fecha_titulo}"
    nombre_pdf = f"{archivo.stem}.pdf"

    try:
        enviar_correo(env, asunto, cuerpo_html, pdf_path, nombre_pdf)
    except Exception as e:
        die(f"Falló el envío: {type(e).__name__}: {e}")
    finally:
        try:
            pdf_path.unlink()
        except OSError:
            pass

    marcar_enviado(log_path, archivo)
    log(f"Enviado a {env['DESTINATARIO']}.")


if __name__ == "__main__":
    main()
