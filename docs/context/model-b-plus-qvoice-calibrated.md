# Modelo B + QVoice calibrado

La ejecución del 8 de octubre de 2026 se encuentra en `output/analysis/engineering/20261008/qvoice-model-b-calibrated-v1/`. El modelo nuevo usa la receta de B como predictor base y aprende una corrección QVoice, seguida de una calibración temporal. Su identificador es independiente del modelo B elegido para la presentación.

## Contrato del modelo

- Población: empleados regulares activos de Engineering, excluyendo RF360.
- Outcome: salida voluntaria posterior al snapshot; ajuste con etiquetas mensuales y evaluación a seis meses.
- Enlace: `cloglog`.
- QVoice: encuesta Y exclusivamente en snapshots del año Y+1, bajo `config/qvoice_annual_lag_policy_20261008.json`.
- Variables B: diez features, incluidas las dos interacciones vigentes. En el nuevo modelo B sirve como offset fijo al ajustar QVoice.
- Candidatos: las 255 combinaciones de ocho bloques y cinco representaciones PCA de los 33 ítems comparables.
- Selección: Brier mensual en dos intervalos anteriores a los de calibración.
- Calibración: intercepto y pendiente positiva en dos intervalos reservados. Después de calibrar no se vuelven a ajustar los coeficientes.
- Evaluación: agosto–diciembre de 2025 y enero–febrero de 2026. Los periodos ya fueron inspeccionados en el desarrollo previo y se identifican como evaluación retrospectiva.

El [plan previo](../plans/attrition-b-plus-qvoice-calibrated-20261008.md) documenta métodos, límites, controles y exclusiones. La configuración ejecutable es `config/qvoice_model_calibrated_20261008.yaml`.

## Artefactos

La ejecución se completó y la carpeta contiene:

- `trained-model/model.json`: parámetros de B, codificador QVoice o PCA, corrección, calibración y límites de fechas.
- `trained-model/selection.json`: los 780 ajustes candidatos del corte final y sus resultados de selección.
- `folds/<periodo>/`: modelos históricos, selección y evaluación con bootstrap.
- `comparison-results.json`: comparación de B, B con calibración comparable, disponibilidad y B + QVoice antes y después de calibrar.
- `informe-modelo-b-qvoice-calibrado.md`: interpretación en español.
- `manifest.json`, `execution-contract.json`, `inputs/` y `validation/`: trazabilidad y comprobaciones.

Los modelos de cada fold evalúan el procedimiento de selección. El modelo de `trained-model/` usa los datos disponibles al corte y puede elegir otra combinación; sus coeficientes no se presentan como si hubieran sido evaluados previamente con información futura.

## Resultado retrospectivo del 8 de octubre de 2026

El artefacto final seleccionó **Q4 + Q12 + Career + promedio de 33 preguntas + Wellbeing (Q8, Q10, Q11)**, con L2 = 0.1. Q4, Q12 y Career aparecieron en las tres selecciones. Los 2,340 ajustes candidatos convergieron y las 29 comprobaciones de artefactos pasaron. Los coeficientes usan etiquetas hasta el 28 de junio de 2026; la calibración usa los snapshots del 28 de junio y 26 de julio, con etiquetas completas hasta el 23 de agosto de 2026. El corte de conocimiento sigue siendo el 7 de septiembre de 2026.

Las dos evaluaciones completaron 780 ajustes cada una y todos convergieron. Para agosto–diciembre de 2025 se seleccionó Q4 + Q12 + Career + Confidence; para enero–febrero de 2026, Q4 + Q12 + Career. Ambos eligieron L2 = 10. Los mejores PCA usaron diez componentes, pero no superaron la combinación seleccionada por Brier mensual.

La extensión calibrada mejora PR-AUC, lift y Brier frente a B en ambos periodos. El error de calibración general es mayor que el de B; por ello cumple seis de las ocho comprobaciones principales y el estado del criterio conjunto es **sin mejora demostrada**. Esta etiqueta indica que no cumple todos los requisitos de sustitución, aunque existan mejoras predictivas parciales. Frente a B con entrenamiento y calibración comparables cumple las cuatro comprobaciones adicionales.

La referencia B se reprodujo con iguales cohortes y métricas, salvo redondeo numérico de máquina en Brier. El detalle y la incertidumbre están en el [informe de la ejecución](../../output/analysis/engineering/20261008/qvoice-model-b-calibrated-v1/informe-modelo-b-qvoice-calibrado.md). El procedimiento y el artefacto se conservan como experimentales; la selección final y sus fechas se consultan en el JSON entrenado, no se sustituyen por las selecciones históricas.

## Reproducción

```powershell
.venv\Scripts\python.exe -B tools/qvoice_calibrated_model.py --config config/qvoice_model_calibrated_20261008.yaml --run-root output/analysis/engineering/20261008/qvoice-model-b-calibrated-v1
.venv\Scripts\python.exe -B tools/build_qvoice_calibrated_report.py --run-root output/analysis/engineering/20261008/qvoice-model-b-calibrated-v1
```

El primer comando es el de la ejecución original; una vez completada, una repetición requiere una carpeta nueva y copias de sus inputs de preflight y referencias de assessment. Una ejecución interrumpida puede continuar en su carpeta si el contrato confirma iguales código, configuración y fuentes. El programa reutiliza únicamente etapas completas de esa misma ejecución.

`predict_artifact(artifact, frame_preparado)` en `tools/qvoice_calibrated_model.py` reconstruye el modelo desde JSON y devuelve el riesgo a seis meses sólo en memoria. El frame debe respetar las definiciones de las features y los estados QVoice declarados en la configuración. La interpretación final y el estado de validación están en el informe y en el manifest de cada ejecución.

Todos los reportes son `presentation`. No se guardan filas, identificadores, respuestas, predicciones ni explicaciones individuales. Los parámetros del modelo se pueden conservar; los resultados compartidos son agregados conforme a la autorización del 1 de octubre de 2026.
