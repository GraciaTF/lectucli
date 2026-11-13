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
9. **Códigos de salida:** 0 bien · 1 fallo al ejecutar · 2 uso incorrecto · 3 configuración inválida · 4 IA no disponible.
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

Con `--nuevo-nombre` (o `-n`) se indica el nombre que aplicará la acción
`renombrar`: **sustituye** la plantilla del JSON, no se suma a ella. En esa
acción son obligatorios `--nuevo-nombre` y `--fichero` con **un único
archivo**; si falta alguno, lectucli avisa y no renombra nada. Si el nombre
nuevo no lleva extensión se conserva la original; si lleva otra, se
respeta. Como en el resto, nunca se sobrescribe: si el nombre ya existe se
añaden los sufijos `(1)`, `(2)`…

```bash
# renombrar conservando la extensión (con --simular no se toca nada)
lectucli ejecutar renombrar CARPETA -f "lectión año nº3.txt" -n "lectura final" --simular
```


## Esquema de acciones.json ##

acciones.json contiene la configuración de las acciones que puede ejecutar lectucli.

| Campo | Descripción |
|---|---|
| `version` | Versión del esquema de configuración. |
| `acciones` | Lista de acciones definidas. |
| `nombre` | Nombre único de la acción. |
| `descripcion` | Explicación de lo que hace la acción. |
| `tipo` | Operación que realizará: mover, copiar, renombrar, borrar, resumir, renombrar-ia o clasificar. |
| `origen` | Carpeta de origen. Opcional si se proporciona al ejecutar la acción. |
| `filtro` | Criterios para seleccionar los archivos. |
| `destino` | Carpeta donde se copiarán o moverán los archivos. No aplica a renombrar-ia ni a clasificar (ahí los destinos los define `categorias`). |
| `plantilla` | Plantilla para generar nombres nuevos al renombrar. No aplica a renombrar-ia ni a clasificar (el nombre lo propone la IA). |
| `categorias` | Solo en tipo clasificar (obligatorio ahí, prohibido en el resto): mapa de categorías, con el identificador que debe responder la IA como clave y la carpeta destino como valor. |
| `confirmar` | Indica si se requiere confirmación antes de borrar. |
| `instrucciones` | Solo en tipos con IA: texto que se añade al mensaje de sistema (opcional). |
| `max_caracteres` | Solo en tipos con IA: tope de caracteres del documento enviado (entre 500 y 50000; por defecto 12000). |


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


## Comprobar la IA: comprobar-ia ##

La orden `lectucli comprobar-ia` comprueba que lectucli puede hablar con el
servidor de inteligencia artificial del centro. Muestra el servidor, el modelo
y «Clave: definida» (**nunca muestra la clave**), hace una pregunta mínima al
modelo con `max_tokens=5` y, si todo va bien, muestra la respuesta, los tokens
de entrada y de salida y el tiempo empleado.

**La conexión real con el servidor del centro está pendiente de
configuración:** mientras no se indique la URL y la clave correctas en el
fichero `.env`, la orden terminará con un mensaje `✘ ...` y el código de
salida 4.

```bash
# comprueba la configuración y hace una pregunta mínima al modelo
uv run lectucli comprobar-ia
```

### Variables de configuración (CENTRO_IA_*)

Se leen del fichero `.env` de la carpeta de trabajo (se carga automáticamente
antes de cada petición). **No se versionan ni se comparten**: la clave no
aparece en pantalla ni en ningún mensaje de error.

| Variable | Obligatoria | Descripción |
|---|---|---|
| `CENTRO_IA_URL` | Sí | URL base del servidor compatible con OpenAI; sin `/chat/completions`, que se añade solo. Debe empezar por `http://` o `https://`. |
| `CENTRO_IA_KEY` | Sí | Clave de acceso. Se envía en la cabecera `Authorization: Bearer ...` y jamás se muestra. |
| `CENTRO_IA_MODELO` | No | Nombre del modelo que se usará (`model` de la petición). Si no se indica, o está vacío, se usa `qwen3.8-flash-next` (el `MODELO_POR_DEFECTO` del proyecto). |
| `CENTRO_IA_CA` | No | Ruta a un fichero `.crt`/`.pem` con el certificado de CA propio del centro. Si no está, se confía en las CA del sistema (certifi). Si la ruta no existe o el fichero no es un certificado válido, lectucli avisa y sale con el código 4. |

Ejemplo mínimo de `.env` (sustituye los valores por los del centro; no los
guardes en el repositorio):

```
CENTRO_IA_URL=
CENTRO_IA_KEY=
# opcional: si se omite se usa qwen3.8-flash-next
CENTRO_IA_MODELO=
# opcional: certificado .crt/.pem del centro
CENTRO_IA_CA=
```


### Códigos de salida

| Código | Significado |
|---|---|
| 0 | Todo ha ido bien. |
| 1 | Fallo al ejecutar una acción. |
| 2 | Uso incorrecto de la orden (faltan argumentos). |
| 3 | Configuración inválida (`acciones.json` no cumple el esquema). |
| 4 | IA no disponible: falta configuración, sin conexión o conexión rechazada, certificado no válido o ausente, tiempo de conexión o de respuesta agotado, HTTP 401, HTTP 429 o respuesta inesperada del servidor. |

Todos los problemas de la IA se convierten en `IANoDisponible`: se muestra un
único mensaje en rojo (`✘ ...`) y la terminal sale con el código 4 **sin
mostrar la traza del error** (traceback).


## La acción resumir (IA) ##

La acción de tipo `resumir` (en acciones.json se llama `resumir`) resume
documentos con la IA del centro y guarda el resultado en un fichero
`nombre.resumen.md`, junto al original o en la carpeta `destino` si la
acción lo indica. Nunca sobrescribe: si el nombre ya existiera se añaden
los sufijos `(1)`, `(2)`…

- **Ficheros que lee:** `.txt`, `.md` (UTF-8) y `.pdf` (con pypdf).
- **Ficheros ilegibles** (PDF sin texto, codificación rara, sin
  extensión admitida): quedan como `SALTADO` con el motivo en la columna
  «Detalle» y la ejecución **continúa** con los demás.
- **Campos opcionales del JSON:** `instrucciones` (texto que se **añade**
  al mensaje de sistema fijo `SISTEMA_RESUMIR`, nunca lo sustituye) y
  `max_caracteres` (entre 500 y 50000, por defecto 12000).
- **Seguridad:** el documento siempre va entre `<documento>` y
  `</documento>` y se trata como contenido para resumir, nunca como
  instrucciones para el modelo; el mensaje de sistema con esa regla se
  envía siempre igual.

### Simulación sin IA

Con `--simular` **no se llama al proveedor de IA ni hace falta `.env`**:
lectucli solo lee cada fichero y muestra en «Detalle» el presupuesto de
caracteres que se enviaría (`presupuesto: N caracteres`).

```bash
# ver qué se resumiría y cuántos caracteres se enviarían, sin tocar nada
uv run lectucli ejecutar resumir CARPETA --simular

# resumir de verdad (necesita CENTRO_IA_URL y CENTRO_IA_KEY en .env)
uv run lectucli ejecutar resumir CARPETA
```

Si falta la configuración de la IA, o el servidor falla (HTTP 401, 429,
sin conexión…), lectucli muestra un único mensaje `✘ ...` y sale con el
código 4 sin traza.


## La acción nombrar-escaneos (IA) ##

La acción de tipo `renombrar-ia` (en acciones.json se llama
`nombrar-escaneos`) propone con la IA un nombre claro para cada escaneo
PDF y lo renombra **en su propia carpeta** (sin `destino`: no mueve
nada). Es destructiva, así que **pide confirmación antes** salvo con
`--simular` o `--si`.

- **Solo PDF:** el filtro del JSON limita a `.pdf` con el patrón
  `(?i)^(escaneo|scan|documento|descarga)`, y el código vuelve a
  comprobarlo: cualquier otro formato sale como `SALTADO` con el motivo
  «solo se renombran ficheros PDF» aunque alguien ampliara el filtro.
- **Procesa la carpeta entera** que cumpla el filtro (no exige
  `--fichero`; si se indica, la selección se restringe a ese fichero).
- **Nombre seguro (`a_nombre_seguro`), en este orden:** solo la primera
  línea; se quita la extensión que añada el modelo; tildes y eñes fuera
  (NFD); minúsculas; todo lo que no sea `a-z`, `0-9` ni `-` pasa a
  guion; sin guiones repetidos ni en los extremos; tope de 60
  caracteres; si queda vacío, el fichero queda `SALTADO` sin tocarse.
  Después se le añade **la extensión original** del fichero.
- **Nunca sobrescribe:** si el nombre libre ya existe se añaden los
  sufijos `(1)`, `(2)`…; y si la IA propone exactamente el nombre que
  ya tiene el fichero, sale `SALTADO` con «el nombre ya es correcto»
  **sin** añadirle `(1)`.
- **Ficheros ilegibles** (PDF sin texto, cifrado, vacío): `SALTADO` con
  el motivo y la ejecución continúa con los demás.
- **Seguridad:** mensaje de sistema fijo `SISTEMA_NOMBRAR` con la
  cláusula anti-inyección; el `instrucciones` del JSON se **añade**,
  nunca lo sustituye; el documento va entre `<documento>` y
  `</documento>`.

```bash
# ver qué se haría, sin tocar nada y sin .env
uv run lectucli ejecutar nombrar-escaneos CARPETA --simular

# renombrar de verdad (necesita .env y confirmación, o bien --si)
uv run lectucli ejecutar nombrar-escaneos CARPETA --si
```


## La acción clasificar-lecturas (IA) ##

La acción de tipo `clasificar` (en acciones.json se llama
`clasificar-lecturas`) pide a la IA una categoría para cada lectura y
**la mueve físicamente** a la carpeta de esa categoría. Es destructiva:
pide confirmación antes salvo con `--simular` o `--si`.

- **Categorías en `categorias` (mapa id → carpeta):** el JSON trae
  `educacioninfantil`, `integracionsocial` y `otros`, con los mismos
  destinos que las acciones `mover-a-*`. La IA debe responder **solo**
  el identificador; las carpetas las crea la acción solo en ejecución
  real (con `--simular` no se crea ninguna).
- **Respuesta inválida:** si la IA responde algo que no es un
  identificador exacto del mapa (tras quitar comillas y pasar a
  minúsculas), el fichero **no se mueve**: sale `SALTADO` con la
  respuesta y las categorías válidas en «Detalle». Nunca se manda a
  ciegas a «otros».
- **Ya está en su categoría:** `SALTADO` con «ya está en su categoría»
  y no se mueve nada.
- **Ficheros que lee:** `.pdf`, `.txt`, `.md` (UTF-8), `.docx` (con
  python-docx) y `.odt` (con odfpy). Los ilegibles (docx corrupto, sin
  texto…) quedan `SALTADO` con el motivo y la ejecución continúa.
- **Seguridad:** mensaje de sistema fijo `SISTEMA_CLASIFICAR` con la
  cláusula anti-inyección, al que se **añaden** las categorías y el
  `instrucciones` del JSON; el documento va entre `<documento>` y
  `</documento>`.

```bash
# ver qué se enviaría y qué categorías hay, sin tocar nada y sin .env
uv run lectucli ejecutar clasificar-lecturas CARPETA --simular

# clasificar de verdad (necesita .env y confirmación, o bien --si)
uv run lectucli ejecutar clasificar-lecturas CARPETA --si
```

En ambos casos, con `--simular` **no se llama al proveedor de IA ni hace
falta `.env`**: solo se muestra en «Detalle» el presupuesto de
caracteres que se enviaría.