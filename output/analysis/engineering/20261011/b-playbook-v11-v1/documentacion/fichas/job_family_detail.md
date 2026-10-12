# Familia de puesto detallada

Primera foto con valor observable en esta carga: 2020-07-26. El soporte se comprueba por año y la elegibilidad se decide sólo con el entrenamiento de cada corte. Valor o evento disponible en la propia foto t.

Modo `presentation` · variable `job_family_detail` · familia RH.
Empleados regulares activos de Engineering, excluyendo RF360, en cada foto mensual. Grain: persona-foto. Corte de conocimiento: 2026-09-07.

[Índice del diccionario](../diccionario.md) · [Decisiones completas](../decisiones.csv) · [Codificaciones de cada modelo](../codificaciones.csv)

## Tratamiento efectivo

| Elemento | Qué se hizo |
|---|---|
| Tipo | Categoría nominal |
| Campos de origen | job_family |
| Valores de origen | Etiquetas registradas de familia de puesto; vocabulario abierto. |
| Valores antes de agrupar categorías raras | Etiquetas normalizadas de job_family; (unknown) |
| Transformación | UPPER(TRIM(campo)); conserva la etiqueta de la propia foto. No se asigna distancia ordinal entre categorías. |
| Faltantes y valores por defecto | Nulo o blanco → (unknown); el pooling posterior usa sólo entrenamiento. |
| Codificación para el modelo | Todas las entradas son categorías con indicadores 0/1. La referencia es la categoría más frecuente por filas de entrenamiento y se omite. Cada categoría restante tiene su propio indicador. Una categoría no aprendida deja todos los indicadores de ese término en cero. Las bandas no se usan como números ordinales ni se estandarizan como variables continuas. |
| Categorías raras | Sólo incorporaciones RH: conserva categorías con al menos 300 personas distintas en todo el entrenamiento; el resto, incluidas categorías nuevas o desconocidos infrecuentes, se transforma en (other). B y QVoice no usan este pooling. Una persona puede contar en más de una categoría si cambió durante el entrenamiento; no es un mínimo por foto. |
| Consideraciones | Los valores concretos que conserva un modelo final se listan en su codificación; el catálogo de origen puede cambiar por fecha. |
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
| 2020 | 142933 | 142933 | 100 | 6 | 47 |
| 2021 | 307054 | 307054 | 100 | 12 | 53 |
| 2022 | 347636 | 347636 | 100 | 12 | 58 |
| 2023 | 369603 | 369603 | 100 | 12 | 57 |
| 2024 | 363189 | 363189 | 100 | 12 | 54 |
| 2025 | 390263 | 390263 | 100 | 12 | 56 |
| 2026 | 288586 | 288586 | 100 | 8 | 58 |

### Selección en cada corte

| Periodo | Base | Fotos internas observables | Cumple condiciones individual | Lista de seis | Decisión |
|---|---|---|---|---|---|
| aug_dec_2025 | B | 52 | Sí | Sí | Seleccionada |
| aug_jan_2024 | B | 40 | Sí | Sí | Seleccionada |
| feb_jul_2024 | B | 34 | Sí | Sí | Seleccionada |
| feb_jul_2025 | B | 46 | Sí | Sí | Seleccionada |
| final | B | 65 | Sí | Sí | Seleccionada |
| jan_feb_2026 | B | 57 | Sí | Sí | Seleccionada |

- **aug_dec_2025 / B:** Seleccionada en combinación con Ciudad laboral, Salidas observadas/esperadas del manager, 6 intervalos. Prueba individual: La incorporación individual cumple las condiciones de validación.
- **aug_jan_2024 / B:** Seleccionada en combinación con Ciudad laboral, Experiencia previa. Prueba individual: La incorporación individual cumple las condiciones de validación.
- **feb_jul_2024 / B:** Seleccionada en combinación con Tiempo en nivel, Ciudad laboral. Prueba individual: La incorporación individual cumple las condiciones de validación.
- **feb_jul_2025 / B:** Seleccionada en combinación con Ciudad laboral, Salidas observadas/esperadas del manager, 6 intervalos. Prueba individual: La incorporación individual cumple las condiciones de validación.
- **final / B:** Seleccionada en combinación con Ciudad laboral, Aproximación postal a oficinas de la ciudad (Onsite). Prueba individual: La incorporación individual cumple las condiciones de validación.
- **jan_feb_2026 / B:** Seleccionada en combinación con Sitio laboral, Capa organizacional registrada. Prueba individual: La incorporación individual cumple las condiciones de validación.

### Resultado externo de añadirla por separado

Cambios respecto a la misma base y población de cada periodo; valores positivos indican mejora de pérdidas o mayor captura. Estas cifras describen el resultado externo y no se emplean para seleccionar.

| Periodo | Base | Mejora log-loss (%) | Mejora Brier (%) | Cambio captura (pp) |
|---|---|---|---|---|
| aug_dec_2025 | B | 0.6 | 0.2 | -0.1 |
| aug_jan_2024 | B | 0.8 | 0.2 | <0.1 |
| feb_jul_2024 | B | 0.9 | 0.2 | 0.3 |
| feb_jul_2025 | B | 0.9 | 0.3 | 0 |
| jan_feb_2026 | B | 1.3 | 0.4 | 0.6 |

**Frecuencia en selecciones anteriores:** B: seleccionada en 5 de 5 cortes.

**Conclusión de selección final:** Sobre B: Seleccionada. Seleccionada en combinación con Ciudad laboral, Aproximación postal a oficinas de la ciudad (Onsite).

**Impacto en score de assessment:** ninguno. Los scores previos no se reasignan con estas pruebas.

**Acción:** Conservar como candidata experimental y confirmar en datos posteriores; no sustituye automáticamente el modelo vigente.

## Codificación de los modelos finales

| Modelo | Referencia omitida | Número de indicadores | Niveles aprendidos |
|---|---|---|---|
| final-B-RH | SOFTWARE ENGINEERING | 24 | (other); ACQUISITION - TECHNICAL; ASICS ENGINEERING; CAMERA ENGINEERING; CELLULAR SYSTEM TEST ENGINEERING; CELLULAR TECHNOLOGIES; CELLULAR TECHNOLOGIES SOFTWARE; CPU ENGINEERING; GPU ASICS ENGINEERING; HARDWARE APPLICATIONS ENGINEERING; HARDWARE ENGINEERING; HARDWARE SYSTEMS ENGINEERING; MACHINE LEARNING ENGINEERING; MODEM ENGINEERING; MODEM SOFTWARE ENGINEERING; MODEM TECHNOLOGIES; MODEM TECHNOLOGIES SOFTWARE; MULTIMEDIA SYSTEMS; PACKAGING ENGINEERING; RFIC DESIGN; SOFTWARE APPLICATIONS ENGINEERING; SOFTWARE ENGINEERING; SOFTWARE TEST ENGINEERING; SYSTEMS ENGINEERING; SYSTEMS TEST ENGINEERING |
| final-B_RH-Q | SOFTWARE ENGINEERING | 24 | (other); ACQUISITION - TECHNICAL; ASICS ENGINEERING; CAMERA ENGINEERING; CELLULAR SYSTEM TEST ENGINEERING; CELLULAR TECHNOLOGIES; CELLULAR TECHNOLOGIES SOFTWARE; CPU ENGINEERING; GPU ASICS ENGINEERING; HARDWARE APPLICATIONS ENGINEERING; HARDWARE ENGINEERING; HARDWARE SYSTEMS ENGINEERING; MACHINE LEARNING ENGINEERING; MODEM ENGINEERING; MODEM SOFTWARE ENGINEERING; MODEM TECHNOLOGIES; MODEM TECHNOLOGIES SOFTWARE; MULTIMEDIA SYSTEMS; PACKAGING ENGINEERING; RFIC DESIGN; SOFTWARE APPLICATIONS ENGINEERING; SOFTWARE ENGINEERING; SOFTWARE TEST ENGINEERING; SYSTEMS ENGINEERING; SYSTEMS TEST ENGINEERING |

## Fuentes trazables

- [engineering_b_incremental_pending_person_month_20261011_v2.sql](<../../../../../../../queries/profiles/engineering_b_incremental_pending_person_month_20261011_v2.sql>)
- [job-family.json](<../../input-evidence/job-family.json>) · 2026-10-12T02:05:37.605896+00:00 · resultado del control: pass · SQL: [engineering_b_incremental_job_family_20261011.sql](<../../../../../../../queries/audits/engineering_b_incremental_job_family_20261011.sql>)
- [hr-feature-support.json](<../../input-evidence/hr-feature-support.json>) · registro de carga de esta ejecución

La fecha de la consulta no reemplaza la fecha de conocimiento de la variable. Un control técnico pass sólo respalda la afirmación acotada de su contrato.
