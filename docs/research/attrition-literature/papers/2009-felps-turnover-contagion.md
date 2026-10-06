# Turnover Contagion: How Coworkers' Job Embeddedness and Job Search Behaviors Influence Quitting

## Ficha

- Autores: Will Felps, Terence R. Mitchell, David R. Hekman, Thomas W. Lee, Brooks C. Holtom y Wendy S. Harman
- Año: 2009
- Revista: *Academy of Management Journal*, 52(3), 545–561
- DOI: `10.5465/amj.2009.41331075`
- URL oficial: https://doi.org/10.5465/amj.2009.41331075
- Fuente consultada: Crossref y OpenAlex; landing page editorial
- Fecha de consulta: 2026-09-14
- Estado de acceso: artículo cerrado; abstract visible en OpenAlex
- Etiquetas: `aplicado-turnover`, `team`, `job-embeddedness`, `multilevel`

## Abstract y resumen

### Abstract original

El abstract reporta un modelo de turnover contagion en el que job embeddedness y
job search de compañeros influyen en la decisión individual de renunciar.

### Resumen en español

La evidencia proviene de 45 sucursales de un banco regional y 1,038 departamentos
de una empresa nacional de hospitalidad. Un análisis multinivel encontró que las
señales de embeddedness y búsqueda de empleo de compañeros explican variación en
el turnover voluntario individual más allá de predictores individuales y grupales.
Es una justificación directa para probar contexto de equipo, pero no autoriza a
construir redes individuales ni a usar resultados futuros del propio equipo.

## Pregunta y datos

- Pregunta: ¿las conductas y el embeddedness de compañeros ayudan a explicar la decisión individual de renunciar?
- Población: empleados de una institución bancaria y de una empresa de hospitalidad
- Tamaño: 45 sucursales y 1,038 departamentos; el abstract no informa el número total de empleados
- Grain: persona anidada en grupo/sucursal/departamento
- Target y horizonte: turnover voluntario individual/quitting; el horizonte exacto no aparece en el abstract
- Censura o competing risks: no se puede confirmar desde el abstract

## Método y validación

- Método: modelo multinivel con predictores individuales y grupales
- Variables: job embeddedness de compañeros y job search de compañeros, además de predictores individuales y del grupo
- Split temporal: no confirmado; el abstract no describe validación out-of-time
- Métricas: varianza incremental explicada por los predictores de grupo; el abstract no reporta AUC, Brier ni calibración
- Resultados: las señales de compañeros aportaron explicación adicional del turnover voluntario individual en las dos poblaciones

## Limitaciones

- Leakage: para HRDA se debe usar una ventana rezagada y excluir la salida futura del propio equipo; el abstract no documenta cómo se resolvió
- Sesgos: dos industrias y organizaciones concretas; la composición y movilidad de equipos puede diferir de Critical Tech
- Generalización: la asociación grupal no demuestra contagio causal ni desempeño en Qualcomm
- Fairness/privacidad: el uso operativo exige cohortes agregadas, mínimo de 30 y no exponer miembros, managers ni búsquedas individuales

## Aplicabilidad a Attrition

- Relación con Critical Tech: coincide con la prioridad de Julia sobre team turnover y manager context
- Variables disponibles relacionadas: turnover agregado rezagado por equipo, cambios de manager y contexto regional, sujetos a definición de membresía y privacidad
- Qué adoptar: hipótesis de features grupales rezagadas y separación entre señal de equipo y outcome individual
- Qué probar como challenger: bloque team/manager contra el mismo split temporal del baseline
- Qué posponer: centralidad de red, job search individual, identidad de compañeros o cualquier feature con aristas no aprobadas

## Acción y decisión

- Señal asociada: salida previa del equipo y comportamiento agregado de movilidad/búsqueda
- Palanca potencial: manager enablement, estabilidad del equipo y conversación de carrera; no se presume causalidad
- Acción candidata: intervención agregada de soporte o carrera con owner definido
- Métrica de seguimiento: lift, calibración, estabilidad temporal y cohortes válidas; después, retención observada
- Decisión: `probar como challenger` para team/manager, condicionado a privacidad y ventana rezagada

## Trazabilidad

- Evidencia consultada: Crossref DOI `10.5465/amj.2009.41331075`; OpenAlex work `W2132723713`; abstract visible
- Sección/página si el texto completo fue revisado: abstract; el texto completo no fue accesible
- Limitaciones de acceso: no se almacenó el artículo cerrado; nivel multinivel, ventana y métricas detalladas quedan pendientes

