# FATEK WinProLadder Tools

Ingeniería inversa reproducible de proyectos FATEK WinProLadder (.pdw) y formatos de intercambio.

## Estado

**Fase 1 avanzada — lectura, recuperación y decodificación mínima comprobada. Sin writer PDW todavía.**

El corpus controlado ya permitió demostrar:

- región de programa candidata de 40.960 bytes = 20.480 words = 20K words;
- recuperación determinística usando registros borrados 0xFF;
- re-guardados con ladder idéntico cambian sólo un word variable al inicio de la imagen recuperada;
- X0 NO -> Y0 = `0x0040 0x00C1`;
- X1 NO -> Y0 = `0x0140 0x00C1`;
- X0 NO -> Y1 = `0x0040 0x01C1`;
- X0 NC -> Y0 = `0x0050 0x00C1`;
- X0 NC -> Y1 = `0x0050 0x01C1`;
- el export LDR de NC X0 -> Y0 contiene literalmente `50 00 C1 00`;
- el segundo gran grupo del PDW no cambia semánticamente con estos ladders una vez eliminados 8 bytes variables de guardado.

## Herramientas

### PDW

    python FATEK/WinProLadder/pdw_tools/analyze.py inspect proyecto.pdw
    python FATEK/WinProLadder/pdw_tools/analyze.py compare A.pdw B.pdw
    python FATEK/WinProLadder/pdw_tools/analyze.py recover-program proyecto.pdw
    python FATEK/WinProLadder/pdw_tools/analyze.py recover-program proyecto.pdw --output program.bin

El resumen incluye un decoder mínimo para los sequential words ya comprobados.

### LDR

    python FATEK/WinProLadder/ldr_tools/analyze.py ladder.ldr

El inspector muestra cabecera, payload, words little-endian y las instrucciones conocidas.

## Documentación

- `docs/FORMAT_PDW.md`
- `docs/PROGRAM_MEMORY.md`
- `docs/SEQUENTIAL_WORDS.md`
- `docs/FORMAT_LDR.md`
- `fixtures/MANIFEST.md`

## Estrategia

Hay dos caminos paralelos:

    Universal IR
       |
       +--> LDR  --> WinProLadder import       [camino corto para lógica]
       |
       +--> PDW  --> proyecto completo         [camino completo]

LDR parece mucho más directo y puede permitir generar ladder importable antes de terminar el empaquetador PDW.

PDW sigue siendo necesario para preservar proyecto completo: hardware, configuración, tablas, comunicaciones y demás recursos.

## Próximos fixtures prioritarios

Para ampliar el set de instrucciones:

1. X2 -> Y0 y X0 -> Y2 para validar el patrón de índice más allá de 0/1.
2. X0 AND X1 -> Y0.
3. X0 OR X1 -> Y0.
4. X0 -> SET Y0.
5. X0 -> RST Y0.
6. Timer simple.
7. Counter simple.
8. Dos networks independientes.
9. Export LDR correspondiente a cada uno.

Después:

- comentarios;
- tablas;
- status pages;
- módulos/I/O;
- comunicaciones;
- configuración de expansión.

## Meta

    PDW <-> FATEK IR <-> IR universal / PLCopen <-> otros fabricantes

La escritura directa de PDW se habilitará únicamente con round-trip comprobado en WinProLadder.
