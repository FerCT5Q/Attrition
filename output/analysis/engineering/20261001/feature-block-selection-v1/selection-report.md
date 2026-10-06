# Selección de variables por bloques — Engineering

Creado: 2026-10-02T04:13:29.941806+00:00. Frontera de conocimiento: 2026-09-07.
Fotos: 2021-07-25 a 2026-07-26; 1,880,719 persona-mes con etiqueta mensual y 1,699,949 con etiqueta a seis meses.
Entrenamiento en memoria (sin persistir filas ni IDs) bajo `config\attrition_model_in_memory_training_authorization_20261001.json`.

## Camino de selección hacia delante (hazard `cloglog`, 4 folds)

| Paso | Bloques | Parámetros | PR-AUC | Lift@10% | Lift@20% | Brier |
|---:|---|---:|---:|---:|---:|---:|
| 0 | base | 23 | 0.0454 | 1.708 | 1.550 | 0.02932 |
| 1 | manager_equipo | 30 | 0.0494 | 1.942 | 1.698 | 0.02927 |
| 2 | carrera, manager_equipo | 31 | 0.0496 | 1.956 | 1.697 | 0.02927 |
| 3 | carrera, geografia, manager_equipo | 35 | 0.0498 | 1.942 | 1.697 | 0.02926 |
| 4 | carrera, compensacion, geografia, manager_equipo | 43 | 0.0495 | 1.928 | 1.695 | 0.02927 |

## Todas las combinaciones evaluadas

| Bloques | PR-AUC | Lift@10% | Lift@20% | Brier |
|---|---:|---:|---:|---:|
| carrera, geografia, manager_equipo | 0.0498 | 1.942 | 1.697 | 0.02926 |
| geografia, manager_equipo | 0.0496 | 1.925 | 1.694 | 0.02926 |
| carrera, manager_equipo | 0.0496 | 1.956 | 1.697 | 0.02927 |
| carrera, compensacion, geografia, manager_equipo | 0.0495 | 1.928 | 1.695 | 0.02927 |
| manager_equipo | 0.0494 | 1.942 | 1.698 | 0.02927 |
| carrera, compensacion, manager_equipo | 0.0490 | 1.909 | 1.696 | 0.02928 |
| compensacion, manager_equipo | 0.0488 | 1.898 | 1.691 | 0.02928 |
| geografia | 0.0461 | 1.691 | 1.553 | 0.02931 |
| carrera | 0.0460 | 1.714 | 1.560 | 0.02932 |
| base | 0.0454 | 1.708 | 1.550 | 0.02932 |
| compensacion | 0.0445 | 1.676 | 1.551 | 0.02932 |

## Regla de parsimonia

Mejor PR-AUC 0.0498; mejor lift@10% 1.956; tolerancia 2% relativo.
Elegibles: [manager_equipo], [carrera, manager_equipo], [geografia, manager_equipo], [carrera, geografia, manager_equipo], [carrera, compensacion, geografia, manager_equipo].
**Elegido: manager_equipo.**

## Techo no lineal (LightGBM, todas las variables)

PR-AUC | Lift@10% | Lift@20% | Brier: 0.0523 | 1.997 | 1.707 | 0.02916

## Contribución de cada variable del elegido (quitar una)

| Variable quitada | PR-AUC | Lift@10% | Lift@20% | Brier |
|---|---:|---:|---:|---:|
| manager_changes_12m | 0.0492 | 1.920 | 1.683 | 0.02928 |
| team_exits_12m | 0.0457 | 1.758 | 1.608 | 0.02931 |
| direct_reports_band | 0.0493 | 1.932 | 1.686 | 0.02928 |

## Modelo elegido por fold

| Fold | L2 | PR-AUC | Lift@10% | Brier | Estimado % | Observado % |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 10.0 | 0.0508 | 2.032 | 0.02939 | 1.80 | 3.03 |
| 2 | 10.0 | 0.0510 | 2.006 | 0.02907 | 2.13 | 3.01 |
| 3 | 10.0 | 0.0525 | 2.045 | 0.02963 | 2.21 | 3.07 |
| 4 | 10.0 | 0.0433 | 1.685 | 0.02899 | 2.36 | 3.00 |

## Hazard ratios del elegido por fold

Referencias: {'level_grouped': '7 - Senior & Lead', 'company_tenure_band': '7+ years', 'calendar_month': '7', 'manager_changes_12m': '0', 'team_exits_12m': '0', 'direct_reports_band': '0'}

| Término | HR por fold | Mismo signo |
|---|---|---|
| team_exits_12m=2+ | 1.58, 1.62, 1.68, 1.75 | sí |
| company_tenure_band=3-7 years | 1.62, 1.66, 1.68, 1.66 | sí |
| direct_reports_band=6+ | 0.61, 0.61, 0.61, 0.60 | sí |
| team_exits_12m=1 | 1.31, 1.33, 1.37, 1.39 | sí |
| company_tenure_band=1-3 years | 1.43, 1.38, 1.39, 1.35 | sí |
| level_grouped=2 - Sr Dir | 0.82, 0.80, 0.79, 0.75 | sí |
| level_grouped=5 - Sr Staff & /Mgr | 0.76, 0.77, 0.77, 0.77 | sí |
| level_grouped=3 - Princ/Directors | 0.81, 0.78, 0.80, 0.78 | sí |
| company_tenure_band=<1 year | 0.83, 0.81, 0.83, 0.81 | sí |
| level_grouped=8 - Assoc & Int/Eng | 1.23, 1.24, 1.22, 1.22 | sí |
| direct_reports_band=1-5 | 0.83, 0.83, 0.83, 0.82 | sí |
| level_grouped=1 - VP & Above | 0.90, 0.87, 0.85, 0.84 | sí |
| manager_changes_12m=2+ | 1.17, 1.14, 1.16, 1.18 | sí |
| time_index | 0.76, 0.82, 0.83, 0.86 | sí |
| manager_changes_12m=1 | 1.11, 1.11, 1.14, 1.15 | sí |
| level_grouped=6 - Staff & /Mgr | 0.89, 0.90, 0.90, 0.89 | sí |
| level_grouped=Misc | 1.00, 1.00, 1.00, 1.00 | sí |
| team_exits_12m=(unknown) | —, 1.00, 1.00, 1.00 | no |

## Grupos (árbol profundidad ≤ 3, hojas ≥ 300 personas), foto 2026-07-26

Riesgo medio estimado a seis meses: 2.33%. R² del árbol sobre el riesgo del modelo: 0.80.

| Grupo | Personas | % población | Riesgo 6m % | Lift | Último fold: estimado % | observado % |
|---|---:|---:|---:|---:|---:|---:|
| company_tenure_band ≠ 7+ years y company_tenure_band ≠ <1 year y team_exits_12m ≠ 0 | 4695 | 12.6 | 4.12 | 1.76 | 4.16 | 4.67 |
| company_tenure_band ≠ 7+ years y company_tenure_band ≠ <1 year y team_exits_12m = 0 | 13191 | 35.4 | 2.78 | 1.19 | 2.83 | 3.50 |
| company_tenure_band ≠ 7+ years y company_tenure_band = <1 year y team_exits_12m ≠ 0 | 1645 | 4.4 | 2.44 | 1.04 | 2.38 | 3.35 |
| company_tenure_band = 7+ years y direct_reports_band = 0 y team_exits_12m ≠ 0 | 1479 | 4.0 | 2.38 | 1.02 | 2.32 | 4.12 |
| company_tenure_band ≠ 7+ years y company_tenure_band = <1 year y team_exits_12m = 0 | 3669 | 9.9 | 1.65 | 0.71 | 1.60 | 2.47 |
| company_tenure_band = 7+ years y direct_reports_band = 0 y team_exits_12m = 0 | 6398 | 17.2 | 1.59 | 0.68 | 1.55 | 2.04 |
| company_tenure_band = 7+ years y direct_reports_band ≠ 0 y team_exits_12m ≠ 0 | 1238 | 3.3 | 1.59 | 0.68 | 1.59 | 2.52 |
| company_tenure_band = 7+ years y direct_reports_band ≠ 0 y team_exits_12m = 0 | 4906 | 13.2 | 1.05 | 0.45 | 1.07 | 1.25 |

## Calibración por subgrupo no protegido (último fold)

| Variable | Categoría | Personas/foto | Estimado % | Observado % | Razón |
|---|---|---:|---:|---:|---:|
| level_grouped | 1 - VP & Above | 212 | 1.17 | 2.75 | 0.43 |
| level_grouped | 2 - Sr Dir | 867 | 1.17 | 1.31 | 0.89 |
| level_grouped | 3 - Princ/Directors | 3225 | 1.35 | 1.87 | 0.72 |
| level_grouped | 5 - Sr Staff & /Mgr | 6216 | 1.52 | 2.09 | 0.73 |
| level_grouped | 6 - Staff & /Mgr | 6632 | 2.16 | 3.15 | 0.69 |
| level_grouped | 7 - Senior & Lead | 11428 | 2.93 | 3.64 | 0.81 |
| level_grouped | 8 - Assoc & Int/Eng | 5276 | 3.25 | 3.46 | 0.94 |
| company_tenure_band | 1-3 years | 5168 | 3.05 | 3.54 | 0.86 |
| company_tenure_band | 3-7 years | 11781 | 3.24 | 3.93 | 0.82 |
| company_tenure_band | 7+ years | 12789 | 1.45 | 2.00 | 0.73 |
| company_tenure_band | <1 year | 4118 | 1.82 | 2.73 | 0.67 |
| manager_changes_12m | 0 | 24742 | 2.19 | 2.80 | 0.78 |
| manager_changes_12m | 1 | 7313 | 2.76 | 3.21 | 0.86 |
| manager_changes_12m | 2+ | 1801 | 3.10 | 4.81 | 0.65 |
| team_exits_12m | 0 | 25750 | 2.08 | 2.65 | 0.79 |
| team_exits_12m | 1 | 6030 | 3.07 | 3.98 | 0.77 |
| team_exits_12m | 2+ | 2076 | 3.77 | 4.39 | 0.86 |
| direct_reports_band | 0 | 26406 | 2.65 | 3.32 | 0.80 |
| direct_reports_band | 1-5 | 5103 | 1.48 | 1.89 | 0.78 |
| direct_reports_band | 6+ | 2347 | 1.07 | 1.74 | 0.61 |
