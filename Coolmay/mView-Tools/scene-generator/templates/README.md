# Plantillas mView

El generador actual clona objetos reales exportados por mView para preservar propiedades internas que todavía no están completamente decodificadas.

## Recomendación

Crear un proyecto/archivo `.sca` de referencia con, al menos:

- botón de cambio de escena;
- botón volver;
- texto estático;
- display numérico;
- input numérico;
- botón momentáneo;
- indicador bit.

El `project_builder.py` incluido nació a partir de un proyecto viejo concreto y sirve como ejemplo de compilación. Para hacerlo universal, el próximo paso es construir un catálogo de widgets identificados por firma estructural y no por índice de escena/objeto.

No se versionan aquí archivos `.sca` privados por defecto. Los fixtures pueden agregarse explícitamente cuando se decida que son publicables.
