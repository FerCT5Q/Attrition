# Non-respondents

## Conocimiento acumulado

Esta variable tiene ahora una distribución exploratoria de participación de
QVoice. Se usa como **proxy de no respuesta** para revisión interna; no es una
definición confirmada de no respondente.

### Supuesto y población

- **Supuesto temporal:** se usa el snapshot almacenado más cercano al día 15
  del mes anterior a cada wave. No se afirma que sea la fecha exacta de envío.
- **Población proxy:** `worker_type='Employee'`, `employee_type='Regular'`,
  `active_status=1` en el snapshot seleccionado.
- **Grain:** empleado elegible por wave.
- **Categorías:** `Responded` = fila QVoice con al menos una respuesta;
  `QVoice row / no answer` = fila QVoice sin respuestas en los campos revisados;
  `No QVoice row` = empleado del snapshot sin una fila en el workbook raw.

### Evidencia agregada

| Wave | Snapshot proxy | Snapshot n | Responded | QVoice row / no answer | No QVoice row |
|---|---:|---:|---:|---:|---:|
| Mar-2023 | 2023-02-19 | 42,745 | 6,094 (14.3%) | 552 (1.3%) | 36,099 (84.5%) |
| Jan-2024 | 2023-12-24 | 40,145 | 32,369 (80.6%) | 903 (2.2%) | 6,873 (17.1%) |
| Jan-2025 | 2024-12-29 | 42,342 | 34,886 (82.4%) | 34 (0.1%) | 7,422 (17.5%) |
| Jan-2026 | 2025-12-28 | 47,134 | 38,439 (81.6%) | 755 (1.6%) | 7,940 (16.8%) |

Cada fila reconcilia con el snapshot. Las categorías `No QVoice row` no deben
leerse como no respuesta definitiva: todavía falta confirmar la lista de
invitados/elegibles y el estado de cierre de cada wave.

### Privacidad, limitaciones y uso

La evidencia publicada contiene sólo conteos agregados y porcentajes; no se
guardan IDs, nombres, correos, respuestas individuales ni texto libre. El
resultado es descriptivo para revisión interna y no es una feature workforce-
linked de attrition. No se promueve a score 2 ni a uso de modelado hasta
validar el roster de invitación, el wave-close status y el join empleado-fecha.

### Evidencia reproducible

- `output/distribution/json/qvoice-nonrespondent-proxy-evidence-2026-09-09.json`
- `tools/build_qvoice_nonrespondent_proxy_evidence.py`
- `queries/audits/qvoice_nonrespondent_snapshot_candidates_20260909.sql`
- `queries/audits/qvoice_nonrespondent_workforce_denominator_20260909.sql`
- `queries/audits/qvoice_nonrespondent_source_reconciliation_20260909.sql`
- `queries/audits/qvoice_nonrespondent_proxy_join_template_20260909.sql`
