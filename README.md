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


## Seleccionar ficheros con --fichero ##

La opción `--fichero` (o `-f`) de `lectucli ejecutar` restringe la acción a
los ficheros indicados **por su nombre**, sin tocar el resto de la carpeta.
Se puede repetir para seleccionar varios ficheros a la vez. El filtro del
JSON sigue aplicándose; en las acciones de tipo `borrar`, sin ningún
`--fichero` no se selecciona nada (no se borra nada).

```bash
# borrar solo estos dos ficheros, con confirmación previa
lectucli ejecutar borrar ~/lecturas/pendientes -f informe.txt -f notas.txt

# ver qué se haría sin tocar el disco
lectucli ejecutar borrar ~/lecturas/pendientes -f informe.txt --simular
```


## Esquema de acciones.json ##

acciones.json contiene la configuración de las acciones que puede ejecutar lectucli.

| Campo | Descripción |
|---|---|
| `version` | Versión del esquema de configuración. |
| `acciones` | Lista de acciones definidas. |
| `nombre` | Nombre único de la acción. |
| `descripcion` | Explicación de lo que hace la acción. |
| `tipo` | Operación que realizará: mover, copiar, renombrar o borrar. |
| `origen` | Carpeta de origen. Opcional si se proporciona al ejecutar la acción. |
| `filtro` | Criterios para seleccionar los archivos. |
| `destino` | Carpeta donde se copiarán o moverán los archivos. |
| `plantilla` | Plantilla para generar nombres nuevos al renombrar. |
| `confirmar` | Indica si se requiere confirmación antes de borrar. |


Filtros disponibles:
- extensiones: extensiones permitidas.
- patron: expresión regular para filtrar nombres.
- mas_antiguo_que_dias: antigüedad mínima en días.
- mayor_que_mb: tamaño mínimo en MB.

Plantillas de renombrado:
- {fecha:%Y-%m-%d}: fecha de modificación.
- {n:03}: contador con tres cifras.
- {ext}: extensión original.
- {nombre}: nombre original sin extensión.