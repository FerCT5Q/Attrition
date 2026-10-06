# Metodología de evaluación de variables

## Fuentes oficiales

- Reglas y umbrales: `.codex/skills/evaluate-attrition-variable/references/scoring-rules.yaml`.
- Contrato del spec: `.codex/skills/evaluate-attrition-variable/references/assessment-spec.md`.
- Inventario histórico v2 de las 43 variables: `config/attrition_candidate_variables.yaml`.
- Profile y workbook v2: conservados en `output/assessments/` como referencia histórica.
- Evidencia vigente futura: spec/profile v4 con verificación calculada de cada 2 cualitativo.

Los documentos anteriores de scoring no son evidencia actual. Cualquier hallazgo histórico debe revalidarse contra la base y quedar incorporado al YAML o al profile generado.

## Escala

- `2`: cumple el criterio y la comprobación calculada pasó.
- `1`: cumplimiento parcial, limpieza, definición o validación pendiente.
- `0`: no cumple, no está disponible o existe una debilidad material.

Se evalúan ocho criterios, cada uno de 0 a 2: source, definition, coverage, missingness, consistency, history, joinability y derivation effort. El máximo es 16. Todo `0` o `1` cualitativo requiere `why`, `evidence` y `recommended_action`. Todo `2` cualitativo requiere consulta guardada, regla de aceptación, resultado `pass` y métricas agregadas; si falta algo, el proceso se detiene.

Los labels por puntos son:

- High: 14-16 y ningún cero.
- Medium: 9-13, o 14-16 con un solo cero corregible.
- Low: 1-8.
- Not available / exclude: total 0.

Los blockers siguen teniendo prioridad sobre el label por puntos.

## Validación semántica

Una columna existente no demuestra su definición. Métricas precalculadas deben
recalcularse o reconciliarse con lineage oficial; features derivadas deben
probar fórmula, ventanas y leakage; agrupaciones deben comprobar su mapping; y
jerarquías deben reconstruir cadenas, raíces, ciclos y convergencia. Un
dashboard, un nombre de campo o un assessment anterior sólo aportan contexto.

El SQL se guarda en `queries/audits/` o `queries/profiles/`. La evidencia
registra fecha, población, métricas y regla de aceptación.

## Umbrales cuantitativos

| Criterio | Score 2 | Score 1 | Score 0 |
|---|---:|---:|---:|
| Coverage | >= 95% | >= 70% y < 95% | < 70% |
| Missingness | <= 5% | > 5% y <= 30% | > 30% |
| Usable history | >= 24 meses | 6-23 meses | < 6 meses o leakage |

`Usable since` es la primera observación de una secuencia de tres observaciones consecutivas con al menos 95% de cobertura, salvo que las reglas editables cambien. Para eventos se separan observabilidad y prevalencia: la ausencia de un evento no se interpreta automáticamente como dato faltante.

## Blockers

Los blockers tienen prioridad sobre la suma de puntos. Una variable puede ser técnicamente sólida y aun así terminar como `Sensitive / restricted`, `External / third-party`, `Not available / exclude` o `TBD`. El resultado por puntos se conserva para trazabilidad, pero no reemplaza la restricción.

## Workbook

El workbook tiene exactamente tres hojas:

1. `Variable assessment`
2. `Coverage`
3. `Score rationale`

Cada score `0` o `1` tiene un comentario breve y exactamente una fila de rationale. Los scores `2` no generan comentarios ni filas. Los outputs nuevos se escriben en `output/assessments/<run-id>/` con `manifest.json`, `profile.json`, Excel, `inputs/`, `evidence/` y `vars/<NN-variable-slug>/` con notebook y HTML; no sobrescriben ejecuciones anteriores.

La hoja `Variable assessment` usa 23 columnas, en este orden: `Category`,
`Variable`, `Notes`, `Considerations`, `Source`, `Source Detail 1`, `Source
Detail 2`, `Level data`, `History available`, `Observation frequency`, `Type`,
`values`, `Blocker / special label`, `Source`, `Definition`, `Coverage`,
`Missingness`, `Consistency`, `History`, `Join`, `Effort`, `Total`, `Result`.

## Plan guiado y reporte

Para una ejecucion nueva, Codex redacta un `analysis-plan-vN.yaml` explicito por
variable despues del preflight y antes de SQL. Cada historia define pregunta,
motivo, metodo, SQL agregado, regla de aceptacion, poblacion y grain.
`validation_focus` es solo una pista; no se convierte automaticamente en una
validacion material. Si la evidencia descubre una brecha nueva, se crea una
version mayor del plan con motivo de revision antes de ejecutar la consulta
adicional.

El notebook se crea al congelar el plan y se ejecuta despues con resultados
agregados congelados. Guarda graficos en `charts/` y `charts-manifest.json`.
El HTML principal, en espanol, explica todos los criterios y cada validacion en
su propia seccion; incorpora esas graficas y tiene tantas paginas como requiera
la evidencia. El HTML del notebook sigue siendo respaldo auditable, no el
reporte para la toma de decisiones.

## Artefactos v4

Cada ejecuci??n se publica bajo `output/assessments/<run-id>/` con `manifest.json`, `profile.json`, Excel, `inputs/`, `evidence/` y `vars/<NN-variable-slug>/` con notebook y HTML por variable.
