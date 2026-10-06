# RFRSF: Employee Turnover Prediction Based on Random Forests and Survival Analysis

## Ficha

- **Autores:** Ziwei Jin, Jiaxing Shang, Qianwen Zhu, Chen Ling, Wu Xie y Baohua Qiang
- **Año:** 2020
- **Libro/conferencia:** *Web Information Systems Engineering – WISE 2020*, Lecture Notes in Computer Science, volumen 12343, pp. 503–515
- **DOI:** `10.1007/978-3-030-62008-0_35`
- **URL oficial:** https://doi.org/10.1007/978-3-030-62008-0_35
- **Fuente consultada:** Springer Nature Link y Crossref
- **Fecha de consulta:** 2026-09-24
- **Estado de acceso:** Abstract oficial visible; capítulo completo cerrado
- **Etiquetas:** `challenger`, `survival`, `random-forest`, `longitudinal`, `multiple-events`

## Abstract y resumen

### Resumen en español

RFRSF parte de una crítica a los enfoques centrados sólo en el empleado que
ignoran eventos históricos de turnover y registros longitudinales de empleo. El
trabajo propone un enfoque centrado en eventos: combina survival analysis para
tratar datos censurados con aprendizaje ensemble para predecir el comportamiento
de turnover. También describe una estrategia para empleados con múltiples
registros de turnover y construye datos de supervivencia con registros censurados.

La evaluación usa datos reales extraídos de una de las mayores plataformas
profesionales en línea de China y compara RFRSF con varios baselines. El abstract
afirma que incorporar survival analysis mejora significativamente el desempeño,
pero no expone tamaño de muestra, features, métricas, split temporal ni cifras de
calibración.

## Pregunta y datos

- **Pregunta:** ¿puede un modelo híbrido de supervivencia y ensemble mejorar la predicción de turnover usando historiales de eventos?
- **Población:** perfiles y registros de una plataforma profesional en línea de China
- **Tamaño:** no reportado en el abstract visible
- **Grain:** historial de eventos de una persona; el tratamiento exacto de cada episodio no está disponible
- **Target y horizonte:** comportamiento de turnover; horizonte operativo no confirmado
- **Censura o competing risks:** censura explícita; la estrategia para múltiples registros se menciona, pero no se puede reconstruir completa sin el capítulo

## Método y validación

- **Método:** RFRSF, híbrido de survival analysis y ensemble/random-forest; el título y las palabras clave también lo relacionan con random survival forests
- **Variables:** historial de empleo y señales disponibles en la plataforma; no se conocen la lista ni la fecha de conocimiento de cada feature
- **Split temporal:** no confirmado
- **Métricas:** comparación contra varios baselines; nombres y valores no expuestos en el abstract
- **Resultados:** el abstract reporta una mejora significativa al incorporar survival analysis; no se importa esa magnitud al modelo local

## Limitaciones

- **Leakage:** no auditable sin conocer las ventanas de extracción y la construcción de los múltiples episodios
- **Sesgos:** una plataforma profesional, una población y un país; posible selección de personas con presencia digital
- **Generalización:** los registros de una red profesional no son equivalentes al HRDA ni prueban desempeño en Critical Tech
- **Fairness/privacidad:** no presenta una auditoría de fairness; sus datos externos no autorizan usar perfiles o texto como features internas

## Aplicabilidad a Attrition

- **Relación con Critical Tech:** respalda mantener survival como estructura principal y probar un challenger no lineal cuando el baseline temporal esté reejecutado con el scope de fase 1
- **Variables disponibles relacionadas:** snapshots de empleo, tenure, cambios y eventos históricos ya documentados; sólo entrarían con fecha de conocimiento y reglas de censura propias
- **Qué adoptar:** representar correctamente persona–periodo, separar eventos observados del futuro y tratar múltiples episodios sólo con una definición interna aprobada
- **Qué probar como challenger:** RFRSF o Random Survival Forest frente a `cloglog`, con el mismo holdout temporal, target de salida voluntaria y métricas de Brier, PR-AUC, lift, calibración y estabilidad
- **Qué posponer:** trasladar features de la plataforma china, importar métricas publicadas o reemplazar el modelo estadístico principal sin evidencia local

## Acción y decisión

- **Señal asociada:** historial longitudinal y estructura de eventos de turnover
- **Palanca potencial:** no la establece; es una fuente metodológica/predictiva
- **Acción candidata:** construir primero el frame interno persona–mes y auditar censura, múltiples salidas y leakage antes de entrenar el challenger
- **Métrica de seguimiento:** desempeño out-of-time, calibración, Brier, PR-AUC, lift y estabilidad por cohorte
- **Decisión:** `probar como challenger`

## Trazabilidad

- **Evidencia consultada:** Springer Nature Link, abstract y ficha del capítulo; Crossref `https://api.crossref.org/works/10.1007%2F978-3-030-62008-0_35`
- **Sección/página si el texto completo fue revisado:** abstract oficial de Springer; no se consultó el capítulo cerrado
- **Limitaciones de acceso:** no se usan tamaño de muestra, variables, baselines, métricas ni detalles del algoritmo que no aparecen en el abstract
