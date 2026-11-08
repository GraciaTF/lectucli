"""Acciones de acciones.json: modelo y aplicación sobre el disco.

Aquí se convierte cada acción, ya validada por config.validar(), en un
objeto Accion de su subclase correspondiente (Mover, Copiar, Renombrar
u Borrar). Este módulo es el único con permiso de escritura en disco y,
aun así, con simular=True no modifica absolutamente nada: cada operación
de escritura (mover, copiar, renombrar, borrar y mkdir) va siempre por
detrás de la comporbación «if simular».

Reglas de la skill acciones-json aplicadas aquí:
- pathlib y shutil; nunca shell=True; nunca se sobrescribe nada: si un
  destino está ocupado se busca el primer nombre libre con sufijos
  «(1)», «(2)»…
- Toda acción devuelve list[Resultado].
- Se expanden las rutas que contienen ~ (expanduser).
"""

from __future__ import annotations

import abc
import pathlib
import re
import shutil
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from lectucli.errores import ConfigError, LectucliError


class Estado(str, Enum):
    """Estado de un Resultado.

    Son exactamente tres: hecho, simulado y saltado. Para mostrarlo en
    pantalla debe usarse su valor, p. ej. Estado.HECHO.value.
    """

    HECHO = "hecho"
    SIMULADO = "simulado"
    SALTADO = "saltado"


@dataclass(frozen=True)
class Resultado:
    """Resultado de aplicar una operación a un fichero.

    destino es None cuando la operación no tiene carpeta de destino
    (renombrar en su misma carpeta y borrar).
    """

    origen: pathlib.Path
    destino: pathlib.Path | None
    estado: Estado


@dataclass(frozen=True)
class Filtro:
    """Criterios de selección de ficheros de una acción.

    La validación de estos campos ya la hizo config.validar(); aquí solo
    se guardan y se comprueban. Un campo ausente no filtra.
    """

    extensiones: tuple[str, ...] = ()
    patron: re.Pattern[str] | None = None
    mas_antiguo_que_dias: int | None = None
    mayor_que_mb: float | None = None

    @classmethod
    def desde_dict(cls, datos: dict | Filtro | None) -> Filtro:
        """Construye el filtro a partir del campo «filtro» de la config."""
        if datos is None:
            return cls()
        if isinstance(datos, Filtro):
            return datos

        extensiones = tuple(
            str(extension).lower()
            for extension in datos.get("extensiones") or ()
        )
        texto = datos.get("patron")
        patron = re.compile(texto) if isinstance(texto, str) else None
        return cls(
            extensiones=extensiones,
            patron=patron,
            mas_antiguo_que_dias=datos.get("mas_antiguo_que_dias"),
            mayor_que_mb=datos.get("mayor_que_mb"),
        )

    def coincide(self, ruta: pathlib.Path) -> bool:
        """Comprueba si un fichero cumple todos los criterios del filtro.

        Un criterio ausente no filtra. Si los metadatos del fichero no se
        pueden leer, el fichero no se selecciona.
        """
        if self.extensiones and ruta.suffix.lower() not in self.extensiones:
            return False
        if self.patron is not None and not self.patron.search(ruta.name):
            return False
        if self.mas_antiguo_que_dias is None and self.mayor_que_mb is None:
            return True

        try:
            stats = ruta.stat()
        except OSError:
            return False

        if self.mas_antiguo_que_dias is not None:
            limite = time.time() - self.mas_antiguo_que_dias * 86_400
            if stats.st_mtime > limite:
                return False
        if self.mayor_que_mb is not None:
            if stats.st_size <= self.mayor_que_mb * 1024 * 1024:
                return False
        return True


def expandir_plantilla(plantilla: str, fichero: pathlib.Path, n: int) -> str:
    """Sustituye los huecos de la plantilla por los datos del fichero.

    Huecos admitidos (ya validados por config.validar()):
    - {nombre}: nombre sin extensión.
    - {ext}: extensión con su punto, p. ej. .pdf.
    - {n:03}: contador con tres cifras.
    - {fecha:%Y-%m-%d}: fecha de modificación del fichero.

    Solo lee metadatos (stat); no escribe nada.
    """
    stats = fichero.stat()
    fecha = datetime.fromtimestamp(stats.st_mtime)
    resultado = plantilla
    resultado = resultado.replace("{nombre}", fichero.stem)
    resultado = resultado.replace("{ext}", fichero.suffix)
    resultado = resultado.replace("{n:03}", f"{n:03d}")
    resultado = resultado.replace("{fecha:%Y-%m-%d}", fecha.strftime("%Y-%m-%d"))
    return resultado


class Accion(abc.ABC):
    """Acción de acciones.json preparada para ejecutarse.

    ejecutar() es el método plantilla: recorre los ficheros seleccionados
    y llama a aplicar(), que implementa cada subclase. La fábrica
    desde_config() elige la subclase consultando el registro, sin ningún
    if/elif por tipo.
    """

    # Registro de subclases: {tipo del JSON: subclase}. Se rellena con el
    # decorador Accion.registrar() al definir cada subclase.
    _REGISTRO: dict[str, type[Accion]] = {}

    # Cada subclase registra su tipo con el decorador y declara si
    # modifica el disco con destructiva.
    tipo: str = ""
    destructiva: bool = False
    # Si es True, el motor solo actúa sobre ficheros nombrados
    # explícitamente desde la CLI (--fichero); sin ninguno, no selecciona
    # nada. Evita que un filtro vacío borre la carpeta entera.
    requiere_ficheros: bool = False

    @classmethod
    def registrar(cls, tipo: str) -> Callable[[type[Accion]], type[Accion]]:
        """Devuelve un decorador que registra una subclase para un tipo.

        Así se evitan los if/elif por tipo: la subclase se da de alta al
        definirse y desde_config() solo consulta el registro.
        """

        def decorador(subclase: type[Accion]) -> type[Accion]:
            subclase.tipo = tipo
            cls._REGISTRO[tipo] = subclase
            return subclase

        return decorador

    @classmethod
    def desde_config(cls, datos: dict) -> Accion:
        """Crea la subclase que corresponde al «tipo» de una acción.

        Presupone que config.validar() ya aprobó la acción.
        """
        tipo = datos.get("tipo")
        subclase = cls._REGISTRO.get(tipo)
        if subclase is None:
            tipos = ", ".join(sorted(cls._REGISTRO))
            raise ConfigError(
                f"El tipo de acción «{tipo}» no está reconocido; "
                f"los tipos válidos son: {tipos}"
            )
        return subclase(
            nombre=datos.get("nombre"),
            descripcion=datos.get("descripcion"),
            origen=datos.get("origen"),
            filtro=datos.get("filtro"),
            destino=datos.get("destino"),
            plantilla=datos.get("plantilla"),
            confirmar=datos.get("confirmar", False),
        )

    def __init__(
        self,
        *,
        nombre: str,
        descripcion: str | None,
        origen: str | pathlib.Path | None = None,
        filtro: dict | Filtro | None = None,
        destino: str | pathlib.Path | None = None,
        plantilla: str | None = None,
        confirmar: bool = False,
    ) -> None:
        """Guarda los campos de la acción, ya convertidos a Python.

        No valida nada: eso ya lo hizo config.validar(). Las rutas que
        contienen ~ se expanden aquí mismo.
        """
        self.nombre = nombre
        self.descripcion = descripcion or ""
        self.origen = pathlib.Path(origen).expanduser() if origen else None
        self.filtro = Filtro.desde_dict(filtro)
        self.destino = pathlib.Path(destino).expanduser() if destino else None
        self.plantilla = plantilla
        self.confirmar = confirmar
        # Nombres de destino ya ocupados en esta ejecución: solo viven en
        # memoria (nunca en disco) para que la simulación y la ejecución
        # real calculen exactamente los mismos destinos.
        self._reservados: set[pathlib.Path] = set()

    def ejecutar(
        self, ficheros: list[pathlib.Path], simular: bool
    ) -> list[Resultado]:
        """Aplica la operación a cada fichero y devuelve sus resultados.

        Método plantilla: vacía la reserva de nombres de esta ejecución,
        crea la carpeta de destino solo si no se simula (crear una carpeta
        ya es escribir en disco) y recorre los ficheros llamando a
        aplicar(), en orden, empezando el contador n por 1.
        """
        self._reservados = set()
        if self.destino is not None and not simular:
            self.destino.mkdir(parents=True, exist_ok=True)
        return [
            self.aplicar(fichero, n, simular)
            for n, fichero in enumerate(ficheros, start=1)
        ]

    @abc.abstractmethod
    def aplicar(self, fichero: pathlib.Path, n: int, simular: bool) -> Resultado:
        """Aplica la operación concreta a un fichero.

        Lo implementa cada subclase. El orden fijo es: calcular el
        destino, buscar nombre libre si hace falta, devolver SIMULADO si
        se simula y, solo entonces, escribir en disco.
        """
        raise NotImplementedError

    def primer_nombre_libre(self, destino: pathlib.Path) -> pathlib.Path:
        """Devuelve el primer nombre libre sumando sufijos «(1)», «(2)»…

        Nunca sobrescribe: si el nombre ya existe en disco o ya se ha
        reservado en esta misma ejecución, prueba con el siguiente. El
        nombre elegido queda reservado para que la simulación y la
        ejecución real calculen exactamente los mismos destinos.

        Solo lee (exists); no escribe nada.
        """
        candidato = destino
        contador = 0
        while candidato.exists() or candidato in self._reservados:
            contador += 1
            candidato = destino.with_name(
                f"{destino.stem} ({contador}){destino.suffix}"
            )
        self._reservados.add(candidato)
        return candidato


@Accion.registrar("mover")
class Mover(Accion):
    """Mueve ficheros a la carpeta de destino sin sobrescribir nada."""

    destructiva = True

    def aplicar(self, fichero: pathlib.Path, n: int, simular: bool) -> Resultado:
        """Mueve un fichero, o lo salta si ya está en la carpeta destino."""
        if self.destino is None:
            raise LectucliError(
                f"La acción «{self.nombre}» no tiene carpeta de destino"
            )
        destino_base = self.destino / fichero.name
        if self.destino.resolve() == fichero.parent.resolve():
            # Mismo origen y destino: no se mueve ni se renombra nada.
            return Resultado(fichero, destino_base, Estado.SALTADO)
        destino = self.primer_nombre_libre(destino_base)
        if simular:
            return Resultado(fichero, destino, Estado.SIMULADO)
        shutil.move(fichero, destino)
        return Resultado(fichero, destino, Estado.HECHO)


@Accion.registrar("copiar")
class Copiar(Accion):
    """Copia ficheros a la carpeta de destino sin sobrescribir nada."""

    destructiva = True

    def aplicar(self, fichero: pathlib.Path, n: int, simular: bool) -> Resultado:
        """Copia un fichero; si el nombre está ocupado, usa sufijo «(1)»."""
        if self.destino is None:
            raise LectucliError(
                f"La acción «{self.nombre}» no tiene carpeta de destino"
            )
        destino_base = self.destino / fichero.name
        destino = self.primer_nombre_libre(destino_base)
        if simular:
            return Resultado(fichero, destino, Estado.SIMULADO)
        shutil.copy2(fichero, destino)
        return Resultado(fichero, destino, Estado.HECHO)


@Accion.registrar("renombrar")
class Renombrar(Accion):
    """Renombra ficheros en su propia carpeta usando la plantilla."""

    destructiva = True

    def __init__(
        self,
        *,
        nombre: str,
        descripcion: str | None,
        origen: str | pathlib.Path | None = None,
        filtro: dict | Filtro | None = None,
        destino: str | pathlib.Path | None = None,
        plantilla: str | None = None,
        confirmar: bool = False,
    ) -> None:
        """Guarda los campos de la acción ignorando «destino».

        El renombrado actúa en la propia carpeta de origen: un destino
        en el JSON solo crearía una carpeta sin sentido.
        """
        super().__init__(
            nombre=nombre,
            descripcion=descripcion,
            origen=origen,
            filtro=filtro,
            destino=None,
            plantilla=plantilla,
            confirmar=confirmar,
        )

    def aplicar(self, fichero: pathlib.Path, n: int, simular: bool) -> Resultado:
        """Calcula el nombre nuevo y renombra, o salta si no es seguro."""
        if self.plantilla is None:
            raise LectucliError(
                f"La acción «{self.nombre}» no tiene plantilla de renombrado"
            )
        nuevo_nombre = expandir_plantilla(self.plantilla, fichero, n)
        if (
            not nuevo_nombre.strip()
            or nuevo_nombre in (".", "..")
            or "/" in nuevo_nombre
            or "\\" in nuevo_nombre
        ):
            # Nombre inseguro: no debe permitir salir de la carpeta.
            return Resultado(fichero, None, Estado.SALTADO)
        destino = fichero.parent / nuevo_nombre
        if destino == fichero:
            # La plantilla no cambia el nombre: no hay nada que renombrar.
            return Resultado(fichero, destino, Estado.SALTADO)
        destino = self.primer_nombre_libre(destino)
        if simular:
            return Resultado(fichero, destino, Estado.SIMULADO)
        fichero.rename(destino)
        return Resultado(fichero, destino, Estado.HECHO)


@Accion.registrar("borrar")
class Borrar(Accion):
    """Borra ficheros.

    La confirmación no es cosa del motor: cli.py la pedirá antes de
    ejecutar (siempre, salvo --si), y nunca en modo simulación.
    """

    destructiva = True
    # Borrar solo con nombres explícitos: sin --fichero no se borra nada.
    requiere_ficheros = True

    def __init__(
        self,
        *,
        nombre: str,
        descripcion: str | None,
        origen: str | pathlib.Path | None = None,
        filtro: dict | Filtro | None = None,
        destino: str | pathlib.Path | None = None,
        plantilla: str | None = None,
        confirmar: bool = False,
    ) -> None:
        """Guarda los campos de la acción ignorando «destino».

        Borrar no tiene carpeta de destino: un destino en el JSON solo
        crearía una carpeta sin sentido.
        """
        super().__init__(
            nombre=nombre,
            descripcion=descripcion,
            origen=origen,
            filtro=filtro,
            destino=None,
            plantilla=plantilla,
            confirmar=confirmar,
        )

    def aplicar(self, fichero: pathlib.Path, n: int, simular: bool) -> Resultado:
        """Borra un fichero, o solo avisa de que se borraría si simula."""
        if simular:
            return Resultado(fichero, None, Estado.SIMULADO)
        fichero.unlink()
        return Resultado(fichero, None, Estado.HECHO)
