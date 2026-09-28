# mView VXF Editor

Editor/inspector de proyectos completos `.vxf` de **mView 1.39.02**.

El `.vxf` original se usa como plantilla canónica. Las herramientas deben
preservar modelo HMI, comunicaciones, macros, recursos y secciones no
interpretadas, modificando únicamente el contenido requerido.

## Regla crítica de escritura

Las escenas viven dentro de un contenedor superior marcado `0x10000004`.

Cualquier cambio de longitud dentro de escenas/objetos obliga a reconstruir
también:

- el `size` de `0x10000004`;
- el CRC16/MODBUS final de `0x10000004`.

**No alcanza con recalcular el CRC del objeto o de la escena.**

El error ya fue reproducido y confirmado en mView: un VXF con objeto válido pero
con size/CRC superior stale muestra el mensaje engañoso:

```text
HMI models are not supported, can't open!
```

La corrección validada fue recalcular únicamente esa capa exterior. Ver
[`FORMAT_VXF.md`](FORMAT_VXF.md).

## API segura

`vxf_core.py` expone:

- `parse_vxf()`
- `validate_vxf()`
- `mutate_project_block()`
- `write_mutated_vxf()`

Para cualquier editor de escenas, usar obligatoriamente:

```python
from vxf_core import mutate_project_block

result = mutate_project_block(original_vxf, mutate_scene_body)
```

El callback recibe el body sin CRC. El core reconstruye size + CRC + zlib y
vuelve a validar el archivo emitido.

## Validación rápida

```powershell
python mView-Tools/vxf-editor/vxf_core.py proyecto.vxf
python -m unittest mView-Tools/vxf-editor/test_vxf.py
```

## Evidencia de regresión

El test cubre explícitamente:

- edición que agrega 400 bytes;
- actualización automática del size superior;
- actualización automática del CRC superior;
- preservación del sufijo no modificado;
- rechazo de CRC stale;
- rechazo de splice de longitud variable con size stale;
- round-trip sin cambios.

## Gate final

El parser valida estructura binaria, pero la compatibilidad práctica se cierra
abriendo el archivo generado en mView. Un archivo no se considera baseline sólo
porque pase los tests offline.
