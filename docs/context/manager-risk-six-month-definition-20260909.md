# Decisión de diseño: señales de contexto del manager a seis cierres

**Estado:** ambas distribuciones agregadas se ejecutaron el 2026-09-09 y
pasaron los controles definidos. Son contexto histórico agregado para análisis
interno; no son etiquetas, rankings, evaluaciones de desempeño ni reglas
aprobadas de intervención para managers.

## Población de managers

Un manager en el cierre mensual `t` es toda persona que aparece como
`manager_employee_id` de al menos un empleado con
`worker_type='Employee'`, `employee_type='Regular'` y `active_status=1` en
ese mismo cierre. Esta relación directa define la membresía y el tamaño del
equipo; `management_level` no se utiliza para decidir quién es manager.

Los campos almacenados `reg_non_intern_dir_reports` y `all_dir_reports` se
mantienen como controles de calidad, no como definición. La auditoría ejecutada
el 2026-09-09 para los últimos 11 cierres, incluido 2026-09-27, no encontró duplicados de
empleado-snapshot ni managers sin registro contemporáneo. En el último cierre,
los 10,567 managers reconstruidos tuvieron `reg_non_intern_dir_reports > 0`,
pero sólo 9,935 (94.0%) coincidieron exactamente en el conteo de reportes;
`all_dir_reports` coincidió exactamente para 7,850 (74.3%). Por ello, ambos
conteos son proxies útiles, pero no sustituyen `manager_employee_id`.

**Evidencia:**
`queries/audits/manager_population_direct_reports_reconciliation_20260909.sql`.

## Ventana común

Ambas señales usan siete cierres dinámicos para formar seis intervalos fiscales
contiguos: `(2026-03-29, 2026-04-26]`, `(2026-04-26, 2026-05-24]`,
`(2026-05-24, 2026-06-28]`, `(2026-06-28, 2026-07-26]`,
`(2026-07-26, 2026-08-23]` y `(2026-08-23, 2026-09-27]`.

Sólo entra al numerador una salida distinta por `employee_id` y `term_date`
con `term_type = 'Voluntary'`. `Voluntary Exception`, involuntarias, nulos y
eventos posteriores al corte quedan excluidos. La salida se asocia únicamente
cuando existe una exposición única del empleado en el **inicio del intervalo**
que contiene la fecha de salida; esta regla evita una atribución temporal amplia.

La historia de eventos repetida en snapshots se deduplica antes de atribuir:
hubo 4,059 filas repetidas de fuente, pero cero duplicados en la clave analítica
de evento. De 1,544 salidas Voluntary únicas, 1,472 tuvieron atribución única.
Las 72 sin exposición inicial única se excluyen explícitamente; no se imputan a
cero ni a otro manager.

## High turnover under this person

Es una distribución descriptiva `0 / 1 / 2+` de salidas Voluntary estrictas
del equipo histórico observable de cada manager. El bucket se asigna sólo a
reportes directos regulares activos en el corte que tienen historial de
exposición observable. No mide causalidad y no evalúa a un manager.

**Resultado al corte 2026-09-27:**

- 10,567 managers actuales y 50,208 reportes directos actuales.
- 10,487 managers y 50,018 reportes tienen historia observable.
- 80 managers y 190 reportes quedan como cobertura histórica desconocida; no
  se convierten en bucket `0`.
- Distribución de reportes observables: `0` = 42,489; `1` = 5,843; `2+` =
  1,686.
- Todos los buckets publicados superan `n >= 30`.

La regla de aceptación exigía seis intervalos contiguos, cero duplicados de
exposición o membresía actual, cero atribuciones múltiples, reconciliación de
buckets y que los reportes `2+` no superaran la población observable. Todos los
controles pasaron.

**Evidencia:**
`queries/audits/high_turnover_under_manager_6m_distribution_20260909.sql`.

## High risk manager

Es una distribución agregada del ratio continuo suavizado
observado/esperado de salidas Voluntary estrictas; no es la misma señal que el
bucket `0 / 1 / 2+`. El esperado se estratifica por intervalo, `region`,
`job_family`, `job_level_primary_position` y banda de tenure disponible al
inicio del intervalo. Las celdas con menos de 30 empleado-intervalos usan la
tasa global del intervalo. Un prior de 60 empleado-intervalos suaviza el ratio
hacia 1 para reducir la volatilidad de equipos pequeños.

**Evidencia ejecutada:**
`queries/audits/high_risk_manager_6m_score_distribution_20260909.sql`.

**Resultado al corte 2026-09-27:**

- 10,487 managers y 50,018 reportes tienen score histórico observable.
- 80 managers y 190 reportes carecen de historia suficiente y permanecen
  separados como desconocidos.
- Bandas agregadas de managers: `<0.50×` = 566; `0.50–<1.00×` = 8,535;
  `1.00–<1.50×` = 268; `≥1.50×` = 1,118.
- Las bandas reconcilian exactamente contra 10,487 managers y 50,018 reportes
  observables; cada grupo publicado supera `n >= 30`.

La regla de aceptación exigía, además de la ventana y atribución comunes, tasa
global positiva, cero duplicados de score, cero asignaciones múltiples y
reconciliación de bandas por managers y reportes. Todos los controles pasaron.

El ratio se conserva como distribución agregada contextual. No se publica una
identidad, ranking, clasificación individual ni un umbral aprobado de “high
risk”; cualquier decisión de uso individual requeriría gobernanza, calibración
temporal adicional y aprobación explícita.

## Límites de interpretación

La pertenencia actual al equipo y la exposición histórica no prueban que un
manager haya causado una salida. Las señales describen patrones históricos
observables en una ventana fiscal concreta y deben volver a ejecutarse si cambia
el corte, la población, la definición de Voluntary o la regla de atribución.
