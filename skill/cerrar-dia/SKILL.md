---
name: cerrar-dia
description: Cierra el día en TaxiCab. Úsalo cuando el usuario diga "cerrar el día", "cerramos día", "cierra el día" o "genera la bitácora". Escribe el reporte del día en HTML, sin lenguaje técnico, para que el envío automático lo mande al día siguiente.
---

# Cerrar el día

Genera la bitácora de HOY (no de mañana) de lo que hizo **esta persona** y la deja
donde la lee el envío automático. Cada persona manda su propio reporte desde su equipo.

RUTA_BITACORA: (escribe aquí la carpeta donde clonaste el repo bitacora-taxicab)

"La carpeta de la bitácora" es esa ruta: ahí están `.env`, `plantilla-bitacora.html` y
`enviar_bitacora.py`.

## 1. Qué contar

Solo el trabajo de hoy de quien lo pide: pregúntale si dudas, y apóyate en
`git log --since=midnight --author="$(git config user.name)"` (en el proyecto donde trabaja, no en la carpeta de la bitácora), en los PR que abrió
y en lo que hizo en esta sesión. Si no hizo nada que un administrativo pueda
entender, dilo en el TL;DR en vez de inventar tarjetas.

## 2. Dónde se guarda

`<REPORTES_DIR>/YYYY-MM-DD-bitacora.html`, con la fecha de hoy. `REPORTES_DIR` sale de
el `.env` de la carpeta de la bitácora; si está vacío, `Documents/TaxiCab-Notas/Reportes` dentro de la
carpeta de usuario (en Windows, `%USERPROFILE%\Documents\TaxiCab-Notas\Reportes`).
En Mac, si la persona instaló el envío en `~/Library/Application Support/TaxiCab-Bitacora/`,
guarda el mismo archivo también en su carpeta `Reportes/`. Si el `.env` del envío no
existe todavía, avísale que falta instalarlo (ver el `README.md` de la carpeta de la bitácora).

Parte de `plantilla-bitacora.html` de la carpeta de la bitácora: copia su estructura completa
(estilos, tipografías, paleta, chips). Cambia solo el `<title>`, el `<h1>` con la
fecha, el eyebrow "Bitácora diaria · Semana N", el TL;DR y las tarjetas.

## 3. Regla crítica de lenguaje

El destinatario no sabe de programación. **Prohibido** mencionar nombres de archivos,
`commit`, `merge`, `PR`, Firebase, colecciones, providers, widgets, ramas ni
comandos. Usa: "la pantalla de choferes", "se guardó el registro", "se publicó al
sitio", "los administradores ven…". Tampoco menciones sistemas operativos ni
dispositivos de prueba.

## 4. Cada tarjeta lleva

- `<h3>` con el cambio en lenguaje llano.
- Chip de estado: `Terminado · falta publicar` / `Publicado a producción` /
  `Corregido · falta publicar` / `Listo para usarse`.
- `<dl class="facts">` con **Quién lo ve** (Administrador, Super Admin, Central,
  Programador, Encargado, Chofer), **Dónde** (ruta clara, p. ej. "Panel Admin → Uso
  de Unidades") y **Estado**.
- `<div class="what">` con **Qué se hizo** y **Por qué importaba**.
- Opcional `<p class="note">` para aclaraciones.

## 5. Después

- Si está disponible la herramienta Artifact, publica el HTML como Artifact (icono
  `report`) y dale el link a la persona.
- Recuerda que el correo sale al día siguiente a la hora programada y que el equipo
  debe estar encendido (en Windows, la tarea corre al encender si se la perdió).
- Si el día cerrado es viernes, ofrece el recap semanal `YYYY-MM-DD-semanal.html`
  (lunes a viernes). El lunes sale el semanal.
- Si no llegó un correo, revisa `.enviados.log` junto al script y corre
  `python3 enviar_bitacora.py diaria` (Windows: `py enviar_bitacora.py diaria`) a
  mano para ver el error.
