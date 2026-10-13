# Validación de F + QVoice

Auditoría agregada de la comparación completa contra C + QVoice. Se usan los mismos dos cortes externos, la misma selección QVoice y una ejecución rápida de réplica. No se guardan filas ni predicciones individuales.

## Resultado por corte

Los deltas son F + QVoice menos C + QVoice; negativo es mejor para pérdidas y error, positivo es mejor para ranking y captura.

| Corte | Log-loss ×1000 | Brier ×1000 | PR-AUC pp | Lift | Captura pp | Error grupo pp |
|---|---:|---:|---:|---:|---:|---:|
| aug_dec_2025 | -0.8 | -0.1 | +0.3 | +0.1 | +0.1 | -0.0 |
| jan_feb_2026 | -1.7 | -0.1 | +0.5 | +0.2 | +0.0 | -0.1 |

## Decisión bajo la regla vigente

**F + QVoice se registra como nuevo candidato experimental y mejor challenger; C + QVoice sigue elegido por la regla vigente.**

F mejora log-loss, Brier, PR-AUC, lift y error de grupo en ambos cortes. La captura mejora en el primer corte y empata en el segundo; por eso la condición estricta de ganar captura en los dos periodos no pasa. La evidencia respalda registrar F + QVoice como nuevo candidato experimental para aprobación, pero no sustituye una validación prospectiva.

## Comprobaciones

- Pruebas ejecutadas: 25.
- Comprobaciones aprobadas: 24.
- Estado del conjunto: fail.
- Evidencia JSON: `validation-f-qvoice.json`.
