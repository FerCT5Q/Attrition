# QVoice: inquietud de política presencial

Primera foto con valor observable en esta carga: 2025-01-26. El soporte se comprueba por año y la elegibilidad se decide sólo con el entrenamiento de cada corte. Política anual: wave 2024 sólo en fotos de 2025; wave 2025 sólo en 2026. Vigencia de 12 meses, inicio incluido/fin excluido; la wave siguiente reemplaza la anterior aunque falte respuesta. Se exige continuidad del episodio desde el ancla de la encuesta; wave 2026 reservada para 2027. Esta política no acredita la fecha real de publicación.

Modo `presentation` · variable `qv_onsite_policy_concern` · familia QVoice.
Empleados regulares activos de Engineering, excluyendo RF360, en cada foto mensual. Grain: persona-foto. Corte de conocimiento: 2026-09-07.

[Índice del diccionario](../diccionario.md) · [Decisiones completas](../decisiones.csv) · [Codificaciones de cada modelo](../codificaciones.csv)

## Tratamiento efectivo

| Elemento | Qué se hizo |
|---|---|
| Tipo | Indicador textual derivado con estados de ausencia |
| Campos de origen | Prompt doing_well; Prompt can_improve; Prompt processes_to_improve |
| Valores de origen | Comentarios de los prompts declarados, procesados sólo en RAM. No se publican textos ni ejemplos individuales. |
| Valores antes de agrupar categorías raras | v0; v1; no_comment; no_available_wave; no_linked_row; different_employment_episode; duplicate |
| Transformación | Normaliza espacios y casefold; los patrones literales se buscan con límites de palabra. Se usan taxonomías completas congeladas, sin escoger temas según salidas futuras. En una misma cláusula, exige un patrón objetivo presencial y otro de inquietud de política; retira home office. Tras normalizar espacios (incluidos saltos de línea), separa prompts con punto y cláusulas por puntuación; cualquier cláusula que cumple → v1; texto que no cumple → v0; sin texto → no_comment. |
| Faltantes y valores por defecto | Sin wave → no_available_wave; sin enlace → no_linked_row; llave repetida → duplicate; episodio no continuo → different_employment_episode (tiene prioridad). La ausencia de comentario se conserva; no se interpreta como ausencia del tema en una respuesta existente. |
| Codificación para el modelo | Todas las entradas son categorías con indicadores 0/1. La referencia es la categoría más frecuente por filas de entrenamiento y se omite. Cada categoría restante tiene su propio indicador. Una categoría no aprendida deja todos los indicadores de ese término en cero. Las bandas no se usan como números ordinales ni se estandarizan como variables continuas. |
| Categorías raras | No se aplica agrupación de categorías raras a este término. |
| Consideraciones | 2024 tiene doing_well y can_improve; processes_to_improve aparece desde 2025. Las menciones pueden pertenecer a varios temas y no prueban sentimiento, intención de salida ni causalidad. Patrones de palabras pueden producir falsos positivos/negativos; se contrasta contenido con disponibilidad emparejada. |
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
| 2025 | 390263 | 153450 | 39.3 | 12 | 2 |
| 2026 | 288586 | 106482 | 36.9 | 8 | 2 |

### Selección en cada corte

| Periodo | Base | Fotos internas observables | Cumple condiciones individual | Lista de seis | Decisión |
|---|---|---|---|---|---|
| aug_dec_2025 | B | — | No | No | No seleccionada |
| aug_dec_2025 | B_RH | — | No | No | No seleccionada |
| final | B | — | No | No | No seleccionada |
| final | B_RH | — | No | No | No seleccionada |
| jan_feb_2026 | B | — | No | No | No seleccionada |
| jan_feb_2026 | B_RH | — | No | No | No seleccionada |

- **aug_dec_2025 / B:** No seleccionada. No supera: Brier no empeora. No entró en las seis primeras para pares y tríos.
- **aug_dec_2025 / B_RH:** No seleccionada. No supera: Brier no empeora. No entró en las seis primeras para pares y tríos.
- **final / B:** No seleccionada. No supera: Brier no empeora. No entró en las seis primeras para pares y tríos.
- **final / B_RH:** No seleccionada. No supera: Brier no empeora. No entró en las seis primeras para pares y tríos.
- **jan_feb_2026 / B:** No seleccionada. No supera: Brier no empeora. No entró en las seis primeras para pares y tríos.
- **jan_feb_2026 / B_RH:** No seleccionada. No supera: Brier no empeora, Error de grupos dentro de tolerancia. No entró en las seis primeras para pares y tríos.

### Resultado externo de añadirla por separado

Cambios respecto a la misma base y población de cada periodo; valores positivos indican mejora de pérdidas o mayor captura. Estas cifras describen el resultado externo y no se emplean para seleccionar.

| Periodo | Base | Mejora log-loss (%) | Mejora Brier (%) | Cambio captura (pp) |
|---|---|---|---|---|
| aug_dec_2025 | B | <0.1 | <0.1 | 0 |
| aug_dec_2025 | B_RH | <0.1 | −<0.1 | 0.7 |
| jan_feb_2026 | B | -0.1 | <0.1 | 0 |
| jan_feb_2026 | B_RH | 0.1 | <0.1 | 0 |

**Frecuencia en selecciones anteriores:** B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes.

**Conclusión de selección final:** Sobre B: No seleccionada. No seleccionada. No supera: Brier no empeora. No entró en las seis primeras para pares y tríos. Sobre B_RH: No seleccionada. No seleccionada. No supera: Brier no empeora. No entró en las seis primeras para pares y tríos.

**Impacto en score de assessment:** ninguno. Los scores previos no se reasignan con estas pruebas.

**Acción:** Mantener el registro de la prueba; no concluir que carece de señal en toda representación o combinación posible.

## Codificación de los modelos finales

No aparece en los modelos finales seleccionados. Sus valores candidatos están descritos arriba; no se inventa una referencia final para una variable que no quedó en esos artefactos.

## Fuentes trazables

- [qvoice-comments.json](<../../../../../../../config/b_playbook_v11_contracts/qvoice-comments.json>)
- [b_v11_qvoice_comments.py](<../../../../../../../tools/b_v11_qvoice_comments.py>)
- [build_qvoice_comment_evidence.py](<../../../../../../../tools/build_qvoice_comment_evidence.py>)
- [build_qvoice_retention_concerns_evidence.py](<../../../../../../../tools/build_qvoice_retention_concerns_evidence.py>)
- [build_qvoice_open_text_request_concern_evidence.py](<../../../../../../../tools/build_qvoice_open_text_request_concern_evidence.py>)
- [source-metadata.json](<../../../../20261008/qvoice-model-b-calibrated-v1/preflight/source-metadata.json>)
- [v11-qvoice-comments.json](<../../input-evidence/v11-qvoice-comments.json>) · 2026-10-12T15:12:44.390952+00:00 · resultado del control: pass · SQL: [engineering_b_v11_qvoice_link_person_month_20261011.sql](<../../../../../../../queries/profiles/engineering_b_v11_qvoice_link_person_month_20261011.sql>)
- [v11-qvoice-comment-keys.json](<../../input-evidence/v11-qvoice-comment-keys.json>) · 2026-10-12T15:09:51.902961+00:00 · resultado del control: pass
- [model-qvoice-comments.json](<../../input-evidence/model-qvoice-comments.json>) · registro de carga de esta ejecución · resultado del control: pass
- [qvoice-feature-support.json](<../../input-evidence/qvoice-feature-support.json>) · registro de carga de esta ejecución

La fecha de la consulta no reemplaza la fecha de conocimiento de la variable. Un control técnico pass sólo respalda la afirmación acotada de su contrato.
