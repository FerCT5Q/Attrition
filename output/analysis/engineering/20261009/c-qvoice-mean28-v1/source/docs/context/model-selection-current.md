# Selección vigente: C + Q y prueba del promedio

Actualización: 9-oct-2026. Modo `presentation`. Etapa: **selección de modelo**.

## Decisión vigente

**C + Q evaluado anteriormente es el candidato preferido.** La nueva
combinación fija con promedio de 28 no justifica sustituirlo: captura las
mismas salidas dentro del 30% priorizado y tiene algo más de error en las
probabilidades. C sigue documentado como referencia.

Esta nota actualiza la recomendación de selección después de la conversación
y de la nueva prueba. La nota histórica `model-c-qvoice-overlap.md` registró
una preferencia conservadora por C al exigir ganar en los dos periodos.
Ese resultado formal se conserva: CQ gana uno y empata otro. La decisión
actual considera magnitud, precisión y el objetivo de priorizar grupos;
no cuenta métricas correlacionadas como votos independientes.

## Resultado de la solicitud «C + Q + promedio»

Se probaron las mismas seis preguntas en las tres variantes nuevas:
Career Goals, Wellbeing (Q8/Q10/Q11) y Confidence (Q13/Q17). Las variantes
usan promedio 33, promedio 28 o ninguna media. El CQ histórico seleccionó
sus preguntas usando el pasado de cada origen; no es idéntico al conjunto
fijo de seis preguntas de esta prueba.

| Modelo | Captura al priorizar 30% ↑ | Cambio de error grupo-mes vs C ↓ | Log-loss × 1000 ↓ | PR-AUC ↑ |
|---|---:|---:|---:|---:|
| C | 42.4% | 0% | 138.8 | 4.9% |
| C + Q anterior | 43.1% | −2.3% | 137.7 | 5.5% |
| C + Q fijo + promedio 33 | 43.1% | +1.9% | 138.2 | 5.2% |
| C + Q fijo + promedio 28 | 43.1% | +1.7% | 138.2 | 5.2% |
| C + Q fijo sin promedio | 43.1% | +3.2% | 138.3 | 5.2% |

Un cambio negativo de error significa mejora. Las medias tienen igual peso
por periodo. La captura cuenta salidas en ventanas de seis meses con
seguimientos parcialmente compartidos; no representa salidas únicas de
una cohorte conjunta.

Frente a CQ anterior, la variante con promedio 28 aumenta 4.1% el error de
grupo-mes, 0.4% el log-loss y 0.1% el Brier. El cambio de log-loss por mil
es +0.5, IC95 [0.2, 0.8], condicionado a modelos y prioridades. El deterioro
es pequeño y no aporta captura adicional. Con adquisición registrada como
cuarto corte, CQ anterior captura 43.3% frente a 43.2% de media28 y mantiene
menor error de grupo-mes.

Sobre las mismas seis preguntas fijas, añadir media28 sí mejora 1.5% el
error frente a no usar promedio. Esa ganancia parcial no alcanza al CQ
anterior; no demuestra que cualquier promedio sea inútil.

## Promedio y colinealidad

Media28 = proporción de indicadores favorables de los 28 ítems restantes,
en las bandas del playbook. Se excluyen Q8, Q10, Q11, Q13 y Q17 del conjunto
original de 33; Career no está en esos 33. Q4/Q12 permanecen dentro del
promedio. Se exige validez de los 33 originales para conservar la misma
elegibilidad. No es un promedio de respuestas Likert.

El recálculo independiente dio cero discrepancias de fórmula, bandas o
elegibilidad en 375184 observaciones comparables. Son registros de fotos
mensuales, no personas distintas. El VIF máximo en casos completos baja
aproximadamente de 4.1 a 3.5 al retirar los componentes repetidos. Persisten
correlaciones entre preguntas y redundancias exactas de los indicadores de
ausencia; L2 permite ajustar, pero no identifica por sí sola sus efectos
separados sin penalización.

## Alcance temporal

- Población: Engineering, Employee, Regular, activo, sin RF360 por snapshot.
- Fotos evaluadas: agosto–diciembre de 2025 y enero–febrero de 2026.
- Outcome: salida voluntaria en los seis meses siguientes; último cierre
  observado del análisis: 22-ago-2026. Conocimiento hasta 7-sep-2026.
- Grupos comunes: antigüedad × salidas previas del equipo × nivel. Prioridad
  principal 30%; sensibilidades 20%, 40% y adquisición registrada como cuarto corte.
- QVoice 2024 para 2025 y QVoice 2025 para 2026, respetando episodio laboral.
- Los coeficientes y L2 se ajustaron antes de cada periodo. La definición
  fija se eligió tras explorar el histórico; es evaluación retrospectiva
  condicionada, sin independencia de toda la selección previa.

## Artefactos y reproducción

- [Tabla actualizada](../../output/analysis/engineering/20261009/c-qvoice-mean28-v1/tabla-comparativa.md).
- [Informe completo](../../output/analysis/engineering/20261009/c-qvoice-mean28-v1/informe.md).
- [Resultados agregados](../../output/analysis/engineering/20261009/c-qvoice-mean28-v1/results.json).
- [Decisión](../../output/analysis/engineering/20261009/c-qvoice-mean28-v1/selection-decision.json).
- [Verificación y preservación](../../output/analysis/engineering/20261009/c-qvoice-mean28-v1/verification.json).
- [Plan](../plans/attrition-c-qvoice-mean28-20261009.md).
- Consulta guardada: `queries/profiles/engineering_c_qvoice_mean28_person_month_20261009.sql`,
  ejecutada el 9-oct-2026. Hash y tiempos en `query-executions.json`.
- Se realizaron 26 ajustes de correcciones, cero reajustes de C y cero
  reajustes del artefacto final. Tiempo de cálculo: 9.9 minutos.
- `trained-model/model-mean28.json` copia exactamente el final del 7-sep-2026.
  Su estructura tiene ahora esta evaluación retrospectiva con coeficientes
  históricos separados; los coeficientes finales de septiembre siguen sin
  evaluación posterior a su ajuste.
- Todos los modelos anteriores se conservan. Sólo se guardan parámetros y
  agregados; filas, respuestas y llaves se procesan exclusivamente en RAM
  bajo `config/attrition_model_in_memory_training_authorization_20261001.json`.

No se modificó la presentación ni se cambiaron scores de assessment.
