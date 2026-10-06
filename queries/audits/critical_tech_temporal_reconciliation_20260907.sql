/*
  Critical Tech temporal reconciliation.

  Claim:
    The archive provides enough effective-date information to assess whether
    historical Critical Tech membership can be reconstructed.

  Acceptance rule:
    The current mapping must be reconciled to the archive at the same family
    grain before historical membership is treated as time-valid. This query
    reports the archive state; it does not promote the current mapping to a
    historical definition by itself.
*/
SELECT
  COUNT(*) AS archive_rows,
  COUNT(DISTINCT tech) AS distinct_archive_tech_values,
  COUNT(DISTINCT current_indicator) AS current_indicator_values,
  MIN(effective_begin_date) AS minimum_effective_begin_date,
  MAX(effective_end_date) AS maximum_effective_end_date,
  SUM(
    CASE WHEN effective_begin_date IS NULL OR effective_end_date IS NULL
         THEN 1 ELSE 0 END
  ) AS missing_effective_dates,
  CASE
    WHEN COUNT(*) > 0
     AND SUM(
       CASE WHEN effective_begin_date IS NULL OR effective_end_date IS NULL
            THEN 1 ELSE 0 END
     ) = 0
    THEN 'review_reconciliation'
    ELSE 'pending'
  END AS outcome
FROM hrda.critical_tech_archive;
