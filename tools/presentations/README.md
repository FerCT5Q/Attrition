# Presentation tools

## Base vigente del deck HTML de selección del modelo

Desde el 5-oct-2026, la base es el archivo simplificado por Julia que el usuario
entregó como `output/presentations/presentacion-eng.html`. Se conserva una copia
exacta en
[`references/presentations/model-selection/20261005-julia/presentacion-eng.html`](../../references/presentations/model-selection/20261005-julia/presentacion-eng.html).
La revisión vigente incorpora el ajuste pedido en el slide 5: **Level / 8 groups**.
Está guardada en
[`references/presentations/model-selection/20261005-julia-8-groups/presentacion-eng.html`](../../references/presentations/model-selection/20261005-julia-8-groups/presentacion-eng.html).
El resto coincide con la versión de Julia. La ruta vigente, su SHA-256 y el
historial de ajustes están registrados en
[`config/presentations/model-selection-base.json`](../../config/presentations/model-selection-base.json).

Para exportar la versión vigente:

```powershell
.venv\Scripts\python.exe -B tools\presentations\build_model_selection_deck_v9.py
```

El comando valida la referencia y copia sus bytes a una carpeta nueva en
`output/presentations/`. También acepta `--out <ruta-nueva.html>` y `--english`;
la base ya está en inglés. `render()` devuelve esa misma base. Este flujo no
vuelve a traducir ni reconstruir las diapositivas con las reglas anteriores,
ni recalcula los datos. No sobrescribe archivos existentes.

Las futuras revisiones parten de esta base y aplican sólo los cambios pedidos.
Se conserva el archivo recibido y se crea una versión nueva. Si se adopta otra
base, guardar una referencia nueva y actualizar el registro con su SHA-256.
Las versiones anteriores en español y el diccionario de traducción son
históricos; no contienen todos los cambios de Julia.

Para reproducir expresamente la v9 anterior desde los agregados:

```powershell
.venv\Scripts\python.exe -B tools\presentations\build_model_selection_deck_v9.py --historical
# Añadir --english para la traducción histórica.
```

`--source-html`, `--draft-selection` y `--january-cover-preview` pertenecen a
ese flujo histórico y requieren `--historical`.

## Herramientas PowerPoint

Scripts conservados para reproducir la presentación vigente:

```powershell
python tools/presentations/build_attrition_story.py `
  "references/presentations/source/Attrition model steps.pptx" `
  "output/presentations/Attrition model story.pptx"

python tools/presentations/refine_workplan_slide.py `
  "output/presentations/Attrition model story.pptx"
```

Requieren `python-pptx`. El segundo script también acepta `--deps <directory>` cuando la dependencia está instalada fuera del environment activo.

## Reportes HTML v2 de variables

`render_variable_assessment_v2.py` crea reportes visuales desde los JSON
congelados de un assessment. No ejecuta notebooks, SQL ni consultas a Redshift,
y no recalcula scores.

```powershell
# Prototipos aprobados
.venv\Scripts\python.exe -B tools\presentations\render_variable_assessment_v2.py `
  --run-dir output\assessments\attrition-43-monthly-fiscal-20260816 `
  --variables 04-location 09-gender 32-comp-ratio

# Lote completo después de aprobar el diseño
.venv\Scripts\python.exe -B tools\presentations\render_variable_assessment_v2.py `
  --run-dir output\assessments\attrition-43-monthly-fiscal-20260816 `
  --all
```

El renderer conserva los HTML originales, escribe `<slug>-v2.html` en cada
carpeta de variable y mantiene `html-v2-manifest.json` en la raíz del run.

El workflow v4 ya lo invoca automáticamente mediante
`config/variable_assessment_project.yaml > reporting.visual_html_v2`. Para
cada variable termina primero los JSON, notebook y documentación acumulativa;
luego genera el HTML v2 como artefacto principal `html`. El HTML exportado desde
el notebook se conserva como `html_notebook` para auditoría. El proyecto puede
sustituir o desactivar estos adaptadores sin modificar el motor del skill.

### Métricas privadas agregadas para variables sensibles

`build_sensitive_report_metrics.py` genera, sólo para variables con blocker
`sensitive_restricted`, un `private-aggregate-metrics.json` que el renderer v2
usa para explicar el comportamiento con gráficos y cifras agregadas. No cambia
scores, no ejecuta el assessment y no guarda filas, IDs, nombres, etiquetas
protegidas, compensación exacta, domicilios ni texto libre. Mantiene cohortes
de al menos 30; Gender se presenta como `CODE_n` y compensación como bandas.

```powershell
# Generar las métricas agregadas; --refresh-gender vuelve a ejecutar únicamente
# el audit agregado aprobado para la distribución anonimizada de Gender.
.venv\Scripts\python.exe -B tools\presentations\build_sensitive_report_metrics.py `
  --run-dir output\assessments\attrition-43-monthly-fiscal-20260816 `
  --refresh-gender --force

# Regenerar solamente los reportes sensibles que consumen esos artefactos.
.venv\Scripts\python.exe -B tools\presentations\render_variable_assessment_v2.py `
  --run-dir output\assessments\attrition-43-monthly-fiscal-20260816 `
  --variables 01-applied-to-a-job 02-more-than-3-job-applications 09-gender `
    14-commute-distance 17-non-respondents 18-intent-to-stay-items `
    19-career-goals-item 20-average-of-all-qvoice-items `
    21-standardized-normalized-within-region 31-compensation-grade `
    32-comp-ratio 33-within-team-compensation-range 36-high-risk-manager `
    37-high-turnover-under-this-person --force
```
