/*
Conceptual aggregate join executed by tools/build_qvoice_nonrespondent_proxy_evidence.py.
The runtime injects raw-workbook employee IDs in memory through chunked IN
predicates; the injected SQL is not persisted because it contains identifiers.

Assumption for internal review:
  - the selected stored workforce snapshot is the proxy for the prior-month
    day-15 survey population;
  - every employee in that snapshot was invited/elegible;
  - an employee is a respondent when at least one original survey-answer field
    in the raw QVoice row is populated.

The aggregate output separates:
  1) a matched QVoice row with at least one answer;
  2) a matched QVoice row with no answer fields populated; and
  3) an eligible snapshot employee with no QVoice row.

Those categories are a non-response proxy until the invitation roster and
survey-platform response status are confirmed.
*/
WITH workforce AS (
    SELECT employee_id
    FROM hrda.post_hire_monthly_worker_dtls
    WHERE fis_mo_end_dt = :snapshot_date
      AND worker_type = 'Employee'
      AND employee_type = 'Regular'
      AND active_status = 1
    GROUP BY employee_id
)
SELECT
    COUNT(*) AS eligible_snapshot_employees,
    /* Runtime adds chunked response/no-answer IN lists. */
    SUM(CASE WHEN employee_id IN (/* responded IDs */) THEN 1 ELSE 0 END) AS responded_proxy,
    SUM(CASE WHEN employee_id IN (/* no-answer IDs */) THEN 1 ELSE 0 END) AS qvoice_row_without_answer,
    SUM(CASE WHEN employee_id NOT IN (/* all QVoice IDs */) THEN 1 ELSE 0 END) AS no_qvoice_row
FROM workforce;
