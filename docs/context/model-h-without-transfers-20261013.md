# H = C sin Transfers y H + QVoice

Fecha: 13-oct-2026. Modo: `presentation`. Estado: sensibilidad retrospectiva; no cambia el modelo elegido.

## Definición

La representación retirada es `transfer_12m`: indicador de una transferencia efectiva en los doce meses anteriores a la foto. `transfer_history` no era predictor de C, por lo que no se declaró retirado.

H conserva las 16 representaciones restantes de C seleccionado el 1-ago-2025 y su L2 = 0.1; sólo reajusta coeficientes con las etiquetas maduras anteriores a ese mismo origen. H + QVoice conserva para cada periodo los bloques y L2 que CQ ya había seleccionado, y reajusta la corrección QVoice sobre H. No se hizo una búsqueda nueva de variables ni de combinaciones QVoice.

## Resultado

| Modelo | Log-loss × 1,000 | Brier × 1,000 | PR-AUC | Captura al 30% | Error de grupo |
|---|---:|---:|---:|---:|---:|
| C | 138.8 | 30.7 | 4.9% | 42.4% | 1.0 pp |
| H = C − Transfers | 140.5 | 30.8 | 4.8% | 41.6% | 1.0 pp |
| C + QVoice | 137.7 | 30.7 | 5.5% | 43.1% | 1.0 pp |
| H + QVoice | 139.4 | 30.8 | 5.4% | 42.4% | 1.0 pp |

Quitar Transfers empeora log-loss y Brier en ambas comparaciones. H pierde 0.81 pp de captura frente a C, IC95 [-1.61, -0.09]. H + QVoice pierde 0.68 pp frente a CQ, IC95 [-1.85, 0.25]: el intervalo de captura incluye cero, pero las diferencias de log-loss y Brier empeoran con IC95 que no contiene cero.

## Controles y límite

C y CQ se reprodujeron numéricamente en los dos periodos antes de ajustar H. Población, fechas, outcome, grupos, capacidades y peso entre periodos son los mismos; los intervalos usan 500 remuestreos pareados por persona. Se cargaron filas persona-mes únicamente en RAM, sin persistir IDs, filas ni scores individuales. La comparación es retrospectiva y no demuestra un efecto causal de realizar una transferencia.

Artefactos: [resultado agregado](../../output/analysis/engineering/20261013/model-h-without-transfers-v3/results.json), [informe](../../output/analysis/engineering/20261013/model-h-without-transfers-v3/informe.md), [verificación](../../output/analysis/engineering/20261013/model-h-without-transfers-v3/verification.json) y [modelo H](../../output/analysis/engineering/20261013/model-h-without-transfers-v3/trained-model/model-h.json).

## Referencia B / Base en la misma cohorte — 13-oct-2026

La ejecución v4 añadió B como referencia restaurada desde su artefacto histórico compatible, sin reajustarlo. Se evaluó con exactamente la misma población Engineering, periodos (agosto–diciembre de 2025 y enero–febrero de 2026), salida voluntaria a seis meses, grupos y capacidad de 30% que C, H, CQ y HQ.

| Modelo | Log-loss × 1,000 | Brier × 1,000 | PR-AUC | Captura al 30% | Error de grupo |
|---|---:|---:|---:|---:|---:|
| B / Base | 138.7 | 30.7 | 4.8% | 41.6% | 0.8 pp |
| C / Enhanced | 138.8 | 30.7 | 4.9% | 42.4% | 1.0 pp |
| H / Enhanced sin Transfers | 140.5 | 30.8 | 4.8% | 41.6% | 1.0 pp |
| CQ / Enhanced + QVoice | 137.7 | 30.7 | 5.5% | 43.1% | 1.0 pp |
| HQ / Enhanced + QVoice sin Transfers | 139.4 | 30.8 | 5.4% | 42.4% | 1.0 pp |

B presenta un intercambio en estos dos cortes: menor log-loss y menor error de grupo que C, mientras que C captura 0.8 puntos porcentuales más de las salidas y tiene mayor PR-AUC. Es una referencia retrospectiva de dos periodos, no una repetición de la selección B → C de cuatro periodos ni una razón para reemplazar C o CQ. La elección vigente de CQ no cambia.

Artefactos v4: [resultado agregado](../../output/analysis/engineering/20261013/model-h-without-transfers-v4/results.json), [informe](../../output/analysis/engineering/20261013/model-h-without-transfers-v4/informe.md) y [verificación](../../output/analysis/engineering/20261013/model-h-without-transfers-v4/verification.json). La ejecución preservó sólo agregados; no persistió filas ni scores individuales.
