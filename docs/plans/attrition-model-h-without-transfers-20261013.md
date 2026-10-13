# H = C sin Transfers y H + QVoice

Fecha: 13-oct-2026. Modo: `presentation`.

## Pregunta

¿Qué cambia al retirar del modelo C el predictor `transfer_12m`, solicitado para
revisión, y al retirar la misma representación de C + QVoice?

## Diseño

Se usa la misma población Engineering, las mismas fotos de agosto–diciembre de
2025 y enero–febrero de 2026, el mismo outcome voluntario a seis meses, la
misma agrupación de antigüedad × salidas del equipo × nivel y el mismo peso por
periodo que CQ.

`transfer_12m` es la representación de C: transferencia efectiva en los doce
meses anteriores a cada foto. `transfer_history` no es predictor de C y no se
trata como si lo fuera.

H conserva las variables seleccionadas y L2 de C con origen 1-ago-2025,
elimina sólo `transfer_12m` y reajusta sus coeficientes usando etiquetas
maduras antes de ese origen. H + QVoice conserva en cada periodo los bloques
QVoice y L2 que ya seleccionó CQ y reajusta la corrección con H como offset.
No se repite la búsqueda exhaustiva de C ni de QVoice: el experimento mide una
ablación, no una nueva búsqueda de modelo.

## Criterios y controles

- Reproducir C y CQ archivados sobre la misma carga antes de interpretar H.
- Mantener idénticas personas, fechas, etiquetas, capacidad y grupos.
- Informar log-loss, Brier, PR-AUC, captura y error de grupo; usar 500
  remuestreos pareados por persona para diferencias de pérdidas y captura.
- No persistir filas persona-mes, IDs ni scores individuales.
- Informar como sensibilidad retrospectiva; no cambiar la selección vigente de
  CQ sin validación posterior.
