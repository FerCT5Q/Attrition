# Selección del modelo de attrition voluntaria — población Engineering

Fecha: 2026-10-01. Sustituye el alcance de
`docs/plans/attrition-model-selection-20260930.md` (Critical Tech fase 1),
que se conserva como antecedente. Clasificación del documento:
`presentation`. Sólo cita agregados; no contiene filas, IDs, nombres ni
categorías protegidas.

Este documento registra **qué modelo elegimos, entre qué alternativas, con qué
datos y por qué**. Su objetivo es servir de fuente única para el deck v4,
incluida la lámina de "historia": de los 43 papers revisados a las familias
de modelos encontradas y de ahí al modelo elegido.

Objetivo final, que guía todas las decisiones: **publicar grupos de
ingenieros con riesgo de salida voluntaria a seis meses que sean fáciles de
identificar, con un modelo interpretable, calibrado y validado en el tiempo**.
Nunca se publican scores ni listas de personas.

---

## 1. Resumen de la decisión

| Pregunta | Decisión 2026-10-01 |
|---|---|
| Población | Empleados `Employee`/`Regular` activos, no RF360, con `eng_or_noneng = 'Engineering'` en cada foto mensual (~37.2k por foto en 2026) |
| Target | Salida `Voluntary` en (t, t+6 meses] desde la foto t |
| Familia de modelo | **Hazard discreto mensual** (GLM binomial, enlace `cloglog`, L2) sobre persona-mes; R6 = 1 − Π(1 − h_m) |
| Benchmarks | Tasa histórica; logística directa a 6 meses |
| Challengers | Hazard con interacciones nivel × antigüedad; LightGBM 6m calibrado; (pendiente) RSF |
| Especificación vigente (2026-10-02) | Nivel, antigüedad, mes calendario, cambios de manager en 12m, salidas del equipo en 12m, reportes directos, nivel × antigüedad y antigüedad × cambios de manager; **sin tendencia** (53 parámetros; `hazard-adjustment-v2`, sección 10) |
| Siguiente paso | Corregir la sobreestimación del quintil más alto (recalibración sobre el modelo final), fairness agregada, intervalos y piloto por grupos (sección 10.6) |
| Validación | Rolling-origin, 4 folds de 6 fotos, embargo de 6 meses en el train de 6m |
| Salida publicada | Grupos de ≥30 personas por foto; tasas observadas sólo con ≥30 salidas |

En una frase: **elegimos la familia de supervivencia en tiempo discreto
porque es la que la literatura con salidas reales recomienda para paneles
mensuales con censura. En nuestra validación temporal fue igual o mejor que
todos los rivales en los cuatro periodos, sin perder interpretabilidad.**

---

## 2. Por qué cambió la población (de Critical Tech a Engineering)

### 2.1 Hallazgo: `seg`/`job_family` dejaron de ser comparables

El 2026-09-01 se reasignó `job_family` de forma masiva. Entre las fotos
2026-08-23 y 2026-09-27, 5,420 de 49,653 empleados regulares activos (10.9%)
cambiaron de `seg` derivado de `hrda.critical_tech`. La regla de aceptación
era que al menos el 99% conservara su segmento; **no se cumplió**
(`queries/audits/critical_tech_seg_stability_job_family_reassignment_20261001.sql`).

Consecuencia: un modelo entrenado con el `seg` histórico y aplicado con el
`seg` nuevo aprendería una variable que significa otra cosa en producción.
`seg` y `job_family` se excluyen como features y como filtro de alcance.

> Para el deck: este dato va en la lámina de datos/población, no en una
> lámina propia. Mensaje: "En septiembre se reclasificó a 1 de cada 10
> personas de segmento; por eso no usamos segmento ni job family".

### 2.2 Alternativas de población evaluadas y descartadas

| Alternativa | Evidencia | Decisión |
|---|---|---|
| Critical Tech sin `Other Eng` (fase 1 del 2026-09-24) | Depende de `seg`, que no es estable (2.1) | Descartada |
| "Núcleo" Priority + Critical Tech (~11.7k) | Sólo existe tras la reasignación: ~5.85k–6.28k por foto hasta 2026-08-23 y 11,656 en 2026-09-27 (`queries/audits/critical_tech_core_scope_size_by_snapshot_20261001.sql`) | Descartada: no hay historia con la definición vigente |
| Congelar los IDs de septiembre y seguirlos hacia atrás | Sesgo de supervivencia: sólo entran quienes siguen activos en 2026-09, así que nadie que se fue antes puede ser evento | Descartada |
| Mapear `job_family` antigua → núcleo nuevo | Pureza insuficiente: 29 families con ≥90% en el núcleo cubren 6,211 personas; 5 families mixtas (10–50%) concentran 26,571 personas, de las que 5,338 están en el núcleo (`queries/audits/critical_tech_core_scope_job_family_crosswalk_purity_20261001.sql`) | Descartada: el crosswalk no es determinístico |
| **Engineering vía `eng_or_noneng`** | Estable: entre ago y sep 2026 el 99.98% conserva el valor (Eng→Eng 37,244; NonEng→Eng 7; Eng→NonEng 1). Sin nulos; Engineering crece de 23,557 (jul-2020) a 37,737 (sep-2026) (`queries/audits/eng_or_noneng_reassignment_flips_20261001.sql`, `queries/audits/eng_or_noneng_scope_stability_by_snapshot_20261001.sql`) | **Adoptada** (decisión del owner del proyecto) |

Frames: `queries/profiles/engineering_model_frame_20261001.sql` (hazard
mensual) y `queries/profiles/engineering_six_month_model_frame_20261001.sql`
(6 meses). Filtros: `worker_type='Employee'`, `employee_type='Regular'`,
`active_status=1`, `is_rf360_yes_no=0`, `TRIM(eng_or_noneng)='Engineering'`
en cada foto.

---

## 3. Historia de la literatura: de 43 trabajos a 10 familias de modelos

### 3.1 Qué revisamos

43 trabajos (P01–P43): 42 revisados y P31 todavía candidato
(`docs/research/attrition-literature/literature-matrix.md`), más el
suplemento S01–S04 (`model-candidates-20260914.md`). El 2026-09-29 y el
2026-09-30 se completaron las fichas individuales de P14–P17, P31, P38,
P39 y P43 (`model-decision-log.md:35-42`).

Por su papel en la decisión, se agrupan así:

| Grupo | Trabajos | Qué aportan a la decisión |
|---|---|---|
| Fundamentos de supervivencia | P01 Cox 1972, P02 Allison 1982, P03 Singer & Willett 1993, P05 Fine & Gray 1999, P07 Putter 2007 | Formato persona-periodo, censura, variables que cambian en el tiempo, riesgos competitivos |
| Supervivencia aplicada a turnover | P04 Somers 1996, P09 Madariaga 2018, P11 Lee 2023 | Las salidas llegan en olas; la supervivencia representa mejor lo longitudinal que un binario aislado; hazard discreto sobre salida observada |
| Challengers ML | P08 RSF 2008, P10 DeepHit 2018, P12 texto + survival 2026, P32 RFRSF 2020, P41 deep learning + LIME, P42 logística vs LightGBM, S02 XGBoost, S03 ensemble | La ventaja sobre una logística es pequeña cuando la validación es comparable (P42: 0.583 vs 0.588 de PR-AUC); los AUC altos vienen de datos simulados, intención de salida o splits aleatorios |
| Constructos (qué variables) | P13 meta-análisis de antecedentes, P14–P18 embeddedness e intención, P19 contagio, P20–P21 apoyo, P22 downsizing, P23–P27 engagement, P28–P30 carrera, P33 talento técnico, P39 inseguridad, P40 early career, P43 voz/silencio, S01 bienestar + HR | Orden de bloques: carrera → manager/equipo → geografía/modalidad → encuesta gobernada → compensación en bandas. Separar constructos y no importar pesos |
| Gobierno y fairness | P34 Köchling & Wehner, P35 justicia procedimental, P36 Green & Hu, P37 Corbett-Davies, P38 causal/SHAP | Fairness como puerta, no como feature; sólo explicaciones agregadas; nada de causalidad sin diseño |

### 3.2 Familias de modelos encontradas y veredicto

| # | Familia | Papers | ¿Probada aquí? | Veredicto |
|---|---|---|---|---|
| 1 | Tasa histórica constante | (referencia del proyecto) | Sí | Benchmark mínimo |
| 2 | Logística binaria (6m) | P09, P15, P16, P42, S02 | Sí | Benchmark fuerte; pierde frente al hazard (5.2) |
| 3 | Cox de riesgos proporcionales | P01, P09 | No | Pospuesta: datos mensuales con empates y riesgos proporcionales dudosos en antigüedad |
| 4 | **Hazard en tiempo discreto** | P02, P03, P04, P11 | Sí | **Elegida** |
| 5 | Riesgos competitivos / multiestado | P05, P07, P09 | No | Pospuesta: falta la semántica aprobada de Voluntary Exception e Involuntary |
| 6 | Random Survival Forest / RFRSF | P08, P32 | Pendiente | Challenger de supervivencia no lineal en la ronda de variables |
| 7 | Gradient boosting (LightGBM/XGBoost/ensembles) | P42, S02, S03 | Sí | Challenger: no supera al hazard (5.2); sirve de techo y de detector de interacciones |
| 8 | Deep learning (DeepHit, texto + survival) | P10, P12, P41 | No | Futuro: opacidad; el texto libre no está permitido |
| 9 | Causal / uplift / SCM | P38, P42 | No | Futuro: no hay intervenciones registradas |
| 10 | SEM / mediación (modelos explicativos) | P17, P21, P30, P31, P39 | No aplica | Aportan hipótesis de constructos, no predicción |

Ningún paper aporta pesos, correlaciones ni desempeño transferibles a
Qualcomm. La literatura **elige la familia y el orden de los bloques**; los
datos locales eligen la especificación.

### 3.3 Cómo se eligió: filtro estructural y después prueba empírica

La elección **no** consistió en entrenar las 10 familias y quedarse con la de
mejor métrica. Tuvo dos etapas:

1. **Filtro estructural.** Lo aplican los criterios C1–C9 de
   `attrition-model-selection-20260930.md`, sección 3, contra las
   propiedades de nuestros datos (sección 3.5). Descarta sin entrenar las
   familias cuyo supuesto choca con los datos o con la política:
   - Cox: empates con fotos mensuales; riesgos proporcionales dudosos.
   - Fine-Gray: no hay semántica aprobada de los tipos de salida.
   - DeepHit y texto: opacidad; el texto libre no está permitido.
   - Causal/uplift: no hay intervenciones registradas.
   - SEM: explica, no predice.
2. **Prueba empírica.** Las familias que pasan el filtro se entrenan con los
   mismos datos, folds, rejillas de hiperparámetros y métricas: tasa
   histórica, logística a 6 meses, hazard aditivo, hazard con interacciones
   y LightGBM. Las reglas de promoción se fijaron el 2026-09-30, **antes**
   de ver los resultados. RSF pasa el filtro pero sigue pendiente: entra
   como techo en la ronda de variables (sección 7).

Resultado: el hazard aditivo es el champion (sección 5.3). Ninguna
alternativa probada le gana en 3 de 4 folds en PR-AUC y lift a la vez.

| Etapa | Familias | Resultado |
|---|---|---|
| Revisadas en la literatura | 10 | — |
| Descartadas por filtro estructural | Cox, Fine-Gray / multiestado, DeepHit / texto, causal / uplift, SEM | Se reconsideran cuando cambie la condición indicada en 3.2 |
| Probadas con datos de Engineering | Tasa histórica, logística 6m, hazard aditivo, hazard + interacciones, LightGBM | **Hazard aditivo elegido** |
| Pendiente de prueba | RSF | Techo no lineal en la selección de variables |

### 3.4 Ventajas del hazard discreto frente a las alternativas

| Dimensión | **Hazard discreto (elegido)** | Logística 6m | LightGBM 6m | Cox | RSF | Fine-Gray | DeepHit |
|---|---|---|---|---|---|---|---|
| Desempeño medido aquí (media de 4 folds) | **PR-AUC 0.0457 · lift 1.734** | 0.0447 · 1.689 | 0.0442 · 1.654 | No probado | Pendiente | No probado | No probado |
| Usa los 6 meses más recientes, sin seguimiento completo | **Sí** (cada mes cuenta) | No (los descarta) | No | Sí | Sí | Sí | Sí |
| Cuenta cada salida una vez | **Sí** | No (ventanas solapadas: hasta 6 veces) | No | Sí | Sí | Sí | Sí |
| Variables que cambian dentro de la ventana (mes, manager, promoción) | **Sí** | Congeladas en la foto | Congeladas | Sí | Limitado | Sí | Limitado |
| Horizonte flexible (1, 3, 6, 12 meses) sin reentrenar | **Sí** | No | No | Sí | Sí | Sí | Sí |
| Datos mensuales con empates | **Natural** | n/a | n/a | Requiere corrección | Aceptable | Requiere corrección | Discretiza |
| Estacionalidad y tendencia | **Covariables directas** (mes, tendencia ×0.97/año) | Covariables | Covariables | Sólo vía estratos / tiempo | Implícita | Covariables | Implícita |
| Interpretabilidad agregada para RH | **Alta**: razón de riesgo por nivel, antigüedad y mes | Alta (odds ratio) | Media-baja | Alta | Baja | Media | Baja |
| Calibración del último fold (observado 3.07%) | 2.85% | 2.60% | 3.56% | — | — | — | — |
| Especificación final 2026-10-02 (sección 10, otro frame) | **PR-AUC 0.0513 · lift 2.014**, estimado/observado 1.08 en el último fold | — | Techo con todas las variables: 0.0523 · 1.997, razón 1.16 | — | — | — | — |
| Costo y privacidad | **Bajo**: IRLS; también entrena sobre celdas agregadas | Bajo | Medio; necesita filas | Bajo | Alto | Medio | Alto |
| Respaldo con salidas reales | **P02, P03, P04, P09, P11** | P09, P15, P16 | P42 (encuesta, CV aleatoria) | P01, P09 | P08, P32 | P05, P07 | P10 |

Lectura para el deck: **el hazard es el único que combina el mejor
desempeño medido con todas las ventajas estructurales**. La logística
interpreta igual de bien, pero pierde los meses recientes y rinde menos.
LightGBM no aporta desempeño a cambio de la menor interpretabilidad. Cox,
RSF, Fine-Gray y DeepHit comparten varias ventajas estructurales, pero no se
probaron porque sus costos o supuestos no compensan con estos datos.

### 3.5 Por qué se adapta a nuestros datos

| Propiedad del dato (Engineering) | Qué exige | Cómo lo resuelve el hazard |
|---|---|---|
| Panel mensual: la misma persona aparece hasta ~74 fotos (jul-2020 a ago-2026) | Validación temporal; no split aleatorio | Formato persona-mes (P02) y folds rolling-origin con embargo |
| Evento raro: 0.53% mensual, ~3.2% a 6 meses | Métricas de ranking y calibración, no accuracy | Probabilidad calibrable; se evalúa PR-AUC, lift y Brier |
| Censura: las fotos de 2026-03 a 2026-08 no tienen 6 meses de seguimiento | No tirar los datos más recientes | Cada mes observado entra al hazard |
| Estacionalidad y tendencia de largo plazo | Covariables de calendario | `calendar_month` + tendencia lineal (×0.97 por año) |
| Variables que cambian mes a mes (antigüedad, cambios de manager, promoción) | Actualizar las x dentro del horizonte | Las x se recalculan en cada mes de la composición R6 = 1 − Π(1 − h) |
| El entregable son grupos con tasa esperada | Riesgos aditivos legibles y calibrados por grupo | Coeficientes por categoría → tasas por grupo y curvas de salida esperada |
| Un horizonte de 6 meses aún no confirmado formalmente | Cambiar de horizonte sin rehacer el modelo | El mismo h_m compone a 3, 6 o 12 meses |

### 3.6 Componentes principales (PCA): considerado y descartado

- La literatura de constructos (P15–P17, P20–P21, P24–P26, P43) insiste en
  separar constructos distintos: vínculos, ajuste, apoyo del supervisor y
  apoyo organizacional, engagement del trabajo y de la organización, voz y
  silencio. Un componente principal los mezcla en una combinación lineal sin
  significado de negocio. Eso contradice el objetivo de grupos fáciles de
  identificar.
- Las features son categóricas o en bandas. PCA supone variables continuas y
  varianza comparable, y su versión categórica (MCA) da ejes igual de
  difíciles de nombrar.
- La colinealidad, que es el problema real que PCA resolvería, se maneja con
  regularización L2 o elastic net dentro del GLM, que conserva coeficientes
  por variable.
- PCA es no supervisado: maximiza la varianza de X, no la capacidad de
  predecir la salida.

Conclusión: no se usa PCA. Si una pareja de variables es redundante, la
selección por bloques y el lasso eligen una (sección 7).

---

## 4. Datos y diseño de la evaluación

### 4.1 Frames

| Frame | Grain | Uso | Volumen (Engineering) |
|---|---|---|---|
| Mensual | persona-mes; evento = salida voluntaria el mes siguiente | Entrena el hazard | 2,171,724 exposiciones, 11,477 salidas |
| Seis meses | persona-foto con seguimiento completo; evento = salida en (t, t+6m] | Entrena logística y LightGBM; evalúa todo | 1,990,954 exposiciones, 63,344 eventos (ventanas solapadas: un mismo evento cuenta en hasta 6 fotos) |

- Fuente: `hrda.post_hire_monthly_worker_dtls`, fotos `fis_mo_end_dt`
  mensuales desde 2020-07.
- Frontera de conocimiento: 2026-09-07. La última foto con seguimiento
  completo a 6 meses es 2026-02-22.
- Hasta ahora el entrenamiento usa celdas agregadas: conteos por foto ×
  combinación de categorías, lo que equivale exactamente al GLM sobre
  persona-mes con features categóricas.

### 4.2 Validación rolling-origin

| Fold | Prueba (6 fotos) | Exposiciones de prueba | Eventos |
|---|---|---:|---:|
| 1 | 2024-02-18 a 2024-07-21 | 179,384 | 5,441 |
| 2 | 2024-08-25 a 2025-01-26 | 185,788 | 5,587 |
| 3 | 2025-02-23 a 2025-07-27 | 190,975 | 5,865 |
| 4 | 2025-08-24 a 2026-02-22 | 238,451 | 7,329 |

- Train mensual: fotos anteriores al inicio de la prueba.
- Train de 6 meses: fotos ≤ inicio de la prueba − 6 meses. Este es el
  embargo: ninguna etiqueta del train ve el periodo de prueba.
- Hiperparámetros (L2 ∈ {0, 0.01, 0.1, 1, 10}; rejilla de LightGBM con
  num_leaves {4, 8, 16}, min_sum_hessian {20, 100} y lambda_l2 {1, 10}): se
  eligen en las 6 fotos de validación previas al corte, con un train interno
  igualmente embargado.
- Todos los modelos se evalúan sobre el mismo frame de prueba a 6 meses.
- Métricas:
  - PR-AUC.
  - Lift@10% y lift@20% (en el deck: "de cada 100 salidas, cuántas caen en
    el 10% de mayor riesgo" = 10 × lift).
  - Brier y log-loss.
  - Calibración global y por grupo.
  - No se usa accuracy (prevalencia ~3%).

Implementación: `tools/critical_tech_model_comparison_rolling_noseg.py
--population engineering` (reutiliza
`tools/critical_tech_model_comparison_rolling.py`,
`critical_tech_discrete_hazard_model.py` y
`critical_tech_lightgbm_challenger.py`).

---

## 5. Resultados de la comparación

### 5.1 Especificaciones ejecutadas

| Run | Features | Carpeta |
|---|---|---|
| v1 | nivel, antigüedad, `manager_change_12m`, mes calendario (+ tendencia) | `output/analysis/engineering/20261001/model-comparison-rolling-v1/` |
| v2 | nivel, antigüedad, mes calendario (+ tendencia) | `output/analysis/engineering/20261001/model-comparison-rolling-v2-sin-manager/` |

- Nivel: `level_grouped`, 8 grupos, de "1 - VP & Above" a "8 - Assoc &
  Int/Eng".
- Antigüedad: `company_tenure_band`, con bandas <1, 1–3, 3–7 y 7+ años.
- Mes calendario: 12 meses, para la estacionalidad.
- Tendencia lineal en el tiempo de calendario.
- Las interacciones del challenger son nivel × antigüedad.

### 5.2 Métricas (media de 4 folds, v2, especificación vigente)

| Modelo | PR-AUC | Lift@10% | Brier | Folds que gana al hazard (PR-AUC / lift / Brier no peor) |
|---|---:|---:|---:|---|
| **Hazard cloglog aditivo** | **0.0457** | **1.734** | 0.02943 | — |
| Hazard + interacciones | 0.0460 | 1.745 | 0.02941 | 3/4 · 2/4 · 4/4 |
| Logística directa 6m | 0.0447 | 1.689 | 0.02943 | 0/4 · 0/4 · 1/4 |
| LightGBM 6m | 0.0442 | 1.654 | 0.02945 | 1/4 · 1/4 · 1/4 |
| Tasa histórica | 0.0287 | 0.786 | 0.02954 | — |

Lift@10% del hazard por fold: 1.755, 1.759, 1.919 y 1.505. El v1, con el
`manager_change_12m` defectuoso (sección 6), da prácticamente lo mismo:
hazard 0.0455 / 1.729; LightGBM 0.0441 / 1.623.

### 5.3 Aplicación de las reglas de promoción fijadas el 2026-09-30

Las reglas son las de la sección 7 de `attrition-model-selection-20260930.md`
y se fijaron antes de estos resultados.

1. **Champion inicial**: hazard (A) frente a logística (B). A no es peor que
   B en más del 5% de PR-AUC (es 2.3% mejor) y su Brier es igual (0.02943).
   → **A es champion.**
2. **Challengers**: para reemplazar al champion deben mejorar PR-AUC y
   lift@10% en al menos 3 de 4 folds sin empeorar Brier.
   - Interacciones: PR-AUC 3/4 pero lift 2/4. **No se promueve.** La
     ganancia media es +0.6% de lift y no compensa añadir una dummy por cada combinación nivel × antigüedad.
   - LightGBM: 1/4. **No se promueve.** Que no gane es la señal de que, con
     estas variables, no falta una no linealidad importante.
   - Logística: 0/4.
3. **Utilidad mínima**:
   - Brier skill > 0 en los 4 folds. Se cumple (0.02937 < 0.02942; 0.02904
     < 0.02917; 0.02959 < 0.02977; 0.02971 < 0.02979). El skill medio es
     modesto (~0.4%), algo esperable con un evento del 3%.
   - Lift@10% ≥ 1.5 en todos los folds. Se cumple, al límite en el fold 4
     (1.505).

### 5.4 Diagnóstico del último fold (2025-08 a 2026-02)

- **Captura**:
  - el 10% de mayor riesgo concentra el 15.0% de las salidas;
  - el 20%, el 28.5%;
  - el 50%, el 62.7% (v1; v2 casi igual).
- **Calibración global**: estimado 2.85% frente a observado 3.07%. El hazard
  **subestima un 7%** en el periodo más reciente; la logística subestima más
  (2.60%) y LightGBM sobreestima (3.56%). La causa fue la tendencia lineal
  extrapolada y se corrigió quitándola (sección 10.2).
- **Por antigüedad**:

  | Antigüedad | Observado | Estimado |
  |---|---:|---:|
  | 1–3 años | 3.65% | 3.65% |
  | 3–7 años | 4.03% | 3.94% |
  | 7+ años | 2.01% | 1.75% |
  | <1 año | 2.91% | 2.21% |

- **Punto débil**: las personas con <1 año en niveles medios y altos. Por
  ejemplo, Princ/Directors con <1 año se estiman en 1.3% y se observan en
  5.7%. El modelo aditivo no tiene información sobre *cómo* entró la persona
  (contratación senior, rehire, adquisición), que es justo lo que agregan
  las candidatas de carrera.
- **Foto vigente** (2026-07-26, modelo con toda la historia): 37,221
  personas, riesgo medio a 6 meses de 2.5%, tendencia de ×0.97 por año y 24
  grupos nivel × antigüedad publicables.

---

## 6. Corrección de `manager_change_12m`

**Pregunta.** ¿La variable de cambio de manager en 12 meses mide lo que dice?

**Motivo.** La regla del frame base marcaba como `unknown` a quien no tenía
`manager_change = 1` con fecha. El 97% de las personas-mes caía en
`unknown`.

**Método.** Auditoría agregada en
`queries/audits/manager_change_flag_vs_date_engineering_20261001.sql` (foto
2026-07-26, ingenieros). Se cruza el flag del mes con el número de fechas
de cambio distintas observadas en las fotos de los 12 meses previos.

**Regla de aceptación.** Si la mayoría de `unknown` tiene flag 0 con fecha
nula, la categoría significa "no cambió este mes", no "sin dato", y la
variable debe reconstruirse.

**Métricas observadas.**

- Personas con flag 0 y fecha nula (el antiguo `unknown`):
  - 26,888 sin ningún cambio en 12 meses;
  - 7,154 con 1 cambio;
  - 1,491 con 2 o más.
- Personas con flag 1 y fecha en la ventana:
  - 1,125 con 1 cambio;
  - 563 con 2 o más.
- Distribución reconstruida: 0 cambios 26,888; 1 cambio 8,279; 2 o más
  2,054.

**Conclusión.** El flag sólo vale 1 en el mes del cambio. La regla anterior
**era incorrecta**: confundía "sin cambio este mes" con "sin dato", y
`manager_change_12m` del v1 no medía la exposición a cambios de manager.

**Impacto.**

- El v1 queda como histórico; la especificación vigente es el v2, sin la
  variable.
- La variable se reconstruye como **número de cambios de manager en los 12
  meses previos (0/1/2+)**, contando `manager_change_date` distintas entre
  fotos ≤ t. Se calcula en memoria sobre persona-mes y entra en el bloque
  manager/equipo de la sección 7.

> Para el deck: el cambio de manager **no** es una de las "x" del modelo
> vigente. Es candidata del bloque manager/equipo, y se explica así.

---

## 7. Cómo se elige la especificación final (variables)

### 7.1 Por qué hasta ahora había 4 variables

No se eligieron por correlación. Eran las únicas que cabían en el diseño de
celdas agregadas: el helper read-only limita cada consulta a 1,000 filas, y
con más de ~5 features categóricas las combinaciones por foto superan ese
límite.

Desde el 2026-10-01 el owner del proyecto autorizó procesar persona-mes **en
memoria**
(`config/attrition_model_in_memory_training_authorization_20261001.json`):

- sin persistir filas;
- sin seleccionar `employee_id`, sólo un sustituto seudónimo efímero para
  deduplicar y hacer bootstrap por persona;
- sin scores ni explicaciones individuales;
- sin atributos protegidos como features;
- con salidas sólo por grupos (≥30 personas, ≥30 eventos).

Todo manifest debe citar esa autorización y declarar
`employee_level_rows_persisted=false`.

### 7.2 Candidatas (inventario de 43 variables del playbook)

| Bloque (orden de la literatura) | Candidatas | Condición de entrada |
|---|---|---|
| 0. Base | nivel, antigüedad, mes calendario, tendencia | Vigentes |
| 1. Carrera | tiempo desde la última promoción; tiempo en el nivel; ruta de entrada al grade; rehire (desde 2022-10); experiencia previa | Derivación conocida en t; las variables con historia corta llevan un indicador de "antes de la fuente" |
| 2. Manager/equipo | número de cambios de manager en 12m (corregido); salida del manager (Alta, 14/16); turnover del equipo rezagado, excluyendo la propia salida; layers (desde 2023-03) | Equipo con ≥5 personas; ventana estrictamente previa |
| 3. Geografía/modalidad | región / labor market agrupado; work arrangement (desde 2024-08) | Categorías con ≥30 personas por foto; resto agrupado |
| 4. Encuesta | QVoice intent to stay y career goals (ola previa a t) | Fuente Excel no gobernada: sólo si se valida la ola y su cobertura; si no, queda fuera |
| 5. Compensación/movilidad | compa-ratio en bandas; comp grade track; transfer | Sólo bandas; nunca el valor exacto |

Quedan fuera:

- **No listas**:
  - applications (feed detenido desde 2024-10);
  - talent index (leakage);
  - high-risk manager (política);
  - commute, texto de QVoice y fuentes externas;
  - campos ET, inflection points, adquisición y team turnover "above
    average".
- **Excluidas por diseño**:
  - género y demás atributos protegidos (sólo para la auditoría de
    fairness);
  - `job_family`/`seg` (sección 2).

### 7.3 Procedimiento y regla de parsimonia

1. **Por bloques, en el orden de la tabla.** Un bloque se conserva si mejora
   PR-AUC o lift@10% en al menos 3 de 4 folds sin empeorar Brier ni la
   calibración por grupo.
2. **Dentro del bloque, elastic net / lasso** sobre el hazard, eligiendo la
   penalización en la validación embargada de cada fold. Se retienen las
   variables seleccionadas en al menos 3 de 4 folds y con signo estable.
3. **Techo de referencia.** LightGBM y RSF con todas las candidatas listas.
   Miden cuánto desempeño queda sobre la mesa.
4. **Regla de parsimonia.** Se elige la especificación **más simple cuya
   media de lift@10% y PR-AUC quede dentro del 2% relativo de la mejor**,
   entre hazards y techo. Si nada supera al v2 por más de 2%, el v2 se queda.
   El resultado puede ser 6, 10 o 15 variables: la cantidad no es un
   objetivo.
5. **Grupos publicables.** Un árbol poco profundo (profundidad ≤ 3) sobre el
   riesgo estimado define los grupos. Cada grupo se describe con 2–3
   condiciones legibles, tiene ≥30 personas por foto y, para la tasa
   observada, ≥30 salidas. Se verifica que el orden de los grupos se
   mantenga entre folds (correlación de rangos).
6. **Puertas finales.**
   - Calibración global y por grupo (corregir el −7% del último fold, por
     ejemplo con recalibración del intercepto en la ventana reciente).
   - Fairness agregada y autorizada: calibración y captura por grupo
     protegido, sin usarlo como feature (P37).
   - Intervalos con bootstrap por persona.
   - Pruebas de leakage por bloque.

---

## 8. Guion sugerido para el deck v4

1. **Qué predecimos.** Salida voluntaria a 6 meses, por grupos, nunca por
   persona.
2. **Historia de la literatura y elección (una o dos láminas).**
   1. Literatura: 43 trabajos en 5 temas (tabla 3.1), con una línea de
      tiempo: Cox 1972 → Allison 1982 → Singer & Willett 1993 → Somers 1996
      → RSF 2008 → DeepHit 2018 → LightGBM frente a logística 2022 → hazard
      discreto aplicado 2023.
   2. 10 familias encontradas → 5 descartadas por filtro → 5 probadas con
      nuestros datos → elegido: hazard discreto (tabla 3.3).
   3. Ventajas del elegido frente a los demás (tabla 3.4, reducida a 4–5
      filas: desempeño, meses recientes, una salida = un evento,
      interpretabilidad, horizonte flexible).
   4. Por qué encaja con nuestros datos (tabla 3.5).
3. **Datos y población.** Ingenieros por `eng_or_noneng`, ~37k por foto,
   desde jul-2020: 2.17M personas-mes y 11,477 salidas. Nota: "en septiembre
   se reclasificó de segmento a 1 de cada 10 personas, por eso no usamos
   segmento".
4. **Variables.** De 43 del playbook a las que entran, y por qué. Explicar
   aquí el cambio de manager (6).
5. **El modelo.** La fórmula
   `cloglog(h) = α + tendencia + mes + nivel + antigüedad (+ bloques)`, con
   las x nombradas.
6. **Cómo lo medimos.** 4 periodos futuros, embargo, métricas.
7. **Resultados.** Comparación de 5 modelos (tabla 5.2), curva de captura,
   calibración, grupos y siguientes pasos.

---

## 9. Riesgos y pendientes

- **Subestimación reciente** (−7% en el último fold, y más en <1 año).
  **Resuelta el 2026-10-02**: la causa era extrapolar la tendencia lineal a la
  baja; sin tendencia la razón estimado/observado pasa de 0.59–0.79 a
  1.07–1.15 (sección 10.2). Queda una **sobreestimación** moderada, sobre todo
  en el quintil más alto (6.0% estimado contra 4.6% observado) y en
  Associate/Engineer (razón 1.39).
- **Variables con historia corta**: work arrangement desde 2024-08 y layers
  desde 2023-03. Sólo pueden probarse en los folds 3–4, o con un indicador
  "antes de la fuente".
- **QVoice**: es la señal más fuerte del playbook (2.7× a 3.8×), pero viene
  de Excel no gobernado. Sin validación de olas no entra.
- **Voluntary Exception** y `term_type` nulo siguen excluidos del evento
  hasta que RH lo confirme.
- **Población**: si se vuelve a reclasificar `eng_or_noneng`, se repite la
  auditoría de flips (regla ≥99%).
- **Convergencia**: el v1 del ajuste eligió L2 = 0 en ajustes que no
  convergieron (razones de riesgo de 0.00 en VP y Sr Dir). El v2 sólo acepta
  L2 de ajustes convergidos; toda nueva corrida debe conservar esa regla.
- **VP & Above**: 212 personas por foto; estimado 0.7% contra 2.7% observado
  en el último fold. No se publica como grupo propio.

---

## 10. Resultados de la selección de variables y del ajuste (2026-10-02)

Frame común: persona-mes en memoria
(`queries/profiles/engineering_person_month_features_20261001.sql`), fotos
2021-07-25 a 2026-07-26 (empieza un año después que la sección 5 porque las
variables de 12 meses necesitan historia previa). 1,880,719 persona-mes y
1,699,949 exposiciones a seis meses con 54,452 eventos. Mismos 4 folds de la
sección 4.2; el último fold tiene un observado de 3.00% (3.07% en el frame de
la sección 5).

### 10.1 Selección por bloques

`output/analysis/engineering/20261001/feature-block-selection-v1/`.

| Paso | Bloques | Parámetros | PR-AUC | Lift@10% |
|---:|---|---:|---:|---:|
| 0 | base (nivel, antigüedad, mes, tendencia) | 23 | 0.0454 | 1.708 |
| 1 | + manager/equipo | 30 | 0.0494 | 1.942 |
| 2 | + carrera (promoción en 12m) | 31 | 0.0496 | 1.956 |
| 3 | + geografía (región) | 35 | 0.0498 | 1.942 |
| 4 | + compensación (compa-ratio en bandas, familia de grade) | 43 | 0.0495 | 1.928 |

- Manager/equipo: cambios de manager en 12m (0/1/2+), salidas del equipo en
  12m (0/1/2+) y reportes directos (0/1–5/6+).
- Regla de parsimonia (2% de la mejor): **elegido manager/equipo**. Carrera,
  geografía y compensación no aportan más del 2%.
- Quitar una variable: sin salidas del equipo el lift cae a 1.758; es la
  señal que más aporta.
- Techo LightGBM con todas las variables: PR-AUC 0.0523, lift 1.997.

### 10.2 Tendencia y recalibración

`output/analysis/engineering/20261001/hazard-adjustment-v2/`.

| Tendencia | Recalibración | Brier | Estimado/observado por fold |
|---|---|---:|---|
| Lineal (vigente hasta aquí) | No | 0.02927 | 0.59, 0.71, 0.72, 0.79 |
| Lineal | Intercepto 12m | 0.02926 | 0.52, 0.78, 0.84, 0.87 |
| **Sin tendencia** | **No** | **0.02917** | **1.15, 1.09, 1.08, 1.07** |
| Sin tendencia | Intercepto 12m | 0.02918 | 0.77, 0.96, 1.00, 0.98 |
| Congelada | No | 0.02922 | 0.71, 0.79, 0.78, 0.83 |

Conclusión: la subestimación venía de proyectar a futuro una tendencia a la
baja que se revirtió en 2025-26. Sin tendencia se obtiene el menor Brier de
las seis variantes, con un ranking prácticamente igual. La recalibración de
intercepto no mejora el Brier, así que no se adopta.

### 10.3 Interacciones

Candidatas preespecificadas: antigüedad × salidas del equipo, antigüedad ×
reportes directos, antigüedad × cambios de manager, nivel × salidas del
equipo y nivel × antigüedad. Cada una se codifica sólo cuando ambas partes
son distintas de su referencia. Entra la que mejor gana la regla de promoción
(≥3/4 folds en PR-AUC y en lift, Brier no peor). Se repite hasta que ninguna
pase.

| Ronda | Aceptada | PR-AUC | Lift@10% |
|---:|---|---:|---:|
| 1 | nivel × antigüedad (4/4 y 3/4) | 0.0510 | 2.002 |
| 2 | antigüedad × cambios de manager (3/4 y 3/4) | 0.0513 | 2.014 |
| 3 | ninguna | — | — |

### 10.4 Modelo final y parsimonia frente al techo

| Especificación | Parámetros | PR-AUC | Lift@10% | Brier |
|---|---:|---:|---:|---:|
| Elegido en 10.1 (con tendencia) | 30 | 0.0494 | 1.942 | 0.02927 |
| **Final: sin tendencia + 2 interacciones** | **53** | **0.0513** | **2.014** | **0.02915** |
| Final + carrera y geografía | 58 | 0.0520 | 2.010 | 0.02914 |
| Techo LightGBM, todas las variables | — | 0.0523 | 1.997 | 0.02916 |

- El final llega al 98% del PR-AUC del techo y lo iguala en lift; gana al
  elegido de 10.1 en 4/4 folds en PR-AUC y en 3/4 en lift.
- Agregar carrera y geografía no supera el 2%. Por parsimonia, se queda el
  de 53 parámetros.
- Todos los ajustes convergieron. El v1 del ajuste se descarta por
  ajustes no convergidos (sección 9) y se conserva como histórico.
- Por fold: lift@10% 2.15, 2.10, 2.14 y 1.67; L2 = 10 en el fold 1 y 0.01
  en los demás.

### 10.5 Grupos publicables (foto 2026-07-26, 37,221 personas)

Árbol de profundidad ≤ 3 y hojas ≥ 300 personas sobre el riesgo del modelo
final (R² 0.64). Riesgo medio a seis meses: 2.9%.

| Grupo | Personas | Riesgo 6m | Último fold: estimado / observado |
|---|---:|---:|---|
| 1–7 años de antigüedad y al menos una salida en el equipo en 12m | 4,695 | 5.3% | 5.9% / 4.7% |
| 7+ años, Senior & Lead, con salidas en el equipo | 371 | 4.4% | 4.8% / 3.7% |
| 1–7 años, sin salidas en el equipo | 13,191 | 3.4% | 3.9% / 3.5% |
| <1 año, con salidas en el equipo | 1,645 | 3.2% | 3.4% / 3.4% |
| 7+ años, Senior & Lead, sin salidas en el equipo | 1,220 | 2.8% | 3.1% / 3.6% |
| <1 año, sin salidas en el equipo | 3,669 | 2.0% | 2.1% / 2.5% |
| 7+ años, otros niveles, sin reportes directos | 6,301 | 2.0% | 2.1% / 2.2% |
| 7+ años, otros niveles, con reportes directos | 6,129 | 1.3% | 1.5% / 1.5% |

Todos tienen ≥30 salidas en el último fold (mínimo 65). El orden de riesgo
estimado y observado coincide salvo en el grupo 5 (7+ años, Senior & Lead,
sin salidas en el equipo: 3.6% observado, por encima de los grupos 3 y 4).

### 10.6 Calibración y pendientes del final

- Por quintil (último fold), en los cuatro primeros la diferencia es ≤0.2
  puntos. En el quintil más alto el estimado es 6.0% contra 4.6% observado.
- Por subgrupo: Associate/Engineer razón 1.39; equipo con 2+ salidas 1.26;
  reportes directos 6+ 0.69; VP & Above 0.24 (212 personas).
- Siguientes pasos:
  1. Recalibración por pendiente (no sólo intercepto) sobre el modelo final.
  2. Fairness agregada autorizada.
  3. Intervalos bootstrap por persona.
  4. Piloto de acciones por grupo.
