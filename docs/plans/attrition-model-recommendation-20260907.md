# Propuesta detallada para el modelo de attrition

Fecha: 2026-09-07  
Estado: propuesta metodológica para revisión de negocio, People Analytics y gobierno de datos.

## 1. Resumen ejecutivo

La recomendación es construir un modelo de **supervivencia discreta mensual**
con enlace complementary log-log (`cloglog`). El modelo estimará el hazard de
salida voluntaria entre el snapshot mensual actual y el siguiente snapshot.

Esta elección se ajusta mejor al dataset que un clasificador binario aislado
porque:

- cada empleado aparece en múltiples snapshots;
- las variables cambian a través del tiempo;
- existe censura al final del historial;
- el evento es poco frecuente;
- los periodos de observación no deben dividirse aleatoriamente entre
  entrenamiento y prueba.

El horizonte operativo recomendado es de **seis meses**. El hazard mensual será
el componente estadístico principal y se comparará contra una regresión
logística directa para el target de seis meses. Un modelo de gradient boosting
se evaluará después como challenger, no como primera opción.

Esta propuesta no afirma que un algoritmo ya haya ganado por AUC: todavía falta
construir el marco de modelado y ejecutar la comparación out-of-time. Define la
arquitectura que debe probarse primero.

## 2. Pregunta de negocio y salida permitida

Pregunta recomendada:

> ¿Qué cohortes de empleados regulares activos presentan mayor probabilidad de
> salida voluntaria en los próximos seis meses, qué señales se asocian con esa
> probabilidad y qué acciones de retención aprobadas pueden priorizarse?

La unidad de entrenamiento será un **empleado-snapshot mensual**. El modelo
puede utilizar información employee-level dentro de un entorno controlado para
entrenamiento, validación y scoring. El output compartido deberá ser agregado:

```text
cohorte + tamaño + riesgo/lift + señales asociadas + acción permitida
+ owner + métrica de seguimiento + fecha de revisión
```

No se deben compartir listas ordenadas de empleados ni scores individuales con
managers. Las cohortes compartidas deben tener al menos 30 personas y se
deberían preferir cohortes de 100 o más para reportes ejecutivos.

Las asociaciones del modelo son hipótesis de priorización. No demuestran que
una intervención concreta cause retención.

## 3. Definición del outcome

### 3.1 Target primario para el hazard

Para cada snapshot `t`:

```text
Y_next_snapshot = 1 si existe una terminación Voluntary con
term_date > snapshot_date y term_date <= next_snapshot_date
```

El intervalo debe usar la fecha real del siguiente snapshot, calculada con
`LEAD(snapshot_date)`, y no una ventana aproximada de 30 días. Esto evita que
los intervalos se solapen artificialmente cuando los cierres fiscales están
separados por aproximadamente 28 días.

La población es:

```text
worker_type = 'Employee'
employee_type = 'Regular'
active_status = 1 en el snapshot de predicción
```

### 3.2 Horizonte operativo de seis meses

Para un modelo directo de comparación:

```text
Y_6m = 1 si existe una terminación Voluntary con
snapshot_date < term_date <= DATEADD(month, 6, snapshot_date)
```

Sólo se incluyen snapshots con seis meses completos de seguimiento. Estas
ventanas pueden solaparse entre snapshots y por eso la evaluación debe ser
temporal y considerar dependencia entre observaciones.

### 3.3 Tratamiento de tipos de terminación

La auditoría ejecutada el 2026-09-07 encontró:

| Tipo | Eventos agregados |
|---|---:|
| `Voluntary` | 9,035 |
| `Involuntary` | 3,837 |
| `Voluntary Exception` | 2,295 |

`Voluntary` será el target inicial. `Involuntary` no se mezcla con el target.
`Voluntary Exception` debe mantenerse como categoría separada hasta que HR
apruebe si representa attrition voluntario, una excepción administrativa o una
clase que debe excluirse.

## 4. Evidencia sobre el horizonte

Las consultas de preflight encontraron los siguientes resultados agregados:

| Horizonte | Periodos completos | Snapshots elegibles | Positivos empleado-snapshot | Prevalencia |
|---|---:|---:|---:|---:|
| Siguiente snapshot | 73 | 2,973,166 | 14,936 | 0.5024% |
| 3 meses | 71 | 2,874,688 | 43,465 | 1.5120% |
| 6 meses | 68 | 2,730,460 | 82,129 | 3.0079% |
| 12 meses | 62 | 2,452,435 | 145,917 | 5.9499% |

El siguiente-snapshot es adecuado para aprender el hazard mensual, pero su
prevalencia es muy baja. Seis meses ofrece más eventos, mayor estabilidad y
tiempo razonable para una acción de retención. Doce meses puede servir como
análisis de sensibilidad, pero puede ser demasiado largo para acciones
operativas y acumular más cambios de contexto.

## 5. Modelo estadístico recomendado

### 5.1 Modelo principal: hazard discreto

Para cada empleado-snapshot se modela:

```text
h(i,t) = P(Y_next_snapshot = 1 | empleado activo en t, X(i,t))
```

La especificación recomendada es:

```text
log(-log(1 - h(i,t))) = α(t) + β'X(i,t)
```

Donde:

- `α(t)` representa el baseline hazard por periodo calendario o fiscal;
- `X(i,t)` son las features disponibles al cierre del snapshot;
- las variables numéricas pueden usar splines o bandas;
- las categorías poco frecuentes deben agruparse antes del ajuste;
- se recomienda regularización elastic net o L2 para reducir inestabilidad y
  colinealidad.

No se deben incluir efectos fijos de empleado en el primer modelo porque
impedirían utilizar correctamente variables constantes y no permitirían
generalizar a empleados nuevos. Para inferencia sobre coeficientes se pueden
usar errores robustos agrupados por empleado; para selección predictiva se debe
priorizar la evaluación out-of-time.

### 5.2 Riesgo acumulado a seis meses

Si el score se actualiza mensualmente, el riesgo acumulado puede calcularse a
partir de los hazards mensuales:

```text
R_6m = 1 - producto(1 - h(i,t+k)), k=1,...,6
```

Cada actualización utilizará únicamente la información disponible en ese nuevo
snapshot. Si el negocio necesita una predicción única en `t`, sin actualizaciones
mensuales, se debe usar el modelo directo `Y_6m` como modelo operativo
alternativo, no insertar features futuras artificialmente.

### 5.3 Modelos de comparación

Se deben entrenar tres referencias con la misma población, target y ventanas:

1. **Baseline ingenuo:** hazard o tasa histórica por periodo y cohortes.
2. **Baseline estadístico:** hazard `cloglog` regularizado.
3. **Challenger no lineal:** gradient boosting con calibración posterior.

El gradient boosting sólo debe convertirse en champion si mejora de manera
estable el lift, la calibración y la estabilidad, y sigue siendo explicable y
gobernable para el uso aprobado.

## 6. Selección de variables

### 6.1 Bloque base para el MVP

El primer modelo debería utilizar variables internas mensuales con buena
historia y cobertura:

**Historia laboral y carrera**

- `Company tenure`;
- `Position / time in level`;
- `Time since last promotion`;
- `Promoted vs. hired into level`;
- `Rehire`;
- `Years of experience prior to Qualcomm`.

**Rol y organización**

- `Job family` agrupada;
- `Level`;
- `Engineering vs. non-engineering`;
- `Region` y `Location`;
- `Remote / hybrid / in office status`;
- `Layers from CEO`, sólo desde la fecha en que la jerarquía sea utilizable y
  con tratamiento explícito para cambios estructurales.

**Movilidad y entorno del manager**

- `Transfer within past year`;
- `Manager change`;
- `Number of manager changes`;
- `Manager leaving`, usando sólo salidas ya conocidas al snapshot;
- `Team turnover` y `More than 1 employee leaves in a year`, siempre calculadas
  con eventos históricos y rezagados;
- `Co-location with manager`, incluyendo categoría de no match o dato ausente.

### 6.2 Bloques challenger

**QVoice.** Debe probarse como bloque incremental separado. Para cada snapshot
se usará la última wave disponible antes de la fecha de predicción, junto con:

- fecha de la wave;
- antigüedad de la respuesta;
- indicador de respuesta válida;
- número de componentes válidos;
- indicador de no respuesta o no elegibilidad, cuando esté disponible.

Los nulos no deben convertirse automáticamente en respuesta desfavorable. La
señal QVoice mostró asociaciones univariadas interesantes, pero todavía no
demuestra lift multivariado fuera de muestra.

**Compensación.** `Comp ratio` y `Within team compensation range` sólo después
de obtener lineage, reconciliar la fórmula y aprobar bandas o percentiles. No
se deben usar valores exactos de compensación.

**Aplicaciones internas.** Se pueden incorporar cuando el feed vuelva a tener
historia vigente, con deduplicación y una ventana cerrada en el snapshot.

**Datos externos.** Deben formar una segunda fase con la misma población y
target que el baseline para medir valor incremental.

### 6.3 Variables excluidas del MVP

- `Gender` como predictor; se reserva para fairness.
- `Talent index`, por historia insuficiente, riesgo de leakage y fórmula no
  reconciliada.
- `High risk manager`, para evitar etiquetas circulares y riesgos de gobernanza.
- Comentarios de QVoice y otros campos de texto libre.
- LinkedIn scraping, commute distance, `ET fields` y conceptos sin definición
  operativa aprobada.

## 7. Construcción del modeling frame

El dataset final debe tener una fila por empleado-snapshot y, como mínimo,
estas columnas internas:

```text
employee_id                  # sólo uso interno
snapshot_date
next_snapshot_date
population_flag
target_next_snapshot
target_6m
feature_source_as_of_date
feature_missingness_flags
feature values
```

El proceso debe:

1. deduplicar el snapshot al grain empleado-fecha;
2. construir el calendario real de snapshots;
3. aplicar la población aprobada antes de crear el target;
4. unir los eventos sólo después del snapshot;
5. calcular cada feature con información conocida a la fecha de predicción;
6. registrar la fecha de disponibilidad de cada fuente;
7. excluir snapshots sin seguimiento completo para el horizonte usado;
8. congelar los parámetros de imputación, bandas, mappings y escalas dentro de
   cada conjunto de entrenamiento.

La ausencia de un evento sólo puede interpretarse como “no ocurrió” cuando la
fuente demuestra que el evento era observable. Para encuestas, aplicaciones y
fuentes externas se deben separar no elegible, no invitado, no respondente,
missing y fuente aún no disponible.

## 8. Prevención de leakage

Los controles mínimos son:

- no usar `term_date`, `term_type`, `term_reason` ni cualquier derivación del
  outcome futuro como feature;
- calcular team turnover y manager signals sólo con eventos conocidos antes del
  snapshot;
- no usar campos cargados posteriormente aunque describan un evento pasado,
  salvo que exista una regla de disponibilidad histórica;
- no usar el valor actual de `Talent index` sin demostrar que era conocido antes
  del snapshot;
- no rellenar QVoice con información de una wave posterior;
- no seleccionar variables, bins o transformaciones mirando todo el historial;
- mantener un embargo de seis meses al evaluar modelos directos de `Y_6m`.

El warehouse reportó un snapshot `2026-09-27` procesado el `2026-09-06`, aunque
la revisión se ejecutó el `2026-09-07`. Hasta explicar si es una fecha fiscal
anticipada o un snapshot realmente futuro, debe excluirse de entrenamiento,
validación y scoring.

## 9. Validación del modelo

### 9.1 Diseño temporal

Se recomienda una validación rolling-origin:

- entrenamiento en periodos antiguos;
- validación en periodos posteriores;
- holdout final en el último bloque completamente observable;
- embargo de seis meses para modelos con target directo a seis meses;
- ningún split aleatorio como evaluación principal.

Un empleado puede aparecer en entrenamiento y prueba en fechas distintas: eso
representa el uso real de predecir el futuro de empleados existentes. Como
análisis separado, se puede medir desempeño en nuevas contrataciones.

### 9.2 Métricas

Las métricas principales serán:

- PR-AUC;
- lift y precision en los percentiles operativamente priorizados;
- Brier score;
- calibración global y por cohortes;
- estabilidad mensual y por año fiscal;
- drift de variables y del score;
- fairness por grupos autorizados.

Accuracy, recall o AUC-ROC por sí solos no son suficientes para un evento con
prevalencia cercana a 0.5% en el siguiente snapshot.

### 9.3 Regla para elegir champion

El champion debe:

1. superar al baseline en lift y PR-AUC en periodos futuros;
2. producir probabilidades razonablemente calibradas;
3. mantener desempeño sin degradación material entre cohortes grandes;
4. conservar estabilidad ante cambios de periodo y población;
5. usar únicamente variables autorizadas y time-safe;
6. permitir una explicación asociada con una acción aprobada;
7. poder mantenerse con la frecuencia de actualización disponible.

## 10. Fases de implementación

### Fase 0 — Contrato del problema

Resolver población, target, tratamiento de `Voluntary Exception`, horizonte,
audiencia, acciones permitidas y regla de cohortes mínimas.

### Fase 1 — Baseline interno

Construir el modeling frame mensual, entrenar el hazard `cloglog`, validar
temporalmente y documentar calibración, lift, estabilidad y fairness.

### Fase 2 — Challengers

Evaluar por separado QVoice, compensación gobernada, aplicaciones restauradas y
datos externos. Cada bloque debe compararse contra el mismo baseline y en los
mismos periodos futuros.

### Fase 3 — Piloto de decisiones

Publicar únicamente cohortes agregadas, asociar cada insight con una acción
permitida y medir si la acción modifica resultados. El modelo no debe
interpretarse como una prueba causal.

### Fase 4 — Operación y monitoreo

Recalcular según la cadencia aprobada y monitorizar cobertura, missingness,
drift, calibración, lift, fairness, cambios de población y disponibilidad de
las fuentes.

## 11. Alcance vigente: Critical Tech

El MVP queda restringido a empleados regulares activos cuyo `job_family`
coincide con `hrda.critical_tech`. La tabla es un filtro de población, no una
variable que el modelo deba predecir. Dentro de ese filtro se descubrirán
cohortes mediante combinaciones de family, segmento, nivel, tenure, manager,
movilidad, engagement y work arrangement.

La auditoría del 2026-09-07 encontró 62 keys en el catálogo, 61 coincidencias
exactas con `job_family`, cero contradicciones family-segment y una key sin
correspondencia. Hasta resolverla, Definition y Join permanecen conservadores.

El output será cohort-level: tamaño, riesgo o lift, señales asociadas, palanca
candidata, acción permitida, owner, métrica y fecha de revisión. Una asociación
predictiva no se presentará como causalidad.

## 12. Decisiones pendientes

1. Confirmar formalmente seis meses como horizonte operativo.
2. Resolver la key sin correspondencia y aprobar la regla de membership
   histórica de `critical_tech_archive`.
3. Resolver el tratamiento de `Voluntary Exception`.
4. Explicar el snapshot `2026-09-27` cargado antes de la fecha de revisión.
5. Aprobar las acciones de retención que pueden asociarse a cada cohorte.
6. Confirmar si QVoice puede utilizarse como input gobernado en scoring
   recurrente.

## 12. Evidencia y referencias

- [Visión del modelo](../context/model-overview.md)
- [Revisión de la historia y el plan](attrition-model-story-review-20260818.md)
- [Assessment v4 de las 43 variables](../../output/assessments/attrition-43-monthly-fiscal-20260816/manifest.json)
- [Perfil del outcome](../../queries/audits/attrition_outcome_label_profile_20260907.sql)
- [Preflight de horizonte](../../queries/audits/attrition_target_horizon_preflight_20260907.sql)
- [Prevalencia exacta del hazard mensual](../../queries/audits/attrition_next_snapshot_hazard_preflight_20260907.sql)
- [Freshness y fecha futura de snapshots](../../queries/audits/attrition_source_date_freshness_20260907.sql)
- [Assessment y análisis longitudinal de QVoice](../../data/QVoice/README.md)
- [Limitaciones de Talent index](../variables/talent-index/README.md)
- [Auditoría de compensación](../variables/compensation/README.md)
