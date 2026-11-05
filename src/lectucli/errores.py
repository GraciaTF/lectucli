"""Excepciones propias de lectucli.

Cada error lleva un código de salida para que la terminal pueda distinguir un
fallo de ejecución (1) de una configuración inválida (3).
"""

from __future__ import annotations

class LectucliError(Exception):
    """Error base de lectucli."""

    codigo_salida = 1


class ConfigError(LectucliError):
    """El fichero acciones.json no se puede leer o no sigue el esquema."""

    codigo_salida = 3


class AccionNoValida(LectucliError):
    """Una acción concreta de acciones.json incumple el esquema."""

    codigo_salida = 3

    def __init__(self, accion: str, campo: str, motivo: str) -> None:
        """Guarda la acción, el campo y el motivo del fallo."""
        self.accion = accion
        self.campo = campo
        self.motivo = motivo
        super().__init__(f"Acción «{accion}», campo «{campo}»: {motivo}")
