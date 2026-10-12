# Plan final: presentación de la evolución de B a C + QVoice

| Campo | Valor |
|---|---|
| Fecha | 10 de octubre de 2026 |
| Estado | **Versión final para implementación** |
| Antecedentes | [Plan original](20261010-presentacion-evolucion-b-cq.md) · [Plan alterno](20261010-presentacion-evolucion-b-cq-alterno.md) · [Observaciones al alterno](20261010-observaciones-plan-alterno-b-cq.md) |
| Clasificación de la futura presentación | `presentation` |
| Criterios aplicados | `morgan-vis` y `build-html-presentation` |

Esta versión parte del plan alterno e incorpora las observaciones O01–O08 y sus ajustes de narrativa. Todas las correcciones de datos se volvieron a comprobar en los JSON archivados. La **parte I** registra qué cambió y por qué. La **parte II** es el plan completo: se puede implementar sin leer los documentos anteriores.

---

# Parte I. Cambios respecto al plan alterno

## I.1 Correcciones de contenido adoptadas

| Obs. | Problema del plan alterno | Comprobación | Resolución |
|---|---|---|---|
| O01 | «No individual scores are produced or shared» afirmaba demasiado | La autorización `config/attrition_model_in_memory_training_authorization_20261001.json` permite procesar filas persona-mes en memoria. Las banderas de S11 sólo acreditan que no se publican scores ni se persisten filas | Texto visible: «Only group-level results are reported; no individual scores are published». El guion distingue procesamiento, almacenamiento y publicación |
| O02 | El 20% de menor sobreestimación tenía protagonismo, pero la selección usa otra medida | Confirmado y agravado: el sesgo de `RSF_Q` es +1.11 en ago–dic 2025 y −0.75 en ene–feb 2026. Su promedio, 0.18, parece el mejor porque se compensan errores de signo contrario, aunque su error por grupo es 10.3% mayor | El **2.3%** (error de grupo-mes) es la medida visible de error en las diapositivas 1, 6 y 8. El 20% queda en el guion como dato complementario, con comparador y alcance |
| O03 | «The worst-estimated group did not improve» era una lectura falsa de un promedio | `worst_publishable_group_error_pp` por periodo: C 1.85 → CQ 2.15 en ago–dic; C 2.40 → CQ 2.33 en ene–feb. Además, no sigue siempre al mismo grupo | Texto visible: «Some group estimates still need improvement». Los valores por periodo pasan al respaldo. El compromiso sobre el grupo de mayor riesgo de B no se da por avanzado con esta evidencia |
| O04 | La referencia aleatoria podía atribuir a QVoice toda la distancia de 30% a 43.1% | Lógica correcta | Dos comparadores con funciones distintas: azar → modelo completo; C → aporte de QVoice (+0.7 puntos). Ambos visibles en la portada y en la diapositiva 6 |
| O05 | «Did not hold in later periods» para el ajuste a seis meses | S07: «Ago–dic 2025: sin ajuste por historia insuficiente; 0 orígenes». Sólo ene–feb 2026 evaluó una corrección efectiva | Texto visible: «The added adjustment did not improve the Jan–Feb 2026 test» |
| O06 | El símbolo «≈» (±0.5 puntos) ocultaba la pérdida reciente de D | Correcto | Se elimina «≈». Cifras con un decimal y una frase de lectura por fila |
| O07 | Riesgo de leer el IC95 como superioridad general | Correcto | La lectura principal es «mejora en un periodo y empate en el otro; mejora modesta». El intervalo queda en el guion con su alcance condicionado. «9 variantes evaluadas», no estudios |
| O08 | «Fairness no evaluado» era una afirmación absoluta | Correcto: sólo se revisaron los estudios del 8 al 10-oct | Fairness: «not found in the studies reviewed; to be confirmed or completed». El uso de QVoice se confirma con el equipo antes de proponerlo como pendiente |

## I.2 Ajustes de narrativa adoptados

- **Diapositiva 3 (5.1–5.2):** el diagrama de cómo B forma los grupos vuelve a ser el elemento principal, y la animación A explica su formación. El estado de los compromisos pasa a una columna lateral. Se retira el conteo «3 of 4». El título deja de asumir que la audiencia vio el deck anterior.
- **«Same group definitions»** sustituye a «Same groups» (5.3). Los nombres sencillos van siempre acompañados de B, C, CQ o D.
- **D se presenta como «Additional signals and model tests (D)»** (5.4). El título de la diapositiva 8 pasa a «Further tests did not justify replacing CQ».
- **Diapositiva 6 aligerada:** barras, línea aleatoria, 2.3% y resumen por periodo. La tabla de estimado frente a observado pasa al guion.
- **Franja de periodos:** cada diapositiva muestra sólo su conjunto de periodos. La explicación de los dos conjuntos aparece una vez, en la agenda.
- **Animaciones:** un único comportamiento (`Play` reproduce la secuencia completa). Se elimina el avance por clic.
- **Fuentes visibles:** cada visual cuantitativo vuelve a llevar una nota breve con estudio, fecha, población y ventana.
- **Evidencia:** las aserciones comprueban campo y fórmula contra la fuente, no dos copias del mismo valor. Las afirmaciones cualitativas también se registran.

## I.3 Aportes propios añadidos al integrar

- **Compromiso «adopt changes only if they improve today's model»:** se muestra en la diapositiva 3 con su matiz. CQ no cumplió la regla estricta de ganar en ambos periodos. La decisión del 10-oct ponderó magnitud, error y utilidad de los grupos (S01). Es más honesto decirlo en pantalla que esperar la pregunta.
- **El ejemplo de `RSF_Q` va en el guion** para explicar por qué un sesgo medio cercano a cero no implica buenas estimaciones por grupo.

## I.4 Matices aceptados sobre la revisión del plan original

- **H3:** comparar con C ya era una referencia explícita. La línea aleatoria **mejora** la lectura del valor absoluto; su ausencia no era un incumplimiento.
- **H4:** el plan original ya distinguía los periodos en subtítulos y notas. La franja aporta **consistencia y visibilidad**.

## I.5 Puntos que el equipo debe confirmar antes de construir

1. Si existe una evaluación de fairness fuera de los estudios del 8 al 10-oct. Si existe, se cita y cambia el estado en la diapositiva 3 y el paso 2 de la 9.
2. Si existe un acuerdo vigente sobre el uso de QVoice para un piloto. Si existe, se cita y cambia el paso 3 de la diapositiva 9.

Si no hay respuesta, se usa la redacción condicional de este plan.

---

# Parte II. Plan final

## 1. Encargo y decisiones cerradas

Presentar a líderes y RH la evolución del modelo de attrition voluntaria de Engineering:

- de dónde partimos (B) y qué queríamos mejorar;
- qué probamos (B + QVoice, C, CQ, mezclas de encuesta, D y bosque de supervivencia);
- qué elegimos: **C + QVoice (CQ), `engineering-c-qvoice-20261008-v1`, sin calibración adicional del riesgo a seis meses**, confirmado el 10-oct-2026 (S01);
- qué falta antes de usarlo.

El piloto no ha comenzado. El artefacto final tiene corte al 7-sep-2026 y sus coeficientes no tienen evaluación posterior a su ajuste.

| Aspecto | Decisión |
|---|---|
| Cantidad | 9 diapositivas; agenda en la 2 |
| Tiempo | 18 min de exposición (1080 s) + 2 de preguntas, sobre la diapositiva 9 |
| Audiencia | Líderes y RH; la presentación debe entenderse sin haber visto el deck anterior |
| Idioma visible | Inglés (`lang="en"`, igual que la base); guion, evidencia y validación en español |
| Formato | Un HTML autónomo, escenario 1440 × 810, funciona sin red |
| Identidad visual | Base vigente de Julia, tipografía Aptos, cuatro temas existentes |
| Comparación central | Grupos priorizados que cubren 30% de la población en cada foto mensual; es un escenario de comparación, no una capacidad aprobada |
| Animaciones | Tres, manuales: diapositiva 3 (formación de grupos), 6 (C frente a CQ) y 7 (cómo funciona CQ) |
| Salida | `output/presentations/<YYYYMMDD-HHmm>_evolucion-b-cq/presentacion-eng.html` |

Al terminar, la audiencia debe poder responder:

1. ¿Qué teníamos con B?
2. ¿Qué aportaron C y QVoice?
3. ¿Por qué CQ sigue elegido después de D?
4. ¿Qué falta comprobar antes de usarlo?

## 2. Base, instrucciones y alcance

- **Base:** [presentacion-eng.html](../references/presentations/model-selection/20261005-julia-8-groups/presentacion-eng.html), SHA-256 `1dfc30dd99a6205ce067ed7a3abf4828748f1f09b736045ae2d6e5465b89a9ae`, registrada en [model-selection-base.json](../config/presentations/model-selection-base.json). Se exporta con `tools/presentations/build_model_selection_deck_v9.py`, sin `--historical`, y se trabaja sobre una copia.
- **Lecturas obligatorias para quien implemente:**
  - [AGENTS.md](../AGENTS.md);
  - [build-html-presentation](../.agents/skills/build-html-presentation/SKILL.md), con su integración técnica y su tabla de precedencia;
  - [morgan-vis](../.agents/skills/morgan-vis/SKILL.md), sus extensiones de Attrition y su checklist;
  - `html-slide-generator`, en las referencias que se usen.
- **Idioma:** el inglés es preferencia explícita del usuario y coincide con la base. Sólo prevalece sobre la regla general de español para el texto proyectado.
- **Alcance:** presentar evidencia archivada hasta el 10-oct-2026. No incluye consultas nuevas a Redshift, entrenamiento, cambios de score ni cambios en la elección. Una consulta nueva sería un cambio de alcance y exige `attrition-redshift-db`.
- No se actualiza el registro de la base oficial.

## 3. Mapa de modelos y nombres visibles

| Interno | Nombre visible (etiqueta secundaria) | Qué es | Papel |
|---|---|---|---|
| B | Core HR model (B) | Modelo del 3-oct: ocho señales de RH y dos combinaciones; riesgo mensual acumulado a 6 meses; grupos por antigüedad × salidas del equipo × nivel | Punto de partida |
| B + QVoice | First survey tests (B + QVoice) | 9 variantes de encuesta, combinaciones más amplias y ajustes posteriores (S05–S07) | La encuesta ordenó mejor el riesgo; no superó todas las comprobaciones |
| C (`C_Bcuts`) | Expanded HR model (C) | Más información de RH, incluido el tiempo en el nivel, con las definiciones de grupo de B | Mejor balance; base para continuar |
| CQ | HR + employee feedback (CQ) | C más una corrección QVoice elegida con la historia disponible en cada origen | **Elegido** |
| `disjoint` (media28), `overlap`, `items_only` | Fixed survey questions | Mismas seis preguntas con promedio 28, promedio 33 o sin promedio | No mejoran el balance de CQ |
| D | Additional signals and model tests (D) | Representaciones QVoice, historia reciente del equipo, interacciones y controles de método | No justificó reemplazar a CQ |
| `RSF_Q` | Alternative method + feedback | Bosque de supervivencia con QVoice | Captura similar y más error por grupo |

**Contenido de CQ**

- Artefacto final (corte 7-sep-2026): Career Goals, promedio de 33 preguntas, Wellbeing Q8/Q10/Q11 y Confidence Q13/Q17.
- Q4 y Q12 entran dentro del promedio de 33, sin coeficiente propio.
- Las métricas históricas evalúan los modelos ajustados antes de cada periodo (`folds/`), no el artefacto final.

**Confusiones que hay que evitar**

- B y C son los modelos ejecutados en octubre, no las letras de documentos de diseño anteriores.
- La comparación B–C usa `B_cuts` frente a `C_Bcuts`, nunca los árboles ni `C_selected`.
- «Level / 8 groups» se refiere a categorías de nivel, no a grupos de riesgo.
- Las definiciones de grupo se conservan, pero las personas, los grupos elegibles y el orden de prioridad cambian entre fechas y modelos.
- D seleccionó sólo Q4, Q12 y Career sobre C. Las señales de historia nueva se probaron, pero no quedaron en su versión final.

## 4. Fuentes

| ID | Fuente | Uso |
|---|---|---|
| S01 | [Decisión vigente](../docs/context/model-selection-current.md) | Elección, argumentos, alcance, regla estricta histórica |
| S02 | Base de Julia y su registro | Estilo; compromisos de su diapositiva 9 |
| S03 | [Confirmación de B](../output/analysis/engineering/20261003/playbook-tenure-confirmation-v1/confirmation-results.json) y [informe](../output/analysis/engineering/20261003/playbook-tenure-confirmation-v1/confirmation-report.md) | Modelo de partida |
| S04 | [Agrupaciones de B](../output/analysis/engineering/20261003/playbook-group-selection-v1/group-selection-results.json) y [manifest](../output/analysis/engineering/20261003/playbook-group-selection-v1/group-selection-manifest.json) | Cortes de B; `groups_eligible` = 22 en la foto del 26-jul-2026; `min_group_people` = 300 |
| S05 | [B + QVoice anual](../output/analysis/engineering/20261008/qvoice-model-b-annual-lag-v2/comparison-results.json) y [informe](../output/analysis/engineering/20261008/qvoice-model-b-annual-lag-v2/informe-modelo-b-qvoice.md) | 9 variantes: todas mejoran el ordenamiento; ninguna pasa todas las comprobaciones; Q4, 7 de 8 |
| S06 | [B + QVoice calibrado](../output/analysis/engineering/20261008/qvoice-model-b-calibrated-v1/comparison-results.json) y [informe](../output/analysis/engineering/20261008/qvoice-model-b-calibrated-v1/informe-modelo-b-qvoice-calibrado.md) | Aporte de QVoice y límites de la calibración general |
| S07 | [Ajuste a 6 meses](../output/analysis/engineering/20261008/qvoice-horizon-calibration-v1/comparison-results.json) y [informe](../output/analysis/engineering/20261008/qvoice-horizon-calibration-v1/informe.md) | Ago–dic 2025 sin ajuste por historia insuficiente; corrección evaluada sólo en ene–feb 2026 |
| S08 | [Cortes B–C](../output/analysis/engineering/20261008/c-group-selection-v1/results.json) | Diapositiva 5 |
| S09 | [Decisión C con cortes de B](../output/analysis/engineering/20261008/model-c-v2/decision-eleccion-c-con-cortes-b.md) | Motivos y límites de C |
| S10 | [C + QVoice](../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/results.json) y [contexto](../docs/context/model-c-plus-qvoice.md) | Procedimiento CQ y combinación final |
| S11 | [Mezclas de encuesta](../output/analysis/engineering/20261009/c-qvoice-mean28-v1/results.json), [informe](../output/analysis/engineering/20261009/c-qvoice-mean28-v1/informe.md) y [decisión](../output/analysis/engineering/20261009/c-qvoice-mean28-v1/selection-decision.json) | CQ frente a mezclas fijas; `intervals`; banderas de publicación y persistencia |
| S12 | [Modelo D](../output/analysis/engineering/20261010/model-d-v1/results.json), [decisión](../output/analysis/engineering/20261010/model-d-v1/selection-decision.json) e [informe](../output/analysis/engineering/20261010/model-d-v1/informe.md) | C, CQ, D, `RSF_Q`, `monthly_logit`, `C_updated`; reglas de adopción de D |
| S13 | [Modelo C](../docs/context/model-c.md) | `time_at_level_band` entre los términos de C |
| S14 | [Autorización de procesamiento en memoria](../config/attrition_model_in_memory_training_authorization_20261001.json) | Distinción entre procesamiento interno, persistencia y publicación |

**Consultas guardadas**, citadas sin volver a ejecutarlas, todas en `queries/profiles/`:

| Uso | Consulta |
|---|---|
| B | `engineering_person_month_features_playbook_v2_20261003.sql` |
| C | `engineering_model_c_person_month_20261008.sql` |
| CQ | `engineering_model_c_qvoice_person_month_20261008.sql` |
| Mezclas de encuesta | `engineering_c_qvoice_mean28_person_month_20261009.sql` |
| S05 | `engineering_qvoice_person_month_20261008.sql` |
| S07 | `engineering_qvoice_horizon_calibration_20261008.sql` |
| D | `engineering_rsf_person_month_20261008.sql` y `engineering_model_d_history_person_month_20261010.sql` |

D registra además cuatro auditorías, `queries/audits/engineering_model_d_*_20261010.sql`, en su `frozen-config.json`.

Las narrativas antiguas que dicen «todavía no sustituye a C» se leen como decisiones históricas; S01 registra la elección vigente.

## 5. Contrato de cifras

### 5.1 Población, lectura y reglas de cálculo

- **Población:** Engineering; Employee, Regular, activos, sin RF360 según cada foto.
- **Resultado:** salida voluntaria en los 6 meses siguientes a cada foto mensual.
- **Priorización:** grupos ordenados por riesgo hasta cubrir exactamente 30%, con fracción uniforme del grupo del límite.
- **Promedios:** igual peso por periodo. Las ventanas y las personas se comparten entre periodos: no sumar exposiciones como personas ni como salidas únicas. En los dos periodos recientes hay 35474 y 35448 personas distintas, respectivamente; no se suman.
- **QVoice:** encuesta 2024 para 2025 y encuesta 2025 para 2026, respetando el episodio laboral. Esta política no acredita una fecha real de publicación de resultados.
- **Dos conjuntos de periodos que no forman una serie:**
  - B–C: 4 periodos, feb-2024 a ene-2026;
  - C–CQ–D: 2 periodos, ago–dic 2025 y ene–feb 2026.
- **Dos medidas de error que no se comparan entre sí:**
  - `group_mae_pp` en B–C;
  - `group_snapshot_mae_pp` en C–CQ–D.
  El registro de evidencia indica cuál usa cada cifra.
- **Cálculo y redondeo:** diferencias y reducciones relativas con los valores originales; se redondea sólo al mostrar. Nunca se recalcula un porcentaje desde cifras ya redondeadas.

### 5.2 Diapositiva 5: B frente a C (S08, `summary["30"]`)

| Medida visible | B (`B_cuts`) | C (`C_Bcuts`) | Campo o fórmula |
|---|---:|---:|---|
| Share of exits in priority groups | 45.2% | 45.4% | `metrics.capture_percent` (45.17 · 45.44) |
| Average gap per group, per 100 people | 0.9 | 0.8 | `metrics.group_mae_pp` (0.8777 · 0.7780) |
| Gap change | — | 11% smaller | `100 × (1 − C/B)` = 11.4 → se muestra «11%» |

- Diferencia de captura: +0.27 puntos, IC95 −0.32 a 0.85; C gana en 3 de 4 periodos. Se describe como pequeña e incierta y no se muestra «+0.3».
- En las notas, el escenario de 40%: 56.4% frente a 57.6%.

### 5.3 Diapositiva 6: C frente a CQ (S12; S11 coincide con tolerancia de 1e-8)

**Visibles**

| Medida | C | CQ | Campo o fórmula |
|---|---:|---:|---|
| Share of exits in priority groups | 42.4% | 43.1% | `summary.<m>.scenarios["30"].capture_percent` |
| Random 30% reference | ~30% | ~30% | Definición de la selección al azar; lift de CQ = 1.44 (`lift`) |
| Gain from adding feedback | — | +0.7 points | 43.106 − 42.442 = 0.66 |
| Average gap per group | — | 2.3% smaller | `group_snapshot_mae_pp`: 0.99401 → 0.97093 |

Por periodo, en `periods[id].evaluation.<m>.scenarios["30"].metrics.capture_percent`:

| Periodo | C | CQ | Lectura |
|---|---:|---:|---|
| Aug–Dec 2025 | 42.1% | 43.5% | Better |
| Jan–Feb 2026 | 42.8% | 42.8% | Tied |

**Respaldo para el guion, no proyectado**

| Medida | C | CQ | Campo |
|---|---:|---:|---|
| Estimated per 100 people in priority groups | 5.2 | 5.1 | `predicted_percent` |
| Actual per 100 people in priority groups | 4.5 | 4.6 | `observed_percent` |
| Average overestimate | 0.68 | 0.55 | `bias_pp` (−20% relativo, CQ frente a C, grupos priorizados al 30%) |
| Largest publishable group gap, Aug–Dec 2025 | 1.85 | 2.15 | `periods[aug_dec_2025]…worst_publishable_group_error_pp` |
| Largest publishable group gap, Jan–Feb 2026 | 2.40 | 2.33 | `periods[jan_feb_2026]…worst_publishable_group_error_pp` |

- El observado cambia entre C y CQ porque cada modelo prioriza grupos distintos.
- El indicador de mayor error no sigue siempre al mismo grupo.
- El sesgo medio puede compensar errores de signo contrario. Ejemplo: `RSF_Q` tiene +1.11 y −0.75 en los dos periodos, promedio 0.18, con 10.3% más error por grupo que CQ. Por eso la selección usa el error de grupo-mes, no el sesgo.
- IC95 de la diferencia de captura CQ − C: 0.17 a 1.21 puntos (S11 `intervals`, `capture30`). Está condicionado a los modelos ajustados, las prioridades y los periodos observados, y no incorpora toda la incertidumbre de selección y entrenamiento.

### 5.4 Diapositiva 8: pruebas adicionales

Diferencia relativa de error dentro de cada estudio: `100 × (error_alt / error_CQ − 1)`, sobre `group_snapshot_mae_pp`.

| Fila visible | Share of exits, 30% | Gap per group vs CQ | Jan–Feb 2026 share | Reading | Fuente |
|---|---:|---:|---:|---|---|
| HR + employee feedback (CQ) · **Selected** | 43.1% | — | 42.8% | Reference | S12 `CQ` |
| Fixed survey questions + revised average | 43.1% | 4.1% larger | 42.8% | Same share; estimates further from actual | S11 `disjoint` |
| Additional signals and model tests (D) | 42.8% | 0.8% smaller | 42.1% | Slightly closer estimates; fewer exits found in the latest period | S12 `D` |
| Alternative method + feedback | 43.1% | 10.3% larger | 42.7% | Similar share; estimates further from actual | S12 `RSF_Q` |

Valores originales:

- disjoint: 1.01046 frente a 0.97093, último periodo 42.76;
- D: 0.96269, 42.82, último periodo 42.11;
- `RSF_Q`: 1.07072, 43.09, último periodo 42.68.

En S12 (`selection-decision.json`), D tiene:

- `promote_D: false`;
- `relative_group_snapshot_error_reduction` = 0.0085, frente al 10% de su ruta de precisión;
- `period_floor: false`, es decir, no cumple el límite de pérdida por periodo.

Diferencia media de captura de D: −0.3 puntos, IC95 −1 a 0.4.

Respaldo para preguntas:

- `overlap` (promedio 33) e `items_only` (sin promedio) tienen más error que `disjoint`.
- `monthly_logit` da prácticamente las mismas métricas que D.
- `C_updated` captura 42.7% con más error.

### 5.5 Diapositiva 4: anclas de B + QVoice

- **S05:** «9 survey variants evaluated: all 9 ranked risk better than B; none passed every agreed check». Q4 fue la más sencilla y prometedora: 7 de 8 comprobaciones. Son 9 variantes sobre los mismos dos periodos, no 9 estudios.
- **S06:** las combinaciones más amplias aportaron información más allá de si la persona respondió la encuesta; la calibración general seguía con límites.
- **S07:** la corrección a seis meses sólo pudo evaluarse en ene–feb 2026 (ago–dic 2025 no tenía historia suficiente) y no mejoró el balance.

### 5.6 Frase de significado

> «In historical checks, 43.1% of observed exits came from priority groups covering 30% of Engineering. A random 30% would hold about 30%; adding employee feedback to the expanded HR model added about 0.7 points.»

No es la probabilidad de que alguien se vaya, ni salidas evitadas, ni «precisión».

## 6. Guion y tiempos

| # | Título visible | Tiempo | Acumulado |
|---|---|---|---|
| 1 | In historical checks, priority groups covering 30% of Engineering contained 43.1% of observed exits | 1:00 | 1:00 |
| 2 | From our starting model to today's choice | 0:45 | 1:45 |
| 3 | We started with understandable groups — what we completed and what remains | 2:00 | 3:45 |
| 4 | Survey answers helped rank risk, but the first tests fell short | 2:00 | 5:45 |
| 5 | The expanded HR model kept the group definitions and cut the gap by 11% | 2:15 | 8:00 |
| 6 | Adding employee feedback found modestly more exits in priority groups | 3:00 | 11:00 |
| 7 | Feedback refines priorities within familiar, group-level views | 2:00 | 13:00 |
| 8 | Further tests did not justify replacing CQ | 3:00 | 16:00 |
| 9 | Next: confirm on new data, review groups, then a limited pilot | 2:00 | 18:00 |

## 7. Especificación por diapositiva

### 7.1 Diapositiva 1. Decisión

- **Título:** «In historical checks, priority groups covering 30% of Engineering contained 43.1% of observed exits».
- **Subtítulo:** «Engineering · Voluntary exits over the next 6 months · October 2026».
- **Tres KPIs**, con el estilo de la portada de Julia:

| KPI | Texto principal | Texto de apoyo |
|---|---|---|
| 1 | «43.1% of exits» | «in priority groups covering 30% of people · ~30% if chosen at random» |
| 2 | «+0.7 points» | «from adding employee feedback to the expanded HR model · 2.3% smaller average gap per group» |
| 3 | «Same group definitions» | «Years at Qualcomm · team exits · level» |

- **Línea de decisión:** «Selected: HR + employee feedback (CQ), for the next validation stage. A pilot has not started».
- **Fuente:** «Engineering · active regular employees, excl. RF360 · Aug 2025–Feb 2026 snapshots · 6-month follow-up · 9–10 Oct 2026 analyses».
- **Notas del presentador:**
  - la ganancia sobre el modelo anterior es modesta;
  - la mayor parte del 43.1% proviene del modelo completo, no sólo de la encuesta;
  - se probaron alternativas antes de mantener CQ.
- **Transición:** «Empecemos por el modelo de partida y los puntos que queríamos mejorar».

### 7.2 Diapositiva 2. Agenda

- **Título:** «From our starting model to today's choice».

| Diapositivas | Etiqueta | Descripción |
|---|---|---|
| 3–4 | Our starting point | Core HR model (B) and the first survey tests |
| 5–7 | What improved | Expanded HR model (C) and employee feedback (CQ) |
| 8 | Further checks | Survey mixes, additional signals (D) and an alternative method |
| 9 | Decision and next steps | Confirm, review, pilot |

- **Franja inferior:** `Core HR (B) → Expanded HR (C) → HR + feedback (CQ) ✓`. Es un diagrama del trabajo, no una serie de cifras. Las pruebas relacionadas aparecen como ramas grises.
- **Nota única sobre periodos:** «Results come from two sets of historical checks — 4 periods (Feb 2024–Jan 2026) and 2 recent periods (Aug 2025–Feb 2026). Numbers compare only within each set».

### 7.3 Diapositiva 3. Punto de partida y avances (animación A)

- **Título:** «We started with understandable groups — what we completed and what remains».
- **Disposición:** dos tercios a la izquierda y una columna lateral de un tercio.

**Zona principal: cómo B forma los grupos**

- Diagrama de división sucesiva, en SVG: All Engineering → Years at Qualcomm → Team exits → Level.
- Cada paso etiquetado con su criterio. En el paso final, un rótulo: «22 groups eligible on 26 Jul 2026 · each with 300+ people» (S04: `groups_eligible`, `min_group_people`).
- Sin riesgos inventados ni tamaños simulados. Si se dibujan proporciones, salen de los agregados de S04 y se registran en la evidencia.
- **Texto de apoyo:**
  - «B used information HR already tracks».
  - «Groups make results easier to discuss and act on».

**Columna lateral: «Since our last update»** (estática, sin animación)

| Commitment | Status |
|---|---|
| Test the remaining model type (random survival forest) | ✓ Done — slide 8 |
| Add more signals: QVoice and time at level | ✓ Done — slides 5–7 |
| Adopt changes only if they improve the model | ◐ Applied with judgment — CQ better in one period, tied in the other (slide 6) |
| Reduce overestimates in the highest-risk group | ◐ Further validation needed — some group estimates still need work |
| Check fairness across groups | ○ Open — not found in the studies reviewed |

- Los símbolos ✓, ◐ y ○ siempre van acompañados de texto.
- **Nota:** «Groups summarize many people; no individual predictions are shown».
- **Animación A:** los cuatro estados de la división de grupos (§8.3).
- **Evidencia:** S02 (compromisos), S04 (grupos), S12 (`RSF_Q`), S13 (`time_at_level_band`), S10 (QVoice), S01 (regla estricta y decisión). Para fairness, la búsqueda del plan alterno: H1 y O08.
- **Notas del presentador:**
  - Para quien no vio el deck anterior: «son los puntos que nos propusimos mejorar».
  - Sobre la regla de adopción: la regla estricta pedía ganar en ambos periodos; CQ ganó uno y empató el otro, y la elección ponderó magnitud, error y utilidad de los grupos.
  - Sobre la sobreestimación: el promedio de los grupos priorizados mejoró, pero esa comparación no sigue al grupo concreto de mayor riesgo mostrado antes.
- **Transición:** «La primera pregunta fue qué podíamos aprender de lo que los empleados dijeron en QVoice».

### 7.4 Diapositiva 4. Primeras pruebas con encuesta

- **Título:** «Survey answers helped rank risk, but the first tests fell short».
- **Disposición:** tres pasos horizontales, cada uno con lo que mejoró y lo que faltó:

| Paso | Lo que mejoró | Lo que faltó | Fuente |
|---|---|---|---|
| «9 survey variants evaluated» | ✓ «All 9 ranked risk better than B» | ✗ «None passed every agreed check» | S05 |
| «Broader combinations» | ✓ «Useful beyond whether people answered» | ◐ «Overall estimates still off» | S06 |
| «Added adjustment to estimated risk» | ✓ «Better fit to earlier data» | ✗ «Did not improve the Jan–Feb 2026 test» | S07 |

- **Pie:** «The feedback was useful — we kept it and changed the base model».
- **Fuente:** «Engineering · 2 historical periods · 8 Oct 2026 analyses».
- **Notas del presentador:**
  - Q4 fue la variante más sencilla y prometedora (7 de 8).
  - Lo que impedía adoptar las variantes era el balance de la estimación global.
  - El ajuste a seis meses no pudo probarse en ago–dic 2025 por falta de historia.
  - No invalida QVoice ni la calibración en general.
  - No se nombran medidas estadísticas.
- **Transición:** «También ampliamos la información de RH y comprobamos si C mejoraba el balance con las mismas definiciones de grupo».

### 7.5 Diapositiva 5. B frente a C

- **Título:** «The expanded HR model kept the group definitions and cut the gap by 11%».
- **Subtítulo:** «Core HR (B) vs Expanded HR (C) · same group definitions · priority groups covering 30% of Engineering».
- **Franja de periodos:** «4 historical periods · Feb 2024–Jan 2026».
- **Disposición:**
  - tabla de §5.2;
  - debajo de «gap», la definición «gap = difference between estimated and actual exits per 100 people, by group»;
  - tres etiquetas: «More HR information, incl. time at level», «Same group definitions», «Similar share of exits».
- **Nota visible:** «The change in share of exits was small and uncertain; the gain is mainly in closer estimates. 11% is a relative reduction of the group gap».
- **Fuente:** «Engineering · active regular employees, excl. RF360 · 4 historical periods · 6-month exits · 8 Oct 2026 analysis».
- **Notas del presentador:**
  - la preferencia por C fue práctica (S09);
  - C no ganó todas las medidas en todas las fechas;
  - si preguntan, el IC de captura y el escenario de 40%.
- **Transición:** «Con esa base, volvimos a comprobar qué añadía QVoice».

### 7.6 Diapositiva 6. C frente a CQ (animación B)

- **Título:** «Adding employee feedback found modestly more exits in priority groups».
- **Subtítulo:** «Share of observed exits in priority groups covering 30% of Engineering · next 6 months».
- **Franja de periodos:** «2 historical periods · Aug 2025–Feb 2026».
- **Gráfico principal:** barras horizontales en una escala de 0 a 50%, con etiquetas directas.
  - Línea vertical punteada en 30%: «Random 30%».
  - «Expanded HR (C) 42.4%» en gris.
  - «HR + feedback (CQ) 43.1%» en el color de énfasis, con la anotación «+0.7 points».
- **Tarjeta lateral:** «2.3% smaller average gap per group» — «difference between estimated and actual exits; relative reduction».
- **Resumen por periodo**, de una línea: «Aug–Dec 2025: 42.1% → 43.5% (better) · Jan–Feb 2026: 42.8% → 42.8% (tied)».
- **Nota visible:** «Historical, average results. Some group estimates still need improvement».
- **Fuente:** «Engineering · active regular employees, excl. RF360 · Aug–Dec 2025 and Jan–Feb 2026 snapshots · 6-month follow-up · 9–10 Oct 2026 analyses».
- **Animación B:**
  1. Línea aleatoria.
  2. Barra de C.
  3. Barra de CQ con «+0.7 points».
  4. Resaltado de la tarjeta 2.3% y del resumen por periodo.
  Los valores finales siempre están escritos; no hay contadores.
- **Notas del presentador:**
  - Frase de §5.6.
  - La línea aleatoria muestra el valor del modelo completo; la diferencia con C muestra el aporte de la encuesta.
  - Mejora en un periodo y empate en el otro: es una mejora modesta.
  - Del respaldo de §5.3: estimado frente a observado, −20% de sobreestimación media (CQ frente a C, grupos priorizados), indicador de mayor error por periodo e IC con su alcance.
- **Transición:** «La encuesta refina las prioridades y los grupos siguen siendo fáciles de describir».

### 7.7 Diapositiva 7. Cómo funciona CQ (animación C)

- **Título:** «Feedback refines priorities within familiar, group-level views».
- **Diagrama conceptual de tres estaciones**, sin datos simulados, personas ni movimientos de ranking:
  1. «HR information» — «Work history, team context, time at level».
  2. «Employee feedback» — «Career goals · overall feedback · wellbeing · confidence».
  3. «Priority groups» — «Years at Qualcomm · team exits · level».
- La estación de encuesta se conecta a la estimación y después al orden de los grupos.
- **Notas visibles:**
  - «Only group-level results are reported; no individual scores are published».
  - «Final September version shown. Historical checks used the model available at each date; the final version still needs a check on later data».
- **Animación C:** RH → retroalimentación → grupos (§8.3).
- **Evidencia:** S01, S10, S11 (`individual_scores_published: false`, `employee_level_rows_persisted: false`) y S14.
- **Notas del presentador:**
  - Durante el análisis autorizado se procesan respuestas individuales en memoria; no se guardan filas de empleados; los resultados compartidos son agregados por grupo y no se publican puntuaciones individuales.
  - Cada encuesta se usa al año siguiente.
  - Las preguntas elegidas variaron entre periodos.
- **Transición:** «Antes de cerrar la elección, comprobamos otras combinaciones y modelos».

### 7.8 Diapositiva 8. Pruebas adicionales

- **Título:** «Further tests did not justify replacing CQ».
- **Subtítulo:** «Share of exits and gap per group · priority groups covering 30% of Engineering».
- **Franja de periodos:** «2 historical periods · Aug 2025–Feb 2026».
- **Disposición:** la tabla de §5.4 con sus cinco columnas visibles. La fila CQ lleva el color de énfasis y la etiqueta «Selected»; las demás van en tonos de contexto. Las cifras van con un decimal y sin símbolos de equivalencia. La columna «Reading» hace que la tabla se entienda sin color.
- **Anotación:** «D: slightly closer estimates (0.8% smaller gap), but fewer exits found in Jan–Feb 2026 (42.1% vs 42.8%) — below its own adoption rules».
- **Nota:** «New team-history signals were tested in D but not kept in its final version».
- **Fuente:** «Engineering · active regular employees, excl. RF360 · Aug–Dec 2025 and Jan–Feb 2026 snapshots · 6-month follow-up · 9–10 Oct 2026 analyses».
- **Notas del presentador:**
  - Las filas resumen grupos de pruebas, no un inventario exhaustivo.
  - El respaldo de §5.4.
  - Las pruebas negativas también son un resultado del trabajo.
- **Transición:** «Con estas comprobaciones, la decisión se mantiene; el siguiente paso es contrastarla con datos nuevos».

### 7.9 Diapositiva 9. Siguientes pasos

- **Título:** «Next: confirm on new data, review groups, then a limited pilot».
- **Frase principal:** «HR + employee feedback (CQ) remains our selected model».
- **Cuatro pasos propuestos:**

| # | Paso | Detalle |
|---|---|---|
| 1 | «Check a new period» | «Evaluate the final September version after its training date, including group-level gaps» |
| 2 | «Review differences across groups» | «Confirm or complete the fairness review» |
| 3 | «Confirm how survey data may be used» | «Agree the scope with HR before any pilot» |
| 4 | «Prepare a limited pilot» | «Scope, owners, capacity (e.g. the 30%) and measures, before starting» |

- **Nota:** «Proposed steps — not yet scheduled or approved. Historical results support the selection; the effect of retention actions has not been measured».
- Si el equipo confirma un acuerdo vigente sobre QVoice o una evaluación de fairness (I.5), se cita y se ajusta el paso correspondiente.
- **Notas del presentador:** repetir la elección en una frase y recordar que la ganancia es modesta. Cerrar hacia el minuto 18; las preguntas se responden sobre esta diapositiva.

## 8. Especificación visual e interacción

### 8.1 Lectura y composición

- Un mensaje por diapositiva. En la 6, el gráfico, la tarjeta 2.3% y el resumen por periodo forman una sola lectura; el resto va al guion.
- Títulos activos de una o dos líneas, de 30 a 36 px; la portada, unos 44 px.
- Cuerpo de 18 a 22 px; celdas y etiquetas de al menos 16 px; fuentes de 12 a 14 px.
- Un color de énfasis para CQ y gris para el contexto, consistentes en todo el deck. Los símbolos ✓, ◐, ○ y ✗ acompañan siempre al texto.
- Barras con origen en cero y escala de 0 a 50%; línea de referencia aleatoria rotulada.
- Cifras alineadas a la derecha y con unidades explícitas. Enteros sin decimales y el resto con un decimal como máximo, también en contenido dinámico. Un positivo que redondea a cero se muestra como `<0.1%`.
- Franja de periodos en las diapositivas 5, 6 y 8, en la misma posición y estilo, con sólo el conjunto que corresponde.
- Fuente breve en todo visual cuantitativo (diapositivas 1, 3, 4, 5, 6 y 8), con identificador S## para enlazarla con el guion y `evidence.json`.

### 8.2 Recursos

- Todo con SVG o HTML/CSS embebido, con texto alternativo que exprese el mensaje.
- Sin red, sin archivos vecinos y sin bibliotecas externas nuevas.
- No se reutiliza `#wt-plane` ni su JavaScript; el diagrama de la diapositiva 3 es nuevo y más sencillo.

### 8.3 Animaciones: comportamiento único

| Animación | Diapositiva | Estados |
|---|---|---|
| A | 3 | All Engineering → Years at Qualcomm → Team exits → Level |
| B | 6 | Línea aleatoria → C → CQ (+0.7) → tarjeta y periodos |
| C | 7 | HR information → Employee feedback → Priority groups |

1. `Play` reproduce la secuencia completa: transiciones de 400 a 700 ms y 6 s como máximo en total.
2. `Replay` reinicia la secuencia; `Show all` muestra de inmediato el estado final.
3. No hay reproducción automática ni avance por clic. El cambio de diapositiva cancela los temporizadores, y al volver la diapositiva aparece en su estado inicial.
4. Con `prefers-reduced-motion` se muestra el estado final y se conserva toda la información.
5. Los botones funcionan con teclado; las flechas siguen navegando entre diapositivas.
6. Los controles y los valores ocupan posiciones estables.
7. Los controladores se añaden después de los bloques JavaScript base. `showSlide` y `applyTheme` están encapsulados: los cambios se detectan por el DOM y los controles existentes.

## 9. Vocabulario visible

| Respaldo | En pantalla |
|---|---|
| Features | HR information / employee feedback |
| Captura al 30% | Share of exits in priority groups |
| `group_mae_pp` / `group_snapshot_mae_pp` | Average gap per group |
| Lift / baseline | vs. a random 30% |
| Calibración | Added adjustment to estimated risk |
| Fold | Model available at each date |
| B / C / CQ / D / `RSF_Q` | Nombres de §3 con su letra |

Quedan fuera de la pantalla: `hazard`, `cloglog`, `L1`, `L2`, `PCA`, `Brier`, `PR-AUC`, `log-loss`, `bootstrap`, `fold` y `bias`.

## 10. Guion del presentador (`guion-presentador.md`, en español)

Para cada diapositiva:

1. objetivo y tiempo acumulado;
2. explicación hablada;
3. momento de pulsar `Play`;
4. cifra que debe recordarse;
5. limitación;
6. transición.

**Preguntas preparadas**

- **¿Por qué no B?** C mantiene las definiciones de grupo y reduce 11% el gap por grupo; el cambio en la proporción de salidas fue pequeño e incierto.
- **¿Por qué CQ si no ganó los dos periodos?** Ganó uno y empató el otro, con +0.7 puntos de media y 2.3% menos de gap. La regla estricta original se conserva como antecedente; la elección ponderó magnitud, error y utilidad (S01).
- **¿Cuánto aporta la encuesta y cuánto el modelo?** Al azar, alrededor de 30%; C, 42.4%; CQ, 43.1%. La encuesta aporta los últimos 0.7 puntos.
- **¿43.1% significa que esas personas se irán?** No. Es la proporción de salidas observadas en grupos que suman 30% de la plantilla.
- **¿Se resolvió la sobreestimación?** En los grupos priorizados, la sobreestimación media de CQ es unos 20% menor que la de C. El grupo con mayor error mejora en un periodo y empeora en el otro, y algunos grupos siguen necesitando trabajo. Esta comparación no sigue al grupo concreto de mayor riesgo mostrado antes.
- **¿Por qué no usar la sobreestimación media para elegir?** Errores de signo contrario se compensan. El método alternativo tiene la media más cercana a cero, pero 10.3% más error por grupo.
- **¿Y fairness?** No se encontró una evaluación archivada en los estudios revisados; es el paso 2.
- **¿Se usan las respuestas individuales de QVoice?** En el análisis autorizado se procesan en memoria; no se guardan filas de empleados; sólo se reportan resultados por grupo y no se publican puntuaciones individuales.
- **¿D fue peor en todo?** No. Acercó un poco las estimaciones (0.8%), pero no alcanzó su propio umbral de 10% y perdió captura en el periodo reciente.
- **¿QVoice causa las salidas?** No. Son asociaciones predictivas.
- **¿Está probado el modelo final de septiembre?** No. Sus coeficientes requieren datos posteriores a su ajuste.
- **¿Por qué 30%?** Es el escenario de comparación; la capacidad real se define para el piloto.
- **¿Por qué C tiene 45.4% en la diapositiva 5 y 42.4% en la 6?** Son conjuntos de periodos distintos; no es un deterioro.

## 11. Construcción y entregables

| Archivo | Función |
|---|---|
| `tools/presentations/build_model_evolution_b_cq.py` | Lee los JSON por ruta y campo, aplica las fórmulas de §5, renderiza y escribe `evidence.json`. Falla si un campo falta o si una cifra central no puede calcularse |
| `tests/test_model_evolution_b_cq_deck.py` | Prueba el formateo (≤1 decimal y `<0.1%`), las fórmulas de §5 contra los campos fuente, la igualdad de CQ entre S11 y S12, y la estructura (9 diapositivas, 9 pills) |
| `config/presentations/model-evolution-b-cq-20261010.json` | Fuentes, campos, fórmulas, nombres visibles, tiempos, idioma y clasificación |
| `<salida>/presentacion-eng.html` | Deck autónomo |
| `<salida>/guion-presentador.md` | Guion y preguntas preparadas |
| `<salida>/evidence.json` | Ver detalle debajo |
| `<salida>/validation.json` | Salida íntegra del verificador, revisión de navegador, privacidad y excepciones |
| `output/preview/<misma ejecución>/` | Capturas y hoja de contacto |

**Contenido de `evidence.json`**

- Por cada cifra: diapositiva, identificador, fuente con SHA-256, fecha, población, periodo, consulta o manifest, campo JSON, medida de error usada, valor original, fórmula y texto mostrado.
- Por cada afirmación cualitativa: fuente, sección y alcance. Entre ellas:
  - se conservan las definiciones de grupo;
  - fairness no se encontró en los estudios revisados;
  - las señales de D no quedaron seleccionadas;
  - la versión final requiere evaluación posterior;
  - la distinción entre procesamiento, persistencia y publicación.
- Datos generales: identidad de la base, versión CQ, los 9 tiempos, `language: en` y `deliverable_classification: presentation`.

El script acepta `--out`. Por defecto crea una carpeta con fecha y hora y se detiene si la ruta ya existe. Las validaciones leen el valor de la fuente y recalculan la fórmula; no comparan dos copias de un valor escrito a mano. La interfaz construye la presentación; no expone entrenamiento ni predicción.

**Orden de implementación**

1. Leer las instrucciones y las fuentes; verificar el hash de la base. Confirmar con el equipo los puntos de I.5.
2. Inventariar los agregados de §5 y comprobar que CQ coincide entre S11 y S12.
3. Crear el config.
4. Exportar una copia de la base.
5. Reemplazar las 9 diapositivas y sincronizar las pills.
6. Construir tablas, barras, diagramas, franjas y fuentes visibles.
7. Añadir los controladores de animación.
8. Escribir el guion y la evidencia.
9. Ejecutar las pruebas y las comprobaciones de §12; corregir y volver a comprobar sólo lo afectado.
10. Entregar los enlaces y el resultado real de la verificación.

## 12. Criterios de aceptación

### 12.1 Evidencia

- [ ] CQ = `engineering-c-qvoice-20261008-v1`; coincide entre S11 y S12 con tolerancia de 1e-8.
- [ ] Cada cifra visible tiene registro en `evidence.json` y pasa su recálculo desde la fuente.
- [ ] B–C (4 periodos) y C–CQ–D (2 periodos) no se conectan como serie; la franja correcta aparece en las diapositivas 5, 6 y 8.
- [ ] Se distinguen dos comparadores: el azar para el modelo completo y C para el aporte de QVoice (+0.7 puntos).
- [ ] El 2.3% figura como reducción relativa del error de grupo-mes; el 11%, como reducción relativa de `group_mae_pp`.
- [ ] El 20% sólo aparece en el guion, con comparador y alcance; nunca como mejora general.
- [ ] El indicador de mayor error no se presenta como seguimiento de un único grupo.
- [ ] El ajuste a seis meses se describe con una sola prueba efectiva (ene–feb 2026).
- [ ] Se muestra la mejora en un periodo y el empate en el otro.
- [ ] D reconoce su pequeña mejora de estimación y su incumplimiento de las reglas; `RSF_Q` aparece con captura «similar», no idéntica.
- [ ] La versión final de septiembre se distingue de los modelos históricos.
- [ ] Fairness y el uso de QVoice se redactan con el alcance de la evidencia revisada.

### 12.2 Estructura e idioma

- [ ] 9 elementos `.slide-stage` y 9 `.nav-pill`, con índices del 0 al 8 e IDs únicos.
- [ ] `lang="en"` y `<meta name="deliverable-classification" content="presentation">`.
- [ ] Nombres sencillos con su letra entre paréntesis.
- [ ] El deck abre en la diapositiva 1; sólo el tema persiste entre aperturas.

### 12.3 Verificador

Ejecutar:

```powershell
.\.venv\Scripts\python.exe -B .agents/skills/build-html-presentation/scripts/verify_deck.py <html> --mode presentation
```

- Conservar la salida íntegra.
- Registrar como excepción de idioma prevista (§1) el error `El elemento <html> debe declarar lang="es".` y los avisos de controles en inglés.
- Corregir cualquier otro error o aviso material; la excepción no cubre privacidad, cifras, recursos, estructura ni problemas visuales.
- El informe distingue «verificador original con excepción documentada de idioma» de «sin errores».
- Una posible opción `--lang en` en el verificador es una mejora separada, con su prueba, y no es requisito de esta presentación.

### 12.4 Navegador

- [ ] 1440 × 810 y 1920 × 1080; las 9 diapositivas en los 4 temas.
- [ ] Sin recortes, superposiciones ni texto principal ilegible. La diapositiva 6 tiene una lectura principal clara.
- [ ] Sin errores de JavaScript; funciona sin red.
- [ ] Animaciones: `Play`, `Replay`, `Show all`, cancelación al salir, estado inicial al volver, movimiento reducido y teclado.
- [ ] Todo se entiende sin color.
- [ ] Legibilidad de las diapositivas 3 y 8 comprobada sobre el HTML renderizado a 1440 × 810: los cinco compromisos de la columna lateral (3) y la tabla de cinco columnas (8) se leen a distancia de sala sin bajar de los tamaños mínimos.

### 12.5 Privacidad

- [ ] Sólo agregados en el HTML y en su JavaScript: sin filas, IDs, nombres, respuestas individuales ni scores personales.
- [ ] Sin las tablas de personas ficticias del deck anterior.
- [ ] Los grupos mostrados respetan el mínimo del estudio (300 personas en B) y la regla general de cohortes de al menos 30.
- [ ] Sin etiquetas protegidas ni compensación individual.

### 12.6 Narrativa

- [ ] La audiencia puede responder las cuatro preguntas de §1, incluso sin haber visto el deck anterior.
- [ ] La ganancia se describe como modesta y retrospectiva, sin superioridad general ni lenguaje causal.
- [ ] El ensayo con las tres animaciones cabe en 18 minutos.
- [ ] Revisión con el checklist de `morgan-vis` sobre capturas renderizadas.

## 13. Correcciones previstas

| Hallazgo | Acción |
|---|---|
| Falta una cifra secundaria | Mostrar «n/a» con nota y registrarlo |
| Falta una cifra central (§5.2–5.4) | Resolverla en el manifest antes de entregar; nunca estimarla |
| Una cifra difiere del JSON | Revisar población, periodo, variante, campo, medida de error y redondeo; documentar |
| El hash de la base no coincide | Detenerse y verificar el registro |
| El contenido no cabe | Pasar texto secundario al guion; no bajar de los tamaños mínimos ni añadir diapositivas |
| Las diapositivas 3 u 8 quedan densas en el render | 3: acortar cada compromiso a una línea y llevar el detalle al guion. 8: pasar primero la columna «Reading» al guion y, si no basta, también la del último periodo; conservar modelo, proporción y diferencia de error |
| Se confirma una evaluación de fairness o un acuerdo de uso de QVoice | Citarlo y ajustar la diapositiva 3 y el paso 2 o 3 de la diapositiva 9 |
| Se pide evaluar fairness ahora | Cambio de alcance: `attrition-redshift-db` más una autorización específica para atributos protegidos |
| Se pide un periodo o un entrenamiento nuevos | Cambio de alcance; este plan usa las ejecuciones archivadas hasta el 10-oct-2026 |

## 14. Definición de terminado

La entrega está terminada cuando se cumplen todas estas condiciones:

- existen el HTML de 9 diapositivas, el guion en español, `evidence.json` con los recálculos superados, `validation.json` y las capturas;
- las cifras están reconciliadas;
- el deck funciona sin red en los cuatro temas;
- las tres animaciones son opcionales y siguen un único comportamiento;
- el ensayo cabe en 18 minutos.

Conclusión que debe poder defenderse:

> **B proporcionó una base comprensible. C acercó las estimaciones a lo observado con las mismas definiciones de grupo. Añadir la retroalimentación de los empleados (CQ) concentró algo más de salidas en los grupos priorizados (43.1% frente a 42.4% de C y ~30% al azar) y redujo el error promedio por grupo, con una mejora en un periodo y un empate en el otro. Las alternativas probadas, incluidas D y el bosque de supervivencia, no ofrecieron un balance mejor y estable. Falta comprobar la versión final con datos nuevos, revisar las diferencias entre grupos y acordar el uso de la encuesta antes de un piloto.**
