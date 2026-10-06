/*
  V7 navigation slide 39 / technical stage 42: 2026 YTD voluntary attrition
  by employee-manager assigned-office/time-zone proximity.

  Population is assigned at the last active monthly snapshot before calendar
  2026. Voluntary exits are calendar dates from 2026-01-01 through the latest
  available HRDA snapshot. This is explicitly YTD, not an annualized rate.
  The catalog map embeds only normalized MD5 office/city-country keys and
  integer UTC offsets calculated locally from IANA zones at the baseline date;
  the query returns aggregate counts and rates only.
*/
WITH source_bounds AS (
    SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS latest_snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
),
baseline AS (
    SELECT MAX(CAST(fis_mo_end_dt AS DATE)) AS baseline_snapshot_date
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt IS NOT NULL
      AND CAST(fis_mo_end_dt AS DATE) < DATE '2026-01-01'
),
source_rows AS (
    SELECT
        CAST(w.employee_id AS BIGINT) AS employee_id,
        MAX(CAST(w.manager_employee_id AS BIGINT)) AS manager_employee_id,
        MAX(MD5(NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.office_site AS VARCHAR(256)))), '[^A-Z0-9]+', ''), ''))) AS office_site_key,
        MAX(CASE WHEN NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.country AS VARCHAR(256)))), '[^A-Z0-9]+', ''), '') IS NOT NULL
                       AND NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), '[^A-Z0-9]+', ''), '') IS NOT NULL
                 THEN MD5(REGEXP_REPLACE(UPPER(TRIM(CAST(w.country AS VARCHAR(256)))), '[^A-Z0-9]+', '') || '|' || REGEXP_REPLACE(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), '[^A-Z0-9]+', '')) END) AS city_country_key,
        COUNT(*) AS source_row_count,
        COUNT(DISTINCT COALESCE(CAST(w.manager_employee_id AS VARCHAR(64)), '<NULL>')) AS manager_id_variants,
        COUNT(DISTINCT COALESCE(NULLIF(UPPER(TRIM(CAST(w.office_site AS VARCHAR(256)))), ''), '<NULL>')) AS office_site_variants,
        COUNT(DISTINCT COALESCE(NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.country AS VARCHAR(256)))), '[^A-Z0-9]+', ''), '') || '|' || NULLIF(REGEXP_REPLACE(UPPER(TRIM(CAST(w.city AS VARCHAR(256)))), '[^A-Z0-9]+', ''), ''), '<NULL>')) AS city_country_variants
    FROM hrda.post_hire_monthly_worker_dtls AS w
    CROSS JOIN baseline AS b
    WHERE CAST(w.fis_mo_end_dt AS DATE) = b.baseline_snapshot_date
      AND w.worker_type = 'Employee'
      AND w.employee_type = 'Regular'
      AND w.active_status = 1
      AND w.employee_id IS NOT NULL
    GROUP BY 1
),
pair_source AS (
    SELECT
        employee.employee_id,
        employee.office_site_key AS employee_office_site_key,
        employee.city_country_key AS employee_city_country_key,
        manager.office_site_key AS manager_office_site_key,
        manager.city_country_key AS manager_city_country_key
    FROM source_rows AS employee
    INNER JOIN source_rows AS manager
      ON manager.employee_id = employee.manager_employee_id
    WHERE employee.source_row_count = 1
      AND employee.manager_id_variants = 1
      AND employee.office_site_variants <= 1
      AND employee.city_country_variants <= 1
      AND manager.source_row_count = 1
      AND manager.office_site_variants <= 1
      AND manager.city_country_variants <= 1
),
pair_zones AS (
    SELECT
        pair.employee_id,
        pair.employee_office_site_key,
        pair.manager_office_site_key,
        COALESCE(CAST(NULL AS INTEGER), CASE pair.employee_city_country_key
              WHEN '048d66ad63e096e443c9a50a10446cb8' THEN 60
              WHEN '087599d95c37d7f032e3509794000e16' THEN 60
              WHEN '0885a3ad7a0d4fe684c21951ac789d9c' THEN -300
              WHEN '0beeb4979a0693df439fb57689b9f296' THEN 0
              WHEN '0c194b86b9856881d4e209dbbff35c4d' THEN 0
              WHEN '0cb93755f1621e84d59f00b26a95a003' THEN 330
              WHEN '12aea7bc5bf1f33cbdc5a4ce6b10daab' THEN 60
              WHEN '12f958e580708029929cd740ff2c0392' THEN 0
              WHEN '16413b9245179786fa0a2bcc584978a4' THEN 60
              WHEN '17a7bcc5789c42e222d021ab8a56a1e8' THEN -360
              WHEN '1853333cf77e77e2ffcaaacb57acbe76' THEN -420
              WHEN '18a3ce7436d9499aaa7431a2afc24bee' THEN 330
              WHEN '1a85248b148fbf704686800ccdbbf59e' THEN 60
              WHEN '1fed499164c0f511d18007ee65c90988' THEN -300
              WHEN '254465d6fab18f6571a9c0b211d30056' THEN -300
              WHEN '257f8072078ce66cabd0d670f48a766b' THEN 540
              WHEN '2d8a6c5edea31534d071de716eb77ee2' THEN -300
              WHEN '3605f56eab4602532b63c7076f8f1681' THEN 60
              WHEN '372b03c8f96548a4ce64957d1360db39' THEN 330
              WHEN '37959c0b6bfcd1bcf689fa6f30a2e12c' THEN -480
              WHEN '390b45fabd478d6aeb04775b7dd0debf' THEN 60
              WHEN '3965cf0c785978006c79b4d27a3e7f36' THEN -360
              WHEN '39bc6048f0a1ddf92cec5955133d60db' THEN 420
              WHEN '3b088bf216b9935642c23ec5c647fbfe' THEN -480
              WHEN '3e2a71b2749dbef74c0821a420c299d9' THEN -480
              WHEN '3eb62aacb48e1025ee6fc7f0d9989353' THEN 0
              WHEN '3f8429601c184229c01e01ce33d94354' THEN 60
              WHEN '408a85c32e167dc6341c8d60e9388b82' THEN 60
              WHEN '4157fb25dcba437bb8798f106a425bed' THEN -300
              WHEN '4189417f01df54afe98a43c16a838da9' THEN -180
              WHEN '423d302d2578494bba84ef4d1ab991b2' THEN 60
              WHEN '43cd86ce9ed82b8a022710f535f937ce' THEN -480
              WHEN '49b378ca63517a070f9f6c5874510bc8' THEN -480
              WHEN '49ccddd7b33751ba3f521ab305c129df' THEN 330
              WHEN '4d18209cef5e81c3d173d81551c93e8a' THEN -300
              WHEN '4e651671c11972256b383449cd9d18b7' THEN 60
              WHEN '544f468b7f4c24c56e7c231829ee968c' THEN -300
              WHEN '5aad71f087c5411ab12263f621e5c03c' THEN 60
              WHEN '5b4ae4c8694f395fe96808f753eb55b4' THEN 60
              WHEN '5b9081a633606bf914e062a0325bb491' THEN -420
              WHEN '5e6ee4d4fc73cadd151dcaff6bc58ee7' THEN 60
              WHEN '5f6a7ed88ab8990cfa14fe2e486318e9' THEN 0
              WHEN '62c6ea3fba14a16c32dfaed1b4027de4' THEN -480
              WHEN '63b8b4176a797bf167a11fc2479e9741' THEN 330
              WHEN '70cd5b9e5880ec91114631bafd265e5c' THEN 60
              WHEN '79e549f94ba583b205b7a81d0c1c7c43' THEN 540
              WHEN '7d5a3cf1dc17f9303d7f3eb6e84a2337' THEN 60
              WHEN '7fc6ea10a089d2849c29ba32e0c75a50' THEN 60
              WHEN '805b6df205d5603a62e31d7672ddf0f2' THEN -480
              WHEN '8120abb46ab2f5c57b04760114c5b0ab' THEN 60
              WHEN '820932500222ee1e4a8b4e53dd40c6d1' THEN -300
              WHEN '8735eec7a464e286de4a95bb4ace0e5b' THEN 60
              WHEN '895c67524197fd08f87af82f4e68290e' THEN 120
              WHEN '96555d0b100f40ec8b28f243ab4668cf' THEN -360
              WHEN 'a088ac6c90913a4da3c9aefcd4b5e086' THEN 330
              WHEN 'a106f407e05fab3917c3a37249fc8227' THEN 60
              WHEN 'a4992853a5bebe3c7007b32b4b5f7431' THEN 60
              WHEN 'a6ec626c80927dde91448b5b90f6ba4f' THEN -480
              WHEN 'add0de222991308d7d718da776bd51d6' THEN -480
              WHEN 'aef6173b052645a5fcabc2492af7f81c' THEN -180
              WHEN 'aef89fc909add0cc837bd3996f3694be' THEN -300
              WHEN 'b19b792f9527dcc6bc02c26e7ce6e4c1' THEN 60
              WHEN 'b1b9a10633d94b2a01a6ae281000c734' THEN -480
              WHEN 'b4c4d3b9dfc7ce43f9b0af303b5ffa81' THEN -300
              WHEN 'b7425ec03e28fb65431220e44066611a' THEN 60
              WHEN 'bc074b0cb8f96c76e37734521f0a458e' THEN 420
              WHEN 'be41b65cbac520f7500bb39b25577a06' THEN 60
              WHEN 'becadb340d48c57697e53681db3e8dd8' THEN -420
              WHEN 'c2fde45d047482a3d7714f33f9c93247' THEN 60
              WHEN 'c5934d84af27c777666b67606fef979e' THEN 420
              WHEN 'c678e0222a3bd0a52212265a2ddc1222' THEN 60
              WHEN 'cbe4da2d4c51183c60139f45ebd2c747' THEN 60
              WHEN 'cd65018cc4ce17ed1020347257bc8225' THEN 60
              WHEN 'cf7becfd6a89f733666a4de8682ee8ac' THEN 120
              WHEN 'cf9be41bea20fc5f63972149245d4c0b' THEN 540
              WHEN 'd651eee36e5c35d418c3b8ac5137cfc1' THEN 60
              WHEN 'd74195836fc5402dacc78b4ecb2511da' THEN 60
              WHEN 'dd9848b3ca82c0ffdb53084580cc9eec' THEN 60
              WHEN 'ded8c85ee4e8a679018c94b080424652' THEN -480
              WHEN 'e55990dfe36fe959bec8f7e97c27aed8' THEN -420
              WHEN 'e5be2fb5ecd5e8bf39152a7e5c34bf6d' THEN 660
              WHEN 'e8eaeb1add7e78235eb564fdb1320220' THEN 330
              WHEN 'ef5ab89522c874b6b033e60b2aac2438' THEN -300
              WHEN 'f1be5d6a4ca1f1ca0f504f430f8fc50e' THEN -300
              WHEN 'f73b374e789618243d935e9fa2ae9caa' THEN -480
              WHEN 'faf0d137f0d089d816c5c28a72db304f' THEN 120
              WHEN 'fbe5354b7bf11565bb48117fd1260a82' THEN 0
              WHEN 'fc280ee572f0dd1213d9dc70f8ae45d8' THEN 60
              END) AS employee_utc_offset_minutes,
        COALESCE(CAST(NULL AS INTEGER), CASE pair.manager_city_country_key
              WHEN '048d66ad63e096e443c9a50a10446cb8' THEN 60
              WHEN '087599d95c37d7f032e3509794000e16' THEN 60
              WHEN '0885a3ad7a0d4fe684c21951ac789d9c' THEN -300
              WHEN '0beeb4979a0693df439fb57689b9f296' THEN 0
              WHEN '0c194b86b9856881d4e209dbbff35c4d' THEN 0
              WHEN '0cb93755f1621e84d59f00b26a95a003' THEN 330
              WHEN '12aea7bc5bf1f33cbdc5a4ce6b10daab' THEN 60
              WHEN '12f958e580708029929cd740ff2c0392' THEN 0
              WHEN '16413b9245179786fa0a2bcc584978a4' THEN 60
              WHEN '17a7bcc5789c42e222d021ab8a56a1e8' THEN -360
              WHEN '1853333cf77e77e2ffcaaacb57acbe76' THEN -420
              WHEN '18a3ce7436d9499aaa7431a2afc24bee' THEN 330
              WHEN '1a85248b148fbf704686800ccdbbf59e' THEN 60
              WHEN '1fed499164c0f511d18007ee65c90988' THEN -300
              WHEN '254465d6fab18f6571a9c0b211d30056' THEN -300
              WHEN '257f8072078ce66cabd0d670f48a766b' THEN 540
              WHEN '2d8a6c5edea31534d071de716eb77ee2' THEN -300
              WHEN '3605f56eab4602532b63c7076f8f1681' THEN 60
              WHEN '372b03c8f96548a4ce64957d1360db39' THEN 330
              WHEN '37959c0b6bfcd1bcf689fa6f30a2e12c' THEN -480
              WHEN '390b45fabd478d6aeb04775b7dd0debf' THEN 60
              WHEN '3965cf0c785978006c79b4d27a3e7f36' THEN -360
              WHEN '39bc6048f0a1ddf92cec5955133d60db' THEN 420
              WHEN '3b088bf216b9935642c23ec5c647fbfe' THEN -480
              WHEN '3e2a71b2749dbef74c0821a420c299d9' THEN -480
              WHEN '3eb62aacb48e1025ee6fc7f0d9989353' THEN 0
              WHEN '3f8429601c184229c01e01ce33d94354' THEN 60
              WHEN '408a85c32e167dc6341c8d60e9388b82' THEN 60
              WHEN '4157fb25dcba437bb8798f106a425bed' THEN -300
              WHEN '4189417f01df54afe98a43c16a838da9' THEN -180
              WHEN '423d302d2578494bba84ef4d1ab991b2' THEN 60
              WHEN '43cd86ce9ed82b8a022710f535f937ce' THEN -480
              WHEN '49b378ca63517a070f9f6c5874510bc8' THEN -480
              WHEN '49ccddd7b33751ba3f521ab305c129df' THEN 330
              WHEN '4d18209cef5e81c3d173d81551c93e8a' THEN -300
              WHEN '4e651671c11972256b383449cd9d18b7' THEN 60
              WHEN '544f468b7f4c24c56e7c231829ee968c' THEN -300
              WHEN '5aad71f087c5411ab12263f621e5c03c' THEN 60
              WHEN '5b4ae4c8694f395fe96808f753eb55b4' THEN 60
              WHEN '5b9081a633606bf914e062a0325bb491' THEN -420
              WHEN '5e6ee4d4fc73cadd151dcaff6bc58ee7' THEN 60
              WHEN '5f6a7ed88ab8990cfa14fe2e486318e9' THEN 0
              WHEN '62c6ea3fba14a16c32dfaed1b4027de4' THEN -480
              WHEN '63b8b4176a797bf167a11fc2479e9741' THEN 330
              WHEN '70cd5b9e5880ec91114631bafd265e5c' THEN 60
              WHEN '79e549f94ba583b205b7a81d0c1c7c43' THEN 540
              WHEN '7d5a3cf1dc17f9303d7f3eb6e84a2337' THEN 60
              WHEN '7fc6ea10a089d2849c29ba32e0c75a50' THEN 60
              WHEN '805b6df205d5603a62e31d7672ddf0f2' THEN -480
              WHEN '8120abb46ab2f5c57b04760114c5b0ab' THEN 60
              WHEN '820932500222ee1e4a8b4e53dd40c6d1' THEN -300
              WHEN '8735eec7a464e286de4a95bb4ace0e5b' THEN 60
              WHEN '895c67524197fd08f87af82f4e68290e' THEN 120
              WHEN '96555d0b100f40ec8b28f243ab4668cf' THEN -360
              WHEN 'a088ac6c90913a4da3c9aefcd4b5e086' THEN 330
              WHEN 'a106f407e05fab3917c3a37249fc8227' THEN 60
              WHEN 'a4992853a5bebe3c7007b32b4b5f7431' THEN 60
              WHEN 'a6ec626c80927dde91448b5b90f6ba4f' THEN -480
              WHEN 'add0de222991308d7d718da776bd51d6' THEN -480
              WHEN 'aef6173b052645a5fcabc2492af7f81c' THEN -180
              WHEN 'aef89fc909add0cc837bd3996f3694be' THEN -300
              WHEN 'b19b792f9527dcc6bc02c26e7ce6e4c1' THEN 60
              WHEN 'b1b9a10633d94b2a01a6ae281000c734' THEN -480
              WHEN 'b4c4d3b9dfc7ce43f9b0af303b5ffa81' THEN -300
              WHEN 'b7425ec03e28fb65431220e44066611a' THEN 60
              WHEN 'bc074b0cb8f96c76e37734521f0a458e' THEN 420
              WHEN 'be41b65cbac520f7500bb39b25577a06' THEN 60
              WHEN 'becadb340d48c57697e53681db3e8dd8' THEN -420
              WHEN 'c2fde45d047482a3d7714f33f9c93247' THEN 60
              WHEN 'c5934d84af27c777666b67606fef979e' THEN 420
              WHEN 'c678e0222a3bd0a52212265a2ddc1222' THEN 60
              WHEN 'cbe4da2d4c51183c60139f45ebd2c747' THEN 60
              WHEN 'cd65018cc4ce17ed1020347257bc8225' THEN 60
              WHEN 'cf7becfd6a89f733666a4de8682ee8ac' THEN 120
              WHEN 'cf9be41bea20fc5f63972149245d4c0b' THEN 540
              WHEN 'd651eee36e5c35d418c3b8ac5137cfc1' THEN 60
              WHEN 'd74195836fc5402dacc78b4ecb2511da' THEN 60
              WHEN 'dd9848b3ca82c0ffdb53084580cc9eec' THEN 60
              WHEN 'ded8c85ee4e8a679018c94b080424652' THEN -480
              WHEN 'e55990dfe36fe959bec8f7e97c27aed8' THEN -420
              WHEN 'e5be2fb5ecd5e8bf39152a7e5c34bf6d' THEN 660
              WHEN 'e8eaeb1add7e78235eb564fdb1320220' THEN 330
              WHEN 'ef5ab89522c874b6b033e60b2aac2438' THEN -300
              WHEN 'f1be5d6a4ca1f1ca0f504f430f8fc50e' THEN -300
              WHEN 'f73b374e789618243d935e9fa2ae9caa' THEN -480
              WHEN 'faf0d137f0d089d816c5c28a72db304f' THEN 120
              WHEN 'fbe5354b7bf11565bb48117fd1260a82' THEN 0
              WHEN 'fc280ee572f0dd1213d9dc70f8ae45d8' THEN 60
              END) AS manager_utc_offset_minutes
    FROM pair_source AS pair
),
pair_categories AS (
    SELECT
        pair.employee_id,
        CASE
          WHEN pair.employee_office_site_key IS NOT NULL AND pair.employee_office_site_key = pair.manager_office_site_key THEN 'same_office_site'
          WHEN pair.employee_utc_offset_minutes IS NULL OR pair.manager_utc_offset_minutes IS NULL THEN 'unmapped_time_zone_proxy'
          WHEN ABS(pair.employee_utc_offset_minutes - pair.manager_utc_offset_minutes) <= 240 THEN 'different_site_up_to_4_hours'
          ELSE 'different_site_more_than_4_hours'
        END AS category
    FROM pair_zones AS pair
),
voluntary_events AS (
    SELECT CAST(employee_id AS BIGINT) AS employee_id, CAST(term_date AS DATE) AS term_date
    FROM hrda.post_hire_monthly_worker_dtls
    CROSS JOIN source_bounds AS bounds
    WHERE worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
      AND CAST(term_date AS DATE) >= DATE '2026-01-01'
      AND CAST(term_date AS DATE) <= bounds.latest_snapshot_date
    GROUP BY 1, 2
),
target_flags AS (
    SELECT
        pair.employee_id,
        pair.category,
        MAX(CASE WHEN event.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS ytd_voluntary_attrition_target
    FROM pair_categories AS pair
    LEFT JOIN voluntary_events AS event
      ON event.employee_id = pair.employee_id
    GROUP BY 1, 2
),
category_metrics AS (
    SELECT
        category,
        COUNT(DISTINCT employee_id) AS employee_count,
        SUM(ytd_voluntary_attrition_target) AS voluntary_exits,
        ROUND(100.0 * SUM(ytd_voluntary_attrition_target) / NULLIF(COUNT(*), 0), 4) AS ytd_voluntary_attrition_rate_percent
    FROM target_flags
    WHERE category IN ('same_office_site', 'different_site_up_to_4_hours', 'different_site_more_than_4_hours')
    GROUP BY 1
)
SELECT
    'category' AS row_type,
    'time_zone_proximity' AS metric,
    category,
    b.baseline_snapshot_date,
    bounds.latest_snapshot_date AS outcome_end_date,
    employee_count,
    voluntary_exits,
    ytd_voluntary_attrition_rate_percent,
    CAST(NULL AS BIGINT) AS diagnostic_value
FROM category_metrics
CROSS JOIN baseline AS b
CROSS JOIN source_bounds AS bounds
UNION ALL
SELECT
    'diagnostic', metric, CAST(NULL AS VARCHAR(64)), b.baseline_snapshot_date, bounds.latest_snapshot_date,
    CAST(NULL AS BIGINT), CAST(NULL AS BIGINT), CAST(NULL AS DECIMAL(18,4)), diagnostic_value
FROM (
    SELECT 'eligible_employee_manager_pair_count' AS metric, COUNT(*)::BIGINT AS diagnostic_value FROM target_flags
    UNION ALL SELECT 'categorized_employee_manager_pair_count', COUNT(*)::BIGINT FROM target_flags WHERE category IN ('same_office_site', 'different_site_up_to_4_hours', 'different_site_more_than_4_hours')
    UNION ALL SELECT 'unmapped_employee_manager_pair_count', COUNT(*)::BIGINT FROM target_flags WHERE category = 'unmapped_time_zone_proxy'
    UNION ALL SELECT 'duplicate_employee_source_count', SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END)::BIGINT FROM source_rows
    UNION ALL SELECT 'location_conflict_count', SUM(CASE WHEN office_site_variants > 1 OR city_country_variants > 1 THEN 1 ELSE 0 END)::BIGINT FROM source_rows
) AS diagnostics
CROSS JOIN baseline AS b
CROSS JOIN source_bounds AS bounds
ORDER BY row_type, category, metric;
