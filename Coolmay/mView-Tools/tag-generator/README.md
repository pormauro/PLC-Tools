# mView Tag Generator

Generador/lector de archivos `.tag` de mView.

La rutina binaria canónica está en `mview_tag.py`. La GUI y Excel son capas de entrada/salida; el serializador no depende de ellas.

## Componentes

- `mview_tag.py` — parser, serializador, CRC y validación.
- `excel_reader.py` — lectura flexible de `.xlsx/.xlsm`.
- `app.py` — GUI Tkinter.
- `cli.py` — generación por consola.
- `FORMAT_TAG.md` — formato binario reconstruido.
- `test_core.py` — prueba de round-trip.

## Uso

```bat
run.bat
```

o:

```bat
python cli.py tags.xlsx salida.tag --sheet 11_TAG_EXPORT --group Estampadora
```

## API mínima

```python
from mview_tag import TagRecord, write_tag

write_tag(
    "estampadora.tag",
    [
        TagRecord("STATE", "D0", "Estado principal", "900", "0"),
        TagRecord("READY", "M10", "Listo", "1", "0"),
    ],
    group_name="Estampadora",
)
```

## Dirección futura con IA

La IA no debería fabricar el binario. Debe generar la sección `tags` del HMI Project Spec y este módulo la compila determinísticamente a `.tag`.
