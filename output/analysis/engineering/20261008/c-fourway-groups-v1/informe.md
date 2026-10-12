# C: más detalle en los grupos

## Añadir una variable mejora ligeramente la captura de C al priorizar al 30%

Modo `presentation`. Ejecución: 8-oct-2026. Población: Engineering, Employee, Regular, activo, sin RF360.

Objetivo: explorar si una cuarta variable permite identificar mejor grupos prioritarios, incluyendo alternativas de aproximadamente 40 grupos. **El modelo C, sus coeficientes y sus predicciones individuales se conservan.** Se modifica la agrupación y el orden de prioridad de sus medias de riesgo.

## Resultado al priorizar al 30%

Promedio con igual peso de cuatro periodos de seis fotos: febrero–julio de 2024, agosto de 2024–enero de 2025, febrero–julio de 2025 y agosto de 2025–enero de 2026. Cada foto se sigue durante seis meses. Son periodos retrospectivos ya explorados, con personas y ventanas parcialmente compartidas.

| Agrupación | Grupos elegibles, promedio | Captura | Cambio frente a C actual | IC95 del cambio | Periodos con mejora | Cumple regla |
|---|---:|---:|---:|---|---:|---|
| C · cortes actuales | 20.1 | 45.4% | Referencia | — | — | Referencia |
| C · cortes actuales + una variable | 21.4 | 45.7% | +0.3 pp | [<0.1, 0.5] pp | 3 de 4 | Sí |
| C · cuatro variables seleccionadas | 27.6 | 45.2% | -0.3 pp | [-1.2, 0.6] pp | 1 de 4 | No |
| C · búsqueda de 30–50 grupos | 33.7 | 45.1% | -0.3 pp | [-1.2, 0.5] pp | 1 de 4 | No |

**Regla declarada:** intervalo de mejora media de captura por encima de cero, mejora en al menos tres de cuatro periodos y error por grupo y grupo-mes que no empeore más de 0.1 pp frente a la prioridad actual evaluada en esa misma partición candidata. El escenario principal es añadir una variable a los cortes actuales; las otras familias y capacidades son diagnósticas.

La mejora de la alternativa principal es pequeña. Su límite inferior del IC95 es positivo pero muy próximo a cero; el cumplimiento de la regla es marginal con las 500 réplicas declaradas. Ese resultado merece una lectura prudente y no establece superioridad universal.

Captura = salidas observadas concentradas en la población priorizada / salidas observadas totales. La capacidad es idéntica por snapshot, usando pesos uniformes en el grupo del límite. Las diferencias se calculan antes del redondeo.

![Cambio de captura e incertidumbre](cambio-captura.png)

## Qué sucede con la precisión al dividir grupos

Una partición más detallada puede revelar errores que se compensaban dentro de grupos grandes. La columna «control comparable» evalúa la prioridad de C actual sobre los mismos subgrupos usados por la alternativa. De ese modo, ambas prioridades se comparan con idéntica granularidad.

| Agrupación | Error propio por grupo | Control comparable | Error propio grupo-mes | Control comparable grupo-mes | Estimado R6 en prioridad | Observado R6 en prioridad |
|---|---:|---:|---:|---:|---:|---:|
| C · cortes actuales | 0.8 pp | 0.8 pp | 0.9 pp | 0.9 pp | 4.8% | 4.6% |
| C · cortes actuales + una variable | 0.8 pp | 0.8 pp | 0.9 pp | 0.9 pp | 4.8% | 4.6% |
| C · cuatro variables seleccionadas | 0.9 pp | 1 pp | 1 pp | 1.2 pp | 4.7% | 4.6% |
| C · búsqueda de 30–50 grupos | 0.8 pp | 1 pp | 0.9 pp | 1.2 pp | 4.8% | 4.6% |

Error por grupo: diferencia absoluta entre estimado y observado por grupo, ponderada por personas. Error grupo-mes: se calcula antes de promediar meses, evitando que errores de distinto signo se cancelen. Son puntos porcentuales. Log-loss, Brier y ranking individual de C no cambian: esta búsqueda no reajusta el hazard.

| Agrupación | Mayor error publicable, promedio | Cobertura publicable de la prioridad | Población en resto | Definiciones elegidas entre cuatro periodos |
|---|---:|---:|---:|---:|
| C · cortes actuales | 1.6 pp | 99.9% | 5.1% | 1 |
| C · cortes actuales + una variable | 1.7 pp | 100% | 8.9% | 3 |
| C · cuatro variables seleccionadas | 1.7 pp | 90.2% | 13.7% | 4 |
| C · búsqueda de 30–50 grupos | 2 pp | 92.6% | 15.6% | 3 |

El mayor error sólo incluye grupos cuyo observado es publicable. La cobertura puede diferir entre agrupaciones. Resto contiene grupos con menos de 300 personas por foto, fuera de la prioridad.

## Variables seleccionadas y consistencia temporal

| Origen del C y selección | Alternativa | Cruce seleccionado | Grupos en desarrollo, promedio | Fallback de desarrollo |
|---|---|---|---:|---|
| 2024-02-01 | C · cortes actuales + una variable | Antigüedad × Salidas en su equipo × Nivel × Salida previa del manager | 21.2 | No |
| 2024-02-01 | C · cuatro variables seleccionadas | Nivel × Última promoción × Tiempo en el nivel × Salida previa del manager | 22.8 | No |
| 2024-02-01 | C · búsqueda de 30–50 grupos | Antigüedad × Reportes directos × Recontratación × Región | 30.5 | No |
| 2024-08-01 | C · cortes actuales + una variable | Antigüedad × Salidas en su equipo × Nivel × Familia de grado | 21.3 | No |
| 2024-08-01 | C · cuatro variables seleccionadas | Antigüedad × Experiencia previa × Familia de grado × Adquisición registrada | 33.8 | No |
| 2024-08-01 | C · búsqueda de 30–50 grupos | Antigüedad × Experiencia previa × Familia de grado × Adquisición registrada | 33.8 | No |
| 2025-02-01 | C · cortes actuales + una variable | Antigüedad × Salidas en su equipo × Nivel × Adquisición registrada | 21.8 | No |
| 2025-02-01 | C · cuatro variables seleccionadas | Antigüedad × Salidas en su equipo × Región × Adquisición registrada | 24.2 | No |
| 2025-02-01 | C · búsqueda de 30–50 grupos | Antigüedad × Reportes directos × Experiencia previa × Adquisición registrada | 33.5 | No |
| 2025-08-01 | C · cortes actuales + una variable | Antigüedad × Salidas en su equipo × Nivel × Adquisición registrada | 21.5 | No |
| 2025-08-01 | C · cuatro variables seleccionadas | Nivel × Última promoción × Tiempo en el nivel × Adquisición registrada | 25.8 | No |
| 2025-08-01 | C · búsqueda de 30–50 grupos | Antigüedad × Reportes directos × Experiencia previa × Adquisición registrada | 34.8 | No |

Si las selecciones cambian, las métricas evalúan la política de volver a seleccionar con el pasado; no prueban una sola combinación en los cuatro periodos. El archivo final conserva la selección del último origen evaluado, 1-ago-2025. No se reajusta hasta septiembre de 2026.

| Fotos evaluadas | Cruces explorados | C actual: captura | + una variable | Cuatro variables | Búsqueda 30–50 grupos |
|---|---:|---:|---:|---:|---:|
| 2024-02-18 a 2024-07-21 | 1365 | 49.1% | 48.3% | 47.1% | 48.1% |
| 2024-08-25 a 2025-01-26 | 330 | 44.2% | 44.7% | 43.9% | 43.9% |
| 2025-02-23 a 2025-07-27 | 715 | 46.1% | 47.1% | 45.3% | 46.6% |
| 2025-08-24 a 2026-01-25 | 1365 | 42.3% | 42.7% | 44.3% | 42% |

## Sensibilidad a la capacidad

| Capacidad | Alternativa | Captura | Cambio frente a C actual | IC95 | Cumple regla |
|---|---|---:|---:|---|---|
| 20% | C · cortes actuales + una variable | 31.8% | +0.1 pp | [-0.1, 0.3] pp | No |
| 20% | C · cuatro variables seleccionadas | 33.2% | +1.5 pp | [0.6, 2.3] pp | Sí |
| 20% | C · búsqueda de 30–50 grupos | 32.6% | +0.9 pp | [0.2, 1.8] pp | Sí |
| 30% | C · cortes actuales + una variable | 45.7% | +0.3 pp | [<0.1, 0.5] pp | Sí |
| 30% | C · cuatro variables seleccionadas | 45.2% | -0.3 pp | [-1.2, 0.6] pp | No |
| 30% | C · búsqueda de 30–50 grupos | 45.1% | -0.3 pp | [-1.2, 0.5] pp | No |
| 40% | C · cortes actuales + una variable | 57.7% | +0.1 pp | [-0.3, 0.4] pp | No |
| 40% | C · cuatro variables seleccionadas | 55.9% | -1.7 pp | [-2.6, -0.6] pp | No |
| 40% | C · búsqueda de 30–50 grupos | 57.3% | -0.2 pp | [-1.2, 0.8] pp | No |

### La granularidad útil depende de cuánta población se atiende

**Al concentrar acciones en el 20%, las agrupaciones más detalladas sí muestran una señal favorable.** La política de seleccionar cuatro variables captura 33.2% de las salidas frente a 31.7% con los cortes actuales: +1.5 pp, IC95 [0.6, 2.3], y mejora en tres de cuatro periodos. La búsqueda de 30–50 grupos mejora 0.9 pp, IC95 [0.2, 1.8]. Ambas cumplen la regla para esa capacidad secundaria declarada.

Para el 30%, la señal favorable corresponde a conservar los tres cortes y añadir una variable, con una ganancia mucho menor. Para el 40%, ninguna alternativa supera la regla. El número de grupos y el porcentaje de población atendida son decisiones distintas.


## Foto madura adicional: febrero de 2026

Foto 2026-02-22, seguimiento hasta 2026-08-22, 35313 personas. Se aplican las selecciones de agosto de 2025; esta foto no se añade al promedio histórico ni se usa para escoger el cruce final.

| Agrupación | Grupos elegibles | Resto | Captura al 30% | Estimado R6 | Observado R6 | Error grupo-mes |
|---|---:|---:|---:|---:|---:|---:|
| C · cortes actuales | 20 | 5.3% | 42.7% | 5.6% | 5% | 1 pp |
| C · cortes actuales + una variable | 23 | 9.4% | 42.9% | 5.6% | 5% | 0.9 pp |
| C · cuatro variables seleccionadas | 30 | 14.2% | 43.5% | 5.3% | 5.1% | 0.9 pp |
| C · búsqueda de 30–50 grupos | 36 | 16.2% | 40.9% | 5.3% | 4.8% | 0.6 pp |

### Cortes finales y grupos completos

| Alternativa | Definición aplicada | Cobertura sin grupo límite | Captura sin grupo límite | Cobertura con grupo límite | Captura con grupo límite |
|---|---|---:|---:|---:|---:|
| C · cortes actuales | Antigüedad × Salidas en su equipo × Nivel | 29% | 41.6% | 36.3% | 49.9% |
| C · cortes actuales + una variable | Antigüedad × Salidas en su equipo × Nivel × Adquisición registrada | 27.9% | 40.5% | 35.1% | 48.7% |
| C · cuatro variables seleccionadas | Nivel × Última promoción × Tiempo en el nivel × Adquisición registrada | 28% | 41.1% | 35.1% | 49.8% |
| C · búsqueda de 30–50 grupos | Antigüedad × Reportes directos × Experiencia previa × Adquisición registrada | 29.3% | 40.2% | 30.6% | 41.5% |

Los grupos concretos de cada alternativa se guardan en `grupos-prioritarios-febrero.csv` y en `results.json`. Las tasas suprimidas permanecen vacías. Los tamaños del CSV son personas efectivas seleccionadas; pueden ser fraccionales por el peso del grupo del límite.

## Recomendación para continuar

- **Con capacidad cercana al 30%:** la alternativa para seguir revisando es antigüedad × salidas del equipo × nivel × adquisición registrada, con 23 grupos elegibles en febrero de 2026. Es la última selección de la política «añadir una variable»; no fue la combinación seleccionada en los cuatro periodos y su ganancia media es marginal.
- **Con capacidad limitada al 20%:** la política de seleccionar cuatro variables merece consideración por su mayor captura en ese escenario. Su último cruce es nivel × última promoción × tiempo en el nivel × adquisición registrada, con 30 grupos en febrero de 2026. La cifra media de mejora evalúa las cuatro selecciones históricas, no sólo este último cruce.
- Las alternativas orientadas a unos 40 grupos generaron 36 en la última foto y no mejoraron la captura al 30%. La granularidad debe elegirse por capacidad, evidencia y precisión, sin fijar 40 como objetivo numérico.
- La mayor fragmentación deja más población en grupos de menos de 300 personas. En febrero, resto pasa de 5.3% con los cortes actuales a 9.4% con la variable adicional y 16.2% con la búsqueda de 30–50 grupos. Es parte del coste de ese detalle.
- «Adquisición registrada» describe el registro disponible. «Sin registro» no demuestra ausencia de adquisición ni identifica una causa de attrition. Las acciones requieren diagnóstico adicional.

## Búsqueda, evidencia y límites

- Se exploraron 3775 cruces entre los cuatro periodos (una misma definición puede aparecer en varios). Se usan todos los cruces de cuatro conceptos del espacio disponible en cada C; no todos los umbrales posibles.
- Los tres conceptos actuales conservan sus cortes. Las variables adicionales usan las bandas originales del C de cada origen, con faltantes explícitos. Se excluyen calendario, interacciones y repeticiones de concepto. La búsqueda anterior empleaba cruces de dos/tres dimensiones y versiones más gruesas de algunas variables.
- En desarrollo: máximo 50 grupos por foto, al menos 80% de población en grupos elegibles y mínimo 300 personas por grupo y foto. La familia de aproximadamente 40 exige media de 30–50. Estos límites de desarrollo no garantizan el mismo número de grupos en fechas futuras.
- Selección: seis fotos con seguimiento R6 terminado antes del origen; mayor captura al 30%, tolerancia 2% relativo; menor exceso de error grupo-mes frente al control comparable, tolerancia 0.1 pp; después menos grupos, mayor captura y nombre estable.
- Fallback: cortes actuales si no hay candidato admisible en desarrollo o la población elegible externa no alcanza para atender 40%. Se registra sin reselección basada en las salidas externas.
- Los IC95 usan 500 remuestreos pareados por persona y conservan sus ventanas. Son condicionales a modelos, selección y asignación fijados; no corrigen comparaciones múltiples ni garantizan estabilidad futura.
- Las etiquetas de desarrollo participaron parcialmente en el ajuste del hazard C. Las salidas externas no eligen sus cortes. La evidencia es retrospectiva y conserva las limitaciones de las fuentes de C.
- Los cortes de referencia proceden de una exploración histórica de B sobre periodos ya inspeccionados. Esa historia puede favorecer la referencia; este experimento no demuestra que se hayan agotado todas las agrupaciones posibles, incluyendo divisiones adaptativas de cada grupo.
- Fuente SQL: `queries/profiles/engineering_model_c_person_month_20261008.sql`, ejecutada el 8-oct-2026; conocimiento hasta 2026-09-07. Se reprodujeron población, métricas C y los cortes actuales contra sus archivos originales.
- Tiempo: 4.1 minutos, incluidos 2.8 de carga. Cero reajustes hazard. Cruces calculados con índices enteros y acumulaciones en memoria.
- Plan: `docs/plans/engineering-c-fourway-groups-20261008.md`; configuración: `frozen-config.json`; selecciones y modelos de agrupación: `selected-groupings.json`; evidencia: `folds/`, `development-candidates/`, `analysis-checks.json`, `preservation.json` y `manifest.json`.
- B, C, B + QVoice y C + QVoice conservan sus archivos. No se publican ni guardan filas, llaves o riesgos individuales. Los grupos expresan asociaciones predictivas; no efectos causales de acciones de retención.
