/* Familia y grupo registrados: mismo snapshot, sin reinterpretar el mapping.
   Regla: cero duplicados/contradicciones y cero mappings detalle-grupo
   ambiguos por foto. Los cambios de mapping históricos se reportan. */
WITH source AS (
  SELECT CAST(fis_mo_end_dt AS DATE) AS snapshot_date, employee_id,
         NULLIF(UPPER(TRIM(job_family)),'') AS family,
         NULLIF(UPPER(TRIM(job_family_group)),'') AS family_group
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE CAST(fis_mo_end_dt AS DATE) BETWEEN DATE '2020-07-26' AND DATE '2026-09-07'
    AND worker_type='Employee' AND employee_type='Regular' AND active_status=1
    AND is_rf360_yes_no=0 AND TRIM(eng_or_noneng)='Engineering' AND employee_id IS NOT NULL
),
keys AS (
  SELECT snapshot_date,employee_id,COUNT(*) AS n,
         COUNT(DISTINCT COALESCE(family,'<NULL>')) AS nf,
         COUNT(DISTINCT COALESCE(family_group,'<NULL>')) AS ng,
         MAX(family) AS family,MAX(family_group) AS family_group
  FROM source GROUP BY 1,2
),
mapping AS (
  SELECT snapshot_date,family,COUNT(DISTINCT family_group) AS ng,MIN(family_group) AS family_group
  FROM source WHERE family IS NOT NULL AND family_group IS NOT NULL GROUP BY 1,2
),
timeline AS (
  SELECT snapshot_date,family,family_group,
         LAG(family_group) OVER(PARTITION BY family ORDER BY snapshot_date) AS previous_group
  FROM mapping WHERE ng=1
),
annual AS (
  SELECT EXTRACT(year FROM snapshot_date)::INTEGER AS year,
         COUNT(*) AS person_snapshots,COUNT(DISTINCT employee_id) AS employee_count,
         COUNT(DISTINCT snapshot_date) AS snapshots,
         SUM(CASE WHEN n<>1 THEN 1 ELSE 0 END) AS duplicate_keys,
         SUM(CASE WHEN nf<>1 OR ng<>1 THEN 1 ELSE 0 END) AS contradictory_cells,
         SUM(CASE WHEN family IS NOT NULL THEN 1 ELSE 0 END) AS family_populated,
         SUM(CASE WHEN family_group IS NOT NULL THEN 1 ELSE 0 END) AS group_populated,
         SUM(CASE WHEN (family IS NULL AND family_group IS NOT NULL)
                       OR (family IS NOT NULL AND family_group IS NULL) THEN 1 ELSE 0 END) AS null_misalignment,
         COUNT(DISTINCT family) AS family_categories,COUNT(DISTINCT family_group) AS group_categories
  FROM keys GROUP BY 1
)
SELECT a.year,a.person_snapshots,a.employee_count,a.snapshots,a.duplicate_keys,
       a.contradictory_cells,a.family_populated,a.group_populated,a.null_misalignment,
       a.family_categories,a.group_categories,
       (SELECT COUNT(*) FROM mapping m WHERE EXTRACT(year FROM m.snapshot_date)=a.year AND m.ng>1) AS ambiguous_mappings,
       (SELECT COUNT(*) FROM timeline t WHERE EXTRACT(year FROM t.snapshot_date)=a.year
          AND t.previous_group IS NOT NULL AND t.previous_group<>t.family_group) AS mapping_changes
FROM annual a WHERE a.employee_count>=30 ORDER BY a.year;
