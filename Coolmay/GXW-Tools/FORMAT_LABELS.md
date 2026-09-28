# GX Works2 — tabla de labels/comentarios en `.gxw`

## Resultado sobre `estampadora.gxw`

La tabla que en este proyecto se usa como **labels legibles por dispositivo** (`B1`, `STATE`, `EV1_P1`, etc.) no está guardada en `label.xml` ni en los archivos de declaraciones `*.gh` / `*.Labels.lh`.

Está en el recurso lógico:

```text
COMMENT.qcd
```

En GX Works2 esta estructura corresponde a **Device Comments**. El CSV del proyecto la trata conceptualmente como una tabla de labels, pero conviene mantener la distinción:

- `COMMENT.qcd`: comentario/nombre visible asociado a un dispositivo físico o interno (`X0`, `M10`, `D0`, `T230`, ...).
- `Global1.gh`: declaraciones de Global Labels. En `estampadora.gxw` está vacío (sólo cabecera).
- `PROGRAMA.Labels.lh`: declaraciones Local Labels por POU. En `estampadora.gxw` también están vacías salvo cabecera/metadatos.
- `label.xml`: en esta baseline sólo contiene versión del esquema de labels; no contiene la tabla de nombres.

Por lo tanto, para esta máquina la tabla efectiva que hay que leer/escribir es `COMMENT.qcd`.

## Estructura observada de `COMMENT.qcd`

Baseline:

- tamaño: `4298` bytes;
- labels/comentarios activos: `133`;
- rangos compactos: `17`;
- timestamp guardado: `2026-09-21 15:54:13`;
- campo de longitud en `0x32`: `4248`, exactamente `filesize - 0x32`;
- marcador de tabla en `0x38`: `0x0A20`;
- cantidad de rangos en `0x3A` (`uint16 LE`);
- rangos desde `0x3C`.

### Range record

Cada rango ocupa 10 bytes:

```text
uint16 type_code
uint32 start_index
uint32 count
```

Tipos confirmados en esta baseline:

| type_code | dispositivo | regla de dirección |
|---:|---|---|
| `0x009C` | X | índice numérico; al mostrar se convierte a octal FX |
| `0x009D` | Y | índice numérico; al mostrar se convierte a octal FX |
| `0x0090` | M | decimal directo |
| `0x00A8` | D | decimal directo |
| `0x00C2` | T200+ | índice relativo a 200 (`0 -> T200`, `18 -> T218`) |

Ejemplo real:

```text
0x009C start=0 count=12  -> X0..X13 (numeración visible octal)
0x0090 start=50 count=6  -> M50..M55
0x00C2 start=30 count=21 -> T230..T250
0x00A8 start=140 count=8 -> D140..D147
```

Los 17 rangos suman exactamente 133 registros.

## Bloque de textos

Después del último rango hay un `uint32 0` y luego los textos en el mismo orden lógico que los rangos.

Cada texto se guarda como:

```text
uint32 char_count_including_nul
UTF-16LE text
uint16 NUL
```

Entre registros consecutivos hay además un `uint32 0`. El último registro termina directamente al final del archivo.

Ejemplo conceptual para `X0 -> B1`:

```text
03 00 00 00      # 3 UTF-16 code units: B, 1, NUL
42 00 31 00 00 00
00 00 00 00      # separador antes del próximo registro
```

## Mapeo confirmado con el CSV canónico

La secuencia binaria reconstruye exactamente las filas `USADO=SI` del archivo:

```text
docs/interno/plc/simplificado/v2_1/estampadora_labels_gx_v2.csv
```

Ejemplos verificados:

```text
X0   -> B1
X4   -> MODE_AUTO
M10  -> EVT_B1
M100 -> HMI_TECH_ENTER
T200 -> DB_B1
T218 -> B1_SINGLE_DELAY
T230 -> REF_P2_UP
D0   -> STATE
D138 -> CFG_VERSION
D147 -> CFG_T_AIR_SETTLE
```

`DESCRIPCION` del CSV **no aparece en `COMMENT.qcd`**. La descripción larga debe seguir siendo mantenida en el CSV/documentación canónica; el GXW conserva el nombre/comentario corto.

## Writer implementado

`gxw_tools/comments.py` implementa:

- parseo de `COMMENT.qcd`;
- reconstrucción determinística;
- conversión X/Y octal FX;
- base relativa T200 para `0xC2`;
- agrupación automática en rangos contiguos;
- UTF-16LE de longitud variable;
- actualización del campo de tamaño en `0x32`;
- import/export CSV compatible con `DISPOSITIVO,LABEL` y con el CSV canónico de la estampadora.

`GXWProject.replace_device_comments()` integra el writer al proyecto y actualiza:

1. `COMMENT.qcd`;
2. `iFileSize` correspondiente en `history.xml`;
3. `szMD5val = Base64(MD5(COMMENT.qcd))`;
4. `_hdb` y el CFB exterior;
5. validación completa posterior.

## Pruebas realizadas

### Round-trip sin cambios

```text
parse COMMENT.qcd
-> 133 registros / 17 rangos
-> serialize
-> bytes idénticos al original
```

Resultado: **PASS byte-identical**.

### Round-trip de proyecto completo desde CSV exportado

```text
GXW -> export-labels CSV -> replace-labels -> GXW
```

Resultado:

- `COMMENT.qcd`: byte-idéntico;
- 90/90 recursos lógicos: byte-idénticos;
- validación GXW: PASS.

### Texto de longitud diferente

Cambio de prueba:

```text
X0: B1 -> B1_TEST_LONG
```

Resultado:

- `COMMENT.qcd`: `4298 -> 4318` bytes;
- nuevo nombre vuelve a parsearse correctamente;
- tamaño/MD5 de `history.xml`: coherentes;
- otros 89 recursos lógicos: byte-idénticos;
- validación completa: **90/90 PASS**.

## CLI

Exportar tabla:

```powershell
python -m gxw_tools export-labels estampadora.gxw -o labels.csv
```

Reemplazar desde el CSV canónico o uno exportado:

```powershell
python -m gxw_tools replace-labels estampadora.gxw labels.csv -o estampadora_labels_mod.gxw
```

## Límite actual

La ingeniería inversa y el writer están cerrados offline para **Device Comments de esta familia/formato**. Todavía se requiere una prueba GUI en GX Works2 para afirmar compatibilidad de escritura nativa al agregar/eliminar rangos en proyectos distintos.

Los verdaderos Global/Local Labels (`*.gh`, `*.Labels.lh`) son una estructura diferente. En esta baseline están vacíos y no es necesario modificarlos para reproducir la tabla visible actual de la estampadora.
