# F + QVoice frente a C + QVoice y B + QVoice

Comparación retrospectiva en modo `presentation`; no se guardaron filas, identificadores ni predicciones individuales.

F+Q reutiliza la selección QVoice archivada de CQ por periodo y añade únicamente `work_city` al modelo C antes de la corrección Q. B+Q es la variante archivada `B_Q` de la ronda V11.

## Promedio de agosto–diciembre de 2025 y enero–febrero de 2026

Menor es mejor para pérdidas y error de grupo; mayor es mejor para PR-AUC, lift y captura.

| Modelo | Log-loss ×1000 ↓ | Brier ×1000 ↓ | PR-AUC ↑ | Lift 10% ↑ | Captura 30% ↑ | Error grupo-mes ↓ |
|---|---:|---:|---:|---:|---:|---:|
| C + ciudad + QVoice | 136.4 | 30.6 | 5.9% | 2.2 | 43.1% | 0.9 pp |
| C + QVoice | 137.7 | 30.7 | 5.5% | 2.1 | 43.1% | 1.0 pp |
| B + QVoice (B_Q archivado) | 137.4 | 30.6 | 5.4% | 2.0 | 41.6% | 0.6 pp |

## Lectura

La comparación F+Q frente a C+Q aísla el aporte de `work_city` manteniendo fija la selección QVoice de CQ. La comparación con B+Q usa el artefacto archivado `B_Q`; sus cifras se reportan como referencia externa de la misma ventana, no como un reajuste nuevo de B.
