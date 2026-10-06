# Reconciliación QVoice 2026: Excel raw vs Redshift

Fecha de ejecución: 2026-08-24

## Resultado ejecutivo

La codificación binaria y la distribución de favorabilidad son consistentes
entre el Excel de enero de 2026 y `hrda.qvoice_survey_data`, pero los conteos
absolutos no cuadran porque las dos fuentes no tienen el mismo universo.

Conclusión: **match de mapping y de señal binaria; no match de población y
conteos absolutos**.

## Alcance y mapping

Se comparó:

- Excel: `data/QVoice/Jan 2026 Qvoice_raw data.xlsx`, hoja `Raw data`.
- Redshift: `hrda.qvoice_survey_data` filtrado a
  `survey_launch_date = DATE '2026-01-07'`.
- Excel: las 53 columnas `*_favorable` correspondientes a los 53 ítems
  estructurados de Redshift.
- Excel: se excluyeron las 4 columnas `*_favorable` adicionales de exit survey.

El mapping se hizo por posición y por coincidencia del texto de la pregunta,
incluyendo los reordenamientos de `Intent to Stay`, `Culture`, `Survey Action
Planning` e `Innovation`.

## Reglas de aceptación

1. Los 53 encabezados Excel deben terminar en `_favorable` y coincidir con la
   pregunta del ítem SQL.
2. Los valores no nulos del Excel deben ser únicamente `0` y `1`.
3. Los valores no nulos de SQL deben ser únicamente `0` y `1`.
4. Para considerar equivalentes los conteos, `populated`, `zero` y `one`
   deben coincidir por ítem.
5. Como prueba secundaria de señal, la diferencia absoluta entre las tasas
   `one / populated` debe ser menor o igual a 1 punto porcentual por ítem.

## Evidencia agregada

| Métrica | Excel raw | Redshift SQL |
|---|---:|---:|
| Ítems comparados | 53 | 53 |
| Mapping de encabezados válido | 53/53 | 53/53 |
| IDs distintos / filas de fuente | 42,203 | 40,721 |
| Filas con algún `Favorable`/binario poblado | 41,385 | 40,661 |
| Filas sin algún `Favorable`/binario poblado | 818 | 60 |
| Filas duplicadas por `Emp ID` en Excel | 0 | No aplica: `emp_id` distinto por fila en esta wave |
| Valores binarios inválidos | 0 en 53 ítems | 0 en 53 ítems |
| Match exacto de `populated`, `zero` y `one` | 0/53 | 0/53 |

El Excel tiene una diferencia de cardinalidad de 1,482 IDs frente a SQL y 724
filas más con algún campo binario poblado. La diferencia total se explica
aritméticamente por 818 filas Excel sin Favorable, 60 filas SQL sin ningún
binario y 724 filas con respuesta binaria en Excel que no aparecen en SQL.
Esto no demuestra por sí solo cuáles IDs fueron excluidos por el proceso SQL.

## Comparación de la señal

| Métrica | Resultado |
|---|---:|
| Total de respuestas no nulas, SQL | 2,087,805 |
| Total de respuestas no nulas, Excel | 2,108,246 |
| Total de `Favorable=1`, SQL | 1,663,794 |
| Total de `Favorable=1`, Excel | 1,677,483 |
| Tasa favorable ponderada, SQL | 79.6911% |
| Tasa favorable ponderada, Excel | 79.5677% |
| Diferencia ponderada | -0.1234 puntos porcentuales |
| Diferencia absoluta media por ítem | 0.1123 puntos porcentuales |
| Diferencia absoluta máxima por ítem | 0.2397 puntos porcentuales |
| Ítems dentro de 1 punto porcentual | 53/53 |

Las mayores diferencias de tasa por ítem fueron pequeñas: `Intent to Stay`
item 2, estrés manejable, energía al trabajar, sentido de pertenencia y
motivación para ir más allá. Todas quedaron dentro de la regla de 1 punto
porcentual.

La cobertura calculada sobre el propio universo no coincide porque los
denominadores son distintos. La diferencia absoluta media de cobertura fue
2.4832 puntos porcentuales y la máxima fue 3.0939 puntos porcentuales.

## Interpretación

La evidencia respalda que las columnas binarias `*_favorable` del Excel son
las comparables con los 53 ítems `smallint` de Redshift. Las tasas de `1` son
prácticamente iguales y no aparecen valores inválidos.

La evidencia no respalda tratar ambas fuentes como el mismo conjunto de filas:

- El Excel contiene 42,203 IDs distintos.
- SQL contiene 40,721 IDs distintos para la wave.
- El Excel incluye 818 IDs sin ningún `Favorable` poblado.
- SQL incluye 60 filas sin ningún binario poblado y 40,661 con algún binario.

Por tanto, el siguiente problema a resolver es la regla de población o de
carga de SQL, no la transformación binaria. La auditoría adicional no encontró
que SQL sea exclusivamente `Employee`/`Regular`/activo, ni encontró un flag
explícito de encuesta válida. Para demostrar igualdad fila a fila se necesita
una reconciliación interna autorizada por `Emp ID` o lineage del proceso de
ingestión; este documento sólo publica agregados.

## Fuentes

- Excel raw: `data/QVoice/Jan 2026 Qvoice_raw data.xlsx`, `Raw data`.
- Consulta SQL ejecutada:
  `queries/audits/qvoice_2026_excel_binary_reconciliation_20260824.sql`.
- Inventario SQL:
  `queries/audits/qvoice_survey_data_column_inventory_20260821.sql`.
- Disponibilidad de wave:
  `queries/audits/qvoice_wave_year_availability_20260821.sql`.
- Diagnóstico de población y filtros:
  `data/QVoice/qvoice_2026_population_filter_diagnostic_20260824.md`.
