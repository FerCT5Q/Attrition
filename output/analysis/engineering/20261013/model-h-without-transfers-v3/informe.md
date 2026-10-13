# H = C sin Transfers y H + QVoice

Modo: `presentation`.

## Métricas retrospectivas

| Modelo | Log-loss × 1,000 ↓ | Brier × 1,000 ↓ | PR-AUC ↑ | Captura al 30% ↑ | Error de grupo ↓ |
|---|---:|---:|---:|---:|---:|
| C | 138.8 | 30.7 | 4.9% | 42.4% | 1.0 pp |
| H | 140.5 | 30.8 | 4.8% | 41.6% | 1.0 pp |
| CQ | 137.7 | 30.7 | 5.5% | 43.1% | 1.0 pp |
| HQ | 139.4 | 30.8 | 5.4% | 42.4% | 1.0 pp |

H menos C en captura al 30%: -0.81 pp, IC95 [-1.61, -0.09].
H + QVoice menos CQ en captura al 30%: -0.68 pp, IC95 [-1.85, 0.25].

## Método y límite

Se retiró sólo `transfer_12m`, que representa una transferencia efectiva en los 12 meses anteriores a la foto. `transfer_history` nunca fue predictor de C. Se mantuvieron las variables restantes, la penalización, el origen de C (1-ago-2025), las personas, periodos, grupos y capacidades. H reajusta sus coeficientes; H + QVoice mantiene por periodo los bloques QVoice y L2 ya seleccionados por CQ y reajusta esa corrección sobre H.

No se repitió la búsqueda de variables ni de combinaciones QVoice: es una ablación retrospectiva, no una selección de un nuevo modelo. C y CQ se reprodujeron antes de interpretar la comparación. Los intervalos usan 500 remuestreos pareados por persona.
