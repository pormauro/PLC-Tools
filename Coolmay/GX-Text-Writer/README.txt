# GX Text Writer V3 - Ladder Keys

No usa LD/OUT textual. Usa teclas de GX Works:

- [NO M8001] -> F5 + M8001 + Enter
- [NC M200] -> F6 + M200 + Enter
- [COIL M200] -> F7 + M200 + Enter
- [APP MOV K10 D100] -> F8 + MOV K10 D100 + Enter

## Uso
1. Abrí GX Works en Ladder.
2. Hacé clic en una celda vacía.
3. Cargá Test simple.
4. Apretá F8 en el programa.
5. En 3 segundos volvé a hacer clic en GX.

Si GX corre como administrador, ejecutá este programa como administrador.

## Crear EXE
Ejecutá build_exe.bat. Queda en dist\GX_Text_Writer_V3.exe

## Regla obligatoria SET / RST

En el Ladder generado para este flujo, cada dispositivo destino puede aparecer como máximo:

- una sola vez con SET en todo el programa;
- una sola vez con RST en todo el programa.

Ejemplo válido:
- [APP SET M18] aparece una sola vez.
- [APP RST M18] aparece una sola vez.

Ejemplo inválido:
- dos o más [APP SET M18] en rungs distintos;
- dos o más [APP RST M18] en rungs distintos.

Para evitar que vuelva a ocurrir, usar `gx_text_writer_gui_v3_1.py`: V3.1 valida el archivo antes de escribir y bloquea la ejecución si detecta SET o RST duplicados para el mismo dispositivo. El V3 original se conserva como baseline.

Recomendación de arquitectura:
- un único escritor por M/Y;
- preferir máquina de estados con MOV/comparaciones;
- usar SET/RST sólo cuando realmente haga falta enclavar un bit;
- nunca resolver varias condiciones escribiendo el mismo SET/RST desde rungs diferentes.



## V3.1 recomendada

Ejecutar:

- python gx_text_writer_gui_v3_1.py

Para generar EXE:

- build_exe_v3_1.bat

El programa de la estampadora V2 se genera además con política más estricta: **cero SET y cero RST**, y un único escritor para cada COIL/PLS.

## Comparaciones en [APP] / F8

GX-Text-Writer escribe en el editor Ladder mediante F8. Para comparaciones dentro de [APP], usar la sintaxis que acepta el cuadro de instrucción de GX Works2:

16 bits:
- [APP = D0 K10]
- [APP > D0 K10]
- [APP < D0 K10]
- [APP <> D0 K10]
- [APP <= D0 K10]
- [APP >= D0 K10]

32 bits:
- [APP D= D128 K0]
- [APP D> D128 K0]
- [APP D< D128 D130]
- [APP D<> D128 D130]
- [APP D<= D128 D130]
- [APP D>= D128 D130]

IMPORTANTE:
- No usar LDD= / LDD> / LDD< dentro de [APP].
- No usar ANDD= / ANDD> / ANDD< dentro de [APP].
Esos son mnemónicos de lista/instrucción y no son la sintaxis esperada por el cuadro F8 de Ladder en este flujo.

