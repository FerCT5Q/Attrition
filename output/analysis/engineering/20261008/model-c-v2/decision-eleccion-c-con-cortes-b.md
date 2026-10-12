# Decisión: continuar con C usando los cortes originales de B

Fecha: 8-oct-2026. Modo de entrega: `presentation`.
Nota de decisión posterior al experimento original, documentada por solicitud del usuario.

## Qué versión elegimos

**Candidato preferido para continuar: modelo C con los grupos definidos por
antigüedad × salidas del equipo × nivel.** En la comparación adicional esta
variante se identifica como **`C_Bcuts`**.

El modelo que estima el riesgo sigue siendo C, de hazard mensual con enlace
cloglog y riesgo acumulado a seis meses. Se conservan sus variables y
coeficientes; los tres cortes sirven para resumir y priorizar sus predicciones
en grupos interpretables. QVoice está excluido de esta versión.

Esta elección es una preferencia práctica para el objetivo del proyecto:
identificar grupos de riesgo alto y parte del riesgo medio, estimar su riesgo
y facilitar acciones de retención. Su alcance es continuar con este candidato;
la nota no registra una promoción a producción ni una superioridad universal.

## Por qué lo elegimos

1. **Mejor balance entre captura y estimación.** Al priorizar al 30% de la
   población, C concentra ligeramente más salidas y reduce el error medio
   dentro de los grupos frente a B usando exactamente las mismas definiciones.
2. **La ventaja aparece en varios periodos.** C gana en captura en tres de
   cuatro periodos, tanto al priorizar 30% como al priorizar 40%.
3. **Resultado más favorable al incluir parte del riesgo medio.** Con capacidad
   del 40%, C cumple el criterio retrospectivo predefinido de captura,
   consistencia temporal, intervalo de confianza y tolerancia de error.
4. **Reglas conocidas y fáciles de explicar.** Se conservan los tres conceptos
   de la agrupación original de B. Esto facilita comparar y dar seguimiento a
   los mismos tipos de grupos, aunque las personas, los tamaños y su orden de
   riesgo cambien. Es una ventaja de interpretación; no demuestra por sí sola
   estabilidad del ranking ni que una intervención evite salidas.

### Evidencia que apoya la decisión

Población: Engineering, Employee, Regular, activo, sin RF360. Objetivo:
salida voluntaria en los seis meses siguientes a cada snapshot. Promedio con
igual peso de cuatro periodos de fotos: febrero–julio de 2024,
agosto de 2024–enero de 2025, febrero–julio de 2025 y
agosto de 2025–enero de 2026.

| Métrica | B con cortes originales | C con los mismos cortes |
|---|---:|---:|
| Captura de salidas al priorizar 30% | 45.2% | 45.4% |
| Error medio por grupo al priorizar 30% | 0.9 pp | 0.8 pp |
| Captura de salidas al priorizar 40% | 56.4% | 57.6% |

Captura es la proporción de salidas observadas que concentra la población
priorizada. El error por grupo es la diferencia absoluta entre riesgo estimado
y observado, ponderada por personas priorizadas. Las observaciones son
persona-snapshot: una salida puede contribuir a varias ventanas mensuales.
La comparación a capacidad exacta usa una fracción uniforme del grupo del
límite; el informe también presenta alternativas con grupos completos.

## Límites que forman parte del veredicto

- **Al 30%, la mejora de captura aún no es concluyente.** La diferencia es
  0.3 pp, con IC95 de −0.3 a 0.8 pp. Este escenario principal no supera la
  regla formal de preferencia. Las diferencias se calculan antes de redondear.
- **Al 40%, la diferencia es 1.1 pp**, con IC95 de 0.5 a 1.7 pp, tres victorias
  temporales y errores dentro de tolerancia. Sí supera la regla para esa
  capacidad secundaria, que se había declarado antes del cálculo.
- La evidencia es retrospectiva, con cuatro periodos ya explorados e
  intervalos puntuales sin corrección por comparaciones múltiples. No implica
  validación prospectiva ni efecto causal de las acciones.
- El menor error es un resultado promedio. En la foto adicional de
  22-feb-2026, C con los mismos cortes captura más que B, pero su error por
  grupo es mayor: 1 pp frente a 0.8 pp. No gana todas las métricas en todas
  las fechas.
- La búsqueda de cortes propios de C eligió cuatro combinaciones distintas
  entre periodos y tuvo captura media prácticamente igual a B. La recomendación
  aquí registrada conserva las definiciones originales de B para favorecer
  continuidad e interpretación; no declara que sean los mejores cortes posibles.
- El experimento original de C, orientado a pérdidas globales, mantiene su
  conclusión de que C no superó aquella regla. Esta decisión posterior se
  basa en el objetivo de priorización de grupos y no modifica esa evidencia.

## Cuántos grupos tiene la versión elegida

**20 grupos elegibles en la foto del 22-feb-2026**, con seguimiento hasta
22-ago-2026. Cada grupo debe tener al menos 300 personas en esa foto; los
grupos menores quedan en resto, fuera de la prioridad. El número elegible
puede cambiar por fecha y no se fija de antemano.

Los cortes son los de la receta original de B:

- Antigüedad: menos de 1 año, 1–2, 2–3, 3–5, 5–10 y 10 o más años.
- Salidas del equipo en 12 meses: sin salidas o con salidas; falta de dato
  conserva su categoría explícita cuando existe.
- Nivel profesional agrupado: entrada, medio y alto; la implementación
  histórica conserva también su categoría residual. Estos nombres describen
  nivel profesional, no nivel de riesgo.

Cada snapshot ordena los grupos por su riesgo medio predicho por C. Los
20 grupos son todos los elegibles; la capacidad del 30% o 40% determina
cuáles se priorizan.

Para evitar confusiones con los archivos anteriores:

| Variante | Grupos elegibles en febrero de 2026 | Relación con esta decisión |
|---|---:|---|
| C con árbol | 8 | Representación del experimento original |
| **C con cortes originales de B (`C_Bcuts`)** | **20** | **Candidato elegido para continuar** |
| C con selección propia de cortes (`C_selected`) | 12 | Alternativa evaluada: última selección de dos dimensiones |

Los 22 grupos históricos de B corresponden a la foto del 26-jul-2026 y a su
ejecución original. Ese conteo no se transfiere automáticamente a otra fecha
ni a C.

## Artefactos y trazabilidad

- Modelo archivado: [trained-model/model-c.json](trained-model/model-c.json).
  Último origen evaluado: 1-ago-2025; no es un reajuste hasta septiembre de 2026.
- Evidencia de esta elección: [results.json de la comparación de cortes](../c-group-selection-v1/results.json),
  secciones `summary["30"].C_Bcuts`, `summary["40"].C_Bcuts`,
  `folds[].evaluation.C_Bcuts` y `extension.evaluation.C_Bcuts`.
- Explicación completa y alternativas: [informe de agrupaciones](../c-group-selection-v1/informe.md).
- Consulta guardada: `queries/profiles/engineering_model_c_person_month_20261008.sql`,
  ejecutada el 8-oct-2026; frontera de conocimiento 7-sep-2026. El control B
  reproduce su receta sobre el mismo frame temporal corregido de C; las
  cifras no son una reproducción del deck histórico.
- [trained-model/groups.json](trained-model/groups.json) conserva el árbol
  original. La definición de los cortes recomendados está en
  `folds[].evaluation.C_Bcuts.definition` de la comparación adicional.
- [selected-grouping.json del estudio](../c-group-selection-v1/selected-grouping.json)
  documenta la selección propia de C de dos dimensiones; corresponde a
  `C_selected` y debe distinguirse de la elección `C_Bcuts` registrada aquí.

Esta nota se añade a la carpeta de C. Los modelos, reglas, resultados y
manifiestos previamente archivados conservan su contenido. B y B+QVoice
permanecen como referencias independientes. No se ejecutaron nuevos modelos
ni consultas para redactar esta decisión.
