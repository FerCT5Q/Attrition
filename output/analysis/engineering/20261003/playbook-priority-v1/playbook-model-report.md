# Modelo v2 de Engineering con variables prioritarias del playbook

Creado: 2026-10-03T17:09:54.342247+00:00. Frontera de conocimiento: 2026-09-07. QVoice excluido (modelo en desarrollo).
Fotos 2021-07-25 a 2026-07-26: 1,699,949 exposiciones a seis meses y 54,452 salidas.
Entrenamiento en memoria bajo `config\attrition_model_in_memory_training_authorization_20261001.json`; sin filas ni IDs persistidos. Hazard `cloglog` sin tendencia ni recalibración.

## 0. Reproducción del modelo vigente con el frame nuevo

| Especificación | Parámetros | PR-AUC | Lift@10% | Lift@20% | Brier | Estimado/observado por fold |
|---|---:|---:|---:|---:|---:|---|
| Vigente publicado (none, sin recal, level_x_tenure + tenure_x_manager_changes) | 53 | 0.0513 | 2.014 | 1.727 | 0.02915 | 1.15, 1.10, 1.08, 1.08 |
| Vigente reproducido | 53 | 0.0512 | 2.014 | 1.727 | 0.02915 | 1.15, 1.10, 1.08, 1.08 |

Exposiciones iguales al vigente: sí. Métricas a menos de 1% relativo: sí. La comparación final usa el vigente reproducido (misma medición que el v2).

## 1. Cortes de antigüedad (base + manager/equipo)

| Cortes | Parámetros | PR-AUC | Lift@10% | Lift@20% | Brier | Estimado/observado | Dentro de 2% | Frente a cortes vigentes |
|---|---:|---:|---:|---:|---:|---|---|---|
| cortes de Julia (<1, 1-3, 3-5, 5+) | 29 | 0.0492 | 1.986 | 1.682 | 0.02918 | 1.15, 1.09, 1.08, 1.07 | no | PR 0/4, lift 4/4, Brier no peor no |
| cortes del playbook (<1, 1-2, 2-3, 3-5, 5-10, 10+) | 31 | 0.0507 | 2.071 | 1.750 | 0.02916 | 1.16, 1.13, 1.11, 1.07 | sí | PR 3/4, lift 4/4, Brier no peor sí |
| cortes vigentes (<1, 1-3, 3-7, 7+) | 29 | 0.0496 | 1.937 | 1.705 | 0.02917 | 1.15, 1.09, 1.08, 1.07 | no | — |

Cortes elegidos: **cortes del playbook (<1, 1-2, 2-3, 3-5, 5-10, 10+)**.

## 2. Variables del playbook (selección hacia delante, regla de promoción)

| Paso | Agregada | Sobre | Parámetros | PR-AUC | Lift@10% | Brier | Gana PR | Gana lift | Brier no peor | Aceptada |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|---|
| 0 | prior_experience_band | base (tenure_playbook_band) + manager/equipo | 36 | 0.0513 | 2.103 | 0.02915 | 4/4 | 4/4 | sí | sí |
| 1 | rehire | base (tenure_playbook_band) + manager/equipo | 33 | 0.0509 | 2.081 | 0.02916 | 4/4 | 3/4 | sí | sí |
| 2 | time_since_promotion_band | base (tenure_playbook_band) + manager/equipo | 39 | 0.0519 | 2.094 | 0.02915 | 4/4 | 3/4 | sí | sí |
| 3 | time_at_level_band | base (tenure_playbook_band) + manager/equipo | 37 | 0.0506 | 2.073 | 0.02916 | 2/4 | 3/4 | no | no |
| 4 | manager_left_6m | base (tenure_playbook_band) + manager/equipo | 32 | 0.0504 | 2.096 | 0.02916 | 1/4 | 3/4 | no | no |
| 5 | ios_12m | base (tenure_playbook_band) + manager/equipo | 34 | 0.0504 | 2.051 | 0.02915 | 1/4 | 2/4 | sí | no |
| 6 | layers_band | base (tenure_playbook_band) + manager/equipo | 37 | 0.0509 | 2.018 | 0.02915 | 2/4 | 2/4 | sí | no |
| 7 | work_arrangement_group | base (tenure_playbook_band) + manager/equipo | 35 | 0.0506 | 2.065 | 0.02915 | 1/4 | 2/4 | sí | no |
| | **aceptada: time_since_promotion_band** | → base (tenure_playbook_band) + manager/equipo + time_since_promotion_band | | | | | | | | |
| 9 | prior_experience_band | base (tenure_playbook_band) + manager/equipo + time_since_promotion_band | 44 | 0.0524 | 2.095 | 0.02914 | 4/4 | 1/4 | sí | no |
| 10 | rehire | base (tenure_playbook_band) + manager/equipo + time_since_promotion_band | 41 | 0.0528 | 2.094 | 0.02914 | 4/4 | 2/4 | sí | no |
| 11 | time_at_level_band | base (tenure_playbook_band) + manager/equipo + time_since_promotion_band | 45 | 0.0521 | 2.116 | 0.02915 | 3/4 | 2/4 | no | no |
| 12 | manager_left_6m | base (tenure_playbook_band) + manager/equipo + time_since_promotion_band | 40 | 0.0514 | 2.099 | 0.02915 | 1/4 | 3/4 | no | no |
| 13 | ios_12m | base (tenure_playbook_band) + manager/equipo + time_since_promotion_band | 42 | 0.0518 | 2.080 | 0.02914 | 1/4 | 1/4 | sí | no |
| 14 | layers_band | base (tenure_playbook_band) + manager/equipo + time_since_promotion_band | 45 | 0.0522 | 2.061 | 0.02914 | 2/4 | 2/4 | sí | no |
| 15 | work_arrangement_group | base (tenure_playbook_band) + manager/equipo + time_since_promotion_band | 43 | 0.0518 | 2.086 | 0.02914 | 1/4 | 0/4 | sí | no |

## 3. Interacciones del vigente con los cortes elegidos

| Paso | Agregada | Sobre | Parámetros | PR-AUC | Lift@10% | Brier | Gana PR | Gana lift | Brier no peor | Aceptada |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|---|
| 0 | level_x_tenure | base (tenure_playbook_band) + manager/equipo + time_since_promotion_band | 70 | 0.0531 | 2.090 | 0.02913 | 4/4 | 2/4 | sí | no |
| 1 | tenure_x_manager_changes | base (tenure_playbook_band) + manager/equipo + time_since_promotion_band | 49 | 0.0516 | 2.089 | 0.02914 | 2/4 | 2/4 | sí | no |

## 4. Contribución de cada variable del playbook en el v2 (quitar una)

| Variable quitada | Parámetros | PR-AUC | Lift@10% | Lift@20% | Brier | Estimado/observado |
|---|---:|---:|---:|---:|---:|---|
| time_since_promotion_band | 31 | 0.0507 | 2.071 | 1.750 | 0.02916 | 1.16, 1.13, 1.11, 1.07 |

## 5. Comparación final

| Especificación | Parámetros | PR-AUC | Lift@10% | Lift@20% | Brier | Estimado/observado por fold |
|---|---:|---:|---:|---:|---:|---|
| Vigente reproducido | 53 | 0.0512 | 2.014 | 1.727 | 0.02915 | 1.15, 1.10, 1.08, 1.08 |
| v2: base (tenure_playbook_band) + manager/equipo + time_since_promotion_band | 39 | 0.0519 | 2.094 | 1.755 | 0.02915 | 1.12, 1.12, 1.06, 1.03 |

Regla de promoción frente al vigente: PR-AUC 2/4, lift@10% 2/4, Brier no peor sí. **El v2 no supera al vigente.**

| Fold | L2 | PR-AUC vigente | PR-AUC v2 | Lift@10% vigente | Lift@10% v2 | Brier vigente | Brier v2 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 10.0 | 0.0535 | 0.0589 | 2.153 | 2.388 | 0.02918 | 0.02913 |
| 2 | 10.0 | 0.0523 | 0.0518 | 2.093 | 2.083 | 0.02895 | 0.02896 |
| 3 | 1.0 | 0.0555 | 0.0524 | 2.142 | 2.114 | 0.02949 | 0.02953 |
| 4 | 1.0 | 0.0434 | 0.0443 | 1.667 | 1.792 | 0.02900 | 0.02896 |

## 6. Hazard ratios del v2 por fold

Referencias: {'level_grouped': '7 - Senior & Lead', 'tenure_playbook_band': '5-10 years', 'calendar_month': '7', 'manager_changes_12m': '0', 'team_exits_12m': '0', 'direct_reports_band': '0', 'time_since_promotion_band': 'sin promo en historial'}

| Término | HR por fold | Mismo signo |
|---|---|---|
| time_since_promotion_band=(unknown) | 1.50, 1.50, 11.81, 11.93 | sí |
| time_since_promotion_band=sin promo, contratado <1 year | 0.69, 0.67, 0.43, 0.41 | sí |
| team_exits_12m=2+ | 1.62, 1.68, 1.82, 1.88 | sí |
| direct_reports_band=6+ | 0.60, 0.60, 0.53, 0.53 | sí |
| level_grouped=1 - VP & Above | 0.90, 0.86, 0.61, 0.57 | sí |
| tenure_playbook_band=10+ years | —, —, 0.61, 0.63 | no |
| level_grouped=2 - Sr Dir | 0.80, 0.78, 0.73, 0.67 | sí |
| team_exits_12m=1 | 1.33, 1.36, 1.42, 1.44 | sí |
| time_since_promotion_band=sin promo, contratado 1-3 years | 0.76, 0.77, 0.67, 0.69 | sí |
| tenure_playbook_band=2-3 years | 1.80, 1.80, 1.48, 1.42 | sí |
| tenure_playbook_band=<1 year | 1.10, 1.14, 1.36, 1.34 | sí |
| tenure_playbook_band=3-5 years | 1.69, 1.74, 1.38, 1.33 | sí |
| level_grouped=8 - Assoc & Int/Eng | 1.31, 1.33, 1.30, 1.30 | sí |
| level_grouped=5 - Sr Staff & /Mgr | 0.74, 0.75, 0.80, 0.78 | sí |
| level_grouped=3 - Princ/Directors | 0.80, 0.77, 0.85, 0.81 | sí |
| manager_changes_12m=2+ | 1.16, 1.15, 1.20, 1.22 | sí |
| direct_reports_band=1-5 | 0.81, 0.82, 0.84, 0.82 | sí |
| manager_changes_12m=1 | 1.12, 1.13, 1.18, 1.19 | sí |
| level_grouped=6 - Staff & /Mgr | 0.88, 0.88, 0.90, 0.87 | sí |
| time_since_promotion_band=promo <1 year | 0.93, 0.94, 0.87, 0.88 | sí |
| time_since_promotion_band=promo 3+ years | 1.01, 1.02, 0.86, 0.89 | no |
| time_since_promotion_band=promo 2-3 years | 0.77, 0.89, 0.87, 0.92 | sí |
| time_since_promotion_band=sin promo, contratado 3+ years | 0.97, 1.04, 1.00, 0.92 | no |
| time_since_promotion_band=promo 1-2 years | 1.09, 1.11, 1.06, 1.05 | sí |
| tenure_playbook_band=1-2 years | 1.27, 1.25, 1.09, 1.04 | sí |
| level_grouped=Misc | 1.00, 1.00, 1.00, 1.00 | sí |
| team_exits_12m=(unknown) | —, 1.00, 1.00, 1.00 | no |
| tenure_playbook_band=5-10 years | 1.28, 1.32, —, — | no |

## 7. Perfil de categorías (todas las fotos con etiqueta a seis meses)

| Variable | Categoría | Personas/foto | Salidas 6m % |
|---|---|---:|---:|
| level_grouped | 1 - VP & Above | 188 | 0.97 |
| level_grouped | 2 - Sr Dir | 759 | 1.23 |
| level_grouped | 3 - Princ/Directors | 2910 | 1.77 |
| level_grouped | 5 - Sr Staff & /Mgr | 5656 | 2.10 |
| level_grouped | 6 - Staff & /Mgr | 5995 | 2.97 |
| level_grouped | 7 - Senior & Lead | 9529 | 4.02 |
| level_grouped | 8 - Assoc & Int/Eng | 5319 | 4.33 |
| company_tenure_band | 1-3 years | 6973 | 4.19 |
| company_tenure_band | 3-7 years | 8832 | 4.22 |
| company_tenure_band | 7+ years | 10974 | 1.90 |
| company_tenure_band | <1 year | 3577 | 2.77 |
| tenure_julia_band | 1-3 years | 6973 | 4.19 |
| tenure_julia_band | 3-5 years | 5189 | 4.72 |
| tenure_julia_band | 5+ years | 14617 | 2.30 |
| tenure_julia_band | <1 year | 3577 | 2.77 |
| tenure_playbook_band | 1-2 years | 3555 | 3.54 |
| tenure_playbook_band | 10+ years | 7169 | 1.52 |
| tenure_playbook_band | 2-3 years | 3418 | 4.88 |
| tenure_playbook_band | 3-5 years | 5189 | 4.72 |
| tenure_playbook_band | 5-10 years | 7448 | 3.04 |
| tenure_playbook_band | <1 year | 3577 | 2.77 |
| manager_changes_12m | 0 | 22190 | 2.96 |
| manager_changes_12m | 1 | 6631 | 3.71 |
| manager_changes_12m | 2+ | 1535 | 4.52 |
| team_exits_12m | 0 | 22572 | 2.83 |
| team_exits_12m | 1 | 5785 | 3.97 |
| team_exits_12m | 2+ | 1998 | 5.15 |
| direct_reports_band | 0 | 23669 | 3.56 |
| direct_reports_band | 1-5 | 4649 | 2.15 |
| direct_reports_band | 6+ | 2039 | 1.47 |
| prior_experience_band | 1-3 years | 4764 | 3.92 |
| prior_experience_band | 10+ years | 4927 | 2.21 |
| prior_experience_band | 3-5 years | 4480 | 3.19 |
| prior_experience_band | 5-10 years | 6371 | 2.59 |
| prior_experience_band | <1 year | 9812 | 3.76 |
| rehire | no | 26203 | 3.06 |
| rehire | yes | 4150 | 4.09 |
| time_since_promotion_band | promo 1-2 years | 3207 | 3.73 |
| time_since_promotion_band | promo 2-3 years | 2112 | 2.84 |
| time_since_promotion_band | promo 3+ years | 1747 | 2.37 |
| time_since_promotion_band | promo <1 year | 3923 | 3.66 |
| time_since_promotion_band | sin promo en historial | 9408 | 2.92 |
| time_since_promotion_band | sin promo, contratado 1-3 years | 4787 | 3.60 |
| time_since_promotion_band | sin promo, contratado 3+ years | 1031 | 4.41 |
| time_since_promotion_band | sin promo, contratado <1 year | 4138 | 2.74 |
| time_at_level_band | (antes de la fuente) | 7406 | 4.35 |
| time_at_level_band | 1-2 years | 5852 | 3.11 |
| time_at_level_band | 2-3 years | 4192 | 3.37 |
| time_at_level_band | 3-5 years | 3641 | 2.69 |
| time_at_level_band | 5+ years | 2725 | 1.59 |
| time_at_level_band | <1 year | 6538 | 2.83 |
| manager_left_6m | no | 29895 | 3.16 |
| manager_left_6m | yes | 461 | 6.27 |
| ios_12m | (antes de la fuente) | 14020 | 3.36 |
| ios_12m | lateral u otro | 333 | 4.40 |
| ios_12m | none | 12609 | 2.90 |
| ios_12m | reorg | 3395 | 3.58 |
| layers_band | (antes de la fuente) | 10145 | 3.74 |
| layers_band | 10+ | 3757 | 4.08 |
| layers_band | 7 | 4022 | 2.32 |
| layers_band | 8 | 5356 | 2.82 |
| layers_band | 9 | 4722 | 3.31 |
| layers_band | <=6 | 2353 | 1.64 |
| work_arrangement_group | (antes de la fuente) | 19370 | 3.29 |
| work_arrangement_group | Interim Modified | 128 | 3.27 |
| work_arrangement_group | Offsite | 298 | 2.46 |
| work_arrangement_group | Onsite | 10365 | 3.04 |
| work_arrangement_group | otro o desconocido | 195 | 4.66 |

## 8. Calibración por subgrupo del v2 (último fold)

| Variable | Categoría | Personas/foto | Estimado % | Observado % | Razón |
|---|---|---:|---:|---:|---:|
| level_grouped | 1 - VP & Above | 212 | 0.89 | 2.75 | 0.32 |
| level_grouped | 2 - Sr Dir | 867 | 1.19 | 1.31 | 0.91 |
| level_grouped | 3 - Princ/Directors | 3225 | 1.67 | 1.87 | 0.90 |
| level_grouped | 5 - Sr Staff & /Mgr | 6216 | 1.96 | 2.09 | 0.94 |
| level_grouped | 6 - Staff & /Mgr | 6632 | 2.89 | 3.15 | 0.92 |
| level_grouped | 7 - Senior & Lead | 11428 | 3.84 | 3.64 | 1.05 |
| level_grouped | 8 - Assoc & Int/Eng | 5276 | 4.28 | 3.46 | 1.24 |
| tenure_playbook_band | 1-2 years | 2964 | 3.21 | 3.10 | 1.04 |
| tenure_playbook_band | 10+ years | 8268 | 1.49 | 1.53 | 0.97 |
| tenure_playbook_band | 2-3 years | 2204 | 4.49 | 4.13 | 1.09 |
| tenure_playbook_band | 3-5 years | 7455 | 4.68 | 4.20 | 1.11 |
| tenure_playbook_band | 5-10 years | 8847 | 3.12 | 3.17 | 0.99 |
| tenure_playbook_band | <1 year | 4118 | 2.48 | 2.73 | 0.91 |
| manager_changes_12m | 0 | 24742 | 2.85 | 2.80 | 1.02 |
| manager_changes_12m | 1 | 7313 | 3.63 | 3.21 | 1.13 |
| manager_changes_12m | 2+ | 1801 | 4.09 | 4.81 | 0.85 |
| team_exits_12m | 0 | 25750 | 2.68 | 2.65 | 1.01 |
| team_exits_12m | 1 | 6030 | 4.09 | 3.98 | 1.02 |
| team_exits_12m | 2+ | 2076 | 5.19 | 4.39 | 1.18 |
| direct_reports_band | 0 | 26406 | 3.48 | 3.32 | 1.05 |
| direct_reports_band | 1-5 | 5103 | 1.94 | 1.89 | 1.02 |
| direct_reports_band | 6+ | 2347 | 1.20 | 1.74 | 0.69 |
| time_since_promotion_band | promo 1-2 years | 3705 | 3.86 | 3.44 | 1.12 |
| time_since_promotion_band | promo 2-3 years | 3141 | 2.85 | 3.31 | 0.86 |
| time_since_promotion_band | promo 3+ years | 5106 | 2.33 | 2.37 | 0.98 |
| time_since_promotion_band | promo <1 year | 3942 | 3.45 | 3.40 | 1.01 |
| time_since_promotion_band | sin promo en historial | 4895 | 2.17 | 1.71 | 1.27 |
| time_since_promotion_band | sin promo, contratado 1-3 years | 4705 | 3.62 | 3.61 | 1.00 |
| time_since_promotion_band | sin promo, contratado 3+ years | 3688 | 4.50 | 3.99 | 1.13 |
| time_since_promotion_band | sin promo, contratado <1 year | 4673 | 2.45 | 2.74 | 0.89 |
