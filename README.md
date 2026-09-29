# PLC-Tools

Herramientas para automatización, lectura, transformación y validación de proyectos PLC/HMI, organizadas por fabricante y con una capa común futura para intercambio de lógica.

## Fabricantes

### Coolmay

- **Coolmay/GX-Text-Writer/**: escritura asistida de Ladder en GX Works2/3.
- **Coolmay/GXW-Tools/**: lectura, auditoría, modificación y round-trip de proyectos GX Works2 .gxw.
- **Coolmay/mView-Tools/**: generación, lectura, modificación y validación de proyectos HMI mView (.tag, .sca y .vxf).

### FATEK

- **FATEK/WinProLadder/**: ingeniería inversa y herramientas para proyectos WinProLadder .pdw y formatos de intercambio .ldr/.tab/.spf/.txt.

## Dirección técnica

La IA trabaja sobre una representación declarativa verificable; los adaptadores determinísticos por fabricante son responsables de serialización binaria, tamaños, hashes, CRC, checksums y validación.

    requisitos / documentación
              |
              v
        representación común
          /           \
         v             v
      Coolmay         FATEK
     GXW/mView     PDW/WinProLadder
         \             /
          v           v
          validación / round-trip

La meta no es esconder diferencias entre fabricantes. La lógica IEC reutilizable vive en una capa común; hardware, memoria, tablas, comunicaciones y extensiones específicas permanecen en adaptadores por marca.

## Reglas

- No escribir binarios propietarios a ciegas.
- Todo writer debe partir de un formato suficientemente entendido y contar con round-trip.
- Los fixtures de ingeniería inversa se comparan con cambios unitarios.
- Hechos observados e hipótesis se documentan por separado.
- Los cambios de estructura de repositorio deben conservar contenido e historia Git.

## Estado existente

El flujo Coolmay/GXW ya puede descomponer el contenedor CFB/OLE exterior, abrir el CFB anidado _hdb, interpretar recursos lógicos y reconstruir ambas capas. Las Device Comments del proyecto viven en COMMENT.qcd; Global/Local Labels son estructuras distintas.

Los proyectos mView VXF usan un contenedor vxpm + zlib. Las mutaciones de escenas reconstruyen también el bloque superior 0x10000004 con tamaño + CRC16/MODBUS.

La línea FATEK comenzó con análisis diferencial de VACIO.pdw y X0-Y0.pdw. Ver FATEK/WinProLadder/README.md y FATEK/WinProLadder/docs/FORMAT_PDW.md.
