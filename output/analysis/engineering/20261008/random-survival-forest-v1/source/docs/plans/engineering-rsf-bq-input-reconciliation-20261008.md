# Reconciliación del contrato histórico de B + QVoice

Fecha: 8-oct-2026. Modo `presentation`. Complemento del experimento RSF.

## Pregunta y motivo

¿Se reproducen B + QVoice y sus calibraciones al restaurar exactamente sus
entradas históricas y evaluar sobre las mismas personas y fechas de C/RSF?
La primera conciliación reveló diferencias en probabilidades agregadas y
ranking. La inspección de los SQL identifica un contrato distinto para
`team_exits_12m`; atribuirlo sólo a empates numéricos fue una hipótesis incompleta.

## Concepto y frontera temporal

`team_exits_12m` es una `derived_feature`: banda de salidas voluntarias de
compañeros del manager directo en (foto menos 12 meses, foto], con membresía
del saliente según su última foto activa previa. El SQL original de BQ filtra
las salidas por fecha efectiva y conocimiento global al 7-sep-2026. El SQL de
C/RSF añade que la salida ya aparezca registrada al cierre de la foto.
La definición completa permanece en ambos SQL. Este paso restaura el contrato
del modelo archivado; no asigna ni cambia scores de variables.

Población: Engineering, Employee, Regular, activo, sin RF360. Grain:
persona-foto mensual. Comparación: agosto–diciembre de 2025 y enero–febrero
de 2026; outcome voluntario dentro de seis meses, completamente observado.
El riesgo de BQ conserva la limitación temporal de su entrada histórica.

## Método y regla previa

1. Leer sin reescribir
   `queries/profiles/engineering_qvoice_horizon_calibration_20261008.sql`.
   Reutilizar el cliente del skill `attrition-redshift-db`, modo read-only,
   whitelist original y la autorización RAM del 1-oct-2026.
2. Cargar sólo las fechas del bloque QVoice y alinear por persona-foto con la
   misma llave efímera. Exigir cero duplicados, faltantes y filas adicionales.
3. Exigir igualdad exacta de etiquetas, fin de intervalo y los tres indicadores
   de episodio. Así se pueden reutilizar las respuestas QVoice enlazadas.
4. Registrar únicamente conteos agregados de bandas discrepantes. Sustituir
   las entradas originales sólo en el predictor BQ; mantener los cortes de
   grupos del frame común C/RSF.
5. Exigir diferencias absolutas menores o iguales a 1e-8 respecto a las
   métricas archivadas de BQ, incluyendo PR-AUC y lift, en ambos periodos y
   sus tres variantes. Detener la conciliación si falla alguna.

## Evidencia y acción

`bq-input-reconciliation.json` registrará fechas, población, hashes SQL,
conteos de join, discrepancias de bandas, conclusión e impacto nulo en scores.
`qvoice-comparison/<periodo>-reconciliation.json` registrará las diferencias
predictivas contra el archivo. El informe explicará el contrato legado y su
limitación. Los modelos, consultas y resultados anteriores se preservan.
