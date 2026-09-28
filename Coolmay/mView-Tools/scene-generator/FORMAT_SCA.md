# Formato `.sca` mView

Ingeniería inversa validada sobre archivos reales.

## Contenedor

```text
"vxsa" + zlib(payload)
```

## Payload global

- `uint32 version`
- `uint32 global_size = len(payload)-8`
- cabecera original hasta offset 32
- `QString group_name`
- 10 bytes de metadata del grupo
- `uint32 scene_count`
- escenas
- `uint16 CRC16/MODBUS global`

CRC global:

```python
crc16_modbus(payload[8:-2])
```

## Escena

```text
QString scene_name
34 bytes scene_metadata
uint32 scene_block_size
scene_block
```

## scene_block

```text
uint32 object_count

repeat object_count:
    uint16 header_a
    uint16 header_b
    uint32 object_payload_size
    object_payload

uint16 scene_crc
```

CRC de escena:

```python
crc16_modbus(scene_block[:-2])
```

## Objeto

`object_payload_size` incluye los 2 bytes de CRC:

```text
object_body
uint16 object_crc
```

CRC:

```python
crc16_modbus(object_body)
```

## QString

```text
uint32 char_count_including_NUL
UTF-16LE(text + NUL)
```

## Rectángulo observado

En los objetos estudiados:

```text
offset 4   int32 left
offset 8   int32 top
offset 12  int32 right
offset 16  int32 bottom
```

## Tipos observados por (header_a, header_b)

- `(9,0)` Static Text
- `(1,1)` Numeric Display
- `(2,3)` Numeric Input / Display editable
- `(0,1)` Bit Indicator
- `(0,3)` Bit Button / Switch
- `(1,2)` Scene Change Button
- `(3,0)` objeto gráfico/fondo observado

Los nombres son inferidos por el uso en proyectos reales.

## Hallazgo crítico

Modificar QString y recalcular sólo el CRC global rompe el stream. Hay que recalcular todos los niveles: objeto → escena → archivo. Eso es lo que implementa `sca_core.py`.
