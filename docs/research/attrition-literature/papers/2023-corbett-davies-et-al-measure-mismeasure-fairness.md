# The Measure and Mismeasure of Fairness

## Ficha

- Autores: Sam Corbett-Davies, Johann D. Gaebler, Hamed Nilforoshan, Ravi Shroff y Sharad Goel
- Año: 2018 (preprint); versión publicada indicada por arXiv en *Journal of Machine Learning Research*, 24, 2023
- Revista/conferencia: *Journal of Machine Learning Research*; arXiv `1808.00023v3`
- DOI: `10.48550/arXiv.1808.00023`
- URL oficial: https://arxiv.org/abs/1808.00023
- Fuente consultada: API y HTML abierto de arXiv, versión v3
- Fecha de consulta: 2026-09-24
- Estado de acceso: Open Access; texto completo consultado en HTML de arXiv
- Etiquetas: `gobierno`, `fairness`, `calibración`, `target`, `auditoría`

## Abstract y resumen

### Abstract original

El abstract visible organiza las definiciones formales de fairness en dos
familias: restricciones sobre disparidades producidas por decisiones y
restricciones sobre el efecto de características protegidas en las decisiones.
Sostiene que aplicar criterios formales sin contexto puede producir políticas
dominadas y que el diseño equitativo debe considerar consecuencias específicas
del dominio.

### Resumen en español

No es un paper de attrition ni de HR. Es una referencia de gobierno que muestra
por qué una sola métrica de fairness no puede certificarse como suficiente sin
definir qué se predice, quién recibe una acción, qué daños se quieren evitar y
qué intercambios se aceptan. Para Attrition, la consecuencia práctica es
separar la auditoría de un score de la decisión de intervenir y documentar la
calibración y demás métricas por grupo autorizado, sin utilizar atributos
protegidos para seleccionar empleados.

## Pregunta y datos

- Pregunta: cómo se relacionan las definiciones matemáticas comunes de fairness con decisiones equitativas y sus consecuencias.
- Población: no hay una población de empleados ni un dataset de turnover; usa análisis formal e ilustraciones de otros dominios.
- Tamaño: no aplica como muestra de personas.
- Grain: regla de decisión, distribución de riesgo y grupo bajo una definición formal.
- Target y horizonte: fairness de decisiones/risk scores; no attrition ni intervención de retención.
- Censura o competing risks: no aplica.

## Método y validación

- Método: taxonomía de definiciones, análisis formal y ejemplos empíricos/ilustrativos para examinar sus consecuencias.
- Variables: riesgo, predicción, decisiones, atributos protegidos, resultados y bienestar/contexto de política; no variables de People Analytics.
- Split temporal: no aplica.
- Métricas: analiza criterios formales y dedica una sección a calibración por grupo; no reporta métricas de un modelo de attrition.
- Resultados: las definiciones formalizadas pueden entrar en conflicto con objetivos de bienestar y con otras nociones de equidad. El texto recomienda declarar dimensiones y trade-offs en lugar de optimizar automáticamente una métrica aislada.

## Limitaciones

- Leakage: no aplica directamente; para Attrition sigue siendo obligatorio validar fecha de conocimiento y label de salida por separado.
- Sesgos: los ejemplos y la discusión normativa se concentran en otros dominios, en gran medida del contexto estadounidense; no proporcionan una regla legal o estadística lista para HR global.
- Generalización: no demuestra que una métrica, umbral o mitigación funcione para attrition de Critical Tech.
- Fairness/privacidad: los atributos protegidos son necesarios, cuando están autorizados, para auditar el sistema; no habilitan su uso como features ni explicaciones o acciones individuales.

## Aplicabilidad a Attrition

- Relación con Critical Tech: convierte la fairness en un gate de diseño y auditoría del modelo, no en una única cifra ni en una feature de targeting.
- Variables disponibles relacionadas: atributos protegidos sólo para auditoría autorizada; target de salida voluntaria, score agregado, calibración, errores y acciones propuestas deben documentarse como objetos distintos.
- Qué adoptar: definir antes de la auditoría el objetivo de decisión, población, métricas, cohortes mínimas, trade-offs y ruta de revisión humana; verificar calibración y desempeño por grupos cuando el tamaño permita reportarlo.
- Qué probar como challenger: no es un predictor. Puede guiar un protocolo de auditoría para champion y challengers, incluyendo métricas por grupo y revisión de diferencias con suficiente soporte agregado.
- Qué posponer: imponer paridad, umbrales o mitigaciones automáticas sin análisis de contexto, autorización, tamaño de cohorte, impacto de las acciones y revisión de stakeholders.

## Acción y decisión

- Señal asociada: divergencia entre el riesgo predicho y el observado, o entre errores de grupos, es una señal de auditoría; no identifica a una persona para intervenir.
- Palanca potencial: definición de target, reglas de reporte, revisión humana, gobernanza de datos y diseño de intervenciones de retención.
- Acción candidata: anexar al gate de promoción una ficha que declare métricas y trade-offs, con resultados agregados sólo para grupos autorizados y suficientemente grandes.
- Métrica de seguimiento: calibración y desempeño temporal por grupo, cobertura de auditoría, estabilidad y registro de decisiones; no una métrica universal de fairness.
- Decisión: `referencia conceptual` con `gobierno adoptado`; no altera el modelo predictivo ni habilita targeting, scoring individual o mitigación automática.

## Trazabilidad

- Evidencia consultada: arXiv API para autores, fechas, resumen y referencia JMLR; texto HTML v3 para secciones 2, 3, 4 y 5.
- Sección/página si el texto completo fue revisado: secciones 2 (definiciones), 3–4 (consecuencias y trade-offs) y 5.1–5.2 (proceso frente a resultados, calibración y selección del target).
- Limitaciones de acceso: se revisó la versión abierta de arXiv. No se conserva una copia local; las recomendaciones para Attrition son una traducción de gobierno, no resultados empíricos del paper en HR.
