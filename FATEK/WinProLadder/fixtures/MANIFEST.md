# Fixture manifest

Los binarios originales no se modifican. Este manifiesto permite comprobar identidad antes de cualquier experimento.

| Nombre | Semántica | Bytes | SHA-256 |
|---|---|---:|---|
| VACIO.pdw | Proyecto base vacío, FBs-24MCT según configuración del usuario | 98.871 | 72054bbf92dd88c92de0ba79c45cb2fef255bb9675ef2ed338e08b255ee1ddfd |
| VACIO(1).pdw | Copia exacta de VACIO.pdw | 98.871 | 72054bbf92dd88c92de0ba79c45cb2fef255bb9675ef2ed338e08b255ee1ddfd |
| VACIO-2.pdw | Re-guardado del proyecto vacío | 98.871 | f3f2341318c9a93dd85b4b5568745f5148d0a94c00ffa9f5fe275469aa2d5ea6 |
| X0-Y0.pdw | X0 NO -> Y0 | 98.871 | ed415db334e916eeec556f6da5df4eecb438ab304bcbe2677be2b1fac9446cb9 |
| X0-Y0-2.pdw | Re-guardado X0 -> Y0 | 98.871 | c133294f0756e1cd9ddadf7dac86b242640969fb40cb0b20dcf8b2e313649fef |
| X1-Y0.pdw | X1 NO -> Y0 | 98.871 | ec9177e2230d9ef8f06b769cdb2caba456cde42925349fd474a071b0fce61eda |
| X0-Y1.pdw | X0 NO -> Y1 | 98.871 | 0144eb00c85a2d97d2f24f8e4da63027284915e96cb27db4834318a95918166e |
| NC-X0-Y0.pdw | X0 NC -> Y0 | 98.871 | 6e8869d39eb9d6157a637a8a58b5ed941ed9c56f9b608df3e4f2331850254fea |
| NC-X0-Y1.pdw | X0 NC -> Y1 | 98.871 | b22adb9b5a6220fde71a3de60612071f62b3a26a6fce45f763b6dbd8e8e94db9 |
| NC-X0-Y0.ldr | Export NC X0 -> Y0 | 277 | 12ad626d979d9a8f02d5ddeeda9a78af319befba9c2932c3d5522eac3ee8d0e5 |
| varios.pdw | 8 networks: branch, M, edge, SET/RST, timer, counter | 98.871 | f808927f76adb5386369a9492f1d8512d3382bcffb1a0b2b4ad25f1769e191a6 |
| varios.ldr | Export exacto de varios.pdw | 422 | 7ffb79a3137f29bbb50c1441f37dffe83419ebbebec7c3623b8a5b75564fe2a3 |
| timer + counter.pdw | C0 PV25 + T0 .01S PV25 | 98.871 | 7d02f3902aebae236a41ae0cde16264592af4cd75af62478666522e7a8662c0a |
| timer + counter 2.pdw | Guardado tras importar probes inicialmente llamados C1/T1; luego visualmente reinterpretados | 98.871 | 6930b15b15d5172caebd07da07e198cf232d617be072926e912afded6041d491 |
| todooo.pdw | PDW generado + seis probes; autoridad visual para corregir T/C | 98.871 | 8c47cc0a83cc393ca48837abb4e928d8af275168c31c4d582c07f8edbd9525d7 |
| todo v2.pdw | Cuatro probes válidos + dos imports fallidos que generan N000/N001 vacíos | 98.871 | 9add9b1724c295ffae817cf4ff9e9b20eeb13c25e098ad5d84806e7e39d85e0d |

## Estado de evidencia

Confirmado:

- X/Y ORG/ORG NOT/OUT e índices 0..2;
- writer PDW mínimo abierto y Syntax Check PASS;
- LDR simple modificado e importado;
- stream multi-network PDW = concatenación de code[] LDR en orden ladder;
- checksum/count/complement/end/0xCA para longitudes 0,2,13,36,53 words;
- M contacts/outputs observados;
- SET/RST normal y P;
- TU/TD observados;
- T0 general .01S = 80FD;
- T0 general .1S = 81FD;
- C0 normal counter usa 40F9 en el bloque observado;
- PV raw bytes high-to-low: 00 19=25, 00 64=100, 01 2C=300;
- counter top M14 y CLR M15 probes.

Correcciones:

- 81FD no es T1;
- 41FD no es C1: screenshot = FUN87 T.01S;
- 42FD no es C2: screenshot = FUN88 T.1S;
- B2F5 no es T50: screenshot = FUN43 NBM;
- importer acceptance alone is not semantic confirmation;
- `9103` y `9105` no cambian T0/C0 por LDR y son canonicalizados de vuelta a `9003`/`9005`;
- dos imports fallidos consecutivos producen dos words `EB5F` y dos networks visibles vacíos;
- `EB5F` queda confirmado como forma de network vacío en el stream observado;
- `todo v2.pdw`: 28 words, checksum 0x2987, complemento 0x4EE3 y fin 0x023A; todas las fórmulas siguen cerrando.

## Política

Originales sólo lectura. Toda escritura sobre copias derivadas y con verificación posterior.
