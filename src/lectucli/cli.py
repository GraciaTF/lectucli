import io
import pathlib
import sys
from datetime import datetime

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from lectucli import __version__, config
from lectucli.errores import LectucliError

app = typer.Typer(
    name="lectucli",
    help="Gestiona y organiza lecturas para actividades de aula desde la terminal.",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)


def _asegurar_utf8(flujo: io.TextIOBase) -> None:
    """Pasa la salida a UTF-8 si la codificación no admite «✔» ni «✘».

    Algunas terminales de Windows usan cp1252 y no pueden imprimir esos
    símbolos. Solo se cambia cuando hace falta: si la codificación ya
    funciona (Linux, macOS y consolas de Windows) no se toca nada.
    """
    codificacion = flujo.encoding or "utf-8"
    try:
        "✔✘".encode(codificacion)
        return
    except (LookupError, UnicodeEncodeError):
        pass

    try:
        flujo.flush()
        flujo.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError, ValueError):
        # Si el flujo no se puede reconfigurar, se deja como está.
        pass


console = Console()
consola_error = Console(stderr=True)

_asegurar_utf8(sys.stdout)
_asegurar_utf8(sys.stderr)


def _tamano_legible(tamano_bytes: int) -> str:
    """Convierte bytes a una cadena legible."""
    for unidad in ("B", "KB", "MB", "GB", "TB"):
        if tamano_bytes < 1024:
            return f"{tamano_bytes:.0f} {unidad}"
        tamano_bytes /= 1024
    return f"{tamano_bytes:.1f} PB"


@app.command()
def version() -> None:
    """Muestra la versión instalada de lectucli."""
    typer.echo(f"lectucli {__version__}")


@app.command()
def listar(carpeta: pathlib.Path = typer.Argument(pathlib.Path("."), help="Ruta de la carpeta a listar (por defecto: actual).")) -> None:
    """Lista el contenido de una carpeta.

    Por defecto lista la carpeta actual. Acepta rutas que empiezan por ~.
    """
    ruta = carpeta.expanduser()

    if not ruta.exists():
        consola_error.print(f"La carpeta '{ruta}' no existe")
        raise typer.Exit(code=1)

    if not ruta.is_dir():
        consola_error.print(f"La ruta '{ruta}' no es una carpeta")
        raise typer.Exit(code=1)

    filas = []
    for entrada in ruta.iterdir():
        try:
            stats = entrada.stat()
        except (OSError, PermissionError):
            continue

        if entrada.is_dir():
            tipo = "carpeta"
        else:
            tipo = entrada.suffix or "fichero"

        filas.append((
            entrada.is_dir(),
            entrada.name.lower(),
            escape(entrada.name),
            tipo,
            _tamano_legible(stats.st_size),
            datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M"),
        ))

    if not filas:
        typer.echo("La carpeta está vacía")
        return

    tabla = Table(title=f"Contenido de {ruta}")
    tabla.add_column("Nombre")
    tabla.add_column("Tipo")
    tabla.add_column("Tamaño")
    tabla.add_column("Modificado")

    for _, _, nombre, tipo, tamaño, modificado in sorted(filas, key=lambda x: (not x[0], x[1])):
        tabla.add_row(nombre, tipo, tamaño, modificado)

    console.print(tabla)


@app.command()
def validar(
    ruta: pathlib.Path = typer.Option(
        pathlib.Path("acciones.json"),
        "--ruta",
        "-r",
        help="Ruta del fichero acciones.json (por defecto: ./acciones.json).",
    ),
) -> None:
    """Comprueba que acciones.json cumple el esquema antes de ejecutar acciones.

    Muestra todos los errores encontrados (no solo el primero) y termina con
    código 3 (configuración inválida) si el fichero no es válido.
    """
    try:
        acciones = config.cargar(ruta)
        errores = config.validar(acciones)
    except LectucliError as exc:
        consola_error.print(f"✘ {exc}", style="red", markup=False)
        raise typer.Exit(code=exc.codigo_salida) from None

    if errores:
        for error in errores:
            consola_error.print(f"✘ {error}", style="red", markup=False)
        raise typer.Exit(code=errores[0].codigo_salida)

    console.print(f"✔ {len(acciones)} acciones válidas", style="green")
