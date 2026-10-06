# Analisis QVoice binario para attrition

Fecha de ejecucion: 2026-08-24

## Conclusion ejecutiva

Para el uso actual de attrition, considero adecuado usar los 53 campos
binarios de QVoice como baseline model-ready. La senal es consistente: cuando
el valor es `0` (desfavorable), la tasa de terminacion posterior es mayor que
cuando el valor es `1` (favorable) en los 53 items.

Esto no demuestra que el binario sea estadisticamente mejor que la escala
original `1-5`. Redshift no conserva esa escala y no existe aun una
comparacion integrada de ambos formatos sobre el mismo outcome. La
recomendacion es usar binarios ahora por disponibilidad, interpretabilidad y
estabilidad, y reservar una prueba posterior de valor incremental para la
escala `1-5`.

## Pregunta y definicion

**Pregunta:** si los flags binarios de QVoice contienen una senal util para
attrition posterior.

**Fuente y wave:** `hrda.qvoice_survey_data`, `survey_launch_date =
2026-01-07`.

**Snapshot baseline:** `2025-12-28`, el ultimo `fis_mo_end_dt` no posterior al
lanzamiento.

**Outcome:** `term_date` posterior a `2026-01-07` y hasta `2026-06-28`, el
ultimo snapshot disponible dentro de seis meses. No se uso `is_termed` solo,
porque puede conservar estados historicos en snapshots posteriores.

**Poblaciones:**

- Principal: `worker_type='Employee'` y `active_status=1`.
- Sensibilidad: la poblacion anterior mas el filtro exacto
  `employee_type='Regular'`.

Se interpreto `0` como desfavorable y `1` como favorable usando el mapping
validado contra las columnas `*_favorable` del Excel. Cada contraste requirio
al menos 30 observaciones por valor binario y se publicaron solo agregados.

## Resultados agregados

| Metrica | Employee activo | Employee Regular activo |
|---|---:|---:|
| Empleados baseline | 40,721 | 37,766 |
| Terminaciones dentro de seis meses | 1,271 | 1,135 |
| Tasa baseline de terminacion | 3.1212% | 3.0053% |
| Items evaluados | 53 | 53 |
| Items con diferencia `rate(0) - rate(1)` positiva | 53/53 | 53/53 |
| Items con diferencia de al menos 1 pp | 52/53 | 51/53 |
| Items con diferencia de al menos 2 pp | 39/53 | 40/53 |
| Diferencia promedio `rate(0) - rate(1)` | 2.690 pp | 2.738 pp |
| Diferencia absoluta promedio entre poblaciones | 0.095 pp | - |
| Diferencia maxima entre poblaciones | 0.256 pp | - |

Los cinco items con mayor diferencia fueron los mismos en ambas poblaciones,
con un cambio menor de orden:

1. `Intent to Stay`: verse trabajando en Qualcomm.
2. `Respect`: ser tratado con respeto en el trabajo.
3. `Innovation`: recibir apoyo para encontrar formas nuevas y mejores.
4. `Growth and Development`: oportunidades para aprender y desarrollarse.
5. `Manager Effectiveness`: el manager mantiene informado al empleado.

Como ejemplo, en `Intent to Stay` item 1, la poblacion principal tuvo una tasa
de terminacion de `7.3177%` cuando el binario fue `0` frente a `2.0205%` cuando
fue `1`, una diferencia de `5.2972 pp`.

## Calidad y cobertura

- Los 53 items SQL tienen dominio binario `0/1` entre sus valores no nulos.
- No se observaron valores binarios invalidos en los 53 items.
- La cobertura por item varia aproximadamente entre 36,615 y 40,402 filas de
  la wave; los nulos no se trataron como `0`.
- La tabla contiene 60 filas sin ningun item binario poblado; no deben
  convertirse automaticamente en respuestas desfavorables.

## Recomendacion de modelado

1. Usar los 53 binarios como baseline de attrition y medir lift, AUC,
   calibracion y estabilidad temporal frente a un modelo sin QVoice.
2. Mantener los nulos como missing. Si se imputa, agregar tambien indicadores
   de no respuesta; nunca mapear null a `0`.
3. Probar una feature agregada de favorabilidad solo despues de definir su
   denominador, minimo de items respondidos y tratamiento de nulos.
4. No mezclar filas Excel y SQL sin resolver la diferencia de poblacion. La
   reconciliacion previa dejo 724 respuestas estructuradas adicionales en
   Excel y 60 filas SQL sin respuestas binarias.
5. Cuando exista una fuente integrada `1-5`, comparar dos modelos con la misma
   poblacion, ventana temporal y validacion longitudinal. Hasta entonces no
   hay evidencia para afirmar que la escala original agregue valor incremental
   frente al binario.

## Limitaciones

Las tasas son asociaciones univariadas y no controlan por tenure, job family,
region, employee type, no respuesta u otras variables. No son efectos causales
ni sustituyen una validacion de modelo con particion temporal. La poblacion
principal incluye contratos fuera del valor exacto `employee_type='Regular'`;
la sensibilidad muestra que la conclusion no cambia al excluirlos.

## Evidencia reproducible

- [Auditoria SQL de asociacion binaria](../../queries/audits/qvoice_2026_binary_attrition_association_20260824.sql)
- [Diagnostico de poblacion](qvoice_2026_population_filter_diagnostic_20260824.md)
- [Reconciliacion Excel vs SQL](qvoice_2026_sql_excel_reconciliation_20260824.md)

La consulta fue read-only, uso joins internos por `emp_id`/`employee_id` y
publico solo conteos y tasas agregadas.

