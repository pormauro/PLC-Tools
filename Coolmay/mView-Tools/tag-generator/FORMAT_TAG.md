# Formato binario mView `.tag`

Formato reconstruido a partir de archivos reales exportados por mView.

## Contenedor

```text
0..3   ASCII "vxtg"
4..N   zlib(payload)
```

Todos los enteros son little-endian.

## Payload

```text
uint32 version        = 0x10000006
uint32 payload_size   = len(payload) - 8
uint32 marker         = 0x00000100
uint32 group_count    = 1

QString group_name
uint32 tag_count

repeat tag_count:
    QString tag_name
    QString plc_address
    QString comment
    QString maximum
    QString minimum

uint16 crc16_modbus
```

## QString

```text
uint32 char_count_including_NUL
UTF-16LE(text + U+0000)
```

## CRC

CRC-16/MODBUS:

- polynomial reflected: `0xA001`
- init: `0xFFFF`
- data: `payload[8:-2]`
- stored as uint16 little-endian

## Implementación

La referencia es `mview_tag.py::build_tag_bytes()`.

El formato observado contiene cinco cadenas por tag. Los metadatos adicionales (tipo, acceso, origen IA, etc.) deben vivir en el spec/Excel o incorporarse al comentario.
