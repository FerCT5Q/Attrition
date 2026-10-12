# QVoice mejora el ranking del modelo B, pero una leve pérdida de calibración impide incorporarlo todavía

Ejecución finalizada el 8 de octubre de 2026. Clasificación: `presentation`. Corte de conocimiento: 7 de septiembre de 2026.

## Decisión

Se probaron nueve variantes de QVoice dentro del modelo B de supervivencia discreta con enlace `cloglog`. Las nueve mejoraron PR-AUC y Brier frente a B en los dos periodos principales. Ninguna cumplió el gate completo porque el error absoluto de calibración general, promediado entre ambos periodos, fue ligeramente mayor que en B.

**El modelo B oficial se conserva sin QVoice.** La variante más útil para la siguiente iteración es **Q4 sola**: pasó siete de ocho comprobaciones, añadió señal frente al modelo que sólo conoce la disponibilidad de QVoice, tuvo la mayor cobertura entre las variantes de intención y evitó la ambigüedad histórica de Career y la menor cobertura del promedio de 33 preguntas.

## Qué se comparó

Para cada variante se ajustaron tres modelos sobre las mismas personas, snapshots y etiquetas:

1. **B:** las diez features vigentes del modelo seleccionado.
2. **B + disponibilidad:** B más el estado que explica si la respuesta QVoice podía enlazarse y usarse.
3. **B + respuesta:** B más el valor observado de QVoice y sus estados explícitos de ausencia.

La tercera comparación contra la segunda separa el valor de la respuesta del posible efecto de participación, enlace o disponibilidad.

La política temporal aplicada fue:

- QVoice 2024 para snapshots de 2025.
- QVoice 2025 para snapshots de 2026.
- QVoice 2026 queda reservada para snapshots de 2027.

Los periodos principales fueron agosto–diciembre de 2025, con cinco snapshots y 35,474 personas distintas, y enero–febrero de 2026, con dos snapshots y 35,448 personas distintas. Todos los modelos de una comparación usaron cohortes idénticas. La evaluación usa la salida voluntaria acumulada en los seis meses posteriores a cada snapshot.

## Resultado de las nueve variantes

Los cambios se calculan contra B. PR-AUC se expresa en puntos porcentuales; un cambio negativo de Brier es favorable. La calibración se muestra en puntos base y corresponde al promedio de los dos periodos; un valor positivo es desfavorable. La cobertura es la proporción de exposiciones mensuales con todas las respuestas requeridas disponibles.

| Variante | Cobertura | Δ PR-AUC 2025 / 2026 | Δ lift@10% 2025 / 2026 | Δ Brier × 10,000 2025 / 2026 | Δ calibración media | Checks aprobados | Decisión |
|---|---:|---:|---:|---:|---:|---:|---|
| Q4 | 62.3–67.5% | +0.5 / +0.8 pp | +0.2 / +0.4 | -0.7 / -1.2 | +2.1 pb | 7 de 8 | Sin mejora demostrada |
| Q12 | 60.8–66.3% | +0.3 / +0.4 pp | +0.1 / +0.2 | -0.4 / -0.6 | +4.4 pb | 6 de 8 | Sin mejora demostrada |
| Q4 + Q12 | 60.2–65.8% | +0.5 / +0.8 pp | +0.2 / +0.4 | -0.7 / -1.4 | +3.8 pb | 6 de 8 | Sin mejora demostrada |
| Q4 y Q12 favorables | 60.2–65.8% | +0.4 / +0.5 pp | +0.1 / +0.1 | -0.5 / -0.7 | +5.3 pb | 6 de 8 | Sin mejora demostrada |
| Career | 61.8–67.8% | +0.2 / +0.3 pp | <+0.1 / +0.1 | -0.3 / -0.3 | +1.2 pb | 6 de 8 | Sin mejora demostrada |
| Promedio 33 | 51.8–58.8% | +0.2 / +0.5 pp | +0.1 / +0.2 | -0.3 / -0.8 | +3.9 pb | 6 de 8 | Sin mejora demostrada |
| Q4 + Q12 + Career | 58.7–65.2% | +0.5 / +0.8 pp | +0.2 / +0.3 | -0.6 / -1.3 | +3.9 pb | 7 de 8 | Sin mejora demostrada |
| Q4 + Q12 + Career + promedio 33 | 51.7–58.7% | +0.5 / +0.8 pp | +0.2 / +0.3 | -0.6 / -1.3 | +4.0 pb | 7 de 8 | Sin mejora demostrada |
| Q4 + Q12 + Career + promedio 31 | 51.7–58.7% | +0.5 / +0.8 pp | +0.2 / +0.3 | -0.6 / -1.3 | +4.1 pb | 7 de 8 | Sin mejora demostrada |

Fuente: `comparison-results.json`, generado el 8 de octubre de 2026. Población: empleados regulares activos de Engineering, excluyendo RF360. Los conteos son personas distintas dentro de cada periodo; las métricas usan exposiciones persona-snapshot.

## Lectura del resultado

### La señal predictiva sí aparece

- Las nueve variantes aumentaron PR-AUC en ambos periodos. Los intervalos bootstrap de 95% quedaron por encima de cero en las 18 comparaciones contra B.
- Q4, Q4 + Q12 y las tres combinaciones amplias también aumentaron el lift del decil superior con intervalos por encima de cero en ambos periodos.
- Q4 redujo Brier en ambos periodos y su mejora permaneció por debajo de cero en los intervalos bootstrap. Esto indica una mejora consistente en el error probabilístico medio.
- La calibración del quintil de mayor riesgo mejoró para todas las variantes al promediar los dos periodos.

### El gate falla por calibración general

Para Q4, el error absoluto de calibración general promedio pasó de 7.0 puntos base en B a 9.1 puntos base con la respuesta QVoice. La diferencia fue de 2.1 puntos base:

- En agosto–diciembre de 2025, el riesgo observado y el estimado con Q4 fueron ambos 2.9%; Q4 mejoró la calibración.
- En enero–febrero de 2026, el riesgo observado fue 3.5% y Q4 estimó 3.3%; B quedó más cerca del total observado.

Los intervalos bootstrap de la diferencia de calibración incluyen cero. La evidencia no demuestra un deterioro estadísticamente claro, pero el criterio acordado era más estricto: no empeorar el valor puntual promedio. Por esa regla, ninguna variante puede promoverse aún.

### Q4 es la opción más parsimoniosa

Q4 ofrece un resultado casi igual al de Q4 + Q12 y las combinaciones mayores, con más cobertura y menos parámetros. También pasó las cuatro comprobaciones incrementales contra el modelo de disponibilidad. Agregar Career o el promedio de 33 preguntas no produjo una mejora material sobre Q4.

Career conserva además una limitación semántica: la redacción de 2024 no es exactamente la misma que en las waves posteriores. El promedio de 33 preguntas reduce la cobertura. La ablación con promedio de 31 preguntas, sobre la misma cohorte, produjo métricas prácticamente iguales al promedio de 33; el solapamiento con Q4 y Q12 no explica una mejora adicional.

## Coberturas que no deben confundirse

Los assessments muestran aproximadamente 80% de cobertura descriptiva para Intent to Stay alrededor del baseline anual. La cobertura de 60–68% de este experimento usa otro denominador: exposiciones mensuales de validación con enlace, continuidad del episodio laboral y todos los componentes requeridos. Las dos cifras responden preguntas distintas.

## Método e incertidumbre

- Modelo de hazard mensual discreto con enlace `cloglog`; riesgo acumulado a seis meses.
- Selección de L2 con Brier mensual en tres intervalos anteriores al periodo evaluado.
- Quinientas réplicas bootstrap pareadas por persona; todas sus observaciones mensuales permanecen juntas.
- Dos periodos principales completos. Los snapshots desde marzo de 2026 no se evaluaron porque no tenían seguimiento completo de seis meses dentro del corte fijado.
- La incertidumbre es condicional a los modelos ajustados; L2 no se vuelve a seleccionar en cada réplica.

## Recomendación

1. Mantener el modelo B vigente para la presentación y el uso actual.
2. Conservar **B + Q4** como candidato experimental.
3. Definir antes del siguiente corte una recalibración temporal basada sólo en historia disponible y volver a evaluar sin cambiar el gate.
4. Añadir el siguiente periodo completo de 2026 cuando sus seis meses de seguimiento estén cerrados.
5. Promover Q4 sólo si mantiene la mejora de ranking y Brier y elimina la pequeña pérdida de calibración general.

## Trazabilidad y privacidad

- [Resultados completos](comparison-results.json)
- [Configuración ejecutada](../../../../../config/qvoice_model_experiment_20261008.yaml)
- [Política temporal](../../../../../config/qvoice_annual_lag_policy_20261008.json)
- [SQL de ventanas temporales](../../../../../queries/audits/qvoice_model_annual_lag_windows_20261008.sql)
- [Validación del SQL del modelo](validation/model-sql-check.json)
- [Assessment de Intent to Stay](../../../../assessments/qvoice-model-20261008-intent-v2)
- [Assessment de Career](../../../../assessments/qvoice-model-20261008-career-v2)
- [Assessment del promedio de 33 preguntas](../../../../assessments/qvoice-model-20261008-mean33-v1)

No se guardaron filas de empleados, identificadores, respuestas individuales, scores individuales ni texto libre. Todos los resultados publicados son agregados y las cohortes superan el mínimo de 30.
