# Factors impacting employee turnover intentions among professionals in Sri Lankan startups

## Ficha

- Autores: Lakshmi Kanchana, Ruwan Jayathilaka y Muhammad Fareed
- Año: 2023
- Revista: *PLOS ONE*, 18(2), e0281729
- DOI: `10.1371/journal.pone.0281729`
- URL oficial: https://doi.org/10.1371/journal.pone.0281729
- Fuente consultada: PLOS ONE y PubMed Central, PMCID `PMC9916568`
- Fecha de consulta: 2026-09-14
- Estado de acceso: Open Access, licencia CC BY
- Etiquetas: `aplicado-turnover`, `people-analytics`, `engagement`, `manager`, `career`

## Abstract y resumen

### Abstract original

El abstract visible describe un estudio con 230 profesionales de startups de Sri
Lanka que usa un modelo probit ordenado para estudiar un indicador de turnover.
Reporta asociaciones negativas de job satisfaction y co-worker support, y una
asociación positiva de leader–member exchange.

### Resumen en español

El estudio construye un indicador ordinal de turnover a partir de una encuesta y
separa niveles bajo, moderado y alto. Considera job satisfaction, work-life
balance, happiness, management support, career management, innovative work
behaviour, leader–member exchange y co-worker support. El modelo final conserva
principalmente satisfacción laboral, LMX, soporte de compañeros e innovación; el
paper también reporta diferencias por edad y género. La evidencia es transversal
y autodeclarada: no demuestra una salida voluntaria observada ni un efecto causal.

## Pregunta y datos

- Pregunta: ¿qué factores psicográficos y sociodemográficos se asocian con niveles de turnover intention en profesionales de startups?
- Población: profesionales que trabajan o habían trabajado en startups de Sri Lanka
- Tamaño: 230 respuestas; 83 con nivel bajo, 79 moderado y 68 alto en el indicador ordinal
- Grain: persona-encuesta, sin seguimiento longitudinal
- Target y horizonte: indicador ordinal de turnover/intención de salida construido con respuestas Likert; sin horizonte futuro definido
- Censura o competing risks: no aplica

## Método y validación

- Método: cuestionario de 1–5 puntos y probit ordenado con selección forward stepwise
- Variables: ocho bloques psicográficos, además de variables demográficas; cada indicador tuvo al menos cuatro preguntas
- Split temporal: no; los datos se recogieron entre agosto y septiembre de 2022 en una sola encuesta
- Métricas: consistencia interna mediante alpha de Cronbach, coeficientes del probit y efectos marginales por nivel de turnover
- Resultados: el paper reporta que job satisfaction y co-worker support se asocian con menor turnover, LMX con mayor turnover e innovative work behaviour con menor turnover alto; el modelo final se describe como explicativo del 71.74% de la variación del indicador

## Limitaciones

- Leakage: no hay ventana de predicción ni separación temporal que permita auditar leakage
- Sesgos: muestra de encuesta, autoinforme y posible common-method bias; el uso de selección stepwise puede hacer inestables los coeficientes
- Generalización: startups de Sri Lanka, con concentración en empleados jóvenes y una parte importante de IT; no es evidencia de Qualcomm
- Fairness/privacidad: el hallazgo demográfico no debe convertirse en targeting; en Attrition sólo puede informar una auditoría autorizada

## Aplicabilidad a Attrition

- Relación con Critical Tech: apoya probar por separado carrera, soporte del manager, soporte del equipo y satisfacción, todos presentes en las prioridades de Julia
- Variables disponibles relacionadas: career goals, intent to stay, engagement, manager context y team turnover agregado, con fecha de conocimiento explícita
- Qué adoptar: hipótesis de bloques y no una variable compuesta indiscriminada
- Qué probar como challenger: bloques QVoice y manager/team en un target de salida voluntaria observada, con split temporal
- Qué posponer: usar LMX o comentarios como features individuales sin definición, fecha y gobierno aprobados

## Acción y decisión

- Señal asociada: satisfacción, soporte de compañeros y relación con el líder
- Palanca potencial: carrera, reconocimiento, soporte del manager y colaboración del equipo
- Acción candidata: evaluar cohortes agregadas y una palanca con owner; el paper no demuestra que la acción funcione
- Métrica de seguimiento: Brier, PR-AUC, lift, calibración, estabilidad y, después, retención observada
- Decisión: `probar como challenger` para los bloques de carrera/manager/team; `referencia metodológica` para el indicador ordinal

## Trazabilidad

- Evidencia consultada: OpenAlex work `W4319827590`; PLOS ONE; PMCID `PMC9916568`; endpoint BioC de PubMed Central
- Sección/página si el texto completo fue revisado: Abstract; Data and methodology; Methodology; Results and discussions; Conclusion
- Limitaciones de acceso: el texto completo abierto sí fue consultado; no se conservó una copia local

