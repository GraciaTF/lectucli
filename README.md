# lectucli

Herramienta de línea de comandos para gestionar y organizar lecturas utilizadas en actividades de aula.

## Objetivo

Facilitar la organización, búsqueda, creación y gestión de lecturas para trabajar con ellas al comienzo de las clases.

## Tecnologías

- Python 3.12
- Typer
- uv


## Instalación

Necesitas [uv](https://docs.astral.sh/uv/).
Instala LectuCLI directamente desde GitHub:

```bash
uv tool install git+https://github.com/GraciaTF/lectucli.git@v1.0.0
```

Comprueba que está instalado:
```bash
lectucli --help
lectucli version
```

## Primeros pasos

### 1. Preparar la configuración

Descarga el fichero [`acciones.json`](https://raw.githubusercontent.com/GraciaTF/lectucli/v1.0.0/acciones.json) y guárdalo en la carpeta desde la que vas a trabajar.

Este fichero define las acciones disponibles, sus tipos, carpetas de origen y destino y filtros aplicables.

**Importante:** adapta las rutas de `origen`, `destino` y `categorias` a las carpetas de tu equipo antes de utilizar las acciones.

Por defecto, LectuCLI busca `acciones.json` en la carpeta actual. Si quieres utilizar otro fichero, puedes indicarlo mediante `--config`.

### 2. Comprobar la configuración

```bash
lectucli validar
```

Comprueba que el fichero JSON tiene una estructura válida. Si encuentra errores, muestra todos ellos.

### 3. Consultar las acciones disponibles

```bash
lectucli acciones
```

Muestra las acciones definidas en `acciones.json`, su tipo, descripción y si necesitan inteligencia artificial.

### 4. Consultar el contenido de una carpeta

```bash
lectucli listar
lectucli listar ~/lecturas/pendientes
```

El primer comando muestra la carpeta actual. El segundo muestra la carpeta indicada.

### 5. Ejecutar una acción

La sintaxis general es:

```bash
lectucli ejecutar NOMBRE_DE_LA_ACCION [CARPETA] [OPCIONES]
```

La carpeta es opcional. Si se indica, tiene prioridad sobre el origen definido en `acciones.json`.

**Opciones disponibles:**

| Opción | Función |
|---|---|
| `--simular` | Muestra qué se haría sin modificar archivos ni conectar con la IA. |
| `--si` | Ejecuta sin solicitar confirmación. |
| `--fichero` o `-f` | Selecciona un archivo concreto por su nombre. Se puede repetir. |
| `--nuevo-nombre` o `-n` | Indica el nuevo nombre para la acción `renombrar`. |

### 6. Ejemplos de ejecución

**Mover un archivo concreto:**

```bash
lectucli ejecutar mover-a-educacioninfantil --fichero lectura.pdf --simular
```

**Mover varios archivos concretos:**

```bash
lectucli ejecutar mover-a-educacioninfantil \
  -f lectura1.pdf \
  -f lectura2.docx \
  --simular
```

**Renombrar un archivo:**

```bash
lectucli ejecutar renombrar ~/lecturas/pendientes \
  -f lectura.pdf \
  -n "lectura-final" \
  --simular
```

**Eliminar archivos seleccionados:**

```bash
lectucli ejecutar borrar ~/lecturas/pendientes \
  -f antiguo.txt \
  --simular
```

Cuando hayas comprobado el resultado de una simulación, puedes repetir el comando sin `--simular` para realizar la operación.

**Importante:** las acciones destructivas solicitan confirmación antes de ejecutarse. La opción `--si` omite esa confirmación.

Las acciones de tipo `mover` y `copiar` utilizan el destino definido en `acciones.json`. Para cambiarlo, modifica el campo `destino` de la acción correspondiente.

### 7. Comprobar la conexión con la IA

```bash
lectucli comprobar-ia
```

Comprueba la conexión con el proveedor de IA del centro. Para utilizar las acciones que necesitan IA es necesario configurar las variables correspondientes en el fichero `.env`.


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
| `version` | Versión del esquema de configuración; debe ser `1`. |
| `acciones` | Lista de acciones definidas; no puede estar vacía. |
| `nombre` | Nombre único de la acción: minúsculas, números y guiones (patrón `^[a-z0-9]+(?:-[a-z0-9]+)*$`), sin guiones al principio ni al final. |
| `descripcion` | Explicación de lo que hace la acción; obligatoria y no vacía. |
| `tipo` | Operación que realizará: mover, copiar, renombrar, borrar, resumir, renombrar-ia o clasificar. Obligatorio; un tipo no admitido es un error de configuración. |
| `origen` | Carpeta de origen. Opcional si se proporciona al ejecutar la acción; si aparece, debe ser un texto no vacío. |
| `filtro` | Criterios para seleccionar los archivos; si aparece, debe ser un objeto (ver «Filtros disponibles»). |
| `destino` | Carpeta donde se copiarán o moverán los archivos. Obligatorio en mover y copiar. No aplica a renombrar-ia ni a clasificar (ahí los destinos los define `categorias`): ponerlo en esos tipos es un error. |
| `plantilla` | Plantilla para generar nombres nuevos al renombrar. Obligatoria en renombrar; no aplica a renombrar-ia ni a clasificar (el nombre lo propone la IA): ponerla en esos tipos es un error. |
| `categorias` | Solo en tipo clasificar (obligatorio ahí y no vacío, prohibido en el resto): mapa de categorías, con el identificador que debe responder la IA como clave (minúsculas, números y guiones) y la carpeta destino no vacía como valor. |
| `confirmar` | Booleano opcional (`true`/`false`) que solo se valida en `config.py`; **no controla la confirmación**. La CLI pide confirmación a todas las acciones destructivas, salvo con `--simular` o `--si`. |
| `instrucciones` | Solo en tipos con IA: texto no vacío que se añade al mensaje de sistema (opcional). Aparecer con valor en un tipo sin IA es un error. |
| `max_caracteres` | Solo en tipos con IA: tope de caracteres del documento enviado (entero entre 500 y 50000; por defecto 12000; `null` o ausente = defecto). Aparecer con valor en un tipo sin IA es un error. |


Filtros disponibles (si `filtro` aparece, debe ser un objeto con criterios válidos):
- extensiones: extensiones permitidas, en minúsculas y con punto (por ejemplo `.pdf`); la lista no puede estar vacía.
- patron: expresión regular válida para filtrar nombres (si no compila, es un error).
- mas_antiguo_que_dias: antigüedad mínima en días; entero mayor que cero.
- mayor_que_mb: tamaño mínimo en MB; número mayor que cero y finito (ni `NaN` ni `inf`).

Plantillas de renombrado (solo se admiten estos cuatro huecos; cualquier otro hueco o unas llaves sin cerrar son un error de configuración):
- {fecha:%Y-%m-%d}: fecha de modificación.
- {n:03}: contador con tres cifras.
- {ext}: extensión original.
- {nombre}: nombre original sin extensión.


## La columna IA de «lectucli acciones» ##

`uv run lectucli acciones` muestra las acciones con las columnas **Nombre**,
**Tipo**, **Descripción** y **IA**:

- `sí` cuando la acción necesita el proveedor de IA del centro (`resumir`,
  `renombrar-ia` y `clasificar`).
- `—` cuando no lo necesita (`mover`, `copiar`, `renombrar` y `borrar`).

El valor sale de la propiedad `necesita_ia` de la propia acción (creada con
`Accion.desde_config()`), nunca de deducirlo por el nombre o la descripción.


## Comprobar la IA: comprobar-ia ##

La orden `lectucli comprobar-ia` comprueba que lectucli puede hablar con el
servidor de inteligencia artificial del centro. Muestra el servidor, el modelo
y «Clave: definida» (**nunca muestra la clave**), hace una pregunta mínima al
modelo con `max_tokens=5` y, si todo va bien, muestra la respuesta, los tokens
de entrada y de salida y el tiempo empleado.

**La conexión real con el servidor del centro está pendiente de
configuración:** mientras no se indique la URL y la clave correctas en el
fichero `.env`, la orden muestra el error en rojo (`✘ ...`), recuerda en una
segunda línea que las acciones sin IA siguen funcionando y termina con el
código de salida 4, sin traza.

```bash
# comprueba la configuración y hace una pregunta mínima al modelo
uv run lectucli comprobar-ia
```

### Variables de configuración (CENTRO_IA_*)

Se leen del fichero `.env` de la carpeta de trabajo. El `.env` se carga **solo
cuando hace falta**: cuando se ejecuta una acción con IA **sin `--simular`**
o cuando se ejecuta `lectucli comprobar-ia`. Las acciones sin IA y las
simulaciones no leen las variables `CENTRO_IA_*` ni abren conexiones.
**No se versionan ni se comparten**: la clave no aparece en pantalla
ni en ningún mensaje de error.

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
| 4 | IA no disponible: faltan `CENTRO_IA_URL` o `CENTRO_IA_KEY` (o la URL no empieza por `http://` o `https://`), sin conexión o conexión rechazada, certificado no válido o ausente, tiempo de conexión o de respuesta agotado, HTTP 401 (clave rechazada), HTTP 429 o respuesta inesperada del servidor. |

Todos los problemas de la IA se convierten en `IANoDisponible`: se muestra el
error en rojo (`✘ ...`) y, en una segunda línea, el aviso
`Las acciones sin IA siguen funcionando: mira cuáles son con «lectucli acciones».`
La terminal sale con el código 4 **sin mostrar la traza del error**
(traceback). El resto de errores conserva su tratamiento: 1 al ejecutar, 2 de
uso incorrecto y 3 de configuración inválida.


## Arquitectura de la IA: ProveedorIA y ProveedorCentro ##

La capa de IA vive en `src/lectucli/ia.py` y se apoya en las excepciones de
`src/lectucli/errores.py`:

- **`ProveedorIA`** (clase abstracta): la interfaz común de cualquier
  proveedor. Expone `completar(sistema, usuario, max_tokens=1000)` y devuelve
  un `Respuesta` con `texto`, `tokens_entrada`, `tokens_salida` y `segundos`.
  Es lo único que conoce `AccionIA`: las acciones no saben con qué servidor
  hablan.
- **`ProveedorCentro`** (subclase): habla con el servidor del centro por
  httpx, con una API compatible con OpenAI (`POST {url}/chat/completions`),
  la clave en la cabecera `Authorization: Bearer ...`, tiempos de espera de
  **10 segundos para conectar y 120 segundos para la respuesta**, y el contexto
  TLS (el CA de `CENTRO_IA_CA` si existe, o las CA del sistema). Se usa como
  gestor de contexto (`with ProveedorCentro.desde_entorno() as proveedor`)
  para cerrar las conexiones con `cerrar()`.
- **`desde_entorno()`** es la fábrica que carga el `.env` y construye el
  proveedor con las variables `CENTRO_IA_*`.

**Creación perezosa del proveedor.** `lectucli ejecutar` no crea el
proveedor: pasa su fábrica (`ProveedorCentro.desde_entorno`, sin llamarla) al
motor, que solo la invoca cuando la acción elegida tiene `necesita_ia`, la
ejecución **no** es una simulación y hay ficheros seleccionados. Por eso:

- una acción sin IA funciona sin clave y sin conexión;
- una acción con IA con `--simular` también funciona sin clave ni conexión, y
  solo calcula e informa del presupuesto de caracteres que se enviaría;
- `.env` y las variables `CENTRO_IA_*` solo se leen en una ejecución real de
  una acción con IA.

Cualquier fallo (falta de configuración, red, certificado, tiempos agotados o
error HTTP) se convierte en `IANoDisponible`, con el tratamiento descrito
más arriba en «Códigos de salida»: mensaje en rojo, segunda línea con el
aviso y salida con el código 4.


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

Con `--simular` **no se llama al proveedor de IA ni hace falta `.env`**: el
proveedor no llega a crearse, así que no se leen las variables `CENTRO_IA_*`
ni se abre ninguna conexión. En simulación (y también en una ejecución real),
`leer_texto()` **carga el fichero completo en memoria** y devuelve como mucho
`max_caracteres` (recortando al final, en todos los formatos: .txt, .md,
.pdf, .docx y .odt). Ese texto es el que se usa para calcular el presupuesto
que se muestra en «Detalle» (`presupuesto: N caracteres`) y, en una
ejecución real, el que se envía al modelo (`N caracteres enviados`). La
columna «Detalle» de la tabla de resultados
aparece únicamente cuando algún resultado lleva información: en las acciones
sin IA no se muestra.

```bash
# ver qué se resumiría y cuántos caracteres se enviarían, sin tocar nada
uv run lectucli ejecutar resumir CARPETA --simular

# resumir de verdad (necesita CENTRO_IA_URL y CENTRO_IA_KEY en .env)
uv run lectucli ejecutar resumir CARPETA
```

Si falta la configuración de la IA, o el servidor falla (HTTP 401, 429,
sin conexión…), lectucli convierte el fallo en `IANoDisponible`: muestra el
error en rojo (`✘ ...`), añade en una segunda línea
`Las acciones sin IA siguen funcionando: mira cuáles son con «lectucli acciones».`
y sale con el código 4 sin traza. En cambio, con `--simular` ningún fallo de
IA puede aparecer: no se consulta `.env` ni se toca la red.


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
  minúsculas), el fichero **se mueve a `sin-clasificar`** y en «Detalle»
  quedan la respuesta y las categorías válidas. Si el JSON define una
  categoría `sin-clasificar` se usa su carpeta; si no, se crea una
  subcarpeta `sin-clasificar` junto al propio fichero. Nunca se manda a
  ciegas a «otros» y, como en el resto de movimientos, si el nombre ya
  está ocupado entra con el sufijo `(1)` en lugar de sobrescribir.
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