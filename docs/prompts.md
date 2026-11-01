# Prompts clave del proyecto

## Adaptación de la plantilla
Adapta esta plantilla a nuestro proyecto lectucli.
# tareas · CLI de tareas con ficheros (proyecto de 1º DAM)
## Stack y órdenes
- Python 3.12 + Typer + Rich, gestionado con uv (src layout, paquete src/tareas).
- Ejecutar: `uv run tareas --help` · Validar config: `uv run tareas validar` · Pruebas (semana 4): `uv run pytest`.
## Normas
- Mensajes y comentarios en español; código claro antes que listo.
- pathlib siempre, encoding="utf-8", nada de os.system ni shell=True: tiene que funcionar en Linux, Windows y macOS.
- Nunca ejecutes acciones sobre carpetas reales: solo en ~/pruebas-tareas y con --simular.
- No toques .env ni escribas claves en ningún fichero. No hagas git push ni commits: los hace el alumno.
- Antes de cambiar un fichero, explica en 2-3 líneas qué vas a hacer.

Cambios necesarios:
- Sustituye tareas por lectucli.
- El paquete es src/lectucli.
- Usamos Python 3.12, Typer y uv.
- Todavía no existe cli.py, así que no afirmes que los comandos funcionan.
- pytest no está instalado todavía.
- Conserva las normas de seguridad y las buenas prácticas de la plantilla.

Primero muéstrame el contenido adaptado. No crees todavía el archivo. 


//Luego le pedí que lo guardase como AGENTS.md

## Primera orden: listar


**Herramienta:** OpenCode

**Modelo utilizado:** Nemotron

**Fecha:** 2026-10-26

### Prompt del plan (agente plan)

Lee @README.md y @pyproject.toml. Quiero src/lectucli/cli.py (app de Typer llamada app) y src/lectucli/__main__.py con dos órdenes: version y listar [CARPETA].
No escribas código todavía: dime qué ficheros crearías, qué funciones tendría cada uno y cómo tratarías la carpeta inexistente, la vacía, los nombres con corchetes y los ficheros que no se pueden leer.

Criterio de aceptación:
- uv run lectucli sin argumentos muestra la ayuda, en español y sin autocompletado.
- version imprime «lectucli 0.1.0» leyendo __version__ del paquete.
- listar (por defecto la carpeta actual, acepta ~) pinta una tabla Rich: Nombre, Tipo (extensión o «carpeta»), Tamaño legible, Modificado (AAAA-MM-DD HH:MM). Carpetas primero, luego alfabético sin distinguir mayúsculas.
- Carpeta inexistente o que no es carpeta: mensaje en stderr, sin traza, código 1. Carpeta vacía: aviso en vez de tabla vacía.
- pathlib, sin os.system ni subprocess, sin dependencias nuevas. uv run python -m lectucli también funciona. 

### Qué corregí del plan
Dos cambios al plan:

1. No añadas órdenes, pruebas ni dependencias que no he pedido. En esta implementación solo quiero `src/lectucli/cli.py` y `src/lectucli/__main__.py`. Typer y Rich ya están disponibles.
2. Si un fichero da error al consultar su tamaño o fecha de modificación (por ejemplo, por falta de permisos o porque es un enlace roto), sáltalo sin interrumpir la tabla. Escapa los nombres con `rich.markup.escape` para que los corchetes se muestren correctamente.

Mantén el resto de criterios de aceptación del prompt original. Repíteme el plan corregido en 5 líneas, sin escribir código ni modificar archivos. 

### Diffs que rechacé o deshice (/undo) y por qué
//No he rechazado o deshecho diffs mediante /undo. Las correcciones las he hecho solicitando cambios concretos al agente.

### ¿Funcionaba a la primera?
//No, no del todo, le pedí las siguientes modificaciones:
He detectado dos problemas al probar `listar`. Corrígelos en `src/lectucli/cli.py`:

1. El argumento `CARPETA` está definido como opción (`--carpeta`), pero el criterio de aceptación pide un argumento posicional opcional: `listar [CARPETA]`. Quiero poder ejecutar `uv run lectucli listar ~/pruebas-lectucli` sin escribir `--carpeta`.
2. La ordenación está colocando los archivos antes que las carpetas. Corrígela para que aparezcan primero las carpetas y después los archivos, ordenados alfabéticamente sin distinguir mayúsculas.

No modifiques ningún otro archivo, no añadas dependencias ni hagas commits. Cuando termines, explícame brevemente qué has cambiado y ejecuta `uv run lectucli listar --help` para que podamos comprobar la definición del argumento. No continúes con más pruebas. 

### Qué fallo le expliqué
//Detecté que dos cosas no funcionaban exactamente como debían, así que le pedí lo siguiente:

Modifica únicamente `src/lectucli/cli.py` para ajustar la implementación al modelo del profesor del apartado 5.6.

Quiero estos dos cambios:

1. **Tipo del argumento `carpeta`:** utiliza `pathlib.Path` directamente como tipo del argumento de Typer, en lugar de `str`. Mantén el argumento posicional opcional, con `Path(".")` como valor predeterminado, y conserva `expanduser()` para admitir rutas que empiezan por `~`.

2. **Salida de errores:** crea una consola independiente con `Console(stderr=True)` y úsala para mostrar los mensajes de error de `listar`, en lugar de `typer.echo(..., err=True)`.

Mantén todo lo demás exactamente igual: órdenes, mensajes, códigos de salida, tabla, ordenación, tratamiento de errores y dependencias.

No modifiques `__main__.py`, no añadas funcionalidades ni hagas commits.

Cuando termines, muéstrame los cambios realizados y comprueba que `uv run lectucli listar --help` sigue mostrando `carpeta` como argumento posicional opcional. 

### Qué aprendí
Aprendí a distinguir entre el modo Plan y el modo Build de OpenCode, a revisar las solicitudes de permisos antes de aceptarlas y a comprobar los comandos para ver si respondían según los criterios de aceptación. También aprendí a leer y entender un archivo Python (un lenguaje que todavía no conozco demasiado) y a revisar el código generado por el agente en lugar de aceptarlo sin más.