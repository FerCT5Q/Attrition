-- Claim: hrda.requisitions y hrda.requisitions_vw contienen requisiciones
-- publicadas externamente, identificables por job_posted_externally, y al
-- menos una de ellas tiene un job_posting_title que contiene 'DevOps Engineer'.
-- Deliverable mode: presentation; aggregate-only.
-- Acceptance rule: cada fuente debe tener (a) >=1 título coincidente y
-- (b) >=1 coincidencia con job_posted_externally = 1. Los conteos <30 se
-- suprimen en la salida, aunque el resultado pass/fail se conserva.

WITH source_metrics AS (
  SELECT
    'hrda.requisitions' AS source_asset,
    COUNT(*) AS requisition_rows,
    SUM(CASE WHEN job_posting_title ILIKE '%DevOps Engineer%' THEN 1 ELSE 0 END) AS devops_title_matches,
    SUM(CASE
      WHEN job_posting_title ILIKE '%DevOps Engineer%'
       AND COALESCE(job_posted_externally, 0) = 1
      THEN 1 ELSE 0
    END) AS devops_external_matches,
    SUM(CASE WHEN COALESCE(job_posted_externally, 0) = 1 THEN 1 ELSE 0 END) AS external_posting_rows
  FROM hrda.requisitions

  UNION ALL

  SELECT
    'hrda.requisitions_vw' AS source_asset,
    COUNT(*) AS requisition_rows,
    SUM(CASE WHEN job_posting_title ILIKE '%DevOps Engineer%' THEN 1 ELSE 0 END) AS devops_title_matches,
    SUM(CASE
      WHEN job_posting_title ILIKE '%DevOps Engineer%'
       AND COALESCE(job_posted_externally, 0) = 1
      THEN 1 ELSE 0
    END) AS devops_external_matches,
    SUM(CASE WHEN COALESCE(job_posted_externally, 0) = 1 THEN 1 ELSE 0 END) AS external_posting_rows
  FROM hrda.requisitions_vw
),
external_flag_profile AS (
  SELECT
    job_posted_internally_externally,
    job_posted_externally,
    COUNT(*) AS requisition_rows
  FROM hrda.requisitions
  GROUP BY 1, 2
  HAVING COUNT(*) >= 30
)
SELECT
  'validation' AS result_type,
  source_asset AS source_or_external_label,
  CASE WHEN devops_title_matches > 0 THEN 'pass' ELSE 'fail' END AS title_contains_devops_engineer,
  CASE WHEN devops_external_matches > 0 THEN 'pass' ELSE 'fail' END AS external_devops_match,
  CASE WHEN external_posting_rows > 0 THEN 'pass' ELSE 'fail' END AS external_posting_present,
  CASE WHEN devops_title_matches >= 30 THEN devops_title_matches ELSE NULL END AS published_devops_match_count,
  CASE WHEN devops_external_matches >= 30 THEN devops_external_matches ELSE NULL END AS published_external_devops_match_count,
  CASE WHEN requisition_rows >= 30 THEN requisition_rows ELSE NULL END AS published_requisition_row_count
FROM source_metrics

UNION ALL

SELECT
  'external_flag_profile' AS result_type,
  COALESCE(job_posted_internally_externally, '(null)') AS source_or_external_label,
  CAST(NULL AS VARCHAR(8)) AS title_contains_devops_engineer,
  CAST(job_posted_externally AS VARCHAR(8)) AS external_devops_match,
  CAST(NULL AS VARCHAR(8)) AS external_posting_present,
  CAST(NULL AS BIGINT) AS published_devops_match_count,
  CAST(NULL AS BIGINT) AS published_external_devops_match_count,
  requisition_rows AS published_requisition_row_count
FROM external_flag_profile
ORDER BY result_type, source_or_external_label;
