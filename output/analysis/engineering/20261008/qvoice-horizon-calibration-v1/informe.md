# B + QVoice: prueba de calibración a seis meses

**Modo:** presentation. Evaluación retrospectiva; artefactos experimentales.

Conservar B + QVoice sin corrección posterior como candidato principal. El nuevo escalar no mejora conjuntamente log-loss, Brier y calibración; no reemplazar B de la presentación.

## Resultados en las mismas cohortes

Riesgo de salida voluntaria durante los seis meses siguientes a cada snapshot. Engineering: empleados regulares activos, excluyendo RF360. Los registros son persona-snapshot; una persona puede aparecer en varios meses.

| Snapshots | Variante | Riesgo observado % | Riesgo estimado % | Error general pp | Error top 20% pp | Log-loss × 1000 | Brier × 1000 |
|---|---|---:|---:|---:|---:|---:|---:|
| Ago–dic 2025 | B | 2.9 | 3 | 0.1 | 0.6 | 129.1 | 28.1 |
| Ago–dic 2025 | B + Q sin corrección | 2.9 | 3 | 0.1 | 1 | 128.4 | 28.1 |
| Ago–dic 2025 | Calibración mensual previa | 2.9 | 2.6 | 0.3 | 0.1 | 128.4 | 28.1 |
| Ago–dic 2025 | Escalar a seis meses (identidad) | 2.9 | 3 | 0.1 | 1 | 128.4 | 28.1 |
| Ene–feb 2026 | B | 3.5 | 3.4 | 0.1 | 1 | 148.1 | 33.3 |
| Ene–feb 2026 | B + Q sin corrección | 3.5 | 3.2 | 0.3 | 0.2 | 146.1 | 33.1 |
| Ene–feb 2026 | Calibración mensual previa | 3.5 | 2.9 | 0.6 | <0.1 | 146.9 | 33.2 |
| Ene–feb 2026 | Escalar a seis meses | 3.5 | 2.8 | 0.7 | 0.6 | 146.7 | 33.1 |

Log-loss y Brier: menor es mejor. Se multiplican por 1000 para hacer visibles las diferencias sin añadir decimales. Error de calibración: distancia absoluta entre riesgo medio observado y estimado, en puntos porcentuales.

## Cómo se aprendió el escalar

`R_ajustada = 1 - (1 - R_sin)^exp(a)`. Un solo parámetro modifica el nivel y conserva exactamente el orden de riesgo acumulado. El ajuste minimiza log-loss a seis meses; el candidato sin corrección equivale a a = 0.

- **Ago–dic 2025**, corte 2025-08-01: sin ajuste por historia insuficiente; 0 orígenes; cambio del hazard acumulado: 0%. Orígenes: ninguno admisible.
- **Ene–feb 2026**, corte 2026-01-01: ajuste estimado; 3 orígenes; cambio del hazard acumulado: -12.3%. Orígenes: 2025-04-27, 2025-05-25, 2025-06-29.
- **Artefacto final**, corte 2026-09-07: ajuste estimado; 6 orígenes; cambio del hazard acumulado: +3.3%. Orígenes: 2025-09-28, 2025-10-26, 2025-11-23, 2025-12-28, 2026-01-25, 2026-02-22.

Cada ajuste auxiliar conserva dos intervalos mensuales reservados como el modelo guardado. Los primeros ajustes QVoice tienen sólo un intervalo de entrenamiento; el detalle por origen registra esta limitación. El calibrador sólo usa resultados a seis meses que ya habían terminado a su fecha de corte.

## Ranking y magnitud

- Ago–dic 2025: 35474 personas, 168175 registros, 4896 registros con salida posterior. PR-AUC sin corrección mejora 10.1% frente a B; lift del 10% superior: 2. El escalar cambia log-loss 0% y Brier 0% frente a no corregir.
- Ene–feb 2026: 35448 personas, 70276 registros, 2432 registros con salida posterior. PR-AUC sin corrección mejora 14.9% frente a B; lift del 10% superior: 2.2. El escalar cambia log-loss 0.4% y Brier 0.1% frente a no corregir.

## Por qué el ajuste empeoró este periodo

Las predicciones históricas de abril–junio de 2025 llevaron a reducir el hazard acumulado en 12.3%. En enero–febrero de 2026, el modelo sin corrección ya subestimaba el riesgo medio. Aplicar esa reducción lo alejó más del resultado real. La corrección sí mejoró el objetivo en la historia usada para aprenderla, pero ese ajuste no se trasladó bien a este periodo posterior. No se demuestra que el cambio de wave sea la causa.

Frente a no corregir, el log-loss subió 0.4%. La diferencia absoluta fue positiva también en el bootstrap por persona: IC del 95% de 0.4 a 0.9 unidades de log-loss × 1000. Este intervalo está condicionado a los modelos y a los meses observados.

## Ganancia de QVoice frente a B

- Ago–dic 2025: log-loss menor en 0.5% y Brier menor en 0.1%.
- Ene–feb 2026: log-loss menor en 1.3% y Brier menor en 0.5%.

La reducción de pérdida es modesta; la mejora relativa de PR-AUC es mayor. B conserva menor error de calibración general en ambos periodos, por lo que B + QVoice sin corrección sigue siendo un candidato y no un reemplazo aprobado.

## Rendimiento

- Ejecución de datos y modelos: 6.3 minutos. 11 ajustes B y 9 correcciones QVoice; cero búsquedas de subconjuntos.
- Predicción optimizada: 2.3 veces la velocidad en la misma cohorte de 20000 registros, mediana de tres repeticiones. Equivalencia numérica comprobada con tolerancia de 1e-12.
- La reducción frente a la búsqueda previa combina menos ajustes y optimización; no representa ejecutar la misma búsqueda completa más rápido.

## Límites y artefactos

- Los periodos ya fueron inspeccionados. La selección de variables y L2 se hereda de una exploración posterior a algunos orígenes auxiliares; la validación es condicional y retrospectiva. Agosto de 2025 no prueba el escalar por falta de historia.
- Las ventanas se solapan. El bootstrap por persona conserva esa repetición, pero no estima toda la incertidumbre por calendario, selección o entrenamiento.
- La wave cambia entre 2025 y 2026; transportar el nivel de riesgo y la redacción Career añade incertidumbre. Estos resultados no demuestran causalidad.
- El modelo final escalar queda como candidato experimental; también se guarda la versión final sin corrección. No se reemplaza B ni la presentación.
- `comparison-results.json`: métricas precisas, diferencias pareadas y sus intervalos. `calibration-history.json`: cortes y métricas agregadas de los ajustes auxiliares. `timings.json`: tiempos por etapa. `trained-model/`: los dos candidatos.
- Fuente SQL: `queries/profiles/engineering_qvoice_horizon_calibration_20261008.sql`. Ejecución: 2026-10-08T19:31:27+00:00. Corte de datos: 2026-09-07. No se guardan filas, identificadores ni scores individuales.
