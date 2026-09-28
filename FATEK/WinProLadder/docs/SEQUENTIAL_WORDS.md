# Sequential words — minimal confirmed map

Estado: **confirmado para los operandos observados en el corpus del 2026-09-28**.

## Programa mínimo recuperado

El código del rung mínimo comienza en el word 257 de la imagen candidata de 20K words.

| Ladder conocido | Word 257 | Word 258 |
|---|---:|---:|
| X0 NO -> Y0 | 0x0040 | 0x00C1 |
| X1 NO -> Y0 | 0x0140 | 0x00C1 |
| X0 NO -> Y1 | 0x0040 | 0x01C1 |
| X0 NC -> Y0 | 0x0050 | 0x00C1 |
| X0 NC -> Y1 | 0x0050 | 0x01C1 |

## Codificación demostrada

Para los casos observados:

    word = (device_index << 8) | opcode

Se demuestra porque:

- X0 -> X1 cambia sólo el byte alto: 0x0040 -> 0x0140.
- Y0 -> Y1 cambia sólo el byte alto: 0x00C1 -> 0x01C1.
- NO -> NC sobre X0 cambia sólo el byte bajo: 0x0040 -> 0x0050.
- cambiar Y0/Y1 no altera el word del contacto;
- cambiar NO/NC no altera el word de salida.

## Mapa confirmado

| Opcode bajo | Forma observada | Evidencia |
|---:|---|---|
| 0x40 | ORG Xn | confirmado para X0 y X1 |
| 0x50 | ORG NOT Xn | confirmado para X0; layout de índice coherente con el esquema general |
| 0xC1 | OUT Yn | confirmado para Y0 y Y1 |

No extrapolar todavía a X2+, Y2+ como contrato de writer sin fixture adicional, aunque el patrón sea muy fuerte.

## Confirmación cruzada LDR

El archivo NC-X0-Y0.ldr contiene, sin la transformación del PDW:

    50 00 C1 00

Interpretado little-endian:

    0x0050
    0x00C1

Esto coincide exactamente con la imagen de programa recuperada desde NC-X0-Y0.pdw y valida de forma independiente el orden de los words.

## Próximos opcodes a mapear

Prioridad MVP:

1. OR / OR NOT
2. AND / AND NOT
3. SET
4. RST
5. timer T
6. counter C
7. segundo network
8. M, S y otros tipos de dispositivo
9. índices mayores para comprobar rollover/anchura de operandos
