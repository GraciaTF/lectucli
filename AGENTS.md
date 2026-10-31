# lectucli · CLI de lecturas para actividades de aula (proyecto de 1º DAM)

## Stack y órdenes
- Python 3.12 + Typer, gestionado con uv (src layout, paquete `src/lectucli`).
- Ejecutar: `uv run lectucli --help` · Validar config: `uv run lectucli validar` · Pruebas: `uv run pytest`.
- `cli.py` todavía no existe: el punto de entrada declarado en `pyproject.toml`
  (`lectucli.cli:app`) aún falla. pytest no está instalado; añádelo con
  `uv add --dev pytest` antes de usarlo.

## Normas
- Mensajes y comentarios en español; código claro antes que listo.
- pathlib siempre, encoding="utf-8", nada de os.system ni shell=True: tiene que
  funcionar en Linux, Windows y macOS.
- Nunca ejecutes acciones sobre carpetas reales: solo en una carpeta de pruebas
  y con `--simular`.
- No toques .env ni escribas claves en ningún fichero. No hagas git push ni
  commits: los hace el alumno.
- Antes de cambiar un fichero, explica en 2-3 líneas qué vas a hacer.
