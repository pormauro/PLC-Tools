# LDR — FATEK WinProLadder Ladder Diagram resource

Estado: **estructura inicial confirmada con un fixture**.

Fixture: `NC-X0-Y0.ldr`, 277 bytes.

## Cabecera observada

| Offset | Contenido |
|---:|---|
| 0x0000 | ASCII `Fatek Resource File Format 1` |
| 0x0080 | ASCII `FB-RES` |
| 0x0090 | ASCII `WinProladder` |
| 0x00A0 | ASCII `FBs-24MC` |
| 0x0100 | inicio del payload observado |

Los campos entre esas cadenas todavía no tienen nombre asignado.

## Payload del fixture

Desde 0x0100:

    12 10 09 00 04 00 50 00 C1 00 01 00 00 04 24 FF
    FF 00 00 00 00

Los dos words de ladder aparecen literalmente en:

- 0x0106: `50 00` -> 0x0050
- 0x0108: `C1 00` -> 0x00C1

El mismo par se recupera desde el PDW correspondiente.

## Consecuencia técnica

El formato LDR es considerablemente más directo que PDW para transportar lógica ladder. Esto habilita dos caminos paralelos:

1. seguir descifrando PDW para preservar proyecto completo;
2. construir antes un generador/importador LDR para iterar lógica ladder de manera universal.

Todavía no conocemos:

- significado exacto de 0x0100..0x0105;
- delimitación de múltiples networks;
- campos finales 0x010A..EOF;
- checksum/longitud del resource;
- codificación de comentarios o geometría del network.

Para mapearlos se requieren exports LDR con cambios unitarios.
