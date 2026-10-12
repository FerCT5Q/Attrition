# Modelo elegido: C + QVoice

Decisión confirmada por el usuario: **10-oct-2026**.
Evidencia de comparación: 8–9-oct-2026. Modo `presentation`.
Etapa: **selección de modelo**. Estado: **elegido**.

**Actualización de contexto: 12-oct-2026.** Terminó la ronda B + playbook V11;
su modelo final permanece experimental y no cambia la decisión de CQ.
La nueva búsqueda se resume al final de este documento.

## Decisión vigente

**El modelo elegido es C + QVoice anterior, identificado como `CQ` en las
comparaciones, sin calibración posterior adicional del riesgo a seis meses.**
El usuario confirmó esta elección y pidió registrar sus argumentos el
10-oct-2026. El objetivo que guía la decisión es identificar grupos con
alto attrition para orientar acciones, conservando estimaciones útiles e
interpretación clara de los grupos.

### Identificación exacta

- Versión: `engineering-c-qvoice-20261008-v1`.
- [Carpeta del modelo elegido](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/).
- [Configuración original](../../config/engineering_model_c_qvoice_20261008.json).
- [Artefacto final archivado](../../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/trained-model/model.json),
  con corte 7-sep-2026.
- Referencia en las tablas: `CQ`, «C + Q anterior» o «C + Q evaluado».
- Fórmula: hazard mensual con enlace cloglog, base C más corrección QVoice;
  riesgo acumulado `R6 = 1 − producto(1 − h_m)`.

Las métricas de selección corresponden al procedimiento ajustado antes de
cada periodo y a sus modelos históricos en `folds/`. El artefacto final de
septiembre contiene Career Goals, promedio de 33 preguntas, Wellbeing
Q8/Q10/Q11 y Confidence Q13/Q17. Sus coeficientes finales siguen sin
evaluación posterior a su ajuste. Esta identificación permite distinguir
la versión elegida de las combinaciones fijas probadas posteriormente.

### Argumentos de la elección

1. **Mejor priorización frente a C.** Al priorizar el 30% de la población,
   CQ concentra 43.1% de las salidas observadas frente a 42.4% de C: una
   ganancia media de 0.7 puntos porcentuales. Gana en agosto–diciembre de
   2025 y empata en enero–febrero de 2026.
2. **Mejores probabilidades en promedio.** El error de grupo-mes baja 2.3%
   relativo frente a C; el log-loss por mil pasa de 138.8 a 137.7 y PR-AUC
   de 4.9% a 5.5%. La elección combina captura de salidas y precisión de
   las estimaciones en los grupos priorizados.
3. **Grupos interpretables.** Conserva los cortes por antigüedad, salidas
   previas del equipo y nivel. QVoice ajusta los riesgos y puede cambiar
   su orden de prioridad; las definiciones de grupo siguen siendo
   comunicables mediante esas variables.
4. **Las nuevas variantes con promedio no lo superan.** La combinación
   fija con promedio de 28 captura el mismo 43.1%, pero tiene 4.1% más
   error de grupo-mes y 0.4% más log-loss que CQ anterior. El promedio de
   33 tampoco mejora ese balance. La selección interna por Brier
   conserva CQ anterior en los dos periodos.
5. **La comprobación con un cuarto corte mantiene la preferencia.** Al
   añadir adquisición registrada a la agrupación, CQ anterior captura
   43.3% frente a 43.2% de la variante fija con promedio de 28 y tiene
   menor error de grupo-mes.

Fuente de estos argumentos: `results.json`, campos `summary`, `periods`,
`four_cuts_summary` e `intervals`, de la evaluación del 9-oct-2026 enlazada
abajo. Población: Engineering, Employee, Regular, activo, sin RF360;
fotos de agosto–diciembre de 2025 y enero–febrero de 2026, con horizonte
de seis meses. Consulta guardada:
`queries/profiles/engineering_c_qvoice_mean28_person_month_20261009.sql`.

### Alcance de la decisión

La elección corresponde a esta etapa de selección. Todavía no se ha
iniciado un piloto. Las mejoras son retrospectivas y promedio: algunos
grupos concretos pueden quedar peor estimados. Los grupos describen
asociaciones predictivas; el análisis no estima el efecto causal de las
acciones de retención. C queda como referencia para comparaciones.

Esta nota actualiza la recomendación de selección después de la conversación
y de la nueva prueba, y registra su confirmación explícita. La nota histórica
`model-c-qvoice-overlap.md` registró
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

## Validación posterior con el modelo D

El 10-oct-2026 se ejecutó el plan final D sobre los mismos periodos externos.
D mantuvo C como offset y probó conjuntamente tres representaciones QVoice,
penalizaciones separadas HR/Q, cuatro bloques históricos, interacciones
preespecificadas, un enlace logit mensual y RSF+Q. Las señales históricas
pasaron auditorías temporales y de consistencia antes del ajuste.

**D no sustituye a CQ.** El ganador de la selección eliminó todos los bloques
históricos y conservó únicamente Q4, Q12 y Career. Frente a CQ:

- captura al 30%: 42.8% frente a 43.1%, diferencia −0.3 pp, IC95
  [−1.0, 0.4];
- error grupo-mes: 0.963 pp frente a 0.971 pp, mejora relativa de 0.8%, por
  debajo del 10% exigido por la ruta de precisión;
- log-loss ×1000: 137.6 frente a 137.7;
- en enero–febrero de 2026 la captura baja de 42.8% a 42.1%, superando el
  máximo permitido de pérdida por periodo.

El control logit mensual produjo prácticamente el mismo orden y métricas que
D cloglog. RSF+Q alcanzó 43.1% de captura, pero elevó el error grupo-mes a
1.071 pp. Ninguno cumple la regla equilibrada congelada. CQ permanece como
modelo elegido y D queda documentado como experimento negativo útil: las
señales históricas nuevas no aportan una mejora estable sobre la corrección
QVoice ya seleccionada.

Artefactos: [informe D](../../output/analysis/engineering/20261010/model-d-v1/informe.md),
[tabla](../../output/analysis/engineering/20261010/model-d-v1/tabla-comparativa.md),
[resultados](../../output/analysis/engineering/20261010/model-d-v1/results.json) y
[decisión](../../output/analysis/engineering/20261010/model-d-v1/selection-decision.json).

## Ronda B + playbook V11: 12 de octubre de 2026

La ejecución `engineering-b-playbook-v11-20261012-v1` terminó con estado
`completed_experimental`. Conservó los 8 predictores y 2 interacciones de B
y examinó incorporaciones RH y QVoice, individualmente y en pares/tríos de
las seis candidatas de cada selección interna.

El [modelo final experimental](../../output/analysis/engineering/20261011/b-playbook-v11-v1/models/final-B_RH-Q.json),
con corte 7-sep-2026, añade familia de puesto detallada, ciudad laboral y
distancia estimada, más Q4 y Q12 de QVoice. Conserva las variables de B;
esto no significa que se hayan mantenido fijos todos sus coeficientes.
La distancia sigue siendo una aproximación postal con catálogo estático,
no un trayecto real validado.

**CQ sigue siendo el modelo elegido.** Esta ejecución comparó las nuevas
alternativas contra B, no directamente contra C o CQ. Sus resultados
retrospectivos evalúan la selección hecha antes de cada periodo; no son
validación posterior de los coeficientes finales de septiembre. Queda
pendiente una comparación con C/CQ bajo las mismas condiciones antes de
concluir que el nuevo modelo es superior.

La [documentación de la ronda](b-playbook-v11-documentacion-variables.md)
reúne contexto, límites y enlaces al diccionario completo. La
[tabla de 43 filas](../../planes/modelo_c/43_variables_playbook_modelo_final_20261012.md)
es un resumen para Julia de esta ronda, no del CQ seleccionado. La
implementación detallada por variable está en las fichas de la ejecución;
`docs/variables/` conserva la documentación conceptual y de preparación.

Fuentes: [manifest de cierre](../../output/analysis/engineering/20261011/b-playbook-v11-v1/manifest.json),
[resultados](../../output/analysis/engineering/20261011/b-playbook-v11-v1/results.json)
y [verificación](../../output/analysis/engineering/20261011/b-playbook-v11-v1/verification.json).
No se sustituyeron los modelos anteriores ni se cambiaron scores de assessment.
