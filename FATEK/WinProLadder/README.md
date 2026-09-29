# FATEK WinProLadder Tools

Ingeniería inversa reproducible de proyectos FATEK WinProLadder (.pdw) y formatos de intercambio.

## Estado

**Fase 2 inicial — writer mínimo validado y estructura multi-network localizada.**

Ya está demostrado:

- recuperación de imagen de programa de 20K words;
- mutación PDW real aceptada por WinProLadder;
- X/Y indices 0,1,2;
- checksum aditivo de programa;
- word count, complement y end pointers;
- LDR importable y registros de network delimitados;
- relación exacta entre LDR por-network y stream PDW;
- M ORG/NOT/OUT/OUT NOT;
- SET/RST normal y P;
- TU/TD en los casos observados;
- localización de bloques timer y counter.

## Herramientas

### PDW

    python FATEK/WinProLadder/pdw_tools/analyze.py inspect proyecto.pdw
    python FATEK/WinProLadder/pdw_tools/analyze.py compare A.pdw B.pdw
    python FATEK/WinProLadder/pdw_tools/analyze.py recover-program proyecto.pdw
    python FATEK/WinProLadder/pdw_tools/analyze.py write-minimal template.pdw salida.pdw --x 2 --y 0

El writer mínimo no sobrescribe el original y valida el resultado decodificándolo.

### LDR

    python FATEK/WinProLadder/ldr_tools/analyze.py varios.ldr

Ahora separa networks, longitudes, code words, trailers y anotaciones conocidas.

## Documentación

- `docs/FORMAT_PDW.md`
- `docs/PROGRAM_MEMORY.md`
- `docs/SEQUENTIAL_WORDS.md`
- `docs/FORMAT_LDR.md`
- `docs/MINIMAL_WRITER_VALIDATION.md`
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

Aislar individualmente:

1. timer T0 con cambios de PV/base;
2. counter C0 con CK/CLR/PV;
3. AND y OR simples sin ramas complejas;
4. dos networks mínimos;
5. SET/RST P sin otros cambios;
6. crecimiento a más de un registro de 1.280 bytes.

Después se avanza sobre tablas, comentarios, I/O, comunicaciones y hardware.
