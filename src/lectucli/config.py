"""Carga y validación del fichero acciones.json.

La validación se realiza ANTES de ejecutar ninguna acción: primero se lee y
estructura el fichero con cargar() y después validar() comprueba todas las
acciones y devuelve TODOS los errores encontrados (no solo el primero).
"""

from __future__ import annotations

import json
import math
import pathlib
import re

from lectucli.errores import AccionNoValida, ConfigError

VERSION_ESQUEMA = 1
TIPOS_ADMITIDOS = ("mover", "copiar", "renombrar", "borrar")

RE_NOMBRE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RE_EXTENSION = re.compile(r"^\.[a-z0-9]+$")
RE_HUECO = re.compile(r"\{([^{}]*)\}")
HUECOS_ADMITIDOS = ("nombre", "ext", "n:03", "fecha:%Y-%m-%d")


def cargar(ruta: str | pathlib.Path) -> list[dict]:
    """Lee acciones.json y devuelve la lista de acciones.

    Comprueba que el fichero existe, que es JSON válido (con línea y columna
    del fallo) y que la estructura raíz es correcta («version» y «acciones»).
    Lanza ConfigError si algo va mal.
    """
    fichero = pathlib.Path(ruta).expanduser()

    if not fichero.is_file():
        raise ConfigError(f"No existe el fichero «{fichero}»")

    try:
        texto = fichero.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ConfigError(f"El fichero «{fichero}» no está codificado en UTF-8") from exc
    except OSError as exc:
        detalle = exc.strerror or str(exc)
        raise ConfigError(f"No se puede leer «{fichero}»: {detalle}") from exc

    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as exc:
        raise ConfigError(
            f"JSON inválido en «{fichero}», línea {exc.lineno}, columna {exc.colno}: {exc.msg}"
        ) from exc

    if not isinstance(datos, dict):
        raise ConfigError(
            f"El contenido de «{fichero}» debe ser un objeto JSON con los campos «version» y «acciones»"
        )

    if "version" not in datos:
        raise ConfigError(f"El fichero «{fichero}» no contiene el campo «version»")
    if isinstance(datos["version"], bool) or datos["version"] != VERSION_ESQUEMA:
        raise ConfigError(
            f"El campo «version» debe valer {VERSION_ESQUEMA}; se ha encontrado «{datos['version']}»"
        )

    if "acciones" not in datos:
        raise ConfigError(f"El fichero «{fichero}» no contiene el campo «acciones»")
    if not isinstance(datos["acciones"], list):
        raise ConfigError(f"El campo «acciones» debe ser una lista de acciones")

    return datos["acciones"]


def validar(acciones: list[dict]) -> list[AccionNoValida]:
    """Comprueba todas las acciones y devuelve todos los errores encontrados.

    Devuelve una lista vacía si no hay fallos; cada AccionNoValida lleva la
    acción, el campo y el motivo para poder mostrarlos todos juntos.
    """
    errores: list[AccionNoValida] = []
    nombres: set[str] = set()

    for posicion, accion in enumerate(acciones):
        if not isinstance(accion, dict):
            errores.append(
                AccionNoValida(
                    f"#{posicion + 1}",
                    "acciones",
                    "cada acción debe ser un objeto con sus campos",
                )
            )
            continue
        errores.extend(_validar_accion(accion, posicion, nombres))

    return errores


def _validar_accion(accion: dict, posicion: int, nombres: set[str]) -> list[AccionNoValida]:
    """Comprueba una acción y devuelve la lista de sus errores."""
    errores: list[AccionNoValida] = []

    def falla(campo: str, motivo: str) -> None:
        errores.append(AccionNoValida(etiqueta, campo, motivo))

    nombre = accion.get("nombre")
    etiqueta = nombre if isinstance(nombre, str) and nombre else f"#{posicion + 1}"

    # nombre: obligatorio, en minúsculas con números y guiones, y único
    if not isinstance(nombre, str):
        falla("nombre", "es obligatorio y debe ser un texto")
    elif not nombre.strip():
        falla("nombre", "no puede estar vacío")
    elif not RE_NOMBRE.match(nombre):
        falla(
            "nombre",
            "solo admite minúsculas, números y guiones, sin guiones al principio o al final",
        )
    if isinstance(nombre, str) and nombre:
        if nombre in nombres:
            falla("nombre", "está repetido: cada acción debe tener un nombre único")
        nombres.add(nombre)

    # descripcion: obligatoria y no vacía
    descripcion = accion.get("descripcion")
    if not isinstance(descripcion, str) or not descripcion.strip():
        falla("descripcion", "es obligatoria y debe explicar qué hace la acción")

    # tipo: obligatorio y admitido
    tipo = accion.get("tipo")
    if not isinstance(tipo, str) or not tipo:
        falla("tipo", "es obligatorio y debe ser un texto")
    elif tipo not in TIPOS_ADMITIDOS:
        falla(
            "tipo",
            f"«{tipo}» no está admitido; los tipos válidos son: {', '.join(TIPOS_ADMITIDOS)}",
        )

    # campos comunes opcionales: solo se comprueba el tipo si aparecen
    if "origen" in accion:
        origen = accion["origen"]
        if not isinstance(origen, str) or not origen.strip():
            falla("origen", "debe ser una ruta de carpeta no vacía")

    if "confirmar" in accion and not isinstance(accion["confirmar"], bool):
        falla("confirmar", "debe ser booleano (true o false)")

    if "destino" not in accion:
        if tipo in ("mover", "copiar"):
            falla("destino", f"es obligatorio para las acciones de tipo «{tipo}»")
    else:
        destino = accion["destino"]
        if not isinstance(destino, str) or not destino.strip():
            falla("destino", "debe ser una ruta de carpeta no vacía")

    # plantilla: obligatoria al renombrar y con huecos admitidos
    if "plantilla" not in accion:
        if tipo == "renombrar":
            falla("plantilla", "es obligatoria para las acciones de tipo «renombrar»")
    else:
        _validar_plantilla(accion, falla)

    # filtro: opcional, pero si aparece debe cumplir sus reglas
    if "filtro" in accion:
        filtro = accion["filtro"]
        if not isinstance(filtro, dict):
            falla("filtro", "debe ser un objeto con los criterios de selección")
        else:
            _validar_filtro(filtro, falla)

    return errores


def _validar_plantilla(accion: dict, falla) -> None:
    """Comprueba que la plantilla usa exactamente los huecos admitidos."""
    plantilla = accion["plantilla"]

    if not isinstance(plantilla, str) or not plantilla.strip():
        falla("plantilla", "debe ser un texto con los huecos a sustituir")
        return

    for hueco in RE_HUECO.finditer(plantilla):
        cuerpo = hueco.group(1)
        if cuerpo not in HUECOS_ADMITIDOS:
            falla(
                "plantilla",
                f"el hueco «{{{cuerpo}}}» no está admitido; solo se admiten "
                "{nombre}, {ext}, {n:03} y {fecha:%Y-%m-%d}",
            )
            return

    resto = RE_HUECO.sub("", plantilla)
    if "{" in resto or "}" in resto:
        falla("plantilla", "tiene llaves sin cerrar o llaves de más; revisa los huecos")


def _validar_filtro(filtro: dict, falla) -> None:
    """Comprueba los criterios de un filtro, si están presentes."""
    if "extensiones" in filtro:
        extensiones = filtro["extensiones"]
        if not isinstance(extensiones, list):
            falla("filtro.extensiones", "debe ser una lista de extensiones")
        elif not extensiones:
            falla("filtro.extensiones", "debe contener al menos una extensión")
        else:
            for extension in extensiones:
                if not isinstance(extension, str) or not RE_EXTENSION.match(extension):
                    falla(
                        "filtro.extensiones",
                        f"«{extension}» no es una extensión válida; debe empezar "
                        "por punto y estar en minúsculas (p. ej. «.pdf»)",
                    )

    if "patron" in filtro:
        patron = filtro["patron"]
        if not isinstance(patron, str):
            falla("filtro.patron", "debe ser una expresión regular en texto")
        else:
            try:
                re.compile(patron)
            except re.error as exc:
                falla("filtro.patron", f"la expresión regular «{patron}» no es válida: {exc}")

    if "mas_antiguo_que_dias" in filtro:
        dias = filtro["mas_antiguo_que_dias"]
        if isinstance(dias, bool) or not isinstance(dias, int):
            falla("filtro.mas_antiguo_que_dias", "debe ser un número entero mayor que cero")
        elif dias <= 0:
            falla(
                "filtro.mas_antiguo_que_dias",
                f"debe ser un número entero mayor que cero; se ha encontrado «{dias}»",
            )

    if "mayor_que_mb" in filtro:
        megas = filtro["mayor_que_mb"]
        if isinstance(megas, bool) or not isinstance(megas, (int, float)):
            falla("filtro.mayor_que_mb", "debe ser un número mayor que cero")
        elif isinstance(megas, float) and not math.isfinite(megas):
            falla(
                "filtro.mayor_que_mb",
                f"debe ser un número finito mayor que cero; se ha encontrado «{megas}»",
            )
        elif megas <= 0:
            falla(
                "filtro.mayor_que_mb",
                f"debe ser un número mayor que cero; se ha encontrado «{megas}»",
            )
