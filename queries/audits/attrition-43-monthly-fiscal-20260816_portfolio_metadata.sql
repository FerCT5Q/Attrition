SELECT
  c.table_schema,
  c.table_name,
  c.column_name,
  c.data_type,
  c.ordinal_position,
  CASE
    WHEN ((c.table_schema = 'hrda' AND c.table_name = 'applications') OR
    (c.table_schema = 'hrda' AND c.table_name = 'master_talent_index') OR
    (c.table_schema = 'hrda' AND c.table_name = 'post_hire_monthly_worker_dtls') OR
    (c.table_schema = 'hrda' AND c.table_name = 'qvoice_survey_data plus hrda.post_hire_monthly_worker_dtls')) THEN 'requested_table'
    ELSE 'semantic_synonym'
  END AS discovery_reason
FROM information_schema.columns c
WHERE ((c.table_schema = 'hrda' AND c.table_name = 'applications') OR
    (c.table_schema = 'hrda' AND c.table_name = 'master_talent_index') OR
    (c.table_schema = 'hrda' AND c.table_name = 'post_hire_monthly_worker_dtls') OR
    (c.table_schema = 'hrda' AND c.table_name = 'qvoice_survey_data plus hrda.post_hire_monthly_worker_dtls'))
   OR (
      c.table_schema IN ('hrda')
      AND (LOWER(c.column_name) LIKE '%about%' OR
      LOWER(c.column_name) LIKE '%application%' OR
      LOWER(c.column_name) LIKE '%applications%' OR
      LOWER(c.column_name) LIKE '%applied%' OR
      LOWER(c.column_name) LIKE '%arrangement%' OR
      LOWER(c.column_name) LIKE '%average%' OR
      LOWER(c.column_name) LIKE '%away%' OR
      LOWER(c.column_name) LIKE '%bonus%' OR
      LOWER(c.column_name) LIKE '%cand%' OR
      LOWER(c.column_name) LIKE '%candidate%' OR
      LOWER(c.column_name) LIKE '%career%' OR
      LOWER(c.column_name) LIKE '%center%' OR
      LOWER(c.column_name) LIKE '%change%' OR
      LOWER(c.column_name) LIKE '%changes%' OR
      LOWER(c.column_name) LIKE '%code%' OR
      LOWER(c.column_name) LIKE '%comment%' OR
      LOWER(c.column_name) LIKE '%commute%' OR
      LOWER(c.column_name) LIKE '%comp%' OR
      LOWER(c.column_name) LIKE '%compa%' OR
      LOWER(c.column_name) LIKE '%company%' OR
      LOWER(c.column_name) LIKE '%compensation%' OR
      LOWER(c.column_name) LIKE '%cost%' OR
      LOWER(c.column_name) LIKE '%country%' OR
      LOWER(c.column_name) LIKE '%cycle%' OR
      LOWER(c.column_name) LIKE '%development%' OR
      LOWER(c.column_name) LIKE '%distance%' OR
      LOWER(c.column_name) LIKE '%draup%' OR
      LOWER(c.column_name) LIKE '%empl%' OR
      LOWER(c.column_name) LIKE '%engineering%' OR
      LOWER(c.column_name) LIKE '%experience%' OR
      LOWER(c.column_name) LIKE '%external coordinates or distance%' OR
      LOWER(c.column_name) LIKE '%external date%' OR
      LOWER(c.column_name) LIKE '%external geography%' OR
      LOWER(c.column_name) LIKE '%external travel-time or time-zone fields%' OR
      LOWER(c.column_name) LIKE '%family%' OR
      LOWER(c.column_name) LIKE '%fields%' OR
      LOWER(c.column_name) LIKE '%gender%' OR
      LOWER(c.column_name) LIKE '%goals%' OR
      LOWER(c.column_name) LIKE '%grade%' OR
      LOWER(c.column_name) LIKE '%group%' OR
      LOWER(c.column_name) LIKE '%grouped%' OR
      LOWER(c.column_name) LIKE '%growth%' OR
      LOWER(c.column_name) LIKE '%high%' OR
      LOWER(c.column_name) LIKE '%hire%' OR
      LOWER(c.column_name) LIKE '%hired%' OR
      LOWER(c.column_name) LIKE '%homeaddresswithcountry%' OR
      LOWER(c.column_name) LIKE '%hours%' OR
      LOWER(c.column_name) LIKE '%hybrid%' OR
      LOWER(c.column_name) LIKE '%index%' OR
      LOWER(c.column_name) LIKE '%industry%' OR
      LOWER(c.column_name) LIKE '%inflection%' OR
      LOWER(c.column_name) LIKE '%intent%' OR
      LOWER(c.column_name) LIKE '%into%' OR
      LOWER(c.column_name) LIKE '%items%' OR
      LOWER(c.column_name) LIKE '%labor%' OR
      LOWER(c.column_name) LIKE '%last%' OR
      LOWER(c.column_name) LIKE '%launch%' OR
      LOWER(c.column_name) LIKE '%layers%' OR
      LOWER(c.column_name) LIKE '%leader%' OR
      LOWER(c.column_name) LIKE '%leaves%')
   )
ORDER BY discovery_reason, c.table_schema, c.table_name, c.ordinal_position
LIMIT 10000
