# Síntesis metodológica

## Conclusión provisional

La literatura respalda formular Attrition como un problema longitudinal. La
supervivencia discreta permite usar snapshots mensuales, censura y variables
que cambian con el tiempo. `cloglog` es una especificación natural para
aproximar el hazard mensual.

## Qué entra al MVP

- modelo pooled de hazard discreto;
- baseline temporal y comparación por Critical Tech segment;
- riesgo acumulado a seis meses;
- validación out-of-time;
- calibración, lift, Brier/PR-AUC y estabilidad;
- cohortes agregadas y explicación asociativa.

## Qué entra como challenger

- logística directa a seis meses;
- Cox con covariables variables en el tiempo;
- Random Survival Forest;
- gradient boosting calibrado.

## Qué queda para fases posteriores

- competing risks si HR aprueba la separación de causas;
- uplift y causalidad para comparar acciones;
- DeepHit o deep survival con justificación de volumen y gobernanza;
- texto, sólo con fuente aprobada, minimización y revisión de privacidad.

## Criterio de acción

Una asociación sólo se convierte en driver accionable cuando es estable,
observable, suficientemente frecuente y existe una palanca con owner. La
literatura predictiva no prueba que la acción vaya a reducir attrition; esa
parte requiere otro diseño.

## Cómo se incorporó la segunda ronda

Los candidatos P13–P40 se organizaron en cinco bloques: turnover y
embeddedness, manager y prácticas de RH, engagement y burnout, carrera/talento
técnico, y fairness/gobierno. El dossier conserva el estado de acceso y las
preguntas pendientes de cada paper; todavía no se usan como evidencia de un
efecto específico en Qualcomm.

La selección actual de Critical Tech es consistente con esa estructura: el
screen agregado encontró que las combinaciones de job family/segment con nivel
y tenure son el primer mapa de cohortes, mientras que manager change aparece
como hipótesis localizada y todavía inestable. La literatura de carrera,
embeddedness, soporte y team turnover se usará para especificar drivers y
acciones candidatas; la literatura de fairness se usará como puerta de
gobierno.

## Evidencia cerrada el 2026-09-14

La revisión adicional cerró cinco fichas. P27 respalda separar recursos de
desarrollo, recursos sociales y engagement, pero sólo ofrece síntesis de
correlaciones y principalmente intención de salida. P33 y P40 aportan
hipótesis sobre carrera, manager, equipo y satisfacción en encuestas
transversales; no prueban salidas observadas. P34 y P36 no son papers de
predicción de attrition: establecen controles de fairness, definición de
categorías, transparencia, auditoría y revisión humana.

La consecuencia para el modelo propio es probar cada bloque contra el mismo
target de salida voluntaria observada, split temporal y métricas de Brier,
PR-AUC, lift, calibración y estabilidad. Ningún coeficiente, correlación o
accuracy de esas poblaciones se transporta como desempeño de Qualcomm.

La tanda adicional de abstracts refuerza tres hipótesis. P19 justifica probar
señales de equipo rezagadas, siempre agregadas y sin usar el outcome futuro del
propio equipo. P20 recomienda separar perceived supervisor support de perceived
organizational support. P13, P28 y P29 apoyan un bloque de carrera, pero también
advierten que los efectos dependen del contexto y que el desarrollo puede
incrementar movilidad si no existe una trayectoria interna clara. Como el texto
completo no estuvo disponible para estos cinco papers, sus detalles de muestra,
temporalidad y tamaños de efecto no se usan para cerrar decisiones empíricas.

## Evidencia cerrada el 2026-09-24

P41 y P42 separan con claridad tres niveles que el proyecto debe mantener
distintos: desempeño predictivo, explicación de un modelo y causalidad de una
acción. P41 demuestra una forma de documentar y diagnosticar un clasificador
con LIME, pero usa el dataset IBM/Kaggle simulado, un split no temporal y
explicaciones individuales. Por ello sólo aporta un gate de explicabilidad
global/agregada y revisión humana; no habilita scores, explicaciones ni listas
por empleado.

P42 compara logística y LightGBM con PR-AUC y estabilidad de importancias en
una encuesta europea. Refuerza que la logística debe competir contra un
challenger no lineal y que PR-AUC es útil ante desbalance. Sin embargo, su
target es intención autodeclarada y su validación es cross-validation aleatoria,
por lo que sus resultados no son un benchmark de attrition voluntario observado
ni justifican cambiar nuestro split temporal.

El análisis causal de P42 depende de un DAG explícito, sus supuestos de
representatividad y el contexto de la encuesta. En Attrition, una importance,
un PDP o una asociación del deck no se llamará causal. Cualquier afirmación de
intervención requerirá un DAG propio, variables y fecha de conocimiento
documentadas, y un diseño de evaluación posterior al modelo.

## Evidencia adicional cerrada el 2026-09-24

P18 añade un recordatorio útil para Critical Tech: un marco de retención como
job embeddedness puede complementar variables tradicionales, pero su asociación
no debe suponerse homogénea entre geografías o mercados laborales. La evidencia
accesible es sólo el abstract y los metadatos; por eso se usan sus constructos
para ordenar hipótesis y no para derivar un score compuesto, un tamaño de
efecto o una interacción obligatoria.

P37 no trata attrition, pero sí fija una disciplina de gobierno: una métrica de
fairness aislada no sustituye definir el target, el uso del score, los daños y
trade-offs relevantes. En el modelo propio, los atributos protegidos quedan
fuera de las features y sólo pueden participar en auditorías autorizadas y
agregadas. La calibración y el desempeño por grupo se revisarán cuando exista
soporte suficiente; no se automatizarán umbrales ni mitigaciones por una
definición abstracta de paridad.

P43 se registró el 2026-09-24 para explorar el significado de voice/silence
alrededor de QVoice. La lectura completa del 2026-09-30 sustituyó ese estado
provisional: aporta distinciones entre conducta, canal y motivos, y mantiene
el efecto del silencio sobre turnover como pregunta abierta. No demuestra que
participación, silencio o una respuesta de encuesta predigan attrition
observado en Critical Tech; véase la [ficha revisada](papers/2023-morrison-employee-voice-silence-decade.md).

P21 profundiza la separación de bloques de encuesta: prácticas de RH percibidas
(participación, fairness de recompensas y oportunidades de crecimiento), apoyo
organizacional, compromiso y satisfacción no son sinónimos. Sus dos muestras
vinculan una encuesta con turnover aproximadamente un año posterior, pero no
constituyen una validación out-of-time de nuestro modelo ni prueban que cambiar
una práctica cause retención. El modelo local probará cada proxy fechado contra
el mismo baseline, evitando sumar temas de QVoice y manager en un único score.

P22 aporta el nivel de análisis complementario: downsizing se estudia frente a
tasas organizacionales de turnover, con compromiso y prácticas de RH agregadas.
Por tanto, cualquier fuente interna sobre una reorganización sólo puede entrar
como contexto histórico agregado y rezagado. Antes de ejecutarla hay que fijar
la fecha efectiva, el grain, la población expuesta y una regla que excluya
headcount o resultados futuros del periodo de predicción.

P23 completa el punto de grain para QVoice: una relación entre
satisfacción-engagement y turnover a nivel de unidad de negocio no permite
concluir lo mismo para una persona. Si se evalúa una señal de cohortes, se
definirá la unidad, la ventana y una regla que la deje disponible antes del
horizonte; sus resultados se reportarán de forma agregada y no se reutilizarán
como score individual.

P24, P25 y P26 convergen en otra restricción: engagement no es un constructo
único. P24 distingue engagement con el trabajo y con la organización y sólo
mide intención de renunciar. P25 identifica seis conceptualizaciones y señala
que la evidencia es mayormente transversal/autoinformada. P26 organiza
demandas, recursos, burnout y engagement con JD-R, sin tratar attrition. En
consecuencia, cada tema QVoice se mapeará primero a un constructo explícito,
fecha de wave y posible palanca; después se probará como bloque separado contra
el target de salida voluntaria observado y el holdout temporal propio.

## Evidencia adicional cerrada el 2026-09-24: P30–P32 y P35

P30 refuerza el bloque de carrera, pero también obliga a separar tres cosas que
no deben mezclarse en el modelo local: percepción de desarrollo, satisfacción y
salida observada. El abstract reporta 687 respuestas de una organización de
salud durante una fusión, con una relación positiva entre desarrollo percibido e
intent-to-stay y mediación por satisfacción. La población, el target de
intención y la falta de detalles temporales impiden importar coeficientes,
causalidad o una interacción publicada; se probarán los proxies internos como
bloques fechados y con target de salida voluntaria observado.

P31 conserva valor histórico por su foco en profesionales MIS, pero no se cerró
cuantitativamente. La comprobación del 2026-09-30 prioriza ACM/Crossref para
identidad y método nominal del título; descarta el supuesto abstract de
OpenAlex por contener controles de interfaz y documenta revista/volumen
contradictorios en Drexel. Sin abstract científico ni texto completo accesible,
no se le atribuyen variables, muestra, resultados o pesos para las technical
job families. Permanece candidato hasta encontrar una fuente autorizada y
verificable.

P32 respalda la arquitectura de challenger: usar survival analysis para
representar censura y registros históricos y un ensemble para capturar
no-linealidad. El capítulo trabaja con una plataforma profesional china y
múltiples registros de turnover, pero el abstract no permite auditar features,
ventanas, leakage, métricas o split temporal. La prueba local debe usar el mismo
frame persona–mes, el alcance de fase 1 de Critical Tech, el target de salida
voluntaria y el holdout temporal del baseline `cloglog`; el resultado publicado
no es benchmark de Qualcomm.

P35 convierte fairness procedimental en una condición de gobierno, no en una
feature. Su estudio de laboratorio muestra que claridad de estándares,
explicación de resultados y control/voz tienen efectos distintos, y que permitir
revisar o ajustar una decisión puede mejorar su aceptación. La transferencia a
Attrition es diseñar contestabilidad, revisión humana, explicación agregada y
trazabilidad; no es evidencia de que una variable prediga attrition ni autoriza
mostrar scores o explicaciones por empleado.

## Revisión individual 2026-09-29 — P14

Permite distinguir intención y salida observada; el uso de la segunda encuesta y la selección de casos requieren una auditoría temporal que el abstract no permite completar.

Probar el bloque de intención con fechas explícitas contra el mismo baseline temporal; no confundir poder predictivo con causa o palanca de retención. Texto completo no accesible, sin número de eventos, coeficientes, instrumentos ni validación externa verificables. Véase la [ficha](papers/2004-van-breukelen-planned-behavior-voluntary-turnover.md).

## Revisión individual 2026-09-30 — P15

El texto completo muestra un índice formativo y apoyo incremental desigual entre muestras; no hay holdout temporal ni calibración predictiva.

Separar vínculos, ajuste del rol y carrera como hipótesis; validar cada bloque sin reproducir el índice comunitario ni importar pesos. Manuscrito autoral; denominadores tras exclusiones por reconciliar, instrumentos distintos y resultados inferenciales dentro de muestra. Véase la [ficha](papers/2001-mitchell-holtom-lee-job-embeddedness.md).

## Revisión individual 2026-09-30 — P16

El contraste directo no demuestra diferencia entre componentes para turnover; las ausencias del año de salida no son una señal disponible al corte inicial.

Separar constructos y outcomes, fijar ventanas previas y comparar hipótesis directamente; no usar significación individual como prueba de superioridad. Una institución, muestras efectivas distintas, solapamiento temporal en ausencias y ausencia de validación externa o intervención causal. Véase la [ficha](papers/2004-lee-job-embeddedness-performance-turnover.md).

## Revisión individual 2026-09-30 — P17

La medida global es reflectiva; la interacción no confirma la dirección anticipada y existe una discrepancia de eventos en la copia consultada.

Distinguir percepción global, índice formativo, satisfacción e intención; probar una medida propia sólo con validación de contenido y evaluación temporal independiente. Copia no editorial de registro, pocos eventos, selección de caminos en la muestra y conteo de salidas por reconciliar. Véase la [ficha](papers/2007-crossley-global-job-embeddedness.md).

## Revisión individual 2026-09-30 — P31

La proximidad ocupacional está confirmada por el título; el contenido empírico sigue sin verificar y dos registros secundarios presentan problemas de calidad.

Conservar como antecedente histórico candidato; no atribuirle predictores, efectos ni capacidad de anticipar salida observada. Faltan abstract primario o copia autorizada, muestra, instrumentos, resultados y diseño temporal. Véase la [ficha](papers/1992-igbaria-greenhaus-mis-turnover-intentions.md).

## Revisión individual 2026-09-30 — P38

El beneficio reportado corresponde a intención simulada; no demuestra reducción de renuncias mediante una intervención real.

Separar explicación predictiva, escenarios bajo supuestos y evaluación causal de acciones; conservar el marco como referencia conceptual. Métodos y resultados completos inaccesibles; procedencia de datos, target, validación temporal, identificación y simulación sin auditar. Véase la [ficha](papers/2026-dubey-shukla-causal-explainable-ai-retention.md).

## Revisión individual 2026-09-30 — P39

La permanencia puede coexistir con inseguridad; trabajo y comunidad moderan de forma distinta, con límites temporales y discrepancias de reporte documentados.

Separar percepción de inseguridad, vinculación, intención y salida; formular interacciones específicas y valorar bienestar junto con retención. Autorreporte, selección de casos completos, salidas tempranas y fecha de intención sin resolver; índice, OR y flujo por conciliar; sin validación predictiva externa. Véase la [ficha](papers/2024-peltokorpi-allen-embeddedness-job-insecurity.md).

## Revisión individual 2026-09-30 — P43

La revisión distingue conducta, canal y motivos; mantiene abierta la relación silencio-turnover y no valida participación como medida de voz o silencio.

Separar participación, contenido, escucha y conducta de voz/silencio; usar cada medida con su significado y comprobar por separado la relación con salida posterior. Síntesis selectiva con predominio de encuestas transversales; sin efecto combinado, modelo predictivo ni prueba de QVoice. Fuentes primarias sobre salida requieren revisión propia. Véase la [ficha](papers/2023-morrison-employee-voice-silence-decade.md).
