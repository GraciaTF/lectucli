"""Pruebas de la capa de IA (ia.py) y de las acciones con IA.

Sin red y sin gastar un token: la red la corta la fixture «sin_red» de
conftest y las respuestas las da el doble «modelo_falso», que registra
cada llamada en «peticiones» (sistema, usuario, max_tokens).
"""

from __future__ import annotations

import httpx
import pytest

from lectucli.acciones import SISTEMA_RESUMIR, Estado, a_nombre_seguro
from lectucli.errores import IANoDisponible
from lectucli.ia import ProveedorCentro
from lectucli.motor import Motor


def _accion(tipo: str, nombre: str, **campos: object) -> dict:
    """Definición mínima de una acción para el motor."""
    accion: dict = {
        "nombre": nombre,
        "descripcion": f"Acción de prueba «{nombre}»",
        "tipo": tipo,
    }
    accion.update(campos)
    return accion


# ---------------------------------------------------------------------------
# a_nombre_seguro: la respuesta del modelo convertida en nombre de fichero
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "respuesta, esperado",
    [
        pytest.param(
            "Tema 3: ¡Linux & Bash!",
            "tema-3-linux-bash",
            id="tildes-y-signos",
        ),
        pytest.param(
            "../../etc/passwd",
            "etc-passwd",
            id="intento-de-salir-de-la-carpeta",
        ),
        pytest.param(
            "Relacion de fuentes.pdf",
            "relacion-de-fuentes",
            id="el-modelo-anade-la-extension-pdf",
        ),
        pytest.param(
            "",
            "",
            id="respuesta-vacia",
        ),
    ],
)
def test_a_nombre_seguro_deja_un_nombre_limpio(respuesta: str, esperado: str) -> None:
    assert a_nombre_seguro(respuesta) == esperado


# ---------------------------------------------------------------------------
# resumir con el doble de IA
# ---------------------------------------------------------------------------


def test_resumir_escribe_el_resumen_y_envuelve_el_documento_en_etiquetas(
    descargas, modelo_falso
) -> None:
    motor = Motor(
        [_accion("resumir", "resumir-lecturas")],
        proveedor=lambda: modelo_falso,
    )

    resultados = motor.ejecutar(
        "resumir-lecturas", descargas, simular=False, ficheros=["factura.pdf"]
    )

    assert [resultado.estado for resultado in resultados] == [Estado.HECHO]
    resumen = descargas / "factura.resumen.md"
    assert resumen.is_file(), "resumir debe guardar el .resumen.md junto al original"
    assert resumen.read_text(encoding="utf-8") == modelo_falso.texto

    assert len(modelo_falso.peticiones) == 1
    sistema, usuario, max_tokens = modelo_falso.peticiones[0]
    assert sistema == SISTEMA_RESUMIR, "las instrucciones se añaden al sistema fijo"
    assert usuario.startswith("<documento>\n")
    assert usuario.endswith("</documento>")
    assert "Factura 42" in usuario, "el documento debe ir dentro de las etiquetas"
    assert max_tokens == 1000, "resumir pide 1000 tokens de respuesta"


def test_simular_no_pregunta_al_modelo_ni_escribe_nada(descargas, modelo_falso) -> None:
    motor = Motor(
        [_accion("resumir", "resumir-lecturas")],
        proveedor=lambda: modelo_falso,
    )

    resultados = motor.ejecutar(
        "resumir-lecturas", descargas, simular=True, ficheros=["factura.pdf"]
    )

    assert [resultado.estado for resultado in resultados] == [Estado.SIMULADO]
    assert modelo_falso.peticiones == [], "la simulación no debe gastar un token"
    assert resultados[0].detalle.startswith("presupuesto:")
    assert not (descargas / "factura.resumen.md").exists(), (
        "ni siquiera en simulación se escribe el .resumen.md"
    )


# ---------------------------------------------------------------------------
# clasificar
# ---------------------------------------------------------------------------


def test_categoria_que_no_esta_en_la_lista_va_a_sin_clasificar(
    tmp_path, descargas, modelo_falso
) -> None:
    """Consigna: si la IA propone una categoría que no está en la lista,
    el fichero acaba en la carpeta «sin-clasificar»."""
    modelo_falso.texto = "inventada"  # respuesta fuera del mapa del JSON
    carpeta_sin_clasificar = tmp_path / "sin-clasificar"
    motor = Motor(
        [
            _accion(
                "clasificar",
                "clasificar-lecturas",
                categorias={
                    "leido": str(tmp_path / "Leidos"),
                    "sin-clasificar": str(carpeta_sin_clasificar),
                },
            )
        ],
        proveedor=lambda: modelo_falso,
    )

    resultados = motor.ejecutar(
        "clasificar-lecturas", descargas, simular=False, ficheros=["factura.pdf"]
    )

    assert (carpeta_sin_clasificar / "factura.pdf").is_file(), (
        "la consigna dice que una categoría fuera de la lista va a "
        f"sin-clasificar; en su lugar salió: {resultados}"
    )
    assert not (descargas / "factura.pdf").exists(), "debe salir de la carpeta origen"
    assert [resultado.estado for resultado in resultados] == [Estado.HECHO]
    assert "inventada" in resultados[0].detalle, (
        "el detalle debe explicar qué respondió la IA: "
        f"{resultados[0].detalle!r}"
    )


def test_sin_clasificar_no_sobrescribe_un_fichero_que_ya_esta(
    tmp_path, descargas, modelo_falso
) -> None:
    """Si en «sin-clasificar» ya hay un fichero con el mismo nombre, el
    original se conserva y el nuevo entra con el sufijo «(1)»."""
    modelo_falso.texto = "inventada"
    carpeta_sin_clasificar = tmp_path / "sin-clasificar"
    carpeta_sin_clasificar.mkdir()
    (carpeta_sin_clasificar / "factura.pdf").write_text(
        "factura que ya estaba\n", encoding="utf-8"
    )
    motor = Motor(
        [
            _accion(
                "clasificar",
                "clasificar-lecturas",
                categorias={
                    "leido": str(tmp_path / "Leidos"),
                    "sin-clasificar": str(carpeta_sin_clasificar),
                },
            )
        ],
        proveedor=lambda: modelo_falso,
    )

    resultados = motor.ejecutar(
        "clasificar-lecturas", descargas, simular=False, ficheros=["factura.pdf"]
    )

    assert [resultado.estado for resultado in resultados] == [Estado.HECHO]
    assert (carpeta_sin_clasificar / "factura.pdf").read_text(encoding="utf-8") == (
        "factura que ya estaba\n"
    ), "nunca se debe pisar el fichero que ya estaba"
    assert (carpeta_sin_clasificar / "factura (1).pdf").is_file()
    assert not (descargas / "factura.pdf").exists()


def test_clasificar_simulado_no_crea_sin_clasificar_ni_pregunta_al_modelo(
    tmp_path, descargas, modelo_falso
) -> None:
    """--simular no toca nada: ni carpetas, ni ficheros, ni tokens."""
    modelo_falso.texto = "inventada"
    categorias = {
        "leido": str(tmp_path / "Leidos"),
        "sin-clasificar": str(tmp_path / "sin-clasificar"),
    }
    motor = Motor(
        [_accion("clasificar", "clasificar-lecturas", categorias=categorias)],
        proveedor=lambda: modelo_falso,
    )

    resultados = motor.ejecutar(
        "clasificar-lecturas", descargas, simular=True, ficheros=["factura.pdf"]
    )

    assert [resultado.estado for resultado in resultados] == [Estado.SIMULADO]
    assert modelo_falso.peticiones == [], "la simulación no debe gastar un token"
    assert not (tmp_path / "sin-clasificar").exists(), (
        "la simulación no debe crear ni siquiera la carpeta sin-clasificar"
    )
    assert not (tmp_path / "Leidos").exists()
    assert (descargas / "factura.pdf").is_file(), "no se debe mover nada"


def test_sin_clasificar_sin_clave_en_el_json_usa_una_subcarpeta_del_origen(
    descargas, modelo_falso
) -> None:
    """Si el mapa no declara «sin-clasificar» (como el acciones.json real),
    el rescate va a una subcarpeta junto al propio fichero."""
    modelo_falso.texto = "inventada"
    motor = Motor(
        [
            _accion(
                "clasificar",
                "clasificar-lecturas",
                categorias={"leido": str(descargas.parent / "Leidos")},
            )
        ],
        proveedor=lambda: modelo_falso,
    )

    resultados = motor.ejecutar(
        "clasificar-lecturas", descargas, simular=False, ficheros=["factura.pdf"]
    )

    assert [resultado.estado for resultado in resultados] == [Estado.HECHO]
    assert (descargas / "sin-clasificar" / "factura.pdf").is_file(), resultados
    assert not (descargas / "factura.pdf").exists()


# ---------------------------------------------------------------------------
# ProveedorCentro: fallos de configuración y de conexión
# ---------------------------------------------------------------------------


def test_sin_clave_del_centro_lanza_ianodisponible(monkeypatch) -> None:
    # aislado ya borró CENTRO_IA_KEY (y URL y CA); solo dejamos la URL
    # para que el fallo sea exactamente la clave que falta.
    monkeypatch.setenv("CENTRO_IA_URL", "https://ia.example.edu/v1")

    with pytest.raises(IANoDisponible, match="CENTRO_IA_KEY"):
        ProveedorCentro.desde_entorno()


def test_url_del_centro_inalcanzable_lanza_ianodisponible() -> None:
    # El puerto 9 (discard) no escucha nada: en lugar de abrir un socket
    # real (la fixture sin_red lo impediría), el cliente se sustituye por
    # uno con httpx.MockTransport que devuelve «conexión rechazada».
    proveedor = ProveedorCentro("http://127.0.0.1:9/v1", "clave", "modelo")
    proveedor.cliente.close()  # el cliente real no llegó a conectarse

    def _conexion_rechazada(solicitud: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=solicitud)

    proveedor.cliente = httpx.Client(
        transport=httpx.MockTransport(_conexion_rechazada)
    )
    try:
        with pytest.raises(IANoDisponible) as captura:
            proveedor.completar("sistema", "usuario")
    finally:
        proveedor.cliente.close()

    mensaje = str(captura.value)
    assert "No se puede conectar" in mensaje, mensaje
    assert "127.0.0.1:9" in mensaje, mensaje
