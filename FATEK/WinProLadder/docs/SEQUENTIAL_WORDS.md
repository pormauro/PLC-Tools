# Sequential words — confirmed map

Estado: **mapa incremental basado en fixtures controlados, LDR importado y guardados canónicos de WinProLadder**.

## X / Y mínimos

| Forma | Word observado |
|---|---:|
| ORG X0 | 0x0040 |
| ORG X1 | 0x0140 |
| ORG X2 | 0x0240 |
| ORG NOT X0 | 0x0050 |
| OUT Y0 | 0x00C1 |
| OUT Y1 | 0x01C1 |
| OUT Y2 | 0x02C1 |

Para X/Y observados:

    word = (device_index << 8) | low_opcode

Writer externo validado en WinProLadder hasta índice 2.

## Hallazgos del fixture varios

### Branch N000

    0140 00A1 0090 00C1

| Word | Instrucción |
|---:|---|
| 0x0140 | ORG X1 |
| 0x00A1 | OR Y0 |
| 0x0090 | AND NOT X0 |
| 0x00C1 | OUT Y0 |

### M

N001:

    1048 11C8 12D8

corresponde a:

    ORG M0
    OUT M1
    OUT NOT M2

Para los M observados, el byte alto es `0x10 + M_index`.

| low byte | instrucción M |
|---:|---|
| 0x48 | ORG M |
| 0x58 | ORG NOT M |
| 0xC8 | OUT M |
| 0xD8 | OUT NOT M |

### SET / RST normal y P

| Forma | function word | operand word |
|---|---:|---:|
| SET M4 | 0x82FC | 0x1408 |
| SET P M6 | 0x82F8 | 0x1608 |
| RST M4 | 0xC4FC | 0x1408 |
| RST P M6 | 0xC4F8 | 0x1608 |

- SET vs RST: `0x82..` vs `0xC4..`
- normal vs P: `FC` vs `F8`
- operand M observado: `0x(0x10+index)08`

### Diferencial / flancos

    0x00EA = TU sobre estado de línea
    0x00E8 = TD sobre estado de línea

Contactos de borde observados:

    0x00E0 + 0x1348 -> ORG TU M3
    0x00E0 + 0x1758 -> ORG TD M7

## Timer — evidencia actual

T0 PV10:

    1B48 80FD 0A00 9003 FC6F 19C8

T0 PV25 guardado por WinProLadder:

    1B48 80FD 1900 9003 FC6F 19C8

T1 PV25 guardado tras importar el probe T1:

    1B48 81FD 1900 9003 FC6F 19C8

Por lo tanto:

- `0x80FD` = T0 en este bloque;
- `0x81FD` = T1;
- PV es un word inmediato little-endian;
- T0 -> T1 cambia sólo el byte alto `0x80 -> 0x81`.

La extrapolación Tn = `(0x80+n)<<8 | 0xFD` sólo está confirmada para n=0,1 hasta probar T50.

## Counter — evidencia actual

C0 PV100 original:

    1C48 1D68 40F9 6400 9005 FC6F 1AC8

C0 PV25:

    1C48 1D68 40F9 1900 9005 FC6F 1AC8

Probe LDR C1 importado:

    ... 41F9 1900 ...

Después de guardar el proyecto, WinProLadder serializó canónicamente:

    1C48 1D68 41FD 1900 9005 FC6F 1AC8

Hallazgo importante:

- C0 observado canónico: `0x40F9`;
- C1 guardado canónico: `0x41FD`;
- `0x41F9` fue aceptado por el importador LDR, pero WinProLadder lo normalizó a `0x41FD`.

No generalizar todavía Cn sólo cambiando el byte alto de C0. El probe siguiente usa C2=`0x42FD` para verificar la familia canónica C1+.

## Preset PV

Los casos controlados confirman:

    PV 10  -> word 0x000A
    PV 25  -> word 0x0019
    PV 100 -> word 0x0064

Pendiente: PV >255 para confirmar explícitamente los 16 bits.

## Regla de evidencia

Diferenciamos:

- **observado**: aparece en un fixture;
- **aceptado**: WinProLadder lo importó/abrió;
- **canónico**: WinProLadder lo volvió a guardar así.

Esta distinción evita tratar una representación tolerada por el importador como formato canónico de proyecto.
