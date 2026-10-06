# HRDA Schema Notes for Attrition

Last inspected: 2026-08-03.

## Main Table

`hrda.post_hire_monthly_worker_dtls`

Observed profile from metadata/aggregate probe:

- Grain appears to be employee-month / worker-month, not one row per employee.
- Approximate rows inspected: 6,907,490.
- Fiscal month range observed: 2016-10-23 through 2026-08-23.
- Fiscal date columns: `fis_mo_beg_dt`, `fis_mo_end_dt`, `fiscal_month`, `fiscal_quarter`, `fiscal_year`.
- The old Claude command referenced `job_level`; that column does not exist. Use `job_level_primary_position`, `level_grouped`, `management_level`, or compensation grade fields instead.

## Nearby Candidate Tables

Use these only after verifying schema and purpose:

- `all_terminations`
- `post_hire_daily_worker_dtls`
- `post_hire_monthly_worker_dtls_term`
- `wd_term`
- `worker_details`
- `worker_details_latest`
- `worker_details_snapshot`
- `worker_snapshot_vw`
- `worker_level`
- `new_hires`
- `new_hires_vw`
- `workers_ios_transfers`
- `workers_on_leave`

## Useful Attrition Columns

Time and snapshot fields:

- `fis_mo_beg_dt`, `fis_mo_end_dt`, `fiscal_month`, `fiscal_quarter`, `fiscal_year`
- `last_modified_date`, `airflow_execution_date`, `airflow_db_processing_ts`

Employment status and termination fields:

- `employee_status`, `active_status`, `is_termed`
- `term_date`, `end_employment_date`
- `term_type`, `term_reason`, `term_reasonall`
- `termination_date_on_after_probation_end_date`

Hire and tenure fields:

- `original_hire_date`, `hire_date_o_ea`, `max_hire_rehire_date`
- `new_hire_date`, `is_new_hire`, `is_hire`, `new_hire_type`
- `rehire_date`, `is_rehire`, `service_date`, `seniority_date`
- `time_in_role`, `time_in_job_profile_start_date`
- `probation_end_date_of_employee`, `probation_period_status`

Job, level, org, and segment fields:

- `worker_type`, `employee_type`, `full_or_part_time`, `fte`, `std_hours`
- `job_family`, `job_family_short`, `job_family_group`, `job_family_group_short`
- `job_level_primary_position`, `level_grouped`, `management_level`
- `job_code`, `job_title`, `job_exempt`, `compensation_grade`, `compensation_grade_profile`
- `business_unit`, `finance_tbu`, `cost_center`, `cost_centerid`, `cost_centername`
- `region`, `country`, `city`, `office_location`, `office_site`, `state_province`, `labor_market`
- `eng_or_noneng`, `technical_employee1`, `classification_e_ne`

Movement/event fields:

- `is_promo`, `promotion_date`
- `is_demoted`, `demotion_date`
- `is_transferred`, `transfer_date`
- `job_family_change`, `job_family_change_date`
- `location_change`, `location_change_date`
- `cost_center_change`, `cost_center_change_date`
- `manager_change`, `manager_change_date`, `manager_effective_date`

Compensation fields. Use only as bands/percentiles/relative metrics, not raw values:

- `compa_ratio`
- `annual_base_pay`, `base_pay_rate`, `total_base_pay_amount`, `fte_annual_base_pay`
- `base_pay_frequency`, `fte_annual_base_pay_currency_code`

Leadership hierarchy fields. Use cautiously because small org slices can identify people:

- `manager_employee_id`, `manager_name`, `dept_head_name`
- `et_leader`, `et_1_leader`, `et_2_leader`, `et_3_leader`, `et_4_leader`, `et_5_leader`, `et_6_leader`, `et_7_leader`, `et_8_leader`, `et_9_leader`, `et_10_leader`, `et_11_leader`
- `worker_supervisory_organization_level_from_top`
- `reg_non_intern_dir_reports`, `reg_non_intern_total_reports`, `all_dir_reports`, `all_total_reports`

## Sensitive or Restricted Columns

Do not output raw values. Do not use in shared dashboards without explicit governance approval.

Identity and contact:

- `employee_id`, `emp_name`, `name`, `legal_first_name`, `legal_last_name`, `preferred_first_name`
- `email`, `manager_work_email`, `supervisor_email`, `supervisor_emplid`, `supervisor_name`
- `homeaddresswithcountry`, `home_city`, `home_state`, `postal_code`

Protected/sensitive demographics:

- `gender`, `race`, `disability_status`, `veteran_status_identification`
- `dateofbirth`, `year_of_birth`, `month_of_birth`
- `primary_citizenship`, `secondary_citizenship`, `country_of_birth_locale_sensitive`

Education and language fields can become identifying in small cohorts:

- `highest_degree`, `highest_degree_major`, `highest_degree_school`, `highest_degree_year`
- `year_degree_received`, `languages`

Compensation exact values:

- `annual_base_pay`, `base_pay_rate`, `total_base_pay_amount`, `fte_annual_base_pay`

Free-text/process fields to treat cautiously:

- `recruiting_instructions`, `business_process_reason`, `term_reasonall`

## Safe Query Examples

Schema discovery:

```sql
SELECT column_name, data_type, ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name = 'post_hire_monthly_worker_dtls'
ORDER BY ordinal_position;
```

Date/range profile:

```sql
SELECT
  COUNT(*) AS row_count,
  MIN(fis_mo_end_dt) AS min_fis_mo_end_dt,
  MAX(fis_mo_end_dt) AS max_fis_mo_end_dt
FROM hrda.post_hire_monthly_worker_dtls;
```

Termination label discovery, aggregated only:

```sql
SELECT
  term_type,
  term_reason,
  COUNT(*) AS n
FROM hrda.post_hire_monthly_worker_dtls
WHERE is_termed = 1
GROUP BY 1, 2
ORDER BY n DESC
LIMIT 50;
```

Monthly attrition by job family with privacy threshold:

```sql
WITH monthly AS (
  SELECT
    fis_mo_end_dt,
    job_family_group,
    COUNT(*) AS worker_month_rows,
    SUM(CASE WHEN is_termed = 1 THEN 1 ELSE 0 END) AS term_rows
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE employee_type = 'Regular'
    AND worker_type = 'Employee'
  GROUP BY 1, 2
)
SELECT
  fis_mo_end_dt,
  job_family_group,
  worker_month_rows,
  term_rows,
  term_rows::decimal(18,4) / NULLIF(worker_month_rows, 0) AS term_rate
FROM monthly
WHERE worker_month_rows >= 30
ORDER BY fis_mo_end_dt DESC, term_rate DESC;
```

Cohort segmentation pattern:

```sql
WITH cohort AS (
  SELECT
    fis_mo_end_dt,
    job_family_group,
    level_grouped,
    region,
    CASE
      WHEN time_in_role IS NULL THEN 'unknown'
      WHEN time_in_role < 1 THEN '<1y'
      WHEN time_in_role < 2 THEN '1-2y'
      WHEN time_in_role < 4 THEN '2-4y'
      ELSE '4y+'
    END AS time_in_role_band,
    COUNT(*) AS n,
    SUM(CASE WHEN is_termed = 1 THEN 1 ELSE 0 END) AS terms
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
  GROUP BY 1, 2, 3, 4, 5
)
SELECT fis_mo_end_dt, job_family_group, level_grouped, region, time_in_role_band, n, terms, terms::decimal(18,4) / NULLIF(n, 0) AS term_rate
FROM cohort
WHERE n >= 30
ORDER BY fis_mo_end_dt DESC, term_rate DESC;
```

