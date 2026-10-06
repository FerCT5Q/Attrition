# Semantic validation patterns

Use this reference before assigning a qualitative score of 2. The objective is
to prove what a field means and how it behaves, not merely that it exists.

## Universal gate

1. State the exact claim being tested.
2. Identify the authoritative definition or lineage.
3. Save the read-only aggregate SQL under `queries/audits/` or
   `queries/profiles/`.
4. State a numeric or invariant-based acceptance rule before interpreting the
   result.
5. Execute through the project's configured read-only database skill; in
   Attrition use `attrition-redshift-db`. Record the date and aggregate metrics.
6. Set `outcome: pass` only when the rule passes. Otherwise score 1 or 0 and
   explain what failed or remains unknown.

The executable engine, not the authored YAML, calculates metrics and outcome.
Every score-2 verification must carry frozen-result provenance with SHA-256
hashes for both SQL and result rows. Declared metrics/outcomes without that
provenance are ignored and cannot enable score 2.

Prior assessments, narrative documents, column names, Tableau captions, and
visual agreement are context only. They are not current proof.

The per-variable HTML must expose how this gate was applied. If a criterion is
1 or 0, the report must show the failed or pending rule, observed aggregate
evidence, and recommended action. If a criterion is 2, the report must show the
saved SQL, acceptance rule, passing outcome, and aggregate metrics. Related
columns used to explain a concept must be profiled and compared separately from
the scoring columns.

## Adaptive one-variable loop

Apply the semantic pattern to each variable's own evidence boundary while
retaining the shared problem and portfolio context. Before querying, translate
the concept into a variable-specific validation plan; after querying, compare
the observed aggregate metrics with that plan.

The first query is not automatically the final analysis. If it reveals an
unexpected domain, mismatch, hierarchy offset, mapping contradiction, event
boundary, missing wave, stale feed, duplicate join, or possible leakage path,
add a focused aggregate validation and rerun the current variable. Record the
new query, acceptance rule, metrics, and effect on the score in the notebook and
HTML.

Only finalize the variable when the sufficiency review explains every score and
all required notebook cells execute. Update its cumulative project document,
then begin the next variable with the shared problem context and accumulated
knowledge available. Prior results and documentation may identify related
columns, dependencies or source behavior, but they do not satisfy the current
variable's evidence gate.

## Direct field

Use `semantic_type: direct_field` only when the requested concept is the source
field itself.

- Confirm table, column, type, access, grain, date field, and eligible
  population.
- Reconcile eligible, populated, and distinct counts.
- Audit blanks, normalization, invalid values, and longitudinal category
  stability.
- Check employee-date uniqueness or the intended temporal join.

Definition metrics require eligible, populated, and distinct counts.
Consistency requires observations/months checked plus anomalies. Join requires
eligible, matched, unmatched, and duplicate or multi-match counts.

## Stored or precomputed metric

Use `semantic_type: precomputed_metric` for stored ratios, indexes, scores, or
groupings whose meaning depends on upstream logic.

- Obtain the actual formula or authoritative lineage, including denominator,
  eligibility, currency/unit, effective date, rounding, null, and edge rules.
- Independently recalculate on the same target population whenever components
  are available.
- Report comparable, within-tolerance, mismatch, and match-rate metrics.
- Investigate aggregate mismatch causes; do not discard them silently.

Testing a similar field in an adjacent table does not confirm the target field.
For example, an offers-table compensation ratio may support a hypothesis but
does not prove the employee-table `compa_ratio` formula.

If components are unavailable, Definition 2 requires authoritative lineage plus
an aggregate reconciliation supplied by the source owner. Otherwise cap
Definition at 1.

## Derived feature

Use `semantic_type: derived_feature` when the final variable does not exist as a
source field.

- Write the complete formula, time window, grain, eligibility, null behavior,
  deduplication, and leakage controls.
- Recalculate independently or compare two independent implementations.
- Test boundary dates and edge cases.
- Report comparable, matched, mismatch, and match-rate metrics.

Coverage of input columns does not prove the derived feature is correctly
defined.

## Hierarchy

Use `semantic_type: hierarchy` for manager chains, organizational roots, spans,
or layers.

- Reconstruct the chain within the same snapshot or effective-date frame.
- Report eligible, reconstructed, unresolved, root, cycle, and convergence
  metrics.
- Validate that the converged root satisfies the authoritative business role;
  one common root alone does not prove "CEO".
- Compare any stored level field with reconstructed edge depth and report exact
  matches and offsets.
- Define treatment of missing managers, self-links, matrix relationships,
  reorganizations, and maximum traversal depth.

Keep names and employee IDs internal. Shared evidence may report "one root and
the approved-root check passed" without exposing identity.

## Grouped categorical mapping

A stored grouping such as `level_grouped` is a `derived_feature` when its
definition depends on mapping a detailed field.

- Cross-tab detailed-to-group mappings internally and report only aggregate
  counts.
- Count detailed values mapping to more than one group in a snapshot and over
  time.
- Count null misalignment and new/unmapped categories.
- Validate effective-date or version rules for mapping changes.

Cardinality alone does not prove that the grouping is correct.

## External source

Use `semantic_type: external_source` only after access, owner, grain, history,
and approved join keys are confirmed. The configured warehouse cannot prove
semantics for an unavailable external feed. Without current aggregate evidence,
Source, Definition, Consistency, or Join should not receive 2.

