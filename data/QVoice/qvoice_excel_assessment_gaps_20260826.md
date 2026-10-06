# Brechas del assessment QVoice Excel v4

Run: `qvoice-excel-v4-20260826-1`

Estado: `validated`

## Regla de mapeo KPI

`data/QVoice/survey_structure.xlsx` se trato como el diccionario autoritativo.
Su unica hoja contiene `question_text`, `kpis` y `driver`. Para cada KPI se
buscaron las preguntas asociadas en los encabezados de cada workbook raw.

Para `Intent to Stay`, el diccionario devuelve dos componentes:

- `Q4`: `I see myself working at Qualcomm in a few years`
- `Q12`: `I rarely think about looking for a new job with another company`

El composite se calcula como el promedio de los componentes validos disponibles
en cada respuesta employee-wave. Cuando solo uno esta disponible, el valor se
conserva como respuesta parcial y no como una respuesta completa del KPI. Los
conteos de respuestas completas y parciales se reportan por separado.

## Evidencia observada

En el longitudinal de 2019-2020 se encontro `Q4`, pero no `Q12`, por lo que
esas waves tienen disponibilidad parcial de componentes. En las waves de
2024-2026 se resolvieron ambos componentes; aun asi, existen respuestas con
solo un componente valido. La wave de 2023 no aporto una columna seleccionable
para este mapping.

Para la forma binaria de `Intent to Stay`, el agregado del run contiene:

- Respuestas elegibles: `178106`.
- Respuestas con al menos un componente valido: `173745`.
- Respuestas completas con los dos componentes: `102955`.
- Respuestas parciales: `70790`.
- Valores invalidos: `0`.

La cobertura reciente ponderada fue `97.2656%` y la missingness reciente fue
`2.7344%`. Estos porcentajes describen la disponibilidad del composite en la
poblacion agregada; no convierten una respuesta parcial en una medicion
equivalente a la de dos componentes.

## Impacto en la interpretacion

- `Definition` queda limitada a score 1 hasta aprobar la politica de promedio
  parcial, la regla de deduplicacion y la reconciliacion independiente del
  composite.
- `Consistency` queda limitada a score 1 porque cambia el conjunto de
  componentes entre waves.
- `Source` queda limitado cuando el diccionario no encuentra todos los
  componentes esperados en los workbooks revisados.
- Las respuestas parciales deben identificarse en cualquier modelo o
  comparacion temporal. Conviene reportar una sensibilidad usando solamente
  respuestas completas.

## Otras limitaciones

- El Excel permite validar el grain interno employee-wave y sus conteos, pero
  no aporta por si solo una reconciliacion completa contra el snapshot mensual
  de workforce. `Join` queda como validacion pendiente.
- La forma 1-5 solo tiene historia utilizable reciente; no debe mezclarse
  automaticamente con la forma binaria.
- Los cambios de wording y de item set se conservan como brechas de
  consistencia y no se interpretan como equivalencia automatica entre waves.
- El blocker de gobernanza permanece como `Sensible / restringida`; los
  artefactos publicados contienen solo resultados agregados.

## Consultas y artefactos

- Mapping agregado: `data/QVoice/qvoice_excel_mapping_20260826.md`.
- Inventario fuente: `data/QVoice/qvoice_excel_source_inventory_20260826.json`.
- Resultados agregados: `data/QVoice/qvoice_excel_aggregate_results_20260826.json`.
- Definicion: `queries/audits/qvoice_excel_definition_audit_20260826.sql`.
- Consistencia: `queries/audits/qvoice_excel_consistency_audit_20260826.sql`.
- Grain y join: `queries/audits/qvoice_excel_join_grain_audit_20260826.sql`.
- Workbook y evidencia: `output/assessments/qvoice-excel-v4-20260826-1/`.
