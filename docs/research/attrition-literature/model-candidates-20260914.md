# Suplemento de modelos y evidencia aplicada — 2026-09-14

## Propósito y nivel de evidencia

Este suplemento continúa la búsqueda sin alterar el tracker oficial `P01–P40`.
No convierte automáticamente un paper nuevo en evidencia para el modelo de
Attrition. Cada trabajo se registra con el alcance que pudo verificarse en
Crossref, OpenAlex, PubMed o la fuente editorial, y conserva una decisión
provisional hasta completar la revisión de muestra, variables, validación y
limitaciones.

La regla de uso es separar cuatro cosas: método transferible, evidencia sobre
variables, evidencia sobre turnover observado y evidencia sobre una acción de
retención. Un resultado de accuracy en otra población no demuestra desempeño
en HRDA ni justifica targeting individual.

## Candidatos priorizados

### S01 — Fukui & Wu (2026)

- **Título:** *Prediction of Behavioral Health Employee Turnover With HR Data–Based Machine Learning Combined With Job Well-Being Indicators*.
- **DOI:** `10.1176/appi.ps.20250364`.
- **Fuente y acceso:** *Psychiatric Services*; OpenAlex identifica versión de repositorio Green OA en PMC; no está en el tracker original.
- **Qué se verificó:** El abstract describe datos HR históricos desde 2011, doce indicadores de bienestar recogidos por encuesta, estado de turnover observado doce meses después, 303 organizaciones y 72 salidas voluntarias. Añadir tres indicadores de carrera, alineación de expectativas y supervisión elevó el AUC reportado de 0.63 a 0.76.
- **Aplicabilidad:** Es la evidencia más cercana a la hipótesis de Julia sobre QVoice, carrera y manager/supervisión. Apoya probar esos bloques como señales gobernadas, siempre con fecha de wave anterior al snapshot y sin convertir el resultado en causalidad.
- **Limitación:** Población de behavioral health y outcome anual; no demuestra que el mismo efecto exista en Critical Tech ni que una intervención reduzca attrition.
- **Decisión provisional:** `probar como challenger` para el bloque survey, condicionado a freshness, join temporal y validación out-of-time.
- **Fuentes:** DOI `10.1176/appi.ps.20250364`; OpenAlex work `W7126269019`.

### S02 — Park, Feng & Jeong (2024)

- **Título:** *Developing an advanced prediction model for new employee turnover intention utilizing machine learning techniques*.
- **DOI:** `10.1038/s41598-023-50593-4`.
- **Fuente y acceso:** *Scientific Reports*; OpenAlex identifica el artículo como Gold OA y no retractado.
- **Qué se verificó:** Usa la Job Movement Path Survey de Korea Employment Information Service y compara logistic regression, KNN y XGBoost para turnover intention; el abstract reporta 78.5% de accuracy para XGB.
- **Aplicabilidad:** Sirve para justificar un challenger no lineal sobre señales de job security, satisfacción y condiciones laborales.
- **Limitación:** El target es intención de salida, no salida voluntaria observada; accuracy no es la métrica principal adecuada para nuestro evento desbalanceado.
- **Decisión provisional:** `referencia metodológica`; no usar su accuracy como benchmark de Attrition.
- **Fuentes:** DOI `10.1038/s41598-023-50593-4`; OpenAlex work `W4390816463`.

### S03 — Wang & Zhi (2021)

- **Título:** *A machine learning-based analytical framework for employee turnover prediction*.
- **DOI:** `10.1080/23270012.2021.1961318`.
- **Fuente y acceso:** *Journal of Management Analytics*; OpenAlex lo identifica como artículo no retractado, pero cerrado.
- **Qué se verificó:** El abstract propone feature engineering, validación y un ensemble, evaluado en dos datasets de contextos y tamaños distintos.
- **Aplicabilidad:** Refuerza el patrón de comparar varios modelos después de congelar el feature engineering y la validación, en vez de escoger un algoritmo por moda.
- **Limitación:** El abstract no permite confirmar el grain longitudinal, el split temporal ni la calibración; no se usará como evidencia de superioridad de un ensemble.
- **Decisión provisional:** `probar como challenger` sólo si el texto completo confirma validación temporal y la complejidad aporta lift/calibración/estabilidad.
- **Fuentes:** DOI `10.1080/23270012.2021.1961318`; OpenAlex work `W3195627748`.

### S04 — Younis, Ahsan & Chatteur (2023)

- **Título:** *An employee retention model using organizational network analysis for voluntary turnover*.
- **DOI:** `10.1007/s13278-023-01031-w`.
- **Fuente y acceso:** *Social Network Analysis and Mining*; abstract disponible en PubMed, PMCID `PMC9893187`.
- **Qué se verificó:** Es una revisión conceptual de 30 trabajos sobre turnover voluntario en redes. Discute posición central, eigenvector, structural holes, K-shell y contagio de turnover.
- **Aplicabilidad:** Da hipótesis para team turnover, manager proximity y contagio entre equipos.
- **Limitación:** Declara que no realizó investigación primaria con participantes; no demuestra que una métrica de red prediga turnover en HRDA. No se debe derivar una red ni usar centralidad sin aristas, owner, privacidad y grain aprobados.
- **Decisión provisional:** `referencia conceptual`; no entra como feature del MVP.
- **Fuentes:** DOI `10.1007/s13278-023-01031-w`; PubMed PMID `36748055`; PMCID `PMC9893187`.

## Traducción a nuestro plan de modelado

1. Mantener el hazard discreto mensual y la logística de seis meses como
   referencias internas, con split temporal y métricas de Brier, PR-AUC, lift,
   calibración y estabilidad.
2. Probar una sola familia de features por vez: primero carrera/tenure y
   manager/equipo; después QVoice gobernado; finalmente un challenger no lineal.
3. Usar QVoice sólo cuando la wave sea conocida en el snapshot, registrar la
   no respuesta como estado de observabilidad y evitar texto libre en el MVP.
4. Tratar manager/team turnover como hipótesis agregada. La literatura de redes
   no sustituye una definición reproducible de membresía, ventana, deduplicación
   y privacidad.
5. No usar papers de intención, accuracy o datasets públicos para declarar que
   una variable causa o predice attrition en Qualcomm.

## Siguiente revisión bibliográfica

La siguiente ronda debe completar primero los candidatos `P13–P40` que afectan
directamente los bloques priorizados por Julia: turnover/embeddedness, manager y
team, engagement/QVoice, carrera/talento técnico y fairness. Los cuatro trabajos
S01–S04 quedan como suplemento priorizado, no como sustituto del conteo ni de
la revisión completa.
