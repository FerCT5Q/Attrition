/* Datos enteramente sintéticos; ninguna fila de empleados. */
WITH nodes AS (
SELECT DATE '2024-01-01' AS snapshot_date,1::BIGINT AS employee_id,NULL::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-01-01' AS snapshot_date,2::BIGINT AS employee_id,1::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-01-01' AS snapshot_date,3::BIGINT AS employee_id,2::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-02-01' AS snapshot_date,1::BIGINT AS employee_id,NULL::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-02-01' AS snapshot_date,2::BIGINT AS employee_id,99::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-02-01' AS snapshot_date,3::BIGINT AS employee_id,2::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-03-01' AS snapshot_date,1::BIGINT AS employee_id,NULL::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-03-01' AS snapshot_date,2::BIGINT AS employee_id,2::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-03-01' AS snapshot_date,3::BIGINT AS employee_id,2::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-04-01' AS snapshot_date,1::BIGINT AS employee_id,NULL::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-04-01' AS snapshot_date,2::BIGINT AS employee_id,3::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-04-01' AS snapshot_date,3::BIGINT AS employee_id,2::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-04-01' AS snapshot_date,4::BIGINT AS employee_id,3::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-05-01' AS snapshot_date,1::BIGINT AS employee_id,NULL::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-05-01' AS snapshot_date,2::BIGINT AS employee_id,NULL::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-05-01' AS snapshot_date,3::BIGINT AS employee_id,1::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,0::BIGINT AS employee_id,NULL::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,1::BIGINT AS employee_id,0::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,2::BIGINT AS employee_id,1::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,3::BIGINT AS employee_id,2::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,4::BIGINT AS employee_id,3::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,5::BIGINT AS employee_id,4::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,6::BIGINT AS employee_id,5::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,7::BIGINT AS employee_id,6::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,8::BIGINT AS employee_id,7::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,9::BIGINT AS employee_id,8::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,10::BIGINT AS employee_id,9::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,11::BIGINT AS employee_id,10::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,12::BIGINT AS employee_id,11::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,13::BIGINT AS employee_id,12::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,14::BIGINT AS employee_id,13::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,15::BIGINT AS employee_id,14::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,16::BIGINT AS employee_id,15::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,17::BIGINT AS employee_id,16::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,18::BIGINT AS employee_id,17::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,19::BIGINT AS employee_id,18::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,20::BIGINT AS employee_id,19::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,21::BIGINT AS employee_id,20::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,22::BIGINT AS employee_id,21::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,23::BIGINT AS employee_id,22::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,24::BIGINT AS employee_id,23::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,25::BIGINT AS employee_id,24::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,26::BIGINT AS employee_id,25::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,27::BIGINT AS employee_id,26::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,28::BIGINT AS employee_id,27::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,29::BIGINT AS employee_id,28::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,30::BIGINT AS employee_id,29::BIGINT AS manager_id,NULL::INTEGER AS stored_level,1 AS eligible,1 AS source_rows,1 AS manager_variants,1 AS level_variants
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
, expected AS (
SELECT DATE '2024-01-01' AS snapshot_date,1::BIGINT AS node,0 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-01-01' AS snapshot_date,2::BIGINT AS node,1 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-01-01' AS snapshot_date,3::BIGINT AS node,2 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-02-01' AS snapshot_date,1::BIGINT AS node,0 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-02-01' AS snapshot_date,2::BIGINT AS node,NULL::INTEGER AS expected_depth,0 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-02-01' AS snapshot_date,3::BIGINT AS node,NULL::INTEGER AS expected_depth,0 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-03-01' AS snapshot_date,1::BIGINT AS node,0 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-03-01' AS snapshot_date,2::BIGINT AS node,NULL::INTEGER AS expected_depth,1 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-03-01' AS snapshot_date,3::BIGINT AS node,NULL::INTEGER AS expected_depth,1 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-04-01' AS snapshot_date,1::BIGINT AS node,0 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-04-01' AS snapshot_date,2::BIGINT AS node,NULL::INTEGER AS expected_depth,1 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-04-01' AS snapshot_date,3::BIGINT AS node,NULL::INTEGER AS expected_depth,1 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-04-01' AS snapshot_date,4::BIGINT AS node,NULL::INTEGER AS expected_depth,1 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-05-01' AS snapshot_date,1::BIGINT AS node,0 AS expected_depth,0 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-05-01' AS snapshot_date,2::BIGINT AS node,0 AS expected_depth,0 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-05-01' AS snapshot_date,3::BIGINT AS node,1 AS expected_depth,0 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,0::BIGINT AS node,0 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,1::BIGINT AS node,1 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,2::BIGINT AS node,2 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,3::BIGINT AS node,3 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,4::BIGINT AS node,4 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,5::BIGINT AS node,5 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,6::BIGINT AS node,6 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,7::BIGINT AS node,7 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,8::BIGINT AS node,8 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,9::BIGINT AS node,9 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,10::BIGINT AS node,10 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,11::BIGINT AS node,11 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,12::BIGINT AS node,12 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,13::BIGINT AS node,13 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,14::BIGINT AS node,14 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,15::BIGINT AS node,15 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,16::BIGINT AS node,16 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,17::BIGINT AS node,17 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,18::BIGINT AS node,18 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,19::BIGINT AS node,19 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,20::BIGINT AS node,20 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,21::BIGINT AS node,21 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,22::BIGINT AS node,22 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,23::BIGINT AS node,23 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,24::BIGINT AS node,24 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,25::BIGINT AS node,25 AS expected_depth,0 AS expected_cycle,1 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,26::BIGINT AS node,NULL::INTEGER AS expected_depth,0 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,27::BIGINT AS node,NULL::INTEGER AS expected_depth,0 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,28::BIGINT AS node,NULL::INTEGER AS expected_depth,0 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,29::BIGINT AS node,NULL::INTEGER AS expected_depth,0 AS expected_cycle,0 AS expected_known
UNION ALL
SELECT DATE '2024-06-01' AS snapshot_date,30::BIGINT AS node,NULL::INTEGER AS expected_depth,0 AS expected_cycle,0 AS expected_known
)
SELECT COUNT(*) AS synthetic_cases,
 SUM(CASE WHEN COALESCE(e.depth,-1)<>COALESCE(x.expected_depth,-1) THEN 1 ELSE 0 END) AS depth_mismatches,
 SUM(CASE WHEN e.cycle<>x.expected_cycle THEN 1 ELSE 0 END) AS cycle_mismatches,
 SUM(CASE WHEN (CASE WHEN e.hierarchy_depth_band='(historia no confirmada)' THEN 0 ELSE 1 END)<>x.expected_known THEN 1 ELSE 0 END) AS known_mismatches
FROM encoded e JOIN expected x ON x.snapshot_date=e.snapshot_date AND x.node=e.employee_id;
