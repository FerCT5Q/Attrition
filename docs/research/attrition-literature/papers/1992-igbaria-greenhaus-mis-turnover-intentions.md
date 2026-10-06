# P31 — Determinants of MIS employees' turnover intentions: a structural equation model

## Ficha y alcance de la revisión

- **Autores:** Magid Igbaria y Jeffrey H. Greenhaus.
- **Publicación:** 1 de febrero de 1992; *Communications of the ACM*, 35(2), 34–49.
- **DOI:** [10.1145/129630.129631](https://doi.org/10.1145/129630.129631).
- **Consulta:** 2026-09-30, America/Mexico_City.
- **Clasificación:** `presentation`; bibliografía pública, sin datos internos de empleados.
- **Nivel de evidencia:** metadatos editoriales comprobados. **No se consiguió un abstract científico ni se leyó el texto completo.**
- **Estado:** `Candidato`. Se cierra la revisión de acceso y trazabilidad de esta tanda; queda pendiente la revisión empírica.

## Resultado de la investigación de fuentes

La página oficial de Communications of the ACM confirma título con subtítulo,
autores, fecha, volumen, número, paginación y DOI. Su cuerpo sólo remite a ACM
Digital Library. Crossref coincide, aunque registra el título sin subtítulo y
no proporciona abstract. La identidad del trabajo queda comprobada.

Se encontraron dos problemas de calidad que se conservan en la evidencia:

1. El campo `abstract` de OpenAlex W2003138832 contiene controles y mensajes de
   la interfaz de ACM: descargas, perfiles y alertas. **No es un resumen
   científico** y no se utiliza para inferir variables ni resultados.
2. Drexel muestra título y autores correctos, pero atribuye la publicación a
   *Communications (Englewood. 1964)*, volumen 29, y a Penton. Esos campos
   contradicen ACM y Crossref. Su sección «Abstract» contiene términos
   temáticos, no un resumen del estudio. Se prioriza la referencia de ACM.

OpenAlex y Semantic Scholar enlazan el PDF editorial como acceso bronze. El
GET devuelve HTTP 403 y ACM muestra una verificación automatizada en el
navegador. Drexel no expuso una copia descargable; ResearchGate abrió una página
sin contenido legible. Las búsquedas por título, autores y PDF localizaron
citas posteriores, pero no una copia primaria verificable. La etiqueta de
acceso de un índice no garantiza que se haya leído el contenido.

## Qué se puede sostener

El título confirma el interés por la **intención de salida de empleados de
sistemas de información (MIS)** y anuncia un modelo de ecuaciones
estructurales. Esa proximidad ocupacional motiva conservarlo como antecedente
histórico para Critical Tech.

No se verificaron país, empresas, composición ocupacional, muestra, fechas,
escalas, predictores, coeficientes ni bondad de ajuste. Tampoco se puede afirmar
si incluye seguimiento de salidas reales o se limita a intención. No se
completan estos campos usando citas de terceros.

## Lectura crítica posible y preguntas abiertas

### 1. El outcome del título no acredita nuestro target

**Pregunta:** ¿sustenta predicción de renuncia voluntaria a seis meses?
**Conclusión:** la evidencia disponible no lo acredita. Intención declarada y
salida observada requieren medidas diferentes. Incluso un buen ajuste para
intención necesitaría probar su relación con eventos posteriores y el
horizonte local.

**Acción:** revisar contenido de la escala, horizonte de la pregunta, registro
de eventos y secuencia temporal. Eventos, censura y causas competidoras
permanecen sin confirmar.

### 2. Ecuaciones estructurales y causalidad

**Pregunta:** ¿el método anunciado permite elegir palancas de retención?
**Conclusión:** el nombre del método no permite juzgar identificación,
dirección temporal ni modelos alternativos. Un camino estimado puede describir
una asociación compatible con varias explicaciones.

**Acción:** comprobar mediciones, fuentes, validez de constructos, restricciones,
estimación e incertidumbre. Si las variables provienen de una misma encuesta,
evaluar el posible efecto de método común; **no se afirma que ése sea el
diseño del paper** sin leerlo.

### 3. Cercanía ocupacional y transportabilidad

**Pregunta:** ¿MIS en 1992 representa a Critical Tech hoy?
**Conclusión:** el rótulo motiva la búsqueda, pero no establece equivalencia de
roles, mercado laboral o prácticas de carrera. La composición de la muestra
permanece desconocida.

**Acción:** contrastar población y medición antes de importar un predictor.
Las hipótesis locales sobre carrera, rol o satisfacción deben sustentarse en
fuentes ya revisadas y evidencia interna propia; no se atribuyen a P31.

### 4. Ajuste explicativo y predicción futura

**Pregunta:** ¿existe evidencia de desempeño para nuevas personas o periodos?
**Conclusión:** no es comprobable. No se conocen particiones, calibración,
incertidumbre predictiva ni validación externa. No se registran cifras.

**Acción:** si se recupera el texto, distinguir ajuste estructural, varianza
explicada e inferencia de evaluación predictiva independiente. Una prueba local
compararía bloques con el mismo baseline y cortes temporales. Éste es un
criterio del proyecto, no un resultado de P31.

## Decisión para Attrition

Conservar P31 como **referencia histórica candidata sobre profesionales MIS**.
No aporta por ahora evidencia empírica para añadir un bloque, elegir estimador,
importar pesos o recomendar una intervención. No modifica scores ni el modelo.

Para reabrir la revisión se necesita una copia autorizada con métodos y
resultados, o al menos un abstract primario para una revisión limitada. La
lectura integral deberá cubrir muestra y exclusiones, instrumentos, cronología,
identificación, resultados e incertidumbre, modelos alternativos y relación
entre intención y salida observada.

## Trazabilidad

- [CACM](https://cacm.acm.org/research/determinants-of-mis-employees-turnover-intentions/): referencia completa; remisión a ACM DL sin contenido científico interior.
- [Crossref](https://api.crossref.org/works/10.1145%2F129630.129631): identidad y publicación; sin abstract.
- [OpenAlex W2003138832](https://api.openalex.org/works/https://doi.org/10.1145/129630.129631): localización bronze; abstract descartado por contaminación con interfaz.
- [Semantic Scholar](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1145/129630.129631?fields=title,authors,abstract,year,venue,openAccessPdf,url): abstract no redistribuido y mismo PDF editorial.
- [ACM DL](https://dl.acm.org/doi/10.1145/129630.129631) y [PDF](https://dl.acm.org/doi/pdf/10.1145/129630.129631): barrera/HTTP 403; ninguna página interior leída.
- [Drexel](https://researchdiscovery.drexel.edu/esploro/outputs/journalArticle/Determinants-of-MIS-employees-turnover-intentions/991020542587004721): leído en navegador; campos bibliográficos contradictorios y sin texto completo accesible.
- Registros: `output/research/attrition-literature/20260929-pending-review/P31/sources/`. Las observaciones del navegador no inventan HTTP ni hash de contenido no capturado.
