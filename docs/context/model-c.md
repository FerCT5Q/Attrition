# Modelo C: referencia del experimento sin QVoice

Estado del experimento original, con prioridad en log-loss: **C no demuestra mejora suficiente bajo la regla**.

## Artefactos

- Carpeta: `output/analysis/engineering/20261008/model-c-v2`.
- Modelo: `trained-model/model-c.json`; encoder, coeficientes, variables, L2 y límite de conocimiento.
- Reglas: `trained-model/groups.json`; sólo grupos, sin identificadores ni puntuaciones personales.
- Informe: `informe.md`; métricas verificables: `results.json`; recorrido: `selection/`.

## Selección y uso

- Alcance de los grupos: el experimento C y la comparación de prioridades usan
  árboles de hasta 8 hojas tanto para B como para C. La agrupación original
  elegida para B era Antigüedad × Salidas del equipo × Nivel, con 22 grupos
  elegibles en la foto 26-jul-2026, más resto. La comparación reciente no
  evalúa esa agrupación original frente a C. La comparación adicional de cortes
  se documenta al final de este archivo. Véase
  `docs/context/model-comparison-grouping-scope.md`.
- Filtrado L1 sobre el pasado, refit cloglog L2, validación temporal anidada y selección por pérdidas R6 con restricciones de ranking.
- Las métricas evalúan la política de selección en cuatro periodos. Se archiva la última especificación evaluada, con corte 2025-08-01; no se terminó el reajuste adicional a septiembre de 2026 porque C no superó la regla de promoción.
- Las filas repetidas de diseño se comprimen exactamente en memoria; penalización, likelihood y criterios permanecen iguales.
- QVoice está excluido del C base. La extensión independiente posterior se
  documenta al final de este archivo.
- B y B + QVoice se conservan en sus carpetas anteriores. El control de esta comparación reproduce la receta B sobre el mismo frame temporal corregido de C.

## Términos del modelo final

- `level_grouped`: Nivel.
- `tenure_playbook_band`: Antigüedad en Qualcomm.
- `calendar_month`: Mes del calendario.
- `manager_changes_12m`: Cambios de manager en 12 meses.
- `team_exits_12m`: Salidas previas del equipo en 12 meses.
- `direct_reports_band`: Reportes directos.
- `time_since_promotion_band`: Tiempo desde promoción.
- `rehire`: Recontratación (proxy).
- `level_x_tenure`: Nivel × antigüedad.
- `prior_experience_band`: Experiencia previa.
- `time_at_level_band`: Tiempo en el nivel.
- `ios_12m`: Movimientos IOS en 12 meses.
- `layers_band`: Capa organizativa almacenada.
- `region`: Región.
- `comp_ratio_band`: Banda de comp ratio almacenado.
- `acquisition_recorded`: Adquisición registrada.
- `transfer_12m`: Transferencia registrada en 12 meses.

## Límites

- Experimento retrospectivo, sin validación prospectiva nueva ni garantía causal de las acciones.
- Transferencia previa al 23 de octubre de 2023 se codifica como historia no confirmada. Comp ratio y capas son valores almacenados; no se demostró aquí su fórmula ni una raíz CEO.
- Consulta: `queries/profiles/engineering_model_c_person_month_20261008.sql`; inventario: `config/engineering_model_c_inventory_20261008.json`.
- No se asignaron nuevos scores de assessment; las comprobaciones de entrada se conservan como evidencia limitada al modelo.

## Revisión orientada a grupos prioritarios: 8 de octubre de 2026

El usuario aprobó priorizar grupos altos y parte de los medios, manteniendo
bajo riesgo en entrenamiento y seguimiento. Se aplicó ese criterio en
`output/analysis/engineering/20261008/bc-priority-comparison-v1/`.
El plan previo está en `docs/plans/attrition-bc-priority-comparison-20261008.md`.

- Se reutilizaron los cuatro C y se reconstruyeron cuatro B con sus parámetros
  ya elegidos. Población, métricas y ranking de grupos reprodujeron el run
  anterior. El cálculo adicional tomó 4.8 minutos, incluidos 3.2 de carga.
- Se compararon capacidades de 20%, 30% y 40%; 30% fue el escenario central
  propuesto antes del cálculo. Son hipótesis de capacidad, no un presupuesto
  operativo confirmado. La hoja que cruza el límite recibe peso fraccional;
  también se documentan coberturas al incluir o excluir la hoja completa.
- Al 30%, captura B 43.6%, C 43.9%; diferencia C − B de 0.4 pp,
  IC95 [0.2, 0.6] por bootstrap de personas. C gana en dos periodos y empata
  en dos, sin derrotas. El error medio por grupo prioritario baja de 0.5 pp
  a 0.4 pp y C gana en tres de cuatro periodos.
- La coincidencia ponderada de prioridad entre reajustes favorece B:
  99.2% frente a 95.5%. El promedio del peor error publicable por periodo
  también favorece B: 1.5 pp frente a 1.6 pp. Existen grupos altos mal
  estimados en ambos modelos.
- Al 20%, C captura más en promedio, pero gana en un periodo, pierde en uno
  y empata en dos; su estabilidad es menor. Al 40%, la captura queda
  prácticamente igual, con ligera diferencia puntual favorable a B.
- En la foto adicional de febrero de 2026, con seguimiento hasta agosto de
  2026, ambos capturan 41.7% al atender 30%; el error por grupo es 0.4 pp
  con B y 0.3 pp con C. Se usaron los modelos de agosto de 2025. Es una
  extensión retrospectiva de una foto, no un holdout virgen.

Interpretación dentro de la comparación con árboles de hasta 8 grupos:
**C ofrece un balance ligeramente favorable para priorizar al 30%**.
Este resultado no demuestra que C supere la agrupación original de B con
22 grupos elegibles. La regla conservadora formal sigue sin cumplirse porque exige tres
victorias temporales en captura: se obtuvieron dos victorias y dos empates.
Se conservan ambos resultados, sin reescribir el criterio previo ni declarar
una mejora general en todas las capacidades. La evidencia es retrospectiva
y no mide salidas evitables ni el efecto de una intervención.

En esta revisión no se reajustó C con datos hasta septiembre de 2026 ni se
inició C + QVoice.
Fuentes: `bc-priority-comparison-v1/results.json`, `informe.md`,
`analysis-checks.json` y `manifest.json`; consulta y población iguales al
experimento original. No se guardaron filas ni puntuaciones individuales.

## Selección adicional de cortes interpretables: 8 de octubre de 2026

Run separado: `output/analysis/engineering/20261008/c-group-selection-v1/`.
Conserva todos los modelos originales y aplica la receta de cortes de B como
referencia principal. Restaura ocho modelos; cero reajustes hazard. Cálculo:
6.5 minutos, incluida la carga. Plan y criterios fijados antes de resultados
en `docs/plans/attrition-c-group-selection-20261008.md`.

- Se compararon todos los cruces de dos/tres dimensiones declaradas y árboles
  de hasta ocho/dieciséis hojas: 562, 288, 366 y 562 candidatos por periodo.
- Al priorizar 30%, C con selección propia captura 45.2%, prácticamente igual
  a B con cortes (45.2%). Error medio por grupo: C 0.7 pp y B 0.9 pp;
  error grupo-snapshot: C 0.7 pp y B 0.9 pp. Diferencia de captura menor a
  0.1 pp, IC95 [-0.9, 0.8], dos victorias y dos derrotas: no cumple la regla.
- C usando exactamente los cortes originales de B captura 45.4%; ventaja
  de 0.3 pp, IC95 [-0.3, 0.8], tres victorias. No es concluyente al 30%.
- Al 40%, ese C con los mismos cortes sí cumple la regla retrospectiva:
  captura 57.6% frente a 56.4%, diferencia 1.1 pp, IC95 [0.5, 1.7], tres
  victorias y errores dentro de tolerancia. Es un escenario secundario
  predefinido, sin promoción automática ni evidencia prospectiva.
- La última selección principal usa antigüedad × salidas del equipo:
  12 grupos elegibles en 22-feb-2026, con seguimiento hasta 22-ago-2026.
  Captura 42%, error 0.5 pp; B cortes en esa foto: 20 grupos, captura 41.2%,
  error 0.8 pp. El modelo y selección tienen origen 1-ago-2025.
- Las cuatro selecciones fueron distintas. Se evalúa la política de elegir
  agrupaciones antes de cada periodo; no una única combinación que gane en
  los cuatro. Regla final archivada en `selected-grouping.json`.

La reducción de error entre agrupaciones distintas también depende de la
granularidad. El informe incluye una comprobación sobre idénticas personas
priorizadas por B: cambiar únicamente el estimador a C reduce el error por
grupo de 0.9 a 0.7 pp y el error grupo-snapshot de 0.9 a 0.8 pp.

Se mantienen los límites del frame, los ocho modelos congelados y QVoice
excluido. No se cambian los resultados ni reglas de runs anteriores. Fuente:
`c-group-selection-v1/results.json`, `analysis-checks.json`, `preservation.json`
y `additional-preservation-after.json`; consulta y población iguales a C.

## Extensión C + QVoice: 8 de octubre de 2026

La extensión independiente está en
`output/analysis/engineering/20261008/model-c-plus-qvoice-v1/` y se resume en
[model-c-plus-qvoice.md](model-c-plus-qvoice.md). Conserva los coeficientes de
C y los cortes elegidos de antigüedad × salidas del equipo × nivel.

En dos periodos retrospectivos, la captura al priorizar 30% sube de 42.4%
a 43.1%, el log-loss baja 0.8% y el error medio por grupo mejora ligeramente.
Gana captura en agosto–diciembre de 2025 y empata en enero–febrero de 2026;
no cumple la regla de mejora en ambos periodos. El mayor error publicable
promedio sube de 2.1 a 2.2 pp. C + Q queda como extensión prometedora para
validación adicional y C se conserva como referencia. El escalar R6 aporta
un cambio mínimo. Los modelos y resultados originales permanecen intactos.

## Lectura de grupos prioritarios y acciones: 8 de octubre de 2026

La revisión está en
[model-c-priority-groups-v1/informe.md](../../output/analysis/engineering/20261008/model-c-priority-groups-v1/informe.md).
Usa exclusivamente agregados archivados de `C_Bcuts`; conserva los modelos.

- Foto 22-feb-2026, con seguimiento hasta 22-ago-2026: 20 grupos elegibles.
  Priorizar 30% selecciona ocho grupos completos y parte de un noveno.
- Ocho grupos completos: 10240 personas, 29% de cobertura y 41.6% de captura.
  Nueve completos: 12820 personas, 36.3% de cobertura y 49.9% de captura.
- El mayor grupo prioritario, entrada con 3–5 años y sin salidas previas del
  equipo, tiene 3986 personas: estimado 5.2%, observado 4.7%. Aparece en las
  24 fotos históricas revisadas.
- El mayor riesgo estimado, entrada con 3–5 años y salidas previas, tiene
  1424 personas: estimado 8.1%, observado 5.5%. Su prioridad persistente
  convive con sobreestimación reciente.
- Se proponen hipótesis de desarrollo, movilidad y continuidad del trabajo
  para diagnóstico. No se atribuyen causas ni salidas evitables. La foto es
  histórica y la pertenencia debe actualizarse para una eventual aplicación.

El informe distingue riesgo, volumen, precisión y persistencia; incluye
gráfico, CSV, fuentes congeladas y reconciliaciones. No se crea otro modelo.

## Exploración posterior: cuatro variables y más grupos

Se documenta en [model-c-fourway-groups.md](model-c-fourway-groups.md) y en
`output/analysis/engineering/20261008/c-fourway-groups-v1/`.

Se exploraron 3775 cruces entre cuatro periodos, sin reajustar C. Al priorizar
30%, añadir una variable a los cortes actuales mejora la captura media de
45.4% a 45.7%, con cumplimiento marginal de la regla retrospectiva. La última
selección añade adquisición registrada y tiene 23 grupos en febrero de 2026.
La familia orientada a unos 40 grupos no mejora la captura al 30%.

Al priorizar 20%, la política de seleccionar cuatro variables mejora la
captura de 31.7% a 33.2%, IC95 del cambio [0.6, 2.3] pp. Es un escenario
secundario declarado. Su último cruce usa nivel, última promoción, tiempo en
el nivel y adquisición registrada, con 30 grupos en febrero de 2026. Las
medias evalúan las selecciones temporales, no sólo esos últimos cortes.

Son alternativas documentadas que conservan la agrupación y el modelo
originales. Su elección depende de capacidad de acción, precisión y
estabilidad; no se impone llegar a 40 grupos.
