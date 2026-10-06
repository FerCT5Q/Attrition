WITH base AS (
  SELECT
    fis_mo_end_dt::date AS snapshot_date,
    fiscal_year,
    employee_id,
    manager_employee_id,
    compensation_grade,
    compa_ratio
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
),
latest_snapshot AS (
  SELECT MAX(snapshot_date) AS snapshot_date
  FROM base
),
recent_snapshots AS (
  SELECT snapshot_date
  FROM (
    SELECT DISTINCT snapshot_date
    FROM base
    ORDER BY snapshot_date DESC
    LIMIT 3
  ) s
),
scoped_base AS (
  SELECT 'full_history' AS scope, b.*
  FROM base b
  UNION ALL
  SELECT 'recent_3_snapshots' AS scope, b.*
  FROM base b
  JOIN recent_snapshots r
    ON b.snapshot_date = r.snapshot_date
  UNION ALL
  SELECT 'latest_snapshot' AS scope, b.*
  FROM base b
  JOIN latest_snapshot l
    ON b.snapshot_date = l.snapshot_date
),
key_counts AS (
  SELECT
    scope,
    snapshot_date,
    employee_id,
    COUNT(*) AS row_count
  FROM scoped_base
  GROUP BY 1, 2, 3
),
key_agg AS (
  SELECT
    scope,
    SUM(CASE WHEN row_count > 1 THEN 1 ELSE 0 END) AS duplicate_key_count,
    SUM(CASE WHEN row_count > 1 THEN row_count - 1 ELSE 0 END) AS duplicate_extra_rows
  FROM key_counts
  GROUP BY 1
),
component_summary AS (
  SELECT
    scope,
    COUNT(*) AS eligible_rows,
    COUNT(DISTINCT snapshot_date) AS snapshot_count,
    SUM(CASE WHEN manager_employee_id IS NULL THEN 1 ELSE 0 END) AS null_manager_rows,
    SUM(CASE WHEN compensation_grade IS NULL THEN 1 ELSE 0 END) AS null_grade_rows,
    SUM(CASE WHEN compa_ratio IS NULL THEN 1 ELSE 0 END) AS null_compa_rows,
    SUM(CASE WHEN compa_ratio IS NOT NULL AND compa_ratio <= 0 THEN 1 ELSE 0 END) AS nonpositive_compa_rows,
    SUM(CASE WHEN compa_ratio > 3 THEN 1 ELSE 0 END) AS high_outlier_compa_rows,
    SUM(CASE WHEN compa_ratio IS NOT NULL AND compa_ratio > 0 AND compa_ratio <= 3 THEN 1 ELSE 0 END) AS valid_compa_rows,
    SUM(CASE
          WHEN manager_employee_id IS NOT NULL
           AND compensation_grade IS NOT NULL
           AND compa_ratio IS NOT NULL
           AND compa_ratio > 0
           AND compa_ratio <= 3
          THEN 1 ELSE 0
        END) AS complete_component_rows
  FROM scoped_base
  GROUP BY 1
),
complete_rows AS (
  SELECT
    scope,
    snapshot_date,
    employee_id,
    manager_employee_id,
    compensation_grade,
    compa_ratio
  FROM scoped_base
  WHERE manager_employee_id IS NOT NULL
    AND compensation_grade IS NOT NULL
    AND compa_ratio IS NOT NULL
    AND compa_ratio > 0
    AND compa_ratio <= 3
),
with_cell_sizes AS (
  SELECT
    scope,
    snapshot_date,
    employee_id,
    manager_employee_id,
    compensation_grade,
    compa_ratio,
    COUNT(*) OVER (
      PARTITION BY scope, snapshot_date, manager_employee_id
    ) AS team_n,
    COUNT(*) OVER (
      PARTITION BY scope, snapshot_date, manager_employee_id, compensation_grade
    ) AS team_grade_n
  FROM complete_rows
),
eligibility_summary AS (
  SELECT
    scope,
    SUM(CASE WHEN team_n >= 30 THEN 1 ELSE 0 END) AS team_rows_ge30,
    SUM(CASE WHEN team_grade_n >= 30 THEN 1 ELSE 0 END) AS team_grade_rows_ge30
  FROM with_cell_sizes
  GROUP BY 1
),
team_cells AS (
  SELECT
    scope,
    snapshot_date,
    manager_employee_id,
    COUNT(*) AS cell_n
  FROM complete_rows
  GROUP BY 1, 2, 3
),
team_cell_summary AS (
  SELECT
    scope,
    COUNT(*) AS team_cells,
    SUM(CASE WHEN cell_n >= 30 THEN 1 ELSE 0 END) AS team_cells_ge30
  FROM team_cells
  GROUP BY 1
),
team_grade_cells AS (
  SELECT
    scope,
    snapshot_date,
    manager_employee_id,
    compensation_grade,
    COUNT(*) AS cell_n
  FROM complete_rows
  GROUP BY 1, 2, 3, 4
),
team_grade_cell_summary AS (
  SELECT
    scope,
    COUNT(*) AS team_grade_cells,
    SUM(CASE WHEN cell_n >= 30 THEN 1 ELSE 0 END) AS team_grade_cells_ge30
  FROM team_grade_cells
  GROUP BY 1
),
team_cell_distribution AS (
  SELECT
    scope,
    CASE
      WHEN cell_n >= 30 THEN '30+'
      WHEN cell_n >= 10 THEN '10-29'
      WHEN cell_n >= 5 THEN '05-09'
      ELSE '01-04'
    END AS size_band,
    COUNT(*) AS cell_count,
    SUM(cell_n) AS employee_rows
  FROM team_cells
  WHERE scope IN ('recent_3_snapshots', 'latest_snapshot')
  GROUP BY 1, 2
),
team_grade_cell_distribution AS (
  SELECT
    scope,
    CASE
      WHEN cell_n >= 30 THEN '30+'
      WHEN cell_n >= 10 THEN '10-29'
      WHEN cell_n >= 5 THEN '05-09'
      ELSE '01-04'
    END AS size_band,
    COUNT(*) AS cell_count,
    SUM(cell_n) AS employee_rows
  FROM team_grade_cells
  WHERE scope IN ('recent_3_snapshots', 'latest_snapshot')
  GROUP BY 1, 2
),
team_ranked_raw AS (
  SELECT
    scope,
    PERCENT_RANK() OVER (
      PARTITION BY scope, snapshot_date, manager_employee_id
      ORDER BY compa_ratio
    ) AS pct_rank
  FROM with_cell_sizes
  WHERE scope IN ('recent_3_snapshots', 'latest_snapshot')
    AND team_n >= 30
),
team_ranked AS (
  SELECT
    scope,
    CASE
      WHEN pct_rank <= 0.10 THEN '01_bottom_10'
      WHEN pct_rank <= 0.25 THEN '02_p10_to_p25'
      WHEN pct_rank < 0.75 THEN '03_middle_50'
      WHEN pct_rank < 0.90 THEN '04_p75_to_p90'
      ELSE '05_top_10'
    END AS percentile_band,
    COUNT(*) AS band_employee_rows
  FROM team_ranked_raw
  GROUP BY 1, 2
),
team_grade_ranked_raw AS (
  SELECT
    scope,
    PERCENT_RANK() OVER (
      PARTITION BY scope, snapshot_date, manager_employee_id, compensation_grade
      ORDER BY compa_ratio
    ) AS pct_rank
  FROM with_cell_sizes
  WHERE scope IN ('recent_3_snapshots', 'latest_snapshot')
    AND team_grade_n >= 30
),
team_grade_ranked AS (
  SELECT
    scope,
    CASE
      WHEN pct_rank <= 0.10 THEN '01_bottom_10'
      WHEN pct_rank <= 0.25 THEN '02_p10_to_p25'
      WHEN pct_rank < 0.75 THEN '03_middle_50'
      WHEN pct_rank < 0.90 THEN '04_p75_to_p90'
      ELSE '05_top_10'
    END AS percentile_band,
    COUNT(*) AS band_employee_rows
  FROM team_grade_ranked_raw
  GROUP BY 1, 2
),
ranked_totals AS (
  SELECT
    'team_percentile_band' AS section,
    scope,
    SUM(band_employee_rows) AS ranked_rows
  FROM team_ranked
  GROUP BY 1, 2
  UNION ALL
  SELECT
    'team_grade_percentile_band' AS section,
    scope,
    SUM(band_employee_rows) AS ranked_rows
  FROM team_grade_ranked
  GROUP BY 1, 2
)
SELECT
  'summary' AS section,
  cs.scope,
  'all' AS band,
  cs.eligible_rows,
  cs.complete_component_rows,
  cs.valid_compa_rows,
  cs.null_manager_rows,
  cs.null_grade_rows,
  (cs.null_compa_rows + cs.nonpositive_compa_rows + cs.high_outlier_compa_rows) AS invalid_compa_rows,
  COALESCE(ka.duplicate_key_count, 0) AS duplicate_key_count,
  COALESCE(ka.duplicate_extra_rows, 0) AS duplicate_extra_rows,
  COALESCE(tcs.team_cells, 0) AS team_cells,
  COALESCE(tcs.team_cells_ge30, 0) AS team_cells_ge30,
  COALESCE(es.team_rows_ge30, 0) AS team_rows_ge30,
  COALESCE(tgcs.team_grade_cells, 0) AS team_grade_cells,
  COALESCE(tgcs.team_grade_cells_ge30, 0) AS team_grade_cells_ge30,
  COALESCE(es.team_grade_rows_ge30, 0) AS team_grade_rows_ge30,
  NULL::BIGINT AS cell_count,
  NULL::BIGINT AS band_employee_rows,
  ROUND(100.0 * cs.complete_component_rows / NULLIF(cs.eligible_rows, 0), 4) AS pct_complete_components,
  ROUND(100.0 * COALESCE(es.team_rows_ge30, 0) / NULLIF(cs.complete_component_rows, 0), 4) AS pct_team_rows_ge30,
  ROUND(100.0 * COALESCE(es.team_grade_rows_ge30, 0) / NULLIF(cs.complete_component_rows, 0), 4) AS pct_team_grade_rows_ge30,
  NULL::DECIMAL(18,4) AS pct_of_ranked_rows
FROM component_summary cs
LEFT JOIN key_agg ka
  ON cs.scope = ka.scope
LEFT JOIN eligibility_summary es
  ON cs.scope = es.scope
LEFT JOIN team_cell_summary tcs
  ON cs.scope = tcs.scope
LEFT JOIN team_grade_cell_summary tgcs
  ON cs.scope = tgcs.scope
UNION ALL
SELECT
  'team_cell_size_distribution' AS section,
  scope,
  size_band AS band,
  NULL::BIGINT AS eligible_rows,
  NULL::BIGINT AS complete_component_rows,
  NULL::BIGINT AS valid_compa_rows,
  NULL::BIGINT AS null_manager_rows,
  NULL::BIGINT AS null_grade_rows,
  NULL::BIGINT AS invalid_compa_rows,
  NULL::BIGINT AS duplicate_key_count,
  NULL::BIGINT AS duplicate_extra_rows,
  NULL::BIGINT AS team_cells,
  NULL::BIGINT AS team_cells_ge30,
  NULL::BIGINT AS team_rows_ge30,
  NULL::BIGINT AS team_grade_cells,
  NULL::BIGINT AS team_grade_cells_ge30,
  NULL::BIGINT AS team_grade_rows_ge30,
  cell_count,
  employee_rows AS band_employee_rows,
  NULL::DECIMAL(18,4) AS pct_complete_components,
  NULL::DECIMAL(18,4) AS pct_team_rows_ge30,
  NULL::DECIMAL(18,4) AS pct_team_grade_rows_ge30,
  NULL::DECIMAL(18,4) AS pct_of_ranked_rows
FROM team_cell_distribution
UNION ALL
SELECT
  'team_grade_cell_size_distribution' AS section,
  scope,
  size_band AS band,
  NULL::BIGINT AS eligible_rows,
  NULL::BIGINT AS complete_component_rows,
  NULL::BIGINT AS valid_compa_rows,
  NULL::BIGINT AS null_manager_rows,
  NULL::BIGINT AS null_grade_rows,
  NULL::BIGINT AS invalid_compa_rows,
  NULL::BIGINT AS duplicate_key_count,
  NULL::BIGINT AS duplicate_extra_rows,
  NULL::BIGINT AS team_cells,
  NULL::BIGINT AS team_cells_ge30,
  NULL::BIGINT AS team_rows_ge30,
  NULL::BIGINT AS team_grade_cells,
  NULL::BIGINT AS team_grade_cells_ge30,
  NULL::BIGINT AS team_grade_rows_ge30,
  cell_count,
  employee_rows AS band_employee_rows,
  NULL::DECIMAL(18,4) AS pct_complete_components,
  NULL::DECIMAL(18,4) AS pct_team_rows_ge30,
  NULL::DECIMAL(18,4) AS pct_team_grade_rows_ge30,
  NULL::DECIMAL(18,4) AS pct_of_ranked_rows
FROM team_grade_cell_distribution
UNION ALL
SELECT
  'team_percentile_band' AS section,
  tr.scope,
  tr.percentile_band AS band,
  NULL::BIGINT AS eligible_rows,
  NULL::BIGINT AS complete_component_rows,
  NULL::BIGINT AS valid_compa_rows,
  NULL::BIGINT AS null_manager_rows,
  NULL::BIGINT AS null_grade_rows,
  NULL::BIGINT AS invalid_compa_rows,
  NULL::BIGINT AS duplicate_key_count,
  NULL::BIGINT AS duplicate_extra_rows,
  NULL::BIGINT AS team_cells,
  NULL::BIGINT AS team_cells_ge30,
  NULL::BIGINT AS team_rows_ge30,
  NULL::BIGINT AS team_grade_cells,
  NULL::BIGINT AS team_grade_cells_ge30,
  NULL::BIGINT AS team_grade_rows_ge30,
  NULL::BIGINT AS cell_count,
  tr.band_employee_rows,
  NULL::DECIMAL(18,4) AS pct_complete_components,
  NULL::DECIMAL(18,4) AS pct_team_rows_ge30,
  NULL::DECIMAL(18,4) AS pct_team_grade_rows_ge30,
  ROUND(100.0 * tr.band_employee_rows / NULLIF(rt.ranked_rows, 0), 4) AS pct_of_ranked_rows
FROM team_ranked tr
JOIN ranked_totals rt
  ON tr.scope = rt.scope
 AND rt.section = 'team_percentile_band'
UNION ALL
SELECT
  'team_grade_percentile_band' AS section,
  tgr.scope,
  tgr.percentile_band AS band,
  NULL::BIGINT AS eligible_rows,
  NULL::BIGINT AS complete_component_rows,
  NULL::BIGINT AS valid_compa_rows,
  NULL::BIGINT AS null_manager_rows,
  NULL::BIGINT AS null_grade_rows,
  NULL::BIGINT AS invalid_compa_rows,
  NULL::BIGINT AS duplicate_key_count,
  NULL::BIGINT AS duplicate_extra_rows,
  NULL::BIGINT AS team_cells,
  NULL::BIGINT AS team_cells_ge30,
  NULL::BIGINT AS team_rows_ge30,
  NULL::BIGINT AS team_grade_cells,
  NULL::BIGINT AS team_grade_cells_ge30,
  NULL::BIGINT AS team_grade_rows_ge30,
  NULL::BIGINT AS cell_count,
  tgr.band_employee_rows,
  NULL::DECIMAL(18,4) AS pct_complete_components,
  NULL::DECIMAL(18,4) AS pct_team_rows_ge30,
  NULL::DECIMAL(18,4) AS pct_team_grade_rows_ge30,
  ROUND(100.0 * tgr.band_employee_rows / NULLIF(rt.ranked_rows, 0), 4) AS pct_of_ranked_rows
FROM team_grade_ranked tgr
JOIN ranked_totals rt
  ON tgr.scope = rt.scope
 AND rt.section = 'team_grade_percentile_band'
ORDER BY 1, 2, 3
