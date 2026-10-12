# Modelo C + QVoice: variables utilizadas y forma de inclusión

**Fecha del documento:** 12-oct-2026. **Clasificación:** `presentation` — documentación compartible, sin datos individuales.

**Modelo:** `engineering-c-qvoice-20261008-v1`, versión **CQ sin calibración adicional de R6**, elegida el 10-oct-2026. Se documenta el [artefacto final con corte 7-sep-2026](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/trained-model/model.json). La [metodología complementaria](metodologia_y_construccion_cq.md) explica la construcción y evaluación.

El modelo final contiene **17 términos de C y 7 campos QVoice**. Los términos de C incluyen 16 efectos principales y una interacción. Los siete campos QVoice proceden de cuatro bloques seleccionados. Esta cuenta no equivale a preguntas independientes: el promedio de 33 ya contiene varias de las preguntas individuales.

## 1. Reglas comunes de inclusión

La población es Engineering, Employee, Regular, activa y sin RF360 en cada snapshot. La unidad es persona × foto mensual. Se incluyen personas con y sin respuesta utilizable de QVoice.

Las variables finales se codifican como **categorías con indicadores binarios por categoría**, también llamados one-hot. Se omite una categoría de referencia por campo, elegida por su frecuencia en el entrenamiento correspondiente. Los valores numéricos de las bandas no se introducen como una pendiente lineal ni se estandarizan.

El código distingue categorías desconocidas o anteriores a la disponibilidad de una fuente. Sólo aprende coeficientes para categorías observadas al entrenar. **Una categoría nueva en predicción aporta cero en las columnas de ese campo**, igual que su referencia; no se estima un coeficiente nuevo para ella.

La parte C conserva **105 coeficientes, incluido su intercepto**, ajustados con origen 1-ago-2025. La corrección QVoice final estima **33 coeficientes, incluido un intercepto adicional**. Los coeficientes de C permanecen fijos. El número de parámetros es mayor que el de variables porque cada campo genera varios indicadores.

## 2. Variables laborales de C que permanecen en CQ

Salvo IOS y el mes calendario, las entradas proceden de `hrda.post_hire_monthly_worker_dtls`. La columna «Construcción» resume el recorrido desde la fuente histórica hasta el término del modelo. Las bandas consecutivas incluyen el límite inferior y excluyen el superior.

| Término y concepto | Construcción y representación | Regla temporal o límite de interpretación |
|---|---|---|
| `level_grouped` — nivel | Etiqueta `level_grouped` de la foto → categoría. El encoder final conserva ocho etiquetas: códigos 1, 2, 3, 5, 6, 7, 8 y `Misc`. | Se usa el nivel registrado en esa foto; los códigos no se tratan como una escala numérica continua. |
| `tenure_playbook_band` — antigüedad en Qualcomm | `original_hire_date` → meses hasta la foto → bandas <1, 1 a <2, 2 a <3, 3 a <5, 5 a <10 y 10+ años. | Utiliza fecha de contratación original, no `service_date`. Fecha ausente o posterior a la foto → desconocido. El cálculo usa `DATEDIFF(month)`. |
| `calendar_month` — estacionalidad | Mes calendario de `snapshot_date` → doce categorías. | Es la única variable que avanza dentro de una proyección R6; no se incluyó una tendencia de año. |
| `manager_changes_12m` — cambios de manager | Registros con `manager_change = 1` → conteo de fechas distintas `manager_change_date` en los 12 meses previos → 0, 1 o 2+. | La fecha del evento y la foto donde se registra deben ser anteriores o iguales al snapshot evaluado. Sin eventos encontrados se codifica 0. |
| `team_exits_12m` — salidas voluntarias previas del equipo | Salidas voluntarias en los 12 meses previos → manager de la última foto activa anterior a cada salida, dentro de tres meses → conteo de salidas asociadas al manager actual → 0, 1 o 2+. | Excluye la propia persona y exige que la salida ya estuviera registrada en el snapshot. Sin manager → desconocido. Es un conteo, no una tasa normalizada por tamaño del equipo. |
| `direct_reports_band` — reportes directos propios | `reg_non_intern_dir_reports` → 0, 1–5 o 6+. | Describe los reportes directos de la persona, no el número de reportes de su manager. Se toma de la foto; nulo → desconocido. |
| `time_since_promotion_band` — tiempo desde promoción | Última `promotion_date` con `is_promo = 1`, conocida en la foto y desde `service_date` cuando existe → <1, 1 a <2, 2 a <3 o 3+ años. | Sin promoción registrada se distingue contratación reciente por antigüedad desde `service_date`, falta de fecha y `sin promo en historial` para contrataciones anteriores al 1-ago-2020. Esta última categoría no significa «nunca promovido». |
| `rehire` — proxy de recontratación | Comparación de fechas → `yes` si `service_date > original_hire_date`; en otro caso `no`. | Fechas ausentes o `service_date` posterior a la foto → desconocido. Es el proxy implementado, no una reconstrucción completa de todos los episodios laborales. |
| `level_x_tenure` — interacción nivel × antigüedad | Cruce de `level_grouped` y `tenure_playbook_band` → indicadores de combinaciones observadas. | Permite que el patrón por antigüedad varíe con el nivel. Las combinaciones donde algún término principal está en su referencia se agrupan como `ref`; se conservan ambos efectos principales. |
| `prior_experience_band` — experiencia previa a Qualcomm | Valor almacenado `prior_qc_work_years` → <1, 1 a <3, 3 a <5, 5 a <10 o 10+ años. | Nulo o negativo → desconocido. Se usa el dato registrado, sin reconstruir empleos anteriores. |
| `time_at_level_band` — tiempo en el nivel | `levelentrydate` → fecha más reciente entre entrada al nivel y `service_date`, cuando esta última existe → meses hasta la foto → <1, 1 a <2, 2 a <3, 3 a <5 o 5+ años. | Antes del 23-oct-2022 → `antes de la fuente`. Entrada ausente o posterior a la foto → desconocido. |
| `ios_12m` — movimientos IOS | `hrda.workers_ios_transfers`, con motivo informado y `effective_date` en los 12 meses previos → `none`, `reorg` o `lateral u otro`. | `lateral u otro` prevalece si algún motivo difiere del patrón de reorganización declarado. Antes del 22-oct-2023 → `antes de la fuente`. Se conoce la fecha efectiva, no la fecha real de publicación; no identifica exclusivamente movilidad voluntaria. |
| `layers_band` — capa organizativa almacenada | `worker_supervisory_organization_level_from_top` → ≤6, 7, 8, 9 o 10+. | Antes del 26-mar-2023 → `antes de la fuente`; nulo → desconocido. No se reconstruyó aquí una cadena jerárquica ni se confirmó profundidad hasta el CEO. |
| `region` — región | Etiqueta `region` almacenada → categoría; vacío → desconocido. | Contexto regional de la foto. No equivale a domicilio ni a una localización personal reconstruida. |
| `comp_ratio_band` — banda del comp ratio registrado | `compa_ratio` → <0.8, 0.8 a <0.9, 0.9 a <1, 1 a <1.1, 1.1 a <1.2 o 1.2+. | Nulo o ≤0 → desconocido. Se utiliza el valor almacenado; este experimento no demuestra su fórmula económica ni expone compensación individual. |
| `acquisition_recorded` — adquisición registrada | Presencia de texto no vacío en `acquisition` → `registrada` o `sin registro`. | Es presencia del registro en la foto. Un vacío no demuestra contratación orgánica ni el indicador representa una adquisición reciente. |
| `transfer_12m` — transferencia registrada | `is_transferred = 1` y `transfer_date` en los 12 meses previos, observada antes o en la foto y desde `service_date` cuando existe → `yes` o `no`. | Antes del 23-oct-2023 → `historia no confirmada`. No debe interpretarse como ausencia de transferencias en esos años ni como un indicador exclusivamente de IOS voluntario. |

Las ventanas de eventos usan `fecha > snapshot − 12 meses` y `fecha ≤ snapshot`. Las reglas específicas de promoción y transferencia acotan además el episodio mediante `service_date`. No se debe extender esa regla a todas las variables por analogía.

Fuentes: [SQL congelado utilizado por CQ](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/source/queries/profiles/engineering_model_c_qvoice_person_month_20261008.sql), [encoder y modelo C](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/source/tools/engineering_model_c.py), [contratos de entrada](../../config/engineering_model_c_input_contracts_20261008.json) y [evidencia de entrada archivada](../../output/analysis/engineering/20261008/model-c-v2/input-evidence/).

## 3. Campos QVoice del ajuste final

El recorrido común es **respuesta binaria de la encuesta anual → validación de dominio y enlace → asignación a los snapshots del año siguiente → categoría en la corrección**. Se utilizan los indicadores favorables de las fuentes de encuesta; no se convierte la escala Likert durante este ajuste.

`v1` significa indicador favorable igual a 1 y `v0` indicador favorable igual a 0. **No favorable no equivale necesariamente a desfavorable**, porque el indicador puede incluir respuestas neutrales en el cero. Ninguno de esos códigos es una etiqueta de salida.

| Campo final | Concepto de la pregunta o resumen | Cómo entra | Referencia del encoder final |
|---|---|---|---|
| `qv_career` | Percepción de que las metas de carrera pueden cumplirse en Qualcomm. | Indicador favorable como categoría, junto con estados de ausencia. Bloque Career. | `v1` |
| `qv_mean33` | Proporción de respuestas favorables entre 33 ítems comparables. | Una de seis bandas, o un estado de ausencia. Bloque promedio de 33. | `different_employment_episode` |
| `qv_Q8` | Sentirse con energía mientras se trabaja. | Indicador favorable como categoría. Bloque Wellbeing. | `v1` |
| `qv_Q10` | Tener suficiente energía después del trabajo para otras actividades. | Indicador favorable como categoría. Bloque Wellbeing. | `v0` |
| `qv_Q11` | Considerar manejable el estrés del trabajo. | Indicador favorable como categoría. Bloque Wellbeing. | `v1` |
| `qv_Q13` | Confianza en el futuro de Qualcomm. | Indicador favorable como categoría. Bloque Confidence. | `v1` |
| `qv_Q17` | Percepción de que Qualcomm realiza los cambios necesarios para competir eficazmente. | Indicador favorable como categoría. Bloque Confidence. | `v1` |

Las referencias son una decisión de codificación basada en frecuencia. Por ejemplo, la referencia `v0` de Q10 no significa que se considere una respuesta deseable. Tampoco la referencia de `qv_mean33` significa que se eliminen las personas con otro estado: cada categoría observada participa en el ajuste.

### Tratamiento temporal y de faltantes

QVoice 2024 se utiliza sólo en snapshots de 2025; QVoice 2025, sólo en snapshots de 2026. El valor anual enlazado se reutiliza en los meses elegibles. La siguiente encuesta reemplaza a la anterior incluso cuando falta respuesta, y se exige continuidad del episodio laboral desde el ancla de la encuesta.

| Estado | Significado en el procesamiento |
|---|---|
| `missing` | Pregunta vacía; para `qv_mean33`, también falta de validez completa de los 33 componentes. |
| `no_linked_row` | No quedó una fila de encuesta enlazable después de los filtros y la exclusión de duplicados. Por sí solo no demuestra que la persona decidiera no responder. |
| `different_employment_episode` | No se acredita continuidad desde el ancla: puede haber una terminación, una fecha de inicio posterior o información de episodio insuficiente. Este estado prevalece sobre la falta de enlace. |
| `no_available_wave` | No hay una encuesta habilitada por la política para esa fecha. |
| `question_absent` | La pregunta no está disponible en esa fuente. |
| `sentinel_255` | La fuente contiene 255; se trata como valor no utilizable, no como respuesta 0. |
| `invalid` | Valor fuera del dominio binario o no interpretable. |

En el encoder **final** los campos binarios tienen `v0`, `v1`, `missing`, `no_linked_row` y `different_employment_episode`. El promedio tiene sus seis bandas y los tres últimos estados de ausencia. Los demás estados están previstos por el parser, pero no tienen un coeficiente específico aprendido en este ajuste final.

La fuente descarta llaves duplicadas completas, sin escoger una de sus respuestas. Cuando existe `Response Type`, el parser admite vacío o `EX` y excluye otros tipos. Los encabezados se emparejan con el mapping documentado de cada año; no se mezclan silenciosamente columnas homónimas.

**Career conserva una limitación semántica:** la pregunta de 2024 comienza con «Overall» y las versiones posteriores no. La configuración permite su transporte exploratorio; no establece que la equivalencia entre años esté demostrada.

Fuentes: [mapping de preguntas](../../output/analysis/engineering/20261008/qvoice-model-b-calibrated-v1/preflight/source-metadata.json), [configuración QVoice congelada](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/source/config/qvoice_model_calibrated_20261008.yaml), [parser](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/source/tools/qvoice_model_data.py) y [enlace a snapshots](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/source/tools/qvoice_horizon_calibration.py).

## 4. Construcción exacta del promedio de 33

Para una misma encuesta anual, si los 33 indicadores son válidos:

```text
porcentaje_favorable = 100 × suma(M01, ..., M33) / 33
```

Todos los ítems pesan igual. La banda se asigna **sin redondear previamente** el porcentaje. Si falta o es inválido cualquiera de los 33, el promedio se marca `missing`; no se cambia el denominador ni se rellena con la media de las preguntas disponibles.

| Categoría almacenada | Intervalo exacto del porcentaje |
|---|---|
| `<50` | Menor que 50% |
| `50–69` | Desde 50% hasta menos de 70% |
| `70–79` | Desde 70% hasta menos de 80% |
| `80–89` | Desde 80% hasta menos de 90% |
| `90–99` | Desde 90% hasta menos de 100% |
| `100` | Exactamente 100% |

Los nombres `M01` a `M33` identifican posiciones en el conjunto comparable; no son los números Q del cuestionario. La siguiente tabla resume en español los textos del mapping archivado. Todos entran mediante `qv_mean33`:

| Componente | Contenido del ítem | Correspondencia Q usada en los bloques |
|---|---|---|
| M01 | Poder cuestionar las maneras tradicionales de hacer las cosas. | — |
| M02 | Poder equilibrar satisfactoriamente trabajo y vida personal. | — |
| M03 | Sentirse cómodo expresando ideas y opiniones diferentes. | — |
| M04 | Recibir un trato respetuoso en el trabajo. | — |
| M05 | Poder plantear inquietudes éticas sin consecuencias negativas. | — |
| M06 | Entender el vínculo entre el trabajo propio y los objetivos de la función. | — |
| M07 | Sentirse cómodo siendo uno mismo en el trabajo. | Q7 |
| M08 | Sentirse alentado a proponer maneras nuevas y mejores de trabajar. | — |
| M09 | Sentirse con energía mientras se trabaja. | Q8 |
| M10 | Sentido de pertenencia a Qualcomm. | Q5 |
| M11 | Confianza en las decisiones del equipo de liderazgo sénior. | — |
| M12 | Confianza en el futuro de Qualcomm. | Q13 |
| M13 | Energía después del trabajo para disfrutar otras actividades. | Q10 |
| M14 | Pensar pocas veces en buscar empleo en otra empresa. | Q12 |
| M15 | Recibir reconocimiento significativo por las contribuciones. | — |
| M16 | Verse trabajando en Qualcomm dentro de algunos años. | Q4 |
| M17 | Entender cómo se determinan las recompensas. | — |
| M18 | Entender qué se necesita para avanzar profesionalmente. | — |
| M19 | Recomendar Qualcomm como un gran lugar para trabajar. | Q1 |
| M20 | Que el puesto aproveche las habilidades y capacidades. | — |
| M21 | Recibir del manager feedback oportuno para mejorar el desempeño. | — |
| M22 | Que el manager ayude a retirar obstáculos para realizar el trabajo. | — |
| M23 | Que el manager apoye el equilibrio entre trabajo y vida personal. | — |
| M24 | Que el equipo busque cambios de procesos para mejorar la productividad. | — |
| M25 | Sentido de logro personal proporcionado por el trabajo. | Q2 |
| M26 | Comunicación de las razones de cambios importantes. | — |
| M27 | Cambios necesarios para competir eficazmente. | Q17 |
| M28 | Motivación para hacer un esfuerzo adicional en el trabajo. | Q3 |
| M29 | Estrés laboral manejable. | Q11 |
| M30 | Cooperación de las personas con quienes se trabaja. | — |
| M31 | Procesos de trabajo que permiten ser productivo. | — |
| M32 | Colaboración eficaz entre equipos. | — |
| M33 | Comunicación abierta y honesta. | — |

**Career no está entre los 33.** En el CQ final, Q8, Q10, Q11, Q13 y Q17 participan tanto en el promedio como con sus propios coeficientes. Q4 y Q12 participan dentro del promedio, pero no tienen coeficientes individuales en septiembre. La regularización L2 limita el ajuste ante variables relacionadas; no convierte estas señales en efectos independientes o causales.

El experimento posterior que retiró esos cinco componentes y usó un promedio de 28 es una variante distinta. No reemplaza al promedio de 33 en el CQ aquí documentado.

## 5. Qué bloques se seleccionaron en cada corte

La tabla distingue las entradas de los modelos históricos de las del ajuste final. «Sí» significa que el bloque fue seleccionado de forma explícita, además de cualquier participación de sus preguntas dentro de un promedio.

| Bloque candidato | Campos del bloque | Agosto de 2025 | Enero de 2026 | Septiembre de 2026, final |
|---|---|---|---|---|
| Q4: permanencia futura | `qv_Q4` | Sí | Sí | Sólo dentro de media33 |
| Q12: búsqueda de otro empleo | `qv_Q12` | Sí | No | Sólo dentro de media33 |
| Career | `qv_career` | Sí | Sí | Sí |
| Promedio de 33 | `qv_mean33` | No | No | Sí |
| Engagement | `qv_Q1`, `qv_Q2`, `qv_Q3` | Sí | Sí | Sólo dentro de media33 |
| Connection | `qv_Q5`, `qv_Q7` | No | No | Sólo dentro de media33 |
| Wellbeing | `qv_Q8`, `qv_Q10`, `qv_Q11` | No | No | Sí |
| Confidence | `qv_Q13`, `qv_Q17` | No | Sí | Sí |
| L2 de la corrección elegida | — | 10 | 1 | 0.1 |
| Número de campos QVoice | — | 6 | 7 | 7 |
| Parámetros QVoice, incluido intercepto | — | 25 | 29 | 33 |

Las cinco alternativas PCA se evaluaron como diagnóstico y no fueron seleccionadas. El campo o bloque seleccionado no implica que su asociación sea causal ni que su coeficiente sea comparable entre cortes con otras referencias y combinaciones.

Fuentes: modelos archivados de [agosto de 2025](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/folds/aug_dec_2025/model.json), [enero de 2026](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/folds/jan_feb_2026/model.json) y [septiembre de 2026](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/trained-model/model.json).

## 6. Cobertura utilizable documentada de QVoice

La corrida del 8-oct-2026 registró la siguiente cobertura después del enlace y del control de episodio, para la población Engineering definida arriba. El denominador es **persona × snapshot**, no personas distintas ni tasa de participación en la encuesta.

- Encuesta 2024: **390263 observaciones**, de las doce fotos entre 26-ene-2025 y 28-dic-2025.
- Encuesta 2025: **288586 observaciones**, de las ocho fotos entre 25-ene-2026 y 23-ago-2026.

Incluye fotos usadas para entrenamiento o proyección, además de las evaluadas. La última foto no tiene etiqueta mensual madura.

| Campo del modelo final | Utilizable con encuesta 2024, snapshots 2025 | Utilizable con encuesta 2025, snapshots 2026 |
|---|---:|---:|
| `qv_career` | 65% | 65% |
| `qv_mean33` | 54.4% | 56.4% |
| `qv_Q8` | 66.4% | 65.4% |
| `qv_Q10` | 66.4% | 65.3% |
| `qv_Q11` | 66.4% | 65.3% |
| `qv_Q13` | 65.9% | 65.5% |
| `qv_Q17` | 65.5% | 64.9% |

La menor cobertura de media33 es coherente con su requisito de 33 respuestas válidas. Las observaciones sin valor utilizable siguen presentes con sus estados de ausencia; no se eliminan del denominador del modelo.

Fuentes: [qvoice-input-checks.json](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/qvoice-input-checks.json), [population.json](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/population.json) y la [consulta archivada](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/source/queries/profiles/engineering_model_c_qvoice_person_month_20261008.sql). Son métricas de la corrida archivada, no una reevaluación actual de coverage o scores.

## 7. Variables para definir grupos y campos auxiliares

Los grupos con los que se comunica la prioridad usan tres dimensiones derivadas. Su codificación es más amplia que la del predictor:

| Dimensión de grupo | Derivación |
|---|---|
| Antigüedad | Las seis bandas de `tenure_playbook_band`; falta de dato se conserva por separado. |
| Salidas previas del equipo | `team_exits_12m` se resume en sin salidas, con salidas o sin dato. |
| Nivel | Los códigos 7 y 8 se agrupan como entrada; 5 y 6 como medio; 1, 2 y 3 como alto; los demás como otro. |

Se cruzan estas dimensiones y se exige un mínimo de 300 personas por grupo y snapshot para que sea elegible para prioridad. QVoice influye en la media de riesgo del grupo y su orden, pero no añade otra dimensión al cruce. Los cortes se implementan en [coarse_keys](../../tools/engineering_playbook_group_selection.py) y la [agrupación utilizada por CQ](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/source/tools/engineering_c_group_selection.py).

| Campo o conjunto auxiliar | Papel; no es una variable predictora adicional del CQ final |
|---|---|
| `y_next`, `y_6m` | Etiquetas de salida para entrenar y evaluar. |
| `label_end`, `r6_end` | Fechas de madurez del seguimiento. |
| `qvoice_wave`, `same_episode_2024`, `same_episode_2025`, `same_episode_2026` | Selección de encuesta y comprobación de continuidad laboral. No entran como coeficientes separados. |
| Llave interna de persona | Enlace y bootstrap pareado; no es predictor ni se publica. |
| `company_tenure_band`, `tenure_julia_band` | Representaciones auxiliares producidas por SQL y retiradas al cargar CQ. La antigüedad predictora es `tenure_playbook_band`. |
| `av_*` | Variables de los controles de disponibilidad, separados de la corrección CQ. |
| `monthly_intercept_control`, `calibrators` | Diagnósticos guardados en el artefacto. El CQ elegido no aplica el escalar adicional de R6. |
| Engineering, Employee, Regular, activo y exclusión de RF360 | Filtros de población; no coeficientes del modelo. |

## 8. Candidatos que no quedaron en esta versión

Del conjunto de 21 términos candidatos de C no quedaron `tenure_x_manager_changes`, `manager_left_6m`, `work_arrangement_group` ni `grade_family`. Que no fueran seleccionados en este ajuste no demuestra que carezcan de información en cualquier otra población o modelo.

En QVoice se excluyeron Q6 y Q9 de los bloques históricos por falta de historia comparable de 2024. Heartbeat, texto libre y comentarios no entraron; la encuesta 2026 quedó fuera por la política anual. La variante con preguntas fijas y media28 tampoco es el CQ elegido.

El [inventario de C](../../config/engineering_model_c_inventory_20261008.json) incluye otros conceptos explorados o pendientes. No debe confundirse ese inventario con la lista efectiva de parámetros de este modelo.

## 9. Comprobación documental

Las listas de las secciones 2 y 3 se cotejaron con `base_model.features` y `correction.encoder.features` del artefacto final; la selección histórica se contrastó con los dos modelos de `folds/`. Las reglas de bandas, faltantes y temporalidad se leyeron en las fuentes congeladas, y las coberturas se tomaron de los agregados de la corrida del 8-oct-2026.

Esta entrega describe **lo que implementó y utilizó esa versión**. No vuelve a validar las definiciones económicas de campos almacenados, no recalifica variables y no reemplaza los límites de sus assessments. Los coeficientes finales de septiembre permanecen sin una evaluación posterior a su ajuste.
