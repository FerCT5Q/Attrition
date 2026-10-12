# Nuevo modelo B + QVoice: búsqueda y calibración temporal

Clasificación: `presentation`. Diseño fijado el 8 de octubre de 2026, antes de ejecutar la búsqueda. El usuario autoriza desarrollar un modelo nuevo y compararlo con B.

## Objetivo y población

Predecir la salida voluntaria a seis meses de empleados regulares activos de Engineering, excluyendo RF360. El grain de ajuste es persona-snapshot con etiqueta del intervalo mensual posterior. Las filas, llaves efímeras y predicciones permanecen en memoria bajo la autorización del 1 de octubre. Sólo se publican parámetros del modelo y agregados de cohortes con al menos 30 personas y 30 eventos.

## Alcance de candidatos

Ocho bloques: Q4, Q12, Career, promedio binario de 33 preguntas, Engagement (Q1/Q2/Q3), Connection histórico (Q5/Q7), Wellbeing histórico (Q8/Q10/Q11) y Confidence (Q13/Q17). Se exploran las 255 combinaciones no vacías. La búsqueda es exhaustiva entre bloques; no entre todos los ítems ni todas las interacciones posibles.

Se añade PCA sobre los 33 ítems binarios comparables, con 1, 2, 3, 5 o 10 componentes. Las medias de imputación, escalas y cargas se aprenden sólo en ajuste; los faltantes llevan indicadores propios. Se publican correlaciones agregadas como diagnóstico de redundancia, sin interpretarlas como importancia causal. PCA maximiza varianza de respuestas y su utilidad predictiva se decide con etiquetas posteriores en validación.

Q6 y Q9 están ausentes en 2024, y Heartbeat no puede reconstruirse con sus 53 ordinales en 2024/2025. Esos bloques no pueden participar en los dos periodos principales bajo la política Y → Y+1. Los comentarios quedan excluidos. Career se conserva como sensibilidad exploratoria por la redacción de 2024.

## Arquitectura

Se conserva la receta B de diez features, interacciones y enlace cloglog. El nuevo modelo añade una corrección QVoice al predictor lineal de B:

`eta_nuevo = eta_B + X_QVoice beta_QVoice`

`h_calibrado = 1 - exp(-exp(a + b eta_nuevo))`, con pendiente positiva.

El riesgo se calcula como `R_6m = 1 - producto(1 - h_m)`; se avanza el calendario conocido y se congelan las demás covariables en cada snapshot. B se ajusta primero y sirve como offset fijo al estimar la corrección. Esta extensión es distinta del reajuste conjunto de todas las features usado en las nueve variantes previas; debe quedar rotulada en la comparación.

Los ajustes B usados como offset fijan L2 en 10. El B de referencia de cada periodo conserva el L2 elegido por su validación mensual anterior. La búsqueda exhaustiva modifica la corrección QVoice, mientras mantiene común el B de soporte entre candidatos.

## Separación temporal

Para cada corte, sólo entran intervalos cuya etiqueta mensual termina antes del corte. Los dos últimos intervalos se reservan para calibración. Los dos anteriores se reservan para selección. Los restantes ajustan los candidatos.

La combinación y L2 (0.1, 1, 10) se eligen por Brier mensual en selección, con desempate por complejidad y L2. El valor de selección es optimista después de muchas comparaciones y no se presenta como resultado final. Se reajustan B y la corrección elegida usando ajuste más selección; después se estima el intercepto y la pendiente de calibración con los dos intervalos reservados. No se vuelve a ajustar el modelo tras calibrarlo. La pendiente se limita a 0.25–4 y tiene penalización 10 hacia 1; el intercepto queda libre.

Se comparan B con toda su historia anterior al corte, B con el mismo entrenamiento y calibración del candidato, B más disponibilidad calibrado, y B + QVoice antes y después de calibrar. Estos controles permiten distinguir información QVoice de cambios de calibración o entrenamiento.

Periodos: agosto–diciembre de 2025 y enero–febrero de 2026, con seguimiento de seis meses dentro del corte 7 de septiembre de 2026. La selección se repite usando únicamente historia anterior a cada periodo. Estos periodos ya se inspeccionaron en el desarrollo previo: constituyen validación retrospectiva del procedimiento, no una prueba externa completamente nueva.

Finalmente se aplica el mismo procedimiento al corte disponible para producir un artefacto entrenado con parámetros, transformaciones, selección y calibración reproducibles. Sus coeficientes se distinguen de los modelos históricos de evaluación.

## Comprobaciones

Verificar cortes y no solapamiento de etiquetas, componentes presentes, coincidencia de cohortes, dominio probabilístico, solver y transformación de calibración. Comparar las fórmulas del solver con una implementación independiente y comprobar que el artefacto serializado reproduce predicciones en datos sintéticos. La evaluación usa PR-AUC, lift@10%, Brier y errores absolutos de calibración general y del quintil superior. Bootstrap pareado de 500 réplicas por persona, condicional a la selección y modelos ya ajustados.

El criterio conjunto conserva mejoras de ranking en ambos periodos y no deterioro medio de Brier ni calibración frente a los controles. Calibrar no garantiza que el error de calibración futuro disminuya; el resultado se informa tal como se observe. Los scores de disponibilidad de variables no se elevan por su resultado predictivo.
