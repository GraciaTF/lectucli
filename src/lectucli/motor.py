"""Motor de ejecución de acciones.

Aquí se decide QUÉ ficheros se ven afectados (seleccionar) y CUÁNDO se
ejecuta una acción (ejecutar). El motor no escribe en disco: no importa
shutil ni llama a mkdir; delega siempre en Accion.ejecutar() y
Accion.aplicar(). Con simular=True no se modifica absolutamente nada.

El motor tampoco es interactivo: no pide confirmaciones. La de las
acciones de tipo «borrar» la pedirá cli.py antes de llamar aquí.
"""

from __future__ import annotations

import pathlib
from collections.abc import Callable

from lectucli.acciones import Accion, Filtro, Resultado
from lectucli.errores import LectucliError
from lectucli.ia import ProveedorIA


def _validar_carpeta(carpeta: pathlib.Path | str) -> None:
    """Comprueba que la carpeta de trabajo no esté vacía ni sea la actual.

    Un valor vacío («» o solo espacios) se convertiría en el directorio
    actual (Path(".")) y una acción destructiva actuaría sobre los
    ficheros desde los que se lanza la CLI. El directorio actual escrito
    como «.» se descarta también porque, una vez convertido, ya no se
    puede distinguir de un vacío.
    """
    texto = str(carpeta)
    if not texto.strip() or texto == ".":
        raise LectucliError(
            "La carpeta de origen está vacía o es el directorio actual: "
            "pasa una ruta concreta (por ejemplo, ~/lecturas)"
        )


class Motor:
    """Ejecuta las acciones de acciones.json sobre el disco."""

    def __init__(
        self,
        acciones: list[dict],
        proveedor: Callable[[], ProveedorIA] | None = None,
    ) -> None:
        """Guarda las acciones ya validadas y la fábrica del proveedor.

        «proveedor» es una función que CREA el proveedor de IA cuando hace
        falta: así una acción normal, una simulación o una carpeta sin
        ficheros nunca necesitan configuración de IA ni tocan la red.
        """
        self.acciones = list(acciones)
        self.proveedor = proveedor

    @staticmethod
    def seleccionar(
        carpeta: pathlib.Path, filtro: Filtro
    ) -> list[pathlib.Path]:
        """Devuelve los ficheros de la carpeta que cumplen el filtro.

        Solo lectura: usa iterdir() e is_file(). Se ignoran las carpetas
        y los ficheros cuyos datos no se puedan leer. El orden es estable
        (alfabético sin distinguir mayúsculas) para que el contador
        {n:03} dé el mismo número en la simulación que en la ejecución
        real.

        Si la carpeta está vacía, es el directorio actual o no se puede
        leer (permisos), lanza LectucliError.
        """
        _validar_carpeta(carpeta)
        try:
            entradas = list(carpeta.iterdir())
        except OSError as exc:
            # Sin permisos o carpeta ilegible: error controlado.
            raise LectucliError(
                f"No se pudo leer la carpeta «{carpeta}»: {exc}"
            ) from exc
        seleccionados: list[pathlib.Path] = []
        for entrada in entradas:
            try:
                if not entrada.is_file():
                    continue
            except OSError:
                # Fichero ilegible (permisos, enlace roto): se salta.
                continue
            if filtro.coincide(entrada):
                seleccionados.append(entrada)
        seleccionados.sort(key=lambda ruta: ruta.name.lower())
        return seleccionados

    def ejecutar(
        self,
        nombre: str,
        carpeta: pathlib.Path | None,
        simular: bool,
        ficheros: list[str] | None = None,
        nuevo_nombre: str | None = None,
    ) -> list[Resultado]:
        """Busca la acción, selecciona sus ficheros y los ejecuta.

        Flujo: localizar la acción por nombre, crearla con la fábrica,
        resolver la carpeta de origen (la del CLI manda sobre la del
        JSON), seleccionar los ficheros que cumplen el filtro y
        delegar en Accion.ejecutar().

        - Acción o carpeta inexistente: LectucliError.
        - Carpeta vacía o directorio actual: LectucliError.
        - Sin permisos para leer o escribir: LectucliError.
        - Si ningún fichero cumple el filtro: lista vacía.
        - ficheros: nombres concretos indicados en la CLI con --fichero;
          si se pasan, solo se actúa sobre esos (intersección por nombre,
          además del filtro). Si la acción tiene requiere_ficheros y no
          se pasa ninguno, no se selecciona nada (lista vacía).
        - nuevo_nombre: valor de --nuevo-nombre; si se pasa, sustituye la
          plantilla de la acción para esta ejecución (no se concatena).
        - simular=True: no se escribe nada en disco.
        """
        datos = None
        for accion in self.acciones:
            if accion.get("nombre") == nombre:
                datos = accion
                break
        if datos is None:
            disponibles = ", ".join(
                sorted(
                    str(accion.get("nombre"))
                    for accion in self.acciones
                    if isinstance(accion.get("nombre"), str)
                )
            ) or "ninguna"
            raise LectucliError(
                f"No existe la acción «{nombre}». "
                f"Acciones disponibles: {disponibles}"
            )

        accion = Accion.desde_config(datos)

        # El nombre nuevo de la CLI sustituye la plantilla del JSON (no
        # se concatena). Se asigna a la instancia creada para ESTA
        # ejecución: los datos de configuración no se tocan y la
        # siguiente llamada crea otra acción desde el JSON original.
        if nuevo_nombre:
            accion.plantilla = nuevo_nombre

        # La carpeta del CLI tiene prioridad sobre el origen de la config.
        if carpeta is not None:
            _validar_carpeta(carpeta)
            origen = pathlib.Path(carpeta).expanduser()
        elif datos.get("origen"):
            origen = pathlib.Path(datos["origen"]).expanduser()
        else:
            raise LectucliError(
                f"La acción «{nombre}» no indica carpeta de origen: pásala "
                "en la línea de comandos o añádela al campo «origen» de "
                "acciones.json"
            )

        try:
            es_carpeta = origen.is_dir()
        except OSError as exc:
            # Sin permisos para consultar la carpeta: error controlado.
            raise LectucliError(
                f"No se pudo comprobar la carpeta de origen «{origen}»: {exc}"
            ) from exc
        if not es_carpeta:
            raise LectucliError(
                f"La carpeta de origen «{origen}» no existe o no es una carpeta"
            )

        # Sin nombres explícitos, una acción que los exige no selecciona
        # nada: ni siquiera se abre la carpeta (req. de seguridad). Va
        # después de validar el origen para no cambiar los errores
        # existentes de carpeta inexistente o vacía.
        if accion.requiere_ficheros and not ficheros:
            return []

        seleccionados = self.seleccionar(origen, accion.filtro)
        if ficheros:
            # Intersección por nombre: solo los indicados con --fichero
            # que además pasan el filtro del JSON. Se compara el nombre
            # (no la ruta completa) y de forma exacta, para que el
            # resultado sea el mismo en Linux, Windows y macOS.
            pedidos = {pathlib.Path(valor).name for valor in ficheros}
            seleccionados = [
                ruta for ruta in seleccionados if ruta.name in pedidos
            ]
        if not seleccionados:
            # Nada que hacer: no se considera un error.
            return []

        # La IA solo hace falta cuando la acción se va a ejecutar de
        # verdad: en simulación no se crea el proveedor, no se llama a
        # ningún modelo y no se necesita configuración en .env.
        if accion.necesita_ia and not simular:
            if self.proveedor is None:
                raise LectucliError(
                    f"La acción «{nombre}» necesita IA y no hay proveedor "
                    "de IA configurado"
                )
            accion.proveedor = self.proveedor()

        try:
            return accion.ejecutar(seleccionados, simular)
        except OSError as exc:
            # Permiso denegado, fichero bloqueado, disco lleno…: se
            # traduce a un error de lectucli sin traza de Python.
            raise LectucliError(
                f"No se pudo ejecutar la acción «{nombre}»: {exc}"
            ) from exc
