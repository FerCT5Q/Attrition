# QVoice: feedback del manager

Primera foto con valor observable en esta carga: 2025-01-26. El soporte se comprueba por año y la elegibilidad se decide sólo con el entrenamiento de cada corte. Política anual: wave 2024 sólo en fotos de 2025; wave 2025 sólo en 2026. Vigencia de 12 meses, inicio incluido/fin excluido; la wave siguiente reemplaza la anterior aunque falte respuesta. Se exige continuidad del episodio desde el ancla de la encuesta; wave 2026 reservada para 2027. Esta política no acredita la fecha real de publicación.

Modo `presentation` · variable `qv_M21` · familia QVoice.
Empleados regulares activos de Engineering, excluyendo RF360, en cada foto mensual. Grain: persona-foto. Corte de conocimiento: 2026-09-07.

[Índice del diccionario](../diccionario.md) · [Decisiones completas](../decisiones.csv) · [Codificaciones de cada modelo](../codificaciones.csv)

## Tratamiento efectivo

| Elemento | Qué se hizo |
|---|---|
| Tipo | Binaria favorable registrada con estados de ausencia |
| Campos de origen | Wave 2024: My manager gives me timely feedback throughout the year that helps me improve my performance_favorable; Wave 2025: My manager gives me timely feedback throughout the year that helps me improve my performance._Favorable |
| Valores de origen | Indicador favorable 0/1 almacenado; también puede haber blancos, 255 y valores inválidos. No se recalcula desde la escala ordinal 1–5. |
| Valores antes de agrupar categorías raras | v0; v1; no_available_wave; no_linked_row; different_employment_episode; missing; question_absent; sentinel_255; invalid |
| Transformación | Correspondencia por texto exacto y encabezado binario unívoco de cada wave; 0 → v0, 1 → v1. Se codifica como categoría. Se conserva sólo Response Type vacío o EX cuando ese campo existe; se excluyen llaves inválidas o duplicadas. |
| Faltantes y valores por defecto | Blanco/nulo → missing; 255 → sentinel_255; fuera de {0,1} o no numérico → invalid; encabezado ausente → question_absent. Sin enlace, incluidas llaves duplicadas excluidas, → no_linked_row. Episodio no continuo → different_employment_episode, con prioridad sobre el resto. Sin wave asignada → no_available_wave. No se imputa v0. |
| Codificación para el modelo | Todas las entradas son categorías con indicadores 0/1. La referencia es la categoría más frecuente por filas de entrenamiento y se omite. Cada categoría restante tiene su propio indicador. Una categoría no aprendida deja todos los indicadores de ese término en cero. Las bandas no se usan como números ordinales ni se estandarizan como variables continuas. |
| Categorías raras | No se aplica agrupación de categorías raras a este término. |
| Consideraciones | Es una de las 33 preguntas comunes; los aliases Q del diccionario no se cuentan como variables adicionales. 0 significa no favorable en el campo binario, no identifica por separado neutralidad y desacuerdo. Se compara contenido contra su disponibilidad emparejada; no se interpreta una asociación como causalidad. |
| Uso en la definición de grupos | Puede modificar la predicción, pero no añade una dimensión de grupo en esta ronda. Los grupos siguen definidos por antigüedad, salidas del equipo y nivel. |

### Encabezados efectivamente utilizados

| Wave | Año de uso | Encabezado binario de origen |
|---|---|---|
| 2024 | 2025 | My manager gives me timely feedback throughout the year that helps me improve my performance_favorable |
| 2025 | 2026 | My manager gives me timely feedback throughout the year that helps me improve my performance._Favorable |

Aliases del diccionario: Q28. Son la misma pregunta, no incorporaciones adicionales.

## Comprobación y decisión

**Pregunta:** ¿Qué aporta esta representación al añadirla a la base, con datos conocidos antes de cada corte?

**Motivo:** separar una transformación de datos de su elegibilidad y de su mejora predictiva; dejar verificable por qué se conservó o quedó fuera.

**Método:** inspección del SQL/código congelado, soporte agregado de la carga, registro de selección interna y codificaciones guardadas. La documentación no reconstruye filas ni cambia decisiones a partir de resultados externos.

**Regla de aceptación:** Ajuste válido y elegibilidad; Brier no empeora; PR-AUC ≥99% del control. En validación de seis meses, además: lift al 10% ≥99% del control, MAE de los mismos grupos ≤control+0.1 pp y captura ≥control−0.5 pp. Entre las opciones que cumplen se minimiza log-loss y se aplica parsimonia dentro de una tolerancia relativa exacta de 0.0005. Se escoge la opción con menos incorporaciones dentro de esa ventana; después log-loss e identificador.

El contenido debe además reducir log-loss frente a un ajuste que sólo conserva los mismos estados de disponibilidad. La reserva mensual del primer corte QVoice usa Brier y PR-AUC; no aplica las tres condiciones de seis meses. La regla de seis fotos RH no se aplica automáticamente a QVoice.

### Métricas observadas de soporte

Son conteos de la representación ya transformada. «Observable» sigue los estados explícitos de ausencia del runner; no prueba por sí solo la definición oficial ni la completitud de eventos. Personas repetidas entre fotos no son personas distintas.

| Año | Persona-fotos | Observables | Cobertura (%) | Fotos observables | Categorías observables |
|---|---|---|---|---|---|
| 2025 | 390263 | 254511 | 65.2 | 12 | 2 |
| 2026 | 288586 | 187986 | 65.1 | 8 | 2 |

### Selección en cada corte

| Periodo | Base | Fotos internas observables | Cumple condiciones individual | Lista de seis | Decisión |
|---|---|---|---|---|---|
| aug_dec_2025 | B | — | Sí | No | No seleccionada |
| aug_dec_2025 | B_RH | — | No | No | No seleccionada |
| final | B | — | Sí | No | No seleccionada |
| final | B_RH | — | No | No | No seleccionada |
| jan_feb_2026 | B | — | No | No | No seleccionada |
| jan_feb_2026 | B_RH | — | No | No | No seleccionada |

- **aug_dec_2025 / B:** No quedó en la opción ganadora: al menos una opción que la incluye cumple las condiciones de validación, pero gana otra alternativa por log-loss y la preferencia por menos incorporaciones cuando la diferencia es mínima. Prueba individual: La incorporación individual cumple las condiciones de validación.
- **aug_dec_2025 / B_RH:** No seleccionada. No supera: Brier no empeora. No entró en las seis primeras para pares y tríos.
- **final / B:** No quedó en la opción ganadora: al menos una opción que la incluye cumple las condiciones de validación, pero gana otra alternativa por log-loss y la preferencia por menos incorporaciones cuando la diferencia es mínima. Prueba individual: La incorporación individual cumple las condiciones de validación.
- **final / B_RH:** No seleccionada. No supera: Brier no empeora. No entró en las seis primeras para pares y tríos.
- **jan_feb_2026 / B:** No seleccionada. No supera: Brier no empeora. No entró en las seis primeras para pares y tríos.
- **jan_feb_2026 / B_RH:** No seleccionada. No supera: Brier no empeora, Error de grupos dentro de tolerancia. No entró en las seis primeras para pares y tríos.

### Resultado externo de añadirla por separado

Cambios respecto a la misma base y población de cada periodo; valores positivos indican mejora de pérdidas o mayor captura. Estas cifras describen el resultado externo y no se emplean para seleccionar.

| Periodo | Base | Mejora log-loss (%) | Mejora Brier (%) | Cambio captura (pp) |
|---|---|---|---|---|
| aug_dec_2025 | B | −<0.1 | <0.1 | 0 |
| aug_dec_2025 | B_RH | −<0.1 | -0.1 | 1.6 |
| jan_feb_2026 | B | <0.1 | <0.1 | 0 |
| jan_feb_2026 | B_RH | 0.2 | <0.1 | -0.2 |

**Frecuencia en selecciones anteriores:** B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes.

**Conclusión de selección final:** Sobre B: No seleccionada. No quedó en la opción ganadora: al menos una opción que la incluye cumple las condiciones de validación, pero gana otra alternativa por log-loss y la preferencia por menos incorporaciones cuando la diferencia es mínima. Sobre B_RH: No seleccionada. No seleccionada. No supera: Brier no empeora. No entró en las seis primeras para pares y tríos.

**Impacto en score de assessment:** ninguno. Los scores previos no se reasignan con estas pruebas.

**Acción:** Mantener el registro de la prueba; no concluir que carece de señal en toda representación o combinación posible.

## Codificación de los modelos finales

No aparece en los modelos finales seleccionados. Sus valores candidatos están descritos arriba; no se inventa una referencia final para una variable que no quedó en esos artefactos.

## Fuentes trazables

- [source-metadata.json](<../../../../20261008/qvoice-model-b-calibrated-v1/preflight/source-metadata.json>)
- [qvoice_model_calibrated_20261008.yaml](<../../../../../../../config/qvoice_model_calibrated_20261008.yaml>)
- [qvoice_annual_lag_policy_20261008.json](<../../../../../../../config/qvoice_annual_lag_policy_20261008.json>)
- [qvoice_model_data.py](<../../../../../../../tools/qvoice_model_data.py>)
- [qvoice_model_experiment.py](<../../../../../../../tools/qvoice_model_experiment.py>)
- [qvoice_horizon_calibration.py](<../../../../../../../tools/qvoice_horizon_calibration.py>)
- [qvoice-feature-support.json](<../../input-evidence/qvoice-feature-support.json>) · registro de carga de esta ejecución

La fecha de la consulta no reemplaza la fecha de conocimiento de la variable. Un control técnico pass sólo respalda la afirmación acotada de su contrato.
