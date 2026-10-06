# Historial de promociones por compensation grade actual

## Actualización de la lámina 30 — tracks y ventana trailing de 12 meses (2026-09-18)

La matriz histórica por grade exacto queda como contexto. La vista vigente de
la lámina 30 colapsa `compensation_grade` por su letra inicial cuando el valor
empieza con letra seguida de dígito: `M10`, `M20` y `M30` se muestran como
track `M`.

- **Corte:** snapshot mensual `2026-08-23` (agosto); no se usa el refresh posterior de septiembre.
- **Ventana:** `(2025-08-24, 2026-08-23]`, exactamente 12 snapshots mensuales.
- **Distribución:** Employee, Regular, activo y sin RF360 en agosto.
- **Promoción:** `promotion_yes_no='Yes' / participantes` del ciclo oficial `AR25`; el track se toma del grade del ciclo.
- **Attrition:** exits strict `VOLUNTARY / headcount mensual promedio` por track en la misma ventana.
- **Privacidad:** se muestran seis tracks con al menos 30 empleados; un track actual menor a 30 se omite sin guardar su etiqueta ni su conteo.

La evidencia agregada está congelada en
`output/distribution/json/attrition-43-variable-distributions-v7.promotion-track-trailing-12m-evidence-20260918.json`.
La consulta principal es
`queries/audits/promotion_track_trailing_12m_20260918.sql`. La auditoría de
fallback es
`queries/audits/promotion_track_unmatched_exit_nonnull_grade_20260918.sql`.
El track pudo asignarse a 99.96% de los exits; un evento con grades
contradictorios se dejó fuera del numerador por track.

## Flujo histórico y alcance

El assessment v4 histórico de `Time since last promotion` no se modifica con
esta revisión. Esta evidencia crea un artefacto descriptivo independiente para
la lámina 29: una matriz de porcentajes de promociones **registradas** dentro
de cada `compensation_grade` actual al corte fijo `2026-08-23`; conserva el
`n` total de cada fila.

- **Modo de entrega:** `internal_analysis`.
- **Población y grain:** empleados regulares activos; un empleado-snapshot
  mensual único en `hrda.post_hire_monthly_worker_dtls`.
- **Fecha de conocimiento:** 2026-08-23; ningún evento posterior entra al
  conteo.
- **Tipo semántico:** `derived_feature`: la categoría resulta de combinar
  evento, fecha, episodio laboral e historial observable.
- **Uso exploratorio en attrition:** contexto descriptivo para examinar la
  distribución de eventos registrados entre grades actuales. No es una señal
  causal ni una clasificación operativa para personas.

La regla válida exige `is_promo=1`, fecha de promoción presente, no posterior
al corte ni a su snapshot de origen y fecha igual o posterior al inicio del
episodio vigente (`max_hire_rehire_date`). Sólo se deduplica el par idéntico
empleado+fecha, internamente en SQL. Los eventos anteriores al rehire se
excluyen del episodio vigente. No se infiere primera promoción, primer empleo,
historial completo ni contratación directa en el grade.

## Validaciones ejecutadas — 2026-09-10

### 1. Integridad del snapshot, grade y episodio

- **Pregunta y motivo:** ¿cada conteo parte de un empleado-snapshot único con
  `compensation_grade` y episodio actual completos? Sin esto se podrían mezclar
  grades o episodios en una misma persona.
- **Método y evidencia:** consulta agregada
  `queries/audits/promotion_history_by_compensation_grade_integrity_20260823.sql`
  sobre `hrda.post_hire_monthly_worker_dtls`.
- **Regla de aceptación:** cero IDs faltantes, duplicados, conflictos de grade
  o episodio, grades/episodios faltantes y fechas de inicio futuras; los
  renglones fuente deben reconciliar exactamente con empleados únicos.
- **Métricas observadas:** 50,043 renglones y 50,043 empleados únicos; cero
  faltantes, duplicados, conflictos o inicios futuros.
- **Conclusión e impacto:** el snapshot fijo permite describir el grade actual
  sin cambiar ningún score v4. No prueba una definición HRIS de carrera.
- **Acción:** repetir la auditoría antes de cualquier refresh de corte.

### 2. Integridad de eventos y frontera de rehire

- **Pregunta y motivo:** ¿los eventos seleccionados corresponden a promociones
  registradas y conocidas dentro del episodio laboral vigente? Un flag o fecha
  inválidos alteraría `0/1/2+`.
- **Método y evidencia:** misma auditoría agregada; valida dominio de
  `is_promo`, alineación flag-fecha, fechas futuras, fechas posteriores a su
  snapshot, conflictos históricos y la selección posterior al rehire.
- **Regla de aceptación:** todos esos contadores de error deben ser cero; los
  eventos previos al episodio pueden existir, pero ninguno puede seleccionarse.
- **Métricas observadas:** cero flags/fechas inválidos, futuros, posteriores al
  snapshot, conflictos o eventos seleccionados antes del episodio; 311 eventos
  candidatos anteriores al episodio se excluyeron; 0 pares duplicados de
  evento requirieron deduplicación.
- **Conclusión e impacto:** `0/1/2+` significa número de eventos válidos
  registrados dentro del episodio observable, no “nunca promovido”.
- **Acción:** conservar la misma frontera de rehire si la matriz se lleva a
  una feature modelable; definir por separado la semántica de política de
  promoción antes de usarla como score.

### 3. Observabilidad histórica y cuatro categorías exhaustivas

- **Pregunta y motivo:** ¿la ausencia de un evento se distingue de historia
  incompleta? La fecha mínima observada no permite afirmar que los episodios
  anteriores tengan historial completo.
- **Método y evidencia:** profile agregado
  `queries/profiles/promotion_history_by_compensation_grade_20260823.sql`.
  Todo episodio iniciado antes del inicio observado se asigna a `Partial
  promotion history`, sin importar eventos registrados; para el resto se usa
  el conteo válido 0/1/2+.
- **Regla de aceptación:** 0/1/2+ debe sumar exactamente los episodios
  observables; `Partial promotion history` debe ser exactamente el resto; las
  cuatro categorías deben sumar 50,043.
- **Métricas observadas:** inicio observado `2016-10-23`; 38,776 episodios
  observables y 11,267 parciales; 26,554 pares válidos de evento para 23,180
  empleados; las filas y categorías reconcilian a 50,043.
- **Conclusión e impacto:** la categoría parcial evita convertir historial
  censurado a cero eventos. No modifica los scores v4 históricos.
- **Acción:** no sustituir `Partial promotion history` por “nunca promovido”
  ni por una etiqueta de contratación.

### 4. Pooling dinámico y privacidad de la matriz

- **Pregunta y motivo:** ¿cada celda visible conserva el mínimo de cohorte sin
  eliminar grades de la población?
- **Método y evidencia:** el constructor
  `tools/build_promotion_history_by_compensation_grade_evidence.py` valida las
  cuatro celdas por grade y agrupa los no publicables sólo en `Other grades`.
  La evidencia congelada se guarda en
  `output/distribution/json/promotion-history-by-compensation-grade-evidence-20260910.json`.
- **Regla de aceptación:** un grade individual necesita `n >= 30` en cada una
  de las cuatro celdas; `Other grades` debe reconciliar todos los grades no
  publicables y también tener `n >= 30` por celda. No se guardan IDs, filas,
  fechas individuales ni compensación exacta.
- **Métricas observadas:** 45 grades fuente; 13 grades individuales y 32 en
  `Other grades`; 14 filas visibles; menor celda publicada `n=37`.
- **Conclusión e impacto:** la matriz es publicable sólo como análisis interno
  agregado. Los labels de grade no revelan compensación exacta.
- **Acción:** conservar la etiqueta `Internal exploratory analysis`; ante un
  destino compartible, revisar de nuevo la política de presentación.

Los hashes SHA-256 del SQL y de los resultados agregados se almacenan en la
evidencia congelada. Este documento es contexto acumulado: no habilita un score
2 ni reemplaza una futura validación de definición, política de promoción o
uso predictivo.
