# Random Survival Forest frente a B, C y sus variantes

Experimento iniciado el 8-oct-2026 y completado el 9-oct-2026. Modo `presentation`. Población: Engineering, Employee, Regular, activo, sin RF360.

## Conclusión

El bosque calibrado no cumple todos los requisitos declarados para sustituir a C.
La captura al priorizar al 30% cambia +0.3 pp, IC95 [0.1, 0.5] pp; mejora en 2 de cuatro periodos.

La regla exige mejora de captura con IC95 positivo y tres victorias, sin aumentar los errores por grupo/grupo-mes más de 0.1 pp ni log-loss/Brier más de 0.5% relativo. La comparación principal usa los mismos cortes de grupos.

La versión sin calibrar es más competitiva: cambia la captura +0.3 pp y gana en 2 de cuatro periodos. Tampoco cumple la regla conjunta: los detalles de cada condición están en verdict-uncalibrated.json.

Recomendación: mantener C como referencia y conservar RSF sin calibrar como candidato experimental. Su ligera ganancia de captura no viene acompañada de una mejora estable entre periodos; la calibración ensayada empeora el promedio histórico. La variante de C que añade un corte ofrece una captura semejante con menor error de los grupos.

![Captura comparada](captura-comparada.png)

## Cuatro periodos históricos

Febrero–julio 2024, agosto 2024–enero 2025, febrero–julio 2025 y agosto 2025–enero 2026. Cada foto tiene seguimiento de seis meses. Las medias dan igual peso a cada periodo; las personas y ventanas pueden repetirse. Las diferencias se calculan antes de redondear.

| Variante | Grupos, media | Captura 20% | Captura 30% | Captura 40% | Error grupo-mes al 30% |
|---|---:|---:|---:|---:|---:|
| B · cortes actuales | 20.1 | 31.5% | 45.2% | 56.4% | 0.9 pp |
| C · cortes actuales | 20.1 | 31.7% | 45.4% | 57.6% | 0.9 pp |
| RSF sin calibrar | 20.1 | 31.9% | 45.8% | 56% | 1 pp |
| RSF calibrado | 20.1 | 31.9% | 45.8% | 56% | 1.4 pp |
| RSF · árbol explicativo | 14.6 | 30.4% | 43.2% | 54.3% | 1.3 pp |
| C · cortes + una variable | 21.4 | 31.8% | 45.7% | 57.7% | 0.9 pp |
| C · cuatro variables | 27.6 | 33.2% | 45.2% | 55.9% | 1 pp |
| C · cerca de 40 grupos | 33.7 | 32.6% | 45.1% | 57.3% | 0.9 pp |
| C · árbol archivado | 8 | 31.2% | 43.9% | 53.7% | 0.5 pp |

Captura = salidas observadas dentro de la prioridad / todas las salidas observadas. La capacidad se iguala en cada foto, con peso uniforme en el grupo del límite. Los grupos de menos de 300 personas van a resto. El número de grupos de la tabla es la media de grupos elegibles por foto, no el número de grupos que se atendería. Las cifras de personas, errores y grupos completos están en los JSON. Error grupo-mes es el promedio absoluto de la diferencia entre riesgo estimado y observado de cada grupo en cada foto, ponderado por su población priorizada. Se expresa en puntos porcentuales.

### Precisión global y discriminación

| Modelo | Log-loss × 1000 ↓ | Brier × 1000 ↓ | PR-AUC ↑ | R6 estimado | R6 observado |
|---|---:|---:|---:|---:|---:|
| B · cortes actuales | 132.4 | 29.2 | 5.2% | 3.3% | 3% |
| C · cortes actuales | 131.9 | 29.1 | 5.3% | 3% | 3% |
| RSF sin calibrar | 131.8 | 29.1 | 5.5% | 2.9% | 3% |
| RSF calibrado | 133.4 | 29.2 | 5.5% | 2.9% | 3% |

Log-loss penaliza probabilidades equivocadas, sobre todo errores con mucha confianza. Brier mide el error cuadrático de las probabilidades. Ambos se muestran multiplicados por 1000 para facilitar la lectura. PR-AUC resume la separación de salidas en un evento poco frecuente. La precisión por grupo se evalúa aparte: una tasa global correcta puede ocultar errores que se compensan.

![Error por periodo](error-grupos-periodos.png)

### Precisión sobre la misma población priorizada por C

Se mantienen los grupos y la selección del 30% de C para comparar únicamente las probabilidades.

| Modelo | R6 estimado | R6 observado | Error por grupo | Error grupo-mes |
|---|---:|---:|---:|---:|
| B · cortes actuales | 5% | 4.6% | 0.9 pp | 1 pp |
| C · cortes actuales | 4.8% | 4.6% | 0.8 pp | 0.9 pp |
| RSF sin calibrar | 4.2% | 4.6% | 0.9 pp | 1 pp |
| RSF calibrado | 4.3% | 4.6% | 1.3 pp | 1.4 pp |

### Referencia anterior: prioridades de los árboles B/C

La comparación archivada de árboles ordenaba las hojas por su riesgo de entrenamiento. Se conserva aquí como referencia histórica. Las tablas anteriores ordenan los grupos por la media de predicciones de cada foto; por eso no se mezclan sus reglas de prioridad.

| Árbol y orden archivados | Captura al 30% | Error grupo-mes |
|---|---:|---:|
| B | 43.6% | 0.6 pp |
| C | 43.9% | 0.5 pp |

## Comparación en los periodos disponibles de QVoice

Agosto–diciembre de 2025 y enero–febrero de 2026; mismo conjunto de personas/fotos para todos los modelos de cada periodo. Se restauraron los parámetros históricos de las variantes. Este bloque tiene menos historia y no se mezcla con el promedio de los cuatro periodos. En enero–febrero de 2026 el bosque tiene ajuste de enero, mientras B y C conservan su último ajuste archivado de agosto de 2025; las correcciones QVoice conservan sus propios cortes de actualización. Es una comparación de las versiones disponibles, no una aislación perfecta del efecto de la familia del modelo.

B + QVoice se reproduce con su SQL original para el historial de salidas del equipo: usa fecha efectiva y frontera global. C/RSF añade que cada salida ya estuviera registrada en la foto. Se alinearon personas, fechas y episodios. Una etiqueta R6 entre 238451 observaciones difiere por el límite global de registro de BQ, confirmado mediante recálculo agregado. Todos los modelos se evalúan con la misma etiqueta y cortes de C; la reproducción de las métricas archivadas de BQ utiliza su etiqueta original. Por tanto BQ conserva la limitación temporal de su versión archivada y C hereda esa diferencia de observación. La conciliación predictiva exige reproducir todas sus métricas, incluido ranking; la diferencia inicial no se atribuye a empates numéricos. Véanse bq-input-reconciliation.json y bq-label-contract-audit.json.

| Variante | Captura al 30% | Error grupo-mes | Log-loss × 1000 | Brier × 1000 |
|---|---:|---:|---:|---:|
| B · cortes actuales | 41.6% | 0.8 pp | 138.7 | 30.7 |
| C · cortes actuales | 42.4% | 1 pp | 138.8 | 30.7 |
| RSF sin calibrar | 42.5% | 0.7 pp | 137.7 | 30.7 |
| RSF calibrado | 42.5% | 0.6 pp | 137.6 | 30.6 |
| RSF · árbol explicativo | 41.8% | 0.5 pp | 137.6 | 30.6 |
| C · cortes + una variable | 42.7% | 0.9 pp | 138.8 | 30.7 |
| C · cuatro variables | 44.1% | 1.1 pp | 138.8 | 30.7 |
| C · cerca de 40 grupos | 41.5% | 0.7 pp | 138.8 | 30.7 |
| C · árbol archivado | 41.5% | 0.5 pp | 138.8 | 30.7 |
| C · intercepto actualizado | 42.4% | 1 pp | 138.8 | 30.7 |
| C · disponibilidad QVoice | 42.5% | 1 pp | 139 | 30.8 |
| C + QVoice sin calibrar | 43.1% | 1 pp | 137.7 | 30.7 |
| C · escalar R6 | 42.4% | 1.1 pp | 138.8 | 30.8 |
| C · intercepto y escalar | 42.4% | 1 pp | 138.8 | 30.7 |
| C · disponibilidad y escalar | 42.5% | 1 pp | 139 | 30.8 |
| C + QVoice con escalar R6 | 43.1% | 1 pp | 137.7 | 30.7 |
| B + QVoice sin calibrar | 43.1% | 0.7 pp | 137.3 | 30.6 |
| B + QVoice con calibración mensual | 43.1% | 0.7 pp | 137.7 | 30.6 |
| B + QVoice con escalar R6 | 43.1% | 0.8 pp | 137.6 | 30.6 |

En estos periodos recientes, el bosque calibrado estima mejor las tasas de los grupos: error 0.6 pp, frente a 1 pp de C + QVoice sin calibración posterior y 0.7 pp de B + QVoice sin calibración posterior. Su captura es 42.5%, frente a 43.1%/43.1%, respectivamente. Es un punto favorable para la precisión reciente de RSF; su ventaja depende del periodo y de la métrica. Las diferencias puntuales entre variantes QVoice y RSF no se presentan como una prueba directa de superioridad estadística.

Las variantes de grupos C comparten sus predicciones individuales; cambian la agrupación y la prioridad. El escalar conserva el orden individual, aunque promediar probabilidades transformadas puede cambiar el orden de grupos. Las variantes QVoice conservan sus fechas originales de ajuste y sus limitaciones de calibración. El bosque de este experimento no incorpora QVoice.

## Foto adicional con modelos del mismo origen

Foto del 22-feb-2026, seguida hasta el 22-ago-2026. Aquí B, C y RSF conservan el origen de agosto de 2025; permite revisar esta fecha con igual antigüedad de los modelos. No se añade al promedio de los cuatro periodos.

| Modelo | Captura al 30% | R6 estimado en prioridad | R6 observado | Error grupo-mes |
|---|---:|---:|---:|---:|
| B · cortes actuales | 41.2% | 5.5% | 4.8% | 0.8 pp |
| C · cortes actuales | 42.7% | 5.6% | 5% | 1 pp |
| RSF sin calibrar | 42.7% | 4.7% | 5% | 0.5 pp |
| RSF calibrado | 42.7% | 4.6% | 5% | 0.6 pp |

## Qué se entrenó y cómo se calibró

- Biblioteca: scikit-survival 0.28.0. Bosque con divisiones log-rank y curvas de supervivencia; horizonte discretizado en seis meses calendario desde cada foto.
- Cada foto es un nuevo origen con covariables conocidas. R6 = 1-S(6); los meses sin seguimiento completo se censuran en el último mes completo al origen. La etiqueta madura coincide con y_6m de C.
- Ocho configuraciones por origen: señales base B o todos los conceptos candidatos de C, hojas mínimas 150/400 y selección de variables sqrt/0.5. One-hot aprendida sólo en entrenamiento.
- 80 árboles al seleccionar; 200 al ajustar. Bootstrap de hasta 40000 filas por árbol, profundidad máxima 12 y cuatro hilos. Las filas de una persona pueden aparecer en distintas fotos; los intervalos de incertidumbre remuestrean personas completas.
- Optimización: se omiten las filas de peso cero de cada muestra bootstrap, conservando los índices seleccionados, sus multiplicidades, el eje temporal y las semillas. El primer árbol de cada ajuste optimizado se contrasta con la ejecución completa de la biblioteca; se exige igualdad de divisiones y curvas dentro de tolerancia numérica. El primer bosque histórico se conserva tal como se ajustó con la implementación completa.
- Tres fotos maduras para elegir la configuración y tres posteriores para calibrar. Todas anteriores al periodo externo. El bosque auxiliar se ajusta antes de las seis fotos.
- Calibración escalar: R ajustado = 1-(1-R crudo)^exp(a). Se transfiere al bosque reajustado al origen; por eso se publican ambas versiones y se comprueba el resultado fuera del ajuste.
- Árbol explicativo: hasta 16 hojas y profundidad 4, ajustado a predicciones del bosque en la última foto de entrenamiento. Sus reglas agrupan; el riesgo lo sigue estimando el bosque.
- El modelo final en trained-model/ usa el corte 7-sep-2026. Sus parámetros se distinguen de los cinco modelos históricos; no se presentan como si ya hubieran sido evaluados a futuro.

### Modelo final archivado

Configuración: `all_C_candidates_leaf150_features0.5`; 200 árboles. El árbol explicativo final tiene 16 hojas. Su número de grupos elegibles dependerá del tamaño de cada grupo en la foto donde se aplique.

Variables: `level_grouped`, `tenure_playbook_band`, `calendar_month`, `manager_changes_12m`, `team_exits_12m`, `direct_reports_band`, `time_since_promotion_band`, `rehire`, `prior_experience_band`, `time_at_level_band`, `manager_left_6m`, `ios_12m`, `layers_band`, `work_arrangement_group`, `region`, `comp_ratio_band`, `grade_family`, `acquisition_recorded`, `transfer_12m`.

### Selecciones por origen

| Origen | Señales elegidas | Hoja mínima | Variables por división | Multiplicador calibración |
|---|---|---:|---|---:|
| 2024-02-01 | all_C_candidates | 150 | sqrt | 0.6 |
| 2024-08-01 | all_C_candidates | 150 | sqrt | 1.3 |
| 2025-02-01 | all_C_candidates | 150 | 0.5 | 1.1 |
| 2025-08-01 | all_C_candidates | 150 | 0.5 | 1 |
| 2026-01-01 | all_C_candidates | 150 | 0.5 | 1 |
| 2026-09-07 | all_C_candidates | 150 | 0.5 | 1.1 |

## Interpretación y límites

- Un bosque puede captar interacciones sin especificarlas previamente, pero sus cientos de árboles son más difíciles de explicar que una fórmula. Los cortes comunes y el árbol explicativo permiten revisar grupos y el coste de simplificar.
- Sólo se estiman y contrastan curvas hasta seis meses. No se valida una extrapolación a 12 meses.
- Se conserva el outcome de B/C: otras salidas no son el evento voluntario. No se añade un modelo de riesgos competitivos. Se heredan límites de registro tardío y observación.
- Se evaluó una rejilla acotada de hiperparámetros y estas representaciones de variables. El resultado describe este experimento; no demuestra que se haya agotado toda la familia RSF.
- Para agrupar el bosque se probaron los cortes comunes y un árbol explicativo de hasta 16 hojas. No se hizo una búsqueda exhaustiva de cruces de cuatro variables específica para RSF; las variantes de cuatro cortes comparadas pertenecen al experimento archivado de C.
- Los periodos fueron explorados anteriormente; la evidencia es retrospectiva. Los IC95 usan 500 remuestreos por persona y son condicionales a modelos, selecciones y prioridades; no corrigen comparaciones múltiples.
- Selección y calibración usan fotos diferentes, pero sus ventanas de seguimiento se superponen. El periodo externo comienza después de que terminaron ambas ventanas; la separación de fotos no implica independencia estadística entre selección y calibración.
- Frecuencia de divisiones en serialization-check.json describe uso de variables; no es importancia causal. Los grupos sugieren dónde investigar, sin demostrar que una acción evite salidas.
- Tiempo del último proceso completado (ajuste final): 8 minutos, incluidos 5.3 de carga. Cero reajustes de B/C y sus variantes.
- Hubo un intento de carga previo interrumpido por permisos de Windows antes de completar el primer candidato. Ese intento y la instalación de dependencias no están incluidos en el tiempo de la ejecución completada; se registra en setup-interruption.json.
- Una segunda interrupción ocurrió al interpretar los identificadores numéricos del árbol archivado de C. El bosque ya entrenado se recuperó de sus parámetros y se corrigió la lectura de esas hojas; evaluation-interruption.json conserva el registro. El tiempo anterior a reanudar tampoco forma parte del último cronómetro de ejecución.
- Las interrupciones del bloque B + QVoice y su corrección de contrato se documentan en resume-history.json; los cinco bosques históricos completos se reutilizaron. El cronómetro final tampoco incluye esas ejecuciones interrumpidas.
- Una carga perdió la conexión a Redshift y terminó con OperationalError e InterfaceError tras el cambio al 9-oct-2026. La carga final usa una conexión por año y reintento acotado. No se confirmó la causa exacta de la desconexión.
- Una segunda desconexión ocurrió al cargar 2026. La comprobación posterior SELECT 1 funcionó. Se separaron las fases de comparación y ajuste final, con keepalive y reintentos de conexión. comparison-completed.json registra el tiempo de la comparación completada; el cronómetro anterior sólo corresponde al último proceso y no al tiempo total de la tarea.

## Fuentes y reproducción

- Configuración: frozen-config.json; plan: source/docs/plans/engineering-random-survival-forest-20261008.md.
- Consulta: queries/profiles/engineering_rsf_person_month_20261008.sql; ejecuciones 8–9 oct 2026; conocimiento hasta 7-sep-2026. Derivada de la consulta C + QVoice conservando las covariables de C.
- Evidencia: population.json, input-checks.json, historical-results.json, qvoice-results.json y extension.json.
- Modelos: folds/<origen>/ y trained-model/. forest-parameters.npz contiene sólo parámetros de inferencia; no contiene filas, llaves, muestras bootstrap ni etiquetas individuales.
- predict_export() en el script del experimento permite reconstruir R6 crudo; model.json contiene el escalar. Las predicciones se mantienen exclusivamente en memoria.
- Preservación: preservation.json y manifest.json. Resultados agregados y tasas suprimidas según los mínimos de publicación; autorización RAM del 1-oct-2026.
- summary-reconciliation.json documenta la actualización de los promedios tras recuperar un bosque: la diferencia de PR-AUC está por debajo del redondeo mostrado. revisions/before-summary-reconciliation/ conserva los agregados y el código anteriores; los parámetros de los modelos y los intervalos bootstrap se conservan.
