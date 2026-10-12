# C + QVoice frente a C

## QVoice mejora la pérdida predictiva de C, pero falta demostrar la mejora conjunta en grupos

Fecha de ejecución: 8-oct-2026. Modo: `presentation`.

Objetivo: identificar grupos donde enfocar acciones de retención, estimando su salida voluntaria a seis meses. Población: Engineering, Employee, Regular, activo, sin RF360. Se conserva la agrupación elegida: **antigüedad × salidas del equipo × nivel**. El modelo C base conserva sus coeficientes.

## Veredicto bajo el criterio declarado

- C + QVoice sin calibración posterior: **no cumple** la regla principal al 30%.
- C + QVoice con escalar R6: **no cumple** esa regla.
- La versión sin calibración cambia la captura media en **0.7 pp**, IC95 [0.2, 1.1]; gana en 1 de dos periodos.
- Su log-loss R6 cambia -0.8% frente a C; un cambio negativo indica menor pérdida.

La regla exige ganar captura en ambos periodos, IC95 medio positivo, errores por grupo y grupo-mes que no empeoren más de 0.1 pp, log-loss y Brier que no empeoren más de 0.5% relativo, y aporte frente al control de disponibilidad. Es una regla retrospectiva, no una promoción automática.

| Comprobación al 30% | C + Q sin calibración | C + Q con escalar R6 |
|---|---|---|
| La captura mejora en ambos periodos | No cumple | No cumple |
| El IC95 del cambio medio de captura queda por encima de cero | Cumple | Cumple |
| El error por grupo queda dentro de la tolerancia | Cumple | Cumple |
| El error grupo-mes queda dentro de la tolerancia | Cumple | Cumple |
| El log-loss queda dentro de la tolerancia | Cumple | Cumple |
| El Brier queda dentro de la tolerancia | Cumple | Cumple |
| Las respuestas capturan más que el control de disponibilidad | Cumple | Cumple |
| Las respuestas tienen pérdida no mayor que el control de disponibilidad | Cumple | Cumple |

Al 30% hay 1 periodo con mejora, 1 empate y 0 derrotas. La ganancia media tiene un intervalo positivo, pero la consistencia temporal exigida por la regla sigue pendiente. **C + QVoice queda como extensión prometedora para validación adicional; C se conserva como referencia.**

El error medio por grupo cambia -2.3% relativo; la diferencia absoluta es pequeña y ambos redondean a 1 pp. El promedio del mayor error publicable por periodo pasa de 2.1 a 2.2 pp. La mejora promedio no garantiza mejores estimaciones en cada grupo.

La calibración adicional conserva la misma captura y apenas cambia las pérdidas: en esta comparación no aporta una ventaja práctica clara sobre C + Q sin calibración posterior.


## Comparación al priorizar al 30%

Promedio con igual peso de dos periodos: fotos de agosto–diciembre de 2025 (cinco fotos) y enero–febrero de 2026 (dos fotos). Cada foto se evalúa por sus siguientes seis meses; la última termina seguimiento en agosto de 2026. No comparar estas cifras directamente con el promedio de cuatro periodos de la selección original de C.

| Modelo | Captura | Estimado en prioridad | Observado en prioridad | Error por grupo | Error grupo-mes |
|---|---:|---:|---:|---:|---:|
| C | 42.4% | 5.2% | 4.5% | 1 pp | 1 pp |
| C + QVoice sin calibración | 43.1% | 5.1% | 4.6% | 1 pp | 1 pp |
| C + QVoice con escalar R6 | 43.1% | 5.1% | 4.6% | 1 pp | 1 pp |
| C con escalar R6 | 42.4% | 5.5% | 4.5% | 1.1 pp | 1.1 pp |
| C con intercepto actualizado | 42.4% | 5.2% | 4.5% | 1 pp | 1 pp |
| C con disponibilidad QVoice | 42.5% | 5.2% | 4.5% | 1 pp | 1 pp |
| C con disponibilidad y escalar | 42.5% | 5.2% | 4.5% | 1 pp | 1 pp |

Captura = salidas observadas en la población priorizada / salidas observadas totales. Los conteos corresponden a persona-snapshot; una persona y su salida pueden contribuir a varias ventanas. Error por grupo = diferencia absoluta de la tasa estimada y observada por grupo, ponderada por personas. Error grupo-mes calcula ese error antes de promediar meses, evitando compensaciones temporales.

![Captura al 30% por periodo](captura-por-periodo.png)

## Estimaciones en toda la población

| Modelo | Log-loss × 1000 ↓ | Brier × 1000 ↓ | PR-AUC ↑ | Lift del 10% ↑ | Estimado R6 | Observado R6 | Error agregado |
|---|---:|---:|---:|---:|---:|---:|---:|
| C | 138.8 | 30.7 | 4.9% | 1.8× | 3.1% | 3.2% | 0.1 pp |
| C + QVoice sin calibración | 137.7 | 30.7 | 5.5% | 2.1× | 3.1% | 3.2% | 0.1 pp |
| C + QVoice con escalar R6 | 137.7 | 30.7 | 5.5% | 2.1× | 3.1% | 3.2% | 0.1 pp |
| C con escalar R6 | 138.8 | 30.8 | 4.9% | 1.8× | 3.3% | 3.2% | 0.1 pp |
| C con intercepto actualizado | 138.8 | 30.7 | 4.9% | 1.8× | 3.1% | 3.2% | 0.1 pp |
| C con disponibilidad QVoice | 139 | 30.8 | 4.9% | 1.8× | 3.1% | 3.2% | 0.2 pp |
| C con disponibilidad y escalar | 139 | 30.8 | 4.9% | 1.8× | 3.1% | 3.2% | 0.1 pp |

El Brier de C + Q cambia -0.2% relativo. El error de calibración agregado aumenta 0.1 pp en promedio, aunque ambos valores mostrados redondean a 0.1 pp.

Log-loss y Brier evalúan la calidad de las probabilidades. Se muestran multiplicados por 1000 para mantener un decimal sin ocultar diferencias; esa escala no cambia las comparaciones. PR-AUC y lift describen el ranking individual usado sólo como diagnóstico interno: no se publica un listado de empleados. Una mejora individual puede quedar diluida al resumirse en los mismos grupos de tres variables.

## Consistencia entre periodos y capacidades

| Periodo de fotos | Personas distintas | Capacidad | C: captura | C + Q: captura | C + Q escalar: captura | C: error grupo-mes | C + Q: error grupo-mes |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2025-08-24 a 2025-12-28 | 35474 | 20% | 29.2% | 29.7% | 29.7% | 1.2 pp | 1.1 pp |
| 2025-08-24 a 2025-12-28 | 35474 | 30% | 42.1% | 43.5% | 43.5% | 1 pp | 1 pp |
| 2025-08-24 a 2025-12-28 | 35474 | 40% | 55.1% | 55.3% | 55.3% | 0.9 pp | 0.8 pp |
| 2026-01-25 a 2026-02-22 | 35448 | 20% | 28.6% | 28.6% | 28.6% | 1.2 pp | 1 pp |
| 2026-01-25 a 2026-02-22 | 35448 | 30% | 42.8% | 42.8% | 42.8% | 0.9 pp | 0.9 pp |
| 2026-01-25 a 2026-02-22 | 35448 | 40% | 54.4% | 54.5% | 54.5% | 0.8 pp | 0.8 pp |

| Variante | Capacidad | Cambio medio de captura frente a C | IC95 | Periodos con mejora | Cumple regla |
|---|---:|---:|---|---:|---|
| C + QVoice sin calibración | 20% | 0.2 pp | [-0.1, 0.6] pp | 1 de 2 | No |
| C + QVoice sin calibración | 30% | 0.7 pp | [0.2, 1.1] pp | 1 de 2 | No |
| C + QVoice sin calibración | 40% | 0.2 pp | [-0.2, 0.7] pp | 2 de 2 | No |
| C + QVoice con escalar R6 | 20% | 0.2 pp | [-0.1, 0.6] pp | 1 de 2 | No |
| C + QVoice con escalar R6 | 30% | 0.7 pp | [0.2, 1.1] pp | 1 de 2 | No |
| C + QVoice con escalar R6 | 40% | 0.2 pp | [-0.2, 0.7] pp | 2 de 2 | No |

Los intervalos se obtuvieron con 500 remuestreos pareados por persona, conservando sus ventanas juntas. Son intervalos puntuales, condicionales a la selección y modelos ajustados; no corrigen comparaciones múltiples. Dos periodos cortos, con personas repetidas y ventanas superpuestas, no establecen estabilidad de largo plazo.

## Qué QVoice se seleccionó

Se buscaron 255 subconjuntos de ocho bloques, además de cinco tamaños PCA como diagnóstico; tres penalizaciones por candidato: 780 ajustes por corte. La selección utiliza dos intervalos mensuales anteriores al periodo externo. Después se reajusta sólo la corrección elegida sobre C con todas las etiquetas mensuales maduras anteriores al origen.

| Corte | C base disponible desde | Combinación seleccionada | Penalización L2 |
|---|---|---|---:|
| 2025-08-01 | 2025-08-01 | Q4 + Q12 + Career Goals + Engagement (Q1/Q2/Q3) | 10 |
| 2026-01-01 | 2025-08-01 | Q4 + Career Goals + Engagement (Q1/Q2/Q3) + Confidence (Q13/Q17) | 1 |
| Final: 2026-09-07 | 2025-08-01 | Career Goals + Promedio de 33 preguntas + Wellbeing (Q8/Q10/Q11) + Confidence (Q13/Q17) | 0.1 |

Bloques disponibles: Intent to Stay Q4 y Q12 por separado; Career Goals; promedio de 33 preguntas; Engagement Q1/Q2/Q3; Connection Q5/Q7; Wellbeing Q8/Q10/Q11; Confidence Q13/Q17. El promedio de 33 incluye preguntas ya presentes en otros bloques; no son fuentes independientes. Career conserva una diferencia de redacción de 2024 y se interpreta exploratoriamente.

En el artefacto final, Intent to Stay Q4 y Q12 entran dentro del promedio de 33 preguntas (M16 y M14, respectivamente), sin coeficientes propios para esas dos preguntas. Mapping conservado en `qvoice-model-b-calibrated-v1/preflight/source-metadata.json`.

La wave 2024 se usa sólo en snapshots de 2025 y la wave 2025 sólo en snapshots de 2026. Se exige continuidad del episodio laboral. Los duplicados de fuente se excluyen y se mantienen estados de ausencia de respuesta o pregunta. Q6/Q9, Heartbeat, comentarios y wave 2026 quedan excluidos.

El modelo final contiene una corrección reajustada al corte de conocimiento; sus coeficientes no se atribuyen retrospectivamente a los periodos evaluados. El C base sigue congelado en agosto de 2025.

### Respuestas utilizables en el frame de C

Cobertura sobre todas las observaciones persona-snapshot cargadas del año correspondiente, después del enlace y del control de episodio. Estos porcentajes incluyen meses que sólo sirven para entrenamiento o proyección; no describen únicamente las dos ventanas evaluadas.

| Wave | Año de los snapshots | Pregunta o resumen | Observaciones del año | Respuesta utilizable |
|---|---:|---|---:|---:|
| 2024 | 2025 | Intent to Stay Q4 | 390263 | 65.5% |
| 2024 | 2025 | Intent to Stay Q12 | 390263 | 64% |
| 2024 | 2025 | Career Goals | 390263 | 65% |
| 2024 | 2025 | Promedio de 33 preguntas | 390263 | 54.4% |
| 2025 | 2026 | Intent to Stay Q4 | 288586 | 64.7% |
| 2025 | 2026 | Intent to Stay Q12 | 288586 | 63.5% |
| 2025 | 2026 | Career Goals | 288586 | 65% |
| 2025 | 2026 | Promedio de 33 preguntas | 288586 | 56.4% |

## Cómo se calibró y qué se puede atribuir a las respuestas

C + Q sin calibración posterior es el candidato principal declarado. La alternativa aplica `R6_calibrado = 1 - (1 - R6)^exp(a)`. El escalar usa etiquetas de seis meses maduras antes del corte y predicciones auxiliares entrenadas antes de sus propias fotos. Con menos de tres orígenes admisibles se utiliza identidad.

| Periodo | C: estado del escalar | C: multiplicador | C + Q: estado del escalar | C + Q: multiplicador |
|---|---|---:|---|---:|
| aug_dec_2025 | Identidad: historia insuficiente | 1× | Identidad: historia insuficiente | 1× |
| jan_feb_2026 | Ajustado | 1.1× | Ajustado | 1× |

Las columnas y penalización elegidas al corte se reutilizan retrospectivamente en los auxiliares: no es una validación anidada completa del calibrador. Las salidas del periodo externo no se utilizan. El escalar conserva el ranking individual; el orden de medias de grupos puede cambiar y se evalúa nuevamente.

Los controles separan tres efectos: C con intercepto actualizado aprende sólo la tasa; C con disponibilidad aprende si hay una respuesta utilizable y los estados de ausencia; C + Q añade el contenido de las respuestas. Se aplica también el escalar a los controles para comparar calibraciones equivalentes.

### Comparaciones pareadas adicionales

| Comparación | Métrica | Diferencia | IC95 |
|---|---|---:|---|
| C + QVoice sin calibración menos C | Captura al 30%, pp | 0.7 | [0.2, 1.1] |
| C + QVoice sin calibración menos C | Log-loss × 1000 | -1.1 | [-1.6, -0.7] |
| C + QVoice con escalar R6 menos C | Captura al 30%, pp | 0.7 | [0.2, 1.1] |
| C + QVoice con escalar R6 menos C | Log-loss × 1000 | -1.1 | [-1.6, -0.7] |
| C + QVoice con escalar R6 menos C con escalar R6 | Captura al 30%, pp | 0.7 | [0.2, 1.1] |
| C + QVoice con escalar R6 menos C con escalar R6 | Log-loss × 1000 | -1.1 | [-1.6, -0.7] |
| C + QVoice sin calibración menos C con disponibilidad QVoice | Captura al 30%, pp | 0.6 | [0.2, 1] |
| C + QVoice sin calibración menos C con disponibilidad QVoice | Log-loss × 1000 | -1.3 | [-1.7, -0.9] |
| C + QVoice con escalar R6 menos C con disponibilidad y escalar | Captura al 30%, pp | 0.6 | [0.2, 1] |
| C + QVoice con escalar R6 menos C con disponibilidad y escalar | Log-loss × 1000 | -1.3 | [-1.7, -0.9] |
| C + QVoice sin calibración menos C con intercepto actualizado | Captura al 30%, pp | 0.7 | [0.2, 1.1] |
| C + QVoice sin calibración menos C con intercepto actualizado | Log-loss × 1000 | -1.1 | [-1.6, -0.7] |
| C + QVoice con escalar R6 menos C + QVoice sin calibración | Captura al 30%, pp | 0 | [0, 0] |
| C + QVoice con escalar R6 menos C + QVoice sin calibración | Log-loss × 1000 | >-0.1 | [>-0.1, >-0.1] |

## Grupos y estimación sobre la misma población priorizada

Las definiciones de grupos son iguales en todas las variantes. El número elegible cambia por foto con el mínimo de 300 personas. Sólo cambia el riesgo estimado medio y, potencialmente, el orden de prioridad. Esta evaluación no crea nuevos grupos por respuestas QVoice.

| Periodo | Grupos elegibles, mínimo–máximo | Estimador sobre prioridad de C | Error por grupo | Error grupo-mes |
|---|---|---|---:|---:|
| aug_dec_2025 | 19–20 | C | 1 pp | 1 pp |
| aug_dec_2025 | 19–20 | C + QVoice sin calibración | 1 pp | 1 pp |
| aug_dec_2025 | 19–20 | C + QVoice con escalar R6 | 1 pp | 1 pp |
| jan_feb_2026 | 20–20 | C | 0.9 pp | 0.9 pp |
| jan_feb_2026 | 20–20 | C + QVoice sin calibración | 0.9 pp | 0.9 pp |
| jan_feb_2026 | 20–20 | C + QVoice con escalar R6 | 0.9 pp | 0.9 pp |

### Grupos priorizados y mayor error publicable al 30%

| Periodo | Modelo | Grupos priorizados por foto, promedio | Mayor error de grupo publicable | Cobertura publicable dentro de prioridad |
|---|---|---:|---:|---:|
| aug_dec_2025 | C | 8.2 | 1.8 pp | 100% |
| aug_dec_2025 | C + QVoice sin calibración | 8.2 | 2.2 pp | 98.4% |
| aug_dec_2025 | C + QVoice con escalar R6 | 8.2 | 2.2 pp | 98.4% |
| jan_feb_2026 | C | 9 | 2.4 pp | 96.2% |
| jan_feb_2026 | C + QVoice sin calibración | 9 | 2.3 pp | 96.2% |
| jan_feb_2026 | C + QVoice con escalar R6 | 9 | 2.4 pp | 96.2% |

El mayor error se calcula sobre los grupos cuyo observado cumple las reglas de publicación. La cobertura indica qué proporción de observaciones priorizadas representan esos grupos; no es el peor error entre todos los grupos pequeños o suprimidos.

### Grupos priorizados por C + Q en enero–febrero de 2026

Se usa la variante principal sin calibración posterior al 30%. Las tasas resumen sólo las fotos en que cada grupo fue priorizado y aplican el peso del grupo del límite. El promedio de personas se calcula sobre las dos fotos. Esta tabla describe el periodo retrospectivo; no es una lista vigente de intervención.

| Grupo | Personas priorizadas por foto, promedio | Riesgo estimado R6 | Salida observada R6 | Error |
|---|---:|---:|---:|---:|
| Antigüedad: 3-5 años · Salidas en su equipo: con salidas · Nivel: entrada | 1396.5 | 7.8% | 5.5% | 2.3 pp |
| Antigüedad: 2-3 años · Salidas en su equipo: con salidas · Nivel: entrada | 401.5 | 7% | — | — |
| Antigüedad: 5-10 años · Salidas en su equipo: con salidas · Nivel: entrada | 875 | 6.5% | 5% | 1.5 pp |
| Antigüedad: 3-5 años · Salidas en su equipo: con salidas · Nivel: medio | 523.5 | 5.4% | 6.1% | 0.7 pp |
| Antigüedad: 3-5 años · Salidas en su equipo: sin salidas · Nivel: entrada | 3965 | 5% | 4.7% | 0.3 pp |
| Antigüedad: 2-3 años · Salidas en su equipo: sin salidas · Nivel: entrada | 1027 | 4.4% | 5.5% | 1.1 pp |
| Antigüedad: 5-10 años · Salidas en su equipo: con salidas · Nivel: medio | 1196.5 | 4.2% | 4.6% | 0.4 pp |
| Antigüedad: 1-2 años · Salidas en su equipo: con salidas · Nivel: entrada | 866 | 4% | 4.9% | 0.9 pp |
| Antigüedad: 5-10 años · Salidas en su equipo: sin salidas · Nivel: entrada | 290.4 | 3.9% | 4% | 0.1 pp |

— indica una cifra suprimida por las reglas de publicación.


### Alternativas con grupos completos alrededor del 30%

| Periodo | Modelo | Cobertura sin grupo límite | Captura sin grupo límite | Cobertura con grupo límite | Captura con grupo límite |
|---|---|---:|---:|---:|---:|
| aug_dec_2025 | C | 28.4% | 39.8% | 35.6% | 49% |
| aug_dec_2025 | C + QVoice sin calibración | 29.2% | 42.4% | 37.4% | 52.3% |
| aug_dec_2025 | C + QVoice con escalar R6 | 29.2% | 42.4% | 37.4% | 52.3% |
| jan_feb_2026 | C | 29.2% | 41.8% | 36.4% | 50.2% |
| jan_feb_2026 | C + QVoice sin calibración | 29.2% | 41.8% | 36.4% | 50.2% |
| jan_feb_2026 | C + QVoice con escalar R6 | 29.2% | 41.8% | 36.4% | 50.2% |

## Alcance, conservación y fuentes

- Los grupos identifican asociaciones predictivas. No estiman salidas evitables ni el efecto de una acción.
- Persisten los límites del C original: revisiones históricas de snapshots, fecha efectiva de IOS, capas/comp ratio almacenados y tratamiento de otras salidas como no voluntarias.
- La regla anual QVoice es una hipótesis de negocio aprobada; no acredita fechas reales de publicación.
- C base se reproduce contra el último fold archivado; la población y etiquetas se reconciliaron. La consulta de C sólo se amplió con los indicadores existentes de continuidad de episodio.
- Consulta: `queries/profiles/engineering_model_c_qvoice_person_month_20261008.sql`. Ejecución 8-oct-2026; conocimiento hasta 2026-09-07.
- Plan previo: `docs/plans/attrition-model-c-plus-qvoice-20261008.md`; configuración congelada: `frozen-config.json`.
- Evidencia: `results.json`, `folds/`, `trained-model/`, `qvoice-input-checks.json`, `analysis-checks.json` y `preservation.json`.
- Tiempo: 45.5 minutos; carga y QVoice: 4.5 minutos. Cero reajustes de C base. Matrices y offsets reutilizados en la búsqueda.
- Los modelos anteriores conservan sus hashes. No se guardan filas, respuestas, llaves o riesgos individuales. Tasas de grupos sólo con al menos 30 personas por foto seleccionada y 30 personas distintas con evento.
