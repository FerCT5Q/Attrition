# Any comment on QVoice

## Conocimiento acumulado

Los cuatro workbooks raw de QVoice contienen prompts abiertos originales. La
ausencia de un campo estructurado en Redshift no debe interpretarse como
ausencia de comentarios. La evidencia actual describe disponibilidad y
presencia de respuesta agregada; no crea aun una feature de attrition.

## Definicion y uso

- **Concepto:** existencia de al menos un valor no vacio en los prompts abiertos seleccionados de una wave.
- **Uso actual:** diagnostico de fuente y denominador de comentarios para analisis interno.
- **Tipo semantico:** `survey` / respuesta abierta agregada.
- **Grain:** participante-wave.
- **Prompts:** doing well, can improve y processes to improve cuando existe.
- **Privacidad:** se publican conteos agregados; no se guardan IDs ni texto.

## Flujo historico y validaciones

1. **Pregunta:** ¿hay una fuente raw identificable en todas las waves objetivo? **Motivo:** la tabla estructurada no contiene un indicador de comentario. **Metodo:** inventario de `Raw data`, campos originales y key usable. **Regla:** Mar-2023, Jan-2024, Jan-2025 y Jan-2026 con los prompts requeridos. **Resultado:** cumple.
2. **Pregunta:** ¿la presencia de comentario tiene un grain unico? **Motivo:** una fila duplicada altera cualquier conteo de participacion. **Metodo:** conteo de filas por key y de comentarios sin key. **Regla:** cero duplicados y cero comentarios sin key. **Resultado:** cumple en las cuatro waves.
3. **Pregunta:** ¿la presencia se puede usar como feature workforce-linked? **Motivo:** responder no demuestra elegibilidad ni pertenencia al workforce objetivo. **Metodo:** revision de limitaciones de denominador y join temporal. **Regla:** no promover a score 2 sin elegibilidad oficial, employee-date join y reconciliacion agregada. **Resultado:** pendiente; el limite se mantiene.

## Conteos agregados de respuesta abierta

| Wave | Participantes con algun comentario | doing well | can improve | processes to improve |
|---|---:|---:|---:|---:|
| Mar-2023 | 3,901 | 3,650 | 3,510 | No disponible |
| Jan-2024 | 20,965 | 19,445 | 19,318 | No disponible |
| Jan-2025 | 20,161 | 17,566 | 17,474 | 7,090 |
| Jan-2026 | 15,351 | 11,077 | 12,192 | 6,536 |

Los conteos de campos pueden solaparse porque una persona puede responder varios
prompts. No son porcentajes y no deben leerse como tasa de respuesta elegible.

## Limitaciones y decision

La población observada es la del workbook, no un denominador oficial de
empleados elegibles. Tampoco existe un join empleado-fecha validado para unir
estos comentarios con snapshots de workforce y attrition. Por ello el estado es
**fuente raw disponible; feature no lista para modelado** y no se asigna score 2.

La distribución de participación/no participación se documenta por separado en
`docs/variables/non-respondents/README.md`. No debe derivarse una no respuesta
a partir de la ausencia de comentario: esa distribución usa un supuesto de
snapshot y una comparación de keys QVoice contra HRDA.

**Evidencia y reproduccion:**

- `output/distribution/json/qvoice-comment-evidence-2026-09-09.json`
- `tools/build_qvoice_comment_evidence.py`
- `output/distribution/json/attrition-43-variable-distributions-v2-manifest.json`

## Vista de preocupaciones de retencion (lamina 19)

La lamina 19 no reutiliza el indicador amplio de “cualquier comentario”. Es
una vista `internal_analysis` separada, descriptiva y agregada de feedback de
mejora potencialmente relevante para retencion. No clasifica sentimiento,
quejas, riesgo individual ni causalidad.

- **Concepto y fuente:** menciones por palabras clave en el prompt original
  `can improve` de cada wave; en Jan-2025 y Jan-2026 incorpora ademas el
  prompt original `processes to improve` cuando existe. No utiliza `doing
  well`, columnas `EN`, datos de exit survey ni atributos de workforce para
  clasificar los comentarios.
- **Denominador:** participantes distintos con al menos un comentario no
  vacio en alguno de los prompts de mejora seleccionados en la misma wave.
  Cada porcentaje es `participantes distintos que hacen match con el tema /
  denominador de comentarios de mejora de la wave`; los temas se superponen y
  no suman 100%.
- **Grain y deduplicacion:** participante-wave-tema. Una persona aporta como
  maximo una vez por tema y wave, aunque responda ambos prompts. Se exige cero
  filas duplicadas de participante y cero comentarios de mejora sin key.
- **Taxonomia fija:** Rewards; Career growth and promotion; Manager,
  leadership and respect; Workload, staffing and work-life; Work
  arrangement/RTO/commute; Tools, processes and bureaucracy; Organizational
  confidence/job security. La alineacion con conceptos de QVoice y exit
  survey es solo contextual: no se lee ni usa exit-survey data en este
  calculo.
- **Lenguaje explicito de salida:** se busca aparte con frases multi-palabra
  ingles/espanol y manejo conservador de negacion. Es una señal contextual
  agregada; nunca una etiqueta de empleado. Si no alcanza `n >= 30`, se
  muestra solo `Not publishable (<30)`.
- **Privacidad:** el artefacto no persiste texto libre, IDs, keys, filas ni
  muestras. Todo conteo o porcentaje mostrado requiere `n >= 30`; los valores
  por debajo se suprimen antes de persistir el JSON o de renderizar HTML.

### Flujo y validaciones especificas

1. **Pregunta:** ¿estan disponibles los prompts de mejora esperados en las
   cuatro waves? **Motivo:** la serie debe declarar el cambio de instrumento.
   **Metodo:** resolucion determinista de encabezados antes de leer respuestas.
   **Regla de aceptacion:** `can improve` en Mar-2023, Jan-2024, Jan-2025 y
   Jan-2026; `processes to improve` solo en Jan-2025 y Jan-2026. **Conclusion:**
   el builder falla si el contrato no se cumple.
2. **Pregunta:** ¿los porcentajes se reconcilian con el denominador correcto?
   **Motivo:** un conteo de menciones no debe usarse como porcentaje de
   empleados ni como tasa de respuesta. **Metodo:** sets de participante por
   wave y tema. **Regla de aceptacion:** cada tema publicado iguala
   `100 * n / participantes con comentario de mejora`; cada conteo publicado
   cumple `n >= 30`. **Conclusion:** el builder valida la reconciliacion y
   suprime los buckets pequenos.
3. **Pregunta:** ¿se puede relacionar un comentario con attrition? **Motivo:**
   la apariencia de una key en el raw no prueba elegibilidad, fecha de
   conocimiento ni un join seguro. **Metodo:** limite explicito de alcance.
   **Regla de aceptacion para cualquier uso de feature:** poblacion elegible,
   join empleado-fecha y reconciliacion agregada aprobados. **Resultado:** no
   validado; la lamina no crea una feature, asociacion de attrition ni score.

La tendencia 2023-2026 de los tres temas principales de Jan-2026 es
descriptiva, no estrictamente comparable: Jan-2025 y Jan-2026 incluyen el
prompt adicional de procesos. El analisis RTO/hibrido detallado se conserva en
la lamina 18; que el tema de arreglo de trabajo aparezca tambien en esta
taxonomia no cambia esa vista.

**Evidencia y reproduccion de la lamina 19:**

- `output/distribution/json/qvoice-retention-concerns-evidence-20260910.json`
- `tools/build_qvoice_retention_concerns_evidence.py`
- `tools/build_distribution_html_v2.py --refresh-qvoice-retention-concerns-slide`
