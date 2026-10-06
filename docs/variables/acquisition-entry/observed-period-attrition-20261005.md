# Attrition desde el primer corte disponible — 5 de octubre de 2026

Clasificación: `internal_analysis`. Audiencia autorizada: el solicitante y Julia, desarrolladores del proyecto. El usuario pidió mostrar tasas aunque hubiera menos de doce meses de datos, identificándolas con un asterisco. La autorización y su alcance están registrados en `config/analysis-plans/20261005-acquisition-observed-period-v1.yaml`, que hereda la autorización de revisión interna de adquisiciones.

La lámina V9 combinaba la distribución actual del 23 de agosto de 2026 con una cohorte anual del 24 de agosto de 2025. El diagnóstico posterior confirmó que cinco etiquetas aparecen después de ese inicio. V10 conserva las ocho tasas anuales existentes y añade la proporción observada desde la primera cohorte disponible para cuatro categorías. Moonshot sólo tiene el primer corte y aún no tiene seguimiento posterior.

| Adquisición | Inicio de cohorte | Fin de seguimiento | Días | Meses aproximados | Salidas voluntarias / base | Attrition observada |
|---|---|---|---:|---:|---:|---:|
| Aqua | 28 dic 2025 | 23 ago 2026 | 238 | 7.8 | 102 / 1,229 | 8.3%* |
| NAPS | 25 ene 2026 | 23 ago 2026 | 210 | 6.9 | 0 / 4 | 0%* |
| Arduino | 29 mar 2026 | 23 ago 2026 | 147 | 4.8 | 2 / 163 | 1.2%* |
| Augentix Inc. | 29 mar 2026 | 23 ago 2026 | 147 | 4.8 | 12 / 130 | 9.2%* |
| Moonshot | 23 ago 2026 | 23 ago 2026 | 0 | 0 | Base inicial: 167 | Sin seguimiento |

El asterisco indica un período menor a doce meses. La proporción se conserva tal como fue observada; no se extrapola a un año. Los meses se calculan como días × 12 / 365.25 y se muestran con máximo un decimal. El período exacto permanece en las fechas y en los tooltips.

## Definición y límites

Se seleccionan empleados `Employee` / `Regular` activos en el primer snapshot con la etiqueta de adquisición. Se fija esa cohorte y se calcula `100 × personas con al menos una salida VOLUNTARY en (inicio, fin] / personas de la cohorte inicial`. Los eventos se normalizan con espacios y mayúsculas; sólo se acepta la etiqueta exacta `VOLUNTARY`. La fuente del numerador sigue siendo `hrda.post_hire_monthly_worker_dtls`, igual que en las tasas anuales originales.

Las personas que se incorporan después no entran retrospectivamente en la cohorte. Esta limitación es especialmente relevante para NAPS: los 4 empleados iniciales siguen presentes al final, pero hay otros 174 empleados actuales fuera de esa cohorte. El 0% describe únicamente a esos 4 empleados iniciales. La lámina conserva una nota visible y el detalle `0 / 4`.

Las fechas iniciales son primeras observaciones de las etiquetas en la tabla mensual; no certifican la fecha legal de adquisición. Las tasas con asterisco tienen períodos distintos y se muestran en gris, sin compararlas por color contra la referencia anual de 3.1%. El gris también identifica a Moonshot como no estimable. Las tasas anuales conservan sus colores, numeradores y denominadores.

## Validaciones y resultados

**Disponibilidad y ventana.** Pregunta: ¿qué primera cohorte y seguimiento tiene cada grupo? Motivo: evitar tratar un período parcial como anual o confundir cero tiempo observado con cero salidas. Método: recalcular la primera fecha con empleados elegibles, deduplicar la cohorte y contar snapshots posteriores. Regla previa: cinco grupos, primeras fechas y conteos actuales coincidentes con el diagnóstico, sin duplicados ni contradicciones en la cohorte inicial. Métricas observadas: las cinco categorías reconcilian; cero duplicados y contradicciones; Aqua tiene 8 cortes posteriores, NAPS 7, Arduino y Augentix 5, y Moonshot 0. Conclusión: cuatro tasas estimables y una sin seguimiento. Impacto en score: ninguno. Acción: publicar cuatro tasas con asterisco y mantener Moonshot sin tasa hasta disponer de un corte posterior.

**Numerador y fórmula.** Pregunta: ¿la tasa cuenta personas únicas de la cohorte inicial dentro de su ventana? Motivo: el feed mensual puede repetir la misma salida y una persona puede salir más de una vez. Método: agregar por persona y fecha, contar una persona con al menos un evento elegible, contrastar con un `COUNT(DISTINCT ...)` independiente sobre la fuente y recalcular la proporción con Decimal y Fraction. Regla previa: ambos numeradores iguales, salidas entre cero y base, diferencia menor a 0.000000000001 puntos y tasa nula con cero seguimiento. Métricas observadas: coincidencia en los cinco grupos. En Aqua, 598 filas de eventos representan 103 combinaciones persona-fecha y 102 personas con salida; el numerador utilizado es 102. Conclusión: las tasas reflejan personas únicas y conservan la fórmula del slide. Impacto en score: ninguno. Acción: preservar la deduplicación y la cohorte fija en futuras actualizaciones.

**Lectura y comparación.** Pregunta: ¿se distinguen tasas anuales, parciales y ausencia de seguimiento? Motivo: los tiempos de exposición afectan la proporción acumulada. Método: asterisco, columna de meses e inicio, detalle salidas/base, notas de NAPS y Moonshot, y color neutro para ventanas parciales. Regla previa: conservar las ocho tasas anuales y las otras 43 láminas; no anualizar ni asignar colores de comparación anual a las tasas parciales. Métricas observadas: se conserva todo el contenido de las otras láminas; cuatro porcentajes con asterisco, un estado sin seguimiento, catorce pruebas de adquisición aprobadas y 53 pruebas del skill de evaluación aprobadas. El verificador estático devuelve cero errores; el deck mantiene el aviso de Plotly por CDN. Los 12 casos visuales —cuatro temas en tres tamaños— pasan, y se inspeccionaron las cuatro capturas de 1440×810. Conclusión: las ventanas y sus límites se leen junto a cada tasa. Impacto en score: ninguno. Acción: usar V10 para esta revisión interna.

## Evidencia y entregables

- SQL ejecutado el 5 de octubre de 2026: `queries/audits/acquisition_observed_period_attrition_20261005.sql`.
- Fuente: `hrda.post_hire_monthly_worker_dtls`; cohorte fijada en la fecha inicial de cada grupo y salidas hasta el 23 de agosto de 2026.
- Plan, copias de SQL y resultados agregados: `output/assessments/acquisition-observed-period-20261005/`.
- Ledger con hashes de SQL, plan y resultados: `output/assessments/acquisition-observed-period-20261005/evidence-ledger.json`.
- Evidencia calculada: `output/distribution/json/attrition-43-variable-distributions-v10.acquisition-observed-period-evidence-20261005.json`.
- Deck: `output/distribution/attrition-43-variable-distributions-v10.html`.
- Manifest: `output/distribution/json/attrition-43-variable-distributions-v10-manifest.json`.
- Capturas y validación del HTML por hash: `output/preview/acquisition-observed-period-20261005/visual-validation.json`.

V8 y V9 se conservan. No se modificaron scores, reglas de producción ni autorizaciones de distribución.
