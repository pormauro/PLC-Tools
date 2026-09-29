# HMI Project Spec

Esta carpeta define el contrato entre una IA/diseñador y los compiladores binarios mView.

## Idea central

La IA produce JSON. No produce `.tag` ni `.sca` directamente.

```text
prompt + PLC + documentación
          ↓
          IA
          ↓
   hmi_project.json
          ↓
   JSON Schema gate
      ↙         ↘
 .tag compiler  .sca compiler
```

## Ventajas

- auditable;
- versionable en Git;
- testeable;
- repetible;
- permite comparar cambios de HMI sin hacer diff binario;
- separa intención de diseño de serialización mView;
- permite reemplazar el modelo IA sin tocar el backend binario.

## Archivo

- `hmi_project.schema.json` — esquema inicial v1.
- `estampadora.example.json` — ejemplo reducido del proyecto actual.

El esquema va a evolucionar a medida que se decodifiquen más propiedades de widgets mView.
