# Salidas bajo el manager actual, 6 intervalos

Primera foto con valor observable en esta carga: 2023-04-23. El soporte se comprueba por año y la elegibilidad se decide sólo con el entrenamiento de cada corte. Valor o evento disponible en la propia foto t.

Modo `presentation` · variable `manager_team_exits6_v11` · familia RH.
Empleados regulares activos de Engineering, excluyendo RF360, en cada foto mensual. Grain: persona-foto. Corte de conocimiento: 2026-09-07.

[Índice del diccionario](../diccionario.md) · [Decisiones completas](../decisiones.csv) · [Codificaciones de cada modelo](../codificaciones.csv)

## Tratamiento efectivo

| Elemento | Qué se hizo |
|---|---|
| Tipo | Conteo de eventos por categoría |
| Campos de origen | manager_employee_id; term_date; term_type; fis_mo_end_dt; region; job_family; job_level_primary_position; max_hire_rehire_date; service_date; original_hire_date |
| Valores de origen | Salidas atribuidas al manager en seis intervalos fiscales mensuales anteriores a t. |
| Valores antes de agrupar categorías raras | 0; 1; 2+; (historia no confirmada) |
| Transformación | Atribuye cada salida voluntaria al manager en la foto anterior al intervalo; sólo eventos conocidos y sin contradicción conocida a t. Exposición de empleados regulares activos sin RF360, también fuera de Engineering. La variable de la persona focal toma la historia de su manager actual. Agrupa salidas6 en 0/1/2+. Usa intervalos entre fotos, no DATEADD de seis meses calendario. |
| Faltantes y valores por defecto | Sin exposición positiva, sin seis intervalos globales o antes de completar el feed → (historia no confirmada); con soporte y sin salidas → 0. |
| Codificación para el modelo | Todas las entradas son categorías con indicadores 0/1. La referencia es la categoría más frecuente por filas de entrenamiento y se omite. Cada categoría restante tiene su propio indicador. Una categoría no aprendida deja todos los indicadores de ese término en cero. Las bandas no se usan como números ordinales ni se estandarizan como variables continuas. |
| Categorías raras | Sólo incorporaciones RH: conserva categorías con al menos 300 personas distintas en todo el entrenamiento; el resto, incluidas categorías nuevas o desconocidos infrecuentes, se transforma en (other). B y QVoice no usan este pooling. Una persona puede contar en más de una categoría si cambió durante el entrenamiento; no es un mínimo por foto. |
| Consideraciones | No es idéntico a team_exits_6m: cambian ventana, atribución y puerta de observabilidad. No exige seis intervalos individuales al manager. |
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
| 2023 | 369603 | 276049 | 74.7 | 9 | 3 |
| 2024 | 363189 | 360771 | 99.3 | 12 | 3 |
| 2025 | 390263 | 386470 | 99 | 12 | 3 |
| 2026 | 288586 | 286338 | 99.2 | 8 | 3 |

### Selección en cada corte

| Periodo | Base | Fotos internas observables | Cumple condiciones individual | Lista de seis | Decisión |
|---|---|---|---|---|---|
| aug_dec_2025 | B | 19 | Sí | No | No seleccionada |
| aug_jan_2024 | B | 7 | No | No | No seleccionada |
| feb_jul_2024 | B | 1 | No | No | No seleccionada |
| feb_jul_2025 | B | 13 | No | No | No seleccionada |
| final | B | 32 | Sí | No | No seleccionada |
| jan_feb_2026 | B | 24 | No | No | No seleccionada |

- **aug_dec_2025 / B:** No quedó en la opción ganadora: al menos una opción que la incluye cumple las condiciones de validación, pero gana otra alternativa por log-loss y la preferencia por menos incorporaciones cuando la diferencia es mínima. Prueba individual: La incorporación individual cumple las condiciones de validación.
- **aug_jan_2024 / B:** No seleccionada. No supera: Brier no empeora, Error de grupos dentro de tolerancia. No entró en las seis primeras para pares y tríos.
- **feb_jul_2024 / B:** No seleccionada. Sólo 1 fotos observables de entrenamiento; se requieren seis. No entró en las seis primeras para pares y tríos.
- **feb_jul_2025 / B:** No seleccionada. No supera: PR-AUC conserva al menos el 99%. No entró en las seis primeras para pares y tríos.
- **final / B:** No quedó en la opción ganadora: al menos una opción que la incluye cumple las condiciones de validación, pero gana otra alternativa por log-loss y la preferencia por menos incorporaciones cuando la diferencia es mínima. Prueba individual: La incorporación individual cumple las condiciones de validación.
- **jan_feb_2026 / B:** No seleccionada. No supera: Brier no empeora, PR-AUC conserva al menos el 99%. No entró en las seis primeras para pares y tríos.

### Resultado externo de añadirla por separado

Cambios respecto a la misma base y población de cada periodo; valores positivos indican mejora de pérdidas o mayor captura. Estas cifras describen el resultado externo y no se emplean para seleccionar.

| Periodo | Base | Mejora log-loss (%) | Mejora Brier (%) | Cambio captura (pp) |
|---|---|---|---|---|
| aug_dec_2025 | B | 0.1 | <0.1 | -0.4 |
| aug_jan_2024 | B | 0.3 | 0.1 | -0.1 |
| feb_jul_2024 | B | 0.4 | 0.1 | 1.5 |
| feb_jul_2025 | B | 0.1 | −<0.1 | <0.1 |
| jan_feb_2026 | B | -0.1 | <0.1 | 0 |

**Frecuencia en selecciones anteriores:** B: seleccionada en 0 de 5 cortes.

**Conclusión de selección final:** Sobre B: No seleccionada. No quedó en la opción ganadora: al menos una opción que la incluye cumple las condiciones de validación, pero gana otra alternativa por log-loss y la preferencia por menos incorporaciones cuando la diferencia es mínima.

**Impacto en score de assessment:** ninguno. Los scores previos no se reasignan con estas pruebas.

**Acción:** Mantener el registro de la prueba; no concluir que carece de señal en toda representación o combinación posible.

## Codificación de los modelos finales

No aparece en los modelos finales seleccionados. Sus valores candidatos están descritos arriba; no se inventa una referencia final para una variable que no quedó en esos artefactos.

## Fuentes trazables

- [engineering_b_v11_manager_history_person_month_20261011_v3.sql](<../../../../../../../queries/profiles/engineering_b_v11_manager_history_person_month_20261011_v3.sql>)
- [v11-manager6-v2.json](<../../input-evidence/v11-manager6-v2.json>) · 2026-10-12T14:18:26.653368+00:00 · resultado del control: pass · SQL: [engineering_b_v11_manager6_v2_2020_20261011.sql](<../../../../../../../queries/audits/engineering_b_v11_manager6_v2_2020_20261011.sql>)
- [v11-manager-feed.json](<../../input-evidence/v11-manager-feed.json>) · 2026-10-12T14:12:41.377007+00:00 · resultado del control: pass · SQL: [engineering_b_v11_manager_feed_20261011.sql](<../../../../../../../queries/audits/engineering_b_v11_manager_feed_20261011.sql>)
- [v11-manager-gate-synthetic.json](<../../input-evidence/v11-manager-gate-synthetic.json>) · 2026-10-12T14:21:46.608893+00:00 · resultado del control: pass · SQL: [engineering_b_v11_manager_gate_synthetic_20261011.sql](<../../../../../../../queries/audits/engineering_b_v11_manager_gate_synthetic_20261011.sql>)
- [hr-feature-support.json](<../../input-evidence/hr-feature-support.json>) · registro de carga de esta ejecución

La fecha de la consulta no reemplaza la fecha de conocimiento de la variable. Un control técnico pass sólo respalda la afirmación acotada de su contrato.
