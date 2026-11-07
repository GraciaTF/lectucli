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

from lectucli.acciones import Accion, Filtro, Resultado
from lectucli.errores import LectucliError


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

    def __init__(self, acciones: list[dict]) -> None:
        """Guarda las acciones ya cargadas y validadas con config."""
        self.acciones = list(acciones)

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

        ficheros = self.seleccionar(origen, accion.filtro)
        if not ficheros:
            # Nada que hacer: no se considera un error.
            return []
        try:
            return accion.ejecutar(ficheros, simular)
        except OSError as exc:
            # Permiso denegado, fichero bloqueado, disco lleno…: se
            # traduce a un error de lectucli sin traza de Python.
            raise LectucliError(
                f"No se pudo ejecutar la acción «{nombre}»: {exc}"
            ) from exc
