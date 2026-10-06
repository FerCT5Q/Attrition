# RTO/hybrid comment in QVoice

## Conocimiento acumulado

La fuente raw de QVoice contiene respuestas abiertas identificadas en Mar-2023,
Jan-2024, Jan-2025 y Jan-2026. Esta disponibilidad corrige el estado anterior
que indicaba que no existia ninguna fuente de comentarios. El entregable actual
es descriptivo e interno: cuenta menciones tematicas, no sentimiento ni quejas.

## Definicion y uso

- **Concepto:** mencion de Remote / WFH, Hybrid o RTO / office attendance en los prompts originales de QVoice.
- **Uso actual:** evidencia descriptiva para explorar temas de modalidad laboral.
- **Tipo semantico:** `survey` / texto abierto agregado.
- **Grain:** caso participante-wave-tema; cada participante cuenta una vez por tema en cada wave, aunque escriba en varios prompts.
- **Prompts:** doing well, can improve y processes to improve cuando existe.
- **Regla de conocimiento:** se usa la fecha de la wave; las columnas 2026 `... EN` son diagnostico agregado y no entran a la tendencia principal.

## Flujo historico y validaciones

1. **Pregunta:** ¿existe una fuente raw y una clave usable en cada wave? **Motivo:** la fuente estructurada de Redshift no conserva el texto abierto. **Metodo:** lectura agregada de la hoja `Raw data` y resolucion de `EmployeeID`, `Participant's Unique Identifier`, `EmpID` y `Emp ID`. **Regla:** cuatro waves, prompts requeridos y key usable. **Resultado:** cumple; 7,314, 36,806, 37,837 y 42,203 claves distintas, respectivamente.
2. **Pregunta:** ¿el grain contiene duplicados o comentarios sin key? **Motivo:** ambos pueden inflar la tendencia o impedir una deduplicacion segura. **Metodo:** conteo de filas por key y de filas con cualquier prompt no vacio sin key. **Regla:** cero duplicados y cero comentarios sin key. **Resultado:** cumple en las cuatro waves.
3. **Pregunta:** ¿las menciones se deduplican por participante-wave-tema? **Motivo:** una persona puede escribir en varios prompts y mencionar varios temas. **Metodo:** clasificacion en memoria con la taxonomia versionada y conjuntos de keys por tema; solo se persisten conteos. **Regla:** una contribucion maxima por tema y wave. **Resultado:** cumple; los temas pueden solaparse.
4. **Pregunta:** ¿las cohortes publicadas cumplen privacidad? **Motivo:** evitar publicar celdas pequenas. **Metodo:** cada conteo visible se compara con `n >= 30`. **Regla:** suprimir cualquier valor menor a 30. **Resultado:** todas las celdas publicadas cumplen.

## Evidencia agregada actual

| Wave | Remote / WFH | Hybrid | RTO / office attendance |
|---|---:|---:|---:|
| Mar-2023 | 345 | 189 | 326 |
| Jan-2024 | 961 | 287 | 559 |
| Jan-2025 | 1,404 | 269 | 1,480 |
| Jan-2026 | 1,376 | 689 | 1,168 |

Los solapamientos son posibles. El diagnostico de 2026 compara las columnas
`... EN` en forma agregada, pero no cambia los valores anteriores.

## Limitaciones y decision

Los conteos no son sentimiento, no confirman una queja y no demuestran causalidad.
El contexto de requirement/friction se cuenta solo cuando coexiste con una
mencion de oficina en prompts de mejora; se presenta como contexto, no como
clasificacion de complaint. Todavia faltan un denominador oficial de workforce,
un join empleado-fecha validado y una regla aprobada de elegibilidad. Por eso no
se promueve esta evidencia a score 2 ni a feature de attrition.

**Evidencia y reproduccion:**

- `output/distribution/json/qvoice-comment-evidence-2026-09-09.json`
- `tools/build_qvoice_comment_evidence.py`
- `output/distribution/json/attrition-43-variable-distributions-v2-manifest.json`

El JSON contiene solo metadatos, conteos y diagnosticos agregados; no contiene
identificadores ni texto libre.
