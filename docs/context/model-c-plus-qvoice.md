# C + QVoice: extensión independiente de C

Fecha: 8-oct-2026. Modo: `presentation`.

## Resultado y recomendación

**Extensión prometedora, con mejora media modesta; todavía no sustituye a C
bajo la regla declarada.** Se mantiene C como referencia y se conserva C + Q
sin calibración posterior como candidato para validación adicional. La
calibración escalar de seis meses apenas cambia sus resultados.

Se evaluaron fotos de agosto–diciembre de 2025 y enero–febrero de 2026,
cada una con seguimiento de seis meses, hasta agosto de 2026. Los dos
periodos reciben igual peso. Son ventanas retrospectivas con personas y
seguimientos parcialmente compartidos; no son una prueba prospectiva nueva.

| Métrica | C | C + Q sin calibración posterior |
|---|---:|---:|
| Captura al priorizar 30% | 42.4% | 43.1% |
| Log-loss R6 × 1000 | 138.8 | 137.7 |
| Brier R6 × 1000 | 30.7 | 30.7 |
| PR-AUC | 4.9% | 5.5% |
| Error medio por grupo prioritario | 1 pp | 1 pp |
| Promedio del mayor error de grupo publicable | 2.1 pp | 2.2 pp |

- La diferencia media de captura es **0.7 pp, IC95 [0.2, 1.1]** mediante
  500 remuestreos pareados por persona. Gana en 2025 y empata exactamente en
  enero–febrero de 2026; no hay derrota al 30%. No cumple la regla que exige
  mejora en ambos periodos. Se mantienen la regla y sus resultados.
- El log-loss baja 0.8% y el Brier 0.2% relativos. La pérdida mejora en ambos
  periodos. El error medio por grupo baja 2.3% relativo, una diferencia
  absoluta pequeña que queda oculta al redondear a un decimal.
- El error de calibración global aumenta 0.1 pp redondeado, y hay grupos
  concretos peor estimados. Una mejora promedio no garantiza precisión en
  todos los grupos de alto riesgo.
- Frente al control que usa sólo disponibilidad de respuestas, C + Q mejora
  la captura en 0.6 pp, IC95 [0.2, 1], y tiene menor log-loss.
- Al 20% y 40% los intervalos de mejora de captura incluyen cero. No se
  demuestra una ventaja en todas las capacidades.

Captura es la proporción de salidas observadas concentrada en el 30%
priorizado. La observación es persona-snapshot: una persona y su salida pueden
contribuir a varias ventanas. El mayor error sólo incluye grupos cuyo
observado es publicable; su cobertura está en el informe. No comparar estas
medias directamente con los cuatro periodos de selección original de C.

## Modelo y variables

C se restaura como offset fijo, con origen 1-ago-2025; no se reajusta su
hazard. Se ajusta una corrección aditiva QVoice con enlace cloglog y se
acumula el riesgo mensual mediante `R6 = 1 - producto(1 - h_m)`.

Se buscaron los 255 subconjuntos de ocho bloques, cinco tamaños PCA de
33 ítems y tres penalizaciones: **780 ajustes por corte, 2340 en total,
todos convergentes**. PCA no fue seleccionado. La selección utiliza Brier
mensual en los dos últimos intervalos completos anteriores a cada origen.

| Corte | Bloques seleccionados | L2 |
|---|---|---:|
| 1-ago-2025 | Q4, Q12, Career Goals, Engagement Q1/Q2/Q3 | 10 |
| 1-ene-2026 | Q4, Career Goals, Engagement Q1/Q2/Q3, Confidence Q13/Q17 | 1 |
| 7-sep-2026, artefacto final | Career Goals, promedio de 33 preguntas, Wellbeing Q8/Q10/Q11, Confidence Q13/Q17 | 0.1 |

Los resultados retrospectivos evalúan los modelos disponibles en cada
periodo. **La combinación final de septiembre todavía no tiene una
evaluación posterior a su ajuste.** Career aparece en los tres cortes y
conserva la limitación por diferencia de redacción de 2024.

En el artefacto final, Q4 y Q12 participan dentro del promedio de 33 preguntas
(M16 y M14, respectivamente), sin coeficientes propios. Mapping conservado
en `qvoice-model-b-calibrated-v1/preflight/source-metadata.json`.

La wave 2024 se usa sólo en 2025 y la wave 2025 sólo en 2026, según la política
anual aprobada. Se exige continuidad del episodio laboral; faltantes y
disponibilidad se modelan explícitamente. La fecha asignada por la política
no acredita la publicación real de la encuesta.

## Grupos e interpretación

Se conservan **antigüedad × salidas del equipo × nivel**, los cortes elegidos
para C (`C_Bcuts`). Hay 19–20 grupos elegibles según la foto y 20 en
enero–febrero de 2026; mínimo 300 personas por snapshot. Al priorizar 30% se
atienden aproximadamente nueve grupos por foto, incluyendo la fracción
uniforme del grupo del límite.

QVoice modifica las predicciones y puede cambiar el orden de esos grupos.
Esta ejecución no crea nuevos cortes por respuestas QVoice. Los grupos
describen asociaciones predictivas, no el efecto de acciones de retención.

## Calibración y límites

Se comparó identidad con `R6_cal = 1 - (1 - R6)^exp(a)` usando etiquetas
maduras y predicciones auxiliares anteriores a cada foto. En el primer
periodo faltan tres orígenes maduros y se usa identidad; en el segundo el
multiplicador C + Q queda muy próximo a uno. Su captura es idéntica a la
variante principal; no aporta una ventaja práctica clara.

Las columnas y L2 seleccionados al corte se reutilizan en los auxiliares:
la calibración no tiene selección completamente anidada. Las salidas del
periodo externo no se utilizan. Se conservan los límites de las fuentes de C
y el carácter retrospectivo de periodos ya explorados.

## Artefactos, conservación y fuentes

- Carpeta independiente:
  `output/analysis/engineering/20261008/model-c-plus-qvoice-v1/`.
- [Informe completo](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/informe.md).
- Modelos por periodo: `folds/`; artefacto final: `trained-model/model.json`.
- Evidencia: `results.json`, `analysis-checks.json`, `qvoice-input-checks.json`,
  `preservation.json` y `manifest.json`.
- Configuración: `config/engineering_model_c_qvoice_20261008.json`.
- Consulta: `queries/profiles/engineering_model_c_qvoice_person_month_20261008.sql`,
  ejecutada el 8-oct-2026; conocimiento hasta 7-sep-2026. Población:
  Engineering, Employee, Regular, activo, sin RF360.
- Duración del cálculo: 45.5 minutos, incluidos 4.5 de carga y enlace.
  El coste principal fueron las tres búsquedas exhaustivas. Cero reajustes
  del hazard C; se reutilizaron matrices y offsets.
- B, B + QVoice y C anteriores conservan sus hashes. No se guardaron filas,
  respuestas, identificadores ni puntuaciones individuales.
