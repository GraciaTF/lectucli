"""Pruebas de lectucli.config: casos feos de cargar() y validar().

Ninguna prueba toca el acciones.json real del proyecto: escribir_config
escribe siempre dentro de tmp_path.
"""

from __future__ import annotations

import pytest

from lectucli import config
from lectucli.errores import AccionNoValida, ConfigError


def _accion(sin: str | None = None, **cambios: object) -> dict:
    """Acción mínima que pasa la validación.

    Los cambios se aplican encima del valor por defecto y «sin» elimina
    un campo, para poder probar también las acciones a las que les falta
    algo obligatorio.
    """
    accion: dict = {
        "nombre": "mover-lecturas",
        "descripcion": "Mueve las lecturas terminadas",
        "tipo": "mover",
        "destino": "~/Leidos",
    }
    accion.update(cambios)
    if sin is not None:
        accion.pop(sin, None)
    return accion


def _config_de_todos_los_tipos() -> list[dict]:
    """Una acción de cada tipo, todas correctas."""
    return [
        _accion(),
        _accion(nombre="copiar-lecturas", tipo="copiar", destino="~/Copia"),
        _accion(
            nombre="ren-numerado",
            tipo="renombrar",
            sin="destino",
            plantilla="{n:03}-{nombre}{ext}",
        ),
        _accion(nombre="borrar-basura", tipo="borrar", sin="destino"),
        _accion(
            nombre="resumir-txt",
            tipo="resumir",
            sin="destino",
            instrucciones="Resume en cinco lineas.",
            max_caracteres=2000,
        ),
        _accion(
            nombre="renombrar-pdf",
            tipo="renombrar-ia",
            sin="destino",
            instrucciones="Propón un nombre de dos palabras.",
        ),
        _accion(
            nombre="clasificar-lecturas",
            tipo="clasificar",
            sin="destino",
            categorias={"leido": "Leidos", "pendiente": "Pendientes"},
        ),
    ]


# ---------------------------------------------------------------------------
# cargar(): el fichero en sí
# ---------------------------------------------------------------------------


def test_cargar_devuelve_la_lista_de_acciones(escribir_config) -> None:
    datos = {"version": 1, "acciones": _config_de_todos_los_tipos()}
    ruta = escribir_config(datos)
    assert config.cargar(ruta) == datos["acciones"]


@pytest.mark.parametrize(
    "contenido, motivo",
    [
        pytest.param(
            "[1, 2]", "debe ser un objeto JSON", id="raiz-que-no-es-un-objeto"
        ),
        pytest.param(
            '"hola"', "debe ser un objeto JSON", id="raiz-que-es-un-texto"
        ),
        pytest.param(
            '{"acciones": []}',
            "no contiene el campo «version»",
            id="sin-campo-version",
        ),
        pytest.param(
            '{"version": 2, "acciones": []}',
            "debe valer 1",
            id="version-dos",
        ),
        pytest.param(
            '{"version": true, "acciones": []}',
            "debe valer 1",
            id="version-booleana-en-vez-de-uno",
        ),
        pytest.param(
            '{"version": "1", "acciones": []}',
            "debe valer 1",
            id="version-escrita-como-texto",
        ),
        pytest.param(
            '{"version": 1}',
            "no contiene el campo «acciones»",
            id="sin-campo-acciones",
        ),
        pytest.param(
            '{"version": 1, "acciones": []}',
            "Falta la lista «acciones» o está vacía",
            id="lista-de-acciones-vacia",
        ),
        pytest.param(
            '{"version": 1, "acciones": {}}',
            "Falta la lista «acciones» o está vacía",
            id="acciones-que-no-es-una-lista",
        ),
        pytest.param(
            '{"version": 1,\n  "acciones": [',
            r"línea \d+, columna \d+",
            id="json-roto-dice-linea-y-columna",
        ),
    ],
)
def test_cargar_rechaza_un_fichero_invalido(
    escribir_config, contenido: str, motivo: str
) -> None:
    ruta = escribir_config(contenido)
    with pytest.raises(ConfigError, match=motivo):
        config.cargar(ruta)


def test_cargar_falla_si_no_existe_el_fichero(tmp_path) -> None:
    with pytest.raises(ConfigError, match="No existe el fichero"):
        config.cargar(tmp_path / "no-existe.json")


def test_cargar_falla_si_el_fichero_no_esta_en_utf8(tmp_path) -> None:
    ruta = tmp_path / "acciones.json"
    ruta.write_bytes(b'{"version": 1, "acciones": []}\xff\xfe')
    with pytest.raises(ConfigError, match="no está codificado en UTF-8"):
        config.cargar(ruta)


# ---------------------------------------------------------------------------
# validar(): campos con valores prohibidos o imposibles
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "accion, campo, motivo",
    [
        pytest.param(
            _accion(nombre="Mover Lecturas"),
            "nombre",
            "solo admite minúsculas",
            id="nombre-con-mayusculas-y-espacios",
        ),
        pytest.param(
            _accion(nombre="mover-"),
            "nombre",
            "sin guiones al principio o al final",
            id="nombre-que-termina-en-guion",
        ),
        pytest.param(
            _accion(nombre=""),
            "nombre",
            "no puede estar vacío",
            id="nombre-vacio",
        ),
        pytest.param(
            _accion(descripcion="   "),
            "descripcion",
            "es obligatoria",
            id="descripcion-en-blanco",
        ),
        pytest.param(
            _accion(tipo="teletransportar"),
            "tipo",
            "no está admitido",
            id="tipo-que-no-existe",
        ),
        pytest.param(
            _accion(sin="destino"),
            "destino",
            "es obligatorio",
            id="mover-sin-destino",
        ),
        pytest.param(
            _accion(tipo="copiar", sin="destino"),
            "destino",
            "es obligatorio",
            id="copiar-sin-destino",
        ),
        pytest.param(
            _accion(destino="   "),
            "destino",
            "no vacía",
            id="destino-en-blanco",
        ),
        pytest.param(
            _accion(tipo="renombrar"),
            "plantilla",
            "es obligatoria",
            id="renombrar-sin-plantilla",
        ),
        pytest.param(
            _accion(tipo="renombrar", plantilla=" "),
            "plantilla",
            "debe ser un texto",
            id="plantilla-en-blanco",
        ),
        pytest.param(
            _accion(tipo="renombrar", plantilla="informe-{ruta}.pdf"),
            "plantilla",
            "no está admitido",
            id="plantilla-con-hueco-desconocido",
        ),
        pytest.param(
            _accion(tipo="renombrar", plantilla="{nombre"),
            "plantilla",
            "llaves sin cerrar",
            id="plantilla-con-llaves-sin-cerrar",
        ),
        pytest.param(
            _accion(tipo="renombrar-ia", destino="~/Escaneos"),
            "destino",
            "no aplica",
            id="destino-prohibido-en-renombrar-ia",
        ),
        pytest.param(
            _accion(tipo="renombrar-ia", sin="destino", plantilla="{nombre}{ext}"),
            "plantilla",
            "no aplica",
            id="plantilla-prohibida-en-renombrar-ia",
        ),
        pytest.param(
            _accion(instrucciones="Resume en tres lineas."),
            "instrucciones",
            "solo aplica a los tipos de IA",
            id="instrucciones-en-un-tipo-normal",
        ),
        pytest.param(
            _accion(max_caracteres=8000),
            "max_caracteres",
            "solo aplica a los tipos de IA",
            id="max-caracteres-en-un-tipo-normal",
        ),
        pytest.param(
            _accion(tipo="resumir", instrucciones=None),
            "instrucciones",
            "debe ser un texto no vacío",
            id="instrucciones-nulas-en-resumir",
        ),
        pytest.param(
            _accion(tipo="resumir", instrucciones="   "),
            "instrucciones",
            "debe ser un texto no vacío",
            id="instrucciones-en-blanco-en-resumir",
        ),
        pytest.param(
            _accion(tipo="resumir", max_caracteres=True),
            "max_caracteres",
            "debe ser un número entero",
            id="max-caracteres-booleano",
        ),
        pytest.param(
            _accion(tipo="resumir", max_caracteres=499),
            "max_caracteres",
            "debe estar entre 500 y 50000",
            id="max-caracteres-demasiado-bajo",
        ),
        pytest.param(
            _accion(tipo="resumir", max_caracteres=50001),
            "max_caracteres",
            "debe estar entre 500 y 50000",
            id="max-caracteres-demasiado-alto",
        ),
        pytest.param(
            _accion(tipo="clasificar", sin="destino"),
            "categorias",
            "es obligatoria",
            id="clasificar-sin-categorias",
        ),
        pytest.param(
            _accion(
                tipo="clasificar",
                sin="destino",
                categorias={"Mala Clave": "Leidos"},
            ),
            "categorias.Mala Clave",
            "identificador",
            id="categoria-con-clave-imposible",
        ),
        pytest.param(
            _accion(categorias={"leido": "Leidos"}),
            "categorias",
            "solo aplica",
            id="categorias-en-un-tipo-normal",
        ),
        pytest.param(
            _accion(confirmar=None),
            "confirmar",
            "booleano",
            id="confirmar-nulo",
        ),
        pytest.param(
            _accion(confirmar="si"),
            "confirmar",
            "booleano",
            id="confirmar-escrito-como-texto",
        ),
        pytest.param(
            _accion(origen="   "),
            "origen",
            "no vacía",
            id="origen-en-blanco",
        ),
        pytest.param(
            _accion(filtro="pdf"),
            "filtro",
            "debe ser un objeto",
            id="filtro-que-no-es-un-objeto",
        ),
        pytest.param(
            _accion(filtro={"extensiones": []}),
            "filtro.extensiones",
            "al menos una",
            id="filtro-sin-extensiones",
        ),
        pytest.param(
            _accion(filtro={"extensiones": ["pdf"]}),
            "filtro.extensiones",
            "debe empezar por punto",
            id="extension-sin-punto",
        ),
        pytest.param(
            _accion(filtro={"extensiones": [".PDF"]}),
            "filtro.extensiones",
            "en minúsculas",
            id="extension-en-mayusculas",
        ),
        pytest.param(
            _accion(filtro={"patron": "[sin cerrar"}),
            "filtro.patron",
            "no es válida",
            id="patron-que-no-compila",
        ),
        pytest.param(
            _accion(filtro={"mas_antiguo_que_dias": 0}),
            "filtro.mas_antiguo_que_dias",
            "se ha encontrado «0»",
            id="filtro-de-dias-a-cero",
        ),
        pytest.param(
            _accion(filtro={"mas_antiguo_que_dias": True}),
            "filtro.mas_antiguo_que_dias",
            "debe ser un número entero mayor que cero",
            id="filtro-de-dias-booleano",
        ),
        pytest.param(
            _accion(filtro={"mayor_que_mb": 0}),
            "filtro.mayor_que_mb",
            "se ha encontrado «0»",
            id="filtro-de-megas-a-cero",
        ),
        pytest.param(
            _accion(filtro={"mayor_que_mb": True}),
            "filtro.mayor_que_mb",
            "debe ser un número mayor que cero",
            id="filtro-de-megas-booleano",
        ),
        pytest.param(
            _accion(filtro={"mayor_que_mb": float("nan")}),
            "filtro.mayor_que_mb",
            "finito",
            id="filtro-de-megas-nan",
        ),
    ],
)
def test_validar_detecta_el_campo_malo(accion: dict, campo: str, motivo: str) -> None:
    errores = config.validar([accion])
    assert any(
        error.campo == campo and motivo in error.motivo for error in errores
    ), f"esperaba un error en «{campo}» con «{motivo}» y salió: {errores}"


def test_validar_devuelve_todos_los_errores_de_una_accion() -> None:
    accion = _accion(nombre="Malo", descripcion="", tipo="teletransportar")
    errores = config.validar([accion])
    assert {error.campo for error in errores} >= {"nombre", "descripcion", "tipo"}
    assert all(isinstance(error, AccionNoValida) for error in errores)


def test_validar_detecta_nombres_repetidos() -> None:
    errores = config.validar([_accion(), _accion()])
    assert any(
        error.campo == "nombre" and "repetido" in error.motivo for error in errores
    ), errores


def test_validar_acumula_errores_de_varias_acciones() -> None:
    primera = {"descripcion": "Sin nombre y con tipo imposible", "tipo": "otra-vez"}
    segunda = {"descripcion": "Otra sin nombre", "tipo": "nada"}
    errores = config.validar([primera, segunda])
    assert {"#1", "#2"} <= {error.accion for error in errores}, errores


def test_validar_acepta_una_configuracion_de_todos_los_tipos() -> None:
    assert config.validar(_config_de_todos_los_tipos()) == []


def test_instrucciones_nulas_en_un_tipo_normal_no_son_un_error() -> None:
    # En un tipo sin IA, «instrucciones: null» es un campo ausente de
    # facto: solo el valor no nulo es un error (lo comprueba el caso
    # «instrucciones-en-un-tipo-normal» de arriba).
    assert config.validar([_accion(instrucciones=None)]) == []


def test_max_caracteres_nulo_en_un_tipo_de_ia_no_es_un_error() -> None:
    # null significa «usa el valor por defecto» (12000), no un error.
    assert config.validar([_accion(tipo="resumir", max_caracteres=None)]) == []
