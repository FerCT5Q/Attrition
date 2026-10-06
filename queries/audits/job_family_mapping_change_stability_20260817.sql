WITH base AS (
  SELECT
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    NULLIF(UPPER(TRIM(CAST(job_family AS VARCHAR(512)))), '') AS family_value,
    NULLIF(UPPER(TRIM(CAST(job_family_group AS VARCHAR(512)))), '') AS group_value,
    NULLIF(UPPER(TRIM(CAST(job_family_group_short AS VARCHAR(512)))), '') AS group_short_value,
    COUNT(*) AS population_rows
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt >= DATE '2020-07-26'
    AND fis_mo_end_dt <= DATE '2026-08-17'
  GROUP BY
    CAST(fis_mo_end_dt AS DATE),
    NULLIF(UPPER(TRIM(CAST(job_family AS VARCHAR(512)))), ''),
    NULLIF(UPPER(TRIM(CAST(job_family_group AS VARCHAR(512)))), ''),
    NULLIF(UPPER(TRIM(CAST(job_family_group_short AS VARCHAR(512)))), '')
),
family_snapshot AS (
  SELECT
    snapshot_date,
    family_value,
    MIN(group_value) AS group_value,
    SUM(population_rows) AS population_rows,
    COUNT(DISTINCT group_value) AS group_count
  FROM base
  WHERE family_value IS NOT NULL
    AND group_value IS NOT NULL
  GROUP BY snapshot_date, family_value
),
sequenced AS (
  SELECT
    snapshot_date,
    family_value,
    group_value,
    population_rows,
    LAG(snapshot_date) OVER (
      PARTITION BY family_value
      ORDER BY snapshot_date
    ) AS previous_snapshot_date,
    LAG(group_value) OVER (
      PARTITION BY family_value
      ORDER BY snapshot_date
    ) AS previous_group_value,
    LAG(population_rows) OVER (
      PARTITION BY family_value
      ORDER BY snapshot_date
    ) AS previous_population_rows
  FROM family_snapshot
  WHERE group_count = 1
),
changes AS (
  SELECT
    ROW_NUMBER() OVER (ORDER BY snapshot_date, family_value) AS change_event_id,
    snapshot_date AS change_date,
    previous_snapshot_date,
    family_value,
    previous_group_value,
    group_value AS new_group_value,
    previous_population_rows,
    population_rows AS new_population_rows
  FROM sequenced
  WHERE previous_group_value IS NOT NULL
    AND previous_group_value <> group_value
),
future_ranked AS (
  SELECT
    changes.change_event_id,
    family_snapshot.snapshot_date,
    family_snapshot.group_value,
    ROW_NUMBER() OVER (
      PARTITION BY changes.change_event_id
      ORDER BY family_snapshot.snapshot_date
    ) AS future_observation_number
  FROM changes
  JOIN family_snapshot
    ON family_snapshot.family_value = changes.family_value
   AND family_snapshot.snapshot_date > changes.change_date
   AND family_snapshot.group_count = 1
),
future_three AS (
  SELECT
    changes.change_event_id,
    COUNT(future_ranked.snapshot_date) AS following_observations_checked,
    SUM(CASE
      WHEN future_ranked.group_value = changes.new_group_value THEN 1 ELSE 0
    END) AS observations_retaining_new_group,
    SUM(CASE
      WHEN future_ranked.group_value = changes.previous_group_value THEN 1 ELSE 0
    END) AS observations_reverting_to_previous_group
  FROM changes
  LEFT JOIN future_ranked
    ON future_ranked.change_event_id = changes.change_event_id
   AND future_ranked.future_observation_number <= 3
  GROUP BY changes.change_event_id
),
change_summary AS (
  SELECT
    COUNT(*) AS mapping_change_events,
    SUM(CASE
      WHEN DATEDIFF(day, previous_snapshot_date, change_date) BETWEEN 20 AND 45
      THEN 1 ELSE 0 END) AS changes_on_expected_snapshot_cadence,
    SUM(CASE
      WHEN previous_population_rows >= 30 AND new_population_rows >= 30
      THEN 1 ELSE 0 END) AS changes_with_both_cohorts_at_least_30,
    MIN(change_date) AS first_mapping_change_date,
    MAX(change_date) AS latest_mapping_change_date
  FROM changes
),
future_summary AS (
  SELECT
    COUNT(*) AS change_events_evaluated,
    SUM(CASE WHEN following_observations_checked = 3 THEN 1 ELSE 0 END)
      AS changes_with_three_following_observations,
    SUM(CASE
      WHEN following_observations_checked = 3
       AND observations_retaining_new_group = 3
      THEN 1 ELSE 0 END) AS changes_stable_for_three_observations,
    SUM(CASE WHEN observations_reverting_to_previous_group > 0 THEN 1 ELSE 0 END)
      AS changes_reverting_within_three_observations
  FROM future_three
),
short_missing_summary AS (
  SELECT
    SUM(population_rows) AS group_short_missing_rows,
    COUNT(DISTINCT snapshot_date) AS snapshots_with_group_short_missing,
    COUNT(DISTINCT group_value) AS groups_with_group_short_missing,
    MIN(snapshot_date) AS first_group_short_missing_date,
    MAX(snapshot_date) AS latest_group_short_missing_date
  FROM base
  WHERE group_value IS NOT NULL
    AND group_short_value IS NULL
)
SELECT
  change_summary.mapping_change_events,
  change_summary.changes_on_expected_snapshot_cadence,
  change_summary.changes_with_both_cohorts_at_least_30,
  change_summary.first_mapping_change_date,
  change_summary.latest_mapping_change_date,
  future_summary.changes_with_three_following_observations,
  future_summary.changes_stable_for_three_observations,
  future_summary.changes_reverting_within_three_observations,
  short_missing_summary.group_short_missing_rows,
  short_missing_summary.snapshots_with_group_short_missing,
  short_missing_summary.groups_with_group_short_missing,
  short_missing_summary.first_group_short_missing_date,
  short_missing_summary.latest_group_short_missing_date
FROM change_summary
CROSS JOIN future_summary
CROSS JOIN short_missing_summary;
