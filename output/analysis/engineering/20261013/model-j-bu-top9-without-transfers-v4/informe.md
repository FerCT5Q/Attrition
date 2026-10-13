# J: BU L3 Top 9 + Other sin Transfers

Modo: `presentation`. Resultado retrospectivo experimental; CQ sigue elegido hasta una decisión posterior.

| Modelo | Log-loss ×1,000 ↓ | Brier ×1,000 ↓ | PR-AUC ↑ | Captura 30% ↑ | Error de grupo ↓ |
|---|---:|---:|---:|---:|---:|
| Base | 138.7 | 30.7 | 4.8% | 32.6% | 0.6 pp |
| Base + QVoice (same protocol) | 137.6 | 30.6 | 5.4% | 32.6% | 0.7 pp |
| Enhanced | 138.8 | 30.7 | 4.9% | 31.4% | 0.5 pp |
| Enhanced + QVoice | 137.7 | 30.7 | 5.5% | 32.6% | 0.7 pp |
| J = Enhanced − Transfers + BU Top 9 + Other | 138.5 | 30.7 | 5.0% | 32.6% | 0.5 pp |
| J + QVoice | 137.5 | 30.7 | 5.6% | 32.6% | 0.5 pp |

Los seis modelos se evaluaron sobre las mismas personas, dos periodos y la misma definición de diez grupos BU. J y J + QVoice retiran `transfer_12m` por requisito y añaden BU L3 sólo como Top 9 + Other. B + QVoice se ajusta con el protocolo QVoice de esta prueba, por lo que no se sustituye el artefacto BQ archivado.

Las nueve BU se aprendieron antes de cada origen; cualquier BU fuera de ellas, incluidos valores desconocidos, se codificó como Other. Los grupos no se cruzan con antigüedad, nivel ni salidas del equipo. Los intervalos son 500 remuestreos pareados por persona y la comparación es retrospectiva.
