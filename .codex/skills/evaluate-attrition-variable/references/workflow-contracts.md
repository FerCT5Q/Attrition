# Contratos del workflow híbrido v4

El assessment conserva `version: 4`. Los contratos de orquestación tienen su
propia versión y no cambian las tres hojas obligatorias del Excel.

## `variable_assessment_project.yaml`

Adaptador portable del proyecto de RH. Define `catalog_spec`, `rules`,
`semantic_hint_registry`, `query_helper`, `output_root`, `audit_sql_root`,
`profile_sql_root`, `documentation.root` y
`metadata.default_schema/search_schemas`. El motor no debe
contener nombres de variables, esquemas ni rutas de conexión concretas. Otro
proyecto de RH reutiliza el workflow sustituyendo este archivo y su catálogo.
Las protecciones base para identidad, compensación exacta, domicilios y texto
libre permanecen en el motor; el adaptador sólo puede añadir columnas sensibles.
El modo `presentation` también suprime atributos protegidos. Un modo
`internal_analysis` solicitado expresamente puede mostrar sus etiquetas
categóricas reales en agregados con cohorte mínima; debe registrarlo en el
artefacto y no puede reutilizarse como entregable de presentación.

Opcionalmente, `reporting.visual_html_v2` declara un `renderer` y, si el
proyecto lo necesita, un `metrics_builder`. El runner los ejecuta por variable
despues de congelar sus JSON y antes de avanzar a la siguiente. El renderer
visual pasa a ser el artefacto `html` principal; el export del notebook se
conserva como `html_notebook`. Los adaptadores, sus rutas, argumentos,
marcadores requeridos y politicas de privacidad pertenecen al proyecto, no al
motor portable.

## `run-request.yaml`

Entrada mínima del usuario. Cada variable necesita nombre, uso analítico de RH,
población y fecha o regla de conocimiento. En Attrition, ese uso describe cómo
se empleará la variable para attrition. Puede incluir decisiones a preguntas del
preflight y `unknown_policy: conservative` para continuar con score máximo 1 o
0 cuando una respuesta se desconoce. El request acepta además contexto global
del problema para conectar las variables con la decisión, outcome, población,
grain, horizonte, restricciones e hipótesis del proyecto.

```yaml
schema_version: 1
language: es
unknown_policy: pause
problem_context:
  problem_statement: Evaluar qué señales de RH aportan información útil para entender attrition.
  decision_or_use_case: Priorizar variables para un modelo longitudinal y análisis de segmentos.
  outcome: Attrition posterior al snapshot mensual.
  population: Empleados regulares activos.
  unit_of_analysis: Empleado-snapshot.
  knowledge_boundary: Cierre del snapshot mensual.
  constraints:
    - No exponer datos sensibles ni usar información futura.
  portfolio_hypotheses:
    - Las señales de compensación base y relativas están conectadas, pero no son equivalentes.
  known_relationships:
    - variables: [Comp ratio, Within team compensation range]
      relationship: La variable relativa depende de la definición del ratio base.
      why_relevant: Una brecha en el concepto base limita la feature derivada.
variables:
  - name: Comp ratio
    intended_use: Medir posición relativa frente al rango salarial aplicable.
    population: Empleados regulares activos en el snapshot.
    knowledge_date: Cierre del snapshot mensual.
decisions: {}
```

`intended_use` es el nombre canónico. `attrition_use` se acepta como alias para
los catálogos históricos de Attrition.

## `portfolio-context.yaml`

Se genera antes de perfiles agregados. Puede usar semántica, documentación y
metadata de la fuente configurada —`information_schema` de Redshift en
Attrition—, pero no valores de empleados ni agregados de población.
Incluye significado probable, tipo semántico inicial, componentes, relaciones,
dependencias, privacidad, preguntas materiales, orden original, orden de
evaluación y ciclos. También conserva `problem_context`, un overview conjunto
de tipos y roles, alineación de cada variable con el caso de uso y un mapa de
relaciones provistas, inferidas por dependencias o compartidas por fuente.

## `analysis-plan-vN.yaml`

For guided runs, Codex authors this plan after metadata preflight and before aggregate SQL.
Invoke `--strict-analysis-plans` and supply one plan per requested variable.
The plan must contain a non-empty explicit `validation_story` with the question,
reason, method, saved aggregate SQL, acceptance rule, evidence role, population
and grain. `validation_focus` is a hypothesis aid only and cannot be
materialized automatically.

If results expose a new material gap, freeze a higher plan version before the
follow-up SQL. Versions above 1 require `plan_revision_reason`. Historical
catalog fallback is migration-only and must be recorded in `plan_authorship`;
it is not allowed by strict guided runs.

Se congela antes de ejecutar SQL para una variable. Contiene claim, población,
grain, límite temporal, historias explícitas, SQL planeado y reglas de
aceptación. Incluye el contexto del problema, la alineación de la variable,
documentación vigente y un resumen compacto del conocimiento acumulado de las
variables ya completadas. Esos elementos guían hipótesis, pero se marcan como
contexto no probatorio. Un nuevo plan sólo puede escribirse como una versión
superior; no se reemplaza una versión ya ejecutada.

## Documentación acumulativa por variable

The managed section reflects the latest assessment and a factual history block
is appended once per `run_id`. The history records plan versions, validation
outcomes/score effects and aggregate SQL references. It stores explained
decisions and evidence, never hidden chain of thought, and is context rather
than score evidence for later variables or runs.

Después de validar notebook, HTML visual principal y artefactos de una variable, el runner crea o
actualiza su Markdown bajo `documentation.root`. `analysis.documentation_path`
puede dirigir varias variables relacionadas a un documento compartido; sin esa
configuración se usa `<variable-slug>/README.md`. El runner reemplaza únicamente
la sección administrada de esa variable y preserva el contenido humano.

La sección registra contexto del problema, relación con el portafolio,
definición, fuente, resultado, hallazgos agregados, limitaciones, acciones y SQL
trazable. La siguiente variable puede leerla como contexto. Nunca habilita score
2 ni sustituye evidencia actual.

## `evidence-ledger.json`

Registra cada SQL ejecutado o reutilizado, hash SHA-256 del SQL y del resultado,
fecha, claim, población, grain, ventana, métricas calculadas, regla y outcome.
Los campos `metrics` y `outcome` declarados en el spec se conservan sólo como
entrada histórica y nunca habilitan score 2.

## Notebook, charts and visual HTML

Freeze a planned `.ipynb` beside every `analysis-plan-vN.yaml` before SQL. It
documents the plan and does not execute queries. After aggregate results are
frozen, the executed notebook creates reusable images in `charts/` and an
ordered `charts-manifest.json`. The primary visual HTML consumes those saved
images and must remain a Spanish human-readable explanation, not a notebook
conversion. It renders every validation and uses dynamic page/navigation counts
so all stories and available charts remain visible.

## `decision.json`

Guarda scores finales, límites automáticos, blocker, dependencias heredadas,
evidencia reutilizada, brechas y acciones. No guarda razonamiento interno libre.
