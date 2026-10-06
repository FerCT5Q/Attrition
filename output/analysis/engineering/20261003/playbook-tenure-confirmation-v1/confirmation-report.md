# Confirmación: cortes de antigüedad del playbook y variables de carrera — Engineering

Creado: 2026-10-03T17:45:05.180142+00:00. Frontera de conocimiento: 2026-09-07.
1,699,949 exposiciones a seis meses y 54,452 salidas; mismos 4 folds.
Entrenamiento en memoria bajo `config\attrition_model_in_memory_training_authorization_20261001.json`; sin filas ni IDs persistidos.

Reglas declaradas antes de correr:

- A: vigente con cortes del playbook en lugar de los heredados; promovido si gana >= 3 de 4 folds en PR-AUC y lift@10% sin peor Brier medio frente al vigente
- B: campeón después de A + tiempo desde la última promoción + recontratación (juntas); misma regla frente a ese campeón

## Métricas

| Modelo | Parámetros | PR-AUC | Lift@10% | Lift@20% | Brier | Estimado/observado por fold |
|---|---:|---:|---:|---:|---:|---|
| Vigente (cortes <1, 1-3, 3-7, 7+) | 53 | 0.0512 | 2.014 | 1.727 | 0.02915 | 1.15, 1.10, 1.08, 1.08 |
| A: vigente con cortes del playbook | 72 | 0.0520 | 2.081 | 1.777 | 0.02915 | 1.16, 1.14, 1.11, 1.08 |
| B: A + promoción + recontratación | 82 | 0.0537 | 2.104 | 1.807 | 0.02912 | 1.11, 1.11, 1.06, 1.04 |

## Decisiones

- A frente al vigente: PR-AUC 3/4, lift@10% 4/4, Brier no peor sí → **promovido**
- Campeón después de A: **A: vigente con cortes del playbook**.
- B frente al campeón después de A: PR-AUC 3/4, lift@10% 3/4, Brier no peor sí → **promovido**
- B frente al vigente (informativo): PR-AUC 4/4, lift@10% 4/4, Brier no peor sí → **promovido**
- **Modelo final: B: A + promoción + recontratación.**

## Por fold

| Fold | PR-AUC vigente | PR-AUC A | PR-AUC B | Lift@10% vigente | Lift@10% A | Lift@10% B | Brier vigente | Brier A | Brier B |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.0535 | 0.0558 | 0.0599 | 2.153 | 2.267 | 2.336 | 0.02918 | 0.02914 | 0.02911 |
| 2 | 0.0523 | 0.0531 | 0.0531 | 2.093 | 2.184 | 2.132 | 0.02895 | 0.02895 | 0.02894 |
| 3 | 0.0555 | 0.0552 | 0.0569 | 2.142 | 2.152 | 2.163 | 0.02949 | 0.02951 | 0.02948 |
| 4 | 0.0434 | 0.0440 | 0.0449 | 1.667 | 1.722 | 1.787 | 0.02900 | 0.02900 | 0.02897 |

## Quitar una variable de carrera de B (informativo)

| Modelo | Parámetros | PR-AUC | Lift@10% | Lift@20% | Brier | Estimado/observado por fold |
|---|---:|---:|---:|---:|---:|---|
| sin time_since_promotion_band | 74 | 0.0522 | 2.082 | 1.778 | 0.02915 | 1.16, 1.14, 1.11, 1.08 |
| sin rehire | 80 | 0.0530 | 2.099 | 1.796 | 0.02913 | 1.11, 1.11, 1.06, 1.03 |

## Grupos de A (árbol profundidad ≤ 3, hojas ≥ 300 personas), foto 2026-07-26

Riesgo medio estimado a seis meses: 2.88%. R² del árbol: 0.56.

| Grupo | Personas | % población | Riesgo 6m % | Lift | Último fold: estimado % | observado % |
|---|---:|---:|---:|---:|---:|---:|
| tenure_playbook_band ≠ 10+ years y team_exits_12m ≠ 0 y tenure_playbook_band = 3-5 years | 1854 | 5.0 | 5.81 | 2.02 | 6.58 | 5.37 |
| tenure_playbook_band ≠ 10+ years y team_exits_12m ≠ 0 y tenure_playbook_band ≠ 3-5 years | 5636 | 15.1 | 4.08 | 1.42 | 4.50 | 4.07 |
| tenure_playbook_band ≠ 10+ years y team_exits_12m = 0 y tenure_playbook_band = 3-5 years | 5294 | 14.2 | 3.83 | 1.33 | 4.36 | 3.79 |
| tenure_playbook_band ≠ 10+ years y team_exits_12m = 0 y tenure_playbook_band ≠ 3-5 years | 15557 | 41.8 | 2.63 | 0.91 | 2.89 | 2.84 |
| tenure_playbook_band = 10+ years y direct_reports_band = 0 y team_exits_12m ≠ 0 | 696 | 1.9 | 2.41 | 0.83 | 2.60 | 3.18 |
| tenure_playbook_band = 10+ years y direct_reports_band = 0 y team_exits_12m = 0 | 3359 | 9.0 | 1.57 | 0.55 | 1.67 | 1.82 |
| tenure_playbook_band = 10+ years y direct_reports_band ≠ 0 y team_exits_12m ≠ 0 | 871 | 2.3 | 1.55 | 0.54 | 1.79 | 1.51 |
| tenure_playbook_band = 10+ years y direct_reports_band ≠ 0 y team_exits_12m = 0 | 3954 | 10.6 | 1.01 | 0.35 | 1.13 | 1.03 |

### Hazard ratios de A por fold

Referencias: {'level_grouped': '7 - Senior & Lead', 'tenure_playbook_band': '5-10 years', 'calendar_month': '7', 'manager_changes_12m': '0', 'team_exits_12m': '0', 'direct_reports_band': '0', 'level_x_tenure': 'ref', 'tenure_x_manager_changes': 'ref'}

| Término | HR por fold | Mismo signo |
|---|---|---|
| level_grouped=1 - VP & Above | 0.90, 0.66, 0.65, 0.43 | sí |
| level_x_tenure=8 - Assoc & Int/Eng | 10+ years | 0.99, 0.90, 0.90, 0.44 | sí |
| level_x_tenure=2 - Sr Dir | 1-2 years | 0.98, 0.88, 0.87, 0.51 | sí |
| team_exits_12m=2+ | 1.61, 1.78, 1.81, 1.87 | sí |
| level_grouped=2 - Sr Dir | 0.82, 0.66, 0.66, 0.54 | sí |
| direct_reports_band=6+ | 0.61, 0.53, 0.54, 0.55 | sí |
| level_x_tenure=2 - Sr Dir | <1 year | 0.99, 0.92, 0.91, 0.56 | sí |
| level_x_tenure=6 - Staff & /Mgr | 1-2 years | 1.17, 1.59, 1.55, 1.74 | sí |
| level_x_tenure=2 - Sr Dir | 3-5 years | 0.99, 0.91, 0.87, 0.58 | sí |
| level_x_tenure=6 - Staff & /Mgr | <1 year | 1.15, 1.55, 1.52, 1.70 | sí |
| level_x_tenure=8 - Assoc & Int/Eng | <1 year | 0.79, 0.69, 0.67, 0.60 | sí |
| level_x_tenure=1 - VP & Above | 3-5 years | 1.01, 1.10, 1.08, 1.62 | sí |
| level_x_tenure=5 - Sr Staff & /Mgr | 1-2 years | 1.09, 1.42, 1.37, 1.59 | sí |
| level_x_tenure=8 - Assoc & Int/Eng | 3-5 years | 1.42, 1.61, 1.58, 1.55 | sí |
| tenure_x_manager_changes=1-2 years | 1 | 0.89, 0.75, 0.71, 0.65 | sí |
| tenure_x_manager_changes=1-2 years | 2+ | 0.96, 0.76, 0.74, 0.65 | sí |
| tenure_x_manager_changes=<1 year | 2+ | 0.97, 0.83, 0.80, 0.66 | sí |
| level_grouped=5 - Sr Staff & /Mgr | 0.77, 0.69, 0.73, 0.67 | sí |
| tenure_x_manager_changes=<1 year | 1 | 0.85, 0.72, 0.72, 0.68 | sí |
| level_x_tenure=2 - Sr Dir | 2-3 years | 1.02, 1.15, 1.12, 1.47 | sí |
| tenure_x_manager_changes=10+ years | 2+ | 1.08, 1.36, 1.41, 1.45 | sí |
| team_exits_12m=1 | 1.32, 1.38, 1.42, 1.44 | sí |
| level_grouped=6 - Staff & /Mgr | 0.87, 0.75, 0.77, 0.70 | sí |
| manager_changes_12m=1 | 1.13, 1.28, 1.34, 1.42 | sí |
| tenure_playbook_band=<1 year | 0.89, 0.99, 0.76, 0.71 | sí |
| level_grouped=3 - Princ/Directors | 0.85, 0.79, 0.82, 0.72 | sí |
| level_x_tenure=1 - VP & Above | 10+ years | 0.91, 0.73, 0.75, 0.72 | sí |
| level_x_tenure=1 - VP & Above | 2-3 years | 1.00, 0.95, 0.94, 0.73 | sí |
| manager_changes_12m=2+ | 1.13, 1.23, 1.24, 1.37 | sí |
| tenure_playbook_band=10+ years | —, —, 0.63, 0.73 | no |
| level_x_tenure=6 - Staff & /Mgr | 3-5 years | 1.02, 1.21, 1.20, 1.33 | sí |
| level_x_tenure=3 - Princ/Directors | 3-5 years | 1.04, 1.22, 1.24, 1.33 | sí |
| level_grouped=8 - Assoc & Int/Eng | 1.22, 1.26, 1.24, 1.32 | sí |
| level_x_tenure=3 - Princ/Directors | 2-3 years | 1.02, 1.10, 1.05, 1.28 | sí |
| level_x_tenure=1 - VP & Above | 1-2 years | 0.99, 0.96, 0.96, 0.79 | sí |
| level_x_tenure=1 - VP & Above | <1 year | 1.00, 0.97, 0.96, 0.79 | sí |
| level_x_tenure=6 - Staff & /Mgr | 2-3 years | 1.03, 1.19, 1.13, 1.26 | sí |
| level_x_tenure=3 - Princ/Directors | 10+ years | 0.78, 0.77, 0.87, 0.79 | sí |
| level_x_tenure=5 - Sr Staff & /Mgr | <1 year | 1.02, 1.22, 1.13, 1.26 | sí |
| tenure_x_manager_changes=3-5 years | 1 | 1.00, 0.85, 0.83, 0.80 | no |
| level_x_tenure=8 - Assoc & Int/Eng | 1-2 years | 0.93, 0.92, 0.88, 0.81 | sí |
| tenure_x_manager_changes=3-5 years | 2+ | 1.03, 0.89, 0.89, 0.82 | no |
| tenure_x_manager_changes=2-3 years | 1 | 1.10, 0.93, 0.89, 0.82 | no |
| tenure_playbook_band=1-2 years | 1.09, 1.15, 0.88, 0.85 | no |
| direct_reports_band=1-5 | 0.84, 0.85, 0.85, 0.85 | sí |
| level_x_tenure=5 - Sr Staff & /Mgr | 3-5 years | 0.99, 1.11, 1.09, 1.17 | no |
| tenure_playbook_band=2-3 years | 1.51, 1.67, 1.22, 1.16 | sí |
| tenure_x_manager_changes=2-3 years | 2+ | 1.04, 0.98, 1.00, 0.87 | no |
| level_x_tenure=3 - Princ/Directors | <1 year | 0.98, 0.93, 1.00, 1.14 | no |
| tenure_playbook_band=3-5 years | 1.50, 1.66, 1.24, 1.13 | sí |
| level_x_tenure=5 - Sr Staff & /Mgr | 10+ years | 0.82, 0.89, 0.96, 0.89 | sí |
| level_x_tenure=5 - Sr Staff & /Mgr | 2-3 years | 1.05, 1.22, 1.03, 1.10 | sí |
| level_x_tenure=3 - Princ/Directors | 1-2 years | 1.01, 1.00, 0.97, 1.09 | no |
| level_x_tenure=8 - Assoc & Int/Eng | 2-3 years | 1.09, 1.02, 1.02, 0.96 | no |
| level_x_tenure=2 - Sr Dir | 10+ years | 0.85, 0.90, 1.04, 0.96 | no |
| level_x_tenure=6 - Staff & /Mgr | 10+ years | 0.84, 0.95, 1.07, 0.97 | no |
| team_exits_12m=(unknown) | —, 1.00, 1.00, 0.99 | no |
| level_grouped=Misc | 1.00, 1.00, 1.00, 0.99 | sí |
| level_x_tenure=Misc | 10+ years | 1.00, 1.00, 1.00, 0.99 | sí |
| tenure_x_manager_changes=10+ years | 1 | 0.99, 1.05, 1.06, 1.01 | no |
| tenure_playbook_band=5-10 years | 1.18, 1.40, —, — | no |

### Calibración por subgrupo de A (último fold)

| Variable | Categoría | Personas/foto | Estimado % | Observado % | Razón |
|---|---|---:|---:|---:|---:|
| level_grouped | 1 - VP & Above | 212 | 0.69 | 2.75 | 0.25 |
| level_grouped | 2 - Sr Dir | 867 | 1.15 | 1.31 | 0.88 |
| level_grouped | 3 - Princ/Directors | 3225 | 1.71 | 1.87 | 0.92 |
| level_grouped | 5 - Sr Staff & /Mgr | 6216 | 2.00 | 2.09 | 0.95 |
| level_grouped | 6 - Staff & /Mgr | 6632 | 2.92 | 3.15 | 0.93 |
| level_grouped | 7 - Senior & Lead | 11428 | 4.01 | 3.64 | 1.10 |
| level_grouped | 8 - Assoc & Int/Eng | 5276 | 4.77 | 3.46 | 1.38 |
| tenure_playbook_band | 1-2 years | 2964 | 3.35 | 3.10 | 1.08 |
| tenure_playbook_band | 10+ years | 8268 | 1.50 | 1.53 | 0.98 |
| tenure_playbook_band | 2-3 years | 2204 | 4.96 | 4.13 | 1.20 |
| tenure_playbook_band | 3-5 years | 7455 | 4.93 | 4.20 | 1.17 |
| tenure_playbook_band | 5-10 years | 8847 | 3.27 | 3.17 | 1.03 |
| tenure_playbook_band | <1 year | 4118 | 2.52 | 2.73 | 0.92 |
| manager_changes_12m | 0 | 24742 | 2.98 | 2.80 | 1.06 |
| manager_changes_12m | 1 | 7313 | 3.83 | 3.21 | 1.19 |
| manager_changes_12m | 2+ | 1801 | 4.24 | 4.81 | 0.88 |
| team_exits_12m | 0 | 25750 | 2.80 | 2.65 | 1.05 |
| team_exits_12m | 1 | 6030 | 4.30 | 3.98 | 1.08 |
| team_exits_12m | 2+ | 2076 | 5.51 | 4.39 | 1.25 |
| direct_reports_band | 0 | 26406 | 3.65 | 3.32 | 1.10 |
| direct_reports_band | 1-5 | 5103 | 1.98 | 1.89 | 1.04 |
| direct_reports_band | 6+ | 2347 | 1.19 | 1.74 | 0.69 |

## Grupos de modelo final (árbol profundidad ≤ 3, hojas ≥ 300 personas), foto 2026-07-26

Riesgo medio estimado a seis meses: 2.79%. R² del árbol: 0.53.

| Grupo | Personas | % población | Riesgo 6m % | Lift | Último fold: estimado % | observado % |
|---|---:|---:|---:|---:|---:|---:|
| tenure_playbook_band ≠ 10+ years y team_exits_12m ≠ 0 y tenure_playbook_band = 3-5 years | 1854 | 5.0 | 5.64 | 2.02 | 6.28 | 5.37 |
| tenure_playbook_band ≠ 10+ years y team_exits_12m ≠ 0 y tenure_playbook_band ≠ 3-5 years | 5636 | 15.1 | 3.92 | 1.40 | 4.28 | 4.07 |
| tenure_playbook_band ≠ 10+ years y team_exits_12m = 0 y tenure_playbook_band = 3-5 years | 5294 | 14.2 | 3.71 | 1.33 | 4.18 | 3.79 |
| tenure_playbook_band ≠ 10+ years y team_exits_12m = 0 y tenure_playbook_band ≠ 3-5 years | 15557 | 41.8 | 2.56 | 0.92 | 2.79 | 2.84 |
| tenure_playbook_band = 10+ years y direct_reports_band = 0 y team_exits_12m ≠ 0 | 696 | 1.9 | 2.33 | 0.83 | 2.52 | 3.18 |
| tenure_playbook_band = 10+ years y direct_reports_band = 0 y team_exits_12m = 0 | 3359 | 9.0 | 1.54 | 0.55 | 1.63 | 1.82 |
| tenure_playbook_band = 10+ years y direct_reports_band ≠ 0 y team_exits_12m ≠ 0 | 871 | 2.3 | 1.54 | 0.55 | 1.73 | 1.51 |
| tenure_playbook_band = 10+ years y direct_reports_band ≠ 0 y team_exits_12m = 0 | 3954 | 10.6 | 1.00 | 0.36 | 1.11 | 1.03 |

### Hazard ratios de modelo final por fold

Referencias: {'level_grouped': '7 - Senior & Lead', 'tenure_playbook_band': '5-10 years', 'calendar_month': '7', 'manager_changes_12m': '0', 'team_exits_12m': '0', 'direct_reports_band': '0', 'time_since_promotion_band': 'sin promo en historial', 'rehire': 'no', 'level_x_tenure': 'ref', 'tenure_x_manager_changes': 'ref'}

| Término | HR por fold | Mismo signo |
|---|---|---|
| time_since_promotion_band=(unknown) | 1.48, 1.48, 4.36, 4.40 | sí |
| rehire=(unknown) | 1.48, 1.48, 4.36, 4.40 | sí |
| time_since_promotion_band=sin promo, contratado <1 year | 0.69, 0.66, 0.42, 0.41 | sí |
| team_exits_12m=2+ | 1.61, 1.67, 1.80, 1.86 | sí |
| direct_reports_band=6+ | 0.61, 0.61, 0.54, 0.55 | sí |
| tenure_playbook_band=<1 year | 1.11, 1.17, 1.69, 1.69 | sí |
| level_x_tenure=8 - Assoc & Int/Eng | 3-5 years | 1.40, 1.50, 1.58, 1.64 | sí |
| level_grouped=1 - VP & Above | 0.89, 0.86, 0.66, 0.61 | sí |
| level_grouped=2 - Sr Dir | 0.81, 0.78, 0.65, 0.61 | sí |
| level_x_tenure=6 - Staff & /Mgr | 1-2 years | 1.18, 1.21, 1.52, 1.56 | sí |
| level_x_tenure=8 - Assoc & Int/Eng | <1 year | 0.82, 0.79, 0.68, 0.64 | sí |
| time_since_promotion_band=sin promo, contratado 1-3 years | 0.73, 0.74, 0.65, 0.66 | sí |
| level_x_tenure=6 - Staff & /Mgr | <1 year | 1.18, 1.21, 1.47, 1.51 | sí |
| tenure_playbook_band=10+ years | —, —, 0.62, 0.67 | no |
| tenure_x_manager_changes=10+ years | 2+ | 1.07, 1.10, 1.41, 1.45 | sí |
| level_x_tenure=5 - Sr Staff & /Mgr | 1-2 years | 1.11, 1.12, 1.39, 1.43 | sí |
| team_exits_12m=1 | 1.32, 1.35, 1.41, 1.43 | sí |
| level_grouped=5 - Sr Staff & /Mgr | 0.76, 0.77, 0.73, 0.71 | sí |
| tenure_x_manager_changes=<1 year | 1 | 0.87, 0.86, 0.73, 0.71 | sí |
| tenure_x_manager_changes=1-2 years | 1 | 0.91, 0.89, 0.74, 0.71 | sí |
| tenure_playbook_band=2-3 years | 1.51, 1.53, 1.43, 1.40 | sí |
| level_x_tenure=1 - VP & Above | 10+ years | 0.90, 0.87, 0.75, 0.72 | sí |
| manager_changes_12m=1 | 1.14, 1.16, 1.34, 1.39 | sí |
| level_grouped=6 - Staff & /Mgr | 0.86, 0.85, 0.77, 0.74 | sí |
| tenure_x_manager_changes=<1 year | 2+ | 0.98, 0.97, 0.80, 0.75 | sí |
| tenure_x_manager_changes=1-2 years | 2+ | 0.98, 0.93, 0.78, 0.75 | sí |
| manager_changes_12m=2+ | 1.13, 1.14, 1.25, 1.31 | sí |
| level_grouped=3 - Princ/Directors | 0.84, 0.81, 0.83, 0.78 | sí |
| level_x_tenure=6 - Staff & /Mgr | 3-5 years | 1.03, 1.06, 1.23, 1.29 | sí |
| level_grouped=8 - Assoc & Int/Eng | 1.23, 1.23, 1.23, 1.24 | sí |
| level_x_tenure=3 - Princ/Directors | 3-5 years | 1.04, 1.05, 1.25, 1.23 | sí |
| level_x_tenure=3 - Princ/Directors | 2-3 years | 1.03, 1.04, 1.12, 1.23 | sí |
| level_x_tenure=3 - Princ/Directors | 10+ years | 0.75, 0.74, 0.87, 0.83 | sí |
| tenure_x_manager_changes=3-5 years | 1 | 1.00, 0.96, 0.83, 0.83 | sí |
| level_x_tenure=6 - Staff & /Mgr | 2-3 years | 1.03, 1.05, 1.14, 1.20 | sí |
| tenure_playbook_band=1-2 years | 1.22, 1.20, 1.21, 1.18 | sí |
| direct_reports_band=1-5 | 0.83, 0.83, 0.86, 0.85 | sí |
| level_x_tenure=2 - Sr Dir | 3-5 years | 0.99, 0.98, 0.88, 0.85 | sí |
| level_x_tenure=5 - Sr Staff & /Mgr | <1 year | 1.04, 1.06, 1.15, 1.18 | sí |
| rehire=yes | 1.07, 1.10, 1.17, 1.16 | sí |
| tenure_x_manager_changes=2-3 years | 1 | 1.10, 1.05, 0.91, 0.86 | no |
| level_x_tenure=2 - Sr Dir | 1-2 years | 0.98, 0.98, 0.86, 0.86 | sí |
| tenure_playbook_band=3-5 years | 1.39, 1.39, 1.21, 1.15 | sí |
| tenure_x_manager_changes=3-5 years | 2+ | 1.03, 0.99, 0.90, 0.87 | no |
| level_x_tenure=8 - Assoc & Int/Eng | 10+ years | 0.99, 0.99, 0.91, 0.88 | sí |
| time_since_promotion_band=promo 3+ years | 1.01, 1.03, 0.86, 0.88 | no |
| level_x_tenure=8 - Assoc & Int/Eng | 1-2 years | 0.94, 0.94, 0.91, 0.88 | sí |
| level_x_tenure=5 - Sr Staff & /Mgr | 3-5 years | 0.99, 1.01, 1.11, 1.13 | no |
| time_since_promotion_band=promo <1 year | 0.93, 0.94, 0.89, 0.89 | sí |
| level_x_tenure=2 - Sr Dir | <1 year | 0.99, 0.99, 0.90, 0.89 | sí |
| time_since_promotion_band=sin promo, contratado 3+ years | 0.96, 1.01, 0.97, 0.90 | no |
| level_x_tenure=2 - Sr Dir | 2-3 years | 1.02, 1.01, 1.11, 1.09 | sí |
| level_x_tenure=5 - Sr Staff & /Mgr | 10+ years | 0.78, 0.75, 0.96, 0.93 | sí |
| level_x_tenure=5 - Sr Staff & /Mgr | 2-3 years | 1.06, 1.06, 1.06, 1.07 | sí |
| time_since_promotion_band=promo 2-3 years | 0.78, 0.91, 0.89, 0.93 | sí |
| time_since_promotion_band=promo 1-2 years | 1.09, 1.12, 1.08, 1.06 | sí |
| level_x_tenure=1 - VP & Above | 3-5 years | 1.01, 1.01, 1.08, 1.06 | sí |
| level_x_tenure=2 - Sr Dir | 10+ years | 0.83, 0.84, 1.05, 0.94 | no |
| tenure_x_manager_changes=2-3 years | 2+ | 1.05, 1.05, 1.03, 0.95 | no |
| level_x_tenure=3 - Princ/Directors | <1 year | 0.99, 0.99, 1.01, 1.05 | no |
| level_x_tenure=1 - VP & Above | 2-3 years | 1.00, 0.99, 0.95, 0.95 | sí |
| level_x_tenure=1 - VP & Above | <1 year | 1.00, 1.00, 0.96, 0.96 | sí |
| level_x_tenure=1 - VP & Above | 1-2 years | 1.00, 0.99, 0.96, 0.96 | sí |
| level_x_tenure=3 - Princ/Directors | 1-2 years | 1.02, 1.00, 0.99, 1.03 | no |
| tenure_x_manager_changes=10+ years | 1 | 0.98, 1.00, 1.06, 1.02 | no |
| level_x_tenure=8 - Assoc & Int/Eng | 2-3 years | 1.09, 1.07, 1.03, 1.01 | sí |
| level_x_tenure=6 - Staff & /Mgr | 10+ years | 0.81, 0.81, 1.06, 1.00 | no |
| team_exits_12m=(unknown) | —, 1.00, 1.00, 1.00 | no |
| level_grouped=Misc | 1.00, 1.00, 1.00, 1.00 | sí |
| level_x_tenure=Misc | 10+ years | 1.00, 1.00, 1.00, 1.00 | sí |
| tenure_playbook_band=5-10 years | 1.11, 1.12, —, — | no |

### Calibración por subgrupo de modelo final (último fold)

| Variable | Categoría | Personas/foto | Estimado % | Observado % | Razón |
|---|---|---:|---:|---:|---:|
| level_grouped | 1 - VP & Above | 212 | 0.84 | 2.75 | 0.31 |
| level_grouped | 2 - Sr Dir | 867 | 1.18 | 1.31 | 0.90 |
| level_grouped | 3 - Princ/Directors | 3225 | 1.66 | 1.87 | 0.89 |
| level_grouped | 5 - Sr Staff & /Mgr | 6216 | 1.93 | 2.09 | 0.93 |
| level_grouped | 6 - Staff & /Mgr | 6632 | 2.84 | 3.15 | 0.90 |
| level_grouped | 7 - Senior & Lead | 11428 | 3.83 | 3.64 | 1.05 |
| level_grouped | 8 - Assoc & Int/Eng | 5276 | 4.54 | 3.46 | 1.31 |
| tenure_playbook_band | 1-2 years | 2964 | 3.17 | 3.10 | 1.02 |
| tenure_playbook_band | 10+ years | 8268 | 1.47 | 1.53 | 0.96 |
| tenure_playbook_band | 2-3 years | 2204 | 4.54 | 4.13 | 1.10 |
| tenure_playbook_band | 3-5 years | 7455 | 4.72 | 4.20 | 1.12 |
| tenure_playbook_band | 5-10 years | 8847 | 3.17 | 3.17 | 1.00 |
| tenure_playbook_band | <1 year | 4118 | 2.50 | 2.73 | 0.92 |
| manager_changes_12m | 0 | 24742 | 2.87 | 2.80 | 1.02 |
| manager_changes_12m | 1 | 7313 | 3.66 | 3.21 | 1.14 |
| manager_changes_12m | 2+ | 1801 | 4.07 | 4.81 | 0.85 |
| team_exits_12m | 0 | 25750 | 2.70 | 2.65 | 1.02 |
| team_exits_12m | 1 | 6030 | 4.11 | 3.98 | 1.03 |
| team_exits_12m | 2+ | 2076 | 5.26 | 4.39 | 1.20 |
| direct_reports_band | 0 | 26406 | 3.51 | 3.32 | 1.05 |
| direct_reports_band | 1-5 | 5103 | 1.91 | 1.89 | 1.01 |
| direct_reports_band | 6+ | 2347 | 1.18 | 1.74 | 0.68 |
| time_since_promotion_band | promo 1-2 years | 3705 | 3.91 | 3.44 | 1.14 |
| time_since_promotion_band | promo 2-3 years | 3141 | 2.90 | 3.31 | 0.88 |
| time_since_promotion_band | promo 3+ years | 5106 | 2.34 | 2.37 | 0.99 |
| time_since_promotion_band | promo <1 year | 3942 | 3.42 | 3.40 | 1.01 |
| time_since_promotion_band | sin promo en historial | 4895 | 2.13 | 1.71 | 1.25 |
| time_since_promotion_band | sin promo, contratado 1-3 years | 4705 | 3.70 | 3.61 | 1.02 |
| time_since_promotion_band | sin promo, contratado 3+ years | 3688 | 4.51 | 3.99 | 1.13 |
| time_since_promotion_band | sin promo, contratado <1 year | 4673 | 2.49 | 2.74 | 0.91 |
| rehire | no | 28765 | 2.94 | 2.77 | 1.06 |
| rehire | yes | 5092 | 4.05 | 4.31 | 0.94 |
