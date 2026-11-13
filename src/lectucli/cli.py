import io
import pathlib
import sys
from datetime import datetime

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table
from rich.text import Text

from lectucli import __version__, config
from lectucli.acciones import Accion, Estado
from lectucli.errores import LectucliError
from lectucli.ia import ProveedorCentro
from lectucli.motor import Motor

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


@app.callback()
def principal(
    ctx: typer.Context,
    config_ruta: pathlib.Path = typer.Option(
        pathlib.Path("acciones.json"),
        "--config",
        help="Ruta del fichero de configuración (por defecto: ./acciones.json).",
    ),
) -> None:
    """Guarda la configuración global para todas las órdenes."""
    ctx.obj = config_ruta


def _ruta_config(ctx: typer.Context) -> pathlib.Path:
    """Ruta de la configuración: la opción --config o ./acciones.json."""
    if isinstance(ctx.obj, pathlib.Path):
        return ctx.obj
    return pathlib.Path("acciones.json")


def _cargar_config(ruta: pathlib.Path) -> list[dict]:
    """Carga y valida la configuración, y sale si tiene errores.

    Muestra en rojo los errores previsibles (con su código de salida:
    3 para ConfigError) y devuelve la lista de acciones cuando todo es
    correcto. No muestra trazas.
    """
    try:
        acciones = config.cargar(ruta)
    except LectucliError as exc:
        consola_error.print(f"✘ {exc}", style="red", markup=False)
        raise typer.Exit(code=exc.codigo_salida) from None

    errores = config.validar(acciones)
    if errores:
        for error in errores:
            consola_error.print(f"✘ {error}", style="red", markup=False)
        raise typer.Exit(code=errores[0].codigo_salida)

    return acciones


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
    ctx: typer.Context,
    ruta: pathlib.Path | None = typer.Option(
        None,
        "--ruta",
        "-r",
        help="Ruta del fichero de configuración (por defecto: la de --config o ./acciones.json).",
    ),
) -> None:
    """Comprueba que la configuración cumple el esquema antes de ejecutar acciones.

    Muestra todos los errores encontrados (no solo el primero) y termina con
    código 3 (configuración inválida) si el fichero no es válido.
    """
    if ruta is None:
        ruta = _ruta_config(ctx)
    acciones = _cargar_config(ruta)
    console.print(f"✔ {len(acciones)} acciones válidas", style="green")


@app.command()
def acciones(ctx: typer.Context) -> None:
    """Muestra las acciones definidas en la configuración."""
    ruta = _ruta_config(ctx)
    datos = _cargar_config(ruta)

    tabla = Table(title=f"Acciones de {ruta.name}")
    tabla.add_column("Nombre")
    tabla.add_column("Tipo")
    tabla.add_column("Descripción")

    for accion in datos:
        tabla.add_row(
            escape(str(accion["nombre"])),
            escape(str(accion["tipo"])),
            escape(str(accion["descripcion"])),
        )

    console.print(tabla)


@app.command()
def ejecutar(
    ctx: typer.Context,
    nombre: str = typer.Argument(
        ...,
        help="Nombre de la acción a ejecutar.",
    ),
    carpeta: pathlib.Path | None = typer.Argument(
        None,
        help="Carpeta de origen; tiene prioridad sobre el origen del JSON.",
    ),
    simular: bool = typer.Option(
        False,
        "--simular",
        help="Muestra lo que se haría sin modificar el disco.",
    ),
    si: bool = typer.Option(
        False,
        "--si",
        help="Ejecuta sin pedir confirmación.",
    ),
    fichero: list[str] = typer.Option(
        [],
        "--fichero",
        "-f",
        help=(
            "Nombre de un fichero concreto de la carpeta de origen "
            "(se puede repetir para varios)."
        ),
    ),
    nuevo_nombre: str | None = typer.Option(
        None,
        "--nuevo-nombre",
        "-n",
        help="Nombre nuevo que se aplicará con la acción renombrar.",
    ),
) -> None:
    """Ejecuta una acción de la configuración sobre una carpeta.

    Con --simular solo se muestra lo que se haría: el disco no se toca.
    Las acciones destructivas piden confirmación salvo con --simular o --si.
    Con --fichero (repetible) solo se actúa sobre los ficheros indicados
    por su nombre. Con --nuevo-nombre se indica el nombre nuevo de la
    acción renombrar: sustituye la plantilla del JSON.
    """
    datos = _cargar_config(_ruta_config(ctx))
    # Se pasa la fábrica (sin llamarla): el proveedor de IA solo se
    # crea si la acción elegida lo necesita y no es una simulación.
    motor = Motor(datos, proveedor=ProveedorCentro.desde_entorno)

    # Definición de la acción pedida: hace falta para las comprobaciones
    # previas, tanto en simulación como en ejecución real.
    definicion = next(
        (
            entrada
            for entrada in datos
            if isinstance(entrada, dict) and entrada.get("nombre") == nombre
        ),
        None,
    )

    # La CLI conoce sus opciones: aquí se exigen los parámetros que
    # «renombrar» necesita, para no renombrar nada si falta alguno.
    # Sale con su código antes de llegar al motor.
    if definicion is not None and definicion.get("tipo") == "renombrar":
        try:
            if not fichero:
                raise LectucliError(
                    "La acción «renombrar» requiere indicar el archivo con --fichero"
                )
            if len(fichero) > 1:
                raise LectucliError(
                    "La acción «renombrar» renombra un archivo cada vez: "
                    "usa un solo --fichero"
                )
            if nuevo_nombre is None or not nuevo_nombre.strip():
                raise LectucliError(
                    "La acción «renombrar» requiere indicar el nombre nuevo "
                    "con --nuevo-nombre"
                )
        except LectucliError as exc:
            consola_error.print(f"✘ {exc}", style="red", markup=False)
            raise typer.Exit(code=exc.codigo_salida) from None

    # El motor no es interactivo: la confirmación se pide aquí, antes de
    # ejecutar. Se reutiliza la fábrica Accion para saber si es destructiva.
    if not simular and not si:
        if definicion is not None and Accion.desde_config(definicion).destructiva:
            typer.confirm(
                f"La acción «{nombre}» es destructiva: ¿continuar?",
                abort=True,
            )

    try:
        resultados = motor.ejecutar(
            nombre, carpeta, simular, ficheros=fichero, nuevo_nombre=nuevo_nombre
        )
    except LectucliError as exc:
        consola_error.print(f"✘ {exc}", style="red", markup=False)
        raise typer.Exit(code=exc.codigo_salida) from None
    except OSError as exc:
        consola_error.print(
            f"✘ No se pudo completar «{nombre}»: {exc}",
            style="red",
            markup=False,
        )
        raise typer.Exit(code=1) from None

    if not resultados:
        console.print(
            f"Ningún fichero cumple el filtro de la acción «{nombre}»",
            style="yellow",
        )
        return

    titulo = f"Resultado de «{nombre}»"
    if simular:
        titulo += " (simulación)"

    # La columna «Detalle» solo aparece si algún resultado la trae (p.
    # ej. el presupuesto de caracteres o el motivo de un fichero
    # saltado): así la tabla de las acciones existentes no cambia.
    con_detalle = any(resultado.detalle for resultado in resultados)

    tabla = Table(title=titulo)
    tabla.add_column("Fichero")
    tabla.add_column("Destino")
    tabla.add_column("Estado")
    if con_detalle:
        tabla.add_column("Detalle")

    colores = {"hecho": "green", "simulado": "cyan", "saltado": "yellow"}
    for resultado in resultados:
        destino = str(resultado.destino) if resultado.destino is not None else "—"
        fila = [
            escape(str(resultado.origen)),
            escape(destino),
            Text(
                resultado.estado.value,
                style=colores.get(resultado.estado.value, "white"),
            ),
        ]
        if con_detalle:
            fila.append(escape(resultado.detalle or ""))
        tabla.add_row(*fila)

    console.print(tabla)

    hechos = sum(1 for r in resultados if r.estado == Estado.HECHO)
    simulados = sum(1 for r in resultados if r.estado == Estado.SIMULADO)
    saltados = sum(1 for r in resultados if r.estado == Estado.SALTADO)
    console.print(
        f"Resumen: {hechos} hechos, {simulados} simulados y {saltados} saltados",
        style="bold",
    )


@app.command()
def comprobar_ia() -> None:
    """Comprueba la conexión con el proveedor de IA del centro.

    Muestra el servidor, el modelo y si hay clave configurada (nunca la
    clave) y hace una pregunta mínima al modelo. Si la IA no está
    disponible termina con código 4 y sin mostrar la traza del error.
    """
    try:
        with ProveedorCentro.desde_entorno() as proveedor:
            console.print(f"Servidor: {proveedor.url}")
            console.print(f"Modelo: {proveedor.modelo}")
            console.print("Clave: definida")
            respuesta = proveedor.completar(
                "Responde con una sola palabra.",
                "Hola",
                max_tokens=5,
            )
    except LectucliError as exc:
        consola_error.print(f"✘ {exc}", style="red", markup=False)
        raise typer.Exit(code=exc.codigo_salida) from None

    console.print(f"Respuesta: {respuesta.texto}", style="green")
    console.print(
        f"Tokens: {respuesta.tokens_entrada} de entrada / "
        f"{respuesta.tokens_salida} de salida · {respuesta.segundos:.2f} s"
    )
