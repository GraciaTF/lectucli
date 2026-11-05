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

- Tipos:
  - mover y copiar (requieren destino).
  - renombrar (requiere plantilla).
  - borrar (requiere confirmación, salvo --si).

- filtro opcional:
  - extensiones (lista de extensiones en minúsculas).
  - patron (expresión regular válida).
  - mas_antiguo_que_dias.
  - mayor_que_mb.

- plantilla: huecos {fecha:%Y-%m-%d}, {n:03}, {ext}, {nombre}.

## Reglas al programar
- Valida el JSON en config.py ANTES de ejecutar; errores con AccionNoValida(accion, campo, motivo).
- pathlib y shutil; encoding="utf-8"; nunca shell=True; nunca sobrescribir (destino_libre).
- Toda acción admite --simular y devuelve list[Resultado].
- Si añades un campo o un tipo nuevo, documéntalo en el README y en esta skill.
- El proyecto debe funcionar en Linux, Windows y macOS.
- Expande las rutas que contengan ~ para acceder al directorio personal del usuario.
- Evita asumir rutas o comandos específicos de un sistema operativo.