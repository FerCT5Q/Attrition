# Señales históricas candidatas del modelo D

Fecha de revisión: 10-oct-2026. Modo: `presentation`.

## Flujo histórico

El modelo C usa conteos a doce meses de cambios de manager y salidas del
equipo. D prueba si la recencia, el tamaño reconstruido del equipo del manager
actual y una tasa por exposición añaden información. Todas las señales se
reconstruyen para cada snapshot y sólo admiten eventos ocurridos y conocidos a
esa fecha.

No se cambió el score de ninguna variable del inventario. Esta revisión sólo
autoriza las representaciones para el experimento retrospectivo D.

## Cambios de manager a 3 y 6 meses

- **Pregunta:** ¿los conteos cortos son temporales y coherentes con 12 meses?
- **Motivo:** distinguir eventos recientes de historia más antigua.
- **Método:** reconstrucción agregada sobre 678849 persona-snapshots y 20
  snapshots; eventos deduplicados por fecha.
- **Regla:** `3m <= 6m <= 12m`, sin conteos negativos; eventos futuros o
  conocidos tarde no entran.
- **Resultado:** cero violaciones; cobertura con al menos un cambio a 12 meses
  de 27.1%.
- **Conclusión:** habilitada como candidata experimental.

## Salidas del equipo y recencia

- **Pregunta:** ¿3/6/12 meses y la última salida cuentan la misma historia?
- **Método:** se atribuye cada salida voluntaria al manager observado antes del
  evento y se exige que la terminación ya fuera conocida.
- **Regla:** monotonicidad, última fecha y banda de recencia sin
  contradicciones.
- **Resultado:** cero violaciones; cobertura de 23.9%. Se excluyeron 668
  asociaciones conocidas después del snapshot.
- **Conclusión:** habilitada como candidata experimental.

## Tamaño del equipo del manager actual

- **Pregunta:** ¿puede reconstruirse el tamaño contemporáneo del equipo?
- **Método:** conteo de empleados regulares activos con el mismo manager en el
  snapshot.
- **Regla:** cobertura completa cuando hay manager, conteos no negativos y
  bandas no vacías.
- **Resultado:** 678849 de 678849 filas reconstruidas; máximo 36. La diferencia
  absoluta media frente a `reg_non_intern_dir_reports` es 5 porque ese campo
  describe los reportes del empleado, no el tamaño del equipo de su manager.
- **Conclusión:** se usa la derivación con nombre explícito; no se considera
  reconciliación del campo almacenado ni evidencia para elevar su score.

## Intensidad de salidas por personas-mes

- **Pregunta:** ¿el conteo puede normalizarse por exposición histórica del
  equipo?
- **Método:** salidas voluntarias a 12 meses divididas entre personas-mes bajo
  el manager, multiplicadas por 100 y agrupadas en bandas.
- **Regla:** denominador positivo, numerador no negativo ni superior a la
  exposición, sin eventos futuros o conocidos tarde.
- **Resultado:** cero violaciones de denominador o exposición; todas las filas
  reciben banda.
- **Conclusión:** habilitada como candidata experimental. La tasa máxima de 50
  por 100 personas-mes corresponde a exposiciones pequeñas y se controla con
  bandas, penalización y validación temporal.

## Evidencia

Las consultas están en `queries/audits/engineering_model_d_*_20261010.sql` y
el ledger agregado en
`output/analysis/engineering/20261010/model-d-history-preflight-v1/evidence-ledger.json`.

