# BU L3

**Nota de revisión, 12-oct-2026:** el `rest` de la prueba selectiva v7 incluye
grupos no priorizados, por lo que no mide sólo fragmentación. La conclusión
de rechazo de esa propuesta no queda validada; véase la
[revisión de Julia y Brian](../../plans/revision-julia-brian-salida-rh-20261012.md).
La comparación predictiva se conserva. La partición que mantiene los grupos
base fuera de prioridad requiere una evaluación corregida.

## Resumen de la variable

BU L3 es una categoría organizacional que se asigna a cada foto mensual de un
empleado a partir de su `cost_centerid` y del catálogo histórico de
departamentos. En esta ronda se evaluó como señal predictiva y como dimensión
posible para definir grupos de priorización de attrition.

La variable se documenta en modo `presentation`. Los resultados publicados son
agregados; no se guardan filas de empleados, identificadores ni predicciones
individuales.

## Flujo histórico y definición operativa

1. La población parte de `hrda.post_hire_monthly_worker_dtls`, filtrada a
   `worker_type = 'Employee'`, `employee_type = 'Regular'`,
   `active_status = 1`, `is_rf360_yes_no = 0` y `eng_or_noneng =
   'Engineering'`.
2. El grain es `employee-snapshot`. Para cada empleado y fecha se conserva un
   único `cost_centerid`; la auditoría no encontró fotos con más de un cost
   center.
3. El join histórico se hace con
   `cost_centerid = d_department.nk_dept_id` y la ventana as-of:
   `edw_effective_dt <= snapshot_date` y
   `edw_end_dt IS NULL OR snapshot_date < edw_end_dt`.
4. Se toma `d.ude_bu_reporting_l3` del registro vigente. Los valores nulos o
   vacíos se codifican como `(unknown)`. Un mapping que sólo aparece en el
   futuro nunca se usa para una foto anterior.
5. La fecha límite de conocimiento es 7-sep-2026. La preparación usa historia
   desde 26-jul-2020 y conserva los cortes de evaluación de agosto-diciembre de
   2025 y enero-febrero de 2026.

El mapping es un `grouped_mapping` temporal: la fuente de BU L3 está en
`d_department`, pero su aplicación al empleado depende de la fecha de la foto.
No se trata como una columna directa de la tabla de empleados.

## Auditoría del mapping

La consulta de join es
[`engineering_bu_l3_join_20261012.sql`](../../../queries/audits/engineering_bu_l3_join_20261012.sql).
La consulta de metadata está en
[`engineering_bu_l3_metadata_20261012.sql`](../../../queries/audits/engineering_bu_l3_metadata_20261012.sql).

| Métrica agregada | Resultado |
|---|---:|
| Fotos empleado-snapshot | 2,209,264 |
| Fotos con cost center | 2,209,256 |
| Fotos con BU L3 válido | 2,209,244 |
| Fotos sin match histórico | 20 |
| Fotos con mapping futuro únicamente | 12 |
| Duplicados de match válido | 0 |
| Multi-match de BU L3 | 0 |
| Fotos con más de un cost center | 0 |
| Fechas de snapshot | 74 |
| IDs de departamento con más de un BU L3 histórico | 3,538 de 29,025 |
| Tasa sin match | 0.0009% |

La regla de aceptación exigía cero duplicados y cero multi-match, reportar los
casos sin match y no usar mappings futuros. La regla pasó. El hecho de que
3,538 departamentos hayan cambiado de BU L3 a lo largo de su historia es la
razón para conservar el join as-of; un `MAX` actual por departamento habría
introducido valores futuros en fotos antiguas.

El perfil agregado por fecha y BU L3 está en
[`engineering_bu_l3_profile_20261012.sql`](../../../queries/profiles/engineering_bu_l3_profile_20261012.sql).
Los buckets compartibles se limitaron a cohortes de al menos 30 personas.

## Codificación en los modelos

BU L3 se incorporó como predictor categórico aditivo. No se convirtió en una
variable ordinal y no se ordenaron sus etiquetas por riesgo.

Para el término del modelo se ajusta el pooling usando únicamente el conjunto
de entrenamiento de cada corte:

- se cuentan personas distintas por BU L3;
- las categorías con menos de 300 personas de entrenamiento se agrupan en
  `(other)`;
- `(unknown)` se conserva como categoría explícita;
- el mismo pool aprendido en entrenamiento se aplica al test.

Para la prueba de grupos se conserva la etiqueta BU L3 del mapping as-of y se
aplican las guardas de elegibilidad por foto. Las combinaciones que no alcanzan
300 personas por snapshot o 30 salidas observadas en la regla correspondiente
contribuyen a `rest`; no se eliminan empleados para mejorar la captura.

## Uso en cada modelo

| Modelo experimental | Cómo se incorporó | ¿Se conserva en el modelo elegido? | Resultado |
|---|---|---|---|
| B + BU L3 | Predictor categórico adicional sobre los 8 términos y 2 interacciones de B; pooling aprendido por corte | No | Mejora pequeña y consistente en log-loss y ranking; queda como challenger |
| C + QVoice + BU L3 | Predictor categórico adicional sobre C y la corrección QVoice archivada | No | Es la mejora predictiva media más grande de las tres pruebas |
| F + QVoice + BU L3 | Predictor categórico adicional sobre F = C + ciudad, sin `job_family_detail`, y la misma corrección QVoice | No | Mejora pequeña; F sigue siendo experimental |

Los modelos B, C + QVoice y F + QVoice se reajustaron en memoria en cada corte;
no se añadieron filas al dataset y no se alteraron los artefactos de B, C ni
CQ. `job_family_detail` no se usó en F ni en esta prueba.

## Efecto predictivo

Los promedios combinan los dos bloques de evaluación. Log-loss y Brier son
mejores cuando bajan; PR-AUC y lift cuando suben.

| Modelo | Log-loss control → BU L3 ×1000 | Brier control → BU L3 ×1000 | PR-AUC control → BU L3 | Lift control → BU L3 |
|---|---:|---:|---:|---:|
| B | 138.7 → 138.2 | 30.7 → 30.7 | 4.8% → 5.0% | 1.8 → 1.9 |
| C + QVoice | 137.7 → 137.0 | 30.7 → 30.6 | 5.5% → 5.7% | 2.1 → 2.1 |
| F + QVoice | 136.4 → 136.0 | 30.6 → 30.6 | 5.9% → 6.0% | 2.2 → 2.3 |

Los intervalos pareados de la diferencia de log-loss, en unidades ×1000,
fueron B `-0.386`, IC95 `[-0.641, -0.130]`; C + QVoice `-0.588`, IC95
`[-0.895, -0.336]`; y F + QVoice `-0.355`, IC95 `[-0.572, -0.181]`.
Los intervalos de Brier son más débiles y cruzan cero en B y F. Esto respalda
tratar BU L3 como señal incremental modesta, no como motivo suficiente para
reemplazar el modelo seleccionado.

## Uso como dimensión de grupos

La estructura actual es `Antigüedad × Salidas en su equipo × Nivel`. Se
probaron BU L3 sola y sus combinaciones con cada subconjunto de esas tres
dimensiones. La mejor candidata exploratoria se definió por mayor captura
media; los desempates usan menor error de grupo, menor `rest` y menor
complejidad.

| Modelo | Captura actual | Mejor candidata | Captura candidata | Error actual pp | Error candidato pp | Decisión |
|---|---:|---|---:|---:|---:|---|
| B | 41.6% | BU L3 × Antigüedad × Salidas en su equipo | 43.6% | 0.8 | 0.9 | No elegible: error y `rest` |
| C + QVoice | 43.1% | BU L3 × Antigüedad × Salidas en su equipo | 44.0% | 1.0 | 0.9 | No elegible: `rest` |
| F + QVoice | 43.1% | BU L3 × Antigüedad × Salidas en su equipo | 44.1% | 0.9 | 0.8 | No elegible: `rest` |

Las guardas fueron: captura dentro del 2% relativo de la máxima, error de
grupo como máximo 0.1 puntos porcentuales por encima del mínimo entre las
candidatas cercanas en captura, y `rest` como máximo 5 puntos porcentuales por
encima del baseline. Ninguna estructura con BU L3 pasó las tres guardas.
La señal organizacional existe, pero al combinarla con antigüedad y salidas
fragmenta demasiado la población para el uso de grupos actual.

### Validación adicional: grupos actuales y refinamiento sólo en riesgo

La corrida v7 volvió a medir C + QVoice + BU L3 y F + QVoice + BU L3 con los
grupos actuales y después subdividió por BU L3 sólo las celdas baseline de
mayor riesgo. Así se evita fragmentar de entrada a toda la población.

| Modelo | Captura 30% | Error grupo-snapshot pp | `rest` |
|---|---:|---:|---:|
| C + QVoice + BU L3 | 43.1% | 0.9 | 5.3% |
| F + QVoice + BU L3 | 43.1% | 0.9 | 5.3% |

Se probaron mínimos de 100, 150, 200 y 300 personas por subcelda. C + QVoice +
BU L3 no alcanzó una asignación elegible para cubrir el 30% con ninguno de
los mínimos. F + QVoice + BU L3 sí alcanzó la capacidad con mínimo de 100,
pero dejó 67.7% en `rest`, frente a 5.3% del baseline, y elevó el error a
1.0 pp; por eso falló las guardas de `rest` y error. Con mínimos de 150, 200
y 300 no hubo población elegible suficiente para la capacidad declarada.

La propuesta es útil como prueba de sensibilidad, pero no permite adoptar
subgrupos BU L3 dentro de los grupos de riesgo bajo la capacidad global actual.
Los grupos actuales permanecen vigentes para ambas variantes.

## Decisión y límites

BU L3 queda documentada como variable disponible y como challenger predictivo.
No se incorpora al modelo elegido ni sustituye los grupos actuales. El
resultado es retrospectivo y usa dos bloques temporales; no es una validación
prospectiva ni una estimación causal. El artefacto de resultados completo es
[`results.json`](../../../output/analysis/engineering/20261012/model-bu-l3-v7/results.json)
y el informe legible es
[`informe.md`](../../../output/analysis/engineering/20261012/model-bu-l3-v7/informe.md).

## Evidencia y código

- [Experimento ejecutable](../../../tools/engineering_bu_l3_experiment.py)
- [Plan y cierre de la ronda](../../plans/attrition-model-bu-l3-20261012.md)
- [Configuración congelada](../../../config/engineering_bu_l3_experiment_20261012_v7.json)
- [Perfil agregado por snapshot](../../../queries/profiles/engineering_bu_l3_profile_20261012.sql)
- [Población y join de modelado](../../../queries/profiles/engineering_bu_l3_person_month_20261012.sql)

La evidencia de entrada de las variables base se conserva dentro de
`output/analysis/engineering/20261012/model-bu-l3-v7/input-evidence/`; sus
resultados no sustituyen la auditoría específica de BU L3.
