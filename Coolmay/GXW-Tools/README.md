# GXW-Tools

Herramientas independientes para inspeccionar, decodificar, validar y modificar proyectos **GX Works2 `.gxw`** de Ladder ordinario.

## Estado

La implementación fue desarrollada por ingeniería inversa sobre `estampadora.gxw` (FX3G/Coolmay) y contrastada con observaciones públicas del formato. **No contiene código copiado de proyectos de terceros.**

Soporta en la baseline actual:

- CFB/OLE v3 exterior y `_hdb` CFB anidado.
- Resolución dinámica `iProjectdataID -> nombre lógico` vía `history.xml` (sin IDs hardcodeados).
- Verificación de `iFileSize` y `szMD5val = Base64(MD5(payload))`.
- `*.Program.pou` de Ladder ordinario, token stream en `0x4F` con framing `[len][payload][len]`.
- Dispositivos `M/X/Y/D/T/C`, constantes `K` y `H`; X/Y en numeración octal FX.
- `LD/LDI/AND/ANDI/OR/ORI/ORB/ANB/OUT/SET/RST/END`, timer/counter output, `PLS`.
- Comparaciones `= <> > >= < <=` y variantes double-word `D...`.
- `MOV`, `DMOV`, `BMOV`, `DADD`, `ZRST`.
- Exportación a sintaxis bracket de `GX-Text-Writer`.
- Recompilación desde la sintaxis bracket soportada.
- Escritura conservadora: actualiza `Program.pou`, las dos copias verificadas del token stream en `.res`, tamaño+MD5 en `history.xml`, reconstruye ambos CFB y vuelve a validar todo.
- Lectura/escritura de la tabla de nombres por dispositivo de esta baseline (`COMMENT.qcd`, Device Comments): 133 registros/17 rangos, X/Y octal, M/D y T200+, UTF-16LE y tamaño variable.
- Auditoría cruzada de dispositivos: detecta lecturas internas sin escritor Ladder y bobinas con múltiples programas escritores; admite whitelist de dispositivos escritos externamente por HMI/SCADA.

## Límite de seguridad

No pretende ser todavía un compilador universal de GX Works2. No inventa soporte para instrucciones desconocidas, Structured Ladder/FBD, ST, SFC, otros PLC ni otras variantes de CFB. Ante una estructura que no coincide con invariantes verificadas, **falla cerrada** en lugar de escribir un proyecto posiblemente corrupto.

Después de modificar un programa se debe abrir la copia generada en GX Works2 y ejecutar **Check Program / Convert / Compile** antes de descargar al PLC. Los archivos generados no deben probarse primero sobre una máquina conectada.

## Uso

```powershell
python -m gxw_tools info estampadora.gxw
python -m gxw_tools validate estampadora.gxw
python -m gxw_tools audit-devices estampadora.gxw --external M100 --external M101
python -m gxw_tools list estampadora.gxw
python -m gxw_tools export estampadora.gxw AUTO -o AUTO.gxtext.txt
python -m gxw_tools export-all estampadora.gxw decoded
python -m gxw_tools rebuild estampadora.gxw -o estampadora_roundtrip.gxw
python -m gxw_tools replace-program estampadora.gxw SALIDAS SALIDAS.gxtext.txt -o estampadora_mod.gxw
python -m gxw_tools export-labels estampadora.gxw -o labels.csv
python -m gxw_tools replace-labels estampadora.gxw labels.csv -o estampadora_labels_mod.gxw
```

## Modelo de escritura

El writer no agrega ni borra streams. Conserva el árbol de directorio OLE y el metadata opaco de cada entrada. Reasigna FAT/MiniFAT desde cero, reinyecta los payloads y luego abre nuevamente el resultado para comprobar:

1. todos los streams lógicos se leen;
2. tamaños/MD5 de `history.xml` coinciden;
3. cada `Program.pou` soportado tokeniza y decodifica;
4. cada `.res` conserva exactamente dos copias del token stream;
5. todos los payloads lógicos no objetivo siguen byte-idénticos.

Este enfoque reduce el riesgo de depender de offsets físicos del archivo original.

## Labels / Device Comments

En la baseline de la estampadora, los nombres `B1`, `STATE`, `EV1_P1`, etc. están serializados en `COMMENT.qcd` como **Device Comments**. Los verdaderos Global/Local Labels (`Global1.gh`, `*.Labels.lh`) están vacíos. Ver [`FORMAT_LABELS.md`](FORMAT_LABELS.md) para el formato binario, mapeo de dispositivos y pruebas de round-trip.


## Auditoría de dependencias

`audit-devices` recorre todos los programas Ladder decodificados y cruza lectores/escritores. Está pensado para detectar errores estructurales antes de escribir un GXW, por ejemplo un contacto `M70` usado sin ninguna bobina/escritura o una salida con más de un programa escritor.

Los dispositivos que deliberadamente son escritos desde HMI/SCADA se declaran con `--external` para evitar falsos positivos. La auditoría es complementaria a `validate`: no sustituye **Check Program / Convert / Compile** de GX Works2.


## GX Works2 — cierre automático de Write to PLC

El checkbox `When processing ends, close this window automatically` pertenece a la UI de GX Works2 y, en la baseline verificada de la estampadora, **no modifica el archivo .gxw**. El GXW probado antes/después fue byte-idéntico.

Para automatizar esa preferencia sin contaminar el formato de proyecto:

```powershell
powershell -ExecutionPolicy Bypass -File .\GXW-Tools\scripts\gxworks2_write_autoclose.ps1
```

El helper espera el diálogo `Write to PLC` y activa únicamente ese checkbox mediante Windows UI Automation. No ejecuta la transferencia ni pulsa confirmaciones.

Ver [GXWORKS2_TRANSFER_AUTOCLOSE.md](GXWORKS2_TRANSFER_AUTOCLOSE.md).
