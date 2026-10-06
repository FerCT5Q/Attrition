# Job Family Reassignment - 2026-09-01

## Summary

The HRDA daily workforce data shows a large reassignment of `job_family` values between the snapshots dated August 31, 2026 and September 1, 2026.

This was primarily a reclassification from broad engineering families into more specific technical families. It was not a comparable update to the Critical Tech catalog: `hrda.critical_tech` still has the same 62 families and its latest metadata date is October 30, 2025.

The main reassignment occurred on September 1. The September 3 snapshot contains only a small number of additional changes and should not be treated as the date of the bulk update.

## Global Impact

Source: `hrda.post_hire_daily_worker_dtls`.

Comparison: employee-level `job_family` values in the August 31 and September 1 snapshots, matched by `employee_id`.

| Metric | August 31 | September 1 |
|---|---:|---:|
| Total employees in daily snapshot | 127,475 | 127,585 |
| Regular, non-RF360 employees | 70,308 | 70,376 |
| Rows flagged with `job_family_change = 1` | 22 | 12,065 |
| Regular, non-RF360 rows flagged | 18 | 11,405 |

Direct comparison of the old and new `job_family` values found:

| Measure | Employees |
|---|---:|
| Actual `job_family` transitions | 12,065 |
| Actual transitions, Regular/non-RF360 on September 1 | 11,405 |

The `job_family_change` flag and the direct comparison are nearly identical, but they should not be treated as interchangeable. The flag is an attribute supplied by the source data; the direct comparison is the reproducible way to identify an actual transition between two snapshots.

## Main Global Transitions

The largest transitions among Regular, non-RF360 employees were:

| Previous job family | New job family | Employees |
|---|---|---:|
| Hardware Engineering | ASICS Engineering | 4,483 |
| Software Engineering | Cellular Technologies Software | 895 |
| Systems Test Engineering | Cellular System Test Engineering | 638 |
| Software Test Engineering | Systems Test Engineering | 549 |
| Hardware Engineering | CPU Engineering | 515 |
| Systems Engineering | Cellular Technologies | 409 |
| Hardware Engineering | GPU ASICS Engineering | 392 |
| Systems Engineering | Camera Engineering | 320 |
| Software Engineering | Camera Software Engineering | 304 |
| Software Engineering | Graphics Software Engineering | 237 |
| Software Engineering | Cellular System Test Engineering | 193 |
| Hardware Engineering | Camera Engineering | 180 |
| Hardware Engineering | CAD Engineering | 174 |
| Systems Engineering | Video Systems, HW Architecture | 147 |
| Systems Engineering | Multimedia Systems | 137 |

These transitions explain the apparent movement from broad families such as `Hardware Engineering`, `Software Engineering`, and `Systems Engineering` into specialized engineering families.

## Effect on Critical Tech Classification

The Critical Tech classification in this analysis is derived by matching:

```text
lower(trim(post_hire.job_family))
= lower(trim(critical_tech.extended_job_family))
```

The current `critical_tech` table contains 62 distinct families. Its metadata is:

| Field | Value |
|---|---|
| `last_modified_date` | 2025-10-30 |
| `airflow_execution_date` | 2025-10-30 |
| Current catalog rows | 62 |
| Current distinct families | 62 |

There is no evidence in HRDA that this catalog was updated around September 1 or September 3, 2026.

Among all employees with a `job_family` transition:

| Old classification | New classification | All employees | Regular/non-RF360 on September 1 |
|---|---|---:|---:|
| Non-Critical | Non-Critical | 11 | 6 |
| Non-Critical | Critical | 3 | 1 |
| Critical | Non-Critical | 0 | 0 |
| Critical | Critical | 12,051 | 11,396 |

Therefore, for the Regular/non-RF360 population, 11,396 of 11,405 transitions moved from one Critical Tech family to another. Only one person moved from non-Critical to Critical, and no one moved from Critical to non-Critical.

The one Regular/non-RF360 employee whose derived classification changed was:

| Employee ID | Employee | Previous family | New family |
|---:|---|---|---|
| 135418 | Shivam Gupta | Security Engineering | Software Engineering |

This means the September 1 update materially changed the granularity and naming of job families, but it had very little effect on the derived Critical Tech classification under the current catalog.

## India Case

For India, the same event was especially visible:

| Date | Regular/non-RF360 HC | Actual job family transitions |
|---|---:|---:|
| 2026-08-31 | 28,889 | 0 |
| 2026-09-01 | 28,930 | 10,001 |
| 2026-09-02 | 28,930 | 27 |
| 2026-09-03 | 28,930 | 11 |
| 2026-09-07 | 28,967 | 5 |

India's largest transitions were:

| Previous job family | New job family | Employees |
|---|---|---:|
| Hardware Engineering | ASICS Engineering | 4,480 |
| Software Engineering | Cellular Technologies Software | 844 |
| Software Test Engineering | Systems Test Engineering | 547 |
| Hardware Engineering | CPU Engineering | 515 |
| Systems Test Engineering | Cellular System Test Engineering | 497 |
| Hardware Engineering | GPU ASICS Engineering | 392 |
| Systems Engineering | Cellular Technologies | 325 |
| Software Engineering | Camera Software Engineering | 225 |
| Software Engineering | Graphics Software Engineering | 214 |

For India, 10,000 of the 10,001 Regular/non-RF360 transitions remained Critical Tech before and after the change. One employee moved from non-Critical to Critical.

## Monthly Cross-Check

The monthly table does not contain a September 1 snapshot, so it cannot be used to observe the event day directly. It does show the resulting state in the next available monthly snapshot.

Source: `hrda.post_hire_monthly_worker_dtls`.

| Monthly snapshot | Regular/non-RF360 HC | Derived Critical Tech HC |
|---|---:|---:|
| 2026-08-23 | 70,088 | 54,776 |
| 2026-09-27 | 70,453 | 55,070 |

For India:

| Monthly snapshot | Regular/non-RF360 HC | Derived Critical Tech HC |
|---|---:|---:|
| 2026-08-23 | 28,801 | 24,892 |
| 2026-09-27 | 28,967 | 25,044 |

The monthly change includes normal workforce movements, hires, terminations, and other changes during the period. It should not be interpreted as the direct impact of the September 1 reassignment alone.

## Recommended Logic for Future Analysis or an Agent

1. Use `post_hire_daily_worker_dtls` to detect the event because it contains daily snapshots and `job_family_change`.
2. Compare two snapshots by `employee_id`, rather than relying only on `job_family_change`.
3. Define the population explicitly as `employee_type = 'Regular'` and `is_rf360_yes_no = 0`.
4. Use the September 1 employee status when reporting the post-change population.
5. Derive Critical Tech from the current `critical_tech.extended_job_family` catalog, matching normalized `job_family` values.
6. Record the catalog metadata date with every analysis. The current catalog is stale relative to the September 2026 employee update.
7. For CTO scope, use the recursive `manager_employee_id` hierarchy from the CTO employee IDs. Do not use `et_leader` or `et_1_leader` as a substitute for all descendants.

## Important Caveats

- `critical_tech` is a family-level catalog, not an employee-level Critical Tech flag.
- The Critical Tech status in this note is derived from the current catalog and may change if the catalog is refreshed.
- `post_hire_daily_worker_dtls` contains multiple historical rows per employee. A daily snapshot must be selected using `airflow_execution_date`; employee-level comparisons must avoid mixing dates.
- The September 3 comment appears to correspond to a follow-up after the bulk September 1 reassignment. The data does not show a comparable bulk update on September 3.
