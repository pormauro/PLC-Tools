# mView Scene Generator

Parser, reconstrucción y generación de archivos de escenas `.sca` de mView.

## Estado

La estructura binaria se reconstruyó a partir de archivos reales exportados por mView. La herramienta recalcula en cascada:

1. CRC/tamaño de cada objeto;
2. CRC/tamaño de cada escena;
3. size/CRC global;
4. compresión zlib y magic `vxsa`.

## Componentes

- `sca_core.py` — parser/serializer canónico.
- `object_factory.py` — clonado y edición segura de objetos reales.
- `project_builder.py` — ejemplo de construcción de las pantallas de la estampadora.
- `app.py` — inspector/generador visual.
- `FORMAT_SCA.md` — documentación del formato.
- `test_core.py` — round-trip sobre un `.sca` real suministrado por el usuario.
- `templates/README.md` — cómo preparar plantillas de objetos.

## Uso

```bat
run.bat
```

Para generar el proyecto de ejemplo de la estampadora:

```bat
python project_builder.py proyecto_base.sca Estampadora_Escenas.sca
```

## Importante

El compilador binario es genérico. El catálogo actual de widgets todavía usa objetos clonados de un proyecto real de referencia. La evolución prevista es reemplazar referencias por índice con una biblioteca de firmas de widgets mView.

La IA futura debe producir un Scene Spec declarativo; este módulo será el compilador determinístico hacia `.sca`.
