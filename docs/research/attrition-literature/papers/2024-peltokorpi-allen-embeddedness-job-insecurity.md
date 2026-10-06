# P39 — Job embeddedness and voluntary turnover in the face of job insecurity

## Ficha y alcance

- **Autores:** Vesa Peltokorpi y David G. Allen.
- **Publicación:** *Journal of Organizational Behavior*, 45(3), 416–433, marzo de 2024; publicación online el 7 de julio de 2023.
- **DOI:** [10.1002/job.2728](https://doi.org/10.1002/job.2728).
- **Consulta:** 2026-09-30, America/Mexico_City.
- **Clasificación:** `presentation`; bibliografía pública sin datos internos.
- **Evidencia:** texto completo editorial de 18 páginas, versión online de 2023 depositada en Warwick; métodos y cifras problemáticas contrastados con el HTML de Wiley, que ya referencia el volumen de 2024.
- **Localizadores:** se usan las páginas 1–18 del PDF consultado, no se presume que esos números sean los del volumen definitivo.
- **Licencia:** PDF, Crossref y Wiley indican CC BY-NC-ND 4.0. Warwick muestra CC BY 4.0 en su ficha; se conserva la discrepancia y se prioriza la indicación editorial. OpenAlex etiqueta esa localización como submittedVersion, aunque el repositorio y el archivo identifican una versión editorial.
- **Estado:** `Revisado`, con lectura integral. Las discrepancias documentadas permanecen abiertas.

## Pregunta y aporte conceptual

El artículo estudia cómo la inseguridad laboral percibida se relaciona con
búsqueda de empleo, intención y salida voluntaria, y cómo la vinculación al
trabajo y a la comunidad modifica esas relaciones. Usa conservación de
recursos y estados próximos a la salida: alguien puede querer quedarse, querer
irse o sentirse limitado para elegir.

Su aporte principal es que **permanecer no demuestra bienestar ni compromiso**.
Una persona muy vinculada a su organización puede temer perder recursos y
reducir la búsqueda de alternativas aun sintiéndose insegura. Los recursos
fuera del trabajo pueden facilitar una respuesta distinta. Es una explicación
plausible apoyada por asociaciones; el estudio no prueba una intervención para
mejorar bienestar o retención.

La inseguridad se mide como percepción subjetiva. Un cambio administrativo,
reorganización o reducción de plantilla no equivale automáticamente a esa
percepción. La vinculación se mide con escalas globales; no es un índice
construido con columnas administrativas.

## Dos estudios y su flujo de observación

Ambos reclutan mediante una empresa de investigación a personas empleadas a
tiempo completo en organizaciones privadas de Japón. Son muestras
independientes, de sectores diversos, con encuestas voluntarias e incentivos
pequeños. No constituyen muestras específicas de Critical Tech.

| Elemento | Estudio 1 | Estudio 2 |
|---|---|---|
| Invitaciones iniciales | 1600 | 1106 |
| Respuestas en T1 | 800 | 785 |
| T2, 3 meses después de T1 | 755 | 596 |
| T3 | 509, a los 24 meses | 540, a los 12 meses |
| Salidas involuntarias excluidas declaradas | 12 | 3 |
| Muestra analítica final | 497 | 516 |
| Muestra final respecto a respuestas T1, recálculo | 62,1 % | 65,7 % |
| Mediador investigado | Búsqueda de empleo | Intención de salida |
| Medida de salida | Autorreporte en T3 | Autorreporte en T3 |

En el estudio 1 se miden inseguridad y vinculación al trabajo en T1, búsqueda
en T2 y salida en T3. En el estudio 2, la descripción ubica inseguridad y
controles en T1, vinculación al trabajo/comunidad en T2 y salida en T3, pero
**no asigna explícitamente la intención de salida a una wave**. La sección de
medidas describe su instrumento sin resolver esa fecha. Esto se confirmó en
la sección 9.1–9.2 del HTML editorial, además del PDF p. 10.

En el estudio 1, 509 menos 12 concilia con 497. En el segundo, 540 menos 3
produce 537, no 516: quedan 21 casos adicionales sin desglosar. Podrían ser
casos incompletos; el texto menciona eliminación listwise. Se registra la
falta de conciliación, **sin clasificar esos 21 como renunciantes ni afirmar
que el tamaño final es falso**.

## Medición y análisis estadístico

El estudio 1 utiliza inseguridad de cuatro ítems, vinculación global al trabajo
de siete ítems tomada de Crossley et al. (P17), y búsqueda de cuatro ítems.
El segundo cambia la escala de inseguridad a tres ítems, mantiene la medida
de vinculación al trabajo, incorpora cinco ítems de vinculación comunitaria y
tres de intención. Un ítem de intención se refiere a los siguientes 12 meses.

Se usan escalas de siete puntos, traducción y retrotraducción; los autores
presentan confiabilidad y análisis factoriales confirmatorios. La medida
global de P17 es conceptualmente distinta del índice formativo de P15. En
particular, no se importan preguntas, pesos o proxies de vínculos privados.

Las pruebas principales combinan regresión de búsqueda/intención, regresión
logística de salida, interacciones y mediación moderada mediante PROCESS,
con 5000 muestras bootstrap. Se consideran características demográficas,
antigüedad, educación y alternativas laborales como controles; su inclusión
en este paper no autoriza su incorporación al modelo local. Se repiten
análisis sin controles.

La proporción de salida publicada es 14 % en la primera muestra y 5 % en la
segunda, redondeada en tablas 1 y 3. No se da un conteo exacto de eventos:
no se reconstruye multiplicando proporciones redondeadas. En particular,
la segunda muestra contiene pocos eventos respecto a la complejidad del
modelo de salida.

## Resultados que pueden describirse

En el estudio 1, la inseguridad se asocia positivamente con búsqueda y salida.
La interacción con vinculación al trabajo en la regresión de búsqueda es
negativa: B = −0.12, p = .004, IC del 95 % [−0.20, −0.04] (tabla 2,
PDF p. 7). Los autores reportan una vía indirecta por búsqueda y un índice
negativo de mediación moderada (pp. 6–8).

En el estudio 2, la interacción de inseguridad con vinculación al trabajo es
negativa en la regresión de intención: B = −0.13, p = .038, IC
[−0.28, −0.01]. La interacción con vinculación fuera del trabajo es positiva:
B = 0.14, p = .033, IC [0.01, 0.26] (tabla 4, PDF p. 12). La interpretación
es que los dos dominios pueden moderar de forma distinta la relación con
intención. **No son interacciones estimadas directamente sobre la probabilidad
de salida.**

No se afirma que una dimensión sea universalmente más importante ni que se
haya demostrado una diferencia de desempeño predictivo. Para comparar
formalmente magnitudes entre dimensiones, escalas o estudios se necesitarían
contrastes y especificaciones apropiados. Los resultados no son efectos
transportables a otra población.

## Comprobaciones numéricas y discrepancias

Las cifras siguientes se contrastaron visualmente en las páginas 10–12 del
PDF y con las secciones 9–10 y tabla 4 del HTML de Wiley.

1. **Signo del índice para vinculación fuera del trabajo.** En H4b se publica
   B = −0.07 con IC [0.01, 0.08], mientras que la interacción y la narrativa
   son positivas. El producto de los coeficientes mostrados, si pertenecen al
   mismo modelo de primera etapa, es 0.14 × 0.48 = 0.0672. Esto apoya la
   necesidad de aclarar el signo; no autoriza cambiarlo a +0.07 por cuenta
   propia. Un intervalo bootstrap no tiene que estar centrado en el punto,
   por lo que el diagnóstico se basa también en la especificación y la
   dirección narrativa. La discrepancia aparece en ambas versiones leídas.
2. **Coeficiente y odds ratio.** Para intención, tabla 4 informa B = 0.48 y
   OR = 1.64. El recálculo exp(0.48) = 1.616074. Incluso considerando redondeo
   convencional a dos decimales, el intervalo compatible con B no alcanza el
   intervalo compatible con OR. Es una discrepancia de reporte que requiere
   la salida exacta. Las cifras equivalentes del estudio 1 sí concilian.
   Además, odds ratio no equivale a multiplicador de probabilidad.
3. **Intervalo próximo a cero.** La mediación de H3 se describe con B = 0.03
   e IC [0.00, 0.10]. El límite inferior redondeado no revela si el valor
   exacto es positivo o cero; no se declara ausencia de significación por
   esa presentación ni se completa un decimal no publicado.
4. **Flujo de casos.** Los 21 casos del estudio 2 señalados arriba requieren
   desglose. Las proporciones finales respecto a T1 se recalcularon de forma
   independiente, sin atribuir causas a las exclusiones.

Cálculos y supuestos:
`output/research/attrition-literature/20260929-pending-review/P39/statistical-check.json`.
No se reprodujeron estimadores, errores estándar ni bootstrap sin sus datos.
Los autores ofrecen datos bajo solicitud razonable; no se realizó contacto ni
se accedió a microdatos.

## Límites que afectan la aplicación

### Cronología, medición intermedia y salida temprana

La salida se pregunta al final como permanencia en la misma organización y,
en caso de salida, si fue voluntaria. No se documentan fechas exactas de cada
evento ni cómo se trata una salida anterior a T2. Por ello no queda garantizado
que la búsqueda, la vinculación medida a los tres meses o la intención
precedieran todas las salidas incluidas.

En el segundo estudio, medir vinculación después de inseguridad también
permite que la primera cambie como respuesta a la segunda. No es un moderador
basal automáticamente estable. Los autores reconocen que no separan cambios
y relaciones recíprocas entre ambos constructos (PDF p. 15).

Una prueba local debe establecer fecha de conocimiento, quién sigue en riesgo
al corte y horizonte posterior. Para usar mediciones de T2, un nuevo corte
tras T2 evita tratarlas como si ya existieran en T1. No se afirma que haya
leakage demostrado; se identifican condiciones que el reporte no resuelve.

### Selección, ausencia de respuesta y causas de salida

El análisis exige completar las encuestas. Los autores no encuentran
diferencias significativas en algunas comparaciones entre quienes completan
y no completan, pero eso no demuestra ausencia de selección ni que los datos
faltantes sean aleatorios.

Además, eliminar salidas involuntarias —un resultado especialmente relacionado
con inseguridad— cambia la población analítica. No equivale a conservar una
cohorte inicial con sus causas de salida y tiempos. Para el objetivo local se
necesita una política explícita de censura/eventos competidores, sin excluir
retrospectivamente personas por un resultado futuro para calcular riesgo
prospectivo.

### Autorreporte y evidencia causal

La salida es un comportamiento declarado, más cercano al target que una
intención, pero no está reconciliada contra registros administrativos. La
voluntariedad también es autorreportada. La separación entre waves reduce
algunos problemas de simultaneidad, pero no elimina método común, confusión,
causalidad recíproca ni selección.

Los dos estudios representan una réplica conceptual con instrumentos,
mediadores y horizontes diferentes; no una validación temporal de un mismo
predictor ya ajustado. El artículo no presenta holdout predictivo, Brier,
calibración o utilidad prospectiva. No prueba que intervenir sobre vinculación
o inseguridad reduzca renuncias.

### Permanencia y bienestar

La posibilidad de sentirse atrapado desaconseja usar retención como único
criterio de éxito de una acción. Las recomendaciones sobre apoyo del manager
y recursos para afrontar incertidumbre son propuestas prácticas; no son
intervenciones aleatorizadas o evaluadas en este artículo.

No se traduce la vinculación comunitaria en inferencias sobre familias,
vivienda, finanzas o vida privada. El resultado conceptual tampoco justifica
restricciones a la movilidad de empleados.

## Decisión para Critical Tech

| Elemento | Decisión bibliográfica |
|---|---|
| Percepción de inseguridad | Hipótesis contextual si existe una medición válida y fechada; no sustituirla por reorganización administrativa. |
| Vinculación al trabajo y a la comunidad | Mantener la distinción conceptual; no construir un único índice con proxies disponibles. |
| Intención, búsqueda y salida | Conservar outcomes y fechas diferentes; la intención no sustituye eventos. |
| Interacciones | Candidatas para pruebas específicas; definir antes de ajustar y validar fuera de muestra. |
| Coeficientes, índices e intervalos | No importar; discrepancias y especificación por aclarar. |
| Retención | Considerar bienestar y capacidad de elección al evaluar acciones. |

P39 aporta una **hipótesis contextual relevante y una advertencia de
interpretación de la permanencia**. Su apoyo cuantitativo debe leerse con las
limitaciones temporales, de selección y de reporte documentadas. No cambia
scores, no acredita variables internas y no promueve un modelo.

## Trazabilidad

- [Warwick: ficha y versión editorial](https://wrap.warwick.ac.uk/id/eprint/176851/).
- [PDF completo consultado](https://wrap.warwick.ac.uk/id/eprint/176851/8/J%20Organ%20Behavior%20-%202023%20-%20Peltokorpi%20-%20Job%20embeddedness%20and%20voluntary%20turnover%20in%20the%20face%20of%20job%20insecurity.pdf): pp. 1–18; diseño/medidas/resultados pp. 5–8 y 10–12; discusión pp. 14–15.
- [Wiley, versión HTML](https://onlinelibrary.wiley.com/doi/10.1002/job.2728): metadatos, secciones 9–10, tabla 4 y disponibilidad de datos contrastados; las discrepancias numéricas siguen visibles.
- [Crossref](https://api.crossref.org/works/10.1002%2Fjob.2728) y [OpenAlex](https://api.openalex.org/works/https://doi.org/10.1002/job.2728): identidad, fechas y localizaciones.
- Fuentes, hash del PDF, páginas leídas y verificaciones:
  `output/research/attrition-literature/20260929-pending-review/P39/`.
- Código de comprobación: `tools/.tmp/verify_p39_published_numbers.py`.
  Las imágenes temporales sirvieron sólo para verificar signos y cifras; no
  forman parte de un paquete de redistribución.
