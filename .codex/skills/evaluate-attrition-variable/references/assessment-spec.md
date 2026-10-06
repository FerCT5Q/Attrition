# Assessment Spec Reference

Use one YAML spec for one or more variables. Keep employee identifiers inside the configured source system; the profiler only accepts date-level aggregate results.

## Required version and evidence gate

New and regenerated specs must use `version: 4`. Versions 1, 2, and 3 are legacy:
they may be inspected as historical records, but the profiler and renderer reject
them because they do not prove qualitative scores of 2.

Before setting a qualitative status that maps to 2, classify the variable as one
of `direct_field`, `precomputed_metric`, `grouped_mapping`, `derived_feature`,
`hierarchy`, `survey`, or `external_source`, run the appropriate aggregate audit,
and add structured `verification`. A field name, dashboard caption, prior
workbook, or plausible business interpretation is not verification.

Read `semantic-validation.md` before preparing a version 4 spec.

The v4 assessment spec remains the scoring contract. Portfolio orchestration is
defined separately in `workflow-contracts.md`: a minimal `run-request.yaml`
captures the HR problem context and selects one or more catalog variables,
preflight writes
`portfolio-context.yaml` and `.html`, and each deep evaluation freezes an
`analysis-plan-vN.yaml`, `evidence-ledger.json`, and `decision.json`.

Before any aggregate employee query, the runner must complete metadata-only
preflight for the whole requested list. The workbook keeps original request
order; execution follows the stable dependency order recorded in the portfolio
context.

## Standard snapshot example

```yaml
version: 4
variables:
  - category: Role / job
    variable: Job family
    notes: CJFs
    definition: Job family and job family group recorded for each active employee snapshot.
    source:
      type: Database
      table: hrda.post_hire_monthly_worker_dtls
      columns: [job_family, job_family_group]
      status: confirmed_accessible
    level_data: Employee snapshot
    measurement:
      type: snapshot
      date_column: fis_mo_end_dt
      fiscal_year_column: fiscal_year
      employee_id_column: employee_id
      observable_columns: [job_family, job_family_group]
      observable_mode: all
    population:
      mode: default
    numerator_definition: Employees with both job family fields populated.
    evidence:
      definition: clear_stable
      consistency: clean_standardized
      join: reliable_employee_date
      effort: direct_or_simple_sql
    verification:
      semantic_type: direct_field
      source:
        method: schema_access_check
        evidence: The table, required columns, and read-only access were checked.
        result: The source is accessible at the intended snapshot grain.
        as_of_date: <YYYY-MM-DD>
        query_reference: queries/audits/job_family_score2_audit.sql
        acceptance_rule: Every required table and column must be accessible.
        outcome: pending
      definition:
        method: authoritative_definition_and_data_audit
        evidence: The source-owned definition was compared with aggregate grain and domain results.
        result: Replace with the observed result after running the audit.
        as_of_date: <YYYY-MM-DD>
        query_reference: queries/audits/job_family_score2_audit.sql
        acceptance_rule: The documented grain and domain must match the aggregate audit.
        outcome: pending
        metrics:
          eligible_rows: null
          populated_rows: null
          distinct_values: null
      consistency:
        method: longitudinal_aggregate_audit
        evidence: Monthly normalized cardinality and mapping stability were audited.
        result: Replace with the observed result after running the audit.
        as_of_date: <YYYY-MM-DD>
        query_reference: queries/audits/job_family_score2_audit.sql
        acceptance_rule: No unexplained normalization or longitudinal mapping anomaly is allowed.
        outcome: pending
        metrics:
          months_checked: null
          anomaly_count: null
      join:
        method: key_grain_and_temporal_reconciliation
        evidence: Employee and snapshot keys were checked for missing and duplicate matches.
        result: Replace with the observed result after running the audit.
        as_of_date: <YYYY-MM-DD>
        query_reference: queries/audits/job_family_score2_audit.sql
        acceptance_rule: Every eligible employee-date key must match once at the intended grain.
        outcome: pending
        metrics:
          eligible_rows: null
          matched_rows: null
          unmatched_rows: null
          duplicate_rows: null
      effort:
        method: direct_field_inspection
        evidence: The requested feature and required filters were inspected.
        result: The feature requires no derivation beyond projection and approved filtering.
        as_of_date: <YYYY-MM-DD>
        query_reference: queries/audits/job_family_score2_audit.sql
        acceptance_rule: No unresolved derivation, mapping, or external dependency is allowed.
        outcome: pending
    blocker: none
```

The `pending` values and null metrics are deliberate. Replace them only with
results from the referenced query. The profiler accepts a score of 2 only when
all required fields are present, required metrics are numeric, and `outcome` is
`pass`.

At runtime, manually written `metrics`, `observed`, and `outcome` values are not
trusted. The runner preserves them as declared input, executes the referenced
SQL, freezes aggregate rows, calculates metrics and outcomes, and records SQL
and result hashes. Missing or failed executable evidence automatically caps the
criterion instead of preserving a declared 2.

The default population is configured in `scoring-rules.yaml`. Override a default field explicitly when needed:

```yaml
population:
  mode: default
  overrides:
    active_status: null
  display: "Regular Employee snapshots, active and inactive"
```

Use `mode: all` for a source without workforce-filter fields. Use `mode: custom` with structured filters and a required display label:

```yaml
population:
  mode: custom
  display: "Completed survey responses"
  filters:
    - column: response_status
      operator: eq
      value: Complete
```

Supported filter operators are `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in`, `not_in`, `is_null`, and `not_null`.

## Event example

For event variables, define observability separately from occurrence. Coverage answers whether the employee-event state can be observed; event prevalence answers how often the event occurred.

```yaml
measurement:
  type: event
  date_column: fis_mo_end_dt
  fiscal_year_column: fiscal_year
  employee_id_column: employee_id
  observable_columns: [manager_change]
  observable_mode: all
  event_conditions:
    - column: manager_change
      operator: eq
      value: 1
```

Supported event operators are `not_null`, `eq`, `in`, and `positive`. Event prevalence uses observable employees as its denominator. Small event counts are suppressed using the privacy threshold in the rules file.

## Custom aggregate SQL

Use custom aggregate SQL for survey eligibility, joins, rolling features, or other cases that cannot be expressed as one source table. Keep the SQL read-only and aggregate-only.

```yaml
profile:
  mode: aggregate_sql
  aggregate_sql_file: qvoice_intent_coverage.sql
population:
  mode: custom
  display: "Active Regular Employees at the pre-survey snapshot"
```

Return exactly one row per observation date with these aliases:

```text
snapshot_date          required date
fiscal_year            optional string or number
eligible_employees     required aggregate count
observable_employees   required aggregate count
event_employees        optional aggregate count
notes                  optional aggregate-safe text
```

The configured read-only database helper must reject write statements, multiple statements and `SELECT *`. In `presentation`, it also rejects protected output labels. In explicitly requested `internal_analysis`, it may return approved protected *categorical* labels only with a distinct-employee aggregate and every displayed bucket at or above the configured cohort minimum. The profiler also suppresses dates whose eligible cohort is below the configured minimum.

## External or unavailable source

Do not invent coverage rows for a source that has not been validated.

```yaml
profile:
  mode: external
source:
  type: External
  detail: External LinkedIn source; not found in HRDA
  columns: [TBD employee/profile match, observation date]
  status: likely_unconfirmed
measurement:
  type: external
evidence:
  definition: needs_alignment
  consistency: unreliable
  join: not_joinable
  effort: heavy_or_unresolved
rationale:
  source:
    why: The source and access path have not been confirmed.
    evidence: No approved LinkedIn feed was found in the validated HRDA schemas.
    recommended_action: Identify an approved source owner and confirm access terms.
  definition:
    why: The employee/profile matching definition is not approved.
    evidence: The proposed source has no validated employee or effective-date key.
    recommended_action: Define the permitted matching method and observation grain.
  consistency:
    why: Value and temporal consistency cannot be assessed without a source.
    evidence: No aggregate history or schema is available for normalization checks.
    recommended_action: Profile aggregate category and date stability after access is approved.
  join:
    why: No reliable time-safe join path has been demonstrated.
    evidence: Required employee/profile and observation-date keys remain TBD.
    recommended_action: Validate a governed crosswalk and effective-date join.
  effort:
    why: The collection and matching approach requires unresolved engineering and governance.
    evidence: Scraping, identity matching, and historical backfill have not been approved.
    recommended_action: Replace scraping with an approved feed and scope the backfill.
blocker: external_third_party
```

Use `profile.mode: unavailable` and `blocker: not_available_exclude` when no usable source or acceptable derivation path exists.

## Guided plan enforcement

For new guided assessments, do not rely on generated stories from
`validation_focus`. Codex authors and supplies an explicit
`analysis-plan-vN.yaml` before SQL, then invokes the runner with
`--strict-analysis-plans`. The plan must contain a non-empty
`validation_story` for the current variable, and every story must name its SQL
reference and acceptance rule. A version greater than 1 requires
`plan_revision_reason` because it was added after evidence review. The legacy
catalog fallback remains only for historical migration and must never be used
to claim that an agent reasoned through a new validation.

Freeze a planned notebook beside the plan before execution. After evidence is
frozen, execute the notebook from captured aggregate results and persist its
figures under `charts/` with `charts-manifest.json`; the visual HTML uses those
files as graph-first evidence.

## Variable-specific analysis plan

A multi-variable spec must provide either an inline `analysis` block
for every variable or a top-level `analysis_catalog` path. The catalog
is keyed by the exact variable name and must cover the spec with no missing or
extra entries.

~~~yaml
analysis_catalog: attrition_variable_analysis_v4.yaml
~~~

Each merged analysis entry requires:

~~~yaml
semantic_type: grouped_mapping
intended_use: Occupational context for the configured modeling use case.
source_reasoning: Detailed and grouped fields represent different levels.
validation_focus:
  - field roles
  - detail-group contradictions
  - unmapped values
  - temporal mapping changes
prediction_cutoff: Use only information known by the prediction snapshot.
prior_evidence_policy: Prior results are context only and require revalidation.
depends_on: []
~~~

The runner derives semantic modules and visualizations from this entry and
writes `analysis-plan.yaml` before executing the variable notebook.
The plan must be specific enough to explain why those checks are required for
the concept. A semantic type by itself is not a complete plan.

`depends_on` is optional and names other variables in the same request. The
runner validates the graph, evaluates prerequisites first, preserves original
order inside cycles, and limits a dependent Definition when a base concept is
not confirmed.

Variables are processed sequentially. The current plan includes the shared
problem context, portfolio overview, variable alignment, existing project
documentation and compact knowledge from variables already completed. Give
priority to dependencies, explicit relationships and shared source concepts,
while retaining the broader portfolio as background. These summaries are never
score evidence. The current variable must still run its own population, grain,
time-window, and acceptance-rule checks.

After execution, `gap_review` must list every score below 2 and any
failed or pending semantic, temporal, join, privacy, or edge-case condition. Add
and execute a purpose-built aggregate validation before finalizing the variable
when the observed results reveal an unplanned gap.

## Detailed report configuration

Use the optional `report` block when the HTML should explain related source fields that are not part of the scoring numerator, or when multiple columns represent levels of the same concept. These fields are profiled with aggregate-only queries and do not change scores by themselves.

```yaml
report:
  related_columns: [job_family_short, job_family_group_short]
  column_descriptions:
    job_family: Detailed job family recorded on the employee monthly snapshot.
    job_family_group: Higher-level grouping of job families.
  comparison_pairs:
    - left: job_family
      right: job_family_group
```

The runner writes `report_detail.json` into each `vars/<NN-variable>/` folder and renders it into the notebook and HTML. The report must show the problem and portfolio context, applied scoring rule, observed metrics, outcome, limitation/action for every criterion, plus safe column profiles, safe value distributions, and safe column comparisons. Render scores, time trends, completeness, distributions, bands and mappings as charts before their complementary detail tables whenever safe aggregate evidence exists. In `presentation`, raw protected-category labels are suppressed with a visible reason. In explicitly requested `internal_analysis`, real labels are permitted only for approved categorical fields and buckets at or above the configured cohort minimum. Identity, individual, compensation-exact, date-like, address-like and free-text values remain suppressed in both modes.

## Spanish validation story

Generated explanatory artifacts use Spanish. An analysis catalog with
`language: es` must provide Spanish `definition`, `numerator_definition`,
`intended_use`, `source_reasoning`, and `validation_focus` values for every
variable. `attrition_use` remains an accepted legacy alias. The runner replaces
historical input prose with these publication values while preserving technical
names and a frozen copy of the source spec.

Use `validation_story` entries for every check in a new guided plan. They need a specific
question, rationale, aggregate query, or contextual relationship:

```yaml
validation_story:
  - id: flag_date_alignment
    criterion: consistency
    evidence_role: defining
    question: ¿Coinciden el flag y la fecha del evento?
    why: Una contradicción impide reconstruir el evento de forma reproducible.
    fields: [event_flag, event_date, snapshot_date]
    method: Reconciliación agregada por snapshot.
    sql_reference: queries/audits/example_event_audit.sql
    acceptance_rule: No debe haber flags sin fecha, fechas sin flag ni fechas futuras.
    metric_checks:
      - metric: flagged_without_date
        aggregate: sum
        operator: eq
        threshold: 0
```

At runtime the report adds observed metrics, outcome, interpretation, score
impact, limitation, and recommended action. `evidence_role` must be one of
`defining`, `supporting`, or `contextual`. Contextual checks cannot increase a
score or satisfy the score-2 evidence gate.
## Evidence statuses

Choose only statuses defined in `scoring-rules.yaml`:

| Criterion | 2 | 1 | 0 |
|---|---|---|---|
| Source | `confirmed_accessible` | `likely_unconfirmed` | `unavailable` |
| Definition | `clear_stable` | `needs_alignment` | `unclear` |
| Consistency | `clean_standardized` | `normalization_needed` | `unreliable` |
| Join | `reliable_employee_date` | `mapping_or_validation` | `not_joinable` |
| Effort | `direct_or_simple_sql` | `moderate_transformation` | `heavy_or_unresolved` |

Coverage, missingness, and history are calculated from the aggregate observations. If a complex case requires an override, provide an explicit reason:

```yaml
score_overrides:
  history:
    score: 0
    reason: Source contains target leakage despite multiple dated cycles.
    evidence: The current composite includes termination information from the modeled outcome window.
    recommended_action: Rebuild the composite from fields known at each prediction snapshot.
```

Set `quality.leakage_risk: true` to force the normal history calculation to zero. Set `quality.systematic_missingness: true` when aggregate segment checks reveal systematic missingness that the overall monthly rate hides.

## Allowed blockers

- `none`
- `sensitive_restricted`
- `external_third_party`
- `not_available_exclude`
- `tbd`

Blocker labels override the point result but do not erase the eight provisional scores.

## Structured score rationale

For each qualitative criterion with status score 0 or 1, add a `rationale`
entry with all three fields below. Profiling fails before an output file is
written when any required field is absent.

```yaml
evidence:
  definition: needs_alignment
  consistency: normalization_needed
  join: reliable_employee_date
  effort: moderate_transformation
rationale:
  definition:
    why: The rolling-window edge cases are not yet part of an approved definition.
    evidence: Source fields and dates exist, but rehire and same-day events lack documented rules.
    recommended_action: Approve and version the edge-case rules before feature engineering.
  consistency:
    why: Longitudinal category normalization has not been validated.
    evidence: Coverage profiling checked nulls but not category stability over time.
    recommended_action: Profile normalized distinct counts and month-to-month stability.
  effort:
    why: The feature requires a rolling employee-date derivation.
    evidence: The source stores dated events rather than the requested trailing-window feature.
    recommended_action: Implement and test a leakage-safe rolling SQL transformation.
```

The canonical fields are `why`, `evidence`, and `recommended_action`.
Do not add 0/1 rationale for a qualitative score 2; add verification instead.
Coverage, missingness, and history rationale is generated automatically from
the configured thresholds, assessment windows, percentages, dates, and
leakage/systematic-missingness flags. Overrides with final score 0 or 1 require
`reason`, `evidence`, and `recommended_action`; their scoring method is
written as `Configured override`.

## Verification for qualitative score 2

Every qualitative score of 2 requires `method`, `evidence`, `result`,
`as_of_date`, `query_reference`, `acceptance_rule`, and `outcome`. Definition,
consistency, and join also require the numeric metric groups configured in
`scoring-rules.yaml`.

```yaml
verification:
  semantic_type: direct_field
  definition:
    method: authoritative_definition_and_data_audit
    evidence: What was checked against the source-owned definition.
    result: What the aggregate audit demonstrated.
    as_of_date: 2026-08-14
    query_reference: queries/audits/example_definition_audit.sql
    acceptance_rule: The explicit rule that the calculated metrics must satisfy.
    outcome: pass
    metrics:
      eligible_rows: 100
      populated_rows: 100
      distinct_values: 8
```

The SQL reference must be an existing project-relative file below
`queries/audits/` or `queries/profiles/`. `outcome: pass` means the stated
acceptance rule passed; data existence alone is insufficient. If a formula,
root, grouping, temporal rule, or join cannot be independently tested, use
score 1 with rationale.

### Precomputed compensation metric

For a stored compensation ratio, `definition: clear_stable` is valid only after
the formula is confirmed for the target employee field and population, not an
adjacent offers table. Required Definition metrics are
`comparable_count`, `matched_within_tolerance_count`, `mismatch_count`, and
`match_rate_percent`. The audit must also state numerator, midpoint,
currency, FTE, effective-date, rounding, tolerance, and acceptance rules.

If the employee source does not expose the components and no authoritative
lineage plus reconciliation is available, Definition cannot be 2.

### Organizational hierarchy

For `Layers from CEO`, reconstruct manager chains by snapshot and record
`eligible_count`, `reconstructed_count`, `unresolved_count`, `root_count`,
`cycle_count`, and `convergence_rate_percent`. Convergence on one person is
necessary but does not prove that person is the governed CEO root. Validate root
semantics independently and keep identities out of shared results.

If evaluating a stored "level from top" field, do not rename it as "Layers
from CEO" unless chain reconstruction and root semantics both pass.

## Derivation options

When no direct field exists, add `derivation_options` or `no_derivation_reason`. Each option must document fields/tables, formula, grain, temporal window, deduplication, null and edge-case handling, leakage controls, snapshot join, sensitivity, validations needed, estimated effort, and decision reason. Allowed statuses are `direct`, `proposed`, `testable`, `validated`, `blocked`, and `rejected`. `proposed` and `testable` cap Definition at 1; `blocked` and `rejected` cap Definition at 0; only `direct` or `validated` can leave Definition eligible for 2.

## Executable v4 validations

Use `scoring_validations` for criterion-level executable checks. Each validation declares `id`, `criterion`, saved SQL reference, acceptance rule, and either an explicit `max_score` or metric comparison (`metric`, `observed`, `operator`, `threshold`). The criterion score is the minimum maximum allowed by status evidence, calculated quantitative rules, derivation gate, executable validations, and score-reducing overrides. Overrides may only reduce scores.

