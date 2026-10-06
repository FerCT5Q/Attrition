# Plan actualizado: evaluar QVoice en el modelo de Engineering

Fecha: 2026-10-06. Estado: plan acordado, pendiente de ejecución.
Clasificación del documento: `presentation`.

## 1. Objetivo y punto de partida

Determinar qué señales de QVoice mejoran la predicción de salida voluntaria a seis meses mediante un experimento controlado.

- Usar el [playbook v11](../../output/distribution/attrition-43-variable-distributions-v11.html) y sus evidencias agregadas para priorizar candidatos. Ya existen asociaciones anuales de Intent to Stay y Career goals para 2024 y 2025.
- Comparar contra el **modelo B del 3 de octubre**, confirmado en [este análisis](../../output/analysis/engineering/20261003/playbook-tenure-confirmation-v1/confirmation-report.md): nivel, antigüedad con cortes del playbook, mes calendario, cambios de manager, salidas del equipo, reportes directos, promoción, recontratación y sus dos interacciones vigentes.
- Mantener la población: empleados regulares activos de Engineering, excluyendo RF360. Conservar inicialmente la frontera de conocimiento del **7 de septiembre de 2026**.

## 2. Señales y orden de evaluación

| Prioridad | Señal | Representación y revisión |
|---|---|---|
| 1 | **Intent to Stay** | Q4 y Q12 por separado y juntas. Evaluar también, como alternativa, la combinación del playbook: ambas respuestas favorables. |
| 2 | **Career goals** | Respuesta binaria; validar la equivalencia del texto de 2024 frente a 2025–2026. |
| 3 | **Promedio de 33 preguntas comparables** | Reproducir el conjunto exacto, fórmula y seis bandas del playbook. Examinar cuánto aporta además de Intent to Stay. |
| 4 | **Engagement** | Q1, Q2 y Q3. |
| 5 | **Workplace Connection** | Q5 y Q7 para la comparación histórica; evaluar adicionalmente el conjunto completo con Q6 desde su disponibilidad. Identificar expresamente ambas versiones. |
| 6 | **Wellbeing** | Q8, Q10 y Q11 para la comparación histórica; evaluar adicionalmente el conjunto completo con Q9 desde su disponibilidad. |
| 7 | **Confidence** | Q13 y Q17. |
| Complementaria | **Heartbeat** | Revisar Q38, Q37, Q32, Q53, Q10 y Q11 con sus tasas posteriores a la encuesta. Su entrada a pruebas temporales depende de reconstruir una definición comparable en entrenamiento y evaluación. |

Las familias se probarán mediante sus preguntas binarias componentes. Los subconjuntos históricos conservarán nombres que indiquen sus componentes; no se presentarán como el KPI completo.

Los comentarios y sus temas aportarán contexto descriptivo a las hipótesis. La extracción del experimento utilizará columnas estructuradas.

## 3. Preparación y validación de los datos anuales

**Inventario y trazabilidad**

- Revisar los Excel de 2024–2026, el diccionario y los extractores existentes. Registrar archivo, hoja, versión de pregunta, dominio, componentes y fecha verificable de disponibilidad.
- Conciliar las cifras del v11 con sus JSON, consultas y cohortes originales. Después calcular la cobertura y las asociaciones para la población específica de Engineering.
- Hacer un preflight conjunto y completar después cada evaluación secuencialmente, siguiendo el assessment v4.

**Uso en snapshots mensuales**

- Incorporar una respuesta desde la fecha verificable en que sus resultados estuvieron disponibles. El año del nombre del archivo y la fecha de lanzamiento no demostrarán esa disponibilidad.
- Mantenerla hasta la siguiente wave disponible o durante un máximo de **12 meses**, lo que ocurra primero.
- Una nueva wave reemplazará a la anterior; la ausencia de respuesta quedará identificada como dato no disponible. Evitar trasladar respuestas entre episodios separados por una salida y recontratación.
- Las predicciones a seis meses utilizarán exclusivamente información conocida en su snapshot.
- Una wave sin fecha de disponibilidad verificable quedará pendiente para el análisis predictivo.

**Respuestas incompletas**

- Distinguir pregunta ausente, respuesta faltante, valor inválido y ausencia de registro enlazable. Ninguno equivale a respuesta desfavorable.
- Exigir 33 respuestas válidas únicamente para calcular el promedio de 33 preguntas. Las otras señales conservarán sus propios criterios de validez.
- Mantener a quienes carecen de QVoice en la evaluación general y mostrar también resultados para las cohortes con respuestas disponibles.
- Comprobar duplicados, contradicciones, joins, componentes y cambios de definición. Las brechas limitarán las conclusiones y los scores correspondientes.

## 4. Experimento y criterios de éxito

**Comparaciones fijadas antes de entrenar**

1. Reproducir el modelo B y sus cuatro periodos históricos para verificar el control.
2. Comparar B contra B más cada bloque de QVoice.
3. Comparar las combinaciones: Intent to Stay + Career goals; los seis temas; Intent to Stay + Career goals + promedio de 33 preguntas.
4. Para esta última combinación, repetir el promedio excluyendo Q4 y Q12, manteniendo la misma cohorte, para medir el solapamiento.
5. Incluir controles con solo indicadores de disponibilidad para distinguir la contribución de las respuestas de la contribución de tener datos.

Todas las comparaciones usarán las mismas personas, snapshots y etiquetas dentro de cada periodo. Se conservará el hazard `cloglog`, con la regularización elegida usando únicamente datos anteriores al periodo de prueba.

**Validación temporal**

- Usar 2024 como primera historia principal de QVoice.
- Establecer dos periodos principales: **febrero–julio de 2025** y **agosto de 2025–enero de 2026**.
- Seleccionar la regularización mediante Brier mensual en los últimos tres intervalos mensuales ya observados antes de cada periodo; entrenar la selección con intervalos anteriores. Aplicar el mismo procedimiento al control.
- Exigir que los componentes evaluados tengan respuestas utilizables tanto en entrenamiento como en validación. Registrar los periodos no evaluables.
- Añadir los snapshots de 2026 que tengan seguimiento completo a seis meses como comprobación suplementaria, indicando su duración real.
- Tratar las ventanas anuales, el acumulado de 2026 y las ventanas retrospectivas del playbook según su definición. Más snapshots no equivalen a más waves independientes.

**Resultado del experimento**

Reportar PR-AUC, lift del 10% superior, Brier, calibración general y del quintil de mayor riesgo, cobertura y estabilidad por periodo. Estimar incertidumbre mediante remuestreo por persona, conservando sus observaciones mensuales juntas.

Un candidato se considerará **prometedor** si mejora PR-AUC y lift en ambos periodos principales, mantiene o reduce el Brier medio y el error de calibración, y demuestra aporte frente al control de disponibilidad. Con menos de dos periodos completos evaluables, el resultado será **evidencia temporal insuficiente**.

## 5. Entregables y comprobaciones

- Configuración versionada del experimento con candidatos, componentes, fechas, ventanas y reglas de comparación.
- Evidencia agregada y assessment v4 por concepto, con consultas guardadas, resultados y limitaciones en español.
- Informe comparativo que concluya para cada señal: **prometedora**, **sin mejora demostrada** o **evidencia insuficiente**.
- Pruebas enfocadas en fechas de disponibilidad, cambio y vencimiento de wave, recontrataciones, faltantes, fórmulas, duplicados y ausencia de información futura.
- Verificación de reproducibilidad del control y de igualdad de cohortes entre modelos; ejecución de los validadores correspondientes si cambia algún contrato.
- Ejecución bajo la [autorización vigente de procesamiento en memoria](../../config/attrition_model_in_memory_training_authorization_20261001.json), con entregables agregados clasificados como `presentation` y los mínimos de publicación del proyecto.

El resultado será una recomendación sustentada para la siguiente revisión del modelo.
