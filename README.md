# lectucli

Herramienta de línea de comandos para gestionar y organizar lecturas utilizadas en actividades de aula.

## Objetivo

Facilitar la organización, búsqueda, creación y gestión de lecturas para trabajar con ellas al comienzo de las clases.

## Tecnologías

- Python 3.12
- Typer
- uv

## Spec (versión 0 · 26/10/2026)

1. **Problema:** cada semana pierdo tiempo en encontrar las lecturas adecuadas para mis clases de ciclos formativos.
2. **Para quién:** para mí y para profesores que quieran usar lecturas breves en sus clases para fomentar la lectura.
3. **Cómo se usa:** `lectucli ORDEN [CARPETA] [opciones]` desde cualquier terminal.
4. **Órdenes de la semana 1:** `lectucli --help`, `lectucli version`, `lectucli listar [CARPETA]`.
5. **Órdenes previstas:** `lectucli acciones`, `lectucli validar`, `lectucli ejecutar NOMBRE --simular`.
6. **Mis 3 acciones (borrador):** buscar, filtrar, organizar.
7. **Nunca hará:** borrar sin preguntar ni tocar ficheros fuera de la carpeta que le indique.
8. **Plataformas:** Linux primero; también Windows y macOS.
9. **Códigos de salida:** 0 bien · 1 fallo al ejecutar · 2 uso incorrecto · 3 configuración inválida.
10. **Instalación:** `uv tool install --editable .` (lo completo en la semana 4).