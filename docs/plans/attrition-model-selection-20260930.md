# Selección del modelo de attrition voluntaria: análisis integral y recomendación

> **Superado en alcance el 2026-10-01.** La población pasó a Engineering
> (`eng_or_noneng`) y la comparación se rehízo con validación rolling-origin:
> ver `docs/plans/attrition-model-engineering-selection-20261001.md`. Este
> documento se conserva como antecedente; los criterios (sección 3) y las
> reglas de promoción (sección 7) se reutilizan sin cambios.

Fecha: 2026-09-30. Alcance: fase 1 de Critical Tech (match exacto, empleados
Regular activos no RF360, sin `seg = 'Other Eng'`). Clasificación del
documento: `presentation`. Sólo contiene agregados ya publicados en el
proyecto y no incluye filas, IDs ni categorías protegidas desagregadas.

Este documento reúne lo que ya se ha producido en el proyecto: el scorecard
de 43 variables, el deck de distribuciones v8 (versión vigente), los
planes del 18 de agosto al 14 de septiembre, los baselines entrenados y la
revisión de 43 papers. Las distribuciones y tasas por variable provienen sólo
de la evidencia que carga el deck v8 (`tools/build_distribution_html_v8.py`);
no se usaron cifras de versiones anteriores del deck ni del playbook de Julia
del 17 de septiembre. Con eso se elige una arquitectura de modelo y se deja
la narrativa para defenderla. No sustituye la validación pendiente: toda
métrica citada viene de un artefacto existente, y lo que aún no se ha medido
se señala como tal.

---

## 1. Resumen ejecutivo

**Recomendación.** Adoptar como modelo champion un **modelo de supervivencia
en tiempo discreto** (hazard mensual persona-mes con enlace `cloglog`,
regularización L2 y estimación pooled sobre Critical Tech). La probabilidad a
6 meses se obtiene encadenando los riesgos mensuales:
`R_6m = 1 - Π(1 - h_t)`. Lo acompañan:

- **Benchmarks obligatorios:** la tasa histórica constante y la logística
  directa a 6 meses. Esta última es el rival más fuerte hoy.
- **Challenger no lineal:** gradient boosting (LightGBM) calibrado. Sólo se
  promueve si supera las puertas de la sección 7.

**Por qué ese y no otro, en una frase:** el problema es de *cuándo* se va
alguien desde un snapshot mensual. El hazard discreto está diseñado para eso:
usa cada mes observado, maneja de forma nativa la censura, las variables que
cambian en el tiempo y la estacionalidad, y produce cohortes y efectos que RH
puede leer como razones de riesgo. Todo eso sin perder, en la evidencia
actual, desempeño frente a la alternativa más simple.

**Advertencia honesta que debe acompañar la recomendación:**

- En el único holdout disponible, hazard y logística están **empatados**:
  Brier 0.02935 en ambos; PR-AUC 0.0407 frente a 0.0412; lift en el decil
  superior 1.51 frente a 1.56.
- La preferencia por el hazard se apoya en criterios estructurales
  (secciones 3 y 4), no en una ventaja de discriminación.
- Si tras la re-ejecución sin `Other Eng`, con validación rolling, la
  logística domina de forma consistente, se adopta la logística. Ambas son
  modelos lineales generalizados con la misma interpretabilidad, así que el
  costo de cambiar es bajo.

---

## 2. Qué dice la evidencia del proyecto (insumos de la decisión)

### 2.1 El problema

| Aspecto | Hecho | Fuente |
|---|---|---|
| Objetivo | Priorizar cohortes de retención; nunca listas de personas | `config/critical_tech_model_spec_v1_20260907.yaml:7-17`; `docs/context/model-overview.md:5-9` |
| Target | Salida `Voluntary` en (t, t+6m]; se excluyen Involuntary, Voluntary Exception y term_type nulo | spec yaml `:38-54` |
| Grano | Empleado-snapshot mensual; el output publicado es por cohorte (n ≥ 30; ≥ 100 para reporte ejecutivo) | spec yaml `:32-35`, `:165-172` |
| Prevalencia | 3.0% a 6 meses (preflight); 3.16% en el screen Critical Tech; 0.50% mensual | `docs/plans/attrition-model-recommendation-20260907.md:111-116`; `output/analysis/critical-tech/20260907/cohort-screen-report.md` |
| Volumen | 2,222,966 exposiciones mensuales con 11,670 eventos; 2,038,274 exposiciones a 6 meses con 64,385 eventos | `baseline-v2-calendar-brier/model-results.json:42-47` |

### 2.2 Las variables

- **Ninguna variable llega a "Alta".** El máximo es 12/16, siempre con
  Definition y Consistency en 1. El reparto de las 43 es: 24 Media, 13
  Sensible/restringida, 4 Externa, 3 No disponible y 1 Por definir
  (`output/assessments/attrition-43-monthly-fiscal-20260816/assessment.xlsx`).
  Implicación: el modelo tiene que ser **auditable variable por variable**,
  porque cada feature todavía carga deuda de definición.
- **Señales más fuertes observadas** (asociaciones agregadas, no causales):

  | Señal | Contraste | Fuente (`output/distribution/json/`) |
  |---|---|---|
  | QVoice "me veo en Qualcomm en unos años" | 11.2% no favorable frente a 2.9% favorable, anual (3.8×) | `qvoice-favorable-unfavorable-question-attrition-evidence-20260923.json` |
  | Intent to Stay / Career goals | 2.7× a 3.0× | ídem |
  | Tenure 2 a <4 años | Lift 1.48 a 6 meses (10+ años: 0.47) | `…v3.six-month-attrition-evidence-20260914.json` |
  | Nivel Assoc/Int/Eng | Lift 1.45 anual (Sr Dir: 0.47) | `…v7.nav28-39-direct-annual-…-20260917.json` |
  | Geografía (Noida, Bangalore, Irlanda) | Lift 1.8, 1.6 y 1.6 a 6 meses; China 0.13 | archivo v3 de 6 meses |
  | Cambios de manager en 6 meses | 0 → 5.3%; 2 → 8.1%; 3+ → 9.7% anual | `…v7.nav38-plus-august-trailing-12m-evidence-20260921.json` |
  | Rehire | 8.0% frente a 5.1% (brecha creciente FY24 → FY26) | `…v7.rehire-comparison-…-20260922.json` |
  | Comp ratio < 0.8 | Lift 1.28 anual | archivo nav28-39 |

- **Señales débiles o nulas:** modalidad onsite (2.83% frente a 2.75%),
  transfer (lift 1.09) y commute (sin gradiente).

### 2.3 Las propiedades de los datos que condicionan el modelo

1. **Panel con historia repetida.** El mismo empleado aparece hasta 68
   meses. El split aleatorio filtra información; hace falta validación
   temporal (Singer & Willett 1993, P03).
2. **Evento raro.** Con una prevalencia del 3%, accuracy no sirve y PR-AUC,
   lift y Brier sí.
3. **Casi todo cambia en el tiempo.** Tenure, tiempo en nivel, cambios de
   manager, comp ratio y la antigüedad de la ola de QVoice.
4. **Estacionalidad y deriva.**
   - El mes calendario 5 frente al 7 tiene una razón de riesgo de 1.66
     (`baseline-v2-calendar-brier/model-report.md:60-71`).
   - Co-location tuvo un pico en FY2022 del 9.3%.
   - El turnover llega "en olas" (Somers 1996, P04).
5. **No linealidades moderadas.**
   - Pico de riesgo a los 2-3 años de tenure.
   - Forma de U en el ratio observado/esperado del manager.
   - Interacción entre ruta de entrada y tiempo en nivel.
6. **Faltantes informativos.**
   - Categorías "Sin Labor Market" y "Sin valor" con lift 2.2-2.4.
   - No respuesta a QVoice (el v8 no la cuantifica; queda por validar).
   - Team turnover con 91% "Unknown".
   - Work arrangement sólo desde 2024-08.
   - Layers sólo desde 2023-03.
7. **Censura.** Los snapshots recientes no tienen 6 meses de seguimiento
   completo.
8. **Jerarquía.** Alrededor de 10,500 managers, además de sitio y job family.
   El contagio de equipo **no es estimable** en Critical Tech (36 de 48
   puntos suprimidos).

---

## 3. Criterios de selección

Se fijan antes de comparar para no elegir el modelo que "gane" por
casualidad. Salen de la story review
(`docs/plans/attrition-model-story-review-20260818.md:240-257`), del spec y
de AGENTS.md.

| # | Criterio | Por qué importa aquí | Peso |
|---|---|---|---|
| C1 | Ajuste al problema temporal (censura, variables que cambian en el tiempo, horizonte) | Es la naturaleza del dato (secciones 2.3.1, 2.3.3 y 2.3.7) | Alto |
| C2 | Calibración global y por cohorte | El entregable es "tasa esperada de la cohorte X"; un ranking sin calibración no sirve | Alto |
| C3 | Discriminación en el tope (PR-AUC, lift y captura por decil) | Prioriza dónde actuar | Alto |
| C4 | Estabilidad temporal (folds, signos, orden de cohortes) | Deriva y olas (sección 2.3.4) | Alto |
| C5 | Interpretabilidad agregada para RH | Los stakeholders piden "interpretable y action-ready" | Alto |
| C6 | Gobierno: privacidad, fairness y ausencia de explicaciones por persona | AGENTS.md; decisión `:23` del decision log | Obligatorio (gate) |
| C7 | Robustez con variables "Media" y faltantes | Ninguna variable está en "Alta" | Medio |
| C8 | Costo operativo y de mantenimiento | Equipo pequeño; el script actual entrena con IRLS sobre celdas agregadas sin persistir filas | Medio |
| C9 | Respaldo en la literatura con eventos observados | Se descartan papers de intención o accuracy (`model-candidates-20260914.md:75-76`) | Medio |

---

## 4. Modelos candidatos

### Modelo A (recomendado como champion): hazard discreto mensual `cloglog` regularizado

`log(-log(1 - h_it)) = α(t) + β'X_it`, estimado sobre filas persona-mes.
`α(t)` recoge el tiempo y el mes calendario. `X_it` son las features en
bandas conocidas al snapshot, más indicadores explícitos de faltante. Lleva
penalización L2 elegida en validación y un modelo pooled, sin modelos por
segmento.

1. **Por qué es buena opción.**
   - La pregunta de negocio es "¿cuántos de esta cohorte se irán en los
     próximos 6 meses?". El hazard modela el riesgo de cada mes y lo compone
     a cualquier horizonte (1, 3, 6 o 12 meses) sin reentrenar.
   - Esto importa porque el horizonte de 6 meses **aún no está confirmado
     formalmente** (`recommendation:398`).
2. **Ventajas frente a las alternativas.**
   - *Frente a la logística a 6 meses:*
     - Usa todos los meses, incluidos los censurados recientes. La logística
       descarta los snapshots sin 6 meses de seguimiento, que son los más
       recientes y relevantes.
     - Evita las ventanas de 6 meses solapadas, que cuentan el mismo evento
       hasta seis veces.
     - Deja que las variables cambien dentro de la ventana, como el mes
       calendario (corrección de v2).
     - Produce curvas de supervivencia por cohorte.
   - *Frente a Cox:*
     - Los datos son mensuales, así que el tiempo discreto es natural.
     - No hay problema de empates.
     - La estacionalidad entra como covariable sin forzar riesgos
       proporcionales en el tiempo de calendario.
   - *Frente a GBM, RSF o deep learning:*
     - Coeficientes auditables y efectos con signo.
     - Menor varianza con 11,670 eventos mensuales.
     - Entrenable sobre celdas agregadas, como hace hoy el script, sin
       persistir filas de empleado. Esta es una ventaja de privacidad
       concreta.
3. **Limitaciones y riesgos.**
   - Sólo captura interacciones que se especifiquen, así que requiere
     diseñarlas: tenure × ruta de entrada, región × segmento.
   - En v2 **subestima el riesgo en los quintiles bajos y medios**
     (observado 1.75% frente a predicho 1.54% en Q1; 2.35% frente a 1.99% en
     Q2). Hay que recalibrar.
   - La composición mensual acumula error si el hazard mensual está sesgado.
   - Las ventajas estructurales no se han traducido todavía en mejores
     métricas.
   - Varias features (`manager_change_12m`, promoción, transfer) necesitan
     validación histórica.
4. **Criterios de selección que cumple.**
   - C1 (máximo), C5, C6, C8 y C9 claramente.
   - C2 y C3 empatados con la logística.
   - C4 está por medir.
5. **Alineación con datos y variables.**
   - Casi todas las señales fuertes (tenure, tiempo en nivel, cambios de
     manager recientes, antigüedad de la ola QVoice) cambian mes a mes. El
     formato persona-mes las representa sin aproximaciones.
   - Las bandas ya definidas en los decks (tenure 2-<4, comp ratio <0.8 y
     0.8-0.9, cambios de manager 0/1/2/3+) se traducen directamente en
     dummies.
   - Los faltantes informativos entran como categoría propia.
   - QVoice es anual: la ola vigente se asigna a cada mes posterior, con su
     antigüedad como covariable.
6. **Evidencia de papers y documentación.**
   - Allison 1982 (P02) define el formato persona-periodo con cloglog como
     especificación natural; el proyecto lo adopta como grain.
   - Singer & Willett 1993 (P03) aportan el frame de supervivencia discreta
     y la validación temporal.
   - Madariaga et al. 2018 (P09): en turnover real, la supervivencia
     "representa mejor el carácter longitudinal" que un modelo binario
     aislado.
   - Somers 1999 compara supervivencia con métodos tradicionales en
     turnover.
   - Lee et al. 2023 (P11) aplican supervivencia discreta al primer
     turnover.
   - Decisión del proyecto: "Modelo pooled de hazard discreto — Adoptada
     para MVP" (`docs/research/attrition-literature/model-decision-log.md:12`)
     y la síntesis metodológica (`methodological-synthesis.md:5-8`).
7. **Prácticas de la industria.**
   - Es el enfoque estándar en churn de suscripciones, riesgo de crédito
     (probabilidad de default por periodo) y epidemiología aplicada. En todos
     ellos hay snapshots periódicos, censura y variables que cambian.
   - Encaja con la gestión de riesgo de modelos tipo champion/challenger
     (por ejemplo, la guía SR 11-7 de la Reserva Federal): un champion simple
     y documentado, y challengers que deben ganarse el puesto.
8. **Interpretabilidad para People Analytics y RH.** Es alta y en un lenguaje
   natural para RH:
   - "Estar entre 3 y 7 años de antigüedad se asocia con 1.66 veces más
     riesgo mensual que 7+ años."
   - "En mayo el riesgo es 1.66 veces el de julio."
   - Se pueden mostrar curvas de supervivencia por cohorte ("de cada 100 en
     esta cohorte, se esperan N salidas en 6 meses").
   - Todas son lecturas agregadas y no requieren explicaciones por persona.
9. **Evaluación.** Ver la sección 6. Métricas clave: Brier a 6 meses y skill
   frente a la tasa histórica, calibración por decil y por cohorte, PR-AUC,
   lift y captura en el 10% y 20% superior, y estabilidad entre folds.

### Modelo B (benchmark fuerte y plan de respaldo): logística directa a 6 meses

Una fila por empleado-snapshot con seguimiento completo y target
`Y_6m ∈ {0,1}`. Mismas features y penalización L2.

1. **Por qué es buena opción.**
   - Es la forma más directa de responder "¿se va en 6 meses?".
   - Es fácil de explicar y hoy tiene el mejor PR-AUC (0.0412) y lift@10%
     (1.56) del holdout.
2. **Ventajas.**
   - Una sola ecuación y probabilidad a 6 meses sin composición.
   - Es el formato que más stakeholders conocen (scorecards de crédito).
   - Es menos sensible a errores del hazard mensual.
3. **Limitaciones y riesgos.**
   - Descarta los últimos 6 meses de datos por falta de seguimiento, que son
     los más relevantes ante deriva.
   - Las ventanas solapadas generan dependencia fuerte entre filas y pueden
     inflar la confianza en los coeficientes.
   - Las variables se congelan en el snapshot aunque cambien dentro de la
     ventana.
   - Sólo sirve para un horizonte: si negocio pide 3 o 12 meses, hay que
     reentrenar.
4. **Criterios.** C3, C5, C6 y C8 altos; C1 medio; C2 empatado.
5. **Alineación.** Buena con variables estables en el snapshot; peor con
   cambios de manager o promociones que ocurren dentro de la ventana.
6. **Evidencia.**
   - Es challenger explícito en la síntesis (`methodological-synthesis.md:19-24`).
   - Lazzari et al. 2022 (P42): una logística ridge queda a 0.005 de PR-AUC
     de LightGBM (0.583 frente a 0.588), en una encuesta europea con CV
     aleatoria, así que no es comparable en validación.
7. **Industria.** Es el caballo de batalla de los scorecards regulados, por
   su transparencia.
8. **Interpretabilidad.** Alta, con odds ratios. Igual que el hazard, salvo
   las curvas de supervivencia.
9. **Evaluación.** El mismo protocolo que el modelo A, sobre el mismo holdout
   y la misma población.

**Por qué no es el champion hoy.** Empata en métricas y pierde en C1:
maneja peor la censura, el solapamiento, las variables que cambian en el
tiempo y la flexibilidad de horizonte. Es el primer sustituto si el modelo A
no mejora su calibración.

### Modelo C (challenger no lineal): gradient boosting (LightGBM) calibrado

LightGBM sobre el mismo frame: persona-mes para el hazard, o 6 meses si se
compara con B. Restricciones monotónicas donde la dirección sea defendible,
calibración isotónica o Platt en validación, y explicación **sólo global o
por cohorte** (importancia, dependencia parcial agregada).

1. **Por qué es buena opción.** Captura sin especificarlas las no
   linealidades e interacciones observadas: pico de tenure, U del manager,
   ruta × antigüedad, región × segmento.
2. **Ventajas.** Suele ser el mejor en tabulares heterogéneos y maneja bien
   faltantes y categorías con muchos niveles.
3. **Limitaciones y riesgos.**
   - Necesita calibración explícita.
   - Tiene más varianza con eventos raros.
   - Su interpretación es menos directa y la tentación de usar SHAP por
     persona está **prohibida** por el proyecto.
   - Es más fácil que se cuele leakage por interacciones con faltantes.
   - Requiere entrenamiento sobre filas, no sobre celdas agregadas, lo que
     endurece el manejo de privacidad en memoria.
   - Aporta poco cuando hay pocas señales fuertes y en bandas.
4. **Criterios.** C3 potencialmente más alto; C2 y C5 más bajos; C8 medio.
5. **Alineación.** Tiene más valor cuando entren los bloques de carrera,
   manager y QVoice, que es donde aparecen las interacciones. Con las 5
   features actuales aportaría poco.
6. **Evidencia.**
   - P42: ventaja de 0.005 de PR-AUC sobre la logística, que "se vuelve
     pequeña o cambia tras ponderar por país" (`papers/2022-lazzari…md:49`).
   - El decision log lo deja "sólo challenger contra attrition voluntario
     observado y el mismo holdout" (`model-decision-log.md:24`).
   - Los estudios con AUC altos (P38, S02, P41) usan intención, datasets
     simulados o splits no temporales, así que no sirven como prueba.
7. **Industria.** Es el estándar de facto en competencias y en muchos
   equipos de churn. En RH, los equipos maduros lo usan como challenger o
   para descubrir interacciones que después se trasladan a un modelo
   explicable.
8. **Interpretabilidad.** Media-baja. Aceptable sólo en forma agregada.
9. **Evaluación.** El mismo protocolo, más calibración post-hoc medida fuera
   de muestra.

**Rol.** Es un challenger que, además, sirve de detector: si gana mucho,
indica qué interacción falta en el modelo A, y se incorpora explícitamente
allí.

### Modelo D (extensión del champion, fase 2): hazard con partial pooling jerárquico

Es el modelo A con efectos aleatorios o shrinkage por sitio, job family o
unidad organizacional, o con target encoding con shrinkage fuera del fold.

- **A favor:** estabiliza cohortes pequeñas sin modelos por segmento.
- **Riesgos:**
  - por manager, roza "high risk manager", que es sensible;
  - el contagio de equipo no es estimable en Critical Tech;
  - añade complejidad.
- **Recomendación:** sólo por sitio o región, y sólo si la estabilidad por
  cohorte del modelo A es insuficiente.

### Alternativas evaluadas y descartadas o pospuestas

| Alternativa | Motivo | Cuándo reconsiderar |
|---|---|---|
| Cox con covariables que cambian en el tiempo (P01) | Tiempo continuo con datos mensuales (empates); supuesto de riesgos proporcionales dudoso para tenure y managers | Si se necesita tiempo exacto de salida |
| Random Survival Forest / RFRSF (P08, P32) | Mismas debilidades de interpretabilidad que GBM, más costo; P32 sin métricas publicadas | Después de GBM, si hay no linealidad en el tiempo |
| Competing risks, Fine-Gray (P05, P07) | Falta la semántica aprobada de Voluntary Exception e Involuntary | Cuando RH defina los tipos de salida |
| DeepHit, deep learning o texto (P10, P12, P41) | Complejidad, opacidad, sin texto libre permitido; P41 usa un dataset simulado | Línea futura |
| Modelos por segmento | Segmentos pequeños; 2 de 12 quedan pooled o suprimidos en el preflight | Sólo con volumen, comportamiento distinto y estabilidad |
| Clustering como método principal | Los clusters pueden no ser accionables (`implementation:176-178`) | Como descriptivo, no como modelo |
| Uplift o causal (P38) | No hay intervenciones registradas; SHAP no es causalidad | Tras pilotos de retención |

---

## 5. Matriz de decisión

La escala va de 1 (débil) a 3 (fuerte). La evidencia aún no medida lleva "?".

| Criterio | A: hazard cloglog | B: logística 6m | C: LightGBM | Tasa histórica |
|---|:-:|:-:|:-:|:-:|
| C1 Ajuste temporal | 3 | 2 | 2 | 1 |
| C2 Calibración | 2 (Q1-Q2 bajos) | 2 | ? (requiere post-hoc) | 3 global / 1 cohorte |
| C3 Discriminación | 2 (PR-AUC 0.041; lift 1.51) | 2 (0.041; 1.56) | ? | 1 (0.028; 0.84) |
| C4 Estabilidad | ? | ? | ? | 3 |
| C5 Interpretabilidad RH | 3 | 3 | 1-2 | 3 |
| C6 Gobierno y privacidad | 3 (celdas agregadas) | 3 | 2 | 3 |
| C7 Robustez con features Media | 2 | 2 | 2 | 3 |
| C8 Costo | 3 | 3 | 2 | 3 |
| C9 Literatura con eventos reales | 3 | 2 | 1 | — |

Lectura: A y B dominan a C mientras C no demuestre ganancia. A supera a B
sólo en C1 y C9, lo que basta para preferirlo con un empate en métricas,
pero no para imponerlo si B gana en C2-C4 tras la validación.

---

## 6. Protocolo de evaluación

1. **Re-ejecutar** A, B y la tasa histórica bajo la población de fase 1 (sin
   `Other Eng`) antes de cualquier comparación (`model-decision-log.md:3-7`).
2. **Validación rolling-origin** con al menos 4 orígenes temporales,
   entrenando con todo lo anterior. Añadir **embargo de 6 meses** entre el
   fin del train y el inicio de la evaluación, para que ningún target del
   train se solape con el periodo evaluado. Hoy hay un solo split y el
   embargo no es explícito (`tools/critical_tech_discrete_hazard_model.py:53-57`).
3. **Intervalos de confianza** con bootstrap por empleado (cluster), no por
   fila.
4. **Métricas, todas a 6 meses sobre el mismo holdout:**
   - Calibración: Brier y *Brier skill* frente a la tasa histórica;
     calibración en la media (observado/predicho) y pendiente; curva por
     decil; **error por cohorte publicable** (n ≥ 100), que es lo que se
     entrega.
   - Discriminación en el tope: PR-AUC; lift, precisión y captura en el 10%
     y 20% superior. AUC-ROC sólo como referencia.
   - Estabilidad: varianza de las métricas entre folds; estabilidad de signo
     y magnitud de coeficientes; correlación de rangos del orden de cohortes
     entre periodos; PSI de features y scores.
   - Fairness, sólo agregada y autorizada: calibración y captura por grupo
     protegido, sin usarlo como feature. Declarar la definición elegida y
     sus trade-offs (Corbett-Davies et al. 2023, P37).
   - Nunca se usa accuracy como métrica.
5. **Bloques de features uno a uno**, con el mismo protocolo, en este orden:
   1. carrera;
   2. manager/equipo;
   3. geografía/modalidad;
   4. QVoice gobernado;
   5. compensación en bandas.

   Un bloque entra sólo si mejora Brier o PR-AUC en la mayoría de los folds
   sin empeorar la calibración por cohorte ni la fairness
   (`attrition-model-feature-expansion-20260914.md:145-158`).
6. **Pruebas de leakage** por bloque:
   - disponibilidad de la feature en la fecha del snapshot;
   - exclusión de la salida propia en las variables de equipo;
   - ola de QVoice anterior al snapshot;
   - seguimiento completo de aplicaciones.

---

## 7. Reglas de promoción (propuesta para aprobar con stakeholders)

Son umbrales propuestos que aún no están acordados
(`story-review:360-361`). Hay que fijarlos antes de ver los resultados.

- **Champion inicial:** A si, sobre la media de folds, no es peor que B en
  más de 5% relativo de PR-AUC y tiene Brier igual o mejor. En caso
  contrario, B.
- **Un challenger (C, D o un bloque nuevo) reemplaza al champion** sólo si
  cumple todo lo siguiente:
  - mejora PR-AUC y lift@10% en al menos 3 de 4 folds;
  - su Brier no empeora;
  - el error absoluto medio de calibración por cohorte no empeora;
  - pasa el gate de fairness;
  - puede explicarse en forma agregada.
- **Criterio de utilidad mínima** para usar el modelo en decisiones: Brier
  skill > 0 y lift@10% ≥ 1.5 estables en todos los folds. Hoy el lift está
  en el límite (1.51 a 1.56 en un solo split).

---

## 8. Narrativa para stakeholders

Historia vertical, del problema a la decisión:

1. **"Queremos anticipar dónde, no a quién."** El entregable son cohortes de
   al menos 100 personas con una tasa esperada, una señal asociada y una
   palanca de RH. Nunca scores individuales ni listas para managers.
2. **"La salida es un evento en el tiempo, y así lo modelamos."** El riesgo
   cambia mes a mes: el pico está a los 2-3 años de antigüedad, hay
   estacionalidad (mayo 1.66 veces julio) y la historia llega censurada. Un
   modelo de supervivencia discreta representa eso de forma nativa. Los
   papers con eventos reales (Allison, Singer & Willett, Madariaga, Somers)
   lo respaldan.
3. **"Elegimos el modelo más simple que no pierde nada."** Frente a la
   logística a 6 meses empata en discriminación y calibración. Frente a la
   tasa histórica sube el PR-AUC de 0.028 a 0.041 y lleva el lift del decil
   superior de 0.8 a 1.5. Además usa los meses más recientes, sirve para
   cualquier horizonte y se entrena sin guardar filas de empleados.
4. **"Lo complejo tiene que ganarse el puesto."** Boosting se evalúa como
   challenger con reglas fijadas de antemano. En la literatura su ventaja
   sobre una logística es de milésimas de PR-AUC. Los AUC de 0.9 publicados
   vienen de datos simulados, de intención de salida o de splits aleatorios.
5. **"Cada efecto se lee en el idioma de RH."** Por ejemplo, "3-7 años de
   antigüedad: 1.7 veces el riesgo". Se muestran curvas de salida esperada
   por cohorte. Todas las lecturas son asociaciones que orientan pilotos,
   no causas.
6. **"Lo que falta y cómo lo cerramos."**
   - Re-ejecutar sin `Other Eng`.
   - Validación rolling con embargo.
   - Corregir la subestimación en cohortes de menor riesgo.
   - Fairness y estabilidad.
   - Agregar variables por bloques; la mayor promesa es la carrera y QVoice
     gobernado (3 a 4 veces más attrition entre no favorables).
7. **Decisión que se pide:**
   - aprobar el marco champion/challenger y sus reglas;
   - confirmar el horizonte de 6 meses;
   - decidir el tratamiento de Voluntary Exception;
   - autorizar el uso gobernado de QVoice y de comp ratio en bandas.

**Preguntas previsibles y respuesta corta:**

| Pregunta | Respuesta |
|---|---|
| "¿Por qué no usar machine learning moderno?" | Está en la evaluación como challenger. Si gana con reglas fijas, se adopta. La evidencia comparable dice que la ganancia suele ser marginal y cuesta interpretabilidad. |
| "Un lift de 1.5 parece bajo." | Es el baseline con 5 variables. Las variables más fuertes (QVoice, carrera) aún no entran. El criterio es mejorar por bloques con validación, no prometer una cifra. |
| "¿Podemos ver quién se va?" | No. Por política el modelo sólo publica cohortes, y la evidencia es asociativa. |
| "¿Por qué no un modelo por segmento?" | Varios segmentos no tienen eventos suficientes. El modelo pooled con efectos por segmento comparte información y es más estable. |

---

## 9. Riesgos que pueden cambiar la recomendación

- **Que la logística gane de forma consistente en C2-C4 tras la
  re-ejecución.** Se cambia a B (sección 7).
- **Que la subestimación del hazard en los quintiles bajos persista tras
  añadir `α(t)` flexible y bloques.** Se recalibra o se cambia a B.
- **Que GBM mejore mucho.** Se interpreta como una interacción omitida: se
  añade a A y se re-evalúa antes de promover C.
- **Membership histórica de Critical Tech no reconstruible**
  (`blocked_missing_common_family_key`). Afecta a todos los modelos por
  igual: se aplica el catálogo vigente de forma retrospectiva y se declara
  la limitación.
- **Cambios en la fuente al refrescar** (el conteo de solicitantes varió
  entre runs). Se congela la extracción por run y se monitorea la deriva.

## Fuentes principales

- `docs/plans/attrition-model-recommendation-20260907.md`,
  `attrition-model-feature-expansion-20260914.md`,
  `attrition-model-story-review-20260818.md`,
  `critical-tech-people-analytics-implementation-20260907.md`
- `config/critical_tech_model_spec_v1_20260907.yaml`
- `output/analysis/critical-tech/20260914/baseline-v2-calendar-brier/`
  (`model-results.json`, `model-report.md`) y `baseline-v1/`
- `output/analysis/critical-tech/20260907/cohort-screen-report.md` y
  `hazard-preflight-report.md`
- `docs/research/attrition-literature/` (`methodological-synthesis.md`,
  `model-candidates-20260914.md`, `model-decision-log.md`, `papers/`)
- `output/assessments/attrition-43-monthly-fiscal-20260816/assessment.xlsx`
- `output/distribution/attrition-43-variable-distributions-v8.html` y la
  evidencia JSON que carga en `output/distribution/json/` (algunos archivos
  conservan "v3" o "v7" en el nombre, pero son insumos del v8)
- `docs/context/comentarios julia.md`
