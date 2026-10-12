# B frente a C: utilidad para priorizar grupos

**C mejora ligeramente la captura y la estimación de los grupos prioritarios al 30%.**

Modo de entrega: `presentation`. Ejecución: 8 de octubre de 2026.

## Qué se comparó

Misma población Engineering, Employee, Regular, activa y sin RF360; salida voluntaria en los seis meses siguientes a cada snapshot. Se evaluaron 24 snapshots, de febrero de 2024 a enero de 2026, agrupados en cuatro periodos. El seguimiento de la última foto termina en julio de 2026. Se da el mismo peso a cada periodo.

Se priorizan hojas de los árboles por el riesgo predicho en entrenamiento, sin usar las salidas del periodo evaluado. Las capacidades de 20%, 30% y 40% son escenarios; el 30% se fijó como central antes del cálculo. Representan alta prioridad y su ampliación; no son etiquetas absolutas de riesgo ni una capacidad operativa confirmada.

**Para igualar capacidad se pondera la hoja que cruza el límite.** Todos sus integrantes reciben la misma probabilidad de selección. La captura es el valor esperado si se atiende aleatoriamente a una parte de esa hoja; más abajo se presentan alternativas con hojas completas. No se publican ni seleccionan personas concretas.

## Resultado principal

![Captura y diferencia entre modelos](captura-por-capacidad.png)

| Capacidad | Captura B | Captura C | Diferencia C − B (pp) | IC95 (pp) | Periodos: C / B / empate | Error por grupo B (pp) | Error por grupo C (pp) |
|---|---:|---:|---:|---|---|---:|---:|
| 20% | 30.4% | 31.2% | 0.7 | [<0.1, 1.5] | 1 / 1 / 2 | 0.6 | 0.5 |
| 30% | 43.6% | 43.9% | 0.4 | [0.2, 0.6] | 2 / 0 / 2 | 0.5 | 0.4 |
| 40% | 53.8% | 53.7% | -0.1 | [-0.3, 0.1] | 0 / 1 / 3 | 0.4 | 0.4 |

Captura = salidas en las ventanas de la selección / salidas en todas las ventanas elegibles. Una persona y una salida pueden contribuir a varias ventanas solapadas. El bootstrap agrupa todas las ventanas de la misma persona. Error por grupo = promedio ponderado del error absoluto de cada hoja seleccionada; evita que se compensen errores entre hojas. Las cifras se redondean; diferencias e intervalos se calculan antes de redondear.

## Escenario central: atender 30%

| Métrica | B | C |
|---|---:|---:|
| Personas atendidas medias por foto (esperadas) | 9491.1 | 9491.1 |
| Attrition observado a 6 meses | 4.4% | 4.4% |
| Attrition estimado a 6 meses | 4.9% | 4.7% |
| Lift frente a toda la población | 1.5× | 1.5× |
| Error del total seleccionado (pp) | 0.5 | 0.3 |
| Error medio por grupo seleccionado (pp) | 0.5 | 0.4 |
| Error medio por grupo y snapshot (pp) | 0.6 | 0.5 |
| Promedio del peor error de grupo publicable por periodo (pp) | 1.5 | 1.6 |
| Personas seleccionadas con tasas de grupo publicables | 98.8% | 98.8% |

El error por grupo y snapshot tampoco permite compensar subestimaciones de un mes con sobreestimaciones de otro. El peor error sólo se publica para hojas que cumplen los mínimos; no se interpreta como máximo de todas las hojas si hay supresión.

C mejora el error medio por grupo prioritario en 3 de 4 periodos. En captura gana en 2, pierde en 0 y empata en 2. La ventaja media al 30% es pequeña. El error del peor grupo publicable y la estabilidad al reajustar siguen favoreciendo B en este escenario.

### Comportamiento temporal

| Snapshots | Captura B | Captura C | Error por grupo B (pp) | Error por grupo C (pp) |
|---|---:|---:|---:|---:|
| 2024-02-18 a 2024-07-21 | 47.4% | 47.7% | 0.2 | 0.5 |
| 2024-08-25 a 2025-01-26 | 42.3% | 43.5% | 0.6 | 0.5 |
| 2025-02-23 a 2025-07-27 | 43% | 43% | 0.6 | 0.2 |
| 2025-08-24 a 2026-01-25 | 41.4% | 41.4% | 0.6 | 0.6 |

### Estimación sobre las mismas personas y reglas

| Grupos y selección definidos por | Error por grupo con estimador B (pp) | Error por grupo con estimador C (pp) |
|---|---:|---:|
| B | 0.5 | 0.5 |
| C | 0.5 | 0.4 |

Esta comparación mantiene fijas las personas y las hojas. Permite separar la selección de grupos de la estimación de su attrition.

### Ampliar desde el 20% prioritario

| Ampliación | Captura adicional B | Captura adicional C | Attrition del tramo añadido B | Attrition del tramo añadido C |
|---|---:|---:|---:|---:|
| 20% → 30% | 13.1% | 12.8% | 4% | 3.9% |
| 20% → 40% | 23.4% | 22.5% | 3.5% | 3.4% |

Captura adicional usa como denominador todas las salidas del periodo. Attrition del tramo añadido usa sólo la población adicional esperada.

## Claridad y estabilidad de los grupos

Los dos modelos usan árboles de hasta 8 hojas y hasta 3 condiciones por hoja, aprendidos antes de la evaluación. C conserva variables originales. El árbol resume el modelo y puede perder parte de su señal.

| Capacidad | Coincidencia al reajustar B | Coincidencia al reajustar C | Captura con ranking individual B | Captura con ranking individual C |
|---|---:|---:|---:|---:|
| 20% | 94.8% | 76.3% | 34.7% | 36.1% |
| 30% | 99.2% | 95.5% | 47.5% | 48.5% |
| 40% | 95.6% | 98.5% | 58% | 60.3% |

Coincidencia: suma del mínimo de las dos asignaciones ponderadas / capacidad, aplicando las reglas anteriores y nuevas a la misma foto. Es el solapamiento de asignaciones esperadas, no la retención real de personas de un programa. Se promedian los tres cambios de periodo. El ranking individual es sólo un diagnóstico agregado; no se publican puntuaciones ni listas individuales.

## Opciones con grupos completos

| Periodo | Modelo | Cobertura media excluyendo hoja del límite | Cobertura media incluyendo hoja del límite |
|---|---|---:|---:|
| 2024-02-01 | B | 24.3% | 37.3% |
| 2024-02-01 | C | 26.4% | 49.9% |
| 2024-08-01 | B | 19.1% | 33.4% |
| 2024-08-01 | C | 22.8% | 33.4% |
| 2025-02-01 | B | 15.7% | 32% |
| 2025-02-01 | C | 15.7% | 32% |
| 2025-08-01 | B | 28.6% | 75.6% |
| 2025-08-01 | C | 28.6% | 75.6% |

Estas alternativas explican el costo de conservar grupos completos. Sus capacidades pueden diferir entre B y C; no se presentan como comparación a igual cantidad de personas. Los límites por snapshot están en results.json.

## Grupos prioritarios del último periodo

Snapshots agosto de 2025 a enero de 2026; grupos ordenados por riesgo de entrenamiento. Personas = media de personas que se atendería por foto, ponderando la hoja del límite al 30%. Las tasas observadas requieren 30 personas efectivas por foto seleccionada y 30 personas distintas con salida.

| Modelo / grupo | Regla | Personas medias esperadas | Observado R6 | Estimado R6 | Error (pp) |
|---|---|---:|---:|---:|---:|
| B / G6 | Antigüedad ≠ 10+ años; Antigüedad = 3-5 años; Nivel = 8 - Assoc & Int/Eng | 1238.8 | 5.1% | 8.5% | 3.3 |
| B / G8 | Antigüedad ≠ 10+ años; Antigüedad ≠ 3-5 años; Antigüedad = 2-3 años | 2203.8 | 4.1% | 4.6% | 0.5 |
| B / G5 | Antigüedad ≠ 10+ años; Antigüedad = 3-5 años; Nivel ≠ 8 - Assoc & Int/Eng | 6216.5 | 4% | 4.2% | 0.2 |
| B / G7 | Antigüedad ≠ 10+ años; Antigüedad ≠ 3-5 años; Antigüedad ≠ 2-3 años | — | — | — | — |
| C / G6 | Antigüedad ≠ 10+ años; Antigüedad = 3-5 años; Nivel = 8 - Assoc & Int/Eng | 1238.8 | 5.1% | 8.7% | 3.5 |
| C / G8 | Antigüedad ≠ 10+ años; Antigüedad ≠ 3-5 años; Antigüedad = 2-3 años | 2203.8 | 4.1% | 4.7% | 0.5 |
| C / G5 | Antigüedad ≠ 10+ años; Antigüedad = 3-5 años; Nivel ≠ 8 - Assoc & Int/Eng | 6216.5 | 4% | 4% | <0.1 |
| C / G7 | Antigüedad ≠ 10+ años; Antigüedad ≠ 3-5 años; Antigüedad ≠ 2-3 años | — | — | — | — |

## Foto adicional: febrero de 2026

Snapshot 2026-02-22; seguimiento hasta 2026-08-22; 35313 personas. Usa los modelos y las reglas del corte de agosto de 2025, sin reajuste. Es una foto adicional fuera de los cuatro periodos originales; no equivale a seis snapshots ni constituye un holdout virgen. Se mantiene aparte del promedio principal.

| Capacidad | Captura B | Captura C | Error por grupo B (pp) | Error por grupo C (pp) |
|---|---:|---:|---:|---:|
| 20% | 29.5% | 29.5% | 0.5 | 0.4 |
| 30% | 41.7% | 41.7% | 0.4 | 0.3 |
| 40% | 51.9% | 51.9% | 0.3 | 0.4 |

## Criterio fijado antes de calcular

La prioridad es capturar salidas dentro de la capacidad disponible, con estimaciones fiables por grupo. Se conservó la exigencia temporal de al menos 3 de 4 periodos y la tolerancia de 0.1 pp del experimento anterior; el error global deja de ser la puerta principal. El criterio es exploratorio, posterior a haber visto los resultados anteriores.

| Comprobación al 30% | Cumple C |
|---|---|
| Mayor captura media | Sí |
| Mayor captura en al menos 3 de 4 periodos | No |
| IC95 de ventaja de captura completamente positivo | Sí |
| Error por grupo prioritario no empeora más de 0.1 pp | Sí |
| Error por grupo-snapshot no empeora más de 0.1 pp | Sí |

**Resultado formal: C no cumple todas las condiciones de la regla conservadora.**

La condición pendiente al 30% es ganar en al menos tres periodos: C obtiene dos victorias y dos empates en captura. La diferencia media de captura tiene un IC95 positivo y C reduce el error medio de los grupos prioritarios. Por ello, el balance práctico favorece ligeramente a C para este escenario, aunque no supera la regla conservadora completa. Se conserva esa regla y su resultado, sin modificar los umbrales después de ver los datos.

El criterio no sustituye una evaluación de costos y beneficios de la acción. Los grupos de bajo riesgo siguen en el entrenamiento y se reportan como seguimiento en results.json; su precisión tiene un papel secundario en esta decisión.

## Límites y reproducción

- Se reutilizan cuatro C congelados y se reconstruye B cuatro veces con las especificaciones ya elegidas. No se repite la selección de variables.
- Población, métricas B/C y ranking de sus grupos reproducen la ejecución original dentro de la tolerancia de cálculo. La evidencia está en analysis-checks.json.
- Los IC95 de captura provienen de 500 réplicas de personas; mantienen fijos modelos, reglas y asignaciones. No incluyen incertidumbre de selección, cambios macrotemporales o efecto de una intervención.
- La evaluación es retrospectiva y usa años ya explorados. La política por capacidad se formuló después de conocer las métricas anteriores. No es confirmación prospectiva independiente.
- La comparación usa definiciones y fechas de conocimiento del experimento C: snapshots fiscales de duración desigual, otras salidas tratadas como no voluntarias, limitaciones de historia de IOS/transferencias y de campos almacenados.
- Capturar una salida no demuestra que una acción pueda evitarla; las asociaciones no identifican causas.
- El modelo C archivado sigue siendo el evaluado con corte agosto de 2025. No es un modelo actualizado a septiembre de 2026; C + QVoice no se ha iniciado.

Tiempo de cálculo: 4.8 minutos, incluida carga de datos (3.2 minutos).

## Fuentes

- Consulta: `queries/profiles/engineering_model_c_person_month_20261008.sql`. Frontera de conocimiento: `2026-09-07`.
- [Resultados agregados](results.json), [configuración previa](frozen-config.json), [comprobaciones del cálculo](analysis-checks.json), [manifiesto](manifest.json).
- Experimento de origen: `../model-c-v2/`; autorización de RAM: `config/attrition_model_in_memory_training_authorization_20261001.json`.
- No se persistieron filas, llaves efímeras, puntuaciones individuales, salarios exactos ni texto libre.
