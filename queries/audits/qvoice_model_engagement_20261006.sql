-- SQLite read-only sobre agregados actuales del concepto, calculados en memoria.
-- El manifest enlaza Excel, SQL Redshift de join, hashes y fecha de ejecución.
SELECT survey_year, snapshot_date, workbooks_checked, header_ambiguities, missing_component_headers, unverified_availability_waves, unresolved_wording_waves, invalid_count, valid_count, missing_count, absent_count, status_reconciliation_difference, comparable_count, recalculated_match_count, mismatch_count, eligible_count, matched_count, unmatched_count, duplicate_count, multi_match_count, full_exceeds_primary_count, overlap_cohort_difference, primary_complete_count, full_complete_count, source_participants, primary_available_count, missing_key_rows, source_duplicate_count, alternative_headers_checked, alternate_comparable_count, alternate_disagreement_count, reconciliation_tests, reconciliation_mismatch_count
FROM qvoice_variable_audit
ORDER BY survey_year;
