# Impacto de BU L3 en los modelos de attrition

Evaluacion experimental retrospectiva en modo `presentation`. BU L3 se unio por cost_centerid = nk_dept_id con una ventana SCD as-of al snapshot. No se guardaron filas, identificadores ni predicciones individuales.

## Calidad del mapping

La auditoria encontro 2,209,264 empleado-snapshot, 0 duplicados temporales y 0 multi-match de BU L3. El unmatched fue 0.0009% y se codifico como `(unknown)`.

## Efecto en prediccion

Menor es mejor para log-loss y Brier; mayor es mejor para PR-AUC y lift.

| Modelo | Control | Con BU L3 | Delta log-loss x1000 | Delta Brier x1000 | Delta PR-AUC | Delta lift |
|---|---:|---:|---:|---:|---:|---:|
| B | 138.7 / 4.8% | 138.2 / 5.0% | -0.5 | -0.031 | 0.2 pp | 0.1 |
| C + QVoice | 137.7 / 5.5% | 137.0 / 5.7% | -0.7 | -0.049 | 0.2 pp | 0.1 |
| F + QVoice | 136.4 / 5.9% | 136.0 / 6.0% | -0.5 | -0.023 | 0.1 pp | 0.1 |

## Validacion del nuevo candidato F + QVoice + BU L3

La comparacion directa usa los mismos cortes y la misma estructura de grupos. Menor es mejor para log-loss y Brier; mayor es mejor para PR-AUC y lift.

| Modelo | Log-loss x1000 | Brier x1000 | PR-AUC | Lift 10% |
|---|---:|---:|---:|---:|
| C + QVoice + BU L3 | 137.0 | 30.6 | 5.7% | 2.1 |
| F + QVoice + BU L3 | 136.0 | 30.6 | 6.0% | 2.3 |

F + QVoice + BU L3 mejora directamente a C + QVoice + BU L3 en log-loss (-1.0 x1000), Brier (-0.073 x1000), PR-AUC (0.3 pp) y lift (0.1); la dirección se mantiene en ambos cortes: si.

## Grupos actuales con las dos variantes

Antes de subdividir por BU L3, las dos variantes se evalúan con la estructura actual: Antigüedad x Salidas en su equipo x Nivel.

| Modelo | Captura 30% | Error grupo-snapshot pp | Rest |
|---|---:|---:|---:|
| C + QVoice + BU L3 | 43.1% | 0.9 | 5.3% |
| F + QVoice + BU L3 | 43.1% | 0.9 | 5.3% |

## Refinamiento de grupos de riesgo

Primero se conservan los grupos actuales y se seleccionan sus celdas de mayor riesgo. BU L3 sólo subdivide esas celdas; no se usa para fragmentar a toda la población. Se muestran el umbral mínimo probado y las guardas de rest, error y capacidad.

| Modelo | Umbral mínimo | Población en grupos de riesgo | Captura | Error grupo pp | Rest | Celdas seleccionadas | Resultado |
|---|---:|---:|---:|---:|---:|---:|---|
| C + QVoice + BU L3 | -- | -- | -- | -- | -- | -- | Sin asignación posible |
| F + QVoice + BU L3 | 100 | 36.9% | 43.2% | 1.0 | 67.7% | 24.7 | Exploratoria; falla rest, error |

## Efecto en grupos

La candidata es la estructura con mayor captura media aunque no sea elegible para sustituir los grupos actuales. La elegibilidad exige simultaneamente las tres guardas definidas.

| Modelo | Grupos actuales | Mejor candidata BU L3 (exploratoria) | Captura actual | Captura candidata | Error actual pp | Error candidata pp | Resultado |
|---|---|---|---:|---:|---:|---:|---|
| B | Antigüedad x Salidas en su equipo x Nivel | BU L3 x Antigüedad x Salidas en su equipo | 41.6% | 43.6% | 0.8 | 0.9 | No elegible: error de grupo fuera de la tolerancia respecto a las candidatas cercanas en captura; rest 21.5% > maximo 10.3% |
| C + QVoice | Antigüedad x Salidas en su equipo x Nivel | BU L3 x Antigüedad x Salidas en su equipo | 43.1% | 44.0% | 1.0 | 0.9 | No elegible: rest 21.5% > maximo 10.3% |
| F + QVoice | Antigüedad x Salidas en su equipo x Nivel | BU L3 x Antigüedad x Salidas en su equipo | 43.1% | 44.1% | 0.9 | 0.8 | No elegible: rest 21.5% > maximo 10.3% |

## Lectura

La recomendacion de predictor se basa en las diferencias pareadas y sus intervalos por persona. BU L3 mejora modestamente las metricas predictivas en los tres modelos y las diferencias de log-loss pareadas excluyen cero. Para grupos, la estructura exploratoria con mayor captura es BU L3 x Antiguedad x Salidas en su equipo; su fragmentacion deja demasiado porcentaje en rest, por lo que no sustituye la estructura actual. La recomendacion de grupos aplica la regla de captura dentro del 2% relativo, error dentro de 0.1 pp y rest no mas de 5 pp peor que el baseline. Los modelos B, C+Q y F+Q originales permanecen sin cambios.
