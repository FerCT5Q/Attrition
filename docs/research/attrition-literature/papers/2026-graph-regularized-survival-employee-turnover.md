# Graph-Regularized Survival Learning with Optimal Transport for Individual Employee Turnover Forecasting

## Ficha

- Año: 2026
- Revista: Mathematics
- DOI: `10.3390/math14152747`
- URL: https://doi.org/10.3390/math14152747
- Consultado: 2026-09-07
- Acceso: Open Access
- Etiquetas: `challenger`, `survival`, `machine-learning`, `future`

## Resumen

El paper propone combinar una función de riesgo tipo survival con optimal
transport y regularización de grafo para suavizar predicciones entre registros
similares. Reporta mejoras de C-index y expected calibration error en dos
benchmarks públicos.

La propia publicación advierte que los benchmarks son cross-sectional y no
contienen trayectorias longitudinales reales ni redes observadas de interacción.
Los tiempos y eventos se construyen como proxies, por lo que el resultado es
survival-inspired risk forecasting y no evidencia de dinámica longitudinal real.

## Aplicabilidad

Es una advertencia útil para Attrition: una mejora de C-index en IBM-HR o
datasets sintéticos no demuestra que el modelo sea mejor para nuestros
snapshots. Tampoco se debe interpretar la similitud como influencia causal de
pares.

## Decisión

`línea futura`; sólo considerar después de validar que el dataset usado sea
realmente longitudinal y que la complejidad aporte valor operativo.
