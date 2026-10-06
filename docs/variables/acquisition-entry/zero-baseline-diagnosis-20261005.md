# Por qué cinco adquisiciones no tienen cohorte anual

Clasificación: `internal_analysis`. Audiencia: el solicitante y Julia. Esta comprobación continúa la revisión interna autorizada de la lámina 8; no cambia el assessment ni sus scores.

La lámina combina la distribución de empleados activos del 23 de agosto de 2026 con attrition de una cohorte fija del 24 de agosto de 2025. La consulta ejecutada el 5 de octubre de 2026 confirma que las etiquetas Aqua, NAPS, Moonshot, Arduino y Augentix Inc. aparecen en los snapshots de HRDA después de ese corte inicial. «Base cero» significa que no había empleados con esas etiquetas en la cohorte inicial; no afirma que las empresas adquiridas carecieran de empleados.

| Etiqueta registrada | Primer snapshot con la etiqueta | Empleados Regular activos en ese primer snapshot | Empleados actuales al 23 ago 2026 |
|---|---|---:|---:|
| Aqua | 28 dic 2025 | 1,229 | 1,148 |
| NAPS | 25 ene 2026 | 4 | 178 |
| Moonshot | 23 ago 2026 | 167 | 167 |
| Arduino | 29 mar 2026 | 163 | 160 |
| Augentix Inc. | 29 mar 2026 | 130 | 118 |

Estas fechas miden la primera observación en la tabla mensual, tanto sin filtros de población como para Employee / Regular activos. No prueban la fecha legal de adquisición ni el primer día de integración. Se conserva la normalización original de espacios y mayúsculas; no se fusionan posibles aliases sin evidencia de su equivalencia.

## Validaciones

**Aparición de las etiquetas.** Pregunta: ¿el cero se explica por una etiqueta que aparece después o sólo por los filtros de población? Motivo: precisar el significado del denominador. Método: conteos distintos por etiqueta y snapshot en todo el histórico hasta el 23 de agosto de 2026, con y sin filtros de elegibilidad. Regla previa: cinco categorías y conteos actuales iguales a los originales; las primeras observaciones posteriores sólo prueban ausencia previa del registro. Resultado: cinco primeras observaciones posteriores al 24 de agosto de 2025 y cero empleados con esas etiquetas en el snapshot inicial, incluso sin filtrar estado o tipo. Los conteos actuales reconcilian exactamente, con 1,771 empleados en total. Conclusión: las cinco categorías carecen de base inicial para la tasa anual de la lámina. Impacto en score: ninguno. Acción: explicar la fecha de aparición y conservar la tasa anual como no estimable con esta cohorte.

**Presencia anterior de los empleados actuales.** Pregunta: ¿todos llegaron al histórico después o algunos ya figuraban bajo otra situación? Motivo: no confundir ausencia de etiqueta con ausencia de la persona. Método: join interno por empleado de los cinco grupos actuales con su histórico; salida exclusivamente agregada. Regla previa: sin etiquetas contradictorias y particiones que reconcilien con el conteo actual. Resultado: sin duplicados ni contradicciones en los grupos actuales; las particiones cierran. En Aqua, 28 de los 1,148 empleados actuales figuran en el snapshot inicial fuera de la población elegible, y otros 5 tienen historia anterior pero no registro en ese snapshot. Los otros 1,115 aparecen por primera vez después. En Moonshot, 1 empleado actual estaba en la cohorte inicial con acquisition vacío, 2 figuraban fuera de la población elegible y 164 aparecen después. En NAPS, Arduino y Augentix Inc., todos los empleados actuales aparecen por primera vez después del corte inicial. Conclusión: el cero del segmento es correcto, pero no debe explicarse afirmando que ninguna de sus personas tenía historia anterior. Impacto en score: ninguno. Acción: conservar la clasificación del momento inicial y no aplicar retrospectivamente las etiquetas actuales.

Una métrica adicional desde la incorporación necesitaría una cohorte y ventana propias para cada adquisición. No sería directamente comparable con la tasa de doce meses publicada. Moonshot sólo tiene un snapshot con esa etiqueta hasta el corte actual, por lo que aún no hay seguimiento mensual posterior para esa cohorte.

## Trazabilidad

- Plan previo: `config/analysis-plans/20261005-acquisition-zero-baseline-diagnosis-v1.yaml`.
- Consulta ejecutada: `queries/audits/acquisition_zero_baseline_diagnosis_20261005.sql`.
- Fuente: `hrda.post_hire_monthly_worker_dtls`; histórico hasta el 23 de agosto de 2026, clasificación basal del 24 de agosto de 2025.
- Resultados agregados y diez comprobaciones aprobadas: `output/assessments/acquisition-zero-baseline-diagnosis-20261005/evidence/query-results.json`.
- Manifest y hashes: `output/assessments/acquisition-zero-baseline-diagnosis-20261005/manifest.json`.
- Autorización heredada: `config/acquisition_attrition_internal_analysis_authorization_20261005.json`; alcance del diagnóstico y conteos internos registrado además en el plan previo.
