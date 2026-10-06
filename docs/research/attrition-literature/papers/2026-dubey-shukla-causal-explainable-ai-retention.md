# P38 — Causal Explainable AI for Employee Retention: A Unified Framework Integrating HRMS Data, Sentiment Dynamics, and Counterfactual Reasoning

## Ficha y alcance de la revisión

- **Autoras:** Rashi Dubey e Indu Shukla.
- **Publicación:** *2026 IEEE 18th International Conference on Computational Intelligence and Communication Networks (CICN)*, 1600–1608.
- **Fechas:** conferencia del 12 al 14 de junio de 2026; Crossref registra publicación el 12 de junio; IEEE informa incorporación a Xplore el 10 de julio de 2026. Son fechas de eventos distintos.
- **DOI:** [10.1109/CICN70047.2026.11594084](https://doi.org/10.1109/CICN70047.2026.11594084).
- **Consulta:** 2026-09-30, America/Mexico_City.
- **Clasificación:** `presentation`; bibliografía pública, sin datos internos.
- **Evidencia:** abstract editorial y vista previa de la introducción leídos en IEEE Xplore; abstract corroborado en Semantic Scholar; identidad en Crossref/OpenAlex.
- **Acceso:** Xplore solicita iniciar sesión para continuar; el enlace indexado como PDF terminó en HTML vacío. No se consiguió copia abierta autorizada.
- **Estado:** `Revisado`, con alcance limitado al abstract y vista previa. **No se leyeron métodos, resultados, tablas ni apéndices completos.**

## Pregunta, propuesta y resultados declarados

El trabajo propone CausalRetain, un marco que combina información de HRMS,
señales de sentimiento en comunicaciones laborales, modelos causales
estructurales y escenarios contrafactuales. El abstract menciona DoWhy para
grafos e inferencia, SHAP/LIME para explicar modelos y un motor de escenarios
para decisiones de RH.

Declara una evaluación con **14.872 registros de empleados de seis sectores** y
AUC-ROC de **0.934**. No informa en el resumen cuántas personas únicas,
organizaciones, periodos o salidas existen, ni si los registros son reales,
sintéticos o una combinación. No debe sustituirse «registros» por «empleados
independientes».

El otro resultado es una **reducción simulada del 23,7 % en intención de
salida**, obtenida en simulaciones de decisiones de RH. No es una reducción
observada de renuncias tras una intervención empresarial. El resumen no permite
determinar el denominador, si es cambio relativo o absoluto, la incertidumbre,
el comparador o la relación entre la intención simulada y el target usado
para calcular AUC.

## Análisis crítico

### 1. Publicación confirmada; identificación causal aún no auditable

**Pregunta:** ¿qué permite llamar causales a los resultados? El uso de un modelo
estructural y de DoWhy describe herramientas, pero no demuestra que se hayan
controlado todos los factores que confunden una relación. Los grafos requieren
supuestos sustantivos sobre las causas y la secuencia de medición.

El abstract afirma encontrar mecanismos causales, pero no presenta el grafo,
la intervención estimada, los conjuntos de ajuste, el soporte de los datos ni
análisis de sensibilidad. Por tanto, **no podemos confirmar ni refutar su
identificación causal con el acceso disponible**. No se transforma el lenguaje
del abstract en evidencia de que una acción reduce renuncias.

**Qué falta:** tratamiento y outcome precisos, orden temporal, supuestos de
confusión, comparabilidad y solapamiento, justificación del grafo, estimador,
incertidumbre, alternativas plausibles y sensibilidad. Las pruebas automáticas
de robustez, si existieran, tampoco probarían por sí solas todos los supuestos.

### 2. Explicación del predictor, escenario y efecto de una acción

SHAP y LIME ayudan a entender cómo un modelo utiliza sus entradas. Esa
explicación no identifica automáticamente el cambio que produciría intervenir
sobre una condición laboral. Con predictores correlacionados, la atribución
también depende de cómo se define la comparación.

Un contrafactual puede indicar qué cambios harían variar la predicción.
Para interpretarlo como resultado de una acción real se necesita además una
intervención factible, relaciones causales válidas y un horizonte coherente.
Cambiar un indicador de sentimiento en una tabla no especifica por sí mismo
qué práctica empresarial lo modificaría ni qué otros efectos produciría.

**Aplicación:** separar en los reportes explicación de riesgo, simulación bajo
supuestos y efecto medido de una intervención. P38 sirve para formular esa
distinción; su abstract no proporciona una política de retención validada.

### 3. La simulación no mide retención conseguida

El 23,7 % corresponde a intención simulada. No se informa una asignación de
intervenciones seguida de observación de salidas. Tampoco sabemos si el mismo
modelo propone escenarios y evalúa su supuesto beneficio.

Si una simulación se valida exclusivamente contra los supuestos que la
generaron, puede resultar internamente consistente sin demostrar efecto en el
mundo real. **Es una pregunta pendiente del diseño, no una acusación de que el
paper lo haya hecho.**

**Aplicación:** no incorporar ese porcentaje a un caso de negocio, ahorro
esperado o meta de reducción de attrition. Una evaluación local de una acción
necesitaría un diseño prospectivo o cuasiexperimental defendible, seguimiento
de salida observada, comparador, costes e incertidumbre.

### 4. Qué demuestra y qué deja abierto el AUC reportado

AUC-ROC resume ordenamiento entre clases bajo una definición concreta del
outcome y de la muestra. No es porcentaje de aciertos, calibración ni beneficio
de una acción. La cifra 0.934 no informa rendimiento sobre nuestro horizonte
de seis meses o sobre Critical Tech.

El abstract no describe prevalencia, número de eventos, partición temporal,
agrupamiento por persona/empresa, ajuste de hiperparámetros, intervalos,
baselines o calibración. Seis sectores dentro del conjunto no equivalen a seis
validaciones externas. Si hubiera registros repetidos, habría que comprobar
que no se repartieron de forma que contaminaran la evaluación.

**Aplicación:** la comparación local mantendría población, corte y horizonte
comunes, con holdout temporal y control de observaciones repetidas. Brier,
calibración, PR-AUC, lift, incertidumbre y estabilidad complementarían AUC.
Son requisitos de una prueba local, no análisis atribuidos al artículo.

### 5. Señales dinámicas y fecha de conocimiento

El uso declarado de sentimiento «en tiempo real» no verifica que cada dato
preceda la predicción. Se necesitan fechas de los textos, procesamiento y
target, así como reglas para información que mencione una salida ya decidida.
El abstract no permite auditar fuga temporal ni descartar esa posibilidad.

**Aplicación:** cualquier hipótesis temporal debe usar sólo información
disponible antes del corte. No se afirma que P38 tenga leakage; se documenta
que no pudo comprobarse.

### 6. Transferencia del sentimiento y límites de medición

No quedan verificadas las fuentes de comunicación, idiomas, anotación,
validación del sentimiento ni relación entre esa medida y el constructo
laboral. Sentimiento textual, satisfacción, engagement, intención y salida
son medidas diferentes.

El proyecto restringe texto libre y datos individuales de empleados. Esta
revisión **no incorpora comunicaciones internas ni crea un análisis de texto**.
La propuesta del paper no justifica recogerlas ni sustituir una medición
autorizada y validada. Cualquier evaluación de datos internos sería un trabajo
separado, con las reglas correspondientes.

## Decisión para Attrition

| Elemento | Uso razonable con la evidencia actual |
|---|---|
| Separar predicción, explicación y decisión | Referencia conceptual para diseñar preguntas y reportes. |
| Modelos causales estructurales | Línea de investigación condicionada a una intervención y supuestos explícitos. |
| SHAP/LIME | Posibles explicaciones de un predictor; no evidencia automática de causalidad. |
| Motor contrafactual | Escenarios exploratorios bajo supuestos; no recomendaciones individuales validadas. |
| AUC y reducción simulada | Cifras declaradas en abstract, sin importar desempeño, ahorro ni metas. |
| Implementación de CausalRetain | Posponer hasta leer métodos, procedencia de datos, validación y límites. |

La decisión es **referencia conceptual de baja prioridad para implementación**.
Se confirma la publicación y se analiza su abstract; no se eleva a evidencia
de eficacia de intervenciones. No modifica el modelo, los scores ni la
selección de variables internas.

## Pendiente para la revisión integral

Obtener una copia autorizada y revisar las secciones III–V, el resto de la
metodología y las conclusiones: procedencia y unidad de los datos, target,
ventanas y particiones, grafo y supuestos, estimación de efectos,
restricciones de los contrafactuales, diseño de la simulación, comparadores,
incertidumbre, reproducibilidad y evaluación fuera de muestra. No se inventan
estos detalles a partir del título de las secciones.

## Trazabilidad

- [IEEE Xplore](https://ieeexplore.ieee.org/document/11594084): abstract y primer fragmento de introducción; aviso de inicio de sesión para continuar. Fechas de conferencia e incorporación al índice verificadas.
- [Crossref](https://api.crossref.org/works/10.1109%2FCICN70047.2026.11594084): autoría, tipo `proceedings-article`, título, páginas y fecha. No contiene abstract; su enlace para similarity-checking no se usó como vía de acceso.
- [OpenAlex W7167894609](https://api.openalex.org/works/https://doi.org/10.1109/CICN70047.2026.11594084): acceso cerrado, sin copia en repositorio ni abstract.
- [Semantic Scholar](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1109/CICN70047.2026.11594084?fields=title,authors,abstract,year,venue,openAccessPdf,url): abstract coincidente con IEEE, sin PDF abierto.
- Búsquedas por título y por CausalRetain/Dubey: no localizaron una versión institucional legible. La ficha exacta de ResearchGate no expuso contenido.
- Evidencia y observaciones: `output/research/attrition-literature/20260929-pending-review/P38/sources/`. Las cifras se conservan como afirmaciones publicadas, no como recálculos ni validación independiente.
