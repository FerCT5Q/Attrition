# Random Survival Forests

## Ficha

- Autores: Hemant Ishwaran, Udaya B. Kogalur, Eugene H. Blackstone y Michael S. Lauer
- Año: 2008
- Revista: The Annals of Applied Statistics
- DOI: `10.1214/08-AOAS169`
- Texto abierto: https://arxiv.org/abs/0811.1645
- Consultado: 2026-09-07
- Acceso: Open Access/arXiv
- Etiquetas: `challenger`, `random-survival-forest`, `nonlinear`

## Resumen

El paper adapta random forests a datos censurados. Los árboles se dividen con
reglas que consideran supervivencia, y el ensemble produce estimaciones de
survival, cumulative hazard y medidas de mortalidad de ensemble.

El método puede capturar no linealidades e interacciones sin especificarlas a
mano. También discute missing data y criterios de importancia de variables,
aunque la interpretación debe tratarse con cuidado.

## Aplicabilidad a Attrition

Es un challenger razonable para descubrir si tenure, manager, team turnover,
engagement y compensación interactúan de forma no lineal. No sustituye al
modelo interpretable: se debe comparar calibración, lift, estabilidad y
capacidad de traducir señales en acciones.

## Decisión

`probar como challenger` después del hazard `cloglog` pooled.
