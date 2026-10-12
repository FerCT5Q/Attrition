# Selección de modelo: tabla actualizada

Engineering; fotos ago–dic 2025 y ene–feb 2026, seguimiento de seis meses. Igual peso por periodo. Evaluación retrospectiva.

| Modelo | Captura al 30% ↑ | Error grupo-mes ↓ | Cambio de error vs C ↓ | Log-loss × 1000 ↓ | PR-AUC ↑ |
|---|---:|---:|---:|---:|---:|
| C | 42.4% | 1 pp | 0% | 138.8 | 4.9% |
| C + Q evaluado | 43.1% | 1 pp | -2.3% | 137.7 | 5.5% |
| C + Q fijo + promedio 33 | 43.1% | 1 pp | 1.9% | 138.2 | 5.2% |
| C + Q fijo + promedio 28 | 43.1% | 1 pp | 1.7% | 138.2 | 5.2% |
| C + Q fijo sin promedio | 43.1% | 1 pp | 3.2% | 138.3 | 5.2% |
