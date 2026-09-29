# LDR — FATEK WinProLadder Ladder Diagram resource

Estado: **estructura de múltiples networks confirmada con dos fixtures**.

Fixtures principales:

- `NC-X0-Y0.ldr`: 1 network, 277 bytes.
- `varios.ldr`: 8 networks, 422 bytes.

## Cabecera

| Offset | Contenido |
|---:|---|
| 0x0000 | ASCII `Fatek Resource File Format 1` |
| 0x0080 | ASCII `FB-RES` |
| 0x0090 | ASCII `WinProladder` |
| 0x00A0 | ASCII `FBs-24MC` |
| 0x0100 | inicio del payload |

## Registro de network — CONFIRMADO

`varios.ldr` permite delimitar exactamente 8 registros.

Cada registro observado tiene:

    12 10
    u16 envelope_len
    u16 code_len
    code[code_len]
    trailer[5]

y cumple:

    envelope_len = code_len + 5
    total_record_len = code_len + 11

El trailer observado tiene 5 bytes. Su función exacta sigue abierta.

Después del último registro aparece:

    FF FF 00 00 00 00

## Orden — CONFIRMADO

Los registros LDR aparecen en **orden inverso de network**.

En `varios.ldr`:

    primer registro  = N007
    ...
    último registro  = N000

Sin embargo, al extraer solamente `code[]` y concatenarlo en orden N000 -> N007 se obtiene byte por byte el stream de programa recuperado desde `varios.pdw`.

## Longitudes de varios.ldr

| Network | code bytes | code words |
|---|---:|---:|
| N000 | 8 | 4 |
| N001 | 6 | 3 |
| N002 | 8 | 4 |
| N003 | 8 | 4 |
| N004 | 8 | 4 |
| N005 | 8 | 4 |
| N006 | 12 | 6 |
| N007 | 14 | 7 |
| **Total** | **72** | **36** |

El PDW correspondiente declara exactamente 36 words de programa.

## Relación LDR <-> PDW — CONFIRMADO

    reverse(LDR network records).code
        ==
    PDW recovered sequential code stream

Esto convierte LDR en un oráculo directo de:

- límites de network;
- bytes exactos de cada network;
- orden del stream PDW.

El PDW no mostró una tabla auxiliar cambiante con los límites de network, incluso comparando VACIO con el fixture de 8 networks. La hipótesis actual es que los límites son reconstruibles desde la gramática secuencial.

## Writer LDR mínimo — VALIDADO

Se modificó el export `NC-X0-Y0.ldr` cambiando:

    50 00 -> 40 00

sin alterar el resto del resource.

WinProLadder importó el archivo resultante como X0 -> Y0 correctamente.

Esto demuestra que el payload de instrucciones puede mutarse preservando el envelope existente para una transformación de igual longitud.

## Herramienta

    python FATEK/WinProLadder/ldr_tools/analyze.py varios.ldr

El inspector actual:

- valida cabecera;
- separa network records;
- expone longitudes y trailer;
- asigna número de network según el orden inverso confirmado;
- lista words;
- reconoce instrucciones ya mapeadas.

## Abierto

- significado exacto de los 5 bytes de trailer;
- construcción de un registro nuevo de longitud distinta;
- geometría/layout gráfico si existe en el resource;
- comentarios;
- reglas para instructions/functions todavía no mapeadas.
