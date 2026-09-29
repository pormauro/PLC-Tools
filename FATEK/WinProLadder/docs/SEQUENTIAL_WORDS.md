# Sequential words — confirmed map

Estado: **mapa incremental basado en fixtures controlados y validación visual WinProLadder**.

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

La captura de pantalla, `varios.pdw` y `varios.ldr` representan exactamente el mismo programa de 8 networks.

### N000

Pantalla:

    X1 en paralelo con Y0
    luego X0 NC
    OUT Y0

Words:

    0140 00A1 0090 00C1

Mapeo:

| Word | Instrucción |
|---:|---|
| 0x0140 | ORG X1 |
| 0x00A1 | OR Y0 |
| 0x0090 | AND NOT X0 |
| 0x00C1 | OUT Y0 |

### M coils

N001:

    1048 11C8 12D8

corresponde a:

    ORG M0
    OUT M1
    OUT NOT M2

Para los M observados, el byte alto es:

    0x10 + M_index

Mapa confirmado:

| low byte | instrucción M |
|---:|---|
| 0x48 | ORG M |
| 0x58 | ORG NOT M |
| 0xC8 | OUT M |
| 0xD8 | OUT NOT M |

### SET / RST normal y por pulso

Bytes/words observados:

| Forma | function word | operand word |
|---|---:|---:|
| SET M4 | 0x82FC | 0x1408 |
| SET P M6 | 0x82F8 | 0x1608 |
| RST M4 | 0xC4FC | 0x1408 |
| RST P M6 | 0xC4F8 | 0x1608 |

Separación empírica:

- SET vs RST: `0x82..` vs `0xC4..`;
- normal vs P: low byte `FC` vs `F8`;
- operand M usa forma `0x(0x10+index)08` en este contexto.

### Diferencial / flancos

Observados:

    0x00EA = TU sobre estado de línea
    0x00E8 = TD sobre estado de línea

Para contactos de borde al inicio de network se observa un prefijo:

    0x00E0 + 0x1348 -> ORG TU M3
    0x00E0 + 0x1758 -> ORG TD M7

No generalizar todavía ese prefijo a otras familias sin fixture.

## Timer y counter — estructura localizada, campos internos todavía parciales

N006, Timer T0, base .01S, PV=10, TUP -> M9:

    1B48 80FD 0A00 9003 FC6F 19C8

Confirmado:

    1B48 = ORG M11
    19C8 = OUT M9

El bloque intermedio corresponde al timer mostrado, pero los subcampos todavía no se etiquetan individualmente.

N007, Counter C0, PV=100, CUP -> M10 con M12/M13 como entradas:

    1C48 1D68 40F9 6400 9005 FC6F 1AC8

Confirmado:

    1C48 = ORG M12
    1AC8 = OUT M10

El resto se conserva como bloque de counter hasta aislar CK/CLR/PV en fixtures unitarios.

## Regla de evidencia

Una secuencia se marca como **confirmada** sólo cuando la semántica está fijada por un fixture controlado o por la captura correspondiente. Los campos internos de bloques complejos permanecen sin nombre hasta aislarse.
