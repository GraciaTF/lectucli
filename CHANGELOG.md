# Changelog

Todos los cambios notables de LectuCLI se recogen en este fichero.
El formato sigue [Keep a Changelog](https://keepachangelog.com/es/1.1.0/)
y las versiones siguen [SemVer](https://semver.org/lang/es/).

## [1.0.0] - 2026-11-19

Primera versión completa de LectuCLI: organiza, resume y clasifica las
lecturas de clase desde la terminal, con o sin inteligencia artificial.

### Añadido

- La orden `lectucli` con todas sus órdenes: `listar`, `ejecutar`, `validar`, `acciones`, `comprobar-ia` y `version`, con su propia ayuda (`--help`).
- El fichero `acciones.json`, donde la persona usuaria define sus propias reglas (qué carpeta, qué filtro, qué plantilla) sin tocar el código; su esquema está explicado en el README y en la carpeta `docs`.
- Acciones sobre carpetas: `mover`, `copiar`, `renombrar` y `borrar`, con filtros por extensión, expresión regular, antigüedad y tamaño.
- `--simular`: en la orden `ejecutar`, permite previsualizar las operaciones de una acción sin modificar los archivos del disco.
- Confirmación de seguridad: las acciones destructivas solicitan confirmación antes de ejecutarse. La opción `--si` permite omitirla y `--simular` permite previsualizar la operación sin modificar el disco.
- Ejemplos ya configurados: mover lecturas a Integración Social y a Educación Infantil, renombrar, borrar y clasificar lecturas.
- Protección contra sobrescrituras: si en el destino ya hay un fichero con ese nombre, el nuevo entra como «nombre (1)» y el original se queda intacto.
- Acciones con IA: `resumir` (guarda un `.resumen.md` junto a la lectura), `renombrar-ia` (propone un nombre claro y seguro) y `clasificar` (elige el ciclo y mueve la lectura a su carpeta).
- Clasificación segura: si la IA responde algo que no coincide con ninguna categoría, el fichero se mueve a `sin-clasificar` con el motivo en pantalla, en lugar de quedarse donde estaba.
- Configuración del centro de IA desde el `.env` (URL, clave, modelo y certificado), sin escribir credenciales en el código ni en el JSON.
- Uso sin IA garantizado: si falta la clave o el centro no responde, las acciones normales siguen funcionando y la CLI lo explica con un mensaje claro y su código de salida (0–4).
- Validación con `lectucli validar`: muestra todos los problemas de la configuración de una vez, no solo el primero.
- Documentación: README con el uso y el esquema de las reglas, guía de las acciones de IA, registro de los prompts y decisiones del proyecto (ADR) y plantilla para crear nuevas acciones.
- 81 pruebas automatizadas, más un workflow de GitHub Actions que las ejecuta en Linux, Windows y macOS en cada push y cada pull request.

### Cambiado

- La herramienta pasa a llamarse **LectuCLI** (antes `tareas`): la orden, los mensajes, el paquete y la documentación usan el nuevo nombre.
- El README y la guía de acciones se amplían para describir el proveedor de IA del centro, cómo configurarlo y las acciones que dependen de él.

### Arreglado

- Los mensajes de error ya no mencionan «tareas»: ahora hablan de «lectucli».
- Corregida la gestión de errores al ejecutar una acción: cada incidencia se muestra con su mensaje y su código de salida correspondientes.
- Corregida la versión de `astral-sh/setup-uv` en el workflow de pruebas, que hacía fallar la integración continua; las pruebas vuelven a pasar en los tres sistemas.
