# Attrition variable distributions

`attrition-43-variable-distributions-v2.html` through `v5.html` are retained as historical versions. The current presentation is `attrition-43-variable-distributions-v6.html`.

V6 preserves the reviewed aggregate data and chart payloads from V5. It applies the visual grammar approved from Julia's slides 7, 11, and 17: concise English copy, a Definition/Population strip, blue distribution bars, whole distribution percentages, integer counts, one-decimal attrition rates, and relative color pills. Specialized V5 charts remain structurally unchanged when there is no clear equivalent in the approved examples.

- Purpose: explain candidate-variable definitions, distributions, and available aggregate attrition evidence; not predict individual resignations or create employee scores or lists.
- Outcome: `term_type = 'VOLUNTARY'` with `term_date` in `(snapshot, snapshot + 6 months]`; Voluntary Exception, null or ambiguous types, and involuntary exits are excluded.
- History: 24 mature monthly snapshots from 2024-03-24 through 2026-02-22.
- Privacy: every published attrition rate requires at least 30 distinct employees, 30 employee-snapshot exposures, and 30 voluntary exits. No employee rows, IDs, names, emails, addresses, free text, or exact compensation are shown.
- Traceability: `json/attrition-43-variable-distributions-v6-manifest.json`; frozen aggregate evidence remains in `json/attrition-43-variable-distributions-v3.six-month-attrition-evidence-20260914.json`, with source SQL in `queries/profiles/attrition_v3_six_month_segment_rates_20260914.sql`.

V6 is classified as `presentation`: protected categories remain anonymized where required, and only aggregate results are displayed.
