# mView VXF — contenedor superior, tamaño y CRC

## Estado confirmado

Formato observado y validado con **mView 1.39.02** sobre un proyecto real de
HMI **TK6043FH**.

El archivo completo comienza con:

```text
vxpm + zlib(...)
```

El payload descomprimido comienza con:

```text
VX-HMI, File Format
```

Dentro del payload existe un bloque superior de proyecto identificado por:

```text
uint32 LE marker = 0x10000004
uint32 LE size
byte[size-2] body
uint16 LE crc16_modbus(body)
```

**`size` incluye los 2 bytes del CRC final.**

## Bug de regresión confirmado — 2026-09-24

Se agregó un único indicador lógico a una escena. El objeto nuevo y su CRC local
eran correctos, pero el writer insertó 400 bytes sin reconstruir el contenedor
`0x10000004`.

Baseline funcional:

```text
project block size = 165798 (0x287A6)
project block CRC  = 0x2207
```

Después de agregar el objeto, el tamaño correcto era:

```text
project block size = 166198 (0x28936)
delta              = +400 bytes
project block CRC  = 0xC295
```

El archivo con el tamaño/CRC superiores viejos fue rechazado por mView con:

```text
HMI models are not supported, can't open!
```

El mensaje es engañoso: el modelo HMI no había cambiado. La causa era la
inconsistencia del contenedor superior.

Al corregir únicamente el size/CRC de `0x10000004`, manteniendo el resto del
cambio, el archivo abrió correctamente en mView.

## Regla obligatoria del writer

Nunca hacer:

```text
payload[:offset] + objeto_nuevo + payload[offset:]
```

y luego corregir solamente CRC/tamaño del objeto o de la escena.

Toda modificación de escenas/objetos debe trabajar sobre el **body** del bloque
`0x10000004` y finalmente pasar por:

```python
mutate_project_block(...)
```

de `vxf_core.py`.

Esa rutina recalcula en cascada la capa exterior que causó la regresión:

1. body modificado;
2. CRC16/MODBUS del bloque `0x10000004`;
3. tamaño del bloque, incluyendo su CRC;
4. recomposición del payload conservando prefijo y sufijo;
5. compresión zlib;
6. reapertura y validación antes de devolver/escribir el VXF.

## Fail closed

El writer rechaza el archivo si:

- no comienza con `vxpm`;
- zlib no descomprime;
- falta `VX-HMI, File Format`;
- no existe exactamente un marcador `0x10000004`;
- el tamaño sale fuera del payload;
- el CRC del bloque no coincide.

Una validación estructural no sustituye el gate final: **abrir el VXF generado en
mView** antes de usarlo como baseline.
