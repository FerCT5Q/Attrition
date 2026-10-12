# Modelo C sin QVoice frente a B

**Resultado: C no demuestra mejora suficiente bajo la regla.**

Modo de entrega: `presentation`. Ejecución del 8 de octubre de 2026; datos con frontera de conocimiento del 7 de septiembre de 2026.

## Resumen

- El C experimental archivado contiene 17 términos y utiliza hazard mensual cloglog, sin calibración posterior. Es la última especificación evaluada, con corte de entrenamiento 2025-08-01.
- La comparación requirió 164 evaluaciones hazard solicitadas; hubo compresión exacta y reutilización de ajustes. No se conserva un conteo completo de ajustes nuevos frente a recuperados de memoria.
- La ejecución optimizada hasta su cierre consumió 35.6 minutos, incluida la selección adicional detenida. La comparación completa y la carga ocuparon aproximadamente 31.6 minutos. Un intento previo se conserva en `model-c-v1/interrupted.json`.
- B se conserva como referencia. C + QVoice no se ha iniciado.
- Las métricas siguientes evalúan el proceso de selección y reajuste de C en cada fecha; las listas varían. Se omitió el reajuste adicional a septiembre de 2026 después de que C no superó la regla de promoción. No se publican pronósticos actuales.

## Comparación global

Promedio simple de cuatro periodos externos de seis snapshots. PR-AUC se informa como average precision. Las pérdidas se escalan por 1000 para que sean legibles. Las cifras visibles se redondean; los cambios relativos se calculan sin redondear.

| Métrica | B | C | Lectura |
|---|---:|---:|---|
| Log-loss × 1000 | 132.4 | 131.9 | 0.4% mejora |
| Brier × 1000 | 29.2 | 29.1 | 0.1% mejora |
| PR-AUC (%) | 5.2 | 5.3 | 2.3% mejora |
| Lift del 10% superior | 2 | 2.1 | 2.3% mejora |
| Error global (pp) | 0.2 | 0.2 | 2.4% mejora |
| Error del 20% superior propio (pp) | 0.4 | 0.5 | 29.5% deterioro |

![Comparación temporal de B y C](comparacion-b-c.png)

Log-loss penaliza probabilidades equivocadas; Brier mide error cuadrático. Menor es mejor en ambos. PR-AUC y lift evalúan concentración de salidas; mayor es mejor. Error en pp compara riesgo medio predicho con frecuencia observada.

## Lo que ocurre dentro de los grupos

Cada árbol se aprende antes del periodo evaluado. Las columnas de error B y C usan exactamente las mismas personas y reglas de C.

| Snapshots de predicción | Error de B en grupos (pp) | Error de C en grupos (pp) | Error B en grupo alto (pp) | Error C en grupo alto (pp) | Cobertura del grupo alto | Salidas capturadas |
|---|---:|---:|---:|---:|---:|---:|
| 2024-02-18 a 2024-07-21 | 0.4 | 0.5 | <0.1 | 0.5 | 24.7% | 40.9% |
| 2024-08-25 a 2025-01-26 | 0.3 | 0.4 | 0.4 | 0.2 | 22.8% | 35.8% |
| 2025-02-23 a 2025-07-27 | 0.3 | 0.3 | 0.6 | 0.1 | 31.9% | 45.7% |
| 2025-08-24 a 2026-01-25 | 0.3 | 0.3 | 0.6 | 0.6 | 28.5% | 39.8% |

El grupo alto suma hojas completas desde el riesgo mayor hasta cubrir al menos 20% en entrenamiento; su tamaño futuro puede variar. No equivale siempre al quintil exacto. Las tasas agregadas cuentan persona-snapshots; una persona o salida puede contribuir a varias ventanas solapadas.

### Capacidad de ordenar grupos, comparando los árboles propios

| Periodo | Lift10 de grupos B | Lift10 de grupos C |
|---|---:|---:|
| 2024-02 a 2024-07 | 2.1 | 2 |
| 2024-08 a 2025-01 | 1.5 | 1.6 |
| 2025-02 a 2025-07 | 1.7 | 1.7 |
| 2025-08 a 2026-01 | 1.5 | 1.5 |

Se ponderan los empates de las hojas para comparar a igual 10% de población. Es una métrica de ranking, no una instrucción para dividir un grupo operativo.

### Grupos del último periodo evaluado

Reglas aprendidas en la foto 2025-06-29. Predicciones desde 2025-08-24 hasta 2026-01-25; seguimiento de la última foto hasta 2026-07-25. Son las reglas del último backtest y del modelo experimental archivado.

| Grupo | Regla | Personas medias por foto | Observado R6 | B estimado | C estimado |
|---|---|---:|---:|---:|---:|
| G5 · alto | Antigüedad en Qualcomm ≠ 10+ años; Antigüedad en Qualcomm = 3-5 años; Nivel ≠ 8 - Assoc & Int/Eng | 6216.5 | 4% | 4.2% | 4% |
| G6 · alto | Antigüedad en Qualcomm ≠ 10+ años; Antigüedad en Qualcomm = 3-5 años; Nivel = 8 - Assoc & Int/Eng | 1238.8 | 5.1% | 8.5% | 8.7% |
| G7 | Antigüedad en Qualcomm ≠ 10+ años; Antigüedad en Qualcomm ≠ 3-5 años; Antigüedad en Qualcomm ≠ 2-3 años | 15929.5 | 3% | 3% | 2.8% |
| G8 · alto | Antigüedad en Qualcomm ≠ 10+ años; Antigüedad en Qualcomm ≠ 3-5 años; Antigüedad en Qualcomm = 2-3 años | 2203.8 | 4.1% | 4.6% | 4.7% |
| G11 | Antigüedad en Qualcomm = 10+ años; Reportes directos ≠ 6+; Salidas previas del equipo en 12 meses ≠ 1 | 5908.3 | 1.5% | 1.6% | 1.4% |
| G12 | Antigüedad en Qualcomm = 10+ años; Reportes directos ≠ 6+; Salidas previas del equipo en 12 meses = 1 | 839.5 | 2.2% | 1.9% | 2.2% |
| G13 | Antigüedad en Qualcomm = 10+ años; Reportes directos = 6+; Capa organizativa almacenada ≠ <=6 | 921.7 | —% | 0.9% | 0.9% |
| G14 | Antigüedad en Qualcomm = 10+ años; Reportes directos = 6+; Capa organizativa almacenada = <=6 | 598.2 | —% | 0.8% | 0.6% |

Una tasa observada no publicable se muestra como —; se exigen al menos 30 personas por foto y 30 personas distintas con salida en las ventanas del grupo.

## Cómo se seleccionó C

1. Se revisaron 21 términos candidatos: 19 variables/representaciones y dos interacciones. Todas las variables base de B podían salir.
2. Un filtro L1 supervisado, ajustado sólo con el pasado, produjo conjuntos de variables. También compitieron B y el conjunto completo.
3. Cada conjunto se reajustó con cloglog y tres intensidades L2. Dos validaciones internas con etiquetas R6 maduras eligieron la combinación.
4. Se priorizó log-loss, con restricciones de Brier y ranking; entre resultados próximos se eligió la lista más corta.
5. Se reajustó antes de cada fecha externa y se evaluaron los seis snapshots siguientes. Las reglas de grupos también se congelaron antes.

Se descartaron 21 combinaciones de variables y L2 que no convergieron en al menos una validación interna. Sus registros permanecen en el recorrido; no se consideraron resultados válidos.

No se usó PCA ni se buscaron todas las combinaciones posibles. L1 selecciona utilizando la salida, mientras PCA busca variación entre predictores. Mantener variables originales facilita explicar los grupos.

| Origen | Términos de C | L2 | Variables seleccionadas |
|---|---:|---:|---|
| 2024-02-01 | 21 | 10 | Nivel, Antigüedad en Qualcomm, Mes del calendario, Cambios de manager en 12 meses, Salidas previas del equipo en 12 meses, Reportes directos, Tiempo desde promoción, Recontratación (proxy), Nivel × antigüedad, Antigüedad × cambios de manager, Experiencia previa, Tiempo en el nivel, Salida del manager en 6 meses, Movimientos IOS en 12 meses, Capa organizativa almacenada, Modalidad de trabajo, Región, Banda de comp ratio almacenado, Prefijo de compensation grade, Adquisición registrada, Transferencia registrada en 12 meses |
| 2024-08-01 | 12 | 10 | Nivel, Antigüedad en Qualcomm, Mes del calendario, Cambios de manager en 12 meses, Reportes directos, Tiempo desde promoción, Nivel × antigüedad, Experiencia previa, Tiempo en el nivel, Región, Prefijo de compensation grade, Adquisición registrada |
| 2025-02-01 | 15 | 10 | Nivel, Antigüedad en Qualcomm, Mes del calendario, Cambios de manager en 12 meses, Salidas previas del equipo en 12 meses, Reportes directos, Tiempo desde promoción, Recontratación (proxy), Nivel × antigüedad, Experiencia previa, Tiempo en el nivel, Capa organizativa almacenada, Región, Banda de comp ratio almacenado, Adquisición registrada |
| 2025-08-01 | 17 | 0.1 | Nivel, Antigüedad en Qualcomm, Mes del calendario, Cambios de manager en 12 meses, Salidas previas del equipo en 12 meses, Reportes directos, Tiempo desde promoción, Recontratación (proxy), Nivel × antigüedad, Experiencia previa, Tiempo en el nivel, Movimientos IOS en 12 meses, Capa organizativa almacenada, Región, Banda de comp ratio almacenado, Adquisición registrada, Transferencia registrada en 12 meses |

### Variables del modelo experimental archivado

- Nivel (`level_grouped`).
- Antigüedad en Qualcomm (`tenure_playbook_band`).
- Mes del calendario (`calendar_month`).
- Cambios de manager en 12 meses (`manager_changes_12m`).
- Salidas previas del equipo en 12 meses (`team_exits_12m`).
- Reportes directos (`direct_reports_band`).
- Tiempo desde promoción (`time_since_promotion_band`).
- Recontratación (proxy) (`rehire`).
- Nivel × antigüedad (`level_x_tenure`).
- Experiencia previa (`prior_experience_band`).
- Tiempo en el nivel (`time_at_level_band`).
- Movimientos IOS en 12 meses (`ios_12m`).
- Capa organizativa almacenada (`layers_band`).
- Región (`region`).
- Banda de comp ratio almacenado (`comp_ratio_band`).
- Adquisición registrada (`acquisition_recorded`).
- Transferencia registrada en 12 meses (`transfer_12m`).

## Artefacto conservado

Se conserva la última especificación que se evaluó fuera de muestra: origen **2025-08-01**, con etiquetas mensuales conocidas hasta **2025-07-27**.

La comparación quedó completa. Se detuvo la selección adicional destinada al reajuste con datos hasta septiembre de 2026 al comprobar que C no superaba B bajo la regla prevista. Este cambio de cierre está registrado en `finalization.json`; no cambia ninguno de los cuatro resultados externos.

El árbol resume los riesgos del modelo con R² de 54.1% en su foto de entrenamiento. Ese R² mide fidelidad del resumen, no exactitud frente a salidas.

## Regla de decisión e incertidumbre

| Comprobación previamente definida | Cumple |
|---|---|
| Log-loss mejora al menos 0,5% | No |
| Brier no empeora | Sí |
| PR-AUC mejora al menos 2% | Sí |
| Lift10 mejora al menos 2% | Sí |
| PR-AUC gana en al menos 3 de 4 periodos | Sí |
| Lift10 gana en al menos 3 de 4 periodos | No |
| Error de grupos no empeora más de 0,1 pp | Sí |
| Error del grupo alto no empeora más de 0,1 pp | Sí |
| IC95 de diferencia de log-loss queda por debajo de cero | Sí |

Diferencia pareada C − B en log-loss × 1000: -0.5; IC95 [-0.7, -0.3]. Negativo favorece C. Bootstrap por persona, 500 réplicas; las ventanas de cada persona permanecen juntas.

Este intervalo reúne todos los persona-snapshots y pondera por su cantidad; la tabla principal da el mismo peso a cada periodo. El árbol usa la última foto del entrenamiento mensual, que tiene un intervalo de salida ya observado; puede ser anterior a la última foto disponible sin etiqueta.

## Alcance y límites

- Evaluación anidada retrospectiva; estos años ya se habían explorado. No es una confirmación prospectiva independiente.
- IOS usa fecha efectiva; no se conoce la fecha de publicación de cada evento. Los snapshots pueden contener revisiones históricas.
- Las tasas de salida voluntaria son etiquetas binarias de población activa; otras salidas cuentan como no voluntarias. No es un modelo de riesgos competitivos.
- Los intervalos entre snapshots fiscales no tienen siempre la misma duración; se conserva la convención mensual de B.
- Candidatos limitados al inventario y representaciones documentadas; no se afirma óptimo global entre todas las combinaciones posibles.
- B y C utilizan la misma población y el mismo frame corregido para exigir fecha de registro previa en salidas usadas como features; las cifras pueden diferir del B publicado anteriormente.
- El bootstrap mantiene fijos los modelos y grupos entrenados; no reentrena la selección en cada réplica y no cubre toda la incertidumbre de selección o de cambios entre años.
- Regiones, antigüedad y adquisición describen contexto; sus coeficientes no identifican causas. No se debe asumir que cambiar una variable reducirá attrition en esa magnitud.
- Capas y comp ratio conservan significado de campo almacenado. Se probaron representaciones limitadas de varios conceptos y se documentaron las exclusiones; no se demuestra un óptimo entre las 43 variables.
- Las reglas permiten orientar revisiones de carrera, movilidad y continuidad del equipo, con contraste de contexto antes de actuar. No se publicaron puntuaciones individuales.

## Trazabilidad

- [Resultados y métricas de cálculo](results.json).
- [Configuración congelada](frozen-config.json).
- [Modelo C entrenado](trained-model/model-c.json).
- [Reglas de grupos](trained-model/groups.json).
- [Manifiesto de fuentes y privacidad](manifest.json).
- Inventario completo: `config/engineering_model_c_inventory_20261008.json`.
- Consulta guardada: `queries/profiles/engineering_model_c_person_month_20261008.sql`.
- Evidencia de entradas: `input-evidence/`; recorrido de selección y cortes temporales: `selection/`.
- Autorización: `config/attrition_model_in_memory_training_authorization_20261001.json`. Sin filas, llaves temporales, scores personales ni compensación exacta persistidos.

## Verificación

Pasaron 224 comprobaciones de artefactos, fechas, cohortes, privacidad, fórmulas y exportación, además de las pruebas sintéticas adjuntas.
