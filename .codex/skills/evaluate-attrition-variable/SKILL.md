---
name: evaluate-attrition-variable
description: Evaluate one or more HR or People Analytics candidate variables using problem context, a joint portfolio preflight, cumulative variable documentation, graph-first reports, and a portable project-configured evidence workflow with mandatory calculation-based verification for qualitative scores of 2. Use for Attrition through its local adapter and for other HR projects that provide compatible catalogs, rules, semantic hints, read-only query helpers, metadata schemas, documentation paths, and output paths.
---

# Evaluate Attrition Variable

Produce a repeatable evidence-based assessment without exposing row-level sensitive data. Keep the engine reusable across HR and People Analytics projects and apply the requested deliverable mode before rendering values. Put concrete variable catalogs, source schemas, source adapters, project-specific rules, additional privacy restrictions, language, and project paths in configuration. In Attrition, compose with the local `attrition-redshift-db` adapter for every database discovery or query.

## HR portability boundary

Keep `scripts/portfolio_workflow.py`, `scripts/profile_variable.py`, and
`scripts/run_assessment.py` free of concrete catalog variable names, source
schemas, and business formulas. Configure each project through
`config/variable_assessment_project.yaml` or equivalent CLI arguments:
catalog spec, scoring rules, semantic hint registry, read-only query helper,
metadata schemas, SQL roots, output root, and optional visual-report adapters.
The Attrition catalog is one
adapter and test portfolio; it is not engine logic. Preserve the engine's
baseline prohibition on HR identity, individual compensation, address, and
free-text values. A project adapter may add sensitive columns but must not
remove that baseline. For an explicitly internal aggregate analysis, the
Attrition adapter may display real protected-category labels that meet its
minimum cohort; `presentation` outputs still suppress or anonymize them. Read
the sibling [`attrition-redshift-db` reporting modes](../attrition-redshift-db/references/reporting-modes.md)
before choosing the mode.

## Required workflow

1. Read `references/scoring-rules.yaml`. Treat it as the editable source of truth for thresholds, score mappings, labels, and privacy suppression. Do not derive rules from narrative documentation at runtime. Resolve and record `presentation` (default) or explicitly requested `internal_analysis` before rendering distributions.
2. Read `references/assessment-spec.md`, `references/semantic-validation.md`, `references/semantic-hints.yaml`, and `references/workflow-contracts.md`. New or regenerated specs must use version 4. Classify every variable as `direct_field`, `precomputed_metric`, `grouped_mapping`, `derived_feature`, `hierarchy`, `survey`, or `external_source`. Semantic hints create questions only; they never prove a definition or raise a score.
3. Invoke the read-only database skill configured by the current project. For Attrition, use `attrition-redshift-db`, read its `SKILL.md` and `references/schema.md`, inspect current schemas when necessary, and validate the table, columns, date grain, entity/date join, population, formula, grouping, or hierarchy claim.
4. Before assigning any qualitative score of 2, save a purpose-built aggregate query under `queries/audits/` or `queries/profiles/`, state the acceptance rule, execute it, and record the actual metrics, date, SQL path, and `outcome: pass`. Do this proactively; do not wait for the user to question the definition.
5. Add structured `why`, `evidence`, and `recommended_action` rationale for every qualitative criterion scored 0 or 1. Add structured `verification` for every qualitative criterion scored 2.
6. Use the default population defined in the active scoring-rules file. The Attrition adapter defines `worker_type='Employee'`, `employee_type='Regular'`, `active_status=1`; another HR project must provide its own population contract. Record every override in the spec and workbook.
7. Apply blockers before interpreting points. Still populate all eight provisional scores. Never let a high point total replace a sensitive, external, unavailable, or TBD label.
8. Create aggregate profiling SQL. For events, measure observability as coverage and report event prevalence separately. Never interpret a missing event date as ordinary feature missingness when an event flag or eligible source feed can establish a non-event.
9. Print and inspect generated SQL before execution:

```powershell
& .venv\Scripts\python.exe -B `
  '.codex\skills\evaluate-attrition-variable\scripts\profile_variable.py' `
  --spec '<assessment-spec.yaml>' --print-sql
```

10. Run the profiler with the project environment and configured read-only query helper. In Attrition this is the local `.venv` plus the sibling Redshift skill, which reuses the secure Slides `.env`; do not copy credentials or connection code.

```powershell
& .venv\Scripts\python.exe -B `
  '.codex\skills\evaluate-attrition-variable\scripts\profile_variable.py' `
  --spec '<assessment-spec.yaml>' --output 'output/assessments/<profile.json>'
```

11. Render a new timestamped three-sheet workbook or use the v4 runner. Do not overwrite an earlier assessment.

```powershell
& .venv\Scripts\python.exe -B `
  '.codex\skills\evaluate-attrition-variable\scripts\render_assessment.py' `
  --profile 'output/assessments/<profile.json>' --output-dir 'output/assessments'
```

12. Open or programmatically inspect the workbook and verify sheet names, exact headers, row counts, totals, result labels, dates, percentages, comments, and rationale rows before reporting completion.

## Mandatory portfolio preflight

For a list, first capture the business problem, decision or use case, outcome,
population, unit of analysis, time horizon, knowledge boundary, constraints,
stakeholder questions, and known relationships. Then analyze the complete
portfolio before any employee aggregate query.
The preflight may use the request, project documentation, the editable semantic
hint registry, and metadata from the configured source only. In Attrition, use
Redshift `information_schema`. It must create
`run-request.yaml`, `portfolio-context.yaml`, and `portfolio-context.html` with
exactly one entry per requested variable, grouped material questions, privacy,
relationships, dependencies, original order, stable dependency order, and
cycles. Add a portfolio overview that connects semantic types, source concepts,
variable roles, hypotheses, dependencies, and the supplied problem context. Do
not profile coverage or prevalence during preflight.

Present unresolved material questions globally. Continue only after decisions
are recorded or under an explicit conservative policy; unknown answers cap the
affected criterion at 1 or 0. For every ratio, rate, or percentage—including
the Attrition variable `Comp ratio`—ask: “Parece una división; ¿qué constituye
el numerador y el denominador?”. Definition cannot be 2 without an independent
recalculation or authoritative lineage plus aggregate reconciliation on the
target population.

Evaluate variables in dependency order and publish the workbook in original
request order. A dependent derived variable inherits a Definition cap when its
base concept remains pending. Keep original order inside a cyclic dependency
group and report the cycle as a gap.

## Guided explicit-plan mode

For a new guided assessment, Codex must author one `analysis-plan-vN.yaml` per
requested variable after metadata preflight and before any aggregate SQL. Run
the runner with `--strict-analysis-plans` and one `--analysis-plan` argument
per variable. Each plan must carry explicit Spanish validation stories,
purpose-built SQL references, acceptance rules, population, grain, knowledge
boundary, semantic type, and source reasoning. `validation_focus` may orient
the plan, but it must never be expanded automatically into a material
validation in this mode.

When observed aggregate evidence reveals a new material gap, stop the current
variable, have Codex author `analysis-plan-vN+1.yaml` with a
`plan_revision_reason`, freeze it before the follow-up query, and then rerun
the variable. The legacy `validation_focus` and automatic adaptive-story paths
exist only for clearly marked historical migration; do not use them for new
guided work.

## Mandatory one-variable reasoning cycle

Do not treat a list of variables as one generic profiling job. Evaluate it
sequentially, one variable at a time, and finish that variable's checkpoint,
notebook, HTML, JSON, and evidence before starting the next one.

For each variable:

1. Start from the shared problem and portfolio context, then establish fresh
   evidence boundaries for the current variable. Define the concept, role in
   the use case, intended use, prediction cutoff, eligible population, and
   result grain.
2. Read the current project documentation and accumulated findings from
   completed variables. Use related concepts, dependencies, shared sources, and
   prior caveats to refine hypotheses and validations. Mark all reused knowledge
   as context, never as evidence for the current score.
3. Use the read-only database skill configured for the project to discover
   direct fields, synonyms, components, related tables, dates, history, and
   join keys. In Attrition, use `attrition-redshift-db`. Classify the semantic
   type before choosing validations.
4. Write a variable-specific analysis plan with source reasoning,
   `validation_focus`, semantic modules, safe visualizations, and
   expected acceptance rules. A generic checklist without concept-specific
   reasoning is invalid.
5. If the requested variable is direct, profile its fields and relevant
   alternatives, including data types, safe domains, top values, relationships,
   temporal behavior, and employee-date grain.
6. If it is not direct, document derivation alternatives and select one. Test
   component availability, formula, boundaries, deduplication, null behavior,
   temporal join, and leakage. A proposed route is not a confirmed feature.
7. Execute aggregate SQL and inspect the actual results. Compare the evidence
   with every planned rule and with the current 2/1/0 outcome.
8. Perform a sufficiency review. When the results expose a missing semantic,
   temporal, join, privacy, or edge-case check, add a purpose-built aggregate
   query or notebook section and rerun this variable before continuing.
9. Finalize the variable only when the notebook executes without errors, the
   configured visual HTML explains all eight scores with graph-first evidence,
   and the checkpoint records the evidence status. Keep the notebook HTML as
   audit support; do not publish it as the primary reader-facing report. Update
   or create its document under the configured
   `docs/variables/` root using a managed cumulative section that preserves
   human-authored content. Then begin the next variable with the updated
   documentation and compact knowledge summary available as context.

Python is the execution, scoring, and rendering layer. It does not replace the
variable-specific reasoning that defines what to query, which tests are
necessary, or how to interpret a failed or pending rule. Shared helpers are
expected; identical analysis plans for semantically different variables are
not.

## Spanish narrative contract

All generated material intended to explain the assessment must be written in
Spanish. This includes notebook markdown and displayed output, HTML reports,
workbook rationales and comments, analysis plans, validation stories,
limitations, conclusions, and recommended actions. Keep canonical scoring
criterion names (`Source`, `Definition`, `Coverage`, `Missingness`,
`Consistency`, `History`, `Join`, and `Effort`), source variable names, table
and column names, SQL, Python code, formulas, and technical identifiers in
their original language when translating them would reduce traceability.

Every variable must define a narrative validation story. The report begins
with a chronological summary of source availability, usable history, material
changes, and the resulting decision. It then explains each validation as a
short auditable story containing:

1. the question or claim being tested;
2. why the check matters for the requested concept and intended HR use;
3. fields, tables, population, grain, and temporal boundary;
4. whether the evidence is `defining`, `supporting`, or `contextual`;
5. saved aggregate SQL and the acceptance rule stated before execution;
6. observed aggregate metrics and outcome;
7. interpretation, affected scoring criterion, and maximum allowed score;
8. limitations and recommended next action.

Use related fields only when the variable-specific hypothesis explains why
the relationship is informative. Contextual evidence can reveal anomalies or
support interpretation, but it cannot by itself prove a definition or raise a
criterion to score 2. For example, a job-family or level change around a
rehire date may describe the new employment episode; it is not required for a
rehire and does not replace flag/date and employment-sequence validation.

## Evidence rules

- Use read-only, aggregate SQL only. Keep employee IDs internal to `COUNT(DISTINCT ...)` and joins.
- Enforce the minimum shared cohort configured in the rules file. Do not output names, IDs, exact compensation, addresses, or free text. In `presentation`, suppress or anonymize protected attributes. In explicitly requested `internal_analysis`, real protected-category labels and their aggregate counts/percentages are allowed only for buckets at or above the minimum cohort; the report must carry that mode and must not be reused as a presentation.
- Define `First observed date` as the first dated aggregate with at least one observable employee.
- Define `Usable since date` as the first observation in a run of three consecutive observations with at least 95% coverage, unless the editable rules change those values.
- Score historical depth from usable history: `2` at 24 or more months, `1` at 6-23 months, and `0` below 6 months, for a single wave, or when leakage makes the history unusable.
- Infer measurement frequency from observation dates. Preserve the semantic prefixes for snapshots, events, derived features, surveys, and external sources.
- Base qualitative scores on concrete schema, definition, distribution, join, and derivation evidence. Use score overrides only with a written reason.
- A qualitative score of 2 is invalid without a current calculation-based verification item containing method, evidence, result, date, saved SQL reference, acceptance rule, passing outcome, and the required aggregate metrics.
- The runner must calculate `metrics`, `observed`, and `outcome` from frozen rows returned by executed SQL. Values written manually in the spec are historical input only and cannot enable score 2. Record SQL and result SHA-256 hashes in `evidence-ledger.json`.
- For a precomputed metric, derived feature, or hierarchy, Definition 2 requires independent recalculation or authoritative lineage plus aggregate reconciliation. Similar fields in adjacent tables do not confirm the target field.
- For hierarchy claims, report reconstructed, unresolved, root, cycle, and convergence metrics, and validate root semantics separately. A single common root does not by itself prove CEO.
- For grouped fields, audit detailed-to-group contradictions and mapping changes over time. Cardinality alone is insufficient.
- A qualitative score of 0 or 1 without structured rationale is invalid and must stop profiling. Coverage, missingness, and history rationale is calculated from the profiled windows, dates, and thresholds.
- A score override of 0 or 1 must include a reason, supporting evidence, and recommended action. Rationale rows identify these as `Configured override`.
- Read `docs/variables/` before each variable for reviewed definitions, relationships, and known caveats; update the configured document after the variable completes. Revalidate database-dependent findings whenever state may have changed. Narrative documentation is cumulative context, not current proof.
- Treat `config/attrition_candidate_variables.yaml` version 2 and its generated workbooks as legacy until each score-2 claim is migrated with current version-4 evidence. Never invent verification to preserve an old score.
- Write workbook rationales, comments, and verification explanations in
  Spanish under the narrative contract above.

## Score-2 stop conditions

Cap the affected criterion at 1 and explain the pending work when any of these
conditions applies:

- the exact business definition, formula, mapping, hierarchy root, or temporal rule is unknown;
- the target field cannot be recalculated and authoritative lineage with reconciliation is unavailable;
- only a field name, dashboard caption, document, adjacent table, or prior score supports the claim;
- the audit SQL is not saved, the metrics are missing, or the acceptance rule did not pass;
- aggregate mismatches, duplicate joins, cycles, unresolved chains, or mapping contradictions remain unexplained.

## Reproducible v4 runner

Use the runner after printing and reviewing SQL, or with offline aggregates for tests:

```powershell
& .venv\Scripts\python.exe -B `
  .codex\skills\evaluate-attrition-variable\scripts\run_assessment.py `
  --spec <assessment-spec.yaml>
```

For a natural variable or list request, use the minimal request contract:

```powershell
& .venv\Scripts\python.exe -B `
  .codex\skills\evaluate-attrition-variable\scripts\run_assessment.py `
  --request <run-request.yaml> --preflight-only
```

The runner loads `config/variable_assessment_project.yaml` by default when it
exists. Use `--project-config`, `--catalog-spec`, `--rules`,
`--semantic-hints`, or `--query-helper` to run the same engine in another HR
project. `intended_use` is the canonical cross-project request field;
`attrition_use` remains a backward-compatible alias.

Review the generated portfolio context, record decisions, then rerun with the
request. Use `--continue-conservative` only when unresolved answers are
explicitly accepted as score caps. Offline integration tests can pass
`--aggregate-results`, `--metadata-results`, and `--skip-metadata`.

The runner evaluates variables sequentially with shared problem context and
fresh variable-level evidence, writes each variable folder, documentation
update, and checkpoint before advancing, and works under a hidden
`.<run-id>.working` directory. It publishes
`output/assessments/<run-id>/` only after every variable artifact and
the workbook pass validation. A failed run keeps `run-state.json` in
the working directory and must not be presented as a validated assessment.

The published run includes the approved three-sheet Excel, `manifest.json`,
`run-request.yaml`, `portfolio-context.yaml`, `portfolio-context.html`, a
run-level `evidence-ledger.json`, copied inputs/evidence SQL, and one
`vars/<NN-variable-slug>/` folder
per assessment row with `.ipynb`, primary visual `.html`, retained notebook
HTML, and per-variable JSON files. When the project enables
`reporting.visual_html_v2`, its visual HTML is the primary `html` artifact and
the executed notebook export remains `html_notebook` for auditability. The
manifest also records each cumulative project-documentation
path updated after a variable completes. Each variable folder must include `analysis-plan.yaml`,
one or more immutable `analysis-plan-vN.yaml` files, `evidence-ledger.json`,
`decision.json`, `variable-spec.yaml`, `checkpoint.json`,
`report_detail.json`, copied SQL, and frozen aggregate query results.
The primary HTML and notebook must be detailed audit reports that explain how
every score was concluded.

Freeze a planned notebook alongside every immutable pre-execution plan. After
SQL execution, create the executable notebook from frozen aggregate results;
it must save reusable PNG charts under `charts/` and list them in
`charts-manifest.json`. The reader-facing visual HTML is the primary report:
it must use the configured presentation template, render every validation in
its own narrative section, include the notebook charts in a graph-first
gallery, and use a dynamic slide count rather than a fixed number of pages.

## Output contract

The preferred runner creates `output/assessments/<run-id>/` with manifest, profile JSON, Excel, inputs, evidence copies, and one `vars/<NN-variable-slug>/` folder per variable containing notebook, primary visual HTML, retained notebook HTML, `assessment.json`, `coverage.json`, `score_rationales.json`, and `report_detail.json`. Configure the primary visual report through `reporting.visual_html_v2` in the project adapter: it may call a project-local aggregate-metrics builder before a generic renderer, and must run after the variable's frozen JSON artifacts exist. The legacy renderer can still create `output/assessments/<variable-slug>_assessment_<YYYYMMDD-HHMMSS>.xlsx`; use `multiple-variables` as the slug for a batch.

The primary per-variable HTML is not a notebook conversion or a summary page.
It must show the problem and
portfolio context, accumulated relevant knowledge, definition and population,
source columns and related columns, aggregate column profiles, safe distinct/top
values, safe column relationship comparisons, coverage, the exact 2/1/0 rule
applied to each criterion, observed evidence, outcome, limitations, and
recommended action. Prefer charts for scores, trends, distributions,
completeness, mappings, bands, and comparisons; place the corresponding tables
after the chart as auditable detail. In `presentation`, do not expose raw
protected-category values; show the suppression reason instead. In explicitly
requested `internal_analysis`, show real categorical labels only when every
displayed bucket meets the configured cohort minimum. Never show identity,
address, free-text, individual, or exact-compensation values in either mode.

The HTML must also tell the reasoning story. Start with a concise historical
flow and then render every validation in planned order using the question,
reason, method, acceptance rule, observed result, interpretation, score impact,
limitation, and action fields. A table of metrics without this narrative is an
incomplete report.

Keep exactly these sheets, in this order:

- `Variable assessment`: one row per variable with exactly these 23 columns, in order: `Category`, `Variable`, `Notes`, `Considerations`, `Source`, `Source Detail 1`, `Source Detail 2`, `Level data`, `History available`, `Observation frequency`, `Type`, `values`, `Blocker / special label`, `Source`, `Definition`, `Coverage`, `Missingness`, `Consistency`, `History`, `Join`, `Effort`, `Total`, `Result`.
- `Coverage`: one row per variable and observation date, including eligible, observable, missing, coverage percentage and score, event prevalence, stable-coverage flag, first observed date, usable-since date, population definition, and numerator definition. Add one evidence row with blank dates when a source is external or unavailable.
- `Score rationale`: exactly one row for every 0/1 score and no rows for score 2, with criterion, score, status/rule, reason, supporting evidence, recommended action, scoring method, source table, and source columns. Every corresponding 0/1 score cell in `Variable assessment` must have a short comment pointing here.

Use `assets/variable-assessment-template.xlsx`; do not silently change its sheet names or headers.

## Resources

- `references/scoring-rules.yaml`: editable rules and thresholds loaded by the scripts at runtime.
- `references/assessment-spec.md`: YAML contract, standard/event/custom-query examples, and allowed evidence statuses.
- `references/semantic-validation.md`: mandatory validation patterns for direct, precomputed, derived, hierarchy, grouped, and external variables.
- `references/semantic-hints.yaml`: editable preflight clues, required topics, grouped questions, and publication policies; never score evidence.
- `references/workflow-contracts.md`: run request, portfolio context, immutable plan, ledger, and decision contracts.
- `config/variable_assessment_project.yaml`: project adapter for catalog, rules, hints, query helper, schemas, cumulative documentation root, output paths, and optional visual-report adapters; it lives in the consuming project, not in engine code.
- `scripts/portfolio_workflow.py`: deterministic preflight, dependency ordering, explicit-story materialization, hashes, and frozen-result evaluation.
- `scripts/profile_variable.py`: guarded aggregate profiler and scoring engine.
- `scripts/render_assessment.py`: deterministic three-sheet workbook renderer and validator.
- `assets/variable-assessment-template.xlsx`: approved workbook layout.

