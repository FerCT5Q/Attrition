# CTO Population Definition

## Purpose

Define the employee population that belongs to the CTO organization for HRDA workforce analysis.

## CTO Leaders

The CTO population starts from these two employee records:

| Leader | Employee ID | Job title | Job level | Management level |
|---|---:|---|---|---|
| Jim Thompson | 892 | Chief Technology Officer | EVP - X45 | Officers |
| Baaziz Achour | 1200 | EVP, Chief Technology Officer | EVP - X45 | Officers |

Both leaders report to Cristiano Amon through `manager_employee_id = 3151` and are at the same formal level.

## Population Filters

Unless an analysis explicitly states otherwise, use:

```text
active_status = 1
employee_type = 'Regular'
is_rf360_yes_no = 0
```

`active_status = 1` is required when reporting current headcount. The monthly table
retains terminated employees for historical attrition analysis, so counting all rows
would overstate the current organization size.

The population should be evaluated in the selected monthly or daily snapshot. Do not mix rows from different snapshot dates.

## Correct CTO Logic

The current HRDA data requires a hybrid definition because the two hierarchy signals are incomplete in different ways:

1. Jim's organization is identified through a recursive `manager_employee_id` chain starting at employee ID `892`.
2. Baaziz's organization is identified through `et_leader = 'Baaziz Achour (1200)'`.

The manager hierarchy is still checked for Baaziz, but it misses 2,252 Regular/non-RF360 employees whose `manager_employee_id` is blank. Conversely, Jim's direct reports have their own values in `et_leader`, so filtering `et_leader = Jim` misses Jim's organization.

The operational CTO population is therefore:

```text
CTO under leaders =
  recursive manager descendants of employee 892
  UNION
  employees where et_leader = 'Baaziz Achour (1200)'
```

Baaziz himself is removed from the second set when counting people "under" the leaders. Jim and Baaziz are added only when reporting organization size including the leaders.

## Do Not Use These Fields as the CTO Definition

Do not define the full CTO organization using only:

```text
et_leader
et_1_leader
```

`et_leader` alone misses Jim's organization. `manager_employee_id` alone misses part of Baaziz's organization because some records have no manager ID. `et_1_leader` is a lower-level organizational attribute and should not be used as the population boundary.

## Latest Validated Counts

Using the latest monthly snapshot available during the analysis (`fis_mo_end_dt = 2026-09-27`) and the Regular/non-RF360 filters:

| CTO root | Direct reports | Descendants under leader | Organization including leader |
|---|---:|---:|---:|
| Jim Thompson | 9 | 19 | 20 |
| Baaziz Achour | 28 manager-direct reports; 2,252 ET-only records | 52,407 | 52,408 |
| Both leaders | 37 manager-direct reports plus ET-only records | 52,426 | 52,428 |

The Jim manager chain and the Baaziz ET population have no overlap in the validated monthly snapshot. The same hybrid logic should be applied to daily data after selecting the latest row per employee for the relevant snapshot.

## CTO and Critical Tech Intersection

Critical Tech is a separate classification. It is derived by matching the employee's normalized `job_family` to the normalized `extended_job_family` in `hrda.critical_tech`:

```text
lower(trim(job_family))
= lower(trim(extended_job_family))
```

The Critical Tech catalog should be joined after the CTO hierarchy has been calculated. The resulting categories are:

| Category | Definition |
|---|---|
| CTO and Critical Tech | Employee is under Jim or Baaziz and their job family matches the Critical Tech catalog |
| CTO only | Employee is under Jim or Baaziz and their job family does not match the catalog |
| Critical Tech only | Employee matches the catalog but is outside both CTO hierarchies |
| Neither | Employee is outside both CTO hierarchies and does not match the catalog |

## Recommended Query Pattern

Conceptually, the query should follow this order:

1. Select one monthly or daily employee snapshot.
2. Apply `Regular` and non-RF360 filters.
3. Build the recursive manager hierarchy from employee ID `892` for Jim.
4. Add employees with `et_leader = 'Baaziz Achour (1200)'` for Baaziz, excluding employee ID `1200` when counting people under the leaders.
5. Deduplicate the union of both sets and verify that there is no overlap.
6. Join the resulting employee population to `hrda.critical_tech` by normalized job family.
7. Aggregate total HC, CTO HC, Critical Tech HC, intersection HC, and the exclusive groups.

## Data Quality Checks

Before using the result, verify:

- The snapshot contains one selected row per employee.
- `manager_employee_id` is populated for expected direct reports, especially in Jim's chain.
- Baaziz's ET population is reconciled against the manager hierarchy and missing manager IDs are quantified.
- The recursive hierarchy terminates and does not produce duplicate employees.
- Jim and Baaziz are not counted twice through an overlapping hierarchy or union.
- The Critical Tech catalog metadata date is recorded with the analysis.
- Employees with `employee_type` other than `Regular` and RF360 employees are excluded when using the standard population definition.

## Known Data Caveats

- `et_leader` and `manager_employee_id` are complementary signals in the current data: `et_leader` is required to recover Baaziz's records with missing manager IDs, while the manager chain is required to recover Jim's organization.
- `et_1_leader` is informative for organizational detail but is not the population boundary.
- `reg_non_intern_dir_reports` and `reg_non_intern_total_reports` should be treated as reference fields, not as the primary membership logic.
- `post_hire_daily_worker_dtls` contains multiple historical rows per employee; daily analysis requires a snapshot selection or latest-row deduplication.
- `hrda.critical_tech` is a family-level catalog, not an employee-level Critical Tech flag.
