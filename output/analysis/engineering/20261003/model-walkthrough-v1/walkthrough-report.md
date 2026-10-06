# Cómo calcula el riesgo el modelo B — Engineering

Creado: 2026-10-03T22:55:11.389111+00:00. Modelo de la 4.ª prueba (entrenado antes de 2025-08-24).

## Paso 1 · Empleados ficticios, foto 2026-01-25 (h mensual %)

Personas inventadas para ilustrar el cálculo; su riesgo sale del modelo real.

| Nombre | Grupo | Descripción | feb | mar | abr | may | jun | jul | R6 % |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Fernando | I | 3-5 años, nivel 8, 2+ salidas en su equipo, 1 cambio de manager, sin reportes, sin promoción registrada | 2.14 | 3.56 | 2.33 | 1.71 | 4.21 | 2.61 | 15.48 |
| Julia | I | 3-5 años, nivel 7, 1 salida en su equipo, sin cambio de manager, sin reportes, promoción hace 1-2 años | 0.83 | 1.40 | 0.91 | 0.67 | 1.65 | 1.02 | 6.31 |
| Leah | II | 5-10 años, nivel 7, sin salidas en su equipo, 1 cambio de manager, sin reportes, promoción hace 3+ años | 0.58 | 0.98 | 0.64 | 0.47 | 1.16 | 0.71 | 4.45 |
| Ana | II | 5-10 años, nivel 8, sin salidas en su equipo, sin cambio de manager, sin reportes, promoción hace 2-3 años | 0.65 | 1.08 | 0.70 | 0.52 | 1.28 | 0.79 | 4.92 |
| Carlos | III | 10+ años, nivel 6, sin salidas en su equipo, sin cambio de manager, 1-5 reportes, promoción hace 3+ años | 0.18 | 0.30 | 0.19 | 0.14 | 0.35 | 0.22 | 1.37 |
| Sofía | III | 10+ años, nivel 5, sin salidas en su equipo, sin cambio de manager, 6+ reportes, promoción hace <1 año | 0.10 | 0.17 | 0.11 | 0.08 | 0.21 | 0.13 | 0.80 |

## Paso 2 · Grupos (promedio de h por mes %)

| Grupo | Personas | feb | mar | abr | may | jun | jul | R6 con la fórmula % | Promedio de R6 % | Real % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| I 3-5 años · con salidas · entrada | 1373 | 0.96 | 1.60 | 1.04 | 0.77 | 1.90 | 1.17 | 7.22 | 7.19 | 5.54 |
| II 5-10 años · sin salidas · entrada | 2515 | 0.50 | 0.84 | 0.55 | 0.40 | 0.99 | 0.61 | 3.83 | 3.83 | 4.02 |
| III 10+ años · sin salidas · medio | 3972 | 0.21 | 0.35 | 0.23 | 0.17 | 0.41 | 0.25 | 1.61 | 1.60 | 1.54 |
| Engineering  | 34963 | 0.44 | 0.73 | 0.47 | 0.35 | 0.87 | 0.53 | 3.34 | 3.33 | 3.41 |

## Paso 3 · Pasos del plano, foto 2026-07-26 (37,221 personas)

- todos: 1 grupos, eficiencia media 0.000, mayor riesgo 2.79%
- antiguedad: 6 grupos, eficiencia media 0.732, mayor riesgo 4.21%
- salidas: 12 grupos, eficiencia media 0.842, mayor riesgo 5.64%
- nivel: 22 grupos, eficiencia media 0.909, mayor riesgo 6.18%
- Árbol (mejor): eficiencia 0.850; 58 candidatas.
