---
name: attrition-redshift-db
description: Safely inspect and query the HRDA Amazon Redshift database for the Attrition project. Use when Codex needs database schema discovery, read-only aggregate queries, attrition/termination analysis, cohort segmentation, feature availability checks, or validation of HR data assumptions from hrda tables. It supports internal aggregate analysis and stricter presentation-ready reporting without exposing employee-level data.
---

# Attrition Redshift DB

## Operating Rules

Use Redshift only for read-only discovery and aggregate analysis. Do not run DDL, DML, COPY, UNLOAD, grants, stored procedures, or writes.

Do not print or store employee-level rows. Prefer aggregate results with `COUNT(*)`, cohort rates, min/max dates, schema metadata, and segment summaries. Use a minimum cohort size of 30 for shared outputs unless the user explicitly requests a different privacy threshold.

Classify the deliverable before writing SQL or rendering results. Read
[`references/reporting-modes.md`](references/reporting-modes.md) for the
applicable mode.

- `presentation` is the default for slides, shareable reports, and ambiguous
  requests. Suppress or anonymize protected-category labels.
- `internal_analysis` applies only when the user explicitly describes the
  deliverable as internal or exploratory. It may show the real stored labels
  for protected *categorical* fields (for example `gender`) with aggregate
  counts and percentages, provided each displayed bucket meets the cohort
  minimum. Label the artifact as internal analysis.

In both modes, never expose identity fields, employee IDs, names, emails,
manager identities, addresses, birth dates, raw free text, or individual
records. Exact salary/base-pay values remain prohibited; use bands, percentiles
or aggregate statistics instead. If sensitive fields are needed for joins or
feature engineering, keep them internal to the query.

Do not infer a formula, grouping, hierarchy root, or business meaning from a
column name, dashboard caption, adjacent table, or prior assessment. Those are
hypotheses until a read-only aggregate calculation or authoritative lineage
reconciliation confirms the claim on the target field and population.

For attrition modeling, prefer cohort/segment outputs over employee-level risk scores. Treat individual predictions as restricted and require explicit governance/legal/privacy approval before producing them.

## Connection

The Attrition folder currently does not contain its own database client or `.env`. Reuse the Redshift credentials from the Slides project without copying them:

- Python interpreter: project `.venv\Scripts\python.exe` for new v4 runs, or `C:\Dev\Python\Slides\.venv\Scripts\python.exe` for legacy probes
- Env file: `C:\Dev\Python\Slides\.env` (reuse only; do not copy)
- Default schema: `hrda`
- Main table: `hrda.post_hire_monthly_worker_dtls`

Run scripts from this skill with the project virtualenv after installing `requirements.txt`:

```powershell
& .venv\Scripts\python.exe -B '.codex\skills\attrition-redshift-db\scripts\inspect_schema.py'
```

If a command fails because the sandbox blocks network or external log/file access, rerun it with approval. Keep queries read-only.

## Workflow

1. Read `references/schema.md` before writing project-specific queries.
2. If the question depends on current database structure, run `scripts/inspect_schema.py`.
3. Classify the claim as direct field, precomputed metric, derived feature, hierarchy, grouped mapping, or external source.
4. State the definition and acceptance rule before interpreting results.
5. Write SQL that returns aggregate results only. Avoid `SELECT *`. Save nontrivial evaluation SQL under `queries/audits/` or `queries/profiles/`.
6. Use `scripts/run_readonly_query.py --sql "<query>" --max-rows 100` for ad hoc checks. For an explicitly internal analysis that returns an allowed protected-category label, pass `--reporting-mode internal_analysis`; the SQL must include a distinct-employee aggregate and every displayed bucket must meet the cohort minimum.
7. Return the query path, execution date, population/date window, numeric metrics, result, and whether the acceptance rule passed.
8. Summarize results in Spanish unless the user asks otherwise. Include caveats about sample size, date window, null/blank values, and whether the query measures headcount-month rows or distinct employees.

## Support for sequential variable assessments

When this skill is composed with `evaluate-attrition-variable`, work
on one variable at a time. Begin with fresh variable-specific assumptions and
return aggregate evidence for that concept before exploring the next one.

- First identify whether the concept is direct, stored/precomputed, grouped,
  derived, hierarchical, survey-based, external, or unavailable.
- Explore synonyms, components, related fields, tables, dates, grain, history,
  and join keys before choosing SQL.
- Let the concept-specific acceptance rules determine the queries. Do not use a
  single generic profile as a substitute for formula, mapping, hierarchy,
  event, rolling-window, survey, or external-source validation.
- After execution, inspect the aggregate result for new ambiguities. Add a
  purpose-built read-only query when the result reveals an untested boundary,
  mismatch, temporal condition, or join risk.
- A prior variable may provide useful source context, but its result cannot
  prove the current claim. Revalidate the population, grain, date window, and
  rule.
- Finish and persist the current variable's SQL and aggregate metrics before
  moving to the next variable.

For a multi-variable run, allow one portfolio preflight before this sequential
loop. Preflight may query `information_schema` metadata for all requested
tables, columns, synonyms, and components, but must not query employee
aggregates, coverage, prevalence, or distributions. Persist the metadata SQL
and keep it separate from per-variable evidence. After preflight, return to the
one-variable-at-a-time loop in dependency order.

Every executed per-variable SQL, including the main Coverage SQL, must be saved
and represented in the assessment evidence ledger with SQL/result hashes. Do
not accept metrics or `outcome` copied from YAML as database evidence.

## Semantic reconciliation for score 2

For v4 derivation and executable scoring, keep every SQL artifact aggregate-only and saved under `queries/audits/` or `queries/profiles/`; proposed or testable derivations are hypotheses until an aggregate validation passes.


When this skill is used by `evaluate-attrition-variable`, follow the sibling
`../evaluate-attrition-variable/references/semantic-validation.md` contract:

- Precomputed metrics: independently calculate the exact target formula on the same eligible population and report comparable, matched-within-tolerance, mismatch, and match-rate counts. If the needed components are unavailable, say so; do not substitute evidence from another table.
- Derived features: implement the full time-safe rule, test boundaries and edge cases, and compare independent results.
- Hierarchies: traverse same-snapshot manager chains, count roots, cycles, unresolved chains, reconstruction coverage, and convergence; separately test that the root satisfies the governed business definition without exposing identity.
- Grouped categories: count one-to-many mapping contradictions, null misalignment, unmapped values, and mapping changes over time.
- Joins: report eligible, matched, unmatched, duplicate, and multi-match counts at the intended employee-date grain.

A schema check establishes availability, not semantic correctness.

## Query Patterns

Use temporal logic for attrition. Avoid random train/test assumptions when querying model data. For model validation, train on earlier fiscal months and test on later fiscal months.

Use the actual level columns. The table does not have `job_level`; use `job_level_primary_position`, `level_grouped`, `management_level`, or compensation grade fields depending on the question.

For attrition labels, start from `is_termed`, `term_date`, `term_type`, `term_reason`, `term_reasonall`, `active_status`, and fiscal month fields. Verify voluntary/involuntary definitions with aggregate distributions before labeling.

For segment outputs, prefer stable and actionable features:

- job family/group, level, management level
- tenure/time in role bands
- region/country/site only with enough cohort size
- worker/employee type
- promotion, transfer, manager change, location change history
- compa-ratio bands or percentile bands, not exact pay

## Resources

- `references/schema.md`: discovered HRDA table notes, useful columns, sensitive columns, and safe query examples.
- `scripts/inspect_schema.py`: read-only metadata/profile probe for the main table.
- `scripts/run_readonly_query.py`: guarded helper for read-only SQL with row limits.
