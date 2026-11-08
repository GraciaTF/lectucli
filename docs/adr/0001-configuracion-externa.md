# ADR-0001: Las acciones viven en acciones.json, no en el código

- Estado: aceptada
- Fecha: 2026-11-08
- Autor/a: Gracia Tortajada

## Contexto

Mi herramienta «lectucli» automatiza tareas repetitivas con ficheros que uso
para las lecturas en mis clases (añadir lecturas, clasificarlas por ciclos, 
añadirles etiquetas, filtrarlas, etc). 
Cada persona que la use tendrá carpetas y manías distintas, y yo mismo voy a querer
añadir acciones nuevas cada pocas semanas. Por ejemplo, quiero poder etiquetar las 
lecturas con palabras clave que se almacenarán en un índice y facilitarán la búsqueda.

## Decisión

Las acciones se describen en un fichero JSON externo (acciones.json) con
un esquema documentado en el README. El código solo contiene el MOTOR que
lee, valida y ejecuta ese fichero. Añadir una acción de un tipo ya
implementado = editar el JSON. Crear un tipo de acción nuevo = ampliar el código del motor.

## Alternativas consideradas

1. Escribir cada acción como una función en Python.
   - A favor: permite aprovechar toda la flexibilidad de Python y controlar con precisión lo que hace cada acción.
   - En contra: cada cambio exige tocar el código y volver a instalar; quien
     no programa no puede añadir acciones.
2. Usar YAML o TOML en vez de JSON.
   - A favor: YAML y TOML permiten escribir configuraciones de forma más cómoda y legible, especialmente cuando son largas.
   - En contra: JSON ya es suficiente para la estructura de nuestras acciones, es sencillo de validar y Python incluye soporte para trabajar con él sin instalar dependencias adicionales.
3. Guardar las acciones en una base de datos.
   - A favor: permitiría gestionar las acciones desde una interfaz y modificarlas sin editar archivos.
   - En contra: añadiría complejidad y dependencias innecesarias para una herramienta pequeña que puede funcionar con un fichero de configuración.

## Consecuencias

- Positivas: añadir una acción del tipo ya implementado no toca el código; el JSON se puede validar
  antes de ejecutar nada; de manera que puedo adaptar las acciones a mis carpetas y necesidades sin modificar el motor; puedo probarlas primero con --simular.
- Negativas: hay que mantener la validación al día cuando el esquema
  crezca; los errores de escritura en el JSON solo se ven al ejecutar
  validar; si quiero crear un tipo de acción completamente nuevo, tendré que añadir su implementación en Python.
- Qué haré si el esquema cambia: añadiré al JSON el campo "version". Si introduzco cambios incompatibles, actualizaré la validación y prepararé la adaptación de los ficheros de configuración existentes.