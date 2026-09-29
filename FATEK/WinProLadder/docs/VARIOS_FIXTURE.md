# Fixture `varios` — multi-network semantic oracle

Fecha: 2026-09-28 local.

La captura suministrada por el usuario, `varios.pdw` y `varios.ldr` son tres representaciones del mismo programa.

## Networks visibles

- N000: rama X1 || Y0, luego X0 negado, OUT Y0.
- N001: M0, salidas M1 normal y M2 negada.
- N002: contacto de flanco ascendente M3, SET M4.
- N003: M5, operación de pulso ascendente, SET P M6.
- N004: contacto de flanco descendente M7, RST M4.
- N005: M8 negado, operación de pulso descendente, RST P M6.
- N006: M11 -> timer T0 .01S PV 10 -> TUP -> M9.
- N007: M12/M13 -> counter C0 PV 100 -> CUP -> M10.

## Stream PDW recuperado

36 words:

    0140 00A1 0090 00C1
    1048 11C8 12D8
    00E0 1348 82FC 1408
    1548 00EA 82F8 1608
    00E0 1758 C4FC 1408
    1858 00E8 C4F8 1608
    1B48 80FD 0A00 9003 FC6F 19C8
    1C48 1D68 40F9 6400 9005 FC6F 1AC8

## LDR

Los 8 records contienen exactamente esos mismos grupos, pero almacenados desde N007 hacia N000.

Longitudes: 14,12,8,8,8,8,6,8 bytes en el orden del archivo.

## Metadata PDW

    n = 36
    count @0x108 = 0x0024
    complement @0x10A = 0x4EDB = 0x4EFF - 36
    end @0x10E = 0x024A
    end @0x110 = 0x024A
    checksum @0x0CC = 0x4A57
    sum(code_words)-1 = 0x4A57
    byte @0x0CA = 0xB3 = (0x23 + 4*36) mod 256

## Importancia

Este fixture prueba simultáneamente:

- programas de más de 2 words;
- múltiples networks;
- branches;
- familia M;
- salidas negadas;
- edges;
- SET/RST normal y P;
- bloques T/C.

Es el primer fixture que permite pasar de un mutador mínimo a un parser/compiler secuencial.
