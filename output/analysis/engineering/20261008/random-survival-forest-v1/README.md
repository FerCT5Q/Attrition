# Experimento Random Survival Forest

Modo `presentation`. Consulta y evaluación del 8–9 oct 2026; corte de conocimiento
7-sep-2026. Ingeniería, empleados regulares activos, sin RF360; salida voluntaria
en los seis meses posteriores a cada foto mensual.

- `informe.md`: conclusión y comparación con B, C, variantes de grupos y QVoice.
- `historical-results.json`: cuatro periodos de seis fotos, febrero 2024–enero 2026.
- `qvoice-results.json`: agosto–diciembre 2025 y enero–febrero 2026, comparables con QVoice.
- `extension.json`: febrero 2026 con los modelos de agosto 2025.
- `folds/<origen>/`: selecciones, calibración y modelos históricos.
- `trained-model/`: selección y parámetros del corte final; no usar sus resultados
  retrospectivamente como si el ajuste hubiera ocurrido en 2024 o 2025.
- `runtime-versions.json`: versiones del entorno, incluida scikit-survival 0.28.0.
- `manifest.json`, `preservation.json` y `source/`: trazabilidad y conservación.
- `bq-input-reconciliation.json` y `qvoice-comparison/`: restauración del
  contrato histórico B + QVoice, alineación de población y métricas archivadas.
- `verdict.json` y `verdict-uncalibrated.json`: criterio de decisión para ambas
  variantes RSF; `artifact-checks.json`: conciliación de los artefactos finales.

Los archivos de interrupciones y `qvoice-reconciliation-failure.json` conservan
los intentos previos. El estado final se consulta en `manifest.json` y las
conciliaciones completadas en `qvoice-comparison/` y `artifact-checks.json`.

## Modelo e inferencia

Cada `model.json` describe las variables, categorías, entrenamiento y escalar de
calibración. `forest-parameters.npz` guarda sólo divisiones y curvas estimadas:
no contiene filas, llaves, muestras bootstrap ni etiquetas individuales.

`predict_export(ruta_del_modelo, frame_autorizado)` en
`tools/engineering_random_survival_forest.py` reconstruye R6 sin calibrar.
El escalar de `model.json` aplica `1-(1-R6)^exp(log_multiplier)`. La reconstrucción
se contrastó contra el bosque antes de guardar cada modelo. Los resultados
individuales de esa función deben permanecer en RAM bajo la autorización vigente.

El bosque aprende curvas hasta seis meses; los grupos para revisión son una
capa adicional de cortes comunes o de reglas del árbol explicativo. El árbol
explicativo no sustituye las probabilidades del bosque.

## Reproducción

El script usa `config/engineering_rsf_20261008.json`. Para repetir el experimento,
crear una configuración con otra carpeta de salida. `--resume` sólo corresponde
a una ejecución interrumpida con la misma configuración; reutiliza sus modelos
completos y vuelve a cargar los datos en RAM. La regla de publicación exige
resultados agregados y nunca permite guardar las filas para acelerar una repetición.

Si la historia ya está completa, `--resume --phase comparison` carga sólo
enero de 2025 a febrero de 2026 y conserva la comparación con QVoice.
Después, `--resume --phase final` carga la historia completa para el ajuste
final y reutiliza las comparaciones. Ambas fases usan los mismos criterios,
fechas de corte y modelos históricos. La conexión se renueva por año, con
keepalive y reintento acotado; los años completos permanecen sólo en RAM.

La compactación bootstrap conserva muestras, pesos, semillas y tiempos; compara
el primer árbol de cada ajuste optimizado con la implementación completa. Los
registros `compact-bootstrap-checks.json` documentan esa equivalencia.
