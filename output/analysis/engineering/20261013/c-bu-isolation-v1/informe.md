# C + BU L3 sin QVoice: comparación específica

Modo `presentation`. Ingeniería, mismas personas y fotos en todos los modelos. Agosto–diciembre 2025 y enero–febrero 2026, igual peso entre periodos. Salida voluntaria a seis meses; ventanas superpuestas.

| Modelo | Log-loss ×1000 ↓ | Brier ×1000 ↓ | Captura 30% ↑ | Error grupo-mes, pp ↓ |
|---|---:|---:|---:|---:|
| C histórico | 138.7716 | 30.7402 | 42.4416% | 0.9940 |
| C reajustado al corte | 138.7532 | 30.7337 | 42.4416% | 0.9395 |
| C + BU L3 (sin QVoice) | 137.9902 | 30.6876 | 42.6558% | 0.9941 |
| CQ | 137.6962 | 30.6808 | 43.1060% | 0.9709 |
| C + BU L3 + QVoice | 136.9544 | 30.6322 | 43.0684% | 0.9234 |
| C + ciudad + QVoice | 136.4335 | 30.5815 | 43.1456% | 0.8875 |
| C + ciudad + BU L3 + QVoice | 135.9700 | 30.5588 | 43.1060% | 0.8893 |

## Diferencias pareadas

Candidato menos referencia; valores negativos favorecen pérdidas/error, positivos favorecen captura. IC95 con 500 remuestreos de personas compartidos entre periodos y modelos; modelos y prioridades fijos.

| Contraste | Δ log-loss ×1000 [IC95] | Δ captura, pp [IC95] | Δ error, pp [IC95] |
|---|---:|---:|---:|
| C + BU L3 (sin QVoice) − C reajustado al corte | -0.7630 [-1.0659, -0.4739] | 0.2143 [-0.0184, 0.4204] | 0.0546 [0.0216, 0.0968] |
| C + BU L3 (sin QVoice) − C histórico | -0.7814 [-1.0858, -0.4833] | 0.2143 [-0.0184, 0.4204] | 0.0001 [-0.0285, 0.0630] |
| C + BU L3 (sin QVoice) − CQ | 0.2941 [-0.2415, 0.8178] | -0.4502 [-0.8035, -0.0428] | 0.0231 [-0.0381, 0.1065] |
| C + BU L3 + QVoice − C + BU L3 (sin QVoice) | -1.0359 [-1.4590, -0.6010] | 0.4125 [0.1215, 0.7015] | -0.0706 [-0.1267, 0.0156] |
| C + BU L3 + QVoice − CQ | -0.7418 [-1.0517, -0.4425] | -0.0376 [-0.1569, 0.1068] | -0.0475 [-0.0636, 0.0194] |
| C + ciudad + BU L3 + QVoice − C + BU L3 + QVoice | -0.9844 [-1.3369, -0.5750] | 0.0376 [-0.1068, 0.1569] | -0.0342 [-0.0602, -0.0016] |
| C + ciudad + BU L3 + QVoice − C + BU L3 (sin QVoice) | -2.0202 [-2.6070, -1.3874] | 0.4502 [0.0428, 0.8035] | -0.1048 [-0.1651, -0.0115] |
| C reajustado al corte − C histórico | -0.0184 [-0.0657, 0.0403] | 0.0000 [0.0000, 0.0000] | -0.0545 [-0.0630, 0.0174] |

## Por periodo

| Periodo | Modelo | Log-loss ×1000 | Brier ×1000 | Captura 30% | Error, pp |
|---|---|---:|---:|---:|---:|
| aug_dec_2025 | C histórico | 129.4724 | 28.1965 | 42.1277% | 1.0447 |
| aug_dec_2025 | C reajustado al corte | 129.4726 | 28.1965 | 42.1277% | 1.0448 |
| aug_dec_2025 | C + BU L3 (sin QVoice) | 129.0885 | 28.1774 | 42.5562% | 1.1720 |
| aug_dec_2025 | CQ | 128.5750 | 28.1677 | 43.4565% | 1.0204 |
| aug_dec_2025 | C + BU L3 + QVoice | 128.2102 | 28.1433 | 43.3812% | 1.0343 |
| aug_dec_2025 | C + ciudad + QVoice | 127.7691 | 28.1068 | 43.5358% | 1.0008 |
| aug_dec_2025 | C + ciudad + BU L3 + QVoice | 127.5707 | 28.1007 | 43.4565% | 1.0143 |
| jan_feb_2026 | C histórico | 148.0708 | 33.2838 | 42.7555% | 0.9433 |
| jan_feb_2026 | C reajustado al corte | 148.0338 | 33.2708 | 42.7555% | 0.8341 |
| jan_feb_2026 | C + BU L3 (sin QVoice) | 146.8920 | 33.1978 | 42.7555% | 0.8161 |
| jan_feb_2026 | CQ | 146.8173 | 33.1939 | 42.7555% | 0.9214 |
| jan_feb_2026 | C + BU L3 + QVoice | 145.6986 | 33.1212 | 42.7555% | 0.8126 |
| jan_feb_2026 | C + ciudad + QVoice | 145.0978 | 33.0561 | 42.7555% | 0.7741 |
| jan_feb_2026 | C + ciudad + BU L3 + QVoice | 144.3694 | 33.0168 | 42.7555% | 0.7642 |

## Interpretación y límites

La ronda v7 incluyó QVoice y no conservó C + BU sin encuesta. Esta ejecución lo evalúa explícitamente y guarda sus coeficientes. C reajustado usa exactamente las fechas, estructura y penalización del candidato: el contraste C + BU menos C reajustado separa BU de la actualización temporal.

CQ conserva en enero su base RH de agosto. Compararlo con los candidatos actualizados es válido como comparación de estimadores completos, pero no aísla una sola variable. La comparación C + BU + QVoice frente a FQ + BU sí comparte los cortes RH y la selección QVoice.

Las capacidades 10/20/30 y sus alternativas de incluir/excluir el grupo límite están en results.json. Los grupos mantienen mínimo 300 y la misma definición; BU se incorpora como predictor. No se publican scores ni filas individuales. Los promedios de tasas se basan en exposiciones persona-mes y no deben interpretarse como salidas únicas de toda la ventana.

Conclusiones retrospectivas y condicionadas a elecciones previas. IOS y la publicación real de QVoice no tienen disponibilidad histórica acreditada. No se cambian scores de assessment ni se adopta otro modelo automáticamente.

Reproducción: `.venv/Scripts/python.exe -B tools/compare_c_bu_isolation.py --config config/engineering_c_bu_isolation_20261013.json` usando otra carpeta de salida. Fuente SQL, hashes, cortes, tiempos, parámetros y verificaciones quedan en esta carpeta.
