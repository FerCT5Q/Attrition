# Modelo C + QVoice: metodología y proceso de construcción

**Fecha del documento:** 12-oct-2026. **Clasificación:** `presentation` — documentación compartible, sin datos individuales.

**Versión documentada:** `engineering-c-qvoice-20261008-v1`, identificada como **CQ**, sin calibración posterior adicional de R6. Es el modelo elegido el 10-oct-2026 según la [decisión vigente](../../docs/context/model-selection-current.md). El ajuste final tiene corte de conocimiento al **7-sep-2026**.

CQ estima el riesgo de salida voluntaria en los siguientes seis meses. Conserva el modelo C de información laboral y añade una corrección basada en QVoice. Después se promedian los riesgos dentro de grupos interpretables para ordenar su prioridad. El [diccionario de variables](variables_del_modelo_cq.md) detalla cada entrada y su transformación.

## 1. Población, unidad de análisis y objetivo

La población incluye empleados **Employee, Regular, activos, de Engineering y excluyendo RF360**, según su situación en cada snapshot. Un snapshot es una foto del cierre fiscal mensual; sus fechas no coinciden necesariamente con el último día del mes calendario.

La unidad de análisis es **persona × snapshot**. La misma persona puede aparecer en varios meses, con la información laboral conocida en cada foto. También se incluyen personas sin una respuesta utilizable de QVoice.

| Elemento | Definición utilizada |
|---|---|
| Objetivo mensual de entrenamiento, `y_next` | Indica si hubo una salida voluntaria después del snapshot y hasta el siguiente snapshot, inclusive. |
| Objetivo de evaluación, `y_6m` | Indica si hubo una salida voluntaria después del snapshot y hasta seis meses después, inclusive. |
| Predicción, `R6` | Probabilidad acumulada de salida voluntaria en esos seis meses, calculada a partir de seis riesgos mensuales. |
| Madurez de la etiqueta | Se usa una etiqueta sólo cuando su intervalo ya terminó antes o en el corte correspondiente. Una foto sin seguimiento completo no se convierte en un caso sin salida. |

Las salidas de otros tipos cuentan como ausencia de salida voluntaria en esta formulación binaria. No se ajustó un modelo de riesgos competitivos. La definición implementada está en la [consulta congelada de CQ](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/source/queries/profiles/engineering_model_c_qvoice_person_month_20261008.sql).

## 2. Cómo se incorporó QVoice entre meses

**Sí: se reutilizó la misma respuesta anual de cada persona en los snapshots elegibles del año siguiente.** Se repite su representación como variable explicativa; cada mes sigue teniendo su propia información laboral y su propio intervalo de salida. No se trata de nuevas respuestas mensuales ni de asignar el promedio del equipo a todas las personas.

| Encuesta anual | Snapshots en los que se permite usarla | Fin de vigencia |
|---|---|---|
| QVoice 2024 | Desde el 1-ene-2025 | Antes del 1-ene-2026 |
| QVoice 2025 | Desde el 1-ene-2026 | Antes del 1-ene-2027; en esta corrida sólo hay datos hasta el corte de septiembre de 2026. |
| QVoice 2026 | Desde el 1-ene-2027 | Fuera del alcance temporal de este modelo. |

Esta asignación procede de una **política anual aprobada**. No demuestra la fecha real en que se publicaron o estuvieron disponibles las respuestas. Véase la [política temporal congelada](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/source/config/qvoice_annual_lag_policy_20261008.json).

El enlace sigue estas reglas:

1. Se elige la encuesta que corresponde al año del snapshot, usando una llave de enlace interna.
2. Se exige continuidad del episodio laboral desde el ancla de esa encuesta. Para 2024 y 2025, el ancla es el 1 de enero de cada año: `service_date` debe ser conocida y anterior o igual al ancla, y no debe existir una terminación registrada entre el ancla y la foto.
3. Si no se acredita esa continuidad, se usa el estado `different_employment_episode`. Es un fallo de la comprobación de continuidad, no una confirmación automática de recontratación.
4. La siguiente encuesta reemplaza a la anterior **aunque la persona no tenga una respuesta enlazable en la nueva**. No se recupera indefinidamente la respuesta anterior.
5. Se excluye por completo una llave duplicada en la fuente de encuesta, incluso si las respuestas duplicadas coinciden. Los faltantes, las respuestas inválidas y la falta de enlace se distinguen de una respuesta no favorable.

Las personas sin respuesta permanecen en el modelo y reciben la corrección aprendida para su estado de ausencia. No se les imputa una respuesta promedio. Por eso, el efecto de QVoice puede recoger tanto contenido de respuestas como patrones de disponibilidad.

### Qué significa «promedio de QVoice»

El campo `qv_mean33` es el **porcentaje de indicadores favorables entre 33 preguntas de la misma persona y encuesta**. Exige que las 33 sean válidas. Se transforma en seis bandas antes de entrar al modelo. No es un promedio de respuestas Likert ni una media por grupo.

Este resumen anual también se reutiliza entre los meses elegibles. Incluye preguntas que pueden aparecer, además, como entradas individuales de la corrección; ese solapamiento se explica en el diccionario.

## 3. Arquitectura: C fijo más una corrección QVoice

El modelo utiliza un enlace **complementary log-log**, abreviado **cloglog**. La corrección QVoice se suma al predictor de C antes de convertirlo en probabilidad:

```text
eta_CQ(m) = eta_C(m) + alpha_Q + suma(beta_Q × indicadores de categorías QVoice)
h_m       = 1 - exp(-exp(eta_CQ(m)))
R6        = 1 - producto, durante seis intervalos, de (1 - h_m)
```

`eta_C(m)` resume la información laboral del modelo base. `alpha_Q` es un intercepto adicional y los demás coeficientes ajustan el riesgo según las categorías de QVoice. **Los coeficientes de C permanecen fijos durante el ajuste de CQ**: la corrida registra cero reajustes de la base.

Dentro de una proyección R6 sólo avanza el mes calendario. Las demás variables laborales y la corrección QVoice se mantienen en el valor del snapshot inicial durante los seis intervalos. En particular, la proyección no incorpora una nueva encuesta a mitad del horizonte. Cuando se evalúa una nueva foto, se vuelven a tomar sus datos y la encuesta elegible en esa fecha.

El CQ elegido usa esta acumulación directamente. Aunque el archivo contiene controles y calibradores diagnósticos, **no se aplica el escalar posterior de R6** en la versión elegida.

## 4. Construcción del modelo C

La base procede de `engineering-model-c-20261008-v2` y se construyó con historia laboral desde julio de 2020:

1. Se preparó una tabla temporal de persona y snapshot con categorías laborales, eventos históricos y etiquetas maduras.
2. Se partió de **21 términos candidatos**. Un filtro L1 sobre el objetivo mensual propuso conjuntos de variables; se conservaron familias completas de categorías y los términos principales de las interacciones seleccionadas.
3. Cada conjunto se reajustó con el enlace cloglog y regularización L2. El filtro inicial era logístico; la predicción final de C es cloglog.
4. La selección utilizó dos validaciones temporales internas: menor log-loss a seis meses, con restricciones de Brier y ranking, y preferencia por menos términos dentro del margen de parsimonia declarado.
5. El procedimiento se evaluó en cuatro orígenes externos: febrero y agosto de 2024, y febrero y agosto de 2025.

El C archivado que utiliza el CQ final contiene **17 términos: 16 efectos principales y una interacción de nivel × antigüedad**. Su origen es **1-ago-2025** y su última etiqueta de entrenamiento termina el **27-jul-2025**. No se realizó un nuevo ajuste de C a septiembre de 2026; lo que se actualizó entonces fue la corrección QVoice.

La selección de C exploró los conjuntos propuestos por el filtro, no todas las combinaciones posibles de variables. Los parámetros efectivos están en la [configuración congelada de C v2](../../output/analysis/engineering/20261008/model-c-v2/frozen-config.json).

## 5. Selección y ajuste de la corrección QVoice

La corrección utiliza los snapshots de 2025 y 2026 y aprende del objetivo **mensual** `y_next`. Para cada corte:

1. Se reservan los **dos últimos intervalos mensuales completos** anteriores al corte para seleccionar la corrección. El entrenamiento inicial utiliza etiquetas que ya habían madurado al comienzo de esos intervalos.
2. Se restaura el C que estaba disponible antes de la validación interna y se mantiene fijo como offset.
3. Se prueban los **255 subconjuntos no vacíos de ocho bloques**: Q4, Q12, Career, promedio de 33, Engagement, Connection, Wellbeing y Confidence.
4. Como diagnóstico se prueban cinco alternativas PCA, con 1, 2, 3, 5 y 10 componentes. Tanto los subconjuntos como PCA se comparan con L2 de **0.1, 1 y 10**: **780 ajustes por corte**.
5. Se elige el menor **Brier mensual** en validación. Los desempates favorecen menos parámetros, mayor penalización y un identificador estable.
6. Se vuelve a estimar la corrección elegida usando **todas las etiquetas mensuales maduras antes del corte**, incluido el tramo que sirvió para selección. Se usa como base el C disponible al origen de ese ajuste.

| Corte de la corrección | Snapshots de selección interna | Última etiqueta mensual madura del reajuste |
|---|---|---|
| 1-ago-2025 | 25-may-2025 y 29-jun-2025 | 27-jul-2025 |
| 1-ene-2026 | 26-oct-2025 y 23-nov-2025 | 28-dic-2025 |
| 7-sep-2026, ajuste final | 28-jun-2026 y 26-jul-2026 | 23-ago-2026 |

En el primer corte, la selección interna usó el C de febrero de 2025 y el reajuste externo usó el C de agosto de 2025. En los otros dos cortes, ambos pasos usaron el C de agosto de 2025. Así se evita atribuir a la validación interna un modelo base que todavía no estaba disponible.

Los **2340 ajustes de búsqueda** convergieron según los artefactos archivados. Son ajustes de búsqueda; los reajustes finales y los controles son operaciones adicionales. PCA no fue seleccionado en ninguno de los tres cortes.

La selección de bloques cambió con el tiempo. En septiembre quedaron **Career, promedio de 33, Wellbeing Q8/Q10/Q11 y Confidence Q13/Q17**, equivalentes a siete campos QVoice. En enero de 2026, la corrección se entrenó con QVoice 2024 y se evaluó sobre snapshots que ya utilizaban QVoice 2025: esa prueba también implica transporte entre encuestas.

## 6. Evaluación temporal y controles

Cada modelo histórico se ajustó antes del periodo que se utilizó para medir sus resultados:

| Periodo evaluado | Fotos efectivas | Número de fotos | Último cierre de seguimiento R6 |
|---|---|---:|---|
| Agosto–diciembre de 2025 | 24-ago-2025 a 28-dic-2025 | 5 | 28-jun-2026 |
| Enero–febrero de 2026 | 25-ene-2026 y 22-feb-2026 | 2 | 22-ago-2026 |

Las cifras resumidas dan **igual peso a los dos periodos**, aunque uno tenga más snapshots. Las observaciones y las salidas pueden aparecer en varias ventanas superpuestas; sus sumas no representan personas o salidas únicas de una cohorte conjunta.

La incertidumbre se estimó con **500 repeticiones de bootstrap pareado por persona**, manteniendo juntos todos sus meses. Los intervalos están condicionados a los modelos, grupos y prioridades ya seleccionados; no repiten toda la búsqueda de variables en cada remuestreo.

Se compararon C intacto, C con un intercepto actualizado, C con estados de disponibilidad de QVoice y CQ con el contenido de las respuestas. Estos controles ayudan a distinguir una actualización de la tasa general, el patrón de respuesta y la información de la encuesta. También se probaron escalares de R6 como diagnóstico separado. No son variables adicionales del CQ elegido.

## 7. Cómo se forman y priorizan los grupos

Los grupos utilizan **antigüedad × salidas previas del equipo × nivel**, con categorías más amplias que algunas entradas del predictor. QVoice modifica el riesgo estimado y puede cambiar el orden de los grupos; no forma parte de su nombre ni de sus cortes.

En cada snapshot se promedian las predicciones R6 de quienes integran cada grupo y se ordenan los grupos de mayor a menor riesgo. Para priorizar son elegibles los grupos con **al menos 300 personas en esa foto**. Los grupos menores siguen formando parte de la población y del denominador de evaluación.

El escenario central cubre **30% de toda la población**. Si el último grupo cruza ese límite, recibe un peso fraccional uniforme. Si hay grupos empatados en riesgo, se tratan como un bloque. Esto permite comparar modelos con la misma capacidad exacta sin ordenar personas dentro del grupo. Es una convención de evaluación; no describe una lista operativa de individuos seleccionados. También se evaluaron capacidades de 20% y 40%.

La publicación de tasas y detalles utiliza además umbrales de al menos 30 personas y 30 personas distintas con evento, según la cohorte publicada.

## 8. Qué resultados respaldan la elección

Comparación sobre los dos periodos anteriores, con prioridad del 30%:

| Métrica | C | CQ |
|---|---:|---:|
| Porcentaje de salidas contenido en la población priorizada | 42.4% | 43.1% |
| Log-loss R6 × 1000; menor es mejor | 138.8 | 137.7 |
| PR-AUC; mayor es mejor | 4.9% | 5.5% |
| Tasa de salida voluntaria observada dentro de la prioridad | 4.5% | 4.6% |

**El 43.1% tiene como denominador todas las salidas observadas**: es la proporción que quedó dentro de los grupos priorizados, cuya cobertura ponderada era 30%. La tasa de salida dentro de esa prioridad fue 4.6%. Son denominadores distintos.

La mejora media de captura fue **0.7 puntos porcentuales**, con IC95 **[0.2, 1.1]**. CQ ganó en agosto–diciembre de 2025 y empató con C en enero–febrero de 2026. El error absoluto medio de las tasas por grupo y snapshot, ponderado por la población priorizada, bajó **2.3% relativo**. Esa mejora promedio no implica que todas las estimaciones de grupos hayan mejorado.

El experimento original exigía ganar captura en ambos periodos: **CQ no cumplió esa regla formal**. La decisión posterior del 10-oct-2026 lo eligió por el balance de captura, error e interpretabilidad, conservando la limitación. La nota original y la elección posterior corresponden a momentos distintos; la elección no convierte el resultado anterior en un cumplimiento de la regla.

Estas métricas pertenecen a los **ajustes históricos guardados en `folds/`**. El artefacto final de septiembre tiene otra corrección y **sus coeficientes todavía no cuentan con evaluación posterior a su ajuste**. El proyecto sigue en selección de modelo; esta documentación no acredita un piloto iniciado.

## 9. Límites que acompañan la metodología

- La evidencia es retrospectiva y los periodos ya habían sido explorados. No demuestra efectos causales ni cuántas salidas evitaría una intervención.
- La disponibilidad de QVoice se asigna por política anual. La redacción de Career en 2024 difiere de la posterior y su equivalencia se mantiene como supuesto exploratorio.
- La cobertura de respuestas es incompleta. Los estados de ausencia conservan población, pero pueden reflejar diferencias de participación, enlace o historia laboral.
- El promedio de 33 contiene las cinco preguntas individuales de Wellbeing y Confidence del ajuste final. Hay información superpuesta y estados de ausencia redundantes; L2 permite ajustar el modelo, pero no identifica efectos causales separados de cada pregunta.
- C utiliza proxies y campos almacenados: recontratación, capa organizativa y comp ratio tienen los límites descritos en el diccionario. IOS usa fecha efectiva; no se conoce la fecha real de publicación de cada evento. Los datos históricos pueden contener revisiones posteriores.
- Los intervalos entre snapshots fiscales no siempre duran lo mismo. Se conserva la convención mensual del modelo, sin un ajuste específico por duración diaria.

## 10. Fuentes y alcance de esta revisión

La corrida documentada se ejecutó el **8-oct-2026**, con conocimiento hasta el 7-sep-2026 y la población definida en la sección 1. Esta revisión del 12-oct cotejó documentación, código congelado, parámetros y agregados archivados; no volvió a consultar la base ni a entrenar modelos.

| Fuente | Qué permite comprobar |
|---|---|
| [Decisión vigente](../../docs/context/model-selection-current.md) | Identidad de CQ, elección posterior y estado del ajuste final. |
| [Configuración de CQ](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/frozen-config.json) y [de C](../../output/analysis/engineering/20261008/model-c-v2/frozen-config.json) | Población, cortes, búsquedas, penalizaciones y reglas de evaluación. |
| [Consulta CQ archivada](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/source/queries/profiles/engineering_model_c_qvoice_person_month_20261008.sql) | Construcción de variables laborales, continuidad de episodio y etiquetas. |
| [Constructor CQ](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/source/tools/engineering_model_c_qvoice.py) y [enlace anual de QVoice](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/source/tools/qvoice_horizon_calibration.py) | Offset fijo, selección, reajuste y repetición anual. |
| [Selección de agosto](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/folds/aug_dec_2025/selection.json), [enero](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/folds/jan_feb_2026/selection.json) y [final](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/trained-model/selection.json) | Fechas internas, ganadores y 780 candidatos por corte. |
| [Modelo final](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/trained-model/model.json) | Variables, categorías, referencias, coeficientes y origen de C. |
| [Resultados](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/results.json) | Métricas por periodo, promedios e intervalos. |
| [Comprobaciones de entradas](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/qvoice-input-checks.json), [análisis](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/analysis-checks.json) y [artefactos](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/artifact-checks.json) | Reconciliación de población, ausencia de duplicados persona-snapshot, reproducción de C y 98 verificaciones archivadas con resultado `pass`. |

También se comprobó que las 15 copias de fuentes enumeradas en [frozen-sources.json](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/frozen-sources.json) coinciden con sus hashes archivados. Esta verificación documental no constituye un nuevo assessment de variables ni cambia sus scores.
