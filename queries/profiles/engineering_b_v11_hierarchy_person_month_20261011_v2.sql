/* Misma foto; hasta 25 enlaces. Sin SQL recursivo ni caminos exportados. */
WITH nodes AS (
 SELECT fis_mo_end_dt::DATE AS snapshot_date,employee_id,
 MAX(manager_employee_id::BIGINT) AS manager_id,
 MAX(worker_supervisory_organization_level_from_top) AS stored_level,
 MAX(CASE WHEN worker_type='Employee' AND employee_type='Regular' AND is_rf360_yes_no=0 AND TRIM(eng_or_noneng)='Engineering' THEN 1 ELSE 0 END) AS eligible,
 COUNT(*) AS source_rows,
 COUNT(DISTINCT COALESCE(manager_employee_id::VARCHAR,'<NULL>')) AS manager_variants,
 COUNT(DISTINCT COALESCE(worker_supervisory_organization_level_from_top::VARCHAR,'<NULL>')) AS level_variants
 FROM hrda.post_hire_monthly_worker_dtls
 WHERE fis_mo_end_dt::DATE BETWEEN DATE '__PERIOD_START__' AND DATE '__PERIOD_END__'
 AND active_status=1 AND employee_id IS NOT NULL GROUP BY 1,2
), walked AS (
 SELECT n0.snapshot_date,n0.employee_id,n0.manager_id,n0.stored_level,n0.eligible,
 n0.source_rows,n0.manager_variants,n0.level_variants,
 CASE
 WHEN n0.employee_id IS NOT NULL AND n0.manager_id IS NULL THEN 0
 WHEN n1.employee_id IS NOT NULL AND n1.manager_id IS NULL THEN 1
 WHEN n2.employee_id IS NOT NULL AND n2.manager_id IS NULL THEN 2
 WHEN n3.employee_id IS NOT NULL AND n3.manager_id IS NULL THEN 3
 WHEN n4.employee_id IS NOT NULL AND n4.manager_id IS NULL THEN 4
 WHEN n5.employee_id IS NOT NULL AND n5.manager_id IS NULL THEN 5
 WHEN n6.employee_id IS NOT NULL AND n6.manager_id IS NULL THEN 6
 WHEN n7.employee_id IS NOT NULL AND n7.manager_id IS NULL THEN 7
 WHEN n8.employee_id IS NOT NULL AND n8.manager_id IS NULL THEN 8
 WHEN n9.employee_id IS NOT NULL AND n9.manager_id IS NULL THEN 9
 WHEN n10.employee_id IS NOT NULL AND n10.manager_id IS NULL THEN 10
 WHEN n11.employee_id IS NOT NULL AND n11.manager_id IS NULL THEN 11
 WHEN n12.employee_id IS NOT NULL AND n12.manager_id IS NULL THEN 12
 WHEN n13.employee_id IS NOT NULL AND n13.manager_id IS NULL THEN 13
 WHEN n14.employee_id IS NOT NULL AND n14.manager_id IS NULL THEN 14
 WHEN n15.employee_id IS NOT NULL AND n15.manager_id IS NULL THEN 15
 WHEN n16.employee_id IS NOT NULL AND n16.manager_id IS NULL THEN 16
 WHEN n17.employee_id IS NOT NULL AND n17.manager_id IS NULL THEN 17
 WHEN n18.employee_id IS NOT NULL AND n18.manager_id IS NULL THEN 18
 WHEN n19.employee_id IS NOT NULL AND n19.manager_id IS NULL THEN 19
 WHEN n20.employee_id IS NOT NULL AND n20.manager_id IS NULL THEN 20
 WHEN n21.employee_id IS NOT NULL AND n21.manager_id IS NULL THEN 21
 WHEN n22.employee_id IS NOT NULL AND n22.manager_id IS NULL THEN 22
 WHEN n23.employee_id IS NOT NULL AND n23.manager_id IS NULL THEN 23
 WHEN n24.employee_id IS NOT NULL AND n24.manager_id IS NULL THEN 24
 WHEN n25.employee_id IS NOT NULL AND n25.manager_id IS NULL THEN 25
 END AS depth,
 CASE
 WHEN n0.employee_id IS NOT NULL AND n0.manager_id IS NULL THEN n0.employee_id
 WHEN n1.employee_id IS NOT NULL AND n1.manager_id IS NULL THEN n1.employee_id
 WHEN n2.employee_id IS NOT NULL AND n2.manager_id IS NULL THEN n2.employee_id
 WHEN n3.employee_id IS NOT NULL AND n3.manager_id IS NULL THEN n3.employee_id
 WHEN n4.employee_id IS NOT NULL AND n4.manager_id IS NULL THEN n4.employee_id
 WHEN n5.employee_id IS NOT NULL AND n5.manager_id IS NULL THEN n5.employee_id
 WHEN n6.employee_id IS NOT NULL AND n6.manager_id IS NULL THEN n6.employee_id
 WHEN n7.employee_id IS NOT NULL AND n7.manager_id IS NULL THEN n7.employee_id
 WHEN n8.employee_id IS NOT NULL AND n8.manager_id IS NULL THEN n8.employee_id
 WHEN n9.employee_id IS NOT NULL AND n9.manager_id IS NULL THEN n9.employee_id
 WHEN n10.employee_id IS NOT NULL AND n10.manager_id IS NULL THEN n10.employee_id
 WHEN n11.employee_id IS NOT NULL AND n11.manager_id IS NULL THEN n11.employee_id
 WHEN n12.employee_id IS NOT NULL AND n12.manager_id IS NULL THEN n12.employee_id
 WHEN n13.employee_id IS NOT NULL AND n13.manager_id IS NULL THEN n13.employee_id
 WHEN n14.employee_id IS NOT NULL AND n14.manager_id IS NULL THEN n14.employee_id
 WHEN n15.employee_id IS NOT NULL AND n15.manager_id IS NULL THEN n15.employee_id
 WHEN n16.employee_id IS NOT NULL AND n16.manager_id IS NULL THEN n16.employee_id
 WHEN n17.employee_id IS NOT NULL AND n17.manager_id IS NULL THEN n17.employee_id
 WHEN n18.employee_id IS NOT NULL AND n18.manager_id IS NULL THEN n18.employee_id
 WHEN n19.employee_id IS NOT NULL AND n19.manager_id IS NULL THEN n19.employee_id
 WHEN n20.employee_id IS NOT NULL AND n20.manager_id IS NULL THEN n20.employee_id
 WHEN n21.employee_id IS NOT NULL AND n21.manager_id IS NULL THEN n21.employee_id
 WHEN n22.employee_id IS NOT NULL AND n22.manager_id IS NULL THEN n22.employee_id
 WHEN n23.employee_id IS NOT NULL AND n23.manager_id IS NULL THEN n23.employee_id
 WHEN n24.employee_id IS NOT NULL AND n24.manager_id IS NULL THEN n24.employee_id
 WHEN n25.employee_id IS NOT NULL AND n25.manager_id IS NULL THEN n25.employee_id
 END AS ancestor,
 CASE WHEN n0.manager_id IN (n0.employee_id) OR n1.manager_id IN (n0.employee_id,n1.employee_id) OR n2.manager_id IN (n0.employee_id,n1.employee_id,n2.employee_id) OR n3.manager_id IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id) OR n4.manager_id IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id) OR n5.manager_id IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id) OR n6.manager_id IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id) OR n7.manager_id IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id) OR n8.manager_id IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id) OR n9.manager_id IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id) OR n10.manager_id IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id) OR n11.manager_id IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id) OR n12.manager_id IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id) OR n13.manager_id IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id) OR n14.manager_id IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id,n14.employee_id) OR n15.manager_id IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id,n14.employee_id,n15.employee_id) OR n16.manager_id IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id,n14.employee_id,n15.employee_id,n16.employee_id) OR n17.manager_id IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id,n14.employee_id,n15.employee_id,n16.employee_id,n17.employee_id) OR n18.manager_id IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id,n14.employee_id,n15.employee_id,n16.employee_id,n17.employee_id,n18.employee_id) OR n19.manager_id IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id,n14.employee_id,n15.employee_id,n16.employee_id,n17.employee_id,n18.employee_id,n19.employee_id) OR n20.manager_id IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id,n14.employee_id,n15.employee_id,n16.employee_id,n17.employee_id,n18.employee_id,n19.employee_id,n20.employee_id) OR n21.manager_id IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id,n14.employee_id,n15.employee_id,n16.employee_id,n17.employee_id,n18.employee_id,n19.employee_id,n20.employee_id,n21.employee_id) OR n22.manager_id IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id,n14.employee_id,n15.employee_id,n16.employee_id,n17.employee_id,n18.employee_id,n19.employee_id,n20.employee_id,n21.employee_id,n22.employee_id) OR n23.manager_id IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id,n14.employee_id,n15.employee_id,n16.employee_id,n17.employee_id,n18.employee_id,n19.employee_id,n20.employee_id,n21.employee_id,n22.employee_id,n23.employee_id) OR n24.manager_id IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id,n14.employee_id,n15.employee_id,n16.employee_id,n17.employee_id,n18.employee_id,n19.employee_id,n20.employee_id,n21.employee_id,n22.employee_id,n23.employee_id,n24.employee_id) OR n25.manager_id IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id,n14.employee_id,n15.employee_id,n16.employee_id,n17.employee_id,n18.employee_id,n19.employee_id,n20.employee_id,n21.employee_id,n22.employee_id,n23.employee_id,n24.employee_id,n25.employee_id) THEN 1 ELSE 0 END AS cycle,
 CASE WHEN n25.manager_id IS NOT NULL THEN 1 ELSE 0 END AS depth_cap,
 CASE WHEN (n0.source_rows<>1 OR n0.manager_variants<>1) OR (n1.source_rows<>1 OR n1.manager_variants<>1) OR (n2.source_rows<>1 OR n2.manager_variants<>1) OR (n3.source_rows<>1 OR n3.manager_variants<>1) OR (n4.source_rows<>1 OR n4.manager_variants<>1) OR (n5.source_rows<>1 OR n5.manager_variants<>1) OR (n6.source_rows<>1 OR n6.manager_variants<>1) OR (n7.source_rows<>1 OR n7.manager_variants<>1) OR (n8.source_rows<>1 OR n8.manager_variants<>1) OR (n9.source_rows<>1 OR n9.manager_variants<>1) OR (n10.source_rows<>1 OR n10.manager_variants<>1) OR (n11.source_rows<>1 OR n11.manager_variants<>1) OR (n12.source_rows<>1 OR n12.manager_variants<>1) OR (n13.source_rows<>1 OR n13.manager_variants<>1) OR (n14.source_rows<>1 OR n14.manager_variants<>1) OR (n15.source_rows<>1 OR n15.manager_variants<>1) OR (n16.source_rows<>1 OR n16.manager_variants<>1) OR (n17.source_rows<>1 OR n17.manager_variants<>1) OR (n18.source_rows<>1 OR n18.manager_variants<>1) OR (n19.source_rows<>1 OR n19.manager_variants<>1) OR (n20.source_rows<>1 OR n20.manager_variants<>1) OR (n21.source_rows<>1 OR n21.manager_variants<>1) OR (n22.source_rows<>1 OR n22.manager_variants<>1) OR (n23.source_rows<>1 OR n23.manager_variants<>1) OR (n24.source_rows<>1 OR n24.manager_variants<>1) OR (n25.source_rows<>1 OR n25.manager_variants<>1) THEN 1 ELSE 0 END AS ambiguous_chain
 FROM nodes n0
 LEFT JOIN nodes n1 ON n1.snapshot_date=n0.snapshot_date AND n1.employee_id=n0.manager_id AND n1.employee_id NOT IN (n0.employee_id)
 LEFT JOIN nodes n2 ON n2.snapshot_date=n0.snapshot_date AND n2.employee_id=n1.manager_id AND n2.employee_id NOT IN (n0.employee_id,n1.employee_id)
 LEFT JOIN nodes n3 ON n3.snapshot_date=n0.snapshot_date AND n3.employee_id=n2.manager_id AND n3.employee_id NOT IN (n0.employee_id,n1.employee_id,n2.employee_id)
 LEFT JOIN nodes n4 ON n4.snapshot_date=n0.snapshot_date AND n4.employee_id=n3.manager_id AND n4.employee_id NOT IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id)
 LEFT JOIN nodes n5 ON n5.snapshot_date=n0.snapshot_date AND n5.employee_id=n4.manager_id AND n5.employee_id NOT IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id)
 LEFT JOIN nodes n6 ON n6.snapshot_date=n0.snapshot_date AND n6.employee_id=n5.manager_id AND n6.employee_id NOT IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id)
 LEFT JOIN nodes n7 ON n7.snapshot_date=n0.snapshot_date AND n7.employee_id=n6.manager_id AND n7.employee_id NOT IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id)
 LEFT JOIN nodes n8 ON n8.snapshot_date=n0.snapshot_date AND n8.employee_id=n7.manager_id AND n8.employee_id NOT IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id)
 LEFT JOIN nodes n9 ON n9.snapshot_date=n0.snapshot_date AND n9.employee_id=n8.manager_id AND n9.employee_id NOT IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id)
 LEFT JOIN nodes n10 ON n10.snapshot_date=n0.snapshot_date AND n10.employee_id=n9.manager_id AND n10.employee_id NOT IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id)
 LEFT JOIN nodes n11 ON n11.snapshot_date=n0.snapshot_date AND n11.employee_id=n10.manager_id AND n11.employee_id NOT IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id)
 LEFT JOIN nodes n12 ON n12.snapshot_date=n0.snapshot_date AND n12.employee_id=n11.manager_id AND n12.employee_id NOT IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id)
 LEFT JOIN nodes n13 ON n13.snapshot_date=n0.snapshot_date AND n13.employee_id=n12.manager_id AND n13.employee_id NOT IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id)
 LEFT JOIN nodes n14 ON n14.snapshot_date=n0.snapshot_date AND n14.employee_id=n13.manager_id AND n14.employee_id NOT IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id)
 LEFT JOIN nodes n15 ON n15.snapshot_date=n0.snapshot_date AND n15.employee_id=n14.manager_id AND n15.employee_id NOT IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id,n14.employee_id)
 LEFT JOIN nodes n16 ON n16.snapshot_date=n0.snapshot_date AND n16.employee_id=n15.manager_id AND n16.employee_id NOT IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id,n14.employee_id,n15.employee_id)
 LEFT JOIN nodes n17 ON n17.snapshot_date=n0.snapshot_date AND n17.employee_id=n16.manager_id AND n17.employee_id NOT IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id,n14.employee_id,n15.employee_id,n16.employee_id)
 LEFT JOIN nodes n18 ON n18.snapshot_date=n0.snapshot_date AND n18.employee_id=n17.manager_id AND n18.employee_id NOT IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id,n14.employee_id,n15.employee_id,n16.employee_id,n17.employee_id)
 LEFT JOIN nodes n19 ON n19.snapshot_date=n0.snapshot_date AND n19.employee_id=n18.manager_id AND n19.employee_id NOT IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id,n14.employee_id,n15.employee_id,n16.employee_id,n17.employee_id,n18.employee_id)
 LEFT JOIN nodes n20 ON n20.snapshot_date=n0.snapshot_date AND n20.employee_id=n19.manager_id AND n20.employee_id NOT IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id,n14.employee_id,n15.employee_id,n16.employee_id,n17.employee_id,n18.employee_id,n19.employee_id)
 LEFT JOIN nodes n21 ON n21.snapshot_date=n0.snapshot_date AND n21.employee_id=n20.manager_id AND n21.employee_id NOT IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id,n14.employee_id,n15.employee_id,n16.employee_id,n17.employee_id,n18.employee_id,n19.employee_id,n20.employee_id)
 LEFT JOIN nodes n22 ON n22.snapshot_date=n0.snapshot_date AND n22.employee_id=n21.manager_id AND n22.employee_id NOT IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id,n14.employee_id,n15.employee_id,n16.employee_id,n17.employee_id,n18.employee_id,n19.employee_id,n20.employee_id,n21.employee_id)
 LEFT JOIN nodes n23 ON n23.snapshot_date=n0.snapshot_date AND n23.employee_id=n22.manager_id AND n23.employee_id NOT IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id,n14.employee_id,n15.employee_id,n16.employee_id,n17.employee_id,n18.employee_id,n19.employee_id,n20.employee_id,n21.employee_id,n22.employee_id)
 LEFT JOIN nodes n24 ON n24.snapshot_date=n0.snapshot_date AND n24.employee_id=n23.manager_id AND n24.employee_id NOT IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id,n14.employee_id,n15.employee_id,n16.employee_id,n17.employee_id,n18.employee_id,n19.employee_id,n20.employee_id,n21.employee_id,n22.employee_id,n23.employee_id)
 LEFT JOIN nodes n25 ON n25.snapshot_date=n0.snapshot_date AND n25.employee_id=n24.manager_id AND n25.employee_id NOT IN (n0.employee_id,n1.employee_id,n2.employee_id,n3.employee_id,n4.employee_id,n5.employee_id,n6.employee_id,n7.employee_id,n8.employee_id,n9.employee_id,n10.employee_id,n11.employee_id,n12.employee_id,n13.employee_id,n14.employee_id,n15.employee_id,n16.employee_id,n17.employee_id,n18.employee_id,n19.employee_id,n20.employee_id,n21.employee_id,n22.employee_id,n23.employee_id,n24.employee_id)
), root_counts AS (
 SELECT snapshot_date,COUNT(DISTINCT ancestor) AS roots,COUNT(*) AS resolved_rows
 FROM walked WHERE eligible=1 AND depth IS NOT NULL AND cycle=0 AND ambiguous_chain=0 GROUP BY 1
), root_sizes AS (
 SELECT snapshot_date,ancestor,COUNT(*) AS members FROM walked
 WHERE eligible=1 AND depth IS NOT NULL AND cycle=0 AND ambiguous_chain=0 GROUP BY 1,2
), convergence AS (SELECT snapshot_date,MAX(members) AS largest_root_rows FROM root_sizes GROUP BY 1),
encoded AS (
 SELECT w.snapshot_date,w.employee_id,w.manager_id,w.stored_level,w.source_rows,w.manager_variants,w.level_variants,
 w.depth,w.ancestor,w.cycle,w.depth_cap,w.ambiguous_chain,
 COALESCE(r.roots,0) AS roots,COALESCE(r.resolved_rows,0) AS resolved_rows,
 COALESCE(c.largest_root_rows,0) AS largest_root_rows,
 CASE WHEN w.depth IS NULL OR w.cycle=1 OR w.ambiguous_chain=1 OR COALESCE(r.roots,0)<>1 THEN '(historia no confirmada)'
      WHEN w.depth<=2 THEN '0-2' WHEN w.depth>=10 THEN '10+' ELSE w.depth::VARCHAR END AS hierarchy_depth_band
 FROM walked w LEFT JOIN root_counts r ON r.snapshot_date=w.snapshot_date
 LEFT JOIN convergence c ON c.snapshot_date=w.snapshot_date WHERE w.eligible=1
)
-- MODEL_OUTPUT
SELECT snapshot_date,MD5(employee_id::VARCHAR||'__RUN_SALT__') AS person_key,hierarchy_depth_band FROM encoded
