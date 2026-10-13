# J: BU L3 Top 9 + Other sin Transfers

Fecha: 13-oct-2026. Modo: `presentation`. Estado: candidato retrospectivo; no sustituye el modelo elegido.

## Definición

J parte de C, retira `transfer_12m` como requisito y agrega `bu_l3_top9_other`: las nueve BU L3 conocidas con más personas distintas antes del origen de ajuste más `(other)`. Valores desconocidos y cualquier BU fuera de las nueve se asignan a `(other)`. J + QVoice usa los bloques y la penalización QVoice ya seleccionados para CQ, sin una nueva búsqueda.

Para la priorización se aplicó la misma regla Top 9 + Other, aprendida antes de cada origen, a los seis modelos: Base, Base + QVoice bajo el mismo protocolo, Enhanced, Enhanced + QVoice, J y J + QVoice. Son sólo grupos BU; no se cruzan con antigüedad, nivel ni salidas del equipo. En enero-febrero una BU Top 9 no tuvo observaciones, pero la partición conserva sus diez categorías definidas.

## Resultado

| Modelo | Log-loss × 1,000 | Brier × 1,000 | PR-AUC | Captura 30% con grupos BU | Error grupo-snapshot |
|---|---:|---:|---:|---:|---:|
| Base | 138.7 | 30.7 | 4.8% | 32.6% | 0.6 pp |
| Base + QVoice | 137.6 | 30.6 | 5.4% | 32.6% | 0.7 pp |
| Enhanced | 138.8 | 30.7 | 4.9% | 31.4% | 0.5 pp |
| Enhanced + QVoice | 137.7 | 30.7 | 5.5% | 32.6% | 0.7 pp |
| J | 138.5 | 30.7 | 5.0% | 32.6% | 0.5 pp |
| J + QVoice | 137.5 | 30.7 | 5.6% | 32.6% | 0.5 pp |

Frente a C, J mejora la captura al 30% en 1.2 pp, IC95 [0.3, 2.1], y el log-loss en 0.24 × 1,000, IC95 [−0.47, −0.02]. Frente a CQ, J + QVoice mejora el log-loss medio en 0.17 × 1,000, pero su IC95 [−0.39, 0.06] incluye cero; la captura al 30% empata exactamente porque ambos priorizan las mismas categorías BU a esa capacidad. A 10% y 20%, J + QVoice captura 4.1 pp y 1.2 pp más que CQ respectivamente con estos grupos.

El modelo J + QVoice mejora la estimación media y el ranking, pero esta evaluación de grupos BU no es directamente comparable con la captura 43.1% de CQ bajo la agrupación vigente de antigüedad × salidas del equipo × nivel. Además, retirar Transfers había empeorado la ablación H/HQ anterior; J compensa parte de ese deterioro con BU L3, sin demostrar aún una mejora concluyente frente a CQ. CQ permanece elegido.

## Controles

Se reprodujeron C y CQ frente al archivo histórico. La población, las fechas, el outcome a seis meses, el peso entre periodos y las capacidades 10/20/30% fueron comunes. Se verificaron diez categorías, conservación de capacidad, ausencia de doble conteo y 500 remuestreos agrupados por persona. Se procesaron filas persona-mes sólo en RAM y se guardaron únicamente agregados.

Artefactos: [resultados](../../output/analysis/engineering/20261013/model-j-bu-top9-without-transfers-v4/results.json), [informe](../../output/analysis/engineering/20261013/model-j-bu-top9-without-transfers-v4/informe.md), [verificación](../../output/analysis/engineering/20261013/model-j-bu-top9-without-transfers-v4/verification.json), [modelo J](../../output/analysis/engineering/20261013/model-j-bu-top9-without-transfers-v4/trained-model/model-j.json) y [configuración](../../config/engineering_model_j_bu_top9_without_transfers_20261013.json).
