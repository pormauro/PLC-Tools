# Fixture manifest

Los binarios originales no se modifican. Este manifiesto permite comprobar identidad antes de cualquier experimento.

| Nombre | Semántica | Bytes | SHA-256 |
|---|---|---:|---|
| VACIO.pdw | Proyecto base vacío, FBs-24MCT según configuración del usuario | 98.871 | 72054bbf92dd88c92de0ba79c45cb2fef255bb9675ef2ed338e08b255ee1ddfd |
| VACIO(1).pdw | Copia exacta de VACIO.pdw | 98.871 | 72054bbf92dd88c92de0ba79c45cb2fef255bb9675ef2ed338e08b255ee1ddfd |
| VACIO-2.pdw | Re-guardado del proyecto vacío, sin cambio semántico | 98.871 | f3f2341318c9a93dd85b4b5568745f5148d0a94c00ffa9f5fe275469aa2d5ea6 |
| X0-Y0.pdw | Contacto NO X0 -> OUT Y0 | 98.871 | ed415db334e916eeec556f6da5df4eecb438ab304bcbe2677be2b1fac9446cb9 |
| X0-Y0(1).pdw | Copia exacta de X0-Y0.pdw | 98.871 | ed415db334e916eeec556f6da5df4eecb438ab304bcbe2677be2b1fac9446cb9 |
| X0-Y0-2.pdw | Re-guardado de X0 -> Y0, sin cambio semántico | 98.871 | c133294f0756e1cd9ddadf7dac86b242640969fb40cb0b20dcf8b2e313649fef |
| X1-Y0.pdw | Contacto NO X1 -> OUT Y0 | 98.871 | ec9177e2230d9ef8f06b769cdb2caba456cde42925349fd474a071b0fce61eda |
| X0-Y1.pdw | Contacto NO X0 -> OUT Y1 | 98.871 | 0144eb00c85a2d97d2f24f8e4da63027284915e96cb27db4834318a95918166e |
| NC-X0-Y0.pdw | Contacto NC X0 -> OUT Y0 | 98.871 | 6e8869d39eb9d6157a637a8a58b5ed941ed9c56f9b608df3e4f2331850254fea |
| NC-X0-Y1.pdw | Contacto NC X0 -> OUT Y1 | 98.871 | b22adb9b5a6220fde71a3de60612071f62b3a26a6fce45f763b6dbd8e8e94db9 |
| NC-X0-Y0.ldr | Export Ladder Diagram del fixture NC-X0-Y0 | 277 | 12ad626d979d9a8f02d5ddeeda9a78af319befba9c2932c3d5522eac3ee8d0e5 |
| varios.pdw | 8 networks: ramas, M, edge, SET/RST normal/P, timer y counter | 98.871 | f808927f76adb5386369a9492f1d8512d3382bcffb1a0b2b4ad25f1769e191a6 |
| varios.ldr | Export Ladder Diagram exacto de varios.pdw | 422 | 7ffb79a3137f29bbb50c1441f37dffe83419ebbebec7c3623b8a5b75564fe2a3 |
| timer + counter.pdw | WinProLadder: C0 PV25 + T0 PV25 | 98.871 | 7d02f3902aebae236a41ae0cde16264592af4cd75af62478666522e7a8662c0a |
| timer + counter 2.pdw | Guardado tras importar probes C1/T1 PV25 | 98.871 | 6930b15b15d5172caebd07da07e198cf232d617be072926e912afded6041d491 |

## Hallazgos reproducibles

- Re-save: el programa recuperado es estable salvo el primer word de estado.
- X/Y: ORG/ORG NOT/OUT e índices 0..2 validados externamente.
- LDR simple: mutación NC -> NO importada correctamente.
- varios: 36 words, 8 networks, stream PDW = concatenación exacta de payloads LDR en orden N000 -> N007.
- checksum PDW: `(sum(code_words)-1) & 0xFFFF`.
- SET/RST normal y P quedan separados en el stream.
- PV Timer/Counter se almacena como word little-endian inmediato: 10=`0x000A`, 25=`0x0019`, 100=`0x0064`.
- timer + counter: 13 words, 2 networks, confirma count/complement/end/checksum/length byte.
- `TEST-GENERATED-TIMER-COUNTER.pdw`, construido desde X0-Y0, fue abierto por WinProLadder y mostró C0 PV25 + T0 PV25 correctamente.
- `timer + counter 2.pdw` recupera T1 como `0x81FD` y C1 como `0x41FD`.
- El probe LDR de C1 había sido importado como `0x41F9`; al guardar, WinProLadder lo normalizó a `0x41FD`. Por lo tanto forma aceptada y forma canónica no son necesariamente idénticas.
- Reconstruyendo desde X0-Y0.pdw el stream canónico de C1+T1 se obtiene una imagen de programa idéntica a `timer + counter 2.pdw` desde byte recuperado 2 hasta el final de la imagen de 20K words.

## Política

Los originales se usan sólo como fixtures de lectura. Toda escritura se hace sobre copias derivadas.
