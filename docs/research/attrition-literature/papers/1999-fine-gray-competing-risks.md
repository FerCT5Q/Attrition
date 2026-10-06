# A Proportional Hazards Model for the Subdistribution of a Competing Risk

## Ficha

- Autores: Jason P. Fine y Robert J. Gray
- Año: 1999
- Revista: Journal of the American Statistical Association
- DOI: `10.1080/01621459.1999.10474144`
- URL: https://doi.org/10.1080/01621459.1999.10474144
- Consultado: 2026-09-07
- Acceso: abstract visible; texto completo normalmente cerrado
- Etiquetas: `competing-risks`, `cumulative-incidence`, `fundacional`

## Resumen

El método modela directamente la incidencia acumulada de una causa específica
cuando existen otros tipos de evento que impiden observarla. Contrasta el
hazard cause-specific con el subdistribution hazard, que mantiene la relación
con la probabilidad acumulada de la causa de interés.

La distinción es importante: una covariable puede aumentar el riesgo de salida
involuntaria y, al mismo tiempo, modificar la probabilidad acumulada de salida
voluntaria porque ambas causas compiten.

## Aplicabilidad a Attrition

Es relevante para separar `Voluntary`, `Involuntary` y posiblemente `Voluntary
Exception`. No debe incorporarse hasta que HR apruebe la semántica de cada tipo
de terminación y el volumen permita estimación estable.

## Decisión

`probar como challenger` para una fase de competing risks; no es el modelo
principal del MVP.
