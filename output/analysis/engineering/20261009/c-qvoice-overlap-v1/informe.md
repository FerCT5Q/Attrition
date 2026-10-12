# C + QVoice: comparación con C y revisión del promedio

Fecha de cálculo: 2026-10-09. Modo: `presentation`.

## Resultado de la revisión

**C + Q mejora algunas métricas, pero no cumple la regla conjunta para sustituir a C.**

Esta ejecución cierra la comprobación con la evidencia disponible. No agrega periodos independientes ni acredita el desempeño futuro del modelo final de septiembre.

Los C + Q históricos seleccionaron preguntas individuales y no incluyeron el promedio de 33. Por tanto, sus resultados frente a C no se explican por duplicar preguntas dentro de ese promedio. El solapamiento sí existe en los artefactos finales de C + Q y B + Q.

### Conclusiones concretas

- C + Q cumple siete de las ocho condiciones originales: mejora el promedio, pero gana en captura en un periodo y empata en el otro. Se conserva C como referencia.
- Retirar las preguntas individuales del promedio conserva exactamente la captura de la versión con promedio completo al 20%, 30% y 40%. Las diferencias de log-loss y Brier entre ambas son pequeñas y sus intervalos incluyen cero.
- En las respuestas completas del corte final, el VIF máximo de C + Q baja de 4.1 a 3.5 al quitar la duplicación; ambos están debajo del umbral descriptivo de 10. La matriz completa sí es singular por indicadores de ausencia compartidos. Eso limita la interpretación separada de coeficientes, aunque L2 permite el ajuste.
- La selección interna mantiene CQ en ambos periodos históricos. En septiembre elige una media de 28 ítems, con una mejora interna menor a 0.1% relativo. Se archiva como experimento; no acredita una mejora externa del modelo final.

## Población, fechas y lectura

Engineering, Employee, Regular, activo y sin RF360 en cada snapshot. Salida voluntaria durante los seis meses siguientes. Fotos de agosto–diciembre de 2025 y enero–febrero de 2026, con seguimiento hasta agosto de 2026. Los periodos tienen igual peso; las personas y las ventanas se repiten. La unidad de evaluación es persona-snapshot.

Priorizar 30% es el escenario principal. Se usa una fracción uniforme del grupo que cruza el límite; no supone que una fracción de empleado sea una acción operativa. Grupos de antigüedad × salidas previas del equipo × nivel, con al menos 300 personas por foto. Las tasas de grupos concretos sólo se publican con al menos 30 personas y 30 eventos distintos.

## Captura y precisión en la misma población

![Comparación](comparacion.png)

| Modelo | Captura al 30% ↑ | Error grupo-mes ↓ | Log-loss × 1000 ↓ | PR-AUC ↑ |
|---|---:|---:|---:|---:|
| C | 42.4% | 1 pp | 138.8 | 4.9% |
| C + Q archivado | 43.1% | 1 pp | 137.7 | 5.5% |
| Preguntas + promedio completo | 42.8% | 0.9 pp | 137.7 | 5.5% |
| Preguntas + promedio sin duplicación | 42.8% | 0.9 pp | 137.7 | 5.5% |
| Sólo preguntas | 43.1% | 1 pp | 137.6 | 5.5% |
| Selección interna ampliada | 43.1% | 1 pp | 137.7 | 5.5% |

Captura = salidas observadas dentro de la prioridad / todas las salidas observadas. Error grupo-mes = diferencia absoluta entre tasa prevista y observada por grupo/foto, ponderada por la población priorizada. Log-loss mide la calidad de las probabilidades; PR-AUC mide discriminación. Menos error no garantiza más captura.

Las tres nuevas representaciones conservan los términos del mejor candidato con promedio de la búsqueda interna de cada origen. Ese candidato puede diferir del C + Q archivado. La comparación entre representaciones mantiene sus otras preguntas; la selección ampliada elige por Brier interno, incluyendo la opción de conservar el C + Q original.

### Comparación por periodo

| Fotos | Personas distintas | Registros persona-foto | Variante | Captura al 30% | Error grupo-mes |
|---|---:|---:|---|---:|---:|
| Ago–dic 2025 | 35474 | 168175 | C | 42.1% | 1 pp |
| Ago–dic 2025 | 35474 | 168175 | C + Q archivado | 43.5% | 1 pp |
| Ago–dic 2025 | 35474 | 168175 | Preguntas + promedio completo | 43.5% | 1 pp |
| Ago–dic 2025 | 35474 | 168175 | Preguntas + promedio sin duplicación | 43.5% | 1 pp |
| Ago–dic 2025 | 35474 | 168175 | Sólo preguntas | 43.5% | 1 pp |
| Ago–dic 2025 | 35474 | 168175 | Selección interna ampliada | 43.5% | 1 pp |
| Ene–feb 2026 | 35448 | 70276 | C | 42.8% | 0.9 pp |
| Ene–feb 2026 | 35448 | 70276 | C + Q archivado | 42.8% | 0.9 pp |
| Ene–feb 2026 | 35448 | 70276 | Preguntas + promedio completo | 42.1% | 0.8 pp |
| Ene–feb 2026 | 35448 | 70276 | Preguntas + promedio sin duplicación | 42.1% | 0.8 pp |
| Ene–feb 2026 | 35448 | 70276 | Sólo preguntas | 42.8% | 0.9 pp |
| Ene–feb 2026 | 35448 | 70276 | Selección interna ampliada | 42.8% | 0.9 pp |

### Incertidumbre de las diferencias

| Comparación | Cambio captura al 30% | IC95 |
|---|---:|---|
| C + Q archivado − C | 0.7 pp | [0.1, 1.2] pp |
| Preguntas + promedio sin duplicación − C | 0.3 pp | [-0.6, 1.2] pp |
| Sólo preguntas − C | 0.7 pp | [0.1, 1.2] pp |
| Selección interna ampliada − C | 0.7 pp | [0.1, 1.2] pp |
| Preguntas + promedio sin duplicación − Preguntas + promedio completo | 0 pp | [0, 0] pp |
| Sólo preguntas − Preguntas + promedio completo | 0.3 pp | [-0.2, 0.9] pp |
| Selección interna ampliada − C + Q archivado | 0 pp | [0, 0] pp |
| C + Q archivado − Sólo disponibilidad QVoice | 0.6 pp | [0.1, 1.1] pp |

Bootstrap pareado de personas con 500 réplicas. Los intervalos son condicionales a modelos y selecciones; no corrigen comparaciones múltiples. Un intervalo favorable en el promedio no demuestra superioridad en cada periodo. Se recalcularon con semilla 20261009 y llaves efímeras nuevas; sus extremos pueden variar respecto del bootstrap anterior de 500 réplicas. Las estimaciones puntuales y las métricas archivadas se reprodujeron.

## Decisión sobre C + Q archivado

Gana en captura en 1 de 2 periodos. Cambio medio: 0.7 pp.

| Condición original | Resultado |
|---|---|
| Mejor captura en ambos periodos | No cumple |
| Intervalo de mejora media positivo | Cumple |
| Error por grupo dentro de tolerancia +0.1 pp | Cumple |
| Error grupo-mes dentro de tolerancia +0.1 pp | Cumple |
| Log-loss dentro de tolerancia +0.5% relativo | Cumple |
| Brier dentro de tolerancia +0.5% relativo | Cumple |
| Más captura que disponibilidad de encuesta | Cumple |
| Pérdida no mayor que disponibilidad de encuesta | Cumple |

Las nuevas representaciones son pruebas de sensibilidad. Sus reglas comparables se guardan en `verdict.json`; no se promueven automáticamente y no tienen un control de disponibilidad propio recalculado. El control original se conserva para C + Q.

## Qué comprobamos del promedio

**Pregunta:** ¿Las preguntas que ya tienen coeficiente propio añaden redundancia al promedio?

**Motivo:** distinguir problemas de identificabilidad de una mejora o deterioro predictivo.

**Método:** mapping de textos, recálculo de bandas, correlaciones y rango de la matriz indicadora. Se exige la misma disponibilidad de los 33 ítems para las dos medias. Se retienen los estados de no respuesta. La media usa indicadores favorables, no valores Likert.

**Regla:** cero discrepancias de mapping, bandas y elegibilidad. |r| ≥ 0.8, VIF ≥ 10 y número de condición ≥ 30 son indicadores descriptivos de revisión, no reglas de promoción.

| Origen | Ítems excluidos | Ítems restantes | Discrepancias |
|---|---|---:|---:|
| aug_dec_2025 | qv_M16, qv_M19, qv_M25, qv_M28 | 29 | 0 |
| jan_feb_2026 | qv_M07, qv_M10, qv_M16 | 30 | 0 |
| trained-model | qv_M09, qv_M12, qv_M13, qv_M27, qv_M29 | 28 | 0 |

### Variables de los modelos finales: diagnóstico sobre muestra común

Se usan las variables seleccionadas por los artefactos finales sobre la muestra mensual de C con etiquetas conocidas hasta 7-sep-2026. Para B + Q es un diagnóstico de sus variables en esa muestra común; su ajuste original sólo usó etiquetas hasta 28-jun-2026. Las columnas indicadoras y referencias se reconstruyen para cada muestra diagnóstica.

| Modelo / muestra | Columnas variables | Rango | Condición | VIF máximo |
|---|---:|---:|---|---|
| C + Q, todas las filas | 32 | 20 | Singular | No identificable |
| C + Q, respuestas completas persona-wave | 11 | 11 | 5.3 | 4.1 |
| B + Q, todas las filas | 32 | 20 | Singular | No identificable |
| B + Q, respuestas completas persona-wave | 11 | 11 | 5.4 | 4.1 |

Una matriz singular impide identificar por separado todos los coeficientes sin penalización. L2 permite ajustar predicciones, pero no convierte esos coeficientes en efectos independientes. Los diagnósticos de casos completos separan la asociación entre respuestas de los indicadores de ausencia compartidos. Las correlaciones y VIF completos están en los JSON; no son importancia causal.

### Representaciones finales: matriz de casos completos

| Representación | Columnas | Rango | Condición | VIF máximo |
|---|---:|---:|---|---|
| Preguntas + promedio completo | 11 | 11 | 5.3 | 4.1 |
| Preguntas + promedio sin duplicación | 11 | 11 | 5 | 3.5 |
| Sólo preguntas | 6 | 6 | 2.6 | 1.7 |

**Impacto en scores:** ninguno. Es una validación del modelo y de la derivación experimental; no actualiza el assessment de las fuentes.

## Sensibilidad a cuatro cortes

Se añade adquisición registrada a los tres cortes comunes, con igual partición para C y todas las variantes. Son resultados separados; no se combinan sus errores con los de tres cortes ni se cambia la comparación principal.

| Variante | Captura al 30% | Error grupo-mes |
|---|---:|---:|
| C | 42.7% | 0.9 pp |
| C + Q archivado | 43.3% | 0.9 pp |
| Preguntas + promedio completo | 42.9% | 0.9 pp |
| Preguntas + promedio sin duplicación | 42.9% | 0.9 pp |
| Sólo preguntas | 43.3% | 0.9 pp |
| Selección interna ampliada | 43.3% | 0.9 pp |

## Decisión y límites de aplicación

Mantener C como referencia si C + Q no satisface la regla conjunta. Conservar las representaciones probadas como evidencia; una mejora interna no equivale a mejora externa.

La selección interna del corte 7-sep-2026 elige **Preguntas + promedio sin duplicación**. Sus parámetros están en `trained-model/selected-model.json`. No tiene evaluación posterior al ajuste. C conserva su base de agosto de 2025; no se realizó un refit del hazard.

Para reconsiderar la sustitución, aplicar el modelo congelado a fotos posteriores a su ajuste, observar seis meses completos y repetir captura y precisión por grupo con población y capacidad comparables. Esta ejecución no genera esos resultados futuros.

- El experimento de representaciones condiciona el subconjunto a la búsqueda original; no agota todas las combinaciones nuevas.
- El promedio sin duplicación puede seguir correlacionado con las preguntas por actitudes compartidas. Quitar componentes comunes no asegura independencia.
- La media de errores puede ocultar grupos altos mal estimados. Las tablas de grupos publicables y el mayor error están en `folds/*/evaluation.json`.
- La política anual y los límites de redacción de Career se heredan de CQ. La fecha asignada por política no demuestra la fecha real de publicación de una encuesta.
- Esta revisión no prueba causalidad ni cuántas salidas evitaría una intervención.

## Reproducción, preservación y fuentes

- SQL: `queries/profiles/engineering_c_qvoice_overlap_person_month_20261009.sql`; fecha: 2026-10-09; corte 7-sep-2026.
- Plan: `docs/plans/attrition-c-qvoice-overlap-20261009.md`.
- Fuentes y parámetros anteriores: hashes en `preservation-before.json`; resultado en `preservation.json`.
- Reconciliaciones de población y métricas: `analysis-checks.json`, `folds/*/reconciliation.json`.
- Resultados: `results.json`, `verdict.json`, diagnósticos y derivaciones por origen.
- 36 ajustes de correcciones; 0 reajustes C. Tiempo del proceso completado: 8.2 minutos; no incluye reintentos anteriores.
- Autorización RAM: `config/attrition_model_in_memory_training_authorization_20261001.json`. No se guardan filas, respuestas, llaves ni predicciones individuales. Se preservan los modelos anteriores.
