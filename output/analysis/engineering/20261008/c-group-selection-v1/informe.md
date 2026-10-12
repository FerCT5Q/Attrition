# Comparación de agrupaciones de B y C

## C con cortes propios muestra una captura media similar a B y menor error por grupo

Ejecución: 8-oct-2026. Modo: `presentation`. Población: Engineering, Employee, Regular, activo, sin RF360.

Objetivo: priorizar grupos para explorar acciones de retención. Resultado objetivo: salida voluntaria en los seis meses siguientes a cada foto. La evidencia describe asociación y capacidad de priorización; no estima el efecto de una intervención.

## Resultado principal: priorizar al 30% de la población

Promedio con igual peso de cuatro periodos. Captura = salidas observadas en la población priorizada / salidas observadas totales. Cada periodo contiene seis snapshots: una persona y su salida pueden contribuir en varias ventanas; los eventos del cálculo son persona-snapshot con salida, no salidas únicas sumadas a través del tiempo.

| Modelo y agrupación | Captura | Estimado R6 | Observado R6 | Error por grupo | Error grupo-mes | Grupos elegibles, media |
|---|---:|---:|---:|---:|---:|---:|
| B · cortes originales | 45.2% | 5% | 4.6% | 0.9 pp | 0.9 pp | 20.1 |
| C · mismos cortes de B | 45.4% | 4.8% | 4.6% | 0.8 pp | 0.9 pp | 20.1 |
| C · selección por prioridad | 45.2% | 4.7% | 4.6% | 0.7 pp | 0.7 pp | 21.8 |
| C · selección por Gini | 45% | 4.8% | 4.5% | 0.5 pp | 0.6 pp | 19.4 |
| B · árbol de hasta 8 grupos | 43.6% | 4.9% | 4.4% | 0.5 pp | 0.6 pp | 7.8 |
| B · árbol de hasta 16 grupos | 43.9% | 4.9% | 4.4% | 0.6 pp | 0.7 pp | 13.5 |
| C · árbol de hasta 8 grupos | 43.9% | 4.7% | 4.4% | 0.4 pp | 0.5 pp | 8 |
| C · árbol de hasta 16 grupos | 44.1% | 4.7% | 4.4% | 0.5 pp | 0.7 pp | 14.1 |

C con selección propia frente a B cortes: **diferencia de captura menor a 0.1 pp**, IC95 [-0.9, 0.8]. Gana en 2 periodos, pierde en 2 y empata en 0. Regla formal de preferencia retrospectiva: **no cumple**.

La regla exige mejora media de captura, al menos tres victorias temporales, IC95 positivo y un empeoramiento no mayor a 0.1 pp en error por grupo y grupo-mes. Se fijó antes del cálculo. El IC es condicional a modelos, cortes y asignaciones ya fijados; no incorpora el proceso completo de selección ni sustituye evidencia prospectiva. Son intervalos puntuales, sin corrección por comparaciones múltiples; los escenarios secundarios conservan carácter exploratorio.

El error por grupo promedia el error absoluto de las tasas de cada grupo durante el periodo, ponderado por personas priorizadas. El error grupo-mes evalúa cada grupo en cada foto antes de promediar, evitando que meses con sobreestimación compensen meses con subestimación. R6 es probabilidad acumulada a seis meses. Todos los errores se expresan en puntos porcentuales. Comparar errores de agrupaciones distintas también cambia la granularidad: grupos grandes pueden suavizar errores. Por eso se incluye más adelante la comparación de B y C sobre exactamente la misma selección y los mismos cortes.

![Comparación de captura](comparacion-captura.png)

## Qué cambia al conservar los mismos cortes

B cortes y C mismos cortes cruzan **antigüedad × salidas del equipo × nivel**. Los modelos estiman el riesgo y ordenan esos mismos segmentos en cada snapshot. Por tanto, pueden seleccionar personas distintas aun usando las mismas definiciones.

C con los mismos cortes cambia la captura en 0.3 pp frente a B. Gana en 3 de cuatro periodos. IC95 de diferencia [-0.3, 0.8] pp: la ventaja de captura no es concluyente al 30%. El error grupo-mes pasa de 0.9 a 0.9 pp.

También se conservó exactamente la población seleccionada por B y se cambió únicamente el estimador a C:

| Estimador sobre la selección de B | Estimado R6 | Observado R6 | Error por grupo | Error grupo-mes |
|---|---:|---:|---:|---:|
| B | 5% | 4.6% | 0.9 pp | 0.9 pp |
| C | 4.8% | 4.6% | 0.7 pp | 0.8 pp |

## Selección temporal de cortes para C

Se restauraron cuatro modelos B y cuatro C. **Cero ajustes hazard**: sus coeficientes y calibración no cambiaron. Se reutilizaron los árboles de ocho hojas y se ajustaron árboles de hasta dieciséis hojas a las predicciones previas al periodo.

Para cada periodo se probaron todos los cruces de dos y tres dimensiones disponibles entre las siete originales de B y las adicionales presentes en el C de ese corte temporal. No se exige que los cuatro C tengan los mismos términos. Se excluyen calendario, interacciones como dimensiones y dimensiones constantes en desarrollo.

| Periodo evaluado: fotos | Desarrollo: fotos maduras | Último resultado conocido del desarrollo | Candidatos | Selección por prioridad | Selección por Gini |
|---|---|---|---:|---|---|
| 2024-02-18 a 2024-07-21 | 2023-02-19 a 2023-07-23 | 2024-01-23 | 562 | Nivel × Última promoción × Tiempo en el nivel | Antigüedad × Experiencia previa |
| 2024-08-25 a 2025-01-26 | 2023-08-20 a 2024-01-21 | 2024-07-21 | 288 | Antigüedad × Experiencia previa | Antigüedad × Cambios de manager |
| 2025-02-23 a 2025-07-27 | 2024-02-18 a 2024-07-21 | 2025-01-21 | 366 | Antigüedad × Capa organizativa registrada | Antigüedad × Capa organizativa registrada |
| 2025-08-24 a 2026-01-25 | 2024-08-25 a 2025-01-26 | 2025-07-26 | 562 | Antigüedad × Salidas en su equipo | Antigüedad × Salidas en su equipo × Adquisición registrada |

La selección principal eligió **4 definiciones distintas en cuatro orígenes**. El promedio evalúa la política de volver a seleccionar con datos anteriores a cada periodo. No demuestra que la última combinación, por sí sola, gane durante los cuatro periodos.

La selección usa las seis últimas fotos con seguimiento a seis meses terminado antes del origen externo. La evaluación utiliza las siguientes seis fotos. Las etiquetas de desarrollo participaron parcialmente en el ajuste del hazard: es desarrollo de agrupaciones, no validación independiente del modelo. Las salidas del periodo externo no escogen sus cortes.

Selección por prioridad: mayor captura al 30%, tolerancia relativa de 2%; entre las candidatas cercanas, error grupo-mes a no más de 0.1 pp del mínimo; después menos dimensiones y menos grupos. Un árbol necesita mejorar captura más de 2% relativo sin empeorar ese error más de 0.1 pp. Selección Gini: diagnóstico que recupera el criterio histórico de conservar el ordenamiento completo, con parsimonia. No se cambia el criterio principal después de mirar estos resultados.

## Comportamiento en cada periodo

| Fotos | B cortes: captura | C mismos cortes: captura | C selección: captura | Diferencia C selección − B | B: error grupo-mes | C selección: error grupo-mes |
|---|---:|---:|---:|---:|---:|---:|
| 2024-02-18 a 2024-07-21 | 47.5% | 49.1% | 48% | 0.5 pp | 0.9 pp | 1 pp |
| 2024-08-25 a 2025-01-26 | 45.9% | 44.2% | 44.3% | -1.7 pp | 1 pp | 0.7 pp |
| 2025-02-23 a 2025-07-27 | 45.4% | 46.1% | 45.3% | -0.1 pp | 0.9 pp | 0.6 pp |
| 2025-08-24 a 2026-01-25 | 41.8% | 42.3% | 43.1% | 1.3 pp | 0.9 pp | 0.6 pp |

## Sensibilidad a la capacidad

| Capacidad | B cortes: captura | C mismos cortes: captura | C selección: captura | C Gini: captura | C selección cumple regla |
|---|---:|---:|---:|---:|---|
| 20% | 31.5% | 31.7% | 32.2% | 31.9% | No |
| 30% | 45.2% | 45.4% | 45.2% | 45% | No |
| 40% | 56.4% | 57.6% | 56.5% | 56.9% | No |

**Resultado favorable en el escenario secundario del 40%:** C con los mismos cortes de B captura 57.6% frente a 56.4%; diferencia 1.1 pp, IC95 [0.5, 1.7]. Gana en 3 periodos y cumple la regla de preferencia retrospectiva. Esta capacidad se declaró antes del cálculo; no sustituye al escenario principal del 30%.

## Conservación del ordenamiento completo

Eficiencia = Gini de concentración de salidas al ordenar grupos / Gini al ordenar personas por el mismo modelo. Se calcula por snapshot y después se promedia. El resto forma un bloque final para esta curva; permanece fuera de la prioridad. Una eficiencia menor en C no prueba peor captura que B: cada eficiencia usa el ranking individual de su propio modelo como denominador.

| Agrupación | Eficiencia Gini | Resto | Peor error publicable, media por periodo |
|---|---:|---:|---:|
| B · cortes originales | 81.5% | 5.1% | 1.5 pp |
| C · mismos cortes de B | 75.8% | 5.1% | 1.6 pp |
| C · selección por prioridad | 77.7% | 1.9% | 1.4 pp |
| C · selección por Gini | 79.6% | 1.9% | 1.3 pp |
| B · árbol de hasta 8 grupos | 76.9% | 0% | 1.5 pp |
| B · árbol de hasta 16 grupos | 81.1% | 0.2% | 2.2 pp |
| C · árbol de hasta 8 grupos | 72.1% | 0% | 1.6 pp |
| C · árbol de hasta 16 grupos | 76.4% | 0.1% | 2.1 pp |

## Grupos completos alrededor de la capacidad del 30%

La comparación exacta al 30% asigna el mismo peso fraccional a las personas del grupo del límite, equivalente a selección aleatoria dentro del grupo. No utiliza un ranking individual para desempatar. Estas alternativas muestran decisiones sobre grupos completos, con capacidades distintas entre diseños:

| Agrupación | Cobertura excluyendo límite | Captura excluyendo límite | Cobertura incluyendo límite | Captura incluyendo límite |
|---|---:|---:|---:|---:|
| B · cortes originales | 27.3% | 42.1% | 32.6% | 48% |
| C · mismos cortes de B | 28.8% | 43.6% | 32.9% | 49.2% |
| C · selección por prioridad | 24.4% | 38.5% | 32.8% | 48.4% |
| C · selección por Gini | 26.4% | 39.9% | 32.4% | 48.2% |

## Foto adicional madura de febrero de 2026

Foto 2026-02-22; seguimiento hasta 2026-08-22; 35313 personas. Modelos y selección de 2025-08-01. No se añade como quinto periodo al promedio y no es un holdout virgen.

| Agrupación | Grupos elegibles | Resto | Captura al 30% | Estimado | Observado | Error grupo-mes |
|---|---:|---:|---:|---:|---:|---:|
| B · cortes originales | 20 | 5.3% | 41.2% | 5.5% | 4.8% | 0.8 pp |
| C · mismos cortes de B | 20 | 5.3% | 42.7% | 5.6% | 5% | 1 pp |
| C · selección por prioridad | 12 | 0% | 42% | 5.4% | 4.9% | 0.5 pp |
| C · selección por Gini | 15 | 2.6% | 43% | 5.5% | 5% | 0.6 pp |
| B · árbol de hasta 8 grupos | 8 | 0% | 41.7% | 5.2% | 4.9% | 0.4 pp |
| B · árbol de hasta 16 grupos | 15 | 0% | 44.2% | 5.4% | 5.2% | 0.5 pp |
| C · árbol de hasta 8 grupos | 8 | 0% | 41.7% | 5.1% | 4.9% | 0.3 pp |
| C · árbol de hasta 16 grupos | 15 | 0% | 44.2% | 5.4% | 5.2% | 0.5 pp |

### Grupos priorizados por la selección principal de C en esa foto

Los nombres de nivel describen nivel profesional, no nivel de riesgo. Las bandas son las representaciones archivadas de C; comp ratio y capas organizativas conservan sus límites semánticos documentados.

| Definición | Personas efectivas seleccionadas | Estimado R6 | Observado R6 | Error |
|---|---:|---:|---:|---:|
| Antigüedad: 3-5 años · Salidas en su equipo: con salidas | 2044 | 7.2% | 5.8% | 1.4 pp |
| Antigüedad: 2-3 años · Salidas en su equipo: con salidas | 474 | 7.2% | — | — |
| Antigüedad: 5-10 años · Salidas en su equipo: con salidas | 2172 | 5% | 4.7% | 0.3 pp |
| Antigüedad: 3-5 años · Salidas en su equipo: sin salidas | 5710 | 4.7% | 4.7% | <0.1 pp |
| Antigüedad: 2-3 años · Salidas en su equipo: sin salidas | 193.9 | 4.6% | 5.7% | 1.1 pp |

Observados suprimidos cuando no hay al menos 30 personas distintas con evento y 30 personas efectivas por foto seleccionada. Las personas efectivas pueden ser fraccionales por la política del límite. La elegibilidad del grupo completo exige al menos 300 personas en cada foto.

## Lectura y límites

- B árbol y B cortes tienen el mismo modelo hazard. Cambia la pérdida de información al resumir el riesgo en grupos; una representación no mejora automáticamente los coeficientes ni el pronóstico individual.
- Los cruces de C conservan reglas de dos o tres dimensiones; los árboles usan hasta tres o cuatro condiciones por hoja. Más grupos no implican mayor utilidad. Importan captura, calibración, tamaño, persistencia y una intervención plausible.
- Se prueban todos los cruces del espacio declarado, no todos los umbrales posibles ni todas las particiones posibles. La selección principal sigue el criterio de prioridad; Gini es una alternativa documentada.
- La prioridad se ordena por riesgo medio predicho vigente en cada snapshot. La comparación previa de árboles ordenaba por el riesgo de entrenamiento congelado. No mezclar ambas tablas como si compartieran la política.
- Se usa la receta de agrupación original de B sobre los B reconstruidos y el frame temporal corregido de C. Esto no reproduce las cifras históricas del deck. Los 22 grupos de julio de 2026 tampoco se imponen a otras fotos.
- El análisis original de B escogió cortes usando el promedio de los mismos cuatro periodos publicados. Aquí C selecciona antes de cada periodo. B conserva una referencia ya favorecida por exploración histórica; la comparación es retrospectiva.
- Sólo cuatro periodos y años explorados previamente. El bootstrap por persona conserva ventanas juntas, pero no demuestra estabilidad ante cambios económicos futuros ni incertidumbre del proceso de selección completo.
- IOS usa fecha efectiva sin fecha de publicación confirmada; snapshots susceptibles a revisiones históricas. Capas y comp ratio son valores almacenados. No se reevaluaron scores ni se sustituyen sus contratos de entrada.
- Otras salidas cuentan como no voluntarias; no se ajusta un modelo de riesgos competitivos. Los snapshots fiscales no siempre distan el mismo número de días.

## Evidencia, conservación y tiempo

- Consulta guardada: `queries/profiles/engineering_model_c_person_month_20261008.sql`. Frontera de conocimiento: 2026-09-07.
- Evidencia: `results.json`, `folds/`, `development-candidates/`, `analysis-checks.json`, `preservation.json` y `manifest.json`.
- Plan: `docs/plans/attrition-c-group-selection-20261008.md`. Configuración congelada: `frozen-config.json`.
- Se reconciliaron población y métricas globales de los ocho modelos. Comprobaciones de capacidad por foto, captura directa frente a agregados, madurez temporal y conservación de artefactos.
- Cálculo: 6.5 minutos; carga: 3.9 minutos. Cero reajustes hazard; ocho modelos restaurados. Informe construido sólo con agregados.
- B, B+QVoice y C conservan sus artefactos. No se inició C+QVoice ni se promovió una especificación a producción.
- No se guardaron filas, claves, riesgos individuales ni salarios exactos.
