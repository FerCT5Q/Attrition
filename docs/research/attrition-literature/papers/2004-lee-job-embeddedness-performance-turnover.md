# P16 — The Effects of Job Embeddedness on Organizational Citizenship, Job Performance, Volitional Absences, and Voluntary Turnover

## Ficha y evidencia alcanzada

- **Autores:** Thomas W. Lee, Terence R. Mitchell, Chris J. Sablynski, James P. Burton y Brooks C. Holtom.
- **Publicación:** 2004; *Academy of Management Journal*, 47(5), 711–722.
- **DOI:** [10.2307/20159613](https://doi.org/10.2307/20159613); la editorial y el repositorio usan también `10.5465/20159613` para este mismo artículo.
- **Consulta y cierre:** 2026-09-30, America/Mexico_City.
- **Clasificación:** `presentation`; sin datos internos de empleados.
- **Fuente completa:** [University of the Pacific, ficha institucional](https://scholarlycommons.pacific.edu/esob-facarticles/210/), con [PDF de 14 páginas](https://scholarlycommons.pacific.edu/cgi/viewcontent.cgi?article=1209&context=esob-facarticles), portada de repositorio y artículo editorial incluidos.
- **Estado:** `Revisado`, texto completo, tablas y apéndice. Lectura en memoria sin guardar ni redistribuir el PDF.
- **Corrección:** el inventario decía Mitchell et al.; el primer autor es Lee. Autoría cotejada en Crossref, OpenAlex, portada y repositorio.

## Diseño y hallazgos comprobados

Se separan embeddedness laboral y comunitario y se estudian cuatro resultados.
La encuesta se aplicó en diciembre de 1998 en un centro de operaciones
financieras; supervisores calificaron desempeño y ciudadanía organizacional
en enero de 1999. Salidas y ausencias proceden de registros de 1999.

Hubo 1,650 invitaciones, 839 respuestas y 829 casos inicialmente utilizables;
136 salidas se clasificaron como voluntarias. Los tamaños de análisis varían:
805 para la regresión principal de salida, 739 para ausencias y 620 para
desempeño y ciudadanía. Se usan logística y mínimos cuadrados, con controles
por satisfacción y compromiso.

En los modelos ajustados, el componente comunitario se asocia con salida y
ausencias; el laboral, con desempeño y ciudadanía. Pero el contraste posterior
entre coeficientes separados y un índice combinado **no resulta significativo
para turnover**. Los autores reconocen límites temporales y necesidad de
diseños causales. Localizadores: pp. 715–720 del artículo, PDF pp. 6–11.

## Lectura crítica

### Significación distinta no equivale a efectos diferentes

El abstract puede invitar a concluir que el componente comunitario es mejor
predictor de salida porque su coeficiente es significativo y el laboral no.
La conclusión más fuerte necesita contrastar directamente la diferencia.

El análisis post hoc del artículo hace una comparación útil: el modelo con
coeficientes separados tiene deviance `706.78`; el modelo que impone el índice
combinado tiene `707.31` (p. 719). Recalculé la diferencia: `G=0.53`; para un
grado de libertad, la cola chi-cuadrado es aproximadamente `p=0.467`. Coincide
con la falta de significación que reportan los autores. El detalle está en
`output/research/attrition-literature/20260929-pending-review/P16/statistical-check.json`.

Por tanto, esta ficha conserva el patrón de coeficientes ajustados, pero no lo
convierte en prueba de superioridad del componente comunitario para turnover.
Tampoco interpreta ausencia de significación como ausencia de relación o como
inutilidad del bloque laboral. La comparación directa ofrece un criterio más
preciso que seleccionar dimensiones por estrellas en una tabla.

### La cronología no permite copiar las ausencias como predictor de un corte inicial

Las ausencias se acumulan durante el año en que se observan las salidas y se
promedian por tiempo trabajado cuando la persona termina antes (p. 716).
Esa variable sirve al análisis retrospectivo publicado, pero no estaría
disponible en el corte inicial de un sistema de predicción.

Además, el tiempo hasta la salida afecta la ventana sobre la que se calcula
ese promedio. Normalizar por meses observados no demuestra que se haya
eliminado toda dependencia del resultado. En una predicción local, cualquier
historia permitida tendría que terminar antes del snapshot y mantenerse
separada del horizonte futuro. El artículo no autoriza incorporar ausencias
al proyecto, cuyo gobierno restringe ese dominio.

La calificación de enero también es posterior a una predicción formulada en
diciembre. Una réplica debería desplazar el inicio del seguimiento o usar
únicamente información ya conocida, y documentar qué ocurre con salidas
anteriores a la disponibilidad de esa medición.

### Una muestra inicial no es el denominador de todas las regresiones

El flujo desde encuesta hasta evaluación del supervisor y registros
administrativos tiene pérdidas diferentes. Las tablas muestran distintos
tamaños efectivos, incluso entre especificaciones de salida. Por ello, las
comparaciones de modelos requieren confirmar que usen los mismos casos; una
diferencia de ajuste podría mezclar cambio de variables y cambio de población.

La comprobación telefónica de la voluntariedad fue parcial: confirma el evento
en las personas contactadas, no en todas las salidas clasificadas por la
organización. La ficha no convierte esa validación parcial en una auditoría
completa del target. En nuestro flujo esto se traduciría en reglas explícitas
para salidas ambiguas, población elegible y faltantes, sin reconstruir motivos
individuales.

### Solapamiento de medidas e interpretación de controles

Satisfacción, compromiso y el componente laboral comparten contenido y
correlacionan fuertemente en esta muestra. Controlar las primeras variables
cambia la pregunta: se estima lo que añade el componente laboral manteniendo
las otras medidas constantes. No se estima el efecto total de mejorar la
experiencia laboral.

Para el proyecto conviene comparar modelos anidados que respondan preguntas
predefinidas y revisar redundancia de constructos. Que el artículo reporte
factores y confiabilidad no demuestra equivalencia con temas QVoice ni con
campos administrativos. El apéndice, además, adapta preguntas al contexto de
la organización; no es un instrumento universal e invariable.

### Las interacciones son hipótesis que necesitan estabilidad

Las interacciones se interpretan con divisiones por la mediana y modelos por
subgrupo. Ese recurso descriptivo no define umbrales operativos para otras
poblaciones. También puede dar una impresión de discontinuidad donde existe
una relación continua.

Hay otra distinción entre prueba individual y prueba conjunta: el bloque de
interacciones de desempeño tiene una mejora publicada de `4.82` con dos
grados de libertad (tabla 3). Su cola chi-cuadrado, recalculada, es
aproximadamente `0.090`. Que un término individual tenga evidencia más fuerte
no convierte automáticamente todo el bloque en una mejora robusta.

Una prueba local conservaría variables continuas o bandas justificadas y
evaluaría interacciones preespecificadas en meses posteriores. La señal no
pasaría al modelo por una interacción aislada ni por diferencias entre grupos
formados después de observar los resultados.

### Longitudinal no significa causal ni validado fuera de muestra

Hay separación entre fuentes de datos y parte de la cronología, lo que mejora
el diseño respecto de una sola encuesta. No hay intervención aleatoria,
validación temporal externa ni demostración de que una acción sobre
embeddedness reduzca salidas. El horizonte anual y el mercado laboral de una
institución financiera tampoco equivalen a Critical Tech en la actualidad.

La diferencia entre permanecer, desempeñarse bien y participar en actividades
adicionales debe mantenerse: predecir uno de estos resultados no acredita los
otros. No se propone usar desempeño o ciudadanía como target sustituto de
salida voluntaria ni construir una etiqueta general de «withdrawal».

## Decisión para el proyecto

Usar P16 para **separar constructos, resultados y ventanas**, y para exigir
comparaciones directas entre hipótesis. Mantener el contexto laboral como
posible bloque de investigación, sin descartar sus componentes por resultados
condicionados de una sola muestra.

No reproducir el componente privado/comunitario, no importar interacciones ni
umbrales, y no usar ausencias futuras. La evidencia bibliográfica no cambia
scores, disponibilidad de datos internos ni la decisión de promoción del
modelo. Las acciones de carrera o conexión laboral siguen siendo propuestas
que necesitarían evaluación propia.

## Trazabilidad

- [Crossref](https://api.crossref.org/works/10.2307%2F20159613): identidad y paginación; [OpenAlex W2076261495](https://api.openalex.org/works/https://doi.org/10.2307/20159613): identidad, abstract y acceso indexado.
- Repositorio institucional y PDF enlazados al inicio. Texto: pp. 711–722; tabla 2, p. 717; tabla 3, p. 718; comparación post hoc, p. 719; apéndice, pp. 721–722.
- SHA-256 de la copia: `83062b6513829b89bea4bee15929c507627a40eaf68075a956b7f7b6167a591c`.
- Registros de lectura y procedencia: `output/research/attrition-literature/20260929-pending-review/P16/sources/`.
- Los recálculos usan estadísticas publicadas redondeadas; no acceden a datos de participantes ni estiman efectos nuevos.
- La matriz factorial completa y una regresión adicional se ofrecen sólo bajo solicitud en el artículo; no se presentan como revisadas y no se contactó a los autores.
