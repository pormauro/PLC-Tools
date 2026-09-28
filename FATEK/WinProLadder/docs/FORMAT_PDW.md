# PDW — notas de formato (trabajo en progreso)

Estado: **evidencia empírica, 2026-09-28**.

Este documento separa deliberadamente **CONFIRMADO**, **HIPÓTESIS FUERTE** e **HIPÓTESIS ABIERTA**.

## Fixtures iniciales

| Fixture | Tamaño | SHA-256 |
|---|---:|---|
| VACIO.pdw | 98.871 | 72054bbf92dd88c92de0ba79c45cb2fef255bb9675ef2ed338e08b255ee1ddfd |
| X0-Y0.pdw | 98.871 | ed415db334e916eeec556f6da5df4eecb438ab304bcbe2677be2b1fac9446cb9 |

La única diferencia semántica intencional conocida es un contacto X0 conectado directamente a una bobina Y0 en el segundo proyecto.

## Cabecera — CONFIRMADO

- 0x0000: ASCII "Fatek WinProladder, File Format 1".
- 0x0080: "FB-PLC".
- 0x0090: "WinProladder".
- 0x00A0: "FBs-24MC".
- 0x010C: "Project0".
- 0x0114: "FBs-24MC".
- 0x0000..0x0121 es idéntico entre ambos; primera diferencia en 0x0122.
- Main_unit1 comienza en 0x10232.
- Sub_unit1 comienza en 0x10248.
- Último byte distinto: 0x10251; 0x10252..EOF coincide byte a byte.

Observación: el archivo almacena FBs-24MC aunque la CPU física/configurada por el usuario sea FBs-24MCT. No inferir todavía que el sufijo de tipo de salida se pierda globalmente; puede estar codificado en otro campo.

## Área de registros — CONFIRMADO

Tomando 0x120 como origen experimental, la similitud entre bytes separados por 1.280 posiciones alcanza aproximadamente 97,5 %. Al partir el rango observado en registros de 1.280 bytes aparecen estas fronteras:

- 0x0120: registro A.
- 0x0620: inicio de registros B repetidos.
- 0xA120: registro C.
- 0xA620: inicio de registros D repetidos.
- 0x10020: registro E parcial.

Patrón por hash dentro de cada archivo:

    A BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB C DDDDDDDDDDDDDDDDDD E

Conteos: A=1, B=31, C=1, D=18, E=1 parcial.

## Capa periódica de 256 bytes — CONFIRMADO

Para los registros B repetidos:

    VACIO_record_B XOR X0Y0_record_B

es exactamente periódico cada **256 bytes** durante los 1.280 bytes completos: el mismo bloque de 256 bytes se repite cinco veces.

En los registros D se observa la misma secuencia de 256 bytes con un desplazamiento cíclico de 4 bytes.

La resta modular byte a byte NO presenta esa propiedad exacta; la propiedad es específicamente compatible con XOR.

## Cancelación de transformación — CONFIRMADO

Como 1.280 es múltiplo de 256, dos registros alineados del mismo archivo comienzan en la misma fase de la transformación periódica:

    N(record_active, record_reference) = record_active XOR record_reference

Al calcular:

    N(VACIO.A, VACIO.B) XOR N(X0Y0.A, X0Y0.B)

quedan sólo **15 bytes no nulos** en un registro de 1.280 bytes:

| Offset relativo | XOR |
|---:|---|
| 0x0000..0x0001 | 11 63 |
| 0x00CA..0x00CD | 08 FF FF FE |
| 0x0103 | 01 |
| 0x0108 | 02 |
| 0x010A | 02 |
| 0x010E | 04 |
| 0x0110 | 04 |
| 0x0202..0x0205 | BF FF 3E FF |

Para el segundo grupo:

    N(VACIO.C, VACIO.D) XOR N(X0Y0.C, X0Y0.D)

quedan sólo 6 bytes no nulos al comienzo del registro.

## Primer grupo = candidato de memoria de programa — HIPÓTESIS FUERTE

El primer grupo contiene exactamente:

    32 * 1280 = 40960 bytes
    40960 / 2 = 20480 words
    20480 words = 20K words

La capacidad publicada para el programa de los PLC FBs es 20K words.

Si se supone que un registro B repetido representa memoria borrada a 0xFF y se usa para derivar la transformación XOR, la imagen recuperada contiene:

- `FBS40003` en 0x0002;
- `55 AA` en 0x01FE;
- 31 registros posteriores completamente 0xFF.

Eso hace muy improbable que la recuperación coherente sea accidental.

En VACIO, desde word 257 el candidato queda borrado. En X0-Y0 aparecen:

| Word | Offset relativo | Valor little-endian |
|---:|---:|---:|
| 257 | 0x0202 | 0x0040 |
| 258 | 0x0204 | 0x00C1 |

La lógica conocida equivale a dos mnemónicos, `ORG X0` y `OUT Y0`. Por ahora sólo se afirma:

    {0x0040, 0x00C1} <-> {ORG X0, OUT Y0}

Todavía NO se asigna cuál word corresponde a cuál instrucción hasta comparar X1/Y1/NOT.

Ver `PROGRAM_MEMORY.md`.

## HIPÓTESIS ABIERTAS

1. La transformación completa del PDW es XOR con keystream/estado de período 256 o una transformación algebraicamente equivalente en estas regiones.
2. El segundo grupo C + 18xD + E corresponde a otra memoria/tabla, aún sin asignación semántica.
3. Los cambios en 0x0000..0x0001 del bloque recuperado pueden ser checksum/CRC/hash.
4. Los campos alrededor de 0x00CA y 0x0100 parecen longitudes/contadores/índices, pero faltan fixtures para etiquetarlos.
5. La relación exacta entre el candidato de 20K words y el layout descargado al PLC todavía debe validarse contra transferencia/round-trip.

## Experimentos que falsan/confirman las hipótesis

- Guardar el mismo proyecto dos veces: revela nonce/timestamp/clave variable por guardado.
- X0-Y0 vs X1-Y0: aísla codificación de entrada.
- X0-Y0 vs X0-Y1: aísla codificación de salida.
- contacto NO vs NC: aísla opcode/tipo de contacto.
- exportación .ldr: aporta representación semántica conocida del mismo rung.
- segundo network: prueba crecimiento y delimitación del stream de programa.
- upload/download del mismo programa: contrasta PDW recuperado con imagen real del PLC.

## Fuentes públicas útiles

- FATEK WinProLadder: https://www.fatek.com/en/download.php?act=list&cid=141
- Manual WinProLadder: documenta exportación/importación .txt, .tab, .ldr y .spf.
- FATEK FBs: especifica capacidad de programa de 20K Words.
- FP-08: documenta edición de mnemónicos directamente en el área de programa.
- UperLogic: puede importar proyectos WinProLadder .pdw y convertirlos al entorno nuevo.
- ZDI-22-028 / 030 / 032 / 033: confirman rutinas específicas de parsing PDW en WinProLadder.

## Regla de escritura

Hasta cerrar formato, longitudes, validaciones y checksums, **no se genera ni modifica un PDW de producción**. Toda futura escritura deberá hacerse sobre copia, abrir correctamente en WinProLadder y pasar validación semántica/round-trip.
