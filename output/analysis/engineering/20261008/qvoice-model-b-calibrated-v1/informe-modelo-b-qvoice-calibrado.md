# Modelo B + QVoice calibrado

Clasificación: `presentation`. Modelo experimental desarrollado el 8 de octubre de 2026. Corte de conocimiento: 7 de septiembre de 2026.

El artefacto entrenado seleccionó **q4+q12+career+mean33+wellbeing**. El procedimiento retrospectivo obtuvo **sin mejora demostrada** según el criterio conjunto de ranking, Brier y calibración.

**QVoice mejora el ranking; la calibración limita el resultado.** La selección final es: Q4: permanencia futura + Q12: rara vez piensa buscar otro empleo + Career: metas de carrera + Promedio de 33 preguntas + Wellbeing (Q8, Q10, Q11).

![Comparación agregada frente a B](charts/comparacion-con-b.png)

## Modelo entregado

- [Parámetros y transformaciones del modelo entrenado](trained-model/model.json)
- [Búsqueda completa del modelo entrenado](trained-model/selection.json)
- [Resultados de la comparación temporal](comparison-results.json)
- [Plan y reglas fijadas antes de ejecutar](../../../../../docs/plans/attrition-b-plus-qvoice-calibrated-20261008.md)

El modelo añade una corrección QVoice al predictor de B y después calibra intercepto y pendiente con meses reservados. La fórmula mensual es `h = 1 − exp(−exp(a + b(eta_B + X_QVoice beta)))`; el riesgo a seis meses es `1 − producto(1 − h_m)`. El calendario avanza y las demás covariables se mantienen en el valor conocido del snapshot.

B conserva su receta de diez features. En esta extensión sus coeficientes se estiman primero y sirven como offset fijo al ajustar QVoice. El experimento anterior reajustaba conjuntamente B y QVoice; las magnitudes de ambas ejecuciones no se consideran intercambiables.

## Resultados en los periodos reservados

PR-AUC se presenta multiplicada por 100; lift compara la tasa del 10% de mayor riesgo con la tasa de toda la cohorte. Brier se multiplica por 10,000. La calibración es el error absoluto entre probabilidad media y tasa observada, en puntos base (100 pb = 1 pp).

### Agosto–diciembre de 2025

35,474 personas distintas; 5 snapshots; 168,175 exposiciones persona-snapshot. La etiqueta mide al menos una salida voluntaria en los seis meses siguientes. La cohorte coincide en los cinco modelos.

Combinación elegida usando sólo meses anteriores: **q4+q12+career+confidence**. Cobertura con todos sus componentes disponibles: 58%.

| Modelo | PR-AUC × 100 | Lift@10% | Brier × 10,000 | Error general (pb) | Error quintil superior (pb) |
|---|---:|---:|---:|---:|---:|
| B de referencia | 4.4 | 1.8 | 281.4 | 7.7 | 58.1 |
| B con calibración comparable | 4.4 | 1.8 | 281.4 | 32.9 | 5.8 |
| B + disponibilidad calibrado | 4.4 | 1.8 | 281.4 | 28.4 | 7.5 |
| B + QVoice sin calibrar | 4.8 | 2 | 281.1 | 7.9 | 101.3 |
| B + QVoice calibrado | 4.8 | 2 | 280.9 | 30.4 | 7.7 |

### Enero–febrero de 2026

35,448 personas distintas; 2 snapshots; 70,276 exposiciones persona-snapshot. La etiqueta mide al menos una salida voluntaria en los seis meses siguientes. La cohorte coincide en los cinco modelos.

Combinación elegida usando sólo meses anteriores: **q4+q12+career**. Cobertura con todos sus componentes disponibles: 65.2%.

| Modelo | PR-AUC × 100 | Lift@10% | Brier × 10,000 | Error general (pb) | Error quintil superior (pb) |
|---|---:|---:|---:|---:|---:|
| B de referencia | 5.3 | 1.8 | 332.6 | 6.3 | 102.3 |
| B con calibración comparable | 5.3 | 1.8 | 332.6 | 54.3 | 15.8 |
| B + disponibilidad calibrado | 5.3 | 1.7 | 332.7 | 57.4 | 11.5 |
| B + QVoice sin calibrar | 6.1 | 2.2 | 331.1 | 27.6 | 16.3 |
| B + QVoice calibrado | 6.1 | 2.2 | 331.5 | 56.3 | 3.3 |

## Resultado del criterio conjunto

El estado del experimento aplica ocho comprobaciones frente a B de referencia y el control de disponibilidad. Se añaden cuatro frente a B con calibración comparable. Para Brier y errores de calibración, «medio» significa la media aritmética de los dos periodos, con igual peso para cada periodo. Para ranking se exige mejorar tanto PR-AUC como lift en cada uno.

| Comprobación | Resultado |
|---|---|
| PR-AUC y lift en ambos periodos frente a B de referencia | Cumple |
| Brier medio frente a B de referencia | Cumple |
| Error general medio frente a B de referencia | No cumple |
| Error del quintil superior medio frente a B de referencia | Cumple |
| PR-AUC y lift en ambos periodos frente a B + disponibilidad calibrado | Cumple |
| Brier medio frente a B + disponibilidad calibrado | Cumple |
| Error general medio frente a B + disponibilidad calibrado | No cumple |
| Error del quintil superior medio frente a B + disponibilidad calibrado | Cumple |
| PR-AUC y lift en ambos periodos frente a B con calibración comparable | Cumple |
| Brier medio frente a B con calibración comparable | Cumple |
| Error general medio frente a B con calibración comparable | Cumple |
| Error del quintil superior medio frente a B con calibración comparable | Cumple |

**Interpretación:** hay aporte predictivo de QVoice en ranking y Brier, pero el modelo calibrado no cumple la regla conjunta porque empeora la calibración general frente a B. El estado «sin mejora demostrada» se refiere a cumplir todo el criterio; no elimina las mejoras parciales observadas.

Frente a B ajustado y calibrado con los mismos tramos, QVoice cumple las cuatro comprobaciones agregadas. Esto respalda un aporte adicional de las respuestas bajo este procedimiento; las magnitudes y la incertidumbre siguen siendo las de una evaluación retrospectiva.

La calibración con meses reservados aumentó el error general respecto a B + QVoice sin calibrar en ambos periodos. Por tanto, haber ejecutado la calibración no significa haber mejorado todas las medidas de calibración futura.

### Tasa media predicha y observada

Cada tasa usa como denominador las exposiciones persona-snapshot del periodo y como evento una salida voluntaria en los seis meses siguientes. Una persona puede aparecer en varios snapshots.

| Periodo | Observada | B de referencia | B con calibración comparable | B + QVoice sin calibrar | B + QVoice calibrado |
|---|---:|---:|---:|---:|---:|
| Agosto–diciembre de 2025 | 2.9% | 3% | 2.6% | 3% | 2.6% |
| Enero–febrero de 2026 | 3.5% | 3.4% | 2.9% | 3.2% | 2.9% |

El control B con calibración comparable usa los mismos tramos que el candidato; el control de disponibilidad conserva los estados de ausencia sin utilizar el contenido de las respuestas. La calibración se estima antes del periodo evaluado y puede deteriorarse cuando cambia la tasa posterior.

## Qué se exploró

Se evaluaron las 255 combinaciones no vacías de ocho bloques: Q4, Q12, Career, promedio 33, Engagement, Connection histórico, Wellbeing histórico y Confidence. Cada combinación probó tres penalizaciones. También se probaron PCA con 1, 2, 3, 5 y 10 componentes, cada uno con tres penalizaciones. Son 780 ajustes por corte; 2,340 entre los dos cortes retrospectivos y el corte del artefacto final.

Esta búsqueda es exhaustiva entre los ocho bloques definidos. No explora todas las interacciones ni los subconjuntos de los 33 ítems individuales. Las correlaciones y la varianza explicada por PCA están en los archivos de selección; describen redundancia y variación, sin medir causalidad ni garantizar capacidad predictiva. PCA resume cómo varían juntas las respuestas; su construcción no usa la etiqueta de attrition. Su utilidad predictiva se compara después con la misma regla de Brier mensual.

| Corte | Candidato seleccionado | Tipo | L2 |
|---|---|---|---:|
| Agosto–diciembre de 2025 | q4+q12+career+confidence | blocks | 10 |
| Enero–febrero de 2026 | q4+q12+career | blocks | 10 |
| Artefacto al 7-sep-2026 | q4+q12+career+mean33+wellbeing | blocks | 0.1 |

### Combinaciones frente a PCA

Los valores siguientes son Brier **mensuales del tramo de selección**, multiplicados por 10,000. Sirven para escoger la representación y no son una estimación independiente de desempeño. Las diferencias pequeñas pueden desaparecer al redondear; los JSON conservan la precisión completa.

| Corte | Ajustes que convergieron / intentados | Mejor combinación | Brier × 10,000 | Mejor PCA | Brier × 10,000 |
|---|---:|---|---:|---|---:|
| Agosto–diciembre de 2025 | 780 / 780 | q4+q12+career+confidence | 52.3 | pca_10 | 52.3 |
| Enero–febrero de 2026 | 780 / 780 | q4+q12+career | 47 | pca_10 | 47 |
| Artefacto al 7-sep-2026 | 780 / 780 | q4+q12+career+mean33+wellbeing | 64.5 | pca_10 | 64.5 |

### Cómo interpretar las señales seleccionadas

El artefacto final conserva **Q4: permanencia futura + Q12: rara vez piensa buscar otro empleo + Career: metas de carrera + Promedio de 33 preguntas + Wellbeing (Q8, Q10, Q11)**. Se eligió por el resultado conjunto al añadirlo a B. Una variable incluida no demuestra que tenga la mayor correlación individual con attrition ni que cause salidas.

Las selecciones históricas y la selección final pueden diferir porque cambian los meses de ajuste y selección. Debe evaluarse esa estabilidad antes de atribuir importancia definitiva a un tema.

Bloques presentes en las tres selecciones: **Q4: permanencia futura, Q12: rara vez piensa buscar otro empleo, Career: metas de carrera**. Es una señal descriptiva de estabilidad; los cortes comparten historia y no son tres experimentos independientes.

### Fechas de selección y calibración

| Modelo | Etiquetas para selección: ajuste hasta | Snapshots de selección | Coeficientes finales: etiquetas hasta | Snapshots de calibración |
|---|---|---|---|---|
| Agosto–diciembre de 2025 | 2025-03-30 | 2025-03-30, 2025-04-27 | 2025-05-25 | 2025-05-25, 2025-06-29 |
| Enero–febrero de 2026 | 2025-08-24 | 2025-08-24, 2025-09-28 | 2025-10-26 | 2025-10-26, 2025-11-23 |
| Artefacto al 7-sep-2026 | 2026-04-26 | 2026-04-26, 2026-05-24 | 2026-06-28 | 2026-06-28, 2026-07-26 |

## Fechas del artefacto entrenado

- Fin máximo de etiquetas usadas para ajustar coeficientes: 2026-06-28.
- Snapshots reservados para calibración: 2026-06-28, 2026-07-26.
- Fin máximo de etiquetas usadas para calibrar: 2026-08-23.

Los folds evalúan el procedimiento que selecciona y calibra; el artefacto final tiene la selección y los coeficientes estimados al corte disponible. Se mantiene como versión experimental hasta obtener evidencia posterior suficiente.

## Límites de interpretación

- Los periodos retrospectivos ya fueron inspeccionados en el desarrollo anterior. No equivalen a un holdout externo nuevo.
- El primer corte dispone de poca historia QVoice bajo la política anual y sólo dos meses para selección y dos para calibración; la selección puede ser inestable.
- Se utiliza QVoice 2024 en 2025 y QVoice 2025 en 2026. QVoice 2026 corresponde a 2027 y queda fuera del modelo actual.
- Q6 y Q9 no tienen historia en ambos periodos; Heartbeat no se reconstruye con sus 53 ordinales en 2024/2025. Los comentarios se excluyen por texto libre.
- Career conserva una diferencia de redacción en 2024. Su equivalencia entre waves sigue siendo exploratoria, incluso cuando el predictor se selecciona.
- Los intervalos bootstrap conservan juntas las observaciones de cada persona. Son condicionales al modelo ajustado y no repiten la selección de 780 candidatos.
- La cobertura completa cuenta todas las respuestas requeridas. Los faltantes permanecen en la cohorte con estados explícitos; PCA los imputa con medias de entrenamiento y conserva indicadores de ausencia.

No se guardaron filas de empleados, llaves, respuestas ni scores individuales. Los parámetros del modelo y los resultados publicados son agregados.

## Comprobaciones y procedencia

- [Pruebas numéricas, temporales, de serialización y contratos](validation/test-results.json).
- [Validación del SQL y del contrato de columnas](validation/model-sql-check.json).
- [Reconciliación de la búsqueda, parámetros, fechas y comparación](validation/artifact-checks.json).
- [Manifest y huellas de los artefactos](manifest.json).

Las definiciones y evaluaciones de los siete conceptos están enlazadas en `variables/<concepto>/assessment-reference.json`. La consulta guardada es `queries/profiles/engineering_qvoice_person_month_20261008_full.sql`; se ejecutó el 8 de octubre de 2026 para la población y el corte declarados. El manifiesto y `inputs/` conservan las fuentes, la política anual, la configuración y el código de esta ejecución.
