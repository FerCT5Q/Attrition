# Capa organizacional registrada

Primera foto con valor observable en esta carga: 2023-03-26. El soporte se comprueba por año y la elegibilidad se decide sólo con el entrenamiento de cada corte. Valor o evento disponible en la propia foto t.

Modo `presentation` · variable `layers_band` · familia RH.
Empleados regulares activos de Engineering, excluyendo RF360, en cada foto mensual. Grain: persona-foto. Corte de conocimiento: 2026-09-07.

[Índice del diccionario](../diccionario.md) · [Decisiones completas](../decisiones.csv) · [Codificaciones de cada modelo](../codificaciones.csv)

## Tratamiento efectivo

| Elemento | Qué se hizo |
|---|---|
| Tipo | Numérica almacenada, por categorías |
| Campos de origen | worker_supervisory_organization_level_from_top |
| Valores de origen | Capa organizacional numérica registrada. |
| Valores antes de agrupar categorías raras | <=6; 7; 8; 9; 10+; (unknown); (antes de la fuente) |
| Transformación | Antes de 2023-03-26 se bloquea la historia. Después se agrupa ≤6, se conservan 7/8/9 y se agrupa ≥10. |
| Faltantes y valores por defecto | Nulo → (unknown); antes de la fuente se conserva como estado distinto. |
| Codificación para el modelo | Todas las entradas son categorías con indicadores 0/1. La referencia es la categoría más frecuente por filas de entrenamiento y se omite. Cada categoría restante tiene su propio indicador. Una categoría no aprendida deja todos los indicadores de ese término en cero. Las bandas no se usan como números ordinales ni se estandarizan como variables continuas. |
| Categorías raras | Sólo incorporaciones RH: conserva categorías con al menos 300 personas distintas en todo el entrenamiento; el resto, incluidas categorías nuevas o desconocidos infrecuentes, se transforma en (other). B y QVoice no usan este pooling. Una persona puede contar en más de una categoría si cambió durante el entrenamiento; no es un mínimo por foto. |
| Consideraciones | La capa almacenada no demuestra profundidad hasta un CEO validado; se compara con la jerarquía reconstruida. |
| Uso en la definición de grupos | Puede modificar la predicción, pero no añade una dimensión de grupo en esta ronda. Los grupos siguen definidos por antigüedad, salidas del equipo y nivel. |

## Comprobación y decisión

**Pregunta:** ¿Qué aporta esta representación al añadirla a la base, con datos conocidos antes de cada corte?

**Motivo:** separar una transformación de datos de su elegibilidad y de su mejora predictiva; dejar verificable por qué se conservó o quedó fuera.

**Método:** inspección del SQL/código congelado, soporte agregado de la carga, registro de selección interna y codificaciones guardadas. La documentación no reconstruye filas ni cambia decisiones a partir de resultados externos.

**Regla de aceptación:** Ajuste válido y elegibilidad; Brier no empeora; PR-AUC ≥99% del control. En validación de seis meses, además: lift al 10% ≥99% del control, MAE de los mismos grupos ≤control+0.1 pp y captura ≥control−0.5 pp. Entre las opciones que cumplen se minimiza log-loss y se aplica parsimonia dentro de una tolerancia relativa exacta de 0.0005. Se escoge la opción con menos incorporaciones dentro de esa ventana; después log-loss e identificador.

La elegibilidad requiere al menos seis fotos observables dentro del entrenamiento de selección y más de una categoría después de agrupar las poco frecuentes. Ese entrenamiento termina antes de la reserva interna; puede ser más corto que el reajuste utilizado para evaluar el periodo externo.

### Métricas observadas de soporte

Son conteos de la representación ya transformada. «Observable» sigue los estados explícitos de ausencia del runner; no prueba por sí solo la definición oficial ni la completitud de eventos. Personas repetidas entre fotos no son personas distintas.

| Año | Persona-fotos | Observables | Cobertura (%) | Fotos observables | Categorías observables |
|---|---|---|---|---|---|
| 2020 | 142933 | 0 | 0 | 0 | 0 |
| 2021 | 307054 | 0 | 0 | 0 | 0 |
| 2022 | 347636 | 0 | 0 | 0 | 0 |
| 2023 | 369603 | 308077 | 83.4 | 10 | 5 |
| 2024 | 363189 | 363189 | 100 | 12 | 5 |
| 2025 | 390263 | 390263 | 100 | 12 | 5 |
| 2026 | 288586 | 288586 | 100 | 8 | 5 |

### Selección en cada corte

| Periodo | Base | Fotos internas observables | Cumple condiciones individual | Lista de seis | Decisión |
|---|---|---|---|---|---|
| aug_dec_2025 | B | 20 | Sí | No | No seleccionada |
| aug_jan_2024 | B | 8 | No | No | No seleccionada |
| feb_jul_2024 | B | 2 | No | No | No seleccionada |
| feb_jul_2025 | B | 14 | No | No | No seleccionada |
| final | B | 33 | No | No | No seleccionada |
| jan_feb_2026 | B | 25 | No | Sí | Seleccionada |

- **aug_dec_2025 / B:** No quedó en la opción ganadora: al menos una opción que la incluye cumple las condiciones de validación, pero gana otra alternativa por log-loss y la preferencia por menos incorporaciones cuando la diferencia es mínima. Prueba individual: La incorporación individual cumple las condiciones de validación.
- **aug_jan_2024 / B:** No seleccionada. No supera: Brier no empeora, Error de grupos dentro de tolerancia, Captura dentro de tolerancia. No entró en las seis primeras para pares y tríos.
- **feb_jul_2024 / B:** No seleccionada. Sólo 2 fotos observables de entrenamiento; se requieren seis. No entró en las seis primeras para pares y tríos.
- **feb_jul_2025 / B:** No seleccionada. No supera: PR-AUC conserva al menos el 99%. No entró en las seis primeras para pares y tríos.
- **final / B:** No seleccionada. No supera: Brier no empeora, PR-AUC conserva al menos el 99%. No entró en las seis primeras para pares y tríos.
- **jan_feb_2026 / B:** Seleccionada en combinación con Familia de puesto detallada, Sitio laboral. La combinación sí cumple, aunque la prueba individual no supera todas las condiciones. Prueba individual: No supera: Lift al 10% conserva al menos el 99%.

### Resultado externo de añadirla por separado

Cambios respecto a la misma base y población de cada periodo; valores positivos indican mejora de pérdidas o mayor captura. Estas cifras describen el resultado externo y no se emplean para seleccionar.

| Periodo | Base | Mejora log-loss (%) | Mejora Brier (%) | Cambio captura (pp) |
|---|---|---|---|---|
| aug_dec_2025 | B | -0.4 | -0.1 | -0.3 |
| aug_jan_2024 | B | 0.2 | <0.1 | -0.1 |
| feb_jul_2024 | B | 0.5 | 0.1 | 1.5 |
| feb_jul_2025 | B | 0.2 | 0.1 | 0 |
| jan_feb_2026 | B | -0.6 | -0.1 | 0 |

**Frecuencia en selecciones anteriores:** B: seleccionada en 1 de 5 cortes.

**Conclusión de selección final:** Sobre B: No seleccionada. No seleccionada. No supera: Brier no empeora, PR-AUC conserva al menos el 99%. No entró en las seis primeras para pares y tríos.

**Impacto en score de assessment:** ninguno. Los scores previos no se reasignan con estas pruebas.

**Acción:** Mantener el registro de la prueba; no concluir que carece de señal en toda representación o combinación posible.

## Codificación de los modelos finales

No aparece en los modelos finales seleccionados. Sus valores candidatos están descritos arriba; no se inventa una referencia final para una variable que no quedó en esos artefactos.

## Fuentes trazables

- [engineering_model_c_qvoice_person_month_20261008.sql](<../../../../../../../queries/profiles/engineering_model_c_qvoice_person_month_20261008.sql>)
- [hr-feature-support.json](<../../input-evidence/hr-feature-support.json>) · registro de carga de esta ejecución

La fecha de la consulta no reemplaza la fecha de conocimiento de la variable. Un control técnico pass sólo respalda la afirmación acotada de su contrato.
