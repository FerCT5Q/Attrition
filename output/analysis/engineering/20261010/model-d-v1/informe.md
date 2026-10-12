# Modelo D: comparación final

**Modo:** `presentation`. Evaluación retrospectiva; etapa de selección.

CQ permanece elegido; D no supera la regla congelada.

| Modelo | Captura al 30% | Error grupo-mes pp | Log-loss ×1000 | PR-AUC % |
|---|---:|---:|---:|---:|
| C | 42.4 | 1.0 | 138.8 | 4.9 |
| CQ | 43.1 | 1.0 | 137.7 | 5.5 |
| C_updated | 42.7 | 1.0 | 138.8 | 4.9 |
| D | 42.8 | 1.0 | 137.6 | 5.4 |
| monthly_logit | 42.8 | 1.0 | 137.6 | 5.4 |
| RSF_Q | 43.1 | 1.1 | 137.5 | 5.4 |

La promoción se decidió con los mismos cortes interpretables de antigüedad, salidas del equipo y nivel. Las filas persona-snapshot y las puntuaciones individuales no se persistieron.

Ruta cumplida: ninguna. Diferencia D−CQ en captura al 30%: -0.3 pp; IC95 [-1.0, 0.4].

## Especificación seleccionada

La selección temporal eligió la misma representación en los dos periodos y
en el corte final: Q4 de Intent to Stay, Q12 de Intent to Stay y Career Goals.
El ajuste final usa L2 QVoice de 0.1 y 13 parámetros de corrección sobre C.

Ninguna de las señales históricas nuevas sobrevivió la selección: cambios de
manager 3/6 meses, salidas del equipo 3/6 meses y recencia, tamaño del equipo
del manager e intensidad por personas-mes quedaron fuera. Esto indica que no
aportaron mejora temporal adicional una vez incluidos C y QVoice; no implica
ausencia de asociación descriptiva.

## Controles y pruebas

- CQ archivado se reprodujo con tolerancia de 1e-8.
- Los artefactos D y RSF se reprodujeron tras serialización.
- C, CQ y RSF anteriores conservaron exactamente sus hashes.
- Pasaron 31 pruebas focalizadas de D, C y QVoice.
- La verificación independiente está en `verification.json` y el log de tests
  en `model-tests.txt`.

## Límites

- QVoice sólo aporta dos waves anuales; las interacciones siguen siendo evidencia retrospectiva.
- La calibración por grupo quedó en identidad porque no existen tres series temporales fuera de ajuste del nuevo D.
- El bosque se comparó sin calibración adicional y su explicación usa los mismos grupos comunes.
