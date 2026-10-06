# Vía de entrada al compensation grade actual

## Flujo histórico y alcance

Esta evidencia descriptiva independiente responde la pregunta de Julia: entre
las personas que actualmente están en cada `compensation_grade`, ¿qué
porcentaje llegó al grade actual mediante una promoción registrada? Alimenta
la lámina 30; no cambia el assessment v4 ni la evidencia de `Time since last
promotion`.

- **Modo de entrega:** `internal_analysis`.
- **Población y grain:** empleados regulares activos; un empleado-snapshot
  mensual único en `hrda.post_hire_monthly_worker_dtls`, al corte fijo
  `2026-08-23`.
- **Tipo semántico:** `derived_feature`. La vía se reconstruye desde snapshots
  mensuales y eventos de promoción dentro del episodio actual, no desde un
  campo HRIS individual.
- **Uso exploratorio en attrition:** contexto descriptivo por grade actual. No
  es una señal causal, un juicio de política de promociones ni una clasificación
  operativa de personas.

Los IDs, snapshots y fechas de eventos se usan sólo dentro de las consultas
read-only agregadas. La evidencia JSON conserva conteos agregados,
porcentajes redondeados y hashes; no guarda filas, IDs, fechas individuales ni
compensación exacta.

## Definición aplicada

Dentro de la última contratación o recontratación (`max_hire_rehire_date`), se
busca el último cambio observable hacia el `compensation_grade` vigente. Una
promoción lo confirma únicamente si `is_promo=1`, la fecha es válida y no
futura, cae después del snapshot previo y hasta el snapshot de entrada, está
dentro del episodio vigente y el grade del snapshot del evento coincide con el
grade actual.

Los estados son excluyentes:

- `Promotion confirmed into current grade`: el último cambio observado al
  grade actual coincide con un evento válido de promoción.
- `Observed entry without registered promotion`: se observa el cambio al
  grade actual, pero no hay un evento que cumpla la regla de confirmación.
- `Current-grade entry not observable`: no existe un cambio previo completo y
  observable al grade actual.

Los dos últimos estados no significan “hired into grade”. En particular, el
estado no observable puede reflejar historia previa incompleta o falta de un
cambio observable, no contratación directa.

`compensation_grade_old` fue rechazado como evidencia definitoria. La auditoría
agregada lo comparó con el snapshot previo observado y encontró 201,395
discrepancias entre 2,418,040 comparables; el campo no participa en el profile
ni en la clasificación.

## Validaciones ejecutadas — 2026-09-10

### 1. Integridad de población, snapshots y episodio

- **Pregunta y motivo:** ¿el denominador representa un empleado regular activo
  único y completo al corte, y la historia queda dentro de su episodio vigente?
  Sin ello se podrían mezclar grades, personas o recontrataciones.
- **Método y evidencia:** consulta agregada
  `queries/audits/current_grade_entry_path_integrity_20260823.sql`.
- **Regla de aceptación:** cero IDs faltantes, duplicados, conflictos de grade
  o episodio, grades/episodios vigentes faltantes e inicios futuros; el conteo
  fuente y el de empleados únicos deben reconciliar.
- **Métricas observadas:** 50,043 renglones objetivo y 50,043 empleados únicos;
  todos los contadores de la regla fueron cero.
- **Conclusión e impacto:** el denominador es apto para una descripción
  agregada del grade actual; no prueba la semántica de una política HRIS.
- **Acción:** repetir la auditoría antes de cambiar el corte.

### 2. Última entrada observable y fronteras temporales

- **Pregunta y motivo:** ¿la clasificación usa el último cambio observado al
  grade actual, sin atribuir una promoción histórica anterior a una entrada más
  reciente?
- **Método y evidencia:** la auditoría reconstruye la línea mensual con
  `LAG`, ordena las entradas descendentes y conserva sólo
  `entry_recency_rank = 1`; también mide reentradas y entradas tras una brecha
  superior a 45 días.
- **Regla de aceptación:** la entrada seleccionada no puede cruzar una brecha
  superior a 45 días; los eventos deben ser posteriores al snapshot previo y
  no posteriores al snapshot de entrada.
- **Métricas observadas:** 27,273 entradas observables; 134 empleados tuvieron
  múltiples entradas observables y se dejaron fuera 139 entradas anteriores;
  cero entradas seleccionadas cruzaron una brecha superior a 45 días.
- **Conclusión e impacto:** una promoción anterior no confirma una entrada
  posterior al mismo grade.
- **Acción:** conservar la selección por última entrada si se refresca la
  lámina.

### 3. Evento de promoción y frontera de recontratación

- **Pregunta y motivo:** ¿la confirmación corresponde a un evento registrado,
  temporalmente alineado y perteneciente al episodio actual?
- **Método y evidencia:** la misma auditoría valida dominio y fecha de
  `is_promo`, eventos futuros, eventos posteriores a su snapshot, la frontera
  de rehire y el grade del snapshot de evento.
- **Regla de aceptación:** todos los contadores de eventos inválidos y de
  mismatch de grade dentro de la ventana deben ser cero; los eventos previos al
  episodio se excluyen.
- **Métricas observadas:** 19,669 pares de promoción válidos y 19,669 empleados
  confirmados; cero flags/fechas inválidos, futuros, posteriores al snapshot o
  mismatches en la ventana. La auditoría identifica candidatos previos al
  episodio sólo para excluirlos, no para clasificarlos.
- **Conclusión e impacto:** la primera categoría significa “promoción
  registrada que confirma la última entrada observable”, no “alguna vez fue
  promovido”.
- **Acción:** no convertirla en una medida de historial completo de carrera.

### 4. Reconciliación, pooling y privacidad

- **Pregunta y motivo:** ¿los tres estados son exhaustivos y cada celda visible
  cumple el umbral de privacidad?
- **Método y evidencia:** profile agregado
  `queries/profiles/current_grade_entry_path_20260823.sql` y constructor
  fail-closed `tools/build_current_grade_entry_path_evidence.py`.
- **Regla de aceptación:** los tres estados deben reconciliar al denominador;
  un grade individual debe tener `n >= 30` en sus tres celdas crudas, y los
  restantes se agregan una vez en `Other grades`.
- **Métricas observadas:** 19,669 promociones confirmadas, 7,604 entradas
  observadas sin promoción registrada y 22,770 no observables; total 50,043.
  De 45 grades fuente, 15 son individuales y 30 se agrupan en `Other grades`;
  hay 16 filas visibles y la menor celda publicada es `n=38`.
- **Conclusión e impacto:** la lámina puede mostrar porcentajes por grade y su
  `n` total sin exponer datos individuales.
- **Acción:** conservar el badge `Internal exploratory analysis` y volver a
  ejecutar las consultas antes de un nuevo corte.

## Artefactos y limitaciones

- Auditoría: `queries/audits/current_grade_entry_path_integrity_20260823.sql`.
- Profile: `queries/profiles/current_grade_entry_path_20260823.sql`.
- Constructor y puertas: `tools/build_current_grade_entry_path_evidence.py`.
- Evidencia congelada:
  `output/distribution/json/current-grade-entry-path-evidence-20260910.json`.

Los porcentajes usan largest remainder a 0.1 puntos porcentuales y suman
100.0% en cada fila. El artefacto no identifica contrataciones directas,
política de promociones, intención de la persona ni causalidad con attrition.

## Nueva evidencia: attrition Voluntary por tenure de la vía de entrada

### Flujo histórico y decisión de publicación

La lámina 28 cruza la vía observable de entrada al `compensation_grade` actual
con bandas fijas de tenure y calcula la tasa anual de salida Voluntary para
FY2021–FY2025. La unidad del denominador es empleado-snapshot mensual; el
evento de terminación se atribuye al último snapshot activo válido anterior a
`term_date`. La evidencia es `presentation`, agregada y descriptiva; no es una
clasificación operativa de personas ni una afirmación causal.

La reconstrucción conserva tres estados excluyentes:

- `Promotion confirmed into current grade`: la última entrada observable al
  grade actual queda confirmada por `is_promo=1` y `promotion_date` alineada
  temporalmente dentro del episodio vigente.
- `Observed entry without registered promotion`: se observa un cambio al grade
  actual, pero no existe un evento que cumpla la confirmación de promoción.
- `Current-grade entry not observable`: no hay un cambio previo completo y
  observable; se conserva como limitación y no se grafica.

La segunda categoría es un proxy de entrada observada sin promoción registrada.
No se describe como `direct hire` ni como `new hire`. `is_new_hire` tampoco se
usa como clasificador principal porque no demuestra por sí solo la vía al grade
actual.

### Derivación y validaciones ejecutadas — 2026-09-11

#### 1. Calendario, población y grain

- **Pregunta y motivo:** ¿la tasa usa cinco años fiscales completos y doce
  snapshots por año sin mezclar otra población?
- **Método y evidencia:** consulta agregada
  `queries/audits/current_grade_entry_path_tenure_attrition_20260911.sql`, con
  `worker_type='Employee'`, `employee_type='Regular'` y `active_status=1`.
- **Regla de aceptación:** FY2021–FY2025 debe contener 60 snapshots, 12 por
  año; los duplicados y conflictos del empleado-snapshot objetivo deben ser
  cero.
- **Métricas observadas:** 60 snapshots, 12 por año, 2,405,034 snapshots
  activos objetivo, duplicados cero y conflictos cero.
- **Conclusión e impacto:** la población y el calendario son consistentes;
  esta validación pasa y no limita el calendario de la lámina.
- **Acción:** conservar la ventana FY2021–FY2025 hasta disponer de una fuente
  histórica de inicio de profile con lineage aprobado.

#### 2. Vía observable al grade y frontera temporal

- **Pregunta y motivo:** ¿la vía se determina en cada snapshot vigente y sin
  atribuir una promoción posterior al evento de terminación?
- **Método y evidencia:** `LAG` por empleado y snapshot; se conserva la última
  entrada observable al grade dentro de `max_hire_rehire_date`. La promoción
  sólo confirma la entrada si `is_promo=1`, `promotion_date` es válida, cae
  después del snapshot previo y hasta el snapshot de entrada, y el grade del
  snapshot del evento coincide.
- **Regla de aceptación:** las bandas y vías deben formar un dominio fijo,
  exclusivo y completo para las observaciones publicables; el estado no
  observable no puede convertirse en una etiqueta de contratación.
- **Métricas observadas:** 432,656 snapshots con promoción confirmada,
  133,759 con entrada observada sin promoción registrada y 1,838,619 no
  observables. El dominio publicado contiene 5 bandas para la primera vía y 4
  para la segunda; la auditoría de dominio pasa.
- **Conclusión e impacto:** la derivación es temporal y separa explícitamente
  historia incompleta de una entrada observable sin promoción. No demuestra
  contratación directa ni una política de promociones.
- **Acción:** mantener `current_grade_entry_not_observable` fuera del gráfico y
  conservar la definición de proxy en cualquier reutilización.

#### 3. Tenure, cobertura y privacidad

- **Pregunta y motivo:** ¿se puede calcular tenure con una fecha de inicio
  disponible antes de `term_date` y publicar tasas por cohorte?
- **Método y evidencia:** se usa
  `GREATEST(time_in_job_profile_start_date, max_hire_rehire_date)`, limitado al
  snapshot observado. La cobertura y la calidad de las fuentes candidatas se
  auditan en `queries/audits/current_grade_entry_path_tenure_source_lineage_20260911.sql`.
- **Regla de aceptación:** el inicio de profile debe estar poblado; cada celda
  publicada debe tener doce meses, mínimo mensual y población distinta de al
  menos 30; las bandas no se reagrupan después de observar los resultados.
- **Métricas observadas:** `time_in_job_profile_start_date` está vacío en los
  2,405,034 snapshots activos FY2021–FY2025. Las tablas candidatas históricas
  revisadas también tienen cero filas pobladas del campo en la ventana. Por
  ello se publicaron 0 de 9 bandas y no se muestran tasas.
- **Conclusión e impacto:** el calendario y el dominio de bandas pasan, pero la
  cobertura del inicio de profile falla; el resultado es `warning` y la tasa
  actual no es publicable. No se imputa la fecha ni se sustituye la fuente sin
  lineage gobernado y reconciliación agregada.
- **Acción:** no usar la lámina para comparar attrition por tenure hasta que la
  fecha esté disponible y validada; repetir esta auditoría antes de publicar un
  nuevo corte.

#### 4. Atribución y reconciliación de eventos

- **Pregunta y motivo:** ¿cada evento Voluntary se cuenta una vez o queda
  explícitamente sin atribuir cuando falta un snapshot previo válido, una vía o
  tenure publicable?
- **Método y evidencia:**
  `queries/audits/current_grade_entry_path_tenure_attrition_gap_20260911.sql`
  selecciona el último snapshot activo válido anterior a `term_date` y
  clasifica el motivo de exclusión.
- **Regla de aceptación:** por año, total de eventos = atribuidos + no
  atribuidos; no se reasignan eventos sin banda válida.
- **Métricas observadas:** hubo 12,631 eventos Voluntary; 0 fueron atribuidos y
  12,631 quedaron no atribuidos. Los motivos agregados fueron 303 sin snapshot
  previo válido, 9,873 con vía no observable y 2,455 con tenure faltante.
- **Conclusión e impacto:** la reconciliación pasa y no existe leakage del
  evento de terminación, pero la ausencia de tenure impide un numerador
  publicable.
- **Acción:** conservar el warning y la separación de motivos; no completar el
  numerador con imputaciones ni con `is_new_hire`.

### Artefactos de esta evidencia

- Consulta principal:
  `queries/audits/current_grade_entry_path_tenure_attrition_20260911.sql`.
- Auditoría de gaps:
  `queries/audits/current_grade_entry_path_tenure_attrition_gap_20260911.sql`.
- Auditoría de lineage:
  `queries/audits/current_grade_entry_path_tenure_source_lineage_20260911.sql`.
- Builder focalizado:
  `tools/build_current_grade_entry_path_tenure_attrition.py`.
- Evidencia agregada:
  `output/distribution/json/attrition-43-variable-distributions-v2.current-grade-entry-path-tenure-attrition-evidence-20260911.json`.

La evidencia nueva no cambia el assessment v4 ni el score de la variable. La
asociación queda como no publicable hasta resolver la cobertura de
`time_in_job_profile_start_date`; las diferencias futuras no deben interpretarse
como causalidad, riesgo individual o contratación directa.
