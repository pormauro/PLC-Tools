# PDW — notas de formato (trabajo en progreso)

Estado: **evidencia empírica, 2026-09-28**.

Este documento separa deliberadamente **CONFIRMADO** de **HIPÓTESIS**.

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

No se asigna todavía significado semántico a A/B/C/D/E.

## Capa periódica de 256 bytes — CONFIRMADO

Para los registros B repetidos:

VACIO_record_B XOR X0Y0_record_B

es exactamente periódico cada **256 bytes** durante los 1.280 bytes completos: el mismo bloque de 256 bytes se repite cinco veces.

En los registros D se observa la misma secuencia de 256 bytes con un desplazamiento cíclico de 4 bytes.

La resta modular byte a byte NO presenta esa propiedad exacta; la propiedad es específicamente compatible con XOR.

## Cancelación de transformación — CONFIRMADO

Como 1.280 es múltiplo de 256, dos registros alineados del mismo archivo comienzan en la misma fase de la transformación periódica. Definimos la normalización empírica:

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

Esto transforma un diff bruto de 65.282 bytes en un problema localizable y comprobable.

## HIPÓTESIS actuales

1. Existe una capa de ofuscación/cifrado basada en XOR con estado o keystream de período 256, o una transformación algebraicamente equivalente para estas regiones.
2. Los registros repetidos B/D representan slots vacíos o plantillas sin uso.
3. A y C son registros activos/cabeceras de dos colecciones distintas.
4. Los bytes relativos alrededor de 0x00CA, 0x0103..0x0110 y 0x0202..0x0205 son candidatos a describir el rung X0 -> Y0, pero NO deben etiquetarse todavía como opcode/operando hasta comparar X1, Y1, contacto NC y .ldr.
5. Los primeros bytes cambiantes de los registros normalizados pueden ser longitud/checksum/contador y no lógica ladder.

## Experimentos que falsan/confirman las hipótesis

- Guardar el mismo proyecto dos veces: revela si existe nonce, timestamp o clave variable por guardado.
- X0-Y0 vs X1-Y0: aísla codificación de entrada.
- X0-Y0 vs X0-Y1: aísla codificación de salida.
- contacto NO vs NC: aísla opcode/tipo de contacto.
- exportación .ldr: aporta una representación semántica conocida del mismo rung.
- proyecto con segundo network: prueba si el área A contiene una lista/stream de networks.

## Fuentes públicas útiles

- FATEK WinProLadder: https://www.fatek.com/en/download.php?act=list&cid=141
- Manual WinProLadder: documenta exportación/importación .txt, .tab, .ldr y .spf.
- UperLogic: puede importar proyectos WinProLadder .pdw y convertirlos al entorno nuevo.
- ZDI-22-028 / 030 / 032 / 033: confirman la existencia de rutinas específicas de parsing PDW en WinProLadder.

## Regla de escritura

Hasta cerrar formato, longitudes y validaciones, **no se genera ni modifica un PDW de producción**. Toda futura escritura deberá hacerse sobre copia, abrir correctamente en WinProLadder y pasar validación semántica/round-trip.
