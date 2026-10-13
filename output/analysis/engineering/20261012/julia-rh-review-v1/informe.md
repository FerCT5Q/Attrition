# Revisión de Julia: estimación, grupos y preparación para RH

**FQ + BU L3 obtiene el menor log-loss medio de esta comparación.** La recomendación predictiva se separa de la adopción: CQ sigue elegido. Ninguna subdivisión principal de 100 personas cumple todas las guardas en ambos periodos.

Modo `presentation`. Resultado retrospectivo en Engineering, Employee, Regular, activa y sin RF360. Fotos de agosto–diciembre de 2025 y enero–febrero de 2026; salida voluntaria a seis meses. Cada periodo pesa la mitad. CQ conserva su condición de modelo elegido; esta ejecución evalúa candidatos y escenarios.

**Comparabilidad del ajuste:** CQ histórico conserva su base RH de 1-ago-2025 en ambos periodos. Las bases FQ/FQ + BU se reajustan a 1-ago-2025 y 1-ene-2026. Se comparan estimadores completos; la diferencia de enero frente a CQ reúne ciudad y actualización de la base, por lo que no aísla el aporte de ciudad. FQ frente a FQ + BU sí comparte origen RH en ambos periodos. Los tres comparten selección QVoice, población, fechas de evaluación y grupos.

| Modelo | Log-loss ×1000 ↓ | Brier ×1000 ↓ | Captura al 30% ↑ | Error de grupo-mes ↓ |
|---|---|---|---|---|
| CQ | 137.7 | 30.7 | 43.1% | 1 pp |
| FQ | 136.4 | 30.6 | 43.1% | 0.9 pp |
| FQ + BU L3 | 136 | 30.6 | 43.1% | 0.9 pp |

![Diferencias de estimación](charts/diferencia-log-loss.png)

FQ frente a CQ: cambio de log-loss ×1000 -1.3, IC95 [-1.7, -0.8]; cambio de captura <0.1 pp, IC95 [-0.1, 0.2]. El empate o una diferencia pequeña de captura no invalida por sí solo una mejora de estimación.

FQ + BU L3 frente a CQ: cambio de log-loss ×1000 -1.7, IC95 [-2.2, -1.3]; cambio de captura 0 pp, IC95 [0, 0]. El empate o una diferencia pequeña de captura no invalida por sí solo una mejora de estimación.

FQ + BU L3 frente a FQ: cambio de log-loss ×1000 -0.5, IC95 [-0.7, -0.2]; cambio de captura >−0.1 pp, IC95 [-0.2, 0.1]. El empate o una diferencia pequeña de captura no invalida por sí solo una mejora de estimación.

## Capacidad y esfuerzo

![Capacidad y captura](charts/capacidad-captura.png)

La capacidad ponderada es exacta en cada foto. Para conversaciones de RH se incluyen también los escenarios de grupos completos: excluir o incluir todo el bloque empatado que cruza el límite. Las personas efectivas ponderadas son capacidad equivalente; no una lista de personas seleccionadas.

| Modelo | Capacidad | Captura | Error grupo-mes | Personas/foto exactas | Grupos/foto | Rango de personas con grupos completos |
|---|---|---|---|---|---|---|
| CQ | 10% | 15.9% | 1.7 pp | 3438.7 | 4.7 | 2944–7300 |
| CQ | 20% | 29.2% | 1.1 pp | 6877.3 | 5 | 3110–7437 |
| CQ | 30% | 43.1% | 1 pp | 10315.9 | 8.6 | 9614–12820 |
| FQ | 10% | 15.8% | 1.6 pp | 3438.7 | 4.7 | 2944–7300 |
| FQ | 20% | 29.1% | 1 pp | 6877.3 | 4.9 | 2989–7401 |
| FQ | 30% | 43.1% | 0.9 pp | 10315.9 | 8.5 | 9240–12820 |
| FQ + BU L3 | 10% | 15.7% | 1.6 pp | 3438.7 | 4.6 | 2936–7184 |
| FQ + BU L3 | 20% | 29% | 1 pp | 6877.3 | 4.7 | 2936–7401 |
| FQ + BU L3 | 30% | 43.1% | 0.9 pp | 10315.9 | 8.6 | 9614–12820 |

## Subdivisión selectiva por BU L3

Se conservan los padres no priorizados y se subdividen sólo los padres inicialmente priorizados. Se mantienen al menos dos hijos BU identificables con soporte, reuniendo categorías restantes en un remanente; si éste queda pequeño se conserva el padre. La prioridad se vuelve a ordenar sobre la partición completa para mantener capacidad.

| Modelo | Capacidad | Mínimo hijo | Mediana de personas/grupo priorizado | Captura | Error | Pasa en ambos periodos |
|---|---|---|---|---|---|---|
| CQ | 10% | 100 | 218.5 | 15.6% | 2.1 pp | No |
| CQ | 10% | 150 | 370.4 | 15.6% | 2 pp | No |
| CQ | 10% | 200 | 470.9 | 15.5% | 1.9 pp | No |
| CQ | 20% | 100 | 247.4 | 29.6% | 1.5 pp | No |
| CQ | 20% | 150 | 411.3 | 29.5% | 1.4 pp | No |
| CQ | 20% | 200 | 490.9 | 29.4% | 1.4 pp | No |
| CQ | 30% | 100 | 225.4 | 42.4% | 1.3 pp | No |
| CQ | 30% | 150 | 415.6 | 42.5% | 1.2 pp | No |
| CQ | 30% | 200 | 517.7 | 42.5% | 1.2 pp | No |
| FQ | 10% | 100 | 232.3 | 16.6% | 1.9 pp | No |
| FQ | 10% | 150 | 358.5 | 16.5% | 1.8 pp | No |
| FQ | 10% | 200 | 491.2 | 16.5% | 1.8 pp | No |
| FQ | 20% | 100 | 307.4 | 30% | 1.3 pp | No |
| FQ | 20% | 150 | 446.9 | 30% | 1.3 pp | No |
| FQ | 20% | 200 | 509.4 | 30.1% | 1.3 pp | No |
| FQ | 30% | 100 | 246 | 43.4% | 1.2 pp | No |
| FQ | 30% | 150 | 412.9 | 43.4% | 1.2 pp | No |
| FQ | 30% | 200 | 489.3 | 43.3% | 1.2 pp | No |
| FQ + BU L3 | 10% | 100 | 213 | 16.6% | 1.7 pp | No |
| FQ + BU L3 | 10% | 150 | 352 | 16.5% | 1.7 pp | Sí |
| FQ + BU L3 | 10% | 200 | 498.8 | 16.6% | 1.7 pp | Sí |
| FQ + BU L3 | 20% | 100 | 265.9 | 29.6% | 1.3 pp | No |
| FQ + BU L3 | 20% | 150 | 433.4 | 29.6% | 1.3 pp | No |
| FQ + BU L3 | 20% | 200 | 505.8 | 29.7% | 1.3 pp | No |
| FQ + BU L3 | 30% | 100 | 233.1 | 43.6% | 1.2 pp | No |
| FQ + BU L3 | 30% | 150 | 396 | 43.5% | 1.1 pp | No |
| FQ + BU L3 | 30% | 200 | 466.8 | 43.3% | 1.1 pp | No |

Las guardas exigen mediana menor, capacidad conservada, pérdida de captura ≤2% relativo, aumento de error ≤0.1 pp y ningún aumento del verdadero REST. Las filas de 100 personas son el escenario principal; 150 y 200 son sensibilidades, sin escoger retrospectivamente un umbral para declarar éxito.

## QVoice: ausencia, información parcial y cobertura

### aug_dec_2025

**CQ**. Cobertura = personas de la foto con todos los campos requeridos válidos / todas las personas de la foto. Se informa además disponibilidad por campo en las fichas; no equivale a participación entre invitados.

| Estado | Personas distintas en el periodo | Observaciones persona-mes | Riesgo medio | Observado | Error absoluto |
|---|---|---|---|---|---|
| ausente | 13726 | 60865 | 2.8 | 3 | 0.2 |
| completa | 19841 | 97908 | 2.9 | 2.8 | 0.1 |
| parcial | 1907 | 9402 | 4 | 3.4 | 0.6 |

En información **completa**, el cambio de riesgo QVoice menos RH es -0.1 pp; cambio de log-loss ×1000 -1.7, IC95 [-2.5, -1]. Coincidencia exacta con RH: No.

En información **parcial**, el cambio de riesgo QVoice menos RH es 0.6 pp; cambio de log-loss ×1000 0.3, IC95 [-2.6, 3.1]. Coincidencia exacta con RH: No.

En información **ausente**, el cambio de riesgo QVoice menos RH es <0.1 pp; cambio de log-loss ×1000 0.2, IC95 [inferior a 0, 0.4]. Coincidencia exacta con RH: No.

**FQ**. Cobertura = personas de la foto con todos los campos requeridos válidos / todas las personas de la foto. Se informa además disponibilidad por campo en las fichas; no equivale a participación entre invitados.

| Estado | Personas distintas en el periodo | Observaciones persona-mes | Riesgo medio | Observado | Error absoluto |
|---|---|---|---|---|---|
| ausente | 13726 | 60865 | 2.8 | 3 | 0.2 |
| completa | 19841 | 97908 | 3 | 2.8 | 0.2 |
| parcial | 1907 | 9402 | 4 | 3.4 | 0.6 |

En información **completa**, el cambio de riesgo QVoice menos RH es >−0.1 pp; cambio de log-loss ×1000 -1.4, IC95 [-2.2, -0.7]. Coincidencia exacta con RH: No.

En información **parcial**, el cambio de riesgo QVoice menos RH es 0.6 pp; cambio de log-loss ×1000 0.6, IC95 [-2.1, 3.2]. Coincidencia exacta con RH: No.

En información **ausente**, el cambio de riesgo QVoice menos RH es >−0.1 pp; cambio de log-loss ×1000 0.2, IC95 [inferior a 0, 0.5]. Coincidencia exacta con RH: No.

**FQ + BU L3**. Cobertura = personas de la foto con todos los campos requeridos válidos / todas las personas de la foto. Se informa además disponibilidad por campo en las fichas; no equivale a participación entre invitados.

| Estado | Personas distintas en el periodo | Observaciones persona-mes | Riesgo medio | Observado | Error absoluto |
|---|---|---|---|---|---|
| ausente | 13726 | 60865 | 2.8 | 3 | 0.2 |
| completa | 19841 | 97908 | 3 | 2.8 | 0.2 |
| parcial | 1907 | 9402 | 4 | 3.4 | 0.6 |

En información **completa**, el cambio de riesgo QVoice menos RH es -0.1 pp; cambio de log-loss ×1000 -1.4, IC95 [-2.2, -0.7]. Coincidencia exacta con RH: No.

En información **parcial**, el cambio de riesgo QVoice menos RH es 0.5 pp; cambio de log-loss ×1000 0.7, IC95 [-1.9, 3.1]. Coincidencia exacta con RH: No.

En información **ausente**, el cambio de riesgo QVoice menos RH es >−0.1 pp; cambio de log-loss ×1000 0.2, IC95 [-0.1, 0.5]. Coincidencia exacta con RH: No.

### jan_feb_2026

**CQ**. Cobertura = personas de la foto con todos los campos requeridos válidos / todas las personas de la foto. Se informa además disponibilidad por campo en las fichas; no equivale a participación entre invitados.

| Estado | Personas distintas en el periodo | Observaciones persona-mes | Riesgo medio | Observado | Error absoluto |
|---|---|---|---|---|---|
| ausente | 11236 | 21956 | 3 | 3.8 | 0.8 |
| completa | 23043 | 45984 | 3.3 | 3.3 | 0.1 |
| parcial | 1169 | 2336 | 4.7 | 3.6 | 1 |

En información **completa**, el cambio de riesgo QVoice menos RH es -0.2 pp; cambio de log-loss ×1000 -2.3, IC95 [-3.2, -1.3]. Coincidencia exacta con RH: No.

En información **parcial**, el cambio de riesgo QVoice menos RH es 0.9 pp; cambio de log-loss ×1000 0.8, IC95 [-4.2, 5.6]. Coincidencia exacta con RH: No.

En información **ausente**, el cambio de riesgo QVoice menos RH es -0.1 pp; cambio de log-loss ×1000 0.6, IC95 [0.4, 0.9]. Coincidencia exacta con RH: No.

**FQ**. Cobertura = personas de la foto con todos los campos requeridos válidos / todas las personas de la foto. Se informa además disponibilidad por campo en las fichas; no equivale a participación entre invitados.

| Estado | Personas distintas en el periodo | Observaciones persona-mes | Riesgo medio | Observado | Error absoluto |
|---|---|---|---|---|---|
| ausente | 11236 | 21956 | 3 | 3.8 | 0.7 |
| completa | 23043 | 45984 | 3.3 | 3.3 | <0.1 |
| parcial | 1169 | 2336 | 4.6 | 3.6 | 1 |

En información **completa**, el cambio de riesgo QVoice menos RH es -0.1 pp; cambio de log-loss ×1000 -1.9, IC95 [-2.8, -1.1]. Coincidencia exacta con RH: No.

En información **parcial**, el cambio de riesgo QVoice menos RH es 0.9 pp; cambio de log-loss ×1000 1.1, IC95 [-3.7, 5.7]. Coincidencia exacta con RH: No.

En información **ausente**, el cambio de riesgo QVoice menos RH es -0.1 pp; cambio de log-loss ×1000 0.7, IC95 [0.4, 1]. Coincidencia exacta con RH: No.

**FQ + BU L3**. Cobertura = personas de la foto con todos los campos requeridos válidos / todas las personas de la foto. Se informa además disponibilidad por campo en las fichas; no equivale a participación entre invitados.

| Estado | Personas distintas en el periodo | Observaciones persona-mes | Riesgo medio | Observado | Error absoluto |
|---|---|---|---|---|---|
| ausente | 11236 | 21956 | 3.1 | 3.8 | 0.6 |
| completa | 23043 | 45984 | 3.3 | 3.3 | <0.1 |
| parcial | 1169 | 2336 | 4.6 | 3.6 | 1 |

En información **completa**, el cambio de riesgo QVoice menos RH es -0.1 pp; cambio de log-loss ×1000 -1.9, IC95 [-2.7, -1]. Coincidencia exacta con RH: No.

En información **parcial**, el cambio de riesgo QVoice menos RH es 0.9 pp; cambio de log-loss ×1000 1.1, IC95 [-3.5, 5.7]. Coincidencia exacta con RH: No.

En información **ausente**, el cambio de riesgo QVoice menos RH es -0.1 pp; cambio de log-loss ×1000 0.6, IC95 [0.3, 1]. Coincidencia exacta con RH: No.

Los estados `missing`, `no_linked_row`, `different_employment_episode`, `no_available_wave` y `question_absent` se conservan según la fuente. Un valor nunca aprendido deja en cero los indicadores de ese término, manteniendo intercepto y otros términos. La ausencia no demuestra descontento ni implica volver automáticamente al modelo RH.

## Calibración y estabilidad

| Periodo | Modelo | Sesgo global | IC95 sesgo | Etapa R6 | Recomendar corrección |
|---|---|---|---|---|---|
| aug_dec_2025 | CQ | <0.1 pp | [-0.1, 0.2] | Identidad: no activa umbral | No |
| aug_dec_2025 | FQ | <0.1 pp | [-0.1, 0.2] | Identidad: no activa umbral | No |
| aug_dec_2025 | FQ + BU L3 | 0.1 pp | [-0.1, 0.2] | Identidad: no activa umbral | No |
| jan_feb_2026 | CQ | -0.3 pp | [-0.4, -0.1] | Escalar contrastado | No |
| jan_feb_2026 | FQ | -0.2 pp | [-0.4, inferior a 0] | Escalar contrastado | No |
| jan_feb_2026 | FQ + BU L3 | -0.2 pp | [-0.4, inferior a 0] | Escalar contrastado | No |

Las cinco bandas usan límites comunes fijados con CQ en la última foto anterior a cada periodo. Los límites, diagnósticos por mes/banda/grupo y supresiones están guardados. Un escalar global no garantiza corregir brechas locales.

| Modelo | Transición | Personas comunes | Cambio absoluto riesgo | Correlación ranking | Solapamiento prioridad ponderada | Cambio de encuesta/modelo |
|---|---|---|---|---|---|---|
| CQ | 2025-08-24 → 2025-09-28 | 32888 | 0.2 pp | 1 | 93.7% | No |
| CQ | 2025-09-28 → 2025-10-26 | 33151 | 0.2 pp | 1 | 96.8% | No |
| CQ | 2025-10-26 → 2025-11-23 | 33295 | 0.3 pp | 1 | 94.4% | No |
| CQ | 2025-11-23 → 2025-12-28 | 33366 | 0.6 pp | 0.9 | 85.1% | No |
| CQ | 2025-12-28 → 2026-01-25 | 34631 | 0.8 pp | 0.9 | 89.5% | Sí |
| CQ | 2026-01-25 → 2026-02-22 | 34828 | 0.2 pp | 1 | 93% | No |
| FQ | 2025-08-24 → 2025-09-28 | 32888 | 0.2 pp | 1 | 93.7% | No |
| FQ | 2025-09-28 → 2025-10-26 | 33151 | 0.2 pp | 1 | 96.8% | No |
| FQ | 2025-10-26 → 2025-11-23 | 33295 | 0.3 pp | 1 | 94.4% | No |
| FQ | 2025-11-23 → 2025-12-28 | 33366 | 0.6 pp | 1 | 85.8% | No |
| FQ | 2025-12-28 → 2026-01-25 | 34631 | 0.8 pp | 0.9 | 77.9% | Sí |
| FQ | 2026-01-25 → 2026-02-22 | 34828 | 0.2 pp | 1 | 93% | No |
| FQ + BU L3 | 2025-08-24 → 2025-09-28 | 32888 | 0.2 pp | 1 | 93.7% | No |
| FQ + BU L3 | 2025-09-28 → 2025-10-26 | 33151 | 0.2 pp | 1 | 96.8% | No |
| FQ + BU L3 | 2025-10-26 → 2025-11-23 | 33295 | 0.3 pp | 1 | 94.4% | No |
| FQ + BU L3 | 2025-11-23 → 2025-12-28 | 33366 | 0.6 pp | 1 | 85.1% | No |
| FQ + BU L3 | 2025-12-28 → 2026-01-25 | 34631 | 0.8 pp | 0.9 | 89.5% | Sí |
| FQ + BU L3 | 2026-01-25 → 2026-02-22 | 34828 | 0.2 pp | 1 | 93% | No |

El anexo separa altas/bajas, cambio sobre personas comunes, cambio del promedio total y residual de composición. El salto entre diciembre de 2025 y enero de 2026 coincide con una nueva encuesta y un nuevo ajuste; no se atribuye todo el movimiento a cambios de opinión.

## Denominadores, privacidad y límites

| Periodo | Personas distintas | Observaciones persona-mes | Exposiciones con evento | Personas con evento | Salidas únicas |
|---|---|---|---|---|---|
| aug_dec_2025 | 35474 | 168175 | 4896 | 1748 | 1750 |
| jan_feb_2026 | 35448 | 70276 | 2433 | 1339 | 1340 |

Las salidas únicas no coinciden exactamente con personas con evento: una persona puede tener más de una salida tras una recontratación. El conteo independiente se guardó en `input-evidence/unique-events.json`. Las fichas que sólo permiten identificar personas con evento no las rotulan como salidas únicas.

Los intervalos de tasas observadas, sesgos y diferencias de métricas usan 500 remuestreos de personas compartidos entre modelos, manteniendo juntos todos sus meses y el peso de cada periodo. Las prioridades quedan fijas. El intervalo aproximado del riesgo medio usa el gradiente del R6 y la covarianza agrupada por persona de RH y QVoice, incluyendo su dependencia. Ninguno es un intervalo de predicción individual; no incluyen toda la incertidumbre de elegir variables/grupos ni toda la dependencia entre equipos.

Los grupos observados requieren 30 personas y 30 personas con evento. Si hay celdas pequeñas se suprime el bloque observado completo para evitar reconstruirlas por resta; esto incluye eventos, tasas, errores e intervalos. El riesgo medio y cobertura sólo aparecen donde el soporte de población permite publicarlos. Las limitaciones de soporte no equivalen a buen o mal desempeño.

IOS en C carece de acreditación histórica de publicación; QVoice usa una política anual, pero su fecha real de publicación no está acreditada. No se afirma que toda la información estuviera operacionalmente disponible en el pasado. La fecha RH, el año de encuesta y la disponibilidad acreditada se mantienen separados.

## Preparación para RH

La comparación permite valorar estimadores y agrupaciones retrospectivas. La preparación para RH exige, además, responsables funcionales, contraste con evidencia organizacional, fechas acreditadas y seguimiento posterior. Las acciones de las fichas son hipótesis: revisar soporte, vacantes, desarrollo y coordinación, sin prometer que cambiar una señal reducirá salidas.

Las diferencias descriptivas por región, nivel, antigüedad y QVoice no se etiquetan automáticamente como sesgo injustificado. Sus agregados, representación en prioridad y errores publicables se consultan en [diagnósticos por segmento](segmentos.md).

## Archivos y reproducción

- [Tabla de 44 variables en Excel](documentacion/variables-44.xlsx), con clasificaciones, acciones, tratamientos y categorías extraídas de los modelos.
- [Primera matriz documental](documentacion/matriz-comentarios.md) y [cierre de comentarios](cierre-comentarios.md).
- [Fichas históricas de grupos](fichas/indice.md).
- [Resultados completos](results.json), [verificación](verification.json) y [anexo técnico](anexo-tecnico.md).
- Ejecutable: `tools/engineering_julia_rh_review.py`; configuración: `config/julia_rh_review_20261012.json`; render: `tools/render_julia_rh_review.py`.

La ejecución conserva modelos y agregados; ninguna fila, llave ni predicción individual se persiste. Los modelos CQ previos permanecen intactos.
