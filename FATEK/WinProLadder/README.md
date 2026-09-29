# FATEK WinProLadder Tools

Ingeniería inversa reproducible de proyectos FATEK WinProLadder (.pdw) y formatos de intercambio.

## Estado

**Fase 2 — writer mínimo validado; writer secuencial corto en validación externa.**

Ya está demostrado:

- recuperación de imagen de programa de 20K words;
- mutación PDW real aceptada por WinProLadder;
- X/Y indices 0,1,2;
- checksum aditivo;
- word count, complement y end pointers;
- fórmulas de metadata confirmadas con 0, 2, 13 y 36 words;
- LDR importable y registros de network delimitados;
- relación exacta entre LDR por-network y stream PDW;
- M ORG/NOT/OUT/OUT NOT;
- SET/RST normal y P;
- TU/TD en los casos observados;
- PV de timer/counter confirmado para 10, 25 y 100;
- reconstrucción sintética de un programa timer+counter idéntica al PDW guardado por WinProLadder desde el byte semántico 2 en adelante.

## Herramientas

### PDW

    python FATEK/WinProLadder/pdw_tools/analyze.py inspect proyecto.pdw
    python FATEK/WinProLadder/pdw_tools/analyze.py compare A.pdw B.pdw
    python FATEK/WinProLadder/pdw_tools/analyze.py recover-program proyecto.pdw
    python FATEK/WinProLadder/pdw_tools/analyze.py write-minimal template.pdw salida.pdw --x 2 --y 0

Writer secuencial experimental, limitado a <=55 words:

    python FATEK/WinProLadder/pdw_tools/analyze.py \
      write-sequential-experimental template.pdw salida.pdw \
      0x1C48 0x1D68 0x40F9 0x1900 0x9005 0xFC6F 0x1AC8

### LDR

    python FATEK/WinProLadder/ldr_tools/analyze.py varios.ldr

Separa network records, longitudes, code words, trailers y anotaciones conocidas.

## Documentación

- `docs/FORMAT_PDW.md`
- `docs/PROGRAM_MEMORY.md`
- `docs/SEQUENTIAL_WORDS.md`
- `docs/FORMAT_LDR.md`
- `docs/MINIMAL_WRITER_VALIDATION.md`
- `docs/VARIOS_FIXTURE.md`\n- `docs/TIMER_COUNTER_ROUNDTRIP.md`
- `docs/TIMER_COUNTER_ROUNDTRIP.md`
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

1. validar externamente TEST-GENERATED-TIMER-COUNTER.pdw;
2. aislar T0 -> T1 y C0 -> C1;
3. probar PV >255;
4. separar CK/CLR y outputs del counter;
5. mapear AND/OR simples y branches;
6. cruzar el límite donde cambian 0xCA/0xCB;
7. luego tablas, comentarios, I/O, comunicaciones y hardware.
