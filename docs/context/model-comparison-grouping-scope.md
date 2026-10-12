# Aclaración: los 22 grupos originales de B y los árboles de 8 grupos

Fecha: 8 de octubre de 2026. Modo: `presentation`.

## Qué significa cada número

| Referencia | Agrupación | Número y alcance |
|---|---|---|
| B original: agrupación elegida el 3-oct-2026 | Antigüedad × Salidas del equipo × Nivel, con cortes fijos | 22 grupos elegibles en la foto 26-jul-2026, más resto; el número elegible puede variar por foto |
| B en `model-c-v2` y `bc-priority-comparison-v1` | Árbol que resume el riesgo de B | Hasta 8 hojas, máximo 3 condiciones por hoja; es una representación alternativa |
| C en esos experimentos | Árbol que resume el riesgo de C | Hasta 8 hojas, máximo 3 condiciones por hoja; la versión archivada tiene 8 |
| Texto «Level / 8 groups» en la base de presentación | Categorías de nivel registradas en `design.level_values_seen` | 8 valores del campo de nivel; no es el número total de segmentos de riesgo de B |

## Evidencia de la agrupación original

El informe `output/analysis/engineering/20261003/playbook-group-selection-v1/group-selection-report.md`
y su `group-selection-results.json` documentan que se compararon combinaciones
fijas de dos y tres variables y árboles de profundidad 3 y 4. La combinación
ganadora fue Antigüedad × Salidas del equipo × Nivel. Los grupos con menos de
300 personas por foto pasan a resto y no entran al top.

`final.groups_eligible` registra 22 para la foto 26-jul-2026, con 37221 personas
y 1406 personas en resto. Estos conteos son una fotografía histórica, no una
garantía de que haya siempre exactamente 22 grupos elegibles.

La configuración `config/presentations/model-selection-base.json` documenta
por separado que el texto «Level / 8 groups» toma su cifra de
`design.level_values_seen`.

### Cómo se tomó la decisión de pasar del árbol a los cruces

El encabezado histórico de `tools/presentations/build_model_selection_deck_v8.py`
registra que el árbol anterior de 8 grupos juntaba antigüedades de 1 a 7 años.
La revisión adoptó B con los seis cortes del playbook y cambió la presentación
de grupos al top 5 de la combinación ganadora.

La evaluación del 3-oct-2026 comparó 58 candidatas para agrupar los resultados
de B: 56 combinaciones fijas de dos o tres variables entre siete conceptos,
y dos árboles, de profundidad 3 y 4. El criterio principal fue conservar la
capacidad de concentrar salidas observadas fuera de muestra. La eficiencia
es Gini de la agrupación / Gini del ranking individual de B; no es exactitud
de clasificación ni porcentaje de salidas capturadas.

| Alternativa histórica | Eficiencia | Captura de salidas al priorizar 25% |
|---|---:|---:|
| Árbol de profundidad 3, hasta 8 hojas | 74.5% | 36.6% |
| Árbol de profundidad 4, hasta 16 hojas | 85% | 38.8% |
| Antigüedad × Salidas del equipo × Nivel | 90.9% | 39.5% |

Son promedios de los cuatro periodos de la evaluación original de Engineering,
para salida voluntaria a seis meses. No son cifras del experimento C reciente.
Entre combinaciones a menos de 2% relativo de la mejor eficiencia, se daba
preferencia a menos variables, luego menos grupos y después estabilidad. El
árbol debía superar a la mejor combinación fija por más de 2% para ganar.

La combinación elegida cruzaba seis bandas de antigüedad, presencia/ausencia
de salidas del equipo en 12 meses y nivel profesional agrupado en entrada,
medio y alto. Estos tres últimos nombres describen nivel, no riesgo. El 22
fue el número de combinaciones elegibles en la foto final, tras aplicar el
umbral de tamaño; no fue un número de grupos fijado de antemano. En el backtest,
el código aplica ese umbral sobre personas medias por foto del periodo.

## Límite de la comparación reciente

La comparación de prioridades del 8-oct-2026 reconstruye B con sus parámetros
ya elegidos y resume B y C mediante árboles de hasta 8 hojas. Las métricas
recientes de captura, error por grupo y estabilidad corresponden a esas
representaciones alternativas. No son una comparación de la agrupación
original de B con 22 grupos frente a los 8 de C.

Por tanto, la ventaja pequeña de C al atender 30% en esa ejecución sólo se
sostiene dentro del experimento con árboles de hasta 8 grupos. La comparación
pendiente de la receta original de cortes ya se ejecutó por separado; sus
resultados se registran más abajo. El conteo de grupos no necesita ser igual
si ambos diseños son interpretables.

La afirmación de que los tres grupos altos de B y C coinciden se refería a
los árboles de la comparación reciente. No describe los grupos originales
de B, que también distinguen salidas del equipo y usan bandas agrupadas de nivel.

## Conservación de versiones

Esta aclaración modifica únicamente documentación de contexto. No altera
coeficientes, reglas, resultados archivados ni la presentación. Los modelos
y evaluaciones anteriores conservan sus carpetas y manifiestos.

## Comparación de cortes completada el 8-oct-2026

Nuevo run: `output/analysis/engineering/20261008/c-group-selection-v1/`.
Plan previo: `docs/plans/attrition-c-group-selection-20261008.md`.
Se restauraron cuatro B y cuatro C, sin reajustes hazard. La agrupación
original de B se aplicó a los B reconstruidos sobre el frame temporal
corregido de C; no reproduce las cifras históricas del deck.

Se evaluaron 562, 288, 366 y 562 agrupaciones de C respectivamente: todos los
cruces de dos/tres dimensiones del espacio declarado y árboles de hasta
ocho/dieciséis hojas. La selección se hizo con seis fotos maduras anteriores
a cada origen externo. Se ordenaron los grupos por riesgo medio vigente en
cada snapshot, con mínimo estricto de 300 personas y resto fuera de prioridad.

Población Engineering, Employee, Regular, activo, sin RF360. Salida voluntaria
a seis meses. Periodos: febrero–julio 2024, agosto 2024–enero 2025,
febrero–julio 2025 y agosto 2025–enero 2026. Promedios al priorizar 30%:

| Modelo y agrupación | Captura | Error por grupo prioritario |
|---|---:|---:|
| B árbol hasta 8 | 43.6% | 0.5 pp |
| B cortes originales | 45.2% | 0.9 pp |
| C árbol hasta 8 | 43.9% | 0.4 pp |
| C mismos cortes de B | 45.4% | 0.8 pp |
| C selección propia por prioridad | 45.2% | 0.7 pp |
| C selección por eficiencia Gini | 45% | 0.5 pp |

B cortes supera a B árbol en captura media por 1.6 pp, aunque el error de
tasas es menor con el árbol. Son dos representaciones del mismo hazard.
C con cortes propios mantiene una captura media prácticamente igual a B
cortes y menor error por grupo; gana captura en dos periodos y pierde en dos,
IC95 de diferencia [-0.9, 0.8] pp. No demuestra mayor captura al 30%.
C con los mismos cortes gana tres periodos, pero su ventaja media de 0.3 pp
tiene IC95 [-0.3, 0.8] pp, por lo que tampoco cumple la regla al 30%.

En el escenario secundario predefinido del 40%, C con los mismos cortes
captura 57.6% frente a 56.4% de B; diferencia de 1.1 pp, IC95 [0.5, 1.7],
tres victorias y errores dentro de tolerancia: cumple la regla retrospectiva
para esa capacidad. No implica promoción ni evidencia prospectiva.

La última selección principal de C cruza antigüedad × salidas del equipo,
con 12 grupos elegibles en la foto 22-feb-2026 (seguimiento hasta
22-ago-2026), frente a 20 de B en esa misma foto. C captura 42% frente a
41.2%; errores por grupo 0.5 y 0.8 pp. Esa foto se informa por separado.
Las cuatro selecciones de C fueron distintas; el promedio evalúa la política
de selección temporal, no una única combinación fija ganadora en todos los años.

Fuente: `c-group-selection-v1/results.json`, `informe.md`, `selected-grouping.json`
y comprobaciones agregadas del run. Consulta:
`queries/profiles/engineering_model_c_person_month_20261008.sql`, ejecutada
8-oct-2026, frontera de conocimiento 7-sep-2026. Se conservaron hashes de los
artefactos anteriores, sin filas ni puntuaciones individuales persistidas.
