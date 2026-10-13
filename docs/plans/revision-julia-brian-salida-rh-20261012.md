# Revisión de los comentarios de Julia y Brian: salida para RH

Fecha de revisión: 12-oct-2026. Modo: `presentation`.
Fuente de los comentarios: captura compartida por el usuario en esta conversación.
Estado: revisión documental y de implementación; las pruebas propuestas abajo todavía no se ejecutan.

## Lectura principal

Los comentarios piden completar la utilidad del modelo para RH: identificar
grupos, comunicar la incertidumbre, orientar una conversación y dar seguimiento
a una acción. La mejora predictiva de F + QVoice frente a CQ justifica mantenerlo
como candidato, pero no demuestra por sí sola que esa salida esté lista.

Se propone cerrar estos puntos sobre F + QVoice, conservando CQ como comparación.
F = C + ciudad laboral; F + QVoice no incluye BU L3 ni `job_family_detail`.
F + QVoice + BU L3 es una variante adicional que debe identificarse aparte.
La población de estas comparaciones es Engineering, Employee, Regular, activa
y sin RF360, con fotos de agosto–diciembre de 2025 y enero–febrero de 2026 y
salida voluntaria en los seis meses siguientes.

## Observaciones, estado y respuesta propuesta

| Comentario de Julia | Qué encontramos | Respuesta propuesta |
|---|---|---|
| Resultado accionable y comprensible para líderes de RH | Existe un marco conceptual de señales y acciones; la evidencia reciente se centra en comparar modelos. | Entregar una ficha por grupo con magnitud, temas a investigar, responsable de RH, acción candidata y fecha de seguimiento. |
| Tratamiento de quienes no tienen respuesta QVoice | El procesamiento conserva estados de ausencia separados de las respuestas. Esto permite estimar riesgo, pero no demuestra igual desempeño en esos casos. | Mostrar cobertura válida por grupo y evaluar error, captura y calibración según disponibilidad de QVoice. No atribuir una opinión a quienes no tienen respuesta utilizable. |
| Clasificar las variables y vincularlas con acciones | Ya existe una clasificación conceptual de contexto, señal, palanca y acción. El resumen de 43 filas corresponde a B + playbook V11, no al CQ seleccionado ni a FQ. | Añadir a la documentación del modelo exacto columnas de uso, acción organizacional posible, responsable y cautela. Mantener separada su inclusión predictiva de su utilidad para actuar. |
| Mostrar personas, salidas, riesgo, intervalo, observado, cobertura y antigüedad | CQ guarda parte de los tamaños y errores por grupo y por periodo; no contiene una ficha completa con todos estos campos. FQ guarda principalmente resúmenes. | Definir primero denominadores y ventanas. Completar el contrato de ficha descrito abajo. |
| Presentar 10%, 20% y 30% como capacidad operativa | CQ tiene escenarios archivados de 20%, 30% y 40%. Los resultados guardados de FQ resumen el 30%. El lift individual al 10% no equivale a priorizar grupos que cubran el 10%. | Comparar ambas variantes a capacidades de grupos del 10%, 20% y 30%, con los mismos cortes y población. Traducir cada escenario a personas, grupos y esfuerzo de RH. |
| Curvas y estabilidad de calibración | Se probaron escalares R6 en CQ y existen diagnósticos globales; el elegido usa identidad. La auditoría ligera de FQ no evaluó curvas ni calibración por grupo. | Evaluar probabilidades contra resultados observados por bandas, grupo y fecha. Comparar una corrección sólo si hay evidencia de desajuste y datos anteriores suficientes para entrenarla. |
| Estabilidad mensual del score y del ranking | Ganar métricas en dos bloques no mide cuánto cambian los grupos cada mes. No se identificó en los resultados FQ revisados un diagnóstico mensual completo. | Medir cambios de riesgo, posición y pertenencia a prioridad entre fotos consecutivas, distinguiendo cambios de composición y de encuesta. |
| Concentración desigual por región, nivel, antigüedad y QVoice | Las métricas globales no resuelven esta pregunta. Excluir atributos protegidos del predictor tampoco garantiza ausencia de sesgo. | Contrastar representación en prioridad, cobertura, observado, predicho y error por esos segmentos, con soporte e incertidumbre. Una diferencia no demuestra por sí sola injusticia ni exige tasas idénticas. |
| Uso para conversaciones organizacionales, sin decisiones laborales individuales | Concuerda con el alcance de cohortes del proyecto. | Entregar agregados y temas por validar; no entregar puntuaciones, respuestas, explicaciones o listas de empleados para etiquetar o sancionar. |

## Cómo tratar QVoice en la salida

El enlace actual distingue, entre otros, `missing`, `no_linked_row`,
`different_employment_episode`, `no_available_wave` y `question_absent`.
`no_linked_row` significa que no se obtuvo una respuesta enlazable después del
procesamiento; no demuestra una decisión de no participar.

Los estados observados en entrenamiento entran como categorías en la corrección
QVoice. Por ello, ausencia de encuesta no significa que el modelo vuelva
automáticamente a C o F sin Q: también puede influir el coeficiente del estado
de ausencia y el intercepto de la corrección. Un estado nunca observado carece
de un coeficiente propio. Este comportamiento debe explicarse y comprobarse.

Para RH, usar «sin información QVoice utilizable» y evitar inferencias de
descontento. El desempeño debe revisarse con y sin información válida, incluyendo
respuestas parciales cuando proceda. Un retorno explícito al modelo RH sería
una política alternativa por evaluar, no una descripción de lo ya implementado.

La cobertura principal propuesta es personas del grupo con información válida
para los campos QVoice requeridos / personas del grupo en esa foto. Añadir
cobertura por bloque para no ocultar respuestas parciales. La proporción de
respuestas válidas entre invitados elegibles es otra medida y requiere su propio
denominador; no se puede llamar tasa de participación al porcentaje enlazado.

Mostrar fecha de la encuesta, fecha de disponibilidad acreditada y fecha de la
foto de RH por separado. La política anual asigna encuesta Y a fotos Y+1, pero
no acredita una fecha real de publicación. El dato ausente debe mostrarse como
no acreditado, sin inventar su antigüedad operacional.

## Clasificación para acciones

Las categorías que propone Julia se pueden superponer. Conviene distinguir dos
ejes: utilidad para actuar/priorizar y cautela al interpretar/comunicar.
Todas las explicaciones que se entreguen deben ser organizacionales y agregadas.
«Potencialmente accionable» significa que existe un proceso que RH puede revisar;
no que modificar la variable vaya a reducir causalmente las salidas.

Ejemplos para diseñar la tabla, sin atribuirles un efecto causal medido:

| Señal o concepto | Utilidad | Tema o acción candidata | Responsable propuesto | Cautela |
|---|---|---|---|---|
| Tiempo desde promoción; tiempo en nivel | Carrera y priorización | Revisar acceso a desarrollo, movilidad y criterios de progresión | RH y responsables de desarrollo | Tiempo transcurrido no equivale a tiempo esperando una promoción ni prueba que sea debida. |
| Compa-ratio | Revisión de compensación | Revisar alineación de bandas y equidad interna a nivel de cohorte | Compensación y RH | No recomendar incrementos individuales a partir del score. |
| Cambios de manager | Contexto de transición | Escuchar sobre continuidad, claridad y apoyo durante cambios | RH y liderazgo | Un cambio no demuestra mala gestión; puede ser reorganización o movilidad positiva. |
| Salidas previas del equipo; tamaño del equipo | Contexto organizacional | Validar carga, vacantes y soporte disponible | RH y responsables operativos | Salidas previas y tamaño no miden directamente carga de trabajo ni desempeño del manager. |
| Career, bienestar o confianza QVoice, si los usa la versión | Temas de escucha agregada | Validar con escucha estructurada los temas con respuestas suficientes | RH y responsables de encuesta | No revelar respuestas ni extrapolarlas a quienes carecen de información válida. |
| Antigüedad, nivel, región, ciudad | Contexto y priorización | Localizar necesidades y comparar cohortes pertinentes | RH responsable de la población | No son palancas que deban cambiarse para bajar el score. |
| BU L3, en su variante experimental | Contexto y asignación organizacional | Identificar un ámbito de seguimiento y posible responsable | RH de la unidad | La unidad no es una causa; la viabilidad de subdividir grupos sigue pendiente de corrección. |

Tabla completa propuesta: variable/representación, modelo y corte donde se usa,
codificación, uso para prioridad, proceso potencialmente accionable, evidencia
que debe validar RH, responsable, cautela y motivo de exclusión cuando corresponda.
Una señal correlacionada o un coeficiente no basta para afirmar que un tema
explica el riesgo específico de un grupo.

## Contrato propuesto de la ficha de grupo

| Campo | Definición necesaria |
|---|---|
| Grupo y fecha | Regla estable de pertenencia y fecha de la foto; dimensión organizacional y responsable cuando sean reportables. |
| Personas | Headcount de personas distintas en esa foto. En una única foto deduplicada, «personas» y «personas distintas» coinciden. |
| Historia | Si se combinan meses, mostrar por separado observaciones persona-foto y personas distintas en toda la ventana. No sumar headcounts y llamarlos personas únicas. |
| Salidas observadas | Numerador de la tasa, tipo de salida y horizonte. En una ventana con seguimientos superpuestos distinguir exposiciones con evento de salidas/personas únicas. |
| Riesgo estimado | Media de probabilidades R6 del grupo en la foto. Rotular «salida voluntaria en próximos seis meses». |
| Incertidumbre | Intervalo del estimador de riesgo identificado por método y alcance. Un intervalo de la tasa observada no es un intervalo del riesgo pronosticado. |
| Tasa observada y error | Salidas / población correspondiente con seis meses de seguimiento completo; error absoluto frente al pronóstico de esa misma cohorte. Si el seguimiento no maduró, mostrar «pendiente». |
| QVoice | Cobertura válida, respuestas parciales, encuesta utilizada y antigüedad; no exponer estados individuales. |
| Estabilidad | Cambio mensual del riesgo y de prioridad, con advertencia cuando cambió la definición o composición del grupo. |
| Acción y seguimiento | Tema por validar, responsable, próxima conversación, métrica de proceso y fecha de revisión. |

Se debe distinguir una ficha de pronóstico actual de una ficha de validación
histórica. El observado de una cohorte anterior puede servir de referencia,
pero no debe presentarse como validación del pronóstico recién emitido.

Para ventanas repetidas, la incertidumbre debe conservar juntas las observaciones
de una persona. Los intervalos por persona son condicionales a modelos y grupos
ya elegidos; no incluyen automáticamente la incertidumbre de seleccionar
variables ni toda la dependencia entre equipos. La ficha no debe prometer un
IC del pronóstico a partir del bootstrap de diferencias de métricas existente.

Los mínimos de publicación y de elegibilidad operativa son diferentes. La regla
general de publicación es al menos 30 personas, con las guardas adicionales de
eventos de la ejecución. CQ usa 300 personas por grupo y foto para priorización.
Un grupo sin soporte publicable conserva su supresión; no se expone para hacer
que la ficha parezca completa.

## Calibración, capacidad y continuidad

No aplicar calibración adicional no demuestra que un modelo esté mal calibrado.
En CQ, el primer corte utilizó identidad por historia insuficiente y el segundo
ajustó un escalar cercano a identidad. Eso tampoco demuestra que FQ esté bien
calibrado en todos los grupos. Es necesario inspeccionar sesgo, errores por
bandas, grupos y tiempo antes de elegir identidad o una corrección.

Las bandas de riesgo se definen con entrenamiento/calibración anterior al corte,
con soporte suficiente y sin elegir límites para mejorar el resultado del test.
El calibrador se ajusta sólo con observaciones maduras anteriores a evaluación.
Se compara identidad frente a una corrección sencilla y se mantiene identidad
si la corrección no aporta. No abrir otra búsqueda de variables para esta tarea.

La capacidad del 30% representa un escenario de atención. No significa que ese
30% vaya a salir. El método actual usa fracciones uniformes de grupos en el
límite para igualar capacidades; para RH deben mostrarse también los escenarios
que incluyen o excluyen el grupo completo y su headcount real. El esfuerzo puede
depender de grupos y responsables, además de personas.

Para continuidad mensual, usar los mismos grupos y reportar cambio absoluto en
riesgo, cambios de posición, entrada/salida de prioridad y solapamiento entre
meses. Mostrar separadamente cambios por nueva encuesta, altas/bajas o cambio de
composición. Una suavización o permanencia mínima sólo sería una política a
evaluar, porque puede retrasar la detección de un cambio real.

## Correcciones de interpretación encontradas en esta revisión

1. **B y C se confundieron en la explicación anterior.** Las cifras de log-loss
   138.8 → 137.7 y captura 42.4% → 43.1% correspondían a C → CQ, no a B → CQ.
   Las mejoras de FQ frente a CQ siguen respaldadas por los resultados, pero
   «ninguna métrica empeora» se limita a las métricas agregadas comparadas en
   esos dos cortes. No describe cada grupo, empleado, capacidad o modelo base.
2. **Las 25 comprobaciones de FQ son una auditoría de agregados.** Comparan
   métricas, listas de predictores, nombres de periodos y selecciones registradas
   entre dos corridas. No generan nuevas predicciones fuera de muestra,
   intervalos de FQ frente a CQ, curvas de calibración, estabilidad mensual ni
   una nueva auditoría de personas idénticas. El nombre «validación formal» no
   debe hacer parecer terminadas esas tareas.
3. **Ganar captura estrictamente en ambos periodos es una condición histórica.**
   El contexto vigente ya documenta que CQ fue elegido considerando magnitud,
   precisión y utilidad, aun ganando un corte y empatando otro. El empate de FQ
   no demuestra inferioridad ni impide registrarlo como candidato. Cualquier
   nueva regla de selección debe explicitarse, sin presentar una regla antigua
   como impedimento universal.
4. **El `REST` de la subdivisión selectiva v7 no es comparable al del baseline.**
   `evaluate_two_stage_groups` define elegibilidad como tamaño suficiente Y
   pertenencia a un grupo priorizado; después cuenta todos los no elegibles
   como `rest`. Eso incluye a personas fuera de la selección de riesgo aunque
   sus grupos base sean válidos. El 67.7% reportado no mide sólo fragmentación.
   La función tampoco conserva el padre para subceldas sin tamaño suficiente.
   Por tanto, la conclusión anterior de descartar la propuesta selectiva era
   demasiado fuerte. La propuesta de conservar los grupos no priorizados y
   subdividir sólo los de riesgo necesita una evaluación corregida. Los fallos
   de capacidad y error de aquella implementación quedan como resultados de
   esa implementación, sin generalizarlos a todas las variantes selectivas.

Para corregir esa prueba, conservar grupos base fuera de prioridad y, dentro de
los priorizados, mantener el padre cuando la partición completa no cumpla soporte
o agrupar remanentes con una regla predefinida. Las celdas finales deben ser
mutuamente excluyentes, exhaustivas y sin doble conteo de padre e hijos. Medir
por separado no priorizados, conservados sin subdivisión y verdadero residual
sin soporte; comparar siempre a igual capacidad.

## Orden de trabajo propuesto para ahorrar tiempo

1. Acordar el contrato de ficha y completar la clasificación de variables del
   modelo exacto. Reutilizar la documentación de codificación ya existente.
2. Reutilizar artefactos y diagnósticos CQ, con hashes y versiones explícitos.
   FQ guarda resúmenes que no permiten reconstruir por sí solos todos los
   diagnósticos nuevos; no prometer que basta releer el JSON.
3. Si se implementa la validación pendiente, hacer una carga común en RAM para
   CQ y FQ; reutilizar selecciones QVoice congeladas y los ajustes disponibles.
   Calcular en la misma pasada capacidades 10/20/30, campos de ficha,
   disponibilidad QVoice, calibración, estabilidad y segmentos solicitados.
   Persistir sólo agregados; nada de cachés con personas o predicciones.
4. Reservar ajustes auxiliares para calibración sólo donde sean necesarios,
   con límites de cómputo y progreso por etapa. La ausencia de un periodo nuevo
   impide llamar independiente a otra lectura del mismo histórico.
5. Incorporar la partición selectiva corregida como escenario de reporte,
   conservando un contraste con grupos actuales. Después preparar la narrativa
   para RH con alcance, incertidumbre y una acción verificable por grupo.

## Fuentes consultadas

- [Decisión y alcance vigentes](../context/model-selection-current.md).
- [Marco existente de acciones](../research/attrition-literature/actionability-framework.md).
- [Variables y faltantes del CQ exacto](../../planes/modelo_c/variables_del_modelo_cq.md).
- [Método CQ y significado de la capacidad](../../planes/modelo_c/metodologia_y_construccion_cq.md).
- [Política anual QVoice](../../config/qvoice_annual_lag_policy_20261008.json).
- [Enlace de respuestas y estados](../../tools/qvoice_horizon_calibration.py), función `attach_selected`.
- [Codificación de la corrección](../../tools/qvoice_calibrated_model.py), `CategoryEncoder`.
- [Evaluación CQ de 2025](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/folds/aug_dec_2025/evaluation.json) y [2026](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/folds/jan_feb_2026/evaluation.json).
- [Calibración CQ de 2025](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/folds/aug_dec_2025/calibration.json) y [2026](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/folds/jan_feb_2026/calibration.json).
- [SQL CQ guardado](../../queries/profiles/engineering_model_c_qvoice_person_month_20261008.sql); ejecución 8-oct-2026, misma población Engineering y cortes arriba declarados.
- [Resultados FQ](../../output/analysis/engineering/20261013/model-f-qvoice-comparison-fast-v1/results.json) y [manifest](../../output/analysis/engineering/20261013/model-f-qvoice-comparison-fast-v1/manifest.json); cierre 13-oct-2026 UTC, 12-oct en hora local.
- [SQL FQ guardado](../../queries/profiles/engineering_f_qvoice_person_month_20261013.sql); población y periodos de FQ declarados arriba.
- [Auditoría ligera de FQ](../../tools/validate_f_qvoice_candidate.py).
- [Resultados BU L3 v7](../../output/analysis/engineering/20261012/model-bu-l3-v7/results.json), [configuración](../../config/engineering_bu_l3_experiment_20261012_v7.json) y [implementación selectiva](../../tools/engineering_bu_l3_experiment.py), función `evaluate_two_stage_groups`.

Esta revisión conserva los artefactos históricos. No asigna scores nuevos a
variables ni declara ejecutados los diagnósticos pendientes.
