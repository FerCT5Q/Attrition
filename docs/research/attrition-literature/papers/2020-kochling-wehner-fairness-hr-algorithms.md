# Discriminated by an algorithm: a systematic review of discrimination and fairness by algorithmic decision-making in the context of HR recruitment and HR development

## Ficha

- Autores: Alina Köchling y Marius Claus Wehner
- Año: 2020
- Revista: *Business Research*, 13, 795–848
- DOI: `10.1007/s40685-020-00134-w`
- URL oficial: https://doi.org/10.1007/s40685-020-00134-w
- Fuente consultada: SpringerLink y PDF publicado en acceso abierto
- Fecha de consulta: 2026-09-14
- Estado de acceso: Open Access, versión publicada, licencia CC BY
- Etiquetas: `gobierno`, `fairness`, `people-analytics`, `systematic-review`

## Abstract y resumen

### Abstract original

El abstract visible presenta una revisión sistemática de 36 artículos de revista
publicados entre 2014 y 2020 sobre decisiones algorítmicas, discriminación y
fairness en reclutamiento y desarrollo de HR.

### Resumen en español

La revisión muestra que los algoritmos de HR pueden heredar sesgo histórico,
sesgo de representación, sesgo técnico y sesgo emergente. También separa fairness
computacional de fairness percibida y recomienda transparencia, auditoría,
responsabilidad humana, participación de las personas afectadas y controles de
calidad de datos. La mayoría de los trabajos revisados eran conceptuales, reviews
o casos; por eso no es evidencia de que un modelo de attrition prediga mejor.

## Pregunta y datos

- Pregunta: ¿qué evidencia existe sobre sesgo, discriminación y fairness en decisiones algorítmicas de HR?
- Población: literatura sobre reclutamiento, selección, desarrollo y capacitación; no una muestra de empleados de un dataset común
- Tamaño: 3,207 registros iniciales; 3,204 después de deduplicación; 102 artículos evaluados en texto completo; 36 incluidos
- Grain: artículo y sistema algorítmico descrito
- Target y horizonte: fairness, sesgo, discriminación o fairness percibida; no target de turnover
- Censura o competing risks: no aplica

## Método y validación

- Método: revisión sistemática guiada por PRISMA, con SSCI, EBSCO Business Source Premier, búsqueda manual de referencias y dos revisores que comprobaron los textos completos
- Variables: tipo de sesgo, definición de fairness, método, contexto de HR, sistema, geografía y hallazgos
- Split temporal: no es un modelo predictivo; la búsqueda principal se realizó en abril de 2020 y hubo un robustness check posterior
- Métricas: conteo de artículos, categorías descriptivas y síntesis cualitativa; el robustness check añadió `justice` y `adverse impact`
- Resultados: 36 estudios incluidos; predominio de evidencia no empírica; 12 estudios sobre fairness percibida y 12 en desarrollo de HR; el análisis concluye que no existe una solución algorítmica neutral por sí sola

## Limitaciones

- Leakage: no aplica como modelo, aunque el trabajo advierte que datos históricos pueden trasladar sesgos al sistema
- Sesgos: sólo artículos en inglés, dos bases principales, corte temporal 2020 y cobertura centrada en reclutamiento/desarrollo
- Generalización: no mide attrition, no valida desempeño predictivo y no prueba ninguna intervención en Qualcomm
- Fairness/privacidad: precisamente es la contribución central; recomienda definir el estándar de fairness antes de desplegar y auditar periódicamente

## Aplicabilidad a Attrition

- Relación con Critical Tech: convierte fairness, calidad de datos, transparencia y revisión humana en puertas de gobierno del modelo
- Variables disponibles relacionadas: atributos protegidos y categorías de auditoría, únicamente con autorización y sin targeting; variables predictoras y sus proxies deben documentarse
- Qué adoptar: auditoría post-hoc, validación de cobertura/definición, data quality checks, documentación de owner y explicación del uso
- Qué probar como challenger: no aplica como predictor; sí como checklist de gobierno para el champion y challengers
- Qué posponer: cualquier decisión automática sobre personas o uso de una categoría protegida como feature de targeting

## Acción y decisión

- Señal asociada: sesgos de datos, representación, definición y uso del algoritmo
- Palanca potencial: gobernanza, revisión humana, transparencia, actualización de datos y participación de stakeholders
- Acción candidata: establecer fairness/privacy gate antes de promover un modelo o una variable
- Métrica de seguimiento: estabilidad, cobertura, calibración y métricas de fairness definidas antes del análisis; no una única cifra universal
- Decisión: `referencia conceptual` y `gobierno adoptado`

## Trazabilidad

- Evidencia consultada: OpenAlex work `W3104114204`; SpringerLink; PDF publicado, páginas 795–848
- Sección/página si el texto completo fue revisado: abstract, Methods (pp. 804–807), resultados descriptivos (p. 808), Discussion (pp. 835–839) y Conclusion (p. 840)
- Limitaciones de acceso: el texto completo abierto fue consultado; no se conservó una copia local

