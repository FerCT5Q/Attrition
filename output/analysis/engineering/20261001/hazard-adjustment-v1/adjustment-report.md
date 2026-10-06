# Ajuste del hazard de Engineering: tendencia, recalibración e interacciones

Creado: 2026-10-02T13:21:00.251441+00:00. Frontera de conocimiento: 2026-09-07.
Mismo frame y folds que `feature-block-selection-v1` (1,699,949 exposiciones a seis meses).
Entrenamiento en memoria bajo `config\attrition_model_in_memory_training_authorization_20261001.json`; sin filas ni IDs persistidos.

## 1. Tendencia y recalibración (base + manager/equipo)

| Especificación | Parámetros | PR-AUC | Lift@10% | Lift@20% | Brier | Estimado/observado por fold |
|---|---:|---:|---:|---:|---:|---|
| linear, sin recal | 30 | 0.0494 | 1.942 | 1.698 | 0.02927 | 0.59, 0.71, 0.72, 0.79 |
| linear, recal 12m | 30 | 0.0494 | 1.928 | 1.694 | 0.02926 | 0.52, 0.78, 0.84, 0.87 |
| none, sin recal | 29 | 0.0497 | 1.935 | 1.705 | 0.02917 | 1.15, 1.09, 1.08, 1.07 |
| none, recal 12m | 29 | 0.0496 | 1.935 | 1.707 | 0.02918 | 0.77, 0.96, 1.00, 0.98 |
| frozen, sin recal | 30 | 0.0496 | 1.942 | 1.700 | 0.02922 | 0.71, 0.79, 0.78, 0.83 |
| frozen, recal 12m | 30 | 0.0496 | 1.943 | 1.700 | 0.02921 | 0.62, 0.88, 0.91, 0.93 |

Mejor calibración (menor Brier medio): **none, sin recal**.

## 2. Interacciones (regla de promoción)

| Paso | Agregada | Sobre | PR-AUC | Lift@10% | Brier | Gana PR | Gana lift | Brier no peor | Promovida |
|---:|---|---|---:|---:|---:|---:|---:|---|---|
| 0 | tenure_x_team_exits | none, sin recal | 0.0501 | 1.932 | 0.02917 | 4/4 | 2/4 | sí | no |
| 1 | tenure_x_direct_reports | none, sin recal | 0.0496 | 1.935 | 0.02917 | 2/4 | 2/4 | no | no |
| 2 | tenure_x_manager_changes | none, sin recal | 0.0501 | 1.969 | 0.02916 | 3/4 | 4/4 | sí | sí |
| 3 | level_x_team_exits | none, sin recal | 0.0498 | 1.945 | 0.02917 | 3/4 | 3/4 | sí | sí |
| 4 | level_x_tenure | none, sin recal | 0.0510 | 2.002 | 0.02916 | 4/4 | 3/4 | sí | sí |
| | **aceptada: level_x_tenure** | → none, sin recal, level_x_tenure | | | | | | | |
| 6 | tenure_x_team_exits | none, sin recal, level_x_tenure | 0.0451 | 1.695 | 0.19513 | 3/4 | 2/4 | no | no |
| 7 | tenure_x_direct_reports | none, sin recal, level_x_tenure | 0.0509 | 1.989 | 0.02916 | 0/4 | 0/4 | no | no |
| 8 | tenure_x_manager_changes | none, sin recal, level_x_tenure | 0.0513 | 2.014 | 0.02915 | 3/4 | 3/4 | sí | sí |
| 9 | level_x_team_exits | none, sin recal, level_x_tenure | 0.0509 | 1.987 | 0.02916 | 2/4 | 1/4 | no | no |
| | **aceptada: tenure_x_manager_changes** | → none, sin recal, level_x_tenure + tenure_x_manager_changes | | | | | | | |
| 11 | tenure_x_team_exits | none, sin recal, level_x_tenure + tenure_x_manager_changes | 0.0390 | 1.407 | 0.24249 | 2/4 | 1/4 | no | no |
| 12 | tenure_x_direct_reports | none, sin recal, level_x_tenure + tenure_x_manager_changes | 0.0512 | 2.020 | 0.02916 | 0/4 | 3/4 | no | no |
| 13 | level_x_team_exits | none, sin recal, level_x_tenure + tenure_x_manager_changes | 0.0512 | 2.006 | 0.02916 | 1/4 | 0/4 | no | no |

## 3. Finalistas

| Especificación | Parámetros | PR-AUC | Lift@10% | Lift@20% | Brier | Estimado/observado por fold |
|---|---:|---:|---:|---:|---:|---|
| linear, sin recal | 30 | 0.0494 | 1.942 | 1.698 | 0.02927 | 0.59, 0.71, 0.72, 0.79 |
| none, sin recal | 29 | 0.0497 | 1.935 | 1.705 | 0.02917 | 1.15, 1.09, 1.08, 1.07 |
| none, sin recal, level_x_tenure + tenure_x_manager_changes | 53 | 0.0513 | 2.014 | 1.727 | 0.02915 | 1.15, 1.10, 1.08, 1.08 |
| none, sin recal, level_x_tenure + tenure_x_manager_changes | 58 | 0.0520 | 2.010 | 1.737 | 0.02914 | 1.14, 1.10, 1.08, 1.07 |

Techo LightGBM (todas las variables, de `feature-block-selection-v1`): 0.0523 | 1.997 | 1.707 | 0.02916 | 0.79, 1.02, 0.87, 1.16

## 4. Parsimonia contra el techo (2% relativo)

| Especificación | PR-AUC / mejor | Lift@10% / mejor | Dentro de 2% |
|---|---:|---:|---|
| linear, sin recal | 0.945 | 0.964 | no |
| none, sin recal | 0.950 | 0.961 | no |
| none, sin recal, level_x_tenure + tenure_x_manager_changes | 0.980 | 1.000 | sí |
| none, sin recal, level_x_tenure + tenure_x_manager_changes | 0.994 | 0.998 | sí |

**Modelo final: none, sin recal, level_x_tenure + tenure_x_manager_changes.** Promoción frente al elegido original: {'pr_auc_wins': 4, 'lift_wins': 3, 'brier_not_worse': True, 'promoted': True}.

## 5. Modelo final por fold

| Fold | L2 | Recal. (log) | PR-AUC | Lift@10% | Brier | Estimado % | Observado % |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 10.0 | 0.000 | 0.0535 | 2.150 | 0.02918 | 3.48 | 3.03 |
| 2 | 0.0 | 0.000 | 0.0525 | 2.097 | 0.02895 | 3.31 | 3.01 |
| 3 | 0.0 | 0.000 | 0.0555 | 2.142 | 0.02949 | 3.33 | 3.07 |
| 4 | 0.0 | 0.000 | 0.0435 | 1.667 | 0.02900 | 3.24 | 3.00 |

## 6. Hazard ratios del final por fold

Referencias: {'level_grouped': '7 - Senior & Lead', 'company_tenure_band': '7+ years', 'calendar_month': '7', 'manager_changes_12m': '0', 'team_exits_12m': '0', 'direct_reports_band': '0', 'level_x_tenure': 'ref', 'tenure_x_manager_changes': 'ref'}

| Término | HR por fold | Mismo signo |
|---|---|---|
| level_x_tenure=8 - Assoc & Int/Eng | 3-7 years | 1.48, 2.91, 3.34, 4.48 | sí |
| level_grouped=1 - VP & Above | 0.90, 0.33, 0.30, 0.28 | sí |
| level_x_tenure=8 - Assoc & Int/Eng | 1-3 years | 0.99, 1.67, 1.90, 2.49 | no |
| level_x_tenure=1 - VP & Above | 3-7 years | 1.00, 2.96, 2.79, 2.28 | sí |
| level_grouped=8 - Assoc & Int/Eng | 1.20, 0.70, 0.60, 0.45 | no |
| level_grouped=2 - Sr Dir | 0.82, 0.52, 0.53, 0.48 | sí |
| tenure_x_manager_changes=<1 year | 2+ | 0.98, 0.56, 0.55, 0.50 | sí |
| team_exits_12m=2+ | 1.61, 1.79, 1.83, 1.88 | sí |
| direct_reports_band=6+ | 0.61, 0.53, 0.54, 0.55 | sí |
| manager_changes_12m=2+ | 1.14, 1.68, 1.68, 1.77 | sí |
| level_x_tenure=8 - Assoc & Int/Eng | <1 year | 0.82, 1.23, 1.38, 1.76 | no |
| level_grouped=3 - Princ/Directors | 0.81, 0.59, 0.60, 0.57 | sí |
| level_x_tenure=6 - Staff & /Mgr | <1 year | 1.13, 1.72, 1.72, 1.75 | sí |
| tenure_x_manager_changes=1-3 years | 2+ | 0.99, 0.62, 0.63, 0.58 | sí |
| level_grouped=5 - Sr Staff & /Mgr | 0.77, 0.60, 0.62, 0.60 | sí |
| tenure_x_manager_changes=<1 year | 1 | 0.87, 0.63, 0.65, 0.64 | sí |
| tenure_x_manager_changes=3-7 years | 2+ | 1.01, 0.66, 0.68, 0.66 | no |
| manager_changes_12m=1 | 1.11, 1.41, 1.47, 1.50 | sí |
| level_x_tenure=3 - Princ/Directors | 1-3 years | 1.03, 1.39, 1.35, 1.49 | sí |
| tenure_x_manager_changes=1-3 years | 1 | 0.97, 0.72, 0.70, 0.68 | sí |
| level_x_tenure=6 - Staff & /Mgr | 1-3 years | 1.08, 1.45, 1.42, 1.47 | sí |
| level_grouped=6 - Staff & /Mgr | 0.92, 0.71, 0.71, 0.69 | sí |
| level_x_tenure=3 - Princ/Directors | <1 year | 0.99, 1.18, 1.36, 1.46 | no |
| team_exits_12m=1 | 1.33, 1.40, 1.43, 1.44 | sí |
| level_x_tenure=5 - Sr Staff & /Mgr | 1-3 years | 1.10, 1.54, 1.41, 1.42 | sí |
| level_x_tenure=5 - Sr Staff & /Mgr | <1 year | 1.02, 1.48, 1.39, 1.41 | sí |
| level_x_tenure=3 - Princ/Directors | 3-7 years | 1.03, 1.39, 1.41, 1.40 | sí |
| company_tenure_band=3-7 years | 1.57, 1.40, 1.42, 1.36 | sí |
| company_tenure_band=1-3 years | 1.44, 1.25, 1.30, 1.26 | sí |
| tenure_x_manager_changes=3-7 years | 1 | 1.03, 0.79, 0.79, 0.79 | no |
| level_x_tenure=6 - Staff & /Mgr | 3-7 years | 0.89, 1.14, 1.17, 1.21 | no |
| level_x_tenure=5 - Sr Staff & /Mgr | 3-7 years | 0.90, 1.12, 1.15, 1.18 | no |
| direct_reports_band=1-5 | 0.83, 0.85, 0.86, 0.85 | sí |
| level_x_tenure=2 - Sr Dir | 1-3 years | 1.00, 1.38, 1.20, 1.16 | sí |
| company_tenure_band=<1 year | 0.96, 0.86, 0.91, 0.87 | sí |
| level_x_tenure=2 - Sr Dir | 3-7 years | 0.99, 1.07, 0.94, 0.89 | no |
| level_grouped=Misc | 1.00, 0.00, 0.00, 0.00 | sí |
| level_x_tenure=1 - VP & Above | 1-3 years | 0.99, 0.00, 0.00, 0.00 | sí |
| level_x_tenure=1 - VP & Above | <1 year | 1.00, 0.00, 0.00, 0.00 | sí |
| level_x_tenure=2 - Sr Dir | <1 year | 0.99, 0.00, 0.00, 0.00 | sí |
| team_exits_12m=(unknown) | —, 0.00, 0.00, 0.00 | no |

## 7. Grupos (árbol profundidad ≤ 3, hojas ≥ 300 personas), foto 2026-07-26

Riesgo medio estimado a seis meses: 2.90%. R² del árbol: 0.64.

| Grupo | Personas | % población | Riesgo 6m % | Lift | Último fold: estimado % | observado % |
|---|---:|---:|---:|---:|---:|---:|
| company_tenure_band ≠ 7+ years y team_exits_12m ≠ 0 y company_tenure_band ≠ <1 year | 4695 | 12.6 | 5.27 | 1.82 | 5.90 | 4.67 |
| company_tenure_band = 7+ years y level_grouped = 7 - Senior & Lead y team_exits_12m ≠ 0 | 371 | 1.0 | 4.45 | 1.54 | 4.80 | 3.69 |
| company_tenure_band ≠ 7+ years y team_exits_12m = 0 y company_tenure_band ≠ <1 year | 13191 | 35.4 | 3.43 | 1.18 | 3.85 | 3.50 |
| company_tenure_band ≠ 7+ years y team_exits_12m ≠ 0 y company_tenure_band = <1 year | 1645 | 4.4 | 3.18 | 1.10 | 3.41 | 3.35 |
| company_tenure_band = 7+ years y level_grouped = 7 - Senior & Lead y team_exits_12m = 0 | 1220 | 3.3 | 2.85 | 0.98 | 3.12 | 3.56 |
| company_tenure_band ≠ 7+ years y team_exits_12m = 0 y company_tenure_band = <1 year | 3669 | 9.9 | 1.99 | 0.69 | 2.14 | 2.47 |
| company_tenure_band = 7+ years y level_grouped ≠ 7 - Senior & Lead y direct_reports_band = 0 | 6301 | 16.9 | 1.96 | 0.68 | 2.09 | 2.19 |
| company_tenure_band = 7+ years y level_grouped ≠ 7 - Senior & Lead y direct_reports_band ≠ 0 | 6129 | 16.5 | 1.29 | 0.45 | 1.45 | 1.50 |

## 8. Calibración por subgrupo no protegido (último fold)

| Variable | Categoría | Personas/foto | Estimado % | Observado % | Razón |
|---|---|---:|---:|---:|---:|
| level_grouped | 1 - VP & Above | 212 | 0.66 | 2.75 | 0.24 |
| level_grouped | 2 - Sr Dir | 867 | 1.17 | 1.31 | 0.90 |
| level_grouped | 3 - Princ/Directors | 3225 | 1.73 | 1.87 | 0.93 |
| level_grouped | 5 - Sr Staff & /Mgr | 6216 | 2.00 | 2.09 | 0.95 |
| level_grouped | 6 - Staff & /Mgr | 6632 | 2.87 | 3.15 | 0.91 |
| level_grouped | 7 - Senior & Lead | 11428 | 4.03 | 3.64 | 1.11 |
| level_grouped | 8 - Assoc & Int/Eng | 5276 | 4.81 | 3.46 | 1.39 |
| company_tenure_band | 1-3 years | 5168 | 4.17 | 3.54 | 1.18 |
| company_tenure_band | 3-7 years | 11781 | 4.50 | 3.93 | 1.14 |
| company_tenure_band | 7+ years | 12789 | 1.93 | 2.00 | 0.96 |
| company_tenure_band | <1 year | 4118 | 2.51 | 2.73 | 0.92 |
| manager_changes_12m | 0 | 24742 | 2.98 | 2.80 | 1.06 |
| manager_changes_12m | 1 | 7313 | 3.85 | 3.21 | 1.20 |
| manager_changes_12m | 2+ | 1801 | 4.31 | 4.81 | 0.90 |
| team_exits_12m | 0 | 25750 | 2.80 | 2.65 | 1.06 |
| team_exits_12m | 1 | 6030 | 4.31 | 3.98 | 1.08 |
| team_exits_12m | 2+ | 2076 | 5.52 | 4.39 | 1.26 |
| direct_reports_band | 0 | 26406 | 3.67 | 3.32 | 1.10 |
| direct_reports_band | 1-5 | 5103 | 1.95 | 1.89 | 1.03 |
| direct_reports_band | 6+ | 2347 | 1.20 | 1.74 | 0.69 |
