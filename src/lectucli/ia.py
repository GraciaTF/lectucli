"""Capa de inteligencia artificial de lectucli.

Habla directamente con el servidor del centro (API compatible con OpenAI)
mediante httpx, sin depender del SDK de OpenAI. Cualquier problema de
configuración, red, certificado o respuesta del servidor se convierte en
IANoDisponible, con código de salida 4 y sin trazas.
"""

from __future__ import annotations

import json
import os
import ssl
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType

import httpx
from dotenv import load_dotenv

from lectucli.errores import IANoDisponible

# Tiempos de espera diferenciados: la conexión debe fallar pronto, pero la
# respuesta de un modelo puede tardar bastante más. Si no se indican, httpx
# usa 5 segundos para todo y cualquier modelo lento dispara un tiempo agotado.
TIEMPO_CONEXION = 10.0
TIEMPO_RESPUESTA = 120.0

# Modelo que usa lectucli cuando CENTRO_IA_MODELO no está definida, está
# vacía o contiene solo espacios.
MODELO_POR_DEFECTO = "qwen3.8-flash-next"


@dataclass(frozen=True)
class Respuesta:
    """Resultado de una petición al modelo."""

    texto: str
    tokens_entrada: int
    tokens_salida: int
    segundos: float


class ProveedorIA(ABC):
    """Interfaz común de cualquier proveedor de inteligencia artificial."""

    @abstractmethod
    def completar(
        self, sistema: str, usuario: str, max_tokens: int = 1000
    ) -> Respuesta:
        """Envía las instrucciones y el texto al modelo y devuelve la respuesta."""
        raise NotImplementedError


class ProveedorCentro(ProveedorIA):
    """Proveedor que usa el servidor del centro (API compatible con OpenAI).

    La URL y la clave son obligatorias; el modelo (CENTRO_IA_MODELO) y el
    certificado CA propio (CENTRO_IA_CA) son opcionales: si no se indican,
    se usa MODELO_POR_DEFECTO y las CA del sistema (certifi).
    """

    def __init__(
        self, url: str, clave: str, modelo: str, ca: str | None = None
    ) -> None:
        """Guarda la configuración y crea el cliente HTTP.

        El certificado CA se valida aquí, al construir el cliente, porque es
        en ese momento cuando httpx prepara el contexto TLS.
        """
        url = url.strip().rstrip("/")
        if not url.startswith(("http://", "https://")):
            raise IANoDisponible(
                f"La URL del centro «{url}» no es válida: "
                "debe empezar por http:// o https://"
            )

        self.url = url
        self.clave = clave
        self.modelo = modelo
        self.ca = ca
        self.cliente = httpx.Client(
            verify=self._contexto_ssl(ca),
            timeout=httpx.Timeout(TIEMPO_RESPUESTA, connect=TIEMPO_CONEXION),
            headers={"Authorization": f"Bearer {clave}"},
        )

    @classmethod
    def desde_entorno(cls) -> ProveedorCentro:
        """Carga el .env y crea el proveedor con las variables CENTRO_IA_*."""
        load_dotenv()

        url = os.getenv("CENTRO_IA_URL")
        clave = os.getenv("CENTRO_IA_KEY")
        # CENTRO_IA_MODELO es opcional: si no está, se usa el modelo
        # predeterminado del proyecto.
        modelo = os.getenv("CENTRO_IA_MODELO", MODELO_POR_DEFECTO)
        ca = os.getenv("CENTRO_IA_CA")

        faltan = [
            nombre
            for nombre, valor in (
                ("CENTRO_IA_URL", url),
                ("CENTRO_IA_KEY", clave),
            )
            if not valor or not valor.strip()
        ]
        if faltan:
            if len(faltan) == 1:
                lista = faltan[0]
            else:
                lista = ", ".join(faltan[:-1]) + " y " + faltan[-1]
            raise IANoDisponible(
                f"Falta configurar {lista} en el archivo .env"
            )

        # Si la variable existe pero está vacía o contiene solo espacios,
        # también se usa el modelo por defecto.
        if not modelo or not modelo.strip():
            modelo = MODELO_POR_DEFECTO

        ca_limpio = ca.strip() if ca else ""
        return cls(url.strip(), clave.strip(), modelo.strip(), ca_limpio or None)

    @staticmethod
    def _contexto_ssl(ca: str | None) -> ssl.SSLContext | bool:
        """Devuelve la configuración TLS: el CA propio si hay, si no certifi."""
        if not ca:
            return True

        ruta = Path(ca).expanduser()
        if not ruta.is_file():
            raise IANoDisponible(
                f"El certificado CA indicado en CENTRO_IA_CA no existe: {ruta}"
            )

        try:
            # Solo se confiará en este CA: es el comportamiento deseable para
            # un servidor interno del centro con su propia autoridad.
            return ssl.create_default_context(cafile=str(ruta))
        except (ssl.SSLError, OSError, ValueError) as exc:
            raise IANoDisponible(
                f"El certificado CA de CENTRO_IA_CA no es válido: {exc}"
            ) from exc

    def completar(
        self, sistema: str, usuario: str, max_tokens: int = 1000
    ) -> Respuesta:
        """Envía una petición de chat al servidor y devuelve la respuesta.

        Todos los fallos previsibles se convierten en IANoDisponible: la
        terminal mostrará un único mensaje y saldrá con el código 4.
        """
        inicio = time.perf_counter()

        try:
            respuesta = self.cliente.post(
                f"{self.url}/chat/completions",
                json={
                    "model": self.modelo,
                    "messages": [
                        {"role": "system", "content": sistema},
                        {"role": "user", "content": usuario},
                    ],
                    "max_tokens": max_tokens,
                },
            )
            respuesta.raise_for_status()
            datos = respuesta.json()
            contenido = datos["choices"][0]["message"]["content"]
            uso = datos.get("usage") or {}
            tokens_entrada = int(uso.get("prompt_tokens") or 0)
            tokens_salida = int(uso.get("completion_tokens") or 0)
        except httpx.ConnectTimeout as exc:
            raise IANoDisponible(
                "Se ha agotado el tiempo de conexión con el servidor de IA "
                f"({self.url}); comprueba la red"
            ) from exc
        except httpx.TimeoutException as exc:
            raise IANoDisponible(
                f"El servidor de IA no ha respondido en {TIEMPO_RESPUESTA:.0f} "
                f"segundos ({self.url})"
            ) from exc
        except httpx.ConnectError as exc:
            raise IANoDisponible(self._mensaje_conexion(exc)) from exc
        except httpx.HTTPStatusError as exc:
            raise IANoDisponible(self._mensaje_estado(exc)) from exc
        except (httpx.InvalidURL, httpx.UnsupportedProtocol) as exc:
            raise IANoDisponible(
                f"La URL del centro «{self.url}» no es válida: "
                "debe empezar por http:// o https://"
            ) from exc
        except httpx.DecodingError as exc:
            raise IANoDisponible(
                "El servidor de IA ha devuelto una respuesta ilegible"
            ) from exc
        except httpx.RequestError as exc:
            raise IANoDisponible(
                f"No se pudo completar la petición al servidor de IA: {exc}"
            ) from exc
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError, IndexError,
                TypeError, ValueError) as exc:
            raise IANoDisponible(
                "El servidor de IA ha devuelto una respuesta que no se puede "
                "interpretar"
            ) from exc

        if not isinstance(contenido, str):
            raise IANoDisponible(
                "El proveedor de IA ha devuelto un contenido que no es texto"
            )
        if not contenido.strip():
            raise IANoDisponible("El proveedor de IA ha devuelto una respuesta vacía")

        return Respuesta(
            texto=contenido,
            tokens_entrada=tokens_entrada,
            tokens_salida=tokens_salida,
            segundos=time.perf_counter() - inicio,
        )

    def _mensaje_conexion(self, exc: httpx.ConnectError) -> str:
        """Distingue un fallo de certificado de un fallo de red o de host."""
        texto = str(exc).upper()
        causa: BaseException | None = exc
        vistas: set[int] = set()
        while causa is not None and id(causa) not in vistas:
            vistas.add(id(causa))
            if isinstance(causa, ssl.SSLCertVerificationError):
                return self._mensaje_certificado()
            if isinstance(causa, ssl.SSLError):
                return (
                    "No se pudo establecer la conexión segura con el servidor "
                    f"de IA ({self.url}): {causa}"
                )
            causa = causa.__cause__ or causa.__context__

        if "CERTIFICATE_VERIFY_FAILED" in texto:
            return self._mensaje_certificado()

        return (
            f"No se puede conectar con el servidor de IA ({self.url}): "
            "conexión rechazada o sin red"
        )

    def _mensaje_certificado(self) -> str:
        """Mensaje cuando el certificado del servidor no encaja con el CA."""
        if self.ca:
            return (
                "El certificado del servidor de IA no es válido o no está "
                "firmado por el CA de CENTRO_IA_CA"
            )
        return "El certificado del servidor de IA no es válido"

    def _mensaje_estado(self, exc: httpx.HTTPStatusError) -> str:
        """Mensaje en español para cada código de estado interesante."""
        estado = exc.response.status_code
        if estado == 401:
            return (
                "El servidor de IA ha rechazado la clave (HTTP 401): "
                "revisa CENTRO_IA_KEY"
            )
        if estado == 429:
            return (
                "El servidor de IA ha recibido demasiadas peticiones "
                "(HTTP 429): inténtalo en unos minutos"
            )
        return f"El servidor de IA ha devuelto un error HTTP {estado}"

    def cerrar(self) -> None:
        """Cierra las conexiones del cliente HTTP."""
        self.cliente.close()

    def __enter__(self) -> ProveedorCentro:
        """Permite usar el proveedor con la instrucción «with»."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Cierra las conexiones al salir del bloque «with»."""
        self.cerrar()
