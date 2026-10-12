# Promedio de 33 preguntas comparables

Clasificación: `presentation`. Asociación descriptiva; no estima el aporte incremental al modelo.

## Flujo histórico

2024–2026: extracción de los Excel anuales y enlace a la población previa de Engineering. Para el modelo, la wave Y se asigna sólo a snapshots Y+1 por la política aprobada; esto no certifica la publicación real.

| Año | Elegibles | Enlazados | Con señal primaria | Cobertura % | Completa primaria | Completa total |
|---|---:|---:|---:|---:|---:|---:|
| 2024 | 29,339 | 24,526 | 19,191 | 65.4 | 19,191 | 19,191 |
| 2025 | 30,996 | 25,525 | 21,731 | 70.1 | 21,731 | 21,731 |
| 2026 | 34,868 | 28,878 | 23,881 | 68.5 | 23,881 | 23,881 |

## Asociaciones por respuesta

Numerador: personas con salida voluntaria en la ventana. Denominador: personas del grupo de respuesta enlazadas a Engineering en el baseline. Se publican tasas con al menos 30 personas y 30 eventos.

| Año | Componente | Respuesta | Personas | Salidas | Attrition % |
|---|---|---|---:|---:|---:|
| 2024 | mean33 | 100 | 3,507 | 90 | 2.6 |
| 2024 | mean33 | 50–69 | 3,293 | 218 | 6.6 |
| 2024 | mean33 | 70–79 | 2,130 | 113 | 5.3 |
| 2024 | mean33 | 80–89 | 2,924 | 106 | 3.6 |
| 2024 | mean33 | 90–99 | 4,175 | 126 | 3 |
| 2024 | mean33 | <50 | 3,162 | 368 | 11.6 |
| 2024 | mean33 | Sin respuesta | 5,335 | 346 | 6.5 |
| 2025 | mean33 | 100 | 4,632 | 130 | 2.8 |
| 2025 | mean33 | 50–69 | 3,455 | 228 | 6.6 |
| 2025 | mean33 | 70–79 | 2,407 | 120 | 5 |
| 2025 | mean33 | 80–89 | 3,191 | 115 | 3.6 |
| 2025 | mean33 | 90–99 | 4,682 | 125 | 2.7 |
| 2025 | mean33 | <50 | 3,364 | 389 | 11.6 |
| 2025 | mean33 | Sin respuesta | 3,794 | 229 | 6 |
| 2026 | mean33 | 100 | 5,619 | 127 | 2.3 |
| 2026 | mean33 | 50–69 | 3,647 | 160 | 4.4 |
| 2026 | mean33 | 70–79 | 2,485 | 75 | 3 |
| 2026 | mean33 | 80–89 | 3,397 | 84 | 2.5 |
| 2026 | mean33 | 90–99 | 5,376 | 117 | 2.2 |
| 2026 | mean33 | <50 | 3,357 | 246 | 7.3 |
| 2026 | mean33 | Sin respuesta | 4,997 | 221 | 4.4 |

## Límites y siguiente acción

- La asignación Y a Y+1 es un supuesto de negocio para este experimento; no demuestra la fecha operativa de publicación.
- El acumulado de 2026 termina en la última foto conocida antes del 7 de septiembre; no es una tasa anual.
- Un registro sin enlace no demuestra que la persona fuera invitada y no respondiera.
- Repetir la validación con la wave 2026 cuando existan snapshots y outcomes de 2027; resolver además las equivalencias pendientes.

Consulta: `queries\audits\qvoice_model_engineering_join_20261006.sql`. Ejecución: 2026-10-08T15:50:24+00:00.
Los criterios, preguntas, reglas, métricas, scores y acciones detalladas se conservan en el assessment v4 de este concepto.
