# Tiempo en perfil de puesto y nivel detallado

## Estado de publicación

`internal_analysis` — publicado como análisis exploratorio en la lámina 26,
con la navegación `Time in role and level`. No presenta los dos relojes como
definiciones de carrera aprobadas por HRIS: describe distribuciones calculadas
con campos almacenados y declara los campos exactos en la tarjeta derecha.

La evidencia histórica disponible no confirma de forma autoritativa los dos
constructos seleccionados: el workbook de Tableau sólo muestra que consume los
campos y el assessment v4 anterior dejó `Definition=1`. Ninguna de esas fuentes
sustituye una confirmación del propietario de HRIS. La lámina se etiqueta como
exploratoria, pero esa brecha no bloquea este uso interno.

## Flujo histórico y decisión actual

1. El assessment v4 de 16-ago-2026 encontró las fechas disponibles y cobertura
   histórica, pero no aprobó la definición, los resets ni el join temporal.
2. Para el corte comparable de 23-ago-2026 se preparó una auditoría agregada de
   unicidad, fechas, reingresos y transiciones de nivel; en paralelo se preparó
   el profile de distribuciones con bandas comunes.
3. La auditoría devuelve población y cobertura completas, pero no satisface la
   regla de transición del nivel detallado. Por decisión de uso, se congeló
   evidencia `exploratory` el 10-sep-2026 y se actualizó el deck sin elevar la
   semántica de los campos a una definición validada.

## Campos mostrados en la tarjeta derecha

La tarjeta derecha de la lámina 26 identifica explícitamente las variables
usadas para que la lectura no dependa de una interpretación implícita:

- **Gráfica izquierda — `Time in current job profile`:**
  `time_in_job_profile_start_date + max_hire_rehire_date`.
- **Gráfica derecha — `Time at current detailed level`:**
  `levelentrydate + job_level_primary_position + max_hire_rehire_date`.
- **Apoyo solamente:** `time_in_role`; no se usa para calcular ninguna de las
  dos gráficas.

El corte y la población también aparecen en la tarjeta: 23-ago-2026 y 50,043
empleados regulares activos. La lista de campos indica qué se usó; no afirma
que esos campos sean la definición oficial de los constructos.

## Definiciones propuestas, condicionadas a aprobación de HRIS

- **Tiempo en perfil de puesto actual:** antigüedad por aniversarios desde el
  máximo entre `time_in_job_profile_start_date` y `max_hire_rehire_date`.
- **Tiempo en nivel detallado actual:** antigüedad por aniversarios desde el
  máximo entre `levelentrydate` y `max_hire_rehire_date`, sólo si
  `job_level_primary_position` identifica el nivel detallado actual.
- **Reingreso:** ambos relojes toman la fecha posterior entre su fecha
  almacenada y `max_hire_rehire_date`.
- **Resets por constructo:** un cambio de perfil reinicia sólo el reloj de
  perfil; un cambio de nivel detallado reinicia sólo el reloj de nivel. Los
  flags de promoción, democión y transferencia son contexto de validación, no
  disparadores automáticos. Manager, ubicación, centro de costo, transferencia,
  familia de puesto y otros eventos no reinician un reloj si no cambia el
  constructo elegido.
- **`time_in_role`:** campo de apoyo para auditoría; no define ninguna gráfica.

## Validaciones y resultados agregados

### 1. ¿El snapshot y los relojes son calculables sin duplicados ni fechas futuras?

**Motivo.** Una distribución requiere un único empleado-snapshot y no puede
mezclar fechas futuras ni reglas de reingreso ambiguas.

**Método.** Consulta agregada
[`role_level_tenure_transition_audit_20260823.sql`](../../../queries/audits/role_level_tenure_transition_audit_20260823.sql)
sobre `hrda.post_hire_monthly_worker_dtls`; población: empleados activos,
regulares, `fis_mo_end_dt='2026-08-23'`; grain: empleado-snapshot. La consulta
no emite IDs, títulos, códigos ni fechas individuales.

**Regla de aceptación.** Cero duplicados o conflictos, cero fechas futuras y
cero flags de reingreso sin `max_hire_rehire_date`.

**Métricas observadas (10-sep-2026).** 50,043 filas y 50,043 empleados únicos;
0 duplicados, 0 conflictos, 0 fechas futuras y 0 flags de reingreso sin fecha.
Los dos relojes son calculables para 50,043 empleados; el ajuste por reingreso
afecta 0 inicios de perfil y 114 inicios de nivel.

**Conclusión e impacto.** Esta parte pasa como evidencia técnica agregada. No
aprueba la semántica del campo ni la gráfica por sí sola.

### 2. ¿Los cambios de nivel detallado concuerdan con `levelentrydate`?

**Motivo.** La propuesta usa `job_level_primary_position` como constructo de
nivel. Si su transición no concuerda con el reset de fecha, el reloj no es
reproducible.

**Método.** La misma auditoría compara snapshots consecutivos separados por
20–45 días. Los cambios de `job_code` o `job_title` se cuentan sólo como proxy
agregado de comportamiento del perfil; nunca sustituyen la definición de
perfil.

**Regla de aceptación.** Cero transiciones de nivel sin reset de
`levelentrydate` explicable y cero resets de fecha sin cambio de nivel, salvo
el ajuste explícito por reingreso.

**Métricas observadas (10-sep-2026).** 2,950,970 snapshots consecutivos
comparables; 43,805 cambios de nivel detallado; 37,707 con reset de fecha en el
intervalo; 6,098 transiciones sin reset explicable y 28 resets sin cambio de
nivel. Como contexto del perfil, se observaron 9,142 resets de fecha, de los
cuales 9,140 coincidieron con un cambio de código o título y 2 no; esos proxies
no se usan para resolver la brecha.

**Conclusión e impacto.** La validación estricta no pasa: los 6,098 y 28 casos
agregados superan la regla de aceptación para una definición validada. Para la
lámina exploratoria, se conservan como resultado de auditoría; no se otorga
`Definition=2` ni se interpreta la distribución como definición oficial.

### 3. ¿Las bandas serían comparables y privadas si se resolviera la definición?

**Motivo.** Las dos gráficas deben comparar los mismos intervalos sin publicar
una cohorte menor a 30.

**Método.** Consulta agregada
[`role_level_tenure_distribution_20260823.sql`](../../../queries/profiles/role_level_tenure_distribution_20260823.sql)
con bandas por aniversario: `<1`, `1–<2`, `2–<3`, `3–<5`, `5–<10` y `10+`
años. El constructor agrupa bandas adyacentes idénticamente en ambos relojes
si cualquiera queda por debajo de 30.

**Regla de aceptación.** Cada distribución suma exactamente su denominador
calculable, sus porcentajes suman 100% y cada banda visible de ambos relojes
tiene `n >= 30`.

**Métricas observadas (10-sep-2026).** Ambas poblaciones calculables son
50,043. Perfil de puesto: 15,250; 11,791; 7,558; 9,897; 4,981; 566. Nivel
detallado: 14,008; 10,890; 7,383; 10,152; 6,390; 1,220. Cada banda cumple el
mínimo y los totales reconcilian, pero este resultado no elimina la brecha
semántica y de transición anterior.

**Conclusión e impacto.** La privacidad y aritmética de display son suficientes
para el análisis interno exploratorio. No resuelven la brecha semántica ni
habilitan una publicación validada.

## Evidencia y artefactos

- Auditoría: `queries/audits/role_level_tenure_transition_audit_20260823.sql`.
- Profile: `queries/profiles/role_level_tenure_distribution_20260823.sql`.
- Constructor: `tools/build_role_level_tenure_evidence.py`; su modo por defecto
  es fail-closed y `--exploratory` produce la evidencia caveatada autorizada
  para este análisis interno.
- Actualización focalizada del deck: `tools/build_distribution_html_v2.py`
  con `--refresh-role-level-tenure-slide`.

La evidencia congelada de esta publicación es
`output/distribution/json/role-level-tenure-distribution-evidence-20260910.json`.
Contiene sólo métricas agregadas, conteos de bandas y hashes de procedencia.

El constructor sólo acepta un JSON de confirmación autoritativa con:
`artifact_type='authoritative_lineage_confirmation'`, autoridad, fecha,
referencia de fuente, aprobación explícita y estas confirmaciones exactas:

```json
{
  "time_in_job_profile_start_date_confirmed_construct": "current_job_profile_start",
  "job_level_primary_position_confirmed_construct": "current_detailed_level",
  "approved": true
}
```

No guardar IDs de empleados, filas de resultados, títulos, códigos ni fechas
individuales en ese artefacto. El constructor persiste sólo métricas agregadas,
bandas, hashes y el resumen de la confirmación.

## Revisión de attrition por cohorte — 20-sep-2026

Para responder la revisión de la lámina, la distribución y el attrition usan
la misma cohorte: el snapshot baseline `2025-08-24`; después se cuentan sus
salidas voluntarias en `(2025-08-24, 2026-08-23]`. Por banda, la tasa es:
`salidas voluntarias de la banda / empleados de la banda en el baseline`.

La distribución visible y la columna izquierda ahora se llaman **Time at
detailed level** y usan
`GREATEST(levelentrydate, max_hire_rehire_date)` con
`job_level_primary_position` poblado. El snapshot baseline tiene 41,757
empleados válidos, 0 duplicados, 0 conflictos y 0 registros inválidos. La
columna derecha mantiene **Time in role** con el campo almacenado y la misma
ventana temporal.

La evidencia agregada está en
[`qvoice_time_at_detailed_level_august_12m_attrition_20260920.sql`](../../../queries/audits/qvoice_time_at_detailed_level_august_12m_attrition_20260920.sql)
y en el JSON de presentación generado el 20-sep-2026. Las tasas son
descriptivas/exploratorias; la confirmación oficial de la semántica HRIS y de
los resets sigue siendo una acción pendiente independiente del cálculo temporal.

## Si se requiere una definición validada en el futuro

1. Obtener la confirmación formal de HRIS para los dos constructos.
2. Investigar y clasificar agregadamente las 6,098 transiciones y 28 resets
   antes de declarar que son excepciones válidas o corregir la fuente.
3. Ejecutar nuevamente ambas consultas y congelar evidencia en modo estricto.
   Hasta entonces, conservar la etiqueta exploratoria y la lista explícita de
   variables de la tarjeta derecha.

Este documento es contexto acumulado; no sustituye evidencia actual ni una
confirmación del propietario de datos.

## Revisión de la lámina 27 — 18-sep-2026

**Decisión.** A petición de la revisión, la lámina de distribución deja de
mostrar el tiempo en nivel detallado. Ahora compara sólo **Time in job
profile** y **Time in role**. Se eliminó el término `field proxy` de la
audiencia y no se presenta a los dos campos como equivalentes.

**Flujo histórico.** `time_in_job_profile_start_date` empezó a tener cobertura
completa en nov-2025; `time_in_role` en ago-2025. En el último snapshot
disponible (27-sep-2026) las dos medidas tienen cobertura completa, no hay
duplicados ni conflictos de empleado-snapshot y no hay valores negativos de
`time_in_role`. Cada banda visible supera `n >= 30`.

**Pregunta.** ¿Se puede mostrar attrition voluntario anual junto a las dos
distribuciones actuales?

**Motivo.** Una tasa anual debe usar el valor conocido al snapshot y una ventana
posterior completa; una única observación histórica no debe compararse con una
distribución de un snapshot más reciente.

**Método.** La evidencia agregada
[`20260918_time_in_job_profile_time_in_role_slide_evidence.sql`](../../../queries/audits/20260918_time_in_job_profile_time_in_role_slide_evidence.sql)
valida el grain, las bandas y el join temporal de salidas voluntarias. El perfil
[`20260918_time_in_job_profile_time_in_role_coverage.sql`](../../../queries/profiles/20260918_time_in_job_profile_time_in_role_coverage.sql)
comprueba la cobertura por snapshot.

**Regla de aceptación.** Para publicar una tasa anual comparable, una medida
requiere cobertura de al menos 95% en tres snapshots mensuales consecutivos con
seguimiento completo de 12 meses, además de `n >= 30` por banda y por evento.

**Métricas observadas.** `Time in job profile` alcanza 11 snapshots consecutivos
de cobertura alta, pero ninguno con seguimiento anual completo. `Time in role`
alcanza 14, pero sólo uno tiene seguimiento anual completo. La regla no pasa
para tasas anuales; sí pasa para las distribuciones actuales.

**Conclusión e impacto.** La lámina muestra sólo las dos distribuciones actuales
y explica en lenguaje sencillo que attrition anual se agregará cuando exista
historia mensual comparable. No se publican tasas, no cambia ningún score y no
se afirma una definición HRIS aprobada.

**Artefactos.** La evidencia congelada es
`output/distribution/json/attrition-43-variable-distributions-v7.time-in-job-profile-time-in-role-evidence-20260918.json`;
el manifest de la revisión es
`output/distribution/json/attrition-43-variable-distributions-v7.time-in-job-profile-time-in-role-revision-20260918.json`.
