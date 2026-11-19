"""Pruebas de la CLI (cli.py) con typer.testing.CliRunner.

Una prueba por código de salida: se comprueba el exit_code y una frase
corta de r.output. El CliRunner de typer mezcla stdout y stderr en
«output», así que también se le pueden leer los mensajes de error que
cli.py imprime en la consola roja.

Nada toca la red ni carpetas reales: la configuración se escribe con
escribir_config (tmp_path) y «aislado» ya borró las variables CENTRO_IA_*.
"""

from __future__ import annotations

from typer.testing import CliRunner

from lectucli.cli import app

ejecutar_cli = CliRunner()


def _config_de_ejemplo(tmp_path) -> dict:
    """Configuración mínima válida: una sola acción de mover."""
    return {
        "version": 1,
        "acciones": [
            {
                "nombre": "mover-lecturas",
                "descripcion": "Mueve las lecturas terminadas",
                "tipo": "mover",
                "destino": str(tmp_path / "Leidos"),
            }
        ],
    }


def test_ayuda_sale_con_codigo_cero(tmp_path) -> None:
    resultado = ejecutar_cli.invoke(app, ["--help"])

    assert resultado.exit_code == 0, resultado.output
    assert "Gestiona y organiza lecturas" in resultado.output


def test_accion_inexistente_sale_con_codigo_uno(tmp_path, escribir_config) -> None:
    ruta = escribir_config(_config_de_ejemplo(tmp_path))
    resultado = ejecutar_cli.invoke(
        app, ["--config", str(ruta), "ejecutar", "accion-que-no-existe"]
    )

    assert resultado.exit_code == 1, resultado.output
    assert "No existe la acción" in resultado.output


def test_opcion_inexistente_sale_con_codigo_dos() -> None:
    resultado = ejecutar_cli.invoke(app, ["listar", "--opcion-que-no-existe"])

    assert resultado.exit_code == 2, resultado.output
    assert "No such option" in resultado.output


def test_json_roto_sale_con_codigo_tres_sin_traza(escribir_config) -> None:
    ruta = escribir_config('{"version": 1, "acciones": [')
    resultado = ejecutar_cli.invoke(app, ["validar", "--ruta", str(ruta)])

    assert resultado.exit_code == 3, resultado.output
    assert "línea" in resultado.output, resultado.output
    assert "Traceback" not in resultado.output, (
        "un error de configuración no debe enseñar la traza"
    )


def test_ia_sin_clave_sale_con_codigo_cuatro_y_el_aviso(monkeypatch) -> None:
    # aislado borró CENTRO_IA_KEY: solo falta la clave (URL para que el
    # fallo sea exactamente «Falta configurar CENTRO_IA_KEY»).
    monkeypatch.setenv("CENTRO_IA_URL", "https://ia.example.edu/v1")

    resultado = ejecutar_cli.invoke(app, ["comprobar-ia"])

    assert resultado.exit_code == 4, resultado.output
    assert "siguen funcionando" in resultado.output, resultado.output
