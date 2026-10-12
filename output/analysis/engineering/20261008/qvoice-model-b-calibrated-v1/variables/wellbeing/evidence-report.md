# Wellbeing — versiones histórica y completa

Clasificación: `presentation`. Asociación descriptiva; no estima el aporte incremental al modelo.

## Flujo histórico

2024–2026: extracción de los Excel anuales y enlace a la población previa de Engineering. Para el modelo, la wave Y se asigna sólo a snapshots Y+1 por la política aprobada; esto no certifica la publicación real.

| Año | Elegibles | Enlazados | Con señal primaria | Cobertura % | Completa primaria | Completa total |
|---|---:|---:|---:|---:|---:|---:|
| 2024 | 29,339 | 24,526 | 23,657 | 80.6 | 23,280 | 0 |
| 2025 | 30,996 | 25,525 | 25,386 | 81.9 | 25,049 | 24,940 |
| 2026 | 34,868 | 28,878 | 28,113 | 80.6 | 27,775 | 27,663 |

## Asociaciones por respuesta

Numerador: personas con salida voluntaria en la ventana. Denominador: personas del grupo de respuesta enlazadas a Engineering en el baseline. Se publican tasas con al menos 30 personas y 30 eventos.

| Año | Componente | Respuesta | Personas | Salidas | Attrition % |
|---|---|---|---:|---:|---:|
| 2024 | Q10 | Sin respuesta | 1,016 | 88 | 8.7 |
| 2024 | Q10 | No favorable | 12,528 | 801 | 6.4 |
| 2024 | Q10 | Favorable | 10,982 | 478 | 4.4 |
| 2024 | Q11 | Sin respuesta | 1,019 | 88 | 8.6 |
| 2024 | Q11 | No favorable | 9,599 | 708 | 7.4 |
| 2024 | Q11 | Favorable | 13,908 | 571 | 4.1 |
| 2024 | Q8 | Sin respuesta | 1,017 | 92 | 9 |
| 2024 | Q8 | No favorable | 6,586 | 606 | 9.2 |
| 2024 | Q8 | Favorable | 16,923 | 669 | 4 |
| 2024 | Q9 | Pregunta ausente | 24,526 | 1,367 | 5.6 |
| 2025 | Q10 | No favorable | 12,865 | 815 | 6.3 |
| 2025 | Q10 | Favorable | 12,373 | 495 | 4 |
| 2025 | Q11 | No favorable | 9,665 | 671 | 6.9 |
| 2025 | Q11 | Favorable | 15,586 | 644 | 4.1 |
| 2025 | Q8 | No favorable | 6,934 | 622 | 9 |
| 2025 | Q8 | Favorable | 18,332 | 688 | 3.8 |
| 2025 | Q9 | No favorable | 8,015 | 603 | 7.5 |
| 2025 | Q9 | Favorable | 17,199 | 707 | 4.1 |
| 2026 | Q10 | Sin respuesta | 912 | 55 | 6 |
| 2026 | Q10 | No favorable | 13,530 | 524 | 3.9 |
| 2026 | Q10 | Favorable | 14,436 | 451 | 3.1 |
| 2026 | Q11 | Sin respuesta | 915 | 56 | 6.1 |
| 2026 | Q11 | No favorable | 10,254 | 449 | 4.4 |
| 2026 | Q11 | Favorable | 17,709 | 525 | 3 |
| 2026 | Q8 | Sin respuesta | 881 | 59 | 6.7 |
| 2026 | Q8 | No favorable | 7,454 | 419 | 5.6 |
| 2026 | Q8 | Favorable | 20,543 | 552 | 2.7 |
| 2026 | Q9 | Sin respuesta | 938 | 56 | 6 |
| 2026 | Q9 | No favorable | 8,280 | 429 | 5.2 |
| 2026 | Q9 | Favorable | 19,660 | 545 | 2.8 |

## Límites y siguiente acción

- La asignación Y a Y+1 es un supuesto de negocio para este experimento; no demuestra la fecha operativa de publicación.
- El acumulado de 2026 termina en la última foto conocida antes del 7 de septiembre; no es una tasa anual.
- Un registro sin enlace no demuestra que la persona fuera invitada y no respondiera.
- Repetir la validación con la wave 2026 cuando existan snapshots y outcomes de 2027; resolver además las equivalencias pendientes.

Consulta: `queries\audits\qvoice_model_engineering_join_20261006.sql`. Ejecución: 2026-10-08T17:54:14+00:00.
Los criterios, preguntas, reglas, métricas, scores y acciones detalladas se conservan en el assessment v4 de este concepto.
