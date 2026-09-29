# mView-Tools

Toolchain experimental para generar y modificar archivos de HMI **mView** de Coolmay.

## Módulos

- `tag-generator/` — genera y valida archivos `.tag`.
- `scene-generator/` — lee, reconstruye y genera archivos de escenas `.sca`.
- `vxf-editor/` — modifica proyectos completos `.vxf` preservando su estructura y recalculando el contenedor superior.
- `specs/` — formato declarativo pensado como interfaz estable para IA.

## Principio de diseño

La capa inteligente decide **qué HMI construir**. La capa binaria decide **cómo serializarla correctamente**.

No mezclar ambas responsabilidades:

1. IA/documentación → especificación HMI.
2. Validación de esquema.
3. Compilador TAG → `.tag`.
4. Compilador de escenas → `.sca`.
5. Editor de proyecto → `.vxf`.
6. Validación estructural y round-trip.
7. Apertura y verificación en mView.

## Regla VXF crítica

Una modificación dentro de escenas/objetos no puede escribirse mediante un
simple splice del payload. El bloque superior `0x10000004` guarda su propio
**tamaño y CRC16/MODBUS**.

Todo cambio VXF de longitud variable debe pasar por
`vxf-editor/vxf_core.py::mutate_project_block()`, que recalcula esa capa antes
de recomprimir el proyecto.

Esta regla se agregó después de reproducir un fallo donde mView mostraba
`HMI models are not supported, can't open!` aunque el modelo HMI era correcto.

Ver:

- [`vxf-editor/README.md`](vxf-editor/README.md)
- [`vxf-editor/FORMAT_VXF.md`](vxf-editor/FORMAT_VXF.md)
