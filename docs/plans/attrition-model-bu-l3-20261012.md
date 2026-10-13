# Plan y cierre: BU L3 en B, C + QVoice y F + QVoice

**Nota de revisión, 12-oct-2026:** la interpretación del `rest` de la prueba
selectiva v7 se corrige en la
[revisión de Julia y Brian](revision-julia-brian-salida-rh-20261012.md).
La implementación contó también como residual a los grupos no priorizados.
Sus resultados no descartan la propuesta de conservar esos grupos y subdividir
sólo los de riesgo. El texto de cierre de v7 que sigue conserva el registro
histórico; esa conclusión selectiva requiere una nueva evaluación corregida.

## Decisión a informar

Evaluar si `ude_bu_reporting_l3`, asignada históricamente por `cost_centerid`,
aporta señal incremental a B, C + QVoice y F + QVoice, y si puede hacer más
precisos los grupos de priorización. La ejecución es experimental,
retrospectiva y en modo `presentation`; no publica filas, identificadores ni
predicciones individuales.

La pregunta de grupos se mantiene separada de la pregunta predictiva. Una
mejora de log-loss no autoriza por sí sola cambiar la definición de grupos.

## Diseño congelado

- **Población:** Engineering, Employee, Regular, activo, sin RF360.
- **Grain:** persona-foto mensual, deduplicado por empleado y fecha.
- **Conocimiento:** hasta 7-sep-2026; historia desde 26-jul-2020.
- **Cortes externos:** agosto-diciembre de 2025 y enero-febrero de 2026.
- **Horizonte:** el mismo outcome de seis meses usado por C y CQ.
- **Modelos:** B, C + QVoice y F + QVoice, cada uno con una variante que añade
  BU L3.
- **Restricción de F:** no usar `job_family_detail`, cuyo histórico no se
  considera confiable.
- **QVoice:** conservar la selección archivada de CQ; no volver a seleccionar
  preguntas mirando esta prueba.
- **Grupos base:** `antigüedad × salidas_equipo × nivel`, con capacidad
  principal de 30%.
- **Candidatas de grupos:** BU L3 sola y BU L3 combinada con cada subconjunto
  no vacío de las tres dimensiones base.
- **Ejecución:** una sola carga en memoria; sólo se persisten agregados y
  hashes de los insumos.

## Validaciones previas

El join se trató como un mapping agrupado temporal. Antes de entrenar se
guardaron y ejecutaron consultas aggregate-only para:

1. confirmar que existen `cost_centerid`, `nk_dept_id`,
   `ude_bu_reporting_l3` y las fechas SCD;
2. reconciliar el grain persona-foto y contar cost centers múltiples;
3. comprobar matches válidos únicos, multi-match de BU L3 y casos sin match;
4. detectar mappings que sólo aparecen después de la fecha de la foto;
5. medir cambios históricos de BU L3 por departamento;
6. perfilar buckets por snapshot sin publicar cohortes menores de 30.

La regla de aceptación exigía cero duplicados y cero multi-match, permitía
reportar unmatched hasta 5%, y exigía codificar como `(unknown)` cualquier
foto sin mapping válido o con mapping futuro únicamente. La regla pasó:
2,209,264 fotos, 20 sin match, 12 con mapping futuro únicamente, cero
duplicados, cero multi-match y 0.0009% unmatched.

## Transformación congelada

El mapping as-of se une con:

```sql
cost_centerid = nk_dept_id
AND edw_effective_dt <= snapshot_date
AND (edw_end_dt IS NULL OR snapshot_date < edw_end_dt)
```

Los vacíos se convierten en `(unknown)`. En el predictor categórico, cada
corte aprende el pooling con personas distintas del entrenamiento: categorías
con menos de 300 personas pasan a `(other)` y `(unknown)` se conserva. El pool
del entrenamiento se aplica sin recalcularlo al test. Para grupos se conserva
la dimensión as-of y se aplican las guardas de tamaño y eventos; la población
fuera de los grupos elegibles queda en `rest`.

## Guardas de decisión

Para el predictor se revisan log-loss, Brier, PR-AUC, lift y los intervalos
pareados por persona. Para grupos, una candidata debe cumplir simultáneamente:

- captura dentro del 2% relativo de la máxima;
- error de grupo dentro de 0.1 puntos porcentuales del mínimo entre las
  candidatas cercanas en captura;
- `rest` no más de 5 puntos porcentuales peor que el baseline.

Además de la selección formal, el resultado conserva la mejor candidata
exploratoria por captura aunque falle una guarda, para que la señal no se
oculte detrás de la etiqueta «no elegible».

## Resultado ejecutado

La ejecución `engineering-bu-l3-20261012-v4` terminó como
`completed_experimental` y duró aproximadamente 13.3 minutos. BU L3 redujo
log-loss en los tres modelos:

| Comparación | Δ log-loss ×1000 | IC95 pareado |
|---|---:|---:|
| B + BU L3 frente a B | -0.386 | [-0.641, -0.130] |
| C + QVoice + BU L3 frente a C + QVoice | -0.588 | [-0.895, -0.336] |
| F + QVoice + BU L3 frente a F + QVoice | -0.355 | [-0.572, -0.181] |

Las mejoras son pequeñas. Los intervalos de Brier cruzan cero en B y F; por
eso la lectura es de señal incremental modesta y consistente en ranking y
log-loss, no de cambio de modelo aprobado.

La mejor estructura de grupos por captura fue BU L3 × antigüedad × salidas en
su equipo: 43.6% para B, 44.0% para C + QVoice y 44.1% para F + QVoice. En los
tres casos `rest` subió a 21.5%, frente a un máximo permitido de 10.3%.
Ninguna candidata BU L3 pasó las tres guardas.

## Actualización v7: grupos actuales y refinamiento sólo en riesgo

La corrida v7 validó explícitamente las dos variantes con la estructura de
grupos actual antes de intentar subdividirla. El baseline fue
`antigüedad × salidas_equipo × nivel`, con capacidad del 30%.

| Modelo | Captura 30% | Error grupo-snapshot pp | `rest` |
|---|---:|---:|---:|
| C + QVoice + BU L3 | 43.1% | 0.9 | 5.3% |
| F + QVoice + BU L3 | 43.1% | 0.9 | 5.3% |

Después se aplicó la propuesta de subdividir por BU L3 únicamente dentro de
las celdas baseline de mayor riesgo. Se probaron mínimos de 100, 150, 200 y
300 personas por celda y se conservaron las mismas guardas de capacidad,
error y `rest`.

- **C + QVoice + BU L3:** ninguno de los cuatro mínimos produjo una
  asignación elegible para cubrir el 30% de capacidad.
- **F + QVoice + BU L3:** con mínimo de 100 personas sí se pudo asignar el
  30%, pero la primera etapa seleccionaba 36.9% de la población, `rest`
  subía a 67.7% y el error grupo-snapshot era 1.0 pp. Falló `rest` y error;
  los mínimos de 150, 200 y 300 no produjeron asignación suficiente.

Por tanto, la subdivisión restringida a grupos de riesgo reduce el alcance de
la fragmentación, pero con la capacidad global actual todavía deja demasiada
población en `rest` y no es elegible. Se conservan los grupos actuales para
las dos variantes.

## Decisión

1. Conservar BU L3 como variable documentada y challenger predictivo.
2. Mantener sin cambios los modelos B, C + QVoice y F + QVoice publicados;
   F sigue excluyendo `job_family_detail`.
3. Mantener los grupos `antigüedad × salidas_equipo × nivel`.
4. No interpretar la mejora como causalidad ni como validación prospectiva.

## Artefactos

- [Resultados agregados v7](../../output/analysis/engineering/20261012/model-bu-l3-v7/results.json)
- [Informe v7](../../output/analysis/engineering/20261012/model-bu-l3-v7/informe.md)
- [Manifest v7](../../output/analysis/engineering/20261012/model-bu-l3-v7/manifest.json)
- [Experimento](../../tools/engineering_bu_l3_experiment.py)
- [Auditoría del join](../../queries/audits/engineering_bu_l3_join_20261012.sql)
- [Perfil agregado](../../queries/profiles/engineering_bu_l3_profile_20261012.sql)
- [Configuración](../../config/engineering_bu_l3_experiment_20261012.json)
- [Configuración v7](../../config/engineering_bu_l3_experiment_20261012_v7.json)

No se cambian scores del assessment de las 43 variables. La ficha acumulativa
de BU L3 está en [`docs/variables/bu-l3/README.md`](../variables/bu-l3/README.md).
