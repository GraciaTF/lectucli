---
name: acciones-json
description: Reglas del fichero acciones.json de la CLI lectucli (campos, tipos, filtros, plantillas, validación y capa de IA). Úsala siempre que crees o cambies acciones, el proveedor de IA o el código que los lee (config.py, acciones.py, motor.py, ia.py, cli.py).
---

# Esquema de acciones.json

- Raíz: {"version": 1, "acciones": [...]}.
- Cada acción contiene:
  - nombre: identificador único (obligatorio; regex ^[a-z0-9]+(?:-[a-z0-9]+)*$: minúsculas, números y guiones, sin guiones al principio o al final; repetido → error).
  - descripcion: obligatoria y no vacía.
  - tipo: obligatorio y de los admitidos (ver «Tipos»); un tipo no reconocido en la ejecución lanza ConfigError.
  - origen: carpeta de origen (opcional; si aparece, texto no vacío. La carpeta que se pase por la CLI tiene prioridad).
  - filtro: criterios para seleccionar archivos (opcional; si aparece, debe ser un objeto).
  - destino: carpeta de destino cuando corresponda (obligatorio en mover y copiar; prohibido en renombrar-ia y clasificar, que usan «categorias»).
  - plantilla: formato del nuevo nombre cuando corresponda (obligatoria en renombrar; prohibida en renombrar-ia y clasificar).
  - confirmar: booleano opcional (true/false); solo se valida en config.py, la confirmación real la pide la CLI a las acciones destructivas.
  - instrucciones: solo en tipos con IA; texto no vacío; en tipos sin IA su presencia con valor es un error. El texto se AÑADE al mensaje de sistema.
  - max_caracteres: solo en tipos con IA; entero entre 500 y 50000, por defecto 12000 (opcional; null o ausente = defecto; en tipos sin IA su presencia con valor es un error).
  - categorias: solo en tipo clasificar (obligatorio ahí y con al menos una categoría, prohibido en el resto); mapa de identificador (misma regex que «nombre») → carpeta destino no vacía. No lleva «destino» ni «plantilla».

- Tipos (TIPOS_TODOS = mover, copiar, renombrar, borrar, resumir, renombrar-ia, clasificar):
  - mover y copiar (requieren destino; destructivas).
  - renombrar (requiere plantilla; destructiva; desde la CLI exige además --fichero con un único archivo y --nuevo-nombre, y sin --fichero no selecciona nada).
  - borrar (destructiva: pide confirmación salvo --simular o --si; sin --fichero no selecciona nada, así que nunca borra la carpeta entera).
  - resumir (IA; lee .txt/.md/.pdf y guarda nombre.resumen.md junto al original o en «destino» si la acción lo indica; destino opcional; no es destructiva).
  - renombrar-ia (IA; solo .pdf, sin destino ni plantilla; renombra en su carpeta con a_nombre_seguro(); destructiva: confirma salvo --simular o --si; no exige --fichero, procesa la carpeta filtrada).
  - clasificar (IA; lee .pdf/.txt/.md/.docx/.odt; mapa «categorias» obligatorio; mueve físicamente; destructiva: confirma salvo --simular o --si; respuesta de la IA que no coincida exactamente con una categoría → SALTADO sin mover).

- filtro opcional (debe ser un objeto):
  - extensiones: lista de extensiones en minúsculas y con punto (patrón `^\.[a-z0-9]+$`); lista vacía → error.
  - patron: expresión regular válida (si no compila → error).
  - mas_antiguo_que_dias: entero mayor que 0.
  - mayor_que_mb: número mayor que 0 y finito (no NaN ni infinito).

- plantilla: obligatoria en renombrar y prohibida en renombrar-ia/clasificar; solo admite los huecos {fecha:%Y-%m-%d}, {n:03}, {ext} y {nombre}; sin llaves sin cerrar ni llaves de más.

- leer_texto() (compartida por resumir, renombrar-ia y clasificar): .txt y .md en UTF-8, .pdf con pypdf, .docx con python-docx y .odt con odfpy (imports perezosos dentro de _leer_docx/_leer_odt; odfpy necesita teletype.extractText(documento.text), no el objeto entero). Si no se puede leer → LectucliError y quien llama decide (SALTADO y sigue).

- a_nombre_seguro(respuesta) → nombre limpio (renombrar-ia): 1ª línea; quita la extensión añadida por el modelo; NFD sin tildes/ñ; minúsculas; lo que no sea [a-z0-9-] → guion; limpia extremos y colapsa guiones repetidos; tope 60; vacío → "". La extensión original la añade quien llama (fichero.suffix) y las colisiones se resuelven con primer_nombre_libre() (nunca sobrescribir).

## Validaciones de config.py
- Orden: primero config.cargar() (fichero existe, UTF-8, JSON válido con línea y columna, raíz con «version» = 1 y lista «acciones» no vacía) y después config.validar(), que devuelve TODOS los errores a la vez (no solo el primero).
- Cada error es AccionNoValida(accion, campo, motivo) con código de salida 3; una raíz ilegible o sin versión es ConfigError, también código 3.
- La validación es de TIPO y de FORMATO, nunca de contenido de carpetas: las rutas se comprueban al ejecutar, no al validar.
- Un campo con valor prohibido para su tipo (destino/plantilla en renombrar-ia o clasificar, instrucciones o max_caracteres con valor fuera de IA, categorias fuera de clasificar) es error, no un campo a ignorar en silencio.

## Reglas de IA (todas las acciones con IA)
- Mensaje de sistema FIJO por subclase en «sistema_base» (SISTEMA_RESUMIR, SISTEMA_NOMBRAR, SISTEMA_CLASIFICAR) con cláusula anti-inyección; el campo «instrucciones» y el mapa de categorías se AÑADEN, nunca lo sustituyen. AccionIA.__init__ lanza ConfigError si sistema_base está vacío.
- El documento siempre va entre <documento> y </documento>, neutralizando etiquetas incrustadas.
- Estados: HECHO (movido/renombrado), SIMULADO (--simular: sin proveedor, sin .env, sin mkdir), SALTADO con motivo en «detalle» (fichero ilegible, IA sin respuesta válida, ya correcto…).
- Nombrar IA compara el nombre propuesto con el actual ANTES de primer_nombre_libre(): si coincide → SALTADO «el nombre ya es correcto» sin «(1)».
- presupuesto(texto) = min(len(texto), max_caracteres): las acciones con IA leen con leer_texto(fichero, max_caracteres), así que el texto ya viene recortado y el presupuesto es en la práctica lo que se envía al modelo.
- Tope de leer_texto(): devuelve como mucho «tope» caracteres en TODOS los formatos (.txt, .md, .pdf, .docx y .odt), con texto[:tope] al final. Pero el fichero completo se carga entero en memoria ANTES de recortar (el .txt/.md íntegros, todas las páginas del PDF, el .docx y el .odt enteros): max_caracteres limita lo que se manda al modelo, no lo que se lee del disco.
- Detalle del presupuesto: en simulación, «presupuesto: N caracteres»; en ejecución real, «N caracteres enviados» (resumir y renombrar-ia) y «categoría: ...» en clasificar.
- max_tokens de la respuesta por subclase: 1000 en resumir (el valor base de AccionIA), 200 en renombrar-ia y 100 en clasificar.

## Capa de IA (ia.py): ProveedorIA y ProveedorCentro
- ProveedorIA (ABC): única interfaz que ve AccionIA; completar(sistema, usuario, max_tokens=1000) → Respuesta(texto, tokens_entrada, tokens_salida, segundos).
- ProveedorCentro(ProveedorIA): httpx contra una API compatible con OpenAI en POST {url}/chat/completions, con la clave en Authorization: Bearer, tiempos TIEMPO_CONEXION = 10 s y TIEMPO_RESPUESTA = 120 s y contexto TLS (el CA de CENTRO_IA_CA si hay, o certifi). Gestor de contexto: with ProveedorCentro.desde_entorno() as proveedor (cierra con cerrar()).
- desde_entorno(): load_dotenv() y lee CENTRO_IA_URL y CENTRO_IA_KEY (obligatorias: vacías o ausentes → «Falta configurar ... en el archivo .env»), CENTRO_IA_MODELO (opcional; vacía o ausente → MODELO_POR_DEFECTO «qwen3.8-flash-next») y CENTRO_IA_CA (opcional; si no, CA del sistema).
- Proveedor perezoso: la CLI pasa la fábrica (ProveedorCentro.desde_entorno, SIN llamarla) al Motor, que solo invoca self.proveedor() si la acción tiene necesita_ia y no es simulación, y siempre después de seleccionar ficheros. Acciones sin IA, --simular y carpetas sin ficheros no tocan .env ni la red.
- Todo fallo se convierte en IANoDisponible (código 4, sin traza): URL que no empieza por http:// o https://, variables faltantes, certificado CA inexistente o no válido, tiempo de conexión o de respuesta agotado, conexión rechazada o sin red, certificado del servidor no válido, HTTP 401 (clave rechazada), HTTP 429 u otro error HTTP, y respuesta ilegible, vacía o ininterpretable.
- La CLI lo trata en un solo sitio (_gestionar_error_ia en cli.py): «✘ <error>» en rojo y, en una segunda línea, `Las acciones sin IA siguen funcionando: mira cuáles son con «lectucli acciones».` saliendo con el código de la excepción (4). Se usa en ejecutar y en comprobar-ia.

## Reglas al programar
- Valida el JSON en config.py ANTES de ejecutar; errores con AccionNoValida(accion, campo, motivo).
- pathlib y shutil; encoding="utf-8"; nunca shell=True; nunca sobrescribir (destino_libre).
- Toda acción admite --simular y devuelve list[Resultado].
- Las acciones con IA (necesita_ia) solo piden el proveedor cuando la ejecución NO es simulación y solo si hay ficheros seleccionados; --simular no necesita .env ni red.
- Resultado admite un campo opcional «detalle» (último) con el motivo de un SALTADO o el presupuesto de caracteres.
- Códigos de salida: 0 bien · 1 fallo al ejecutar · 2 uso incorrecto · 3 configuración inválida · 4 IA no disponible.
- «lectucli acciones» muestra la columna «IA» («sí» o «—») leída de Accion.necesita_ia (la acción se crea con Accion.desde_config): nunca se deduce del nombre o la descripción.
- La herramienta y el comando se llaman lectucli, nunca «tareas».
- Si añades un campo o un tipo nuevo, documéntalo en el README y en esta skill.
- El proyecto debe funcionar en Linux, Windows y macOS.
- Expande las rutas que contengan ~ para acceder al directorio personal del usuario.
- Evita asumir rutas o comandos específicos de un sistema operativo.