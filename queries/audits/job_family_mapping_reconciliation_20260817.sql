WITH base AS (
  SELECT
    employee_id,
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    fiscal_year,
    NULLIF(UPPER(TRIM(CAST(job_family AS VARCHAR(512)))), '') AS family_value,
    NULLIF(UPPER(TRIM(CAST(job_family_short AS VARCHAR(512)))), '') AS family_short_value,
    NULLIF(UPPER(TRIM(CAST(job_family_group AS VARCHAR(512)))), '') AS group_value,
    NULLIF(UPPER(TRIM(CAST(job_family_group_short AS VARCHAR(512)))), '') AS group_short_value,
    CASE
      WHEN job_family IS NOT NULL
       AND CAST(job_family AS VARCHAR(512)) <> TRIM(CAST(job_family AS VARCHAR(512)))
      THEN 1 ELSE 0
    END AS family_whitespace_flag,
    CASE
      WHEN job_family_group IS NOT NULL
       AND CAST(job_family_group AS VARCHAR(512)) <> TRIM(CAST(job_family_group AS VARCHAR(512)))
      THEN 1 ELSE 0
    END AS group_whitespace_flag
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt >= DATE '2020-07-26'
    AND fis_mo_end_dt <= DATE '2026-08-17'
),
latest_snapshot AS (
  SELECT MAX(snapshot_date) AS latest_snapshot_date
  FROM base
),
key_level AS (
  SELECT
    employee_id,
    snapshot_date,
    COUNT(*) AS row_count,
    COUNT(DISTINCT family_value) AS family_count,
    COUNT(DISTINCT group_value) AS group_count,
    MAX(CASE WHEN family_value IS NOT NULL AND group_value IS NOT NULL THEN 1 ELSE 0 END)
      AS populated_pair_flag
  FROM base
  WHERE employee_id IS NOT NULL
    AND snapshot_date IS NOT NULL
  GROUP BY employee_id, snapshot_date
),
key_summary AS (
  SELECT
    COUNT(*) AS employee_snapshot_keys,
    SUM(populated_pair_flag) AS populated_employee_snapshot_keys,
    SUM(CASE WHEN populated_pair_flag = 0 THEN 1 ELSE 0 END) AS incomplete_employee_snapshot_keys,
    SUM(CASE WHEN row_count > 1 THEN 1 ELSE 0 END) AS duplicate_employee_snapshot_keys,
    SUM(CASE WHEN row_count > 1 THEN row_count - 1 ELSE 0 END) AS duplicate_extra_rows,
    SUM(CASE WHEN family_count > 1 OR group_count > 1 THEN 1 ELSE 0 END)
      AS conflicting_employee_snapshot_keys,
    MAX(row_count) AS maximum_rows_per_employee_snapshot
  FROM key_level
),
family_snapshot_mapping AS (
  SELECT
    snapshot_date,
    family_value,
    COUNT(DISTINCT group_value) AS mapped_group_count,
    MIN(group_value) AS single_group_value
  FROM base
  WHERE family_value IS NOT NULL
    AND group_value IS NOT NULL
  GROUP BY snapshot_date, family_value
),
same_snapshot_mapping_summary AS (
  SELECT
    SUM(CASE WHEN mapped_group_count > 1 THEN 1 ELSE 0 END)
      AS family_snapshot_mapping_conflicts,
    MAX(mapped_group_count) AS maximum_groups_per_family_snapshot
  FROM family_snapshot_mapping
),
family_history_mapping AS (
  SELECT
    family_value,
    COUNT(DISTINCT group_value) AS historical_group_count
  FROM base
  WHERE family_value IS NOT NULL
    AND group_value IS NOT NULL
  GROUP BY family_value
),
family_history_summary AS (
  SELECT
    SUM(CASE WHEN historical_group_count > 1 THEN 1 ELSE 0 END)
      AS families_with_multiple_historical_groups,
    MAX(historical_group_count) AS maximum_historical_groups_per_family
  FROM family_history_mapping
),
unambiguous_family_snapshot AS (
  SELECT
    snapshot_date,
    family_value,
    single_group_value AS group_value
  FROM family_snapshot_mapping
  WHERE mapped_group_count = 1
),
sequenced_family_mapping AS (
  SELECT
    snapshot_date,
    family_value,
    group_value,
    LAG(group_value) OVER (
      PARTITION BY family_value
      ORDER BY snapshot_date
    ) AS previous_group_value
  FROM unambiguous_family_snapshot
),
mapping_change_events AS (
  SELECT
    snapshot_date,
    family_value
  FROM sequenced_family_mapping
  WHERE previous_group_value IS NOT NULL
    AND previous_group_value <> group_value
),
mapping_change_summary AS (
  SELECT
    COUNT(*) AS mapping_change_events,
    COUNT(DISTINCT family_value) AS families_with_mapping_changes,
    MIN(snapshot_date) AS first_mapping_change_date,
    MAX(snapshot_date) AS latest_mapping_change_date
  FROM mapping_change_events
),
family_short_mapping AS (
  SELECT
    snapshot_date,
    family_value,
    COUNT(DISTINCT family_short_value) AS mapped_short_count
  FROM base
  WHERE family_value IS NOT NULL
    AND family_short_value IS NOT NULL
  GROUP BY snapshot_date, family_value
),
group_short_mapping AS (
  SELECT
    snapshot_date,
    group_value,
    COUNT(DISTINCT group_short_value) AS mapped_short_count
  FROM base
  WHERE group_value IS NOT NULL
    AND group_short_value IS NOT NULL
  GROUP BY snapshot_date, group_value
),
short_mapping_summary AS (
  SELECT
    (SELECT SUM(CASE WHEN mapped_short_count > 1 THEN 1 ELSE 0 END)
       FROM family_short_mapping) AS family_short_mapping_conflicts,
    (SELECT SUM(CASE WHEN mapped_short_count > 1 THEN 1 ELSE 0 END)
       FROM group_short_mapping) AS group_short_mapping_conflicts
),
family_lifespan AS (
  SELECT
    family_value,
    MIN(snapshot_date) AS first_seen_date,
    MAX(snapshot_date) AS latest_seen_date
  FROM base
  WHERE family_value IS NOT NULL
  GROUP BY family_value
),
group_lifespan AS (
  SELECT
    group_value,
    MIN(snapshot_date) AS first_seen_date,
    MAX(snapshot_date) AS latest_seen_date
  FROM base
  WHERE group_value IS NOT NULL
  GROUP BY group_value
),
lifespan_summary AS (
  SELECT
    (SELECT SUM(CASE
       WHEN family_lifespan.latest_seen_date < DATEADD(month, -12, latest_snapshot.latest_snapshot_date)
       THEN 1 ELSE 0 END)
     FROM family_lifespan
     CROSS JOIN latest_snapshot) AS retired_family_candidates,
    (SELECT SUM(CASE
       WHEN family_lifespan.first_seen_date >= DATEADD(month, -12, latest_snapshot.latest_snapshot_date)
       THEN 1 ELSE 0 END)
     FROM family_lifespan
     CROSS JOIN latest_snapshot) AS new_family_candidates_last_12_months,
    (SELECT SUM(CASE
       WHEN group_lifespan.latest_seen_date < DATEADD(month, -12, latest_snapshot.latest_snapshot_date)
       THEN 1 ELSE 0 END)
     FROM group_lifespan
     CROSS JOIN latest_snapshot) AS retired_group_candidates,
    (SELECT SUM(CASE
       WHEN group_lifespan.first_seen_date >= DATEADD(month, -12, latest_snapshot.latest_snapshot_date)
       THEN 1 ELSE 0 END)
     FROM group_lifespan
     CROSS JOIN latest_snapshot) AS new_group_candidates_last_12_months
),
overall AS (
  SELECT
    COUNT(*) AS eligible_rows,
    COUNT(DISTINCT snapshot_date) AS snapshots_checked,
    MIN(snapshot_date) AS first_snapshot_date,
    MAX(snapshot_date) AS latest_snapshot_date,
    COUNT(DISTINCT family_value) AS distinct_families,
    COUNT(DISTINCT group_value) AS distinct_groups,
    COUNT(DISTINCT family_short_value) AS distinct_family_short_values,
    COUNT(DISTINCT group_short_value) AS distinct_group_short_values,
    SUM(CASE WHEN employee_id IS NULL OR snapshot_date IS NULL THEN 1 ELSE 0 END)
      AS rows_with_null_join_key,
    SUM(CASE WHEN family_value IS NOT NULL AND group_value IS NULL THEN 1 ELSE 0 END)
      AS family_present_group_missing_rows,
    SUM(CASE WHEN family_value IS NULL AND group_value IS NOT NULL THEN 1 ELSE 0 END)
      AS group_present_family_missing_rows,
    SUM(CASE WHEN family_value IS NOT NULL AND family_short_value IS NULL THEN 1 ELSE 0 END)
      AS family_present_short_missing_rows,
    SUM(CASE WHEN family_value IS NULL AND family_short_value IS NOT NULL THEN 1 ELSE 0 END)
      AS family_short_present_family_missing_rows,
    SUM(CASE WHEN group_value IS NOT NULL AND group_short_value IS NULL THEN 1 ELSE 0 END)
      AS group_present_short_missing_rows,
    SUM(CASE WHEN group_value IS NULL AND group_short_value IS NOT NULL THEN 1 ELSE 0 END)
      AS group_short_present_group_missing_rows,
    SUM(family_whitespace_flag) + SUM(group_whitespace_flag) AS whitespace_rows,
    SUM(CASE WHEN
      family_value IN ('UNKNOWN', 'OTHER', 'UNASSIGNED', 'NOT ASSIGNED', 'NOT APPLICABLE', 'N/A', 'NA', 'NONE')
      OR family_value LIKE '%UNKNOWN%'
      OR family_value LIKE 'OTHER%'
      OR family_value LIKE '%UNASSIGNED%'
      THEN 1 ELSE 0 END) AS special_family_label_rows,
    COUNT(DISTINCT CASE WHEN
      family_value IN ('UNKNOWN', 'OTHER', 'UNASSIGNED', 'NOT ASSIGNED', 'NOT APPLICABLE', 'N/A', 'NA', 'NONE')
      OR family_value LIKE '%UNKNOWN%'
      OR family_value LIKE 'OTHER%'
      OR family_value LIKE '%UNASSIGNED%'
      THEN family_value END) AS special_family_label_values,
    SUM(CASE WHEN
      group_value IN ('UNKNOWN', 'OTHER', 'UNASSIGNED', 'NOT ASSIGNED', 'NOT APPLICABLE', 'N/A', 'NA', 'NONE')
      OR group_value LIKE '%UNKNOWN%'
      OR group_value LIKE 'OTHER%'
      OR group_value LIKE '%UNASSIGNED%'
      THEN 1 ELSE 0 END) AS special_group_label_rows,
    COUNT(DISTINCT CASE WHEN
      group_value IN ('UNKNOWN', 'OTHER', 'UNASSIGNED', 'NOT ASSIGNED', 'NOT APPLICABLE', 'N/A', 'NA', 'NONE')
      OR group_value LIKE '%UNKNOWN%'
      OR group_value LIKE 'OTHER%'
      OR group_value LIKE '%UNASSIGNED%'
      THEN group_value END) AS special_group_label_values
  FROM base
)
SELECT
  overall.first_snapshot_date,
  overall.latest_snapshot_date,
  overall.snapshots_checked,
  overall.eligible_rows,
  key_summary.employee_snapshot_keys,
  key_summary.populated_employee_snapshot_keys,
  key_summary.incomplete_employee_snapshot_keys,
  overall.distinct_families,
  overall.distinct_groups,
  overall.distinct_family_short_values,
  overall.distinct_group_short_values,
  overall.rows_with_null_join_key,
  key_summary.duplicate_employee_snapshot_keys,
  key_summary.duplicate_extra_rows,
  key_summary.conflicting_employee_snapshot_keys,
  key_summary.maximum_rows_per_employee_snapshot,
  overall.family_present_group_missing_rows,
  overall.group_present_family_missing_rows,
  overall.family_present_short_missing_rows,
  overall.family_short_present_family_missing_rows,
  overall.group_present_short_missing_rows,
  overall.group_short_present_group_missing_rows,
  same_snapshot_mapping_summary.family_snapshot_mapping_conflicts,
  same_snapshot_mapping_summary.maximum_groups_per_family_snapshot,
  family_history_summary.families_with_multiple_historical_groups,
  family_history_summary.maximum_historical_groups_per_family,
  mapping_change_summary.mapping_change_events,
  mapping_change_summary.families_with_mapping_changes,
  mapping_change_summary.first_mapping_change_date,
  mapping_change_summary.latest_mapping_change_date,
  short_mapping_summary.family_short_mapping_conflicts,
  short_mapping_summary.group_short_mapping_conflicts,
  overall.whitespace_rows,
  overall.special_family_label_rows,
  overall.special_family_label_values,
  overall.special_group_label_rows,
  overall.special_group_label_values,
  lifespan_summary.retired_family_candidates,
  lifespan_summary.new_family_candidates_last_12_months,
  lifespan_summary.retired_group_candidates,
  lifespan_summary.new_group_candidates_last_12_months
FROM overall
CROSS JOIN key_summary
CROSS JOIN same_snapshot_mapping_summary
CROSS JOIN family_history_summary
CROSS JOIN mapping_change_summary
CROSS JOIN short_mapping_summary
CROSS JOIN lifespan_summary;
