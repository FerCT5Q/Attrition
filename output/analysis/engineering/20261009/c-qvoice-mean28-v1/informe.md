# C + Q con promedio de 28: evaluación de la combinación concreta

Fecha de cálculo: 2026-10-09. Modo `presentation`. Etapa: **selección de modelo**.

## Qué se evaluó

Se entrenó en cada origen la misma combinación: **Career Goals + Wellbeing (Q8/Q10/Q11) + Confidence (Q13/Q17) + promedio de 28 preguntas**. Los coeficientes y L2 se aprendieron sólo con datos anteriores a cada periodo externo.

Esto difiere de la prueba anterior, cuyos subconjuntos cambiaron entre periodos. La definición fija corresponde al candidato elegido en septiembre, después de explorar el histórico; por ello esta evaluación es retrospectiva y condicionada a esa elección. No es una validación prospectiva independiente de toda la selección.

## Tabla actualizada

![Comparación](comparacion.png)

| Modelo | Captura al 30% ↑ | Error grupo-mes ↓ | Cambio de error vs C ↓ | Log-loss × 1000 ↓ | PR-AUC ↑ |
|---|---:|---:|---:|---:|---:|
| C | 42.4% | 1 pp | 0% | 138.8 | 4.9% |
| C + Q evaluado | 43.1% | 1 pp | -2.3% | 137.7 | 5.5% |
| C + Q fijo + promedio 33 | 43.1% | 1 pp | 1.9% | 138.2 | 5.2% |
| C + Q fijo + promedio 28 | 43.1% | 1 pp | 1.7% | 138.2 | 5.2% |
| C + Q fijo sin promedio | 43.1% | 1 pp | 3.2% | 138.3 | 5.2% |

Captura: proporción de salidas observadas dentro del 30% priorizado. Error grupo-mes: distancia absoluta entre tasa prevista y observada por grupo/foto, ponderada por población priorizada. Log-loss y Brier evalúan probabilidades; PR-AUC evalúa discriminación. El cambio relativo de error permite distinguir diferencias que desaparecen al redondear los puntos porcentuales. Un cambio negativo representa menor error.

“Q evaluado” conserva los modelos históricos elegidos anteriormente. “Q fijo” usa las seis mismas preguntas en ambas ventanas. Comparar media 28 frente a 33 o sin media aísla el cambio de representación; frente a Q evaluado también cambia el conjunto de preguntas. Todos usan los mismos coeficientes base C y la misma agrupación.

## Resultado por periodo

| Fotos | Variante | Personas distintas | Captura al 30% | Error grupo-mes |
|---|---|---:|---:|---:|
| Ago–dic 2025 | C | 35474 | 42.1% | 1 pp |
| Ago–dic 2025 | C + Q evaluado | 35474 | 43.5% | 1 pp |
| Ago–dic 2025 | C + Q fijo + promedio 33 | 35474 | 43.5% | 1.1 pp |
| Ago–dic 2025 | C + Q fijo + promedio 28 | 35474 | 43.5% | 1.1 pp |
| Ago–dic 2025 | C + Q fijo sin promedio | 35474 | 43.5% | 1.1 pp |
| Ene–feb 2026 | C | 35448 | 42.8% | 0.9 pp |
| Ene–feb 2026 | C + Q evaluado | 35448 | 42.8% | 0.9 pp |
| Ene–feb 2026 | C + Q fijo + promedio 33 | 35448 | 42.8% | 0.9 pp |
| Ene–feb 2026 | C + Q fijo + promedio 28 | 35448 | 42.8% | 0.9 pp |
| Ene–feb 2026 | C + Q fijo sin promedio | 35448 | 42.8% | 1 pp |

### Probabilidades sobre la misma prioridad elegida por C

Se mantiene exactamente la población priorizada por C y sólo cambia el estimador. Esto ayuda a separar la precisión de probabilidades del cambio de grupos seleccionados.

| Modelo | Riesgo observado | Riesgo estimado | Sesgo estimado − observado | Error grupo-mes |
|---|---:|---:|---:|---:|
| C | 4.5% | 5.2% | 0.7 pp | 1 pp |
| C + Q evaluado | 4.5% | 5.1% | 0.6 pp | 0.9 pp |
| C + Q fijo + promedio 33 | 4.5% | 5.1% | 0.6 pp | 1 pp |
| C + Q fijo + promedio 28 | 4.5% | 5.1% | 0.6 pp | 1 pp |
| C + Q fijo sin promedio | 4.5% | 5.2% | 0.7 pp | 1 pp |

## Incertidumbre de la captura

| Comparación | Cambio medio al 30% | IC95 |
|---|---:|---|
| Media 28 − C | 0.7 pp | [0.2, 1.2] pp |
| Media 28 − C + Q evaluado | 0 pp | [0, 0] pp |
| Media 28 − C + Q fijo + promedio 33 | 0 pp | [0, 0] pp |
| Media 28 − C + Q fijo sin promedio | 0 pp | [0, 0] pp |
| Media 28 − C + disponibilidad de Q fijo | 0.6 pp | [0.1, 1.1] pp |

### Incertidumbre de las probabilidades

| Media 28 frente a | Cambio log-loss × 10000 ↓ | IC95 | Cambio Brier × 100000 ↓ | IC95 |
|---|---:|---|---:|---|
| C | -5.4 | [-8.8, -1.7] | -2.5 | [-6, 1.3] |
| C + Q evaluado | 5.4 | [2.4, 8] | 3.5 | [0.3, 6.2] |
| C + Q fijo + promedio 33 | 0.5 | [-0.2, 1.3] | 0.3 | [-0.4, 1.1] |
| C + Q fijo sin promedio | -1.1 | [-2.6, 0.4] | -1 | [-2.4, 0.4] |

500 remuestreos pareados de personas, igual peso por periodo. Intervalos condicionales a parámetros, configuración y prioridades, sin corrección por múltiples comparaciones. Las ventanas y personas se comparten; los dos periodos no son experimentos independientes. Los extremos pueden variar respecto de bootstraps anteriores. Un intervalo de captura [0, 0] refleja aportaciones iguales de las salidas observadas dentro de esta prioridad fija; no demuestra equivalencia universal.

## Selección de modelo

Mantener C + Q evaluado anteriormente como candidato preferido en la selección. La combinación fija con promedio de 28 no aporta captura adicional y estima las probabilidades algo peor que ese C + Q. C se conserva como referencia documentada.

- Captura al priorizar 30%: 43.1% tanto para C + Q anterior como para las tres variantes fijas. El promedio de 28 empata con C + Q anterior en los dos periodos; no hay ganancia de captura en esta comparación.
- Frente a C + Q anterior, el promedio de 28 aumenta 4.1% el error de grupo-mes, 0.4% el log-loss y 0.1% el Brier. PR-AUC baja de 5.5% a 5.2%. El error por grupos es mayor en ambos periodos, también al fijar exactamente la prioridad de C.
- El cambio de log-loss frente a C + Q anterior es +0.5 por mil, IC95 [0.2, 0.8]. Es un deterioro pequeño, pero no viene acompañado de mayor captura. Los intervalos son condicionales a los modelos y prioridades ya elegidos.
- Sobre las mismas seis preguntas fijas, añadir el promedio de 28 sí reduce 1.5% el error de grupo-mes y 0.1% el log-loss frente a omitirlo. La diferencia de pérdida tiene un intervalo que incluye cero y no cambia la captura. Esa mejora pequeña no alcanza a C + Q anterior.
- Retirar las cinco preguntas individuales del promedio reduce el VIF máximo de aproximadamente 4.1 a 3.5 en casos completos. Elimina el solapamiento de componentes, aunque permanecen correlaciones y redundancias exactas de ausencia. No produce una mejora predictiva clara frente al promedio de 33.
- La selección interna por Brier conserva C + Q anterior en ambos periodos. Con adquisición registrada como cuarto corte, C + Q anterior captura 43.3% frente a 43.2% del promedio de 28 y tiene menor error por grupos.
- C + Q anterior sigue favorecido frente a C por el objetivo de priorizar grupos: captura 43.1% frente a 42.4%, menor error de grupo-mes y menores pérdidas. Gana un periodo y empata otro. El fallo de la antigua condición de ganar ambos se conserva como diagnóstico y no cambia por sí solo esta decisión de selección.

La regla estricta anterior se conserva como diagnóstico, separada de la decisión práctica de selección. No se suman métricas correlacionadas como si fueran votos independientes. Ningún resultado implica un piloto o despliegue.

| Media 28 frente a | Victorias en captura | Empates | Derrotas |
|---|---:|---:|---:|
| C | 1 | 1 | 0 |
| C + Q evaluado | 0 | 2 | 0 |

## Población, grupos y derivación

- Población: Engineering, Employee, Regular, activo, sin RF360 por snapshot.
- Outcome: salida voluntaria en los seis meses siguientes a cada foto. Fotos de agosto–diciembre de 2025 y enero–febrero de 2026; seguimiento hasta agosto de 2026.
- Grupos: antigüedad × salidas previas del equipo × nivel. Mínimo 300 personas por foto; tasas concretas sólo con 30 personas y 30 eventos distintos. El grupo del límite del 30% recibe peso uniforme fraccional.
- Promedio 28: suma de indicadores favorables restantes / 28, en las seis bandas del playbook. Excluye Q8, Q10, Q11, Q13 y Q17 del promedio original de 33. Career no está entre los 33. Se exige validez de los 33 originales para conservar elegibilidad.
- Mapping por texto, no por posición supuesta. Se conserva la política de encuesta 2024 para 2025 y 2025 para 2026, con continuidad del episodio laboral.
- Controles: media de 33, mismas preguntas sin media y disponibilidad de las preguntas de la variante media 28. L2 en {0.1, 1, 10}; mismos intervalos internos.

### Sensibilidades de capacidad

| Variante | Captura al 20% | Captura al 30% | Captura al 40% |
|---|---:|---:|---:|
| C | 28.9% | 42.4% | 54.7% |
| C + Q evaluado | 29.2% | 43.1% | 54.9% |
| C + Q fijo + promedio 33 | 29% | 43.1% | 54.9% |
| C + Q fijo + promedio 28 | 29.1% | 43.1% | 54.9% |
| C + Q fijo sin promedio | 29% | 43.1% | 54.9% |

### Sensibilidad de agrupación: añadir adquisición registrada

| Variante | Captura al 30% | Error grupo-mes |
|---|---:|---:|
| C | 42.7% | 0.9 pp |
| C + Q evaluado | 43.3% | 0.9 pp |
| C + Q fijo + promedio 33 | 43.2% | 1 pp |
| C + Q fijo + promedio 28 | 43.2% | 1 pp |
| C + Q fijo sin promedio | 43.3% | 1 pp |

Las particiones son iguales entre modelos dentro de cada tabla. No se mezclan errores de particiones con distinta granularidad. La adquisición registrada describe el dato almacenado; “sin registro” no prueba ausencia de adquisición.

## Colinealidad en las mismas preguntas fijas

| Corte de ajuste | Variante | VIF máximo, casos completos | Número de condición | Rango / columnas, matriz completa |
|---|---|---:|---:|---|
| 2025-08-01 | C + Q fijo + promedio 33 | 4.1 | 5.2 | 20 / 32 |
| 2025-08-01 | C + Q fijo + promedio 28 | 3.5 | 5 | 20 / 32 |
| 2025-08-01 | C + Q fijo sin promedio | 1.6 | 2.5 | 14 / 24 |
| 2026-01-01 | C + Q fijo + promedio 33 | 4.1 | 5.2 | 20 / 32 |
| 2026-01-01 | C + Q fijo + promedio 28 | 3.5 | 5 | 20 / 32 |
| 2026-01-01 | C + Q fijo sin promedio | 1.6 | 2.5 | 14 / 24 |

Los casos completos usan personas-encuesta distintas. VIF y condición describen las columnas QVoice, no toda la matriz conjunta con C ni efectos causales. Retirar preguntas del promedio elimina ese solapamiento aritmético, pero las preguntas aún pueden estar correlacionadas. Los estados compartidos de ausencia generan redundancias exactas en la matriz completa; L2 permite el ajuste, sin volver identificables sus efectos separados al quitar la penalización.

## Artefacto final y límites

El archivo `trained-model/model-mean28.json` es una copia exacta del modelo final del 7-sep-2026. Su estructura ahora tiene esta evaluación retrospectiva, con coeficientes históricos separados. Los coeficientes finales de septiembre todavía no tienen evaluación posterior a su ajuste. C base conserva origen 1-ago-2025.

La selección de seis preguntas fue posterior a la exploración del histórico. El resultado permite comparar candidatos en esta etapa; no demuestra generalización a periodos aún no observados ni el efecto causal de acciones de retención. La disponibilidad real de encuestas y la redacción de Career mantienen sus límites previos.

## Reproducción y comprobaciones

- Plan: `docs/plans/attrition-c-qvoice-mean28-20261009.md`.
- Consulta: `queries/profiles/engineering_c_qvoice_mean28_person_month_20261009.sql`, ejecutada el 2026-10-09 con corte 7-sep-2026.
- Resultados: `results.json`, `tabla-comparativa.csv`, `folds/*/evaluation.json`.
- Reproducción de C/CQ: `folds/*/reconciliation.json`. Derivación: `folds/*/*-derivation.json`.
- Preservación: `preservation.json`; verificación y hashes: `verification.json` y `manifest.json`.
- 26 ajustes de correcciones, cero reajustes C y cero reajustes del final de septiembre. Proceso completado en 9.9 minutos.
- Autorización: `config/attrition_model_in_memory_training_authorization_20261001.json`. Filas, respuestas y llaves sólo en RAM; se guardan parámetros y agregados. No se modifican modelos previos ni scores.
