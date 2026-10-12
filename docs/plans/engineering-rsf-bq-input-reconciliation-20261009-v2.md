# Reconciliación BQ: revisión de la etiqueta histórica

Fecha: 9-oct-2026. Modo `presentation`. Complementa el plan del 8-oct-2026,
que se conserva. No cambia scores ni artefactos anteriores.

## Motivo de la revisión

La alineación uno a uno encontró 238451 observaciones comunes, sin duplicados,
faltantes ni diferencias de episodio. Una etiqueta `y_6m` difiere; `y_next` y
el fin de intervalo coinciden. La afirmación previa de etiquetas idénticas
no se sostiene para toda la ventana agosto 2025–febrero 2026.

## Pregunta y método

¿La diferencia se explica por el límite global de fecha de registro en BQ?
Tipo semántico: `derived_feature`. Recalcular por persona-foto dos etiquetas
de salida voluntaria en (foto, foto + 6 meses]: con todos los eventos efectivos
hasta 7-sep-2026, y con los registrados en fotos hasta esa misma frontera.
Población: Engineering, Employee, Regular, activo, sin RF360; mismas siete fotos.
SQL agregado: `queries/audits/engineering_rsf_bq_label_contract_20261009.sql`.
Regla previa: 238451 observaciones, una diferencia en dirección C=1/BQ=0,
cero diferencias inversas. Persistir sólo agregados, hash, fecha y resultado.

## Comparación y aceptación revisadas

El modelo BQ se reconstruye con sus entradas y etiquetas históricas para
comprobar sus métricas archivadas con tolerancia 1e-8. Las predicciones de
todos los modelos se comparan usando la etiqueta común C/RSF y los mismos
cortes de grupos. Las diferencias entre etiquetas deben reproducir el audit
agregado; cualquier diferencia adicional detiene la conciliación.

Así se distingue reproducibilidad del archivo de comparación entre modelos.
El informe debe explicar la única discrepancia de etiqueta y el límite temporal
heredado de C. No se presenta el contrato C como un historial completo de lo
que estaba registrado físicamente al 7-sep-2026.
