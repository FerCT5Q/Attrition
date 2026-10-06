# Brechas del assessment QVoice Excel v4 regenerado

Run: `qvoice-excel-v4-20260826-2-final2`

Estado: `validated`

## Alcance y regla de componentes

El run procesa 16 variables y nueve waves. `survey_structure.xlsx` se uso como
diccionario de KPI: se leyeron `question_text`, `kpis` y `driver`, se agruparon
las preguntas por KPI y se resolvieron sus encabezados por texto normalizado en
cada workbook. Los identificadores se usaron solo en memoria para deduplicar
empleado-wave; los artefactos publicados contienen conteos agregados.

Para cada KPI y forma de respuesta:

- Se espera el conjunto de preguntas definido por el diccionario.
- Se calcula el promedio con los componentes validos disponibles.
- `complete` significa que todos los componentes esperados tienen respuesta
  valida.
- `partial` significa que al menos un componente es valido, pero falta otro.
- `missing` significa que no hay componentes validos.
- Valores fuera del dominio binario `0-1` o ordinal `1-5` se cuentan como
  invalidos y no entran al promedio.

La regla de promedio parcial es una decisión técnica exploratoria y no una
confirmación de la definición de negocio. Por eso el reporte mantiene por
separado los conteos de completas y parciales, y los criterios cualitativos
afectados conservan sus límites v4.

## Mapeo del diccionario

| KPI | Preguntas |
|---|---|
| `Engagement` | Q1, Q2, Q3 |
| `Intent to Stay` | Q4, Q12 |
| `Workplace Connection` | Q5, Q6, Q7 |
| `Wellbeing` | Q8, Q9, Q10, Q11 |
| `Confidence` | Q13, Q17 |

## Disponibilidad de headers por wave

La siguiente tabla resume la forma binaria; la forma `-scale` conserva el mismo
histórico de componentes con su propio dominio y disponibilidad.

| Wave | Engagement | Intent to Stay | Workplace Connection | Wellbeing | Confidence |
|---|---:|---:|---:|---:|---:|
| 2019-05-01 | 2/3 | 1/2 | 1/3 | 0/4 | 0/2 |
| 2020 | 2/3 | 1/2 | 1/3 | 0/4 | 0/2 |
| 2023-03-01 | 0/3 | 0/2 | 0/3 | 0/4 | 0/2 |
| 2024-01-01 | 3/3 | 2/2 | 2/3 | 3/4 | 2/2 |
| 2025-01-01 | 3/3 | 2/2 | 3/3 | 4/4 | 2/2 |
| 2026-01-01 | 3/3 | 2/2 | 3/3 | 4/4 | 2/2 |

`Coverage` muestra cada wave individual de 2020. La columna `Notes` incluye
los nombres de componentes, su estado `disponible` o `no disponible`, y los
conteos de respuestas completas, parciales y sin componente valido.

## Impacto en la evaluación

- `Definition` queda limitada cuando el promedio depende de un subconjunto o
  cuando la formula y la elegibilidad no tienen aprobación de negocio.
- `Consistency` conserva la brecha cuando cambia el item set, el wording o el
  formato entre waves.
- `History` refleja la historia observada, pero una wave sin componentes no se
  interpreta como una observación utilizable.
- `Join` confirma solo el grain interno de Excel; falta la reconciliación
  temporal agregada contra workforce.
- Los composites de todos los items y las normalizaciones regionales no se
  consideran equivalentes a los KPI del diccionario; tienen reglas de
  derivación independientes y cohortes regionales menores de 30 suprimidas.
- El blocker de gobernanza permanece como `Sensible / restringida`.

## Artefactos y evidencia

- Agregados: `qvoice_excel_aggregate_results_20260826-2.json`.
- Inventario: `qvoice_excel_source_inventory_20260826-2.json`.
- Mapeo: `qvoice_excel_mapping_20260826-2.md`.
- Auditorías: `queries/audits/qvoice_excel_*_20260826-2.sql`.
- Workbook y reportes: `output/assessments/qvoice-excel-v4-20260826-2-final2/`.
