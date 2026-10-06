/*
Claim: HRDA exposes an approved QVoice invitation/eligibility roster and a
response indicator that can support a non-respondent denominator.
Mode: internal_analysis; metadata only; no employee rows.
Acceptance rule: identify the QVoice-related table(s), their row grain clues,
and columns that can represent invitation, eligibility, response, wave, or
participant status. A response-only table does not establish non-respondents.
*/
SELECT
    c.table_schema,
    c.table_name,
    c.ordinal_position,
    c.column_name,
    c.data_type
FROM information_schema.columns AS c
WHERE c.table_schema = 'hrda'
  AND (
      LOWER(c.table_name) LIKE '%qvoice%'
      OR LOWER(c.table_name) LIKE '%survey%'
      OR LOWER(c.table_name) LIKE '%pulse%'
      OR LOWER(c.column_name) LIKE '%qvoice%'
      OR LOWER(c.column_name) LIKE '%survey%'
      OR LOWER(c.column_name) LIKE '%respond%'
      OR LOWER(c.column_name) LIKE '%participant%'
  )
ORDER BY c.table_name, c.ordinal_position
LIMIT 500;
