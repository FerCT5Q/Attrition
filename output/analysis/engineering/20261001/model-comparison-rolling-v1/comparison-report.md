# Comparación rolling-origin sin segmento (Engineering)

Creado: 2026-10-02T02:45:57.523188+00:00. Frontera de conocimiento: 2026-09-07.

`seg` se excluye por la reasignación de job family del 2026-09-01
(10.9% de las personas cambió de segmento).


## Alcance `engineering_noseg`

### PR-AUC

| Modelo | 2024-02-18 | 2024-08-25 | 2025-02-23 | 2025-08-24 | Media |
|---|---:|---:|---:|---:|---:|
| Hazard cloglog aditivo | 0.04497 | 0.04560 | 0.04994 | 0.04134 | 0.04546 |
| Hazard + interacciones | 0.04476 | 0.04580 | 0.05082 | 0.04201 | 0.04585 |
| Logística directa 6m | 0.04269 | 0.04445 | 0.04878 | 0.04151 | 0.04435 |
| LightGBM 6m | 0.04551 | 0.04043 | 0.04901 | 0.04150 | 0.04411 |
| Promedio histórico | 0.03034 | 0.02613 | 0.03118 | 0.02719 | 0.02871 |

### Lift@10%

| Modelo | 2024-02-18 | 2024-08-25 | 2025-02-23 | 2025-08-24 | Media |
|---|---:|---:|---:|---:|---:|
| Hazard cloglog aditivo | 1.75097 | 1.74513 | 1.91567 | 1.50486 | 1.72916 |
| Hazard + interacciones | 1.75097 | 1.75210 | 1.93652 | 1.52582 | 1.74135 |
| Logística directa 6m | 1.65999 | 1.72580 | 1.86653 | 1.52149 | 1.69345 |
| LightGBM 6m | 1.75350 | 1.48669 | 1.75818 | 1.49300 | 1.62284 |
| Promedio histórico | 0.82972 | 0.66036 | 0.85768 | 0.79712 | 0.78622 |

### Brier

| Modelo | 2024-02-18 | 2024-08-25 | 2025-02-23 | 2025-08-24 | Media |
|---|---:|---:|---:|---:|---:|
| Hazard cloglog aditivo | 0.02937 | 0.02904 | 0.02959 | 0.02972 | 0.02943 |
| Hazard + interacciones | 0.02936 | 0.02903 | 0.02956 | 0.02971 | 0.02941 |
| Logística directa 6m | 0.02932 | 0.02907 | 0.02961 | 0.02972 | 0.02943 |
| LightGBM 6m | 0.02930 | 0.02907 | 0.02959 | 0.02979 | 0.02944 |
| Promedio histórico | 0.02942 | 0.02917 | 0.02977 | 0.02979 | 0.02954 |

### Folds ganados frente al hazard aditivo

- Hazard + interacciones: PR-AUC 3/4, lift@10% 3/4, Brier no peor 4/4.
- Logística directa 6m: PR-AUC 1/4, lift@10% 1/4, Brier no peor 1/4.
- LightGBM 6m: PR-AUC 2/4, lift@10% 1/4, Brier no peor 2/4.

### Eventos por fold

- 2024-02-18 a 2024-07-21: 179384 exposiciones, 5441 eventos.
- 2024-08-25 a 2025-01-26: 185788 exposiciones, 5587 eventos.
- 2025-02-23 a 2025-07-27: 190975 exposiciones, 5865 eventos.
- 2025-08-24 a 2026-02-22: 238451 exposiciones, 7329 eventos.


## Curva de captura del último periodo (hazard aditivo)

- 0% de personas: 0.0% de salidas
- 10% de personas: 15.0% de salidas
- 20% de personas: 28.2% de salidas
- 30% de personas: 40.2% de salidas
- 40% de personas: 51.1% de salidas
- 50% de personas: 62.7% de salidas
- 60% de personas: 73.2% de salidas
- 70% de personas: 82.2% de salidas
- 80% de personas: 88.9% de salidas
- 90% de personas: 94.4% de salidas
- 100% de personas: 100.0% de salidas

## Grupos del último periodo (hazard aditivo)

| Nivel | Antigüedad | Personas/foto | Estimado % | Observado % |
|---|---|---:|---:|---:|
| 8 - Assoc & Int/Eng | 3-7 years | 1283 | 5.0 | 5.4 |
| 8 - Assoc & Int/Eng | 1-3 years | 2396 | 4.2 | 3.7 |
| 7 - Senior & Lead | 3-7 years | 6653 | 4.2 | 4.0 |
| 6 - Staff & /Mgr | 3-7 years | 2485 | 3.5 | 3.5 |
| 7 - Senior & Lead | 1-3 years | 1927 | 3.4 | 3.4 |
| 6 - Staff & /Mgr | 1-3 years | 478 | 2.8 | 5.4 |
| 5 - Sr Staff & /Mgr | 3-7 years | 987 | 2.8 | 3.8 |
| 8 - Assoc & Int/Eng | <1 year | 1500 | 2.6 | 2.0 |
| 3 - Princ/Directors | 3-7 years | 345 | 2.5 | 4.2 |
| 7 - Senior & Lead | 7+ years | 1133 | 2.5 | 3.7 |
| 5 - Sr Staff & /Mgr | 1-3 years | 268 | 2.3 | 2.8 |
| 7 - Senior & Lead | <1 year | 1844 | 2.2 | 3.2 |
| 6 - Staff & /Mgr | 7+ years | 3305 | 2.1 | 2.6 |
| 3 - Princ/Directors | 1-3 years | 85 | 2.0 | — |
| 6 - Staff & /Mgr | <1 year | 420 | 1.8 | 3.5 |
| 2 - Sr Dir | 3-7 years | 62 | 1.7 | — |
| 5 - Sr Staff & /Mgr | 7+ years | 4751 | 1.6 | 1.7 |
| 3 - Princ/Directors | 7+ years | 2652 | 1.5 | 1.4 |
| 5 - Sr Staff & /Mgr | <1 year | 262 | 1.4 | 3.4 |
| 3 - Princ/Directors | <1 year | 179 | 1.3 | 5.7 |
| 2 - Sr Dir | 7+ years | 781 | 1.0 | 1.1 |
| 1 - VP & Above | 7+ years | 186 | 0.7 | — |
