# QVoice: comparación raw y Redshift

Fecha de revisión: 2026-08-24

## Conclusión actual

Los archivos raw contienen historia anterior a 2026 y mezclan varios formatos
de respuesta. La tabla `hrda.qvoice_survey_data` no es una copia completa de
los Excel raw: es una capa más estrecha y aparentemente transformada.

En Redshift, la columna `survey_launch_date` sólo tiene una wave observada:
`2026-01-07`. Por tanto, para la fecha de esta revisión, la tabla sólo tiene
una wave de encuesta de 2026. Otros campos de fecha no representan waves
adicionales:

| Campo | Fecha observada | Interpretación |
|---|---:|---|
| `survey_launch_date` | 2026-01-07 | Wave de encuesta |
| `hierarchy_date` | 2025-12-15 | Fecha de jerarquía asociada |
| `last_modified_date` | 2026-07-22 | Fecha de modificación |
| `airflow_execution_date` | 2026-07-22 | Fecha de procesamiento |

La tabla contiene 40,721 filas, 40,721 `emp_id` distintos y una sola fecha de
`survey_launch_date`. La fecha anterior de `hierarchy_date` no demuestra que
exista una wave 2025.

La reconciliación de la wave 2026 encontró 42,203 IDs en Excel contra 40,721
en SQL. Excel tiene 41,385 filas con algún `Favorable`; SQL tiene 40,661 filas
con algún binario y 60 filas sin ningún ítem binario poblado. El diagnóstico de
población documenta que SQL no es solamente una población de empleados
regulares: 37,766 son `Employee`/`Regular`/activos y 2,955 son `Employee` no
`Regular`, mientras que todos los 40,721 hacen match con workforce y tienen
`active_status=1` en el snapshot de lanzamiento.

Ninguna de las dos fuentes revisadas tiene un flag explícito de encuesta válida
o elegible. El Excel sí tiene `Response Type`, con valor `EX` en los 42,203
registros, pero SQL no tiene esa columna.

## Assessment Excel v4

El assessment completo de las formas binarias, ordinales, composites y
normalizaciones quedo publicado el 2026-08-26 en
`output/assessments/qvoice-excel-v4-20260826-1/`. Las ocho variables fueron
procesadas y quedaron como `Sensible / restringida`. El diccionario KPI de
`survey_structure.xlsx` se uso para resolver los componentes; las brechas
especificas del run estan en
[qvoice_excel_assessment_gaps_20260826.md](qvoice_excel_assessment_gaps_20260826.md).

- [Workbook v4](../../output/assessments/qvoice-excel-v4-20260826-1/assessment.xlsx)
- [Manifest v4](../../output/assessments/qvoice-excel-v4-20260826-1/manifest.json)
- [Documentacion por variable](../../docs/variables/qvoice-excel/)

### Regeneracion con componentes por KPI

El run validado mas reciente es
`output/assessments/qvoice-excel-v4-20260826-2-final2/`. Procesa 16 variables:
las cinco familias KPI de `survey_structure.xlsx` en forma binaria y 1-5,
career goals, los dos composites de todos los items y sus dos normalizaciones
regionales. Se conservaron nueve waves: 2019-05-01, cuatro observaciones de
2020, 2023-03-01, 2024-01-01, 2025-01-01 y 2026-01-01.

Para cada KPI se calcula el promedio con los componentes validos disponibles
por empleado-wave. Una respuesta con menos componentes que los esperados se
conserva como `partial`; una respuesta sin componentes validos queda como
`missing`. El reporte no presenta el KPI como completo cuando falta una
pregunta: la pestaña `Coverage`, en la columna `Notes`, muestra por wave el
estado de cada componente, el numero de respuestas completas, parciales y sin
componente valido.

| KPI | Componentes del diccionario |
|---|---|
| `Engagement` | Q1, Q2, Q3 |
| `Intent to Stay` | Q4, Q12 |
| `Workplace Connection` | Q5, Q6, Q7 |
| `Wellbeing` | Q8, Q9, Q10, Q11 |
| `Confidence` | Q13, Q17 |

En 2019-2020 la disponibilidad binaria fue parcial para varios KPI; 2023 no
aporto componentes seleccionables; 2024 recupero la mayor parte del mapping y
2025-2026 mostraron el conjunto completo de los cinco KPI. Las respuestas
parciales, el cambio de item set y la ausencia de una reconciliacion temporal
completa contra workforce mantienen los limites de Definition, Consistency y
Join. La forma 1-5 conserva sus propias waves y no se mezcla automaticamente
con la forma binaria.

- [Workbook v4 regenerado](../../output/assessments/qvoice-excel-v4-20260826-2-final2/assessment.xlsx)
- [Manifest v4 regenerado](../../output/assessments/qvoice-excel-v4-20260826-2-final2/manifest.json)
- [Resultados agregados](qvoice_excel_aggregate_results_20260826-2.json)
- [Inventario de componentes](qvoice_excel_source_inventory_20260826-2.json)
- [Mapeo documentado](qvoice_excel_mapping_20260826-2.md)
- [Brechas del run](qvoice_excel_assessment_gaps_20260826-2-final2.md)
- [Documentacion por variable](../../docs/variables/)

## Inventario local

Se revisaron las hojas principales de datos raw. Las dimensiones son las
dimensiones declaradas por Excel e incluyen la fila de encabezados; no deben
interpretarse automáticamente como filas deduplicadas de empleados.

| Archivo | Hoja | Filas declaradas | Columnas |
|---|---|---:|---:|
| `Longitudinal Pulse File - May 2019 to June 2022.xlsx` | `Raw Data` | 132,713 | 153 |
| `March 2023 Pulse_raw data.xlsx` | `Raw data` | 7,315 | 153 |
| `Jan 2024 Qvoice raw data.xlsx` | `Raw data` | 36,808 | 255 |
| `Jan 2025_Qvoice_raw data.xlsx` | `Raw data` | 37,838 | 310 |
| `Jan 2026 Qvoice_raw data.xlsx` | `Raw data` | 42,204 | 337 |

También existen hojas auxiliares con pivots, análisis, códigos de ítems,
segmentaciones y temas de texto. No se trataron como una segunda tabla raw.

## Diferencia de formato

La muestra agregada de las primeras 1,000 filas de cada hoja principal mostró
los siguientes tipos de campos:

| Formato observado en raw | Evidencia agregada |
|---|---|
| Pregunta original | Celdas de texto en campos de pregunta |
| `Favorable` / `Unfavorable` | Campos numéricos binarios `0/1` |
| Escala `1-5` | Campos numéricos con rango observado `1` a `5` |
| `Response Type` | Campo de texto categórico |
| Sentiment score | En la wave de marzo de 2023, campo numérico con rango observado `-2` a `2` |

La muestra no publica valores individuales. La revisión completa de estructura
identificó además campos derivados y hojas de análisis en los workbooks 2024,
2025 y 2026.

En contraste, `hrda.qvoice_survey_data` tiene 59 columnas: 53 ítems
estructurados, `emp_id`, fechas y metadatos de procesamiento. La auditoría de
dominio ejecutada sobre los 53 ítems encontró:

- 53 de 53 columnas con exactamente dos valores no nulos observados.
- Mínimo `0` y máximo `1` en cada columna.
- Cero valores no binarios entre los valores no nulos.
- Tipo SQL `smallint` para los 53 ítems.

La interpretación operativa es que Redshift conserva una codificación binaria
de los ítems estructurados, mientras que los raw conservan preguntas originales
y distintas representaciones, incluida la escala 1-5. La correspondencia
exacta entre cada columna raw y cada columna de Redshift todavía requiere
lineage o una reconciliación agregada por wave; no debe asumirse sólo por el
nombre de la columna.

## Fuentes y consultas

- Inventario de columnas Redshift:
  `queries/audits/qvoice_survey_data_column_inventory_20260821.sql`
- Disponibilidad por año de `survey_launch_date`:
  `queries/audits/qvoice_wave_year_availability_20260821.sql`
- Disponibilidad de todos los campos de fecha:
  `queries/audits/qvoice_all_date_fields_year_availability_20260821.sql`
- Auditoría de dominio de los 53 ítems:
  `queries/audits/qvoice_response_domain_audit_20260824.sql`
- Auditoría de ausencia de columnas de comentario o texto en la tabla:
  `queries/audits/voice_table_metadata_audit_20260820.sql`
- Reconciliación binaria Excel vs SQL:
  `data/QVoice/qvoice_2026_sql_excel_reconciliation_20260824.md`
- Diagnóstico de población y filtros:
  `data/QVoice/qvoice_2026_population_filter_diagnostic_20260824.md`
- Auditoría de población y flags:
  `queries/audits/qvoice_2026_population_filter_diagnostic_20260824.sql`
- Seguimiento de respuestas y `employee_type`:
  `queries/audits/qvoice_2026_response_population_and_employee_type_followup_20260824.sql`
- Analisis de asociacion binaria con attrition:
  `data/QVoice/qvoice_2026_binary_attrition_analysis_20260824.md`
- Auditoria SQL de asociacion binaria:
  `queries/audits/qvoice_2026_binary_attrition_association_20260824.sql`

## Pendientes

1. Obtener o reconstruir el mapping entre los 53 ítems Redshift y las columnas
   raw (`Favorable`, `Unfavorable`, pregunta original o escala).
2. Confirmar si la tabla Redshift fue diseñada para almacenar el flag favorable,
   el desfavorable o una codificación distinta.
3. Definir si las waves 2019-2025 deben incorporarse a una tabla histórica y
   conservar `survey_launch_date`, wave, población elegible y reglas de
   deduplicación.
4. Reconciliar conteos agregados de filas, respondentes y valores poblados por
   wave antes de usar un promedio de todos los ítems.
