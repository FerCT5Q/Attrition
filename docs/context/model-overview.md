# Visión del modelo de attrition

## Objetivo

El MVP debe identificar cohortes con mayor riesgo relativo de attrition voluntaria durante los seis meses posteriores a un snapshot mensual. El producto es un sistema de apoyo a decisiones de retención, no una lista de empleados que supuestamente van a renunciar.

Pregunta de negocio recomendada:

> ¿Qué grupos tienen mayor probabilidad de salir voluntariamente en los próximos seis meses, qué características comparten y dónde puede HR enfocar acciones de retención aprobadas?

## Población y target propuestos

- Población: empleados regulares activos en cada `fis_mo_end_dt`.
- Grano: una fila por empleado y snapshot mensual.
- Target: salida `Voluntary` dentro de los siguientes seis meses.
- Exclusiones iniciales: salidas involuntarias, retiro, fin de contrato o internship, `Voluntary Exception` y `term_type` nulo hasta que HR confirme su tratamiento.
- Regla temporal: toda feature debe existir a la fecha del snapshot; ninguna información posterior puede utilizarse para predecir ese snapshot.

La revisión agregada de agosto de 2026 encontró 6,907,668 worker-month rows, 141,680 empleados históricos y cobertura desde 2016-10-23 hasta 2026-08-23. El corte activo utilizado en el análisis general contenía 50,043 empleados regulares. Estas cifras describen la auditoría realizada; deben refrescarse antes de una ejecución productiva.

## Gobierno y privacidad

- Usar datos employee-level sólo para joins, entrenamiento y validación controlada.
- Publicar resultados por cohortes; no entregar risk scores ni drill-down por empleado.
- Ocultar cohortes con menos de 30 personas y preferir al menos 100 para reporting ejecutivo.
- No mostrar nombres, IDs, correos, atributos protegidos, exact pay, direcciones, leave, medical ni benefits.
- Usar atributos protegidos únicamente para auditorías de fairness autorizadas, no para targeting operativo.
- Tratar asociaciones y explicaciones del modelo como hipótesis, no como causalidad.

## Estrategia de modelado

1. Baseline histórico general.
2. Baseline por cohortes amplias.
3. Regresión logística como benchmark interpretable.
4. Modelo de árboles o boosting sólo si mejora lift, calibración y estabilidad.
5. Validación temporal con meses futuros; no usar un split aleatorio como evaluación principal.

Las métricas principales deben ser lift contra baseline, calibración, precision/recall en los grupos priorizados, estabilidad mensual y fairness. Accuracy por sí sola no es adecuada para un evento poco frecuente.

## Diseño del output

Cada insight debe contener:

```text
cohorte + señal + driver hipotético + acción permitida + owner + métrica + cadencia
```

El output mínimo debe incluir segmento, tamaño de población, riesgo o lift, drivers probables, calidad de datos, acción recomendada, responsable y fecha de revisión. Acciones posibles incluyen conversaciones de carrera, revisión de movilidad, manager enablement, onboarding, role clarity y revisión agregada de posición salarial.

## Alcance vigente: Engineering (desde 2026-10-01)

La población del modelo son los empleados `Employee`/`Regular` activos, no
RF360, con `eng_or_noneng = 'Engineering'` en cada foto mensual (~37k por
foto en 2026). Sustituye a Critical Tech porque la reasignación de job family
del 2026-09-01 cambió el `seg` del 10.9% de las personas, mientras que
`eng_or_noneng` se mantuvo en el 99.98%. El modelo elegido (hazard discreto
`cloglog`), las alternativas descartadas, los resultados rolling-origin y el
protocolo de selección de variables están en
`docs/plans/attrition-model-engineering-selection-20261001.md`.

## Alcance anterior: Critical Tech (superado el 2026-10-01)

La población aprobada para el MVP es la intersección de empleados regulares
activos con `hrda.critical_tech`. El catálogo define quién entra al análisis;
no es un target ni una variable que el modelo deba aprender. Los grupos de
alto attrition se descubrirán dentro de esa población con combinaciones de
family, segmento, nivel, tenure, manager, movilidad, engagement y work
arrangement.

Cada cohorte priorizada debe tener tamaño suficiente, lift frente al baseline,
estabilidad temporal y una palanca candidata. Los drivers se describen como
asociaciones; las acciones se medirán después mediante pilotos o diseños
causales.

La regla operativa de la fase 1 es más estricta: cada exposición debe ser de
un empleado `Regular` activo, no RF360, cuya `job_family` tenga un match
normalizado exacto con una sola `extended_job_family` del catálogo vigente y
con un único `seg` no vacío. Se excluye `seg = 'Other Eng'`. `Other Eng` es
una categoría residual del catálogo, no una family de Critical Tech que se
deba usar como cohorte, referencia o feature. Esta misma población se debe
mantener fija para el baseline, los bloques incrementales y sus comparaciones
temporales.

## Flujo de evidencia: variables, literatura y modelo

Los tres insumos se usan juntos, pero responden preguntas distintas:

1. Los assessments y la documentación por variable validan significado,
   fuente, cobertura, grain, historia, fecha de conocimiento y ausencia de
   leakage. Una variable sin esa puerta de datos no entra al frame, aunque
   parezca prometedora en una lámina o en un paper.
2. El playbook de distribuciones y attrition aporta evidencia exploratoria
   local para priorizar hipótesis: muestra distribución, tamaño de cohortes y
   asociaciones con attrition observado cuando la ventana es segura. No es una
   prueba causal, un coeficiente de correlación ni una validación predictiva.
3. La literatura organiza las variables en constructos, sugiere hipótesis y
   limita el método; no transfiere pesos, correlaciones ni desempeño de otra
   población a Qualcomm.
4. Sólo los candidatos que pasan las tres revisiones se prueban como un bloque
   incremental en el mismo modelo y split temporal. Se conservan únicamente si
   mejoran o complementan de manera estable la calibración, lift, PR-AUC,
   Brier, fairness y capacidad de acción.

La ejecución de ese flujo está en
`docs/plans/attrition-model-feature-expansion-20260914.md`; la conexión con
la evidencia bibliográfica está en
`docs/research/attrition-literature/methodological-synthesis.md`.

## Primer resultado ejecutado

El primer screen de Critical Tech ya está implementado como consulta agregada
y artefacto reproducible. Usa 68 snapshots completos con seguimiento de seis
meses, 2,038,274 exposiciones employee-snapshot y un baseline de 3.1588% de
attrition voluntario a seis meses. El screen publicó únicamente cohortes con
al menos 30 empleados y 30 eventos; 54 quedaron como prioritarias para
validación y 35 como hipótesis accionables. Las categorías `unknown` de
eventos se separaron como brecha de calidad y no como driver.

La evidencia y el registro de acciones están en
`output/analysis/critical-tech/20260907/`. El patrón dominante combina
segmento/job family con nivel y tenure. Estas asociaciones orientan el hazard
pooled y las conversaciones de carrera, movilidad, staffing y modalidad de
trabajo; no deben convertirse en targeting individual ni interpretarse como
causalidad.

El preflight del hazard mensual dejó 10 segmentos con volumen suficiente para
diagnóstico agregado y 2 segmentos que deben permanecer poolenados o
suprimidos. El detalle está en
`output/analysis/critical-tech/20260907/hazard-preflight-report.md`.

## Baseline propio ejecutado — 2026-09-14

Se ejecutó un baseline agregado con hazard discreto mensual `cloglog` y una
regresión logística directa a seis meses. El frame usa `seg`, `level_grouped`,
`company_tenure_band`, `manager_change_12m` y `calendar_month`; la validación
separó train, selección temporal y holdout futuro, sin persistir filas
employee-level ni scores individuales.

Este baseline se conserva como evidencia histórica del 2026-09-14, pero no es
el control reutilizable de la fase 1: sus resultados contienen `Other Eng`
como categoría de referencia. Antes de comparar cualquier bloque de variables
se debe reejecutar el baseline con la población de fase 1 definida arriba y
versionar el nuevo artefacto; no se deben reinterpretar ni sobrescribir los
resultados históricos.

En el holdout, el hazard obtuvo Brier 0.029346, PR-AUC 0.040745 y lift@10%
1.5134; la logística obtuvo Brier 0.029349, PR-AUC 0.041204 y lift@10% 1.5597.
La diferencia de Brier es mínima y la logística conserva ventaja en PR-AUC y
lift, por lo que ningún modelo se promueve todavía. El artefacto reproducible
está en
`output/analysis/critical-tech/20260914/baseline-v2-calendar-brier/`.

La siguiente comparación debe agregar bloques de variables uno por uno —
carrera/tenure, manager/equipo, QVoice gobernado y después challengers no
lineales— con la misma validación temporal, calibración, estabilidad y fairness.

## Decisiones pendientes de negocio

- Confirmar la definición final de voluntary attrition.
- Resolver `Voluntary Exception` y `term_type` nulo.
- Aprobar audiencia, cohort minimum y campos restringidos.
- Aprobar las acciones permitidas para cada tipo de driver.
- Definir cómo se medirán pilotos e intervenciones antes de escalarlos.

## Presentación vigente

La presentación fuente está en `references/presentations/source/`. El entregable consolidado está en `output/presentations/Attrition model story.pptx`.
