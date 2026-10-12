# Calibración de B + QVoice a seis meses

## Pregunta y diseño previo a la ejecución

Comparar el modelo guardado sin corrección, la calibración mensual previa y una
corrección de un parámetro aprendida directamente sobre el riesgo a seis meses.
El control es B, con su receta y L2 anteriores. Población: empleados regulares
activos de Engineering, excluyendo RF360, por snapshot. Corte: 7 de septiembre
de 2026. Modo: `presentation`. Se conserva la política wave Y para snapshots Y+1.

La transformación es `R_ajustada = 1 - (1 - R_original)^exp(a)`. Identidad:
`a = 0`. El ajuste minimiza log-loss binomial del evento a seis meses, con límites
predefinidos para `a`. Preserva el orden del riesgo acumulado; también equivale
a multiplicar por `exp(a)` el hazard acumulado de cada mes del pronóstico.

Se reutilizan los modelos y variables elegidos anteriormente. Para aprender el
escalar se generan predicciones auxiliares temporales: en cada origen se ajusta
B y la corrección QVoice respetando los dos intervalos mensuales reservados en
la receta guardada. Se exige al menos un intervalo QVoice y 30 eventos para el
ajuste auxiliar; los primeros ajustes tienen poca historia y se reportan así.
Se usan los últimos seis orígenes
con etiqueta a seis meses madura al corte; mínimo tres. Si no alcanza, se aplica
identidad. Agosto de 2025 carece de historia suficiente y no valida el escalar.
No se aplican coeficientes finales a meses anteriores para fabricar historia.

La selección de variables y L2 es heredada de una exploración posterior a parte
de los orígenes auxiliares. Es una evaluación retrospectiva condicionada a esa
selección; no constituye validación externa nueva. Las ventanas a seis meses
se solapan: no son muestras temporales independientes. El bootstrap por persona
conserva su repetición en varios snapshots, pero no captura todos los shocks de
calendario ni la incertidumbre de selección y entrenamiento.

## Comparación y reglas de aceptación

- Log-loss y Brier fuera de muestra, riesgo medio estimado/observado, error
  general y del quintil superior; PR-AUC y lift para confirmar el mismo orden.
- Reconstruir B de referencia; reconciliar todas las métricas previas con
  tolerancia absoluta de 1e-8. Desacuerdos bloquean las conclusiones.
- Verificar predicción optimizada contra la implementación original, tolerancia
  absoluta de 1e-12, y registrar tiempo comparable en la misma cohorte.
- Validar límites temporales, convergencia, identidad y conservación de orden.
- Bootstrap pareado por persona para diferencias de log-loss y Brier, 500 réplicas.
- Informar si el nuevo escalar mejora log-loss sin empeorar Brier, error general
  o error del quintil superior frente a no corregir. No promover automáticamente
  un artefacto: sólo hay un periodo principal donde el escalar puede evaluarse.

## Rendimiento y persistencia

No repetir los 2340 ajustes de selección. Leer Redshift una vez, cada wave una
vez, seleccionar sólo los campos necesarios y omitir ordinales Heartbeat que
no se usan. Reutilizar B por origen y sumar coeficientes categóricos para
predicción sin construir matrices densas. Cronometrar cada etapa; no atribuir
toda reducción de tiempo a optimización, pues también disminuye el trabajo.

Usar el helper de `attrition-redshift-db` y la autorización
`config/attrition_model_in_memory_training_authorization_20261001.json`.
Filas, llaves y scores sólo en memoria; guardar únicamente parámetros,
resultados agregados y hashes. Consulta nueva en `queries/profiles/`.
No sobrescribir la búsqueda anterior ni el modelo B de la presentación.
