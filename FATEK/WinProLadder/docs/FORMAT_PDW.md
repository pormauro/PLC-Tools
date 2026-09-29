# PDW — notas de formato (trabajo en progreso)

Estado: **evidencia empírica, 2026-09-28**.

Este documento separa deliberadamente **CONFIRMADO**, **HIPÓTESIS FUERTE** e **HIPÓTESIS ABIERTA**.

## Corpus controlado

Ver `../fixtures/MANIFEST.md`.

El corpus ya incluye:

- proyecto vacío y re-guardado sin cambios;
- X0 NO -> Y0 y re-guardado sin cambios;
- X1 NO -> Y0;
- X0 NO -> Y1;
- X0 NC -> Y0;
- X0 NC -> Y1;
- export LDR de NC X0 -> Y0.

Todos los PDW del corpus tienen 98.871 bytes.

## Cabecera — CONFIRMADO

- 0x0000: ASCII `Fatek WinProladder, File Format 1`.
- 0x0080: `FB-PLC`.
- 0x0090: `WinProladder`.
- 0x00A0: `FBs-24MC`.
- 0x010C: `Project0`.
- 0x0114: `FBs-24MC`.
- la región transformada comienza alrededor de 0x0122;
- `Main_unit1` aparece cerca de 0x10232;
- `Sub_unit1` aparece cerca de 0x10248.

Observación: los archivos muestran `FBs-24MC` aunque el equipo usado por el usuario sea FBs-24MCT. No se concluye todavía dónde se conserva el subtipo exacto de salida.

## Registros de 1.280 bytes — CONFIRMADO

Tomando 0x120 como origen experimental aparece el patrón:

    A + 31xB + C + 18xD + E(parcial)

con registros de 1.280 bytes.

Dentro de cada archivo los B son idénticos entre sí y los D son idénticos entre sí.

## Transformación periódica — CONFIRMADO

Entre fixtures, el XOR de registros repetidos B es periódico cada 256 bytes durante 1.280 bytes completos.

Como:

    1280 = 5 * 256

los registros alineados permiten cancelar la transformación sin conocer inicialmente su algoritmo absoluto.

La evidencia es compatible con una capa XOR/keystream periódica en estas regiones.

## Primer grupo = imagen de programa de 20K words — HIPÓTESIS FUERTE

El primer grupo contiene exactamente:

    32 * 1280 = 40960 bytes
    40960 / 2 = 20480 words
    20480 words = 20K words

Esto coincide exactamente con la capacidad de programa publicada para FBs.

Usando un registro B repetido como representación de memoria borrada a 0xFF, la recuperación produce:

- `FBS40003` en la cabecera interna;
- marcador `55 AA` en 0x01FE;
- 31 registros posteriores exactamente 0xFF;
- código ladder coherente desde el word 257.

## Re-guardados — CONFIRMADO

### VACIO

`VACIO.pdw` y `VACIO-2.pdw` tienen miles de bytes raw distintos por la transformación de guardado.

Después de recuperar la imagen de 20K words:

- sólo cambian los bytes relativos 0x0000..0x0001;
- desde 0x0002 hasta el final de los 40.960 bytes la imagen recuperada es idéntica.

### X0 -> Y0

`X0-Y0.pdw` y `X0-Y0-2.pdw` muestran exactamente el mismo comportamiento:

- sólo cambian los bytes recuperados 0x0000..0x0001;
- el código y toda la imagen restante son idénticos.

Consecuencia: esos primeros 2 bytes son **estado variable de guardado o transformación**, no un fingerprint semántico estable del ladder.

El analizador calcula por eso un `semantic_sha256_ignoring_first_word`.

## Sequential words mínimos — CONFIRMADO

Desde el word 257:

| Ladder | Word 257 | Word 258 |
|---|---:|---:|
| X0 NO -> Y0 | 0x0040 | 0x00C1 |
| X1 NO -> Y0 | 0x0140 | 0x00C1 |
| X0 NO -> Y1 | 0x0040 | 0x01C1 |
| X0 NC -> Y0 | 0x0050 | 0x00C1 |
| X0 NC -> Y1 | 0x0050 | 0x01C1 |

Para los casos observados:

    word = (device_index << 8) | opcode

Mapa ya demostrado:

- low opcode 0x40: `ORG Xn`, confirmado X0/X1;
- low opcode 0x50: `ORG NOT Xn`, confirmado X0;
- low opcode 0xC1: `OUT Yn`, confirmado Y0/Y1.

Ver `SEQUENTIAL_WORDS.md`.

## Confirmación independiente con LDR — CONFIRMADO

`NC-X0-Y0.ldr` no usa la transformación del PDW.

Su payload contiene literalmente:

    50 00 C1 00

que, little-endian, es:

    0x0050
    0x00C1

Es exactamente el mismo par recuperado desde `NC-X0-Y0.pdw`.

Esto confirma tanto los words como su orden.

## Segundo grupo — CONFIRMADO COMO NO SEMÁNTICO PARA ESTE CORPUS

Usando un registro D repetido como referencia de borrado 0xFF, el segundo grupo recupera al final una secuencia:

    FATEKFATEKFATEK...

La comparación de **todos** los fixtures actuales muestra:

- al ignorar los primeros 6 bytes recuperados;
- y los últimos 2 bytes recuperados;

el segundo grupo es byte-a-byte idéntico entre:

- VACIO;
- VACIO re-guardado;
- X0/Y0 y re-guardado;
- X1/Y0;
- X0/Y1;
- NC X0/Y0;
- NC X0/Y1.

Por lo tanto, en este corpus el segundo grupo **no transporta la semántica del ladder**.

Los 8 bytes variables son candidatos a estado de guardado, integridad o estado de transformación. No se les asigna todavía significado.

## Consecuencia para un futuro writer

La arquitectura probable queda mucho más simple:

    PDW template
       |
       +-- cabecera/configuración de proyecto
       |
       +-- imagen programa 20K words  <-- ladder
       |
       +-- otras áreas/configuración
       |
       +-- estado de guardado/transformación

Todavía NO se escribe PDW porque falta demostrar:

1. cómo regenerar o preservar correctamente los campos variables;
2. si existe validación de integridad al abrir/guardar;
3. comportamiento con programas más largos;
4. múltiples networks;
5. instrucciones de longitud variable;
6. tablas, I/O, comunicaciones y demás configuración;
7. round-trip real en WinProLadder.

## HIPÓTESIS ABIERTAS

1. Algoritmo exacto que genera el keystream/transformación.
2. Función de los 2 bytes variables iniciales de la imagen recuperada.
3. Función de los 6+2 bytes variables del segundo grupo.
4. Semántica completa del segundo grupo y de las áreas posteriores.
5. Estructura exacta de contadores, longitudes y checks internos.
6. Cómo se serializan instrucciones más complejas y operands fuera del rango mínimo observado.

## Regla de escritura

Hasta cerrar formato, validaciones y round-trip:

**no se genera ni modifica un PDW para uso real**.

Las futuras pruebas de escritura se harán únicamente sobre copias derivadas y deben abrir correctamente en WinProLadder antes de considerarse válidas.
