# Attrition project

Este repositorio reúne la definición, evaluación y documentación del proyecto de attrition. La navegación principal es:

- [Documentación](docs/README.md): contexto del modelo y explicaciones por concepto.
- [Inventario histórico v2](config/attrition_candidate_variables.yaml): definición de las 43 variables, pendiente de migración con evidencia v4.
- [Último assessment v2](output/assessments/multiple-variables_assessment_20260812-205647.xlsx): referencia histórica; no debe regenerarse como evaluación vigente.
- [Consultas agregadas](queries/README.md): auditorías read-only y perfiles usados por el assessment.
- [Materiales de referencia](references/README.md): presentación fuente, ejemplos y workbook de Tableau.

## Fuentes de verdad

1. Las reglas de scoring viven en `.codex/skills/evaluate-attrition-variable/references/scoring-rules.yaml`.
2. Las definiciones candidatas viven en `config/attrition_candidate_variables.yaml`; sus scores v2 son históricos hasta migrarlos.
3. Los nuevos resultados v4 viven en `output/assessments/<run-id>/` y deben incluir evidencia calculada para cada 2 cualitativo, derivaciones trazables, manifest y notebooks HTML.
4. `docs/variables/` explica los conceptos, decisiones y limitaciones; no reemplaza el assessment.

El workflow v4 comienza con un `run-request.yaml` mínimo y un preflight de
portafolio basado únicamente en semántica, documentación y metadata. La
evaluación profunda sigue dependencias una variable a la vez; el Excel conserva
el orden original. Cada run validado incluye `portfolio-context`, planes
inmutables `analysis-plan-vN`, evidence ledgers con hashes y `decision.json`.

Los archivos de `output/` son generados. Los binarios de `references/` son insumos y no deben editarse como si fueran resultados.

Consulta `AGENTS.md` para las reglas obligatorias de Redshift, privacidad,
organización y validación semántica.
