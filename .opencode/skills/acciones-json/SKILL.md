---
name: acciones-json
description: Reglas del fichero acciones.json de la CLI lectucli (campos, tipos, filtros, plantillas y validación). Úsala siempre que crees o cambies acciones o el código que las lee (config.py, acciones.py, motor.py).
---

# Esquema de acciones.json

- Raíz: {"version": 1, "acciones": [...]}.
- Cada acción contiene:
  - nombre: identificador único, en minúsculas y con guiones.
  - descripcion: explica qué hace.
  - tipo: operación que realizará.
  - origen: carpeta de origen (opcional).
  - filtro: criterios para seleccionar archivos (opcional).
  - destino: carpeta de destino cuando corresponda.
  - plantilla: formato del nuevo nombre cuando corresponda
  - confirmar: indica si requiere confirmación cuando corresponda.
  - instrucciones: solo en tipos con IA; texto que se AÑADE al mensaje de sistema (opcional).
  - max_caracteres: solo en tipos con IA; entero entre 500 y 50000, por defecto 12000 (opcional; null o ausente = defecto).
  - categorias: solo en tipo clasificar (obligatorio ahí, prohibido en el resto); mapa de identificador → carpeta destino. No lleva «destino» ni «plantilla».

- Tipos:
  - mover y copiar (requieren destino).
  - renombrar (requiere plantilla).
  - borrar (requiere confirmación, salvo --si).
  - resumir (IA; lee .txt/.md/.pdf y guarda nombre.resumen.md; destino opcional).
  - renombrar-ia (IA; solo .pdf, sin destino ni plantilla; renombra en su carpeta con a_nombre_seguro(); destructiva: confirma salvo --simular o --si; no exige --fichero, procesa la carpeta filtrada).
  - clasificar (IA; lee .pdf/.txt/.md/.docx/.odt; mapa «categorias» obligatorio; mueve físicamente; destructiva: confirma salvo --simular o --si; respuesta de la IA que no coincida exactamente con una categoría → SALTADO sin mover).

- filtro opcional:
  - extensiones (lista de extensiones en minúsculas).
  - patron (expresión regular válida).
  - mas_antiguo_que_dias.
  - mayor_que_mb.

- plantilla: huecos {fecha:%Y-%m-%d}, {n:03}, {ext}, {nombre}.

- leer_texto() (compartida por resumir, renombrar-ia y clasificar): .txt y .md en UTF-8, .pdf con pypdf, .docx con python-docx y .odt con odfpy (imports perezosos dentro de _leer_docx/_leer_odt; odfpy necesita teletype.extractText(documento.text), no el objeto entero). Si no se puede leer → LectucliError y quien llama decide (SALTADO y sigue).

- a_nombre_seguro(respuesta) → nombre limpio (renombrar-ia): 1ª línea; quita la extensión añadida por el modelo; NFD sin tildes/ñ; minúsculas; lo que no sea [a-z0-9-] → guion; limpia extremos y colapsa guiones repetidos; tope 60; vacío → "". La extensión original la añade quien llama (fichero.suffix) y las colisiones se resuelven con primer_nombre_libre() (nunca sobrescribir).

## Reglas de IA (todas las acciones con IA)
- Mensaje de sistema FIJO por subclase en «sistema_base» (SISTEMA_RESUMIR, SISTEMA_NOMBRAR, SISTEMA_CLASIFICAR) con cláusula anti-inyección; el campo «instrucciones» y el mapa de categorías se AÑADEN, nunca lo sustituyen. AccionIA.__init__ lanza ConfigError si sistema_base está vacío.
- El documento siempre va entre <documento> y </documento>, neutralizando etiquetas incrustadas.
- Estados: HECHO (movido/renombrado), SIMULADO (--simular: sin proveedor, sin .env, sin mkdir), SALTADO con motivo en «detalle» (fichero ilegible, IA sin respuesta válida, ya correcto…).
- Nombrar IA compara el nombre propuesto con el actual ANTES de primer_nombre_libre(): si coincide → SALTADO «el nombre ya es correcto» sin «(1)».

## Reglas al programar
- Valida el JSON en config.py ANTES de ejecutar; errores con AccionNoValida(accion, campo, motivo).
- pathlib y shutil; encoding="utf-8"; nunca shell=True; nunca sobrescribir (destino_libre).
- Toda acción admite --simular y devuelve list[Resultado].
- Las acciones con IA (necesita_ia) solo piden el proveedor cuando la ejecución NO es simulación; --simular no necesita .env.
- Resultado admite un campo opcional «detalle» (último) con el motivo de un SALTADO o el presupuesto de caracteres.
- Si añades un campo o un tipo nuevo, documéntalo en el README y en esta skill.
- El proyecto debe funcionar en Linux, Windows y macOS.
- Expande las rutas que contengan ~ para acceder al directorio personal del usuario.
- Evita asumir rutas o comandos específicos de un sistema operativo.