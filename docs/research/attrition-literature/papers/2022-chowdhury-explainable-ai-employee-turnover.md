# Embedding Transparency in Artificial Intelligence Machine Learning Models: Managerial Implications on Predicting and Explaining Employee Turnover

## Ficha

- Autores: Soumyadeb Chowdhury, Sian Joel-Edgar, Prasanta Kumar Dey, Sudeshna Bhattacharya y Alexander A. Kharlamov
- Año: 2022 en línea; volumen publicado en 2023
- Revista: *The International Journal of Human Resource Management*, 34(14), 2732–2764
- DOI: `10.1080/09585192.2022.2066981`
- URL oficial: https://doi.org/10.1080/09585192.2022.2066981
- Fuente consultada: Repository@Nottingham y ficha OpenAlex `W4293154704`
- Fecha de consulta: 2026-09-24
- Estado de acceso: manuscrito de repositorio abierto con licencia CC BY; texto completo consultado
- Etiquetas: `aplicado-turnover`, `challenger`, `gobierno`, `explicabilidad`

## Abstract y resumen

### Abstract original

El abstract visible describe una demostración de Local Interpretable
Model-Agnostic Explanations (LIME) para explicar predicciones de turnover de
un modelo de machine learning y discutir la transparencia algorítmica en HR.

### Resumen en español

El artículo propone un flujo de preparación de datos, clasificación y
explicación con LIME. Su contribución útil para Attrition es de gobierno:
documentar variables de entrada, inspeccionar errores y explicaciones, y no
tratar un modelo complejo como una caja negra. No constituye evidencia de que
un algoritmo ni una variable prediga attrition en Qualcomm: el experimento usa
el dataset simulado IBM/Kaggle, un split aleatorio y resultados a nivel de
caso individual que no son un output permitido en nuestro proyecto.

## Pregunta y datos

- Pregunta: ¿cómo puede LIME hacer más comprensibles para managers las predicciones de un clasificador de employee turnover?
- Población: dataset simulado de IBM Watson distribuido en Kaggle, descrito por los autores como basado en información de vida real
- Tamaño: el paper no presenta esta demostración como una cohorte longitudinal de empleados reales
- Grain: registro sintético individual
- Target y horizonte: etiqueta de attrition del dataset simulado; no se establece un horizonte prospectivo equivalente al de Attrition
- Censura o competing risks: no aplica; no se modela historia de eventos ni causas de salida

## Método y validación

- Método: selección de 23 inputs, one-hot encoding, normalización, clasificador deep learning en H2O y explicaciones locales/globales con LIME
- Variables: los autores exigen que cada input sea disponible en HRIS, no discriminatorio y justificable; eliminan filas con missing y columnas consideradas inconsistentes
- Split temporal: no. Aplican 70% train, 15% validation y 15% test mediante una partición de muestras representativas por clustering; no es un holdout futuro
- Métricas: precision y recall; reportan 62% de precision y 79% de recall para la demostración
- Resultados: no encontraron diferencias estadísticamente significativas entre algoritmos y seleccionaron deep learning por ser más opaco y, por tanto, ilustrar LIME. Las explicaciones muestran que una variable con peso alto puede contribuir a falsos positivos.

## Limitaciones

- Leakage: el paper discute el riesgo, pero la población es simulada y el split no reproduce la frontera temporal requerida para nuestros snapshots
- Sesgos: el tratamiento de missing elimina filas; no existe evidencia de que el dataset ni los pesos de variables representen una organización real o Critical Tech
- Generalización: precisión, recall, importancia de overtime, promociones u otras variables no son métricas ni efectos transferibles a Qualcomm
- Fairness/privacidad: LIME se usa para explicaciones por persona. Ese uso no es compatible con nuestro output agregado por cohortes ni con la prohibición de compartir scores o explicaciones individuales.

## Aplicabilidad a Attrition

- Relación con Critical Tech: apoya que un challenger no lineal sólo se considere con registro de inputs, diagnóstico de errores, validación de calidad y explicación comprensible para el gobierno
- Variables disponibles relacionadas: todas las variables candidatas requieren su assessment, fecha de conocimiento y validación temporal antes de llegar a cualquier modelo explicable
- Qué adoptar: documentación de feature lineage, revisión de errores, explicación global/agregada de cohortes y revisión humana de la calidad del modelo
- Qué probar como challenger: un modelo no lineal sólo después del baseline temporal y sólo si mejora lift, Brier, PR-AUC, calibración, estabilidad y fairness; sus explicaciones se resumirán por cohortes reportables
- Qué posponer: LIME por empleado, listas de riesgo, seleccionar una variable por su peso en un dataset sintético, o usar precision/recall de este paper como benchmark

## Acción y decisión

- Señal asociada: explicabilidad y diagnóstico de errores, no una señal de retención específica
- Palanca potencial: gobernanza del modelo, data dictionary, revisión de drift y discusión agregada de drivers
- Acción candidata: añadir un gate de explicabilidad global y de revisión humana si un challenger no lineal supera al baseline temporal
- Métrica de seguimiento: lift, PR-AUC, Brier, calibración, estabilidad temporal, fairness autorizada y calidad de explicaciones agregadas
- Decisión: `referencia metodológica y de gobierno`; no promueve deep learning ni LIME individual para el MVP

## Trazabilidad

- Evidencia consultada: Repository@Nottingham, PDF `19367.pdf`; OpenAlex work `W4293154704`; DOI y metadatos editoriales
- Sección/página si el texto completo fue revisado: Abstract; Methodology (pp. 10–12 del manuscrito); Sense-making and Results (pp. 13–17); Conclusion (p. 21)
- Limitaciones de acceso: se consultó el texto abierto del repositorio; no se conservó una copia local en el proyecto
