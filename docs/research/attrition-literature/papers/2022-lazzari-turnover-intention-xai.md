# Predicting and Explaining Employee Turnover Intention

## Ficha

- Autores: Matilde Lazzari, José M. Álvarez y Salvatore Ruggieri
- Año: 2022
- Revista: *International Journal of Data Science and Analytics*, 14, 279–292
- DOI: `10.1007/s41060-022-00329-w`
- URL oficial: https://doi.org/10.1007/s41060-022-00329-w
- Fuente consultada: SpringerLink, PDF abierto y OpenAlex work `W4281396470`
- Fecha de consulta: 2026-09-24
- Estado de acceso: Open Access, licencia CC BY 4.0; texto completo consultado
- Etiquetas: `challenger`, `people-analytics`, `explicabilidad`, `causalidad`, `futuro`

## Abstract y resumen

### Abstract original

El abstract visible presenta una encuesta europea sobre intención de turnover,
comparando regresión logística, LightGBM y otros clasificadores, con ranking de
variables y un análisis causal basado en un grafo estructural explícito.

### Resumen en español

El paper separa tres actividades que a menudo se confunden: desempeño
predictivo, importancia de variables y efecto causal. Compara modelos mediante
PR-AUC, encuentra a logística y LightGBM como los mejores en su encuesta y
agrega estabilidad de importancias entre folds. Después formula un grafo causal
para estudiar intervenciones. Es útil como diseño de challenger y como
advertencia metodológica; no prueba attrition observado ni una relación causal
transportable a Critical Tech porque el target es intención autodeclarada y la
validación es cross-validation aleatoria.

## Pregunta y datos

- Pregunta: ¿qué modelos predicen mejor intención de turnover y qué factores pueden interpretarse bajo un grafo causal declarado?
- Población: encuesta Global Employee Engagement Index de 30 países europeos
- Tamaño: 9,296 respuestas, con una fila por participante; la tasa positiva media es 22.5%
- Grain: persona-encuesta transversal
- Target y horizonte: intención reportada de dejar la organización; no salida voluntaria observada ni horizonte prospectivo
- Censura o competing risks: no aplica

## Método y validación

- Método: ridge logistic regression, k-nearest neighbors, decision tree, random forest, XGBoost, LightGBM y TabNet; ranking de importancias agregado entre folds y análisis con structural causal model/PDP
- Variables: 23 themes de engagement y 112 items, además de país, industria, función, antigüedad, educación, género y estado de trabajo; eliminaron themes que contenían una pregunta cercana al target
- Split temporal: no. Usan cross-validation estratificada 10-fold repetida 10 veces y búsqueda de hiperparámetros dentro del entrenamiento
- Métricas: PR-AUC, intervalos de confianza y pruebas de diferencia entre clasificadores; es correcto para su desbalance, pero no equivale a un holdout temporal
- Resultados: en el dataset de themes, LightGBM obtuvo PR-AUC 0.588 y logística 0.583; en el dataset de items, 0.641 y 0.635 respectivamente. La diferencia se vuelve pequeña o cambia tras ponderar por país. Las conclusiones causales dependen del grafo causal y de supuestos de representatividad.

## Limitaciones

- Leakage: eliminan preguntas cercanas al target, pero no hay una fecha de conocimiento, evento futuro observado ni prueba out-of-time
- Sesgos: muestra de encuesta y reponderación sólo por país; los autores reconocen que no pueden ponderar por todos los atributos contextuales
- Generalización: intención de turnover, países, instrumentos y población no son equivalentes a salida voluntaria en Critical Tech
- Fairness/privacidad: incluye género y otros atributos contextuales; en Attrition sólo pueden usarse para una auditoría de fairness autorizada, nunca como targeting

## Aplicabilidad a Attrition

- Relación con Critical Tech: apoya mantener logística como benchmark y usar LightGBM como challenger posterior, no como champion por defecto
- Variables disponibles relacionadas: intent to stay, career goals, engagement, tenure, región y contexto laboral pueden evaluarse por bloques, con fecha de wave y sin preguntas que reproduzcan el outcome
- Qué adoptar: PR-AUC para un evento desbalanceado, comparación explícita de un modelo interpretable frente a un challenger, y estabilidad de importancias entre ventanas temporales
- Qué probar como challenger: LightGBM después de reejecutar el baseline de fase 1 y sólo contra el mismo holdout temporal de attrition voluntario observado
- Qué posponer: usar su PR-AUC, importancias, themes o supuestos causales como evidencia local; cualquier intervención exige un diseño causal propio

## Acción y decisión

- Señal asociada: engagement, motivación, carrera y antigüedad son familias de hipótesis; no son pesos ni drivers confirmados para Qualcomm
- Palanca potencial: diagnóstico agregado de carrera, claridad de rol, engagement y movilidad, con owner y medición posterior
- Acción candidata: comparar bloques QVoice gobernados y de carrera contra el baseline temporal; definir un DAG y un plan de evaluación separado antes de afirmar causalidad
- Métrica de seguimiento: PR-AUC, lift, Brier, calibración, estabilidad temporal y fairness autorizada; para acciones, retención observada bajo un diseño de intervención
- Decisión: `probar como challenger` sólo para LightGBM bajo nuestra validación temporal; `referencia metodológica` para PR-AUC, estabilidad de importancias y separación de predicción/causalidad

## Trazabilidad

- Evidencia consultada: SpringerLink, PDF publicado; OpenAlex work `W4281396470`; DOI y metadatos editoriales
- Sección/página si el texto completo fue revisado: Abstract y Introduction (pp. 279–281); datos y validación (pp. 282–285); factores explicativos (p. 286); análisis causal y limitaciones (pp. 287–291)
- Limitaciones de acceso: el texto completo abierto fue consultado; no se conservó una copia local en el proyecto
