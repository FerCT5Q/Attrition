# C: alternativas de agrupación con cuatro variables

Fecha: 8-oct-2026. Modo `presentation`.

## Alcance y resultado

Se amplió la búsqueda de agrupaciones de C a cruces de cuatro conceptos,
incluyendo una familia orientada a 30–50 grupos. C conserva sus coeficientes,
predicciones individuales y calibración. No se incorpora QVoice ni se
sustituyen automáticamente las agrupaciones archivadas.

Se evaluaron 3775 cruces entre cuatro periodos (las definiciones pueden
repetirse entre periodos). Cada selección usó seis fotos maduras anteriores
al origen y se evaluó en seis fotos posteriores. Población: Engineering,
Employee, Regular, activo, sin RF360; salida voluntaria a seis meses.

| Agrupación | Grupos elegibles, media | Captura al 20% | Captura al 30% |
|---|---:|---:|---:|
| C con cortes actuales | 20.1 | 31.7% | 45.4% |
| Cortes actuales + una variable | 21.4 | 31.8% | 45.7% |
| Cuatro variables seleccionadas | 27.6 | 33.2% | 45.2% |
| Búsqueda de 30–50 grupos | 33.7 | 32.6% | 45.1% |

Promedios con igual peso de febrero–julio 2024, agosto 2024–enero 2025,
febrero–julio 2025 y agosto 2025–enero 2026. La comparación al 30% fue
principal; 20% y 40% son escenarios secundarios declarados.

## Interpretación por capacidad

- **Al 30%:** añadir una variable mejora 0.3 pp y gana en tres de cuatro
  periodos. Cumple marginalmente la regla: el IC95 tiene extremo inferior
  positivo menor a 0.1 pp, muy próximo a cero, y superior de 0.5 pp. Los
  errores quedan dentro de tolerancia. No es una mejora amplia ni definitiva.
- **Al 20%:** seleccionar cuatro variables mejora 1.5 pp, IC95 [0.6, 2.3],
  con tres victorias temporales. La familia orientada a 30–50 grupos mejora
  0.9 pp, IC95 [0.2, 1.8]. Ambas cumplen la regla en ese escenario secundario.
- **Al 40%:** ninguna alternativa supera la regla. Las agrupaciones más
  detalladas no ganan en todas las capacidades.

La regla exige IC95 medio positivo, tres victorias de cuatro periodos y
errores por grupo y grupo-mes no mayores al control comparable más 0.1 pp.
El control comparable aplica la prioridad actual a los mismos subgrupos
candidatos, evitando confundir granularidad con precisión. El informe
también conserva los errores propios de cada agrupación.

## Últimos cortes archivados

Selección de 1-ago-2025 aplicada a la foto 22-feb-2026, seguida hasta
22-ago-2026. No es una selección nueva con datos de septiembre de 2026.

| Alternativa | Definición final | Grupos elegibles en febrero de 2026 |
|---|---|---:|
| Actual | Antigüedad × salidas del equipo × nivel | 20 |
| + una variable | Antigüedad × salidas del equipo × nivel × adquisición registrada | 23 |
| Cuatro seleccionadas | Nivel × última promoción × tiempo en el nivel × adquisición registrada | 30 |
| Orientada a unos 40 | Antigüedad × reportes directos × experiencia previa × adquisición registrada | 36 |

Al 30% en esa foto, la variable adicional cambia captura de 42.7% a 42.9%
y error grupo-mes de 1 a 0.9 pp. Sin embargo, aumenta la población en grupos
pequeños fuera de prioridad de 5.3% a 9.4%. Con 36 grupos, resto llega a
16.2% y la captura al 30% baja a 40.9%.

Las cuatro selecciones históricas pueden diferir; las métricas promedio
evalúan la política de selección, no una única combinación final. En la
familia principal se eligieron salida previa del manager, familia de grado
y adquisición registrada. La última se repite en los dos orígenes más recientes.

## Recomendación

La variable adicional de la última selección al 30% es
**adquisición registrada (`acquisition_recorded`)**, utilizada como cuarto
corte de **antigüedad × salidas previas del equipo × nivel**. Su significado,
el origen de selección, los 23 grupos de febrero de 2026 y el alcance de la
recomendación quedan reunidos en la
[nota de la variable adicional](../../output/analysis/engineering/20261008/c-fourway-groups-v1/variable-adicional.md).
«Sin registro» no confirma ausencia de adquisición. Los 23 son grupos elegibles
totales, no necesariamente grupos a atender.

Con alcance cercano al 30%, la extensión de 23 grupos merece continuar como
alternativa de mejora pequeña. Con alcance de 20%, la política de seleccionar
cuatro variables ofrece una señal más clara y merece consideración. La
granularidad debe decidirse junto con la capacidad de acción; 40 grupos no
es un objetivo por sí mismo.

Adquisición registrada describe el dato almacenado; «sin registro» no prueba
ausencia de adquisición ni causalidad. Se conservan las limitaciones de C.
Los cortes de referencia ya fueron favorecidos por exploración histórica de
B; este análisis es retrospectivo. Los IC95 son puntuales, con 500 réplicas
por persona, condicionales a los modelos y selecciones, sin corrección por
comparaciones múltiples. El extremo inferior de la mejora principal es
marginal; no se presenta como evidencia concluyente de superioridad.

## Artefactos y fuentes

- [Informe completo](../../output/analysis/engineering/20261008/c-fourway-groups-v1/informe.md).
- Carpeta: `output/analysis/engineering/20261008/c-fourway-groups-v1/`.
- Configuración: `config/engineering_c_fourway_groups_20261008.json`.
- Selecciones: `selected-groupings.json`; búsqueda: `development-candidates/`.
- Métricas y cohortes: `results.json`, `folds/`, `grupos-prioritarios-febrero.csv`.
- Consulta guardada: `queries/profiles/engineering_model_c_person_month_20261008.sql`,
  ejecutada el 8-oct-2026; conocimiento hasta 7-sep-2026.
- Se reprodujeron población, métricas C y cortes actuales. Tiempo: 4.1
  minutos, incluidos 2.8 de carga; cero reajustes hazard. No se guardaron
  filas, llaves, respuestas ni riesgos individuales. Modelos originales intactos.
