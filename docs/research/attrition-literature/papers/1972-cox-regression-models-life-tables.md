# Regression Models and Life-Tables

## Ficha

- Autor: D. R. Cox
- Año: 1972
- Revista: Journal of the Royal Statistical Society, Series B
- DOI: `10.1111/j.2517-6161.1972.tb00899.x`
- URL: https://doi.org/10.1111/j.2517-6161.1972.tb00899.x
- Consultado: 2026-09-07
- Acceso: abstract visible; texto completo normalmente cerrado
- Etiquetas: `fundacional`, `survival`, `hazard`

## Resumen

El paper introduce el modelo de riesgos proporcionales. El hazard se expresa
como una función base del tiempo multiplicada por una función de covariables.
La función base no necesita especificarse paramétricamente para estimar los
efectos relativos de las covariables.

La idea central es separar el cambio temporal del riesgo de la comparación
entre individuos o grupos. Esto permite modelar censura y distintos tiempos de
seguimiento sin convertir todo en una clasificación binaria única.

## Aplicabilidad a Attrition

Sirve como fundamento para un challenger Cox con covariables variables en el
tiempo y para explicar por qué el tiempo debe formar parte del modelo. El MVP
usará supervivencia discreta porque los snapshots son mensuales, pero la lógica
de hazard y baseline temporal permanece relevante.

## Limitaciones

El supuesto de riesgos proporcionales puede ser poco realista para managers,
tenure o cambios organizacionales. No resuelve por sí solo competing risks ni
descubre grupos accionables.

## Decisión

`referencia conceptual`; probar Cox como challenger después del modelo de
supervivencia discreta.
