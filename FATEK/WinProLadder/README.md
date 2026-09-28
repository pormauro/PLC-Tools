# FATEK WinProLadder Tools

Ingeniería inversa reproducible de proyectos FATEK WinProLadder (.pdw) y sus formatos de intercambio.

## Estado

**Fase 1 — reconocimiento estructural / sólo lectura.**

Confirmado sobre el par mínimo VACIO.pdw vs X0-Y0.pdw:

- ambos tienen 98.871 bytes;
- firma: Fatek WinProladder, File Format 1;
- aparecen FB-PLC, WinProladder, FBs-24MC, Project0, Main_unit1 y Sub_unit1;
- los primeros 290 bytes son idénticos;
- el último byte distinto está en 0x10251; desde 0x10252 al EOF ambos fixtures son idénticos;
- desde 0x120 existe una periodicidad estructural dominante de 1.280 bytes;
- al dividir por 1.280 bytes aparece en ambos el patrón A + 31xB + C + 18xD + E(parcial);
- en los registros repetidos, VACIO XOR X0-Y0 tiene período exacto de 256 bytes;
- como 1.280 = 5 x 256, XOR entre registros alineados del mismo archivo permite cancelar esa capa periódica sin conocer todavía la clave/algoritmo;
- normalizando el registro 0 contra el registro repetido 1, el cambio lógico bruto se reduce de 65.282 bytes a **15 bytes no nulos**.

Esto es evidencia fuerte de una transformación XOR/periódica o equivalente sobre una estructura estable. Todavía no se afirma que todo PDW use un único XOR simple ni que los 15 bytes sean exclusivamente el rung: faltan más fixtures controlados.

## Herramienta actual

    python FATEK/WinProLadder/pdw_tools/analyze.py inspect proyecto.pdw
    python FATEK/WinProLadder/pdw_tools/analyze.py compare VACIO.pdw X0-Y0.pdw

El analizador es estrictamente de sólo lectura.

## Próximos fixtures de alto valor

1. VACIO_SAVE2.pdw: abrir VACIO y guardar otra vez sin cambiar nada.
2. X0-Y0_SAVE2.pdw: guardar otra vez sin cambiar la lógica.
3. X1-Y0.pdw.
4. X0-Y1.pdw.
5. NC_X0-Y0.pdw.
6. Exportación .ldr del proyecto X0-Y0.
7. Exportaciones .tab, .spf y comentarios cuando agreguemos esos contenidos.

Los dos SAVE2 separan datos semánticos de nonce/timestamp/clave de guardado. Los cambios unitarios X/Y permiten mapear operandos e instrucciones.

## Vías oficiales útiles

WinProLadder permite importar/exportar cuatro clases de contenido: comentarios (.txt), tablas (.tab), ladder (.ldr) y páginas de estado (.spf). Esos formatos serán usados como oráculo semántico.

UperLogic también puede importar proyectos WinProLadder .pdw. Lo usaremos como segundo parser independiente para comprobar ladder, tablas y configuración de E/S.

## Meta

PDW <-> FATEK IR <-> IR universal / PLCopen <-> otros fabricantes

La escritura de PDW se habilitará únicamente cuando haya tests de round-trip y validación en WinProLadder.
