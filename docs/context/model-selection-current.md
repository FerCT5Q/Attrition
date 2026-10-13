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

## Modelo E y F: señales V11 sobre C — 12 y 13 de octubre de 2026

El primer challenger E probó también `job_family_detail`. Aunque produjo una
mejora retrospectiva, esa variable queda fuera de las decisiones siguientes
porque su histórico no se considera confiable. El resultado E original se
conserva sólo como trazabilidad y queda superseded; no se recomienda usarlo ni
la combinación ciudad + familia.

F repitió la comparación sin `job_family_detail`: `work_city`, `work_country`,
`manager_observed_expected6_band` y `manager_team_exits6_v11`, cada una sobre C
y sin QVoice. En los cuatro periodos, las cuatro variantes redujeron el
log-loss y el Brier frente a C. La mejora media de captura fue:

- ciudad laboral: +0.3 pp;
- país laboral: +0.1 pp;
- salidas observadas/esperadas del manager: +0.4 pp;
- salidas bajo el manager actual: +0.4 pp.

Ciudad obtuvo el mayor descenso de log-loss entre las señales de F: 131.0
frente a 131.9 ×1000, con captura de 45.7% frente a 45.4% y error de grupo de
0.6 pp frente a 0.7 pp. País aportó una mejora menor: log-loss 131.5 ×1000,
captura 45.6% y error de grupo 0.6 pp. Los intervalos pareados de país fueron
[0.24, 0.43] en log-loss ×1000 de C menos F, [0.01, 0.02] en Brier ×1000 y
[0.06, 0.24] puntos porcentuales de captura.

F sigue siendo experimental: la comparación fue contra C y no contra CQ, no
reoptimizó los grupos y no demuestra superioridad frente a CQ. C y CQ no
cambian.

Artefactos: [informe E original](../../output/analysis/engineering/20261012/model-e-signal-expansion-v1/informe.md),
[informe F](../../output/analysis/engineering/20261012/model-f-no-job-family-v1/informe.md),
[resultados F](../../output/analysis/engineering/20261012/model-f-no-job-family-v1/results.json),
[configuración F](../../config/engineering_model_f_no_job_family_20261012.json) y
[plan F](../plans/attrition-model-f-no-job-family-20261012.md).

## Actualizacion F + QVoice - 13 de octubre de 2026

La comparacion completa esta documentada en [el plan F + QVoice](../plans/attrition-model-f-qvoice-comparison-20261013.md) y [los resultados agregados](../../output/analysis/engineering/20261013/model-f-qvoice-comparison-fast-v1/results.json).

La actualizacion de F + QVoice supersede la frase anterior que indicaba que
F solo se habia comparado contra C. Se probo `C + work_city + QVoice`, sin
`job_family_detail`, frente a `C + QVoice` y la referencia archivada
`B + QVoice`. Se conservaron las selecciones QVoice de CQ y los grupos por
antiguedad x salidas del equipo x nivel.

| Modelo | Log-loss x1000 (menor) | Brier x1000 (menor) | PR-AUC (mayor) | Lift 10% (mayor) | Captura 30% (mayor) | Error grupo-mes (menor) |
|---|---:|---:|---:|---:|---:|---:|
| C + ciudad + QVoice | 136.4 | 30.6 | 5.9% | 2.2 | 43.1% | 0.9 pp |
| C + QVoice | 137.7 | 30.7 | 5.5% | 2.1 | 43.1% | 1.0 pp |
| B + QVoice | 137.4 | 30.6 | 5.4% | 2.0 | 41.6% | 0.6 pp |

Ciudad mejora a CQ en log-loss, Brier, PR-AUC, lift y error de grupo. La
captura media al 30% aumenta solo 0.04 pp. Frente a B + QVoice, F + QVoice
mejora las perdidas y el ranking, y captura 1.5 pp mas de salidas, pero su
error de grupo es 0.3 pp mayor. F + QVoice queda como challenger favorable
para ranking y captura; CQ permanece como modelo elegido y no se reoptimizan
los grupos.

La auditoría ligera de F + QVoice comprobó 25 condiciones sobre agregados de
la corrida completa y una réplica rápida: 24 pasaron. F mejora log-loss,
Brier, PR-AUC, lift y error de grupo en ambos cortes. La captura mejora
0.1 pp en el primero y empata en el segundo. La condición histórica de ganar
captura en ambos cortes no pasa; la decisión de CQ ya había considerado una
victoria y un empate, por lo que esa condición no es un impedimento universal.
F + QVoice queda registrado como nuevo candidato experimental y CQ conserva
su elección previa. La ausencia de deterioro se refiere a las seis métricas
agregadas frente a CQ en esos dos cortes, no a cada grupo o capacidad.
La [auditoría archivada](../../output/analysis/engineering/20261013/model-f-qvoice-comparison-v3/validacion-f-qvoice.md)
no constituye validación independiente ni completa las pruebas de calibración,
estabilidad o diferencias por segmento. Su alcance se precisa en la
[revisión de Julia y Brian](../plans/revision-julia-brian-salida-rh-20261012.md).

La evaluacion usa agosto-diciembre de 2025 y enero-febrero de 2026, los dos
cortes con QVoice disponible. Es retrospectiva y reutiliza la seleccion
QVoice archivada; no es una validacion prospectiva independiente.

## BU L3 como senal y dimension de grupos - 12 de octubre de 2026

La ronda de BU L3 esta documentada en el [plan y cierre](../plans/attrition-model-bu-l3-20261012.md),
la [ficha de la variable](../variables/bu-l3/README.md) y el [informe agregado v7](../../output/analysis/engineering/20261012/model-bu-l3-v7/informe.md).
Se uso el mapping historico `cost_centerid = d_department.nk_dept_id` con
ventana as-of por snapshot y `ude_bu_reporting_l3` como valor. El mapping paso
la auditoria: 2,209,264 fotos, cero duplicados y cero multi-match; 20 fotos
quedaron sin match y se codificaron como `(unknown)`.

BU L3 redujo modestamente el log-loss de B, C + QVoice y F + QVoice. Las
diferencias pareadas fueron -0.386, -0.588 y -0.355 x1000, respectivamente,
con intervalos de log-loss que excluyen cero. El efecto sobre Brier fue mas
debil en B y F.

Como dimension de grupos, la mejor candidata por captura fue BU L3 x
antiguedad x salidas en su equipo, pero elevo `rest` a 21.5% frente al maximo
permitido de 10.3%. Ninguna candidata paso las tres guardas de captura, error y
`rest`. BU L3 queda como challenger documentado; el modelo elegido CQ y los
grupos actuales permanecen sin cambios. `job_family_detail` no se utilizo en F
ni en esta ronda.

La corrida v7 también evaluó las dos variantes con grupos actuales.
C + QVoice + BU L3 obtuvo 43.1% de captura, 0.9 pp de error y 5.3% en `rest`;
F + QVoice + BU L3 obtuvo 43.1%, 0.9 pp y 5.3%.

La revisión de código posterior encontró que la subdivisión selectiva contaba
como `rest` también a la población fuera de los grupos priorizados. Por ello,
el 67.7% reportado para F no mide sólo fragmentación y no es comparable al
`rest` del baseline. La implementación tampoco conserva grupos padre cuando
sus subceldas carecen de soporte. Sus fallos de capacidad y error quedan
documentados, pero no descartan la propuesta de conservar los demás grupos y
dividir sólo los de riesgo. La evaluación corregida se completó en la revisión
siguiente; los grupos actuales siguen como referencia. Véase la
[revisión de Julia y Brian](../plans/revision-julia-brian-salida-rh-20261012.md).

## Revisión conjunta y preparación para RH — cierre 13-oct-2026

La [revisión implementada](julia-rh-review-20261012.md) compara CQ, FQ y
FQ + BU L3 sobre las mismas personas, fechas y grupos, a capacidad 10/20/30%.
**CQ continúa elegido.** FQ + BU L3 es el mejor candidato en log-loss y Brier
medios: log-loss ×1000 de 136 frente a 136.4 de FQ y 137.7 de CQ; los tres
capturan aproximadamente 43.1% al 30%. El resultado mejora estimación sin
justificar por sí solo un cambio operativo. En enero CQ conserva su base RH
de agosto y FQ la reajusta; el contraste no aísla el aporte de ciudad.

La subdivisión corregida de 100 personas no pasa todas las guardas en ambos
periodos; sólo pasan 150/200 con FQ + BU L3 y capacidad 10%. El verdadero REST
se conserva. El escalar R6 probado empeora el sesgo posterior y no se aplica.
La revisión entrega 44 filas, fichas, diagnósticos y una copia actualizada del
deck de evolución. Deja explícitos los límites de disponibilidad histórica de
IOS y publicación QVoice y la necesidad de evaluación posterior al ajuste.

## Comprobación C + BU sin QVoice — 13-oct-2026

La [prueba específica](c-bu-isolation-20261013.md) completa la variante que
faltaba en el informe BU v7. C + BU sin QVoice obtiene log-loss ×1000 de 138
y captura de 42.7%, frente a 137.7 y 43.1% de CQ. Mejora las pérdidas de C
reajustado al mismo corte, pero su error de grupo-mes medio aumenta.
No supera el balance de CQ. Con QVoice, C + BU llega a 137 y 43.1%; añadir
ciudad reduce la pérdida a 136 con captura similar. FQ + BU conserva la
menor pérdida predictiva media; **CQ continúa elegido**.

Se reusaron los referentes y se hicieron cuatro ajustes RH y dos Q, sin
nueva búsqueda. Se preservaron los periodos, población, grupos y capacidades;
500 remuestreos por persona producen diferencias pareadas. El contexto
enlazado explica los intervalos y el límite temporal de la base CQ.
La presentación de la revisión fue corregida para conservar las nueve
diapositivas originales; la expansión de 16 deja de ser la entrega vigente.

## Sensibilidad H = C sin Transfers — 13-oct-2026

La [ablación H](model-h-without-transfers-20261013.md) retira exclusivamente
`transfer_12m` de C; `transfer_history` nunca fue predictor de C. Se conservaron
el origen de 1-ago-2025, las variables restantes, L2, población, periodos,
grupos y capacidades. C y CQ se reprodujeron antes de la comparación.

H obtiene log-loss ×1000 de 140.5 y captura de 41.6% al 30%, frente a 138.8
y 42.4% para C. H + QVoice obtiene 139.4 y 42.4%, frente a 137.7 y 43.1%
para CQ. Quitar Transfers empeora las pérdidas en ambas variantes; la captura
de H también disminuye 0.81 pp, IC95 [-1.61, -0.09]. Por tanto, **CQ continúa
elegido** y la solicitud de retirar Transfers no se adopta con esta evidencia
retrospectiva.

## Referencia B en la sensibilidad de Transfers — 13 de octubre de 2026

La ejecución [H v4](model-h-without-transfers-20261013.md) restauró B como referencia, sin reajuste, sobre los mismos dos periodos recientes usados para la sensibilidad de Transfers. B obtuvo log-loss ×1,000 de 138.7, PR-AUC de 4.8%, captura de 41.6% al 30% y error de grupo de 0.8 pp; C obtuvo 138.8, 4.9%, 42.4% y 1.0 pp, respectivamente. Por tanto, el corte corto muestra un intercambio: B tiene menor pérdida y error de grupo, pero C captura 0.8 pp más salidas y ordena mejor.

Este contraste de dos periodos no reabre la selección B → C de cuatro periodos ni cambia la decisión vigente. CQ continúa elegido por su balance histórico frente a C y por la preparación para uso grupal; retirar Transfers tampoco mejora C ni CQ.

## J: BU L3 Top 9 + Other sin Transfers — 13 de octubre de 2026

La prueba [J](model-j-bu-top9-without-transfers-20261013.md) cumple el requisito de retirar `transfer_12m` y añade BU L3 como nueve categorías conocidas más `Other`; también incluye J + QVoice. Para evitar la fragmentación observada al cruzar BU con otros criterios, la prioridad usa sólo los diez grupos BU, aprendidos antes de cada origen, para todos los modelos.

J + QVoice obtiene log-loss ×1,000 de 137.5 y PR-AUC de 5.6%, frente a 137.7 y 5.5% para CQ. La diferencia de log-loss es −0.17 ×1,000, IC95 [−0.39, 0.06], por lo que no es concluyente frente a CQ. A capacidad de 30%, ambos capturan 32.6% de las salidas dentro de estos grupos BU; J + QVoice reduce el error de grupo a 0.5 pp frente a 0.7 pp de CQ. La captura no es comparable con 43.1% de CQ bajo los grupos actuales, porque cambió la definición de grupos.

Los controles reprodujeron C/CQ y verificaron capacidad, diez categorías y ausencia de doble conteo. CQ sigue elegido. La presentación de nueve diapositivas incorpora una nota concisa del candidato sin cambiar esa decisión.
