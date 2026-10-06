-- Hours away from manager: metadata-only external-source preflight.
--
-- Claim tested: HRDA metadata contains a candidate, effective-dated reference
-- that links an office/site identifier to approved travel duration or time-zone
-- information. No employee, site, postal, coordinate, or free-text values are
-- returned.
--
-- Acceptance rule: metadata must identify at least one effective-dated
-- office/site-to-travel or office/site-to-time-zone candidate. Before this can
-- confirm the feature source or definition, the source owner must separately
-- provide an approved business definition, units, routing/time-zone rules,
-- reference validity dates, and permitted employee-manager join keys.

WITH table_flags AS (
    SELECT
        table_name,
        MAX(CASE
            WHEN LOWER(column_name) LIKE '%office%'
              OR LOWER(column_name) LIKE '%site%'
              OR LOWER(column_name) LIKE '%work_location%'
              OR LOWER(column_name) LIKE '%work_site%'
            THEN 1 ELSE 0
        END) AS has_office_or_site_identifier,
        MAX(CASE
            WHEN LOWER(column_name) LIKE '%time_zone%'
              OR LOWER(column_name) LIKE '%timezone%'
            THEN 1 ELSE 0
        END) AS has_time_zone,
        MAX(CASE WHEN LOWER(column_name) LIKE '%travel%' THEN 1 ELSE 0 END) AS has_travel,
        MAX(CASE WHEN LOWER(column_name) LIKE '%commute%' THEN 1 ELSE 0 END) AS has_commute,
        MAX(CASE WHEN LOWER(column_name) LIKE '%distance%' THEN 1 ELSE 0 END) AS has_distance,
        MAX(CASE WHEN LOWER(column_name) LIKE '%latitude%' THEN 1 ELSE 0 END) AS has_latitude,
        MAX(CASE WHEN LOWER(column_name) LIKE '%longitude%' THEN 1 ELSE 0 END) AS has_longitude,
        MAX(CASE
            WHEN LOWER(column_name) IN (
                'employee_id', 'worker_id', 'worker_system_id',
                'employee_number', 'person_id', 'worker_unique_id'
            ) THEN 1 ELSE 0
        END) AS has_employee_identifier,
        MAX(CASE
            WHEN LOWER(column_name) LIKE '%effective%'
              OR LOWER(column_name) LIKE '%snapshot%'
              OR LOWER(column_name) LIKE '%as_of%'
              OR LOWER(column_name) LIKE '%date%'
            THEN 1 ELSE 0
        END) AS has_effective_or_snapshot_date
    FROM information_schema.columns
    WHERE table_schema = 'hrda'
    GROUP BY table_name
)
SELECT
    COUNT(*) AS hrda_tables_inspected,
    SUM(CASE
        WHEN has_office_or_site_identifier = 1
         AND has_time_zone = 1
        THEN 1 ELSE 0
    END) AS office_site_time_zone_candidates,
    SUM(CASE
        WHEN has_office_or_site_identifier = 1
         AND (has_travel = 1 OR has_commute = 1 OR has_distance = 1)
        THEN 1 ELSE 0
    END) AS office_site_travel_or_distance_candidates,
    SUM(CASE
        WHEN has_office_or_site_identifier = 1
         AND has_latitude = 1
         AND has_longitude = 1
         AND has_employee_identifier = 0
        THEN 1 ELSE 0
    END) AS non_employee_office_coordinate_reference_candidates,
    SUM(CASE
        WHEN has_office_or_site_identifier = 1
         AND has_latitude = 1
         AND has_longitude = 1
         AND has_employee_identifier = 1
        THEN 1 ELSE 0
    END) AS employee_scoped_coordinate_candidates,
    SUM(CASE
        WHEN has_office_or_site_identifier = 1
         AND has_time_zone = 1
         AND has_effective_or_snapshot_date = 1
        THEN 1 ELSE 0
    END) AS effective_dated_office_site_time_zone_candidates,
    SUM(CASE
        WHEN has_office_or_site_identifier = 1
         AND (has_travel = 1 OR has_commute = 1 OR has_distance = 1)
         AND has_effective_or_snapshot_date = 1
        THEN 1 ELSE 0
    END) AS effective_dated_office_site_travel_or_distance_candidates
FROM table_flags;
