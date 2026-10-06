# Selección analítica de los grupos del slide 6 — modelo B — Engineering

Creado: 2026-10-03T20:19:03.268544+00:00. Modelo: B: A + promoción + recontratación.

Reglas declaradas antes de correr:

- candidatas: combinaciones de 2 y 3 variables con cortes gruesos fijos, y árbol de riesgo de profundidad 3 y 4 ajustado en la última foto de entrenamiento de cada periodo
- grupos con < 300 personas por foto van a resto (nunca entra al top)
- eficiencia = Gini de la curva de concentración de salidas observadas ordenando grupos por riesgo estimado / Gini del ranking individual del modelo, en cada uno de los 4 periodos de prueba
- selección: entre combinaciones fijas a <= 2% de la mejor eficiencia media, menos variables, después menos grupos, después más estabilidad
- el árbol sólo gana si supera a la mejor combinación fija por más de 2%
- captura@25% y estabilidad son informativas

## Decisión

- Mejor eficiencia media de una combinación fija: 0.909.
- Dentro de la tolerancia: Antigüedad × Salidas en su equipo × Nivel.
- **Ganadora: Antigüedad × Salidas en su equipo × Nivel** (menos variables, después menos grupos y después más estabilidad entre las combinaciones a <= tolerancia de la mejor).

## Candidatas (orden por eficiencia media en los 4 periodos)

| Agrupación | Eficiencia | Eficiencia por periodo | Captura@25% grupos | Captura@25% individual | Grupos | % resto | Correlación de rangos | Top 5 = último periodo |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| Antigüedad × Salidas en su equipo × Nivel | 0.909 | 0.946, 0.920, 0.870, 0.897 | 39.5% | 42.7% | 20.0 | 5.2% | 1.00 | 93% |
| Antigüedad × Salidas en su equipo × Cambios de manager | 0.886 | 0.924, 0.886, 0.845, 0.892 | 39.2% | 42.7% | 22.5 | 1.2% | 0.99 | 73% |
| Antigüedad × Salidas en su equipo × Recontratación | 0.879 | 0.890, 0.834, 0.825, 0.965 | 38.2% | 42.7% | 17.5 | 3.5% | 0.99 | 87% |
| Antigüedad × Salidas en su equipo × Reportes | 0.859 | 0.871, 0.851, 0.827, 0.886 | 39.3% | 42.7% | 16.5 | 2.7% | 0.99 | 87% |
| Antigüedad × Nivel × Cambios de manager | 0.853 | 0.869, 0.854, 0.849, 0.840 | 39.3% | 42.7% | 20.2 | 4.8% | 0.99 | 100% |
| Árbol de riesgo, profundidad 4 | 0.850 | 0.907, 0.825, 0.801, 0.867 | 38.8% | 42.7% | 14.2 | 0.4% | 0.98 | 27% |
| Antigüedad × Salidas en su equipo | 0.842 | 0.882, 0.841, 0.764, 0.878 | 38.5% | 42.7% | 12.0 | 0.0% | 0.98 | 93% |
| Antigüedad × Cambios de manager × Recontratación | 0.840 | 0.850, 0.793, 0.824, 0.893 | 37.4% | 42.7% | 18.5 | 3.1% | 0.99 | 67% |
| Antigüedad × Nivel × Recontratación | 0.838 | 0.869, 0.805, 0.840, 0.838 | 39.0% | 42.7% | 19.8 | 2.6% | 0.99 | 100% |
| Antigüedad × Salidas en su equipo × Última promoción | 0.830 | 0.876, 0.855, 0.751, 0.840 | 38.0% | 42.7% | 23.0 | 2.8% | 0.99 | 87% |
| Antigüedad × Nivel | 0.818 | 0.860, 0.796, 0.816, 0.798 | 38.3% | 42.7% | 12.8 | 2.0% | 0.99 | 80% |
| Antigüedad × Nivel × Última promoción | 0.809 | 0.840, 0.801, 0.795, 0.802 | 38.8% | 42.7% | 23.5 | 5.3% | 0.99 | 87% |
| Antigüedad × Reportes × Cambios de manager | 0.808 | 0.822, 0.783, 0.793, 0.834 | 37.9% | 42.7% | 17.0 | 2.0% | 0.97 | 100% |
| Antigüedad × Reportes × Nivel | 0.808 | 0.835, 0.788, 0.818, 0.790 | 38.3% | 42.7% | 15.2 | 5.0% | 0.99 | 80% |
| Antigüedad × Reportes × Recontratación | 0.804 | 0.817, 0.743, 0.804, 0.853 | 37.6% | 42.7% | 15.5 | 1.7% | 0.98 | 93% |
| Antigüedad × Cambios de manager | 0.798 | 0.827, 0.785, 0.760, 0.822 | 37.2% | 42.7% | 12.0 | 0.0% | 0.99 | 100% |
| Antigüedad × Recontratación | 0.793 | 0.820, 0.723, 0.769, 0.860 | 37.0% | 42.7% | 11.0 | 0.4% | 0.98 | 93% |
| Antigüedad × Cambios de manager × Última promoción | 0.789 | 0.852, 0.787, 0.738, 0.780 | 37.6% | 42.7% | 24.0 | 1.8% | 0.99 | 80% |
| Salidas en su equipo × Nivel × Última promoción | 0.787 | 0.809, 0.787, 0.795, 0.757 | 38.5% | 42.7% | 15.8 | 1.5% | 0.99 | 100% |
| Antigüedad × Última promoción × Recontratación | 0.779 | 0.802, 0.710, 0.752, 0.854 | 37.3% | 42.7% | 20.8 | 3.5% | 0.98 | 80% |
| Antigüedad × Reportes | 0.760 | 0.782, 0.734, 0.738, 0.787 | 37.5% | 42.7% | 9.5 | 1.1% | 0.98 | 100% |
| Salidas en su equipo × Nivel × Cambios de manager | 0.756 | 0.763, 0.818, 0.778, 0.667 | 36.2% | 42.7% | 11.0 | 0.5% | 1.00 | 100% |
| Antigüedad × Reportes × Última promoción | 0.756 | 0.778, 0.740, 0.724, 0.781 | 37.9% | 42.7% | 19.2 | 3.6% | 0.99 | 100% |
| Árbol de riesgo, profundidad 3 | 0.745 | 0.775, 0.699, 0.696, 0.812 | 36.6% | 42.7% | 7.8 | 0.2% | 0.94 | 53% |
| Salidas en su equipo × Reportes × Nivel | 0.742 | 0.735, 0.745, 0.764, 0.723 | 35.8% | 42.7% | 9.0 | 0.8% | 0.99 | 100% |
| Salidas en su equipo × Nivel × Recontratación | 0.739 | 0.753, 0.736, 0.770, 0.696 | 36.9% | 42.7% | 10.0 | 1.1% | 0.99 | 100% |
| Antigüedad × Última promoción | 0.735 | 0.790, 0.724, 0.663, 0.762 | 37.5% | 42.7% | 13.2 | 0.3% | 0.96 | 93% |
| Salidas en su equipo × Nivel | 0.704 | 0.731, 0.742, 0.731, 0.611 | 35.0% | 42.7% | 6.0 | 0.0% | 1.00 | 100% |
| Nivel × Cambios de manager × Última promoción | 0.702 | 0.744, 0.711, 0.723, 0.632 | 36.2% | 42.7% | 15.5 | 1.5% | 0.98 | 80% |
| Reportes × Nivel × Última promoción | 0.675 | 0.684, 0.638, 0.745, 0.634 | 35.8% | 42.7% | 13.2 | 1.4% | 0.98 | 100% |
| Nivel × Última promoción × Recontratación | 0.660 | 0.673, 0.614, 0.720, 0.634 | 35.3% | 42.7% | 14.5 | 1.8% | 0.99 | 87% |
| Nivel × Última promoción | 0.658 | 0.701, 0.638, 0.686, 0.608 | 35.2% | 42.7% | 9.0 | 0.0% | 0.99 | 100% |
| Nivel × Cambios de manager × Recontratación | 0.651 | 0.662, 0.656, 0.728, 0.558 | 35.2% | 42.7% | 9.8 | 1.4% | 0.99 | 100% |
| Salidas en su equipo × Reportes × Cambios de manager | 0.646 | 0.581, 0.666, 0.670, 0.666 | 35.9% | 42.7% | 8.0 | 0.0% | 0.99 | 100% |
| Salidas en su equipo × Reportes × Última promoción | 0.637 | 0.626, 0.634, 0.636, 0.650 | 36.1% | 42.7% | 12.0 | 0.0% | 1.00 | 100% |
| Salidas en su equipo × Reportes × Recontratación | 0.634 | 0.578, 0.603, 0.650, 0.706 | 36.7% | 42.7% | 7.0 | 0.4% | 1.00 | 100% |
| Reportes × Nivel × Cambios de manager | 0.625 | 0.606, 0.661, 0.677, 0.556 | 33.3% | 42.7% | 9.0 | 0.8% | 0.99 | 100% |
| Nivel × Cambios de manager | 0.619 | 0.620, 0.666, 0.668, 0.524 | 33.3% | 42.7% | 6.0 | 0.0% | 1.00 | 100% |
| Reportes × Nivel × Recontratación | 0.616 | 0.627, 0.577, 0.696, 0.566 | 33.8% | 42.7% | 7.5 | 2.0% | 1.00 | 100% |
| Nivel × Recontratación | 0.595 | 0.628, 0.565, 0.680, 0.507 | 33.8% | 42.7% | 6.0 | 0.0% | 0.96 | 93% |
| Salidas en su equipo × Cambios de manager × Recontratación | 0.586 | 0.540, 0.600, 0.574, 0.631 | 36.0% | 42.7% | 8.0 | 0.0% | 0.98 | 100% |
| Reportes × Nivel | 0.577 | 0.586, 0.578, 0.626, 0.517 | 32.1% | 42.7% | 5.0 | 0.2% | 1.00 | 100% |
| Salidas en su equipo × Reportes | 0.563 | 0.528, 0.571, 0.563, 0.591 | 34.8% | 42.7% | 4.0 | 0.0% | 1.00 | 80% |
| Salidas en su equipo × Cambios de manager × Última promoción | 0.561 | 0.526, 0.623, 0.546, 0.548 | 36.1% | 42.7% | 11.8 | 0.2% | 0.97 | 87% |
| Salidas en su equipo × Última promoción × Recontratación | 0.543 | 0.514, 0.541, 0.511, 0.606 | 36.5% | 42.7% | 11.0 | 0.6% | 0.99 | 100% |
| Reportes × Cambios de manager × Recontratación | 0.538 | 0.453, 0.506, 0.586, 0.609 | 33.6% | 42.7% | 7.0 | 0.4% | 1.00 | 100% |
| Reportes × Cambios de manager × Última promoción | 0.534 | 0.500, 0.514, 0.575, 0.548 | 33.2% | 42.7% | 11.8 | 0.2% | 0.99 | 100% |
| Salidas en su equipo × Cambios de manager | 0.504 | 0.473, 0.569, 0.491, 0.481 | 35.3% | 42.7% | 4.0 | 0.0% | 1.00 | 80% |
| Reportes × Última promoción × Recontratación | 0.490 | 0.448, 0.417, 0.523, 0.572 | 32.1% | 42.7% | 9.0 | 1.8% | 0.98 | 100% |
| Salidas en su equipo × Recontratación | 0.489 | 0.462, 0.487, 0.458, 0.549 | 35.5% | 42.7% | 4.0 | 0.0% | 1.00 | 80% |
| Salidas en su equipo × Última promoción | 0.482 | 0.481, 0.520, 0.450, 0.477 | 35.0% | 42.7% | 6.0 | 0.0% | 0.98 | 100% |
| Reportes × Cambios de manager | 0.453 | 0.371, 0.497, 0.483, 0.461 | 31.8% | 42.7% | 4.0 | 0.0% | 1.00 | 80% |
| Reportes × Última promoción | 0.451 | 0.463, 0.411, 0.474, 0.456 | 31.8% | 42.7% | 6.0 | 0.0% | 1.00 | 100% |
| Reportes × Recontratación | 0.442 | 0.379, 0.356, 0.496, 0.538 | 31.2% | 42.7% | 4.0 | 0.0% | 1.00 | 80% |
| Cambios de manager × Última promoción × Recontratación | 0.393 | 0.306, 0.415, 0.418, 0.432 | 32.3% | 42.7% | 11.0 | 0.6% | 0.98 | 100% |
| Cambios de manager × Recontratación | 0.360 | 0.290, 0.356, 0.375, 0.417 | 32.1% | 42.7% | 4.0 | 0.0% | 1.00 | 80% |
| Cambios de manager × Última promoción | 0.327 | 0.249, 0.409, 0.340, 0.311 | 30.4% | 42.7% | 6.0 | 0.0% | 0.89 | 100% |
| Última promoción × Recontratación | 0.265 | 0.248, 0.221, 0.247, 0.343 | 29.6% | 42.7% | 6.0 | 0.0% | 0.98 | 100% |

## Top 5 de la ganadora, foto 2026-07-26

37,221 personas; riesgo medio estimado a seis meses 2.79%. 22 grupos elegibles; 1,406 personas en resto.

| Grupo | Personas | % población | Riesgo 6m % | × promedio | % salidas esperadas | Último periodo: estimado % | observado % |
|---|---:|---:|---:|---:|---:|---:|---:|
| 3-5 años · con salidas · entrada | 1310 | 3.5 | 6.18 | 2.21 | 7.8 | 6.95 | 5.50 |
| 2-3 años · con salidas · entrada | 572 | 1.5 | 5.68 | 2.03 | 3.1 | 6.46 | 4.80 |
| 5-10 años · con salidas · entrada | 1028 | 2.8 | 4.94 | 1.77 | 4.9 | 5.35 | 3.84 |
| 3-5 años · con salidas · medio | 478 | 1.3 | 4.45 | 1.59 | 2.0 | 4.71 | 5.43 |
| 3-5 años · sin salidas · entrada | 3807 | 10.2 | 4.06 | 1.45 | 14.8 | 4.61 | 3.94 |

El top 5 reúne el 19.3% de las personas y el 32.7% de las salidas esperadas; el mismo % de personas con mayor riesgo individual reúne el 35.9%.
Último periodo observado: top 5 31.3% de las salidas; ranking individual 31.9%.

## Todos los grupos elegibles de la ganadora (referencia)

| Grupo | Personas | % población | Riesgo 6m % | × promedio | % salidas esperadas | Último periodo: estimado % | observado % |
|---|---:|---:|---:|---:|---:|---:|---:|
| 3-5 años · con salidas · entrada | 1310 | 3.5 | 6.18 | 2.21 | 7.8 | 6.95 | 5.50 |
| 2-3 años · con salidas · entrada | 572 | 1.5 | 5.68 | 2.03 | 3.1 | 6.46 | 4.80 |
| 5-10 años · con salidas · entrada | 1028 | 2.8 | 4.94 | 1.77 | 4.9 | 5.35 | 3.84 |
| 3-5 años · con salidas · medio | 478 | 1.3 | 4.45 | 1.59 | 2.0 | 4.71 | 5.43 |
| 3-5 años · sin salidas · entrada | 3807 | 10.2 | 4.06 | 1.45 | 14.8 | 4.61 | 3.94 |
| <1 año · con salidas · medio | 337 | 0.9 | 3.92 | 1.40 | 1.3 | 3.64 | 4.23 |
| 2-3 años · sin salidas · entrada | 1397 | 3.8 | 3.76 | 1.34 | 5.0 | 4.21 | 3.65 |
| 1-2 años · con salidas · entrada | 849 | 2.3 | 3.74 | 1.34 | 3.0 | 4.21 | 3.34 |
| 5-10 años · con salidas · medio | 1108 | 3.0 | 3.29 | 1.18 | 3.5 | 3.53 | 5.00 |
| 5-10 años · sin salidas · entrada | 3215 | 8.6 | 3.21 | 1.15 | 9.9 | 3.51 | 3.59 |
| <1 año · con salidas · entrada | 1179 | 3.2 | 3.05 | 1.09 | 3.5 | 3.32 | 2.93 |
| 3-5 años · sin salidas · medio | 1319 | 3.5 | 2.88 | 1.03 | 3.7 | 3.14 | 3.32 |
| 1-2 años · sin salidas · medio | 421 | 1.1 | 2.63 | 0.94 | 1.1 | 2.82 | 4.31 |
| <1 año · sin salidas · medio | 733 | 2.0 | 2.58 | 0.92 | 1.8 | 2.30 | 2.94 |
| 1-2 años · sin salidas · entrada | 2366 | 6.4 | 2.46 | 0.88 | 5.6 | 2.74 | 2.88 |
| 5-10 años · sin salidas · medio | 3886 | 10.4 | 2.18 | 0.78 | 8.1 | 2.37 | 2.20 |
| 10+ años · con salidas · medio | 889 | 2.4 | 2.09 | 0.75 | 1.8 | 2.21 | 2.92 |
| 5-10 años · sin salidas · alto | 305 | 0.8 | 1.94 | 0.70 | 0.6 | 2.04 | — |
| <1 año · sin salidas · entrada | 2756 | 7.4 | 1.93 | 0.69 | 5.1 | 2.15 | 2.29 |
| 10+ años · con salidas · alto | 654 | 1.8 | 1.57 | 0.56 | 1.0 | 1.81 | 1.18 |
| 10+ años · sin salidas · medio | 4376 | 11.8 | 1.34 | 0.48 | 5.7 | 1.47 | 1.34 |
| 10+ años · sin salidas · alto | 2830 | 7.6 | 1.05 | 0.38 | 2.9 | 1.15 | 1.39 |
