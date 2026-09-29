# Sequential words — confirmed map

Estado: **mapa incremental basado en fixtures controlados, screenshots, LDR importado y PDW guardado por WinProLadder**.

## X / Y

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

## Branch mínimo confirmado

`varios` N000:

    0140 00A1 0090 00C1

| Word | Instrucción |
|---:|---|
| 0x0140 | ORG X1 |
| 0x00A1 | OR Y0 |
| 0x0090 | AND NOT X0 |
| 0x00C1 | OUT Y0 |

## M

    1048 = ORG M0
    11C8 = OUT M1
    12D8 = OUT NOT M2

Para los M observados, byte alto = `0x10 + index`.

| low byte | forma |
|---:|---|
| 0x48 | ORG M |
| 0x58 | ORG NOT M |
| 0x68 | segunda entrada M observada en counter/CLR path |
| 0xC8 | OUT M |
| 0xD8 | OUT NOT M |

Los probes posteriores confirmaron:

    1E48 -> M14 en entrada superior
    1F68 -> M15 en entrada CLR

## SET / RST

| Forma | function word | operand word |
|---|---:|---:|
| SET M4 | 0x82FC | 0x1408 |
| SET P M6 | 0x82F8 | 0x1608 |
| RST M4 | 0xC4FC | 0x1408 |
| RST P M6 | 0xC4F8 | 0x1608 |

## TU / TD

    0x00EA = TU sobre estado de línea
    0x00E8 = TD sobre estado de línea

Contactos de borde observados:

    0x00E0 + 0x1348 -> ORG TU M3
    0x00E0 + 0x1758 -> ORG TD M7

## Timer general — corrección confirmada por screenshot

T0 .01S PV25:

    1B48 80FD 1900 9003 FC6F 19C8

T0 .1S PV25:

    1B48 81FD 1900 9003 FC6F 19C8

Por lo tanto:

- `80FD` selecciona base .01S;
- `81FD` selecciona base .1S;
- **no** representan T0/T1;
- `9003` queda como candidato de referencia T0.

## Counter general

C0 PV25:

    1C48 1D68 40F9 1900 9005 FC6F 1AC8

- `40F9` forma parte del counter normal C0 observado;
- `9005` queda como candidato de referencia C0;
- cambiar `40F9` a otras familias NO es una forma válida de cambiar C index.

## Function instructions descubiertas

Por validación visual:

    0x41FD -> FUN87 T.01S
    0x42FD -> FUN88 T.1S
    0xB2F5 -> FUN43 NBM

La documentación oficial FATEK coincide en que FUN87/88 son acumulative timers .01S/.1S.

## Preset

La lectura correcta es por bytes del payload:

    00 0A = 10
    00 19 = 25
    00 64 = 100
    01 2C = 300

Nuestro agrupamiento diagnóstico en words little-endian muestra esos pares como 0x0A00, 0x1900, 0x6400, 0x2C01 respectivamente. No confundir ese word diagnóstico con el valor numérico del preset.

## Regla de evidencia

- **observado**: aparece en bytes;
- **visual-confirmed**: screenshot de WinProLadder fija su semántica;
- **accepted**: el importador lo toleró;
- **canonical**: WinProLadder lo volvió a guardar así;
- **candidate**: hipótesis preparada para el próximo probe.

Nunca promover `accepted` a `canonical` o `confirmed semantic` sin la validación visual correspondiente.
