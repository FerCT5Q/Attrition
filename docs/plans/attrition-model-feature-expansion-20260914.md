# Expansión del modelo de attrition a partir de variables y comentarios de Julia

## Objetivo

Extender el baseline propio de Critical Tech con variables que Julia señaló
como potencialmente accionables, sin convertir una hipótesis descriptiva en una
feature aprobada. Cada bloque se incorpora por separado y se compara contra el
mismo baseline temporal.

El producto sigue siendo un análisis de cohortes y apoyo a decisiones de
retención. No se publican scores, IDs ni listas de empleados.

## Alcance fijo de fase 1

La población para cada frame, baseline y bloque incremental es: empleado
`Regular` activo, no RF360, con match normalizado exacto a una sola
`extended_job_family` de `hrda.critical_tech`, un `seg` no vacío y
`seg <> 'Other Eng'`. La categoría residual `Other Eng` se excluye, incluso
como referencia del modelo. Esta regla ya respalda las distribuciones V7/V8;
el baseline del 2026-09-14 que aún contiene `Other Eng` se conserva sólo como
artefacto histórico y debe reejecutarse antes de iniciar la comparación de
bloques.

## Cómo se seleccionan los bloques

La selección combina tres fuentes, sin confundir sus roles. La documentación y
los assessments de variables establecen si una feature es definida, completa y
time-safe. Las distribuciones con attrition del playbook aportan asociaciones
exploratorias locales para priorizar una hipótesis, no causalidad ni evidencia
predictiva final. La literatura agrupa esas hipótesis en constructos y orienta
la especificación y el gobierno, pero no transfiere efectos o pesos a Qualcomm.

Un bloque llega al modelo sólo después de pasar la puerta de datos y se prueba
contra el mismo baseline temporal de fase 1. Así, el modelo es la validación
conjunta de viabilidad de la variable, señal local y fundamento metodológico;
no una carga simultánea de las 43 variables.

## Baseline de control

El baseline ejecutado el 2026-09-14 usa:

- `seg`;
- `level_grouped`;
- `company_tenure_band`;
- `manager_change_12m`;
- `calendar_month`.

Como contiene `Other Eng`, este baseline no debe utilizarse para decidir la
inclusión de bloques bajo el alcance final de fase 1. La próxima ejecución
debe comenzar con su equivalente reejecutado bajo el alcance fijo anterior.

Compara hazard discreto mensual `cloglog` contra logística directa a seis
meses con train/validación/holdout temporal. El artefacto está en
`output/analysis/critical-tech/20260914/baseline-v2-calendar-brier/`.

En el holdout ninguno se promueve todavía: el hazard tiene Brier ligeramente
menor, mientras la logística conserva una ventaja pequeña en PR-AUC y lift.
Faltan estabilidad temporal y fairness para cerrar el gate.

## Orden de expansión

### Bloque 1 — Carrera y etapa laboral

**Candidatos:** `position_time_in_level`, `time_in_current_job_profile`,
`current_grade_entry_path`, `time_since_last_promotion`, `company_tenure_band`.

**Hipótesis de Julia:** el tiempo en el perfil o nivel actual y la vía de
entrada al grade pueden distinguir espera de promoción, onboarding y movilidad.

**Regla de uso:** usar bandas conocidas al snapshot; no usar una fecha o evento
posterior. `position_time_in_level` y `time_in_current_job_profile` permanecen
exploratorios hasta resolver la discrepancia de transiciones documentada en
`docs/variables/position-time-in-level/README.md`. `current_grade_entry_path`
es una derivación contextual, no una etiqueta de contratación directa.

### Bloque 2 — Manager y equipo

**Candidatos:** `team_turnover_lagged`, `number_of_manager_changes`,
`manager_leaving_lookback`, `co_location_with_manager` y `span` agregado.

**Hipótesis de Julia:** la exposición a un equipo con turnover por encima de un
baseline y los cambios de manager pueden señalar inestabilidad local.

**Regla de uso:** construir la señal con una ventana cerrada antes del
snapshot, atribuir salidas al manager histórico correcto, excluir la persona
del denominador de su propio equipo y aplicar shrinkage/pooling. No usar
`high_risk_manager` como label ni como sustituto de team turnover. La
definición actual de `team_turnover` sigue pendiente de fórmula, deduplicación,
join temporal y leakage.

### Bloque 3 — Geografía y modalidad

**Candidatos:** `region`, `labor_market`, `office_site` y un mapping gobernado
de `work_arrangement`.

**Hipótesis de Julia:** region/market puede capturar competencia laboral y
office site puede separar zonas relevantes, incluyendo India.

**Regla de uso:** usar categorías versionadas y agrupadas con cohortes mínimas.
No inferir `hybrid` desde etiquetas crudas: el documento de work arrangement
reporta dominio histórico heterogéneo, cambios sin frontera efectiva y razones
potencialmente sensibles. Esta bloque entra sólo después de fijar el mapping
publicable.

### Bloque 4 — QVoice gobernado

**Candidatos:** `intent_to_stay`, `career_goals`, `engagement` y
`nonrespondent`; los comentarios de texto quedan fuera.

**Hipótesis de Julia:** señales binarias o un heartbeat relativo pueden aportar
información sobre intención, carrera y engagement.

**Regla de uso:** la wave debe estar disponible en o antes del snapshot; se
debe conservar la fecha de wave, medir cobertura y separar no respuesta de
respuesta negativa. No interpolar una encuesta anual como si fuera mensual.
El paper S01 del suplemento 2026-09-14 apoya probar el bloque, pero no prueba
su efecto en Qualcomm.

### Bloque 5 — Compensación y movilidad

**Candidatos:** `compa_ratio_band`, `transfer_12m`, `promotion_12m` y
`applied_to_a_job`.

**Hipótesis de Julia:** compa-ratio bajo, movilidad y aplicaciones pueden
separar riesgo de mercado o espera de carrera.

**Regla de uso:** compa-ratio sólo en bandas/percentiles y con fórmula o
lineage reconciliado; transfer y promotion deben distinguirse y no mezclarse.
Applications sólo entra si existe una fuente actual, una ventana cerrada y
una regla que distinga cero de missingness. La observación histórica de FY2024
no basta para una feature vigente.

## Fuera del MVP o reservadas

- `gender`: sólo auditoría de fairness; no targeting.
- texto libre de QVoice: fuera hasta aprobación de fuente, minimización y
  gobierno NLP.
- `commute_distance`: fase posterior; requiere población onsite y contexto
  geográfico comparable.
- `talent_index_current`: no entra hasta reconciliar definición, componentes y
  fecha de disponibilidad.
- `high_risk_manager`: no es label ni feature primaria.
- scraping, LinkedIn o identity matching externo: fuera del MVP.

## Gate para cada bloque

1. Definir claim, población, grain, fecha de conocimiento, ventana y regla de
   no leakage.
2. Confirmar metadata y ruta mediante el skill de Redshift; para una feature
   derivada, guardar SQL de fórmula, bordes, duplicados y join temporal.
3. Ejecutar el modelo incremental con exactamente el mismo split temporal que
   el baseline.
4. Comparar Brier, PR-AUC, lift operativo, calibración, estabilidad mensual y
   drift. Un challenger no se promueve por accuracy aislada.
5. Revisar fairness con atributos protegidos sólo para auditoría autorizada,
   sin publicarlos como cohortes de targeting.
6. Mantener el bloque sólo si mejora de forma consistente o aporta una señal
   interpretable y accionable sin degradar calibración, estabilidad ni gobierno.

## Decisión provisional

Ya es viable construir un modelo propio ajustado a nuestros datos: el baseline
lo demuestra. La siguiente versión no debe intentar meter las 43 variables a
la vez. Debe avanzar en el orden carrera → manager/equipo → geografía/modalidad
→ QVoice → compensación/movilidad, conservando el benchmark logístico y el
hazard como referencias en cada paso.
