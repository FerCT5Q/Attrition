# Plan congelado: modelo D

Fecha: 10-oct-2026. Modo: `presentation`. Etapa: selección de modelo.

## Objetivo

Construir un candidato D que incorpore QVoice desde el ajuste, conserve la
historia aprendida por C y mejore la priorización o la precisión de los grupos
de alto riesgo. CQ permanece como referencia elegida hasta que D cumpla la
regla predefinida.

## Población y tiempo

- Engineering, Employee, Regular, activo, sin RF360.
- Observación persona-snapshot; outcome principal salida voluntaria en seis
  meses.
- Evaluación externa: agosto-diciembre de 2025 y enero-febrero de 2026.
- Frontera de conocimiento: 7-sep-2026.
- QVoice 2024 se usa en snapshots 2025; QVoice 2025 en snapshots 2026.
- Capacidad principal 30%; sensibilidades 20% y 40%.

## Diseño de candidatos

1. Reproducir C y CQ archivados.
2. Actualizar C mediante una corrección HR penalizada sobre el predictor C.
3. Ajustar conjuntamente correcciones HR y Q sobre C. Representaciones Q:
   Intent/Career; temas interpretables; temas más media33. L2 HR y Q en
   `{0.1, 1, 10}`.
4. Evaluar las interacciones preespecificadas Career×antigüedad,
   Career×tiempo desde promoción, Q4×salidas del equipo y
   Wellbeing×cambios de manager.
5. Evaluar bloques históricos, únicamente después de pasar auditoría:
   cambios de manager 3/6m; salidas del equipo 3/6m y recencia; span
   reconstruido del manager; intensidad de salidas por personas-mes.
6. Comparar hazard logit mensual y RSF con QVoice. Si no existe historia
   suficiente para selección RSF en un origen, usar la configuración RSF
   histórica predeclarada y marcarla como transferida.
7. Evaluar grupos comunes y, como diagnóstico secundario, adquisición,
   Career, Q4 y árbol sustituto de hasta 16 hojas. La promoción principal usa
   los grupos comunes para aislar el estimador.
8. Comparar identidad con calibración por grupo con shrinkage, entrenada sólo
   con predicciones temporales fuera del ajuste; si faltan tres fotos R6
   maduras, usar identidad.

## Selección interna

Usar las últimas tres fotos R6 maduras antes del origen, con entrenamiento que
termine antes de la primera. Si QVoice no tiene historia suficiente, usar las
últimas tres etiquetas mensuales maduras y registrar `monthly_fallback`.
Elegir menor log-loss entre candidatos con Brier dentro de 0.5% del mínimo;
para R6 exigir además PR-AUC al menos 98% del máximo. Desempatar por menos
parámetros y mayor penalización.

## Regla equilibrada de promoción

D puede sustituir CQ por una de dos rutas:

- Captura: mejora media al 30% de al menos 0.5 pp, IC95 inferior mayor que
  cero y error grupo-mes no peor por más de 0.1 pp.
- Precisión: captura no inferior con margen de 0.2 pp, IC95 compatible con ese
  margen, y reducción del error grupo-mes de al menos 10%.

En ambas rutas, log-loss y Brier no empeoran más de 0.5% relativo; el peor
error publicable no aumenta más de 0.1 pp; ningún periodo pierde más de 0.5 pp
de captura. Entre candidatos equivalentes se elige el más simple.

## Privacidad y conservación

Los datos persona-mes y respuestas sólo existen en RAM bajo
`config/attrition_model_in_memory_training_authorization_20261001.json`.
No se persisten llaves, filas, respuestas ni puntuaciones individuales. Los
resultados publicados son agregados con los mínimos vigentes. Todos los runs
anteriores se verifican por hash antes y después.

