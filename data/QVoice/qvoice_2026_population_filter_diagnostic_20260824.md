# Diagnostico de poblacion QVoice 2026

Fecha de ejecucion: 2026-08-24

## Conclusion

La diferencia de cardinalidad entre Excel y Redshift no se explica solamente
por un filtro de empleados regulares o activos. En el snapshot mas cercano al
lanzamiento, los 40,721 registros de Redshift hacen match con workforce, todos
tienen `worker_type='Employee'` y `active_status=1`, pero 2,955 estan fuera
del valor exacto `employee_type='Regular'`.

La brecha total se descompone asi:

```text
42,203 filas Excel - 40,721 filas SQL = 1,482
1,482 = 818 filas Excel sin Favorable - 60 filas SQL sin binario
       + 724 filas con algun Favorable en Excel que no estan en SQL
```

La ultima diferencia, de 724 filas con respuesta, es la pendiente principal.
Esta auditoria no puede atribuirla a un flag de encuesta valida porque ninguna
de las dos estructuras revisadas expone un campo explicito `valid`, `eligible`
o equivalente.

## Poblacion observada

| Metrica | Excel raw | Redshift |
|---|---:|---:|
| Filas de la wave | 42,203 | 40,721 |
| IDs distintos | 42,203 | 40,721 |
| Filas con algun item binario/Favorable | 41,385 | 40,661 |
| Filas sin ningun item binario/Favorable | 818 | 60 |
| Duplicados por ID | 0 | 0 |
| `Response Type` | `EX` en 42,203 | Campo no disponible |

En Excel, los campos de segmentacion encontrados fueron `IC/Mgmt Status` y
`Arriver employees`; no son flags de validez o elegibilidad. `IC/Mgmt Status`
tuvo 33,032 registros `IC` y 9,171 `MGMT`; `Arriver employees` tuvo 767
registros. Estos campos no tienen una contraparte directa documentada en
`hrda.qvoice_survey_data`.

## Validacion contra workforce

### Regla y poblacion

Se tomo como snapshot principal el ultimo `fis_mo_end_dt` menor o igual a la
fecha de lanzamiento `2026-01-07`: `2025-12-28`. La poblacion de referencia es
la regla del proyecto: `worker_type='Employee'`, `employee_type='Regular'` y
`active_status=1`.

La consulta uso IDs solamente dentro de joins y conteos distintos. No publica
filas individuales.

### Resultado del join launch-aligned

| Validacion | IDs QVoice |
|---|---:|
| QVoice total | 40,721 |
| Match en workforce snapshot | 40,721 |
| Sin match | 0 |
| Claves duplicadas en QVoice | 0 |
| Claves duplicadas en workforce snapshot | 0 |
| `worker_type='Employee'` | 40,721 |
| `employee_type='Regular'` | 37,766 |
| `active_status=1` | 40,721 |
| Employee regular activo | 37,766 |

El grupo fuera del valor exacto `Regular` suma 2,955 registros. El breakdown
visible por privacidad muestra `employee_type='Regular Contract (Fixed Term)'
con 2,949; los grupos menores se omitieron del breakdown. No se interpreta el
label de workforce como elegible o inelegible sin una definicion de negocio.

### Sensibilidad de fecha

`hierarchy_date` de QVoice es `2025-12-15`. Si se usa el ultimo snapshot no
posterior a esa fecha, `2025-11-23`, el resultado cambia a 37,501 empleados
regulares activos, 3,019 empleados fuera de `Regular` activos, 18 empleados no
activos y 183 IDs sin match. Esto demuestra sensibilidad temporal, pero no
demuestra que el proceso SQL haya filtrado por esa regla. El snapshot de
lanzamiento es el criterio principal para esta comparacion.

## Flag de encuesta valida

`hrda.qvoice_survey_data` no tiene columnas de validez, elegibilidad,
`Response Type`, tipo de trabajador o tipo de empleado. Por tanto:

- no se puede confirmar un filtro `valid survey` desde la tabla QVoice;
- no se puede comparar directamente `Response Type=EX` contra SQL;
- SQL no es una poblacion puramente `Regular`: conserva 2,955 empleados fuera
  del valor exacto `Regular` en el snapshot de lanzamiento;
- SQL tampoco es una poblacion puramente de filas con respuesta, porque
  contiene 60 filas sin ningun item binario poblado.

## Interpretacion y accion

La hipotesis de que SQL aplica exclusivamente el filtro exacto
`employee_type='Regular'` queda descartada como explicacion de la menor
cantidad de SQL: si ese fuera el filtro aplicado, no deberian permanecer los
2,955 registros fuera de ese valor. Falta confirmar si el negocio considera
`Regular Contract (Fixed Term)` parte de la poblacion elegible.

Los 818 registros Excel sin Favorable probablemente representan filas de la
fuente raw sin respuesta estructurada y no deben compararse como respuestas.
Sin embargo, al excluirlos aun quedan 724 respuestas estructuradas mas en
Excel que en SQL. Esa diferencia requiere una reconciliacion autorizada por
ID o el lineage de ingesta para distinguir entre exclusiones de carga,
versiones de roster, fechas de corte, filtros de fuente o diferencias de
deduplicacion.

La validacion no permite afirmar que los 724 IDs sean validos, elegibles o
regulares, porque esas etiquetas no existen en el Excel/SQL revisados.

## Evidencia reproducible

- [Auditoria de poblacion y flags](../../queries/audits/qvoice_2026_population_filter_diagnostic_20260824.sql)
- [Seguimiento de respuestas y employee_type](../../queries/audits/qvoice_2026_response_population_and_employee_type_followup_20260824.sql)
- [Reconciliacion binaria Excel vs SQL](qvoice_2026_sql_excel_reconciliation_20260824.md)

Las consultas fueron read-only y devolvieron solo agregados. Los resultados
corresponden a la wave `survey_launch_date = 2026-01-07` y fueron ejecutados el
2026-08-24.
