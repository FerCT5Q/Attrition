# Plan alterno: presentación de la evolución de B a C + QVoice

| Campo | Valor |
|---|---|
| Fecha | 10 de octubre de 2026 |
| Estado | Plan alterno para revisión; no reemplaza ni modifica el plan original |
| Plan de partida | [20261010-presentacion-evolucion-b-cq.md](20261010-presentacion-evolucion-b-cq.md) |
| Clasificación de la futura presentación | `presentation` |
| Skills aplicados en la revisión | [morgan-vis](../.claude/skills/morgan-vis/SKILL.md) y [build-html-presentation](../.claude/skills/build-html-presentation/SKILL.md) |

Este documento tiene dos partes. La **parte I** reúne la revisión del plan original: qué se comprobó, qué está bien, qué errores u omisiones tiene y qué mejoras se proponen. La **parte II** es el plan completo mejorado, que puede implementarse sin leer el original ni la conversación.

---

# Parte I. Revisión del plan original

## I.1 Qué se revisó

- El plan original completo.
- La base de Julia ([presentacion-eng.html](../references/presentations/model-selection/20261005-julia-8-groups/presentacion-eng.html)): textos visibles de sus 9 diapositivas, en especial la portada y los pendientes de la diapositiva 9.
- [model-selection-current.md](../docs/context/model-selection-current.md) y [model-c.md](../docs/context/model-c.md).
- Los resultados agregados S05, S08, S11 y S12, leyendo directamente sus campos JSON.
- Los skills `morgan-vis` (método, extensiones de Attrition y checklist) y `build-html-presentation` (precedencia y conflictos).

## I.2 Cifras verificadas contra las fuentes

Todas las cifras del plan original coinciden con los JSON:

| Afirmación del plan | Fuente y campo | Valor leído | ¿Coincide? |
|---|---|---|---|
| B 45.2% · C 45.4% de captura al 30% | S08 `summary["30"].<B_cuts|C_Bcuts>.metrics.capture_percent` | 45.17 · 45.44 | Sí |
| Error B 0.9 · C 0.8 | S08 `group_mae_pp` | 0.878 · 0.778 | Sí |
| C 42.4% · CQ 43.1% | S11 y S12 `summary.<m>.scenarios["30"].capture_percent` | 42.44 · 43.11 | Sí |
| Error de CQ 2.3% menor que el de C | S12 `group_snapshot_mae_pp` | 0.994 → 0.971 | Sí (−2.3%) |
| Por periodo: C 42.1/42.8 · CQ 43.5/42.8 | S12 `periods[].evaluation` | 42.13/42.76 · 43.46/42.76 | Sí |
| D 42.8% de captura, error −0.8% | S12 | 42.82 · 0.963 | Sí (−0.85%) |
| RSF_Q 43.1% de captura, error +10.3% | S12 | 43.09 · 1.071 | Sí |
| Preguntas fijas (media28) +4.1% de error | S11 `disjoint` | 1.0105 / 0.9709 | Sí |
| Último periodo: CQ 42.8 · D 42.1 | S12 `periods[jan_feb_2026]` | 42.76 · 42.11 | Sí |
| CQ igual en S11 y S12 | Ambos | Diferencia < 1e-14 | Sí |

**Conclusión:** el plan original es sólido en evidencia, trazabilidad, privacidad, la excepción de idioma del verificador y el diseño técnico de las animaciones. Las mejoras que siguen son de **narrativa y lectura para líderes y RH**, no de exactitud.

## I.3 Hallazgos: omisiones y errores de enfoque

### H1. No da seguimiento a los compromisos del deck anterior (omisión importante)

La diapositiva 9 de Julia, que esta audiencia ya vio, prometió cuatro cosas:

1. «Test the remaining model: Random survival forest».
2. «Check more signals: QVoice (intent to stay) and time at current level».
3. «Fix and validate: Reduce overestimates in the highest-risk group and check fairness across groups».
4. «Choose the final version: Use the same 4 tests; adopt changes only if they improve today's model».

El plan original no las retoma de forma explícita. Estado según la evidencia archivada:

| Compromiso | Estado | Evidencia |
|---|---|---|
| Random survival forest | ✓ Probado | `RSF_Q` en S12 |
| QVoice y tiempo en el nivel | ✓ Incluidos | `time_at_level_band` en C ([model-c.md](../docs/context/model-c.md)); QVoice en CQ |
| Reducir la sobreestimación | ◐ Parcial | Ver H2 |
| Revisar fairness entre grupos | ✗ Pendiente | No se encontró una evaluación de fairness archivada en los resultados de modelo del 8 al 10-oct |
| Adoptar cambios sólo si mejoran el modelo actual | ✓ Aplicado, con matiz | CQ ganó un periodo y empató el otro; la decisión del 10-oct ponderó magnitud y precisión (S01) |

**Riesgo:** sin esta tabla, el silencio sobre fairness se notará. **Mejora:** convertir la diapositiva 3 en «Where we left off», con estos compromisos y su estado, y añadir fairness a los pasos siguientes.

### H2. No responde qué pasó con la sobreestimación

Era el pendiente más concreto del deck anterior. S12, escenario 30%, en los grupos priorizados, promedio de dos periodos:

| Modelo | Estimado por cada 100 | Observado por cada 100 | Sobreestimación (`bias_pp`) | Peor grupo (`worst_publishable_group_error_pp`) |
|---|---:|---:|---:|---:|
| C | 5.2 | 4.5 | 0.7 | 2.1 |
| CQ | 5.1 | 4.6 | 0.5 | 2.2 |

- La sobreestimación media baja alrededor de 20% (0.68 → 0.55 puntos).
- El grupo peor estimado no mejora.

Es una lectura más comprensible que «2.3% smaller average gap» y responde lo que se prometió. **Mejora:** usarla en las diapositivas 1 y 6 y mostrar la limitación del peor grupo.

Nota de lectura: el observado cambia entre modelos porque cada uno prioriza grupos distintos.

### H3. Falta la referencia aleatoria (incumple el checklist de morgan-vis)

«43.1% de las salidas en 30% de la población» no se interpreta sin baseline. Un 30% elegido al azar concentraría alrededor de 30% de las salidas (lift de CQ = 1.44 en S12). Dos barras de 42.4 y 43.1 sin esa línea se ven iguales y la animación pierde sentido.

**Mejora:** línea «Random 30% of people → ~30% of exits» en la escala 0–50%.

### H4. «El mismo C» con dos números en pantalla

En la diapositiva 5, C aparece con 45.4% y en la 6 con 42.4%. El plan sólo lo resuelve en el guion de preguntas; en pantalla parecerá un error.

**Mejoras:**

- Una franja de periodos fija y visible en las diapositivas 5, 6 y 8: «4 historical periods, Feb 2024–Jan 2026» o «2 recent periods, Aug 2025–Feb 2026».
- En la 5, el mensaje relativo: misma captura (~45%) y 11% menos error de grupo (0.878 → 0.778).

### H5. Las letras B, C, CQ y D no significan nada para líderes y RH

Títulos como «C + QVoice is our selected model» están escritos para el equipo del proyecto.

**Mejora:** nombres en lenguaje llano, con la letra como etiqueta secundaria. Portada con título activo y KPIs, igual que el deck de Julia.

| Letra | Nombre visible |
|---|---|
| B | Core HR model |
| C | Expanded HR model |
| CQ | HR + employee feedback |
| D | Extra history test |
| RSF_Q | Alternative method (forest) + feedback |

### H6. Falta la línea de gobierno sobre QVoice

Para RH, usar respuestas de encuesta para estimar salidas es sensible. El plan no aclara en pantalla que no hay scores individuales.

**Mejoras:**

- Nota visible en la diapositiva 7: «Survey answers are used only for group-level estimates; no individual scores are produced or shared». Respaldo: `individual_scores_published: false` y `employee_level_rows_persisted: false` en S11.
- Paso propuesto en la diapositiva 9: confirmar con RH el uso de QVoice antes de un piloto. No hay una política registrada; se presenta como propuesta.

### H7. Diapositivas débiles o con riesgo técnico

| # | Problema en el original | Mejora |
|---|---|---|
| 3 | Reubicar `#wt-plane` desde la antigua slide 6 implica JavaScript acoplado al deck anterior; además, la audiencia ya vio esos grupos | «Where we left off»: tres cortes de B en pequeño más la tabla de compromisos. La animación A revela un compromiso por clic. Elimina la dependencia de `#wt-plane` |
| 4 | Tabla 3×3 sólo de texto, 2 minutos sin ningún ancla | Tres pasos con ✓/◐ y una cifra ancla: «9 of 9 survey variants ranked risk better; 0 of 9 passed every check» (S05) |
| 6 | El 2.3% es abstracto; no se aprovecha que el intervalo de captura CQ−C no incluye cero | Barras con línea aleatoria más «estimate vs actual». En notas: +0.7 puntos, IC95 0.2–1.2, condicionado a modelos y prioridades (S11 `intervals`) |
| 8 | La columna de captura no discrimina: todas las filas rondan 43% | Scorecard de tres columnas: captura (≈), error de grupo frente a CQ (+4.1%, −0.8%, +10.3%) y último periodo, con símbolos legibles sin color |
| 9 | Falta fairness; el 30% no tiene dueño de capacidad | Cuatro pasos: nuevo periodo, fairness, gobierno de QVoice, piloto acotado; todos marcados como propuestos |

### H8. Mejoras técnicas menores

- **Verificador:** se podría añadir un parámetro `--lang en` a `verify_deck.py`, que es un skill del proyecto, con prueba incluida. Así se evita repetir la excepción manual. Es opcional; la excepción documentada del original sigue siendo válida. Si se hace, debe ser un cambio separado, con su prueba, y no sólo para este deck.
- **Constructor:** el script debe leer cada cifra de los JSON y generar `evidence.json` con aserciones, sin copiar valores a mano. Añadir una prueba de formateo: como máximo un decimal y `<0.1%` para positivos que redondean a cero.
- **Sin dependencia de `#wt-plane`:** al rediseñar la diapositiva 3 baja el riesgo de romper la navegación y los temas.

## I.4 Decisiones que quedan abiertas

1. **Diapositiva 3:** este plan adopta el registro de compromisos (recomendado). La alternativa es conservar la animación de agrupación de B del plan original (§8, diapositiva 3 del original).
2. **Gobierno de QVoice:** confirmar si ya existe un acuerdo con RH o con el área legal; si existe, citarlo en lugar de proponerlo.
3. **Nombres llanos:** confirmar que la audiencia no conoce ya las letras B, C y D por presentaciones anteriores.

---

# Parte II. Plan mejorado

## 1. Encargo

Presentar a líderes y RH la evolución del modelo de attrition voluntaria de Engineering:

- de dónde partimos (B y los compromisos del deck del 5-oct);
- qué probamos (B + QVoice, C, CQ, mezclas de encuesta, D y bosque de supervivencia);
- qué elegimos: **C + QVoice (CQ), `engineering-c-qvoice-20261008-v1`, sin calibración adicional a seis meses**, confirmado el 10-oct-2026 (S01).

| Aspecto | Decisión |
|---|---|
| Cantidad | 9 diapositivas; agenda en la 2 |
| Tiempo | 18 min de exposición + 2 de preguntas (1080 s) |
| Audiencia | Líderes y RH |
| Idioma visible | Inglés (`lang="en"`, igual que la base); guion y evidencia en español |
| Formato | HTML autónomo, escenario 1440 × 810, sin red |
| Identidad visual | Base vigente de Julia, Aptos, cuatro temas existentes |
| Comparación central | Grupos priorizados que cubren 30% de la población en cada foto mensual; es un escenario, no una capacidad aprobada |
| Animaciones | Tres, manuales: diapositivas 3, 6 y 7 |
| Salida | `output/presentations/<YYYYMMDD-HHmm>_evolucion-b-cq/presentacion-eng.html` |

Al terminar, la audiencia debe poder responder cinco preguntas:

1. ¿Qué prometimos?
2. ¿Qué cumplimos?
3. ¿Qué aportó la encuesta?
4. ¿Por qué no cambiamos a D?
5. ¿Qué falta antes de usarlo?

## 2. Base, instrucciones y alcance

- Base: [presentacion-eng.html](../references/presentations/model-selection/20261005-julia-8-groups/presentacion-eng.html), SHA-256 `1dfc30dd99a6205ce067ed7a3abf4828748f1f09b736045ae2d6e5465b89a9ae`, registrada en [model-selection-base.json](../config/presentations/model-selection-base.json). Se exporta con `tools/presentations/build_model_selection_deck_v9.py`, sin `--historical`, y se trabaja sobre una copia.
- Leer antes de implementar:
  - [AGENTS.md](../AGENTS.md);
  - [build-html-presentation](../.agents/skills/build-html-presentation/SKILL.md) con su integración y su tabla de precedencia;
  - [morgan-vis](../.agents/skills/morgan-vis/SKILL.md), sus extensiones y su checklist;
  - `html-slide-generator`, en las referencias que se usen.
- El inglés es preferencia explícita del usuario y coincide con la base. Prevalece sobre la regla general de español sólo para el texto proyectado.
- **Alcance:** presentar evidencia archivada hasta el 10-oct-2026. Sin consultas nuevas a Redshift, entrenamiento, cambios de score ni cambios en la elección. Una consulta nueva sería un cambio de alcance y exige `attrition-redshift-db`.
- No se actualiza el registro de la base oficial.

## 3. Mapa de modelos

Información de respaldo; en pantalla se usan los nombres llanos.

| Interno | Nombre visible | Qué es | Papel |
|---|---|---|---|
| B | Core HR model | Modelo del 3-oct: ocho señales de RH y dos combinaciones; riesgo mensual acumulado a 6 meses | Punto de partida |
| B + QVoice | Core HR + feedback tests | Variantes de encuesta, combinaciones y ajustes posteriores (S05–S07) | La encuesta aportó señal; el balance global no se cerró |
| C (`C_Bcuts`) | Expanded HR model | Más información de RH (incluye tiempo en el nivel), con los cortes de B | Mejor balance; base para continuar |
| CQ | HR + employee feedback | C más una corrección QVoice elegida con la historia disponible en cada origen | **Elegido** |
| `disjoint` (media28) y otras mezclas | Fixed survey questions | Mismas seis preguntas con promedio 33, promedio 28 o sin promedio | No superan a CQ |
| D | Extra history test | Historia reciente del equipo, interacciones y controles | No mejora de forma estable |
| `RSF_Q` | Alternative method + feedback | Bosque de supervivencia con QVoice | Captura similar y más error |

Contenido de CQ:

- Artefacto final con corte al 7-sep-2026: Career Goals, promedio de 33 preguntas, Wellbeing Q8/Q10/Q11 y Confidence Q13/Q17.
- Q4 y Q12 entran dentro del promedio de 33, sin coeficiente propio.
- Los coeficientes finales no tienen evaluación posterior a su ajuste.
- Las métricas históricas evalúan los modelos ajustados antes de cada periodo (`folds/`).

Confusiones que hay que evitar:

- B y C son los modelos de octubre, no las letras de documentos de diseño anteriores.
- La comparación B–C usa `B_cuts` frente a `C_Bcuts`, no los árboles ni `C_selected`.
- «Level / 8 groups» se refiere a categorías de nivel.
- D seleccionó sólo Q4, Q12 y Career; las señales de historia nueva se probaron, pero no quedaron en su versión final.

## 4. Fuentes

| ID | Fuente | Uso |
|---|---|---|
| S01 | [Decisión vigente](../docs/context/model-selection-current.md) | Elección, argumentos y límites |
| S02 | Base de Julia y su registro | Estilo y compromisos de su diapositiva 9 |
| S03 | [Confirmación de B](../output/analysis/engineering/20261003/playbook-tenure-confirmation-v1/confirmation-results.json) | Modelo de partida |
| S04 | [Agrupaciones de B](../output/analysis/engineering/20261003/playbook-group-selection-v1/group-selection-results.json) | Cortes de B |
| S05 | [B + QVoice anual](../output/analysis/engineering/20261008/qvoice-model-b-annual-lag-v2/comparison-results.json), [informe](../output/analysis/engineering/20261008/qvoice-model-b-annual-lag-v2/informe-modelo-b-qvoice.md) | 9 variantes: todas ordenan mejor el riesgo; ninguna pasó todas las comprobaciones |
| S06 | [B + QVoice calibrado](../output/analysis/engineering/20261008/qvoice-model-b-calibrated-v1/comparison-results.json) | Combinaciones y calibración mensual |
| S07 | [Calibración a 6 meses](../output/analysis/engineering/20261008/qvoice-horizon-calibration-v1/comparison-results.json) | Ajuste adicional que no se sostuvo |
| S08 | [Cortes B–C](../output/analysis/engineering/20261008/c-group-selection-v1/results.json) | Diapositiva 5 |
| S09 | [Decisión C con cortes de B](../output/analysis/engineering/20261008/model-c-v2/decision-eleccion-c-con-cortes-b.md) | Motivos de C |
| S10 | [C + QVoice](../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/results.json), [contexto](../docs/context/model-c-plus-qvoice.md) | Procedimiento CQ |
| S11 | [Mezclas de encuesta](../output/analysis/engineering/20261009/c-qvoice-mean28-v1/results.json) | CQ frente a mezclas fijas; intervalos; banderas de privacidad |
| S12 | [Modelo D](../output/analysis/engineering/20261010/model-d-v1/results.json), [decisión](../output/analysis/engineering/20261010/model-d-v1/selection-decision.json) | C, CQ, D, RSF_Q; sobreestimación; periodos |
| S13 | [Modelo C](../docs/context/model-c.md) | `time_at_level_band` entre los términos de C |

Consultas guardadas que se citan sin volver a ejecutarlas:

- `queries/profiles/engineering_person_month_features_playbook_v2_20261003.sql` (B)
- `engineering_model_c_person_month_20261008.sql` (C)
- `engineering_model_c_qvoice_person_month_20261008.sql` (CQ)
- `engineering_c_qvoice_mean28_person_month_20261009.sql` (mezclas)
- `engineering_qvoice_person_month_20261008.sql` (S05)
- `engineering_qvoice_horizon_calibration_20261008.sql` (S07)
- `engineering_rsf_person_month_20261008.sql` y `engineering_model_d_history_person_month_20261010.sql` (D), con las cuatro auditorías `queries/audits/engineering_model_d_*_20261010.sql` registradas en `frozen-config.json`

## 5. Contrato de cifras

### 5.1 Población y lectura

- Engineering; Employee, Regular, activos, sin RF360 según cada foto.
- Resultado: salida voluntaria en los 6 meses siguientes a cada foto mensual.
- Priorización: grupos ordenados por riesgo hasta cubrir exactamente 30%, con fracción uniforme del grupo del límite.
- Promedios con igual peso por periodo. Las ventanas se solapan: no sumar exposiciones como personas ni como salidas únicas.
- **B–C usa 4 periodos y C–CQ–D usa 2. No forman una serie.** Esto se muestra en pantalla con la franja de periodos (§7.2).

### 5.2 Diapositiva 5: B frente a C (S08, `summary["30"]`)

| Medida visible | B (`B_cuts`) | C (`C_Bcuts`) | Campo |
|---|---:|---:|---|
| Share of exits in priority groups | 45.2% | 45.4% | `metrics.capture_percent` |
| Average gap per group, per 100 people | 0.9 | 0.8 | `metrics.group_mae_pp` |
| Gap change | — | 11% smaller | `100 × (1 − 0.7780/0.8777)` = 11.4 |

- Diferencia de captura: +0.27 puntos, IC95 −0.32 a 0.85; C gana en 3 de 4 periodos. Pequeña y no concluyente; no se muestra una etiqueta «+0.3».
- Escenario 40%, sólo en notas: 56.4% frente a 57.6%.

### 5.3 Diapositiva 6: C frente a CQ (S12; S11 coincide)

| Medida | C | CQ | Campo |
|---|---:|---:|---|
| Share of exits in priority groups | 42.4% | 43.1% | `scenarios["30"].capture_percent` |
| Random 30% reference | 30% | 30% | Definición; lift de CQ = 1.44 (`lift`) |
| Estimated per 100 people | 5.2 | 5.1 | `predicted_percent` |
| Actual per 100 people | 4.5 | 4.6 | `observed_percent` |
| Overestimate, per 100 | 0.7 | 0.5 | `bias_pp`: 0.681 → 0.545 (−20%) |
| Average gap per group | — | 2.3% smaller | `group_snapshot_mae_pp`: 0.9940 → 0.9709 |
| Worst-estimated group gap | 2.1 | 2.2 | `worst_publishable_group_error_pp` |

Por periodo, en `periods[].evaluation.<m>.scenarios["30"].metrics.capture_percent`:

| Periodo | C | CQ | Lectura |
|---|---:|---:|---|
| Aug–Dec 2025 | 42.1% | 43.5% | CQ mejora |
| Jan–Feb 2026 | 42.8% | 42.8% | Empate |

Notas para el presentador:

- Ganancia de captura de +0.66 puntos, IC95 0.17 a 1.21 (S11 `intervals`, `capture30`), condicionada a modelos y prioridades.
- El 2.3% es una reducción relativa del error, no puntos porcentuales.

### 5.4 Diapositiva 8: pruebas adicionales

Las diferencias de error se calculan dentro de cada estudio: `100 × (error_alt / error_CQ − 1)`, sobre `group_snapshot_mae_pp`.

| Fila visible | Captura al 30% | Gap vs selected | Latest period (Jan–Feb 2026) | Fuente |
|---|---:|---:|---:|---|
| HR + employee feedback · **Selected** | 43.1% | — | 42.8% | S12 `CQ` |
| Fixed survey questions + revised average | 43.1% | +4.1% | 42.8% | S11 `disjoint` |
| Extra history test (D) | 42.8% | −0.8% | 42.1% | S12 `D` |
| Alternative method + feedback | 43.1% | +10.3% | 42.7% | S12 `RSF_Q` |

- La columna «Latest period» de la fila de preguntas fijas sale de S11, `periods[jan_feb_2026].evaluation.disjoint.scenarios["30"].metrics.capture_percent` = 42.76.
- Notas:
  - D mejora el error sólo 0.8%, frente al 10% que exigía su ruta de precisión; captura −0.3 puntos, IC95 −1 a 0.4; no cumple el límite de pérdida por periodo.
  - `monthly_logit` da prácticamente las mismas métricas que D.
  - `C_updated` captura 42.7% con más error.
  - `overlap` (promedio 33) e `items_only` (sin promedio) tienen más error que `disjoint`.
  - `RSF_Q` tiene una captura similar al redondear, no idéntica.

### 5.5 Diapositiva 4: anclas de B + QVoice (S05 a S07)

- S05: «9 of 9 survey variants ranked risk better than B; 0 of 9 passed every agreed check». Q4 fue la más sencilla y prometedora (7 de 8 comprobaciones).
- S06 y S07: los ajustes posteriores mejoraron el ajuste sobre datos anteriores, pero no se sostuvieron de forma consistente en el periodo siguiente. Al construir, extraer de cada fuente una cifra de apoyo verificable; si no existe una sencilla, dejar sólo texto.

### 5.6 Frase de significado que se conserva

«43.1% of observed exits came from priority groups covering 30% of Engineering; a random 30% would hold about 30%».

No es la probabilidad de que alguien se vaya, ni salidas evitadas, ni «precisión».

## 6. Guion y tiempos

| # | Título visible | Tiempo | Acumulado |
|---|---|---|---|
| 1 | Adding employee feedback sharpened where we focus — modestly | 1:00 | 1:00 |
| 2 | From our last update to today's choice | 0:45 | 1:45 |
| 3 | Where we left off: 3 of 4 commitments addressed | 2:00 | 3:45 |
| 4 | Survey answers helped rank risk, but the first tests fell short | 2:00 | 5:45 |
| 5 | The expanded HR model kept the same groups and cut the gap by 11% | 2:15 | 8:00 |
| 6 | Employee feedback raised exits found in priority groups to 43.1% | 3:00 | 11:00 |
| 7 | Feedback refines priorities within familiar, group-level views | 2:00 | 13:00 |
| 8 | Three further tests did not beat the selected model | 3:00 | 16:00 |
| 9 | Next: confirm on new data, check fairness, then a limited pilot | 2:00 | 18:00 |

Los minutos 18 a 20 son para preguntas, sobre la diapositiva 9.

## 7. Especificación por diapositiva

### 7.1 Diapositiva 1. Portada con decisión

- **Título:** «Adding employee feedback sharpened where we focus — modestly».
- **Subtítulo:** «Engineering · Voluntary exits over the next 6 months · October 2026».
- **Tres KPIs**, con el estilo de la portada de Julia:
  1. «43.1% of exits in 30% of people» — «vs. ~30% if chosen at random».
  2. «Overestimate down ~20%» — «5.1 estimated vs 4.6 actual per 100, priority groups».
  3. «Same understandable groups» — «Years at Qualcomm · team exits · level».
- **Línea de decisión:** «Selected model: HR + employee feedback (C + QVoice). Selected for validation — a pilot has not started».
- **Evidencia:** S01 y S12.
- **Notas:** anticipar que la ganancia es moderada y que se probaron alternativas; las cifras se explican en la 6.
- **Transición:** «Empecemos por lo que les prometimos la última vez».

### 7.2 Diapositiva 2. Agenda

- **Título:** «From our last update to today's choice».

| Diapositivas | Etiqueta | Descripción |
|---|---|---|
| 3–4 | Where we left off | Commitments and first survey tests |
| 5–7 | What improved | Expanded HR model and employee feedback |
| 8 | Further checks | Survey mixes, extra history and an alternative method |
| 9 | Decision and next steps | Confirm, check fairness, pilot |

- Franja inferior: `Core HR → Expanded HR → HR + feedback ✓`. Las pruebas relacionadas aparecen como ramas grises.
- **Elemento nuevo, la franja de periodos.** Se define aquí y se repite en las diapositivas 5, 6 y 8 en la misma posición: «Results come from two sets of historical checks: 4 periods (Feb 2024–Jan 2026) and 2 recent periods (Aug 2025–Feb 2026). Numbers are comparable only within each set».

### 7.3 Diapositiva 3. Compromisos del deck anterior (animación A)

- **Título:** «Where we left off: 3 of 4 commitments addressed».
- **Subtítulo:** «Commitments from our 5 Oct update».
- **Disposición:**
  - A la izquierda, una tarjeta pequeña «Core HR model (B)» con los tres cortes de grupo (Years at Qualcomm → Team exits → Level), como diagrama sin datos.
  - A la derecha, la tabla de compromisos:

| We said | Status | Where |
|---|---|---|
| Test the remaining model type (random survival forest) | ✓ Done | Slide 8 |
| Check more signals: QVoice and time at current level | ✓ Done | Slides 5–7 |
| Reduce overestimates | ◐ Partly | Slide 6 |
| Check fairness across groups | ✗ Next step | Slide 9 |

- **Animación A:** revela una fila por paso (4 estados). Los símbolos ✓, ◐ y ✗ acompañan siempre al texto; el color no es la única señal.
- **Nota:** «Groups summarize many people; no individual predictions are shown».
- **Evidencia:** S02 (compromisos), S12 (RSF_Q), S13 (tiempo en el nivel), S10 (QVoice), S12 (`bias_pp`), §I.3 H1 (fairness).
- **Notas:** el compromiso de «adoptar cambios sólo si mejoran» se explica en la 6 y la 8.
- **Si se decide la alternativa** (§I.4): usar el componente `#wt-plane` como en el plan original, sin tablas personales y comprobando su JavaScript.

### 7.4 Diapositiva 4. B + QVoice

- **Título:** «Survey answers helped rank risk, but the first tests fell short».
- **Disposición:** tres pasos horizontales, cada uno con un estado y una frase:
  1. «Single questions and combinations» — ✓ «9 of 9 ranked risk better» / ✗ «0 of 9 passed every check» (S05).
  2. «Broader combinations» — ✓ «Useful beyond whether people answered» / ◐ «Overall estimates still off» (S06).
  3. «Extra adjustment to estimated risk» — ✓ «Better fit to earlier data» / ✗ «Did not hold in later periods» (S07).
- **Pie:** «Feedback was useful — we kept it and changed the base model».
- **Notas:** Q4 fue la más simple y prometedora. No se nombran medidas estadísticas. No invalida QVoice ni la calibración en general.

### 7.5 Diapositiva 5. B frente a C

- **Título:** «The expanded HR model kept the same groups and cut the gap by 11%».
- **Subtítulo:** «Core HR vs. Expanded HR · same group definitions · 4 historical periods · priority groups covering 30% of Engineering».
- **Disposición:** tabla de §5.2 (dos modelos, niveles y cambio de gap) y franja de periodos. Tres etiquetas debajo: «More HR information, incl. time at level», «Same familiar groups», «Similar share of exits».
- **Nota visible:** «The change in share of exits was small and uncertain; the gain is mainly in closer estimates».
- **Notas:** preferencia práctica (S09); escenario de 40%, si preguntan.

### 7.6 Diapositiva 6. C frente a CQ (animación B)

- **Título:** «Employee feedback raised exits found in priority groups to 43.1%».
- **Subtítulo:** «Share of observed exits in priority groups covering 30% of Engineering · next 6 months · 2 recent periods».
- **Gráfico principal:** barras horizontales en una escala de 0 a 50%, con etiquetas directas.
  - Línea vertical punteada en 30%: «Random 30%».
  - Barras: «Expanded HR 42.4%» en gris; «HR + feedback 43.1%» en color de énfasis.
- **Tarjeta derecha, «Estimates vs actual»:** C 5.2 frente a 4.5 y CQ 5.1 frente a 4.6 por cada 100 personas, con la frase «Overestimate down ~20%».
- **Mini tabla por periodo:** la de §5.3.
- **Animación B:**
  1. La línea aleatoria.
  2. C.
  3. CQ.
  4. Resaltar la tarjeta de estimado frente a observado.
  Los valores finales están siempre escritos; no hay contadores.
- **Notas visibles:**
  - «Better in Aug–Dec 2025; tied in Jan–Feb 2026».
  - «The worst-estimated group did not improve».
- **Notas del presentador:** frase de §5.6. Mencionar el IC de captura y que el 2.3% es relativo. El grupo peor estimado (2.1 → 2.2) explica por qué la sobreestimación queda «parcial» en la diapositiva 3.

### 7.7 Diapositiva 7. Cómo funciona CQ (animación C)

- **Título:** «Feedback refines priorities within familiar, group-level views».
- **Diagrama de tres estaciones**, conceptual y sin datos simulados:
  1. «HR information» — «Work history, team context, time at level».
  2. «Employee feedback» — «Career goals · overall feedback · wellbeing · confidence».
  3. «Priority groups» — «Years at Qualcomm · team exits · level».
- **Animación C:** RH → retroalimentación → grupos.
- **Notas visibles:**
  - «Survey answers are used only for group-level estimates; no individual scores are produced or shared».
  - «Final September version shown; historical checks used the model available at each date. The final version still needs a check on later data».
- **Evidencia:** S01, S10 y S11 (`individual_scores_published: false`, `employee_level_rows_persisted: false`).
- **Notas del presentador:** las respuestas de una encuesta se usan al año siguiente (2024 → 2025, 2025 → 2026); esta política no acredita una fecha real de publicación. Las preguntas elegidas variaron entre periodos.

### 7.8 Diapositiva 8. Pruebas adicionales

- **Título:** «Three further tests did not beat the selected model».
- **Subtítulo:** «Same 2 recent periods · priority groups covering 30% of Engineering».
- **Disposición:** scorecard de §5.4. La fila elegida lleva el color de énfasis y la etiqueta «Selected».
- **Símbolos en las celdas**, legibles sin color:
  - «≈» cuando la captura queda a ±0.5 puntos de CQ;
  - «▲ worse» / «▼ better» en el gap;
  - «▼» cuando el último periodo es menor.
- **Anotación:** «Extra history test: slightly closer estimates (−0.8%), but fewer exits found in the latest period (42.1% vs 42.8%)».
- **Notas del presentador:** §5.4. Las pruebas negativas también son un resultado: delimitan lo que no aporta.

### 7.9 Diapositiva 9. Siguientes pasos

- **Título:** «Next: confirm on new data, check fairness, then a limited pilot».
- **Frase principal:** «HR + employee feedback (C + QVoice) remains our selected model».
- **Cuatro pasos propuestos:**
  1. «Check a new period» — «Evaluate the final September version on data after its training date».
  2. «Check fairness across groups» — «Commitment from our last update, still open».
  3. «Confirm survey use with HR» — «Agree how employee feedback may be used before any pilot».
  4. «Prepare a limited pilot» — «Scope, owners, capacity (e.g. the 30%) and measures, before starting».
- **Nota:** «Proposed steps — not yet scheduled or approved. Historical results support the selection; the effect of retention actions has not been measured».
- **Notas del presentador:** cerrar hacia el minuto 18; preguntas en esta misma diapositiva.

## 8. Especificación visual e interacción

- Un mensaje por diapositiva. Títulos activos de una o dos líneas, de 30 a 36 px; la portada, unos 44 px. Cuerpo de 18 a 22 px; celdas y etiquetas de al menos 16 px; fuentes de 12 a 14 px.
- Un color de énfasis para el modelo elegido y gris para el contexto, consistentes en todo el deck. Los símbolos ✓, ◐, ✗, ▲, ▼ y ≈ acompañan al color.
- Barras con origen en cero y la misma escala; línea de referencia aleatoria rotulada.
- Cifras alineadas a la derecha y con unidad explícita. Enteros sin decimales y el resto con un decimal como máximo, también en contenido dinámico.
- **Franja de periodos** en las diapositivas 5, 6 y 8, en la misma posición y con el mismo estilo.
- Todo con SVG o HTML/CSS embebido, con texto alternativo; sin dependencias nuevas ni red.
- **Animaciones A, B y C:**
  - controles `Play`, `Replay` y `Show all`, accesibles con teclado;
  - transiciones de 400 a 700 ms; secuencia completa de 6 s como máximo;
  - sin reproducción automática; los temporizadores se cancelan al salir y la diapositiva vuelve a su estado inicial al regresar;
  - con `prefers-reduced-motion` se muestra directamente el estado final;
  - las flechas siguen navegando entre diapositivas;
  - los controladores se añaden después de los bloques JavaScript base. `showSlide` y `applyTheme` están encapsulados: los cambios se detectan por el DOM.

## 9. Vocabulario visible

| Respaldo | En pantalla |
|---|---|
| Features | HR information / employee feedback |
| Captura al 30% | Share of exits in priority groups |
| `group_mae_pp` / `group_snapshot_mae_pp` | Average gap per group |
| `bias_pp` | Overestimate (estimated vs actual) |
| Lift / baseline | vs. a random 30% |
| Calibración | Extra adjustment to estimated risk |
| Fold | Model available at each date |
| B / C / CQ / D / RSF_Q | Nombres de §3 |

Fuera de la pantalla: `hazard`, `cloglog`, `L1`, `L2`, `PCA`, `Brier`, `PR-AUC`, `log-loss`, `bootstrap` y `fold`.

## 10. Guion del presentador (`guion-presentador.md`, en español)

Para cada diapositiva:

1. objetivo y tiempo acumulado;
2. explicación hablada;
3. momento de activar la animación;
4. cifra que debe recordarse;
5. limitación;
6. transición.

Preguntas preparadas:

- **¿Por qué no B?** C mantiene los grupos y reduce 11% el gap; la ganancia de captura es pequeña.
- **¿Por qué CQ si no ganó los dos periodos?** Ganó uno y empató el otro; la captura es +0.7 puntos (IC 0.2–1.2) con menos sobreestimación. La regla estricta original se conserva como antecedente (S01).
- **¿43.1% significa que esas personas se irán?** No. Es la proporción de salidas observadas en grupos que suman 30% de la plantilla.
- **¿Se resolvió la sobreestimación?** En parte: −20% en promedio, pero el grupo peor estimado no mejoró.
- **¿Y fairness?** No se ha evaluado todavía; es el paso 2.
- **¿Se usan las respuestas individuales de QVoice?** Sólo para estimaciones de grupo; no se publican scores individuales.
- **¿D fue peor en todo?** No. Acercó un poco las estimaciones, pero perdió captura en el periodo reciente.
- **¿QVoice causa las salidas?** No. Son asociaciones predictivas.
- **¿Está probado el modelo final de septiembre?** No. Requiere datos posteriores a su ajuste.
- **¿Por qué 30%?** Es el escenario de comparación; la capacidad real se define para el piloto.
- **¿Por qué C tiene 45.4% en la diapositiva 5 y 42.4% en la 6?** Son conjuntos de periodos distintos (franja de periodos).

## 11. Construcción y entregables

| Archivo | Función |
|---|---|
| `tools/presentations/build_model_evolution_b_cq.py` | Lee los JSON, aplica las fórmulas de §5, renderiza y escribe `evidence.json` con aserciones (falla si una cifra no coincide) |
| `tests/test_model_evolution_b_cq_deck.py` | Prueba el formateo (≤1 decimal y `<0.1%`), las correspondencias de §5 y la estructura (9 diapositivas, 9 pills) |
| `config/presentations/model-evolution-b-cq-20261010.json` | Fuentes, campos, nombres visibles, tiempos e idioma |
| `<salida>/presentacion-eng.html` | Deck autónomo |
| `<salida>/guion-presentador.md` | Guion y preguntas preparadas |
| `<salida>/evidence.json` | Por cifra: diapositiva, fuente, SHA-256, fecha, población, periodo, campo, valor original, cálculo y texto mostrado |
| `<salida>/validation.json` | Resultados del verificador, del navegador y de privacidad |
| `output/preview/<misma ejecución>/` | Capturas y hoja de contacto |

El script acepta `--out`. Por defecto crea una carpeta con fecha y hora, y se detiene si la ruta ya existe.

**Orden de implementación:**

1. Leer instrucciones y fuentes; verificar el hash de la base.
2. Inventariar los agregados de §5, incluidos los campos nuevos (`bias_pp`, `predicted_percent`, `observed_percent`, `worst_publishable_group_error_pp`, `lift`, `intervals` y el último periodo de `disjoint`).
3. Crear el config.
4. Exportar una copia de la base.
5. Reemplazar las 9 diapositivas y sincronizar las pills.
6. Construir tablas, barras, diagramas y la franja de periodos.
7. Añadir los controladores de animación.
8. Escribir el guion y la evidencia.
9. Ejecutar las pruebas y las comprobaciones de §12; corregir y volver a comprobar sólo lo afectado.
10. Entregar los enlaces y el resultado de la verificación.

## 12. Criterios de aceptación

### 12.1 Evidencia

- [ ] CQ = `engineering-c-qvoice-20261008-v1`. CQ coincide entre S11 y S12 con tolerancia de 1e-8.
- [ ] Cada cifra visible está en `evidence.json` y pasa su aserción.
- [ ] B–C (4 periodos) y C–CQ–D (2 periodos) no se conectan; la franja aparece en las diapositivas 5, 6 y 8.
- [ ] La línea aleatoria está en la diapositiva 6 y el baseline se menciona en la portada.
- [ ] La sobreestimación se presenta como parcial, con el peor grupo indicado.
- [ ] Fairness aparece como pendiente, no como hecho.
- [ ] El 2.3% figura como reducción relativa; la captura, como +0.7 puntos.
- [ ] D reconoce su pequeña mejora de estimación; RSF_Q tiene captura «similar», no idéntica.
- [ ] La versión final de septiembre se distingue de los modelos históricos.

### 12.2 Estructura e idioma

- [ ] 9 elementos `.slide-stage` y 9 `.nav-pill`, con índices del 0 al 8 e IDs únicos.
- [ ] `lang="en"` y `<meta name="deliverable-classification" content="presentation">`.
- [ ] Nombres llanos en pantalla y letras sólo como etiqueta secundaria.
- [ ] El deck abre en la diapositiva 1; sólo el tema persiste entre aperturas.

### 12.3 Verificador

Ejecutar:

```powershell
.\.venv\Scripts\python.exe -B .agents/skills/build-html-presentation/scripts/verify_deck.py <html> --mode presentation
```

- Se conserva la salida íntegra.
- El error `El elemento <html> debe declarar lang="es".` y los avisos de controles en inglés se registran como excepción de idioma prevista (§1).
- Cualquier otro error se corrige.
- Si se opta por añadir `--lang en` al verificador (§I.3 H8), hacerlo en un cambio separado con su prueba y ejecutar las pruebas del skill.

### 12.4 Navegador

- [ ] 1440 × 810 y 1920 × 1080; las 9 diapositivas en los 4 temas.
- [ ] Sin recortes ni superposiciones; sin errores de JavaScript; funciona sin red.
- [ ] Animaciones: `Play`, `Replay`, `Show all`, cancelación al salir, movimiento reducido y teclado.
- [ ] Todo se entiende sin color (símbolos presentes).

### 12.5 Privacidad

- [ ] Sólo agregados, sin filas, IDs, nombres, respuestas individuales ni scores personales, incluido el JavaScript.
- [ ] Sin las tablas de personas ficticias del deck anterior.
- [ ] Sin etiquetas protegidas ni compensación individual.

### 12.6 Narrativa

- [ ] La audiencia puede responder las cinco preguntas de §1.
- [ ] Ganancia descrita como modesta, sin superioridad universal ni lenguaje causal.
- [ ] Ensayo dentro de 18 minutos con las tres animaciones.
- [ ] Revisión con el checklist de `morgan-vis` sobre capturas renderizadas.

## 13. Correcciones previstas

| Hallazgo | Acción |
|---|---|
| Falta un campo previsto | Buscarlo en el manifest; si no existe, mostrar «n/a» con nota; nunca estimarlo |
| Una cifra difiere del JSON | Revisar población, periodo, variante, campo y redondeo; documentar |
| El hash de la base no coincide | Detenerse y verificar el registro |
| El contenido no cabe | Recortar texto secundario hacia el guion; no reducir la letra por debajo de los mínimos |
| Se confirma que ya existe una política de uso de QVoice | Citarla y cambiar el paso 3 de la diapositiva 9 a «Apply the agreed survey-use policy» |
| Se decide conservar `#wt-plane` | Seguir el plan original para la diapositiva 3 y auditar su JavaScript |
| Se pide evaluar fairness ahora | Cambio de alcance: requiere `attrition-redshift-db` y una autorización específica para atributos protegidos |

## 14. Definición de terminado

Existen el HTML de 9 diapositivas, el guion en español, `evidence.json` con aserciones superadas, `validation.json` y las capturas. Las cifras están reconciliadas, el deck funciona sin red en los cuatro temas, las animaciones son opcionales y el ensayo cabe en 18 minutos.

Conclusión que debe poder defenderse: **CQ es la elección vigente. Concentra algo más de salidas que C (43.1% frente a 42.4%, contra ~30% al azar) y reduce la sobreestimación media, conservando grupos comprensibles. Las alternativas, incluidas D y el bosque de supervivencia, no mostraron un balance mejor y estable. Quedan pendientes la comprobación del modelo final con datos nuevos, la revisión de fairness y el acuerdo sobre el uso de la encuesta antes de un piloto.**
