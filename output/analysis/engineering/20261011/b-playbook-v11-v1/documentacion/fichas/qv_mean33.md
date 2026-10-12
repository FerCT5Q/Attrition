# QVoice: promedio de 33 preguntas

Primera foto con valor observable en esta carga: 2025-01-26. El soporte se comprueba por año y la elegibilidad se decide sólo con el entrenamiento de cada corte. Política anual: wave 2024 sólo en fotos de 2025; wave 2025 sólo en 2026. Vigencia de 12 meses, inicio incluido/fin excluido; la wave siguiente reemplaza la anterior aunque falte respuesta. Se exige continuidad del episodio desde el ancla de la encuesta; wave 2026 reservada para 2027. Esta política no acredita la fecha real de publicación.

Modo `presentation` · variable `qv_mean33` · familia QVoice.
Empleados regulares activos de Engineering, excluyendo RF360, en cada foto mensual. Grain: persona-foto. Corte de conocimiento: 2026-09-07.

[Índice del diccionario](../diccionario.md) · [Decisiones completas](../decisiones.csv) · [Codificaciones de cada modelo](../codificaciones.csv)

## Tratamiento efectivo

| Elemento | Qué se hizo |
|---|---|
| Tipo | Promedio de binarias transformado en bandas |
| Campos de origen | qv_M01; qv_M02; qv_M03; qv_M04; qv_M05; qv_M06; qv_M07; qv_M08; qv_M09; qv_M10; qv_M11; qv_M12; qv_M13; qv_M14; qv_M15; qv_M16; qv_M17; qv_M18; qv_M19; qv_M20; qv_M21; qv_M22; qv_M23; qv_M24; qv_M25; qv_M26; qv_M27; qv_M28; qv_M29; qv_M30; qv_M31; qv_M32; qv_M33 |
| Valores de origen | Treinta y tres indicadores favorables 0/1 válidos. |
| Valores antes de agrupar categorías raras | <50; 50–69; 70–79; 80–89; 90–99; 100; no_available_wave; no_linked_row; different_employment_episode; missing |
| Transformación | 100×suma/33, sólo si las 33 respuestas son válidas. Comparaciones enteras exactas para las bandas: [0,50), [50,70), [70,80), [80,90), [90,100), {100}. Se introducen indicadores de banda, no el promedio continuo. |
| Faltantes y valores por defecto | Si falta alguna de las 33 respuestas binarias válidas → missing (incluye 255, inválida o pregunta ausente). Sin enlace o llave duplicada excluida → no_linked_row; episodio no continuo → different_employment_episode; sin wave asignada → no_available_wave. No se promedia sólo lo contestado. |
| Codificación para el modelo | Todas las entradas son categorías con indicadores 0/1. La referencia es la categoría más frecuente por filas de entrenamiento y se omite. Cada categoría restante tiene su propio indicador. Una categoría no aprendida deja todos los indicadores de ese término en cero. Las bandas no se usan como números ordinales ni se estandarizan como variables continuas. |
| Categorías raras | No se aplica agrupación de categorías raras a este término. |
| Consideraciones | Una combinación del promedio con alguna pregunta comparte información de origen; esta ronda permite ese solapamiento y no demuestra que los aportes sean independientes. |
| Uso en la definición de grupos | Puede modificar la predicción, pero no añade una dimensión de grupo en esta ronda. Los grupos siguen definidos por antigüedad, salidas del equipo y nivel. |

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
| 2025 | 390263 | 212443 | 54.4 | 12 | 6 |
| 2026 | 288586 | 162741 | 56.4 | 8 | 6 |

### Selección en cada corte

| Periodo | Base | Fotos internas observables | Cumple condiciones individual | Lista de seis | Decisión |
|---|---|---|---|---|---|
| aug_dec_2025 | B | — | Sí | Sí | No seleccionada |
| aug_dec_2025 | B_RH | — | No | Sí | No seleccionada |
| final | B | — | Sí | Sí | No seleccionada |
| final | B_RH | — | Sí | Sí | No seleccionada |
| jan_feb_2026 | B | — | Sí | Sí | No seleccionada |
| jan_feb_2026 | B_RH | — | No | Sí | No seleccionada |

- **aug_dec_2025 / B:** No quedó en la opción ganadora: al menos una opción que la incluye cumple las condiciones de validación, pero gana otra alternativa por log-loss y la preferencia por menos incorporaciones cuando la diferencia es mínima. Prueba individual: La incorporación individual cumple las condiciones de validación.
- **aug_dec_2025 / B_RH:** No quedó en la opción ganadora: al menos una opción que la incluye cumple las condiciones de validación, pero gana otra alternativa por log-loss y la preferencia por menos incorporaciones cuando la diferencia es mínima. Prueba individual: No supera: Brier no empeora.
- **final / B:** No quedó en la opción ganadora: al menos una opción que la incluye cumple las condiciones de validación, pero gana otra alternativa por log-loss y la preferencia por menos incorporaciones cuando la diferencia es mínima. Prueba individual: La incorporación individual cumple las condiciones de validación.
- **final / B_RH:** No quedó en la opción ganadora: al menos una opción que la incluye cumple las condiciones de validación, pero gana otra alternativa por log-loss y la preferencia por menos incorporaciones cuando la diferencia es mínima. Prueba individual: La incorporación individual cumple las condiciones de validación.
- **jan_feb_2026 / B:** No quedó en la opción ganadora: al menos una opción que la incluye cumple las condiciones de validación, pero gana otra alternativa por log-loss y la preferencia por menos incorporaciones cuando la diferencia es mínima. Prueba individual: La incorporación individual cumple las condiciones de validación.
- **jan_feb_2026 / B_RH:** No seleccionada. No supera: Error de grupos dentro de tolerancia. Ninguna combinación probada que la incluye supera todas las condiciones.

### Resultado externo de añadirla por separado

Cambios respecto a la misma base y población de cada periodo; valores positivos indican mejora de pérdidas o mayor captura. Estas cifras describen el resultado externo y no se emplean para seleccionar.

| Periodo | Base | Mejora log-loss (%) | Mejora Brier (%) | Cambio captura (pp) |
|---|---|---|---|---|
| aug_dec_2025 | B | 0.4 | 0.1 | 0 |
| aug_dec_2025 | B_RH | 0.3 | 0.1 | 1.3 |
| jan_feb_2026 | B | 0.6 | 0.2 | 0 |
| jan_feb_2026 | B_RH | 0.7 | 0.2 | −<0.1 |

**Frecuencia en selecciones anteriores:** B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes.

**Conclusión de selección final:** Sobre B: No seleccionada. No quedó en la opción ganadora: al menos una opción que la incluye cumple las condiciones de validación, pero gana otra alternativa por log-loss y la preferencia por menos incorporaciones cuando la diferencia es mínima. Sobre B_RH: No seleccionada. No quedó en la opción ganadora: al menos una opción que la incluye cumple las condiciones de validación, pero gana otra alternativa por log-loss y la preferencia por menos incorporaciones cuando la diferencia es mínima.

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
- [qvoice-regional.json](<../../input-evidence/qvoice-regional.json>) · registro de carga de esta ejecución · resultado del control: pass
- [qvoice-feature-support.json](<../../input-evidence/qvoice-feature-support.json>) · registro de carga de esta ejecución

La fecha de la consulta no reemplaza la fecha de conocimiento de la variable. Un control técnico pass sólo respalda la afirmación acotada de su contrato.
