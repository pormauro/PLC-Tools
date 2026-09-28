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

## Hallazgos reproducibles con este corpus

- VACIO.pdw y VACIO-2.pdw recuperan la misma imagen de programa al ignorar sólo los 2 primeros bytes variables de guardado.
- X0-Y0.pdw y X0-Y0-2.pdw hacen lo mismo.
- X0 -> Y0: words `0x0040 0x00C1`.
- X1 -> Y0: words `0x0140 0x00C1`.
- X0 -> Y1: words `0x0040 0x01C1`.
- NC X0 -> Y0: words `0x0050 0x00C1`.
- NC X0 -> Y1: words `0x0050 0x01C1`.
- NC-X0-Y0.ldr contiene literalmente `50 00 C1 00` en su payload.

## Política

Antes de analizar un fixture, verificar tamaño y SHA-256. Los experimentos de escritura, cuando existan, se harán siempre sobre copias derivadas y nunca sobre estos originales.
