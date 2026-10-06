# Catalogo observado de Compensation grade

## Alcance

Esta nota describe el mapping observado entre `compensation_grade`,
`job_level_primary_position`, `level_grouped` y `management_level`.
El corte de conocimiento es `2026-08-25` y el ultimo snapshot utilizado es
`2026-08-23`. La poblacion es `worker_type = 'Employee'`,
`employee_type = 'Regular'` y `active_status = 1`.

La regla de divulgacion exige al menos 30 empleados distintos por categoria.
El catalogo de abajo es, por tanto, el mapping observable de categorias con
cohorte suficiente; no representa necesariamente todos los grades existentes.

## Hallazgo principal

El sufijo numerico no tiene un significado universal fuera de su prefijo.
Por ejemplo, `P40`, `R40` y `T40` se observan en la banda `6 - Staff & /Mgr`,
mientras `M40` se observa en `4 - Mgrs Corp` y `S40` en `9 - Support`.
Por eso no se debe ordenar ni interpretar `40`, `50` u otro sufijo sin
considerar el prefijo y el campo de nivel relacionado.

En el ultimo snapshot, cada una de las 36 categorias compartibles se asocia a
un solo `job_level_primary_position`. El mapping de `level_grouped` es estable
para la mayoria, pero hubo cambios historicos en cuatro grades.

La reconciliacion historica agregada encontro 37 grades con al menos 30
empleados distintos: 33 tuvieron una sola banda `level_grouped` y 4 tuvieron
mas de una por cambios temporales. 36 tuvieron un solo `management_level`; una
categoria tuvo una asociacion adicional de baja frecuencia que no se publica.
Esto confirma que `management_level` y `level_grouped` son dimensiones
relacionadas pero no intercambiables: por ejemplo, `P60` aparece en la banda
`4 - Mgrs Corp` con `management_level = Professional`, mientras grades `M` y
`T` de esa banda aparecen como `Management`.

## Mapping vigente observado

| Grade | `job_level_primary_position` | `level_grouped` | `management_level` |
|---|---|---|---|
| V10 | VP - V10 | 1 - VP & Above | VP/SVP |
| V30 | SVP - V30 | 1 - VP & Above | VP/SVP |
| M60 | Sr Dir Corp - M60 | 2 - Sr Dir | Directors/Sr Director |
| R80 | Sr Dir Tech - R80 | 2 - Sr Dir | Directors/Sr Director |
| T80 | Sr Dir Eng - T80 | 2 - Sr Dir | Directors/Sr Director |
| M50 | Dir Corp - M50 | 3 - Princ/Directors | Directors/Sr Director |
| R60 | Principal Eng - R60 | 3 - Princ/Directors | Directors/Sr Director |
| T60 | Principal/Mgr Eng - T60 | 3 - Princ/Directors | Directors/Sr Director |
| T70 | Dir Eng - T70 | 3 - Princ/Directors | Directors/Sr Director |
| M05 | Supv Mfg - M05 | 4 - Mgrs Corp | Management |
| M10 | Supv/Assoc Mgr Corp - M10 | 4 - Mgrs Corp | Management |
| M20 | Manager Corp - M20 | 4 - Mgrs Corp | Management |
| M30 | Sr Mgr Corp - M30 | 4 - Mgrs Corp | Management |
| M40 | Staff Mgr Corp - M40 | 4 - Mgrs Corp | Management |
| P60 | Principal Corp - P60 | 4 - Mgrs Corp | Professional |
| P50 | Sr Staff Corp - P50 | 5 - Sr Staff & /Mgr | Professional |
| R50 | Sr Staff Eng - R50 | 5 - Sr Staff & /Mgr | Professional |
| T50 | Sr Staff/Mgr Eng - T50 | 5 - Sr Staff & /Mgr | Management |
| P40 | Staff Corp - P40 | 6 - Staff & /Mgr | Professional |
| R40 | Staff Eng - R40 | 6 - Staff & /Mgr | Professional |
| T40 | Staff/Mgr Eng - T40 | 6 - Staff & /Mgr | Management |
| P30 | Senior Corp - P30 | 7 - Senior & Lead | Professional |
| P35 | Lead Corp - P35 | 7 - Senior & Lead | Professional |
| R30 | Sr Eng - R30 | 7 - Senior & Lead | Professional |
| R35 | Lead Eng - R35 | 7 - Senior & Lead | Professional |
| P10 | Assoc Corp - P10 | 8 - Assoc & Int/Eng | Professional |
| P20 | Intermediate Corp - P20 | 8 - Assoc & Int/Eng | Professional |
| R10 | Assoc Eng - R10 | 8 - Assoc & Int/Eng | Professional |
| R20 | Engineer - R20 | 8 - Assoc & Int/Eng | Professional |
| S00 | Mfg Operator I - S00 | 9 - Support | Support |
| S05 | Mfg Operator II - S05 | 9 - Support | Support |
| S10 | Support I - S10 | 9 - Support | Support |
| S20 | Support II - S20 | 9 - Support | Support |
| S30 | Support III - S30 | 9 - Support | Support |
| S40 | Support IV - S40 | 9 - Support | Support |
| S50 | Support V - S50 | 9 - Support | Support |

`S60` aparece en la historia agregada como `Support VI - S60`, pero no supera
el umbral de 30 empleados distintos en el ultimo snapshot y por eso no se
incluye en el mapping vigente compartible.

## Cambios historicos observados

La relacion no fue completamente estable durante toda la historia:

- `M05`: `Misc` hasta `2023-11-19`; `4 - Mgrs Corp` desde `2023-12-24`.
- `P60`: `3 - Princ/Directors` hasta `2023-11-19`; `4 - Mgrs Corp` desde
  `2023-12-24`. Su `management_level` observado permanecio `Professional`.
- `S00`: `Misc` hasta `2023-11-19`; `9 - Support` desde `2023-12-24`.
- `S05`: `Misc` hasta `2023-11-19`; `9 - Support` desde `2023-12-24`.

Estos cambios parecen corresponder a una actualizacion del mapping de
`level_grouped`, pero no demuestran por si solos un cambio real de puesto o de
compensacion. Deben tratarse como cambios de version del mapping hasta contar
con lineage de HRIS/Compensation.

## Fuentes y grado de autoridad

- La tabla principal es `hrda.post_hire_monthly_worker_dtls`; los cuatro campos
  son columnas directas.
- `hrda.compgrade_benefitsusd_mapping` existe, pero solo contiene
  `compensation_grade_profile` y `benefits_allocation_usd`; no es un catalogo de
  jerarquia de grades.
- `hrda.annual_review_report` contiene `grade`, `job_level` y
  `management_level`, pero es un reporte de ciclo con datos de empleados, no un
  diccionario de definiciones.
- El workbook Tableau
  `references/tableau/organizational-csi-dashboard/Organizational CSI Dashboard.twb`
  contiene una clasificacion manual de `job_level_primary_position_manager`
  hacia bandas como `2 - Sr Dir`, `3 - Princ/Directors`, `5 - Sr Staff & /Mgr`,
  `6 - Staff & /Mgr`, `7 - Senior & Lead`, `8 - Assoc & Int/Eng` y
  `9 - Support`. Es una fuente operativa de contexto, no una aprobacion formal
  de negocio.
- La consulta de comentarios de Redshift no encontro comentarios oficiales
  para estas columnas.

## Uso recomendado

Para cohortes y reporting, usar `level_grouped` o `management_level` en lugar
de derivar una jerarquia parseando el texto de `compensation_grade`.
Conservar `compensation_grade` como categoria gobernada y sensible. No afirmar
que las letras (`M`, `P`, `R`, `S`, `T`, `V`) tienen un significado universal
sin documentacion oficial de Compensation.

## Evidencia reproducible

- `queries/audits/compensation_grade_current_catalog_20260825.sql`
- `queries/audits/compensation_grade_job_level_catalog_20260825.sql`
- `queries/audits/compensation_grade_level_mapping_summary_20260825.sql`
- `queries/audits/compensation_grade_to_level_relationships_20260825.sql`
- `queries/audits/compensation_grade_mapping_contradictions_20260825.sql`
- `queries/audits/compensation_grade_mapping_metadata_20260825.sql`
- `queries/audits/compensation_grade_documentation_comments_20260825.sql`

Todas las consultas usan solo resultados agregados, el corte temporal indicado
y un minimo de 30 empleados distintos para compartir categorias.

## Teoria de trabajo (no confirmada)

Esta es una hipotesis de trabajo, no una definicion oficial de Compensation.
Se basa en los nombres observados de `job_level_primary_position`, el orden
manual del workbook Tableau y las asociaciones agregadas de Redshift:

- `M` podria representar una escalera de management corporativo u operativo:
  desde `Supv Mfg - M05` y `Manager Corp - M20` hasta `Sr Dir Corp - M60`.
- `P` podria representar una escalera profesional corporativa: `Assoc Corp`,
  `Intermediate Corp`, `Senior Corp`, `Lead Corp`, `Staff Corp`, `Sr Staff
  Corp` y `Principal Corp`.
- `R` podria representar una escalera de engineering/technical: `Assoc Eng`,
  `Engineer`, `Sr Eng`, `Lead Eng`, `Staff Eng`, `Sr Staff Eng`, `Principal
  Eng` y `Sr Dir Tech`.
- `S` podria representar la escalera de support/manufacturing operations:
  `Mfg Operator I/II` y `Support I` a `Support VI`.
- `T` podria representar una escalera engineering-management o de roles
  tecnicos con responsabilidad de management: `Staff/Mgr Eng`, `Sr Staff/Mgr
  Eng`, `Principal/Mgr Eng`, `Dir Eng` y `Sr Dir Eng`.
- `V` parece corresponder a la escalera ejecutiva VP/SVP. El workbook tambien
  contiene referencias a niveles `EVP` con prefijo `X`, pero esos valores no
  forman parte del catalogo compartible actual.
- `Y10` aparece en Tableau como `Temporary/Acquisition` dentro de `Misc`; no se
  ha validado suficientemente en la poblacion actual.

El sufijo parece ordenar seniority dentro de una misma familia, pero no es una
escala transversal: `R40`, `P40` y `T40` comparten banda observada, mientras
`M40` y `S40` pertenecen a otras bandas. Los cambios de `M05`, `P60`, `S00` y
`S05` muestran ademas que el mapping puede cambiar por version.

Por tanto, esta teoria solo sirve para orientar preguntas y validaciones. No
debe usarse como definicion de negocio, mapping oficial, regla de modelado ni
evidencia suficiente para elevar el score. Para confirmarla hace falta un
catalogo o lineage aprobado por HRIS/Compensation.
