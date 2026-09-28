# GX Works2 — cerrar automáticamente la ventana al terminar Write to PLC

## Hallazgo confirmado — 2026-09-24

Durante la prueba de `Estampadora_PLC_MANUAL_V1.gxw` se activó en GX Works2 el checkbox:

```text
When processing ends, close this window automatically.
```

La opción pertenece al diálogo de progreso de **Write to PLC**.

Se comparó byte a byte el GXW antes y después de usar esa opción:

- tamaño: 1,206,784 bytes en ambos;
- SHA-256 en ambos: `fcbd6f111bbfeef22c590ec27c22d51db7b7a4c90f431cdf8e71113031218bc1`;
- diferencia binaria: **0 bytes**.

Conclusión: **este estado no se serializa en el archivo .gxw de esta baseline**. No debe intentarse implementar modificando streams, offsets, CFB, `history.xml` ni payloads del proyecto.

La documentación oficial de GX Works2 muestra el checkbox en el diálogo de escritura y también documenta opciones globales relacionadas con el cierre automático de las ventanas PLC Read/Write.

## Consecuencia para GXW-Tools

El writer GXW debe seguir siendo estrictamente de proyecto. La preferencia de UI se trata como una automatización externa de GX Works2.

Se agrega:

```text
scripts/gxworks2_write_autoclose.ps1
```

El helper usa **Windows UI Automation** para:

1. esperar que aparezca la ventana `Write to PLC`;
2. localizar un CheckBox cuyo texto corresponda a `When processing ends, close this window automatically`;
3. activarlo sólo si está desmarcado;
4. no tocar el proyecto ni escribir el PLC por sí mismo.

## Uso

Abrir GX Works2 y lanzar el helper antes de ejecutar la transferencia:

```powershell
powershell -ExecutionPolicy Bypass -File .\GXW-Tools\scripts\gxworks2_write_autoclose.ps1
```

Por defecto espera hasta 60 segundos.

Para esperar más:

```powershell
powershell -ExecutionPolicy Bypass -File .\GXW-Tools\scripts\gxworks2_write_autoclose.ps1 -WaitSeconds 180
```

Luego en GX Works2:

1. `Online -> Write to PLC`;
2. seleccionar los datos;
3. `Execute`;
4. el helper marca el checkbox cuando aparece la ventana de progreso.

## Fail closed

El helper:

- sólo actúa sobre una ventana cuyo título corresponde a `Write to PLC`;
- sólo modifica un control de tipo CheckBox;
- exige que el nombre del control coincida con el texto esperado;
- si no encuentra el control dentro del timeout, termina con error;
- no hace clic en `Execute`, `Yes`, `Close` ni ninguna acción de transferencia;
- no modifica el `.gxw`.

Si una versión/localización futura de GX Works2 cambia el texto o la estructura del diálogo, hay que capturar esa variante y ampliar los patrones conscientemente; no se debe hacer click por coordenadas.

## Regla futura

Cuando un usuario diga que cambió una preferencia de GX Works2 y el GXW parece distinto:

1. guardar copia A y B;
2. comparar tamaño y SHA-256;
3. si son idénticos, tratar el cambio como preferencia externa;
4. si difieren, usar GXW-Tools para localizar qué stream lógico cambió antes de implementar soporte.

