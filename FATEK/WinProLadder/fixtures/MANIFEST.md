# Fixture manifest

Los binarios originales no se modifican. Este manifiesto permite comprobar identidad antes de cualquier experimento.

| Nombre | Semántica | Bytes | SHA-256 |
|---|---|---:|---|
| VACIO.pdw | Proyecto base vacío, FBs-24MCT según configuración del usuario | 98.871 | 72054bbf92dd88c92de0ba79c45cb2fef255bb9675ef2ed338e08b255ee1ddfd |
| X0-Y0.pdw | Mismo proyecto con X0 -> Y0 | 98.871 | ed415db334e916eeec556f6da5df4eecb438ab304bcbe2677be2b1fac9446cb9 |

## Política

Antes de analizar un fixture, verificar tamaño y SHA-256. Los experimentos de escritura, cuando existan, se harán siempre sobre copias derivadas y nunca sobre estos originales.
