# FATEK WinProLadder Tools

Ingeniería inversa reproducible de proyectos FATEK WinProLadder (.pdw) y formatos de intercambio.

## Estado

**Fase 2 — writer PDW mínimo validado; parser multi-network y metodología de probes activos.**

Confirmado actualmente:

- imagen de programa de 20K words;
- transformación reversible preservando un template;
- writer PDW aceptado por WinProLadder;
- X/Y índices 0,1,2;
- checksum, word count, complement, end pointers y campo derivado 0xCA;
- fórmulas verificadas hasta 53 words;
- LDR con records de network;
- equivalencia exacta LDR code[] <-> PDW sequential stream;
- M, SET/RST, pulse, TU/TD y branch mínimo;
- timer general T0 con bases .01S y .1S;
- counter normal C0;
- preset T/C en bytes high-to-low;
- diferenciación explícita entre accepted/canonical/visual-confirmed.

El fixture `todooo.pdw` fue especialmente útil para **refutar** hipótesis que el importador aceptaba pero WinProLadder interpretaba con otra semántica.

## Herramientas

### PDW

    python FATEK/WinProLadder/pdw_tools/analyze.py inspect proyecto.pdw
    python FATEK/WinProLadder/pdw_tools/analyze.py compare A.pdw B.pdw
    python FATEK/WinProLadder/pdw_tools/analyze.py recover-program proyecto.pdw
    python FATEK/WinProLadder/pdw_tools/analyze.py write-minimal template.pdw salida.pdw --x 2 --y 0

### LDR

    python FATEK/WinProLadder/ldr_tools/analyze.py varios.ldr

## Documentación clave

- `docs/FORMAT_PDW.md`
- `docs/PROGRAM_MEMORY.md`
- `docs/SEQUENTIAL_WORDS.md`
- `docs/FORMAT_LDR.md`
- `docs/MINIMAL_WRITER_VALIDATION.md`
- `docs/VARIOS_FIXTURE.md`
- `docs/TIMER_COUNTER.md`
- `docs/TODOOO_FIXTURE.md`
- `fixtures/MANIFEST.md`

## Arquitectura objetivo

    Ladder / Universal IR
             |
             +--> FATEK sequential IR
                        |
                        +--> LDR
                        |
                        +--> PDW program image
                                |
                                +--> template-preserving project pack

## Próxima prioridad

1. probar T-index en el campo candidato `9003`;
2. probar C-index en `9005`;
3. confirmar PV300 con bytes `01 2C`;
4. confirmar general timer 1S;
5. luego T50/C2;
6. seguir con AND/OR/branches y construcción automática de networks;
7. cruzar el primer límite de 1.280 bytes;
8. tablas, comentarios, I/O, comunicaciones y hardware.
