# Arquitectura para generación HMI con IA

## Meta

Poder describir una máquina en lenguaje natural, documentación de ingeniería, tabla de I/O y lógica PLC, y producir un proyecto HMI reproducible.

## Contrato recomendado

La IA no genera bytes mView. Genera un **HMI Project Spec** JSON.

Ese spec contiene:

- nombre de proyecto/grupo;
- tags y direcciones PLC;
- tipos y acceso;
- escenas;
- objetos visuales;
- navegación;
- textos;
- estados;
- alarmas;
- parámetros;
- permisos;
- reglas de seguridad.

Después, compiladores determinísticos generan los artefactos binarios.

## Pipeline

```text
PLC + documentación + intención del usuario
                │
                ▼
      AI planner / designer
                │
                ▼
      hmi_project.json
                │
         JSON Schema gate
                │
         ┌──────┴──────┐
         ▼             ▼
  Tag compiler    Scene compiler
      .tag             .sca
         └──────┬──────┘
                ▼
      binary validators
                ▼
            mView import
```

## Reglas

- Nunca permitir que la IA calcule CRC o tamaños manualmente.
- Nunca permitir escritura directa de salidas físicas desde HMI salvo diseño explícitamente auditado.
- Los nombres de tags son el contrato entre PLC, HMI y documentación.
- Los generadores deben ser idempotentes: mismo spec → mismo resultado lógico.
- Todo artefacto generado debe poder volver a parsearse y validarse.
- Los formatos reverse-engineered deben estar cubiertos por fixtures y pruebas.
- Las plantillas binarias deben tratarse como compatibilidad de formato, no como fuente de lógica de negocio.

## Próximos pasos

1. Unificar TAG + SCA detrás de un único modelo `HMIProject`.
2. Agregar catálogo de widgets mView conocidos.
3. Reemplazar selección de objetos por índices con firmas estructurales.
4. Render previo de escenas desde el spec.
5. Generador de spec asistido por IA.
6. Comparador spec ↔ proyecto mView importado.
7. Tests con distintas versiones de mView/Coolmay.
