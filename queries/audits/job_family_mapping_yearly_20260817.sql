WITH base AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    fiscal_year,
    NULLIF(UPPER(TRIM(CAST(job_family AS VARCHAR(512)))), '') AS family_value,
    NULLIF(UPPER(TRIM(CAST(job_family_group AS VARCHAR(512)))), '') AS group_value
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt >= DATE '2020-07-26'
    AND fis_mo_end_dt <= DATE '2026-08-17'
),
family_snapshot_mapping AS (
  SELECT
    snapshot_date,
    MIN(fiscal_year) AS fiscal_year,
    family_value,
    COUNT(DISTINCT group_value) AS mapped_group_count,
    MIN(group_value) AS single_group_value
  FROM base
  WHERE family_value IS NOT NULL
    AND group_value IS NOT NULL
  GROUP BY snapshot_date, family_value
),
sequenced_family_mapping AS (
  SELECT
    snapshot_date,
    fiscal_year,
    family_value,
    single_group_value AS group_value,
    LAG(single_group_value) OVER (
      PARTITION BY family_value
      ORDER BY snapshot_date
    ) AS previous_group_value
  FROM family_snapshot_mapping
  WHERE mapped_group_count = 1
),
yearly_mapping AS (
  SELECT
    fiscal_year,
    COUNT(*) AS family_snapshot_mappings,
    SUM(CASE WHEN mapped_group_count > 1 THEN 1 ELSE 0 END)
      AS family_snapshot_mapping_conflicts
  FROM family_snapshot_mapping
  GROUP BY fiscal_year
),
yearly_changes AS (
  SELECT
    fiscal_year,
    COUNT(*) AS mapping_change_events,
    COUNT(DISTINCT family_value) AS families_with_mapping_changes
  FROM sequenced_family_mapping
  WHERE previous_group_value IS NOT NULL
    AND previous_group_value <> group_value
  GROUP BY fiscal_year
),
yearly_domain AS (
  SELECT
    fiscal_year,
    COUNT(*) AS eligible_rows,
    COUNT(DISTINCT snapshot_date) AS snapshots_checked,
    COUNT(DISTINCT family_value) AS distinct_families,
    COUNT(DISTINCT group_value) AS distinct_groups,
    SUM(CASE WHEN family_value IS NULL OR group_value IS NULL THEN 1 ELSE 0 END)
      AS incomplete_mapping_rows,
    SUM(CASE WHEN
      family_value IN ('UNKNOWN', 'OTHER', 'UNASSIGNED', 'NOT ASSIGNED', 'NOT APPLICABLE', 'N/A', 'NA', 'NONE')
      OR family_value LIKE '%UNKNOWN%'
      OR family_value LIKE 'OTHER%'
      OR family_value LIKE '%UNASSIGNED%'
      THEN 1 ELSE 0 END) AS special_family_label_rows,
    SUM(CASE WHEN
      group_value IN ('UNKNOWN', 'OTHER', 'UNASSIGNED', 'NOT ASSIGNED', 'NOT APPLICABLE', 'N/A', 'NA', 'NONE')
      OR group_value LIKE '%UNKNOWN%'
      OR group_value LIKE 'OTHER%'
      OR group_value LIKE '%UNASSIGNED%'
      THEN 1 ELSE 0 END) AS special_group_label_rows
  FROM base
  GROUP BY fiscal_year
)
SELECT
  yearly_domain.fiscal_year,
  yearly_domain.snapshots_checked,
  yearly_domain.eligible_rows,
  yearly_domain.distinct_families,
  yearly_domain.distinct_groups,
  yearly_domain.incomplete_mapping_rows,
  yearly_domain.special_family_label_rows,
  yearly_domain.special_group_label_rows,
  COALESCE(yearly_mapping.family_snapshot_mappings, 0) AS family_snapshot_mappings,
  COALESCE(yearly_mapping.family_snapshot_mapping_conflicts, 0)
    AS family_snapshot_mapping_conflicts,
  COALESCE(yearly_changes.mapping_change_events, 0) AS mapping_change_events,
  COALESCE(yearly_changes.families_with_mapping_changes, 0)
    AS families_with_mapping_changes
FROM yearly_domain
LEFT JOIN yearly_mapping
  ON yearly_mapping.fiscal_year = yearly_domain.fiscal_year
LEFT JOIN yearly_changes
  ON yearly_changes.fiscal_year = yearly_domain.fiscal_year
ORDER BY yearly_domain.fiscal_year;
