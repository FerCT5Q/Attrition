# Estado de la ronda B + playbook V11

La referencia autorizada es `output/distribution/attrition-43-variable-distributions-v11.html`.
Se conservan los ocho predictores y dos interacciones de B. Se compararon
B + X, combinaciones pequeñas de RH y preguntas/temas de QVoice, con selección
temporal interna y evaluación externa. La ejecución completa comenzó el
12-oct-2026 a las 15:30 UTC y terminó a las 17:10 UTC. La verificación final pasó.

Salida verificada: `output/analysis/engineering/20261011/b-playbook-v11-v1/`.
El preflight, la correspondencia V11 y la configuración ampliada ya están
congelados; no reanudar las rondas b-incremental-v1/v2. El log está en
`output/analysis/engineering/20261011/b-playbook-v11-v1-training.log`.

Preparaciones terminadas y evidencias que habilitan entradas:

- Ciudad: `v11-city.json`; mercado: `v11-labor-market.json`.
- Modalidad V11: **`v11-arrangement-v2.json`**, con el valor completo
  `Interim Modified – Short-Term Remote Work`. La primera revisión no
  identificaba ese grupo y queda sustituida.
- Adquisición detallada: `v11-acquisition.json`.
- Entrada al grado, tiempo desde entrada y pay track:
  `v11-grade-entry.json`.
- Jerarquía: **`v11-hierarchy-v3.json`** y
  `v11-hierarchy-synthetic-v3.json` (47 casos, cero diferencias).
  Las variantes v1/v2 fueron demasiado pesadas y no habilitan resultados.
- Contexto de seis intervalos: **`v11-manager6-v2.json`**,
  `v11-manager-feed.json`, `v11-manager-gate-synthetic.json`.
  Inicio observado del feed: **2022-10-23**; exigir seis intervalos posteriores
  completos. El fixture integral grande se interrumpió; el filtro real sí
  pasó diez casos sintéticos enfocados.

Terminada: auditoría **manager18-v3**, con 18 intervalos completos posteriores
a 2022-10-23, promedio de equipo >=4, al menos dos salidas y umbral 1.3 veces
el benchmark. v2 falló por pérdida de precisión decimal del control
independiente; v3 usa doble precisión y reconcilia sin cambiar la feature.
Los siete años pasaron, con 24,295 persona-fotos observables en 2026.

SQL activos para carga adicional:

- `queries/profiles/engineering_b_v11_categories_person_month_20261011_v2.sql`
  → work_city, labor_market_detail, work_arrangement_v11, acquisition_detail.
- `queries/profiles/engineering_b_v11_grade_entry_person_month_20261011.sql`
  → current_grade_entry_path, time_since_grade_entry_band, pay_track_detail.
- `queries/profiles/engineering_b_v11_hierarchy_person_month_20261011_v3.sql`
  → hierarchy_depth_band.
- `queries/profiles/engineering_b_v11_manager_history_person_month_20261011_v3.sql`
  → manager_observed_expected6_band, manager_team_exits6_v11,
  manager_above_average18.

Limitación confirmada: IOS tiene seis motivos preparados descriptivamente,
pero todas las cargas/modificaciones actuales son 2026-10-11. No se verifica
conocimiento histórico de resoluciones. `v11-ios-knowledge.json` conserva el
fallo; los seis motivos y el antiguo adicional `ios_12m` quedan fuera de la
selección temporal. No se retira ningún término de B.

Terminadas: proximidad y zonas horarias (`v11-timezone-v3.json`,
`v11-timezone-prepared.json`, `v11-timezone-dst.json`). SQL activo v3;
mapping público en RAM. Las dos consultas anteriores se cancelaron por coste.

Terminada la preparación de distancia (`v11-commute-inputs.json`,
`v11-commute-prepared.json`, `v11-commute-mapping.json`). Sólo es una
aproximación postal a oficinas de la ciudad para Onsite: todo el mapping
resuelve por ciudad, hay varias oficinas posibles y falta país de domicilio
estructurado. No presentarla como commute real validado.

Terminados: comentarios QVoice de 2024/2025, con catorce representaciones,
taxonomías completas congeladas y desfase anual. La llave duplicada de
encabezado 2024 reconcilió en 36,806 pares; se usa la columna original.
La evidencia `v11-qvoice-comments.json` pasó. Las preparaciones pendientes
se cerraron el 12-oct-2026:

- Aplicaciones: `applications` termina en octubre de 2024; la vista actual
  tiene eventos recientes pero no un historial verificado del enlace.
- Annual Review: grain limpio, AR20–AR25; cargas de 2025 sin publicación
  histórica confirmada. El flag de ciclo no se añade.
- Heartbeat: 2024 sin escalas; 2025 con 52 de 53, falta Q42. No se cambia la
  definición exacta ni se adelanta 2026.
- Talent index: una tabla y tres timestamps técnicos; falta fecha de negocio.
- Rol almacenado: `v11-stored-role.json` pasó; primer dato 24-ago-2025.
  Se incorpora con la limitación de historia y semántica del campo almacenado.

El cargador/modelo ya admite `extra_hr_queries` y `extra_evidence` en la
configuración. El informe acepta `playbook_scope` para usar la correspondencia
V11 en lugar del viejo inventario. El scope final está en
`config/b_playbook_v11_scope_20261012.json`. Se añadió
un diagnóstico agregado de captura al 30% sin la restricción de los grupos,
con empates proporcionales; no cambia la selección ni publica rankings.

Pasaron 101 pruebas: 31 de B incremental, geografía y comentarios; 17 del
modelo y del helper read-only; 53 del skill de assessment. El precheck
`inputs-ready.json` pasó con 35 entradas de evidencia aceptadas, queries
read-only y hashes de fuentes vigentes. La ejecución terminó como
`completed_experimental`, con 12 registros de selección y 18 modelos.
La verificación encontró 205 intentos externos RH y 204 QVoice con ajuste
correcto; 27 intentos RH se distinguen por historia insuficiente.
La configuración ejecutable es `config/engineering_b_playbook_v11_20261012.json`:
41 candidatas RH y 51 QVoice; IOS queda fuera y B se conserva íntegro.
Las 42 vistas analíticas del V11 están relacionadas con sus representaciones;
el nombre del archivo «43 variables» no es un conteo de columnas independientes.
La fuente activa de compensación de la ronda anterior sigue siendo
`engineering_b_incremental_pending_person_month_20261011_v2.sql`.

El slide 3 ya quedó corregido en
`output/presentations/20261011-2034_evolucion-b-cq-mejora-modesta/presentacion-eng.html`;
no necesita repetirse ese cambio.

Documentación final disponible:

- [Diccionario en Excel](../../output/analysis/engineering/20261011/b-playbook-v11-v1/documentacion/diccionario.xlsx).
- [Índice de las fichas](../../output/analysis/engineering/20261011/b-playbook-v11-v1/documentacion/diccionario.md).
- [Informe de resultados](../../output/analysis/engineering/20261011/b-playbook-v11-v1/documentacion/informe.md).
- [Contexto y límites de la entrega](../context/b-playbook-v11-documentacion-variables.md).

El suplemento incluye 102 representaciones, siete exclusiones, 109 fichas,
612 decisiones y 217 registros de codificación. Documenta los valores de
origen, transformaciones, bandas, categorías, faltantes, temporalidad,
referencias aprendidas y motivos por periodo. El Excel se reconcilió celda
por celda con sus tablas fuente; también se verificaron los hashes y 1085
enlaces locales. Tiene manifest propio y conserva el manifest de entrenamiento.
