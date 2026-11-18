"""Andamiaje común de las pruebas de lectucli.

Ninguna prueba toca las carpetas reales del proyecto ni habla con el
servidor de IA del centro:

- «aislado» (autouse) mueve el directorio actual y el directorio
  personal a un temporal nuevo, borra las variables CENTRO_IA_* y
  desactiva la lectura del .env real del proyecto.
- «sin_red» (autouse) bloquea cualquier conexión real: los dobles de IA
  (ProveedorFalso o httpx.MockTransport) no abren sockets, así que
  siguen funcionando.
- «descargas» fabrica una carpeta temporal de ejemplo con PDF, Word,
  fotos y un fichero con 40 días de antigüedad.
- «escribir_config» escribe un acciones.json dentro del temporal.
- «modelo_falso» devuelve un ProveedorFalso: el proveedor de IA de
  mentira que registra cada petición que recibiría el modelo.
"""

from __future__ import annotations

import json
import os
import pathlib
import socket
import time

import pytest

from lectucli.ia import ProveedorIA, Respuesta

# Texto que responde siempre el proveedor falso.
RESPUESTA_FALSA = "respuesta del modelo"


# ---------------------------------------------------------------------------
# Aislamiento de cada prueba
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def aislado(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Aísla cada prueba de las carpetas y la configuración reales.

    - El directorio actual pasa a ser tmp_path: las rutas relativas
      (./acciones.json, «listar .») caen siempre en el temporal.
    - HOME y USERPROFILE apuntan a tmp_path: expanduser(«~/…») nunca
      llega al directorio personal de verdad.
    - Se borran las variables del centro y load_dotenv() queda sin
      efecto: aunque una acción llame a desde_entorno(), no puede
      recuperar las credenciales del .env real.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.delenv("CENTRO_IA_URL", raising=False)
    monkeypatch.delenv("CENTRO_IA_KEY", raising=False)
    monkeypatch.delenv("CENTRO_IA_CA", raising=False)
    # load_dotenv() buscaría el .env del proyecto y volvería a poner las
    # variables que acabamos de borrar: se convierte en un no-op.
    monkeypatch.setattr("lectucli.ia.load_dotenv", lambda *args, **kwargs: False)
    return tmp_path


def _conexion_bloqueada(*args: object, **kwargs: object) -> None:
    raise AssertionError(
        "Las pruebas no pueden usar la red: simula el servidor con "
        "httpx.MockTransport o con ProveedorFalso."
    )


@pytest.fixture(autouse=True)
def sin_red(monkeypatch: pytest.MonkeyPatch) -> None:
    """Impide que una prueba abra una conexión real.

    Se corta la capa de socket (conexión y resolución de nombres), que
    es por donde pasan httpx, urllib y compañía: si alguna prueba llega
    a tocar la red, falla de forma ruidosa en lugar de llamar al
    servidor del centro. Un cliente httpx con httpx.MockTransport no
    abre sockets, así que los dobles de red siguen funcionando.
    """
    monkeypatch.setattr(socket.socket, "connect", _conexion_bloqueada)
    monkeypatch.setattr(socket, "getaddrinfo", _conexion_bloqueada)
    monkeypatch.setattr(socket, "create_connection", _conexion_bloqueada)


# ---------------------------------------------------------------------------
# Carpeta de descargas de ejemplo
# ---------------------------------------------------------------------------


def _escribir_pdf(ruta: pathlib.Path, texto: str) -> None:
    """Crea un PDF de una página con «texto» (en latin-1) legible.

    Se construye con pypdf (una página en blanco más un flujo de
    contenido con la fuente Helvetica, que es una de las 14 estándar y
    no hace falta incrustarla) para que leer_texto() extraiga el texto
    igual que lo haría con un PDF descargado de verdad.
    """
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    cuerpo = " ".join(texto.split())
    cuerpo = cuerpo.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    escritor = PdfWriter()
    pagina = escritor.add_blank_page(width=595, height=842)  # A4 en puntos
    pagina[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject(
                {
                    NameObject("/F1"): DictionaryObject(
                        {
                            NameObject("/Type"): NameObject("/Font"),
                            NameObject("/Subtype"): NameObject("/Type1"),
                            NameObject("/BaseFont"): NameObject("/Helvetica"),
                        }
                    )
                }
            )
        }
    )
    flujo = DecodedStreamObject()
    flujo.set_data(f"BT /F1 12 Tf 72 720 Td ({cuerpo}) Tj ET".encode("latin-1"))
    pagina[NameObject("/Contents")] = escritor._add_object(flujo)
    with ruta.open("wb") as archivo:
        escritor.write(archivo)


def _escribir_docx(ruta: pathlib.Path, texto: str) -> None:
    """Crea un documento Word con «texto» para poder leerlo con python-docx."""
    from docx import Document

    documento = Document()
    documento.add_paragraph(texto)
    documento.save(str(ruta))


@pytest.fixture
def descargas(tmp_path: pathlib.Path) -> pathlib.Path:
    """Carpeta temporal «Descargas» con ficheros de ejemplo.

    Contenido:

    - factura.pdf: PDF de una página con texto (se puede leer).
    - apuntes de redes.docx: documento Word con texto (se puede leer).
    - FOTO1.JPG y «cumpleaños 2.png»: binarios que no son documentos de
      texto; el primero además lleva la extensión en mayúsculas y el
      segundo, espacios y eñe en el nombre.
    - viejo.tmp: fichero con 40 días de antigüedad (para el filtro
      mas_antiguo_que_dias; se fija con os.utime).
    """
    carpeta = tmp_path / "Descargas"
    carpeta.mkdir()

    _escribir_pdf(carpeta / "factura.pdf", "Factura 42 del curso de redes.")
    _escribir_docx(carpeta / "apuntes de redes.docx", "Apuntes de redes: modelo TCP/IP.")
    (carpeta / "FOTO1.JPG").write_bytes(b"\xff\xd8\xff\xe0 foto de la clase")
    (carpeta / "cumpleaños 2.png").write_bytes(b"\x89PNG\r\n\x1a\nfoto de cumpleanos")

    viejo = carpeta / "viejo.tmp"
    viejo.write_text("fichero antiguo\n", encoding="utf-8")
    antiguo = time.time() - 40 * 86_400
    os.utime(viejo, (antiguo, antiguo))

    return carpeta


# ---------------------------------------------------------------------------
# Configuración de ejemplo
# ---------------------------------------------------------------------------


@pytest.fixture
def escribir_config(tmp_path: pathlib.Path):
    """Escribe un acciones.json en el temporal y devuelve su ruta.

    «datos» puede ser un objeto JSON (dict o lista) o texto crudo, para
    poder probar también ficheros rotos. El fichero se llama
    «acciones.json» salvo que se pida otro nombre.
    """

    def _escribir(
        datos: dict | list | str, nombre: str = "acciones.json"
    ) -> pathlib.Path:
        ruta = tmp_path / nombre
        if not isinstance(datos, str):
            datos = json.dumps(datos, ensure_ascii=False, indent=2)
        ruta.write_text(datos, encoding="utf-8")
        return ruta

    return _escribir


# ---------------------------------------------------------------------------
# Doble de IA
# ---------------------------------------------------------------------------


class ProveedorFalso(ProveedorIA):
    """Proveedor de IA de mentira: no toca la red y registra las peticiones.

    - «texto» es la respuesta que devuelve a cualquier pregunta.
    - «peticiones» guarda (sistema, usuario, max_tokens) en orden, para
      comprobar qué habría recibido el modelo (sistema fijo, documento
      entre <documento>…</documento>, max_tokens por subclase).
    - «fallo» es una excepción (p. ej. IANoDisponible) que lanza en
      lugar de responder, para simular un centro caído.
    """

    def __init__(self, texto: str = RESPUESTA_FALSA, fallo: Exception | None = None) -> None:
        self.texto = texto
        self.fallo = fallo
        self.peticiones: list[tuple[str, str, int]] = []

    def completar(self, sistema: str, usuario: str, max_tokens: int = 1000) -> Respuesta:
        self.peticiones.append((sistema, usuario, max_tokens))
        if self.fallo is not None:
            raise self.fallo
        # Los tokens no interesan en las pruebas: solo el texto.
        return Respuesta(texto=self.texto, tokens_entrada=0, tokens_salida=0, segundos=0.0)


@pytest.fixture
def modelo_falso() -> ProveedorFalso:
    """Doble de IA para las pruebas: responde siempre lo mismo y no red."""
    return ProveedorFalso()
