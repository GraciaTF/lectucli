# ADR-0002: La IA va detrás de una interfaz (ProveedorIA)

- Estado: aceptada
- Fecha: 2026-11-14
- Autor/a: MªGracia Tortajada

## Contexto

Mis acciones resumir, renombrar-ia y clasificar necesitan un modelo de
lenguaje. Hoy uso el servidor del centro (API de OpenAI, CENTRO_IA_URL),
pero en casa o el año que viene puede ser otro, y en las pruebas de la
semana 4 no quiero depender de la red. 
En mi caso, desarrollo y pruebo el proyecto desde casa y no tengo acceso a la URL ni a la clave del servidor del centro. Además, el modelo que utilizo en OpenCode no puedo reutilizarlo directamente desde lectucli.
Por eso necesito que el desarrollo y las pruebas puedan continuar sin depender de un servidor real ni de una conexión a Internet. También quiero poder cambiar de proveedor en el futuro sin tener que modificar las acciones que utilizan IA.

## Decisión

Toda llamada a un modelo pasa por la clase abstracta ProveedorIA, con un
único método completar(sistema, usuario).
ProveedorCentro implementa esa interfaz utilizando httpx para comunicarse con una API compatible con OpenAI.
Las acciones no saben qué servidor hay detrás ni cómo se realiza la conexión. Solo utilizan la interfaz común del proveedor.
El proveedor se crea de forma perezosa: únicamente cuando se ejecuta una acción que necesita IA y no está en modo simulación.

## Alternativas consideradas

1. Llamar a httpx directamente desde cada acción.
   - A favor: sería una solución sencilla al principio y no necesitaría una clase adicional para el proveedor.
   - En contra: cada acción tendría que gestionar las conexiones, las claves, los errores y las respuestas. Si cambiara el servidor, habría que modificar varias partes del programa. También sería más difícil probar las acciones sin conexión.
2. Usar la librería oficial de OpenAI (uv add openai).
   - A favor: proporciona una interfaz preparada para realizar peticiones a modelos de OpenAI y evita escribir parte del código de comunicación HTTP.
   - En contra: añade una dependencia y vincula la implementación a una librería concreta. Preferí utilizar httpx directamente para controlar la comunicación con la API compatible con OpenAI que utiliza el centro.
3. Utilizar directamente ProveedorCentro, sin una interfaz abstracta.
    - A favor: tendría menos clases y una implementación inicial más sencilla.
    - En contra: las acciones dependerían directamente del proveedor del centro. Si quisiera utilizar otro servidor o crear un proveedor falso para las pruebas, tendría que modificar más partes del programa.

## Consecuencias

- Positivas: cambiar de servidor es escribir otra subclase de ProveedorIA, sin modificar las acciones. Las pruebas pueden utilizar un proveedor falso, sin necesitar conexión a Internet ni consumir tokens. Las acciones no dependen de los detalles de comunicación con el servidor. El proveedor se crea únicamente cuando hace falta, por lo que las acciones que no utilizan IA siguen funcionando sin configuración. La simulación permite comprobar el presupuesto de caracteres sin contactar con ningún modelo.
- Negativas: Hay más clases y una capa adicional de abstracción que mantener. Para incorporar otro proveedor hay que implementar y probar una nueva subclase. La implementación actual de ProveedorCentro depende de que el servidor ofrezca una API compatible con OpenAI.
- La clave: La URL y la clave se guardan en un archivo .env de la carpeta de trabajo. El archivo .env está excluido del repositorio mediante .gitignore. La clave no se escribe directamente en el código, no se sube a Git ni se incluye en los mensajes de error. Así se evita publicar secretos y se puede utilizar una configuración diferente en cada entorno.
