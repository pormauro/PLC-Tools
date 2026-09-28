# FATEK

Herramientas y documentación para PLC FATEK.

La primera línea de trabajo es **WinProLadder / formato PDW**, con una metodología de ingeniería inversa basada en diferencias controladas, formatos de intercambio oficiales y validación por round-trip.

## Principios

- No escribir binarios a ciegas.
- Separar hechos observados de hipótesis.
- Preservar fixtures originales mediante hashes.
- Implementar primero lectores/inspectores; habilitar escritura sólo cuando el formato esté suficientemente probado.
- Mantener una representación intermedia independiente del fabricante y adaptadores por marca.

Ver WinProLadder/README.md.
