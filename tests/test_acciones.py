"""Pruebas de las acciones sobre el disco (acciones.py y motor.py).

Todo ocurre dentro de tmp_path con la fixture «descargas»: ninguna
prueba toca carpetas reales del proyecto. Las acciones destructivas se
ejecutan sobre esa carpeta temporal, nunca sobre una descarga real.
"""

from __future__ import annotations

import datetime

from lectucli.acciones import Estado, expandir_plantilla
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


def test_mover_real_crea_el_destino_y_mueve_todo(tmp_path, descargas) -> None:
    destino = tmp_path / "Leidos"
    motor = Motor([_accion("mover", "mover-lecturas", destino=str(destino))])

    resultados = motor.ejecutar("mover-lecturas", descargas, simular=False)

    assert [resultado.estado for resultado in resultados] == [Estado.HECHO] * 5
    assert destino.is_dir()
    assert (destino / "factura.pdf").is_file()
    assert (destino / "cumpleaños 2.png").is_file()
    assert list(descargas.iterdir()) == [], "la carpeta origen debe quedar vacía"


def test_mover_simulado_no_crea_la_carpeta_destino_ni_siquiera_mkdir(
    tmp_path, descargas
) -> None:
    destino = tmp_path / "NoDebeCrearse"
    motor = Motor([_accion("mover", "mover-lecturas", destino=str(destino))])

    resultados = motor.ejecutar("mover-lecturas", descargas, simular=True)

    assert [resultado.estado for resultado in resultados] == [Estado.SIMULADO] * 5
    assert not destino.exists(), "la simulación no debe crear la carpeta destino"
    assert sorted(entrada.name for entrada in tmp_path.iterdir()) == ["Descargas"]
    assert len(list(descargas.iterdir())) == 5, "la simulación no mueve nada"


def test_nunca_sobrescribe_y_usa_el_sufijo_uno(tmp_path, descargas) -> None:
    destino = tmp_path / "Leidos"
    destino.mkdir()
    (destino / "factura.pdf").write_text("factura original\n", encoding="utf-8")
    motor = Motor([_accion("mover", "mover-lecturas", destino=str(destino))])

    resultados = motor.ejecutar(
        "mover-lecturas", descargas, simular=False, ficheros=["factura.pdf"]
    )

    assert [resultado.estado for resultado in resultados] == [Estado.HECHO]
    assert (destino / "factura.pdf").read_text(encoding="utf-8") == (
        "factura original\n"
    ), "no se debe pisar el fichero que ya estaba"
    assert (destino / "factura (1).pdf").is_file()
    assert (destino / "factura (1).pdf").read_bytes().startswith(b"%PDF")
    assert not (descargas / "factura.pdf").exists()


def test_el_filtro_de_extensiones_detecta_la_jpg_en_mayusculas(tmp_path, descargas) -> None:
    destino = tmp_path / "Fotos"
    motor = Motor(
        [
            _accion(
                "mover",
                "mover-fotos",
                destino=str(destino),
                filtro={"extensiones": [".jpg"]},
            )
        ]
    )

    resultados = motor.ejecutar("mover-fotos", descargas, simular=True)

    assert [resultado.origen.name for resultado in resultados] == ["FOTO1.JPG"]


def test_borrar_solo_lo_viejo_deja_intactos_los_nuevos(descargas) -> None:
    motor = Motor(
        [_accion("borrar", "borrar-viejo", filtro={"mas_antiguo_que_dias": 30})]
    )

    resultados = motor.ejecutar(
        "borrar-viejo", descargas, simular=False, ficheros=["viejo.tmp"]
    )

    assert [resultado.estado for resultado in resultados] == [Estado.HECHO]
    assert not (descargas / "viejo.tmp").exists(), "el fichero de 40 días debe irse"
    assert (descargas / "factura.pdf").is_file()
    assert (descargas / "FOTO1.JPG").is_file()
    assert (descargas / "apuntes de redes.docx").is_file()


def test_borrar_no_toca_los_ficheros_que_no_cumplen_el_filtro(descargas) -> None:
    motor = Motor(
        [_accion("borrar", "borrar-viejo", filtro={"mas_antiguo_que_dias": 30})]
    )

    resultados = motor.ejecutar(
        "borrar-viejo", descargas, simular=False, ficheros=["factura.pdf"]
    )

    assert resultados == [], "factura.pdf es nuevo: no debe ni seleccionarse"
    assert (descargas / "factura.pdf").is_file()


def test_renombrar_aplica_la_plantilla_del_json(descargas) -> None:
    motor = Motor(
        [_accion("renombrar", "ren-numerado", plantilla="{n:03}-{nombre}{ext}")]
    )

    resultados = motor.ejecutar(
        "ren-numerado", descargas, simular=False, ficheros=["factura.pdf"]
    )

    assert [resultado.estado for resultado in resultados] == [Estado.HECHO]
    assert (descargas / "001-factura.pdf").is_file()
    assert not (descargas / "factura.pdf").exists()


def test_expandir_plantilla_sustituye_los_huecos_admitidos(tmp_path) -> None:
    fichero = tmp_path / "informe.txt"
    fichero.write_text("texto de prueba\n", encoding="utf-8")
    fecha = datetime.datetime.fromtimestamp(fichero.stat().st_mtime).strftime(
        "%Y-%m-%d"
    )

    assert expandir_plantilla("{nombre}{ext}", fichero, 1) == "informe.txt"
    assert expandir_plantilla("{n:03}-{nombre}", fichero, 7) == "007-informe"
    assert expandir_plantilla("{fecha:%Y-%m-%d}-{nombre}", fichero, 1) == (
        f"{fecha}-informe"
    )
