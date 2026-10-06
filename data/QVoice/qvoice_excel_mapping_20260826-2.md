# Mapeo de QVoice Excel para assessment v4

Fecha de generacion: 2026-08-26

Este inventario se genero leyendo las hojas raw. El extractor usa los identificadores solo en memoria para deduplicar empleado-wave; los artefactos persistidos contienen unicamente conteos y metricas agregadas.

## Diccionario KPI

`survey_structure.xlsx` define las preguntas que componen cada KPI. El promedio de un KPI usa las respuestas validas de sus preguntas disponibles; si falta una pregunta en una wave, se permite un promedio parcial solo como evidencia exploratoria y se registra la brecha.

### `Engagement`

- `Q1`: I would recommend Qualcomm as a great place to work
- `Q2`: My work gives me a sense of personal accomplishment
- `Q3`: Qualcomm motivates me to go above and beyond in my work

### `Intent to Stay`

- `Q4`: I see myself working at Qualcomm in a few years
- `Q12`: I rarely think about looking for a new job with another company

### `Workplace Connection`

- `Q5`: I have a sense of belonging at Qualcomm
- `Q6`: At Qualcomm, the potential for professional growth and success is accessible to everyone, regardless of their personal background (e.g., all demographic attributes, personal characteristics)
- `Q7`: I feel comfortable being myself at work

### `Wellbeing`

- `Q8`: I feel energized when I am working
- `Q9`: I feel empowered to make changes to improve my wellbeing
- `Q10`: I have enough energy after work to enjoy other activities (e.g. socializing, hobbies, exercise)
- `Q11`: The amount of stress in my job is manageable

### `Confidence`

- `Q13`: I have confidence in the future of Qualcomm
- `Q17`: Qualcomm is making the changes necessary to compete effectively

## Formas

- Las variables sin sufijo usan columnas binarias `_favorable` o `_FAV`; el longitudinal tambien conserva un encabezado con sufijo `_S`. Su semantica de negocio no esta confirmada y los valores observados en ese campo son binarios `0/1`.
- Las variables con sufijo `-scale` usan columnas `_1-5 scale`.
- En 2026 se conservan los 53 items que tienen pareja binaria y escala; los cuatro items adicionales de exit survey quedan fuera.
- El promedio exige al menos 70% de los items de la wave y excluye filas con valores invalidos del composite; es una regla tecnica pendiente de aprobacion.
- La normalizacion calcula un z-score poblacional por region y wave; las cohortes menores de 30 no se publican ni se usan para el z-score.

## Inventario por workbook

| Archivo | Hoja | Filas escaneadas | Binarios | Escala 1-5 | Fecha / wave |
|---|---|---:|---:|---:|---|
| `Longitudinal Pulse File - May 2019 to June 2022.xlsx` | `Raw Data` | 132712 | 52 | 0 | Snapshot Date |
| `March 2023 Pulse_raw data.xlsx` | `Raw data` | 7314 | 0 | 0 | Recorded Date |
| `Jan 2024 Qvoice raw data.xlsx` | `Raw data` | 36807 | 52 | 0 | Recorded Date |
| `Jan 2025_Qvoice_raw data.xlsx` | `Raw data` | 37837 | 52 | 52 | wave fija |
| `Jan 2026 Qvoice_raw data.xlsx` | `Raw data` | 42203 | 53 | 53 | Recorded Date |

## Componentes seleccionados

### `Longitudinal Pulse File - May 2019 to June 2022.xlsx`

- `binary_targets`:
  - `intent_1`: I see myself working at Qualcomm in a few years. _S
  - `intent_2`: no disponible
  - `career`: (1.11) Overall, I feel that my career goals can be met at Qualcomm._FAV
- `scale_targets`:
  - `intent_1`: no disponible
  - `intent_2`: no disponible
  - `career`: no disponible
- `kpi_components`:
  - `Engagement` `binary`: (1.13) I would recommend Qualcomm as a great place to work._FAV, My work gives me a sense of personal accomplishment. _FAV, no disponible
  - `Engagement` `scale`: no disponible, no disponible, no disponible
  - `Intent to Stay` `binary`: I see myself working at Qualcomm in a few years. _S, no disponible
  - `Intent to Stay` `scale`: no disponible, no disponible
  - `Workplace Connection` `binary`: no disponible, no disponible, I feel comfortable being myself at work. _FAV
  - `Workplace Connection` `scale`: no disponible, no disponible, no disponible
  - `Wellbeing` `binary`: no disponible, no disponible, no disponible, no disponible
  - `Wellbeing` `scale`: no disponible, no disponible, no disponible, no disponible
  - `Confidence` `binary`: no disponible, no disponible
  - `Confidence` `scale`: no disponible, no disponible

### `March 2023 Pulse_raw data.xlsx`

- `binary_targets`:
  - `intent_1`: no disponible
  - `intent_2`: no disponible
  - `career`: no disponible
- `scale_targets`:
  - `intent_1`: no disponible
  - `intent_2`: no disponible
  - `career`: no disponible
- `kpi_components`:
  - `Engagement` `binary`: no disponible, no disponible, no disponible
  - `Engagement` `scale`: no disponible, no disponible, no disponible
  - `Intent to Stay` `binary`: no disponible, no disponible
  - `Intent to Stay` `scale`: no disponible, no disponible
  - `Workplace Connection` `binary`: no disponible, no disponible, no disponible
  - `Workplace Connection` `scale`: no disponible, no disponible, no disponible
  - `Wellbeing` `binary`: no disponible, no disponible, no disponible, no disponible
  - `Wellbeing` `scale`: no disponible, no disponible, no disponible, no disponible
  - `Confidence` `binary`: no disponible, no disponible
  - `Confidence` `scale`: no disponible, no disponible

### `Jan 2024 Qvoice raw data.xlsx`

- `binary_targets`:
  - `intent_1`: I see myself working at Qualcomm in a few years_favorable
  - `intent_2`: I rarely think about looking for a new job with another company_favorable
  - `career`: Overall, I feel that my career goals can be met at Qualcomm_favorable
- `scale_targets`:
  - `intent_1`: no disponible
  - `intent_2`: no disponible
  - `career`: no disponible
- `kpi_components`:
  - `Engagement` `binary`: I would recommend Qualcomm as a great place to work_favorable, My work gives me a sense of personal accomplishment_favorable, Qualcomm motivates me to go above and beyond in my work_favorable
  - `Engagement` `scale`: no disponible, no disponible, no disponible
  - `Intent to Stay` `binary`: I see myself working at Qualcomm in a few years_favorable, I rarely think about looking for a new job with another company_favorable
  - `Intent to Stay` `scale`: no disponible, no disponible
  - `Workplace Connection` `binary`: I have a sense of belonging at Qualcomm_favorable, no disponible, I feel comfortable being myself at work_favorable
  - `Workplace Connection` `scale`: no disponible, no disponible, no disponible
  - `Wellbeing` `binary`: I feel energized when I am working_favorable, no disponible, I have enough energy after work to enjoy other activities (e.g. socializing, hobbies, exercise)_favorable, The amount of stress in my job is manageable_favorable
  - `Wellbeing` `scale`: no disponible, no disponible, no disponible, no disponible
  - `Confidence` `binary`: I have confidence in the future of Qualcomm_favorable, Qualcomm is making the changes necessary to compete effectively_favorable
  - `Confidence` `scale`: no disponible, no disponible

### `Jan 2025_Qvoice_raw data.xlsx`

- `binary_targets`:
  - `intent_1`: I see myself working at Qualcomm in a few years._Favorable
  - `intent_2`: I rarely think about looking for a new job with another company._Favorable
  - `career`: I feel that my career goals can be met at Qualcomm._Favorable
- `scale_targets`:
  - `intent_1`: I see myself working at Qualcomm in a few years._1-5 scale
  - `intent_2`: I rarely think about looking for a new job with another company._1-5 scale
  - `career`: I feel that my career goals can be met at Qualcomm._1-5 scale
- `kpi_components`:
  - `Engagement` `binary`: I would recommend Qualcomm as a great place to work._Favorable, My work gives me a sense of personal accomplishment._Favorable, Qualcomm motivates me to go above and beyond in my work._Favorable
  - `Engagement` `scale`: I would recommend Qualcomm as a great place to work._1-5 scale, My work gives me a sense of personal accomplishment._1-5 scale, Qualcomm motivates me to go above and beyond in my work._1-5 scale
  - `Intent to Stay` `binary`: I see myself working at Qualcomm in a few years._Favorable, I rarely think about looking for a new job with another company._Favorable
  - `Intent to Stay` `scale`: I see myself working at Qualcomm in a few years._1-5 scale, I rarely think about looking for a new job with another company._1-5 scale
  - `Workplace Connection` `binary`: I have a sense of belonging at Qualcomm._Favorable, At Qualcomm, the potential for professional growth and success is accessible to everyone, regardless of their personal background (e.g., all demographic attributes, personal characteristics)._Favorable, I feel comfortable being myself at work._Favorable
  - `Workplace Connection` `scale`: I have a sense of belonging at Qualcomm._1-5 scale, At Qualcomm, the potential for professional growth and success is accessible to everyone, regardless of their personal background (e.g., all demographic attributes, personal characteristics)._1-5 scale, I feel comfortable being myself at work._1-5 scale
  - `Wellbeing` `binary`: I feel energized when I am working._Favorable, I feel empowered to make changes to improve my wellbeing._Favorable, I have enough energy after work to enjoy other activities (e.g. socializing, hobbies, exercise)._Favorable, The amount of stress in my job is manageable._Favorable
  - `Wellbeing` `scale`: I feel energized when I am working._1-5 scale, I feel empowered to make changes to improve my wellbeing._1-5 scale, I have enough energy after work to enjoy other activities (e.g. socializing, hobbies, exercise)._1-5 scale, The amount of stress in my job is manageable._1-5 scale
  - `Confidence` `binary`: I have confidence in the future of Qualcomm._Favorable, Qualcomm is making the changes necessary to compete effectively._Favorable
  - `Confidence` `scale`: I have confidence in the future of Qualcomm._1-5 scale, Qualcomm is making the changes necessary to compete effectively._1-5 scale

### `Jan 2026 Qvoice_raw data.xlsx`

- `binary_targets`:
  - `intent_1`: I see myself working at Qualcomm in a few years._favorable
  - `intent_2`: I rarely think about looking for a new job with another company._favorable
  - `career`: I feel that my career goals can be met at Qualcomm._favorable
- `scale_targets`:
  - `intent_1`: I see myself working at Qualcomm in a few years._1-5 scale
  - `intent_2`: I rarely think about looking for a new job with another company._1-5 scale
  - `career`: I feel that my career goals can be met at Qualcomm._1-5 scale
- `kpi_components`:
  - `Engagement` `binary`: I would recommend Qualcomm as a great place to work._favorable, My work gives me a sense of personal accomplishment._favorable, Qualcomm motivates me to go above and beyond in my work._favorable
  - `Engagement` `scale`: I would recommend Qualcomm as a great place to work._1-5 scale, My work gives me a sense of personal accomplishment._1-5 scale, Qualcomm motivates me to go above and beyond in my work._1-5 scale
  - `Intent to Stay` `binary`: I see myself working at Qualcomm in a few years._favorable, I rarely think about looking for a new job with another company._favorable
  - `Intent to Stay` `scale`: I see myself working at Qualcomm in a few years._1-5 scale, I rarely think about looking for a new job with another company._1-5 scale
  - `Workplace Connection` `binary`: I have a sense of belonging at Qualcomm._favorable, At Qualcomm, the potential for professional growth and success is accessible to everyone, regardless of their personal background (e.g., all demographic attributes, personal characteristics)._favorable, I feel comfortable being myself at work._favorable
  - `Workplace Connection` `scale`: I have a sense of belonging at Qualcomm._1-5 scale, At Qualcomm, the potential for professional growth and success is accessible to everyone, regardless of their personal background (e.g., all demographic attributes, personal characteristics)._1-5 scale, I feel comfortable being myself at work._1-5 scale
  - `Wellbeing` `binary`: I feel energized when I am working._favorable, I feel empowered to make changes to improve my wellbeing._favorable, I have enough energy after work to enjoy other activities (e.g. socializing, hobbies, exercise)._favorable, The amount of stress in my job is manageable._favorable
  - `Wellbeing` `scale`: I feel energized when I am working._1-5 scale, I feel empowered to make changes to improve my wellbeing._1-5 scale, I have enough energy after work to enjoy other activities (e.g. socializing, hobbies, exercise)._1-5 scale, The amount of stress in my job is manageable._1-5 scale
  - `Confidence` `binary`: I have confidence in the future of Qualcomm._favorable, Qualcomm is making the changes necessary to compete effectively._favorable
  - `Confidence` `scale`: I have confidence in the future of Qualcomm._1-5 scale, Qualcomm is making the changes necessary to compete effectively._1-5 scale

## Resultado agregado por variable

| Variable | Waves | Primera wave | Ultima wave |
|---|---:|---|---|
| `Engagement items` | 9 | 2019-05-01 | 2026-01-01 |
| `Engagement items-scale` | 9 | 2019-05-01 | 2026-01-01 |
| `Intent to Stay items` | 9 | 2019-05-01 | 2026-01-01 |
| `Intent to Stay items-scale` | 9 | 2019-05-01 | 2026-01-01 |
| `Workplace Connection items` | 9 | 2019-05-01 | 2026-01-01 |
| `Workplace Connection items-scale` | 9 | 2019-05-01 | 2026-01-01 |
| `Wellbeing items` | 9 | 2019-05-01 | 2026-01-01 |
| `Wellbeing items-scale` | 9 | 2019-05-01 | 2026-01-01 |
| `Confidence items` | 9 | 2019-05-01 | 2026-01-01 |
| `Confidence items-scale` | 9 | 2019-05-01 | 2026-01-01 |
| `Career goals item` | 9 | 2019-05-01 | 2026-01-01 |
| `Career goals item-scale` | 9 | 2019-05-01 | 2026-01-01 |
| `Average of all Qvoice items` | 9 | 2019-05-01 | 2026-01-01 |
| `Average of all Qvoice items-scale` | 9 | 2019-05-01 | 2026-01-01 |
| `Standardized / normalized within region` | 9 | 2019-05-01 | 2026-01-01 |
| `Standardized / normalized within region-scale` | 9 | 2019-05-01 | 2026-01-01 |

## Limitaciones que pasan al assessment

- Excel no aporta en este flujo un roster oficial de elegibilidad ni una reconciliacion completa al snapshot mensual de workforce; Join queda como validacion pendiente.
- Los cambios historicos de wording y de item set se conservan como metricas de consistencia; no se tratan como equivalencia automatica entre waves.
- La fuente es confidencial y el reporte del assessment debe interpretarse bajo el blocker de gobernanza configurado para survey data.
