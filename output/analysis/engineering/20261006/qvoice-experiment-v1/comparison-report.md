# QVoice en el modelo de Engineering

Ejecución iniciada el 6 de octubre de 2026. Informe generado el 2026-10-07 (UTC). Clasificación: `presentation`.

## Resultado

Se implementaron **17 configuraciones** y se completaron **8 assessments v4**. El modelo B se reprodujo correctamente. Hay **0 encuestas con fecha acreditada de disponibilidad de resultados**.

**El aporte predictivo de QVoice sigue pendiente.** Ninguna configuración tiene dos periodos principales evaluables. Las tasas anuales permiten priorizar señales, pero no sustituyen una comparación con información disponible antes de cada predicción.

## Control B

La reproducción mantuvo la población, las diez features, el hazard cloglog, las interacciones y el procedimiento histórico del 3 de octubre.

| Comprobación | Resultado |
|---|---:|
| Registros persona-mes | 1,880,719 |
| Exposiciones con etiqueta a seis meses | 1,699,949 |
| Exposiciones con salida | 54,452 |
| Parámetros | 82 |

| Métrica histórica media | Valor |
|---|---:|
| PR-AUC × 100 | 5.4 |
| Lift del 10% superior | 2.1 |
| Brier × 1,000 | 29.1 |

Los 32 controles de reproducción cumplieron. Las exposiciones con evento incluyen observaciones mensuales repetidas de una persona; no son un conteo de personas distintas.

[Resultados completos del control](<control/control-reproduction.json>)

## Señales y cobertura descriptiva

La población corresponde a Engineering activo Regular, excluyendo RF360, en la foto previa a cada encuesta. Esta cobertura aún no acredita que la respuesta pudiera usarse en ese snapshot.

![Cobertura descriptiva](charts/cobertura-qvoice-engineering.png)

| Concepto | 2024 | 2025 | 2026 | Assessment |
|---|---:|---:|---:|---|
| Intent to Stay (Q4/Q12) | 79.8% | 81.3% | 80.1% | [Abrir HTML](<../../../../assessments/qvoice-model-20261006-intent-v2-r3/vars/01-intent-to-stay-q4-y-q12/intent-to-stay-q4-y-q12-v2.html>) |
| Career goals | 78.3% | 81% | 78.7% | [Abrir HTML](<../../../../assessments/qvoice-model-20261006-career-v2/vars/01-career-goals-respuesta-binaria/career-goals-respuesta-binaria-v2.html>) |
| Promedio de 33 preguntas | 65.4% | 70.1% | 68.5% | [Abrir HTML](<../../../../assessments/qvoice-model-20261006-mean33-v1-r2/vars/01-promedio-de-33-preguntas-comparables/promedio-de-33-preguntas-comparables-v2.html>) |
| Engagement (Q1/Q2/Q3) | 80.8% | 81.9% | 80.7% | [Abrir HTML](<../../../../assessments/qvoice-model-20261006-engagement-v1/vars/01-engagement-q1-q2-y-q3/engagement-q1-q2-y-q3-v2.html>) |
| Connection (Q5/Q7) | 80.7% | 81.9% | 80.6% | [Abrir HTML](<../../../../assessments/qvoice-model-20261006-connection-v1/vars/01-workplace-connection-versiones-hist-rica-y-completa/workplace-connection-versiones-hist-rica-y-completa-v2.html>) |
| Wellbeing (Q8/Q10/Q11) | 80.6% | 81.9% | 80.6% | [Abrir HTML](<../../../../assessments/qvoice-model-20261006-wellbeing-v2/vars/01-wellbeing-versiones-hist-rica-y-completa/wellbeing-versiones-hist-rica-y-completa-v2.html>) |
| Confidence (Q13/Q17) | 79.8% | 81.9% | 80% | [Abrir HTML](<../../../../assessments/qvoice-model-20261006-confidence-v1/vars/01-confidence-q13-y-q17/confidence-q13-y-q17-v2.html>) |
| Heartbeat (6 signos) | 0% | 0% | 79.4% | [Abrir HTML](<../../../../assessments/qvoice-model-20261006-heartbeat-v4/vars/01-heartbeat-signos-relativos-de-seis-preguntas/heartbeat-signos-relativos-de-seis-preguntas-v2.html>) |

Las familias usan al menos un componente primario válido. El promedio exige 33 respuestas válidas; Heartbeat aplica su regla ordinal completa. Los assessments detallan completitud, ausencia de pregunta, falta de respuesta, valor inválido y falta de enlace por separado.

## Asociaciones anuales comprobadas

![Asociaciones anuales](charts/asociaciones-anuales-intent-career.png)

| Año | Señal | Respuesta | Personas | Salidas | Tasa |
|---|---|---|---:|---:|---:|
| 2024 | Q12 | No favorable | 9,838 | 806 | 8.2% |
| 2024 | Q12 | Favorable | 12,785 | 403 | 3.2% |
| 2024 | Q4 | No favorable | 5,757 | 684 | 11.9% |
| 2024 | Q4 | Favorable | 17,400 | 549 | 3.2% |
| 2024 | Q4 y Q12 | No favorable | 10,239 | 836 | 8.2% |
| 2024 | Q4 y Q12 | Favorable | 12,125 | 348 | 2.9% |
| 2025 | Q12 | No favorable | 9,700 | 805 | 8.3% |
| 2025 | Q12 | Favorable | 14,836 | 457 | 3.1% |
| 2025 | Q4 | No favorable | 5,727 | 685 | 12% |
| 2025 | Q4 | Favorable | 19,269 | 591 | 3.1% |
| 2025 | Q4 y Q12 | No favorable | 10,172 | 846 | 8.3% |
| 2025 | Q4 y Q12 | Favorable | 14,175 | 392 | 2.8% |
| 2024 | Career goals | No favorable | 6,269 | 618 | 9.9% |
| 2024 | Career goals | Favorable | 16,704 | 614 | 3.7% |
| 2025 | Career goals | No favorable | 6,689 | 653 | 9.8% |
| 2025 | Career goals | Favorable | 18,433 | 650 | 3.5% |

Ventanas: (1 de enero de 2024, 1 de enero de 2025] y (1 de enero de 2025, 1 de enero de 2026]. Baselines: 24 de diciembre de 2023 y 29 de diciembre de 2024. Se exige respuesta válida por componente; la alternativa Q4 y Q12 exige ambas válidas. El contraste anual puede incluir salidas anteriores a la publicación de resultados; por eso es descriptivo.

## Conciliación con el playbook v11

- Los conteos del Excel, la fórmula del promedio y sus seis bandas se contrastaron con sus JSON originales; los resultados detallados están en la evidencia por concepto.
- La plantilla actual con el filtro original tiene 40,144 personas en el baseline de 2024 y 42,341 en el de 2025: una menos en cada año que en el JSON publicado. La consulta independiente confirma estos totales y cero duplicados. La causa del cambio individual no se puede establecer con los agregados históricos disponibles.
- Las pequeñas diferencias de cohortes y tasas de Intent/Career quedan registradas; no se alteraron cifras para forzar una coincidencia.
- Heartbeat: 93 de 93 comprobaciones coinciden al reproducir el filtro retrospectivo del playbook. Al limitar los registros de eventos a snapshots conocidos al corte, 12 segmentos tienen entre 1 y 3 salidas menos. Las cifras principales conservan ese límite. Los segmentos se solapan entre preguntas; esas diferencias no se suman como personas distintas.
- El acumulado descriptivo de 2026 termina el 23 de agosto, la última foto conocida al corte del 7 de septiembre. Las referencias anuales de Intent/Career llegan al 27 de septiembre; esas tasas no tienen la misma ventana. La referencia de Heartbeat sí termina el 23 de agosto y sus 18 segmentos se concilian con esa misma ventana.

[SQL de conciliación del baseline](<../../../../../queries/audits/qvoice_model_baseline_reconciliation_20261006.sql>)

## Resultado por configuración

| Configuración | Periodos principales completos | Conclusión |
|---|---:|---|
| `intent_q4` | 0 | evidencia temporal insuficiente |
| `intent_q12` | 0 | evidencia temporal insuficiente |
| `intent_components` | 0 | evidencia temporal insuficiente |
| `intent_both` | 0 | evidencia temporal insuficiente |
| `career` | 0 | evidencia temporal insuficiente |
| `mean33` | 0 | evidencia temporal insuficiente |
| `engagement` | 0 | evidencia temporal insuficiente |
| `connection_q5_q7` | 0 | evidencia temporal insuficiente |
| `connection_q5_q6_q7` | 0 | evidencia temporal insuficiente |
| `wellbeing_q8_q10_q11` | 0 | evidencia temporal insuficiente |
| `wellbeing_q8_q9_q10_q11` | 0 | evidencia temporal insuficiente |
| `confidence` | 0 | evidencia temporal insuficiente |
| `heartbeat` | 0 | evidencia temporal insuficiente |
| `intent_career` | 0 | evidencia temporal insuficiente |
| `six_themes_common` | 0 | evidencia temporal insuficiente |
| `intent_career_mean33` | 0 | evidencia temporal insuficiente |
| `intent_career_mean31_same_cohort` | 0 | evidencia temporal insuficiente |

### Brechas que condicionan las comparaciones

- La equivalencia del texto de Career goals de 2024 sigue pendiente; no se mezcla con las versiones posteriores.
- Q6 no existe en la fuente binaria de 2024; el conjunto completo necesita historia propia.
- Q9 no existe en la fuente binaria de 2024; el conjunto completo necesita historia propia.
- No se puede reconstruir el promedio ordinal exacto: 2024: 0 de 53; 2025: 52 de 53.
- Las tres fechas de publicación siguen pendientes. El año del archivo, las fechas de respuesta y el lanzamiento no las sustituyen.

### Procedimiento implementado

- Periodos principales: febrero–julio de 2025 y agosto de 2025–enero de 2026. Sólo se admiten snapshots con seguimiento completo a seis meses.
- Selección L2 mediante Brier mensual en los últimos tres intervalos terminados antes del inicio calendario del periodo. Todas las etiquetas de entrenamiento respetan ese corte.
- Comparación con B y con indicadores de disponibilidad usando las mismas personas, snapshots y etiquetas. Los faltantes permanecen en la cohorte general.
- Se evalúa también la cohorte con respuestas completas cuando cumple los mínimos de publicación.
- Incertidumbre mediante 500 réplicas pareadas por persona, conservando juntas sus observaciones mensuales.
- PR-AUC, lift del decil, Brier y calibración general y del quintil superior. La nueva comparación agrupa empates; la reproducción B conserva el método histórico para comprobar sus cifras.
- Una nueva wave reemplaza a la anterior aunque falte la respuesta. Caducidad máxima de 12 meses y comprobación de continuidad del episodio laboral.

## Entregables y siguiente paso

1. Aportar evidencia de la fecha de disponibilidad de cada wave y registrar fecha, estado y referencia en la configuración.
2. Confirmar la equivalencia de Career goals de 2024 y mantener separadas las versiones completas de Connection y Wellbeing.
3. Ejecutar una nueva carpeta de experimento con las fechas verificadas. El pipeline conserva el bloqueo cuando falta historia comparable.

- [Excel consolidado de ocho conceptos](<../../../../assessments/qvoice-experiment-v1-consolidated/assessment.xlsx>)
- [Resultados de las 17 configuraciones](<comparison-results.json>)
- [Configuración ejecutable](<../../../../../config/qvoice_model_experiment_20261006.yaml>)
- [Guía de reproducción](<../../../../../docs/context/qvoice-model-experiment.md>)
- [Pruebas y verificaciones](<validation/test-results.json>)

Todos los entregables contienen agregados. No se guardaron filas de empleados, identificadores, predicciones individuales ni texto libre. El procesamiento del modelo respeta la autorización de uso en memoria del 1 de octubre.
