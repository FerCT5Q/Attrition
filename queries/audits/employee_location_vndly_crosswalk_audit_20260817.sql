-- Aggregate-only discovery of exact identifier/name overlaps between the two
-- employee location fields and VNDLY work-site codes/names. It returns only
-- counts, never location labels, codes, ZIPs, or employees.
--
-- Acceptance rule: an employee location field may serve as a direct crosswalk
-- only if every populated value maps to exactly one VNDLY code or name, with
-- governed temporal lineage. This query tests the exact-string prerequisite.

WITH employee_locations AS (
  SELECT
    'office_site' AS employee_location_field,
    UPPER(NULLIF(TRIM(CAST(office_site AS VARCHAR(256))), '')) AS location_value
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND office_site IS NOT NULL

  UNION ALL

  SELECT
    'office_location' AS employee_location_field,
    UPPER(NULLIF(TRIM(CAST(office_location AS VARCHAR(256))), '')) AS location_value
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND office_location IS NOT NULL
),
employee_values AS (
  SELECT DISTINCT
    employee_location_field,
    location_value
  FROM employee_locations
  WHERE location_value IS NOT NULL
),
vndly_names AS (
  SELECT
    UPPER(NULLIF(TRIM(CAST(tdw_wo_work_site_name AS VARCHAR(256))), '')) AS location_value,
    COUNT(DISTINCT NULLIF(TRIM(CAST(tdw_wo_work_site_code AS VARCHAR(256))), '')) AS code_count
  FROM hrda.vndly_assignment
  WHERE tdw_wo_work_site_name IS NOT NULL
  GROUP BY 1
),
vndly_codes AS (
  SELECT
    UPPER(NULLIF(TRIM(CAST(tdw_wo_work_site_code AS VARCHAR(256))), '')) AS location_value,
    COUNT(DISTINCT NULLIF(TRIM(CAST(tdw_wo_work_site_name AS VARCHAR(256))), '')) AS name_count
  FROM hrda.vndly_assignment
  WHERE tdw_wo_work_site_code IS NOT NULL
  GROUP BY 1
),
matches AS (
  SELECT
    e.employee_location_field,
    e.location_value,
    COALESCE(n.code_count, 0) AS matching_vndly_codes_by_name,
    COALESCE(c.name_count, 0) AS matching_vndly_names_by_code
  FROM employee_values e
  LEFT JOIN vndly_names n ON e.location_value = n.location_value
  LEFT JOIN vndly_codes c ON e.location_value = c.location_value
)
SELECT
  employee_location_field,
  COUNT(*) AS populated_distinct_employee_location_values,
  SUM(CASE WHEN matching_vndly_codes_by_name = 1 THEN 1 ELSE 0 END)
    AS values_matching_one_vndly_name,
  SUM(CASE WHEN matching_vndly_names_by_code = 1 THEN 1 ELSE 0 END)
    AS values_matching_one_vndly_code,
  SUM(CASE
    WHEN matching_vndly_codes_by_name = 0 AND matching_vndly_names_by_code = 0
    THEN 1 ELSE 0
  END) AS values_without_exact_vndly_match,
  SUM(CASE
    WHEN matching_vndly_codes_by_name > 1 OR matching_vndly_names_by_code > 1
    THEN 1 ELSE 0
  END) AS values_with_ambiguous_vndly_match
FROM matches
GROUP BY employee_location_field
ORDER BY employee_location_field;
