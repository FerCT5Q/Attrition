# Modelo E: señales V11 añadidas sobre C

Ejecución experimental en modo `presentation`; no se guardaron filas, identificadores ni scores individuales.

Se reutilizaron las features y L2 seleccionadas en cada fold de C. Las variantes añaden señales V11 y reajustan el hazard mensual con la misma penalización.

## Promedio de los cuatro periodos

Menor es mejor para pérdidas y error de grupo; mayor es mejor para PR-AUC, lift y captura.

| Variante | Log-loss × 1000 | Brier × 1000 | PR-AUC (%) | Lift 10% | Captura 30% (%) | Error grupo (pp) |
|---|---:|---:|---:|---:|---:|---:|
| C | 131.9 | 29.1 | 5.3 | 2.1 | 45.4 | 0.7 |
| C_plus_work_city | 131.0 | 29.1 | 5.6 | 2.2 | 45.7 | 0.6 |
| C_plus_job_family_detail | 130.8 | 29.1 | 5.7 | 2.3 | 45.7 | 0.6 |
| C_plus_manager_expected6 | 131.6 | 29.1 | 5.5 | 2.1 | 45.9 | 0.6 |
| C_plus_manager_team_exits6 | 131.7 | 29.1 | 5.4 | 2.1 | 45.9 | 0.6 |
| C_plus_city_job_family | 130.4 | 29.0 | 5.8 | 2.3 | 45.8 | 0.6 |

## Intervalos pareados frente a C

Un intervalo de captura completamente positivo favorece a la variante; un intervalo de pérdidas completamente positivo en `C - variante` favorece a la variante.

| Variante | IC95 log-loss C − variante | IC95 Brier C − variante | IC95 captura variante − C (pp) |
|---|---:|---:|---:|
| C_plus_work_city | [0.69, 1.00] | [0.04, 0.07] | [0.17, 0.42] |
| C_plus_job_family_detail | [0.92, 1.25] | [0.06, 0.09] | [0.17, 0.43] |
| C_plus_manager_expected6 | [0.19, 0.40] | [0.01, 0.03] | [0.20, 0.61] |
| C_plus_manager_team_exits6 | [0.08, 0.22] | [0.01, 0.02] | [0.26, 0.60] |
| C_plus_city_job_family | [1.25, 1.64] | [0.08, 0.11] | [0.22, 0.50] |

## Lectura

La comparación es incremental y retrospectiva. Una variante con señal positiva sobre C sigue siendo experimental: no se reoptimizaron los grupos, no se seleccionaron variables usando el periodo externo y la prueba no demuestra causalidad ni superioridad frente a C o CQ.
