# Revisión interna de attrition por adquisición — 5 de octubre de 2026

Clasificación: `internal_analysis`. Audiencia: el solicitante y Julia, desarrolladores del proyecto. La excepción está registrada en `config/acquisition_attrition_internal_analysis_authorization_20261005.json`.

El 29 de septiembre de 2026 se ejecutó la consulta agregada que alimentó la lámina de adquisiciones de V8. El contrato de presentación dejó cuatro tasas sin mostrar porque tenían menos de 30 salidas voluntarias. El 5 de octubre el usuario pidió completar esos valores para revisión interna. Esta revisión conserva los agregados, fechas, categorías y denominadores de la consulta original y calcula nuevamente la división; no es una consulta nueva a Redshift ni una nueva evaluación de scores.

La característica es el valor `acquisition` registrado en el snapshot, normalizado únicamente con espacios y mayúsculas. La métrica derivada es `100 × salidas voluntarias únicas / empleados de la cohorte inicial`. Se consideran empleados `Employee` / `Regular` activos al 24 de agosto de 2025, incluidos RF360, y salidas con `term_type` normalizado exactamente `VOLUNTARY` en `(2025-08-24, 2026-08-23]`. La etiqueta de adquisición se fija en la fecha inicial; los empleados actuales al 23 de agosto de 2026 sólo alimentan las barras de distribución.

| Adquisición | Empleados iniciales | Salidas voluntarias | Attrition anual |
|---|---:|---:|---:|
| RF360 | 2,597 | 56 | 2.2% |
| CSR | 658 | 21 | 3.2% |
| Hercules | 618 | 28 | 4.5% |
| Atheros | 530 | 10 | 1.9% |
| TDK (SAW/BAW filter and module business) | 307 | 1 | 0.3% |
| Otras adquisiciones | 1,438 | 77 | 5.4% |

Aqua, NAPS, Moonshot, Arduino y Augentix Inc. tenían cero empleados clasificados en esas categorías en la cohorte basal. Sus tasas anuales no son estimables con esta cohorte. El estado «Sin cohorte» refleja esa falta de denominador y no una supresión de privacidad; no se utiliza la población actual ni una clasificación futura para inventar la comparación anual.

Las validaciones se definieron antes del recálculo en `config/analysis-plans/20261005-acquisition-internal-attrition-v1.yaml`:

- **Procedencia.** Pregunta: ¿se reutilizan exactamente los conteos originales? Motivo: conservar el corte y aislar la corrección de visualización. Método: hashes SHA-256 del SQL, resultado y ledgers. Regla: coincidencia exacta con el run validado. Resultado: coinciden las 16 filas agregadas y los hashes registrados; ejecución original `2026-09-29T20:56:17-06:00`. Conclusión: el recálculo usa la evidencia original. Impacto en score: ninguno. Acción: conservar esos artefactos como fuente de esta revisión.
- **Fórmula.** Pregunta: ¿cada tasa corresponde a salidas/base? Motivo: evitar usar empleados actuales o el umbral de publicación como denominador. Método: división Decimal y comprobación con Fraction. Regla: base positiva, salidas entre cero y base, error menor a `0.000000000001` puntos; base cero produce tasa nula. Resultado: seis tasas detalladas estimables, cuatro recuperadas y cinco categorías sin base; error máximo cero. Conclusión: las cuatro tasas omitidas pueden mostrarse bajo la excepción interna. Impacto en score: ninguno. Acción: mantener el numerador y denominador junto a cada tasa.
- **Reconciliación.** Pregunta: ¿Top 10 y Otras forman el mismo total? Motivo: detectar pérdidas y doble conteo. Método: sumar empleados actuales, empleados basales y salidas. Regla: igualdad exacta con el segmento con adquisición registrada. Resultado: 7,711 empleados actuales, 6,148 iniciales y 193 salidas, todos coincidentes. Conclusión: el detalle conserva los totales y la tasa general de 3.1%. Impacto en score: ninguno. Acción: repetir la comprobación si cambia el corte.
- **Visualización interna.** Pregunta: ¿la lámina muestra toda tasa estimable bajo la autorización? Motivo: distinguir privacidad de falta de cohorte. Método: verificar clasificación, autorización, tasas, conteos y estados vacíos en el HTML. Regla: ocho tasas numéricas en la lámina —dos generales y seis detalladas—, cinco estados sin cohorte y ninguna supresión por eventos. Conclusión: la revisión interna puede mostrar los cuatro valores faltantes. Impacto en score: ninguno. Acción: conservar el uso descriptivo y la audiencia autorizada.

Se mantienen dos límites de la evidencia original: la base de 45,002 empleados difiere en uno de otros artefactos históricos del deck, y la fuente principal registra tres salidas de la cohorte que no coinciden con `all_terminations`. Se documentan como diferencias de origen pendientes; no se cambió la fuente del numerador para esta revisión. La ausencia de adquisición registrada no confirma una vía de contratación.

La consulta fuente es `queries/audits/acquisition_entry_distribution_attrition_20260929.sql`, con resultado congelado en `output/assessments/acquisition-entry-v4-20260929-r4/vars/01-ingreso-por-adquisici-n/evidence/query-results.json`. El SQL normalizado tiene hash `4c0bef229458d3cce31edbb26e74a6863012eec853eba1a4a30cccacbb5b6af8` y sus filas agregadas, `3567cc86914e6ddb2947c08c92a5db0939382ac1dc7ebf91c70df6c249651930`.

El resultado del recálculo y su autorización están en `output/distribution/json/attrition-43-variable-distributions-v9.acquisition-internal-attrition-evidence-20261005.json`; el manifest y la lámina revisada se entregan en V9. V8 y el assessment original se conservan como antecedentes.

La validación visual terminó con 12 casos aprobados: cuatro temas en 1440×810, 1280×720 y 1920×1080. Se comprobaron las ocho tasas, los seis pares salidas/base, los cinco estados «Sin cohorte», la navegación, los colores y la ausencia de recortes, superposiciones y errores de JavaScript. También se inspeccionaron las cuatro capturas de la lámina a 1440×810. El reporte `output/preview/acquisition-internal-20261005/visual-validation.json` conserva el hash del HTML validado, coincidente con el manifest; los hashes de V8 y de la evidencia original siguen intactos.
