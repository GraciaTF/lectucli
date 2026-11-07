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


## Prompts para validar
Carga la skill @acciones-json y lee el fichero @acciones.json.

Quiero validar acciones.json ANTES de ejecutar nada.

Propón una implementación para lectucli que incluya:

- src/lectucli/errores.py con las clases LectucliError, ConfigError y AccionNoValida.
- src/lectucli/config.py con una función cargar(ruta) -> list[dict].
- La orden «lectucli validar» en src/lectucli/cli.py.

La validación debe comprobar el fichero completo antes de permitir ejecutar acciones. Los errores deben identificar la acción, el campo y el motivo cuando corresponda.

Ten en cuenta nuestro esquema: nombre, descripcion, tipo, origen opcional, filtro opcional, destino, plantilla y confirmar. Comprueba también nombres duplicados, tipos no admitidos, campos obligatorios según el tipo, filtros y expresiones regulares inválidas.

El proyecto debe funcionar en Linux, Windows y macOS.

No modifiques ningún fichero ni ejecutes cambios todavía. Primero dime qué ficheros crearías o modificarías, qué clases y funciones implementarías y qué casos de error detectarías. 

### Solicito las siguientes modificaciones
El plan está bastante bien, pero quiero revisar algunos puntos antes de aprobarlo:

1. La validación no debe limitarse al comando «lectucli validar». También debe realizarse antes de ejecutar cualquier acción, para impedir que se toque el disco si acciones.json contiene errores.

2. Para las acciones de tipo «borrar», el comportamiento debe ser el siguiente:
   - Por defecto, siempre se pide confirmación antes de borrar.
   - Si el usuario añade --si al comando de borrado, se elimina directamente sin pedir confirmación.
   - No queremos que el campo «confirmar» sea obligatorio en acciones.json para conseguir este comportamiento. La confirmación es la opción predeterminada.
   - Refleja esta regla en el diseño y explica cómo se implementaría.

3. Para los nombres de las acciones, quiero permitir también números, además de letras minúsculas y guiones.

4. Explica cómo combinarías la detección de varios errores con la clase AccionNoValida: queremos poder mostrar todos los errores encontrados, no solamente el primero.

5. No añadas restricciones que no estén justificadas por nuestro esquema. Si alguna regla, como los valores mínimos de los filtros, necesita una decisión, indícalo en lugar de inventarla.

Actualiza el plan, pero no modifiques ningún fichero ni escribas código todavía. 

//Añado una puntualización y respondo a una pregunta suya:
Vamos a cerrar las decisiones pendientes:

1. El campo confirmar será opcional y, si aparece, deberá ser booleano. Tanto si vale true como si vale false, la acción borrar seguirá pidiendo confirmación. La única forma de omitirla será añadir --si expresamente al comando de ejecución.

2. mas_antiguo_que_dias debe ser un número entero mayor que cero.

3. mayor_que_mb debe ser un número mayor que cero.

4. La lista extensiones debe contener al menos una extensión válida.

Actualiza el plan con estas decisiones. No modifiques ficheros ni escribas código todavía. 

// El resultado es el que pedimos a Build que construya.
// Luego le pedimos:
Carga la skill @acciones-json y revisa los tres archivos implementados: errores.py, config.py y cli.py.

La estructura general está aprobada, pero antes de terminar necesito estos ajustes:

1. Corrige los textos en español que tengan palabras pegadas o errores de espaciado en los mensajes, comentarios y ayudas.

2. Revisa la validación de plantillas:
   - Admitir exactamente `{nombre}`, `{ext}`, `{n:03}` y `{fecha:%Y-%m-%d}`.
   - Rechazar formatos desconocidos o incompletos.
   - No aceptar formatos de fecha o contador inventados.

3. En `mayor_que_mb`, rechaza valores no finitos como NaN e infinito, además de los valores menores o iguales a cero. Mantén el rechazo de booleanos.

4. Comprueba que los errores de estructura y de cada acción identifican claramente el campo y, cuando sea posible, la acción afectada.

5. No cambies el comportamiento de `listar`, `version` ni otras partes que no estén relacionadas con esta tarea.

6. No añadas dependencias. No modifiques acciones.json, README.md ni pyproject.toml.

7. Ejecuta pruebas de:
   - Validación correcta.
   - JSON mal formado, mostrando línea y columna.
   - Varias acciones inválidas, mostrando todos los errores.
   - Código de salida 3 para errores de configuración.
   - Ausencia de traceback.
   - Mensajes en rojo y mensaje de éxito en verde.

Puedes utilizar archivos de prueba temporales, pero no modifiques acciones.json.

Antes de modificar, explícame brevemente qué vas a corregir. Después implementa únicamente los cambios necesarios en los tres archivos acordados y resume las pruebas realizadas. 

## Prompts relacionados con el motor
### Correcciones al plan inicial
//En el primer plan, me propone que accion sea una dataclass y mover, copiar, etc sean funciones. Por tanto, le pido que rehaga el plan conservando la arquitectura indicada en el doc del profesor:

La propuesta tiene ideas interesantes, pero quiero que respetes la arquitectura indicada en el ejercicio.

Necesito que revises el diseño teniendo en cuenta estos requisitos:

1. `Accion` debe ser una clase base abstracta, no una dataclass.
2. Debe tener los métodos `ejecutar(ficheros, simular)` y `aplicar(fichero, n, simular)`, siendo `aplicar` abstracto.
3. Deben existir las subclases `Mover`, `Copiar`, `Renombrar` y `Borrar`, que implementarán su propio método `aplicar`.
4. La fábrica debe ser `Accion.desde_config(dict)` y utilizar un registro de subclases, sin `if/elif` por tipo.
5. `Resultado` debe contener `origen`, `destino` y `estado`, con los tres estados previstos: `hecho`, `simulado` y `saltado`.
6. Debe existir una clase `Motor(acciones)` con los métodos `seleccionar(carpeta, filtro)` y `ejecutar(nombre, carpeta, simular)`.
7. No quiero modificar `cli.py` ni `errores.py` en este paso. El alcance es crear `acciones.py` y `motor.py`.

Vuelve a explicarme cómo organizarías estas dos clases y cómo garantizarías que `--simular` no modifica absolutamente nada del disco. No escribas código todavía. 

//Tras esto, su propuesta se ajusta a lo solicitado y me pide que confirme 4 aspectos. Confirmo y paso a Build

## Prompts relacionados con segunda acción
//Quiero que mi segunda acción sea mover las lecturas para organizarlas según los ciclos que imparto: Integración Social, PROMIG, Educación Infantil, Animación Sociocultural y turística y Dependencia, he empezado por crear el movimiento a integración social:


Quiero añadir la acción: mover-a-integracionsocial "mueve documentos de la carpeta pendientes a la carpeta Integración Social"

1. Carga la skill acciones-json.
2. Propón primero la entrada JSON y espera mi visto bueno.
3. Si el tipo ya existe, solo edita acciones.json. Si no, añade la clase en src/lectucli/acciones.py siguiendo el patrón de las demás.
4. Termina ejecutando `uv run lectucli validar` y dime qué orden con --simular debo probar yo.

Estado actual del repo:


//Hago una corrección:
Corrige las rutas:
- origen: ~/lecturas/pendientes
- destino: ~/lecturas/Integración Social

Añade el filtro de extensiones .pdf, .docx, .odt y .txt.

Mantén el tipo mover. Muéstrame el JSON actualizado y espera mi aprobación. No modifiques todavía ningún archivo. 

//funciona

## Prompts relacionados con el trabajo del subagente
//He pedido al subagente la revisión de src/lectucli/motor.py y ha detectado algunos errores que no se estaban gestionando como deberían, además de que carpeta "" podría interpretarse como actual path, por lo que le pido que lo arregle:

Usa el informe del subagente `revisor` sobre `src/lectucli/motor.py` y realiza únicamente estas dos correcciones:

**1. Protección frente a carpetas vacías**
- Evita que `carpeta = ""` se interprete como el directorio actual (`Path(".")`).
- Si la carpeta recibida está vacía o no es válida, lanza un error controlado de `LectucliError`.
- Comprueba que la protección también impide ejecutar acciones destructivas sobre el directorio actual por accidente.

**2. Gestión de errores de permisos y operaciones de archivos**
- Captura los `PermissionError` y `OSError` relevantes en las operaciones identificadas por el revisor:
  - `iterdir()` en `seleccionar()`.
  - `origen.is_dir()` en `ejecutar()`.
  - `accion.ejecutar(...)` en `ejecutar()`.
- Convierte esos errores en excepciones `LectucliError`, conservando mensajes claros en español y sin mostrar trazas de Python al usuario.

**Restricciones:**
- Modifica exclusivamente `src/lectucli/motor.py`.
- Mantén la arquitectura actual y el patrón de diseño existente.
- No cambies la CLI, el JSON de configuración ni otros archivos.
- No introduzcas funcionalidades nuevas ni aproveches para hacer otras mejoras.
- Respeta las normas de `AGENTS.md` y la skill del proyecto.
- No ocultes errores inesperados con capturas demasiado generales.

**Al terminar:**
1. Indica exactamente qué has cambiado y por qué.
2. Ejecuta las pruebas existentes relacionadas con el motor.
3. Comprueba que una carpeta vacía no provoca operaciones sobre el directorio actual.
4. Confirma que no has modificado ningún otro archivo.