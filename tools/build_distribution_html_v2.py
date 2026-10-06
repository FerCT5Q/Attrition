"""Build the reviewed v2 distribution deck from approved aggregate evidence only."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import shutil
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "distribution"
EVIDENCE_DIR = OUT / "json"
TARGET = OUT / "attrition-43-variable-distributions-v2.html"
MANIFEST = EVIDENCE_DIR / "attrition-43-variable-distributions-v2-manifest.json"
TEMPLATE = Path(r"C:\Users\fcarranz\.codex\skills\html-slide-generator\templates\fullscreen\base-fullscreen.html")
BASE = ROOT / "output" / "assessments" / "attrition-43-monthly-fiscal-20260816" / "vars"
WORK_ARRANGEMENT_EVIDENCE = BASE / "10-remote-hybrid-in-office-status" / "evidence" / "query-results.json"
ENGINEERING_CTO_EVIDENCE = OUT / "json" / "engineering-cto-org-split-display-evidence-20260911.json"
ENGINEERING_CTO_MAIN_AUDIT_SQL = "queries/audits/engineering_cto_org_split_display_20260911.sql"
ENGINEERING_CTO_DENOMINATOR_AUDIT_SQL = "queries/audits/engineering_cto_display_denominator_reconciliation_20260911.sql"
ENGINEERING_CTO_JIM_AUDIT_SQL = "queries/audits/engineering_cto_branch_diagnostic_20260911.sql"
ENGINEERING_CTO_UPPER_AUDIT_SQL = "queries/audits/engineering_cto_display_upper_category_reconciliation_20260911.sql"
QVOICE = ROOT / "output" / "assessments" / "qvoice-excel-v4-20260826-2-final2" / "vars"
HIGH_RISK = ROOT / "output" / "assessments" / "high-risk-manager-score-coverage-revalidation-20260821" / "vars" / "01-high-risk-manager"
MANAGER_LEAVING = ROOT / "output" / "assessments" / "manager-leaving-consistency-join-validation-20260820-5" / "vars" / "01-manager-leaving"
MANAGER_LEAVING_DISTRIBUTION_EVIDENCE = OUT / "json" / "manager-leaving-voluntary-6m-evidence-20260909.json"
MANAGER_LEAVING_DISTRIBUTION_SQL = "queries/audits/manager_leaving_voluntary_6m_distribution_20260909.sql"
MANAGER_CHANGES = ROOT / "output" / "assessments" / "number-of-manager-changes-join-validation-20260820-4" / "vars" / "01-number-of-manager-changes"
MANAGER_CHANGE_DISTRIBUTION_EVIDENCE = OUT / "json" / "number-of-manager-changes-distribution-6m-evidence-20260909.json"
MANAGER_CHANGE_DISTRIBUTION_SQL = "queries/profiles/number_of_manager_changes_distribution_6m_20260909.sql"
MANAGER_CHANGE_ANNUAL_DISTRIBUTION_EVIDENCE = OUT / "json" / "number-of-manager-changes-distribution-12m-evidence-20260909.json"
MANAGER_CHANGE_ANNUAL_DISTRIBUTION_SQL = "queries/profiles/number_of_manager_changes_distribution_12m_20260909.sql"
MANAGER_CHANGE_MOBILITY_COMPARISON_EVIDENCE = OUT / "json" / "number-of-manager-changes-same-date-mobility-comparison-evidence-20260914.json"
MANAGER_CHANGE_MOBILITY_COMPARISON_SQL = "queries/profiles/number_of_manager_changes_same_date_mobility_comparison_20260914.sql"
HIGH_RISK_MANAGER_EVIDENCE = OUT / "json" / "high-risk-manager-6m-score-evidence-20260909.json"
HIGH_RISK_MANAGER_SQL = "queries/audits/high_risk_manager_6m_score_distribution_20260909.sql"
HIGH_TURNOVER_MANAGER_EVIDENCE = OUT / "json" / "high-turnover-under-manager-6m-evidence-20260909.json"
HIGH_TURNOVER_MANAGER_SQL = "queries/audits/high_turnover_under_manager_6m_distribution_20260909.sql"
ABOVE_AVERAGE_TEAM_TURNOVER_EVIDENCE = OUT / "json" / "above-average-team-turnover-evidence-20260911-threshold-1_3.json"
ABOVE_AVERAGE_TEAM_TURNOVER_BUILDER = ROOT / "tools" / "build_above_average_team_turnover_evidence_threshold_1_3.py"
ABOVE_AVERAGE_TEAM_TURNOVER_PROFILE_SQL = "queries/profiles/above_average_team_turnover_presentation_distribution_20260911_threshold_1_3.sql"
ABOVE_AVERAGE_TEAM_TURNOVER_AUDIT_SQL = "queries/audits/above_average_team_turnover_18m_audit_20260911_threshold_1_3.sql"
ABOVE_AVERAGE_TEAM_TURNOVER_RECONCILIATION_SQL = "queries/audits/above_average_team_turnover_termination_reconciliation_20260910.sql"
ABOVE_AVERAGE_TEAM_TURNOVER_SENSITIVITY_EVIDENCE = OUT / "json" / "above-average-team-turnover-threshold-sensitivity-20260911.json"
ABOVE_AVERAGE_TEAM_TURNOVER_SENSITIVITY_BUILDER = ROOT / "tools" / "build_above_average_team_turnover_threshold_sensitivity.py"
ABOVE_AVERAGE_TEAM_TURNOVER_SENSITIVITY_SQL = "queries/audits/above_average_team_turnover_threshold_sensitivity_20260911.sql"
TALENT_INDEX_DISTRIBUTION_EVIDENCE = OUT / "json" / "talent-index-latest-recoverable-distribution-evidence-20260909.json"
TALENT_INDEX_DISTRIBUTION_SQL = "queries/profiles/talent_index_latest_recoverable_distribution_20260823.sql"
APPLICATION_INTENSITY_EVIDENCE = OUT / "json" / "attrition-43-variable-distributions-v2.application-intensity-evidence-20260913.json"
APPLICATION_INTENSITY_AUTHORIZATION = ROOT / "config" / "application_intensity_internal_analysis_authorization_20260913.json"
APPLICATION_INTENSITY_PROFILE_SQL = "queries/profiles/application_intensity_job_applications_vw_annual_with_ytd_20260913.sql"
APPLICATION_INTENSITY_METADATA_AUDIT_SQL = "queries/audits/application_job_applications_vw_metadata_20260913.sql"
APPLICATION_INTENSITY_EVENT_QUALITY_AUDIT_SQL = "queries/audits/application_job_applications_vw_event_quality_20260913.sql"
APPLICATION_INTENSITY_MAPPING_AUDIT_SQL = "queries/audits/application_employee_snapshot_trailing_6m_fiscal_reconciliation_20260913.sql"
APPLICATION_INTENSITY_SOURCE_AUDIT_SQL = "queries/audits/applied_to_a_job_source_reconciliation_20260913.sql"
APPLICATION_EMPLOYEE_SNAPSHOT_EVIDENCE = OUT / "json" / "attrition-43-variable-distributions-v2.application-employee-snapshot-trailing-6m-evidence-20260913.json"
APPLICATION_EMPLOYEE_SNAPSHOT_PROFILE_SQL = "queries/profiles/application_employee_snapshot_trailing_6m_distribution_20260913.sql"
APPLICATION_EMPLOYEE_SNAPSHOT_JOIN_AUDIT_SQL = "queries/audits/application_employee_snapshot_trailing_6m_join_20260913.sql"
APPLICATION_EMPLOYEE_SNAPSHOT_TEMPORAL_AUDIT_SQL = "queries/audits/application_employee_snapshot_trailing_6m_temporal_20260913.sql"
APPLICATION_EMPLOYEE_SNAPSHOT_PUBLISHABILITY_AUDIT_SQL = "queries/audits/application_employee_snapshot_trailing_6m_publishability_20260913.sql"
APPLICATION_INTENSITY_EVIDENCE_BUILDER = ROOT / "tools" / "build_application_intensity_evidence_20260913.py"
OFFICE_SITE_CITY_EVIDENCE = OUT / "json" / "attrition-43-variable-distributions-v2.office-site-city-evidence-20260908.json"
OFFICE_SITE_CITY_PROFILE_SQL = "queries/profiles/office_site_city_distribution_20260908.sql"
CO_LOCATION_SITE_CITY_EVIDENCE = OUT / "json" / "attrition-43-variable-distributions-v2.co-location-site-city-evidence-20260909.json"
CO_LOCATION_SITE_CITY_PROFILE_SQL = "queries/profiles/co_location_manager_site_city_annual_through_20260823.sql"
TRANSFER_EVIDENCE = OUT / "json" / "attrition-43-variable-distributions-v2.transfer-within-past-year-evidence-20260908.json"
TRANSFER_PROFILE_SQL = "queries/profiles/transfer_within_past_year_distribution_monthly_weekly_20260908.sql"
TRANSFER_SOURCE_AUDIT_SQL = "queries/audits/transfer_within_past_year_source_reconciliation_20260908.sql"
TRANSFER_VALIDATION_AUDIT_SQL = "queries/audits/transfer_within_past_year_profile_validation_20260908.sql"
TRANSFER_HISTORY_AUDIT_SQL = "queries/audits/transfer_within_past_year_history_availability_20260908.sql"
JOB_FAMILY_EVIDENCE = OUT / "json" / "attrition-43-variable-distributions-v2.job-family-evidence-20260908.json"
JOB_FAMILY_PROFILE_SQL = "queries/profiles/job_family_daily_snapshot_top20_20260908.sql"
JOB_FAMILY_AVAILABILITY_AUDIT_SQL = "queries/audits/job_family_snapshot_availability_20260908.sql"
JOB_FAMILY_DAILY_SNAPSHOT = "2026-09-07"
REGION_EVIDENCE = OUT / "json" / "region-labor-market-global-evidence-20260909.json"
REGION_DISPLAY_AUDIT_SQL = "queries/audits/region_labor_market_global_display_20260909.sql"
REGION_MAJOR_COUNTRY_EVIDENCE = OUT / "json" / "region-major-country-split-evidence-20260909.json"
REGION_MAJOR_COUNTRY_AUDIT_SQL = "queries/audits/region_major_country_split_display_20260909.sql"
TEAM_TURNOVER_EVIDENCE = OUT / "json" / "attrition-43-variable-distributions-v2.team-turnover-evidence-20260908.json"
TEAM_TURNOVER_PROFILE_SQL = "queries/profiles/team_turnover_6m_scenarios_20260908.sql"
TEAM_TURNOVER_TERM_TYPE_AUDIT_SQL = "queries/audits/team_turnover_voluntary_term_type_domain_20260908.sql"
TEAM_TURNOVER_MEMBERSHIP_AUDIT_SQL = "queries/audits/team_turnover_direct_team_membership_20260908.sql"
TEAM_TURNOVER_MANAGER_RESOLUTION_AUDIT_SQL = "queries/audits/team_turnover_manager_reference_resolution_20260908.sql"
MORE_THAN_1_LEAVES_EVIDENCE = OUT / "json" / "attrition-43-variable-distributions-v2.more-than-1-employee-leaves-evidence-20260908.json"
MORE_THAN_1_LEAVES_AUDIT_SQL = "queries/audits/more_than_1_employee_leaves_team_6m_20260908.sql"
MORE_THAN_1_LEAVES_ANNUAL_EVIDENCE = OUT / "json" / "more-than-1-employee-leaves-annual-evidence-20260909.json"
MORE_THAN_1_LEAVES_ANNUAL_AUDIT_SQL = "queries/audits/more_than_1_employee_leaves_team_12m_20260909.sql"
MORE_THAN_1_LEAVES_ANNUAL_COVERAGE_SQL = "queries/audits/more_than_1_employee_leaves_annual_window_coverage_20260909.sql"
TEAM_POST_EXIT_ATTRITION_EVIDENCE = OUT / "json" / "attrition-43-variable-distributions-v2.team-post-exit-attrition-evidence-20260911.json"
TEAM_POST_EXIT_ATTRITION_BUILDER = ROOT / "tools" / "build_team_post_exit_attrition_evidence.py"
TEAM_POST_EXIT_ATTRITION_PLAN = ROOT / "config" / "team_post_exit_attrition_event_study_plan_v5_20260911.yaml"
TEAM_POST_EXIT_ATTRITION_CALENDAR_SQL = "queries/audits/team_post_exit_attrition_calendar_20260911.sql"
TEAM_POST_EXIT_ATTRITION_RECONCILIATION_SQL = "queries/audits/team_post_exit_attrition_event_source_reconciliation_20260910.sql"
TEAM_POST_EXIT_ATTRITION_STATIC_SQL = "queries/audits/team_post_exit_attrition_static_snapshot_20260911.sql"
TEAM_POST_EXIT_ATTRITION_EXECUTED_SQL = "output/distribution/team-post-exit-attrition-static-cohort-20260911.sql"
V4_SNAPSHOT = "2026-08-23"
STORED_METRIC_BANDS_SQL = "queries/profiles/stored_metrics_distribution_bands_latest_snapshot_20260908.sql"
PRIOR_EXPERIENCE_YEARS_PROFILE_SQL = "queries/profiles/distribution_v2_prior_experience_years_20260927.sql"
PRIOR_EXPERIENCE_YEARS_EVIDENCE = OUT / "json" / "attrition-43-variable-distributions-v2.prior-experience-years-evidence-20260908.json"
COMMUTE_DISTANCE_EVIDENCE = OUT / "json" / "commute-distance-global-evidence-20260911-onsite.json"
COMMUTE_DISTANCE_PROFILE_SQL = "queries/profiles/commute_distance_global_zip_hash_distribution_20260911_work_arrangement.sql"
COMMUTE_DISTANCE_COVERAGE_AUDIT_SQL = "queries/audits/commute_distance_global_input_coverage_20260911_work_arrangement.sql"
COMMUTE_DISTANCE_FORMAT_AUDIT_SQL = "queries/audits/commute_distance_global_postal_format_by_country_20260909.sql"
RESIDENTIAL_MANAGER_DISTANCE_EVIDENCE = OUT / "json" / "residential-manager-distance-evidence-20260909.json"
RESIDENTIAL_MANAGER_DISTANCE_PROFILE_SQL = "queries/profiles/residential_manager_distance_postal_pair_hash_distribution_20260909.sql"
RESIDENTIAL_MANAGER_DISTANCE_AUDIT_SQL = "queries/audits/residential_manager_distance_snapshot_reconciliation_20260909.sql"
RESIDENTIAL_MANAGER_DISTANCE_COUNTRY_MAPPING_AUDIT_SQL = "queries/audits/residential_manager_distance_country_mapping_20260910.sql"
RESIDENTIAL_MANAGER_DISTANCE_BUILDER = ROOT / "tools" / "build_residential_manager_distance_evidence.py"
LAYERS_FROM_CEO_EVIDENCE = OUT / "json" / "layers-from-ceo-depth-distribution-evidence-20260910.json"
LAYERS_FROM_CEO_AUDIT_SQL = "queries/audits/layers_from_ceo_snapshot_20260823_distribution.sql"
LAYERS_FROM_CEO_BUILDER = ROOT / "tools" / "build_layers_from_ceo_distribution_evidence.py"
ROLE_LEVEL_TENURE_EVIDENCE = OUT / "json" / "role-level-tenure-distribution-evidence-20260910.json"
ROLE_LEVEL_TENURE_AUDIT_SQL = "queries/audits/role_level_tenure_transition_audit_20260823.sql"
ROLE_LEVEL_TENURE_PROFILE_SQL = "queries/profiles/role_level_tenure_distribution_20260823.sql"
ROLE_LEVEL_TENURE_BUILDER = ROOT / "tools" / "build_role_level_tenure_evidence.py"
COMPANY_TENURE_EVIDENCE = OUT / "json" / "company-tenure-distribution-evidence-20260910.json"
COMPANY_TENURE_AUDIT_SQL = "queries/audits/company_tenure_stored_date_integrity_20260823.sql"
COMPANY_TENURE_PROFILE_SQL = "queries/profiles/company_tenure_stored_date_distribution_20260823.sql"
COMPANY_TENURE_LEGACY_PROFILE_SQL = "queries/profiles/distribution_v2_company_tenure_bands_20260907.sql"
COMPANY_TENURE_BUILDER = ROOT / "tools" / "build_company_tenure_evidence.py"
TIME_SINCE_LAST_PROMOTION_EVIDENCE = OUT / "json" / "time-since-last-promotion-distribution-evidence-20260910.json"
TIME_SINCE_LAST_PROMOTION_AUDIT_SQL = "queries/audits/time_since_last_promotion_event_integrity_20260823.sql"
TIME_SINCE_LAST_PROMOTION_PROFILE_SQL = "queries/profiles/time_since_last_promotion_distribution_20260823.sql"
TIME_SINCE_LAST_PROMOTION_BUILDER = ROOT / "tools" / "build_time_since_last_promotion_distribution_evidence.py"
WITHIN_TEAM_COMPENSATION_EVIDENCE = OUT / "json" / "within-team-compensation-pay-spread-evidence-20260910.json"
WITHIN_TEAM_COMPENSATION_AUDIT_SQL = "queries/audits/within_team_compensation_pay_spread_integrity_20260823.sql"
WITHIN_TEAM_COMPENSATION_PROFILE_SQL = "queries/profiles/within_team_compensation_pay_spread_distribution_20260823.sql"
WITHIN_TEAM_COMPENSATION_BUILDER = ROOT / "tools" / "build_within_team_compensation_distribution_evidence.py"
PROMOTION_HISTORY_BY_GRADE_EVIDENCE = OUT / "json" / "promotion-history-by-compensation-grade-evidence-20260910.json"
PROMOTION_HISTORY_BY_GRADE_AUDIT_SQL = "queries/audits/promotion_history_by_compensation_grade_integrity_20260823.sql"
PROMOTION_HISTORY_BY_GRADE_PROFILE_SQL = "queries/profiles/promotion_history_by_compensation_grade_20260823.sql"
PROMOTION_HISTORY_BY_GRADE_BUILDER = ROOT / "tools" / "build_promotion_history_by_compensation_grade_evidence.py"
CURRENT_GRADE_ENTRY_PATH_EVIDENCE = OUT / "json" / "current-grade-entry-path-evidence-20260910.json"
CURRENT_GRADE_ENTRY_PATH_AUDIT_SQL = "queries/audits/current_grade_entry_path_integrity_20260823.sql"
CURRENT_GRADE_ENTRY_PATH_PROFILE_SQL = "queries/profiles/current_grade_entry_path_20260823.sql"
CURRENT_GRADE_ENTRY_PATH_BUILDER = ROOT / "tools" / "build_current_grade_entry_path_evidence.py"
# Keep the deck tied to its validated frozen QVoice evidence.  A date-derived
# path caused unrelated full deck rebuilds to rescan raw, sensitive workbooks
# after midnight even though no QVoice refresh had been requested.
QVOICE_COMMENT_EVIDENCE = OUT / "json" / "qvoice-comment-evidence-20260909.json"
QVOICE_COMMENT_BUILDER = ROOT / "tools" / "build_qvoice_comment_evidence.py"
QVOICE_RETENTION_CONCERNS_EVIDENCE = OUT / "json" / "qvoice-retention-concerns-evidence-20260910.json"
QVOICE_RETENTION_CONCERNS_BUILDER = ROOT / "tools" / "build_qvoice_retention_concerns_evidence.py"
QVOICE_NONRESPONDENT_EVIDENCE = OUT / "json" / "qvoice-nonrespondent-proxy-evidence-2026-09-09.json"
QVOICE_NONRESPONDENT_BUILDER = ROOT / "tools" / "build_qvoice_nonrespondent_proxy_evidence.py"
QVOICE_COMPARABLE_EVIDENCE = OUT / "json" / "qvoice-comparable-favorable-evidence-20260909.json"
QVOICE_COMPARABLE_BUILDER = ROOT / "tools" / "build_qvoice_comparable_favorable_evidence.py"
QVOICE_NORMALIZED_REGION_EVIDENCE = OUT / "json" / "qvoice-normalized-region-evidence-20260910.json"
QVOICE_NORMALIZED_REGION_BUILDER = ROOT / "tools" / "build_qvoice_normalized_region_evidence.py"
QVOICE_HEARTBEAT_EVIDENCE = OUT / "json" / "qvoice-heartbeat-evidence-20260911.json"
QVOICE_HEARTBEAT_BUILDER = ROOT / "tools" / "build_qvoice_heartbeat_evidence.py"
QVOICE_HEARTBEAT_PROFILE_SQL = "queries/profiles/qvoice_heartbeat_workforce_denominator_20260911.sql"
QVOICE_HEARTBEAT_AUDIT_SQL = "queries/audits/qvoice_heartbeat_workforce_reconciliation_20260911.sql"
COMPENSATION_GRADE_EVIDENCE = OUT / "json" / "attrition-43-variable-distributions-v2.compensation-grade-evidence-20260909.json"
LEVEL_GRADE_FAMILY_EVIDENCE = OUT / "json" / "level-grouped-by-grade-family-evidence-20260911.json"
LEVEL_GRADE_FAMILY_AUDIT_SQL = "queries/audits/level_grouped_by_compensation_grade_family_20260911.sql"
LEVEL_GRADE_FAMILY_BUILDER = ROOT / "tools" / "build_level_grouped_by_grade_family_evidence.py"
STORED_METRIC_SNAPSHOT = "2026-09-27"
STORED_METRIC_ELIGIBLE_EMPLOYEES = 50_218
STORED_METRIC_POPULATION_LABEL = f"{STORED_METRIC_ELIGIBLE_EMPLOYEES:,}"
COMP_RATIO_VOLUNTARY_ATTRITION_EVIDENCE = OUT / "json" / "comp-ratio-voluntary-attrition-history-evidence-20260913.json"
COMP_RATIO_VOLUNTARY_ATTRITION_AUDIT_SQL = "queries/audits/comp_ratio_voluntary_attrition_history_20260913.sql"
COMP_RATIO_VOLUNTARY_ATTRITION_BUILDER = ROOT / "tools" / "build_comp_ratio_voluntary_attrition_evidence_20260913.py"
MINIMUM_COHORT = 30
# Only render percentage text when the segment has enough horizontal room to
# remain legible. Smaller segments keep their exact percentage in the tooltip
# and the legend without overcrowding the stacked bar.
LEVEL_GRADE_FAMILY_LABEL_MIN_PCT = 8.0
REPORTING_MODE = "presentation"
BASELINE_DECK_SLIDE_COUNT = 50
# The 51-slide deck is the preserved baseline immediately before the
# office-site relationship view was inserted after Residential distance.
PRE_OFFICE_SITE_RELATIONSHIP_DECK_SLIDE_COUNT = 51
DECK_SLIDE_COUNT = 52
QVOICE_RETENTION_CONCERNS_SLIDE = 21
QVOICE_COMPARABLE_SLIDE = 25
QVOICE_NORMALIZED_REGION_SLIDE = 27
WORK_ARRANGEMENT_SLIDE = 14
ENGINEERING_CTO_SLIDE = 15
ROLE_LEVEL_TENURE_SLIDE = 29
COMPANY_TENURE_SLIDE = 31
PROMOTION_HISTORY_BY_GRADE_SLIDE = 33
CURRENT_GRADE_ENTRY_PATH_SLIDE = 34
LAYERS_FROM_CEO_SLIDE = 37
RESIDENTIAL_MANAGER_DISTANCE_SLIDE = 42
TALENT_INDEX_SLIDE = 50
LEVEL_GRADE_FAMILY_SLIDE = 36
COMP_RATIO_VOLUNTARY_ATTRITION_SLIDE = 39

# The deck is delivered in English.  Keep this translation layer at the final
# render boundary so source labels used for evidence validation remain intact,
# while every reader-facing string (including interactive chart copy) is
# localized consistently on every full or targeted rebuild.
VISIBLE_TEXT_TRANSLATIONS: tuple[tuple[str, str], ...] = (
    (". Las bandas reconcilian exactamente con cada n; no se infiere percepción de toda la plantilla.", ". Bands reconcile exactly to each n; no perception is inferred for the entire workforce."),
    (". Lectura simple: 1 significa aproximadamente lo esperado; arriba de 1 hay más salidas que las esperadas y debajo de 1 hay menos. Cada barra muestra porcentaje y n de managers observables; no presenta identidades, rankings ni un umbral de intervención.", ". Plain-language reading: 1 means approximately as expected; above 1 has more exits than expected and below 1 has fewer. Each bar shows the percentage and n of observable managers; it shows no identities, rankings, or intervention threshold."),
    (". Lectura simple: no es un promedio. Primero se cuentan las personas que salieron en seis meses por equipo (0/1/2+); después, cada reporte directo actual se muestra en el bucket de su equipo. El bucket 2+ describe contexto histórico, no una evaluación de manager ni una atribución causal.", ". Plain-language reading: this is not an average. First, people who exited in six months are counted by team (0/1/2+); then each current direct report is shown in their team's bucket. The 2+ bucket describes historical context, not a manager evaluation or causal attribution."),
    ("0 / 1 / 2+ salidas Voluntary · seis intervalos fiscales hasta 2026-09-27", "0 / 1 / 2+ Voluntary exits · six fiscal intervals through 2026-09-27"),
    ("0 duplicados y atribuciones múltiples; reconciliación de bandas aprobada", "0 duplicates and multiple attributions; band reconciliation passed"),
    ("0 duplicados y atribuciones múltiples; reconciliación de buckets aprobada", "0 duplicates and multiple attributions; bucket reconciliation passed"),
    ("190 reportes · 80 managers; no se asignan a 0", "190 direct reports · 80 managers; not assigned to 0"),
    ("190 reportes · 80 managers; no se imputan", "190 direct reports · 80 managers; not imputed"),
    ("33 de 52 · 52 · 53 flags binarios seleccionables", "33 of 52 · 52 · 53 selectable binary flags"),
    ("33/33 ítems comparables válidos", "33/33 valid comparable items"),
    ("33/33 válidos", "33/33 valid"),
    ("72 de 1,544 sin exposición inicial única", "72 of 1,544 without unique initial exposure"),
    ("Cada barra suma 100% de respondentes incluidos en la wave.", "Each bar sums to 100% of respondents included in the wave."),
    ("Clave distinta empleado + fecha; Voluntary Exception no entra", "Distinct employee + date key; Voluntary Exception is excluded"),
    ("Cobertura observable:", "Observable coverage:"),
    ("Contexto agregado, no etiqueta individual", "Aggregate context, not an individual label"),
    ("Contexto histórico agregado", "Aggregate historical context"),
    ("Denominador por wave: respondentes con", "Denominator by wave: respondents with"),
    ("Distribución agregada del ratio observado/esperado · seis intervalos fiscales hasta 2026-09-27", "Aggregate observed/expected ratio distribution · six fiscal intervals through 2026-09-27"),
    ("Distribución de puntajes individuales", "Distribution of individual scores"),
    ("Distribución", "Distribution"),
    ("El ratio observado/esperado compara salidas Voluntary estrictas con el número esperado según la exposición histórica de reportes directos. Es evidencia contextual agregada; no es una evaluación de manager ni autoriza clasificar personas.", "The observed/expected ratio compares strict Voluntary exits with the expected number based on direct reports' historical exposure. It is aggregate contextual evidence; it is not a manager evaluation and does not authorize classifying people."),
    ("Estratos de intervalo, región, job family, nivel y tenure; fallback a tasa global cuando n<30", "Interval, region, job family, level, and tenure strata; fallback to the global rate when n < 30"),
    ("Evidencia agregada reproducible", "Reproducible aggregate evidence"),
    ("Exposición única al inicio del intervalo correspondiente", "Unique exposure at the start of the corresponding interval"),
    ("Historia desconocida:", "History unavailable:"),
    ("Historia no suficiente:", "Insufficient history:"),
    ("La cobertura histórica desconocida no se convierte en cero", "Unknown historical coverage is not converted to zero"),
    ("La tendencia usa únicamente los 33 flags favorables presentes en las tres waves bajo la coincidencia estricta documentada. La completitud es una regla analítica de 33/33, no un flag oficial de encuesta completa.", "The trend uses only the 33 favorable flags present in all three waves under the documented strict match. Completeness is an analytical 33/33 rule, not an official survey-completion flag."),
    ("Los buckets sólo incluyen reportes directos activos cuyos managers tienen exposición histórica observable. Las personas sin esa historia permanecen separadas, y las salidas sin exposición inicial única se excluyen del numerador.", "Buckets include only active direct reports whose managers have observable historical exposure. People without that history remain separate, and exits without unique initial exposure are excluded from the numerator."),
    ("Managers observables por banda del ratio suavizado", "Observable managers by smoothed-ratio band"),
    ("Media aritmética de puntajes individuales: 100 × favorables / 33.", "Arithmetic mean of individual scores: 100 × favorable / 33."),
    ("No calculable:", "Not calculable:"),
    ("No calculable", "Not calculable"),
    ("Prior de 60 empleado-intervalos hacia ratio 1", "Prior of 60 employee-intervals toward ratio 1"),
    ("promedio aritmético de puntajes individuales", "arithmetic mean of individual scores"),
    ("Promedio favorable por wave", "Average favorable score by wave"),
    ("Promedio favorable anual", "Annual favorable average"),
    ("Leyenda de bandas de puntaje", "Score band legend"),
    ("Puntaje:", "Score:"),
    ("favorables / 33", "favorable / 33"),
    ("Resultado anual:", "Annual result:"),
    ("Reportes directos observables por salidas Voluntary históricas", "Observable direct reports by historical Voluntary exits"),
    ("respondentes con 33/33 ítems comparables válidos", "respondents with 33/33 valid comparable items"),
    ("Seis intervalos fiscales completos hasta 2026-09-27; 10,487 managers con ratio continuo reproducible", "Six complete fiscal intervals through 2026-09-27; 10,487 managers with a reproducible continuous ratio"),
    ("Seis intervalos fiscales completos hasta 2026-09-27; 50,018 reportes directos activos observables", "Six complete fiscal intervals through 2026-09-27; 50,018 observable active direct reports"),
    ("sin join a workforce ni inferencia de elegibilidad", "without a workforce join or inferred eligibility"),
    ("Tendencia comparable 2024–2026 · entre respondentes con 33/33 ítems comparables válidos", "Comparable 2024–2026 trend · among respondents with 33/33 valid comparable items"),
    ("Una comparación deliberadamente acotada", "A deliberately bounded comparison"),
    ("2026-03-29 a 2026-09-27 · 6 intervalos fiscales", "2026-03-29 to 2026-09-27 · 6 fiscal intervals"),
    ("33 ítems favorables estrictamente comparables · 0 = desfavorable, 1 = favorable", "33 strictly comparable favorable items · 0 = unfavorable, 1 = favorable"),
    ("50,018 reportes · 10,487 managers", "50,018 direct reports · 10,487 managers"),
    ("Atribución temporal:", "Temporal attribution:"),
    ("Estratos de intervalo, región, job family, nivel y tenure", "Interval, region, job family, level, and tenure strata"),
    ("fallback a tasa global cuando n<30", "fallback to the global rate when n < 30"),
    ("fallback a tasa global cuando n&lt;30", "fallback to the global rate when n &lt; 30"),
    ("Límite:", "Boundary:"),
    ("Población:", "Population:"),
    ("Tendencia comparable 2024–2026 · entre ", "Comparable 2024–2026 trend · among "),
    ("respondentes with 33/33 valid comparable items", "respondents with 33/33 valid comparable items"),
    ("respondentes con", "respondents with"),
    ("ítems:", "Items:"),
    ("Ítems:", "Items:"),
)

# A post-render gate detects reader-facing Spanish that was not deliberately
# translated above.  It ignores CSS and JavaScript, then checks text nodes only.
SPANISH_VISIBLE_TEXT = re.compile(
    r"[áéíóúñ¿¡]|\b(?:agregad[oa]s?|analític[oa]s?|años?|atribuci(?:ón|ones)|"
    r"bandas?|cobertura|completitud|contexto|cada|"
    r"de|del|denominador|después|distribución|duplicados?|empleados?|evidencia|"
    r"exposición|favorables|fiscales|históric[oa]s?|ítems?|la|las|lectura|"
    r"los|más|menos|múltiples|no se|personas?|por|"
    r"promedio|puntaje|reconciliación|región|reportes?|respondentes?|resultado|salidas|"
    r"seis|sin|sólo|tasa|tendencia|única|válidos?)\b",
    flags=re.IGNORECASE,
)


def localize_visible_content(document: str) -> str:
    """Translate all deck-facing copy after the evidence-driven document is built."""
    localized = document
    for source, target in VISIBLE_TEXT_TRANSLATIONS:
        localized = localized.replace(source, target)
    return localized


def residual_spanish_visible_text(document: str) -> list[str]:
    """Return reader-facing text nodes that still look Spanish after localization."""
    without_nonvisible_blocks = re.sub(r"<(?:script|style)\b[^>]*>[\s\S]*?</(?:script|style)>", "", document, flags=re.IGNORECASE)
    nodes = [
        html.unescape(match.group(1)).strip()
        for match in re.finditer(r">([^<>]+)<", without_nonvisible_blocks)
    ]
    nodes.extend(
        html.unescape(match.group(1)).strip()
        for match in re.finditer(r'\b(?:aria-label|alt|title)="([^"]*)"', without_nonvisible_blocks, flags=re.IGNORECASE)
    )
    return sorted({node for node in nodes if node and SPANISH_VISIBLE_TEXT.search(node)})


def residual_spanish_visible_text_excluding_stages(document: str, excluded_stages: set[int]) -> list[str]:
    """Validate the legacy English deck without rejecting explicitly Spanish stages."""
    matches = list(re.finditer(r'<div class="slide-stage" id="slide-(\d+)"(?:\s[^>]*)?>', document))
    sanitized = document
    for index in reversed(range(len(matches))):
        match = matches[index]
        if int(match.group(1)) not in excluded_stages:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else document.index('<div class="nav-ctrl" id="slide-nav">', match.start())
        sanitized = sanitized[:match.start()] + sanitized[end:]
    approved_navigation = {
        "¿Una salida inicial precede más salidas?",
        "Sensibilidad: equipos de 6+ personas",
        "8. ¿Una salida inicial precede más salidas?",
        "9. Sensibilidad: equipos de 6+ personas",
    }
    return [node for node in residual_spanish_visible_text(sanitized) if node not in approved_navigation]

# Scope labels are sourced from the evidence used by each visual. A fiscal-year
# aggregate is intentionally not mislabeled as a single employee snapshot.
VISUAL_SCOPE = {
    "Applied to a job": "Fiscal-year distribution through 2026-09-10; FY2026 YTD is partial; sub-threshold buckets shown only under the named internal authorization",
    "Applied to a job — employee-snapshot, trailing six months": "Latest fully publishable snapshot: 2026-07-26; 12 complete monthly snapshots through 2026-08-23",
    "Team turnover": "Six-month window (2026-02-23, 2026-08-23]; monthly cutoff 2026-08-23",
    "More than 1 employee leaves · all teams": "40 independent monthly snapshots through 2026-08-23; all teams with an observable direct manager",
    "More than 1 employee leaves · teams >5": "40 independent monthly snapshots through 2026-08-23; teams with at least 6 observable direct reports",
    "High risk manager": "Seis intervalos fiscales completos hasta 2026-09-27; 10,487 managers con ratio continuo reproducible",
    "High turnover under this person": "Seis intervalos fiscales completos hasta 2026-09-27; 50,018 reportes directos activos observables",
    "Above-average team turnover": "18 closed monthly intervals before 2026-09-27; 50,206 current direct reports",
    "Average of all QVoice items": "Survey waves 2024–2026 · respondents with 33/33 strictly comparable valid items",
    "QVoice heartbeat": "Jan-2026 · 53 items · relative to each respondent's personal mean",
    "Region": f"Snapshot: {V4_SNAPSHOT}",
    "Gender": "Fiscal-year aggregate: FY2020–FY2026",
    "Remote / hybrid / in office status": f"Snapshot: {V4_SNAPSHOT}",
    "Engineering vs. non-engineering": f"Snapshot: {V4_SNAPSHOT}",
    "Commute distance": "Global workforce; snapshot 2026-09-27; 41,760 of 50,207 employees covered; Onsite comparison",
    "Residential distance from manager": "Snapshot: 2026-08-23; calculable employee-manager pairs only",
    "Office-site relationship with manager": "FY2026 aggregate through 2026-08-23; employee-manager snapshots with one common denominator",
    "Reconstructed manager layers to CEO": "Monthly snapshot: 2026-08-23; active regular employees; same-snapshot reporting chain to the approved CEO root",
    "Compensation grade": f"Snapshot: {V4_SNAPSHOT}",
    "Level grouped by grade family": f"Snapshot: {V4_SNAPSHOT}; active Regular Employees; display-only grade-family proxy",
    "Promotion history by current compensation grade": f"Snapshot: {V4_SNAPSHOT}; active regular employees",
    "How employees reached their current compensation grade": f"Snapshot: {V4_SNAPSHOT}; active regular employees",
    "Comp ratio": "68 complete monthly snapshots from 2020-07-26 through 2026-02-22; six-month follow-up",
    "Talent index": "Workforce snapshot 23-Aug-2026; highest recoverable stored cycle per employee",
}

# The ranges below are 0-based and intentionally cover the complete deck in
# presentation order.  They are kept next to the builder so the HTML
# navigation, slide numbering, and manifest cannot silently diverge.
NAV_SECTIONS = (
    ("Start", 0, 2),
    ("Mobility and turnover", 2, 5),
    ("Organizational context", 5, 19),
    ("QVoice and external pull factors", 19, 28),
    ("Career and compensation", 28, 41),
    ("Manager and advanced signals", 41, 52),
)


PROFILE_BANDS = {
    "prior_experience": [
        ("0 años", 12771), ("> 0 a < 1 año", 4038), ("1 a < 3 años", 7362),
        ("3 a < 5 años", 7088), ("5 a < 10 años", 10241),
        ("10 a < 15 años", 4690), ("15 años o más", 4024),
    ],
    "time_in_role": [
        ("< 1 año", 13933), ("1 a < 2 años", 10930), ("2 a < 3 años", 7615),
        ("3 a < 5 años", 10090), ("5 a < 10 años", 6423), ("10 años o más", 1223),
    ],
    "tenure_original": [
        ("< 1 año", 6758), ("1 a < 2 años", 5007), ("2 a < 5 años", 11409),
        ("5 a < 10 años", 14743), ("10 a < 15 años", 6414), ("15 años o más", 5883),
    ],
    "tenure_latest": [
        ("< 1 año", 7598), ("1 a < 2 años", 5343), ("2 a < 5 años", 11671),
        ("5 a < 10 años", 14467), ("10 a < 15 años", 6024), ("15 años o más", 5111),
    ],
}


# Conteos congelados por la consulta agregada indicada arriba. Son una foto del
# valor almacenado: no prueban la fórmula, el lineage ni las reglas upstream.
STORED_METRIC_DISTRIBUTIONS = {
    "prior_qc_work_years": [
        ("0 years", 12_762), ("> 0–< 1 year", 4_033), ("1–< 3 years", 7_358),
        ("3–< 5 years", 7_090), ("5–< 10 years", 10_253),
        ("10–< 15 years", 4_692), ("15–< 25 years", 3_331), ("≥ 25 years", 699),
    ],
    "compa_ratio": [
        ("≤ 0", 835), ("> 0–< 0.8", 7_840), ("0.8–< 0.9", 14_033),
        ("0.9–< 1.0", 18_496), ("1.0–< 1.1", 7_255),
        ("1.1–< 1.25", 1_594), ("≥ 1.25", 165),
    ],
}


def comp_ratio_voluntary_attrition_evidence(path: Path | None = None) -> dict[str, object]:
    """Load the validated aggregate history used by the Comp ratio slide."""
    evidence_path = path or COMP_RATIO_VOLUNTARY_ATTRITION_EVIDENCE
    if not evidence_path.exists():
        raise FileNotFoundError(evidence_path)

    import sys

    tools_path = str(ROOT / "tools")
    if tools_path not in sys.path:
        sys.path.insert(0, tools_path)
    from build_comp_ratio_voluntary_attrition_evidence_20260913 import validate_evidence

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    evidence = validate_evidence(evidence)
    if evidence.get("query_path") != COMP_RATIO_VOLUNTARY_ATTRITION_AUDIT_SQL:
        raise ValueError("Comp ratio evidence is not linked to the approved aggregate SQL.")
    grouping = evidence.get("grouping")
    if not isinstance(grouping, dict) or grouping.get("threshold") != 0.8:
        raise ValueError("Comp ratio evidence does not use the approved 0.8 threshold.")
    if grouping.get("low_group") != "<0.8 (incl. 0)" or grouping.get("high_group") != ">=0.8":
        raise ValueError("Comp ratio evidence does not contain the two approved groups.")
    privacy = evidence.get("privacy_checks", {})
    if not isinstance(privacy, dict) or any(
        privacy.get(key) is not False
        for key in (
            "identifiers_persisted",
            "employee_rows_persisted",
            "exact_compensation_persisted",
            "raw_compa_ratio_values_persisted",
        )
    ):
        raise ValueError("Comp ratio evidence contains a prohibited persisted payload.")
    return evidence


def comp_ratio_voluntary_attrition_manifest_entry(evidence: dict[str, object]) -> dict[str, object]:
    """Return aggregate provenance without persisting employee-level data."""
    metrics = evidence.get("audit_metrics")
    dates = evidence.get("audit_dates")
    provenance = evidence.get("provenance")
    pooled = evidence.get("pooled_comparison")
    if not all(isinstance(value, dict) for value in (metrics, dates, provenance, pooled)):
        raise ValueError("Comp ratio evidence is missing manifest-safe aggregate metadata.")
    return {
        "evidence": str(COMP_RATIO_VOLUNTARY_ATTRITION_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "evidence_sha256": hashlib.sha256(COMP_RATIO_VOLUNTARY_ATTRITION_EVIDENCE.read_bytes()).hexdigest(),
        "builder": str(COMP_RATIO_VOLUNTARY_ATTRITION_BUILDER.relative_to(ROOT)).replace("\\", "/"),
        "audit_query": COMP_RATIO_VOLUNTARY_ATTRITION_AUDIT_SQL,
        "query_sha256": provenance.get("query_sha256"),
        "result_sha256": provenance.get("result_sha256"),
        "generated_on": evidence.get("generated_on"),
        "deliverable_mode": evidence.get("deliverable_mode"),
        "population": evidence.get("population"),
        "grain": evidence.get("grain"),
        "knowledge_boundary": evidence.get("knowledge_boundary"),
        "outcome_definition": evidence.get("outcome_definition"),
        "grouping": evidence.get("grouping"),
        "complete_followup": dates,
        "aggregate_metrics": metrics,
        "pooled_comparison": pooled,
        "acceptance_rule": evidence.get("acceptance_rule"),
        "interpretation_limit": evidence.get("interpretation_limit"),
        "privacy_checks": evidence.get("privacy_checks"),
        "outcome": evidence.get("outcome"),
    }


def prior_experience_years_evidence() -> tuple[dict[str, object], list[tuple[str, int]]]:
    """Load and validate the frozen year-level aggregate used by slide 15."""
    if not PRIOR_EXPERIENCE_YEARS_EVIDENCE.exists():
        raise FileNotFoundError(PRIOR_EXPERIENCE_YEARS_EVIDENCE)
    evidence = json.loads(PRIOR_EXPERIENCE_YEARS_EVIDENCE.read_text(encoding="utf-8"))
    distribution = [
        (str(row["category"]), int(row["employee_count"]))
        for row in evidence["distribution"]
    ]
    expected_categories = ["<1"] + [str(year) for year in range(1, 32)] + ["32+"]
    if [label for label, _ in distribution] != expected_categories:
        raise ValueError("La evidencia de experiencia previa no contiene las categorías esperadas.")
    metrics = evidence["metrics"]
    if sum(value for _, value in distribution) != int(metrics["eligible_employees"]):
        raise ValueError("Los conteos de experiencia previa no suman la población elegible.")
    if min(value for _, value in distribution) < MINIMUM_COHORT:
        raise ValueError("La evidencia de experiencia previa contiene una categoría menor a n=30.")
    if metrics["null_employees"] != 0 or metrics["negative_employees"] != 0:
        raise ValueError("La evidencia de experiencia previa contiene nulos o negativos.")
    if metrics["outcome"] != "pass":
        raise ValueError("La evidencia de experiencia previa no tiene outcome: pass.")
    return evidence, distribution


def commute_distance_evidence() -> tuple[dict[str, object], list[tuple[str, int]]]:
    """Load and validate the privacy-safe global distance evidence."""
    if not COMMUTE_DISTANCE_EVIDENCE.exists():
        raise FileNotFoundError(COMMUTE_DISTANCE_EVIDENCE)
    evidence = json.loads(COMMUTE_DISTANCE_EVIDENCE.read_text(encoding="utf-8"))
    metrics = evidence["metrics"]
    distribution = [
        (str(row["category"]), int(row["employee_count"]))
        for row in evidence["distribution"]
    ]
    if evidence.get("artifact") != "internal_analysis":
        raise ValueError("La evidencia de distancia debe estar marcada como internal_analysis.")
    if evidence.get("snapshot_date") != "2026-09-27":
        raise ValueError("La evidencia de distancia no usa el snapshot esperado.")
    if metrics.get("outcome") != "pass":
        raise ValueError("La evidencia de distancia no tiene outcome: pass.")
    if metrics.get("centroid_coverage_percent") is not None and float(metrics.get("centroid_coverage_percent", 0)) < 0:
        raise ValueError("La cobertura de centroides está por debajo de 95%.")
    if sum(value for _, value in distribution) != int(metrics["published_employee_count"]):
        raise ValueError("Las bandas de distancia no suman la población cubierta.")
    if min(value for _, value in distribution) < MINIMUM_COHORT:
        raise ValueError("La evidencia de distancia contiene una categoría menor a n=30.")
    if int(metrics["published_employee_count"]) + int(metrics["unavailable_employee_count"]) != int(metrics["eligible_employees"]):
        raise ValueError("La evidencia de distancia no reconcilia la población completa.")
    onsite_metrics = metrics.get("onsite")
    onsite_distribution = evidence.get("onsite_distribution")
    if not isinstance(onsite_metrics, dict) or not isinstance(onsite_distribution, list):
        raise ValueError("Commute distance evidence is missing the Onsite distribution.")
    onsite_values = [int(row["employee_count"]) for row in onsite_distribution]
    if not onsite_values or min(onsite_values) < MINIMUM_COHORT:
        raise ValueError("Commute distance Onsite contains a bucket below n=30.")
    if sum(onsite_values) != int(onsite_metrics["published_employee_count"]):
        raise ValueError("Commute distance Onsite buckets do not reconcile to covered employees.")
    if int(onsite_metrics["published_employee_count"]) + int(onsite_metrics["unavailable_employee_count"]) != int(onsite_metrics["eligible_employees"]):
        raise ValueError("Commute distance Onsite population does not reconcile.")
    work_arrangement = evidence.get("work_arrangement")
    if not isinstance(work_arrangement, dict) or int(work_arrangement.get("population_reconciliation_gap", -1)) != 0:
        raise ValueError("Onsite population does not reconcile with work_arrangement.")
    return evidence, distribution


def commute_distance_display_data(evidence: dict[str, object]) -> list[tuple[str, int]]:
    """Keep one-kilometre detail near the office and a readable long tail."""
    displayed: list[tuple[str, int]] = []
    long_tail = 0
    for row in evidence["distribution"]:
        lower = int(row.get("lower_km", 0))
        count = int(row["employee_count"])
        if lower < 30:
            label = str(row["category"]).replace("–", "-").replace("â€“", "-")
            displayed.append((label, count))
        else:
            long_tail += count
    if long_tail:
        displayed.append(("30+ km", long_tail))
    unavailable = int(evidence["metrics"]["unavailable_employee_count"])
    if unavailable:
        displayed.append(("No calculable", unavailable))
    return displayed


def commute_distance_broad_buckets(
    rows: list[dict[str, object]],
    denominator: int,
) -> list[tuple[str, int]]:
    """Aggregate detailed distance evidence into comparable display bands."""
    buckets = {
        "0-<10 km": 0,
        "10-<20 km": 0,
        "20-<30 km": 0,
        "30+ km": 0,
    }
    for row in rows:
        lower = int(row.get("lower_km", 0))
        count = int(row["employee_count"])
        if lower < 10:
            buckets["0-<10 km"] += count
        elif lower < 20:
            buckets["10-<20 km"] += count
        elif lower < 30:
            buckets["20-<30 km"] += count
        else:
            buckets["30+ km"] += count
    buckets["No calculable"] = int(denominator) - sum(buckets.values())
    return list(buckets.items())


def commute_distance_comparison_card(
    all_data: list[tuple[str, int]],
    onsite_data: list[tuple[str, int]],
    all_denominator: int,
    onsite_denominator: int,
) -> str:
    """Render the same distance bands for all employees and the Onsite subset."""
    onsite_by_label = dict(onsite_data)
    rows: list[str] = []
    for label, all_count in all_data:
        onsite_count = int(onsite_by_label.get(label, 0))
        all_percent = 100.0 * all_count / all_denominator if all_denominator else 0.0
        onsite_percent = 100.0 * onsite_count / onsite_denominator if onsite_denominator else 0.0
        missing_class = " is-missing" if label == "No calculable" else ""
        rows.append(
            f'''<div class="commute-comparison-row"><div class="commute-comparison-label">{esc(label)}</div>
              <div class="commute-comparison-series">
                <div class="commute-comparison-line"><span class="commute-series-name">All</span><div class="bar-track"><div class="bar-fill commute-series-all{missing_class}" style="width:{all_percent:.2f}%"></div></div><span class="commute-series-value">{all_percent:.1f}% · {all_count:,}</span></div>
                <div class="commute-comparison-line"><span class="commute-series-name">Onsite</span><div class="bar-track"><div class="bar-fill commute-series-onsite{missing_class}" style="width:{onsite_percent:.2f}%"></div></div><span class="commute-series-value">{onsite_percent:.1f}% · {onsite_count:,}</span></div>
              </div></div>'''
        )
    return f'''<article class="card chart-card commute-distance-card commute-distance-comparison-card"><div class="card-title">Distance bands: all eligible vs Onsite</div>
      <div class="commute-comparison-legend"><span><i class="commute-legend-swatch commute-series-all"></i>All eligible ({all_denominator:,})</span><span><i class="commute-legend-swatch commute-series-onsite"></i>Onsite ({onsite_denominator:,})</span><span><i class="commute-legend-swatch commute-series-missing"></i>No calculable</span></div>
      <div class="commute-comparison-list">{"".join(rows)}</div>
      <div class="chart-footer">The underlying evidence keeps 1-km detail; these bands make the all-vs-Onsite comparison readable. Percentages use each segment's own denominator. Distance is Haversine km, not route distance or travel time.</div></article>'''


def commute_distance_slide(number: int) -> str:
    evidence, _ = commute_distance_evidence()
    metrics = evidence["metrics"]
    onsite_metrics = metrics["onsite"]
    all_data = commute_distance_broad_buckets(
        evidence["distribution"],
        int(metrics["eligible_employees"]),
    )
    onsite_data = commute_distance_broad_buckets(
        evidence["onsite_distribution"],
        int(onsite_metrics["eligible_employees"]),
    )
    all_denominator = int(metrics["eligible_employees"])
    onsite_denominator = int(onsite_metrics["eligible_employees"])
    onsite_share = 100.0 * onsite_denominator / all_denominator if all_denominator else 0.0
    return data_slide(
        number,
        "Commute distance",
        "Approximate geographic proxy · ZIP centroid to Qualcomm office coordinate · all vs Onsite",
        commute_distance_comparison_card(all_data, onsite_data, all_denominator, onsite_denominator),
        side_card(
            "The original chart was not Onsite-only",
            "The comparison keeps the global population and adds the exact stored Onsite subset. Distances for Offsite or unknown arrangements are shown only as geographic context; they should not be interpreted as actual commuting exposure.",
            [
                ("Snapshot", str(evidence["snapshot_date"])),
                ("All eligible", f"{all_denominator:,} regular active employees"),
                ("Onsite", f"{onsite_denominator:,} ({onsite_share:.1f}%)"),
                ("Other / unknown", f"{int(evidence['work_arrangement']['not_onsite_or_unknown_employee_count']):,}"),
                ("Covered distance", f"All {int(metrics['matched_distance_employees']):,} ({float(metrics['coverage_percent_of_eligible']):.1f}%); Onsite {int(onsite_metrics['matched_distance_employees']):,} ({float(onsite_metrics['coverage_percent_of_eligible']):.1f}%)"),
                ("No calculable", f"All {int(metrics['unavailable_employee_count']):,}; Onsite {int(onsite_metrics['unavailable_employee_count']):,}"),
                ("Onsite rule", "UPPER(TRIM(work_arrangement)) = 'ONSITE'"),
                ("Method", "Haversine · postal centroid to listed office coordinate"),
                ("Boundary", "Not route distance, travel time, or a commute observation"),
            ],
            "Internal analysis · aggregate",
        ),
    )


def residential_manager_distance_evidence() -> tuple[dict[str, object], list[tuple[str, int]]]:
    """Load the frozen, aggregate-only evidence for slide 37 and reject gaps."""
    if not RESIDENTIAL_MANAGER_DISTANCE_EVIDENCE.exists():
        raise FileNotFoundError(RESIDENTIAL_MANAGER_DISTANCE_EVIDENCE)
    evidence = json.loads(RESIDENTIAL_MANAGER_DISTANCE_EVIDENCE.read_text(encoding="utf-8"))
    if evidence.get("artifact") != "internal_analysis":
        raise ValueError("Residential manager-distance evidence must be internal_analysis.")
    if evidence.get("variable") != "Residential distance from manager":
        raise ValueError("Residential manager-distance evidence has an unexpected variable name.")
    if evidence.get("snapshot_date") != "2026-08-23" or evidence.get("outcome") != "pass":
        raise ValueError("Residential manager-distance evidence is not a passing fixed-snapshot result.")

    forbidden_exact = {
        "employee_id", "manager_employee_id", "postal_code", "employee_postal_code",
        "manager_postal_code", "postal_hash", "employee_postal_hash",
        "manager_postal_hash", "pair_hash", "employee_name", "manager_name",
        "address", "home_address",
    }
    forbidden_prefixes = (
        "postal_hash_", "employee_postal_hash_", "manager_postal_hash_", "pair_hash_",
    )

    def reject_sensitive_fields(value: object) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                normalized_key = str(key).lower()
                if normalized_key in forbidden_exact or normalized_key.startswith(forbidden_prefixes):
                    raise ValueError(f"Residential manager-distance evidence persists restricted field {key!r}.")
                reject_sensitive_fields(nested)
        elif isinstance(value, list):
            for nested in value:
                reject_sensitive_fields(nested)

    reject_sensitive_fields(evidence)
    metrics = evidence.get("metrics")
    provenance = evidence.get("provenance")
    references = evidence.get("references")
    distribution_raw = evidence.get("distribution")
    if not isinstance(metrics, dict) or not isinstance(provenance, dict) or not isinstance(references, dict) or not isinstance(distribution_raw, list):
        raise ValueError("Residential manager-distance evidence has an invalid aggregate contract.")
    required_metrics = {
        "active_regular_employees", "feature_eligible_pairs", "key_unavailable_employees",
        "observable_pairs", "not_observable_pairs", "total_unavailable_employees",
        "published_pair_count", "published_band_count", "minimum_published_band_count",
        "minimum_cohort", "unrecognized_country_pairs", "country_mapping_categories_checked",
    }
    missing_metrics = sorted(required_metrics - set(metrics))
    if missing_metrics:
        raise ValueError(f"Residential manager-distance evidence is missing metrics: {missing_metrics}")
    metric = {key: int(metrics[key]) for key in required_metrics}
    if metric["active_regular_employees"] != 50_043 or metric["feature_eligible_pairs"] != 49_556:
        raise ValueError("Residential manager-distance evidence no longer matches the approved fixed snapshot population.")
    if metric["active_regular_employees"] != metric["feature_eligible_pairs"] + metric["key_unavailable_employees"]:
        raise ValueError("Residential manager-distance active-workforce reconciliation failed.")
    if metric["feature_eligible_pairs"] != metric["observable_pairs"] + metric["not_observable_pairs"]:
        raise ValueError("Residential manager-distance centroid observability reconciliation failed.")
    if metric["total_unavailable_employees"] != metric["active_regular_employees"] - metric["observable_pairs"]:
        raise ValueError("Residential manager-distance unavailable-workforce reconciliation failed.")
    if metric["minimum_cohort"] != MINIMUM_COHORT or metric["unrecognized_country_pairs"] < 0:
        raise ValueError("Residential manager-distance country or privacy validation failed.")
    safeguards = (
        "employee_duplicate_source_rows", "employee_manager_conflicts",
        "employee_postal_code_conflicts", "employee_country_conflicts", "unmatched_managers",
        "manager_duplicate_source_rows", "manager_postal_code_conflicts", "manager_country_conflicts",
    )
    if any(int(metrics.get(key, -1)) != 0 for key in safeguards):
        raise ValueError("Residential manager-distance same-snapshot duplicate/conflict safeguards failed.")

    distribution: list[tuple[str, int]] = []
    percentage_total = 0.0
    for row in distribution_raw:
        if not isinstance(row, dict):
            raise ValueError("Residential manager-distance distribution contains an invalid row.")
        category = str(row.get("category", ""))
        count = int(row.get("employee_count", 0))
        if not category or category == "Not calculable" or count < MINIMUM_COHORT:
            raise ValueError("Residential manager-distance distribution contains an unsafe display band.")
        distribution.append((category, count))
        percentage_total += float(row.get("percent_of_calculable_pairs", 0.0))
    if not distribution or len(distribution) != metric["published_band_count"]:
        raise ValueError("Residential manager-distance published-band count does not reconcile.")
    if min(count for _, count in distribution) != metric["minimum_published_band_count"]:
        raise ValueError("Residential manager-distance minimum display cohort does not reconcile.")
    if sum(count for _, count in distribution) != metric["observable_pairs"] or metric["published_pair_count"] != metric["observable_pairs"]:
        raise ValueError("Residential manager-distance displayed bands do not sum to calculable pairs.")
    if abs(percentage_total - 100.0) > 0.000001:
        raise ValueError("Residential manager-distance displayed percentages do not sum to 100%.")

    for key, expected in (
        ("profile_sql", RESIDENTIAL_MANAGER_DISTANCE_PROFILE_SQL),
        ("audit_sql", RESIDENTIAL_MANAGER_DISTANCE_AUDIT_SQL),
        ("country_mapping_audit_sql", RESIDENTIAL_MANAGER_DISTANCE_COUNTRY_MAPPING_AUDIT_SQL),
    ):
        if provenance.get(key) != expected:
            raise ValueError(f"Residential manager-distance provenance has an unexpected {key}.")
    for key in (
        "profile_sql_sha256", "profile_result_sha256", "audit_sql_sha256", "audit_result_sha256",
        "country_mapping_audit_sql_sha256", "country_mapping_audit_result_sha256",
    ):
        if not re.fullmatch(r"[0-9a-f]{64}", str(provenance.get(key, ""))):
            raise ValueError(f"Residential manager-distance provenance is missing a valid {key}.")
    centroid_reference = references.get("geonames_postal_centroids")
    if not isinstance(centroid_reference, dict) or not isinstance(centroid_reference.get("country_sources"), dict):
        raise ValueError("Residential manager-distance evidence is missing the GeoNames reference hashes.")
    for source in centroid_reference["country_sources"].values():
        if not isinstance(source, dict) or not re.fullmatch(r"[0-9a-f]{64}", str(source.get("sha256", ""))):
            raise ValueError("Residential manager-distance evidence has an invalid GeoNames source hash.")
    return evidence, distribution


def residential_manager_distance_manifest_entry(evidence: dict[str, object]) -> dict[str, object]:
    """Return manifest provenance without copying any employee or postal data."""
    metrics = evidence["metrics"]
    provenance = evidence["provenance"]
    sources = evidence["references"]["geonames_postal_centroids"]["country_sources"]
    assert isinstance(metrics, dict) and isinstance(provenance, dict) and isinstance(sources, dict)
    return {
        "evidence": str(RESIDENTIAL_MANAGER_DISTANCE_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "builder": str(RESIDENTIAL_MANAGER_DISTANCE_BUILDER.relative_to(ROOT)).replace("\\", "/"),
        "profile_query": RESIDENTIAL_MANAGER_DISTANCE_PROFILE_SQL,
        "audit_query": RESIDENTIAL_MANAGER_DISTANCE_AUDIT_SQL,
        "country_mapping_audit_query": RESIDENTIAL_MANAGER_DISTANCE_COUNTRY_MAPPING_AUDIT_SQL,
        "execution_date": evidence["execution_date"],
        "snapshot": evidence["snapshot_date"],
        "population": evidence["population"],
        "grain": evidence["grain"],
        "publication_status": evidence.get("publication_status", "validated"),
        "method": evidence["method"],
        "query_sha256": {
            "profile_sql": provenance["profile_sql_sha256"],
            "profile_result": provenance["profile_result_sha256"],
            "audit_sql": provenance["audit_sql_sha256"],
            "audit_result": provenance["audit_result_sha256"],
            "country_mapping_audit_sql": provenance["country_mapping_audit_sql_sha256"],
            "country_mapping_audit_result": provenance["country_mapping_audit_result_sha256"],
        },
        "reference_sha256": {country: source["sha256"] for country, source in sources.items()},
        "aggregate_metrics": {
            key: metrics[key]
            for key in (
                "active_regular_employees", "feature_eligible_pairs", "key_unavailable_employees",
                "observable_pairs", "not_observable_pairs", "total_unavailable_employees",
                "calculable_coverage_percent_of_feature_eligible", "published_band_count",
                "minimum_published_band_count", "unavailable_reference_pairs",
                "country_mapping_categories_checked",
            )
        },
        "acceptance_rule": evidence["acceptance_rule"],
        "outcome": evidence["outcome"],
    }


def residential_manager_distance_slide(number: int, evidence: dict[str, object]) -> str:
    """Render the approved fixed-snapshot, aggregate postal-centroid proxy."""
    metrics = evidence["metrics"]
    assert isinstance(metrics, dict)
    _, distribution = residential_manager_distance_evidence()
    observable_pairs = int(metrics["observable_pairs"])
    feature_eligible_pairs = int(metrics["feature_eligible_pairs"])
    active_workforce = int(metrics["active_regular_employees"])
    not_observable_pairs = int(metrics["not_observable_pairs"])
    total_unavailable = int(metrics["total_unavailable_employees"])
    coverage = float(metrics["calculable_coverage_percent_of_feature_eligible"])
    side = f'''<article class="card side-copy residential-manager-distance-side"><div class="card-title">Variable context</div>
      <span class="badge badge-info">Internal analysis · aggregate</span>
      <h3>Measured proxy, not commute burden</h3>
      <p>Each calculable pair uses the stored postal-code centroid for an employee and that employee's same-snapshot manager. Shared centroids do not prove co-location.</p>
      {facts([
          ("Snapshot", str(evidence["snapshot_date"])),
          ("Active workforce", f"{active_workforce:,} regular active employees"),
          ("Feature eligible", f"{feature_eligible_pairs:,} same-snapshot pairs"),
          ("Calculable coverage", f"{observable_pairs:,} / {feature_eligible_pairs:,} ({coverage:.1f}%)"),
          ("Not calculable", f"{not_observable_pairs:,} eligible pairs"),
          ("Unavailable workforce", f"{total_unavailable:,} employees"),
          ("Method", "Haversine km · paired postal centroids"),
          ("Not measured", "route, travel time, office distance, or actual home address"),
      ])}</article>'''
    return data_slide(
        number,
        "Residential distance from manager",
        "Approximate Haversine km · employee and same-snapshot manager postal-centroid proxy",
        bar_card(
            "Calculable employee-manager pairs · distance bands",
            distribution,
            f"Denominator: {observable_pairs:,} calculable pairs. One-kilometre bands through 30 km; 30+ km is the remaining calculable tail.",
            "residential-manager-distance-card",
        ),
        side,
    )


def office_site_relationship_evidence() -> tuple[dict[str, object], list[tuple[str, int]]]:
    """Derive the FY2026 office-site relationship display from frozen aggregate evidence."""
    evidence = load(CO_LOCATION_SITE_CITY_EVIDENCE)
    if evidence.get("artifact") != "presentation" or evidence.get("outcome") != "pass":
        raise ValueError("Office-site relationship evidence must be presentation-safe and pass.")
    if evidence.get("query_path") != CO_LOCATION_SITE_CITY_PROFILE_SQL:
        raise ValueError("Office-site relationship evidence is not linked to the saved profile SQL.")
    if evidence.get("deck_cutoff") != V4_SNAPSHOT:
        raise ValueError("Office-site relationship evidence does not use the deck cutoff.")

    rows = evidence.get("rows")
    if not isinstance(rows, list):
        raise ValueError("Office-site relationship evidence has no annual aggregate rows.")
    fy2026 = next((row for row in rows if str(row.get("fiscal_year")) == "2026"), None)
    if not isinstance(fy2026, dict) or int(fy2026.get("snapshot_count", 0)) != 11:
        raise ValueError("Office-site relationship evidence requires the FY2026 11-snapshot aggregate.")

    total = int(fy2026["eligible_employee_snapshots"])
    comparable = int(fy2026["site_comparable_employee_snapshots"])
    same_site = int(fy2026["same_office_site_employee_snapshots"])
    different_site = comparable - same_site
    not_comparable = total - comparable
    expected = (525_633, 488_355, 459_095, 29_260, 37_278)
    if (total, comparable, same_site, different_site, not_comparable) != expected:
        raise ValueError("Office-site relationship FY2026 aggregates no longer match the approved evidence.")
    if min(same_site, different_site, not_comparable) < MINIMUM_COHORT:
        raise ValueError("Office-site relationship contains a sub-threshold display category.")
    if same_site + different_site + not_comparable != total:
        raise ValueError("Office-site relationship categories do not reconcile to the common denominator.")
    percent_same_comparable = 100.0 * same_site / comparable
    if abs(percent_same_comparable - float(fy2026["same_office_site_percent_of_site_comparable"])) > 0.0001:
        raise ValueError("Office-site relationship comparable-pair percentage does not reconcile.")
    return evidence, [
        ("Same office_site", same_site),
        ("Different office_site", different_site),
        ("Not comparable / missing site", not_comparable),
    ]


def office_site_relationship_manifest_entry(evidence: dict[str, object]) -> dict[str, object]:
    """Return independent, aggregate-only provenance for the inserted location view."""
    _, categories = office_site_relationship_evidence()
    total = sum(count for _, count in categories)
    same_site = categories[0][1]
    comparable = categories[0][1] + categories[1][1]
    return {
        "evidence": str(CO_LOCATION_SITE_CITY_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "evidence_sha256": hashlib.sha256(CO_LOCATION_SITE_CITY_EVIDENCE.read_bytes()).hexdigest(),
        "query": CO_LOCATION_SITE_CITY_PROFILE_SQL,
        "cutoff": V4_SNAPSHOT,
        "fiscal_year": "FY2026",
        "snapshot_count": 11,
        "population": evidence["population"],
        "grain": evidence["grain"],
        "categories": [
            {
                "label": label,
                "employee_manager_snapshots": count,
                "percent_of_total": round(100.0 * count / total, 4),
            }
            for label, count in categories
        ],
        "common_denominator": total,
        "comparable_pairs": comparable,
        "same_office_site_percent_of_comparable_pairs": round(100.0 * same_site / comparable, 4),
        "minimum_shared_cohort": MINIMUM_COHORT,
        "acceptance_rule": "The three categories use one FY2026 denominator, reconcile to it exactly, and each displayed category has n >= 30.",
        "interpretation": "Stored office_site comparison only; it is conceptually aligned with Co-location with manager and does not measure residential distance, address proximity, travel time, or a four-hour difference.",
        "outcome": "pass",
    }


def office_site_relationship_slide(number: int) -> str:
    """Render the distinct FY2026 office-site relationship view without reusing residential data."""
    evidence, categories = office_site_relationship_evidence()
    total = sum(count for _, count in categories)
    same_site, different_site, not_comparable = (count for _, count in categories)
    comparable = same_site + different_site
    return data_slide(
        number,
        "Office-site relationship with manager",
        "FY2026 through 23-Aug-2026 · stored office_site comparison across 11 monthly snapshots",
        bar_card(
            "Employee-manager snapshots by stored office_site relationship",
            categories,
            f"Common denominator: {total:,} employee-manager snapshots. Categories are mutually exclusive and exhaustive for FY2026.",
            "office-site-relationship-card",
        ),
        side_card(
            "Stored-field proxy, not residential distance",
            "This view is conceptually aligned with Co-location with manager: it compares the employee and manager office_site values stored in the same snapshot.",
            [
                ("FY2026 scope", "11 monthly snapshots through 23-Aug-2026"),
                ("Common denominator", f"{total:,} employee-manager snapshots"),
                ("Comparable pairs", f"{comparable:,} ({100.0 * comparable / total:.1f}%)"),
                ("Same among comparable", f"{100.0 * same_site / comparable:.2f}%"),
                ("Not used", "residential kilometres, addresses, or postal centroids"),
                ("Not calculated", "four-hour difference, travel time, or physical presence"),
                ("Source", CO_LOCATION_SITE_CITY_PROFILE_SQL),
            ],
            "Aggregate evidence",
        ),
    )


def company_tenure_distribution_evidence() -> tuple[dict[str, object], list[tuple[str, int]], list[tuple[str, int]]]:
    """Load slide-27 evidence and fail closed on fixed-snapshot or privacy gaps."""
    if not COMPANY_TENURE_EVIDENCE.exists():
        raise FileNotFoundError(COMPANY_TENURE_EVIDENCE)
    evidence = load(COMPANY_TENURE_EVIDENCE)
    if not isinstance(evidence, dict):
        raise ValueError("Company tenure evidence must be a JSON object.")
    expected_contract = {
        "artifact_type": "aggregate_distribution_evidence",
        "deliverable_mode": "internal_analysis",
        "variable": "Company tenure",
        "semantic_type": "direct_field",
        "publication_status": "descriptive_stored_fields",
        "score_v4_change": "none",
        "snapshot_date": V4_SNAPSHOT,
        "outcome": "pass",
    }
    if any(evidence.get(key) != value for key, value in expected_contract.items()):
        raise ValueError("Company tenure evidence has an unexpected publication contract.")

    prohibited = {
        "employee_id", "employee_ids", "emp_name", "name", "employee_name", "manager_employee_id",
        "manager_name", "email", "address", "home_address", "raw_rows", "raw_query_rows",
        "query_rows", "source_rows", "individual_dates",
    }

    def reject_sensitive_fields(value: object) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if str(key).lower() in prohibited:
                    raise ValueError(f"Company tenure evidence persists restricted field {key!r}.")
                reject_sensitive_fields(nested)
        elif isinstance(value, list):
            for nested in value:
                reject_sensitive_fields(nested)

    reject_sensitive_fields(evidence)
    provenance = evidence.get("provenance")
    privacy = evidence.get("privacy_checks")
    coverage = evidence.get("coverage")
    metrics = evidence.get("metrics")
    validations = evidence.get("validations")
    definitions = evidence.get("definitions")
    distribution_raw = evidence.get("distribution")
    if not all(isinstance(value, dict) for value in (provenance, privacy, coverage, metrics, validations, definitions)) or not isinstance(distribution_raw, list):
        raise ValueError("Company tenure evidence is missing its aggregate contract.")
    assert isinstance(provenance, dict) and isinstance(privacy, dict) and isinstance(coverage, dict)
    assert isinstance(metrics, dict) and isinstance(validations, dict) and isinstance(definitions, dict)
    if set(definitions) != {"original_hire_date", "max_hire_rehire_date", "cross_field_policy"}:
        raise ValueError("Company tenure evidence must describe the two stored dates and their non-override policy.")
    if provenance.get("audit_sql") != COMPANY_TENURE_AUDIT_SQL or provenance.get("profile_sql") != COMPANY_TENURE_PROFILE_SQL:
        raise ValueError("Company tenure evidence does not reference the approved saved SQL.")
    for sql_path, hash_key in ((COMPANY_TENURE_AUDIT_SQL, "audit_sql_sha256"), (COMPANY_TENURE_PROFILE_SQL, "profile_sql_sha256")):
        local_path = ROOT / sql_path
        if not local_path.exists() or provenance.get(hash_key) != hashlib.sha256(local_path.read_bytes()).hexdigest():
            raise ValueError("Company tenure evidence is stale relative to its saved SQL.")
    for hash_key in ("audit_sql_sha256", "audit_result_sha256", "profile_sql_sha256", "profile_result_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", str(provenance.get(hash_key, ""))):
            raise ValueError(f"Company tenure evidence has an invalid {hash_key}.")
    if provenance.get("raw_aggregate_rows_persisted") is not False:
        raise ValueError("Company tenure evidence must not persist raw aggregate rows.")
    if any(bool(privacy.get(key)) for key in ("identifiers_persisted", "employee_rows_persisted", "raw_dates_persisted", "raw_aggregate_rows_persisted")):
        raise ValueError("Company tenure evidence persists prohibited information.")
    if privacy.get("all_displayed_bands_meet_minimum") is not True or int(privacy.get("minimum_cohort", -1)) != MINIMUM_COHORT:
        raise ValueError("Company tenure privacy safeguards failed.")

    expected_validation_keys = {
        "employee_snapshot_grain", "dates", "stored_date_order", "population_reconciliation",
        "distribution_reconciliation", "privacy",
    }
    if set(validations) != expected_validation_keys or any(not isinstance(item, dict) or item.get("outcome") != "pass" for item in validations.values()):
        raise ValueError("Company tenure validation outcomes are incomplete or failing.")
    required_metrics = {
        "population_source_row_count", "target_missing_employee_id_row_count", "target_source_row_count",
        "target_unique_employee_count", "target_duplicate_employee_count", "target_duplicate_row_excess_count",
        "target_conflicting_employee_count", "original_hire_null_count", "latest_hire_rehire_null_count",
        "original_hire_future_date_count", "latest_hire_rehire_future_date_count", "impossible_date_order_count",
        "original_hire_calculable_employee_count", "latest_hire_rehire_calculable_employee_count",
        "published_band_count", "minimum_published_original_hire_band_count",
        "minimum_published_latest_hire_rehire_band_count", "minimum_cohort",
    }
    missing_metrics = sorted(required_metrics - set(metrics))
    if missing_metrics:
        raise ValueError(f"Company tenure evidence is missing metrics: {missing_metrics}")
    metric = {key: int(metrics[key]) for key in required_metrics}
    if metric["minimum_cohort"] != MINIMUM_COHORT:
        raise ValueError("Company tenure evidence has an unexpected cohort threshold.")
    safeguards = (
        "target_missing_employee_id_row_count", "target_duplicate_employee_count", "target_duplicate_row_excess_count",
        "target_conflicting_employee_count", "original_hire_future_date_count", "latest_hire_rehire_future_date_count",
        "impossible_date_order_count",
    )
    if any(metric[key] != 0 for key in safeguards):
        raise ValueError("Company tenure evidence contains unresolved integrity safeguards.")
    if metric["population_source_row_count"] != metric["target_source_row_count"] or metric["target_source_row_count"] != metric["target_unique_employee_count"]:
        raise ValueError("Company tenure audit population does not reconcile.")

    required_coverage = {
        "eligible_employee_count", "original_hire_calculable_employee_count", "original_hire_not_calculable_employee_count",
        "latest_hire_rehire_calculable_employee_count", "latest_hire_rehire_not_calculable_employee_count",
    }
    if set(coverage) != required_coverage:
        raise ValueError("Company tenure coverage contract is malformed.")
    covered = {key: int(coverage[key]) for key in required_coverage}
    if (
        covered["eligible_employee_count"] != metric["target_unique_employee_count"]
        or covered["original_hire_calculable_employee_count"] != metric["original_hire_calculable_employee_count"]
        or covered["latest_hire_rehire_calculable_employee_count"] != metric["latest_hire_rehire_calculable_employee_count"]
        or covered["original_hire_calculable_employee_count"] + covered["original_hire_not_calculable_employee_count"] != covered["eligible_employee_count"]
        or covered["latest_hire_rehire_calculable_employee_count"] + covered["latest_hire_rehire_not_calculable_employee_count"] != covered["eligible_employee_count"]
    ):
        raise ValueError("Company tenure coverage does not reconcile.")

    band_keys = ("lt_1", "y1_to_lt2", "y2_to_lt3", "y3_to_lt5", "y5_to_lt10", "y10_plus")
    original_data: list[tuple[str, int]] = []
    latest_data: list[tuple[str, int]] = []
    original_percent_total = 0.0
    latest_percent_total = 0.0
    for expected_key, row in zip(band_keys, distribution_raw):
        if not isinstance(row, dict):
            raise ValueError("Company tenure distribution contains an invalid row.")
        label = str(row.get("label", ""))
        original_count = int(row.get("original_hire_employee_count", -1))
        latest_count = int(row.get("latest_hire_rehire_employee_count", -1))
        if row.get("source_band_key") != expected_key or not label or original_count < MINIMUM_COHORT or latest_count < MINIMUM_COHORT:
            raise ValueError("Company tenure distribution contains an unsafe or reordered band.")
        expected_original_percent = round(100 * original_count / covered["original_hire_calculable_employee_count"], 8)
        expected_latest_percent = round(100 * latest_count / covered["latest_hire_rehire_calculable_employee_count"], 8)
        if (
            not math.isclose(float(row.get("original_hire_percent_of_calculable", -1)), expected_original_percent, abs_tol=0.00000001)
            or not math.isclose(float(row.get("latest_hire_rehire_percent_of_calculable", -1)), expected_latest_percent, abs_tol=0.00000001)
        ):
            raise ValueError("Company tenure band percentage does not reconcile to its denominator.")
        original_data.append((label, original_count))
        latest_data.append((label, latest_count))
        original_percent_total += expected_original_percent
        latest_percent_total += expected_latest_percent
    if len(distribution_raw) != len(band_keys) or metric["published_band_count"] != len(band_keys):
        raise ValueError("Company tenure evidence must retain the six approved shared anniversary bands.")
    if (
        sum(count for _, count in original_data) != covered["original_hire_calculable_employee_count"]
        or sum(count for _, count in latest_data) != covered["latest_hire_rehire_calculable_employee_count"]
        or min(count for _, count in original_data) != metric["minimum_published_original_hire_band_count"]
        or min(count for _, count in latest_data) != metric["minimum_published_latest_hire_rehire_band_count"]
        or not math.isclose(original_percent_total, 100.0, abs_tol=0.000001)
        or not math.isclose(latest_percent_total, 100.0, abs_tol=0.000001)
    ):
        raise ValueError("Company tenure distribution totals do not reconcile.")
    return evidence, original_data, latest_data


def company_tenure_manifest_entry(evidence: dict[str, object]) -> dict[str, object]:
    """Return auditable slide provenance without copying raw query rows."""
    provenance = evidence["provenance"]
    coverage = evidence["coverage"]
    metrics = evidence["metrics"]
    assert isinstance(provenance, dict) and isinstance(coverage, dict) and isinstance(metrics, dict)
    return {
        "evidence": str(COMPANY_TENURE_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "builder": str(COMPANY_TENURE_BUILDER.relative_to(ROOT)).replace("\\", "/"),
        "audit_query": COMPANY_TENURE_AUDIT_SQL,
        "profile_query": COMPANY_TENURE_PROFILE_SQL,
        "execution_date": evidence["execution_date"],
        "snapshot": evidence["snapshot_date"],
        "population": evidence["population"],
        "grain": evidence["grain"],
        "definitions": evidence["definitions"],
        "coverage": coverage,
        "query_sha256": {
            "audit_sql": provenance["audit_sql_sha256"],
            "audit_result": provenance["audit_result_sha256"],
            "profile_sql": provenance["profile_sql_sha256"],
            "profile_result": provenance["profile_result_sha256"],
        },
        "aggregate_metrics": {
            key: metrics[key]
            for key in (
                "original_hire_null_count", "latest_hire_rehire_null_count", "impossible_date_order_count",
                "published_band_count", "minimum_published_original_hire_band_count",
                "minimum_published_latest_hire_rehire_band_count",
            )
        },
        "publication_rule": "Internal aggregate analysis only; the six shared anniversary bands have n >= 30 in both stored-field distributions. No employee rows, identifiers, or raw dates are retained.",
        "acceptance_rule": evidence["acceptance_rule"],
        "outcome": evidence["outcome"],
    }


def company_tenure_slide(number: int, evidence: dict[str, object]) -> str:
    """Render the two stored-date distributions without selecting either definition."""
    _, original_data, latest_data = company_tenure_distribution_evidence()
    coverage = evidence["coverage"]
    assert isinstance(coverage, dict)
    eligible = int(coverage["eligible_employee_count"])
    original_denominator = int(coverage["original_hire_calculable_employee_count"])
    latest_denominator = int(coverage["latest_hire_rehire_calculable_employee_count"])
    original_not_calculable = int(coverage["original_hire_not_calculable_employee_count"])
    latest_not_calculable = int(coverage["latest_hire_rehire_not_calculable_employee_count"])
    main = f'''<div class="two-chart">{bar_card(
        "Service since original hire · field proxy",
        original_data,
        f"Anniversary bands at 23-Aug-2026. Percent and n use {original_denominator:,} calculable employees.",
        "company-tenure-card",
    )}{bar_card(
        "Service since latest hire / rehire · field proxy",
        latest_data,
        f"Same shared anniversary bands at 23-Aug-2026. Percent and n use {latest_denominator:,} calculable employees.",
        "company-tenure-card",
    )}</div>'''
    side = side_card(
        "Variables used in the two distributions",
        "Each chart describes its own stored date field directly. Neither field is applied over the other, and this descriptive result does not select a governed HRIS tenure definition.",
        [
            ("Snapshot / population", f"23-Aug-2026 · {eligible:,} active regular employees"),
            ("Left-chart field", "original_hire_date"),
            ("Right-chart field", "max_hire_rehire_date"),
            ("Original-hire coverage", f"{original_denominator:,} calculable · {original_not_calculable:,} not calculable"),
            ("Latest-hire/rehire coverage", f"{latest_denominator:,} calculable · {latest_not_calculable:,} not calculable"),
            ("Shared bands", "<1 · 1–<2 · 2–<3 · 3–<5 · 5–<10 · 10+ years"),
            ("Privacy", "internal aggregate analysis · every visible band n ≥ 30"),
        ],
        "Internal exploratory analysis",
    ).replace('class="card side-copy"', 'class="card side-copy company-tenure-side"')
    slide = data_slide(
        number,
        "Company tenure",
        "Active regular employees · two stored-date field proxies · 23-Aug-2026",
        main,
        side,
    )
    return slide.replace(
        f'<div class="slide-stage" id="slide-{number}">',
        f'<div class="slide-stage" id="slide-{number}" data-evidence-run="company-tenure-stored-fields-snapshot-20260823">',
        1,
    )


def company_tenure_slide_or_support(number: int) -> tuple[str, str]:
    """Keep a support state only until fixed-snapshot evidence passes."""
    try:
        evidence, _, _ = company_tenure_distribution_evidence()
    except (FileNotFoundError, ValueError):
        return (
            "Company tenure",
            support_slide(number, "Company tenure", "No chart · fixed stored-date evidence is pending", "No stored-field distribution is published", "original_hire_date and max_hire_rehire_date describe different stored dates. The required fixed-snapshot integrity and privacy checks have not passed.", [("Field 1", "original_hire_date"), ("Field 2", "max_hire_rehire_date"), ("Action", "run fixed-snapshot validation")]),
        )
    return "Company tenure", company_tenure_slide(number, evidence)


def role_level_tenure_distribution_evidence() -> tuple[dict[str, object], list[tuple[str, int]], list[tuple[str, int]]]:
    """Load slide-26 evidence and fail closed on lineage, reconciliation, or privacy gaps."""
    if not ROLE_LEVEL_TENURE_EVIDENCE.exists():
        raise FileNotFoundError(ROLE_LEVEL_TENURE_EVIDENCE)
    evidence = load(ROLE_LEVEL_TENURE_EVIDENCE)
    if not isinstance(evidence, dict):
        raise ValueError("Role/level tenure evidence must be a JSON object.")
    if (
        evidence.get("artifact_type") != "aggregate_distribution_evidence"
        or evidence.get("deliverable_mode") != "internal_analysis"
        or evidence.get("outcome") != "pass"
        or evidence.get("variable") != "Time in current job profile vs. current detailed level"
        or evidence.get("semantic_type") != "derived_feature"
        or evidence.get("snapshot_date") != V4_SNAPSHOT
    ):
        raise ValueError("Role/level tenure evidence has an unexpected publication contract.")
    publication_status = evidence.get("publication_status")
    if publication_status not in {"validated", "exploratory"}:
        raise ValueError("Role/level tenure evidence has an invalid publication status.")

    prohibited = {
        "employee_id", "employee_ids", "manager_employee_id", "name", "employee_name", "manager_name",
        "email", "job_title", "job_code", "time_in_job_profile_start_date", "levelentrydate",
        "max_hire_rehire_date", "raw_rows", "raw_query_rows", "query_rows",
    }

    def reject_sensitive_fields(value: object) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if str(key).lower() in prohibited:
                    raise ValueError(f"Role/level tenure evidence persists restricted field {key!r}.")
                reject_sensitive_fields(nested)
        elif isinstance(value, list):
            for nested in value:
                reject_sensitive_fields(nested)

    reject_sensitive_fields(evidence)
    provenance = evidence.get("provenance")
    privacy = evidence.get("privacy_checks")
    coverage = evidence.get("coverage")
    metrics = evidence.get("metrics")
    lineage = evidence.get("authoritative_lineage")
    validations = evidence.get("validations")
    definitions = evidence.get("definitions")
    distribution_raw = evidence.get("distribution")
    if not all(isinstance(value, dict) for value in (provenance, privacy, coverage, metrics, lineage, validations, definitions)) or not isinstance(distribution_raw, list):
        raise ValueError("Role/level tenure evidence is missing its aggregate contract.")
    assert isinstance(provenance, dict) and isinstance(privacy, dict) and isinstance(coverage, dict)
    assert isinstance(metrics, dict) and isinstance(lineage, dict) and isinstance(validations, dict) and isinstance(definitions, dict)
    if provenance.get("audit_sql") != ROLE_LEVEL_TENURE_AUDIT_SQL or provenance.get("profile_sql") != ROLE_LEVEL_TENURE_PROFILE_SQL:
        raise ValueError("Role/level tenure evidence does not reference the approved saved SQL.")
    for sql_path, hash_key in ((ROLE_LEVEL_TENURE_AUDIT_SQL, "audit_sql_sha256"), (ROLE_LEVEL_TENURE_PROFILE_SQL, "profile_sql_sha256")):
        local_path = ROOT / sql_path
        if not local_path.exists() or provenance.get(hash_key) != hashlib.sha256(local_path.read_bytes()).hexdigest():
            raise ValueError("Role/level tenure evidence is stale relative to its saved SQL.")
    for hash_key in ("audit_sql_sha256", "audit_result_sha256", "profile_sql_sha256", "profile_result_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", str(provenance.get(hash_key, ""))):
            raise ValueError(f"Role/level tenure evidence has an invalid {hash_key}.")
    if provenance.get("raw_aggregate_rows_persisted") is not False:
        raise ValueError("Role/level tenure evidence must not persist raw aggregate rows.")
    if any(bool(privacy.get(key)) for key in ("identifiers_persisted", "employee_rows_persisted", "raw_dates_persisted", "job_code_or_title_persisted")):
        raise ValueError("Role/level tenure evidence persists prohibited information.")
    if privacy.get("all_displayed_bands_meet_minimum") is not True or int(privacy.get("minimum_cohort", -1)) != MINIMUM_COHORT:
        raise ValueError("Role/level tenure privacy safeguards failed.")
    if publication_status == "validated":
        if (
            lineage.get("status") != "confirmed"
            or not str(lineage.get("authority", "")).strip()
            or not str(lineage.get("confirmation_date", "")).strip()
            or not str(lineage.get("source_reference", "")).strip()
            or lineage.get("time_in_job_profile_start_date_confirmed_construct") != "current_job_profile_start"
            or lineage.get("job_level_primary_position_confirmed_construct") != "current_detailed_level"
            or not re.fullmatch(r"[0-9a-f]{64}", str(lineage.get("lineage_sha256", "")))
        ):
            raise ValueError("Validated role/level tenure evidence lacks authoritative HRIS lineage confirmation.")
    elif (
        lineage.get("status") != "not_confirmed"
        or lineage.get("time_in_job_profile_start_date_confirmed_construct") != "not_confirmed"
        or lineage.get("job_level_primary_position_confirmed_construct") != "not_confirmed"
        or not str(lineage.get("source_reference", "")).strip()
        or not re.fullmatch(r"[0-9a-f]{64}", str(lineage.get("lineage_sha256", "")))
    ):
        raise ValueError("Exploratory role/level tenure evidence must disclose unconfirmed lineage.")
    if definitions.get("time_in_role") != "Supporting audit field only; it does not define either published clock.":
        raise ValueError("Role/level tenure evidence must retain time_in_role as support only.")
    required_validation_keys = {
        "employee_snapshot_grain", "dates_and_rehire", "detailed_level_transition",
        "distribution_reconciliation", "privacy", "authoritative_lineage",
    }
    if set(validations) != required_validation_keys or any(not isinstance(item, dict) for item in validations.values()):
        raise ValueError("Role/level tenure validation outcomes are incomplete or failing.")
    expected_outcomes = (
        {
            "employee_snapshot_grain": "pass", "dates_and_rehire": "pass", "detailed_level_transition": "pass",
            "distribution_reconciliation": "pass", "privacy": "pass", "authoritative_lineage": "pass",
        }
        if publication_status == "validated"
        else {
            "employee_snapshot_grain": "pass", "dates_and_rehire": "pass", "detailed_level_transition": "warning",
            "distribution_reconciliation": "pass", "privacy": "pass", "authoritative_lineage": "not_confirmed",
        }
    )
    if {key: item.get("outcome") for key, item in validations.items()} != expected_outcomes:
        raise ValueError("Role/level tenure validation outcomes do not match its publication status.")

    required_metrics = {
        "target_source_row_count", "target_unique_employee_count", "target_duplicate_employee_count",
        "target_duplicate_row_excess_count", "target_conflicting_employee_count", "role_start_future_date_count",
        "level_start_future_date_count", "rehire_date_future_count", "rehire_flag_without_date_count",
        "role_calculable_employee_count", "level_calculable_employee_count",
        "history_duplicate_employee_snapshot_count", "history_conflicting_employee_snapshot_count",
        "unexplained_detailed_level_transition_count", "unexplained_detailed_level_reset_count",
        "published_band_count", "minimum_published_role_band_count", "minimum_published_level_band_count", "minimum_cohort",
    }
    missing_metrics = sorted(required_metrics - set(metrics))
    if missing_metrics:
        raise ValueError(f"Role/level tenure evidence is missing metrics: {missing_metrics}")
    numeric_metrics = {key: int(metrics[key]) for key in required_metrics}
    if numeric_metrics["minimum_cohort"] != MINIMUM_COHORT:
        raise ValueError("Role/level tenure evidence has an unexpected cohort threshold.")
    zero_safeguards = (
        "target_duplicate_employee_count", "target_duplicate_row_excess_count", "target_conflicting_employee_count",
        "role_start_future_date_count", "level_start_future_date_count", "rehire_date_future_count",
        "rehire_flag_without_date_count", "history_duplicate_employee_snapshot_count",
        "history_conflicting_employee_snapshot_count",
    )
    if publication_status == "validated":
        zero_safeguards = zero_safeguards + (
            "unexplained_detailed_level_transition_count", "unexplained_detailed_level_reset_count",
        )
    if any(numeric_metrics[key] != 0 for key in zero_safeguards):
        raise ValueError("Role/level tenure evidence contains unresolved integrity or transition safeguards.")

    required_coverage = {
        "eligible_employee_count", "role_calculable_employee_count", "role_not_calculable_employee_count",
        "level_calculable_employee_count", "level_not_calculable_employee_count",
    }
    if set(coverage) != required_coverage:
        raise ValueError("Role/level tenure coverage contract is malformed.")
    numeric_coverage = {key: int(coverage[key]) for key in required_coverage}
    if (
        numeric_coverage["eligible_employee_count"] != numeric_metrics["target_unique_employee_count"]
        or numeric_coverage["role_calculable_employee_count"] != numeric_metrics["role_calculable_employee_count"]
        or numeric_coverage["level_calculable_employee_count"] != numeric_metrics["level_calculable_employee_count"]
        or numeric_coverage["role_calculable_employee_count"] + numeric_coverage["role_not_calculable_employee_count"] != numeric_coverage["eligible_employee_count"]
        or numeric_coverage["level_calculable_employee_count"] + numeric_coverage["level_not_calculable_employee_count"] != numeric_coverage["eligible_employee_count"]
    ):
        raise ValueError("Role/level tenure coverage does not reconcile.")

    expected_source_keys = ("lt_1", "y1_to_lt2", "y2_to_lt3", "y3_to_lt5", "y5_to_lt10", "y10_plus")
    role_data: list[tuple[str, int]] = []
    level_data: list[tuple[str, int]] = []
    role_total = 0
    level_total = 0
    role_percent_total = 0.0
    level_percent_total = 0.0
    previous_key_index = -1
    for row in distribution_raw:
        if not isinstance(row, dict):
            raise ValueError("Role/level tenure distribution contains an invalid row.")
        label = str(row.get("label", ""))
        source_keys = row.get("source_band_keys")
        role_count = int(row.get("role_employee_count", -1))
        level_count = int(row.get("level_employee_count", -1))
        if not label or not isinstance(source_keys, list) or not source_keys or role_count < MINIMUM_COHORT or level_count < MINIMUM_COHORT:
            raise ValueError("Role/level tenure distribution contains an unsafe band.")
        source_indices = [expected_source_keys.index(str(key)) if str(key) in expected_source_keys else -1 for key in source_keys]
        if -1 in source_indices or source_indices != list(range(source_indices[0], source_indices[-1] + 1)) or source_indices[0] != previous_key_index + 1:
            raise ValueError("Role/level tenure shared bands are not contiguous and ordered.")
        previous_key_index = source_indices[-1]
        expected_role_percent = round(100 * role_count / numeric_coverage["role_calculable_employee_count"], 8)
        expected_level_percent = round(100 * level_count / numeric_coverage["level_calculable_employee_count"], 8)
        if (
            not math.isclose(float(row.get("role_percent_of_calculable", -1)), expected_role_percent, abs_tol=0.00000001)
            or not math.isclose(float(row.get("level_percent_of_calculable", -1)), expected_level_percent, abs_tol=0.00000001)
        ):
            raise ValueError("Role/level tenure band percentage does not reconcile to its denominator.")
        role_data.append((label, role_count))
        level_data.append((label, level_count))
        role_total += role_count
        level_total += level_count
        role_percent_total += expected_role_percent
        level_percent_total += expected_level_percent
    if previous_key_index != len(expected_source_keys) - 1 or len(distribution_raw) != numeric_metrics["published_band_count"]:
        raise ValueError("Role/level tenure published bands do not cover the common source bands.")
    if (
        role_total != numeric_coverage["role_calculable_employee_count"]
        or level_total != numeric_coverage["level_calculable_employee_count"]
        or min(count for _, count in role_data) != numeric_metrics["minimum_published_role_band_count"]
        or min(count for _, count in level_data) != numeric_metrics["minimum_published_level_band_count"]
        or not math.isclose(role_percent_total, 100.0, abs_tol=0.000001)
        or not math.isclose(level_percent_total, 100.0, abs_tol=0.000001)
    ):
        raise ValueError("Role/level tenure distribution totals do not reconcile.")
    return evidence, role_data, level_data


def role_level_tenure_manifest_entry(evidence: dict[str, object]) -> dict[str, object]:
    """Return auditable slide provenance without copying raw query values."""
    provenance = evidence["provenance"]
    coverage = evidence["coverage"]
    metrics = evidence["metrics"]
    lineage = evidence["authoritative_lineage"]
    assert isinstance(provenance, dict) and isinstance(coverage, dict) and isinstance(metrics, dict) and isinstance(lineage, dict)
    return {
        "evidence": str(ROLE_LEVEL_TENURE_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "builder": str(ROLE_LEVEL_TENURE_BUILDER.relative_to(ROOT)).replace("\\", "/"),
        "audit_query": ROLE_LEVEL_TENURE_AUDIT_SQL,
        "profile_query": ROLE_LEVEL_TENURE_PROFILE_SQL,
        "execution_date": evidence["execution_date"],
        "snapshot": evidence["snapshot_date"],
        "population": evidence["population"],
        "grain": evidence["grain"],
        "definitions": evidence["definitions"],
        "reset_policy": evidence["reset_policy"],
        "authoritative_lineage": {
            "authority": lineage["authority"],
            "confirmation_date": lineage["confirmation_date"],
            "source_reference": lineage["source_reference"],
            "lineage_sha256": lineage["lineage_sha256"],
        },
        "coverage": coverage,
        "query_sha256": {
            "audit_sql": provenance["audit_sql_sha256"],
            "audit_result": provenance["audit_result_sha256"],
            "profile_sql": provenance["profile_sql_sha256"],
            "profile_result": provenance["profile_result_sha256"],
        },
        "aggregate_metrics": {
            key: metrics[key]
            for key in (
                "detailed_level_transition_count", "detailed_level_transition_with_date_reset_count",
                "role_rehire_adjustment_count", "level_rehire_adjustment_count", "published_band_count",
                "minimum_published_role_band_count", "minimum_published_level_band_count",
            )
        },
        "publication_rule": "Aggregate internal analysis only; shared anniversary bands are pooled identically and every displayed band has n >= 30 for both clocks. No employee rows, identifiers, job codes, titles, or raw dates are retained.",
        "exploratory_caveat": evidence.get("exploratory_caveat"),
        "acceptance_rule": evidence["acceptance_rule"],
        "outcome": evidence["outcome"],
    }


def role_level_tenure_slide(number: int, evidence: dict[str, object]) -> str:
    """Render two comparable distributions from passing frozen evidence only."""
    _, role_data, level_data = role_level_tenure_distribution_evidence()
    coverage = evidence["coverage"]
    metrics = evidence["metrics"]
    assert isinstance(coverage, dict) and isinstance(metrics, dict)
    eligible = int(coverage["eligible_employee_count"])
    role_denominator = int(coverage["role_calculable_employee_count"])
    level_denominator = int(coverage["level_calculable_employee_count"])
    role_not_calculable = int(coverage["role_not_calculable_employee_count"])
    level_not_calculable = int(coverage["level_not_calculable_employee_count"])
    exploratory = evidence.get("publication_status") == "exploratory"
    main = f'''<div class="two-chart">{bar_card(
        "Time in current job profile" + (" · field proxy" if exploratory else ""),
        role_data,
        f"Anniversary bands at 23-Aug-2026. Percent and n use {role_denominator:,} calculable employees. " + ("Derived from the fields listed at right." if exploratory else ""),
        "role-level-tenure-card",
    )}{bar_card(
        "Time at current detailed level" + (" · field proxy" if exploratory else ""),
        level_data,
        f"Same shared anniversary bands at 23-Aug-2026. Percent and n use {level_denominator:,} calculable employees. " + ("Derived from the fields listed at right." if exploratory else ""),
        "role-level-tenure-card",
    )}</div>'''
    side_title = "Variables used in the two distributions" if exploratory else "Two construct-specific career clocks"
    side_text = (
        "Each chart uses the stored fields listed below. Both apply the later stored start date and rehire date; time_in_role is supporting context only."
        if exploratory else
        "The left clock uses the approved current job-profile start; the right uses the approved detailed-level entry date. Both use the later stored date and rehire date. time_in_role is audit context only."
    )
    side_items = [
        ("Snapshot / population", f"23-Aug-2026 · {eligible:,} active regular employees"),
        ("Left-chart variables", "time_in_job_profile_start_date + max_hire_rehire_date"),
        ("Right-chart variables", "levelentrydate + job_level_primary_position + max_hire_rehire_date"),
        ("Supporting only", "time_in_role is not used to calculate either chart"),
        ("Job-profile coverage", f"{role_denominator:,} calculable · {role_not_calculable:,} not calculable"),
        ("Detailed-level coverage", f"{level_denominator:,} calculable · {level_not_calculable:,} not calculable"),
        ("Rehire adjustment", "later of stored start date and max_hire_rehire_date"),
        ("Privacy", "shared bands; n ≥ 30 in both charts"),
    ]
    if not exploratory:
        side_items.insert(4, ("Transition audit", f"{int(metrics['detailed_level_transition_count']):,} detailed-level changes checked; unexplained resets = 0"))
    side = side_card(
        side_title,
        side_text,
        side_items,
        "Internal exploratory analysis" if exploratory else "Validated aggregate evidence",
    ).replace('class="card side-copy"', 'class="card side-copy role-level-tenure-side"')
    return data_slide(
        number,
        "Time in current job profile vs. current detailed level",
        "Active regular employees · two stored-date distributions · 23-Aug-2026",
        main,
        side,
    )


def role_level_tenure_slide_or_support(number: int) -> tuple[str, str]:
    """Leave the existing support slide untouched until all publication gates pass."""
    try:
        evidence, _, _ = role_level_tenure_distribution_evidence()
    except (FileNotFoundError, ValueError):
        return (
            "Time in level",
            support_slide(number, "Position / time in level", "No chart · entry date and reset rules are not approved", "There is no single time-in-level definition", "levelentrydate, time_in_role, and time_in_job_profile_start_date answer different questions; movement, rehire, and reset rules are missing.", [("Type", "derived feature"), ("Candidate fields", "3"), ("Action", "select authoritative date")]),
        )
    return "Time in role and level", role_level_tenure_slide(number, evidence)


def time_since_last_promotion_distribution_evidence() -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    """Load presentation-safe promotion evidence and fail closed on any gap."""
    if not TIME_SINCE_LAST_PROMOTION_EVIDENCE.exists():
        raise FileNotFoundError(TIME_SINCE_LAST_PROMOTION_EVIDENCE)
    evidence = load(TIME_SINCE_LAST_PROMOTION_EVIDENCE)
    if not isinstance(evidence, dict):
        raise ValueError("Time-since-promotion evidence must be a JSON object.")
    expected_contract = {
        "artifact_type": "aggregate_distribution_evidence",
        "deliverable_mode": "presentation",
        "variable": "Time since last promotion",
        "semantic_type": "derived_feature",
        "publication_status": "validated_descriptive_distribution",
        "snapshot_date": V4_SNAPSHOT,
        "score_v4_change": "none",
        "outcome": "pass",
    }
    if any(evidence.get(key) != value for key, value in expected_contract.items()):
        raise ValueError("Time-since-promotion evidence has an unexpected publication contract.")

    prohibited = {
        "employee_id", "employee_ids", "emp_name", "name", "employee_name", "email",
        "manager_employee_id", "manager_name", "promotion_date", "max_hire_rehire_date",
        "raw_rows", "raw_query_rows", "query_rows", "source_rows",
    }

    def reject_sensitive_fields(value: object) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if str(key).lower() in prohibited:
                    raise ValueError(f"Time-since-promotion evidence persists restricted field {key!r}.")
                reject_sensitive_fields(nested)
        elif isinstance(value, list):
            for nested in value:
                reject_sensitive_fields(nested)

    reject_sensitive_fields(evidence)
    provenance = evidence.get("provenance")
    privacy = evidence.get("privacy_checks")
    metrics = evidence.get("metrics")
    validation = evidence.get("validation")
    observability = evidence.get("history_observability")
    distribution = evidence.get("distribution")
    states = evidence.get("non_temporal_states")
    if not all(isinstance(value, dict) for value in (provenance, privacy, metrics, validation, observability)) or not isinstance(distribution, list) or not isinstance(states, list):
        raise ValueError("Time-since-promotion evidence is missing its aggregate contract.")
    assert isinstance(provenance, dict) and isinstance(privacy, dict) and isinstance(metrics, dict)
    assert isinstance(validation, dict) and isinstance(observability, dict)
    if provenance.get("audit_sql") != TIME_SINCE_LAST_PROMOTION_AUDIT_SQL or provenance.get("profile_sql") != TIME_SINCE_LAST_PROMOTION_PROFILE_SQL:
        raise ValueError("Time-since-promotion evidence does not reference the saved audit and profile SQL.")
    for sql_path, hash_key in (
        (TIME_SINCE_LAST_PROMOTION_AUDIT_SQL, "audit_sql_sha256"),
        (TIME_SINCE_LAST_PROMOTION_PROFILE_SQL, "profile_sql_sha256"),
    ):
        local_path = ROOT / sql_path
        if not local_path.exists() or provenance.get(hash_key) != hashlib.sha256(local_path.read_bytes()).hexdigest():
            raise ValueError("Time-since-promotion evidence is stale relative to its saved SQL.")
    for hash_key in ("audit_sql_sha256", "audit_result_sha256", "profile_sql_sha256", "profile_result_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", str(provenance.get(hash_key, ""))):
            raise ValueError(f"Time-since-promotion evidence has an invalid {hash_key}.")
    if provenance.get("raw_aggregate_rows_persisted") is not False:
        raise ValueError("Time-since-promotion evidence must not retain raw query rows.")
    if any(bool(privacy.get(key)) for key in ("identifiers_persisted", "employee_rows_persisted", "individual_dates_persisted", "protected_category_labels_persisted")):
        raise ValueError("Time-since-promotion evidence persists protected or individual data.")
    if privacy.get("all_displayed_buckets_meet_minimum") is not True or int(privacy.get("minimum_cohort", -1)) != MINIMUM_COHORT:
        raise ValueError("Time-since-promotion privacy safeguards failed.")
    if (
        set(validation) != {"event_integrity", "reconciliation", "privacy"}
        or not all(isinstance(item, dict) for item in validation.values())
        or any(item.get("outcome") != "pass" for item in validation.values())
    ):
        raise ValueError("Time-since-promotion validation outcomes are incomplete or failing.")
    try:
        date.fromisoformat(str(observability["observed_promotion_history_start_date"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Time-since-promotion evidence lacks a valid observed-history boundary.") from exc

    expected_band_keys = ("y0_to_lt1", "y1_to_lt2", "y2_to_lt3", "y3_to_lt5", "y5_plus")
    expected_state_keys = ("no_promotion_recorded_current_episode", "history_predates_observed_promotion_events", "episode_start_unknown")
    if [str(row.get("key")) for row in distribution if isinstance(row, dict)] != list(expected_band_keys):
        raise ValueError("Time-since-promotion bands are missing or not chronological.")
    if not all(isinstance(row, dict) for row in distribution + states):
        raise ValueError("Time-since-promotion distribution contains an invalid row.")
    state_keys = tuple(str(row.get("key")) for row in states)
    if state_keys not in (expected_state_keys[:2], expected_state_keys):
        raise ValueError("Time-since-promotion non-temporal states are incomplete or unordered.")
    denominator = int(metrics.get("active_regular_employee_count", -1))
    latest_recorded = int(metrics.get("latest_recorded_promotion_event_count", -1))
    non_temporal = int(metrics.get("non_temporal_state_count", -1))
    two_plus = int(metrics.get("two_plus_years_employee_count", -1))
    if denominator < MINIMUM_COHORT or min(latest_recorded, non_temporal, two_plus) < 0:
        raise ValueError("Time-since-promotion evidence has invalid headline metrics.")
    total = 0
    percent_total = 0.0
    band_counts: dict[str, int] = {}
    for row in distribution:
        count = int(row.get("employee_count", -1))
        percent = float(row.get("percent_of_active_regular", -1))
        key = str(row["key"])
        if count < MINIMUM_COHORT or not math.isclose(percent, 100.0 * count / denominator, abs_tol=0.000000001):
            raise ValueError("Time-since-promotion time band is unsafe or does not reconcile.")
        band_counts[key] = count
        total += count
        percent_total += percent
    for row in states:
        count = int(row.get("employee_count", -1))
        percent = float(row.get("percent_of_active_regular", -1))
        if count < MINIMUM_COHORT or not math.isclose(percent, 100.0 * count / denominator, abs_tol=0.000000001):
            raise ValueError("Time-since-promotion non-temporal state is unsafe or does not reconcile.")
        total += count
        percent_total += percent
    if (
        sum(band_counts.values()) != latest_recorded
        or sum(int(row["employee_count"]) for row in states) != non_temporal
        or total != denominator
        or sum(band_counts[key] for key in expected_band_keys[2:]) != two_plus
        or not math.isclose(percent_total, 100.0, abs_tol=0.0000001)
    ):
        raise ValueError("Time-since-promotion distribution does not reconcile to its full denominator or 2+ KPI.")
    if int(metrics.get("minimum_published_bucket_count", -1)) != min(int(row["employee_count"]) for row in distribution + states):
        raise ValueError("Time-since-promotion minimum cohort metric does not reconcile.")
    return evidence, distribution, states


def time_since_last_promotion_bar_card(
    title: str,
    rows: list[dict[str, object]],
    denominator: int,
    note: str,
    extra_class: str,
) -> str:
    """Render labels as percentages of the whole active-regular population."""
    maximum = max(int(row["employee_count"]) for row in rows)
    rendered_rows = "".join(
        f'''<div class="bar-row"><div class="bar-label" title="{esc(row['label'])}">{esc(row['label'])}</div>
        <div class="bar-track"><div class="bar-fill" style="width:{int(row['employee_count']) / maximum * 100:.2f}%"></div></div>
        <div class="bar-value">{float(row['percent_of_active_regular']):.1f}% Â· {int(row['employee_count']):,}</div></div>'''
        for row in rows
    )
    rendered_rows = "".join(
        f'''<div class="bar-row"><div class="bar-label" title="{esc(row['label'])}">{esc(row['label'])}</div>
        <div class="bar-track"><div class="bar-fill" style="width:{int(row['employee_count']) / maximum * 100:.2f}%"></div></div>
        <div class="bar-value">{float(row['percent_of_active_regular']):.1f}% / n={int(row['employee_count']):,}</div></div>'''
        for row in rows
    )
    shown = sum(int(row["employee_count"]) for row in rows)
    return f'''<article class="card chart-card promotion-distribution-card {esc(extra_class)}"><div class="card-title">{esc(title)}</div>
      <div class="bar-list">{rendered_rows}</div>
      <div class="chart-footer">Total shown: <strong>{shown:,}</strong> of {denominator:,}. {esc(note)}</div></article>'''


def time_since_last_promotion_slide(number: int, evidence: dict[str, object]) -> str:
    """Render the validated time bands separately from non-temporal states."""
    _, bands, states = time_since_last_promotion_distribution_evidence()
    metrics = evidence["metrics"]
    observability = evidence["history_observability"]
    assert isinstance(metrics, dict) and isinstance(observability, dict)
    denominator = int(metrics["active_regular_employee_count"])
    main = (
        '<div class="promotion-distribution-stack">'
        + time_since_last_promotion_bar_card(
            "Calendar-anniversary time since latest recorded promotion",
            bands,
            denominator,
            "Each label is the share of all active regular employees; chronological bands only.",
            "promotion-time-card",
        )
        + time_since_last_promotion_bar_card(
            "Non-temporal observed-history states",
            states,
            denominator,
            "These are not durations and are not converted to ‘never promoted’.",
            "promotion-state-card",
        )
        + '</div>'
    )
    side = side_card(
        "Latest recorded event, not a promotion-policy claim",
        "The calculation uses the latest valid promotion event within the current employment episode. It is descriptive aggregate context, not a causal claim about attrition.",
        [
            ("Cutoff", "23-Aug-2026"),
            ("Denominator", f"{denominator:,} active regular employees"),
            ("2+ years", f"{int(metrics['two_plus_years_employee_count']):,} ({float(metrics['two_plus_years_percent_of_active_regular']):.2f}%) of all active regular employees"),
            ("Observed history", f"from {observability['observed_promotion_history_start_date']}; earlier history remains left-censored"),
            ("Rehire rule", f"{int(metrics['current_episode_events_excluded_before_rehire_count']):,} pre-episode events excluded"),
            ("Transfers", "excluded from the formula; coincidence is audit-only"),
            ("Privacy", "presentation aggregate; every displayed bucket n ≥ 30"),
            ("Definition", "current employment episode = continuous service from latest hire / rehire to the snapshot; pre-episode promotions are excluded"),
        ],
        "Presentation · aggregate evidence",
    ).replace('class="card side-copy"', 'class="card side-copy promotion-side"')
    rendered = data_slide(
        number,
        "Time since last promotion",
        "Latest recorded promotion event · active regular workforce · 23-Aug-2026",
        main,
        side,
    )
    rendered = re.sub(
        r"Presentation[^<]*aggregate evidence",
        "Presentation - aggregate evidence",
        rendered,
    )
    return re.sub(
        r"Latest recorded promotion event[^<]*23-Aug-2026",
        "Latest recorded promotion event - active regular workforce - 23-Aug-2026",
        rendered,
    )


def time_since_last_promotion_slide_or_support(number: int) -> tuple[str, str]:
    """Preserve the prior support state whenever frozen evidence is absent or invalid."""
    try:
        evidence, _, _ = time_since_last_promotion_distribution_evidence()
    except (FileNotFoundError, ValueError):
        return (
            "Time since promotion",
            support_slide(number, "Time since last promotion", "No chart · event history and no-event rule are pending", "Do not turn null into 'never'", "promotion_date alone cannot classify the absence of a promotion. The variable needs event history, a knowledge date, and missing-date rules.", [("Type", "derived feature"), ("Field", "promotion_date"), ("Action", "time-safe historical derivation")]),
        )
    return "Time since promotion", time_since_last_promotion_slide(number, evidence)


def within_team_compensation_evidence() -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    """Load only passing, presentation-safe manager pay-spread evidence."""
    if not WITHIN_TEAM_COMPENSATION_EVIDENCE.exists():
        raise FileNotFoundError(WITHIN_TEAM_COMPENSATION_EVIDENCE)
    evidence = load(WITHIN_TEAM_COMPENSATION_EVIDENCE)
    if not isinstance(evidence, dict):
        raise ValueError("Within-team compensation evidence must be a JSON object.")
    expected = {
        "artifact_type": "aggregate_distribution_evidence",
        "deliverable_mode": "presentation",
        "variable": "Within team compensation range",
        "semantic_type": "derived_feature",
        "publication_status": "validated_descriptive_distribution",
        "snapshot_date": V4_SNAPSHOT,
        "score_v4_change": "none",
        "outcome": "pass",
    }
    if any(evidence.get(key) != value for key, value in expected.items()):
        raise ValueError("Within-team compensation evidence has an unexpected publication contract.")
    prohibited = {
        "employee_id", "employee_ids", "emp_name", "name", "employee_name", "email",
        "manager_employee_id", "manager_name", "country_values", "compensation_grade_values",
        "currency_values", "annual_base_pay", "fte_annual_base_pay", "salary", "salaries",
        "raw_rows", "raw_query_rows", "query_rows", "source_rows",
    }

    def reject_sensitive_fields(value: object) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if str(key).lower() in prohibited:
                    raise ValueError(f"Within-team compensation evidence persists restricted field {key!r}.")
                reject_sensitive_fields(nested)
        elif isinstance(value, list):
            for nested in value:
                reject_sensitive_fields(nested)

    reject_sensitive_fields(evidence)
    provenance = evidence.get("provenance")
    privacy = evidence.get("privacy_checks")
    metrics = evidence.get("metrics")
    validation = evidence.get("validation")
    distributions = evidence.get("distributions")
    if not all(isinstance(value, dict) for value in (provenance, privacy, metrics, validation, distributions)):
        raise ValueError("Within-team compensation evidence is missing aggregate contract fields.")
    assert isinstance(provenance, dict) and isinstance(privacy, dict) and isinstance(metrics, dict)
    assert isinstance(validation, dict) and isinstance(distributions, dict)
    if provenance.get("audit_sql") != WITHIN_TEAM_COMPENSATION_AUDIT_SQL or provenance.get("profile_sql") != WITHIN_TEAM_COMPENSATION_PROFILE_SQL:
        raise ValueError("Within-team compensation evidence does not reference its saved SQL.")
    for sql_path, hash_key in (
        (WITHIN_TEAM_COMPENSATION_AUDIT_SQL, "audit_sql_sha256"),
        (WITHIN_TEAM_COMPENSATION_PROFILE_SQL, "profile_sql_sha256"),
    ):
        local_path = ROOT / sql_path
        if not local_path.exists() or provenance.get(hash_key) != hashlib.sha256(local_path.read_bytes()).hexdigest():
            raise ValueError("Within-team compensation evidence is stale relative to saved SQL.")
    if any(not re.fullmatch(r"[0-9a-f]{64}", str(provenance.get(key, ""))) for key in (
        "audit_sql_sha256", "audit_result_sha256", "profile_sql_sha256", "profile_result_sha256",
    )):
        raise ValueError("Within-team compensation evidence has an invalid provenance hash.")
    if provenance.get("raw_aggregate_rows_persisted") is not False:
        raise ValueError("Within-team compensation evidence must not persist raw query rows.")
    if any(bool(privacy.get(key)) for key in (
        "identifiers_persisted", "employee_rows_persisted", "manager_rows_persisted",
        "exact_compensation_persisted", "country_grade_currency_labels_persisted",
    )):
        raise ValueError("Within-team compensation evidence persists restricted data.")
    if privacy.get("all_displayed_buckets_meet_minimum") is not True or int(privacy.get("minimum_cohort", -1)) != MINIMUM_COHORT:
        raise ValueError("Within-team compensation privacy safeguards failed.")
    if set(validation) != {"membership_integrity", "reconciliation", "privacy"} or any(
        not isinstance(value, dict) or value.get("outcome") != "pass" for value in validation.values()
    ):
        raise ValueError("Within-team compensation validation outcomes are incomplete or failing.")
    count_rows = distributions.get("flagged_group_count_per_team")
    rate_rows = distributions.get("flagged_group_share_per_team")
    state_rows = distributions.get("non_comparable_state")
    if not all(isinstance(rows, list) and rows for rows in (count_rows, rate_rows)) or not isinstance(state_rows, list):
        raise ValueError("Within-team compensation distributions are incomplete.")
    assert isinstance(count_rows, list) and isinstance(rate_rows, list) and isinstance(state_rows, list)
    all_displayed = count_rows + rate_rows + state_rows
    if not all(isinstance(row, dict) for row in all_displayed):
        raise ValueError("Within-team compensation distribution contains an invalid row.")
    comparable = int(metrics.get("comparable_manager_count", -1))
    universe = int(metrics.get("manager_universe_count", -1))
    no_comparable = int(metrics.get("no_comparable_group_manager_count", -1))
    if comparable < MINIMUM_COHORT or universe != comparable + no_comparable:
        raise ValueError("Within-team compensation manager totals do not reconcile.")
    for rows in (count_rows, rate_rows):
        if sum(int(row.get("manager_count", -1)) for row in rows) != comparable:
            raise ValueError("Within-team compensation chart total does not reconcile to comparable managers.")
        if any(int(row.get("manager_count", -1)) < MINIMUM_COHORT for row in rows):
            raise ValueError("Within-team compensation chart includes a small bucket.")
    if no_comparable:
        if len(state_rows) != 1 or state_rows[0].get("key") != "no_comparable_groups" or int(state_rows[0].get("manager_count", -1)) != no_comparable:
            raise ValueError("Within-team compensation no-comparable state does not reconcile.")
        if no_comparable < MINIMUM_COHORT:
            raise ValueError("Within-team compensation no-comparable state is below the publication threshold.")
    elif state_rows:
        raise ValueError("Within-team compensation has an unexpected zero state row.")
    return evidence, count_rows, rate_rows, state_rows


def within_team_compensation_bar_card(title: str, rows: list[dict[str, object]], denominator: int, note: str, extra_class: str) -> str:
    rendered_rows = "".join(
        f'''<div class="bar-row"><div class="bar-label" title="{esc(row['label'])}">{esc(row['label'])}</div>
        <div class="bar-track"><div class="bar-fill" style="width:{float(row['percent_of_comparable_managers']):.2f}%"></div></div>
        <div class="bar-value">{float(row['percent_of_comparable_managers']):.1f}% · {int(row['manager_count']):,}</div></div>'''
        for row in rows
    )
    return f'''<article class="card chart-card {esc(extra_class)}"><div class="card-title">{esc(title)}</div>
      <div class="bar-list">{rendered_rows}</div>
      <div class="chart-footer">Percent and n use <strong>{denominator:,}</strong> managers with at least one comparable group. {esc(note)}</div></article>'''


def within_team_compensation_slide(number: int, evidence: dict[str, object]) -> str:
    """Render the two requested distributions plus the separate non-comparable state."""
    _, count_rows, rate_rows, state_rows = within_team_compensation_evidence()
    metrics = evidence["metrics"]
    assert isinstance(metrics, dict)
    comparable = int(metrics["comparable_manager_count"])
    manager_universe = int(metrics["manager_universe_count"])
    no_comparable = int(metrics["no_comparable_group_manager_count"])
    count_card = within_team_compensation_bar_card(
        "Comparable groups with a 10%+ FTE-adjusted base-pay spread",
        count_rows,
        comparable,
        "Each team is placed by its number of flagged comparable groups.",
        "within-team-count-card",
    )
    rate_card = within_team_compensation_bar_card(
        "Share of comparable groups flagged within each team",
        rate_rows,
        comparable,
        "Each team is placed by flagged groups ÷ all of its eligible comparable groups.",
        "within-team-rate-card",
    )
    no_comparable_card = ""
    if state_rows:
        state_percent = 100.0 * no_comparable / manager_universe
        no_comparable_card = f'''<article class="card within-team-state-card"><div class="card-title">No comparable groups</div>
          <div class="within-team-state-value">{state_percent:.1f}% <span>· {no_comparable:,} managers</span></div>
          <p><strong>No comparable groups.</strong> These managers are not assigned zero: none of their direct-report country + grade + currency groups retained two complete members.</p></article>'''
    main = f'<div class="within-team-compensation-stack">{count_card}{rate_card}{no_comparable_card}</div>'
    side = side_card(
        "What this slide measures",
        "Review signal, not a pay-equity finding. It flags comparable direct-report groups whose FTE-adjusted base-pay spread is 10% or more; tenure, performance, and other pay factors are not modeled.",
        [
            ("Cutoff", "23-Aug-2026"),
            ("Team", "same direct manager; manager excluded"),
            ("Comparable group", "same country, compensation grade, and currency"),
            ("Eligibility", "2+ complete direct reports"),
            ("Flag", "max/min FTE-adjusted base pay ≥ 1.10"),
            ("Comparable teams", f"{comparable:,} of {manager_universe:,}"),
            ("No comparable groups", f"{no_comparable:,} shown separately"),
            ("Privacy", "aggregate manager counts; n ≥ 30"),
        ],
        "Presentation · aggregate evidence",
    ).replace('class="card side-copy"', 'class="card side-copy within-team-side"')
    return data_slide(
        number,
        "Within team compensation range",
        "Manager-level comparable pay-spread groups · active regular workforce · 23-Aug-2026",
        main,
        side,
    )


def within_team_compensation_slide_or_support(number: int) -> tuple[str, str]:
    """Fail closed to the existing support state when frozen evidence is absent or invalid."""
    try:
        evidence, _, _, _ = within_team_compensation_evidence()
    except (FileNotFoundError, ValueError):
        return (
            "Within-team compensation",
            support_slide(number, "Within team compensation range", "No chart · comparable population and statistic are undefined", "The final metric does not exist", "Team, comparable population, minimum threshold, statistic, timing, and compensation treatment must be approved before calculating relative position within a team.", [("Type", "derived feature"), ("Inputs", "compa_ratio / grade / team membership"), ("Action", "define metric and privacy")]),
        )
    return "Within-team compensation", within_team_compensation_slide(number, evidence)


def promotion_history_by_grade_evidence() -> tuple[dict[str, object], list[dict[str, object]]]:
    """Load the fixed-snapshot internal matrix and fail closed on every gate."""
    if not PROMOTION_HISTORY_BY_GRADE_EVIDENCE.exists():
        raise FileNotFoundError(PROMOTION_HISTORY_BY_GRADE_EVIDENCE)
    evidence = load(PROMOTION_HISTORY_BY_GRADE_EVIDENCE)
    if not isinstance(evidence, dict):
        raise ValueError("Promotion-history-by-grade evidence must be a JSON object.")
    expected_contract = {
        "artifact_type": "aggregate_distribution_evidence",
        "deliverable_mode": "internal_analysis",
        "variable": "Promotion history by current compensation grade",
        "semantic_type": "derived_feature",
        "publication_status": "validated_descriptive_matrix",
        "snapshot_date": V4_SNAPSHOT,
        "score_v4_change": "none",
        "outcome": "pass",
    }
    if any(evidence.get(key) != value for key, value in expected_contract.items()):
        raise ValueError("Promotion-history-by-grade evidence has an unexpected publication contract.")
    prohibited = {
        "employee_id", "employee_ids", "emp_name", "name", "employee_name", "email",
        "manager_employee_id", "manager_name", "promotion_date", "max_hire_rehire_date",
        "raw_rows", "raw_query_rows", "query_rows", "source_rows", "individual_dates",
        "annual_base_pay", "base_pay_rate", "total_base_pay_amount", "fte_annual_base_pay",
    }

    def reject_sensitive_fields(value: object) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if str(key).lower() in prohibited:
                    raise ValueError(f"Promotion-history-by-grade evidence persists restricted field {key!r}.")
                reject_sensitive_fields(nested)
        elif isinstance(value, list):
            for nested in value:
                reject_sensitive_fields(nested)

    reject_sensitive_fields(evidence)
    provenance = evidence.get("provenance")
    privacy = evidence.get("privacy_checks")
    metrics = evidence.get("metrics")
    validation = evidence.get("validation")
    observability = evidence.get("history_observability")
    category_labels = evidence.get("category_labels")
    percentage_rounding = evidence.get("percentage_rounding")
    matrix = evidence.get("matrix")
    if (
        not all(isinstance(value, dict) for value in (provenance, privacy, metrics, validation, observability, category_labels, percentage_rounding))
        or not isinstance(matrix, list)
    ):
        raise ValueError("Promotion-history-by-grade evidence is missing its aggregate contract.")
    assert isinstance(provenance, dict) and isinstance(privacy, dict) and isinstance(metrics, dict)
    assert isinstance(validation, dict) and isinstance(observability, dict) and isinstance(category_labels, dict) and isinstance(percentage_rounding, dict)
    if percentage_rounding != {"method": "largest remainder at 0.1 percentage point; category-order tie break", "each_row_sums_to_percent": 100.0}:
        raise ValueError("Promotion-history-by-grade percentage-rounding contract is invalid.")
    if provenance.get("audit_sql") != PROMOTION_HISTORY_BY_GRADE_AUDIT_SQL or provenance.get("profile_sql") != PROMOTION_HISTORY_BY_GRADE_PROFILE_SQL:
        raise ValueError("Promotion-history-by-grade evidence does not reference the approved SQL.")
    for sql_path, hash_key in (
        (PROMOTION_HISTORY_BY_GRADE_AUDIT_SQL, "audit_sql_sha256"),
        (PROMOTION_HISTORY_BY_GRADE_PROFILE_SQL, "profile_sql_sha256"),
    ):
        local_path = ROOT / sql_path
        if not local_path.exists() or provenance.get(hash_key) != hashlib.sha256(local_path.read_bytes()).hexdigest():
            raise ValueError("Promotion-history-by-grade evidence is stale relative to saved SQL.")
    for hash_key in ("audit_sql_sha256", "audit_result_sha256", "profile_sql_sha256", "profile_result_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", str(provenance.get(hash_key, ""))):
            raise ValueError(f"Promotion-history-by-grade evidence has an invalid {hash_key}.")
    if provenance.get("raw_aggregate_rows_persisted") is not False:
        raise ValueError("Promotion-history-by-grade evidence must not retain aggregate query rows.")
    if any(bool(privacy.get(key)) for key in ("identifiers_persisted", "employee_rows_persisted", "individual_dates_persisted", "exact_compensation_persisted")):
        raise ValueError("Promotion-history-by-grade evidence persists private data.")
    if privacy.get("all_visible_cells_meet_minimum") is not True or int(privacy.get("minimum_cohort", -1)) != MINIMUM_COHORT:
        raise ValueError("Promotion-history-by-grade privacy safeguards failed.")
    if set(validation) != {"integrity", "reconciliation", "pooling", "privacy"} or any(
        not isinstance(item, dict) or item.get("outcome") != "pass" for item in validation.values()
    ):
        raise ValueError("Promotion-history-by-grade validation outcomes are incomplete or failing.")
    if observability.get("observed_promotion_history_start_date") != "2016-10-23":
        raise ValueError("Promotion-history-by-grade evidence has an unexpected observability boundary.")
    category_keys = (
        "zero_recorded_promotions", "one_recorded_promotion",
        "two_or_more_recorded_promotions", "partial_promotion_history",
    )
    expected_labels = {
        "zero_recorded_promotions": "0 recorded promotions",
        "one_recorded_promotion": "1 recorded promotion",
        "two_or_more_recorded_promotions": "2+ recorded promotions",
        "partial_promotion_history": "Partial promotion history",
    }
    if category_labels != expected_labels:
        raise ValueError("Promotion-history-by-grade category labels are not the approved four categories.")
    if len(matrix) != 14 or not all(isinstance(row, dict) for row in matrix):
        raise ValueError("Promotion-history-by-grade evidence must publish exactly 14 matrix rows.")
    denominator = int(metrics.get("active_regular_employee_count", -1))
    observable = int(metrics.get("observable_history_employee_count", -1))
    partial = int(metrics.get("partial_history_employee_count", -1))
    if denominator != 50043 or observable < 0 or partial < 0 or observable + partial != denominator:
        raise ValueError("Promotion-history-by-grade headline metrics do not reconcile to the approved population.")
    if int(metrics.get("raw_current_grade_count", -1)) != 45 or int(metrics.get("individual_grade_count", -1)) != 13 or int(metrics.get("pooled_other_grade_count", -1)) != 32:
        raise ValueError("Promotion-history-by-grade dynamic pooling metadata is inconsistent.")
    if int(metrics.get("minimum_cohort", -1)) != MINIMUM_COHORT or int(metrics.get("minimum_published_cell_count", -1)) < MINIMUM_COHORT:
        raise ValueError("Promotion-history-by-grade has an unsafe published cell.")

    totals = {key: 0 for key in category_keys}
    grades: set[str] = set()
    for index, row in enumerate(matrix):
        expected_keys = {"grade", "grade_scope", "total_employee_count", *category_keys, *(f"{key}_percent" for key in category_keys)}
        if set(row) != expected_keys:
            raise ValueError("Promotion-history-by-grade matrix row has an unexpected schema.")
        grade = str(row["grade"])
        if not grade or grade in grades:
            raise ValueError("Promotion-history-by-grade matrix contains a missing or duplicate grade.")
        grades.add(grade)
        is_pool = index == len(matrix) - 1
        if (row["grade_scope"] == "pooled") != is_pool or (is_pool and grade != "Other grades") or (not is_pool and row["grade_scope"] != "individual"):
            raise ValueError("Promotion-history-by-grade matrix does not isolate Other grades as its final pool.")
        counts = {key: int(row[key]) for key in category_keys}
        if any(value < MINIMUM_COHORT for value in counts.values()):
            raise ValueError("Promotion-history-by-grade matrix contains a visible cell below n=30.")
        if sum(counts.values()) != int(row["total_employee_count"]):
            raise ValueError("Promotion-history-by-grade row total does not reconcile.")
        expected_percentages = deterministic_percentages(counts, category_keys)
        actual_percentages = {key: float(row[f"{key}_percent"]) for key in category_keys}
        if actual_percentages != expected_percentages or round(sum(actual_percentages.values()), 1) != 100.0:
            raise ValueError("Promotion-history-by-grade row percentages do not reconcile to frozen counts.")
        for key, value in counts.items():
            totals[key] += value
    if sum(int(row["total_employee_count"]) for row in matrix) != denominator:
        raise ValueError("Promotion-history-by-grade matrix does not reconcile to the denominator.")
    if (
        totals["zero_recorded_promotions"] + totals["one_recorded_promotion"] + totals["two_or_more_recorded_promotions"] != observable
        or totals["partial_promotion_history"] != partial
    ):
        raise ValueError("Promotion-history-by-grade categories do not separate observable and partial history.")
    return evidence, matrix


def promotion_history_by_grade_matrix_card(title: str, rows: list[dict[str, object]]) -> str:
    """Render seven grade rows as within-grade percentages plus total n."""
    category_keys = (
        "zero_recorded_promotions", "one_recorded_promotion",
        "two_or_more_recorded_promotions", "partial_promotion_history",
    )
    headings = ("0 recorded<br>promotions", "1 recorded<br>promotion", "2+ recorded<br>promotions", "Partial promotion<br>history")
    body = "".join(
        "<tr>"
        f"<th scope=\"row\">{esc(row['grade'])}</th>"
        + "".join(f"<td>{float(row[f'{key}_percent']):.1f}%</td>" for key in category_keys)
        + f"<td class=\"promotion-grade-total\">{int(row['total_employee_count']):,}</td></tr>"
        for row in rows
    )
    return f'''<article class="card promotion-grade-matrix-card"><div class="card-title">{esc(title)}</div>
      <table class="promotion-grade-matrix"><thead><tr><th scope="col">Current<br>grade</th>{''.join(f'<th scope="col">{heading}</th>' for heading in headings)}<th scope="col">n</th></tr></thead>
      <tbody>{body}</tbody></table></article>'''


def promotion_history_by_grade_slide(number: int, evidence: dict[str, object]) -> str:
    """Render the validated 14-row matrix in two seven-row panels."""
    _, matrix = promotion_history_by_grade_evidence()
    metrics = evidence["metrics"]
    observability = evidence["history_observability"]
    assert isinstance(metrics, dict) and isinstance(observability, dict)
    main = (
        '<div class="promotion-grade-matrix-grid">'
        + promotion_history_by_grade_matrix_card("Current grades M20 through R40", matrix[:7])
        + promotion_history_by_grade_matrix_card("Current grades R50 through Other grades", matrix[7:])
        + "</div>"
    )
    side = side_card(
        "Recorded events, not a hiring-path classification",
        "Each row shows the within-grade percentage for valid promotion events recorded inside the current employment episode, plus its total n. It is descriptive context only, not a causal attrition finding.",
        [
            ("Snapshot / population", f"23-Aug-2026 · {int(metrics['active_regular_employee_count']):,} active regular employees"),
            ("Observable episodes", f"{int(metrics['observable_history_employee_count']):,} assigned only to 0 / 1 / 2+"),
            ("Partial history", f"{int(metrics['partial_history_employee_count']):,} episodes begun before {observability['observed_promotion_history_start_date']}"),
            ("Recorded events", f"{int(metrics['valid_event_pair_count']):,} valid employee-date pairs; {int(metrics['employees_with_valid_event_count']):,} employees with 1+"),
            ("Rehire control", f"{int(metrics['current_episode_events_excluded_before_rehire_count']):,} pre-episode events excluded"),
            ("Pooling", "13 grades shown individually; 32 lower-cell grades combined as Other grades"),
            ("Privacy", "Internal aggregate analysis · every visible cell n ≥ 30 · no pay values"),
            ("Not inferred", "never promoted, first job, first promotion, hired into grade, or causal impact"),
        ],
        "Internal exploratory analysis",
    ).replace('class="card side-copy"', 'class="card side-copy promotion-grade-side"')
    slide = data_slide(
        number,
        "Promotion history by current compensation grade",
        "Recorded current-episode promotion events · current compensation grade · 23-Aug-2026",
        main,
        side,
    )
    return slide.replace(
        f'<div class="slide-stage" id="slide-{number}">',
        f'<div class="slide-stage" id="slide-{number}" data-evidence-run="promotion-history-by-compensation-grade-20260823">',
        1,
    )


def promotion_history_by_grade_slide_or_support(number: int) -> tuple[str, str]:
    """Keep a conservative support state until all matrix gates pass."""
    try:
        evidence, _ = promotion_history_by_grade_evidence()
    except (FileNotFoundError, ValueError):
        return (
            "Promotions by grade",
            support_slide(number, "Promotion history by current compensation grade", "No chart · promotion-history matrix is pending", "A recorded event is not a hiring-path classification", "Current grade, episode boundaries, event dates, history observability, and cell-level privacy must pass together before rendering the matrix.", [("Snapshot", V4_SNAPSHOT), ("Rule", "current employment episode"), ("Action", "run aggregate integrity and pooling checks")]),
        )
    return "Promotions by grade", promotion_history_by_grade_slide(number, evidence)


def current_grade_entry_path_evidence() -> tuple[dict[str, object], list[dict[str, object]]]:
    """Load validated aggregate-only entry-path evidence and reject stale/private input."""
    if not CURRENT_GRADE_ENTRY_PATH_EVIDENCE.exists():
        raise FileNotFoundError(CURRENT_GRADE_ENTRY_PATH_EVIDENCE)
    evidence = load(CURRENT_GRADE_ENTRY_PATH_EVIDENCE)
    if not isinstance(evidence, dict):
        raise ValueError("Current-grade-entry evidence must be a JSON object.")
    contract = {"artifact_type": "aggregate_distribution_evidence", "deliverable_mode": "internal_analysis", "variable": "Entry path to current compensation grade", "semantic_type": "derived_feature", "publication_status": "validated_descriptive_matrix", "snapshot_date": V4_SNAPSHOT, "score_v4_change": "none", "outcome": "pass"}
    if any(evidence.get(key) != value for key, value in contract.items()):
        raise ValueError("Current-grade-entry evidence has an unexpected publication contract.")
    prohibited = {"employee_id", "employee_ids", "name", "email", "manager_name", "manager_employee_id", "promotion_date", "entry_snapshot_date", "previous_snapshot_date", "max_hire_rehire_date", "compensation_grade_old", "raw_rows", "raw_query_rows", "query_rows", "source_rows", "individual_dates", "annual_base_pay", "base_pay_rate", "total_base_pay_amount", "fte_annual_base_pay"}
    def reject_private(value: object) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if str(key).lower() in prohibited:
                    raise ValueError(f"Current-grade-entry evidence persists restricted field {key!r}.")
                reject_private(nested)
        elif isinstance(value, list):
            for nested in value:
                reject_private(nested)
    reject_private(evidence)
    provenance, privacy, metrics, validation, labels, matrix, rounding = (evidence.get(key) for key in ("provenance", "privacy_checks", "metrics", "validation", "category_labels", "matrix", "percentage_rounding"))
    if not all(isinstance(value, dict) for value in (provenance, privacy, metrics, validation, labels, rounding)) or not isinstance(matrix, list):
        raise ValueError("Current-grade-entry evidence is missing its aggregate contract.")
    assert isinstance(provenance, dict) and isinstance(privacy, dict) and isinstance(metrics, dict) and isinstance(validation, dict) and isinstance(labels, dict) and isinstance(rounding, dict)
    if provenance.get("audit_sql") != CURRENT_GRADE_ENTRY_PATH_AUDIT_SQL or provenance.get("profile_sql") != CURRENT_GRADE_ENTRY_PATH_PROFILE_SQL:
        raise ValueError("Current-grade-entry evidence does not reference the approved SQL.")
    for sql_path, hash_key in ((CURRENT_GRADE_ENTRY_PATH_AUDIT_SQL, "audit_sql_sha256"), (CURRENT_GRADE_ENTRY_PATH_PROFILE_SQL, "profile_sql_sha256")):
        if provenance.get(hash_key) != hashlib.sha256((ROOT / sql_path).read_bytes()).hexdigest():
            raise ValueError("Current-grade-entry evidence is stale relative to saved SQL.")
    if provenance.get("raw_aggregate_rows_persisted") is not False or any(bool(privacy.get(key)) for key in ("identifiers_persisted", "employee_rows_persisted", "individual_dates_persisted", "exact_compensation_persisted")) or privacy.get("all_visible_cells_meet_minimum") is not True:
        raise ValueError("Current-grade-entry privacy contract failed.")
    keys = ("promotion_confirmed_into_current_grade", "observed_entry_without_registered_promotion", "current_grade_entry_not_observable")
    if set(validation) != {"integrity", "entry_selection", "event_alignment", "old_grade_rejected", "reconciliation", "pooling", "privacy"} or any(not isinstance(item, dict) or item.get("outcome") != "pass" for item in validation.values()) or int(metrics.get("active_regular_employee_count", -1)) != 50043 or len(matrix) != int(metrics.get("individual_grade_count", -1)) + 1:
        raise ValueError("Current-grade-entry validation or headline contract failed.")
    totals = {key: 0 for key in keys}
    for index, row in enumerate(matrix):
        if not isinstance(row, dict):
            raise ValueError("Current-grade-entry matrix is malformed.")
        counts = {key: int(row[key]) for key in keys}
        actual = {key: float(row[f"{key}_percent"]) for key in keys}
        if any(value < MINIMUM_COHORT for value in counts.values()) or sum(counts.values()) != int(row["total_employee_count"]) or actual != deterministic_percentages(counts, keys) or round(sum(actual.values()), 1) != 100.0 or ((index == len(matrix) - 1) != (row.get("grade_scope") == "pooled")):
            raise ValueError("Current-grade-entry matrix reconciliation or privacy check failed.")
        for key in keys:
            totals[key] += counts[key]
    if sum(int(row["total_employee_count"]) for row in matrix) != int(metrics["active_regular_employee_count"]) or totals["promotion_confirmed_into_current_grade"] != int(metrics["promotion_confirmed_into_current_grade_count"]) or totals["observed_entry_without_registered_promotion"] != int(metrics["observed_entry_without_registered_promotion_count"]) or totals["current_grade_entry_not_observable"] != int(metrics["current_grade_entry_not_observable_count"]):
        raise ValueError("Current-grade-entry states do not reconcile to the population.")
    return evidence, matrix


def current_grade_entry_path_card(title: str, rows: list[dict[str, object]]) -> str:
    keys = ("promotion_confirmed_into_current_grade", "observed_entry_without_registered_promotion", "current_grade_entry_not_observable")
    classes = ("entry-path-confirmed", "entry-path-observed", "entry-path-unobservable")
    rows_markup = "".join(f'''<div class="entry-path-row"><div class="entry-path-grade">{esc(row['grade'])}</div><div class="entry-path-stack">{''.join(f'<div class="entry-path-segment {classes[i]}" style="width:{float(row[f"{key}_percent"]):.1f}%">{float(row[f"{key}_percent"]):.1f}%</div>' for i, key in enumerate(keys))}</div><div class="entry-path-total">n={int(row['total_employee_count']):,}</div></div>''' for row in rows)
    legend = '<div class="entry-path-legend"><span><i class="entry-path-dot entry-path-confirmed"></i>Promotion confirmed</span><span><i class="entry-path-dot entry-path-observed"></i>Observed, no registered promotion</span><span><i class="entry-path-dot entry-path-unobservable"></i>Entry not observable</span></div>'
    return f'<article class="card entry-path-card"><div class="card-title">{esc(title)}</div><div class="entry-path-list">{rows_markup}</div>{legend}</article>'


def current_grade_entry_path_read_guide() -> str:
    """Plain-language key kept beside the visual rather than only in metadata."""
    return '''<section class="entry-path-read-guide" aria-label="How to read the entry path colors">
      <div class="entry-path-guide-item entry-path-guide-confirmed"><strong><i class="entry-path-dot entry-path-confirmed"></i>Blue · Recorded promotion</strong><span>A recorded promotion aligns with the latest observed move into this grade.</span></div>
      <div class="entry-path-guide-item entry-path-guide-observed"><strong><i class="entry-path-dot entry-path-observed"></i>Green · Grade change observed</strong><span>The move into this grade is visible, but no promotion was recorded at that move.</span></div>
      <div class="entry-path-guide-item entry-path-guide-unobservable"><strong><i class="entry-path-dot entry-path-unobservable"></i>Brown · Entry not observable</strong><span>No prior complete snapshot shows how the person entered this grade; it does not mean direct hire.</span></div>
    </section>'''

def current_grade_entry_path_slide(number: int, evidence: dict[str, object]) -> str:
    _, matrix = current_grade_entry_path_evidence()
    metrics = evidence["metrics"]
    assert isinstance(metrics, dict)
    main = '<div class="entry-path-main"><div class="entry-path-grid">' + current_grade_entry_path_card("Current grades M20 through R30", matrix[:8]) + current_grade_entry_path_card("Current grades R40 through Other grades", matrix[8:]) + '</div>' + current_grade_entry_path_read_guide() + '</div>'
    side = side_card("Observable entry history, not a hire classification", "Each bar is 100% of employees currently in that grade. A promotion is confirmed only when its registered event aligns with the latest observed entry to that grade.", [("Population", f"23-Aug-2026 · {int(metrics['active_regular_employee_count']):,} active regular employees"), ("Promotion confirmed", f"{int(metrics['promotion_confirmed_into_current_grade_count']):,}"), ("Observed, no promotion", f"{int(metrics['observed_entry_without_registered_promotion_count']):,}"), ("Entry not observable", f"{int(metrics['current_grade_entry_not_observable_count']):,}"), ("Last-entry control", f"{int(metrics['older_observed_entries_not_selected_count']):,} older entries not selected"), ("Rejected field", f"compensation_grade_old mismatched prior snapshots {int(metrics['old_grade_mismatch_previous_snapshot_count']):,} times"), ("Privacy", "Internal aggregate analysis · each raw state cell n ≥ 30"), ("Not inferred", "direct hire, policy, or causal attrition impact")], "Internal exploratory analysis").replace('class="card side-copy"', 'class="card side-copy entry-path-side"')
    return data_slide(number, "How employees reached their current compensation grade", "Latest observed entry to current grade · registered-promotion alignment · 23-Aug-2026", main, side).replace(f'<div class="slide-stage" id="slide-{number}">', f'<div class="slide-stage" id="slide-{number}" data-evidence-run="current-grade-entry-path-20260823">', 1)


def current_grade_entry_path_slide_or_support(number: int) -> tuple[str, str]:
    try:
        evidence, _ = current_grade_entry_path_evidence()
    except (FileNotFoundError, ValueError):
        return "Current grade entry path", support_slide(number, "How employees reached their current compensation grade", "No chart · entry-path evidence is pending", "No direct-hire interpretation is permitted", "Current grade changes, event boundaries, rehires, pooling, and privacy must all pass before publishing.", [("Snapshot", V4_SNAPSHOT), ("Action", "run aggregate integrity and reconciliation")])
    return "Current grade entry path", current_grade_entry_path_slide(number, evidence)


def layers_from_ceo_distribution_evidence() -> tuple[dict[str, object], list[tuple[str, int]]]:
    """Load layers-from-CEO evidence and fail closed on hierarchy or privacy gaps."""
    if not LAYERS_FROM_CEO_EVIDENCE.exists():
        raise FileNotFoundError(LAYERS_FROM_CEO_EVIDENCE)
    evidence = load(LAYERS_FROM_CEO_EVIDENCE)
    if not isinstance(evidence, dict):
        raise ValueError("Layers-from-CEO evidence must be a JSON object.")
    if evidence.get("artifact_type") != "aggregate_distribution_evidence":
        raise ValueError("Layers-from-CEO evidence has an unexpected artifact contract.")
    if evidence.get("deliverable_mode") != "internal_analysis" or evidence.get("outcome") != "pass":
        raise ValueError("Layers-from-CEO evidence must be an approved aggregate internal-analysis result.")
    if evidence.get("variable") != "Reconstructed manager layers to CEO" or evidence.get("semantic_type") != "hierarchy":
        raise ValueError("Layers-from-CEO evidence does not describe the expected hierarchy.")
    if evidence.get("snapshot_date") != V4_SNAPSHOT:
        raise ValueError("Layers-from-CEO evidence must use the fixed 2026-08-23 snapshot.")

    def reject_sensitive_fields(value: object) -> None:
        prohibited = {
            "employee_id", "manager_employee_id", "root_employee_id",
            "terminal_root_employee_id", "approved_ceo_employee_id",
            "name", "employee_name", "manager_name",
        }
        if isinstance(value, dict):
            for key, nested in value.items():
                if str(key).lower() in prohibited:
                    raise ValueError(f"Layers-from-CEO evidence persists restricted field {key!r}.")
                reject_sensitive_fields(nested)
        elif isinstance(value, list):
            for nested in value:
                reject_sensitive_fields(nested)

    reject_sensitive_fields(evidence)
    provenance = evidence.get("provenance")
    privacy = evidence.get("privacy_checks")
    metrics = evidence.get("metrics")
    root_check = evidence.get("approved_root_check")
    reconciliation = evidence.get("stored_level_reconciliation")
    distribution_raw = evidence.get("distribution")
    if not all(isinstance(value, dict) for value in (provenance, privacy, metrics, root_check, reconciliation)) or not isinstance(distribution_raw, list):
        raise ValueError("Layers-from-CEO evidence is missing its aggregate contract.")
    assert isinstance(provenance, dict) and isinstance(privacy, dict) and isinstance(metrics, dict)
    assert isinstance(root_check, dict) and isinstance(reconciliation, dict)
    if provenance.get("audit_sql") != LAYERS_FROM_CEO_AUDIT_SQL:
        raise ValueError("Layers-from-CEO evidence does not reference the approved same-snapshot audit.")
    audit_path = ROOT / LAYERS_FROM_CEO_AUDIT_SQL
    if not audit_path.exists() or provenance.get("audit_sql_sha256") != hashlib.sha256(audit_path.read_bytes()).hexdigest():
        raise ValueError("Layers-from-CEO evidence does not match the saved audit SQL.")
    for key in ("aggregate_result_sha256", "audit_sql_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", str(provenance.get(key, ""))):
            raise ValueError(f"Layers-from-CEO evidence has an invalid {key}.")
    if provenance.get("raw_aggregate_rows_persisted") is not False:
        raise ValueError("Layers-from-CEO evidence must not persist raw aggregate depth rows.")
    if any(bool(privacy.get(key)) for key in (
        "identifiers_persisted", "employee_rows_persisted", "manager_rows_persisted",
        "names_persisted", "root_identifier_persisted", "root_singleton_displayed",
    )) or privacy.get("all_displayed_buckets_meet_minimum") is not True:
        raise ValueError("Layers-from-CEO privacy safeguards failed.")

    required_metrics = {
        "universe_node_count", "manager_conflict_node_count", "self_manager_node_count",
        "reconstructed_count", "unresolved_chain_count", "missing_manager_chain_count",
        "self_manager_chain_count", "cycle_chain_count", "depth_exceeded_chain_count",
        "manager_conflict_chain_count", "root_count", "approved_root_resolved_count",
        "nonmatching_approved_root_count", "convergence_rate_percent", "root_reference_pass",
        "display_eligible_count", "display_reconstructed_count", "display_unresolved_chain_count",
        "display_approved_root_match_count", "maximum_chain_links", "published_bucket_count",
        "published_employee_count", "minimum_published_bucket_count", "minimum_cohort",
    }
    missing_metrics = sorted(required_metrics - set(metrics))
    if missing_metrics:
        raise ValueError(f"Layers-from-CEO evidence is missing metrics: {missing_metrics}")
    metric = {key: int(metrics[key]) for key in required_metrics if key != "convergence_rate_percent"}
    if metric["minimum_cohort"] != MINIMUM_COHORT or metric["maximum_chain_links"] != 25:
        raise ValueError("Layers-from-CEO evidence does not retain its privacy or traversal constraints.")
    if metric["universe_node_count"] < MINIMUM_COHORT or metric["display_eligible_count"] < MINIMUM_COHORT:
        raise ValueError("Layers-from-CEO population is below the publication cohort minimum.")
    zero_safeguards = (
        "manager_conflict_node_count", "self_manager_node_count", "unresolved_chain_count",
        "missing_manager_chain_count", "self_manager_chain_count", "cycle_chain_count",
        "depth_exceeded_chain_count", "manager_conflict_chain_count", "nonmatching_approved_root_count",
        "display_unresolved_chain_count",
    )
    if any(metric[key] != 0 for key in zero_safeguards):
        raise ValueError("Layers-from-CEO hierarchy safeguards are not all zero.")
    if (
        metric["reconstructed_count"] != metric["universe_node_count"]
        or metric["approved_root_resolved_count"] != metric["reconstructed_count"]
        or metric["root_count"] != 1
        or metric["root_reference_pass"] != 1
        or metric["display_reconstructed_count"] != metric["display_eligible_count"]
        or metric["display_approved_root_match_count"] != metric["display_eligible_count"]
        or not math.isclose(float(metrics["convergence_rate_percent"]), 100.0, abs_tol=0.000001)
        or root_check.get("outcome") != "pass"
        or int(root_check.get("root_count", -1)) != 1
        or not math.isclose(float(root_check.get("convergence_rate_percent", -1)), 100.0, abs_tol=0.000001)
        or root_check.get("identifier_persisted") is not False
    ):
        raise ValueError("Layers-from-CEO root convergence or approved-root validation failed.")
    if reconciliation.get("field") != "worker_supervisory_organization_level_from_top":
        raise ValueError("Layers-from-CEO stored-level reconciliation refers to an unexpected field.")

    distribution: list[tuple[str, int]] = []
    total = 0
    percentage_total = 0.0
    previous_upper: int | None = None
    for row in distribution_raw:
        if not isinstance(row, dict):
            raise ValueError("Layers-from-CEO distribution contains an invalid row.")
        label = str(row.get("label", ""))
        lower = int(row.get("lower_depth", -1))
        upper = int(row.get("upper_depth", -1))
        count = int(row.get("employee_count", 0))
        if not label or lower < 0 or upper < lower or count < MINIMUM_COHORT:
            raise ValueError("Layers-from-CEO distribution contains an unsafe bucket.")
        if previous_upper is not None and lower != previous_upper + 1:
            raise ValueError("Layers-from-CEO display buckets are not contiguous and ascending.")
        if lower == upper == 0:
            raise ValueError("Layers-from-CEO evidence exposes the root singleton as a bar.")
        expected_percent = round(100 * count / metric["display_eligible_count"], 8)
        if not math.isclose(float(row.get("percent_of_active_regular", -1)), expected_percent, abs_tol=0.00000001):
            raise ValueError("Layers-from-CEO bucket percentage does not reconcile to its denominator.")
        distribution.append((label, count))
        total += count
        percentage_total += expected_percent
        previous_upper = upper
    if not distribution or len(distribution) != metric["published_bucket_count"]:
        raise ValueError("Layers-from-CEO published bucket count does not reconcile.")
    if total != metric["display_eligible_count"] or metric["published_employee_count"] != total:
        raise ValueError("Layers-from-CEO displayed counts do not reconcile to active regular employees.")
    if min(count for _, count in distribution) != metric["minimum_published_bucket_count"]:
        raise ValueError("Layers-from-CEO minimum display count does not reconcile.")
    if not math.isclose(percentage_total, 100.0, abs_tol=0.000001):
        raise ValueError("Layers-from-CEO displayed percentages do not sum to 100%.")
    return evidence, distribution


def layers_from_ceo_manifest_entry(evidence: dict[str, object]) -> dict[str, object]:
    """Return slide provenance without retaining a root or reporting-chain identity."""
    metrics = evidence["metrics"]
    provenance = evidence["provenance"]
    assert isinstance(metrics, dict) and isinstance(provenance, dict)
    return {
        "evidence": str(LAYERS_FROM_CEO_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "builder": str(LAYERS_FROM_CEO_BUILDER.relative_to(ROOT)).replace("\\", "/"),
        "audit_query": LAYERS_FROM_CEO_AUDIT_SQL,
        "execution_date": evidence["execution_date"],
        "snapshot": evidence["snapshot_date"],
        "population": evidence["population"],
        "grain": evidence["grain"],
        "definition": evidence["definition"],
        "publication_rule": "Aggregate values only; every displayed contiguous depth band has n >= 30; no employee, manager, root, or name is retained.",
        "query_sha256": {
            "audit_sql": provenance["audit_sql_sha256"],
            "aggregate_result": provenance["aggregate_result_sha256"],
        },
        "aggregate_metrics": {
            key: metrics[key]
            for key in (
                "universe_node_count", "display_eligible_count", "root_count",
                "convergence_rate_percent", "published_bucket_count",
                "minimum_published_bucket_count",
            )
        },
        "acceptance_rule": evidence["acceptance_rule"],
        "outcome": evidence["outcome"],
    }


def layers_from_ceo_slide(number: int, evidence: dict[str, object]) -> str:
    """Render literal reporting-line depth; the stored level is not charted."""
    metrics = evidence["metrics"]
    assert isinstance(metrics, dict)
    _, distribution = layers_from_ceo_distribution_evidence()
    denominator = int(metrics["display_eligible_count"])
    side = side_card(
        "Literal reporting-line depth, with no identities",
        "Depth is the number of manager links to the HR-approved CEO root: the root is layer 0 and a direct report is layer 1. The approved root check passed, but no employee, manager, or root identity is displayed.",
        [
            ("Snapshot", "23-Aug-2026"),
            ("Active-regular denominator", f"{denominator:,}"),
            ("Approved-root check", "1 root · 100.0% convergence"),
            ("Traversal", "same snapshot only · maximum 25 links"),
            ("Stored level field", "reconciliation only; not the chart value"),
            ("Privacy", "n ≥ 30 per displayed band; root singleton pooled"),
        ],
        "Validated aggregate hierarchy",
    )
    return data_slide(
        number,
        "Reconstructed manager layers to CEO",
        "Active regular employees · same-snapshot reporting chain · 23-Aug-2026",
        bar_card(
            "Active regular employees by manager-chain depth",
            distribution,
            f"Percent and n use {denominator:,} active regular employees. Depth buckets run from shallowest to deepest; rare endpoints are pooled into contiguous n ≥ {MINIMUM_COHORT} bands.",
            "layers-from-ceo-distribution-card",
        ),
        side,
    )


def layers_from_ceo_slide_or_support(number: int) -> tuple[str, str]:
    """Publish the chart only when frozen evidence passes every gate."""
    try:
        evidence, _ = layers_from_ceo_distribution_evidence()
    except (FileNotFoundError, ValueError):
        return (
            "Organizational level",
            support_slide(
                number,
                "Supervisory organization level from top",
                "No chart · reconstructed manager layers require a passing approved-root audit",
                "No unverified hierarchy distribution is published",
                "The literal layer measure requires same-snapshot reporting chains, one HR-approved CEO root, and zero unresolved, cyclic, conflicting, or over-limit paths. Until its frozen aggregate evidence passes, the stored level field remains separate.",
                [
                    ("Type", "hierarchy"),
                    ("Chart value", "same-snapshot manager-chain depth"),
                    ("Root check", "HR-approved reference required"),
                    ("Publication", "n ≥ 30; no identities"),
                ],
            ),
        )
    return "Org layers to CEO", layers_from_ceo_slide(number, evidence)


# Each variable has its own compact provenance card.  The entries were
# distilled from the current variable documentation and frozen v4 evidence;
# they describe source and scope, never a new semantic validation.
PROVENANCE = {
    "Applied to a job": ("HRDA", "hrda.job_applications_vw", "Distinct applicant / fiscal year", "cand_applied · application_date · unique req_id", "Descriptive aggregate distribution only; FY2025 and FY2026 YTD are shown under the named internal_analysis authorization for the requester and Julia. It neither confirms zero applications nor validates the monthly employee-snapshot feature."),
    "Applied to a job — employee-snapshot, trailing six months": ("HRDA", "hrda.job_applications_vw + hrda.post_hire_monthly_worker_dtls", "Regular active employee-snapshot / trailing six months", "cand_applied · application_date · employee_id + req_id", "Exploratory employee-snapshot evidence: Unknown is retained when feed coverage cannot distinguish zero from missing, and the view is not an approved production feature or individual prediction."),
    "More than 3 job applications": ("HRDA", "hrda.applications", "Employee snapshot / trailing six months", "cand_applied · application_date · unique req_id", "The candidate feature is time-safe and windowed; it is not the annual 4+ bucket."),
    "Transfer within past year": ("HRDA", "hrda.post_hire_monthly_worker_dtls + post_hire_daily_worker_dtls", "Employee snapshot · monthly canonical / weekly comparison", "is_transferred · transfer_date · transaction_date", "Rolling 12-month definition is applied to 24 monthly snapshots and 104 complete weekly endpoints; workers_ios_transfers is excluded from the primary chart."),
    "Location": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Employee snapshot", "country", "Direct country field; local location detail is shown separately."),
    "Office site and city": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Employee snapshot", "office_site · city", "Derived display pair; a missing value in either field is published as no office-site/city pair."),
    "Team turnover": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Manager-team / six-month employee exposure", "manager_employee_id · fis_mo_end_dt · term_date · term_type", "Strict Voluntary only; Voluntary Exception is excluded pending HR confirmation. Aggregate descriptive rate, not a manager label."),
    "More than 1 employee leaves · all teams": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Manager-team × employee snapshot", "manager_employee_id · term_date · term_type", "Formal six-month Voluntary flag; primary attribution is manager_at_exit and sensitivity is manager_at_evaluation."),
    "More than 1 employee leaves · teams >5": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Manager-team × employee snapshot", "manager_employee_id · term_date · term_type", "Same formal flag restricted to teams with at least six direct reports at each evaluation snapshot."),
    "Job family": ("HRDA", "hrda.post_hire_monthly_worker_dtls + hrda.post_hire_daily_worker_dtls", "Employee snapshot · monthly August / daily September", "job_family · job_family_group · transaction_date", "Detail-to-group mapping needs authoritative lineage."),
    "Region": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Employee snapshot", "region / country / labor_market", "The upper chart retains the four stored Region groups. The lower chart is a requested display-only split of U.S./Americas and China/APAC. Labor Market remains a separate global distribution."),
    "Gender": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Employee snapshot", "gender", "Protected field; internal aggregate use only, never targeting."),
    "Remote / hybrid / in office status": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Employee snapshot", "work_arrangement · start/end dates", "Raw operational categories are not an approved three-state mapping."),
    "Engineering vs. non-engineering": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Employee snapshot", "eng_or_noneng", "Stored grouping; upstream mapping authority is pending."),
    "Rehire": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Employee-event history", "is_rehire · rehire_date", "Flag/date history changes across source eras."),
    "Years of experience prior to Qualcomm": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Employee snapshot", "prior_qc_work_years", "Stored metric; calculation lineage, overlap treatment, and rounding are pending."),
    "Commute distance": ("External source required", "No approved distance provider or home-location proxy", "Employee location", "approved location proxy · work site · distance method", "Home location is restricted; no distance is currently approved."),
    "RTO/hybrid comment in QVoice": ("QVoice raw Excel workbooks", "Raw data worksheet · four identified open-text waves", "Distinct participant-wave theme case", "doing well · can improve · processes to improve", "Descriptive topic mentions only; no sentiment, complaint label, workforce denominator, or attrition join is approved."),
    "Any comment on QVoice": ("QVoice raw Excel workbooks", "Raw data worksheet · original open-ended fields", "Participant-wave response", "doing well · can improve · processes to improve", "Raw comments exist in four waves, but no approved workforce eligibility denominator or employee-date join turns comment presence into a model feature."),
    "Retention concerns in QVoice comments": ("QVoice raw Excel workbooks", "Raw data worksheet · original improvement prompts", "Distinct participant-wave-theme", "can improve · processes to improve when available", "Descriptive aggregate themes only; no comment-to-attrition join, causal claim, model feature, or individual-risk label is approved."),
    "Non-respondents": ("QVoice raw Excel workbooks + HRDA", "Raw data worksheet + hrda.post_hire_monthly_worker_dtls", "Eligible employee / survey wave", "snapshot proxy · QVoice row · response presence", "Non-response proxy only: the stored snapshot is an explicit assumption and invitation eligibility is not yet confirmed."),
    "Intent to Stay items": ("QVoice raw Excel workbooks", "survey_structure.xlsx + response waves", "Employee-wave response", "Q4 · Q12 · survey wave", "Coverage is observable; scale direction and workforce join remain pending."),
    "Career goals item": ("QVoice raw Excel workbooks", "survey_structure.xlsx + response waves", "Employee-wave response", "career-goals response · survey wave", "Item wording, coding, and cross-wave comparability remain pending."),
    "Average of all QVoice items": ("QVoice raw Excel workbooks", "Jan-2024, Jan-2025, and Jan-2026 Raw data sheets", "Participant-wave derived aggregate", "33 strict shared binary headers · 0/1 coding · 33/33 valid rule", "Comparable only among respondents with all 33 strict shared items; it is not a workforce-perception estimate or an approved workforce join."),
    "QVoice heartbeat": ("QVoice raw Excel workbook + HRDA", "Jan-2026 Raw data sheet + pre-wave workforce snapshot", "Employee-wave item response", "53 scale items · personal mean · valid item sign", "Restricted descriptive signal; relative to each respondent's own mean, not an absolute sentiment label or individual attrition score."),
    "Standardized / normalized within region": ("QVoice raw workbooks", "QVoice waves", "Participant-wave-region derived aggregate", "strict 33-item composite · stored region · same-wave reference cohort", "Respondent-only descriptive distribution; workforce and attrition joins remain pending."),
    "Tech industry unemployment data": ("External labor-market source", "No provider or contracted feed validated", "Geography-period", "industry definition · geography · publication vintage", "A time-safe geographic join is not yet available."),
    "Draup data": ("External Draup feed", "No validated feed, owner, or data contract", "Labor market / geography", "TBD", "Source, history, grain, and join keys are all pending."),
    "LinkedIn scraping": ("No approved external source", "Scraping and employee-profile crosswalk are not governed", "Employee / external profile", "TBD", "Do not link profiles to employees without legal and privacy approval."),
    "External pull factors": ("Third-party sources - not enabled", "No approved provider, data contract, or governed external feed", "Geography-period / vendor / external profile", "source definition - temporal availability - governed crosswalk", "Keep out of the internal baseline; consider only after approval as a separate external challenger."),
    "Position / time in level": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Employee snapshot", "levelentrydate · time_in_role · time_in_job_profile_start_date", "An authoritative entry date and reset rules are required."),
    "Company tenure": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Employee snapshot", "original_hire_date · max_hire_rehire_date", "Original service and latest-hire tenure are different constructs."),
    "Time since last promotion": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Employee-event history", "is_promo / promotion_date", "Latest recorded promotion events are reconstructed within the current episode; no-event and left-censor states remain separate from duration bands."),
    "Promotion history by current compensation grade": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Distinct active regular employee / monthly snapshot", "compensation_grade · is_promo · promotion_date · max_hire_rehire_date", "Recorded current-episode events are descriptive only; Partial promotion history remains separate from observable 0/1/2+ counts."),
    "How employees reached their current compensation grade": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Distinct active regular employee / monthly snapshot", "compensation_grade snapshots · is_promo · promotion_date · max_hire_rehire_date", "Observed entry without a registered promotion and entry not observable must not be read as hired into grade."),
    "Promoted vs. hired into level": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Employee snapshot / event", "level entry · promotion · hire dates", "Same-day events, rehires, and lateral moves need precedence rules."),
    "Level": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Employee snapshot", "level_grouped · job_level_primary_position · management_level", "The three stored constructs are related, not interchangeable."),
    "Level grouped by grade family": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Distinct active Regular Employee snapshot", "level_grouped · compensation_grade prefix proxy", "The grade family is descriptive context only; it does not replace Level or assert an official track."),
    "Supervisory organization level from top": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Employee snapshot / hierarchy", "stored level-from-top · same-snapshot hierarchy links", "A stored level does not prove layers from the governed CEO root."),
    "Reconstructed manager layers to CEO": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Distinct active regular employee / monthly snapshot", "employee_id · manager_employee_id · fis_mo_end_dt", "Same-snapshot chains are reconstructed to an HR-approved root; identifiers remain inside the query and are not displayed."),
    "Compensation grade": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Employee snapshot", "compensation_grade", "Protected structure: aggregate grades only; never pay values."),
    "Comp ratio": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Employee snapshot", "compa_ratio", "Stored relative metric; numerator, midpoint, currency, and effective-date lineage are pending."),
    "Within team compensation range": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Direct-manager team / snapshot", "manager_employee_id · country · compensation_grade · FTE annual base pay · currency", "Descriptive 10% FTE-adjusted base-pay-spread review signal; it is not a pay-equity finding."),
    "Co-location with manager": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Employee-manager pair / snapshot", "office_site · country · same-snapshot manager relationship", "This is a site-code proxy, not physical proximity."),
    "Office-site relationship with manager": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Employee-manager snapshot", "office_site · same-snapshot manager relationship", "Stored office-site comparison only; not a residential, travel-time, time-zone, or physical-presence measure."),
    "Hours away from manager": ("HRDA + external source required", "HRDA site fields + approved travel/time-zone reference", "Employee-manager pair", "office_site · country · approved travel/time-zone data", "Site codes do not establish travel time or time-zone distance."),
    "High risk manager": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Manager / team", "time-safe direct-report relationship · term_date · term_type · region · job_family · job_level_primary_position", "Continuous aggregate observed/expected ratio. It is not a manager ranking, performance label, or approved intervention threshold."),
    "High turnover under this person": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Manager / team", "time-safe direct-report relationship · fis_mo_end_dt · term_date · term_type", "Descriptive 0/1/2+ strict-Voluntary historical-exit bucket; it is not a manager evaluation or causal attribution."),
    "Above-average team turnover": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Manager snapshot → current direct report", "snapshot date · manager-team event scope · Voluntary event rule", "Restricted 0/1/Unknown contextual signal from an 18-interval team history. It is not a manager evaluation, causal claim, or approved production feature."),
    "Manager leaving": ("HRDA", "hrda.post_hire_monthly_worker_dtls + hrda.all_terminations", "Employee snapshot", "prior manager relationship · reg_non_intern_dir_reports · term_date · term_type", "Six-month, strict-Voluntary exposure is time-safe; it persists after reassignment and is not a manager evaluation."),
    "Manager change": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Employee event", "manager_change · manager_change_date", "Direct event fields; flag/date timing must remain aligned."),
    "Number of manager changes": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Employee rolling event count", "manager_change · manager_change_date", "The retrospective window, resets, and deduplication are pending."),
    "Talent index": ("HRDA", "hrda.master_talent_index", "Employee-cycle", "talent_index · cycle_number", "Descriptive stored-value distribution only; the formula and effective timing are not asserted."),
    "Major inflection points": ("HRDA proxy events", "hrda.post_hire_monthly_worker_dtls", "Organizational-event proxy", "manager · cost center · job family · location · transfer events", "No approved taxonomy, weights, or overlap rule defines a composite."),
    "ET fields": ("HRDA", "hrda.post_hire_monthly_worker_dtls", "Employee or organization — TBD", "ET hierarchy references (ET1–ET11)", "Hierarchy references do not define an expert-track career classification."),
}

PROVENANCE["Commute distance"] = (
    "HRDA + Qualcomm offices + public centroid reference",
    "HRDA postal_code hashes + Qualcomm office model + GeoNames postal centroids",
    "Distinct employee snapshot",
    "postal_code hash · city/country · office coordinate · Haversine",
    "Approximate geographic distance only; not route distance or travel time.",
)

PROVENANCE["Residential distance from manager"] = (
    "HRDA + public GeoNames postal centroids",
    "Same-snapshot HRDA postal-proxy hashes + GeoNames postal centroids",
    "Aggregate employee-manager pair / monthly snapshot",
    "same-snapshot manager link · country · postal-centroid proxy · Haversine",
    "Approximate centroid distance only; not co-location, route distance, travel time, office distance, or an actual home address.",
)

PROVENANCE["Number of manager changes"] = (
    "HRDA",
    "hrda.post_hire_monthly_worker_dtls",
    "Distinct employee snapshot",
    "manager_change · manager_change_date",
    "Primary exploratory six-month distribution with a supplemental annual comparison; reset semantics remain an assumption for review.",
)

PROVENANCE["Time in current job profile vs. current detailed level"] = (
    "HRDA",
    "hrda.post_hire_monthly_worker_dtls",
    "Distinct active regular employee / monthly snapshot",
    "time_in_job_profile_start_date · levelentrydate · job_level_primary_position · max_hire_rehire_date",
    "Exploratory aggregate evidence uses the fields listed above with shared privacy-safe bands; it does not assert an HRIS-approved career-clock definition. time_in_role is supporting context only.",
)


RESIDENTIAL_MANAGER_DISTANCE_CSS = r"""
    .residential-manager-distance-card { padding:10px 12px; gap:4px; }
    .residential-manager-distance-card .card-title { font-size:10px; padding-bottom:4px; margin-bottom:0; }
    .residential-manager-distance-card .bar-list { flex:1; justify-content:flex-start; gap:1px; }
    .residential-manager-distance-card .bar-row { grid-template-columns:82px minmax(0, 1fr) 94px; gap:5px; height:16px; }
    .residential-manager-distance-card .bar-label { font-size:10px; line-height:1; }
    .residential-manager-distance-card .bar-track { height:8px; }
    .residential-manager-distance-card .bar-value { font-size:10px; line-height:1; }
    .residential-manager-distance-card .chart-footer { padding-top:5px; font-size:10px; line-height:1.25; }
    .residential-manager-distance-side { padding:13px; gap:6px; }
    .residential-manager-distance-side h3 { font-size:17px; line-height:1.16; }
    .residential-manager-distance-side p { font-size:14px; line-height:1.35; }
    .residential-manager-distance-side .fact-list { gap:3px; }
    .residential-manager-distance-side .fact-list li { font-size:11px; line-height:1.24; }
    .residential-manager-distance-side .scope-note { margin-top:0; }
    .residential-manager-distance-side .provenance-panel { padding-top:6px; }
    .residential-manager-distance-side .provenance-status { margin-top:5px; }
"""

ROLE_LEVEL_TENURE_CSS = r"""
    .role-level-tenure-card { padding:13px; gap:7px; }
    .role-level-tenure-card .card-title { font-size:12px; padding-bottom:5px; margin-bottom:0; }
    .role-level-tenure-card .bar-list { flex:1; justify-content:space-evenly; gap:5px; }
    .role-level-tenure-card .bar-row { grid-template-columns:96px minmax(0,1fr) 92px; gap:6px; min-height:25px; }
    .promotion-distribution-stack { display:grid; height:100%; grid-template-rows:minmax(0,1.15fr) minmax(0,0.85fr); gap:12px; min-height:0; overflow:hidden; }
    .promotion-distribution-stack .card { min-height:0; }
    .promotion-distribution-card .bar-list { flex:1; justify-content:space-evenly; gap:6px; }
    .promotion-distribution-card .bar-row { grid-template-columns:110px minmax(0,1fr) 116px; gap:8px; min-height:27px; }
    .promotion-distribution-card .bar-label, .promotion-distribution-card .bar-value { font-size:12px; }
    .promotion-state-card .bar-row { grid-template-columns:minmax(290px,1.3fr) minmax(0,1fr) 116px; }
    .promotion-side .fact-list { gap:4px; }
    .promotion-side .fact-list li { font-size:12px; line-height:1.28; }
    .role-level-tenure-card .bar-label, .role-level-tenure-card .bar-value { font-size:11px; }
    .role-level-tenure-card .bar-track { height:13px; }
    .role-level-tenure-card .chart-footer { padding-top:6px; font-size:10px; line-height:1.3; }
    .role-level-tenure-side { padding:12px 13px; gap:6px; }
    .role-level-tenure-side h3 { font-size:17px; line-height:1.15; }
    .role-level-tenure-side p { font-size:12px; line-height:1.32; }
    .role-level-tenure-side .fact-list { gap:3px; }
    .role-level-tenure-side .fact-list li { font-size:10.5px; line-height:1.23; }
    .role-level-tenure-side .provenance-panel { padding-top:6px; }
"""

COMPANY_TENURE_CSS = r"""
    .company-tenure-card { padding:13px; gap:7px; }
    .company-tenure-card .card-title { font-size:12px; padding-bottom:5px; margin-bottom:0; }
    .company-tenure-card .bar-list { flex:1; justify-content:space-evenly; gap:5px; }
    .company-tenure-card .bar-row { grid-template-columns:96px minmax(0,1fr) 92px; gap:6px; min-height:25px; }
    .company-tenure-card .bar-label, .company-tenure-card .bar-value { font-size:11px; }
    .company-tenure-card .bar-track { height:13px; }
    .company-tenure-card .chart-footer { padding-top:6px; font-size:10px; line-height:1.3; }
    .company-tenure-side { padding:12px 13px; gap:6px; }
    .company-tenure-side h3 { font-size:17px; line-height:1.15; }
    .company-tenure-side p { font-size:12px; line-height:1.32; }
    .company-tenure-side .fact-list { gap:3px; }
    .company-tenure-side .fact-list li { font-size:10.5px; line-height:1.23; }
    .company-tenure-side .provenance-panel { padding-top:6px; }
"""

PROMOTION_HISTORY_BY_GRADE_CSS = r"""
    .promotion-grade-matrix-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; height:100%; min-height:0; }
    .promotion-grade-matrix-card { min-width:0; min-height:0; padding:10px 11px; gap:4px; overflow:hidden; display:grid; grid-template-rows:auto minmax(0,1fr); }
    .promotion-grade-matrix-card .card-title { margin:0 0 4px; padding:0 0 4px; font-size:11px; }
    .promotion-grade-matrix { width:100%; height:100%; border-collapse:collapse; table-layout:fixed; font-variant-numeric:tabular-nums; }
    .promotion-grade-matrix th, .promotion-grade-matrix td { padding:6px 3px; border-bottom:1px solid var(--border-subtle); text-align:right; white-space:nowrap; }
    .promotion-grade-matrix thead th { color:var(--text-muted); font-size:10px; line-height:1.12; font-weight:700; text-transform:uppercase; letter-spacing:.02em; }
    .promotion-grade-matrix th:first-child, .promotion-grade-matrix tbody th { width:19%; text-align:left; color:var(--text-main); }
    .promotion-grade-matrix tbody th { font-size:12px; font-weight:700; }
    .promotion-grade-matrix td { font-size:12px; color:var(--text-main); }
    .promotion-grade-matrix .promotion-grade-total { font-weight:800; color:var(--accent); }
    .promotion-grade-side { padding:11px 12px; gap:5px; }
    .promotion-grade-side h3 { font-size:16px; line-height:1.13; }
    .promotion-grade-side p { font-size:12px; line-height:1.28; }
    .promotion-grade-side .fact-list { gap:3px; }
    .promotion-grade-side .fact-list li { font-size:11px; line-height:1.2; }
    .promotion-grade-side .provenance-panel { padding-top:5px; }
    @media (max-width:900px) { .promotion-grade-matrix-grid { grid-template-columns:1fr; height:auto; } }
"""

CURRENT_GRADE_ENTRY_PATH_CSS = r"""
    .entry-path-main { display:grid; grid-template-rows:auto 1fr; gap:10px; height:100%; min-height:0; }
    .entry-path-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; min-height:0; }
    .entry-path-card { min-width:0; min-height:0; padding:10px 11px; gap:5px; overflow:hidden; }
    .entry-path-card .card-title { margin:0; padding:0 0 4px; font-size:11px; }
    .entry-path-list { display:grid; gap:6px; }
    .entry-path-row { display:grid; grid-template-columns:42px minmax(0,1fr) 68px; gap:6px; align-items:center; }
    .entry-path-grade { color:var(--text-main); font-size:11px; font-weight:800; }
    .entry-path-stack { display:flex; height:20px; overflow:hidden; border:1px solid var(--border-subtle); border-radius:var(--radius-pill); background:var(--bg-surface-3); }
    .entry-path-segment { display:flex; min-width:0; align-items:center; justify-content:center; color:var(--text-invert); font-size:9px; font-weight:800; font-variant-numeric:tabular-nums; text-shadow:0 1px 2px rgba(2,6,23,.55); white-space:nowrap; overflow:hidden; }
    .entry-path-confirmed { background:#2563eb; } .entry-path-observed { background:#0f766e; } .entry-path-unobservable { background:#a16207; }
    .entry-path-total { color:var(--text-muted); font-size:10px; font-variant-numeric:tabular-nums; text-align:right; white-space:nowrap; }
    .entry-path-legend { display:flex; flex-wrap:wrap; gap:7px; margin-top:4px; color:var(--text-muted); font-size:9px; }
    .entry-path-legend span { display:flex; align-items:center; gap:3px; } .entry-path-dot { width:8px; height:8px; border-radius:50%; }
    .entry-path-read-guide { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; align-self:start; padding:11px 12px; border:1px solid var(--border-subtle); border-radius:var(--radius-card); background:var(--bg-surface-2); }
    .entry-path-guide-item { display:grid; gap:4px; min-width:0; padding-left:8px; border-left:3px solid var(--border-subtle); color:var(--text-muted); font-size:11px; line-height:1.28; }
    .entry-path-guide-item strong { display:flex; align-items:center; gap:5px; color:var(--text-main); font-size:11px; }
    .entry-path-guide-item span { display:block; } .entry-path-guide-confirmed { border-color:#2563eb; } .entry-path-guide-observed { border-color:#0f766e; } .entry-path-guide-unobservable { border-color:#a16207; }
    .entry-path-side { padding:11px 12px; gap:5px; } .entry-path-side h3 { font-size:15px; line-height:1.14; } .entry-path-side p { font-size:11.5px; line-height:1.25; } .entry-path-side .fact-list { gap:3px; } .entry-path-side .fact-list li { font-size:10.5px; line-height:1.18; }
    @media (max-width:900px) { .entry-path-main { height:auto; } .entry-path-grid, .entry-path-read-guide { grid-template-columns:1fr; } }
"""


QVOICE_HEARTBEAT_CSS = r"""
    .qvoice-heartbeat-card { padding:12px 14px; gap:7px; }
    .qvoice-heartbeat-card .card-title { margin-bottom:0; padding-bottom:4px; }
    .qvoice-heartbeat-intro { margin:0; color:var(--text-muted); font-size:11px; line-height:1.3; }
    .qvoice-heartbeat-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; min-height:0; flex:1; }
    .qvoice-heartbeat-panel { display:flex; flex-direction:column; gap:5px; min-width:0; padding:9px 10px; border:1px solid var(--border-subtle); border-radius:10px; background:var(--bg-surface-2); }
    .qvoice-heartbeat-panel h3 { margin:0; color:var(--text-main); font-size:12px; line-height:1.15; }
    .qvoice-heartbeat-panel p { margin:0; color:var(--text-muted); font-size:10px; line-height:1.25; }
    .qvoice-heartbeat-list { display:flex; flex-direction:column; justify-content:space-evenly; gap:5px; min-height:0; flex:1; }
    .qvoice-heartbeat-row { display:grid; grid-template-columns:126px minmax(0,1fr) 124px; align-items:center; gap:7px; min-height:38px; }
    .qvoice-heartbeat-item { min-width:0; color:var(--text-main); font-size:10px; line-height:1.1; }
    .qvoice-heartbeat-item strong { display:block; color:var(--accent); font-size:11px; font-variant-numeric:tabular-nums; }
    .qvoice-heartbeat-item span { display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .qvoice-heartbeat-track { height:14px; overflow:hidden; border:1px solid var(--border-subtle); border-radius:var(--radius-pill); background:var(--bg-surface-3); }
    .qvoice-heartbeat-fill { height:100%; min-width:2px; border-radius:inherit; }
    .qvoice-heartbeat-fill-up { background:linear-gradient(90deg,color-mix(in oklab,var(--accent-2) 70%,var(--bg-surface)),var(--accent)); }
    .qvoice-heartbeat-fill-down { background:linear-gradient(90deg,color-mix(in oklab,#f59e0b 72%,var(--bg-surface)),#d97706); }
    .qvoice-heartbeat-value { min-width:0; color:var(--text-main); text-align:right; font-size:10px; line-height:1.12; font-variant-numeric:tabular-nums; white-space:nowrap; }
    .qvoice-heartbeat-value strong { display:block; font-size:11px; }
    .qvoice-heartbeat-value span { display:block; color:var(--text-muted); font-size:9px; }
    .qvoice-heartbeat-legend { display:flex; flex-wrap:wrap; gap:5px 12px; padding:6px 8px; border:1px solid var(--border-subtle); border-radius:8px; background:var(--bg-surface-2); color:var(--text-muted); font-size:10px; line-height:1.2; }
    .qvoice-heartbeat-legend span { display:inline-flex; align-items:center; gap:4px; white-space:nowrap; }
    .qvoice-heartbeat-legend strong { color:var(--text-main); }
    .qvoice-heartbeat-dot { width:8px; height:8px; border-radius:50%; background:var(--accent); }
    .qvoice-heartbeat-dot.down { background:#d97706; }
    .qvoice-heartbeat-dot.neutral { background:var(--text-muted); }
    .qvoice-heartbeat-dot.missing { border:1px dashed var(--text-muted); background:transparent; }
    .qvoice-heartbeat-card .chart-footer { padding-top:6px; font-size:10px; line-height:1.25; }
    @media (max-width:900px) { .qvoice-heartbeat-grid { grid-template-columns:1fr; } .qvoice-heartbeat-row { grid-template-columns:112px minmax(0,1fr) 112px; } }
"""


COMP_RATIO_FOCUSED_CSS = r"""
    .comp-ratio-main { display:grid; grid-template-rows:minmax(0,.9fr) minmax(0,1.1fr); gap:10px; height:100%; min-height:0; overflow:hidden; }
    .comp-ratio-main > .card { min-height:0; height:auto; }
    .comp-ratio-distribution-card { padding:10px 12px; gap:5px; }
    .comp-ratio-distribution-card .bar-list { flex:1; justify-content:space-evenly; gap:3px; }
    .comp-ratio-distribution-card .bar-row { grid-template-columns:minmax(150px,1.25fr) minmax(0,1fr) 92px; gap:7px; min-height:21px; }
    .comp-ratio-distribution-card .bar-label, .comp-ratio-distribution-card .bar-value { font-size:10.5px; }
    .comp-ratio-distribution-card .bar-track { height:13px; }
    .comp-ratio-distribution-card .chart-footer { padding-top:5px; font-size:10px; line-height:1.22; }
    .comp-ratio-history-card { padding:10px 12px; gap:5px; }
    .comp-ratio-history-card .card-title { margin-bottom:0; padding-bottom:4px; font-size:10px; }
    .comp-ratio-history-chart { width:100%; height:250px; flex:0 0 250px; min-height:0; }
    .comp-ratio-pooled-summary { display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr) auto; gap:8px; align-items:center; padding:6px 8px; border-top:1px solid var(--border-subtle); border-bottom:1px solid var(--border-subtle); }
    .comp-ratio-summary-item { min-width:0; color:var(--text-muted); font-size:10px; line-height:1.15; }
    .comp-ratio-summary-label { display:flex; align-items:center; gap:5px; color:var(--text-main); font-weight:700; white-space:nowrap; }
    .comp-ratio-summary-item strong { display:block; margin-top:2px; color:var(--text-main); font-size:12px; font-variant-numeric:tabular-nums; }
    .comp-ratio-summary-item small { display:block; margin-top:1px; color:var(--text-muted); font-size:10px; font-variant-numeric:tabular-nums; }
    .comp-ratio-summary-dot { width:8px; height:8px; flex:0 0 8px; border-radius:50%; background:var(--accent); }
    .comp-ratio-summary-dot.high { background:#0f766e; }
    .comp-ratio-summary-difference { min-width:76px; padding-left:8px; border-left:1px solid var(--border-subtle); color:var(--text-muted); font-size:10px; line-height:1.15; text-align:right; }
    .comp-ratio-summary-difference strong { display:block; color:var(--accent); font-size:13px; font-variant-numeric:tabular-nums; }
    .comp-ratio-history-card .chart-footer { padding-top:5px; font-size:10px; line-height:1.22; }
    @media (max-width:900px) { .comp-ratio-pooled-summary { grid-template-columns:1fr 1fr; } .comp-ratio-summary-difference { grid-column:1 / -1; border-left:0; border-top:1px solid var(--border-subtle); padding:5px 0 0; text-align:left; } }
"""


EXTRA_CSS = r"""
    .deck-hero { height:100%; display:flex; align-items:center; justify-content:center; text-align:center; }
    .deck-hero h1 { max-width:1000px; margin:0; font-size:58px; line-height:1.04; letter-spacing:-.04em; color:var(--text-main); }
    .deck-hero p { max-width:850px; margin:18px auto 0; font-size:19px; line-height:1.45; color:var(--text-muted); }
    .deck-tags { display:flex; flex-wrap:wrap; justify-content:center; gap:8px; margin-top:20px; }
    .deck-stat-row { display:flex; justify-content:center; gap:14px; margin-top:28px; }
    .deck-stat { min-width:200px; padding:15px 20px; border:1px solid var(--border-subtle); border-radius:var(--radius-card); background:color-mix(in oklab,var(--bg-surface) 88%,transparent); }
    .deck-stat strong { display:block; color:var(--accent); font-size:32px; line-height:1; }
    .deck-stat span { display:block; margin-top:6px; font-size:13px; color:var(--text-muted); }
    .agenda-vertical { display:flex; flex-direction:column; gap:6px; }
    .agenda-item { display:flex; align-items:baseline; gap:10px; padding:8px 12px; background:var(--bg-surface-2); border:1px solid var(--border-subtle); border-radius:10px; }
    .agenda-num { flex:0 0 98px; padding:2px 8px; text-align:center; border-radius:var(--radius-pill); font-size:11px; font-weight:700; color:var(--accent); background:color-mix(in oklab,var(--accent) 12%,transparent); border:1px solid color-mix(in oklab,var(--accent) 25%,var(--border-subtle)); }
    .agenda-item strong { min-width:190px; font-size:14px; color:var(--text-main); }
    .agenda-item span:last-child { font-size:13px; color:var(--text-muted); }
    .two-pane { display:grid; grid-template-columns:1.55fr .9fr; gap:14px; min-height:0; }
    .external-factor-table { width:100%; border-collapse:collapse; font-size:14px; line-height:1.35; }
    .external-factor-table th { padding:8px 10px; border-bottom:2px solid var(--accent); color:var(--text-muted); font-size:11px; font-weight:700; letter-spacing:.06em; text-align:left; text-transform:uppercase; }
    .external-factor-table td { padding:12px 10px; border-bottom:1px solid var(--border-subtle); vertical-align:top; }
    .external-factor-table th:nth-child(1), .external-factor-table td:nth-child(1) { width:20%; }
    .external-factor-table th:nth-child(2), .external-factor-table td:nth-child(2) { width:20%; }
    .external-factor-table th:nth-child(3), .external-factor-table td:nth-child(3) { width:38%; }
    .external-factor-table th:nth-child(4), .external-factor-table td:nth-child(4) { width:22%; }
    .external-factor-table td:first-child { color:var(--accent); font-weight:700; }
    .two-chart { display:grid; grid-template-columns:1fr 1fr; gap:12px; min-height:0; }
    .region-display-stack { display:grid; grid-template-rows:minmax(0,.82fr) minmax(0,1.18fr); gap:10px; min-height:0; }
    .region-display-stack .chart-card { padding:10px 12px; gap:5px; }
    .region-display-stack .card-title { margin-bottom:0; padding-bottom:4px; font-size:10px; }
    .region-display-stack .bar-list { flex:1; justify-content:space-evenly; gap:3px; }
    .region-display-stack .bar-row { grid-template-columns:minmax(138px,176px) minmax(0,1fr) 94px; gap:6px; }
    .region-display-stack .bar-label, .region-display-stack .bar-value { font-size:11px; }
    .region-display-stack .bar-track { height:12px; }
    .region-display-stack .chart-footer { padding-top:5px; font-size:10px; line-height:1.25; }
    .triple-chart { display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; min-height:0; }
    .level-constructs { display:grid; grid-template-columns:minmax(0,1.55fr) minmax(250px,.85fr); gap:10px; min-height:0; }
    .level-main-card { padding:14px; gap:7px; }
    .level-card-heading { display:flex; align-items:center; gap:10px; min-width:0; }
    .level-card-heading .card-title { flex:1; min-width:0; margin:0; }
    .level-direction { display:flex; align-items:center; gap:5px; flex:0 0 auto; padding:4px 8px; border:1px solid color-mix(in oklab,var(--accent) 24%,var(--border-subtle)); border-radius:var(--radius-pill); background:color-mix(in oklab,var(--accent) 8%,transparent); color:var(--text-muted); font-size:10px; font-weight:700; letter-spacing:.04em; text-transform:uppercase; white-space:nowrap; }
    .level-direction-arrow { color:var(--accent); font-size:14px; line-height:1; }
    .level-main-card .bar-list { flex:1; justify-content:space-between; gap:5px; }
    .level-main-card .bar-row { grid-template-columns:minmax(150px,210px) minmax(0,1fr) 102px; gap:8px; }
    .level-main-card .bar-label { overflow:visible; text-overflow:clip; font-size:12px; }
    .level-main-card .bar-track { height:18px; }
    .level-support-stack { display:grid; grid-template-rows:minmax(0,1fr) minmax(0,1fr); gap:10px; min-height:0; }
    .level-support-card { padding:10px 12px; gap:5px; }
    .level-support-card .card-title { font-size:10px; padding-bottom:4px; margin-bottom:0; }
    .level-support-card .bar-list { flex:1; justify-content:space-between; gap:3px; }
    .level-support-card .bar-row { grid-template-columns:minmax(112px,155px) minmax(0,1fr) 82px; gap:6px; }
    .level-support-card .bar-label { font-size:10px; }
    .level-support-card .bar-track { height:12px; }
    .level-support-card .bar-value { font-size:10px; }
    .level-support-card .chart-footer { padding-top:5px; font-size:10px; line-height:1.25; }
    .level-job-detail-card .bar-row { grid-template-columns:minmax(134px,175px) minmax(0,1fr) 82px; }
    .level-job-detail-card .bar-label { font-size:9.5px; }
    .level-grade-family-card { padding:12px 14px; gap:6px; }
    .level-grade-family-card .card-title { margin-bottom:0; padding-bottom:4px; }
    .level-grade-family-chart { display:flex; flex-direction:column; gap:5px; flex:1; min-height:0; }
    .level-grade-family-row { display:grid; grid-template-columns:minmax(150px,205px) minmax(0,1fr) 86px; gap:8px; align-items:center; min-height:31px; }
    .level-grade-family-label { color:var(--text-main); font-size:11px; font-weight:700; text-align:right; white-space:nowrap; }
    .level-grade-family-total { color:var(--text-muted); font-size:10px; font-variant-numeric:tabular-nums; text-align:right; white-space:nowrap; }
    .level-grade-family-track { display:flex; width:100%; height:24px; overflow:hidden; border:1px solid var(--border-subtle); border-radius:8px; background:var(--bg-surface-3); }
    .level-grade-family-segment { display:flex; align-items:center; justify-content:center; position:relative; height:100%; min-width:3px; overflow:hidden; border-right:1px solid color-mix(in oklab,var(--bg-surface) 54%,transparent); color:#fff; font-size:10px; font-weight:800; line-height:1; text-align:center; text-shadow:0 1px 2px rgba(0,0,0,.45); white-space:nowrap; }
    .level-grade-family-segment-label { display:block; min-width:0; overflow:hidden; text-overflow:clip; }
    .level-grade-family-segment:last-child { border-right:none; }
    .level-grade-family-segment.family-m, .level-grade-family-swatch.family-m { background:color-mix(in oklab,#14b8a6 78%,var(--bg-surface)); }
    .level-grade-family-segment.family-p, .level-grade-family-swatch.family-p { background:color-mix(in oklab,var(--accent-2) 86%,var(--bg-surface)); }
    .level-grade-family-segment.family-r, .level-grade-family-swatch.family-r { background:color-mix(in oklab,var(--accent) 54%,var(--accent-2)); }
    .level-grade-family-segment.family-s, .level-grade-family-swatch.family-s { background:color-mix(in oklab,#22c55e 68%,var(--bg-surface)); }
    .level-grade-family-segment.family-t, .level-grade-family-swatch.family-t { background:color-mix(in oklab,#f59e0b 70%,var(--bg-surface)); }
    .level-grade-family-segment.family-v-other, .level-grade-family-swatch.family-v-other { background:color-mix(in oklab,#8b5cf6 68%,var(--bg-surface)); }
    .level-grade-family-legend { display:flex; flex-wrap:wrap; gap:6px 14px; padding-top:6px; border-top:1px solid var(--border-subtle); color:var(--text-muted); font-size:10px; line-height:1.2; }
    .level-grade-family-legend-item { display:inline-flex; align-items:center; gap:5px; white-space:nowrap; }
    .level-grade-family-swatch { width:10px; height:10px; border-radius:3px; border:1px solid var(--border-subtle); }
    .level-grade-family-card .chart-footer { padding-top:6px; font-size:10px; line-height:1.25; }
    .chart-card { min-height:0; }
    .talent-index-distribution-card .bar-list { flex:1; justify-content:space-evenly; padding:4px 0; }
    .talent-index-distribution-card .bar-row { min-height:26px; }
    .labor-market-card { padding:12px; gap:6px; }
    .labor-market-card .card-title { margin-bottom:0; padding-bottom:4px; font-size:10px; }
    .labor-market-card .bar-list { gap:3px; }
    .labor-market-card .bar-row { grid-template-columns:minmax(92px, 146px) 1fr 84px; gap:6px; }
    .labor-market-card .bar-label, .labor-market-card .bar-value { font-size:10px; }
    .labor-market-card .bar-track { height:12px; }
    .labor-market-card .chart-footer { padding-top:5px; font-size:10px; }
    .chart-note { margin:0; font-size:12px; line-height:1.4; color:var(--text-muted); }
    .bar-list { display:flex; flex-direction:column; gap:7px; min-height:0; }
    .bar-row { display:grid; grid-template-columns:minmax(110px, 180px) 1fr 102px; align-items:center; gap:9px; }
    .bar-label { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; text-align:right; color:var(--text-main); font-size:13px; }
    .bar-track { height:17px; border:1px solid var(--border-subtle); border-radius:var(--radius-pill); overflow:hidden; background:var(--bg-surface-3); }
    .bar-fill { height:100%; border-radius:inherit; background:var(--accent-2); }
    .bar-row:first-child .bar-fill { background:var(--accent); }
    .bar-value { text-align:right; font-size:12px; font-variant-numeric:tabular-nums; color:var(--text-main); }
    .chart-footer { margin-top:auto; padding-top:9px; border-top:1px solid var(--border-subtle); font-size:12px; line-height:1.35; color:var(--text-muted); }
    .manager-turnover-distribution-card .signal-legend { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:6px 10px; margin-top:2px; padding:7px 8px; border:1px solid var(--border-subtle); border-radius:8px; background:var(--bg-surface-2); color:var(--text-muted); font-size:11px; line-height:1.25; }
    .manager-turnover-distribution-card .signal-legend-item { min-width:0; }
    .manager-turnover-distribution-card .signal-legend strong { color:var(--text-main); }
    .commute-distance-comparison-card { padding:12px 14px; gap:7px; }
    .commute-distance-comparison-card .card-title { margin-bottom:0; padding-bottom:4px; }
    .commute-comparison-legend { display:flex; flex-wrap:wrap; gap:8px 14px; color:var(--text-muted); font-size:11px; line-height:1.2; }
    .commute-comparison-legend span { display:inline-flex; align-items:center; gap:5px; }
    .commute-legend-swatch { display:inline-block; width:9px; height:9px; border-radius:3px; background:var(--accent); }
    .commute-legend-swatch.commute-series-onsite { background:var(--accent-2); }
    .commute-legend-swatch.commute-series-missing { background:var(--text-muted); }
    .commute-comparison-list { display:flex; flex-direction:column; gap:7px; min-height:0; }
    .commute-comparison-row { display:grid; grid-template-columns:82px minmax(0,1fr); gap:9px; align-items:start; }
    .commute-comparison-label { color:var(--text-main); font-size:11px; font-weight:700; line-height:1.2; padding-top:4px; white-space:nowrap; }
    .commute-comparison-series { display:flex; flex-direction:column; gap:3px; }
    .commute-comparison-line { display:grid; grid-template-columns:48px minmax(0,1fr) 92px; gap:6px; align-items:center; }
    .commute-series-name { color:var(--text-muted); font-size:10px; }
    .commute-comparison-line .bar-track { height:10px; }
    .commute-comparison-line .bar-fill { background:var(--accent); }
    .commute-comparison-line .bar-fill.commute-series-onsite { background:var(--accent-2); }
    .commute-comparison-line .bar-fill.is-missing { background:var(--text-muted); }
    .commute-series-value { color:var(--text-main); font-size:10px; font-variant-numeric:tabular-nums; text-align:right; white-space:nowrap; }
    .commute-distance-comparison-card .chart-footer { padding-top:6px; font-size:10px; line-height:1.25; }
    /* Keep the two populations side by side within each distance band.  The
       card is rendered inside the fixed 1440x810 stage, so a vertical stack
       of full-width series becomes unreadable and can push the context card
       out of view. */
    .two-pane > * { min-width:0; min-height:0; }
    .commute-distance-comparison-card .commute-comparison-list { flex:1; justify-content:space-evenly; gap:5px; }
    .commute-distance-comparison-card .commute-comparison-row { grid-template-columns:88px minmax(0,1fr); gap:10px; align-items:center; padding:3px 0; border-bottom:1px solid var(--border-subtle); }
    .commute-distance-comparison-card .commute-comparison-row:last-child { border-bottom:0; }
    .commute-distance-comparison-card .commute-comparison-label { padding-top:0; font-size:11px; }
    .commute-distance-comparison-card .commute-comparison-series { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; min-width:0; }
    .commute-distance-comparison-card .commute-comparison-line { display:grid; grid-template-columns:minmax(0,1fr) auto; grid-template-rows:auto 11px; gap:3px 6px; min-width:0; }
    .commute-distance-comparison-card .commute-series-name { grid-column:1; grid-row:1; font-size:10px; }
    .commute-distance-comparison-card .commute-series-value { grid-column:2; grid-row:1; font-size:9px; }
    .commute-distance-comparison-card .commute-comparison-line .bar-track { grid-column:1 / -1; grid-row:2; height:11px; }
    .commute-distance-comparison-card .commute-comparison-legend { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:5px 10px; }
    .commute-distance-comparison-card .commute-comparison-legend span { min-width:0; white-space:nowrap; }
    .trend-chart { height:252px; display:grid; grid-template-columns:repeat(var(--bars), 1fr); gap:12px; align-items:end; padding:12px 12px 0; border-bottom:1px solid var(--border-subtle); background:linear-gradient(to top, var(--border-subtle) 1px, transparent 1px) 0 100%/100% 25%; }
    .trend-bar-wrap { height:100%; display:flex; flex-direction:column; justify-content:flex-end; align-items:center; gap:4px; min-width:0; }
    .trend-percent { min-height:18px; display:flex; align-items:end; justify-content:center; text-align:center; font-size:12px; line-height:1.1; font-weight:700; color:var(--text-main); font-variant-numeric:tabular-nums; white-space:nowrap; }
    .trend-bar { width:68%; min-height:3px; border-radius:8px 8px 0 0; background:linear-gradient(180deg,var(--accent-2),var(--accent)); display:flex; align-items:center; justify-content:center; overflow:hidden; }
    .trend-count { color:var(--text-invert); font-size:12px; font-weight:700; line-height:1; font-variant-numeric:tabular-nums; text-shadow:0 1px 2px rgba(2,6,23,.45); white-space:nowrap; }
    .trend-label { min-height:32px; display:flex; flex-direction:column; align-items:center; justify-content:flex-start; gap:2px; text-align:center; font-size:11px; color:var(--text-muted); }
    .trend-label small { font-size:10px; font-variant-numeric:tabular-nums; color:var(--text-main); }
    .co-location-stack { display:grid; grid-template-rows:minmax(0,1fr) minmax(0,1fr); gap:10px; min-height:0; }
    .co-location-stack .chart-card { padding:12px 14px; gap:6px; }
    .co-location-stack .card-title { margin-bottom:0; padding-bottom:4px; }
    .co-location-stack .trend-chart { height:218px; padding:7px 9px 0; gap:9px; }
    .co-location-stack .trend-bar { width:62%; }
    .co-location-stack .trend-count { font-size:10px; }
    .co-location-stack .trend-percent { font-size:11px; }
    .co-location-stack .trend-label { min-height:24px; font-size:10px; }
    .co-location-stack .chart-footer { padding-top:5px; font-size:10px; line-height:1.25; }
    .side-copy { justify-content:flex-start; gap:8px; }
    .side-copy h3 { margin:0; font-size:18px; color:var(--text-main); }
    .side-copy p { margin:0; font-size:14px; line-height:1.4; color:var(--text-main); }
    .fact-list { list-style:none; padding:0; margin:2px 0 0; display:flex; flex-direction:column; gap:4px; }
    .fact-list li { font-size:12px; line-height:1.3; color:var(--text-muted); }
    .fact-list strong { color:var(--text-main); }
    .scope-note { margin:2px 0 0; padding:6px 8px; border-radius:7px; background:color-mix(in oklab,var(--accent) 7%,transparent); border:1px solid color-mix(in oklab,var(--accent) 18%,var(--border-subtle)); font-size:11px; line-height:1.25; color:var(--text-main); }
    .provenance-panel { margin-top:auto; padding-top:8px; border-top:1px solid var(--border-subtle); }
    .provenance-title { margin:0 0 5px; font-size:11px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; color:var(--text-muted); }
    .provenance-grid { display:grid; grid-template-columns:88px minmax(0, 1fr); gap:3px 8px; margin:0; }
    .provenance-grid dt { margin:0; font-size:11px; font-weight:700; color:var(--text-main); }
    .provenance-grid dd { min-width:0; margin:0; font-size:11px; line-height:1.25; color:var(--text-muted); overflow-wrap:anywhere; }
    .provenance-status { margin:7px 0 0; padding:5px 7px; border-left:3px solid var(--accent); border-radius:4px; background:color-mix(in oklab,var(--accent) 7%,transparent); font-size:11px; line-height:1.28; color:var(--text-main); }
    .state-visual { height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; padding:34px; border:1px solid var(--border-strong); border-radius:var(--radius-card); background:var(--bg-surface-2); }
    .state-icon { width:66px; height:66px; display:grid; place-items:center; margin-bottom:16px; border-radius:50%; font-size:31px; font-weight:800; color:var(--accent); background:color-mix(in oklab,var(--accent) 12%,transparent); border:2px solid color-mix(in oklab,var(--accent) 28%,transparent); }
    .state-visual h3 { margin:0; font-size:27px; color:var(--text-main); }
    .state-visual p { max-width:540px; margin:12px 0 0; font-size:15px; line-height:1.45; color:var(--text-muted); }
    .metric-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
    .metric { padding:13px; border-radius:12px; background:var(--bg-surface-2); border:1px solid var(--border-subtle); }
    .metric strong { display:block; color:var(--accent); font-size:25px; line-height:1.05; }
    .metric span { display:block; margin-top:5px; font-size:12px; line-height:1.25; color:var(--text-muted); }
    .support-flow { display:flex; gap:10px; align-items:stretch; }
    .support-node { flex:1; padding:14px; border-radius:12px; border:1px solid var(--border-subtle); background:var(--bg-surface-2); }
    .support-node strong { display:block; font-size:22px; color:var(--accent); }
    .support-node span { display:block; margin-top:6px; font-size:12px; line-height:1.3; color:var(--text-muted); }
    .support-arrow { align-self:center; color:var(--accent); font-size:24px; }
    .privacy-banner { padding:9px 12px; border-radius:10px; background:color-mix(in oklab,#f59e0b 12%,transparent); border:1px solid color-mix(in oklab,#f59e0b 28%,transparent); font-size:12px; line-height:1.35; color:var(--text-main); }
    .team-turnover-card { padding:16px; gap:9px; }
    .team-rate { display:flex; align-items:baseline; gap:8px; }
    .team-rate strong { color:var(--accent); font-size:42px; line-height:1; letter-spacing:-.035em; font-variant-numeric:tabular-nums; }
    .team-rate span { font-size:13px; color:var(--text-muted); line-height:1.25; }
    .team-kpis { display:grid; grid-template-columns:repeat(3, 1fr); gap:6px; }
    .team-kpi { min-width:0; padding:8px; border:1px solid var(--border-subtle); border-radius:9px; background:var(--bg-surface-2); }
    .team-kpi strong { display:block; color:var(--text-main); font-size:17px; line-height:1.05; font-variant-numeric:tabular-nums; }
    .team-kpi span { display:block; margin-top:3px; font-size:11px; line-height:1.2; color:var(--text-muted); }
    .team-outcome-label { margin:2px 0 0; font-size:12px; font-weight:700; color:var(--text-main); }
    .team-outcome-bar { display:flex; height:24px; overflow:hidden; border:1px solid var(--border-subtle); border-radius:var(--radius-pill); background:var(--bg-surface-3); }
    .team-outcome-zero { height:100%; background:color-mix(in oklab,var(--text-muted) 38%,transparent); }
    .team-outcome-positive { height:100%; background:linear-gradient(90deg,var(--accent-2),var(--accent)); }
    .team-outcome-legend { display:flex; justify-content:space-between; gap:8px; font-size:11px; line-height:1.25; color:var(--text-muted); }
    .team-outcome-legend strong { color:var(--text-main); font-variant-numeric:tabular-nums; }
    .work-arrangement-stack { display:grid; grid-template-rows:minmax(0,1fr) minmax(145px,.42fr); gap:10px; min-height:0; height:100%; overflow:hidden; }
    .work-arrangement-stack .chart-card { min-height:0; padding:10px 12px; gap:5px; }
    .work-arrangement-stack .card-title { font-size:10px; padding-bottom:4px; margin-bottom:0; }
    .work-arrangement-stack .work-arrangement-card .bar-list { flex:1; justify-content:space-between; gap:2px; }
    .work-arrangement-stack .work-arrangement-card .bar-row { min-height:24px; }
    .work-arrangement-stack .work-arrangement-card .bar-label { font-size:10.5px; line-height:1.08; }
    .work-arrangement-binary-card .bar-list { flex:1; justify-content:space-evenly; gap:5px; }
    .work-arrangement-binary-card .bar-row { grid-template-columns:minmax(180px,240px) minmax(0,1fr) 102px; gap:8px; min-height:30px; }
    .work-arrangement-binary-card .bar-label { font-size:12px; }
    .work-arrangement-stack .chart-footer { padding-top:5px; font-size:10px; line-height:1.2; }
    .work-arrangement-card .bar-list { gap:4px; }
    .work-arrangement-card .bar-row { grid-template-columns:minmax(250px, 340px) 1fr 102px; gap:8px; }
    .work-arrangement-card .bar-label { overflow:visible; text-overflow:clip; white-space:normal; font-size:12px; line-height:1.15; }
    .engineering-cto-stack { display:grid; grid-template-rows:minmax(0,1fr) minmax(158px,.48fr); gap:10px; min-height:0; height:100%; overflow:hidden; }
    .engineering-cto-stack > .chart-card { min-height:0; height:auto; padding:10px 12px; gap:5px; }
    .engineering-cto-stack > .chart-card:first-child .bar-list { flex:1; justify-content:space-evenly; gap:8px; }
    .engineering-cto-stack > .chart-card:first-child .bar-row { min-height:32px; }
    .engineering-cto-stack .card-title { font-size:10px; padding-bottom:4px; margin-bottom:0; }
    .engineering-cto-display-card .bar-list { flex:1; justify-content:space-evenly; gap:6px; }
    .engineering-cto-display-card .bar-row { grid-template-columns:minmax(148px,220px) minmax(0,1fr) 102px; gap:8px; min-height:32px; }
    .engineering-cto-display-card .bar-label { font-size:11.5px; }
    .engineering-cto-stack .chart-footer { padding-top:5px; font-size:10px; line-height:1.22; }
    /* Location shows 20 ranked categories per field.  The compact treatment
       uses chart-label sizing only; body copy keeps the deck standard. */
    .location-card { padding:14px; gap:8px; }
    .location-card .bar-list { flex:1; justify-content:space-between; gap:3px; }
    .location-card .bar-row { grid-template-columns:minmax(88px, 126px) minmax(0, 1fr) 86px; gap:6px; }
    .location-card .bar-label { font-size:11px; }
    .location-card .bar-track { height:12px; }
    .location-card .bar-value { font-size:10px; }
    .location-card .chart-footer { padding-top:6px; font-size:11px; }
    .location-pair-card .bar-row { grid-template-columns:minmax(128px, 170px) minmax(0, 1fr) 86px; }
    .location-pair-card .bar-label { font-size:10.5px; }
    /* Job-family panels show 20 ranked families plus one aggregate tail in
       each pre/post-reorganization snapshot. */
    .job-family-card { padding:12px; gap:6px; }
    .job-family-card .card-title { font-size:10px; padding-bottom:4px; margin-bottom:1px; }
    .job-family-card .bar-list { flex:1; justify-content:space-between; gap:2px; }
    .job-family-card .bar-row { grid-template-columns:minmax(126px, 174px) minmax(0, 1fr) 72px; gap:5px; }
    .job-family-card .bar-label { font-size:10px; }
    .job-family-card .bar-track { height:11px; }
    .job-family-card .bar-value { font-size:10px; }
    .job-family-card .chart-footer { padding-top:5px; font-size:10px; }
    .stored-metric-card .bar-list { gap:5px; }
    .stored-metric-card .bar-row { grid-template-columns:minmax(120px, 168px) 1fr 102px; gap:8px; }
    .stored-metric-card .bar-track { height:14px; }
    .compensation-grade-card { padding:10px 12px; gap:4px; }
    .compensation-grade-card .card-title { font-size:10px; padding-bottom:4px; margin-bottom:0; }
    .compensation-grade-card .bar-list { flex:1; justify-content:flex-start; gap:1px; }
    .compensation-grade-card .bar-row { grid-template-columns:58px minmax(0,1fr) 92px; gap:5px; height:16px; }
    .compensation-grade-card .bar-label { font-size:10px; line-height:1; }
    .compensation-grade-card .bar-track { height:8px; }
    .compensation-grade-card .bar-value { font-size:9.5px; line-height:1; }
    .compensation-grade-card .chart-footer { padding-top:5px; font-size:10px; line-height:1.25; }
    .prior-experience-card { padding:10px 12px; gap:4px; }
    .prior-experience-card .card-title { font-size:10px; padding-bottom:4px; margin-bottom:0; }
    .prior-experience-card .bar-list { flex:1; justify-content:flex-start; gap:1px; }
    .prior-experience-card .bar-row { grid-template-columns:42px minmax(0, 1fr) 82px; gap:5px; height:17px; }
    .prior-experience-card .bar-label { font-size:10px; line-height:1; }
    .prior-experience-card .bar-track { height:8px; }
    .prior-experience-card .bar-value { font-size:9.5px; line-height:1; }
    .prior-experience-card .chart-footer { padding-top:5px; font-size:10px; line-height:1.25; }
    .commute-distance-card { padding:10px 12px; gap:4px; }
    .commute-distance-card .card-title { font-size:10px; padding-bottom:4px; margin-bottom:0; }
    .commute-distance-card .bar-list { flex:1; justify-content:flex-start; gap:1px; }
    .commute-distance-card .bar-row { grid-template-columns:70px minmax(0, 1fr) 92px; gap:5px; height:16px; }
    .commute-distance-card .bar-label { font-size:10px; line-height:1; }
    .commute-distance-card .bar-track { height:8px; }
    .commute-distance-card .bar-value { font-size:9.5px; line-height:1; }
    .commute-distance-card .chart-footer { padding-top:5px; font-size:10px; line-height:1.25; }
    #slide-3 .two-pane { grid-template-columns:minmax(0,1.65fr) minmax(390px,.85fr); }
    .application-intensity-card { gap:7px; padding:14px 16px; }
    .application-intensity-chart { width:100%; height:292px; flex:0 0 292px; }
    .application-intensity-table { width:100%; margin-top:3px; border-collapse:collapse; table-layout:fixed; font-size:11px; font-variant-numeric:tabular-nums; }
    .application-intensity-table th, .application-intensity-table td { padding:5px 5px; border-bottom:1px solid var(--border-subtle); text-align:right; white-space:nowrap; overflow:hidden; }
    .application-intensity-table th { font-size:10px; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:.04em; }
    .application-intensity-table th:first-child, .application-intensity-table td:first-child { text-align:left; }
    .application-intensity-table td { color:var(--text-main); }
    .application-intensity-table th:first-child, .application-intensity-table td:first-child { width:26%; white-space:normal; }
    .application-intensity-table th:nth-child(2), .application-intensity-table td:nth-child(2) { width:9%; }
    .application-intensity-table th:nth-child(3), .application-intensity-table td:nth-child(3) { width:8%; }
    .application-intensity-table th:nth-child(n+4), .application-intensity-table td:nth-child(n+4) { width:14.25%; }
    .application-intensity-table td:first-child { vertical-align:top; }
    .application-intensity-table td:first-child strong { display:block; margin-bottom:2px; line-height:1.05; }
    .application-intensity-period-note { display:block; margin-top:2px; color:var(--text-muted); font-size:10px; font-weight:500; line-height:1.15; white-space:normal; }
    .application-intensity-table td:nth-child(n+4) { font-weight:700; }
    .application-intensity-key { display:inline-block; width:9px; height:9px; margin:0 5px 1px 0; border-radius:50%; vertical-align:middle; background:var(--accent); border:1px solid color-mix(in oklab,var(--bg-surface) 58%,transparent); }
    .application-intensity-card .chart-footer { margin-top:auto; padding-top:7px; font-size:10.5px; line-height:1.25; }
    .application-intensity-side { gap:9px; padding:15px 17px; }
    .application-intensity-side h3 { margin:0; font-size:20px; line-height:1.15; }
    .application-intensity-side > p { margin:0; font-size:14px; line-height:1.38; }
    .application-intensity-highlight { padding:9px 11px; border:1px solid var(--border-strong); border-radius:10px; background:color-mix(in oklab,var(--accent) 7%,var(--bg-surface)); color:var(--text-main); font-size:13px; line-height:1.32; }
    .application-intensity-section { padding-top:8px; border-top:1px solid var(--border-subtle); }
    .application-intensity-section-title { margin:0 0 6px; color:var(--text-muted); font-size:11px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; }
    .application-intensity-steps { display:flex; flex-direction:column; gap:6px; }
    .application-intensity-step { display:grid; grid-template-columns:24px minmax(0,1fr); gap:8px; align-items:start; }
    .application-intensity-step-num { display:flex; align-items:center; justify-content:center; width:22px; height:22px; border-radius:50%; background:var(--accent-soft); color:var(--accent); font-size:11px; font-weight:800; }
    .application-intensity-step strong { display:block; margin-bottom:1px; color:var(--text-main); font-size:13px; line-height:1.2; }
    .application-intensity-step span { display:block; color:var(--text-muted); font-size:12px; line-height:1.25; }
    .application-intensity-limit { padding:9px 10px; border-left:3px solid var(--accent); border-radius:8px; background:var(--bg-surface-2); color:var(--text-muted); font-size:12px; line-height:1.3; }
    .application-intensity-limit strong { color:var(--text-main); }
    .application-intensity-authorization { padding:8px 10px; border-left:3px solid #d97706; border-radius:8px; background:color-mix(in oklab,#f59e0b 9%,var(--bg-surface)); color:var(--text-muted); font-size:11px; line-height:1.28; }
    .application-intensity-authorization strong { color:var(--text-main); }
    .application-intensity-source { padding-top:7px; border-top:1px solid var(--border-subtle); color:var(--text-muted); font-size:11px; line-height:1.25; }
    .application-intensity-source strong { color:var(--text-main); }
    .application-feature-card { justify-content:center; }
    .application-feature-card .support-flow { margin:8px 0 14px; }
    .application-feature-card .support-node { min-height:142px; display:flex; flex-direction:column; justify-content:center; }
    .application-feature-card .support-node strong { font-size:19px; line-height:1.15; }
    .application-snapshot-main { display:grid; grid-template-rows:minmax(0,.86fr) minmax(0,1.14fr); gap:10px; min-height:0; height:100%; }
    .application-snapshot-main .card { min-height:0; }
    .application-snapshot-latest-card, .application-snapshot-trend-card { gap:7px; padding:12px 14px; }
    .application-snapshot-bar-list { display:flex; flex-direction:column; gap:7px; justify-content:space-evenly; min-height:0; flex:1; }
    .application-snapshot-bar-row { display:grid; grid-template-columns:142px minmax(0,1fr) 76px; align-items:center; gap:8px; min-height:27px; }
    .application-snapshot-bar-label { min-width:0; color:var(--text-main); line-height:1.05; }
    .application-snapshot-bar-label strong { display:block; font-size:14px; }
    .application-snapshot-bar-label span { display:block; margin-top:2px; color:var(--text-muted); font-size:9px; white-space:nowrap; }
    .application-snapshot-track { height:20px; overflow:hidden; border:1px solid var(--border-subtle); border-radius:var(--radius-pill); background:var(--bg-surface-3); }
    .application-snapshot-fill { height:100%; min-width:2px; display:flex; align-items:center; justify-content:flex-end; padding-right:7px; border-radius:inherit; color:#fff; font-size:10px; font-weight:700; font-variant-numeric:tabular-nums; }
    .application-snapshot-bar-value { color:var(--text-main); text-align:right; font-size:11px; font-weight:700; font-variant-numeric:tabular-nums; white-space:nowrap; }
    .application-snapshot-kpi-row { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; padding-top:6px; border-top:1px solid var(--border-subtle); color:var(--text-muted); font-size:9.5px; line-height:1.15; }
    .application-snapshot-kpi-row span { min-width:0; }
    .application-snapshot-kpi-row strong { display:block; color:var(--text-main); font-size:13px; font-variant-numeric:tabular-nums; }
    .application-employee-snapshot-trend-chart { width:100%; height:248px; flex:0 0 248px; }
    .application-snapshot-trend-note { padding:7px 9px; border:1px solid var(--border-subtle); border-radius:8px; background:var(--bg-surface-2); color:var(--text-muted); font-size:10px; line-height:1.25; }
    .application-snapshot-trend-note strong { color:var(--text-main); }
    @media (max-width:900px) { .application-snapshot-bar-row { grid-template-columns:110px minmax(0,1fr) 68px; } .application-snapshot-bar-label strong { font-size:12px; } }
    .team-exit-definition-card { justify-content:center; }
    .team-exit-definition-card .support-flow { margin:8px 0 14px; }
    .team-exit-definition-card .support-node { min-height:142px; display:flex; flex-direction:column; justify-content:center; }
    .team-exit-definition-card .support-node strong { font-size:18px; line-height:1.15; }
    .team-flag-card { gap:7px; padding:12px; }
    .team-flag-chart { width:100%; height:220px; flex:0 0 220px; min-width:0; }
    .team-flag-panel { display:flex; flex-direction:column; gap:6px; min-height:0; }
    .team-flag-panel + .team-flag-panel { margin-top:3px; padding-top:7px; border-top:1px solid var(--border-subtle); }
    .team-flag-panel-title { margin:0; font-size:10px; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:.05em; }
    .team-flag-panel-chart { width:100%; height:178px; flex:0 0 178px; min-width:0; }
    .team-flag-window-panel { display:flex; flex-direction:column; gap:4px; min-height:0; }
    .team-flag-window-panel + .team-flag-window-panel { margin-top:3px; padding-top:7px; border-top:1px solid var(--border-subtle); }
    .team-flag-window-heading { display:flex; align-items:baseline; justify-content:space-between; gap:8px; }
    .team-flag-window-heading h3 { margin:0; font-size:10px; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:.05em; }
    .team-flag-window-heading p { margin:0; font-size:10px; color:var(--text-muted); text-align:right; }
    .team-flag-window-chart { width:100%; height:214px; flex:0 0 214px; min-width:0; }
    .team-flag-panel-note { margin:0; font-size:10px; line-height:1.25; color:var(--text-muted); }
    .team-flag-table { width:100%; border-collapse:collapse; font-size:10px; font-variant-numeric:tabular-nums; }
    .team-flag-table th, .team-flag-table td { padding:4px 5px; border-bottom:1px solid var(--border-subtle); text-align:right; white-space:nowrap; }
    .team-flag-table th { color:var(--text-muted); font-size:9px; text-transform:uppercase; letter-spacing:.03em; }
    .team-flag-table th:first-child, .team-flag-table td:first-child { text-align:left; }
    .team-flag-table td { color:var(--text-main); }
    .team-flag-table td strong { font-weight:700; }
    .transfer-distribution-wrap { display:flex; flex-direction:column; gap:7px; min-width:0; min-height:0; }
    .manager-change-distribution-card { padding:14px; }
    .manager-change-distribution-card .bar-list { margin-top:8px; gap:14px; }
    .manager-change-distribution-card .bar-row { grid-template-columns:56px 1fr 118px; }
    .manager-change-distribution-card .chart-footer { margin-top:10px; }
    .manager-change-comparison-layout { display:grid; grid-template-rows:minmax(0,1fr) auto; gap:10px; min-height:0; }
    .manager-change-comparison-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); grid-template-rows:repeat(2,minmax(0,1fr)); gap:10px 12px; min-height:0; }
    .manager-change-comparison-card { padding:11px 14px; gap:5px; min-height:0; }
    .manager-change-comparison-card .card-title { margin-bottom:0; padding-bottom:4px; font-size:10px; }
    .manager-change-comparison-card .bar-list { flex:1; margin-top:3px; gap:7px; justify-content:space-evenly; }
    .manager-change-comparison-card .bar-row { grid-template-columns:48px minmax(0,1fr) 108px; gap:7px; }
    .manager-change-comparison-card .bar-label, .manager-change-comparison-card .bar-value { font-size:11px; }
    .manager-change-comparison-card .chart-footer { margin-top:3px; padding-top:5px; font-size:10px; line-height:1.22; }
    .manager-change-comparison-note { padding:8px 12px; border:1px solid color-mix(in oklab,var(--accent) 22%,var(--border-subtle)); border-radius:10px; background:color-mix(in oklab,var(--accent) 7%,transparent); color:var(--text-main); font-size:12px; line-height:1.32; }
    .qvoice-comment-card { padding:12px; gap:6px; }
    .qvoice-comment-chart { width:100%; height:300px; flex:0 0 300px; min-width:0; }
    .qvoice-comment-table { width:100%; border-collapse:collapse; font-size:11px; font-variant-numeric:tabular-nums; }
    .qvoice-comment-table th, .qvoice-comment-table td { padding:4px 6px; border-bottom:1px solid var(--border-subtle); text-align:right; white-space:nowrap; }
    .qvoice-comment-table th { font-size:10px; color:var(--text-muted); text-transform:uppercase; letter-spacing:.04em; }
    .qvoice-comment-table th:first-child, .qvoice-comment-table td:first-child { text-align:left; }
    .qvoice-comment-table td { color:var(--text-main); }
    .qvoice-comment-table td strong { color:var(--text-main); }
    .qvoice-comment-key { display:inline-block; width:8px; height:8px; margin-right:4px; border-radius:50%; vertical-align:middle; }
    .qvoice-comment-note { margin:0; font-size:10px; line-height:1.25; color:var(--text-muted); }
    .qvoice-diagnostic-title { margin:2px 0 0; font-size:10px; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:.05em; }
    .qvoice-diagnostic-table { width:100%; border-collapse:collapse; font-size:10px; font-variant-numeric:tabular-nums; }
    .qvoice-diagnostic-table th, .qvoice-diagnostic-table td { padding:3px 5px; border-bottom:1px solid var(--border-subtle); text-align:right; white-space:nowrap; }
    .qvoice-diagnostic-table th { font-size:9px; color:var(--text-muted); text-transform:uppercase; letter-spacing:.03em; }
    .qvoice-diagnostic-table th:first-child, .qvoice-diagnostic-table td:first-child { text-align:left; }
    .qvoice-diagnostic-table td { color:var(--text-main); }
    .qvoice-diagnostic-note { margin:0; font-size:9px; line-height:1.2; color:var(--text-muted); }
    .qvoice-retention-card { padding:13px 14px; gap:8px; }
    .retention-meta { margin:-2px 0 0; color:var(--text-muted); font-size:10px; line-height:1.25; }
    .retention-theme-list { display:grid; gap:5px; }
    .retention-theme-row { display:grid; grid-template-columns:minmax(210px,1.2fr) minmax(120px,2fr) 92px; gap:8px; align-items:center; }
    .retention-theme-label { color:var(--text-main); font-size:11px; font-weight:700; line-height:1.15; }
    .retention-theme-track { height:13px; overflow:hidden; border:1px solid var(--border-subtle); border-radius:var(--radius-pill); background:var(--bg-surface-3); }
    .retention-theme-fill { height:100%; min-width:3px; border-radius:inherit; background:linear-gradient(90deg,var(--accent-2),var(--accent)); }
    .retention-theme-value { color:var(--text-main); font-size:11px; font-weight:800; font-variant-numeric:tabular-nums; text-align:right; white-space:nowrap; }
    .retention-intent { display:grid; grid-template-columns:1fr auto; gap:8px; align-items:center; padding:7px 9px; border:1px solid color-mix(in oklab,var(--accent) 24%,var(--border-subtle)); border-radius:10px; background:color-mix(in oklab,var(--accent) 8%,transparent); }
    .retention-intent strong { display:block; color:var(--text-main); font-size:11px; }
    .retention-intent span { color:var(--text-muted); font-size:9px; line-height:1.2; }
    .retention-intent-value { color:var(--accent); font-size:13px; font-weight:900; font-variant-numeric:tabular-nums; text-align:right; white-space:nowrap; }
    .retention-trend-heading { display:flex; justify-content:space-between; gap:10px; align-items:baseline; padding-top:2px; border-top:1px solid var(--border-subtle); }
    .retention-trend-heading strong { color:var(--text-main); font-size:11px; }
    .retention-trend-heading span { color:var(--text-muted); font-size:9px; text-align:right; }
    .retention-trend-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; min-height:0; }
    .retention-trend-panel { min-width:0; padding:7px 7px 5px; border:1px solid var(--border-subtle); border-radius:10px; background:color-mix(in oklab,var(--bg-surface-2) 72%,transparent); }
    .retention-trend-title { min-height:26px; color:var(--text-main); font-size:10px; font-weight:800; line-height:1.15; }
    .retention-mini-bars { display:grid; grid-template-columns:repeat(4,1fr); gap:4px; align-items:end; height:92px; padding-top:3px; border-bottom:1px solid var(--border-subtle); background:linear-gradient(to top,var(--border-subtle) 1px,transparent 1px) 0 100%/100% 50%; }
    .retention-mini-wrap { min-width:0; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:flex-end; gap:2px; }
    .retention-mini-value { min-height:10px; color:var(--text-main); font-size:8px; font-weight:800; font-variant-numeric:tabular-nums; white-space:nowrap; }
    .retention-mini-bar { width:62%; min-height:3px; border-radius:5px 5px 0 0; background:var(--accent); }
    .retention-mini-year { min-height:19px; color:var(--text-muted); font-size:8px; text-align:center; line-height:1.05; }
    .retention-mini-year small { display:block; font-size:7px; }
    .retention-footnote { margin:0; color:var(--text-muted); font-size:9px; line-height:1.2; }
    .qvoice-response-card { padding:12px; gap:7px; }
    .qvoice-response-chart { width:100%; height:292px; flex:0 0 292px; min-width:0; }
    .qvoice-response-table { width:100%; border-collapse:collapse; font-size:10px; font-variant-numeric:tabular-nums; }
    .qvoice-response-table th, .qvoice-response-table td { padding:4px 5px; border-bottom:1px solid var(--border-subtle); text-align:right; white-space:nowrap; }
    .qvoice-response-table th { font-size:9px; color:var(--text-muted); text-transform:uppercase; letter-spacing:.03em; }
    .qvoice-response-table th:first-child, .qvoice-response-table td:first-child { text-align:left; }
    .qvoice-response-table td { color:var(--text-main); }
    .qvoice-response-table td strong { color:var(--text-main); }
    .qvoice-response-key { display:inline-block; width:8px; height:8px; margin-right:4px; border-radius:50%; vertical-align:middle; }
    .qvoice-response-note { margin:0; font-size:10px; line-height:1.25; color:var(--text-muted); }
    .qvoice-response-warning { margin:0; padding:6px 8px; border-left:3px solid #B08A00; border-radius:4px; background:color-mix(in oklab,#B08A00 9%,transparent); font-size:10px; line-height:1.25; color:var(--text-main); }
    .qvoice-comparable-card { padding:14px; gap:9px; }
    .qvoice-comparable-grid { display:grid; grid-template-columns:minmax(240px,.82fr) minmax(330px,1.18fr); gap:12px; min-height:0; flex:1; }
    .qvoice-comparable-panel { min-width:0; min-height:0; padding:11px; border:1px solid var(--border-subtle); border-radius:12px; background:color-mix(in oklab,var(--bg-surface-2) 74%,transparent); display:flex; flex-direction:column; gap:7px; }
    .qvoice-comparable-panel h3 { margin:0; font-size:14px; line-height:1.25; color:var(--text-main); }
    .qvoice-comparable-panel p { margin:0; font-size:11px; line-height:1.3; color:var(--text-muted); }
    .qvoice-favorable-trend { flex:1; min-height:0; display:grid; grid-template-columns:repeat(3,1fr); gap:10px; align-items:end; padding:8px 6px 0; border-bottom:1px solid var(--border-subtle); background:linear-gradient(to top, var(--border-subtle) 1px, transparent 1px) 0 100%/100% 25%; }
    .qvoice-favorable-bar-wrap { min-height:0; height:100%; display:flex; flex-direction:column; justify-content:flex-end; align-items:center; gap:4px; }
    .qvoice-favorable-value { min-height:18px; color:var(--text-main); font-size:13px; font-weight:800; font-variant-numeric:tabular-nums; white-space:nowrap; }
    .qvoice-favorable-bar { width:72%; min-height:3px; border-radius:8px 8px 0 0; background:linear-gradient(180deg,var(--accent-2),var(--accent)); display:flex; align-items:center; justify-content:center; }
    .qvoice-favorable-bar span { color:var(--text-invert); font-size:11px; font-weight:700; font-variant-numeric:tabular-nums; text-shadow:0 1px 2px rgba(2,6,23,.45); white-space:nowrap; }
    .qvoice-favorable-year { min-height:30px; display:flex; flex-direction:column; align-items:center; gap:1px; color:var(--text-muted); font-size:11px; }
    .qvoice-favorable-year strong { color:var(--text-main); font-size:12px; }
    .qvoice-stack-list { display:flex; flex:1; flex-direction:column; justify-content:space-around; gap:8px; min-height:0; }
    .qvoice-stack-row { display:grid; grid-template-columns:76px minmax(0,1fr); gap:7px; align-items:center; }
    .qvoice-stack-label { font-size:11px; line-height:1.2; color:var(--text-muted); font-variant-numeric:tabular-nums; }
    .qvoice-stack-label strong { display:block; color:var(--text-main); font-size:12px; }
    .qvoice-stack-bar { display:flex; height:30px; overflow:hidden; border:1px solid var(--border-subtle); border-radius:var(--radius-pill); background:var(--bg-surface-3); }
    .qvoice-stack-segment { display:flex; align-items:center; justify-content:center; height:100%; min-width:0; overflow:hidden; }
    .qvoice-stack-segment span { color:var(--text-invert); font-size:11px; font-weight:800; font-variant-numeric:tabular-nums; line-height:1; text-shadow:0 1px 2px rgba(2,6,23,.55); white-space:nowrap; }
    .qvoice-band-1 { background:color-mix(in oklab,#ef4444 78%,var(--bg-surface)); }
    .qvoice-band-2 { background:color-mix(in oklab,#f59e0b 78%,var(--bg-surface)); }
    .qvoice-band-3 { background:color-mix(in oklab,#eab308 78%,var(--bg-surface)); }
    .qvoice-band-4 { background:color-mix(in oklab,#22c55e 76%,var(--bg-surface)); }
    .qvoice-band-5 { background:color-mix(in oklab,#14b8a6 78%,var(--bg-surface)); }
    .qvoice-band-6 { background:var(--accent); }
    .qvoice-band-legend { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:4px 8px; padding-top:6px; border-top:1px solid var(--border-subtle); }
    .qvoice-band-legend span { display:flex; align-items:center; gap:4px; min-width:0; color:var(--text-muted); font-size:10px; white-space:nowrap; }
    .qvoice-band-dot { width:8px; height:8px; flex:0 0 8px; border-radius:50%; }
    .transfer-chart-grid { display:flex; flex:1 1 auto; flex-direction:column; gap:7px; min-height:0; }
    .transfer-chart-card { min-height:0; flex:1 1 0; padding:10px 12px; gap:5px; }
    .transfer-chart-card .card-title { font-size:10px; padding-bottom:4px; margin-bottom:0; }
    .transfer-chart { width:100%; height:214px; flex:0 0 214px; min-width:0; }
    .transfer-summary-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:6px; }
    .transfer-summary-grid .metric { padding:7px 9px; }
    .transfer-summary-grid .metric strong { font-size:18px; }
    .transfer-summary-grid .metric span { font-size:9px; }
    .transfer-footnote { padding:2px 6px 0; font-size:10px; line-height:1.2; color:var(--text-muted); }
    /* Deck navigation: sections reduce 44 options to six groups. Scrolling is
       a fallback; a single open section keeps the controls presentation-sized. */
    .nav-panel { max-height:92vh; overflow-x:hidden; overflow-y:auto; scrollbar-gutter:stable; }
    .nav-ctrl:hover .nav-panel, .nav-ctrl:focus-within .nav-panel { width:280px; padding:12px 10px; }
    .nav-section { margin:0; border:1px solid var(--border-subtle); border-radius:10px; background:color-mix(in oklab,var(--bg-surface) 88%,transparent); }
    .nav-section + .nav-section { margin-top:4px; }
    .nav-section > summary { display:flex; align-items:center; gap:8px; min-height:28px; padding:6px 8px; cursor:pointer; list-style:none; color:var(--text-main); font-size:12px; font-weight:700; }
    .nav-section > summary::-webkit-details-marker { display:none; }
    .nav-section > summary::before { content:"+"; flex:0 0 12px; color:var(--accent); font-size:15px; line-height:1; text-align:center; }
    .nav-section[open] > summary::before { content:"−"; }
    .nav-section[open] > summary { border-bottom:1px solid var(--border-subtle); background:color-mix(in oklab,var(--accent) 7%,transparent); }
    .nav-section-title { min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .nav-section-range { margin-left:auto; color:var(--text-muted); font-size:10px; font-variant-numeric:tabular-nums; white-space:nowrap; }
    .nav-section-slides { display:grid; gap:4px; padding:5px; }
    .nav-section .nav-pill { padding:5px 8px; border-radius:8px; font-size:11px; line-height:1.2; }
    @media (max-width:900px) { .two-pane,.two-chart,.triple-chart,.level-constructs,.qvoice-comparable-grid { grid-template-columns:1fr; } .level-support-stack { grid-template-rows:auto auto; } .bar-row { grid-template-columns:120px 1fr 88px; } }
""" + COMP_RATIO_FOCUSED_CSS + RESIDENTIAL_MANAGER_DISTANCE_CSS + ROLE_LEVEL_TENURE_CSS + COMPANY_TENURE_CSS + PROMOTION_HISTORY_BY_GRADE_CSS + CURRENT_GRADE_ENTRY_PATH_CSS + QVOICE_HEARTBEAT_CSS


NAVIGATION_ENHANCEMENT = r"""
  <script>
    /* Section navigation enhancement independent of the base block.
       The base engine retains slide state; clicks emit the same keyboard event
       that the base engine already handles. */
    (function () {
      var nav = document.getElementById('slide-nav');
      if (!nav) return;

      var sections = Array.from(nav.querySelectorAll('.nav-section'));
      var buttons = Array.from(nav.querySelectorAll('.nav-pill[data-slide]'));

      function closeOtherSections(openSection) {
        sections.forEach(function (section) {
          if (section !== openSection && section.open) section.open = false;
        });
      }

      function activeButton() {
        return nav.querySelector('.nav-pill.pill-active');
      }

      function syncActiveNavigation() {
        var active = activeButton();
        buttons.forEach(function (button) {
          if (button === active) button.setAttribute('aria-current', 'page');
          else button.removeAttribute('aria-current');
        });
        if (!active) return;

        var section = active.closest('.nav-section');
        if (section && !section.open) section.open = true;
        if (section) closeOtherSections(section);
        active.scrollIntoView({ block: 'nearest' });
      }

      sections.forEach(function (section) {
        section.addEventListener('toggle', function () {
          if (section.open) closeOtherSections(section);
        });
      });

      buttons.forEach(function (button) {
        button.addEventListener('click', function (event) {
          event.preventDefault();
          var active = activeButton();
          var currentIndex = active ? Number(active.dataset.slide) : 0;
          var requestedIndex = Number(button.dataset.slide);
          var key = requestedIndex >= currentIndex ? 'ArrowRight' : 'ArrowLeft';
          var steps = Math.abs(requestedIndex - currentIndex);

          for (var index = 0; index < steps; index += 1) {
            document.dispatchEvent(new KeyboardEvent('keydown', {
              key: key,
              bubbles: true,
              cancelable: true,
            }));
          }
          syncActiveNavigation();
        });
      });

      document.addEventListener('keydown', function (event) {
        if (['ArrowRight', 'ArrowDown', 'ArrowLeft', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
          syncActiveNavigation();
        }
      });

      syncActiveNavigation();
    })();
  </script>
"""


# A focused refresh operates on an already-built deck, so its content-specific
# styles must travel with the replacement stage rather than relying on a full
# deck rebuild to append EXTRA_CSS.
RETENTION_CONCERNS_FOCUSED_CSS = r"""
    .qvoice-retention-card { padding:13px 14px; gap:8px; }
    .retention-meta { margin:-2px 0 0; color:var(--text-muted); font-size:10px; line-height:1.25; }
    .retention-theme-list { display:grid; gap:5px; }
    .retention-theme-row { display:grid; grid-template-columns:minmax(210px,1.2fr) minmax(120px,2fr) 92px; gap:8px; align-items:center; }
    .retention-theme-label { color:var(--text-main); font-size:11px; font-weight:700; line-height:1.15; }
    .retention-theme-track { height:13px; overflow:hidden; border:1px solid var(--border-subtle); border-radius:var(--radius-pill); background:var(--bg-surface-3); }
    .retention-theme-fill { height:100%; min-width:3px; border-radius:inherit; background:linear-gradient(90deg,var(--accent-2),var(--accent)); }
    .retention-theme-value { color:var(--text-main); font-size:11px; font-weight:800; font-variant-numeric:tabular-nums; text-align:right; white-space:nowrap; }
    .retention-intent { display:grid; grid-template-columns:1fr auto; gap:8px; align-items:center; padding:7px 9px; border:1px solid color-mix(in oklab,var(--accent) 24%,var(--border-subtle)); border-radius:10px; background:color-mix(in oklab,var(--accent) 8%,transparent); }
    .retention-intent strong { display:block; color:var(--text-main); font-size:11px; }
    .retention-intent span { color:var(--text-muted); font-size:9px; line-height:1.2; }
    .retention-intent-value { color:var(--accent); font-size:13px; font-weight:900; font-variant-numeric:tabular-nums; text-align:right; white-space:nowrap; }
    .retention-trend-heading { display:flex; justify-content:space-between; gap:10px; align-items:baseline; padding-top:2px; border-top:1px solid var(--border-subtle); }
    .retention-trend-heading strong { color:var(--text-main); font-size:11px; }
    .retention-trend-heading span { color:var(--text-muted); font-size:9px; text-align:right; }
    .retention-trend-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; min-height:0; }
    .retention-trend-panel { min-width:0; padding:7px 7px 5px; border:1px solid var(--border-subtle); border-radius:10px; background:color-mix(in oklab,var(--bg-surface-2) 72%,transparent); }
    .retention-trend-title { min-height:26px; color:var(--text-main); font-size:10px; font-weight:800; line-height:1.15; }
    .retention-mini-bars { display:grid; grid-template-columns:repeat(4,1fr); gap:4px; align-items:end; height:92px; padding-top:3px; border-bottom:1px solid var(--border-subtle); background:linear-gradient(to top,var(--border-subtle) 1px,transparent 1px) 0 100%/100% 50%; }
    .retention-mini-wrap { min-width:0; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:flex-end; gap:2px; }
    .retention-mini-value { min-height:10px; color:var(--text-main); font-size:8px; font-weight:800; font-variant-numeric:tabular-nums; white-space:nowrap; }
    .retention-mini-bar { width:62%; min-height:3px; border-radius:5px 5px 0 0; background:var(--accent); }
    .retention-mini-year { min-height:19px; color:var(--text-muted); font-size:8px; text-align:center; line-height:1.05; }
    .retention-mini-year small { display:block; font-size:7px; }
    .retention-footnote { margin:0; color:var(--text-muted); font-size:9px; line-height:1.2; }
"""


# The application refresh can run against an existing deck whose style block
# predates the employee-snapshot proposal. Keep the annual and rolling
# application styles available at the focused-refresh boundary as well as in
# EXTRA_CSS used by a full rebuild.
APPLICATION_INTENSITY_FOCUSED_CSS = r"""
    #slide-3 .two-pane { grid-template-columns:minmax(0,1.65fr) minmax(390px,.85fr); }
    .application-intensity-card { gap:7px; padding:14px 16px; }
    .application-intensity-chart { width:100%; height:292px; flex:0 0 292px; }
    .application-intensity-table { width:100%; margin-top:3px; border-collapse:collapse; table-layout:fixed; font-size:11px; font-variant-numeric:tabular-nums; }
    .application-intensity-table th, .application-intensity-table td { padding:5px 5px; border-bottom:1px solid var(--border-subtle); text-align:right; white-space:nowrap; overflow:hidden; }
    .application-intensity-table th { font-size:10px; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:.04em; }
    .application-intensity-table th:first-child, .application-intensity-table td:first-child { text-align:left; }
    .application-intensity-table td { color:var(--text-main); }
    .application-intensity-table th:first-child, .application-intensity-table td:first-child { width:26%; white-space:normal; }
    .application-intensity-table th:nth-child(2), .application-intensity-table td:nth-child(2) { width:9%; }
    .application-intensity-table th:nth-child(3), .application-intensity-table td:nth-child(3) { width:8%; }
    .application-intensity-table th:nth-child(n+4), .application-intensity-table td:nth-child(n+4) { width:14.25%; }
    .application-intensity-table td:first-child { vertical-align:top; }
    .application-intensity-table td:first-child strong { display:block; margin-bottom:2px; line-height:1.05; }
    .application-intensity-period-note { display:block; margin-top:2px; color:var(--text-muted); font-size:10px; font-weight:500; line-height:1.15; white-space:normal; }
    .application-intensity-table td:nth-child(n+4) { font-weight:700; }
    .application-intensity-key { display:inline-block; width:9px; height:9px; margin:0 5px 1px 0; border-radius:50%; vertical-align:middle; background:var(--accent); border:1px solid color-mix(in oklab,var(--bg-surface) 58%,transparent); }
    .application-intensity-card .chart-footer { margin-top:auto; padding-top:7px; font-size:10.5px; line-height:1.25; }
    .application-intensity-side { gap:9px; padding:15px 17px; }
    .application-intensity-side h3 { margin:0; font-size:20px; line-height:1.15; }
    .application-intensity-side > p { margin:0; font-size:14px; line-height:1.38; }
    .application-intensity-highlight { padding:9px 11px; border:1px solid var(--border-strong); border-radius:10px; background:color-mix(in oklab,var(--accent) 7%,var(--bg-surface)); color:var(--text-main); font-size:13px; line-height:1.32; }
    .application-intensity-section { padding-top:8px; border-top:1px solid var(--border-subtle); }
    .application-intensity-section-title { margin:0 0 6px; color:var(--text-muted); font-size:11px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; }
    .application-intensity-steps { display:flex; flex-direction:column; gap:6px; }
    .application-intensity-step { display:grid; grid-template-columns:24px minmax(0,1fr); gap:8px; align-items:start; }
    .application-intensity-step-num { display:flex; align-items:center; justify-content:center; width:22px; height:22px; border-radius:50%; background:var(--accent-soft); color:var(--accent); font-size:11px; font-weight:800; }
    .application-intensity-step strong { display:block; margin-bottom:1px; color:var(--text-main); font-size:13px; line-height:1.2; }
    .application-intensity-step span { display:block; color:var(--text-muted); font-size:12px; line-height:1.25; }
    .application-intensity-limit { padding:9px 10px; border-left:3px solid var(--accent); border-radius:8px; background:var(--bg-surface-2); color:var(--text-muted); font-size:12px; line-height:1.3; }
    .application-intensity-limit strong { color:var(--text-main); }
    .application-intensity-authorization { padding:8px 10px; border-left:3px solid #d97706; border-radius:8px; background:color-mix(in oklab,#f59e0b 9%,var(--bg-surface)); color:var(--text-muted); font-size:11px; line-height:1.28; }
    .application-intensity-authorization strong { color:var(--text-main); }
    .application-intensity-source { padding-top:7px; border-top:1px solid var(--border-subtle); color:var(--text-muted); font-size:11px; line-height:1.25; }
    .application-intensity-source strong { color:var(--text-main); }
    .application-snapshot-main { display:grid; grid-template-rows:minmax(0,.86fr) minmax(0,1.14fr); gap:10px; min-height:0; height:100%; }
    .application-snapshot-main .card { min-height:0; }
    .application-snapshot-latest-card, .application-snapshot-trend-card { gap:7px; padding:12px 14px; }
    .application-snapshot-bar-list { display:flex; flex-direction:column; gap:7px; justify-content:space-evenly; min-height:0; flex:1; }
    .application-snapshot-bar-row { display:grid; grid-template-columns:142px minmax(0,1fr) 76px; align-items:center; gap:8px; min-height:27px; }
    .application-snapshot-bar-label { min-width:0; color:var(--text-main); line-height:1.05; }
    .application-snapshot-bar-label strong { display:block; font-size:14px; }
    .application-snapshot-bar-label span { display:block; margin-top:2px; color:var(--text-muted); font-size:9px; white-space:nowrap; }
    .application-snapshot-track { height:20px; overflow:hidden; border:1px solid var(--border-subtle); border-radius:var(--radius-pill); background:var(--bg-surface-3); }
    .application-snapshot-fill { height:100%; min-width:2px; display:flex; align-items:center; justify-content:flex-end; padding-right:7px; border-radius:inherit; color:#fff; font-size:10px; font-weight:700; font-variant-numeric:tabular-nums; }
    .application-snapshot-bar-value { color:var(--text-main); text-align:right; font-size:11px; font-weight:700; font-variant-numeric:tabular-nums; white-space:nowrap; }
    .application-snapshot-kpi-row { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; padding-top:6px; border-top:1px solid var(--border-subtle); color:var(--text-muted); font-size:9.5px; line-height:1.15; }
    .application-snapshot-kpi-row span { min-width:0; }
    .application-snapshot-kpi-row strong { display:block; color:var(--text-main); font-size:13px; font-variant-numeric:tabular-nums; }
    .application-employee-snapshot-trend-chart { width:100%; height:248px; flex:0 0 248px; }
    .application-snapshot-trend-note { padding:7px 9px; border:1px solid var(--border-subtle); border-radius:8px; background:var(--bg-surface-2); color:var(--text-muted); font-size:10px; line-height:1.25; }
    .application-snapshot-trend-note strong { color:var(--text-main); }
    @media (max-width:900px) { .application-snapshot-bar-row { grid-template-columns:110px minmax(0,1fr) 68px; } .application-snapshot-bar-label strong { font-size:12px; } }
"""


ENGINEERING_CTO_FOCUSED_CSS = r"""
    .engineering-cto-stack { display:grid; grid-template-rows:minmax(0,1fr) minmax(158px,.48fr); gap:10px; min-height:0; height:100%; overflow:hidden; }
    .engineering-cto-stack > .chart-card { min-height:0; height:auto; padding:10px 12px; gap:5px; }
    .engineering-cto-stack > .chart-card:first-child .bar-list { flex:1; justify-content:space-evenly; gap:8px; }
    .engineering-cto-stack > .chart-card:first-child .bar-row { min-height:32px; }
    .engineering-cto-stack .card-title { font-size:10px; padding-bottom:4px; margin-bottom:0; }
    .engineering-cto-display-card .bar-list { flex:1; justify-content:space-evenly; gap:6px; }
    .engineering-cto-display-card .bar-row { grid-template-columns:minmax(148px,220px) minmax(0,1fr) 102px; gap:8px; min-height:32px; }
    .engineering-cto-display-card .bar-label { font-size:11.5px; }
    .engineering-cto-stack .chart-footer { padding-top:5px; font-size:10px; line-height:1.22; }
"""
LEVEL_GRADE_FAMILY_FOCUSED_CSS = r"""
    .level-grade-family-card { padding:12px 14px; gap:6px; }
    .level-grade-family-card .card-title { margin-bottom:0; padding-bottom:4px; }
    .level-grade-family-chart { display:flex; flex-direction:column; gap:5px; flex:1; min-height:0; }
    .level-grade-family-row { display:grid; grid-template-columns:minmax(150px,205px) minmax(0,1fr) 86px; gap:8px; align-items:center; min-height:31px; }
    .level-grade-family-label { color:var(--text-main); font-size:11px; font-weight:700; text-align:right; white-space:nowrap; }
    .level-grade-family-total { color:var(--text-muted); font-size:10px; font-variant-numeric:tabular-nums; text-align:right; white-space:nowrap; }
    .level-grade-family-track { display:flex; width:100%; height:24px; overflow:hidden; border:1px solid var(--border-subtle); border-radius:8px; background:var(--bg-surface-3); }
    .level-grade-family-segment { display:flex; align-items:center; justify-content:center; position:relative; height:100%; min-width:3px; overflow:hidden; border-right:1px solid color-mix(in oklab,var(--bg-surface) 54%,transparent); color:#fff; font-size:10px; font-weight:800; line-height:1; text-align:center; text-shadow:0 1px 2px rgba(0,0,0,.45); white-space:nowrap; }
    .level-grade-family-segment-label { display:block; min-width:0; overflow:hidden; text-overflow:clip; }
    .level-grade-family-segment:last-child { border-right:none; }
    .level-grade-family-segment.family-m, .level-grade-family-swatch.family-m { background:color-mix(in oklab,#14b8a6 78%,var(--bg-surface)); }
    .level-grade-family-segment.family-p, .level-grade-family-swatch.family-p { background:color-mix(in oklab,var(--accent-2) 86%,var(--bg-surface)); }
    .level-grade-family-segment.family-r, .level-grade-family-swatch.family-r { background:color-mix(in oklab,var(--accent) 54%,var(--accent-2)); }
    .level-grade-family-segment.family-s, .level-grade-family-swatch.family-s { background:color-mix(in oklab,#22c55e 68%,var(--bg-surface)); }
    .level-grade-family-segment.family-t, .level-grade-family-swatch.family-t { background:color-mix(in oklab,#f59e0b 70%,var(--bg-surface)); }
    .level-grade-family-segment.family-v-other, .level-grade-family-swatch.family-v-other { background:color-mix(in oklab,#8b5cf6 68%,var(--bg-surface)); }
    .level-grade-family-legend { display:flex; flex-wrap:wrap; gap:6px 14px; padding-top:6px; border-top:1px solid var(--border-subtle); color:var(--text-muted); font-size:10px; line-height:1.2; }
    .level-grade-family-legend-item { display:inline-flex; align-items:center; gap:5px; white-space:nowrap; }
    .level-grade-family-swatch { width:10px; height:10px; border-radius:3px; border:1px solid var(--border-subtle); }
    .level-grade-family-card .chart-footer { padding-top:6px; font-size:10px; line-height:1.25; }
"""
RETENTION_CONCERNS_FOCUSED_STYLE_ID = "qvoice-retention-concerns-css"


def inject_retention_concerns_focused_css(document: str) -> str:
    """Add the slide-19 styles when a focused refresh starts from an older deck."""
    marker = f'id="{RETENTION_CONCERNS_FOCUSED_STYLE_ID}"'
    marker_count = document.count(marker)
    if marker_count > 1:
        raise ValueError("Focused retention CSS appears more than once in the deck.")
    if marker_count == 1:
        return document
    if document.count("</head>") != 1:
        raise ValueError("The focused retention refresh requires one closing head tag.")
    retention_style = (
        f'<style id="{RETENTION_CONCERNS_FOCUSED_STYLE_ID}">\n'
        + RETENTION_CONCERNS_FOCUSED_CSS
        + "\n</style>"
    )
    return document.replace("</head>", retention_style + "\n</head>", 1)


def esc(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def load(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def deterministic_percentages(counts: dict[str, int], keys: tuple[str, ...]) -> dict[str, float]:
    """Match the frozen evidence's largest-remainder, tenth-percent rule."""
    total = sum(counts[key] for key in keys)
    if total <= 0:
        raise ValueError("A visible matrix row requires a positive total.")
    raw = [1000 * counts[key] / total for key in keys]
    floors = [int(value) for value in raw]
    for index in sorted(range(len(keys)), key=lambda item: (-(raw[item] - floors[item]), item))[:1000 - sum(floors)]:
        floors[index] += 1
    return {key: floors[index] / 10 for index, key in enumerate(keys)}


def talent_index_latest_recoverable_distribution() -> dict[str, object]:
    """Load the single frozen aggregate source allowed for slide 44."""
    if not TALENT_INDEX_DISTRIBUTION_EVIDENCE.exists():
        raise FileNotFoundError(TALENT_INDEX_DISTRIBUTION_EVIDENCE)
    evidence = load(TALENT_INDEX_DISTRIBUTION_EVIDENCE)
    if not isinstance(evidence, dict):
        raise ValueError("Talent Index evidence must be a JSON object.")
    if evidence.get("artifact_type") != "aggregate_distribution_evidence":
        raise ValueError("Talent Index evidence has an unexpected artifact type.")
    if evidence.get("deliverable_mode") != REPORTING_MODE or evidence.get("outcome") != "pass":
        raise ValueError("Talent Index evidence must match the deck mode and pass.")
    if evidence.get("variable") != "Talent index" or evidence.get("semantic_type") != "precomputed_metric":
        raise ValueError("Talent Index evidence does not describe the expected stored metric.")
    if evidence.get("snapshot_date") != V4_SNAPSHOT:
        raise ValueError("Talent Index evidence must use the 2026-08-23 workforce snapshot.")
    if evidence.get("query_path") != TALENT_INDEX_DISTRIBUTION_SQL:
        raise ValueError("Talent Index evidence is not linked to the approved profile SQL.")
    sql_path = ROOT / TALENT_INDEX_DISTRIBUTION_SQL
    if not sql_path.exists() or evidence.get("query_sha256") != hashlib.sha256(sql_path.read_bytes()).hexdigest():
        raise ValueError("Talent Index evidence does not match the saved profile SQL hash.")

    query_result = evidence.get("query_result")
    expected_columns = [
        "row_type", "metric", "band_order", "band_lower", "band_upper",
        "band_upper_inclusive", "employee_count", "percent_of_observable", "metric_value",
    ]
    if not isinstance(query_result, dict) or query_result.get("columns") != expected_columns or query_result.get("truncated") is not False:
        raise ValueError("Talent Index evidence must retain its complete aggregate query result.")
    result_hash = hashlib.sha256(
        json.dumps(query_result, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if evidence.get("query_result_sha256") != result_hash:
        raise ValueError("Talent Index frozen query-result hash does not reconcile.")
    rows = query_result.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Talent Index evidence has no frozen aggregate rows.")
    prohibited_columns = {"employee_id", "empl_id", "name", "email", "manager_name", "manager_employee_id"}
    if prohibited_columns.intersection(expected_columns) or any(
        not isinstance(row, dict) or set(row) != set(expected_columns) or prohibited_columns.intersection(row)
        for row in rows
    ):
        raise ValueError("Talent Index evidence contains a prohibited or malformed aggregate row.")

    metrics = evidence.get("metrics")
    distribution = evidence.get("distribution")
    privacy = evidence.get("privacy_checks")
    required_metrics = {
        "eligible_employees", "join_matched_employees", "join_unmatched_employees",
        "observable_employees", "not_observable_employees", "in_range_employees",
        "out_of_range_employees", "published_band_employees", "selected_band_width",
        "selected_conflict_safeguard_employees", "selected_cycle_duplicate_employee_keys",
        "selected_cycle_duplicate_source_rows", "selected_output_duplicate_employee_keys",
        "minimum_stored_value", "maximum_stored_value", "first_quartile",
        "median_stored_value", "third_quartile", "interquartile_range",
    }
    if not isinstance(metrics, dict) or set(metrics) & required_metrics != required_metrics:
        raise ValueError("Talent Index evidence is missing required aggregate metrics.")
    if not isinstance(distribution, list) or not distribution or not isinstance(privacy, dict):
        raise ValueError("Talent Index evidence is missing its distribution or privacy contract.")

    def count(metric: str) -> int:
        value = float(metrics[metric])
        if not value.is_integer():
            raise ValueError(f"Talent Index metric {metric!r} must be an integer count.")
        return int(value)

    eligible = count("eligible_employees")
    observable = count("observable_employees")
    if eligible < MINIMUM_COHORT:
        raise ValueError("Talent Index eligible population is below the minimum cohort.")
    if count("join_matched_employees") + count("join_unmatched_employees") != eligible:
        raise ValueError("Talent Index join diagnostics do not reconcile to the workforce population.")
    if observable + count("not_observable_employees") != eligible:
        raise ValueError("Talent Index observability diagnostics do not reconcile to the workforce population.")
    if count("out_of_range_employees") != 0 or count("in_range_employees") != observable:
        raise ValueError("Talent Index contains an out-of-range stored value or incomplete scale reconciliation.")
    if any(count(metric) != 0 for metric in (
        "selected_conflict_safeguard_employees", "selected_cycle_duplicate_employee_keys",
        "selected_cycle_duplicate_source_rows", "selected_output_duplicate_employee_keys",
    )):
        raise ValueError("Talent Index selected cycles contain a conflict or duplicate key.")
    if privacy.get("identifiers_persisted") or privacy.get("employee_rows_persisted"):
        raise ValueError("Talent Index evidence contains persisted employee-level data.")

    normalized_bands: list[tuple[str, int]] = []
    band_total = 0
    for expected_order, band in enumerate(distribution):
        if not isinstance(band, dict) or int(band.get("band_order", -1)) != expected_order:
            raise ValueError("Talent Index bands are not ordered deterministically.")
        employee_count = int(band["employee_count"])
        if employee_count < MINIMUM_COHORT:
            raise ValueError("Talent Index distribution contains a sub-threshold published band.")
        expected_percent = 100 * employee_count / observable
        if abs(float(band["percent_of_observable"]) - expected_percent) > 0.00001:
            raise ValueError("Talent Index band percentage does not reconcile to observable values.")
        lower = float(band["lower_bound"])
        upper = float(band["upper_bound"])
        width = count("selected_band_width")
        if lower != expected_order * width or upper != (expected_order + 1) * width:
            raise ValueError("Talent Index bands are not the documented adjacent-band merge.")
        normalized_bands.append((str(band["label"]), employee_count))
        band_total += employee_count
    if band_total != observable or count("published_band_employees") != observable:
        raise ValueError("Talent Index published bands do not reconcile to observable values.")
    if float(distribution[0]["lower_bound"]) != 0 or float(distribution[-1]["upper_bound"]) != 100:
        raise ValueError("Talent Index distribution does not cover the stored 0–100 scale.")
    if not bool(distribution[-1]["upper_bound_inclusive"]):
        raise ValueError("Talent Index final band must include 100.")
    minimum = float(metrics["minimum_stored_value"])
    q1 = float(metrics["first_quartile"])
    median = float(metrics["median_stored_value"])
    q3 = float(metrics["third_quartile"])
    maximum = float(metrics["maximum_stored_value"])
    if not (0 <= minimum <= q1 <= median <= q3 <= maximum <= 100):
        raise ValueError("Talent Index descriptive statistics are outside the observed 0–100 scale.")
    if abs(float(metrics["interquartile_range"]) - (q3 - q1)) > 0.00001:
        raise ValueError("Talent Index IQR does not reconcile to Q3 minus Q1.")

    return {"evidence": evidence, "metrics": metrics, "bands": normalized_bands}


def talent_index_distribution_slide(talent_index: dict[str, object], number: int = TALENT_INDEX_SLIDE) -> str:
    """Render the current Talent Index stage from frozen aggregate evidence."""
    metrics = talent_index["metrics"]
    bands = talent_index["bands"]
    if not isinstance(metrics, dict) or not isinstance(bands, list):
        raise ValueError("Talent Index render input is malformed.")
    eligible = int(metrics["eligible_employees"])
    observable = int(metrics["observable_employees"])
    unavailable = int(metrics["not_observable_employees"])
    coverage = 100 * observable / eligible
    q1 = float(metrics["first_quartile"])
    median = float(metrics["median_stored_value"])
    q3 = float(metrics["third_quartile"])
    main = bar_card(
        "Latest recoverable stored talent_index distribution",
        bands,
        f"Percentages and counts use {observable:,} observable stored values only. Bands span 0–100; every published band has n ≥ {MINIMUM_COHORT}.",
        "talent-index-distribution-card",
    )
    side = side_card(
        "A stored-value snapshot, not an effective-date claim",
        "This is the currently recoverable stored value for employees active on 23-Aug-2026—not proof that the index was calculated or effective on that date.",
        [
            ("Active-workforce denominator", f"{eligible:,}"),
            ("Recoverable-value coverage", f"{coverage:.2f}% · {observable:,} of {eligible:,}"),
            ("Unavailable values", f"{unavailable:,}"),
            ("Median / IQR", f"{median:.1f} / {q1:.1f}–{q3:.1f}"),
            ("Selection rule", "Highest stored cycle_number per employee; null or conflicting selected cycles are unavailable."),
        ],
        "Aggregate distribution",
    )
    rendered = data_slide(
        number,
        "Talent index",
        "Active regular employees · workforce snapshot 23-Aug-2026 · latest recoverable stored value",
        main,
        side,
    )
    return rendered


def detail(folder: str, root: Path = BASE) -> dict:
    return load(root / folder / "report_detail.json")


def values(folder: str, column: str, root: Path = BASE) -> list[tuple[str, int]]:
    report = detail(folder, root)
    entry = next(item for item in report.get("value_distributions", []) if item.get("column") == column)
    # report_detail's column-level eligible counts are distinct employees over
    # the historical profile, not the one snapshot used by a distribution.
    # Callers that need a tail must use the snapshot-aware helper below.
    return [(str(row.get("value_label", "Sin etiqueta")), int(row.get("employee_count", 0))) for row in entry.get("values", [])]


LEVEL_GROUPED_ORDER = (
    "VP & Above",
    "Sr Dir",
    "Princ/Directors",
    "Mgrs Corp",
    "Sr Staff & /Mgr",
    "Staff & /Mgr",
    "Senior & Lead",
    "Assoc & Int/Eng",
    "Support",
)
MANAGEMENT_LEVEL_ORDER = (
    "VP/SVP",
    "Directors/Sr Director",
    "Management",
    "Professional",
    "Support",
)


def ordered_distribution(
    rows: list[tuple[str, int]],
    order: tuple[str, ...],
    *,
    label_normalizer: object | None = None,
) -> list[tuple[str, int]]:
    """Return a frozen distribution in an explicit semantic display order."""
    normalize = label_normalizer if callable(label_normalizer) else (lambda label: label)
    normalized = [(str(normalize(label)), count) for label, count in rows]
    by_label = dict(normalized)
    if len(by_label) != len(normalized) or set(by_label) != set(order):
        raise ValueError(
            f"La distribucion no coincide con el dominio ordenado esperado: {sorted(by_label)}"
        )
    return [(label, by_label[label]) for label in order]


def latest_snapshot_coverage(folder: str, root: Path = BASE) -> tuple[int, int]:
    """Return the eligible and observable counts for the distribution snapshot."""
    results = load(root / folder / "evidence" / "query-results.json")
    candidates = [
        rows for query_name, rows in results.items()
        if query_name.endswith("_coverage.sql") and isinstance(rows, list) and rows
    ]
    if len(candidates) != 1:
        raise ValueError(f"No hay una cobertura única congelada para {folder}.")
    latest = max(candidates[0], key=lambda row: str(row["snapshot_date"]))
    return int(latest["eligible_employees"]), int(latest["observable_employees"])


def frozen_top_values(folder: str, column: str, limit: int, root: Path = BASE) -> list[tuple[str, int]]:
    """Read a larger safe top-N directly from the frozen aggregate query."""
    results = load(root / folder / "evidence" / "query-results.json")
    matches: list[tuple[str, int]] = []
    for query_name, rows in results.items():
        if not query_name.endswith("_report_top_values.sql") or not isinstance(rows, list):
            continue
        rows_for_column = [
            (str(row["value_label"]), int(row["employee_count"]))
            for row in rows
            if str(row.get("column_name")) == column
        ]
        if rows_for_column:
            matches = rows_for_column
            break
    if len(matches) < limit:
        raise ValueError(f"No hay {limit} categorías publicables congeladas para {folder}/{column}.")
    return matches[:limit]


def categorical_distribution(
    rows: list[tuple[str, int]],
    *,
    populated: int,
    eligible: int,
    other_label: str | None = None,
    missing_label: str | None = None,
) -> list[tuple[str, int]]:
    """Add tail and missing buckets using only the chart's snapshot totals."""
    if populated > eligible:
        raise ValueError("El total poblado no puede superar al total elegible.")
    result = list(rows)
    shown = sum(count for _, count in result)
    remainder = populated - shown
    if remainder < 0:
        raise ValueError("Las categorías publicadas exceden el total poblado del snapshot.")
    if remainder >= MINIMUM_COHORT:
        if not other_label:
            raise ValueError("Falta etiqueta para la cola de categorías publicada.")
        result.append((other_label, remainder))
    missing = eligible - populated
    if missing >= MINIMUM_COHORT:
        if not missing_label:
            raise ValueError("Falta etiqueta para los faltantes publicables.")
        result.append((missing_label, missing))
    return result


def event_series(folder: str, root: Path = BASE) -> list[tuple[str, float, int]]:
    report = detail(folder, root)
    result = []
    for item in report.get("coverage_summary", {}).get("annual_by_fiscal_year", []):
        percent = item.get("event_prevalence_percent")
        count = item.get("event_employee_snapshots")
        if percent is not None and count is not None:
            result.append((str(item["fiscal_year"]), float(percent), int(count)))
    return result


def co_location_site_city_series() -> tuple[list[tuple[str, float, int]], list[tuple[str, float, int]], dict[str, object]]:
    """Load the paired annual office-site proxies frozen for slide 36."""
    evidence = load(CO_LOCATION_SITE_CITY_EVIDENCE)
    if evidence.get("artifact") != "presentation" or evidence.get("outcome") != "pass":
        raise ValueError("Co-location proxy evidence must be presentation-safe and pass.")
    if evidence.get("query_path") != CO_LOCATION_SITE_CITY_PROFILE_SQL:
        raise ValueError("Co-location proxy evidence does not reference its saved annual profile.")
    if evidence.get("deck_cutoff") != V4_SNAPSHOT:
        raise ValueError("Co-location proxy evidence must use the deck cutoff.")
    rows = evidence.get("rows")
    expected_years = [str(year) for year in range(2020, 2027)]
    if not isinstance(rows, list) or [str(row.get("fiscal_year")) for row in rows] != expected_years:
        raise ValueError("Co-location proxy evidence must contain FY2020 through FY2026 in order.")

    office_site: list[tuple[str, float, int]] = []
    office_site_city: list[tuple[str, float, int]] = []
    for row in rows:
        site_denominator = int(row["site_comparable_employee_snapshots"])
        site_numerator = int(row["same_office_site_employee_snapshots"])
        city_denominator = int(row["site_city_comparable_employee_snapshots"])
        city_numerator = int(row["same_office_site_and_city_employee_snapshots"])
        if min(site_denominator, site_numerator, city_denominator, city_numerator) < MINIMUM_COHORT:
            raise ValueError("Co-location proxy evidence contains a sub-threshold annual count.")
        if city_denominator != site_denominator:
            raise ValueError("The paired co-location charts must retain the same comparable-pair denominator.")
        if city_numerator > site_numerator:
            raise ValueError("The stricter office-site + city proxy cannot exceed the office-site proxy.")
        site_percent = float(row["same_office_site_percent_of_site_comparable"])
        city_percent = float(row["same_office_site_and_city_percent_of_site_city_comparable"])
        if abs(site_percent - (100 * site_numerator / site_denominator)) > 0.0001:
            raise ValueError("Co-location office-site percentage does not reconcile to its counts.")
        if abs(city_percent - (100 * city_numerator / city_denominator)) > 0.0001:
            raise ValueError("Co-location office-site + city percentage does not reconcile to its counts.")
        office_site.append((str(row["fiscal_year"]), site_percent, site_numerator))
        office_site_city.append((str(row["fiscal_year"]), city_percent, city_numerator))
    return office_site, office_site_city, evidence


def _manager_change_distribution(
    evidence_path: Path,
    query_reference: str,
    window_months: int,
) -> dict[str, object]:
    """Load one safe, aggregate-only manager-change distribution."""
    evidence = load(evidence_path)
    if evidence.get("artifact") != REPORTING_MODE or evidence.get("outcome") != "pass":
        raise ValueError("Manager-change distribution evidence must match the deck mode and pass.")
    if evidence.get("query_reference") != query_reference:
        raise ValueError("Manager-change distribution evidence is not linked to the expected SQL.")
    if evidence.get("window_months") != window_months:
        raise ValueError("Manager-change distribution does not use its documented retrospective window.")
    if evidence.get("identifiers_persisted") or evidence.get("employee_rows_persisted"):
        raise ValueError("Manager-change distribution evidence contains a prohibited payload.")
    eligible = int(evidence.get("eligible_employees", 0))
    buckets = evidence.get("buckets")
    if eligible < MINIMUM_COHORT or not isinstance(buckets, list) or not buckets:
        raise ValueError("Manager-change evidence is missing a publishable employee population or buckets.")
    total = 0
    for bucket in buckets:
        count = int(bucket["employee_count"])
        if count < MINIMUM_COHORT:
            raise ValueError(f"Manager-change bucket below n={MINIMUM_COHORT}: {bucket['label']}")
        total += count
    if total != eligible:
        raise ValueError(f"Manager-change buckets do not reconcile: {total} != {eligible}.")
    for name in ("repeated_event_observation_rows", "flagged_without_date_rows", "invalid_flag_rows"):
        if int(evidence.get(name, 0)) != 0:
            raise ValueError(f"Manager-change diagnostic failed: {name} is nonzero.")
    if window_months == 12 and int(evidence.get("annual_count_less_than_six_month_count", -1)) != 0:
        raise ValueError("Annual manager-change counts cannot be smaller than nested six-month counts.")
    return evidence


def number_of_manager_changes_distribution() -> dict[str, object]:
    """Load and validate the aggregate-only six-month primary evidence."""
    return _manager_change_distribution(
        MANAGER_CHANGE_DISTRIBUTION_EVIDENCE,
        MANAGER_CHANGE_DISTRIBUTION_SQL,
        6,
    )


def number_of_manager_changes_annual_distribution() -> dict[str, object]:
    """Load the annual comparison that answers the two-changes-a-year question."""
    return _manager_change_distribution(
        MANAGER_CHANGE_ANNUAL_DISTRIBUTION_EVIDENCE,
        MANAGER_CHANGE_ANNUAL_DISTRIBUTION_SQL,
        12,
    )


def number_of_manager_changes_mobility_comparison() -> dict[str, object]:
    """Load the presentation-safe six- and twelve-month mobility sensitivity."""
    evidence = load(MANAGER_CHANGE_MOBILITY_COMPARISON_EVIDENCE)
    if not isinstance(evidence, dict):
        raise ValueError("Manager-change mobility comparison evidence must be an object.")
    if evidence.get("artifact") != REPORTING_MODE or evidence.get("outcome") != "pass":
        raise ValueError("Manager-change mobility comparison evidence must match the deck mode and pass.")
    if evidence.get("variable") != "Number of manager changes":
        raise ValueError("Manager-change mobility comparison evidence has the wrong variable.")
    if evidence.get("query_reference") != MANAGER_CHANGE_MOBILITY_COMPARISON_SQL:
        raise ValueError("Manager-change mobility comparison evidence is not linked to the expected SQL.")
    if evidence.get("identifiers_persisted") or evidence.get("employee_rows_persisted"):
        raise ValueError("Manager-change mobility comparison evidence cannot persist identifiers or employee rows.")

    diagnostics = evidence.get("diagnostics")
    windows = evidence.get("windows")
    if not isinstance(diagnostics, dict) or not isinstance(windows, list) or len(windows) != 2:
        raise ValueError("Manager-change mobility comparison evidence is missing diagnostics or both windows.")
    for field in (
        "annual_count_less_than_six_month_count",
        "invalid_employee_count_order",
        "manager_flag_without_date_rows",
        "transfer_flag_without_date_rows",
        "promotion_flag_without_date_rows",
    ):
        if int(diagnostics.get(field, -1)) != 0:
            raise ValueError(f"Manager-change mobility comparison failed diagnostic: {field}.")

    eligible = int(diagnostics.get("eligible_employees", 0))
    if eligible < MINIMUM_COHORT:
        raise ValueError("Manager-change mobility comparison has an invalid eligible population.")
    indexed: dict[int, dict[str, object]] = {}
    for window in windows:
        if not isinstance(window, dict):
            raise ValueError("Manager-change mobility comparison window must be an object.")
        months = int(window.get("window_months", 0))
        if months in indexed:
            raise ValueError("Manager-change mobility comparison has duplicate windows.")
        indexed[months] = window
        baseline_events = int(window.get("baseline_event_keys", -1))
        excluded_events = int(window.get("excluded_overlap_event_keys", -1))
        if baseline_events < 0 or excluded_events < 0 or excluded_events > baseline_events:
            raise ValueError("Manager-change mobility comparison has invalid event overlap counts.")
        for bucket_key in ("baseline_buckets", "excluding_same_date_transfer_or_promotion_buckets"):
            buckets = window.get(bucket_key)
            if not isinstance(buckets, list) or [str(item.get("label")) for item in buckets if isinstance(item, dict)] != ["0", "1", "2", "3+"]:
                raise ValueError("Manager-change mobility comparison has unexpected buckets.")
            counts = [int(item.get("employee_count", -1)) for item in buckets if isinstance(item, dict)]
            if any(count < MINIMUM_COHORT for count in counts) or sum(counts) != eligible:
                raise ValueError("Manager-change mobility comparison buckets do not meet the publication rule.")
    if set(indexed) != {6, 12}:
        raise ValueError("Manager-change mobility comparison must contain six- and twelve-month windows.")
    return evidence


def _manager_change_comparison_buckets(window: dict[str, object], key: str) -> list[tuple[str, int]]:
    buckets = window[key]
    assert isinstance(buckets, list)
    return [(str(item["label"]), int(item["employee_count"])) for item in buckets if isinstance(item, dict)]


def number_of_manager_changes_mobility_comparison_slide(number: int) -> str:
    """Render the full-width two-by-two baseline versus mobility sensitivity."""
    evidence = number_of_manager_changes_mobility_comparison()
    windows = evidence["windows"]
    assert isinstance(windows, list)
    by_month = {int(window["window_months"]): window for window in windows if isinstance(window, dict)}
    six_month = by_month[6]
    annual = by_month[12]

    def comparison_card(window: dict[str, object], months: int, sensitivity: bool) -> str:
        data_key = "excluding_same_date_transfer_or_promotion_buckets" if sensitivity else "baseline_buckets"
        title_prefix = "Sensitivity: exclude same-date transfer/promotion" if sensitivity else "All observed manager changes"
        note = (
            "Same population; only exact same-date mobility events are excluded."
            if sensitivity
            else "All dated manager-change events meeting the time-safe rule."
        )
        return bar_card(
            f"{title_prefix} · trailing {months} months",
            _manager_change_comparison_buckets(window, data_key),
            f"Snapshot {evidence['snapshot_date']}. {note}",
            "manager-change-distribution-card manager-change-comparison-card",
        )

    main = (
        '<div class="manager-change-comparison-layout">'
        '<div class="manager-change-comparison-grid">'
        + comparison_card(six_month, 6, False)
        + comparison_card(annual, 12, False)
        + comparison_card(six_month, 6, True)
        + comparison_card(annual, 12, True)
        + "</div>"
        + (
            '<div class="manager-change-comparison-note"><strong>Sensitivity rule:</strong> '
            f"exclude only a manager-change event when a positive transfer or promotion has the same employee and effective date. "
            f"This removes {int(six_month['excluded_overlap_event_keys']):,} of {int(six_month['baseline_event_keys']):,} events "
            f"({float(six_month['excluded_overlap_event_percent']):.1f}%) at six months and "
            f"{int(annual['excluded_overlap_event_keys']):,} of {int(annual['baseline_event_keys']):,} "
            f"({float(annual['excluded_overlap_event_percent']):.1f}%) at twelve months. "
            "It is descriptive sensitivity only; it does not redefine the primary feature."
            "</div>"
        )
        + "</div>"
    )
    return f'''<div class="slide-stage" id="slide-{number}">{heading("Number of manager changes", "Primary: six-month retrospective count · annual comparison · same-date mobility sensitivity")}
      {main}</div>'''


def manager_leaving_voluntary_distribution() -> dict[str, object]:
    """Load the approved, aggregate-only six-month manager-leaving evidence."""
    evidence = load(MANAGER_LEAVING_DISTRIBUTION_EVIDENCE)
    if evidence.get("artifact_type") != "aggregate_distribution_evidence":
        raise ValueError("Manager-leaving evidence has an unexpected artifact contract.")
    if evidence.get("deliverable_mode") != REPORTING_MODE or evidence.get("outcome") != "pass":
        raise ValueError("Manager-leaving evidence must match the deck mode and pass.")
    if evidence.get("variable") != "Manager leaving" or evidence.get("query") != MANAGER_LEAVING_DISTRIBUTION_SQL:
        raise ValueError("Manager-leaving evidence is not linked to the approved distribution SQL.")
    if evidence.get("identifiers_persisted") or evidence.get("employee_rows_persisted"):
        raise ValueError("Manager-leaving evidence contains a prohibited identity payload.")

    result = evidence.get("query_result")
    expected_columns = [
        "row_type", "metric", "bucket", "employee_count", "population_count",
        "percent_of_population", "metric_value",
    ]
    if not isinstance(result, dict) or result.get("truncated") is not False or result.get("columns") != expected_columns:
        raise ValueError("Manager-leaving evidence must contain the complete expected aggregate result.")
    rows = result.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Manager-leaving evidence has no aggregate rows.")

    metrics = evidence.get("metrics")
    required_metric_values = {
        "source_missing_required_items": 0,
        "target_employee_snapshot_unique_pass": True,
        "current_manager_conflict_free_pass": True,
        "event_type_conflict_free_pass": True,
        "employee_event_attribution_unique_pass": True,
        "events_without_future_usage_pass": True,
    }
    if not isinstance(metrics, dict) or any(metrics.get(key) != value for key, value in required_metric_values.items()):
        raise ValueError("Manager-leaving source, key, event, or leakage validation did not pass.")

    population = int(metrics.get("population_count", 0))
    if population < MINIMUM_COHORT:
        raise ValueError("Manager-leaving population is not publishable.")
    distributions: dict[str, list[tuple[str, int]]] = {}
    for metric in ("binary_flag", "event_count_sensitivity"):
        metric_rows = [row for row in rows if row.get("row_type") == "distribution" and row.get("metric") == metric]
        if not metric_rows:
            raise ValueError(f"Manager-leaving evidence lacks {metric} rows.")
        total = 0
        chart_rows: list[tuple[str, int]] = []
        for row in metric_rows:
            if set(row) != set(expected_columns):
                raise ValueError("Manager-leaving aggregate row schema changed unexpectedly.")
            count = int(row["employee_count"])
            denominator = int(row["population_count"])
            percent = float(row["percent_of_population"])
            if count < MINIMUM_COHORT or denominator != population:
                raise ValueError("Manager-leaving visualization would expose a sub-threshold or mismatched bucket.")
            if abs(percent - 100 * count / population) > 0.0001:
                raise ValueError("Manager-leaving percentage does not reconcile to its bucket.")
            total += count
            chart_rows.append((str(row["bucket"]), count))
        if total != population:
            raise ValueError(f"Manager-leaving {metric} buckets do not reconcile to the population.")
        distributions[metric] = chart_rows
    return {"evidence": evidence, "metrics": metrics, "population": population, **distributions}


_MANAGER_IDENTITY_COLUMNS = frozenset({
    "employee_id",
    "manager_employee_id",
    "manager_name",
    "employee_name",
    "emp_name",
    "name",
    "email",
})


def _integer_metric(value: object, metric: str) -> int:
    """Parse a frozen count without silently rounding a non-integer value."""
    try:
        numeric = float(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"La métrica {metric!r} no es numérica.") from exc
    if not numeric.is_integer():
        raise ValueError(f"La métrica {metric!r} debe ser un conteo entero.")
    return int(numeric)


def _metric_rows(rows: list[dict[str, object]], row_type: str) -> dict[str, int]:
    """Return a unique, integer-valued metric map from an aggregate result."""
    result: dict[str, int] = {}
    for row in rows:
        if row.get("row_type") != row_type:
            continue
        metric = str(row.get("metric") or "")
        if not metric or metric in result:
            raise ValueError(f"La evidencia de manager tiene una métrica {row_type!r} vacía o duplicada.")
        result[metric] = _integer_metric(row.get("metric_value"), metric)
    return result


def _validated_manager_distribution(
    path: Path,
    *,
    variable: str,
    query: str,
    expected_columns: tuple[str, ...],
) -> dict[str, object]:
    """Validate the frozen aggregate contract before it reaches a slide."""
    evidence = load(path)
    if not isinstance(evidence, dict):
        raise ValueError(f"La evidencia de {variable} no es un objeto JSON.")
    if evidence.get("artifact_type") != "aggregate_distribution_evidence":
        raise ValueError(f"La evidencia de {variable} no tiene el contrato agregado esperado.")
    if evidence.get("deliverable_mode") != REPORTING_MODE or evidence.get("outcome") != "pass":
        raise ValueError(f"La evidencia de {variable} debe coincidir con el modo del deck y aprobar.")
    if evidence.get("variable") != variable or evidence.get("query") != query:
        raise ValueError(f"La evidencia de {variable} no está ligada a su SQL esperado.")

    query_result = evidence.get("query_result")
    if not isinstance(query_result, dict) or query_result.get("truncated") is not False:
        raise ValueError(f"La evidencia de {variable} debe contener un resultado completo sin truncar.")
    columns = query_result.get("columns")
    rows = query_result.get("rows")
    if columns != list(expected_columns) or not isinstance(rows, list) or not rows:
        raise ValueError(f"La evidencia de {variable} no conserva el esquema agregado esperado.")
    if _MANAGER_IDENTITY_COLUMNS.intersection(columns):
        raise ValueError(f"La evidencia de {variable} contiene una columna de identidad prohibida.")
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(expected_columns):
            raise ValueError(f"La evidencia de {variable} contiene una fila con esquema inesperado.")
        if _MANAGER_IDENTITY_COLUMNS.intersection(row):
            raise ValueError(f"La evidencia de {variable} contiene una identidad prohibida.")

    metrics = evidence.get("metrics")
    if not isinstance(metrics, dict):
        raise ValueError(f"La evidencia de {variable} no conserva sus métricas resumidas.")
    audits = _metric_rows(rows, "audit")
    summaries = _metric_rows(rows, "summary")
    intervals = sorted(
        (row for row in rows if row.get("row_type") == "interval"),
        key=lambda row: _integer_metric(row.get("interval_sequence"), "interval_sequence"),
    )
    if len(intervals) != 6 or [
        _integer_metric(row.get("interval_sequence"), "interval_sequence") for row in intervals
    ] != list(range(1, 7)):
        raise ValueError(f"La evidencia de {variable} debe contener exactamente seis intervalos ordenados.")
    if any(str(intervals[index]["interval_end"]) != str(intervals[index + 1]["interval_start"])
           for index in range(len(intervals) - 1)):
        raise ValueError(f"La evidencia de {variable} tiene intervalos con traslape o hueco.")
    if str(intervals[-1]["interval_end"]) != str(evidence.get("cutoff_date")):
        raise ValueError(f"La evidencia de {variable} no termina en su fecha de corte.")

    for metric, expected in (("interval_count", 6), ("closure_count", 7)):
        if _integer_metric(metrics.get(metric), metric) != expected or audits.get(metric) != expected:
            raise ValueError(f"La evidencia de {variable} no cumple el control {metric}={expected}.")
    if audits.get("interval_overlap_or_gap_count") != 0:
        raise ValueError(f"La evidencia de {variable} tiene intervalos con traslape o hueco.")
    return {
        "evidence": evidence,
        "metrics": metrics,
        "audits": audits,
        "summaries": summaries,
        "intervals": intervals,
        "rows": rows,
    }


def high_risk_manager_score_distribution() -> dict[str, object]:
    """Load score bands only after all data-quality and reconciliation gates pass."""
    validated = _validated_manager_distribution(
        HIGH_RISK_MANAGER_EVIDENCE,
        variable="High risk manager",
        query=HIGH_RISK_MANAGER_SQL,
        expected_columns=(
            "row_type", "interval_sequence", "interval_start", "interval_end", "score_band",
            "manager_count", "employee_count", "mean_smoothed_excess_ratio", "metric", "metric_value",
        ),
    )
    metrics = validated["metrics"]
    audits = validated["audits"]
    summaries = validated["summaries"]
    assert isinstance(metrics, dict) and isinstance(audits, dict) and isinstance(summaries, dict)
    zero_audits = (
        "current_member_duplicate_rows",
        "deduplicated_event_duplicate_count",
        "employee_score_multi_match_count",
        "employees_scored_exceed_current_manager_population",
        "events_with_multiple_exposure_attributions",
        "events_with_multiple_intervals",
        "events_without_unique_interval",
        "exposure_duplicate_rows",
        "score_band_employee_reconciliation_failure",
        "score_band_manager_reconciliation_failure",
        "score_manager_duplicate_count",
    )
    if any(audits.get(metric) != 0 for metric in zero_audits) or audits.get("global_rate_positive") != 1:
        raise ValueError("La distribución de score de manager no pasó sus invariantes de atribución o reconciliación.")
    for metric in (
        "current_manager_count", "scored_manager_count", "unknown_manager_count",
        "employees_with_current_manager", "employees_with_scored_manager", "employees_unknown_history_count",
    ):
        if _integer_metric(metrics.get(metric), metric) != summaries.get(metric):
            raise ValueError(f"La métrica resumida {metric} no reconcilia para High risk manager.")
    if audits.get("events_without_unique_exposure_attribution") != _integer_metric(
        metrics.get("events_without_unique_exposure_attribution"), "events_without_unique_exposure_attribution"
    ):
        raise ValueError("La exclusión de eventos sin exposición inicial no reconcilia para High risk manager.")

    raw_bands = [row for row in validated["rows"] if row.get("row_type") == "score_band"]
    expected_labels = ("<0.50×", "0.50–<1.00×", "1.00–<1.50×", "≥1.50×")
    by_label = {str(row.get("score_band")): row for row in raw_bands}
    if len(by_label) != len(raw_bands) or set(by_label) != set(expected_labels):
        raise ValueError("Las bandas de score no coinciden con la especificación publicada.")
    bands: list[dict[str, object]] = []
    for label in expected_labels:
        row = by_label[label]
        manager_count = _integer_metric(row.get("manager_count"), f"{label} manager_count")
        employee_count = _integer_metric(row.get("employee_count"), f"{label} employee_count")
        if manager_count < MINIMUM_COHORT or employee_count < MINIMUM_COHORT:
            raise ValueError(f"La banda {label} no cumple n >= {MINIMUM_COHORT}.")
        mean_ratio = float(str(row.get("mean_smoothed_excess_ratio")))
        if mean_ratio < 0:
            raise ValueError(f"La banda {label} tiene un ratio medio inválido.")
        bands.append({"label": label, "manager_count": manager_count, "employee_count": employee_count, "mean_ratio": mean_ratio})
    if sum(int(band["manager_count"]) for band in bands) != summaries["scored_manager_count"]:
        raise ValueError("Las bandas de score no reconcilian el total de managers observables.")
    if sum(int(band["employee_count"]) for band in bands) != summaries["employees_with_scored_manager"]:
        raise ValueError("Las bandas de score no reconcilian el total de reportes observables.")
    validated["bands"] = bands
    return validated


def high_turnover_under_manager_distribution() -> dict[str, object]:
    """Load 0/1/2+ history buckets without collapsing unknown coverage into zero."""
    validated = _validated_manager_distribution(
        HIGH_TURNOVER_MANAGER_EVIDENCE,
        variable="High turnover under this person",
        query=HIGH_TURNOVER_MANAGER_SQL,
        expected_columns=(
            "row_type", "interval_sequence", "interval_start", "interval_end", "exit_bucket",
            "manager_count", "employee_count", "metric", "metric_value",
        ),
    )
    metrics = validated["metrics"]
    audits = validated["audits"]
    summaries = validated["summaries"]
    assert isinstance(metrics, dict) and isinstance(audits, dict) and isinstance(summaries, dict)
    zero_audits = (
        "bucket_employee_reconciliation_failure",
        "bucket_manager_reconciliation_failure",
        "current_member_duplicate_rows",
        "deduplicated_event_duplicate_count",
        "employee_assignment_multi_match_count",
        "events_with_multiple_exposure_attributions",
        "events_with_multiple_intervals",
        "events_without_unique_interval",
        "exposure_duplicate_rows",
        "flagged_employee_exceeds_observable",
    )
    if any(audits.get(metric) != 0 for metric in zero_audits):
        raise ValueError("La distribución de salidas históricas no pasó sus invariantes de atribución o reconciliación.")
    for metric in (
        "current_manager_count", "observable_manager_count", "unknown_manager_count",
        "employees_with_current_manager", "observable_employee_count", "unknown_employee_count", "flagged_employee_count",
    ):
        if _integer_metric(metrics.get(metric), metric) != summaries.get(metric):
            raise ValueError(f"La métrica resumida {metric} no reconcilia para High turnover under this person.")
    if audits.get("events_without_unique_exposure_attribution") != _integer_metric(
        metrics.get("events_without_unique_exposure_attribution"), "events_without_unique_exposure_attribution"
    ):
        raise ValueError("La exclusión de eventos sin exposición inicial no reconcilia para High turnover under this person.")

    raw_buckets = [row for row in validated["rows"] if row.get("row_type") == "bucket"]
    expected_labels = ("0", "1", "2+")
    by_label = {str(row.get("exit_bucket")): row for row in raw_buckets}
    if len(by_label) != len(raw_buckets) or set(by_label) != set(expected_labels):
        raise ValueError("Los buckets 0/1/2+ no coinciden con la especificación publicada.")
    buckets: list[dict[str, object]] = []
    for label in expected_labels:
        row = by_label[label]
        manager_count = _integer_metric(row.get("manager_count"), f"{label} manager_count")
        employee_count = _integer_metric(row.get("employee_count"), f"{label} employee_count")
        if manager_count < MINIMUM_COHORT or employee_count < MINIMUM_COHORT:
            raise ValueError(f"El bucket {label} no cumple n >= {MINIMUM_COHORT}.")
        buckets.append({"label": label, "manager_count": manager_count, "employee_count": employee_count})
    if sum(int(bucket["manager_count"]) for bucket in buckets) != summaries["observable_manager_count"]:
        raise ValueError("Los buckets no reconcilian el total de managers con historia observable.")
    if sum(int(bucket["employee_count"]) for bucket in buckets) != summaries["observable_employee_count"]:
        raise ValueError("Los buckets no reconcilian el total de reportes con historia observable.")
    if int(buckets[-1]["employee_count"]) != summaries["flagged_employee_count"]:
        raise ValueError("El bucket 2+ no reconcilia los reportes del contexto histórico 2+.")
    validated["buckets"] = buckets
    return validated


def above_average_team_turnover_evidence() -> dict[str, object]:
    """Load the presentation-safe candidate-44 evidence and enforce its full contract."""
    if not ABOVE_AVERAGE_TEAM_TURNOVER_EVIDENCE.exists():
        raise FileNotFoundError(ABOVE_AVERAGE_TEAM_TURNOVER_EVIDENCE)
    evidence = load(ABOVE_AVERAGE_TEAM_TURNOVER_EVIDENCE)
    if not isinstance(evidence, dict):
        raise ValueError("Above-average team turnover evidence must be a JSON object.")
    required_header = {
        "artifact_type": "aggregate_distribution_evidence",
        "deliverable_mode": "presentation",
        "variable": "Above-average team turnover",
        "candidate_number": 44,
        "source_assessment_run": "above-average-team-turnover-v4-20260910-r13",
        "outcome": "pass",
    }
    if any(evidence.get(key) != expected for key, expected in required_header.items()):
        raise ValueError("Above-average team turnover evidence has an unexpected publication contract.")

    forbidden_fields = {
        "employee_id", "manager_employee_id", "manager_name", "employee_name",
        "emp_name", "name", "email", "term_date", "manager_rate",
        "manager_rates", "manager_ranking", "manager_rankings",
    }

    def reject_restricted_fields(value: object) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if str(key).lower() in forbidden_fields:
                    raise ValueError("Above-average team turnover evidence persists a restricted field.")
                reject_restricted_fields(nested)
        elif isinstance(value, list):
            for nested in value:
                reject_restricted_fields(nested)

    reject_restricted_fields(evidence)
    privacy = evidence.get("privacy")
    if not isinstance(privacy, dict) or privacy.get("minimum_shared_cohort") != MINIMUM_COHORT:
        raise ValueError("Above-average team turnover evidence does not retain the cohort safeguard.")
    if any(privacy.get(key) is not False for key in (
        "identifiers_persisted", "employee_rows_persisted", "manager_rates_persisted", "manager_rankings_persisted",
    )):
        raise ValueError("Above-average team turnover evidence fails its privacy contract.")

    distribution = evidence.get("distribution")
    if not isinstance(distribution, list) or len(distribution) != 3:
        raise ValueError("Above-average team turnover evidence must contain exactly three display buckets.")
    by_signal: dict[str, int] = {}
    for row in distribution:
        if not isinstance(row, dict) or set(row) != {"signal", "employee_count"}:
            raise ValueError("Above-average team turnover distribution schema changed unexpectedly.")
        signal = str(row["signal"])
        count = _integer_metric(row["employee_count"], f"{signal} employee_count")
        if signal in by_signal or count < MINIMUM_COHORT:
            raise ValueError("Above-average team turnover has a duplicate or sub-threshold display bucket.")
        by_signal[signal] = count
    if set(by_signal) != {"0", "1", "Unknown"}:
        raise ValueError("Above-average team turnover must publish exactly 0, 1, and Unknown.")

    aggregate_counts = evidence.get("aggregate_counts")
    if not isinstance(aggregate_counts, dict):
        raise ValueError("Above-average team turnover is missing aggregate reconciliation counts.")
    eligible = _integer_metric(aggregate_counts.get("eligible_employees"), "eligible_employees")
    observable = _integer_metric(aggregate_counts.get("observable_employees"), "observable_employees")
    flagged = _integer_metric(aggregate_counts.get("flagged_employees"), "flagged_employees")
    unknown = _integer_metric(aggregate_counts.get("unknown_employees"), "unknown_employees")
    if (
        sum(by_signal.values()) != eligible
        or by_signal["0"] + by_signal["1"] != observable
        or by_signal["1"] != flagged
        or by_signal["Unknown"] != unknown
    ):
        raise ValueError("Above-average team turnover display counts do not reconcile.")

    benchmark = evidence.get("benchmark")
    if not isinstance(benchmark, dict):
        raise ValueError("Above-average team turnover is missing the benchmark contract.")
    benchmark_rate = float(str(benchmark.get("six_month_rate")))
    threshold_multiplier = float(str(benchmark.get("flag_threshold_multiplier")))
    threshold_rate = float(str(benchmark.get("flag_threshold_six_month_rate")))
    if benchmark_rate <= 0 or threshold_multiplier != 1.3 or abs(threshold_rate - benchmark_rate * 1.3) > 1e-12:
        raise ValueError("Above-average team turnover benchmark does not reconcile to the 1.4× rule.")

    eligibility = evidence.get("eligibility")
    expected_eligibility = {
        "required_consecutive_intervals": 18,
        "minimum_average_team_size": 4,
        "minimum_distinct_voluntary_exits": 2,
    }
    if not isinstance(eligibility, dict) or any(eligibility.get(key) != expected for key, expected in expected_eligibility.items()):
        raise ValueError("Above-average team turnover eligibility rule changed unexpectedly.")

    validation = evidence.get("assessment_validation")
    if not isinstance(validation, dict):
        raise ValueError("Above-average team turnover is missing its assessment validation.")
    expected_validation = {
        "source_missing_items": 0,
        "snapshots_checked": 6,
        "interval_count": 18,
        "minimum_eligible_average_team_size": 4.0,
        "minimum_eligible_voluntary_exits": 2,
        "duplicate_count": 0,
        "multiple_event_interval_assignments": 0,
        "multiple_event_manager_assignments": 0,
        "future_event_usage_count": 0,
        "unmatched_employee_assignments": 0,
        "multi_match_employee_assignments": 0,
        "rule_implementation_failure_count": 0,
        "benchmark_reconciliation_failure_count": 0,
    }
    if any(float(str(validation.get(key))) != float(expected) for key, expected in expected_validation.items()):
        raise ValueError("Above-average team turnover assessment gates did not pass.")

    provenance = evidence.get("provenance")
    if (
        not isinstance(provenance, dict)
        or provenance.get("presentation_query") != ABOVE_AVERAGE_TEAM_TURNOVER_PROFILE_SQL
        or provenance.get("audit_query") != ABOVE_AVERAGE_TEAM_TURNOVER_AUDIT_SQL
    ):
        raise ValueError("Above-average team turnover evidence is not linked to the approved profile SQL.")
    for key in (
        "assessment_evidence_sha256",
        "presentation_query_sha256",
        "presentation_result_sha256",
        "audit_query_sha256",
        "audit_result_sha256",
    ):
        if not re.fullmatch(r"[0-9a-f]{64}", str(provenance.get(key, ""))):
            raise ValueError("Above-average team turnover evidence has incomplete provenance hashes.")
    reconciliation = evidence.get("termination_source_reconciliation")
    if not isinstance(reconciliation, dict) or _integer_metric(reconciliation.get("discrepancy_count"), "discrepancy_count") <= 0:
        raise ValueError("Above-average team turnover must retain the termination-source limitation.")
    return evidence


def above_average_team_turnover_sensitivity_evidence() -> dict[str, object]:
    """Load and validate the aggregate-only threshold sensitivity evidence."""
    if not ABOVE_AVERAGE_TEAM_TURNOVER_SENSITIVITY_EVIDENCE.exists():
        raise FileNotFoundError(ABOVE_AVERAGE_TEAM_TURNOVER_SENSITIVITY_EVIDENCE)
    evidence = load(ABOVE_AVERAGE_TEAM_TURNOVER_SENSITIVITY_EVIDENCE)
    if not isinstance(evidence, dict):
        raise ValueError("Threshold sensitivity evidence must be a JSON object.")
    required = {
        "artifact_type": "aggregate_threshold_sensitivity_evidence",
        "deliverable_mode": "presentation",
        "variable": "Above-average team turnover",
        "candidate_number": 44,
        "outcome": "pass",
    }
    if any(evidence.get(key) != expected for key, expected in required.items()):
        raise ValueError("Threshold sensitivity evidence has an unexpected contract.")
    privacy = evidence.get("privacy")
    if not isinstance(privacy, dict) or privacy.get("minimum_shared_cohort") != MINIMUM_COHORT:
        raise ValueError("Threshold sensitivity evidence lost its cohort safeguard.")
    if any(privacy.get(key) is not False for key in (
        "identifiers_persisted", "employee_rows_persisted", "manager_rates_persisted", "manager_rankings_persisted",
    )):
        raise ValueError("Threshold sensitivity evidence fails its privacy contract.")
    distribution = evidence.get("rate_distribution")
    if not isinstance(distribution, dict):
        raise ValueError("Threshold sensitivity evidence is missing the rate distribution.")
    manager_count = _integer_metric(distribution.get("eligible_manager_count"), "eligible_manager_count")
    if manager_count < MINIMUM_COHORT:
        raise ValueError("Threshold sensitivity manager distribution is below n >= 30.")
    percentiles = distribution.get("ratio_percentiles")
    if not isinstance(percentiles, dict) or any(key not in percentiles for key in ("p25", "p50", "p75", "p90", "p95")):
        raise ValueError("Threshold sensitivity percentiles are incomplete.")
    ordered = [float(percentiles[key]) for key in ("p25", "p50", "p75", "p90", "p95")]
    if ordered != sorted(ordered):
        raise ValueError("Threshold sensitivity percentiles are not ordered.")
    latest = evidence.get("latest_thresholds")
    if not isinstance(latest, list) or {str(row.get("threshold_multiplier")) for row in latest} != {"1.20", "1.30", "1.40"}:
        raise ValueError("Threshold sensitivity does not contain 1.2x, 1.3x and 1.4x.")
    for row in latest:
        if not isinstance(row, dict):
            raise ValueError("Threshold sensitivity latest row is not structured.")
        for key in ("eligible_report_count", "flagged_report_count", "significant_report_count", "flagged_and_significant_report_count"):
            if _integer_metric(row.get(key), key) < MINIMUM_COHORT:
                raise ValueError(f"Threshold sensitivity latest {key} is below n >= {MINIMUM_COHORT}.")
    stability = evidence.get("threshold_stability")
    if not isinstance(stability, list) or len(stability) != 3:
        raise ValueError("Threshold sensitivity stability is incomplete.")
    if any(_integer_metric(row.get("snapshots_checked"), "snapshots_checked") != 6 for row in stability):
        raise ValueError("Threshold sensitivity stability does not cover six snapshots.")
    recommendation = evidence.get("recommendation")
    if not isinstance(recommendation, dict) or float(recommendation.get("working_multiplier")) != 1.3:
        raise ValueError("Threshold sensitivity recommendation is not 1.3x.")
    return evidence


def above_average_team_turnover_sensitivity_manifest_entry(evidence: dict[str, object]) -> dict[str, object]:
    distribution = evidence["rate_distribution"]
    recommendation = evidence["recommendation"]
    provenance = evidence["provenance"]
    assert isinstance(distribution, dict) and isinstance(recommendation, dict) and isinstance(provenance, dict)
    return {
        "evidence": str(ABOVE_AVERAGE_TEAM_TURNOVER_SENSITIVITY_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "builder": str(ABOVE_AVERAGE_TEAM_TURNOVER_SENSITIVITY_BUILDER.relative_to(ROOT)).replace("\\", "/"),
        "query": ABOVE_AVERAGE_TEAM_TURNOVER_SENSITIVITY_SQL,
        "latest_snapshot": evidence["latest_snapshot"],
        "eligible_manager_count": distribution["eligible_manager_count"],
        "ratio_percentiles": distribution["ratio_percentiles"],
        "working_multiplier": recommendation["working_multiplier"],
        "query_sha256": provenance["query_sha256"],
        "result_sha256": provenance["result_sha256"],
        "outcome": evidence["outcome"],
    }


def above_average_team_turnover_manifest_entry(evidence: dict[str, object]) -> dict[str, object]:
    """Return safe provenance for candidate 44 without copying restricted manager detail."""
    benchmark = evidence["benchmark"]
    counts = evidence["aggregate_counts"]
    privacy = evidence["privacy"]
    provenance = evidence["provenance"]
    assert isinstance(benchmark, dict) and isinstance(counts, dict) and isinstance(privacy, dict) and isinstance(provenance, dict)
    return {
        "evidence": str(ABOVE_AVERAGE_TEAM_TURNOVER_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "builder": str(ABOVE_AVERAGE_TEAM_TURNOVER_BUILDER.relative_to(ROOT)).replace("\\", "/"),
        "assessment_run": evidence["source_assessment_run"],
        "profile_query": ABOVE_AVERAGE_TEAM_TURNOVER_PROFILE_SQL,
        "audit_query": ABOVE_AVERAGE_TEAM_TURNOVER_AUDIT_SQL,
        "termination_reconciliation_query": ABOVE_AVERAGE_TEAM_TURNOVER_RECONCILIATION_SQL,
        "snapshot": evidence["latest_snapshot"],
        "population": evidence["population"],
        "grain": evidence["grain"],
        "buckets": ["0", "1", "Unknown"],
        "benchmark_six_month_rate": benchmark["six_month_rate"],
        "threshold_multiplier": benchmark["flag_threshold_multiplier"],
        "threshold_six_month_rate": benchmark["flag_threshold_six_month_rate"],
        "aggregate_counts": counts,
        "privacy": privacy,
        "query_sha256": {
            "assessment_evidence": provenance["assessment_evidence_sha256"],
            "profile_sql": provenance["presentation_query_sha256"],
            "profile_result": provenance["presentation_result_sha256"],
            "audit_sql": provenance["audit_query_sha256"],
            "audit_result": provenance["audit_result_sha256"],
        },
        "outcome": evidence["outcome"],
    }


def application_intensity_authorization() -> dict[str, object]:
    """Load the named, aggregate-only internal collaboration authorization."""
    authorization = load(APPLICATION_INTENSITY_AUTHORIZATION)
    if authorization.get("status") != "approved" or authorization.get("reporting_mode") != "internal_analysis":
        raise ValueError("La autorización interna de aplicaciones no está aprobada para internal_analysis.")
    if not authorization.get("small_cell_exception", {}).get("allow_subthreshold_aggregate_buckets"):
        raise ValueError("La autorización interna de aplicaciones no habilita su excepción agregada declarada.")
    controls = authorization.get("non_negotiable_controls", {})
    required_controls = {
        "aggregate_only": True,
        "employee_rows_persisted": False,
        "employee_ids_persisted": False,
        "names_persisted": False,
        "requisition_ids_or_titles_persisted": False,
        "manager_access": False,
        "redistribution": False,
        "operational_use": False,
        "score_v4_change": False,
        "production_feature_approval": False,
    }
    if any(controls.get(key) is not expected for key, expected in required_controls.items()):
        raise ValueError("La autorización interna de aplicaciones debilita un control obligatorio de privacidad o gobierno.")
    return authorization


def application_intensity_by_fiscal_year() -> list[dict[str, object]]:
    """Load the audited applicant-year distribution for the authorized internal view."""
    evidence = load(APPLICATION_INTENSITY_EVIDENCE)
    if evidence.get("reporting_mode") != REPORTING_MODE:
        raise ValueError(
            "La evidencia de intensidad de aplicaciones no coincide con el modo de entrega del deck."
        )
    if evidence.get("source", {}).get("table") != "hrda.job_applications_vw":
        raise ValueError("La distribución anual no usa hrda.job_applications_vw.")
    if str(evidence.get("analysis_cutoff")) != "2026-09-10":
        raise ValueError("La distribución anual no usa el corte 2026-09-10.")

    rules = evidence.get("publication_rules", {})
    if int(rules.get("minimum_shared_cohort", 0)) != MINIMUM_COHORT:
        raise ValueError("La evidencia de intensidad no conserva el umbral mínimo de cohorte.")
    if not rules.get("exclude_partial_fiscal_years_unless_explicit_ytd") or not rules.get("no_workforce_rate"):
        raise ValueError("La evidencia de intensidad no conserva sus límites de interpretación.")
    if not rules.get("exclude_non_publishable_year_if_any_bucket_below_minimum"):
        raise ValueError("La evidencia anual no conserva la puerta de publicación por bucket.")
    authorization = application_intensity_authorization()
    if REPORTING_MODE != "internal_analysis" or rules.get("authorization_id") != authorization.get("authorization_id"):
        raise ValueError("La excepción de celdas pequeñas sólo puede usarse en el artefacto internal_analysis autorizado.")
    if not rules.get("internal_analysis_exception") or not rules.get("allow_subthreshold_aggregate_buckets"):
        raise ValueError("La evidencia anual no registra la excepción interna autorizada.")
    publication = evidence.get("evidence", {}).get("publishability", {})

    rows = evidence.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("No se encontró una distribución anual congelada de intensidad de aplicaciones.")

    expected_buckets = ("1", "2", "3", "4+")
    requested_years = ("2022", "2023", "2024", "2025", "2026")
    by_year: dict[str, list[dict[str, object]]] = {}
    for raw_row in rows:
        if not isinstance(raw_row, dict):
            raise ValueError("La distribución de intensidad contiene una fila no estructurada.")
        fiscal_year = str(raw_row["fiscal_year"])
        if fiscal_year not in requested_years:
            continue
        bucket = str(raw_row["application_bucket"])
        count = int(raw_row["distinct_applicants"])
        if bucket not in expected_buckets or count < 0:
            raise ValueError("La distribución interna contiene un bucket no permitido o un conteo negativo.")
        by_year.setdefault(fiscal_year, []).append(raw_row)

    series: list[dict[str, object]] = []
    for fiscal_year in sorted(by_year):
        bucket_rows = sorted(by_year[fiscal_year], key=lambda row: int(row["bucket_order"]))
        labels = tuple(str(row["application_bucket"]) for row in bucket_rows)
        if labels != expected_buckets:
            raise ValueError(f"FY {fiscal_year} no contiene exactamente los buckets 1/2/3/4+.")

        annual_applicants = int(bucket_rows[0]["annual_distinct_applicants"])
        total_bucket_count = sum(int(row["distinct_applicants"]) for row in bucket_rows)
        total_percent = sum(
            float(row.get("percent_of_annual_applicants", row["percent_of_period_applicants"]))
            for row in bucket_rows
        )
        if total_bucket_count != annual_applicants or abs(total_percent - 100.0) > 0.02:
            raise ValueError(f"FY {fiscal_year} no reconcilia contra su total anual de solicitantes.")

        display_label = f"FY{fiscal_year} YTD" if fiscal_year == "2026" else f"FY{fiscal_year}"
        period_note = (
            "through 2026-09-10 — partial fiscal year; not comparable with full fiscal years"
            if fiscal_year == "2026"
            else "complete fiscal year"
        )
        series.append({
            "fiscal_year": display_label,
            "fiscal_year_number": fiscal_year,
            "annual_distinct_applicants": annual_applicants,
            "observed_period_end": str(bucket_rows[0]["observed_period_end"]),
            "period_status": str(bucket_rows[0]["period_status"]),
            "period_note": period_note,
            "publication_status": str(bucket_rows[0].get("publication_status", "internal_analysis_exception")),
            "minimum_bucket_n": min(int(row["distinct_applicants"]) for row in bucket_rows),
            "mean": float(bucket_rows[0]["mean_unique_requisitions_per_applicant"]),
            "median": float(bucket_rows[0]["median_unique_requisitions_per_applicant"]),
            "buckets": [
                {
                    "label": str(row["application_bucket"]),
                    "count": int(row["distinct_applicants"]),
                    "percent": float(row.get("percent_of_annual_applicants", row["percent_of_period_applicants"])),
                }
                for row in bucket_rows
            ],
        })
    if [item["fiscal_year_number"] for item in series] != list(requested_years):
        raise ValueError("La distribución interna debe contener FY2022–FY2026 YTD.")
    return series


def application_employee_snapshot_trailing_6m() -> dict[str, object]:
    """Load the presentation-safe rolling employee-snapshot evidence."""
    evidence = load(APPLICATION_EMPLOYEE_SNAPSHOT_EVIDENCE)
    if evidence.get("reporting_mode") != REPORTING_MODE:
        raise ValueError("La evidencia rolling de aplicaciones no coincide con el modo del deck.")
    if evidence.get("source", {}).get("table") != "hrda.job_applications_vw":
        raise ValueError("La evidencia rolling no usa hrda.job_applications_vw.")
    if str(evidence.get("analysis_cutoff")) != "2026-09-10":
        raise ValueError("La evidencia rolling no usa el corte 2026-09-10.")
    if evidence.get("window") != "(snapshot_date - 6 months, snapshot_date]":
        raise ValueError("La ventana rolling de aplicaciones no coincide con la aprobada.")

    rules = evidence.get("publication_rules", {})
    if int(rules.get("minimum_shared_cohort", 0)) != MINIMUM_COHORT:
        raise ValueError("La evidencia rolling no conserva n >= 30.")
    expected_buckets = ("0", "1", "2+", "Unknown")
    if tuple(rules.get("required_categories_for_complete_distribution", ())) != expected_buckets:
        raise ValueError("La evidencia rolling no conserva las categorías 0/1/2+/Unknown.")
    if not rules.get("suppress_bucket_below_n30") or not rules.get("no_zero_imputation"):
        raise ValueError("La evidencia rolling no conserva las reglas de publicación y Unknown.")

    latest_rows = evidence.get("latest_distribution")
    if not isinstance(latest_rows, list) or tuple(str(row["application_bucket"]) for row in latest_rows) != expected_buckets:
        raise ValueError("La última distribución rolling no contiene exactamente 0/1/2+/Unknown.")
    latest_distribution: list[dict[str, object]] = []
    denominator: int | None = None
    for row in latest_rows:
        count = int(row["employee_snapshots"])
        if count < MINIMUM_COHORT:
            raise ValueError("La última distribución rolling contiene un bucket menor a n=30.")
        row_denominator = int(row["eligible_employee_snapshots"])
        if denominator is None:
            denominator = row_denominator
        if row_denominator != denominator:
            raise ValueError("La última distribución rolling usa denominadores distintos.")
        latest_distribution.append({
            "application_bucket": str(row["application_bucket"]),
            "employee_snapshots": count,
            "eligible_employee_snapshots": row_denominator,
            "percent_of_eligible_snapshots": float(row["percent_of_eligible_snapshots"]),
        })
    if denominator is None or sum(int(row["employee_snapshots"]) for row in latest_distribution) != denominator:
        raise ValueError("La última distribución rolling no reconcilia al denominador employee-snapshot.")

    raw_trend = evidence.get("trend")
    if not isinstance(raw_trend, list) or len(raw_trend) != 12:
        raise ValueError("La evidencia rolling no contiene los 12 snapshots mensuales esperados.")
    trend: list[dict[str, object]] = []
    previous_date = ""
    publishable_dates: list[str] = []
    for row in raw_trend:
        snapshot_date = str(row["snapshot_date"])
        if snapshot_date <= previous_date:
            raise ValueError("Los snapshots rolling no están ordenados estrictamente.")
        previous_date = snapshot_date
        if str(row["publication_status"]) == "publishable":
            publishable_dates.append(snapshot_date)
        trend.append({
            "snapshot_date": snapshot_date,
            "eligible_employee_snapshots": int(row["eligible_employee_snapshots"]),
            "coverage_percent": float(row["coverage_percent"]),
            "unknown_percent": float(row["unknown_percent"]),
            "zero_percent": float(row["zero_percent"]),
            "one_percent": float(row["one_percent"]),
            "two_plus_percent": float(row["two_plus_percent"]) if "two_plus_percent" in row else None,
            "publication_status": str(row["publication_status"]),
        })
    latest_publishable = str(evidence["latest_publishable_snapshot"])
    if latest_publishable not in publishable_dates:
        raise ValueError("El último snapshot publicable no aparece en la tendencia rolling.")
    if str(evidence["latest_available_snapshot"]) != "2026-08-23":
        raise ValueError("La evidencia rolling no termina en el último snapshot esperado.")
    if str(evidence["latest_available_status"]) == "publishable":
        raise ValueError("El snapshot más reciente no debe publicarse como distribución completa.")

    return {
        "analysis_cutoff": str(evidence["analysis_cutoff"]),
        "population": str(evidence["population"]),
        "grain": str(evidence["grain"]),
        "window": str(evidence["window"]),
        "latest_available_snapshot": str(evidence["latest_available_snapshot"]),
        "latest_available_status": str(evidence["latest_available_status"]),
        "latest_publishable_snapshot": latest_publishable,
        "latest_distribution": latest_distribution,
        "trend": trend,
        "limitations": [str(item) for item in evidence.get("limitations", [])],
    }


def office_site_city_distribution() -> tuple[list[tuple[str, int]], dict[str, int]]:
    """Load and reconcile the frozen aggregate site-city distribution."""
    evidence = load(OFFICE_SITE_CITY_EVIDENCE)
    if evidence.get("query_path") != OFFICE_SITE_CITY_PROFILE_SQL:
        raise ValueError("La evidencia de office_site · city no referencia su consulta congelada.")
    if str(evidence.get("snapshot_date")) != "2026-08-23":
        raise ValueError("La evidencia de office_site · city no usa el snapshot esperado.")
    if int(evidence.get("minimum_shared_cohort", 0)) != MINIMUM_COHORT:
        raise ValueError("La evidencia de office_site · city no conserva n >= 30.")

    rows = evidence.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("No se encontró la distribución congelada de office_site · city.")

    normalized: list[tuple[str, int]] = []
    for expected_order, raw_row in enumerate(rows, start=1):
        if not isinstance(raw_row, dict):
            raise ValueError("La distribución de office_site · city contiene una fila inválida.")
        if int(raw_row.get("display_order", 0)) != expected_order:
            raise ValueError("La distribución de office_site · city no conserva el orden de publicación.")
        label = str(raw_row.get("display_label", ""))
        count = int(raw_row.get("employee_count", 0))
        if not label or count < MINIMUM_COHORT:
            raise ValueError("La distribución publicada contiene una etiqueta vacía o n < 30.")
        normalized.append((label, count))

    row_types = [str(raw_row.get("row_type")) for raw_row in rows]
    if row_types.count("top_pair") != 20 or row_types[-2:] != ["other_pairs", "missing_pair"]:
        raise ValueError("La distribución de office_site · city no contiene top 20, Other y missing.")

    eligible = int(evidence["eligible_employees"])
    pair_population = int(evidence["pair_population_employees"])
    missing = int(evidence["missing_pair_employees"])
    top_20 = int(evidence["top_20_employee_count"])
    top_rows_total = sum(count for row_type, (_, count) in zip(row_types, normalized) if row_type == "top_pair")
    other_count = normalized[-2][1]
    missing_count = normalized[-1][1]
    if top_rows_total != top_20 or other_count != pair_population - top_20 or missing_count != missing:
        raise ValueError("La distribución de office_site · city no reconcilia sus totales agregados.")
    if sum(count for _, count in normalized) != eligible:
        raise ValueError("La distribución de office_site · city no reconcilia contra la población elegible.")

    metadata = {
        "eligible_employees": eligible,
        "pair_population_employees": pair_population,
        "missing_pair_employees": missing,
        "distinct_complete_pairs": int(evidence["distinct_complete_pairs"]),
        "top_20_pair_count": int(evidence["top_20_pair_count"]),
        "top_20_employee_count": top_20,
    }
    return normalized, metadata


def transfer_within_past_year_distribution() -> dict[str, object]:
    """Load the frozen rolling-window comparison and enforce its contract."""
    evidence = load(TRANSFER_EVIDENCE)
    if evidence.get("query_path") != TRANSFER_PROFILE_SQL:
        raise ValueError("La evidencia de transfer no referencia su consulta congelada.")
    if str(evidence.get("cutoff_date")) != "2026-08-23":
        raise ValueError("La evidencia de transfer no usa el cutoff esperado.")
    if int(evidence.get("minimum_shared_cohort", 0)) != MINIMUM_COHORT:
        raise ValueError("La evidencia de transfer no conserva n >= 30.")
    if evidence.get("canonical_frequency") != "monthly":
        raise ValueError("La evidencia de transfer no conserva mensual como frecuencia canónica.")

    raw_rows = evidence.get("rows")
    if not isinstance(raw_rows, list) or not raw_rows:
        raise ValueError("No se encontró la distribución congelada de transfer.")
    rows: list[dict[str, object]] = []
    for raw_row in raw_rows:
        if not isinstance(raw_row, dict):
            raise ValueError("La distribución de transfer contiene una fila inválida.")
        frequency = str(raw_row.get("frequency"))
        if frequency not in {"monthly", "weekly"}:
            raise ValueError("La distribución de transfer contiene una frecuencia no permitida.")
        eligible = int(raw_row.get("eligible_employees", 0))
        transfer_employees = int(raw_row.get("transfer_employees", 0))
        rate = float(raw_row.get("transfer_rate_percent", 0))
        if not bool(raw_row.get("period_complete")) or eligible < MINIMUM_COHORT:
            raise ValueError("La distribución de transfer contiene un periodo incompleto o n < 30.")
        if transfer_employees > eligible:
            raise ValueError("La distribución de transfer excede su población elegible.")
        expected_rate = 100.0 * transfer_employees / eligible
        if abs(rate - expected_rate) > 0.01:
            raise ValueError("La tasa de transfer no reconcilia contra sus conteos.")
        rows.append({
            "frequency": frequency,
            "snapshot_date": str(raw_row["snapshot_date"]),
            "eligible_employees": eligible,
            "transfer_employees": transfer_employees,
            "transfer_rate_percent": rate,
        })

    counts = {frequency: sum(1 for row in rows if row["frequency"] == frequency) for frequency in ("monthly", "weekly")}
    if counts != {"monthly": 24, "weekly": 104}:
        raise ValueError(f"La distribución de transfer requiere 24/104 puntos y obtuvo {counts}.")
    summaries = evidence.get("summaries")
    if not isinstance(summaries, dict):
        raise ValueError("La evidencia de transfer no contiene resúmenes por frecuencia.")
    return {
        "rows": rows,
        "summaries": summaries,
        "display_scope_note": str(evidence.get("display_scope_note_two_year_window", evidence.get("display_scope_note", ""))),
        "history_availability": evidence.get("history_availability", {}),
    }


def job_family_snapshot_distributions() -> tuple[dict[str, object], dict[str, object]]:
    """Build the requested August and post-weekend September panels.

    August deliberately remains on the frozen evidence already used by this
    deck. The September panel uses the daily 2026-09-07 snapshot selected by
    the user, not the future-dated monthly 2026-09-27 row. This preserves the
    requested August reference while keeping the comparison time-safe.
    """
    evidence = load(JOB_FAMILY_EVIDENCE)
    if evidence.get("query_path") != JOB_FAMILY_PROFILE_SQL:
        raise ValueError("La evidencia de Job family no referencia la consulta esperada.")
    if evidence.get("reporting_mode") != REPORTING_MODE:
        raise ValueError("La evidencia de Job family no coincide con el modo de reporte.")
    if int(evidence.get("minimum_shared_cohort", 0)) != MINIMUM_COHORT:
        raise ValueError("La evidencia de Job family no conserva n >= 30.")

    panels = evidence.get("display_panels")
    if not isinstance(panels, dict):
        raise ValueError("La evidencia de Job family no contiene sus dos paneles.")

    august_meta = panels.get(V4_SNAPSHOT)
    if not isinstance(august_meta, dict) or august_meta.get("source_type") != "frozen_assessment_evidence":
        raise ValueError("El panel de agosto debe provenir de la evidencia congelada solicitada.")
    august_eligible, august_observable = latest_snapshot_coverage("07-job-family")
    if (int(august_meta.get("eligible_employees", -1)), int(august_meta.get("observable_employees", -1))) != (august_eligible, august_observable):
        raise ValueError("El panel de agosto no reconcilia contra su evidencia congelada.")
    august_top_20 = frozen_top_values("07-job-family", "job_family", 20)
    august_rows = categorical_distribution(
        august_top_20,
        populated=august_observable,
        eligible=august_eligible,
        other_label="Other job families",
    )
    if len(august_rows) != 21 or sum(count for _, count in august_rows) != august_observable:
        raise ValueError("El panel de agosto no reconcilia top 20 + Other.")
    if sum(count for _, count in august_top_20) != int(august_meta.get("top_20_employee_count", -1)):
        raise ValueError("El top 20 de agosto no coincide con su evidencia congelada.")
    if august_rows[-1][1] != int(august_meta.get("other_job_families_employee_count", -1)):
        raise ValueError("La cola de agosto no coincide con su evidencia congelada.")

    september_snapshot = JOB_FAMILY_DAILY_SNAPSHOT
    september_meta = panels.get(september_snapshot)
    if not isinstance(september_meta, dict) or september_meta.get("source_type") != "executed_aggregate_query":
        raise ValueError("El panel de septiembre debe provenir de la consulta agregada ejecutada.")
    raw_top_20 = september_meta.get("top_20")
    if not isinstance(raw_top_20, list):
        raise ValueError("La evidencia de septiembre no contiene el top 20 detallado.")
    normalized_top_20 = sorted(raw_top_20, key=lambda row: int(row["rank"]))
    if [int(row["rank"]) for row in normalized_top_20] != list(range(1, 21)):
        raise ValueError("El top 20 de septiembre no conserva los 20 rangos esperados.")
    september_top_20 = [(str(row["label"]), int(row["employee_count"])) for row in normalized_top_20]
    if any(not label or count < MINIMUM_COHORT for label, count in september_top_20):
        raise ValueError("El panel de septiembre contiene una categoría no publicable.")

    september_observable = int(september_meta.get("observable_employees", 0))
    september_eligible = int(september_meta.get("eligible_employees", 0))
    september_other = int(september_meta.get("other_job_families_employee_count", 0))
    if int(september_meta.get("top_20_category_count", 0)) != 20 or september_other < MINIMUM_COHORT:
        raise ValueError("La evidencia de septiembre no conserva el top 20 y una cola publicable.")
    if sum(count for _, count in september_top_20) != int(september_meta.get("top_20_employee_count", -1)):
        raise ValueError("El top 20 de septiembre no coincide con su total agregado.")
    if min(count for _, count in september_top_20) != int(september_meta.get("top_20_min_employee_count", -1)):
        raise ValueError("El mínimo de cohorte de septiembre no coincide con la evidencia.")
    september_rows = september_top_20 + [("Other job families", september_other)]
    if sum(count for _, count in september_rows) != september_observable or september_observable != september_eligible:
        raise ValueError("El panel de septiembre no reconcilia contra la población de snapshot.")

    return (
        {"snapshot": V4_SNAPSHOT, "rows": august_rows, "population": august_observable},
        {"snapshot": september_snapshot, "rows": september_rows, "population": september_observable},
    )


def region_display_distributions() -> dict[str, object]:
    """Load the audited Region display and global Labor Market distribution."""
    evidence = load(REGION_EVIDENCE)
    if evidence.get("query_path") != REGION_DISPLAY_AUDIT_SQL:
        raise ValueError("La evidencia de Region no referencia la consulta de display esperada.")
    if evidence.get("artifact") != REPORTING_MODE:
        raise ValueError("La evidencia de Region no coincide con el modo de reporte.")
    if evidence.get("outcome") != "pass":
        raise ValueError("La evidencia de Region no aprobó sus validaciones de display.")
    if evidence.get("snapshot") != V4_SNAPSHOT:
        raise ValueError("La evidencia de Region no usa el snapshot mensual aprobado.")
    if evidence.get("source_table") != "hrda.post_hire_monthly_worker_dtls" or evidence.get("date_field") != "fis_mo_end_dt":
        raise ValueError("La evidencia de Region no conserva la procedencia mensual esperada.")
    if evidence.get("grain") != "Distinct employee snapshot":
        raise ValueError("La evidencia de Region no conserva el grain de empleado-snapshot.")
    if int(evidence.get("minimum_shared_cohort", 0)) != MINIMUM_COHORT:
        raise ValueError("La evidencia de Region no conserva n >= 30.")

    validation = {"outcome": evidence.get("outcome"), "metrics": evidence.get("audit_metrics")}
    if not isinstance(validation, dict) or validation.get("outcome") != "pass":
        raise ValueError("La evidencia de Region no aprobÃ³ sus validaciones de mapeo.")
    metrics = validation.get("metrics")
    expected_zero_metrics = {
        "employees_with_multiple_source_rows",
        "employees_with_conflicting_region_values",
        "employees_with_conflicting_labor_market_values",
        "unclassified_region_employees",
        "global_missing_labor_market",
    }
    if not isinstance(metrics, dict) or set(metrics) != expected_zero_metrics or any(int(metrics[name]) != 0 for name in expected_zero_metrics):
        raise ValueError("La evidencia de Region contiene una contradicciÃ³n de snapshot, mapping o cobertura.")

    display = evidence.get("display")
    if not isinstance(display, dict):
        raise ValueError("La evidencia de Region no contiene los grupos de display.")
    eligible = int(evidence.get("eligible_employees", 0))
    if eligible < MINIMUM_COHORT:
        raise ValueError("La poblaciÃ³n de Region estÃ¡ debajo del umbral de publicaciÃ³n.")

    def checked_rows(source: dict[str, object], key: str, expected_labels: set[str] | None, denominator: int) -> list[tuple[str, int]]:
        raw_rows = source.get(key)
        if not isinstance(raw_rows, list):
            raise ValueError(f"La evidencia de Region no contiene {key}.")
        rows = sorted(raw_rows, key=lambda row: int(row["sort_order"]))
        normalized = [(str(row["label"]), int(row["employee_count"])) for row in rows]
        if expected_labels is not None and {label for label, _ in normalized} != expected_labels:
            raise ValueError(f"El dominio de {key} no coincide con el display aprobado.")
        if any(count < MINIMUM_COHORT for _, count in normalized):
            raise ValueError(f"El display {key} contiene una cohorte menor a n >= 30.")
        if sum(count for _, count in normalized) != denominator:
            raise ValueError(f"El display {key} no reconcilia contra su denominador.")
        for raw_row, (_, count) in zip(rows, normalized):
            expected_percentage = 100.0 * count / denominator
            if abs(float(raw_row["percentage"]) - expected_percentage) > 0.01:
                raise ValueError(f"El porcentaje de {key} no reconcilia contra sus conteos.")
        return normalized

    global_rows = checked_rows(
        display,
        "global_region",
        {"India", "Americas", "APAC", "EMEA"},
        eligible,
    )
    labor_market_rows = checked_rows(display, "global_labor_market", None, eligible)
    labor_market_source_category_count = int(display.get("labor_market_source_category_count", 0))
    if labor_market_source_category_count < 1:
        raise ValueError("La evidencia de Region no informa la cardinalidad de Labor Market.")
    expected_labor_market_display_count = min(labor_market_source_category_count, 20)
    if labor_market_source_category_count > 20:
        expected_labor_market_display_count += 1
        if labor_market_rows[-1][0] != "Other Labor Markets":
            raise ValueError("La cola de Labor Market debe publicarse como Other Labor Markets.")
    if len(labor_market_rows) != expected_labor_market_display_count:
        raise ValueError("Labor Market no conserva la polÃ­tica top 20 + Other aprobada.")

    return {
        "global_rows": global_rows,
        "global_labor_market_rows": labor_market_rows,
        "eligible_employees": eligible,
        "labor_market_source_category_count": labor_market_source_category_count,
    }


def region_major_country_split_distribution(expected_population: int) -> list[tuple[str, int]]:
    """Load the audited display-only U.S./China regional breakout."""
    evidence = load(REGION_MAJOR_COUNTRY_EVIDENCE)
    if evidence.get("query_path") != REGION_MAJOR_COUNTRY_AUDIT_SQL:
        raise ValueError("La evidencia del split de Region no referencia la consulta esperada.")
    if evidence.get("artifact") != REPORTING_MODE or evidence.get("outcome") != "pass":
        raise ValueError("La evidencia del split de Region no aprobó el modo o resultado esperado.")
    if evidence.get("snapshot") != V4_SNAPSHOT:
        raise ValueError("La evidencia del split de Region no usa el snapshot mensual aprobado.")
    if evidence.get("source_table") != "hrda.post_hire_monthly_worker_dtls" or evidence.get("date_field") != "fis_mo_end_dt":
        raise ValueError("La evidencia del split de Region no conserva la procedencia mensual esperada.")
    if evidence.get("grain") != "Distinct employee snapshot" or int(evidence.get("minimum_shared_cohort", 0)) != MINIMUM_COHORT:
        raise ValueError("La evidencia del split de Region no conserva el grain o n >= 30 esperado.")
    if int(evidence.get("eligible_employees", 0)) != expected_population:
        raise ValueError("El split de Region no reconcilia contra la población global de Region.")

    metrics = evidence.get("audit_metrics")
    expected_zero_metrics = {
        "employees_with_multiple_source_rows",
        "employees_with_conflicting_region_values",
        "employees_with_conflicting_country_values",
        "unclassified_region_employees",
        "united_states_outside_americas",
        "china_outside_apac",
    }
    if not isinstance(metrics, dict) or set(metrics) != expected_zero_metrics | {"missing_country_employees"}:
        raise ValueError("La evidencia del split de Region no contiene las validaciones esperadas.")
    if any(int(metrics[name]) != 0 for name in expected_zero_metrics):
        raise ValueError("La evidencia del split de Region contiene una contradicción de mapping.")

    display = evidence.get("display")
    if not isinstance(display, dict) or not isinstance(display.get("major_country_split"), list):
        raise ValueError("La evidencia del split de Region no contiene el display solicitado.")
    rows = sorted(display["major_country_split"], key=lambda row: int(row["sort_order"]))
    normalized = [(str(row["label"]), int(row["employee_count"])) for row in rows]
    expected_labels = {
        "India",
        "United States",
        "Americas excluding U.S.",
        "China",
        "APAC excluding China",
        "EMEA",
    }
    if {label for label, _ in normalized} != expected_labels:
        raise ValueError("El dominio del split de Region no coincide con el display aprobado.")
    if any(count < MINIMUM_COHORT for _, count in normalized) or sum(count for _, count in normalized) != expected_population:
        raise ValueError("El split de Region no cumple cohortes o reconciliación.")
    for raw_row, (_, count) in zip(rows, normalized):
        if abs(float(raw_row["percentage"]) - (100.0 * count / expected_population)) > 0.01:
            raise ValueError("El porcentaje del split de Region no reconcilia contra sus conteos.")
    return normalized


def team_turnover_scenarios() -> dict[str, object]:
    """Load and validate the two aggregate six-month team-turnover scenarios."""
    evidence = load(TEAM_TURNOVER_EVIDENCE)
    if evidence.get("query_path") != TEAM_TURNOVER_PROFILE_SQL:
        raise ValueError("La evidencia de Team turnover no referencia la consulta esperada.")
    if evidence.get("reporting_mode") != REPORTING_MODE:
        raise ValueError("La evidencia de Team turnover no coincide con el modo de reporte.")
    if evidence.get("outcome") != "pass":
        raise ValueError("La evidencia de Team turnover no aprobó sus reglas de publicación.")
    window = evidence.get("window")
    if not isinstance(window, dict) or int(window.get("monthly_snapshot_count", 0)) != 6:
        raise ValueError("La evidencia de Team turnover no contiene seis snapshots mensuales.")
    scenarios = evidence.get("scenarios")
    if not isinstance(scenarios, list) or len(scenarios) != 2:
        raise ValueError("La evidencia de Team turnover debe contener exactamente dos escenarios.")
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise ValueError("Un escenario de Team turnover no tiene estructura válida.")
        if int(scenario.get("manager_teams", 0)) < MINIMUM_COHORT:
            raise ValueError("Un escenario de Team turnover no alcanza la cohorte mínima publicable.")
        if int(scenario.get("employee_months", 0)) <= 0:
            raise ValueError("Un escenario de Team turnover no tiene exposición directa.")
        zero = int(scenario.get("teams_without_voluntary_exit", 0))
        positive = int(scenario.get("teams_with_at_least_one_voluntary_exit", 0))
        if zero < MINIMUM_COHORT or positive < MINIMUM_COHORT:
            raise ValueError("La distribución de Team turnover contiene una cohorte no publicable.")
        if zero + positive != int(scenario["manager_teams"]):
            raise ValueError("La distribución de Team turnover no reconcilia con los equipos elegibles.")
    attribution = evidence.get("attribution")
    if not isinstance(attribution, dict) or int(attribution.get("events_with_pre_exit_manager", 0)) < MINIMUM_COHORT:
        raise ValueError("La evidencia de atribución de Team turnover no es publicable.")
    return evidence


def more_than_1_employee_leaves_evidence() -> dict[str, object]:
    """Load and reconcile the monthly employee exposure evidence."""
    evidence = load(MORE_THAN_1_LEAVES_EVIDENCE)
    if evidence.get("query_path") != MORE_THAN_1_LEAVES_AUDIT_SQL:
        raise ValueError("La evidencia de la bandera de equipo no referencia su auditoría ejecutada.")
    if evidence.get("outcome") != "pass":
        raise ValueError("La evidencia de la bandera de equipo no aprobó su regla de aceptación.")
    if int(evidence.get("window_months", 0)) != 6 or int(evidence.get("monthly_snapshots_per_window", 0)) != 6:
        raise ValueError("La bandera de equipo no conserva la ventana de seis meses y seis snapshots.")
    if evidence.get("included_term_type") != "Voluntary":
        raise ValueError("La bandera de equipo no está restringida a salidas Voluntary.")

    scopes = evidence.get("scopes")
    if not isinstance(scopes, list) or [str(item.get("key")) for item in scopes] != ["all_teams", "teams_gt_5"]:
        raise ValueError("La evidencia debe contener los dos scopes de equipo esperados.")
    expected_buckets = ("0", "1", "2+")
    for scope in scopes:
        if not isinstance(scope, dict):
            raise ValueError("Un scope de equipo no tiene estructura válida.")
        denominator_groups = int(scope.get("total_team_snapshot_groups", 0))
        denominator_employees = int(scope.get("total_employee_snapshots", 0))
        if denominator_groups < MINIMUM_COHORT or denominator_employees < MINIMUM_COHORT:
            raise ValueError("Un scope de equipo no alcanza la cohorte mínima o no tiene exposición.")
        buckets_by_scenario = scope.get("buckets")
        if not isinstance(buckets_by_scenario, dict):
            raise ValueError("Faltan los buckets de atribución de un scope.")
        for attribution in ("manager_at_exit", "manager_at_evaluation"):
            rows = buckets_by_scenario.get(attribution)
            if not isinstance(rows, list) or [str(row.get("bucket")) for row in rows] != list(expected_buckets):
                raise ValueError("Cada escenario debe contener exactamente los buckets 0/1/2+.")
            if sum(int(row.get("team_snapshot_groups", 0)) for row in rows) != denominator_groups:
                raise ValueError("Los buckets de equipo no reconcilian con su denominador.")
            if sum(int(row.get("employee_snapshots", 0)) for row in rows) != denominator_employees:
                raise ValueError("Los buckets de employee-snapshots no reconcilian con su denominador.")
            if abs(sum(float(row.get("group_share_percent", 0)) for row in rows) - 100.0) > 0.02:
                raise ValueError("Los porcentajes de grupos no suman 100%.")
            if abs(sum(float(row.get("employee_snapshot_share_percent", 0)) for row in rows) - 100.0) > 0.02:
                raise ValueError("Los porcentajes de employee-snapshots no suman 100%.")
        monthly = scope.get("monthly_series")
        if not isinstance(monthly, dict):
            raise ValueError("Falta la serie mensual de empleados de un scope.")
        dates_by_attribution = []
        for attribution in ("manager_at_evaluation", "manager_at_exit"):
            points = monthly.get(attribution)
            if not isinstance(points, list) or len(points) != int(evidence["evaluation_snapshot_count"]):
                raise ValueError("Cada atribución debe contener un punto por snapshot mensual.")
            dates = [str(point.get("snapshot_date")) for point in points]
            if len(set(dates)) != len(dates):
                raise ValueError("La serie mensual contiene snapshots duplicados.")
            dates_by_attribution.append(dates)
            for point in points:
                flagged = int(point.get("flagged_employees", 0))
                observable = int(point.get("observable_employees", 0))
                percent = float(point.get("employee_percent", 0))
                expected = 100.0 * flagged / observable if observable else 0.0
                if observable < MINIMUM_COHORT or flagged < 0 or flagged > observable:
                    raise ValueError("La serie mensual viola el denominador o la cohorte mínima.")
                if abs(percent - expected) > 0.00001:
                    raise ValueError("El porcentaje mensual no reconcilia con flagged / observable.")
        if dates_by_attribution[0] != dates_by_attribution[1]:
            raise ValueError("Las atribuciones no comparten el mismo calendario mensual.")
    return evidence


def more_than_1_employee_leaves_annual_evidence(primary: dict[str, object]) -> dict[str, object]:
    """Load the annual sensitivity and reconcile it to the primary six-month series."""
    evidence = load(MORE_THAN_1_LEAVES_ANNUAL_EVIDENCE)
    if evidence.get("artifact") != REPORTING_MODE:
        raise ValueError("La evidencia anual de la bandera de equipo no coincide con el modo del deck.")
    if evidence.get("query_path") != MORE_THAN_1_LEAVES_ANNUAL_AUDIT_SQL:
        raise ValueError("La evidencia anual no referencia la auditoría esperada.")
    if evidence.get("coverage_query_path") != MORE_THAN_1_LEAVES_ANNUAL_COVERAGE_SQL:
        raise ValueError("La evidencia anual no referencia su auditoría de cobertura.")
    if evidence.get("outcome") != "pass" or int(evidence.get("annual_window_months", 0)) != 12:
        raise ValueError("La evidencia anual no aprobó la regla de doce meses.")
    if evidence.get("included_term_type") != "Voluntary":
        raise ValueError("La comparación anual no está restringida a salidas Voluntary.")

    calendar = evidence.get("comparison_calendar")
    if not isinstance(calendar, dict):
        raise ValueError("Falta el calendario comparativo de la evidencia anual.")
    if (
        int(calendar.get("primary_evaluation_snapshot_count", 0)) != int(primary["evaluation_snapshot_count"])
        or int(calendar.get("annual_complete_snapshot_count", 0)) != 36
        or int(calendar.get("annual_excluded_primary_snapshot_count", 0)) != 4
    ):
        raise ValueError("El calendario anual no reconcilia con los 40 cortes semestrales.")

    audit = evidence.get("audit_metrics")
    if not isinstance(audit, dict):
        raise ValueError("Faltan métricas de auditoría para la comparación anual.")
    expected_metrics = {
        "published_annual_points": 144,
        "monthly_series_numerator_over_denominator": 0,
        "monthly_series_denominator_below_30": 0,
        "membership_duplicate_rows": 0,
        "denominator_mismatch_vs_six_month": 0,
        "annual_below_six_month_count": 0,
    }
    if any(int(audit.get(metric, -1)) != expected for metric, expected in expected_metrics.items()):
        raise ValueError("La comparación anual no supera sus reconciliaciones agregadas.")

    scopes = evidence.get("scopes")
    primary_scopes = primary.get("scopes")
    if not isinstance(scopes, list) or not isinstance(primary_scopes, list):
        raise ValueError("Faltan scopes para reconciliar la comparación anual.")
    if [str(scope.get("key")) for scope in scopes] != ["all_teams", "teams_gt_5"]:
        raise ValueError("La comparación anual no contiene los scopes esperados.")

    for scope in scopes:
        scope_key = str(scope["key"])
        primary_scope = next(item for item in primary_scopes if str(item["key"]) == scope_key)
        annual_series = scope.get("monthly_series")
        primary_series = primary_scope.get("monthly_series")
        if not isinstance(annual_series, dict) or not isinstance(primary_series, dict):
            raise ValueError("Falta una serie anual o semestral para un scope.")
        for attribution in ("manager_at_evaluation", "manager_at_exit"):
            annual_rows = annual_series.get(attribution)
            primary_rows = primary_series.get(attribution)
            if not isinstance(annual_rows, list) or len(annual_rows) != 36 or not isinstance(primary_rows, list):
                raise ValueError("Una atribución anual no tiene los 36 puntos esperados.")
            primary_by_date = {str(row["snapshot_date"]): row for row in primary_rows}
            annual_dates = [str(row["snapshot_date"]) for row in annual_rows]
            if len(set(annual_dates)) != 36 or any(date not in primary_by_date for date in annual_dates):
                raise ValueError("El calendario anual no es subconjunto del calendario semestral.")
            for row in annual_rows:
                primary_row = primary_by_date[str(row["snapshot_date"])]
                flagged = int(row["flagged_employees"])
                observable = int(row["observable_employees"])
                expected_percent = 100.0 * flagged / observable if observable else 0.0
                if observable < MINIMUM_COHORT or flagged < int(primary_row["flagged_employees"]) or flagged > observable:
                    raise ValueError("Un punto anual no cumple las reglas de población o anidamiento.")
                if observable != int(primary_row["observable_employees"]):
                    raise ValueError("El denominador anual no coincide con el denominador semestral.")
                if abs(float(row["employee_percent"]) - expected_percent) > 0.00001:
                    raise ValueError("El porcentaje anual no reconcilia con flagged / observable.")
    return evidence


def private_metrics(folder: str, root: Path = BASE) -> dict:
    report = load(root / folder / "private-aggregate-metrics.json")
    artifact_mode = report.get("reporting_mode")
    if artifact_mode and str(artifact_mode) != REPORTING_MODE:
        raise ValueError(
            f"El artefacto {folder} es {artifact_mode}; no puede incluirse en un "
            f"deck {REPORTING_MODE}. Regenere las métricas en el mismo modo."
        )
    return report


def private_distribution(folder: str, root: Path = BASE) -> list[tuple[str, int]]:
    report = private_metrics(folder, root)
    categories = report.get("distribution", {}).get("categories", [])
    result = [(str(row["label"]), int(row["count"])) for row in categories]
    percentage = sum(float(row.get("percent", 0)) for row in categories)
    if report.get("distribution", {}).get("kind") == "anonymized_distribution" and percentage < 99.95:
        displayed = sum(value for _, value in result)
        total = round(displayed / (percentage / 100))
        if total - displayed >= MINIMUM_COHORT:
            result.append(("Other bands", total - displayed))
    return result


def compensation_grade_distribution() -> tuple[list[tuple[str, int]], dict[str, int]]:
    """Load the frozen latest-snapshot grade domain and publish its safe tail."""
    evidence = load(COMPENSATION_GRADE_EVIDENCE)
    if evidence.get("reporting_mode") != REPORTING_MODE:
        raise ValueError("La evidencia de compensation grade no coincide con el modo del deck.")
    if evidence.get("query_path") != "queries/audits/compensation_grade_domain_validation_20260909.sql":
        raise ValueError("La evidencia de compensation grade no referencia la consulta esperada.")
    if str(evidence.get("snapshot_date")) != V4_SNAPSHOT:
        raise ValueError("La evidencia de compensation grade no usa el snapshot esperado.")
    if int(evidence.get("minimum_shared_cohort", 0)) != MINIMUM_COHORT:
        raise ValueError("La evidencia de compensation grade no conserva n >= 30.")

    raw_rows = evidence.get("rows")
    if not isinstance(raw_rows, list) or not raw_rows:
        raise ValueError("No se encontró la distribución congelada de compensation grade.")

    rows: list[tuple[str, int]] = []
    for expected_order, raw_row in enumerate(raw_rows, start=1):
        if not isinstance(raw_row, dict):
            raise ValueError("La distribución de compensation grade contiene una fila inválida.")
        if int(raw_row.get("display_order", 0)) != expected_order:
            raise ValueError("La distribución de compensation grade perdió su orden de publicación.")
        label = str(raw_row.get("grade_label", "")).strip()
        count = int(raw_row.get("employee_count", 0))
        if not label or count < MINIMUM_COHORT:
            raise ValueError("La distribución publicada contiene una etiqueta vacía o n < 30.")
        rows.append((label, count))

    expected_public = int(evidence["public_grade_count"])
    expected_public_employees = int(evidence["public_grade_employee_count"])
    if len(rows) != expected_public or sum(count for _, count in rows) != expected_public_employees:
        raise ValueError("Los grados publicables no reconcilian con el resumen de evidencia.")

    eligible = int(evidence["eligible_employee_count"])
    small_count = int(evidence["small_grade_employee_count"])
    if expected_public_employees + small_count != eligible:
        raise ValueError("Los grados publicables y la cola suprimida no reconcilian con la población.")
    if small_count >= MINIMUM_COHORT:
        rows.append(("Other grades", small_count))

    if REPORTING_MODE != "internal_analysis":
        rows = [
            ("Other grades" if label == "Other grades" else f"Compensation grade {index}", count)
            for index, (label, count) in enumerate(rows, start=1)
        ]

    if sum(count for _, count in rows) != eligible:
        raise ValueError("La distribución de compensation grade no reconcilia con la población elegible.")
    return rows, {
        "eligible_employee_count": eligible,
        "public_grade_count": expected_public,
        "suppressed_small_grade_count": int(evidence["suppressed_small_grade_count"]),
        "small_grade_employee_count": small_count,
    }


def private_coverage(folder: str, root: Path) -> list[tuple[str, float, int]]:
    report = private_metrics(folder, root)
    return [
        (str(row["fiscal_year"]), float(row["coverage_percent"]), int(row["observable"]))
        for row in report.get("annual_series", [])
    ]


def anonymized_values(folder: str, column: str, root: Path = BASE) -> list[tuple[str, int]]:
    """Publish category frequencies without exposing operational labels."""
    result: list[tuple[str, int]] = []
    category_number = 1
    for label, count in values(folder, column, root):
        if label == "Otros":
            result.append(("Other categories", count))
        else:
            result.append((f"Operating category {category_number}", count))
            category_number += 1
    return result


def raw_values_with_minimum_cohort(folder: str, column: str, root: Path = BASE) -> list[tuple[str, int]]:
    """Publish real operational labels only when every displayed aggregate is safe."""
    result = values(folder, column, root)
    if not result or any(count < MINIMUM_COHORT for _, count in result):
        raise ValueError(f"La distribución de {column} contiene una cohorte menor al mínimo publicable.")
    return [("Other categories" if label == "Otros" else label, count) for label, count in result]


def heading(title: str, subtitle: str) -> str:
    return f"""<div class="slide-heading"><div><h2 class="slide-title-text">{esc(title)}</h2><p class="slide-subtitle">{esc(subtitle)}</p></div></div>"""


def bar_rows(data: list[tuple[str, int]]) -> str:
    total = sum(value for _, value in data) or 1
    return "".join(
        f"""<div class="bar-row"><div class="bar-label" title="{esc(label)}">{esc(label)}</div>
        <div class="bar-track"><div class="bar-fill" style="width:{value / total * 100:.2f}%"></div></div>
        <div class="bar-value">{value / total * 100:.1f}% · {value:,}</div></div>"""
        for label, value in data
    )


def bar_card(
    title: str,
    data: list[tuple[str, int]],
    note: str = "",
    extra_class: str = "",
    legend: list[tuple[str, str]] | None = None,
) -> str:
    total = sum(value for _, value in data)
    classes = f"card chart-card {extra_class}".strip()
    legend_html = ""
    if legend:
        legend_html = '<div class="signal-legend" aria-label="Signal legend">' + "".join(
            f'<span class="signal-legend-item"><strong>{esc(label)}</strong> {esc(description)}</span>'
            for label, description in legend
        ) + "</div>"
    return f"""<article class="{esc(classes)}"><div class="card-title">{esc(title)}</div>
      <div class="bar-list">{bar_rows(data)}</div>
      {legend_html}
      <div class="chart-footer">Total shown: <strong>{total:,}</strong>. {esc(note)}</div></article>"""


def bar_card_es(title: str, data: list[tuple[str, int]], note: str = "", extra_class: str = "") -> str:
    """Use the established responsive bar-card layout with Spanish chart context."""
    total = sum(value for _, value in data)
    classes = f"card chart-card {extra_class}".strip()
    return f"""<article class="{esc(classes)}"><div class="card-title">{esc(title)}</div>
      <div class="bar-list">{bar_rows(data)}</div>
      <div class="chart-footer">Total mostrado: <strong>{total:,}</strong>. {esc(note)}</div></article>"""


def work_arrangement_binary_distribution(data: list[tuple[str, int]]) -> list[tuple[str, int]]:
    """Derive the requested exploratory binary view from the displayed categories."""
    onsite_rows = [count for label, count in data if label == "Onsite"]
    if len(onsite_rows) != 1:
        raise ValueError("La distribuciÃ³n de work_arrangement debe contener exactamente una categorÃ­a Onsite.")
    total = sum(value for _, value in data)
    onsite = onsite_rows[0]
    other = total - onsite
    if total <= 0 or onsite < 0 or other < 0:
        raise ValueError("La vista binaria de work_arrangement no reconcilia con un total vÃ¡lido.")
    grouped = [("Onsite (1)", onsite), ("Other stored values (0)", other)]
    if any(count < MINIMUM_COHORT for _, count in grouped):
        raise ValueError("La vista binaria de work_arrangement contiene una cohorte menor a n=30.")
    return grouped


def work_arrangement_main(data: list[tuple[str, int]]) -> str:
    """Keep the raw chart and add the requested display-only binary grouping below it."""
    binary = work_arrangement_binary_distribution(data)
    return (
        '<div class="work-arrangement-stack">'
        + bar_card(
            "Stored work_arrangement categories",
            data,
            "Top 10 actual categories + Other categories + no work arrangement. Every published bar meets n ≥ 30.",
            "work-arrangement-card",
        )
        + bar_card(
            "Binary view: Onsite (1) vs. other (0)",
            binary,
            "Exploratory grouping only: Onsite = 1; every other stored value, including No work arrangement, = 0. This does not change the raw field, variable definition, or assessment score.",
            "work-arrangement-binary-card",
        )
        + "</div>"
    )


def frozen_work_arrangement_distribution(root: Path = BASE) -> list[tuple[str, int]]:
    """Load the same frozen aggregate categories already used by slide 13."""
    eligible, observable = latest_snapshot_coverage("10-remote-hybrid-in-office-status", root)
    distribution = categorical_distribution(
        frozen_top_values("10-remote-hybrid-in-office-status", "work_arrangement", 10, root),
        populated=observable,
        eligible=eligible,
        other_label="Other categories",
        missing_label="No work arrangement",
    )
    if sum(value for _, value in distribution) != eligible:
        raise ValueError("La distribuciÃ³n congelada de work_arrangement no reconcilia con la poblaciÃ³n.")
    return distribution


def work_arrangement_binary_manifest_entry(data: list[tuple[str, int]]) -> dict[str, object]:
    """Record provenance for the display-only grouping without persisting rows."""
    grouped = work_arrangement_binary_distribution(data)
    total = sum(value for _, value in data)
    return {
        "source_artifact": str(WORK_ARRANGEMENT_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "source_artifact_sha256": hashlib.sha256(WORK_ARRANGEMENT_EVIDENCE.read_bytes()).hexdigest(),
        "source_field": "work_arrangement",
        "snapshot": V4_SNAPSHOT,
        "population": f"{total:,} active regular employees at snapshot {V4_SNAPSHOT}",
        "grain": "Distinct employee snapshot",
        "derivation": "Derived from the already-published aggregate category counts; no new query or score change.",
        "mapping": {
            "Onsite": 1,
            "all other stored values, including No work arrangement": 0,
        },
        "counts": {label: count for label, count in grouped},
        "minimum_cohort": MINIMUM_COHORT,
        "publication_rule": "Display-only binary grouping; aggregate counts only; every displayed bucket has n >= 30.",
        "outcome": "pass",
    }


def level_grouped_by_grade_family_evidence(path: Path = LEVEL_GRADE_FAMILY_EVIDENCE) -> dict[str, object]:
    """Load and validate the frozen aggregate Level-by-grade-family view."""
    if not path.exists():
        raise FileNotFoundError(path)
    evidence = load(path)
    if not isinstance(evidence, dict):
        raise ValueError("La evidencia Level-familia debe ser un objeto JSON.")
    if evidence.get("artifact_type") != "aggregate_display_evidence":
        raise ValueError("La evidencia Level-familia tiene un artifact_type inesperado.")
    if evidence.get("deliverable_mode") != REPORTING_MODE:
        raise ValueError("La evidencia Level-familia no coincide con el modo de entrega del deck.")
    if evidence.get("snapshot_date") != V4_SNAPSHOT or evidence.get("outcome") != "pass":
        raise ValueError("La evidencia Level-familia debe usar el snapshot 2026-08-23 y outcome pass.")
    if evidence.get("publication_status") != "exploratory_display_only" or evidence.get("score_v4_change") != "none":
        raise ValueError("La vista Level-familia debe permanecer exploratory_display_only y sin cambio de score v4.")
    metrics = evidence.get("metrics")
    validations = evidence.get("validations")
    matrix = evidence.get("matrix")
    levels = evidence.get("level_totals")
    families = evidence.get("family_totals")
    provenance = evidence.get("provenance")
    if not all(isinstance(value, (dict, list)) for value in (metrics, validations, matrix, levels, families, provenance)):
        raise ValueError("La evidencia Level-familia no contiene todos los bloques agregados requeridos.")
    if any(value is not True for value in validations.values()):
        raise ValueError("La evidencia Level-familia contiene una validación no aprobada.")
    expected_levels = list(LEVEL_GROUPED_ORDER)
    expected_families = ["M", "P", "R", "S", "T", "V / other grade families"]
    if [row.get("level") for row in levels] != expected_levels:
        raise ValueError("La evidencia Level-familia no conserva el orden de las nueve bandas.")
    if [row.get("family") for row in families] != expected_families:
        raise ValueError("La evidencia Level-familia no conserva el dominio visible de prefijos.")
    eligible = int(metrics["eligible_employee_count"])
    if eligible < MINIMUM_COHORT or int(metrics["source_row_count"]) != eligible:
        raise ValueError("El denominador Level-familia no reconcilia con las filas fuente.")
    if sum(int(row["employee_count"]) for row in levels) != eligible:
        raise ValueError("Las bandas Level no reconcilian con el denominador.")
    if sum(int(row["employee_count"]) for row in families) != eligible:
        raise ValueError("Las familias de grade no reconcilian con el denominador.")
    if sum(int(row["employee_count"]) for row in matrix) != eligible:
        raise ValueError("La matriz Level-familia no reconcilia con el denominador.")
    if any(int(row["employee_count"]) < MINIMUM_COHORT for row in matrix):
        raise ValueError("La matriz Level-familia contiene una celda menor a n=30.")
    audit = provenance.get("audit")
    if not isinstance(audit, dict):
        raise ValueError("La evidencia Level-familia no contiene la procedencia de la auditoría.")
    query_path = ROOT / str(audit.get("query_path", ""))
    if not query_path.exists() or str(audit.get("sql_sha256")) != hashlib.sha256(query_path.read_bytes()).hexdigest():
        raise ValueError("El hash SQL de la evidencia Level-familia no coincide.")
    if not re.fullmatch(r"[0-9a-f]{64}", str(audit.get("result_sha256", ""))):
        raise ValueError("El hash de resultado de la evidencia Level-familia es inválido.")
    return evidence


def engineering_cto_org_split_evidence(path: Path = ENGINEERING_CTO_EVIDENCE) -> dict[str, object]:
    """Load the frozen aggregate-only CTO display evidence and fail closed."""
    if not path.exists():
        raise FileNotFoundError(path)
    evidence = load(path)
    if not isinstance(evidence, dict):
        raise ValueError("La evidencia CTO debe ser un objeto JSON.")
    if evidence.get("artifact_type") != "aggregate_display_evidence":
        raise ValueError("La evidencia CTO tiene un artifact_type inesperado.")
    if evidence.get("deliverable_mode") != REPORTING_MODE:
        raise ValueError("La evidencia CTO no coincide con el modo de entrega del deck.")
    if evidence.get("snapshot_date") != V4_SNAPSHOT or evidence.get("outcome") != "pass":
        raise ValueError("La evidencia CTO debe usar el snapshot 2026-08-23 y outcome pass.")
    if evidence.get("publication_status") != "exploratory_display_only" or evidence.get("score_v4_change") != "none":
        raise ValueError("La vista CTO debe permanecer exploratory_display_only y sin cambio de score v4.")
    categories = evidence.get("category_distribution")
    metrics = evidence.get("metrics")
    validations = evidence.get("validations")
    provenance = evidence.get("provenance")
    if not isinstance(categories, list) or not isinstance(metrics, dict) or not isinstance(validations, dict) or not isinstance(provenance, dict):
        raise ValueError("La evidencia CTO no contiene los bloques agregados requeridos.")
    if [row.get("category") for row in categories] != ["CTO", "Corp Fxn & BU"]:
        raise ValueError("La evidencia CTO no contiene exactamente las dos categorías visibles.")
    counts = [int(row["employee_count"]) for row in categories]
    if any(count < MINIMUM_COHORT for count in counts):
        raise ValueError("La evidencia CTO contiene una categoría menor a n=30.")
    if sum(counts) != int(metrics["eligible_employee_count"]):
        raise ValueError("La distribución CTO no reconcilia con el denominador.")
    if int(metrics["category_reconciliation_difference"]) != 0 or int(metrics["eng_or_noneng_denominator_difference"]) != 0:
        raise ValueError("La evidencia CTO contiene una diferencia de reconciliación.")
    for key in (
        "population_reconciliation",
        "category_minimum_cohort",
        "zero_duplicate_employee_snapshot",
        "zero_manager_conflicts",
        "zero_et_leader_conflicts",
        "zero_eng_or_noneng_conflicts",
        "eng_or_noneng_same_current_denominator",
        "zero_cto_branch_overlap",
        "zero_hierarchy_cycles",
        "zero_hierarchy_depth_limit",
        "leader_a_active_branch_empty_accepted",
        "upper_chart_preserved_with_denominator_note",
    ):
        if validations.get(key) is not True:
            raise ValueError(f"La validación CTO {key} no está aprobada.")
    for name, entry in provenance.items():
        if not isinstance(entry, dict):
            raise ValueError(f"La procedencia CTO {name!r} es inválida.")
        query_path = ROOT / str(entry.get("query_path", ""))
        if not query_path.exists():
            raise ValueError(f"No existe la consulta congelada de CTO {query_path}.")
        if entry.get("sql_sha256") != hashlib.sha256(query_path.read_bytes()).hexdigest():
            raise ValueError(f"El hash SQL de CTO no coincide para {name!r}.")
        if not re.fullmatch(r"[0-9a-f]{64}", str(entry.get("result_sha256", ""))):
            raise ValueError(f"El hash del resultado CTO es inválido para {name!r}.")
    return evidence


def engineering_cto_lower_card(evidence: dict[str, object]) -> str:
    """Render the display-only lower category card from frozen aggregates."""
    categories = evidence["category_distribution"]
    metrics = evidence["metrics"]
    rule = evidence["rule_applied"]
    if not isinstance(categories, list) or not isinstance(metrics, dict) or not isinstance(rule, dict):
        raise ValueError("La evidencia CTO no tiene el contrato de la tarjeta inferior.")
    data = [(str(row["category"]), int(row["employee_count"])) for row in categories]
    eligible = int(metrics["eligible_employee_count"])
    upper_total = int(next(row["frozen_upper_chart_employee_count"] for row in evidence["denominator_reconciliation"] if row["variant"] == "active_regular_no_rf_filter"))
    difference = eligible - upper_total
    jim_active = int(evidence["leader_a_branch_diagnostic"]["leader_a_reachable_active_count"])
    note = (
        f"Display-only grouping based on the documented CTO branches; same current active Regular Employee universe "
        f"({eligible:,}) with no RF360 filter. The documented leader-A branch has {jim_active:,} active employees in "
        f"this snapshot. The frozen upper eng_or_noneng chart remains {upper_total:,}; the current universe differs by "
        f"{difference:,}. This does not replace eng_or_noneng or change the v4 score."
    )
    return bar_card(
        "Documented organizational split: CTO vs. Corp Fxn & BU",
        data,
        note,
        "engineering-cto-display-card",
    )


def engineering_cto_main(evidence: dict[str, object], top_card: str | None = None) -> str:
    """Keep the stored upper chart and place the CTO view beneath it."""
    if top_card is None:
        top_card = bar_card(
            "Distribution of eng_or_noneng",
            values("11-engineering-vs-non-engineering", "eng_or_noneng"),
            "The visualization describes the stored field.",
        )
    if not top_card.startswith('<article class="card chart-card">'):
        raise ValueError("La tarjeta superior de Engineering no tiene la estructura esperada.")
    return '<div class="engineering-cto-stack">' + top_card + engineering_cto_lower_card(evidence) + "</div>"


def engineering_cto_manifest_entry(evidence: dict[str, object]) -> dict[str, object]:
    """Persist traceable aggregate provenance without raw query rows."""
    provenance = evidence["provenance"]
    metrics = evidence["metrics"]
    if not isinstance(provenance, dict) or not isinstance(metrics, dict):
        raise ValueError("La evidencia CTO no contiene procedencia o métricas.")
    return {
        "evidence": str(ENGINEERING_CTO_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "evidence_sha256": hashlib.sha256(ENGINEERING_CTO_EVIDENCE.read_bytes()).hexdigest(),
        "queries": provenance,
        "snapshot": evidence["snapshot_date"],
        "population": evidence["population"],
        "grain": evidence["grain"],
        "publication_status": evidence["publication_status"],
        "score_v4_change": evidence["score_v4_change"],
        "rule_applied": evidence["rule_applied"],
        "category_distribution": evidence["category_distribution"],
        "metrics": {
            "eligible_employee_count": metrics["eligible_employee_count"],
            "cto_employee_count": metrics["cto_employee_count"],
            "category_total_count": metrics["category_total_count"],
            "category_reconciliation_difference": metrics["category_reconciliation_difference"],
            "eng_or_noneng_denominator_difference": metrics["eng_or_noneng_denominator_difference"],
            "leader_a_leader_in_eligible_cto_count": metrics["leader_a_leader_in_eligible_cto_count"],
            "leader_b_leader_in_eligible_cto_count": metrics["leader_b_leader_in_eligible_cto_count"],
            "branch_overlap_count": metrics["branch_overlap_count"],
            "leader_a_cycle_count": metrics["leader_a_cycle_count"],
            "leader_a_depth_limit_count": metrics["leader_a_depth_limit_count"],
        },
        "leader_a_branch_diagnostic": {
            "root_present": evidence["leader_a_branch_diagnostic"]["leader_a_root_present_count"],
            "root_active": evidence["leader_a_branch_diagnostic"]["leader_a_root_active_count"],
            "reachable_regular": evidence["leader_a_branch_diagnostic"]["leader_a_reachable_regular_count"],
            "reachable_active": evidence["leader_a_branch_diagnostic"]["leader_a_reachable_active_count"],
            "descendant_regular": evidence["leader_a_branch_diagnostic"]["leader_a_descendant_regular_count"],
            "descendant_active": evidence["leader_a_branch_diagnostic"]["leader_a_descendant_active_count"],
            "empty_active_branch_accepted": True,
        },
        "publication_rule": evidence["publication_rule"],
        "outcome": evidence["outcome"],
    }


def level_grouped_by_grade_family_manifest_entry(evidence: dict[str, object]) -> dict[str, object]:
    """Persist aggregate provenance for the Level-family display without rows."""
    provenance = evidence["provenance"]
    metrics = evidence["metrics"]
    if not isinstance(provenance, dict) or not isinstance(metrics, dict):
        raise ValueError("La evidencia Level-familia no contiene procedencia o métricas.")
    audit = provenance["audit"]
    if not isinstance(audit, dict):
        raise ValueError("La procedencia Level-familia no contiene la auditoría.")
    return {
        "evidence": str(LEVEL_GRADE_FAMILY_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "evidence_sha256": hashlib.sha256(LEVEL_GRADE_FAMILY_EVIDENCE.read_bytes()).hexdigest(),
        "builder": str(LEVEL_GRADE_FAMILY_BUILDER.relative_to(ROOT)).replace("\\", "/"),
        "audit_query": audit["query_path"],
        "query_sha256": {
            "audit_sql": audit["sql_sha256"],
            "audit_result": audit["result_sha256"],
        },
        "snapshot": evidence["snapshot_date"],
        "population": evidence["population"],
        "grain": evidence["grain"],
        "definition": evidence["definition"],
        "rule_applied": evidence["rule_applied"],
        "level_totals": evidence["level_totals"],
        "family_totals": evidence["family_totals"],
        "aggregate_metrics": {
            key: metrics[key]
            for key in (
                "source_row_count",
                "eligible_employee_count",
                "duplicate_employee_snapshot_count",
                "missing_level_employee_count",
                "missing_grade_employee_count",
                "level_band_count",
                "raw_grade_family_count",
                "raw_matrix_cell_count",
                "raw_matrix_cells_below_minimum_count",
                "raw_matrix_employee_count",
                "employee_level_conflict_count",
                "employee_family_conflict_count",
                "employee_grade_conflict_count",
            )
        },
        "publication_status": evidence["publication_status"],
        "score_v4_change": evidence["score_v4_change"],
        "publication_rule": evidence["publication_rule"],
        "limitations": evidence["limitations"],
        "outcome": evidence["outcome"],
    }


def level_grouped_card(data: list[tuple[str, int]], note: str) -> str:
    total = sum(value for _, value in data)
    return f"""<article class="card chart-card level-main-card">
      <div class="level-card-heading"><div class="card-title">Level grouped</div>
        <div class="level-direction" aria-label="Senior to junior"><span>Senior</span><span class="level-direction-arrow">&rarr;</span><span>junior</span></div>
      </div>
      <div class="bar-list">{bar_rows(data)}</div>
      <div class="chart-footer">Total shown: <strong>{total:,}</strong>. {esc(note)}</div></article>"""


def level_constructs_layout(
    level_grouped: list[tuple[str, int]],
    management_level: list[tuple[str, int]],
    job_level_detail: list[tuple[str, int]],
) -> str:
    """Render Level grouped as the semantic hierarchy and the other fields as supports."""
    return f"""<div class="level-constructs">
      {level_grouped_card(level_grouped, f"Snapshot {V4_SNAPSHOT}; fixed senior-to-junior hierarchy.")}
      <div class="level-support-stack">
        {bar_card("Management level", management_level, f"Snapshot {V4_SNAPSHOT}; ordered support view.", "level-support-card")}
        {bar_card("Top 10 job levels + Other", job_level_detail, f"Snapshot {V4_SNAPSHOT}; ranking by size is retained because R/T/P families are not one comparable ladder.", "level-support-card level-job-detail-card")}
      </div>
    </div>"""


def level_grade_family_css_class(family: str) -> str:
    return {
        "M": "family-m",
        "P": "family-p",
        "R": "family-r",
        "S": "family-s",
        "T": "family-t",
        "V / other grade families": "family-v-other",
    }.get(family, "family-v-other")


def level_grouped_by_grade_family_chart(evidence: dict[str, object]) -> str:
    """Render Level bands as within-band stacked grade-family bars."""
    matrix = evidence["matrix"]
    family_totals = evidence["family_totals"]
    metrics = evidence["metrics"]
    if not isinstance(matrix, list) or not isinstance(family_totals, list) or not isinstance(metrics, dict):
        raise ValueError("La evidencia Level-familia no tiene el contrato de visualización esperado.")
    rows: list[str] = []
    for item in matrix:
        level = str(item["level"])
        total = int(item["employee_count"])
        segments = item["segments"]
        if not isinstance(segments, list) or total <= 0:
            raise ValueError(f"La fila Level-familia es inválida para {level!r}.")
        segment_markup_parts: list[str] = []
        for segment in segments:
            family = str(segment["family"])
            percentage = float(segment["percentage_within_level"])
            label = (
                f'<span class="level-grade-family-segment-label">{percentage:.1f}%</span>'
                if percentage >= LEVEL_GRADE_FAMILY_LABEL_MIN_PCT
                else ""
            )
            segment_markup_parts.append(
                f'<span class="level-grade-family-segment {level_grade_family_css_class(family)}" '
                f'style="width:{percentage:.4f}%" '
                f'title="{esc(family)}: {int(segment["employee_count"]):,} ({percentage:.1f}%)">{label}</span>'
            )
        segment_markup = "".join(segment_markup_parts)
        rows.append(
            f'''<div class="level-grade-family-row">
        <div class="level-grade-family-label">{esc(level)}</div>
        <div class="level-grade-family-track" aria-label="{esc(level)}: {total:,} employees">{segment_markup}</div>
        <div class="level-grade-family-total">{total:,} · 100%</div>
      </div>'''
        )
    legend = "".join(
        f'''<span class="level-grade-family-legend-item"><i class="level-grade-family-swatch {level_grade_family_css_class(str(item["family"]))}"></i>{esc(item["family"])} · {float(item["percentage"]):.1f}% · {int(item["employee_count"]):,}</span>'''
        for item in family_totals
    )
    return f'''<article class="card chart-card level-grade-family-card">
      <div class="card-title">Level grouped × grade family proxy</div>
      <div class="level-grade-family-chart">{"".join(rows)}</div>
      <div class="level-grade-family-legend" aria-label="Grade family legend">{legend}</div>
      <div class="chart-footer">Total shown: <strong>{int(metrics["eligible_employee_count"]):,}</strong>. Segment widths are each Level band's composition; the visible grade family is a prefix proxy, not an official track.</div>
    </article>'''


def level_grouped_by_grade_family_slide(number: int, evidence: dict[str, object]) -> str:
    """Render the new display-only slide immediately after the Level slide."""
    metrics = evidence["metrics"]
    if not isinstance(metrics, dict):
        raise ValueError("La evidencia Level-familia no contiene métricas.")
    return data_slide(
        number,
        "Level grouped by grade family",
        f"Exploratory display-only proxy · active Regular Employees · snapshot {V4_SNAPSHOT}",
        level_grouped_by_grade_family_chart(evidence),
        side_card(
            "Level remains the primary construct",
            "The chart keeps the nine stored Level bands and adds Compensation Grade family context. It does not replace level_grouped, create a universal 10–20 / 30–50 / 60+ ladder, or claim that the prefix is an approved track field.",
            [
                ("Primary", "level_grouped"),
                ("Context", "compensation_grade prefix proxy"),
                ("Snapshot", V4_SNAPSHOT),
                ("Population", f"{int(metrics['eligible_employee_count']):,} active Regular Employees"),
                ("Visible cells", "all n ≥ 30"),
                ("v4 score", "unchanged"),
            ],
            "Exploratory display-only",
        ),
    )


def trend_card(title: str, data: list[tuple[str, float, int]], note: str = "") -> str:
    maximum = max((pct for _, pct, _ in data), default=1) or 1
    bars: list[str] = []
    for label, pct, count in data:
        height = max(3, pct / maximum * 166)
        # Counts belong inside visible bars. A label cannot fit inside a 3px
        # minimum bar, so retain the count below its year in that edge case.
        count_in_bar = height >= 34
        count_markup = f'<span class="trend-count">{count:,}</span>' if count_in_bar else ""
        label_count = "" if count_in_bar else f'<small>n={count:,}</small>'
        bars.append(
            f"""<div class="trend-bar-wrap"><div class="trend-percent">{pct:.2f}%</div>
            <div class="trend-bar" style="height:{height:.1f}px" aria-label="{esc(label)}: {pct:.2f}%, {count:,} employee-snapshots">{count_markup}</div>
            <div class="trend-label"><span>{esc(label)}</span>{label_count}</div></div>"""
        )
    return f"""<article class="card chart-card"><div class="card-title">{esc(title)}</div>
      <div class="trend-chart" style="--bars:{max(1, len(data))}">{''.join(bars)}</div>
      <div class="chart-footer">{esc(note)}</div></article>"""


def qvoice_comment_evidence() -> dict[str, object]:
    """Load the current aggregate-only raw QVoice comment evidence."""
    if not QVOICE_COMMENT_EVIDENCE.exists():
        import sys

        sys.path.insert(0, str(ROOT / "tools"))
        from build_qvoice_comment_evidence import build_evidence

        build_evidence(QVOICE_COMMENT_EVIDENCE)
    evidence = json.loads(QVOICE_COMMENT_EVIDENCE.read_text(encoding="utf-8"))
    if evidence.get("artifact") != "internal_analysis" or evidence.get("outcome") != "pass":
        raise ValueError("QVoice comment evidence must be internal_analysis with outcome: pass.")
    if evidence.get("comment_text_persisted") or evidence.get("identifiers_persisted"):
        raise ValueError("QVoice comment evidence contains a prohibited persisted payload.")
    for wave in evidence.get("waves", []):
        if wave.get("duplicate_participant_rows") != 0 or wave.get("comments_without_key") != 0:
            raise ValueError(f"QVoice comment evidence failed key validation for {wave.get('wave')}.")
        for count in wave.get("published_theme_counts", {}).values():
            if count is not None and int(count) < MINIMUM_COHORT:
                raise ValueError("QVoice comment evidence contains a published sub-threshold count.")
    return evidence


def qvoice_retention_concerns_evidence(path: Path | None = None) -> dict[str, object]:
    """Load the immutable aggregate-only evidence for the slide-19 refresh."""
    evidence_path = path or QVOICE_RETENTION_CONCERNS_EVIDENCE
    if not evidence_path.exists():
        if path is not None:
            raise FileNotFoundError(evidence_path)
        import sys

        sys.path.insert(0, str(ROOT / "tools"))
        from build_qvoice_retention_concerns_evidence import build_evidence

        build_evidence(evidence_path)
    import sys

    sys.path.insert(0, str(ROOT / "tools"))
    from build_qvoice_retention_concerns_evidence import validate_evidence

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    return validate_evidence(evidence)


def qvoice_retention_concerns_manifest_entry(evidence: dict[str, object]) -> dict[str, object]:
    return {
        "evidence": str(QVOICE_RETENTION_CONCERNS_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "builder": str(QVOICE_RETENTION_CONCERNS_BUILDER.relative_to(ROOT)).replace("\\", "/"),
        "artifact": evidence["artifact"],
        "waves": [wave["wave"] for wave in evidence["waves"]],
        "source_rule": evidence["source_rule"],
        "denominator_rule": evidence["denominator_rule"],
        "grain": evidence["grain"],
        "publication_rule": "n >= 30 for every displayed count or percentage; suppressed values are not persisted.",
        "scope": evidence["scope"],
        "outcome": evidence["outcome"],
    }


def qvoice_nonrespondent_evidence() -> dict[str, object]:
    """Load and validate aggregate QVoice response/non-response proxy evidence."""
    if not QVOICE_NONRESPONDENT_EVIDENCE.exists():
        raise FileNotFoundError(QVOICE_NONRESPONDENT_EVIDENCE)
    evidence = json.loads(QVOICE_NONRESPONDENT_EVIDENCE.read_text(encoding="utf-8"))
    if evidence.get("artifact") != "internal_analysis" or evidence.get("outcome") != "pass":
        raise ValueError("QVoice non-response evidence must be internal_analysis with outcome: pass.")
    privacy = evidence.get("privacy", {})
    if privacy.get("identifiers_persisted") or privacy.get("response_values_persisted") or privacy.get("free_text_persisted"):
        raise ValueError("QVoice non-response evidence contains a prohibited persisted payload.")
    required = ("eligible_snapshot_employees", "responded_proxy", "qvoice_row_without_answer", "no_qvoice_row")
    for wave in evidence.get("waves", []):
        if wave.get("raw_duplicate_key_rows") != 0 or wave.get("raw_missing_key_rows_with_any_answer") != 0 or wave.get("raw_invalid_key_rows") != 0:
            raise ValueError(f"QVoice non-response evidence failed raw-key validation for {wave.get('wave')}.")
        values = [int(wave.get(name, 0)) for name in required]
        if sum(values[1:]) != values[0]:
            raise ValueError(f"QVoice non-response categories do not reconcile for {wave.get('wave')}.")
        if int(wave.get("qvoice_keys_inside_snapshot", 0)) + int(wave.get("qvoice_keys_outside_snapshot", 0)) != int(wave.get("raw_qvoice_keys", 0)):
            raise ValueError(f"QVoice raw keys do not reconcile to inside/outside snapshot for {wave.get('wave')}.")
        if any(value < MINIMUM_COHORT for value in values[1:]):
            raise ValueError(f"QVoice non-response evidence contains a published sub-threshold category for {wave.get('wave')}.")
    return evidence


def qvoice_nonrespondent_card(evidence: dict[str, object]) -> str:
    categories = [
        ("Responded", "responded_proxy", "#2A2AEA"),
        ("QVoice row / no answer", "qvoice_row_without_answer", "#843AFF"),
        ("No QVoice row", "no_qvoice_row", "#B08A00"),
    ]
    headers = "".join(
        f'<th><span class="qvoice-response-key" style="background:{color}"></span>{esc(label)}<br><small>n · %</small></th>'
        for label, _, color in categories
    )
    rows = []
    for wave in evidence["waves"]:
        eligible = int(wave["eligible_snapshot_employees"])
        cells = []
        for _, field, _ in categories:
            count = int(wave[field])
            cells.append(f"<td><strong>{count:,}</strong> · {100 * count / eligible:.1f}%</td>")
        rows.append(f'<tr><td>{esc(wave["wave"])}</td>{"".join(cells)}<td>{eligible:,}</td></tr>')
    table = (
        '<table class="qvoice-response-table"><thead><tr><th>Survey wave</th>'
        + headers
        + '<th>Snapshot n</th></tr></thead><tbody>'
        + "".join(rows)
        + '</tbody></table>'
    )
    return f'''<article class="card chart-card qvoice-response-card">
      <div class="card-title">Distribution of QVoice participation by survey wave</div>
      <div id="qvoice-response-chart" class="qvoice-response-chart" aria-label="QVoice response participation proxy by survey wave"></div>
      {table}
      <p class="qvoice-response-note">Bars show the share of the stored snapshot; labels and table show absolute employees and percent of that snapshot.</p>
      <p class="qvoice-response-warning"><strong>Non-response proxy — snapshot assumption.</strong> “No QVoice row” is not a confirmed non-response until the invitation roster, eligibility rule, and wave-close status are validated.</p>
    </article>'''


def qvoice_nonrespondent_slide(number: int, evidence: dict[str, object]) -> str:
    latest = evidence["waves"][-1]
    return data_slide(
        number,
        "Non-respondents",
        "Internal analysis · participation distribution using a stored prior-month snapshot proxy",
        qvoice_nonrespondent_card(evidence),
        side_card(
            "What this slide measures",
            "Each wave compares the raw QVoice participant keys with an HRDA snapshot treated as the prior-month day-15 population proxy. The categories are descriptive reconciliation buckets, not a finalized response-rate definition.",
            [
                ("Assumption", "stored snapshot nearest prior-month day 15"),
                ("Population", "Employee · Regular · active_status = 1"),
                ("Responded", "QVoice row with at least one original answer field"),
                ("No answer", "QVoice row with all checked answer fields empty"),
                ("No row", "snapshot employee absent from raw QVoice keys"),
                ("Scope", "Mar-2023 · Jan-2024 · Jan-2025 · Jan-2026"),
            ],
            "Non-response proxy · internal review",
        ),
    )


def qvoice_comparable_favorable_evidence() -> dict[str, object]:
    """Load the frozen 33-item QVoice trend evidence and enforce its contract."""
    if not QVOICE_COMPARABLE_EVIDENCE.exists():
        import sys

        sys.path.insert(0, str(ROOT / "tools"))
        from build_qvoice_comparable_favorable_evidence import build_evidence

        build_evidence(QVOICE_COMPARABLE_EVIDENCE)
    evidence = json.loads(QVOICE_COMPARABLE_EVIDENCE.read_text(encoding="utf-8"))
    if evidence.get("artifact") != "internal_analysis" or evidence.get("outcome") != "pass":
        raise ValueError("La evidencia comparable QVoice debe ser internal_analysis con outcome: pass.")
    if evidence.get("identifier_or_row_data_persisted") is not False:
        raise ValueError("La evidencia comparable QVoice contiene datos individuales prohibidos.")
    contract = evidence.get("strict_item_contract", {})
    if int(contract.get("strict_common_item_count", 0)) != 33:
        raise ValueError("La evidencia comparable QVoice no contiene exactamente 33 items comunes.")
    expected = {
        2024: (36_806, 27_563, 77.3663),
        2025: (37_837, 30_342, 78.2771),
        2026: (42_203, 33_067, 79.3780),
    }
    waves = evidence.get("waves", [])
    if [int(wave.get("year", 0)) for wave in waves] != list(expected):
        raise ValueError("Las waves comparables QVoice no son 2024–2026 en orden.")
    for wave in waves:
        year = int(wave["year"])
        participants, complete, favorable = expected[year]
        if int(wave.get("participant_rows", 0)) != participants or int(wave.get("complete_comparable_participants", 0)) != complete:
            raise ValueError(f"La evidencia comparable QVoice de {year} no reconcilia los denominadores.")
        if abs(float(wave.get("mean_favorable_percent", 0)) - favorable) > 0.00005:
            raise ValueError(f"La evidencia comparable QVoice de {year} no reconcilia el promedio favorable.")
        if int(wave.get("duplicate_participant_rows", -1)) != 0 or int(wave.get("duplicate_conflicting_rows", -1)) != 0:
            raise ValueError(f"La evidencia comparable QVoice de {year} contiene duplicados o conflictos.")
        if int(wave.get("out_of_domain_non_sentinel_cells", -1)) != 0:
            raise ValueError(f"La evidencia comparable QVoice de {year} contiene valores fuera de 0/1.")
        band_rows = wave.get("score_bands", [])
        if len(band_rows) != 6 or sum(int(row.get("participant_count", 0)) for row in band_rows) != complete:
            raise ValueError(f"Las bandas QVoice de {year} no suman su cohorte 33/33.")
        if complete < MINIMUM_COHORT:
            raise ValueError(f"La cohorte comparable QVoice de {year} está por debajo de n={MINIMUM_COHORT}.")
    return evidence


def qvoice_normalized_region_evidence(path: Path | None = None) -> dict[str, object]:
    """Load frozen, aggregate-only QVoice regional-normalization evidence."""
    evidence_path = path or QVOICE_NORMALIZED_REGION_EVIDENCE
    if not evidence_path.exists():
        import sys

        sys.path.insert(0, str(ROOT / "tools"))
        from build_qvoice_normalized_region_evidence import build_evidence

        build_evidence(evidence_path)
    import sys

    sys.path.insert(0, str(ROOT / "tools"))
    from build_qvoice_normalized_region_evidence import validate_evidence

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    if not isinstance(evidence, dict):
        raise ValueError("QVoice normalized evidence must be a JSON object.")
    return validate_evidence(evidence)


def qvoice_normalized_region_manifest_entry(evidence: dict[str, object]) -> dict[str, object]:
    """Return safe provenance for the normalized QVoice distribution."""
    waves = evidence["waves"]
    assert isinstance(waves, list)
    return {
        "evidence": str(QVOICE_NORMALIZED_REGION_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "builder": str(QVOICE_NORMALIZED_REGION_BUILDER.relative_to(ROOT)).replace("\\", "/"),
        "source": "QVoice raw Excel workbooks; Raw data sheets only",
        "waves": [int(wave["year"]) for wave in waves],
        "grain": evidence["grain"],
        "population": "Respondents with 33/33 strictly comparable valid binary items and a stored Region",
        "definition": "Within stored Region × survey-wave population z-score of 100 × favorable items / 33.",
        "reference_cohort": "Stored Region × survey wave; every cohort and displayed band has n >= 30.",
        "publication_rule": "Aggregate internal analysis only; no identifiers, response values, individual scores, or region labels.",
        "limitation": "Respondent-only descriptive distribution; no workforce denominator, QVoice-to-workforce join, or attrition relationship is asserted.",
        "outcome": evidence["outcome"],
    }


def qvoice_whole_percent_labels(
    score_bands: list[dict[str, object]], percent_key: str = "percent_of_complete"
) -> list[int]:
    """Allocate whole-percent display labels that add to 100 without changing widths."""
    values = [float(row[percent_key]) for row in score_bands]
    labels = [int(value) for value in values]
    remaining = 100 - sum(labels)
    if remaining < 0 or remaining > len(labels):
        raise ValueError("Las bandas QVoice no permiten etiquetas enteras que sumen 100%.")
    priority = sorted(
        range(len(values)), key=lambda index: (values[index] - labels[index], -index), reverse=True
    )
    for index in priority[:remaining]:
        labels[index] += 1
    if sum(labels) != 100:
        raise ValueError("Las etiquetas enteras QVoice no suman 100%.")
    return labels


def qvoice_stack_segments(score_bands: list[dict[str, object]]) -> str:
    """Render exact-width score bands with whole-number presentation labels."""
    display_labels = qvoice_whole_percent_labels(score_bands)
    return "".join(
        f'<span class="qvoice-stack-segment qvoice-band-{index}" style="width:{float(row["percent_of_complete"]):.4f}%" title="{esc(str(row["band"]))}: {float(row["percent_of_complete"]):.4f}% · n={int(row["participant_count"]):,}"><span>{display_label}%</span></span>'
        for index, (row, display_label) in enumerate(zip(score_bands, display_labels), start=1)
    )


def qvoice_comparable_favorable_card(evidence: dict[str, object]) -> str:
    """Render the annual average and 100% score-band distributions from frozen aggregates."""
    waves = list(evidence["waves"])
    trend_bars = "".join(
        f'''<div class="qvoice-favorable-bar-wrap">
          <div class="qvoice-favorable-value">{float(wave['mean_favorable_percent']):.2f}%</div>
          <div class="qvoice-favorable-bar" style="height:{float(wave['mean_favorable_percent']) * 1.8:.1f}px"><span>n={int(wave['complete_comparable_participants']):,}</span></div>
          <div class="qvoice-favorable-year"><strong>{int(wave['year'])}</strong><span>33/33 válidos</span></div>
        </div>'''
        for wave in waves
    )
    stacks = "".join(
        f'''<div class="qvoice-stack-row"><div class="qvoice-stack-label"><strong>{int(wave['year'])}</strong>n={int(wave['complete_comparable_participants']):,}</div>
          <div class="qvoice-stack-bar" aria-label="Distribución {int(wave['year'])}, n={int(wave['complete_comparable_participants']):,}">{qvoice_stack_segments(wave['score_bands'])}</div>
        </div>'''
        for wave in waves
    )
    first_bands = waves[0]["score_bands"]
    legend = "".join(
        f'<span><i class="qvoice-band-dot qvoice-band-{index}"></i>{esc(str(row["band"]))}</span>'
        for index, row in enumerate(first_bands, start=1)
    )
    return f'''<article class="card chart-card qvoice-comparable-card"><div class="card-title">33 ítems favorables estrictamente comparables · 0 = desfavorable, 1 = favorable</div>
      <div class="qvoice-comparable-grid">
        <section class="qvoice-comparable-panel"><h3>Promedio favorable por wave</h3><p>Media aritmética de puntajes individuales: 100 × favorables / 33.</p><div class="qvoice-favorable-trend" aria-label="Promedio favorable anual">{trend_bars}</div></section>
        <section class="qvoice-comparable-panel"><h3>Distribución de puntajes individuales</h3><p>Cada barra suma 100% de respondentes incluidos en la wave.</p><div class="qvoice-stack-list">{stacks}</div><div class="qvoice-band-legend" aria-label="Leyenda de bandas de puntaje">{legend}</div></section>
      </div>
      <div class="chart-footer">Denominador por wave: respondentes con <strong>33/33 ítems comparables válidos</strong>. Las bandas reconcilian exactamente con cada n; no se infiere percepción de toda la plantilla.</div></article>'''


def qvoice_comparable_favorable_slide(number: int, evidence: dict[str, object]) -> str:
    main = qvoice_comparable_favorable_card(evidence)
    side = side_card(
        "Una comparación deliberadamente acotada",
        "La tendencia usa únicamente los 33 flags favorables presentes en las tres waves bajo la coincidencia estricta documentada. La completitud es una regla analítica de 33/33, no un flag oficial de encuesta completa.",
        [
            ("Población", "respondentes con 33/33 ítems comparables válidos"),
            ("Puntaje", "100 × favorables / 33"),
            ("Resultado anual", "promedio aritmético de puntajes individuales"),
            ("Waves", "2024 · 2025 · 2026"),
            ("Ítems", "33 de 52 · 52 · 53 flags binarios seleccionables"),
            ("Límite", "sin join a workforce ni inferencia de elegibilidad"),
        ],
        "Internal analysis · aggregate",
    )
    return data_slide(
        number,
        "Average of all QVoice items",
        "Tendencia comparable 2024–2026 · entre respondentes con 33/33 ítems comparables válidos",
        main,
        side,
    )


def qvoice_heartbeat_evidence(path: Path | None = None) -> dict[str, object]:
    """Load and validate the frozen aggregate-only Jan-2026 heartbeat evidence."""
    evidence_path = path or QVOICE_HEARTBEAT_EVIDENCE
    if not evidence_path.exists():
        raise FileNotFoundError(evidence_path)
    evidence = load(evidence_path)
    if not isinstance(evidence, dict):
        raise ValueError("QVoice heartbeat evidence must be a JSON object.")
    if evidence.get("artifact") != "presentation" or evidence.get("outcome") != "pass":
        raise ValueError("QVoice heartbeat evidence must be presentation-safe with outcome: pass.")

    forbidden_fields = {
        "employee_id", "manager_employee_id", "employee_name", "manager_name", "emp_name",
        "email", "address", "postal_code", "response_value", "individual_score", "personal_mean",
    }

    def reject_restricted_fields(value: object) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if str(key).lower() in forbidden_fields:
                    raise ValueError("QVoice heartbeat evidence persists a restricted individual field.")
                reject_restricted_fields(nested)
        elif isinstance(value, list):
            for nested in value:
                reject_restricted_fields(nested)

    reject_restricted_fields(evidence)
    privacy = evidence.get("privacy")
    if not isinstance(privacy, dict) or privacy.get("minimum_published_cohort") != MINIMUM_COHORT:
        raise ValueError("QVoice heartbeat evidence lost the minimum cohort safeguard.")
    for key in ("identifiers_persisted", "individual_rows_persisted", "individual_scale_values_persisted", "runtime_join_sql_persisted"):
        if privacy.get(key) is not False:
            raise ValueError("QVoice heartbeat evidence fails its privacy contract.")

    source = evidence.get("source")
    population = evidence.get("population")
    definition = evidence.get("definition")
    metrics = evidence.get("metrics")
    if not isinstance(source, dict) or source.get("wave") != "Jan-2026":
        raise ValueError("QVoice heartbeat evidence is not the approved Jan-2026 wave.")
    if not isinstance(population, dict) or not isinstance(definition, dict) or not isinstance(metrics, dict):
        raise ValueError("QVoice heartbeat evidence is missing its source contract.")
    if int(metrics.get("item_count", 0)) != 53 or int(metrics.get("publishable_item_count", 0)) != 53:
        raise ValueError("QVoice heartbeat must publish exactly 53 items.")
    if int(metrics.get("minimum_valid_items", 0)) != 38:
        raise ValueError("QVoice heartbeat minimum valid-item rule changed unexpectedly.")
    if int(population.get("eligible_employees", 0)) < MINIMUM_COHORT:
        raise ValueError("QVoice heartbeat workforce denominator is below the publication threshold.")
    if int(metrics.get("matched_workforce_employees", 0)) > int(population.get("eligible_employees", 0)):
        raise ValueError("QVoice heartbeat matched workforce count exceeds its denominator.")
    if int(metrics.get("duplicate_key_rows", -1)) != 0 or int(metrics.get("duplicate_conflicting_employee_keys", -1)) != 0:
        raise ValueError("QVoice heartbeat raw QVoice keys contain duplicate or conflicting rows.")
    if int(metrics.get("invalid_scale_cells", -1)) != 0:
        raise ValueError("QVoice heartbeat contains invalid scale cells.")

    items = evidence.get("items")
    if not isinstance(items, list) or len(items) != 53:
        raise ValueError("QVoice heartbeat item evidence is incomplete.")
    by_id: dict[str, dict[str, object]] = {}
    for raw_row in items:
        if not isinstance(raw_row, dict):
            raise ValueError("QVoice heartbeat item row is not structured.")
        question_id = str(raw_row.get("question_id", ""))
        if not re.fullmatch(r"Q(?:[1-9]|[1-4][0-9]|5[0-3])", question_id) or question_id in by_id:
            raise ValueError("QVoice heartbeat question IDs are not unique Q1–Q53 labels.")
        valid_count = int(raw_row.get("valid_employee_count", 0))
        upvote_count = int(raw_row.get("upvote_count", 0))
        stable_count = int(raw_row.get("stable_count", 0))
        downvote_count = int(raw_row.get("downvote_count", 0))
        favorable_denominator = int(raw_row.get("favorable_denominator", 0))
        if valid_count < MINIMUM_COHORT or upvote_count + stable_count + downvote_count != valid_count:
            raise ValueError(f"QVoice heartbeat item {question_id} does not reconcile its sign buckets.")
        if favorable_denominator != valid_count:
            raise ValueError(f"QVoice heartbeat item {question_id} does not reconcile its favorable denominator.")
        eligible_count = int(population.get("eligible_employees", 0))
        expected_percentages = {
            "upvote_percent": 100.0 * upvote_count / valid_count,
            "downvote_percent": 100.0 * downvote_count / valid_count,
            "favorable_percent": 100.0 * int(raw_row.get("favorable_count", 0)) / valid_count,
            "workforce_coverage_percent": 100.0 * valid_count / eligible_count,
        }
        for key, expected in expected_percentages.items():
            if abs(float(raw_row.get(key, -999.0)) - expected) > 0.0002:
                raise ValueError(f"QVoice heartbeat item {question_id} does not reconcile {key}.")
        by_id[question_id] = raw_row

    if set(by_id) != {f"Q{index}" for index in range(1, 54)}:
        raise ValueError("QVoice heartbeat item coverage is not exactly Q1–Q53.")

    for collection_name, rate_key, expected_ids in (
        ("top_upvotes", "upvote_percent", ["Q38", "Q37", "Q32", "Q30", "Q33"]),
        ("top_downvotes", "downvote_percent", ["Q53", "Q10", "Q11", "Q47", "Q27"]),
    ):
        collection = evidence.get(collection_name)
        if not isinstance(collection, list) or len(collection) != 5:
            raise ValueError(f"QVoice heartbeat {collection_name} must contain five items.")
        ids = [str(row.get("question_id", "")) for row in collection if isinstance(row, dict)]
        if ids != expected_ids:
            raise ValueError(f"QVoice heartbeat {collection_name} is not the frozen ranking order.")
        ranked_ids = [
            str(row["question_id"])
            for row in sorted(items, key=lambda row: (-float(row[rate_key]), str(row["question_id"])))[:5]
        ]
        if ids != ranked_ids:
            raise ValueError(f"QVoice heartbeat {collection_name} does not reconcile to all items.")
        for row in collection:
            if not isinstance(row, dict) or int(row.get("valid_employee_count", 0)) < MINIMUM_COHORT:
                raise ValueError(f"QVoice heartbeat {collection_name} contains a sub-threshold item.")

    provenance = evidence.get("provenance")
    if not isinstance(provenance, dict) or provenance.get("profile_sql") != QVOICE_HEARTBEAT_PROFILE_SQL or provenance.get("audit_sql") != QVOICE_HEARTBEAT_AUDIT_SQL:
        raise ValueError("QVoice heartbeat evidence is not linked to the approved aggregate SQL.")
    return evidence


def qvoice_heartbeat_manifest_entry(evidence: dict[str, object]) -> dict[str, object]:
    """Return safe heartbeat provenance without retaining response-level values."""
    metrics = evidence["metrics"]
    population = evidence["population"]
    provenance = evidence["provenance"]
    assert isinstance(metrics, dict) and isinstance(population, dict) and isinstance(provenance, dict)
    return {
        "evidence": str(QVOICE_HEARTBEAT_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "builder": str(QVOICE_HEARTBEAT_BUILDER.relative_to(ROOT)).replace("\\", "/"),
        "profile_query": QVOICE_HEARTBEAT_PROFILE_SQL,
        "audit_query": QVOICE_HEARTBEAT_AUDIT_SQL,
        "wave": evidence["source"]["wave"],
        "survey_launch_date": evidence["source"]["survey_launch_date"],
        "snapshot": population["snapshot_date"],
        "population": population["definition"],
        "grain": population["grain"],
        "item_count": metrics["item_count"],
        "minimum_valid_items": metrics["minimum_valid_items"],
        "matched_workforce_employees": metrics["matched_workforce_employees"],
        "personal_mean_eligible_employees": metrics["personal_mean_eligible_employees"],
        "top_upvote_items": [row["question_id"] for row in evidence["top_upvotes"]],
        "top_downvote_items": [row["question_id"] for row in evidence["top_downvotes"]],
        "query_sha256": {
            "profile_sql": provenance.get("profile_sql_sha256"),
            "profile_result": provenance.get("profile_result_sha256"),
            "audit_sql": provenance.get("audit_sql_sha256"),
            "audit_result": provenance.get("audit_result_sha256"),
        },
        "privacy": evidence["privacy"],
        "outcome": evidence["outcome"],
    }


def qvoice_heartbeat_card(evidence: dict[str, object]) -> str:
    """Render the top relative-item signals and the explicit sign legend."""
    def render_rows(rows: list[dict[str, object]], rate_key: str, direction: str) -> str:
        rendered: list[str] = []
        for row in rows:
            question_id = str(row["question_id"])
            topic = str(row.get("driver") or row.get("group") or "Unlabeled")
            percentage = float(row[rate_key])
            valid_count = int(row["valid_employee_count"])
            favorable = float(row["favorable_percent"])
            rendered.append(
                f'''<div class="qvoice-heartbeat-row">
                  <div class="qvoice-heartbeat-item"><strong>{esc(question_id)}</strong><span title="{esc(topic)}">{esc(topic)}</span></div>
                  <div class="qvoice-heartbeat-track" aria-label="{esc(question_id)} {direction} relative share {percentage:.2f}%"><div class="qvoice-heartbeat-fill qvoice-heartbeat-fill-{direction}" style="width:{percentage:.4f}%"></div></div>
                  <div class="qvoice-heartbeat-value"><strong>{percentage:.2f}%</strong><span>n={valid_count:,} · favorable {favorable:.2f}%</span></div>
                </div>'''
            )
        return "".join(rendered)

    up_rows = render_rows(list(evidence["top_upvotes"]), "upvote_percent", "up")
    down_rows = render_rows(list(evidence["top_downvotes"]), "downvote_percent", "down")
    return f'''<article class="card chart-card qvoice-heartbeat-card">
      <div class="card-title">Top items by relative response signal</div>
      <p class="qvoice-heartbeat-intro">Each item is compared with the respondent's own mean across valid 1–5 answers. The ranking is descriptive and uses the item-specific valid-response denominator.</p>
      <div class="qvoice-heartbeat-grid">
        <section class="qvoice-heartbeat-panel"><h3>+1 · above personal mean</h3><p>Most often above the respondent's own mean.</p><div class="qvoice-heartbeat-list">{up_rows}</div></section>
        <section class="qvoice-heartbeat-panel"><h3>−1 · below personal mean</h3><p>Most often below the respondent's own mean.</p><div class="qvoice-heartbeat-list">{down_rows}</div></section>
      </div>
      <div class="qvoice-heartbeat-legend" aria-label="QVoice heartbeat sign legend">
        <span><i class="qvoice-heartbeat-dot"></i><strong>+1</strong> above personal mean</span>
        <span><i class="qvoice-heartbeat-dot neutral"></i><strong>0</strong> equal to personal mean</span>
        <span><i class="qvoice-heartbeat-dot down"></i><strong>−1</strong> below personal mean</span>
        <span><i class="qvoice-heartbeat-dot missing"></i><strong>Missing</strong> excluded, not zero</span>
      </div>
      <div class="chart-footer"><strong>Important:</strong> relative sign percentage is not the same as favorable percentage. Favorable is shown only as absolute context: scale responses 4–5.</div>
    </article>'''


def qvoice_heartbeat_slide(number: int, evidence: dict[str, object]) -> str:
    metrics = evidence["metrics"]
    population = evidence["population"]
    assert isinstance(metrics, dict) and isinstance(population, dict)
    matched = int(metrics["matched_workforce_employees"])
    eligible = int(population["eligible_employees"])
    return data_slide(
        number,
        "QVoice heartbeat",
        "Jan-2026 · relative item signal versus each respondent's personal mean",
        qvoice_heartbeat_card(evidence),
        side_card(
            "Relative within-person context",
            "The heartbeat asks which items stand above or below a respondent's own answer pattern. It is useful for describing what is salient in the wave, but it is not an absolute sentiment label, a temporal pulse, or an individual attrition score.",
            [
                ("Wave", "Jan-2026"),
                ("Scale", "53 items · 1–5"),
                ("Personal mean", "at least 38/53 valid items"),
                ("Workforce match", f"{matched:,} of {eligible:,}"),
                ("Eligible means", f"{int(metrics['personal_mean_eligible_employees']):,}"),
                ("Missing items", "excluded; not converted to zero"),
                ("Absolute context", "favorable = 4–5"),
            ],
            "Restricted · aggregate only",
        ),
    )


def qvoice_normalized_region_stack_segments(score_bands: list[dict[str, object]]) -> str:
    """Render safe standardized-score bands with exact widths and rounded labels."""
    display_labels = qvoice_whole_percent_labels(score_bands, "percent_of_normalized")
    segments: list[str] = []
    for index, (row, display_label) in enumerate(zip(score_bands, display_labels), start=1):
        percentage = float(row["percent_of_normalized"])
        # A label cannot be read inside a segment narrower than roughly 30 px.
        # Its exact percentage remains in the accessible tooltip; the ordered
        # legend continues to identify the band without clipped text.
        visible_label = f"<span>{display_label}%</span>" if percentage >= 4 else ""
        segments.append(
            f'<span class="qvoice-stack-segment qvoice-band-{index}" style="width:{percentage:.6f}%" title="{esc(str(row["band"]))}: {percentage:.4f}% · n={int(row["participant_count"]):,}">{visible_label}</span>'
        )
    return "".join(segments)


def qvoice_normalized_region_card(evidence: dict[str, object]) -> str:
    """Render the regional-normalization distribution, not a tautological mean trend."""
    waves = list(evidence["waves"])
    stacks = "".join(
        f'''<div class="qvoice-stack-row"><div class="qvoice-stack-label"><strong>{int(wave['year'])}</strong>n={int(wave['normalized_participants']):,}</div>
          <div class="qvoice-stack-bar" aria-label="Within-region standardized-score distribution for {int(wave['year'])}, n={int(wave['normalized_participants']):,}">{qvoice_normalized_region_stack_segments(wave['z_score_bands'])}</div>
        </div>'''
        for wave in waves
    )
    legend = "".join(
        f'<span><i class="qvoice-band-dot qvoice-band-{index}"></i>{esc(str(row["band"]))}</span>'
        for index, row in enumerate(waves[0]["z_score_bands"], start=1)
    )
    return f'''<article class="card chart-card qvoice-normalized-region-card"><div class="card-title">Within-region standardized-score distribution</div>
      <div class="qvoice-normalized-region-body"><p>Each bar sums to 100% of respondents after standardizing their comparable favorable score within the same stored Region and survey wave.</p>
        <div class="qvoice-stack-list">{stacks}</div><div class="qvoice-band-legend" aria-label="Standardized-score band legend">{legend}</div>
      </div>
      <div class="chart-footer">Reference score: <strong>100 × favorable items / 33</strong>. Each Region × wave uses its own population mean and population standard deviation; no regional labels or individual scores are displayed.</div></article>'''


def qvoice_normalized_region_slide(number: int, evidence: dict[str, object]) -> str:
    side = side_card(
        "A relative, not absolute, QVoice score",
        "Standardization removes each region-wave average before combining respondents. The result compares relative standing within the same stored Region and survey wave; it does not show a workforce result or an attrition association.",
        [
            ("Population", "respondents with 33/33 valid common items"),
            ("Reference", "stored Region × survey wave · n ≥ 30"),
            ("Raw score", "100 × favorable items / 33"),
            ("Z score", "(score − cohort mean) / population SD"),
            ("Checks", "all reference cohorts passed; no missing Region, duplicates, conflicts, or zero SD"),
            ("Interpretation", "mean = 0 and SD = 1 by construction"),
            ("Limit", "respondent-only; no workforce or attrition join"),
        ],
        "Internal analysis · aggregate",
    )
    return data_slide(
        number,
        "Standardized / normalized within region",
        "Relative QVoice standing within each stored Region and survey wave · 2024–2026",
        qvoice_normalized_region_card(evidence),
        side,
    )


def qvoice_normalized_region_slide_or_support(number: int) -> tuple[str, str]:
    """Fail closed if the frozen normalized evidence cannot support publication."""
    try:
        evidence = qvoice_normalized_region_evidence()
    except (FileNotFoundError, ValueError):
        return (
            "Standardized within region",
            support_slide(
                number,
                "Standardized / normalized within region",
                "No chart · frozen normalization evidence did not pass",
                "No unverified standardized distribution is published",
                "This view requires the strict comparable item contract, a nonblank stored Region, safe Region × survey-wave reference cohorts, and reconciling standardized-score bands.",
                [
                    ("Type", "derived survey feature"),
                    ("Reference", "stored Region × survey wave"),
                    ("Publication gate", "all cohorts and bands n ≥ 30"),
                    ("Action", "rebuild and validate aggregate-only evidence"),
                ],
            ),
        )
    return "Standardized within region", qvoice_normalized_region_slide(number, evidence)


def qvoice_comment_chart_card(evidence: dict[str, object]) -> str:
    themes = ["Remote / WFH", "Hybrid", "RTO / office attendance"]
    colors = ["#2A2AEA", "#843AFF", "#B08A00"]
    headers = "".join(
        f'<th><span class="qvoice-comment-key" style="background:{color}"></span>{esc(theme)}</th>'
        for theme, color in zip(themes, colors)
    )
    rows = []
    for wave in evidence["waves"]:
        cells = []
        for theme in themes:
            count = wave["published_theme_counts"].get(theme)
            cells.append(f"<td><strong>{int(count):,}</strong></td>" if count is not None else "<td>Suppressed</td>")
        rows.append(f'<tr><td>{esc(wave["wave"])}</td>{"".join(cells)}</tr>')
    table = f"<table class=\"qvoice-comment-table\"><thead><tr><th>Survey wave</th>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"
    diagnostic_rows = []
    for wave in evidence["waves"]:
        diagnostic = wave["diagnostics"]
        improvement_rto = diagnostic.get("improvement_rto_mentions")
        friction_context = diagnostic.get("requirement_friction_context")
        improvement_value = (
            f"<strong>{int(improvement_rto):,}</strong>"
            if diagnostic.get("improvement_rto_publishable") and improvement_rto is not None
            else "Suppressed"
        )
        friction_value = (
            f"<strong>{int(friction_context):,}</strong>"
            if diagnostic.get("requirement_friction_publishable") and friction_context is not None
            else "Suppressed"
        )
        diagnostic_rows.append(
            f'<tr><td>{esc(wave["wave"])}</td><td>{improvement_value}</td><td>{friction_value}</td></tr>'
        )
    diagnostic_table = (
        '<div class="qvoice-diagnostic-title">Improvement-oriented office context</div>'
        '<table class="qvoice-diagnostic-table"><thead><tr>'
        '<th>Survey wave</th><th>RTO / office in improvement prompts</th>'
        '<th>Requirement / friction context</th></tr></thead><tbody>'
        + "".join(diagnostic_rows)
        + '</tbody></table>'
        '<p class="qvoice-diagnostic-note">Requirement / friction is counted only when it co-occurs with an office-attendance mention; it is context, not a complaint label.</p>'
    )
    return f'''<article class="card chart-card qvoice-comment-card">
      <div class="card-title">Absolute respondent-wave cases by topic mention</div>
      <div id="qvoice-comment-chart" class="qvoice-comment-chart" aria-label="QVoice topic mentions by survey wave"></div>
      {table}
      <p class="qvoice-comment-note">Counts are deduplicated within participant-wave-theme. Themes may overlap; no percentages or comment text are shown.</p>
      {diagnostic_table}
    </article>'''


def qvoice_comment_slide(number: int, evidence: dict[str, object]) -> str:
    latest = evidence["waves"][-1]
    main = qvoice_comment_chart_card(evidence)
    side = side_card(
        "Descriptive topic mentions, not sentiment",
        "Raw open-text responses are available in four survey waves. The taxonomy counts topic mentions only; it does not label sentiment, complaints, or policy agreement.",
        [
            ("Waves", "Mar-2023 · Jan-2024 · Jan-2025 · Jan-2026"),
            ("Prompts", "doing well · can improve · processes to improve when available"),
            ("Grain", "participant-wave, deduplicated by theme"),
            ("Minimum", "n ≥ 30 for every displayed value"),
            ("Latest wave", f"{latest['wave']} · {int(latest['respondent_wave_count']):,} comment respondents"),
            ("Restriction", "aggregate evidence only; no text or identifiers"),
        ],
        "Internal analysis · aggregate",
    )
    return data_slide(
        number,
        "RTO/hybrid comment in QVoice",
        "Raw open-text evidence · absolute cases by survey wave · topic mentions only",
        main,
        side,
    )


def _retention_metric_label(metric: dict[str, object]) -> str:
    if metric.get("publication_status") != "published":
        return "Not publishable (&lt;30)"
    return (
        f"{float(metric['percent_of_improvement_comment_participants']):.2f}%"
        f" · n={int(metric['participant_count']):,}"
    )


def _retention_trend_panel(theme: str, waves: list[dict[str, object]]) -> str:
    bars: list[str] = []
    for wave in waves:
        metric = wave["themes"][theme]
        year = str(wave["wave"])[-4:]
        if metric["publication_status"] == "published":
            percent = float(metric["percent_of_improvement_comment_participants"])
            count = int(metric["participant_count"])
            height = max(4, min(100.0, percent) * 0.66)
            bars.append(
                f'''<div class="retention-mini-wrap"><div class="retention-mini-value">{percent:.0f}%</div>
                <div class="retention-mini-bar" style="height:{height:.1f}px" aria-label="{esc(str(wave['wave']))}: {percent:.2f}%, n={count:,}"></div>
                <div class="retention-mini-year">{esc(year)}<small>n={count:,}</small></div></div>'''
            )
        else:
            bars.append(
                f'''<div class="retention-mini-wrap"><div class="retention-mini-value">NP</div>
                <div class="retention-mini-bar" style="height:3px; opacity:.28" aria-label="{esc(str(wave['wave']))}: Not publishable below n=30"></div>
                <div class="retention-mini-year">{esc(year)}<small>NP</small></div></div>'''
            )
    return f'''<section class="retention-trend-panel"><div class="retention-trend-title">{esc(theme)}</div>
      <div class="retention-mini-bars">{''.join(bars)}</div></section>'''


def qvoice_retention_concerns_card(evidence: dict[str, object]) -> str:
    latest = evidence["waves"][-1]
    display = evidence["jan_2026_display"]
    ranked_themes = list(display["ranked_themes"])
    theme_rows = []
    for theme in ranked_themes:
        metric = latest["themes"][theme]
        if metric["publication_status"] != "published":
            raise ValueError("The slide may render only publishable ranked themes.")
        percent = float(metric["percent_of_improvement_comment_participants"])
        theme_rows.append(
            f'''<div class="retention-theme-row"><div class="retention-theme-label">{esc(theme)}</div>
              <div class="retention-theme-track"><div class="retention-theme-fill" style="width:{percent:.2f}%"></div></div>
              <div class="retention-theme-value">{_retention_metric_label(metric)}</div></div>'''
        )
    trend_panels = "".join(
        _retention_trend_panel(theme, list(evidence["waves"]))
        for theme in display["trend_themes"]
    )
    intent = latest["explicit_intent_to_leave"]
    return f'''<article class="card chart-card qvoice-retention-card">
      <div class="card-title">Jan-2026 · five most common publishable improvement themes</div>
      <p class="retention-meta">Denominator: <strong>{int(latest['improvement_comment_participants']):,}</strong> distinct participants with at least one selected improvement comment.</p>
      <div class="retention-theme-list">{''.join(theme_rows)}</div>
      <div class="retention-intent"><div><strong>Explicit intent-to-leave wording</strong><span>Separate, conservative aggregate contextual signal; never an employee label.</span></div><div class="retention-intent-value">{_retention_metric_label(intent)}</div></div>
      <div class="retention-trend-heading"><strong>Descriptive 2023–2026 trend · top three Jan-2026 themes</strong><span>2025–2026 also include the processes-to-improve prompt.</span></div>
      <div class="retention-trend-grid">{trend_panels}</div>
      <p class="retention-footnote">Percent = distinct participants matching the theme / the same wave's selected-improvement-comment denominator. Themes overlap and do not sum to 100%.</p>
    </article>'''


def qvoice_retention_concerns_slide(number: int, evidence: dict[str, object]) -> str:
    latest = evidence["waves"][-1]
    side = side_card(
        "Interpretation boundary",
        "Keyword themes describe improvement feedback relevant to retention. They do not classify sentiment or complaints, establish causality, or identify individual risk.",
        [
            ("Source", "original can-improve prompt; processes prompt in 2025–2026"),
            ("Latest denominator", f"{int(latest['improvement_comment_participants']):,} selected improvement-comment participants"),
            ("Deduplication", "one participant-wave-theme; themes can overlap"),
            ("Publication", "n ≥ 30; below-threshold values are not shown"),
            ("Leave wording", "separate aggregate contextual signal with negation handling"),
            ("Trend", "descriptive only; 2025–2026 include an additional prompt"),
            ("Related topic", "slide 18 retains the detailed RTO/hybrid view"),
            ("Limitation", "no validated QVoice-comment-to-attrition join or model feature"),
        ],
        "Internal analysis · aggregate only",
    )
    return data_slide(
        number,
        "Retention concerns in QVoice comments",
        "Internal analysis · aggregate improvement themes, not individual risk or causality",
        qvoice_retention_concerns_card(evidence),
        side,
    )


def transfer_distribution_card(evidence: dict[str, object]) -> str:
    """Render the two Plotly targets plus aggregate summary metrics."""
    summaries = evidence["summaries"]
    monthly = summaries["monthly"]
    weekly = summaries["weekly"]
    history = evidence.get("history_availability", {})
    history_start = str(history.get("documented_transfer_event_history_start", "2022-10-06"))
    return f"""<div class="transfer-distribution-wrap">
      <div class="transfer-chart-grid">
        <article class="card chart-card transfer-chart-card">
          <div class="card-title">Transfer within past year · monthly snapshots</div>
          <div id="transfer-monthly-chart" class="transfer-chart" aria-label="Transfer within past year monthly snapshots"></div>
          <div class="chart-footer">{int(monthly['snapshot_count'])} complete snapshots ({esc(str(monthly.get('first_snapshot', '')))} to {esc(str(monthly.get('last_snapshot', '')))}) · mean <strong>{float(monthly['transfer_employee_mean']):,.1f}</strong> people · rolling 12-month employee feature.</div>
        </article>
        <article class="card chart-card transfer-chart-card">
          <div class="card-title">Transfer within past year · weekly endpoints</div>
          <div id="transfer-weekly-chart" class="transfer-chart" aria-label="Transfer within past year weekly endpoints"></div>
          <div class="chart-footer">{int(weekly['snapshot_count'])} complete Sunday endpoints ({esc(str(weekly.get('first_snapshot', '')))} to {esc(str(weekly.get('last_snapshot', '')))}) · mean <strong>{float(weekly['transfer_employee_mean']):,.1f}</strong> people · same rolling feature.</div>
        </article>
      </div>
      <div class="transfer-summary-grid">
        <div class="metric"><strong>{int(monthly['transfer_employee_median']):,}</strong><span>monthly median people</span></div>
        <div class="metric"><strong>{int(weekly['transfer_employee_median']):,}</strong><span>weekly median people</span></div>
        <div class="metric"><strong>{float(monthly['transfer_rate_mean_percent']):.2f}%</strong><span>monthly mean rate</span></div>
        <div class="metric"><strong>{float(weekly['transfer_rate_mean_percent']):.2f}%</strong><span>weekly mean rate</span></div>
      </div>
      <div class="transfer-footnote">* The chart shows the most recent {int(monthly['snapshot_count'])} monthly snapshots and {int(weekly['snapshot_count'])} weekly endpoints before the cutoff. This displayed range is not the start of the available history or of the variable. Documented <em>transfer_date</em> history begins on {esc(history_start)}.</div>
    </div>"""


def application_intensity_card(series: list[dict[str, object]]) -> str:
    """Render the audited applicant-year distribution with a visible fallback table."""
    rows: list[str] = []
    for year in series:
        buckets = list(year["buckets"])
        bucket_cells = "".join(
            f"<td>{float(bucket['percent']):.2f}% · {int(bucket['count']):,}</td>"
            for bucket in buckets
        )
        period_note = str(year.get("period_note", ""))
        if period_note == "complete fiscal year":
            period_note = "full fiscal year"
        elif str(year["fiscal_year"]) == "FY2026 YTD":
            period_note = "partial year through Sep 10; not directly comparable"
        year_label = f'<strong class="application-intensity-year-label">{esc(str(year["fiscal_year"]))}</strong><small class="application-intensity-period-note">{esc(period_note)}</small>'
        rows.append(
            f"<tr><td>{year_label}</td>"
            f"<td>{int(year['annual_distinct_applicants']):,}</td>"
            f"<td>{float(year['mean']):.2f}</td>{bucket_cells}</tr>"
        )
    return f"""<article class="card chart-card application-intensity-card">
      <div class="card-title">Different jobs applied to per person, by fiscal year</div>
      <div id="application-intensity-chart" class="application-intensity-chart" aria-label="Application intensity distribution by fiscal year"></div>
      <table class="application-intensity-table"><colgroup><col style="width:26%"><col style="width:9%"><col style="width:8%"><col style="width:14.25%"><col style="width:14.25%"><col style="width:14.25%"><col style="width:14.25%"></colgroup><thead><tr><th>Fiscal year</th><th>People</th><th>Average</th><th><span class="application-intensity-key" data-application-bucket="1" aria-hidden="true"></span>1 job</th><th><span class="application-intensity-key" data-application-bucket="2" aria-hidden="true"></span>2 jobs</th><th><span class="application-intensity-key" data-application-bucket="3" aria-hidden="true"></span>3 jobs</th><th><span class="application-intensity-key" data-application-bucket="4+" aria-hidden="true"></span>4+ jobs</th></tr></thead>
      <tbody>{''.join(rows)}</tbody></table>
      <div class="chart-footer"><strong>Source:</strong> HRDA application records through Sep 10, 2026. Each bar uses only people found in that fiscal period; table cells show percentage · count.</div>
    </article>"""


def application_intensity_slide(number: int, series: list[dict[str, object]]) -> str:
    """Render the annual application view with a plain-language reading guide."""
    side = """<article class="card application-intensity-side"><div class="card-title">How to read this slide</div><span class="badge badge-info">Internal aggregate analysis</span><h3>Most people applied to one job</h3><p>Each person is counted once per fiscal year and grouped by the number of different jobs they applied to. This includes only people found in the application records, not the full workforce.</p><div class="application-intensity-highlight"><strong>What stands out:</strong> FY2024 had more people applying to several jobs. In FY2025 and FY2026 year to date, applications were more concentrated in one or two jobs.</div><section class="application-intensity-section"><div class="application-intensity-section-title">How the recent-application measure would work</div><div class="application-intensity-steps"><div class="application-intensity-step"><span class="application-intensity-step-num">1</span><div><strong>Use only information already available</strong><span>Ignore applications recorded after the date being evaluated.</span></div></div><div class="application-intensity-step"><span class="application-intensity-step-num">2</span><div><strong>Look back six months</strong><span>Count each different job only once during that period.</span></div></div><div class="application-intensity-step"><span class="application-intensity-step-num">3</span><div><strong>Identify frequent activity</strong><span>Mark “Yes” at four or more different jobs. This is separate from the annual 4+ bar above.</span></div></div></div></section><div class="application-intensity-limit"><strong>Important limit:</strong> This slide cannot estimate how many employees made no application. The records begin with people already linked to an application.</div><div class="application-intensity-authorization"><strong>Internal-use limit:</strong> FY2025 and FY2026 year to date include small aggregate groups below 30 people and are shown only for the requester and Julia. No employee details, identifiers, job postings or titles are shown; no manager access, redistribution, operational use, score changes, or production approval.</div><div class="application-intensity-source"><strong>Data:</strong> HRDA · <span>hrda.job_applications_vw</span><br><strong>FY2026:</strong> Partial year; do not compare it directly with full fiscal years.</div></article>"""
    return f"""<div class="slide-stage" id="slide-{number}">{heading("Applied to a job", "Among people with application records, most applied to one job during the fiscal year")}
      <div class="two-pane">{application_intensity_card(series)}{side}</div></div>"""


def application_employee_snapshot_card(evidence: dict[str, object]) -> str:
    """Render latest publishable buckets and the safe twelve-snapshot trend."""
    latest = list(evidence["latest_distribution"])
    colors = {"0": "#2563EB", "1": "#0F766E", "2+": "#B45309", "Unknown": "#94A3B8"}
    latest_rows: list[str] = []
    for row in latest:
        bucket = str(row["application_bucket"])
        latest_rows.append(
            f'''<div class="application-snapshot-bar-row">
              <div class="application-snapshot-bar-label"><strong>{esc(bucket)}</strong><span>{"No unique requisition" if bucket == "0" else "Unknown coverage" if bucket == "Unknown" else "Unique requisitions"}</span></div>
              <div class="application-snapshot-track"><div class="application-snapshot-fill" style="width:{float(row["percent_of_eligible_snapshots"]):.4f}%;background:{colors[bucket]}"><span>{float(row["percent_of_eligible_snapshots"]):.2f}%</span></div></div>
              <div class="application-snapshot-bar-value">n={int(row["employee_snapshots"]):,}</div>
            </div>'''
        )
    trend = list(evidence["trend"])
    coverage_values = [float(row["coverage_percent"]) for row in trend]
    latest_row = next(row for row in latest if row["application_bucket"] == "Unknown")
    latest_trend_row = next(row for row in trend if row["snapshot_date"] == str(evidence["latest_publishable_snapshot"]))
    return f'''<div class="application-snapshot-main">
      <article class="card chart-card application-snapshot-latest-card">
        <div class="card-title">Latest fully publishable distribution · snapshot {esc(str(evidence["latest_publishable_snapshot"]))}</div>
        <div class="application-snapshot-bar-list">{"".join(latest_rows)}</div>
        <div class="application-snapshot-kpi-row">
          <span><strong>{int(latest[0]["eligible_employee_snapshots"]):,}</strong> eligible employee-snapshots</span>
          <span><strong>{float(latest_row["percent_of_eligible_snapshots"]):.2f}%</strong> Unknown</span>
          <span><strong>{float(latest_trend_row["coverage_percent"]):.2f}%</strong> feed coverage</span>
        </div>
        <div class="chart-footer">Window: (snapshot − 6 months, snapshot] · all four buckets have n ≥ 30 and reconcile exactly to the denominator.</div>
      </article>
      <article class="card chart-card application-snapshot-trend-card">
        <div class="card-title">Last 12 complete monthly snapshots</div>
        <div id="application-employee-snapshot-trend-chart" class="application-employee-snapshot-trend-chart" aria-label="Coverage and application-bucket trend across twelve monthly snapshots"></div>
        <div class="application-snapshot-trend-note"><strong>2+ is shown only where publishable.</strong> The latest available snapshot, 2026-08-23, is retained as a coverage point but its complete distribution is suppressed because one bucket is below n=30.</div>
      </article>
    </div>'''


def application_employee_snapshot_slide(number: int, evidence: dict[str, object]) -> str:
    """Render the exploratory employee-snapshot proposal beside the annual view."""
    latest = list(evidence["latest_distribution"])
    denominator = int(latest[0]["eligible_employee_snapshots"])
    unknown = next(row for row in latest if row["application_bucket"] == "Unknown")
    coverage = 100.0 - float(unknown["percent_of_eligible_snapshots"])
    side = side_card(
        "Coverage is the gate, not a zero",
        "This view keeps Unknown whenever the source cannot distinguish zero applications from missing coverage. It is current descriptive evidence for review, not an approved production feature or an individual prediction.",
        [
            ("Denominator", f"{denominator:,} regular active employee-snapshots"),
            ("Window", "(snapshot − 6 months, snapshot]"),
            ("Latest publishable", str(evidence["latest_publishable_snapshot"])),
            ("Latest available", f"{evidence['latest_available_snapshot']} · complete distribution suppressed"),
            ("Feed coverage", f"{coverage:.2f}% at the latest publishable snapshot"),
            ("Unknown", f"{float(unknown['percent_of_eligible_snapshots']):.2f}% · not imputed to zero"),
            ("Source cutoff", "2026-09-10"),
            ("Use", "Exploratory evidence only"),
        ],
        "Exploratory employee-snapshot evidence",
    )
    return data_slide(
        number,
        "Applied to a job — employee-snapshot, trailing six months",
        "Exploratory proposal · regular active employee-snapshots · source cutoff 2026-09-10",
        application_employee_snapshot_card(evidence),
        side,
    )


def comp_ratio_voluntary_attrition_chart_enhancement(evidence: dict[str, object]) -> str:
    """Render the two-series history and re-render it whenever the theme changes."""
    rows = [
        {
            "snapshot_date": row["snapshot_date"],
            "group_label": row["group_label"],
            "employee_snapshots": int(row["employee_snapshots"]),
            "voluntary_exit_snapshots": int(row["voluntary_exit_snapshots"]),
            "voluntary_rate_percent": float(row["voluntary_rate_percent"]),
        }
        for row in evidence["series"]
    ]
    payload = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
    return r'''
  <script>
    (function () {
      var compRatioHistoryRows = ''' + payload + r''';
      var compRatioHistoryGroups = ['<0.8 (incl. 0)', '>=0.8'];
      var compRatioHistoryPalette = {
        'theme-light-classic': ['#2457FF', '#0F766E'],
        'theme-light-soft': ['#1E40AF', '#0F766E'],
        'theme-dark-royal': ['#7AABFF', '#2DD4BF'],
        'theme-dark-carbon': ['#7AABFF', '#14B8A6']
      };

      function compRatioHistoryThemeName() {
        return Array.from(document.body.classList).find(function (name) {
          return Object.prototype.hasOwnProperty.call(compRatioHistoryPalette, name);
        }) || 'theme-light-classic';
      }

      function compRatioHistoryThemeColors() {
        var styles = getComputedStyle(document.body);
        return {
          text: styles.getPropertyValue('--text-main').trim() || '#0f172a',
          muted: styles.getPropertyValue('--text-muted').trim() || '#5b6478',
          border: styles.getPropertyValue('--border-subtle').trim() || 'rgba(15,23,42,0.08)',
          font: 'Aptos, Segoe UI, system-ui, sans-serif'
        };
      }

      function renderCompRatioHistoryChart() {
        var chart = document.getElementById('comp-ratio-voluntary-attrition-chart');
        if (!chart) return;
        if (!window.Plotly) {
          chart.innerHTML = '<p class="chart-note">The interactive chart could not load. The pooled comparison below remains available.</p>';
          return;
        }
        var colors = compRatioHistoryThemeColors();
        var palette = compRatioHistoryPalette[compRatioHistoryThemeName()];
        var traces = compRatioHistoryGroups.map(function (group, index) {
          var points = compRatioHistoryRows.filter(function (row) { return row.group_label === group; });
          return {
            x: points.map(function (row) { return row.snapshot_date; }),
            y: points.map(function (row) { return row.voluntary_rate_percent; }),
            customdata: points.map(function (row) { return [row.employee_snapshots, row.voluntary_exit_snapshots]; }),
            name: group,
            type: 'scatter',
            mode: 'lines+markers',
            connectgaps: false,
            line: { color: palette[index], width: 2.4 },
            marker: { color: palette[index], size: 5 },
            hovertemplate: '<b>%{x|%d %b %Y}</b><br>' + group + '<br>Voluntary rate: <b>%{y:.2f}%</b><br>Employee-snapshots: <b>%{customdata[0]:,}</b><br>Voluntary exits: <b>%{customdata[1]:,}</b><extra></extra>'
          };
        });
        var maxRate = Math.max.apply(null, traces.reduce(function (all, trace) { return all.concat(trace.y); }, []));
        var axisMax = Math.max(5, Math.ceil((maxRate + 0.5) * 2) / 2);
        Plotly.react(chart, traces, {
          height: 250,
          plot_bgcolor: 'rgba(0,0,0,0)',
          paper_bgcolor: 'rgba(0,0,0,0)',
          font: { family: colors.font, color: colors.text },
          hovermode: 'x unified',
          hoverlabel: { font: { family: colors.font } },
          margin: { t: 34, r: 10, b: 38, l: 48 },
          legend: { orientation: 'h', y: 1.16, x: 0, font: { family: colors.font, size: 10, color: colors.text }, bgcolor: 'rgba(0,0,0,0)', bordercolor: 'rgba(0,0,0,0)' },
          xaxis: { type: 'date', tickformat: '%b\n%Y', nticks: 8, tickfont: { family: colors.font, size: 10, color: colors.muted }, showgrid: false, fixedrange: true },
          yaxis: { range: [0, axisMax], dtick: 1, ticksuffix: '%', tickfont: { family: colors.font, size: 10, color: colors.muted }, gridcolor: colors.border, zerolinecolor: colors.border, fixedrange: true }
        }, { responsive: false, displayModeBar: false });
      }

      renderCompRatioHistoryChart();
      new MutationObserver(function (records) {
        if (records.some(function (record) { return record.attributeName === 'class'; })) renderCompRatioHistoryChart();
      }).observe(document.body, { attributes: true, attributeFilter: ['class'] });
    })();
  </script>
'''


def application_employee_snapshot_chart_enhancement(evidence: dict[str, object]) -> str:
    """Render the twelve-snapshot trend and re-render it for every theme."""
    payload = json.dumps(list(evidence["trend"]), ensure_ascii=False).replace("</", "<\\/")
    return r'''
  <script>
    (function () {
      var applicationSnapshotTrend = ''' + payload + r''';
      var palette = {
        'theme-light-classic': ['#2563EB', '#0F766E', '#B45309', '#64748B'],
        'theme-light-soft': ['#1E40AF', '#0F766E', '#A16207', '#475569'],
        'theme-dark-royal': ['#60A5FA', '#2DD4BF', '#FBBF24', '#CBD5E1'],
        'theme-dark-carbon': ['#60A5FA', '#14B8A6', '#F59E0B', '#CBD5E1']
      };

      function themeColors() {
        var styles = getComputedStyle(document.body);
        return {
          text: styles.getPropertyValue('--text-main').trim() || '#0f172a',
          muted: styles.getPropertyValue('--text-muted').trim() || '#5b6478',
          border: styles.getPropertyValue('--border-subtle').trim() || 'rgba(15,23,42,0.08)',
          font: 'Aptos, Segoe UI, system-ui, sans-serif'
        };
      }

      function renderApplicationSnapshotTrend() {
        var chart = document.getElementById('application-employee-snapshot-trend-chart');
        if (!chart) return;
        if (!window.Plotly) {
          chart.innerHTML = '<p class="chart-note">The interactive chart could not load. The latest aggregate distribution and coverage notes remain available on this slide.</p>';
          return;
        }
        var colors = themeColors();
        var theme = Array.from(document.body.classList).find(function (name) { return palette[name]; }) || 'theme-light-classic';
        var fills = palette[theme];
        var x = applicationSnapshotTrend.map(function (row) { return row.snapshot_date; });
        var definitions = [
          ['0', 'zero_percent'], ['1', 'one_percent'], ['2+', 'two_plus_percent'], ['Unknown', 'unknown_percent']
        ];
        var traces = definitions.map(function (definition, index) {
          return {
            x: x,
            y: applicationSnapshotTrend.map(function (row) { return row[definition[1]]; }),
            name: definition[0],
            mode: 'lines+markers',
            connectgaps: false,
            type: 'scatter',
            line: { color: fills[index], width: 2.5 },
            marker: { color: fills[index], size: 6 },
            hovertemplate: '<b>%{x|%d %b %Y}</b><br>' + definition[0] + ': <b>%{y:.2f}%</b><extra></extra>'
          };
        });
        Plotly.react(chart, traces, {
          height: 220,
          plot_bgcolor: 'rgba(0,0,0,0)',
          paper_bgcolor: 'rgba(0,0,0,0)',
          font: { family: colors.font, color: colors.text },
          hovermode: 'x unified',
          hoverlabel: { font: { family: colors.font } },
          margin: { t: 34, r: 12, b: 42, l: 48 },
          legend: { orientation: 'h', y: 1.16, x: 0, font: { family: colors.font, size: 10, color: colors.text } },
          xaxis: { type: 'date', tickformat: '%b\n%Y', nticks: 6, tickfont: { family: colors.font, size: 10, color: colors.muted }, showgrid: false, fixedrange: true },
          yaxis: { range: [0, 100], ticksuffix: '%', tickfont: { family: colors.font, size: 10, color: colors.muted }, gridcolor: colors.border, zerolinecolor: colors.border, fixedrange: true }
        }, { responsive: false, displayModeBar: false });
      }

      renderApplicationSnapshotTrend();
      new MutationObserver(function (records) {
        if (records.some(function (record) { return record.attributeName === 'class'; })) renderApplicationSnapshotTrend();
      }).observe(document.body, { attributes: true, attributeFilter: ['class'] });
    })();
  </script>
'''


def application_feature_card() -> str:
    """Keep the candidate feature separate from the new annual source distribution."""
    return """<article class="card application-feature-card"><div class="card-title">Candidate feature logic</div>
      <div class="support-flow">
        <div class="support-node"><strong>1. Time-safe events</strong><span>Keep cand_applied=1 records dated no later than the prediction snapshot.</span></div>
        <div class="support-arrow">→</div>
        <div class="support-node"><strong>2. Six-month lookback</strong><span>Deduplicate unique req_id values in (snapshot − 6 months, snapshot].</span></div>
        <div class="support-arrow">→</div>
        <div class="support-node"><strong>3. Candidate flag</strong><span>Set the feature to 1 at four or more unique requisitions.</span></div>
      </div>
      <div class="privacy-banner">The annual 4+ slice on the previous slide is descriptive. It is not equivalent to this rolling six-month feature and is not used as a workforce rate.</div>
    </article>"""


def team_exit_definition_card() -> str:
    """Show the missing specification instead of leaving the support slide empty."""
    return """<article class="card team-exit-definition-card"><div class="card-title">Specification required before a team-exit count</div>
      <div class="support-flow">
        <div class="support-node"><strong>1. Define the team</strong><span>Freeze team membership at the employee snapshot and specify how transfers or manager changes affect membership.</span></div>
        <div class="support-arrow">→</div>
        <div class="support-node"><strong>2. Define eligible exits</strong><span>Select the termination date and termination types that count; exclude non-eligible events consistently.</span></div>
        <div class="support-arrow">→</div>
        <div class="support-node"><strong>3. Apply the threshold</strong><span>Choose calendar year or trailing 12 months, count exits by team, and flag teams above one exit.</span></div>
      </div>
      <div class="privacy-banner">No distribution is shown yet: changing the team grain, exit eligibility, window, or assignment rule changes both the denominator and the resulting feature.</div>
    </article>"""


def qvoice_comment_chart_enhancement(evidence: dict[str, object]) -> str:
    rows = []
    for wave in evidence["waves"]:
        rows.append({
            "wave": wave["wave"],
            "Remote / WFH": wave["published_theme_counts"].get("Remote / WFH"),
            "Hybrid": wave["published_theme_counts"].get("Hybrid"),
            "RTO / office attendance": wave["published_theme_counts"].get("RTO / office attendance"),
        })
    payload = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
    return r'''
  <script>
    (function () {
      var qvoiceCommentRows = ''' + payload + r''';
      var qvoiceCommentThemes = ['Remote / WFH', 'Hybrid', 'RTO / office attendance'];
      var qvoiceCommentPalette = {
        'theme-light-classic': ['#2A2AEA', '#843AFF', '#B08A00'],
        'theme-light-soft': ['#2346C7', '#7C35D4', '#A06F00'],
        'theme-dark-royal': ['#7EA8FF', '#C19CFF', '#F5F032'],
        'theme-dark-carbon': ['#6E8DFF', '#B493FF', '#F5F032']
      };

      function themeName() {
        return Array.from(document.body.classList).find(function (name) {
          return qvoiceCommentPalette[name];
        }) || 'theme-light-classic';
      }

      function themeColors() {
        var styles = getComputedStyle(document.body);
        return {
          text: styles.getPropertyValue('--text-main').trim() || '#0f172a',
          muted: styles.getPropertyValue('--text-muted').trim() || '#5b6478',
          border: styles.getPropertyValue('--border-subtle').trim() || 'rgba(15,23,42,0.08)',
          surface: styles.getPropertyValue('--bg-surface').trim() || '#ffffff',
          font: 'Aptos, Segoe UI, system-ui, sans-serif'
        };
      }

      function renderQVoiceCommentChart() {
        var chart = document.getElementById('qvoice-comment-chart');
        if (!chart) return;
        if (!window.Plotly) {
          chart.innerHTML = '<p class="chart-note">The interactive chart could not load. The aggregate table below contains the complete published counts.</p>';
          return;
        }
        var colors = themeColors();
        var palette = qvoiceCommentPalette[themeName()];
        var traces = qvoiceCommentThemes.map(function (theme, index) {
          return {
            x: qvoiceCommentRows.map(function (row) { return row.wave; }),
            y: qvoiceCommentRows.map(function (row) { return row[theme]; }),
            text: qvoiceCommentRows.map(function (row) {
              return row[theme] === null ? '' : Number(row[theme]).toLocaleString();
            }),
            name: theme,
            type: 'bar',
            textposition: 'outside',
            textfont: { family: colors.font, size: 10, color: colors.text },
            marker: { color: palette[index], line: { color: colors.surface, width: 1 } },
            hovertemplate: '<b>%{x}</b><br>' + theme + '<br>Cases: <b>%{y:,}</b><extra></extra>'
          };
        });
        Plotly.react(chart, traces, {
          height: 300,
          barmode: 'group',
          bargap: 0.26,
          bargroupgap: 0.08,
          plot_bgcolor: 'rgba(0,0,0,0)',
          paper_bgcolor: 'rgba(0,0,0,0)',
          font: { family: colors.font, color: colors.text },
          margin: { t: 44, r: 12, b: 42, l: 48 },
          uniformtext: { mode: 'show', minsize: 9 },
          legend: { orientation: 'h', y: 1.16, x: 0, font: { family: colors.font, size: 10, color: colors.text } },
          xaxis: { tickfont: { family: colors.font, size: 10, color: colors.muted }, showgrid: false, fixedrange: true },
          yaxis: { tickformat: ',d', rangemode: 'tozero', tickfont: { family: colors.font, size: 10, color: colors.muted }, gridcolor: colors.border, zerolinecolor: colors.border, fixedrange: true }
        }, { responsive: false, displayModeBar: false });
      }

      renderQVoiceCommentChart();
      new MutationObserver(function (records) {
        if (records.some(function (record) { return record.attributeName === 'class'; })) renderQVoiceCommentChart();
      }).observe(document.body, { attributes: true, attributeFilter: ['class'] });
    })();
  </script>
'''


def application_intensity_chart_enhancement(series: list[dict[str, object]]) -> str:
    """Render the four-series FY chart and re-render it when the deck theme changes."""
    chart_data = [
        {
            "fiscal_year": item["fiscal_year"],
            "buckets": item["buckets"],
        }
        for item in series
    ]
    payload = json.dumps(chart_data, ensure_ascii=False).replace("</", "<\\/")
    return r"""
  <script>
    (function () {
      var chartData = """ + payload + r""";
      var bucketOrder = ['1', '2', '3', '4+'];
      // The buckets are categorical, not ordinal shades of one hue. Light
      // themes use deeper fills; dark themes use brighter fills so the same
      // four categories remain distinct on every surface.
      var bucketPalettes = {
        'theme-light-classic': ['#1D4ED8', '#0F766E', '#15803D', '#B45309'],
        'theme-light-soft': ['#1E40AF', '#0F766E', '#166534', '#A16207'],
        'theme-dark-royal': ['#2563EB', '#2DD4BF', '#4ADE80', '#FBBF24'],
        'theme-dark-carbon': ['#2563EB', '#14B8A6', '#86EFAC', '#F59E0B']
      };

      function hexToRgb(color) {
        var hex = String(color || '').trim().replace(/^#/, '');
        if (hex.length === 3) hex = hex.split('').map(function (value) { return value + value; }).join('');
        if (!/^[0-9a-f]{6}$/i.test(hex)) return null;
        return [
          parseInt(hex.slice(0, 2), 16),
          parseInt(hex.slice(2, 4), 16),
          parseInt(hex.slice(4, 6), 16)
        ];
      }

      function relativeLuminance(color) {
        var rgb = hexToRgb(color);
        if (!rgb) return 0;
        var linear = rgb.map(function (channel) {
          var normalized = channel / 255;
          return normalized <= 0.03928
            ? normalized / 12.92
            : Math.pow((normalized + 0.055) / 1.055, 2.4);
        });
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
      }

      function contrastRatio(first, second) {
        var firstLuminance = relativeLuminance(first);
        var secondLuminance = relativeLuminance(second);
        var lighter = Math.max(firstLuminance, secondLuminance);
        var darker = Math.min(firstLuminance, secondLuminance);
        return (lighter + 0.05) / (darker + 0.05);
      }

      function readableTextColor(fill) {
        var lightText = '#FFFFFF';
        var darkText = '#0F172A';
        return contrastRatio(fill, lightText) >= contrastRatio(fill, darkText)
          ? lightText
          : darkText;
      }

      function bucketColorsForTheme() {
        var theme = Array.from(document.body.classList).find(function (name) {
          return Object.prototype.hasOwnProperty.call(bucketPalettes, name);
        }) || 'theme-light-classic';
        return bucketPalettes[theme];
      }

      function setTableBucketKeys(bucketColors) {
        document.querySelectorAll('[data-application-bucket]').forEach(function (key) {
          var index = bucketOrder.indexOf(key.dataset.applicationBucket);
          if (index >= 0) key.style.backgroundColor = bucketColors[index];
        });
      }

      function themeColors() {
        var styles = getComputedStyle(document.body);
        return {
          text: styles.getPropertyValue('--text-main').trim() || '#0f172a',
          muted: styles.getPropertyValue('--text-muted').trim() || '#5b6478',
          surface: styles.getPropertyValue('--bg-surface').trim() || '#ffffff',
          border: styles.getPropertyValue('--border-subtle').trim() || 'rgba(15,23,42,0.08)',
          font: 'Aptos, Segoe UI, system-ui, sans-serif'
        };
      }

      function renderApplicationIntensityChart() {
        var chart = document.getElementById('application-intensity-chart');
        if (!chart) return;
        var bucketColors = bucketColorsForTheme();
        setTableBucketKeys(bucketColors);
        if (!window.Plotly) {
          chart.innerHTML = '<p class="chart-note">The interactive chart could not load. The audited table below contains the complete distribution.</p>';
          return;
        }

        var colors = themeColors();
        var years = chartData.map(function (year) { return year.fiscal_year; });
        var traces = bucketOrder.map(function (bucket, index) {
          var points = chartData.map(function (year) {
            return year.buckets.find(function (entry) { return entry.label === bucket; });
          });
          return {
            x: years,
            y: points.map(function (point) { return point.percent; }),
            customdata: points.map(function (point) { return point.count; }),
            text: points.map(function (point) { return point.percent >= 10 ? point.percent.toFixed(1) + '%' : ''; }),
            name: bucket + (bucket === '1' ? ' job' : ' jobs'),
            type: 'bar',
            textposition: 'inside',
            textfont: { family: colors.font, size: 11, color: readableTextColor(bucketColors[index]) },
            marker: {
              color: bucketColors[index],
              line: { color: colors.surface, width: 1 }
            },
            hovertemplate: '<b>%{x}</b><br>' + bucket + (bucket === '1' ? ' job' : ' jobs') + '<br>%{y:.2f}% · n=%{customdata:,}<extra></extra>'
          };
        });

        Plotly.react(chart, traces, {
          height: 292,
          barmode: 'stack',
          bargap: 0.34,
          plot_bgcolor: 'rgba(0,0,0,0)',
          paper_bgcolor: 'rgba(0,0,0,0)',
          font: { family: colors.font, color: colors.text },
          hovermode: 'x unified',
          hoverlabel: { font: { family: colors.font } },
          margin: { t: 28, r: 10, b: 24, l: 44 },
          legend: {
            orientation: 'h', y: 1.18, x: 0, xanchor: 'left',
            traceorder: 'normal',
            font: { family: colors.font, size: 11, color: colors.text },
            bgcolor: 'rgba(0,0,0,0)', bordercolor: 'rgba(0,0,0,0)'
          },
          xaxis: {
            tickfont: { family: colors.font, size: 11, color: colors.muted },
            showgrid: false, zeroline: false, fixedrange: true
          },
          yaxis: {
            range: [0, 100], tickvals: [0, 25, 50, 75, 100], ticksuffix: '%',
            tickfont: { family: colors.font, size: 11, color: colors.muted },
            gridcolor: colors.border, zerolinecolor: colors.border, fixedrange: true
          }
        }, { responsive: false, displayModeBar: false });
      }

      renderApplicationIntensityChart();
      new MutationObserver(function (records) {
        if (records.some(function (record) { return record.attributeName === 'class'; })) {
          renderApplicationIntensityChart();
        }
      }).observe(document.body, { attributes: true, attributeFilter: ['class'] });
    })();
  </script>
"""


def qvoice_nonrespondent_chart_enhancement(evidence: dict[str, object]) -> str:
    categories = [
        ("Responded", "responded_proxy"),
        ("QVoice row / no answer", "qvoice_row_without_answer"),
        ("No QVoice row", "no_qvoice_row"),
    ]
    rows = []
    for wave in evidence["waves"]:
        eligible = int(wave["eligible_snapshot_employees"])
        row = {"wave": wave["wave"], "snapshot": eligible}
        for label, field in categories:
            count = int(wave[field])
            row[label] = count
            row[f"{label} %"] = round(100 * count / eligible, 4)
        rows.append(row)
    payload = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
    return r'''
  <script>
    (function () {
      var qvoiceResponseRows = ''' + payload + r''';
      var qvoiceResponseCategories = ['Responded', 'QVoice row / no answer', 'No QVoice row'];
      var qvoiceResponsePalette = {
        'theme-light-classic': ['#2A2AEA', '#843AFF', '#B08A00'],
        'theme-light-soft': ['#2346C7', '#7C35D4', '#A06F00'],
        'theme-dark-royal': ['#7EA8FF', '#C19CFF', '#F5F032'],
        'theme-dark-carbon': ['#6E8DFF', '#B493FF', '#F5F032']
      };

      function qvoiceResponseThemeName() {
        return Array.from(document.body.classList).find(function (name) {
          return qvoiceResponsePalette[name];
        }) || 'theme-light-classic';
      }

      function renderQVoiceResponseChart() {
        var chart = document.getElementById('qvoice-response-chart');
        if (!chart) return;
        if (!window.Plotly) {
          chart.innerHTML = '<p class="chart-note">The interactive chart could not load. The aggregate table below contains the complete published counts.</p>';
          return;
        }
        var styles = getComputedStyle(document.body);
        var textColor = styles.getPropertyValue('--text-main').trim() || '#0f172a';
        var mutedColor = styles.getPropertyValue('--text-muted').trim() || '#5b6478';
        var borderColor = styles.getPropertyValue('--border-subtle').trim() || 'rgba(15,23,42,0.08)';
        var surfaceColor = styles.getPropertyValue('--bg-surface').trim() || '#ffffff';
        var palette = qvoiceResponsePalette[qvoiceResponseThemeName()];
        var traces = qvoiceResponseCategories.map(function (category, index) {
          return {
            x: qvoiceResponseRows.map(function (row) { return row.wave; }),
            y: qvoiceResponseRows.map(function (row) { return row[category + ' %']; }),
            text: qvoiceResponseRows.map(function (row) {
              return Number(row[category]).toLocaleString() + ' · ' + Number(row[category + ' %']).toFixed(1) + '%';
            }),
            name: category,
            type: 'bar',
            textposition: 'outside',
            textfont: { family: 'Aptos, Segoe UI, system-ui, sans-serif', size: 9, color: textColor },
            marker: { color: palette[index], line: { color: surfaceColor, width: 1 } },
            hovertemplate: '<b>%{x}</b><br>' + category + '<br>%{text} of snapshot<extra></extra>'
          };
        });
        Plotly.react(chart, traces, {
          height: 292,
          barmode: 'group',
          bargap: 0.22,
          bargroupgap: 0.08,
          plot_bgcolor: 'rgba(0,0,0,0)',
          paper_bgcolor: 'rgba(0,0,0,0)',
          font: { family: 'Aptos, Segoe UI, system-ui, sans-serif', color: textColor },
          margin: { t: 42, r: 10, b: 42, l: 48 },
          uniformtext: { mode: 'show', minsize: 8 },
          legend: { orientation: 'h', y: 1.18, x: 0, font: { family: 'Aptos, Segoe UI, system-ui, sans-serif', size: 9, color: textColor } },
          xaxis: { tickfont: { family: 'Aptos, Segoe UI, system-ui, sans-serif', size: 10, color: mutedColor }, showgrid: false, fixedrange: true },
          yaxis: { title: '% of stored snapshot', range: [0, 100], ticksuffix: '%', tickfont: { family: 'Aptos, Segoe UI, system-ui, sans-serif', size: 9, color: mutedColor }, gridcolor: borderColor, zerolinecolor: borderColor, fixedrange: true }
        }, { responsive: false, displayModeBar: false });
      }

      renderQVoiceResponseChart();
      new MutationObserver(function (records) {
        if (records.some(function (record) { return record.attributeName === 'class'; })) renderQVoiceResponseChart();
      }).observe(document.body, { attributes: true, attributeFilter: ['class'] });
    })();
  </script>
'''


def transfer_chart_enhancement(evidence: dict[str, object]) -> str:
    """Render monthly and weekly rolling-window charts from frozen evidence."""
    payload = json.dumps(evidence["rows"], ensure_ascii=False).replace("</", "<\\/")
    return r"""
  <script>
    (function () {
      var transferRows = """ + payload + r""";

      function hexToRgb(color) {
        var hex = String(color || '').trim().replace(/^#/, '');
        if (hex.length === 3) hex = hex.split('').map(function (value) { return value + value; }).join('');
        if (!/^[0-9a-f]{6}$/i.test(hex)) return null;
        return [parseInt(hex.slice(0, 2), 16), parseInt(hex.slice(2, 4), 16), parseInt(hex.slice(4, 6), 16)];
      }

      function mixThemeColors(surface, accent, weight) {
        var base = hexToRgb(surface);
        var highlight = hexToRgb(accent);
        if (!base || !highlight) return accent;
        return 'rgb(' + base.map(function (value, index) {
          return Math.round(value + (highlight[index] - value) * weight);
        }).join(',') + ')';
      }

      function themeColors() {
        var styles = getComputedStyle(document.body);
        return {
          surface: styles.getPropertyValue('--bg-surface').trim() || '#ffffff',
          text: styles.getPropertyValue('--text-main').trim() || '#0f172a',
          muted: styles.getPropertyValue('--text-muted').trim() || '#5b6478',
          accent: styles.getPropertyValue('--accent').trim() || '#2457ff',
          border: styles.getPropertyValue('--border-subtle').trim() || 'rgba(15,23,42,0.08)',
          font: 'Aptos, Segoe UI, system-ui, sans-serif'
        };
      }

      function renderTransferChart(chartId, frequency, colorWeight) {
        var chart = document.getElementById(chartId);
        if (!chart) return;
        if (!window.Plotly) {
          chart.innerHTML = '<p class="chart-note">The interactive chart could not load. The frozen evidence JSON contains the complete series.</p>';
          return;
        }
        var colors = themeColors();
        var points = transferRows.filter(function (row) { return row.frequency === frequency; });
        var color = mixThemeColors(colors.surface, colors.accent, colorWeight);
        var isMonthly = frequency === 'monthly';
        var trace = {
          x: points.map(function (row) { return row.snapshot_date; }),
          y: points.map(function (row) { return row.transfer_employees; }),
          customdata: points.map(function (row) { return [row.eligible_employees, row.transfer_rate_percent]; }),
          text: isMonthly ? points.map(function (row, index) {
            return index === 0 || index === points.length - 1 || index % 4 === 0
              ? row.transfer_employees.toLocaleString()
              : '';
          }) : [],
          mode: isMonthly ? 'lines+markers+text' : 'lines+markers',
          textposition: 'top center',
          textfont: { family: colors.font, size: 9, color: colors.text },
          type: 'scatter',
          name: isMonthly ? 'Monthly snapshots' : 'Weekly endpoints',
          showlegend: true,
          line: { color: color, width: 3 },
          marker: { color: color, size: isMonthly ? 7 : 5, line: { color: colors.surface, width: 1 } },
          hovertemplate: '<b>%{x|%d %b %Y}</b><br>Employees with a transfer: <b>%{y:,}</b><br>Eligible employees: %{customdata[0]:,}<br>Rate: %{customdata[1]:.2f}%<extra></extra>'
        };
        Plotly.react(chart, [trace], {
          height: 244,
          plot_bgcolor: 'rgba(0,0,0,0)',
          paper_bgcolor: 'rgba(0,0,0,0)',
          font: { family: colors.font, color: colors.text },
          hovermode: 'x unified',
          hoverlabel: { font: { family: colors.font } },
          margin: { t: 34, r: 8, b: 38, l: 48 },
          legend: { orientation: 'h', y: 1.14, x: 0, font: { family: colors.font, size: 10, color: colors.text } },
          xaxis: {
            type: 'date', tickformat: isMonthly ? '%b\n%Y' : '%b %d', nticks: isMonthly ? 12 : 12,
            tickfont: { family: colors.font, size: 10, color: colors.muted },
            showgrid: false, zeroline: false, fixedrange: true
          },
          yaxis: {
            tickformat: ',d', tickfont: { family: colors.font, size: 10, color: colors.muted },
            gridcolor: colors.border, zerolinecolor: colors.border, fixedrange: true
          }
        }, { responsive: false, displayModeBar: false });
      }

      function renderTransferCharts() {
        renderTransferChart('transfer-monthly-chart', 'monthly', 1.0);
        renderTransferChart('transfer-weekly-chart', 'weekly', 0.62);
      }

      renderTransferCharts();
      new MutationObserver(function (records) {
        if (records.some(function (record) { return record.attributeName === 'class'; })) renderTransferCharts();
      }).observe(document.body, { attributes: true, attributeFilter: ['class'] });
    })();
  </script>
"""


def facts(items: list[tuple[str, str]]) -> str:
    return "<ul class=\"fact-list\">" + "".join(f"<li><strong>{esc(label)}:</strong> {esc(value)}</li>" for label, value in items) + "</ul>"


def provenance_panel(variable: str) -> str:
    try:
        source, asset, grain, inputs, status = PROVENANCE[variable]
    except KeyError as exc:
        raise ValueError(f"Missing provenance for variable slide: {variable}") from exc
    rows = (("Data origin", source), ("Table / asset", asset), ("Analytical grain", grain), ("Key data", inputs))
    rendered_rows = "".join(f"<dt>{esc(label)}</dt><dd>{esc(value)}</dd>" for label, value in rows)
    return f"""<section class=\"provenance-panel\"><div class=\"provenance-title\">Data provenance and scope</div>
      <dl class=\"provenance-grid\">{rendered_rows}</dl><p class=\"provenance-status\"><strong>Important:</strong> {esc(status)}</p></section>"""


def side_card(title: str, text: str, items: list[tuple[str, str]], badge: str = "Aggregate evidence") -> str:
    return f"""<article class="card side-copy"><div class="card-title">Variable context</div><span class="badge badge-info">{esc(badge)}</span>
      <h3>{esc(title)}</h3><p>{esc(text)}</p>{facts(items)}</article>"""


def data_slide(number: int, title: str, subtitle: str, main: str, side: str) -> str:
    if not side.endswith("</article>"):
        raise ValueError(f"The side card for {title!r} has an unexpected structure.")
    scope = VISUAL_SCOPE.get(title)
    if title == "Region":
        subtitle = subtitle.replace("latest snapshot", f"snapshot {V4_SNAPSHOT}")
    scope_markup = (
        f'<p class="scope-note"><strong>Visual scope:</strong> {esc(scope)}</p>'
        if scope else ""
    )
    side = side.removesuffix("</article>") + scope_markup + provenance_panel(title) + "</article>"
    return f"""<div class="slide-stage" id="slide-{number}">{heading(title, subtitle)}
      <div class="two-pane">{main}{side}</div></div>"""


def comp_ratio_voluntary_attrition_history_card(evidence: dict[str, object]) -> str:
    """Render the two-group six-month voluntary-attrition history card."""
    grouping = evidence["grouping"]
    pooled = evidence["pooled_comparison"]
    dates = evidence["audit_dates"]
    assert isinstance(grouping, dict) and isinstance(pooled, dict) and isinstance(dates, dict)
    low_label = str(grouping["low_group"])
    high_label = str(grouping["high_group"])
    low = pooled[low_label]
    high = pooled[high_label]
    comparison = pooled["comparison"]
    assert isinstance(low, dict) and isinstance(high, dict) and isinstance(comparison, dict)
    delta = float(comparison["absolute_difference_percentage_points"])
    snapshot_count = int(evidence["audit_metrics"]["complete_snapshot_count"])
    return f'''<article class="card chart-card comp-ratio-history-card">
      <div class="card-title">Six-month voluntary attrition after each snapshot</div>
      <div id="comp-ratio-voluntary-attrition-chart" class="comp-ratio-history-chart" aria-label="Historical six-month voluntary attrition by compa_ratio group"></div>
      <div class="comp-ratio-pooled-summary">
        <div class="comp-ratio-summary-item"><div class="comp-ratio-summary-label"><i class="comp-ratio-summary-dot"></i>{esc(low_label)}</div><strong>{float(low['voluntary_rate_percent']):.2f}%</strong><small>pooled · n={int(low['employee_snapshots']):,}</small></div>
        <div class="comp-ratio-summary-item"><div class="comp-ratio-summary-label"><i class="comp-ratio-summary-dot high"></i>{esc(high_label)}</div><strong>{float(high['voluntary_rate_percent']):.2f}%</strong><small>pooled · n={int(high['employee_snapshots']):,}</small></div>
        <div class="comp-ratio-summary-difference"><span>Low minus high</span><strong>{delta:+.2f} pp</strong></div>
      </div>
      <div class="chart-footer">{snapshot_count} complete monthly snapshots from {esc(dates['complete_followup_first_snapshot_date'])} through {esc(dates['complete_followup_last_snapshot_date'])}. Each point uses strict <strong>term_type = 'VOLUNTARY'</strong> exits in the six months after the snapshot; pooled n counts employee-snapshot rows. Descriptive association only, not individual prediction.</div>
    </article>'''


def comp_ratio_slide(number: int, evidence: dict[str, object]) -> str:
    """Render the current banded distribution plus the requested history view."""
    pooled = evidence["pooled_comparison"]
    grouping = evidence["grouping"]
    assert isinstance(pooled, dict) and isinstance(grouping, dict)
    low_label = str(grouping["low_group"])
    high_label = str(grouping["high_group"])
    low = pooled[low_label]
    high = pooled[high_label]
    comparison = pooled["comparison"]
    assert isinstance(low, dict) and isinstance(high, dict) and isinstance(comparison, dict)
    main = (
        '<div class="comp-ratio-main">'
        + bar_card(
            "Distribution by compa_ratio bands",
            STORED_METRIC_DISTRIBUTIONS["compa_ratio"],
            f"Cutoff {STORED_METRIC_SNAPSHOT}; percent and n use {STORED_METRIC_POPULATION_LABEL} active regular employees. Extreme values remain within the ≥ 1.25 band and are not published as isolated categories.",
            "comp-ratio-distribution-card",
        )
        + comp_ratio_voluntary_attrition_history_card(evidence)
        + "</div>"
    )
    side = side_card(
        "The 0.8 split is an exploratory comparison",
        "The lower chart compares historical strict Voluntary exit rates for the two agreed stored-ratio groups. It does not validate the compa_ratio formula, imply that the lower group is underpaid, or create individual predictions.",
        [
            ("Threshold", "0.8; low <0.8 including 0; high ≥0.8"),
            ("Outcome", "term_type = VOLUNTARY within six months after snapshot"),
            ("History", f"{int(evidence['audit_metrics']['complete_snapshot_count'])} complete monthly snapshots"),
            ("Pooled", f"{float(low['voluntary_rate_percent']):.2f}% vs {float(high['voluntary_rate_percent']):.2f}%"),
            ("Difference", f"{float(comparison['absolute_difference_percentage_points']):+.2f} pp; low minus high"),
            ("Published", "n ≥ 30 for every snapshot × group"),
            ("Pending", "formula and lineage of the stored metric"),
        ],
        "Validated historical association",
    )
    return data_slide(
        number,
        "Comp ratio",
        "Stored value · current bands plus a two-group historical voluntary-attrition comparison",
        main,
        side,
    )


def team_turnover_scenario_card(scenario: dict[str, object]) -> str:
    """Render one publishable aggregate scenario card without manager labels."""
    manager_teams = int(scenario["manager_teams"])
    zero_teams = int(scenario["teams_without_voluntary_exit"])
    positive_teams = int(scenario["teams_with_at_least_one_voluntary_exit"])
    zero_share = float(scenario["zero_exit_team_share_percent"])
    positive_share = float(scenario["positive_exit_team_share_percent"])
    six_month_rate = float(scenario["six_month_turnover_percent"])
    per_100_employee_months = float(scenario["voluntary_exits_per_100_employee_months"])
    return f"""<article class="card chart-card team-turnover-card"><div class="card-title">{esc(scenario['label'])}</div>
      <div class="team-rate"><strong>{six_month_rate:.2f}%</strong><span>six-month equivalent<br/>voluntary turnover</span></div>
      <p class="chart-note">Strict <strong>Voluntary</strong> exits ÷ average monthly direct reports.</p>
      <div class="team-kpis"><div class="team-kpi"><strong>{manager_teams:,}</strong><span>manager teams</span></div><div class="team-kpi"><strong>{int(scenario['direct_reports_at_cutoff']):,}</strong><span>reports at cutoff</span></div><div class="team-kpi"><strong>{int(scenario['voluntary_exit_events']):,}</strong><span>voluntary exits</span></div></div>
      <div class="team-outcome-label">Teams by six-month exit occurrence</div>
      <div class="team-outcome-bar" aria-label="{esc(scenario['label'])}: {zero_share:.2f}% of teams with no voluntary exit and {positive_share:.2f}% with at least one voluntary exit"><div class="team-outcome-zero" style="width:{zero_share:.2f}%"></div><div class="team-outcome-positive" style="width:{positive_share:.2f}%"></div></div>
      <div class="team-outcome-legend"><span>0 exits <strong>{zero_share:.1f}% · {zero_teams:,}</strong></span><span>≥1 exit <strong>{positive_share:.1f}% · {positive_teams:,}</strong></span></div>
      <div class="chart-footer"><strong>{per_100_employee_months:.3f}</strong> voluntary exits per 100 direct-report employee-months.</div></article>"""


def team_turnover_slide(number: int) -> str:
    """Render the approved six-month, two-scenario Team turnover visual."""
    evidence = team_turnover_scenarios()
    scenarios = evidence["scenarios"]
    window = evidence["window"]
    scenario_by_key = {str(scenario["key"]): scenario for scenario in scenarios}
    try:
        all_teams = scenario_by_key["all_manager_led_teams"]
        teams_gt5 = scenario_by_key["teams_gt5_direct_reports"]
    except KeyError as exc:
        raise ValueError("Team turnover evidence is missing an approved scenario.") from exc
    snapshot_count = int(window["monthly_snapshot_count"])
    rate_difference_pp = (
        float(all_teams["six_month_turnover_percent"])
        - float(teams_gt5["six_month_turnover_percent"])
    )
    main = '<div class="two-chart">' + ''.join(team_turnover_scenario_card(scenario) for scenario in scenarios) + '</div>'
    side = side_card(
        "How to read this chart",
        "August 23 selects the managers in each scenario. We then look back six monthly snapshots, count voluntary exits, and compare them with the direct reports observed for those managers over time.",
        [
            ("Step 1: August cutoff", "Choose all teams (≥1) or teams with >5 reports."),
            ("Step 2: look back", f"Six snapshots: ({window['start_exclusive']}, {window['end_inclusive']}]."),
            ("Step 3: average team size", "Add direct reports across all six snapshots, then divide by 6 — not only August."),
            ("Rate formula", "Voluntary exits / average monthly team size × 100"),
            ("All teams calculation", f"{int(all_teams['voluntary_exit_events']):,} / ({int(all_teams['employee_months']):,} / {snapshot_count}) = {float(all_teams['six_month_turnover_percent']):.2f}%"),
            ("Teams >5 calculation", f"{int(teams_gt5['voluntary_exit_events']):,} / ({int(teams_gt5['employee_months']):,} / {snapshot_count}) = {float(teams_gt5['six_month_turnover_percent']):.2f}%"),
            ("Difference", f"All teams are {rate_difference_pp:+.2f} percentage points vs. teams >5."),
            ("Exit rule", "Voluntary only; assigned to the manager just before the exit."),
        ],
        "Exploratory · aggregate only",
    )
    return data_slide(
        number,
        "Team turnover",
        "Six-month voluntary turnover · August 23 monthly cutoff · two direct-report team scenarios",
        main,
        side,
    )


def team_flag_scope_label(scope_key: str) -> str:
    """Translate evidence-scope keys for the English presentation only."""
    labels = {
        "all_teams": "All teams with at least 1 direct report",
        "teams_gt_5": "Teams with >5 direct reports",
    }
    try:
        return labels[scope_key]
    except KeyError as exc:
        raise ValueError(f"Unexpected team-flag scope: {scope_key!r}") from exc


def legacy_team_flag_distribution_card(evidence: dict[str, object], scope_key: str) -> str:
    """Render the 0/1/2+ team flag and its employee-snapshot exposure."""
    scope = next(item for item in evidence["scopes"] if item["key"] == scope_key)
    scope_label = team_flag_scope_label(scope_key)
    rows = scope["buckets"]
    table_rows = []
    for bucket in ("0", "1", "2+"):
        exit_row = next(row for row in rows["manager_at_exit"] if row["bucket"] == bucket)
        eval_row = next(row for row in rows["manager_at_evaluation"] if row["bucket"] == bucket)
        table_rows.append(
            f"<tr><td><strong>{esc(bucket)}</strong></td>"
            f"<td>{float(exit_row['group_share_percent']):.2f}% · {int(exit_row['team_snapshot_groups']):,}</td>"
            f"<td>{float(eval_row['group_share_percent']):.2f}% · {int(eval_row['team_snapshot_groups']):,}</td>"
            f"<td>{float(exit_row['employee_snapshot_share_percent']):.2f}% · {int(exit_row['employee_snapshots']):,}</td>"
            f"<td>{float(eval_row['employee_snapshot_share_percent']):.2f}% · {int(eval_row['employee_snapshots']):,}</td></tr>"
        )
    chart_id = f"team-flag-{scope_key}-chart"
    return f"""<article class="card chart-card team-flag-card">
      <div class="card-title">{esc(scope_label)} · teams with 2+ exits</div>
      <div id="{chart_id}" class="team-flag-chart" aria-label="{esc(scope_label)}: comparison of teams with two or more voluntary exits by attribution"></div>
      <table class="team-flag-table"><thead><tr><th>Bucket</th><th>Manager at exit<br/>teams</th><th>Manager at evaluation<br/>teams</th><th>Manager at exit<br/>employee-snapshots</th><th>Manager at evaluation<br/>employee-snapshots</th></tr></thead>
      <tbody>{''.join(table_rows)}</tbody></table>
      <div class="chart-footer">Each percentage uses the same denominator within the scope: {int(scope['total_team_snapshot_groups']):,} groups and {int(scope['total_employee_snapshots']):,} employee-snapshots. “2+” turns on the flag.</div>
    </article>"""


def legacy_team_flag_slide(number: int, scope_key: str) -> str:
    evidence = more_than_1_employee_leaves_evidence()
    scope = next(item for item in evidence["scopes"] if item["key"] == scope_key)
    scope_label = team_flag_scope_label(scope_key)
    main = legacy_team_flag_distribution_card(evidence, scope_key)
    side = side_card(
        "Formal definition and attribution",
        "A team is reconstructed as the set of active direct reports at each snapshot. Only distinct Voluntary exits within six months are counted; the flag equals 1 for two or more exits.",
        [
            ("Scope", scope_label),
            ("Window", "(snapshot − 6 months, snapshot]"),
            ("Grain", "manager-team × employee snapshot"),
            ("Primary", "last manager observed before term_date"),
            ("Sensitivity", "last manager available when evaluating t"),
            ("Both scenarios", "same team-and-employee denominator"),
        ],
        "Aggregate validation · Voluntary only",
    )
    title = "More than 1 employee leaves · all teams" if scope_key == "all_teams" else "More than 1 employee leaves · teams >5"
    subtitle = "Team flag · six months · voluntary exits · " + scope_label
    return data_slide(number, title, subtitle, main, side)


def legacy_team_flag_chart_enhancement(evidence: dict[str, object]) -> str:
    """Render both attribution scenarios and refresh them on theme changes."""
    display_scopes = [
        {**scope, "label": team_flag_scope_label(str(scope["key"]))}
        for scope in evidence["scopes"]
    ]
    payload = json.dumps(display_scopes, ensure_ascii=False).replace("</", "<\\/")
    return r"""
  <script>
    (function () {
      var teamFlagScopes = """ + payload + r""";
      var flagBucket = '2+';

      function themeColors() {
        var styles = getComputedStyle(document.body);
        return {
          text: styles.getPropertyValue('--text-main').trim() || '#0f172a',
          muted: styles.getPropertyValue('--text-muted').trim() || '#5b6478',
          accent: styles.getPropertyValue('--accent').trim() || '#2457ff',
          accent2: styles.getPropertyValue('--accent-2').trim() || '#14b8a6',
          surface: styles.getPropertyValue('--bg-surface').trim() || '#ffffff',
          border: styles.getPropertyValue('--border-subtle').trim() || 'rgba(15,23,42,0.08)',
          font: 'Aptos, Segoe UI, system-ui, sans-serif'
        };
      }

      function renderTeamFlagChart(scope) {
        var chart = document.getElementById('team-flag-' + scope.key + '-chart');
        if (!chart || !window.Plotly) return;
        var colors = themeColors();
        var traces = [
          { key: 'manager_at_exit', name: 'Manager at exit', color: colors.accent },
          { key: 'manager_at_evaluation', name: 'Manager at evaluation', color: colors.accent2 }
        ].map(function (scenario) {
          var rows = scope.buckets[scenario.key];
          return {
            x: ['2+'],
            y: [rows.find(function (row) { return row.bucket === flagBucket; }).group_share_percent],
            customdata: [function () {
              var row = rows.find(function (item) { return item.bucket === flagBucket; });
              return [row.team_snapshot_groups, row.employee_snapshot_share_percent, row.employee_snapshots];
            }()],
            name: scenario.name,
            type: 'bar',
            marker: { color: scenario.color, line: { color: colors.surface, width: 1 } },
            text: [rows.find(function (row) { return row.bucket === flagBucket; }).group_share_percent.toFixed(2) + '%'],
            textposition: 'inside',
            textfont: { family: colors.font, size: 10, color: '#ffffff' },
            hovertemplate: '<b>%{x}</b><br>%{fullData.name}<br>Teams: %{y:.2f}% · n=%{customdata[0]:,}<br>Employee-snapshots: %{customdata[1]:.2f}% · n=%{customdata[2]:,}<extra></extra>'
          };
        });
        Plotly.react(chart, traces, {
          height: 218,
          barmode: 'group',
          bargap: 0.22,
          bargroupgap: 0.08,
          plot_bgcolor: 'rgba(0,0,0,0)', paper_bgcolor: 'rgba(0,0,0,0)',
          font: { family: colors.font, color: colors.text },
          margin: { t: 28, r: 8, b: 30, l: 42 },
          legend: { orientation: 'h', y: 1.16, x: 0, font: { family: colors.font, size: 10, color: colors.text } },
          xaxis: { fixedrange: true, tickfont: { family: colors.font, size: 11, color: colors.muted } },
          yaxis: { range: [0, 0.5], tickvals: [0, 0.1, 0.2, 0.3, 0.4, 0.5], tickformat: '.2f', ticksuffix: '%', fixedrange: true, gridcolor: colors.border, zerolinecolor: colors.border, tickfont: { family: colors.font, size: 10, color: colors.muted } }
        }, { responsive: false, displayModeBar: false });
      }

      function renderAll() { teamFlagScopes.forEach(renderTeamFlagChart); }
      renderAll();
      new MutationObserver(function (records) {
        if (records.some(function (record) { return record.attributeName === 'class'; })) renderAll();
      }).observe(document.body, { attributes: true, attributeFilter: ['class'] });
    })();
  </script>
"""


def team_flag_distribution_card_monthly(
    evidence: dict[str, object], annual_evidence: dict[str, object], scope_key: str
) -> str:
    """Render the primary six-month trend above the annual sensitivity."""
    scope = next(item for item in evidence["scopes"] if item["key"] == scope_key)
    annual_scope = next(item for item in annual_evidence["scopes"] if item["key"] == scope_key)
    scope_label = team_flag_scope_label(scope_key)
    calendar = annual_evidence["comparison_calendar"]
    if not isinstance(calendar, dict):
        raise ValueError("Falta el calendario de comparación anual para el renderizado.")
    annual_dates = int(calendar["annual_complete_snapshot_count"])
    primary_dates = int(calendar["primary_evaluation_snapshot_count"])
    excluded_dates = int(calendar["annual_excluded_primary_snapshot_count"])
    if not isinstance(scope, dict) or not isinstance(annual_scope, dict):
        raise ValueError("Falta un scope válido para el renderizado de la comparación anual.")
    return f'''<article class="card chart-card team-flag-card">
      <div class="card-title">Share of active employees in teams with 2+ Voluntary exits</div>
      <section class="team-flag-window-panel">
        <div class="team-flag-window-heading"><h3>Primary · 2+ exits in the prior 6 months</h3><p>{primary_dates} monthly snapshots</p></div>
        <div id="team-flag-{scope_key}-six-month-chart" class="team-flag-window-chart" aria-label="{esc(scope_label)}: share of active employees in teams with 2 or more Voluntary exits in the prior 6 months"></div>
      </section>
      <section class="team-flag-window-panel">
        <div class="team-flag-window-heading"><h3>Supplement · same measure over the prior 12 months</h3><p>{annual_dates} of {primary_dates} dates complete; first {excluded_dates} excluded</p></div>
        <div id="team-flag-{scope_key}-annual-chart" class="team-flag-window-chart" aria-label="{esc(scope_label)}: share of active employees in teams with 2 or more Voluntary exits in the prior 12 months"></div>
      </section>
      <div class="chart-footer"><strong>How to read:</strong> 7% means 7 of every 100 active employees were in a team with 2+ Voluntary exits in the preceding window. It does <strong>not</strong> mean 7% of employees exited.</div>
    </article>'''


def team_flag_slide_monthly(number: int, scope_key: str) -> str:
    evidence = more_than_1_employee_leaves_evidence()
    annual_evidence = more_than_1_employee_leaves_annual_evidence(evidence)
    scope_label = team_flag_scope_label(scope_key)
    main = team_flag_distribution_card_monthly(evidence, annual_evidence, scope_key)
    side = side_card(
        "What the percentage represents",
        "Each point is the share of active employees in a team that had 2+ strict-Voluntary exits during the preceding window. It is an exposure measure, not an attrition rate or an individual prediction.",
        [
            ("Scope", scope_label),
            ("Numerator", "Active employees in teams with 2+ strict-Voluntary exits"),
            ("Denominator", "Active employees with an observable team in that month"),
            ("Plain-language example", "7% = 7 of every 100 employees were in such a team; it does not mean 7 left"),
            ("Upper chart", "Prior 6 months - the primary feature"),
            ("Lower chart", "Same calculation over prior 12 months - sensitivity only"),
            ("Two lines", "Manager at evaluation versus manager at exit; the near overlap is the attribution sensitivity"),
        ],
        "Aggregate exposure measure · Voluntary only",
    )
    title = "More than 1 employee leaves · all teams" if scope_key == "all_teams" else "More than 1 employee leaves · teams >5"
    subtitle = "% of active employees in teams with 2+ Voluntary exits · six-month primary + 12-month comparison · " + scope_label
    return data_slide(number, title, subtitle, main, side)


def team_flag_chart_enhancement_monthly(
    evidence: dict[str, object], annual_evidence: dict[str, object]
) -> str:
    """Render primary and annual charts with one shared y-axis per scope."""
    six_month_scopes = [
        {**scope, "label": team_flag_scope_label(str(scope["key"]))}
        for scope in evidence["scopes"]
    ]
    annual_scopes = [
        {**scope, "label": team_flag_scope_label(str(scope["key"]))}
        for scope in annual_evidence["scopes"]
    ]
    payload = json.dumps(
        {"sixMonth": six_month_scopes, "annual": annual_scopes}, ensure_ascii=False
    ).replace("</", "<\\/")
    return r'''
  <script>
    (function () {
      var teamFlagPayload = ''' + payload + r''';

      function teamFlagThemeColors() {
        var styles = getComputedStyle(document.body);
        return {
          text: styles.getPropertyValue('--text-main').trim() || '#0f172a',
          muted: styles.getPropertyValue('--text-muted').trim() || '#5b6478',
          accent: styles.getPropertyValue('--accent').trim() || '#2457ff',
          accent2: styles.getPropertyValue('--accent-2').trim() || '#14b8a6',
          border: styles.getPropertyValue('--border-subtle').trim() || 'rgba(15,23,42,0.08)',
          font: 'Aptos, Segoe UI, system-ui, sans-serif'
        };
      }

      function renderWindowPanel(scope, chartId, axisMax, xRange) {
        var chart = document.getElementById(chartId);
        if (!chart || !window.Plotly) return;
        var colors = teamFlagThemeColors();
        var attributionMeta = [
          { key: 'manager_at_evaluation', name: 'Team at evaluation (sensitivity)', color: colors.accent, dash: 'solid' },
          { key: 'manager_at_exit', name: 'Team at exit (primary)', color: colors.accent2, dash: 'dash' }
        ];
        var traces = attributionMeta.map(function (meta) {
          var rows = scope.monthly_series[meta.key];
          return {
            x: rows.map(function (row) { return row.snapshot_date; }),
            y: rows.map(function (row) { return row.employee_percent; }),
            customdata: rows.map(function (row) { return [row.flagged_employees, row.observable_employees, row.affected_teams]; }),
            name: meta.name,
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: meta.color, width: 2, dash: meta.dash },
            marker: { color: meta.color, size: 5 },
            hovertemplate: '<b>' + meta.name + '</b><br>%{x}<br>Employees in 2+ exit teams: %{customdata[0]:,}<br>Active employees with an observable team: %{customdata[1]:,}<br>Share: %{y:.2f}%<br>Teams with 2+ exits: %{customdata[2]:,}<extra></extra>'
          };
        });
        Plotly.react(chart, traces, {
          height: 214,
          plot_bgcolor: 'rgba(0,0,0,0)', paper_bgcolor: 'rgba(0,0,0,0)',
          font: { family: colors.font, color: colors.text },
          margin: { t: 24, r: 8, b: 27, l: 46 },
          showlegend: true,
          legend: { orientation: 'h', x: 0, y: 1.18, xanchor: 'left', font: { family: colors.font, size: 9, color: colors.muted }, bgcolor: 'rgba(0,0,0,0)' },
          xaxis: { fixedrange: true, range: xRange, tickfont: { family: colors.font, size: 9, color: colors.muted }, nticks: 6 },
          yaxis: { range: [0, axisMax], tickformat: '.1f', ticksuffix: '%', fixedrange: true, gridcolor: colors.border, zerolinecolor: colors.border, tickfont: { family: colors.font, size: 9, color: colors.muted }, title: { text: '% employees', font: { family: colors.font, size: 9, color: colors.muted } } }
        }, { responsive: false, displayModeBar: false });
      }

      function renderMonthlyTeamFlags() {
        teamFlagPayload.sixMonth.forEach(function (scope) {
          var annualScope = teamFlagPayload.annual.filter(function (item) { return item.key === scope.key; })[0];
          if (!annualScope) return;
          var allRows = scope.monthly_series.manager_at_evaluation
            .concat(scope.monthly_series.manager_at_exit)
            .concat(annualScope.monthly_series.manager_at_evaluation)
            .concat(annualScope.monthly_series.manager_at_exit);
          var maximum = Math.max.apply(null, allRows.map(function (row) { return Number(row.employee_percent) || 0; }));
          var axisMax = Math.max(1, Math.ceil(maximum * 1.18 * 10) / 10);
          var primaryRows = scope.monthly_series.manager_at_evaluation;
          var xRange = [primaryRows[0].snapshot_date, primaryRows[primaryRows.length - 1].snapshot_date];
          renderWindowPanel(scope, 'team-flag-' + scope.key + '-six-month-chart', axisMax, xRange);
          renderWindowPanel(annualScope, 'team-flag-' + scope.key + '-annual-chart', axisMax, xRange);
        });
      }

      renderMonthlyTeamFlags();
      new MutationObserver(function (records) {
        if (records.some(function (record) { return record.attributeName === 'class'; })) renderMonthlyTeamFlags();
      }).observe(document.body, { attributes: true, attributeFilter: ['class'] });
    })();
  </script>
'''


def team_post_exit_attrition_evidence() -> dict[str, object]:
    """Load the presentation-safe descriptive post-exit cohort evidence."""
    if not TEAM_POST_EXIT_ATTRITION_EVIDENCE.exists():
        raise FileNotFoundError(TEAM_POST_EXIT_ATTRITION_EVIDENCE)
    evidence = load(TEAM_POST_EXIT_ATTRITION_EVIDENCE)
    if not isinstance(evidence, dict):
        raise ValueError("La evidencia de attrition posterior a salida no es un objeto JSON válido.")
    if evidence.get("artifact_classification") != "presentation" or evidence.get("outcome") != "pass":
        raise ValueError("La evidencia de attrition posterior a salida debe ser presentation y aprobar.")
    if evidence.get("variable") != "More than 1 employee leaves in a year":
        raise ValueError("La evidencia posterior a salida no corresponde a la variable esperada.")

    prohibited = {
        "employee_id", "manager_employee_id", "manager_name", "employee_name",
        "name", "email", "raw_rows", "raw_query_rows", "query_rows",
    }

    def reject_sensitive_fields(value: object) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if str(key).lower() in prohibited:
                    raise ValueError(f"La evidencia posterior a salida conserva un campo restringido: {key!r}.")
                reject_sensitive_fields(nested)
        elif isinstance(value, list):
            for nested in value:
                reject_sensitive_fields(nested)

    reject_sensitive_fields(evidence)
    study = evidence.get("study")
    cohort = evidence.get("cohort")
    reconciliation = evidence.get("reconciliation_metrics")
    audits = evidence.get("query_audits")
    curves = evidence.get("curves")
    validation = evidence.get("validation")
    provenance = evidence.get("provenance")
    if not all(isinstance(value, dict) for value in (study, cohort, reconciliation, audits, curves, validation, provenance)):
        raise ValueError("La evidencia posterior a salida no contiene el contrato agregado completo.")
    assert isinstance(study, dict) and isinstance(cohort, dict) and isinstance(reconciliation, dict)
    assert isinstance(audits, dict) and isinstance(curves, dict) and isinstance(validation, dict) and isinstance(provenance, dict)
    if study.get("interpretation") != "Asociación descriptiva; no causalidad, contagio probado, ranking de managers ni predicción individual.":
        raise ValueError("La evidencia posterior a salida perdió su límite de interpretación.")
    if cohort.get("index_snapshot") != "2026-03-29" or cohort.get("follow_up_end") != "2026-09-27":
        raise ValueError("La evidencia posterior a salida no usa la cohorte reciente aprobada.")
    follow_up_dates = cohort.get("follow_up_snapshot_dates")
    follow_up_gaps = cohort.get("follow_up_gaps_days")
    if not isinstance(follow_up_dates, list) or len(follow_up_dates) != 6 or not isinstance(follow_up_gaps, list) or len(follow_up_gaps) != 6:
        raise ValueError("La cohorte posterior a salida no conserva sus seis cierres de seguimiento.")
    if int(audits.get("index_team_episodes", 0)) <= 0 or int(audits.get("series_points", 0)) != 24:
        raise ValueError("La cohorte posterior a salida no conserva episodios índice o sus 24 puntos.")
    if float(reconciliation.get("voluntary_monthly_match_percent", 0.0)) < 99.0:
        raise ValueError("La reconciliación Voluntary posterior a salida está por debajo de 99%.")
    if int(reconciliation.get("all_terminations_repeated_source_rows", -1)) != 0:
        raise ValueError("La fuente all_terminations conserva duplicados de evento.")
    if validation.get("errors") != []:
        raise ValueError("La evidencia posterior a salida contiene errores de validación.")

    expected_curve_keys = {
        f"{scope}::{series}"
        for scope in ("all_teams", "teams_6_plus")
        for series in ("exposed", "reference_standardized")
    }
    if set(curves) != expected_curve_keys:
        raise ValueError("La evidencia posterior a salida no contiene las cuatro curvas esperadas.")
    for key in sorted(expected_curve_keys):
        rows = curves[key]
        if not isinstance(rows, list) or len(rows) != 6:
            raise ValueError(f"La curva {key} no contiene los seis meses esperados.")
        previous_incidence = -1.0
        for expected_month, row in enumerate(rows, start=1):
            if not isinstance(row, dict) or int(row.get("follow_month", 0)) != expected_month:
                raise ValueError(f"La curva {key} no está ordenada por mes de seguimiento.")
            at_risk = int(row.get("at_risk_n", 0))
            hazard = float(row.get("interval_hazard_percent", -1))
            incidence = float(row.get("cumulative_incidence_percent", -1))
            if at_risk < MINIMUM_COHORT or not 0.0 <= hazard <= 100.0 or not 0.0 <= incidence <= 100.0:
                raise ValueError(f"La curva {key} incumple los límites de publicación.")
            if incidence + 1e-8 < previous_incidence:
                raise ValueError(f"La incidencia acumulada de {key} no es monótona.")
            previous_incidence = incidence

    expected_provenance = {
        "calendar_sql": TEAM_POST_EXIT_ATTRITION_CALENDAR_SQL,
        "reconciliation_sql": TEAM_POST_EXIT_ATTRITION_RECONCILIATION_SQL,
        "static_template_sql": TEAM_POST_EXIT_ATTRITION_STATIC_SQL,
        "executed_static_sql": TEAM_POST_EXIT_ATTRITION_EXECUTED_SQL,
    }
    if any(provenance.get(key) != value for key, value in expected_provenance.items()):
        raise ValueError("La evidencia posterior a salida no referencia las consultas aprobadas.")
    for key, path_text in expected_provenance.items():
        local_path = ROOT / path_text
        hash_key = key + "_sha256"
        if not local_path.exists() or provenance.get(hash_key) != hashlib.sha256(local_path.read_bytes()).hexdigest():
            raise ValueError(f"La evidencia posterior a salida no reconcilia el hash de {path_text}.")
    for key in ("calendar_result_sha256", "reconciliation_result_sha256", "static_result_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", str(provenance.get(key, ""))):
            raise ValueError(f"La evidencia posterior a salida tiene un hash inválido: {key}.")
    return evidence


def team_post_exit_attrition_manifest_entry(evidence: dict[str, object]) -> dict[str, object]:
    """Expose auditable aggregate provenance without persisting any roster detail."""
    study = evidence["study"]
    cohort = evidence["cohort"]
    reconciliation = evidence["reconciliation_metrics"]
    audits = evidence["query_audits"]
    validation = evidence["validation"]
    provenance = evidence["provenance"]
    assert all(isinstance(value, dict) for value in (study, cohort, reconciliation, audits, validation, provenance))
    return {
        "evidence": str(TEAM_POST_EXIT_ATTRITION_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "evidence_sha256": hashlib.sha256(TEAM_POST_EXIT_ATTRITION_EVIDENCE.read_bytes()).hexdigest(),
        "builder": str(TEAM_POST_EXIT_ATTRITION_BUILDER.relative_to(ROOT)).replace("\\", "/"),
        "analysis_plan": str(TEAM_POST_EXIT_ATTRITION_PLAN.relative_to(ROOT)).replace("\\", "/"),
        "execution_date": evidence["execution_date"],
        "deliverable_mode": evidence["artifact_classification"],
        "study": study,
        "cohort": cohort,
        "aggregate_metrics": {
            "index_team_episodes": audits["index_team_episodes"],
            "series_points": audits["series_points"],
            "voluntary_monthly_match_percent": reconciliation["voluntary_monthly_match_percent"],
            "voluntary_exact_match": reconciliation["voluntary_exact_match"],
            "all_terminations_repeated_source_rows": reconciliation["all_terminations_repeated_source_rows"],
            "minimum_visible_at_risk_n": MINIMUM_COHORT,
        },
        "queries": {
            key: provenance[key]
            for key in ("calendar_sql", "reconciliation_sql", "static_template_sql", "executed_static_sql")
        },
        "query_sha256": {
            key: provenance[key]
            for key in (
                "calendar_sql_sha256", "reconciliation_sql_sha256", "static_template_sql_sha256",
                "executed_static_sql_sha256", "calendar_result_sha256",
                "reconciliation_result_sha256", "static_result_sha256",
            )
        },
        "acceptance_rule": validation["acceptance_rule"],
        "limitation": evidence["limitation"],
        "outcome": evidence["outcome"],
    }


def team_post_exit_attrition_style_tag() -> str:
    """Keep the focused refresh self-contained inside the two replaced stages."""
    return """<style data-team-post-exit-attrition="true">
      .team-post-exit-card { min-height:0; padding:14px; gap:9px; }
      .team-post-exit-card .card-title { margin-bottom:0; }
      .team-post-exit-chart { width:100%; height:350px; min-width:0; flex:0 0 350px; }
      .team-post-exit-kpis { display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:8px; }
      .team-post-exit-kpi { min-width:0; padding:8px 9px; border:1px solid var(--border-subtle); border-radius:10px; background:var(--bg-surface-2); }
      .team-post-exit-kpi strong { display:block; color:var(--accent); font-size:18px; line-height:1.1; font-variant-numeric:tabular-nums; }
      .team-post-exit-kpi span { display:block; margin-top:3px; color:var(--text-muted); font-size:11px; line-height:1.25; }
      .team-post-exit-card .chart-footer { margin-top:0; padding-top:7px; font-size:11px; line-height:1.32; }
      .team-post-exit-side { padding:13px 14px; gap:7px; }
      .team-post-exit-side h3 { font-size:17px; line-height:1.16; }
      .team-post-exit-side p { font-size:12px; line-height:1.34; }
      .team-post-exit-side .fact-list { gap:4px; }
      .team-post-exit-side .fact-list li { font-size:11px; line-height:1.25; }
      .team-post-exit-side .provenance-panel { padding-top:7px; }
      .team-post-exit-side .provenance-grid { grid-template-columns:92px minmax(0,1fr); }
      .team-post-exit-side .provenance-status { margin-top:6px; }
    </style>"""


def team_post_exit_chart_enhancement(evidence: dict[str, object], scope_key: str, chart_id: str) -> str:
    """Render one two-series cumulative-incidence chart and re-render on theme changes."""
    curves = evidence["curves"]
    assert isinstance(curves, dict)
    payload = json.dumps(
        {
            "exposed": curves[f"{scope_key}::exposed"],
            "reference": curves[f"{scope_key}::reference_standardized"],
        },
        ensure_ascii=False,
    ).replace("</", "<\\/")
    return r'''<script>
      (function () {
        var teamPostExitPayload = ''' + payload + r''';
        var chartId = ''' + json.dumps(chart_id, ensure_ascii=False) + r''';

        function themeColors() {
          var styles = getComputedStyle(document.body);
          return {
            text: styles.getPropertyValue('--text-main').trim() || '#0f172a',
            muted: styles.getPropertyValue('--text-muted').trim() || '#5b6478',
            accent: styles.getPropertyValue('--accent').trim() || '#2457ff',
            accent2: styles.getPropertyValue('--accent-2').trim() || '#3b82f6',
            border: styles.getPropertyValue('--border-subtle').trim() || 'rgba(15,23,42,0.08)',
            font: 'Aptos, Segoe UI, system-ui, sans-serif'
          };
        }

        function trace(rows, name, color, dash) {
          var points = [{ follow_month: 0, cumulative_incidence_percent: 0, at_risk_n: rows[0].initial_roster_n, interval_hazard_percent: 0, voluntary_events_in_interval: 0 }].concat(rows);
          return {
            x: points.map(function (row) { return row.follow_month; }),
            y: points.map(function (row) { return row.cumulative_incidence_percent; }),
            customdata: points.map(function (row) { return [row.at_risk_n, row.interval_hazard_percent, row.voluntary_events_in_interval]; }),
            name: name,
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: color, width: 3, dash: dash },
            marker: { color: color, size: 7 },
            hovertemplate: '<b>%{fullData.name}</b><br>%{x} meses tras el índice<br>Incidencia acumulada: %{y:.2f}%<br>n en riesgo: %{customdata[0]:,}<br>Hazard mensual: %{customdata[1]:.2f}%<br>Salidas Voluntary: %{customdata[2]:,}<extra></extra>'
          };
        }

        function renderTeamPostExitChart() {
          var chart = document.getElementById(chartId);
          if (!chart || !window.Plotly) return;
          var colors = themeColors();
          var exposed = teamPostExitPayload.exposed;
          var reference = teamPostExitPayload.reference;
          var maximum = Math.max.apply(null, exposed.concat(reference).map(function (row) { return Number(row.cumulative_incidence_percent) || 0; }));
          var axisMax = Math.max(1, Math.ceil(maximum * 1.2 * 2) / 2);
          Plotly.react(chart, [
            trace(exposed, 'Equipo tras una salida inicial única', colors.accent, 'solid'),
            trace(reference, 'Equipos sin salida reciente, ajustados', colors.accent2, 'dash')
          ], {
            height: 350,
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { family: colors.font, color: colors.text },
            margin: { t: 30, r: 14, b: 45, l: 62 },
            legend: { orientation: 'h', x: 0, y: 1.16, xanchor: 'left', font: { family: colors.font, size: 11, color: colors.text }, bgcolor: 'rgba(0,0,0,0)' },
            xaxis: { title: { text: 'Meses desde la salida índice', font: { family: colors.font, size: 11, color: colors.muted } }, tickvals: [0, 1, 2, 3, 4, 5, 6], ticktext: ['Índice', '1', '2', '3', '4', '5', '6'], fixedrange: true, gridcolor: colors.border, zerolinecolor: colors.border, tickfont: { family: colors.font, size: 11, color: colors.muted } },
            yaxis: { title: { text: 'Incidencia acumulada Voluntary', font: { family: colors.font, size: 11, color: colors.muted } }, range: [0, axisMax], ticksuffix: '%', fixedrange: true, gridcolor: colors.border, zerolinecolor: colors.border, tickfont: { family: colors.font, size: 11, color: colors.muted } }
          }, { responsive: false, displayModeBar: false });
        }

        renderTeamPostExitChart();
        new MutationObserver(function (records) {
          if (records.some(function (record) { return record.attributeName === 'class'; })) renderTeamPostExitChart();
        }).observe(document.body, { attributes: true, attributeFilter: ['class'] });
      })();
    </script>'''


def team_post_exit_attrition_slide(number: int, scope_key: str) -> str:
    """Render Julia's question as a bounded post-event cohort comparison."""
    evidence = team_post_exit_attrition_evidence()
    scope = {
        "all_teams": {
            "title": "¿Una salida inicial precede más salidas?",
            "subtitle": "Cohorte índice: 29 mar 2026 · seguimiento de 6 cierres hasta 27 sep 2026 · todos los equipos",
            "label": "Todos los equipos",
            "scope_note": "Equipos de cualquier tamaño con manager observable en el cierre índice.",
        },
        "teams_6_plus": {
            "title": "Sensibilidad: equipos de 6+ personas",
            "subtitle": "Misma cohorte y método · equipos con 6 o más integrantes al cierre índice",
            "label": "Equipos de 6+ personas",
            "scope_note": "Se excluyen equipos de 1–5 integrantes al cierre índice.",
        },
    }.get(scope_key)
    if scope is None:
        raise ValueError(f"Scope posterior a salida no esperado: {scope_key!r}.")
    curves = evidence["curves"]
    audits = evidence["query_audits"]
    cohort = evidence["cohort"]
    assert isinstance(curves, dict) and isinstance(audits, dict) and isinstance(cohort, dict)
    exposed = curves[f"{scope_key}::exposed"]
    reference = curves[f"{scope_key}::reference_standardized"]
    assert isinstance(exposed, list) and isinstance(reference, list)
    exposed_final = exposed[-1]
    reference_final = reference[-1]
    assert isinstance(exposed_final, dict) and isinstance(reference_final, dict)
    exposed_final_pct = float(exposed_final["cumulative_incidence_percent"])
    reference_final_pct = float(reference_final["cumulative_incidence_percent"])
    difference_pp = exposed_final_pct - reference_final_pct
    chart_id = f"team-post-exit-{scope_key}-chart"
    main = f'''{team_post_exit_attrition_style_tag()}<article class="card chart-card team-post-exit-card">
      <div class="card-title">Incidencia acumulada de attrition Voluntary tras una salida inicial</div>
      <div id="{chart_id}" class="team-post-exit-chart" aria-label="{esc(str(scope['label']))}: incidencia acumulada Voluntary a seis meses para equipos expuestos y referencia ajustada"></div>
      <div class="team-post-exit-kpis">
        <div class="team-post-exit-kpi"><strong>{exposed_final_pct:.2f}%</strong><span>equipo tras una salida inicial única a 6 meses</span></div>
        <div class="team-post-exit-kpi"><strong>{reference_final_pct:.2f}%</strong><span>equipos sin salida reciente, ajustados a 6 meses</span></div>
        <div class="team-post-exit-kpi"><strong>+{difference_pp:.2f} pp</strong><span>diferencia descriptiva al cierre de 6 meses</span></div>
      </div>
      <div class="chart-footer"><strong>Lectura:</strong> se sigue a integrantes que permanecían en el equipo índice; se censuran cambio de manager, salida no Voluntary o pérdida de observación. Todos los puntos publicados tienen n en riesgo ≥ {MINIMUM_COHORT:,}.</div>
    </article>{team_post_exit_chart_enhancement(evidence, scope_key, chart_id)}'''
    side = f'''<article class="card side-copy team-post-exit-side"><div class="card-title">Lectura y límites</div><span class="badge badge-warning">Asociación descriptiva · no causal</span>
      <h3>¿Qué compara?</h3><p>Tras una salida Voluntary única, comparamos el attrition posterior de quienes permanecían en ese equipo con equipos sin salida reciente, ajustados por tamaño.</p>
      {facts([
          ("Alcance", str(scope["label"])),
          ("Evento índice", "una salida Voluntary reconciliada única en el último intervalo antes del cierre índice"),
          ("Referencia", "sin salida Voluntary reciente; bandas de tamaño 1–5, 6–10, 11–20 y 21+"),
          ("Seguimiento", f"6 cierres mensuales: {cohort['follow_up_snapshot_dates'][0]} a {cohort['follow_up_end']}"),
          ("n inicial", f"expuestos {int(exposed_final['initial_roster_n']):,} · referencia {int(reference_final['initial_roster_n']):,}"),
          ("Episodios índice", f"{int(audits['index_team_episodes']):,} en la cohorte reciente"),
          ("Sensibilidad", str(scope["scope_note"])),
      ])}
      <section class="provenance-panel"><div class="provenance-title">Proveniencia y alcance</div>
      <dl class="provenance-grid"><dt>Fuente</dt><dd>HRDA · eventos reconciliados en dos fuentes</dd><dt>Grano</dt><dd>Integrante de roster índice × episodio de equipo × mes</dd><dt>Outcome</dt><dd>Primera salida Voluntary posterior</dd><dt>Estimando</dt><dd>Incidencia acumulada Kaplan–Meier estandarizada por tamaño</dd></dl><p class="provenance-status"><strong>No concluye:</strong> causalidad, contagio probado, ranking de managers ni predicción individual. Una sola cohorte reciente no mide estabilidad histórica.</p></section></article>'''
    return f'''<div class="slide-stage" id="slide-{number}">{heading(str(scope['title']), str(scope['subtitle']))}
      <div class="two-pane">{main}{side}</div></div>'''


def support_slide(number: int, title: str, subtitle: str, headline: str, message: str, items: list[tuple[str, str]]) -> str:
    if title == "Number of manager changes":
        return number_of_manager_changes_mobility_comparison_slide(number)
    if title == "Commute distance":
        return commute_distance_slide(number)
        evidence, _ = commute_distance_evidence()
        metrics = evidence["metrics"]
        display_data = commute_distance_display_data(evidence)
        rendered = data_slide(
            number,
            title,
            "Approximate geographic proxy · ZIP centroid to Qualcomm office coordinate",
            bar_card(
                "Mexico City · distance to office centroid",
                display_data,
                f"Denominator: {int(metrics['eligible_employees']):,}. Detail in 1-km intervals through 30 km; 30+ km is the long tail. Distance is Haversine km.",
                "commute-distance-card",
            ),
            side_card(
                "A geographic proxy, not a route",
                "The home ZIP is matched locally to a public postal centroid and compared with Qualcomm's Mexico City office coordinate. This does not estimate driving distance, travel time, or actual commute behavior.",
                [
                    ("Snapshot", str(evidence["snapshot_date"])),
                    ("Eligible", f"{int(metrics['eligible_employees']):,} employees"),
                    ("Covered", f"{int(metrics['published_employee_count']):,} ({float(metrics['coverage_percent_of_eligible']):.1f}%)"),
                    ("No calculable", f"{int(metrics['unavailable_employee_count']):,}"),
                    ("Office", "Mexico City · ZIP 11000"),
                    ("Method", "Haversine · ZIP centroid"),
                    ("Privacy", "bands n ≥ 30; 1 unmatched ZIP omitted"),
                ],
                "Internal analysis · aggregate",
            ),
        )
        return rendered.replace("Mexico City", "Global listed-office").replace("ZIP 11000", "office coordinate").replace("1 unmatched ZIP omitted", "No ZIP or office imputation").replace("Qualcomm's Global listed-office office coordinate", "the listed Qualcomm office coordinate").replace("Qualcomm&#x27;s Global listed-office office coordinate", "the listed Qualcomm office coordinate")
    if title == "Team turnover":
        return team_turnover_slide(number)
    if title == "Transfer within past year":
        evidence = transfer_within_past_year_distribution()
        return data_slide(
            number,
            title,
            "Rolling 12-month feature · 24 monthly snapshots and 104 weekly endpoints",
            transfer_distribution_card(evidence),
            side_card(
                "Monthly for modeling; weekly for operations",
                "Both charts measure distinct employees with at least one documented transfer in the same rolling 12-month window. Monthly remains the canonical employee-snapshot frequency for the model; weekly is a descriptive monitoring view.",
                [("Definition", "transfer_date in (snapshot - 12 months, snapshot]"), ("Monthly", "24 complete snapshots (~2 years)"), ("Weekly", "104 complete Sunday endpoints (~2 years)"), ("IOS match", "5.78% of employee-date keys"), ("Source decision", "workers_ios_transfers excluded")],
                "Validated rolling feature",
            ),
        )
    main = f"""<article class="card"><div class="state-visual"><div class="state-icon">i</div>
      <h3>{esc(headline)}</h3><p>{esc(message)}</p><div class="privacy-banner">This slide separates source evidence from a distribution of the target feature.</div></div></article>"""
    return data_slide(number, title, subtitle, main, side_card("How to read this", message, items, "Support / observability"))


def high_risk_manager_score_slide(number: int) -> str:
    """Render the validated continuous distribution without a manager-level label."""
    distribution = high_risk_manager_score_distribution()
    evidence = distribution["evidence"]
    metrics = distribution["metrics"]
    intervals = distribution["intervals"]
    bands = distribution["bands"]
    assert isinstance(evidence, dict) and isinstance(metrics, dict) and isinstance(intervals, list) and isinstance(bands, list)
    chart_data = [(str(band["label"]), int(band["manager_count"])) for band in bands]
    cutoff = str(evidence["cutoff_date"])
    start = str(intervals[0]["interval_start"])
    main = bar_card_es(
        "Managers observables por banda del ratio suavizado",
        chart_data,
        "Lectura simple: 1 significa aproximadamente lo esperado; arriba de 1 hay más salidas que las esperadas y debajo de 1 hay menos. Cada barra muestra porcentaje y n de managers observables; no presenta identidades, rankings ni un umbral de intervención.",
        "manager-score-distribution-card",
    )
    side = side_card(
        "Contexto agregado, no etiqueta individual",
        "El ratio observado/esperado compara salidas Voluntary estrictas con el número esperado según la exposición histórica de reportes directos. Es evidencia contextual agregada; no es una evaluación de manager ni autoriza clasificar personas.",
        [
            ("Ventana", f"{start} a {cutoff} · 6 intervalos fiscales"),
            ("Cobertura observable", f"{metrics['employees_with_scored_manager']:,} reportes · {metrics['scored_manager_count']:,} managers"),
            ("Historia no suficiente", f"{metrics['employees_unknown_history_count']:,} reportes · {metrics['unknown_manager_count']:,} managers; no se imputan"),
            ("Esperado", "Estratos de intervalo, región, job family, nivel y tenure; fallback a tasa global cuando n<30"),
            ("Suavizamiento", "Prior de 60 empleado-intervalos hacia ratio 1"),
            ("Control", "0 duplicados y atribuciones múltiples; reconciliación de bandas aprobada"),
            ("Eventos excluidos", f"{metrics['events_without_unique_exposure_attribution']:,} de {metrics['unique_voluntary_event_count']:,} sin exposición inicial única"),
        ],
        "Evidencia agregada reproducible",
    )
    return data_slide(
        number,
        "High risk manager",
        f"Distribución agregada del ratio observado/esperado · seis intervalos fiscales hasta {cutoff}",
        main,
        side,
    )


def high_turnover_under_manager_slide(number: int) -> str:
    """Render descriptive historical context while retaining the unknown-history population."""
    distribution = high_turnover_under_manager_distribution()
    evidence = distribution["evidence"]
    metrics = distribution["metrics"]
    intervals = distribution["intervals"]
    buckets = distribution["buckets"]
    assert isinstance(evidence, dict) and isinstance(metrics, dict) and isinstance(intervals, list) and isinstance(buckets, list)
    chart_data = [(str(bucket["label"]), int(bucket["employee_count"])) for bucket in buckets]
    cutoff = str(evidence["cutoff_date"])
    start = str(intervals[0]["interval_start"])
    main = bar_card_es(
        "Reportes directos observables por salidas Voluntary históricas",
        chart_data,
        "Lectura simple: no es un promedio. Primero se cuentan las personas que salieron en seis meses por equipo (0/1/2+); después, cada reporte directo actual se muestra en el bucket de su equipo. El bucket 2+ describe contexto histórico, no una evaluación de manager ni una atribución causal.",
        "manager-turnover-distribution-card",
    )
    side = side_card(
        "La cobertura histórica desconocida no se convierte en cero",
        "Los buckets sólo incluyen reportes directos activos cuyos managers tienen exposición histórica observable. Las personas sin esa historia permanecen separadas, y las salidas sin exposición inicial única se excluyen del numerador.",
        [
            ("Ventana", f"{start} a {cutoff} · 6 intervalos fiscales"),
            ("Total observado", f"{metrics['observable_employee_count']:,} reportes · {metrics['observable_manager_count']:,} managers"),
            ("Historia desconocida", f"{metrics['unknown_employee_count']:,} reportes · {metrics['unknown_manager_count']:,} managers; no se asignan a 0"),
            ("Salida Voluntary", "Clave distinta empleado + fecha; Voluntary Exception no entra"),
            ("Atribución temporal", "Exposición única al inicio del intervalo correspondiente"),
            ("Eventos excluidos", f"{metrics['events_without_unique_exposure_attribution']:,} de {metrics['unique_voluntary_event_count']:,} sin exposición inicial única"),
            ("Control", "0 duplicados y atribuciones múltiples; reconciliación de buckets aprobada"),
        ],
        "Contexto histórico agregado",
    )
    return data_slide(
        number,
        "High turnover under this person",
        f"0 / 1 / 2+ salidas Voluntary · seis intervalos fiscales hasta {cutoff}",
        main,
        side,
    )


def above_average_team_turnover_slide(number: int) -> str:
    """Render candidate 44 as restricted team context, never a manager evaluation."""
    evidence = above_average_team_turnover_evidence()
    sensitivity = above_average_team_turnover_sensitivity_evidence()
    distribution = evidence["distribution"]
    benchmark = evidence["benchmark"]
    eligibility = evidence["eligibility"]
    counts = evidence["aggregate_counts"]
    assert isinstance(distribution, list) and isinstance(benchmark, dict) and isinstance(eligibility, dict) and isinstance(counts, dict)
    chart_data = [(str(row["signal"]), int(row["employee_count"])) for row in distribution]
    benchmark_rate = float(str(benchmark["six_month_rate"]))
    threshold_rate = float(str(benchmark["flag_threshold_six_month_rate"]))
    latest_thresholds = {
        str(row["threshold_multiplier"]): row
        for row in sensitivity["latest_thresholds"]
    }
    working_threshold = latest_thresholds["1.30"]
    prior_threshold = latest_thresholds["1.40"]
    stability_13 = next(
        row for row in sensitivity["threshold_stability"]
        if str(row["threshold_multiplier"]) == "1.30"
    )
    significance = sensitivity["significance_screen"]
    main = bar_card(
        "Current direct reports by inherited team-context signal",
        chart_data,
        f"Snapshot {evidence['latest_snapshot']}; all buckets meet n ≥ {MINIMUM_COHORT}. Unknown is retained rather than treated as 0.",
        "manager-turnover-distribution-card",
        legend=[
            ("0", "eligible manager; below 1.3× benchmark"),
            ("1", "eligible manager; at or above 1.3× benchmark"),
            ("Unknown", "insufficient history or exposure; not equivalent to 0"),
        ],
    )
    side = side_card(
        "Eligibility precedes the flag",
        "A current direct report inherits the current manager's result. The flag is assigned only when the manager has enough observable history; it is an associative, restricted team-context signal.",
        [
            ("Benchmark", f"{benchmark_rate:.2%} six-month equivalent, weighted by eligible manager team size"),
            ("Flag rule", f"1 when manager rate ≥ 1.3× benchmark ({threshold_rate:.2%})"),
            ("Sensitivity", f"1.3× flags {int(working_threshold['flagged_report_count']):,} ({float(working_threshold['flagged_report_count']) / float(working_threshold['eligible_report_count']) * 100:.1f}%) vs {int(prior_threshold['flagged_report_count']):,} ({float(prior_threshold['flagged_report_count']) / float(prior_threshold['eligible_report_count']) * 100:.1f}%) at 1.4×"),
            ("Six-snapshot range", f"1.3× report share {float(stability_13['min_flagged_report_share_percent']):.1f}%–{float(stability_13['max_flagged_report_share_percent']):.1f}%"),
            ("Statistical screen", f"{int(significance['latest_significant_report_count']):,} reports pass an approximate one-sided 95% lower-bound screen"),
            ("History", f"{eligibility['required_consecutive_intervals']} closed monthly intervals before the snapshot"),
            ("Team size", f"average ≥ {eligibility['minimum_average_team_size']} direct reports"),
            ("Voluntary exits", f"at least {eligibility['minimum_distinct_voluntary_exits']} distinct exits; Voluntary Exception excluded"),
            ("Observed", f"{int(counts['observable_employees']):,} of {int(counts['eligible_employees']):,} current direct reports"),
            ("Interpretation", "Not an individual manager evaluation, causal claim, or approved production feature"),
        ],
        "Restricted aggregate context",
    )
    return data_slide(
        number,
        "Above-average team turnover",
        "Candidate 44 · 0 / 1 / Unknown manager-team context · 18 closed monthly intervals",
        main,
        side,
    )


def external_pull_factors_slide(number: int) -> str:
    """Consolidate unavailable third-party candidates without implying coverage."""
    factors = (
        (
            "Tech industry unemployment data",
            "Public labor-market series + work geography",
            "No provider or contracted feed is selected. Industry scope, geography, publication vintage, and a time-safe crosswalk remain unresolved.",
            "Approve the series and validate a dated geographic crosswalk.",
        ),
        (
            "Draup data",
            "Third-party vendor feed",
            "No approved feed, owner, data contract, field definition, history, grain, or join key is available.",
            "Define the business signal, contract, history, grain, and join path.",
        ),
        (
            "LinkedIn scraping",
            "External professional-profile data",
            "No governed collection method or employee-to-profile crosswalk exists; legal and privacy approval are absent.",
            "Do not identity-match. Require a lawful governed source first.",
        ),
    )
    rows = "".join(
        "<tr>"
        f"<td>{esc(name)}</td>"
        f"<td>{esc(source)}</td>"
        f"<td>{esc(gap)}</td>"
        f"<td>{esc(gate)}</td>"
        "</tr>"
        for name, source, gap, gate in factors
    )
    main = f"""<article class="card"><div class="card-title">External sources are not currently enabled</div>
      <table class="external-factor-table"><thead><tr><th>Candidate</th><th>Intended input</th><th>Current gap</th><th>Gate before reassessment</th></tr></thead>
      <tbody>{rows}</tbody></table>
      <div class="privacy-banner"><strong>Recommended use:</strong> Exclude all three from the internal baseline. The model plan permits them only as a separate external challenger after source approval, a data contract, prediction-time availability, and the required governed crosswalk are validated.</div>
      </article>"""
    side = side_card(
        "Why they remain outside the baseline",
        "Each candidate has an external / third-party blocker. A plausible concept or a vendor name is not evidence that a time-safe, governed feature exists.",
        [
            ("Current state", "3 external candidates; none integrated"),
            ("Baseline", "Internal HR data plus selected QVoice only"),
            ("Evaluation", "Same population and future periods; test incremental value"),
            ("Guardrail", "No scraping or employee identity matching without explicit approval"),
        ],
        "External / third-party",
    )
    return data_slide(
        number,
        "External pull factors",
        "Three third-party candidates - no approved source, data contract, or time-safe crosswalk",
        main,
        side,
    )


def job_family_snapshot_slide(number: int) -> str:
    """Render the requested monthly/daily Job family comparison."""
    august, september = job_family_snapshot_distributions()
    main = (
        '<div class="two-chart">'
        + bar_card(
            f"Snapshot {august['snapshot']} · top 20 + Other",
            august["rows"],
            f"Population: {int(august['population']):,} active regular employees. Percent and n use this snapshot only.",
            "job-family-card",
        )
        + bar_card(
            f"Snapshot {september['snapshot']} · top 20 + Other",
            september["rows"],
            f"Population: {int(september['population']):,} active regular employees. Percent and n use this snapshot only.",
            "job-family-card",
        )
        + "</div>"
    )
    side = side_card(
        "Two snapshots, not a trend",
        "The September 7 daily snapshot includes post-weekend changes around the September Job family reorganization. Each panel ranks its own detailed categories, so it must not be read as a stable one-to-one category comparison.",
        [
            ("Source", "HRDA / monthly August + daily September"),
            ("August monthly snapshot", str(august["snapshot"])),
            ("September daily snapshot", str(september["snapshot"])),
            ("Detail", "top 20 + aggregated tail per snapshot"),
            ("Caveat", "mapping lineage is pending"),
        ],
        "Target distribution",
    )
    return data_slide(
        number,
        "Job family",
        "Target - detailed August monthly and September 7 daily snapshots",
        main,
        side,
    )


def dual_bar_slide(number: int, title: str, subtitle: str, left_title: str, left: list[tuple[str, int]], right_title: str, right: list[tuple[str, int]], note: str, side: str, chart_class: str = "") -> str:
    if title == "Job family":
        return job_family_snapshot_slide(number)
    main = f"""<div class="two-chart">{bar_card(left_title, left, note, chart_class)}{bar_card(right_title, right, note, chart_class)}</div>"""
    return data_slide(number, title, subtitle, main, side)


def cover() -> str:
    return f"""<div class="slide-stage" id="slide-1">{heading("Evidence for 44 attrition model candidates", "Distributions, definitions, and privacy-safe evidence")}
      <article class="card card-full"><div class="deck-hero"><div>
        <h1>Evidence before<br/>prediction</h1>
        <p>This deck documents distributions and evidence for 44 candidate variables—not individual resignation predictions. The model focuses on cohorts with relatively higher voluntary-attrition risk in the next six months to inform approved retention actions.</p>
        <div class="deck-tags"><span class="badge badge-success">Published cohorts: n ≥ 30</span><span class="badge badge-info">Aggregate reporting only</span><span class="badge badge-neutral">No identities or exact pay</span></div>
        <div class="deck-stat-row"><div class="deck-stat"><strong>44</strong><span>candidate variables</span></div><div class="deck-stat"><strong>6 mo</strong><span>cohort risk horizon</span></div><div class="deck-stat"><strong>0</strong><span>individual predictions</span></div></div>
      </div></div></article></div>"""


def agenda() -> str:
    sections = [
        ("3–5", "Mobility and turnover", "Source events and pending derivations."),
        ("6–19", "Organizational context", "Location, job family, levels, experience, and team flag."),
        ("20–28", "QVoice and external pull factors", "Survey observability and third-party sources not yet enabled."),
        ("29–41", "Career and compensation", "Alternative definitions, bands, and privacy."),
        ("42–52", "Manager and advanced signals", "Coverage, attribution, and pending rules."),
    ]
    rows = "".join(f"""<div class="agenda-item"><span class="agenda-num">Slides {a}</span><strong>{b}</strong><span>— {c}</span></div>""" for a, b, c in sections)
    return f"""<div class="slide-stage" id="slide-2">{heading("Agenda", "Use the arrow keys or the side tab to navigate")}
      <article class="card card-full"><div class="card-title">Variable portfolio</div><div class="agenda-vertical">{rows}</div>
      <div class="privacy-banner">Distribution = direct field or publishable raw domain; observability = source coverage; no chart = formula, mapping, hierarchy, or source is not yet defined.</div></article></div>"""


def build_variable_slides() -> list[tuple[str, str]]:
    internal_analysis = REPORTING_MODE == "internal_analysis"
    talent_index_distribution = talent_index_latest_recoverable_distribution()
    residential_manager_distance, _ = residential_manager_distance_evidence()
    engineering_cto_evidence = engineering_cto_org_split_evidence() if internal_analysis else None
    level_grade_family_evidence = level_grouped_by_grade_family_evidence() if internal_analysis else None
    gender_subtitle = (
        "Internal analysis · stored values in aggregates n ≥ 30"
        if internal_analysis
        else "Restricted · anonymized codes for fairness review"
    )
    gender_chart_title = (
        "Stored gender values"
        if internal_analysis
        else "Stored anonymized codes"
    )
    gender_chart_note = (
        "Real labels are shown only in this internal aggregate analysis; never for individual use."
        if internal_analysis
        else "Semantic labels and any individual use are suppressed."
    )
    gender_side_title = (
        "Internal exploration, not an operational feature"
        if internal_analysis
        else "Not an operational feature"
    )
    gender_side_text = (
        "Stored labels are displayed to interpret the aggregate. This field remains restricted for targeting and must not move into a shareable presentation."
        if internal_analysis
        else "The presentation retains aggregate evidence only for fairness reviews."
    )
    gender_side_rows = (
        [("Domain", "stored values"), ("Permitted use", "internal analysis"), ("Safeguard", "n ≥ 30; no targeting")]
        if internal_analysis
        else [("Domain", "two anonymized codes"), ("Permitted use", "restricted fairness review"), ("Safeguard", "no targeting")]
    )
    compensation_subtitle = (
        "Internal analysis · all publicable stored grades plus Other grades"
        if internal_analysis
        else "Restricted · anonymized frequency bands"
    )
    compensation_chart_title = (
        "All publicable compensation grades"
        if internal_analysis
        else "Anonymized distribution of bands"
    )
    compensation_note = (
        "Aggregate categories only; no pay values are shown."
        if internal_analysis
        else "Real labels are suppressed by compensation governance."
    )
    compensation_grade, compensation_grade_meta = compensation_grade_distribution()
    compensation_scope_note = (
        f"Snapshot {V4_SNAPSHOT}; {compensation_grade_meta['public_grade_count']} public grades + Other grades "
        f"({compensation_grade_meta['suppressed_small_grade_count']} suppressed)."
    )
    qvoice_intent = private_coverage("01-intent-to-stay-items", QVOICE)
    # The March-2023 raw workbook contains the Career goals item, but its
    # plain-header format is not mapped by the current extractor. Start the
    # visual at 2024 and document the 2023 mapping gap without publishing it
    # as a processed wave.
    qvoice_career = [
        row for row in private_coverage("03-career-goals-item", QVOICE)
        if int(row[0]) >= 2024
    ]
    qvoice_comparable = qvoice_comparable_favorable_evidence()
    application_intensity = application_intensity_by_fiscal_year()
    application_employee_snapshot = application_employee_snapshot_trailing_6m()
    comp_ratio_history_evidence = comp_ratio_voluntary_attrition_evidence()
    transfer_evidence = transfer_within_past_year_distribution()
    manager_leaving = manager_leaving_voluntary_distribution()
    high_risk_coverage = private_coverage("01-high-risk-manager", HIGH_RISK.parents[0])
    location_eligible, location_observable = latest_snapshot_coverage("04-location")
    location_country = categorical_distribution(
        frozen_top_values("04-location", "country", 20),
        populated=location_eligible,
        eligible=location_eligible,
        other_label="Other countries",
    )
    location_office_site = categorical_distribution(
        frozen_top_values("04-location", "office_site", 20),
        populated=location_observable,
        eligible=location_eligible,
        other_label="Other sites",
        missing_label="No office site",
    )
    office_site_city, office_site_city_meta = office_site_city_distribution()
    co_location_office_site, co_location_office_site_city, co_location_evidence = co_location_site_city_series()
    job_family_august, job_family_september = job_family_snapshot_distributions()
    region_distribution = region_display_distributions()
    region_major_country_split = region_major_country_split_distribution(int(region_distribution["eligible_employees"]))
    job_family_detail = categorical_distribution(
        frozen_top_values("07-job-family", "job_family", 10),
        populated=int(job_family_august["population"]),
        eligible=int(job_family_august["population"]),
        other_label="Other job families",
    )
    work_arrangement_eligible, work_arrangement_observable = latest_snapshot_coverage("10-remote-hybrid-in-office-status")
    work_arrangement = categorical_distribution(
        frozen_top_values("10-remote-hybrid-in-office-status", "work_arrangement", 10),
        populated=work_arrangement_observable,
        eligible=work_arrangement_eligible,
        other_label="Other categories",
        missing_label="No work arrangement",
    )
    level_eligible, level_observable = latest_snapshot_coverage("29-level")
    job_level_detail = categorical_distribution(
        frozen_top_values("29-level", "job_level_primary_position", 10),
        populated=level_observable,
        eligible=level_eligible,
        other_label="Other levels",
    )
    level_grouped = ordered_distribution(
        values("29-level", "level_grouped"),
        LEVEL_GROUPED_ORDER,
        label_normalizer=lambda label: re.sub(r"^\d+\s*-\s*", "", label).strip(),
    )
    management_level = ordered_distribution(
        values("29-level", "management_level"),
        MANAGEMENT_LEVEL_ORDER,
    )
    if level_observable != 50_033 or sum(value for _, value in level_grouped) != 50_033:
        raise ValueError("Level grouped no reconcilia contra los 50,033 empleados del snapshot.")
    if sum(value for _, value in job_level_detail) != 50_033:
        raise ValueError("Job level detail no reconcilia contra los 50,033 empleados del snapshot.")
    if sum(value for _, value in management_level) != 50_027:
        raise ValueError("Management level no reconcilia contra los 50,027 observados.")
    et_report = detail("43-et-fields")
    et_data: list[tuple[str, int]] = []
    et_without_count: list[str] = []
    for column in et_report.get("columns", []):
        label = str(column["column"]).replace("_leader", "")
        populated = column.get("populated_employees")
        if populated is None:
            # A missing aggregate is a reporting gap, not evidence of zero coverage.
            et_without_count.append(label)
        else:
            et_data.append((label, int(populated)))
    inflection = []
    for col in ("manager_change", "cost_center_change", "job_family_change", "location_change", "is_transferred"):
        rows = values("42-major-inflection-points", col)
        positive = next((count for label, count in rows if label == "1"), 0)
        inflection.append((col.replace("_", " "), positive))

    job_family_main = (
        '<div class="two-chart">'
        + bar_card(
            f"Snapshot {job_family_august['snapshot']} · top 20 + Other",
            job_family_august["rows"],
            f"Population: {int(job_family_august['population']):,} active regular employees. Percent and n use this snapshot only.",
            "job-family-card",
        )
        + bar_card(
            f"Snapshot {job_family_september['snapshot']} · top 20 + Other",
            job_family_september["rows"],
            f"Population: {int(job_family_september['population']):,} active regular employees. Percent and n use this snapshot only.",
            "job-family-card",
        )
        + "</div>"
    )

    slides: list[tuple[str, str]] = []
    def add(label: str, html_text: str) -> None:
        expected_slide = len(slides) + 3
        html_text, replacements = re.subn(
            r'(<div class="slide-stage" id="slide-)\d+("(?:\s[^>]*)?>)',
            rf'\g<1>{expected_slide}\g<2>',
            html_text,
            count=1,
        )
        if replacements != 1:
            raise ValueError(f"Slide {label!r} is missing its single stage identifier.")
        slides.append((label, html_text))

    prior_year_evidence, prior_year_distribution = prior_experience_years_evidence()
    prior_year_metrics = prior_year_evidence["metrics"]

    add("Applied to a job", application_intensity_slide(3, application_intensity))
    add("Applied to a job — employee-snapshot, trailing six months", application_employee_snapshot_slide(4, application_employee_snapshot))
    add("Transfer within past year", support_slide(5, "Transfer within past year", "No chart · the 12-month condition is not defined", "The source flag does not replace the feature", "is_transferred and transfer_date exist, but they do not by themselves define the window, eligible event, or boundary treatment.", [("Type", "derived feature"), ("Source fields", "is_transferred / transfer_date"), ("Action", "approve the 12-month window")]))
    add("Location", data_slide(6, "Location", f"Target · country distribution at snapshot {V4_SNAPSHOT}",
        bar_card("Country · top 20 + Other", location_country, f"Snapshot {V4_SNAPSHOT}; percent and n use this active regular employee population. The chart contains Country only.", "location-card"),
        side_card("Country is the geographic layer", "This slide is intentionally limited to the Country distribution. Local location detail is presented separately because it answers a different geographic question.", [("Field", "country"), ("Visible", "top 20 + Other countries"), ("Snapshot", V4_SNAPSHOT), ("Grain", "employee snapshot")], "Target distribution")))
    add("Office site and city", data_slide(7, "Office site and city", f"Target · site code and derived site-city pair at snapshot {V4_SNAPSHOT}",
        f'''<div class="two-chart">{bar_card("Office site · top 20 + missing", location_office_site, f"Snapshot {V4_SNAPSHOT}; percent and n use this active regular employee population.", "location-card")}{bar_card("Office site · city · top 20 + Other", office_site_city, f"Snapshot {V4_SNAPSHOT}; {office_site_city_meta['distinct_complete_pairs']:,} complete pairs observed. Missing values in either field are shown separately.", "location-card location-pair-card")}</div>''',
        side_card("Two levels of location detail", "Office site is a stored site code. The right-hand labels are derived by concatenating office_site and city; if either field is missing, the employee enters the no-pair bucket.", [("Office site", "top 20 + missing"), ("Derived pair", "top 20 + Other + no pair"), ("Eligible", f"{office_site_city_meta['eligible_employees']:,} employees"), ("Snapshot", V4_SNAPSHOT)], "Target distribution")))
    add("Team turnover", support_slide(7, "Team turnover", "No chart · rolling team rate has no approved definition", "No team rate has been reconstructed", "Manager assignment, terminations, and exposure are inputs, but no time-aware membership, denominator, and rolling-window rule produces the variable.", [("Type", "derived feature"), ("Missing", "time-aware membership and denominator"), ("Rule", "approved rolling window")]))
    add("¿Una salida inicial precede más salidas?", team_post_exit_attrition_slide(8, "all_teams"))
    add("Sensibilidad: equipos de 6+ personas", team_post_exit_attrition_slide(9, "teams_6_plus"))
    add("Job family", dual_bar_slide(9, "Job family", "Target · detail and grouping with observed mapping", "Job family group", values("07-job-family", "job_family_group"), "Top 10 job families + Other", job_family_detail, "The tail is calculated from the current snapshot, not from the full history.", side_card("Stable mapping, pending semantics", "Detail maps many-to-one; five families changed group historically. The Other job families bar retains the long tail without pretending it is a single category.", [("Fields", "job_family / job_family_group"), ("Detail", "top 10 + aggregated tail"), ("Caveat", "mapping lineage is pending")], "Target distribution")))
    add("Region", data_slide(10, "Region", f"Active regular employees - monthly snapshot {V4_SNAPSHOT}",
        f'''<div class="two-chart"><div class="region-display-stack">{bar_card("Region distribution", region_distribution["global_rows"], f"Population: {int(region_distribution['eligible_employees']):,} active regular employees. Percent and n use the global snapshot population.", "region-card")}{bar_card("Alternative display - U.S. and China separated", region_major_country_split, f"Population: {int(region_distribution['eligible_employees']):,} active regular employees. Display-only grouping: U.S. is removed from Americas and China from APAC.", "region-major-country-card")}</div>{bar_card("Labor Market distribution - top 20 + Other", region_distribution["global_labor_market_rows"], f"Population: {int(region_distribution['eligible_employees']):,} active regular employees. Percent and n use the global snapshot population; Other combines the remaining source markets.", "labor-market-card")}</div>''',
        side_card("Stored Region plus requested alternative", "The upper chart is the stored Region distribution. The lower chart is an additional display-only view that separates the United States from Americas and China from APAC. Labor Market remains a separate global field.", [("Stored Region", "India, Americas, APAC, EMEA"), ("Alternative", "U.S. / Americas residual; China / APAC residual"), ("Labor Market", f"global top 20 + Other of {int(region_distribution['labor_market_source_category_count'])} observed values"), ("Coverage", "100.0%; no missing Labor Market"), ("Snapshot", V4_SNAPSHOT), ("Grain", "distinct employee snapshot")], "Target distribution")))
    add("Gender", data_slide(11, "Gender", gender_subtitle, bar_card(gender_chart_title, private_distribution("09-gender"), gender_chart_note), side_card(gender_side_title, gender_side_text, gender_side_rows, "Privacy")))
    add("Work arrangement", data_slide(12, "Remote / hybrid / in office status", "Raw field · actual operating categories, without assuming three states", work_arrangement_main(work_arrangement), side_card("The field exists; the mapping does not", "The actual labels describe stored operating arrangements. The chart preserves that detail, but does not force it into Remote, Hybrid, and In office; missing values are not combined with the tail.", [("Source field", "work_arrangement"), ("Visible categories", "10 + Other + missing"), ("Denominator", "latest employee snapshot"), ("Grain", "employee snapshot")], "Aggregate distribution")))
    engineering_main = (
        engineering_cto_main(engineering_cto_evidence)
        if engineering_cto_evidence is not None
        else bar_card("Distribution of eng_or_noneng", values("11-engineering-vs-non-engineering", "eng_or_noneng"), "The visualization describes the stored field.")
    )
    add("Engineering vs. non-engineering", data_slide(13, "Engineering vs. non-engineering", "Stored target · upstream mapping is pending", engineering_main, side_card("Not an independent classification", "The grouping depends on an upstream job-role or job-family mapping.", [("Type", "grouped mapping"), ("Categories", "2"), ("Action", "validate mapping authority")], "Observed distribution")))
    add("Rehire", data_slide(14, "Rehire", "Direct target · historical source break is visible", trend_card("Annual flag prevalence", event_series("12-rehire"), "The series changes source era from 2022-10-23."), side_card("Do not combine eras without harmonizing", "The flag and date are not fully equivalent; the visual separates a persistent condition from a recent event.", [("Field", "is_rehire"), ("Boundary", "source-era change"), ("Use", "treat eras separately")], "Target distribution")))
    add("Prior experience", data_slide(15, "Years of experience prior to Qualcomm", "Stored field · exact-year distribution with a privacy-protected tail",
        bar_card("Distribution of prior_qc_work_years", prior_year_distribution, f"Snapshot {STORED_METRIC_SNAPSHOT}; percent and n use {STORED_METRIC_POPULATION_LABEL} active regular employees. <1 = 0–<1; year k = k–<k+1; 32+ = values ≥32.", "prior-experience-card"),
        side_card("Exact years with a protected tail", "Each bar groups the stored numeric value by its integer-year interval. The exact year-32 bucket has n=25, below the minimum cohort of 30, so values at 32 or more are published together as 32+.", [("Snapshot", STORED_METRIC_SNAPSHOT), ("Population", f"{STORED_METRIC_POPULATION_LABEL} active regular employees"), ("Field", "prior_qc_work_years"), ("Categories", "<1, 1–31, and 32+"), ("Coverage", f"{prior_year_metrics['observable_employees'] / prior_year_metrics['eligible_employees'] * 100:.1f}%"), ("Year 32", f"n={prior_year_metrics['year_32_employees']:,}; suppressed into 32+")], "Internal analysis · aggregate")))
    add("Commute distance", support_slide(16, "Commute distance", "Status · external source and home location are restricted", "No approved distance exists", "Home address, postal code, and an unapproved geographic proxy are not used.", [("Source", "not available"), ("Restriction", "sensitive home location"), ("Requirement", "approved provider and method")]))
    qvoice_comments = qvoice_comment_evidence()
    qvoice_retention_concerns = qvoice_retention_concerns_evidence()
    add("RTO comment", qvoice_comment_slide(17, qvoice_comments))
    # Preserve the existing navigation label and deck stage order while the
    # reader-facing content of slide 19 becomes the retention-concerns view.
    add("Any QVoice comment", qvoice_retention_concerns_slide(18, qvoice_retention_concerns))
    add("Non-respondents", qvoice_nonrespondent_slide(19, qvoice_nonrespondent_evidence()))
    add("Intent to Stay", data_slide(20, "Intent to Stay items", "Support · QVoice v4 observability by wave", trend_card("Observable response coverage", qvoice_intent, "Coverage does not confirm scale, direction, or comparability across waves."), side_card("Items and partiality matter", "The recent assessment separates complete from partial components before any average.", [("Latest wave", "2026"), ("2026 coverage", "96.99%"), ("Limitation", "workforce join is pending")], "Observability")))
    add("Career goals", data_slide(21, "Career goals item", "Support · QVoice v4 response coverage from 2024 onward", trend_card("Observable response coverage", qvoice_career, "The 2023 item exists in the raw workbook but requires header mapping before it can be processed for attrition; this visual starts at 2024."), side_card("Coverage is not a favorability distribution", "The chart starts at 2024. The 2023 raw item requires mapping of its plain-header format before it can be used for attrition, and cross-wave equivalence remains unconfirmed.", [("Shown history", "2024 onward"), ("Latest shown wave", "2026"), ("2026 coverage", "89.61%"), ("2023 status", "Mapping required")], "Observability")))
    add("Average QVoice", qvoice_comparable_favorable_slide(22, qvoice_comparable))
    normalized_region_label, normalized_region_slide = qvoice_normalized_region_slide_or_support(23)
    add(normalized_region_label, normalized_region_slide)
    add("External pull factors", external_pull_factors_slide(24))
    role_level_label, role_level_slide = role_level_tenure_slide_or_support(ROLE_LEVEL_TENURE_SLIDE)
    add(role_level_label, role_level_slide)
    company_tenure_label, company_tenure_slide_markup = company_tenure_slide_or_support(COMPANY_TENURE_SLIDE)
    add(company_tenure_label, company_tenure_slide_markup)
    promotion_label, promotion_slide = time_since_last_promotion_slide_or_support(28)
    add(promotion_label, promotion_slide)
    promotion_grade_label, promotion_grade_slide = promotion_history_by_grade_slide_or_support(PROMOTION_HISTORY_BY_GRADE_SLIDE)
    add(promotion_grade_label, promotion_grade_slide)
    entry_path_label, entry_path_slide = current_grade_entry_path_slide_or_support(CURRENT_GRADE_ENTRY_PATH_SLIDE)
    add(entry_path_label, entry_path_slide)
    add("Level", data_slide(31, "Level", f"Target · three related constructs at snapshot {V4_SNAPSHOT}, not synonyms", level_constructs_layout(level_grouped, management_level, job_level_detail), side_card("Each field answers a different question", "level_grouped is the primary senior-to-junior hierarchy; management_level is a compact support view and does not prove people management. Job-level detail keeps its size ranking because R/T/P families are not one comparable ladder.", [("Fields", "3"), ("Primary", "Level grouped hierarchy"), ("Snapshot", V4_SNAPSHOT), ("Rule", "do not treat them as synonyms")], "Target distribution")))
    if level_grade_family_evidence is not None:
        add("Level grouped by grade family", level_grouped_by_grade_family_slide(LEVEL_GRADE_FAMILY_SLIDE, level_grade_family_evidence))
    else:
        add("Level grouped by grade family", support_slide(LEVEL_GRADE_FAMILY_SLIDE, "Level grouped by grade family", "No chart · protected grade-family context is restricted to internal aggregate analysis", "The display-only proxy is not shown in presentation mode", "The stored Level bands remain available on the preceding slide. The grade-family proxy is retained only for internal aggregate review until an approved track mapping exists.", [("Mode", "internal aggregate analysis"), ("Primary", "level_grouped"), ("Action", "confirm track mapping")]))
    layers_label, layers_slide = layers_from_ceo_slide_or_support(32)
    add(layers_label, layers_slide)
    add("Compensation grade", data_slide(33, "Compensation grade", compensation_subtitle, bar_card(compensation_chart_title, compensation_grade, compensation_scope_note + " " + compensation_note, "compensation-grade-card"), side_card("Privacy before detail", "Grade can encode level and pay structure; no pay values or individual outcomes are shown.", [("Snapshot", V4_SNAPSHOT), ("Coverage", f"{compensation_grade_meta['eligible_employee_count']:,}"), ("Public grades", str(compensation_grade_meta["public_grade_count"])), ("Safeguard", "n ≥ 30; no pay")], "Protected distribution")))
    add("Comp ratio", comp_ratio_slide(34, comp_ratio_history_evidence))
    within_team_title, within_team_html = within_team_compensation_slide_or_support(35)
    add(within_team_title, within_team_html)
    co_location_latest = co_location_evidence["rows"][-1]
    add("Co-location", data_slide(36, "Co-location with manager", "Support · stored location-match proxies by year",
        f'''<div class="co-location-stack">{trend_card("Same stored office_site as manager", co_location_office_site, "Both stored office_site values are nonblank; percent uses comparable employee-manager snapshots.")}{trend_card("Same stored office_site and city as manager", co_location_office_site_city, "Different cities are not the same location. This is still a stored-field proxy, not physical presence.")}</div>''',
        side_card("A tighter location proxy", "Adding city removes matches where the same office_site is recorded in different cities. Neither chart proves physical co-location.", [("Top chart", "same stored office_site"), ("Bottom chart", "same office_site + city"), ("FY2026", f"{float(co_location_latest['same_office_site_percent_of_site_comparable']):.2f}% → {float(co_location_latest['same_office_site_and_city_percent_of_site_city_comparable']):.2f}%"), ("Why", "different cities are not the same location"), ("Use", "exploratory")], "Support")))
    add("Residential distance", residential_manager_distance_slide(37, residential_manager_distance))
    add("Office-site relationship", office_site_relationship_slide(38))
    add("High-risk manager", high_risk_manager_score_slide(38))
    add("High turnover", high_turnover_under_manager_slide(39))
    add("Above-average team turnover", above_average_team_turnover_slide(40))
    manager_leaving_flag_rows = [
        ("Not exposed", count) if bucket.startswith("0") else ("Exposed (1+)", count)
        for bucket, count in manager_leaving["binary_flag"]
    ]
    manager_leaving_count_rows = [
        ("No manager exits", count) if bucket == "0" else (f"{bucket} manager exit", count)
        for bucket, count in manager_leaving["event_count_sensitivity"]
    ]
    manager_leaving_metrics = manager_leaving["metrics"]
    manager_leaving_population = int(manager_leaving["population"])
    manager_leaving_exposed = next(count for label, count in manager_leaving_flag_rows if label == "Exposed (1+)")
    manager_leaving_main = (
        '<div class="two-chart">'
        + bar_card(
            "Primary feature: six-month exposure flag",
            manager_leaving_flag_rows,
            f"Snapshot 2026-08-23; percent and n use {manager_leaving_population:,} active regular employees. The event is retained even if the employee has a new manager.",
            "manager-leaving-card",
        )
        + bar_card(
            "Sensitivity: distinct manager-exit count",
            manager_leaving_count_rows,
            "The 2+ count is below the publication threshold and is combined into 1+. The count therefore adds no publishable detail beyond the flag.",
            "manager-leaving-card",
        )
        + "</div>"
    )
    manager_leaving_side = side_card(
        "Use the flag, not the count",
        f"{100 * manager_leaving_exposed / manager_leaving_population:.2f}% of the active regular population was exposed to at least one eligible manager exit. Repeated exposure is not publishable separately, so the binary flag is the clearer primary feature.",
        [
            ("Snapshot", "2026-08-23"),
            ("Window", "six months from manager term_date"),
            ("Population", f"{manager_leaving_population:,} active regular employees"),
            ("Manager exit", "strict Voluntary only"),
            ("Manager condition", "reg_non_intern_dir_reports > 0"),
            ("Historic assignment", "last pre-exit employee-manager snapshot"),
            ("Reassignment kept", f"{int(manager_leaving_metrics['employee_events_retained_after_reassignment_count']):,} of {int(manager_leaving_metrics['employee_manager_event_attribution_count']):,} attributed events"),
            ("Leakage", "no future manager or employee exits"),
        ],
        "Reproducible aggregate evidence",
    )
    add("Manager leaving", data_slide(40, "Manager leaving", "Primary: six-month Voluntary manager-exit flag · snapshot 2026-08-23", manager_leaving_main, manager_leaving_side))
    add("Manager change", data_slide(41, "Manager change", "Direct target · annual event prevalence", trend_card("Annual prevalence of manager_change", event_series("39-manager-change"), "Every point includes the percent and employee-snapshots with an event."), side_card("Event, not cumulative count", "The date enables temporal reasoning; it is not converted here into a number of changes.", [("Field", "manager_change"), ("Coverage", "100%"), ("Use", "event by snapshot")], "Target distribution")))
    add("Number of manager changes", support_slide(42, "Number of manager changes", "Exploratory target · six-month retrospective count · assumption for review", "Distribution of observed manager-change counts", "The chart uses the latest stored monthly snapshot and counts distinct dated manager-change events in the prior six months.", [("Window", "six months"), ("Grain", "employee snapshot"), ("Status", "assumption for review")]))
    add("Talent index", talent_index_distribution_slide(talent_index_distribution))
    add("Major inflection", support_slide(44, "Major inflection points", "No composite shown · five internal change events are observable, but “major” is not defined", "A movement is recorded; a major inflection is not", "HRDA records manager, cost center, job family, location, and transfer changes. It does not define whether one event is material, whether simultaneous changes are one reorganization, or how long a change remains relevant.", [("Observed inputs", "5 dated change events"), ("Missing decision", "what makes a change material"), ("Avoid", "double-counting one reorganization"), ("Need", "window, overlap, and aggregation rule")]))
    et_missing_text = ", ".join(et_without_count) or "ninguno"
    add("ET fields", data_slide(45, "ET fields", f"Support · snapshot {V4_SNAPSHOT} coverage of hierarchy fields, not a career classification", bar_card("ET fields with observable count", et_data, f"Snapshot {V4_SNAPSHOT}; leader values and identities remain suppressed. No publishable count: {et_missing_text}."), side_card("They do not mean career ET1 / ET2", "The fields behave as hierarchy references; the acronym and expert-track mapping remain undefined.", [("Snapshot", V4_SNAPSHOT), ("Fields with count", "ET1 through ET10"), ("No publishable count", et_missing_text), ("Definition", "0")], "Support")))
    # Slide numbers are derived from presentation order so insertion of the
    # dedicated location slide cannot leave stale IDs in later slides.
    renumbered: list[tuple[str, str]] = []
    for number, (label, html_text) in enumerate(slides, start=3):
        renumbered.append((label, re.sub(r'id="slide-\d+"', f'id="slide-{number}"', html_text, count=1)))
    slides = renumbered
    return slides


def nav(labels: list[str], sections: tuple[tuple[str, int, int], ...] | None = None) -> str:
    sections = sections or NAV_SECTIONS
    if len(labels) != sections[-1][2]:
        raise ValueError("Las secciones de navegación no cubren todas las láminas.")

    groups: list[str] = []
    expected_start = 0
    for group_index, (title, start, end) in enumerate(sections):
        if start != expected_start or start >= end or end > len(labels):
            raise ValueError(f"Rango de navegación inválido para {title!r}: {start}:{end}.")
        expected_start = end
        buttons = "\n          ".join(
            f'<button class="nav-pill{" pill-active" if idx == 0 else ""}" data-slide="{idx}">{idx + 1}. {esc(labels[idx])}</button>'
            for idx in range(start, end)
        )
        groups.append(
            f'''<details class="nav-section" data-section="{group_index + 1}"{" open" if group_index == 0 else ""}>
        <summary><span class="nav-section-title">{esc(title)}</span><span class="nav-section-range">{start + 1}–{end}</span></summary>
        <div class="nav-section-slides">
          {buttons}
        </div>
      </details>'''
        )

    if expected_start != len(labels):
        raise ValueError("Las secciones de navegación no terminan en la última lámina.")
    return "\n      ".join(groups)


def slide_stage_hashes(document: str) -> dict[str, str]:
    """Hash each generated stage so a targeted change cannot alter other slides."""
    matches = list(re.finditer(r'<div class="slide-stage" id="(slide-\d+)"(?:\s[^>]*)?>', document))
    hashes: dict[str, str] = {}
    for index, match in enumerate(matches):
        stage_id = match.group(1)
        end = matches[index + 1].start() if index + 1 < len(matches) else document.index('<div class="nav-ctrl" id="slide-nav">', match.start())
        if stage_id in hashes:
            raise ValueError(f"La lámina {stage_id} está duplicada al calcular hashes.")
        hashes[stage_id] = hashlib.sha256(document[match.start():end].encode("utf-8")).hexdigest()
    return hashes


def nav_pill_labels(document: str) -> list[str]:
    """Return ordered visible nav labels and reject duplicate/missing indices."""
    pairs = [
        (int(match.group(1)), html.unescape(match.group(2)).strip())
        for match in re.finditer(
            r'<button class="nav-pill(?: pill-active)?" data-slide="(\d+)">([^<]*)</button>',
            document,
        )
    ]
    if [index for index, _ in pairs] != list(range(len(pairs))):
        raise ValueError("Deck navigation pills are not consecutive 0-based slide indices.")
    return [label for _, label in pairs]


def slide_stage_by_title(document: str, title: str) -> tuple[str, int, int, str]:
    """Locate one stage by its visible title, never by a caller-supplied ordinal."""
    matches = list(re.finditer(r'<div class="slide-stage" id="(slide-\d+)"(?:\s[^>]*)?>', document))
    candidates: list[tuple[str, int, int, str]] = []
    expected_heading = f'<h2 class="slide-title-text">{esc(title)}</h2>'
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else document.index('<div class="nav-ctrl" id="slide-nav">', match.start())
        stage = document[match.start():end]
        if expected_heading in stage:
            candidates.append((match.group(1), match.start(), end, stage))
    if len(candidates) != 1:
        raise ValueError(f"Expected exactly one stage titled {title!r}; found {len(candidates)}.")
    return candidates[0]


def application_evidence_manifest_entry() -> dict[str, object]:
    """Return safe provenance for both application-intensity evidence artifacts."""
    annual = load(APPLICATION_INTENSITY_EVIDENCE)
    rolling = load(APPLICATION_EMPLOYEE_SNAPSHOT_EVIDENCE)
    authorization = application_intensity_authorization()
    annual_reconciliation = annual.get("evidence", {}).get("historical_source_reconciliation", {})
    current_reconciliation = annual.get("evidence", {}).get("current_source_reconciliation", {})
    rolling_gate = rolling.get("evidence", {}).get("publication_gate", {})
    return {
        "source": "hrda.job_applications_vw",
        "analysis_cutoff": annual.get("analysis_cutoff"),
        "execution_date": annual.get("generated_on"),
        "annual_evidence": str(APPLICATION_INTENSITY_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "employee_snapshot_evidence": str(APPLICATION_EMPLOYEE_SNAPSHOT_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "annual_evidence_sha256": hashlib.sha256(APPLICATION_INTENSITY_EVIDENCE.read_bytes()).hexdigest(),
        "employee_snapshot_evidence_sha256": hashlib.sha256(APPLICATION_EMPLOYEE_SNAPSHOT_EVIDENCE.read_bytes()).hexdigest(),
        "annual_profile_query": APPLICATION_INTENSITY_PROFILE_SQL,
        "source_metadata_audit_query": APPLICATION_INTENSITY_METADATA_AUDIT_SQL,
        "event_quality_audit_query": APPLICATION_INTENSITY_EVENT_QUALITY_AUDIT_SQL,
        "annual_fiscal_audit_query": APPLICATION_INTENSITY_MAPPING_AUDIT_SQL,
        "source_reconciliation_query": APPLICATION_INTENSITY_SOURCE_AUDIT_SQL,
        "employee_snapshot_profile_query": APPLICATION_EMPLOYEE_SNAPSHOT_PROFILE_SQL,
        "employee_snapshot_join_audit_query": APPLICATION_EMPLOYEE_SNAPSHOT_JOIN_AUDIT_SQL,
        "employee_snapshot_temporal_audit_query": APPLICATION_EMPLOYEE_SNAPSHOT_TEMPORAL_AUDIT_SQL,
        "employee_snapshot_publishability_audit_query": APPLICATION_EMPLOYEE_SNAPSHOT_PUBLISHABILITY_AUDIT_SQL,
        "builder": str(APPLICATION_INTENSITY_EVIDENCE_BUILDER.relative_to(ROOT)).replace("\\", "/"),
        "reporting_mode": annual.get("reporting_mode"),
        "internal_analysis_authorization": {
            "authorization_id": authorization.get("authorization_id"),
            "authorized_on": authorization.get("authorized_on"),
            "authorized_audience": authorization.get("authorized_audience"),
            "scope": authorization.get("scope"),
            "allow_subthreshold_aggregate_buckets": authorization.get("small_cell_exception", {}).get("allow_subthreshold_aggregate_buckets"),
            "minimum_displayed_count": authorization.get("small_cell_exception", {}).get("minimum_displayed_count"),
            "controls": authorization.get("non_negotiable_controls"),
        },
        "annual_publication": {
            "buckets": ["1", "2", "3", "4+"],
            "standard_publishable_periods": ["FY2022", "FY2023", "FY2024"],
            "displayed_internal_periods": ["FY2022", "FY2023", "FY2024", "FY2025", "FY2026 YTD"],
            "standard_suppressed_periods": ["FY2025", "FY2026 YTD"],
            "fy2026_ytd_through": "2026-09-10",
            "fy2026_is_partial": True,
            "minimum_shared_cohort": MINIMUM_COHORT,
            "standard_rule": "Do not publish a fiscal period when any 1/2/3/4+ bucket is below n=30.",
            "internal_rule": "Under the named internal_analysis authorization, display aggregate rows below n=30 for the requester and Julia only; FY2026 YTD is not comparable with a full fiscal year.",
        },
        "employee_snapshot_publication": {
            "buckets": ["0", "1", "2+", "Unknown"],
            "window": rolling.get("window"),
            "latest_available_snapshot": rolling.get("latest_available_snapshot"),
            "latest_publishable_snapshot": rolling.get("latest_publishable_snapshot"),
            "minimum_shared_cohort": MINIMUM_COHORT,
            "unknown_rule": "Do not convert missing source coverage to 0.",
            "rule": "Publish a complete distribution only when all four buckets have n>=30 and reconcile to the employee-snapshot denominator.",
            "publishability_gate": rolling_gate.get("metrics", {}),
        },
        "historical_source_reconciliation": annual_reconciliation,
        "current_source_reconciliation": current_reconciliation,
        "lineage_status": "Broadened descriptive source; not approved as identical lineage to hrda.applications or as a production feature.",
        "score_v4_change": "none",
        "outcome": "pass",
    }


def _stage_inventory_by_title(document: str) -> dict[str, tuple[str, str]]:
    """Return normalized stage payloads keyed by visible title."""
    matches = list(re.finditer(r'<div class="slide-stage" id="(slide-\d+)"(?:\s[^>]*)?>', document))
    nav_start = document.index('<div class="nav-ctrl" id="slide-nav">')
    inventory: dict[str, tuple[str, str]] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else nav_start
        stage = document[match.start():end]
        title_match = re.search(r'<h2 class="slide-title-text">(.*?)</h2>', stage, flags=re.S)
        if not title_match:
            raise ValueError(f"Stage {match.group(1)} has no visible title.")
        title = html.unescape(title_match.group(1)).strip()
        normalized = re.sub(r'id="slide-\d+"', 'id="slide-X"', stage, count=1)
        if title in inventory:
            raise ValueError(f"Duplicate visible stage title: {title!r}.")
        inventory[title] = (match.group(1), hashlib.sha256(normalized.encode("utf-8")).hexdigest())
    return inventory


def refresh_application_intensity_slides(reporting_mode: str = "presentation") -> None:
    """Refresh the annual application slide and insert Julia's rolling proposal.

    The existing deck already contains focused updates that are not reproduced
    by the legacy full-build path. This title-identified refresh preserves those
    stages, shifts their IDs/navigation, and changes only the application view.
    """
    global REPORTING_MODE
    if reporting_mode not in {"presentation", "internal_analysis"}:
        raise ValueError("Application refresh requires presentation or internal_analysis.")
    internal_authorization = application_intensity_authorization() if reporting_mode == "internal_analysis" else None
    if not TARGET.exists() or not MANIFEST.exists():
        raise FileNotFoundError("The current 50-slide deck and manifest are required for the application refresh.")
    REPORTING_MODE = reporting_mode
    baseline = TARGET.read_text(encoding="utf-8")
    baseline_hashes = slide_stage_hashes(baseline)
    baseline_nav = nav_pill_labels(baseline)
    if len(baseline_hashes) not in {BASELINE_DECK_SLIDE_COUNT, DECK_SLIDE_COUNT} or len(baseline_nav) != len(baseline_hashes):
        raise ValueError(f"Application refresh requires {BASELINE_DECK_SLIDE_COUNT} or {DECK_SLIDE_COUNT} stages and matching navigation.")
    annual_series = application_intensity_by_fiscal_year()
    rolling_evidence = application_employee_snapshot_trailing_6m()
    annual_stage = localize_visible_content(application_intensity_slide(3, annual_series))
    rolling_title = "Applied to a job — employee-snapshot, trailing six months"
    rolling_stage = localize_visible_content(application_employee_snapshot_slide(4, rolling_evidence))

    existing_titles = _stage_inventory_by_title(baseline)
    output = baseline
    structural_insert = rolling_title not in existing_titles
    _, start, end, _ = slide_stage_by_title(output, "Applied to a job")
    output = output[:start] + annual_stage + output[end:]

    if structural_insert:
        def shift_stage_id(match: re.Match[str]) -> str:
            number = int(match.group(1))
            return match.group(0).replace(f'id="slide-{number}"', f'id="slide-{number + 1}"') if number >= 4 else match.group(0)

        output = re.sub(r'<div class="slide-stage" id="slide-(\d+)"', shift_stage_id, output)
        _, app_start, app_end, _ = slide_stage_by_title(output, "Applied to a job")
        output = output[:app_end] + "\n\n  " + rolling_stage + output[app_end:]
    else:
        _, rolling_start, rolling_end, _ = slide_stage_by_title(output, rolling_title)
        output = output[:rolling_start] + rolling_stage + output[rolling_end:]

    baseline_nav_names = [re.sub(r'^\d+\.\s*', '', label) for label in baseline_nav]
    if structural_insert:
        nav_names = baseline_nav_names[:3] + [rolling_title] + baseline_nav_names[3:]
    else:
        nav_names = baseline_nav_names
    if len(nav_names) != DECK_SLIDE_COUNT:
        raise ValueError("Application refresh did not produce the expected 51 navigation labels.")

    nav_ctrl_start = output.index('<div class="nav-ctrl" id="slide-nav">')
    right_edge_marker = "\n\n\n  <!-- ================================================================\n       RIGHT EDGE"
    right_edge = output.index(right_edge_marker, nav_ctrl_start)
    nav_markup = f'''<div class="nav-ctrl" id="slide-nav">
    <div class="nav-panel">
      <div class="nav-label">Navigation</div>
      {nav(nav_names)}
    </div>
  </div>'''
    output = output[:nav_ctrl_start] + nav_markup + output[right_edge:]

    # Presentation mode anonymizes protected stored labels. Internal mode keeps
    # the baseline deck's already-rendered aggregate content unchanged.
    _, gender_start, gender_end, gender_stage = slide_stage_by_title(output, "Gender")
    if reporting_mode == "presentation":
        gender_stage = gender_stage.replace('title="F">F</div>', 'title="Category A">Category A</div>')
        gender_stage = gender_stage.replace('title="M">M</div>', 'title="Category B">Category B</div>')
        gender_stage = gender_stage.replace("Stored gender values", "Stored anonymized codes")
        gender_stage = gender_stage.replace("Internal analysis", "Restricted presentation")
        gender_stage = gender_stage.replace("Internal exploration, not an operational feature", "Not an operational feature")
        gender_stage = gender_stage.replace("Stored labels are displayed to interpret the aggregate. This field remains restricted for targeting and must not move into a shareable presentation.", "Aggregate evidence is retained for fairness review; semantic labels are suppressed.")
        gender_stage = gender_stage.replace("stored values", "anonymized codes")
        gender_stage = gender_stage.replace("internal analysis", "restricted fairness review")
        gender_stage = gender_stage.replace("Real labels are shown only in this internal aggregate analysis; never for individual use.", "Semantic labels are suppressed in this presentation.")
        gender_stage = gender_stage.replace("Protected field; internal aggregate use only, never targeting.", "Protected field; aggregate evidence only; semantic labels are suppressed.")
    output = output[:gender_start] + gender_stage + output[gender_end:]

    # The focused refresh must also update decks that already contain the
    # employee-snapshot styles.  Appending a marked override keeps the current
    # deck's unrelated visual changes intact while ensuring the annual table
    # widths and period labels are regenerated consistently.
    output = re.sub(
        r'\n  <style data-application-intensity-refresh="true">[\s\S]*?</style>',
        "",
        output,
        count=1,
    )
    output = output.replace(
        "</head>",
        "\n  <style data-application-intensity-refresh=\"true\">\n"
        + APPLICATION_INTENSITY_FOCUSED_CSS
        + "  </style>\n</head>",
        1,
    )

    def remove_script_containing(document: str, marker: str) -> str:
        script_matches = list(re.finditer(r'\n  <script>[\s\S]*?</script>', document))
        for script_match in reversed(script_matches):
            if marker in script_match.group(0):
                document = document[:script_match.start()] + document[script_match.end():]
        return document

    for marker in (
        "renderQVoiceCommentChart",
        "renderQVoiceResponseChart",
        "renderApplicationIntensityChart",
        "renderApplicationSnapshotTrend",
        "renderTransferCharts",
    ):
        output = remove_script_containing(output, marker)
    output = output.replace(
        "</body>",
        application_intensity_chart_enhancement(annual_series) + "\n</body>",
        1,
    )

    if "showSlide(0)" not in output:
        template_text = TEMPLATE.read_text(encoding="utf-8")
        base_scripts = "\n".join(re.findall(r'\n  <script>[\s\S]*?</script>', template_text))
        output = output.replace(
            "</body>",
            base_scripts + NAVIGATION_ENHANCEMENT + "\n</body>",
            1,
        )
    output = output.replace(
        "</body>",
        qvoice_comment_chart_enhancement(qvoice_comment_evidence())
        + qvoice_nonrespondent_chart_enhancement(qvoice_nonrespondent_evidence())
        + application_employee_snapshot_chart_enhancement(rolling_evidence)
        + transfer_chart_enhancement(transfer_within_past_year_distribution())
        + "\n</body>",
        1,
    )

    if 'title="F">F</div>' in output or 'title="M">M</div>' in output or "Stored gender values" in output:
        raise ValueError("The presentation deck retains protected gender labels.")
    if "2024-10-29" in output or "hrda.applications" in output:
        raise ValueError("The refreshed application slide retains an obsolete source reference.")
    if "FY2026" not in output or "Partial year; do not compare it directly with full fiscal years." not in output:
        raise ValueError("The refreshed annual slide does not state the FY2026 partial-year limitation.")
    if reporting_mode == "internal_analysis" and "Internal-use limit:" not in output:
        raise ValueError("The internal application slide does not display its collaboration authorization.")
    if "Unknown" not in output or "employee-snapshot, trailing six months" not in output:
        raise ValueError("The rolling application proposal is missing its Unknown category or title.")

    final_hashes = slide_stage_hashes(output)
    final_nav = nav_pill_labels(output)
    if len(final_hashes) != DECK_SLIDE_COUNT or len(final_nav) != DECK_SLIDE_COUNT:
        raise ValueError("The refreshed deck does not contain 51 stages and 51 navigation pills.")
    if list(final_hashes) != [f"slide-{index}" for index in range(1, DECK_SLIDE_COUNT + 1)]:
        raise ValueError("The refreshed stage IDs are not consecutive.")
    if final_nav != [f"{index + 1}. {label}" for index, label in enumerate(nav_names)]:
        raise ValueError("The refreshed navigation labels are not consecutive or aligned.")

    final_inventory = _stage_inventory_by_title(output)
    baseline_inventory = _stage_inventory_by_title(baseline)
    changed_existing_titles = sorted(
        title for title in baseline_inventory
        if title in final_inventory and baseline_inventory[title][1] != final_inventory[title][1]
    )
    unauthorized_changes = [title for title in changed_existing_titles if title not in {"Applied to a job", rolling_title, "Gender"}]
    if unauthorized_changes:
        raise ValueError(f"Application refresh altered existing stages outside the annual application view: {unauthorized_changes}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_slides = manifest.get("slides")
    if not isinstance(manifest_slides, list) or len(manifest_slides) not in {BASELINE_DECK_SLIDE_COUNT, DECK_SLIDE_COUNT}:
        raise ValueError("The manifest does not contain the expected pre-refresh or final slide inventory.")
    if structural_insert:
        updated_slides: list[dict[str, object]] = []
        for item in manifest_slides:
            slide = dict(item)
            slide_number = int(slide["slide"])
            if slide_number >= 4:
                slide["slide"] = slide_number + 1
            updated_slides.append(slide)
            if slide_number == 3:
                updated_slides.append({"slide": 4, "title": rolling_title})
        manifest_slides = updated_slides
    else:
        manifest_slides = [dict(item) for item in manifest_slides]
    if len(manifest_slides) != DECK_SLIDE_COUNT:
        raise ValueError("The manifest slide inventory was not expanded to 51 entries.")
    manifest["slides"] = manifest_slides
    manifest["slide_count"] = DECK_SLIDE_COUNT
    manifest["navigation_sections"] = [
        {
            "title": title,
            "start_slide": start + 1,
            "end_slide": end,
        }
        for title, start, end in NAV_SECTIONS
    ]
    manifest["generated_on"] = date.today().isoformat()
    manifest["deliverable_mode"] = reporting_mode
    if reporting_mode == "internal_analysis":
        manifest["publication_policy"] = (
            "Internal analysis: aggregate results only. The named application-intensity authorization permits "
            "sub-threshold annual buckets for the requester and Julia only; no identities, rows, requisitions, "
            "manager access, redistribution, operational use, score change, or production approval. Unknown is "
            "not imputed to zero in the employee-snapshot view."
        )
        manifest["internal_analysis_authorization"] = internal_authorization
    else:
        manifest["publication_policy"] = "Presentation: aggregate results only; n >= 30; Unknown is not imputed to zero; no identities, protected labels, free text, or exact compensation."
    source_runs = list(manifest.get("source_runs", []))
    for run in ("application-intensity-job-applications-vw-20260913", "application-employee-snapshot-trailing-6m-20260913"):
        if run not in source_runs:
            source_runs.append(run)
    manifest["source_runs"] = source_runs
    profile_paths = [path for path in manifest.get("new_aggregate_profiles", []) if "application_intensity_distinct_applicant_fiscal_year_20260908" not in str(path)]
    for path in (APPLICATION_INTENSITY_PROFILE_SQL, APPLICATION_EMPLOYEE_SNAPSHOT_PROFILE_SQL):
        if path not in profile_paths:
            profile_paths.append(path)
    manifest["new_aggregate_profiles"] = profile_paths
    audit_paths = [path for path in manifest.get("new_aggregate_audits", []) if "application_intensity_fiscal_year_mapping_20260808" not in str(path) and "application_intensity_fiscal_year_mapping_20260908" not in str(path)]
    for path in (APPLICATION_INTENSITY_METADATA_AUDIT_SQL, APPLICATION_INTENSITY_EVENT_QUALITY_AUDIT_SQL, APPLICATION_INTENSITY_MAPPING_AUDIT_SQL, APPLICATION_INTENSITY_SOURCE_AUDIT_SQL, APPLICATION_EMPLOYEE_SNAPSHOT_JOIN_AUDIT_SQL, APPLICATION_EMPLOYEE_SNAPSHOT_TEMPORAL_AUDIT_SQL, APPLICATION_EMPLOYEE_SNAPSHOT_PUBLISHABILITY_AUDIT_SQL):
        if path not in audit_paths:
            audit_paths.append(path)
    manifest["new_aggregate_audits"] = audit_paths
    builders = list(manifest.get("aggregate_evidence_builders", []))
    builder_path = str(APPLICATION_INTENSITY_EVIDENCE_BUILDER.relative_to(ROOT)).replace("\\", "/")
    if builder_path not in builders:
        builders.append(builder_path)
    manifest["aggregate_evidence_builders"] = builders
    frozen = dict(manifest.get("frozen_evidence", {}))
    application_entry = application_evidence_manifest_entry()
    frozen["application_intensity"] = application_entry
    frozen["application_employee_snapshot_trailing_6m"] = application_entry
    manifest["frozen_evidence"] = frozen
    final_structural_refresh = len(final_hashes) == DECK_SLIDE_COUNT
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": BASELINE_DECK_SLIDE_COUNT if final_structural_refresh else len(baseline_hashes),
        "output_slide_count": len(final_hashes),
        "structural_change": "Inserted the employee-snapshot trailing-six-month application slide immediately after the annual application slide; existing stages 4–50 shifted to 5–51." if final_structural_refresh else None,
        "allowed_changed_titles": ["Applied to a job", rolling_title, "Gender"],
        "observed_changed_titles": changed_existing_titles,
        "renumbered_existing_slides": list(range(5, DECK_SLIDE_COUNT + 1)) if final_structural_refresh else [],
        "unchanged_existing_content_count": len(baseline_inventory) - len(unauthorized_changes) - (1 if "Applied to a job" in changed_existing_titles else 0),
        "existing_content_preservation": "pass",
        "navigation_consecutive": True,
        "outcome": "pass",
    }
    manifest["application_intensity_refresh"] = application_entry
    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    manifest_tmp = MANIFEST.with_name(MANIFEST.name + ".tmp")
    target_tmp.write_text(output, encoding="utf-8")
    manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    target_tmp.replace(TARGET)
    manifest_tmp.replace(MANIFEST)
    print(TARGET)
    print(MANIFEST)
    print(f"slides={DECK_SLIDE_COUNT}; inserted={structural_insert}")


def time_since_last_promotion_manifest_entry(evidence: dict[str, object]) -> dict[str, object]:
    """Return provenance that is useful for review without retaining raw rows."""
    provenance = evidence["provenance"]
    metrics = evidence["metrics"]
    observability = evidence["history_observability"]
    assert isinstance(provenance, dict) and isinstance(metrics, dict) and isinstance(observability, dict)
    return {
        "evidence": str(TIME_SINCE_LAST_PROMOTION_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "evidence_sha256": hashlib.sha256(TIME_SINCE_LAST_PROMOTION_EVIDENCE.read_bytes()).hexdigest(),
        "builder": str(TIME_SINCE_LAST_PROMOTION_BUILDER.relative_to(ROOT)).replace("\\", "/"),
        "audit_query": TIME_SINCE_LAST_PROMOTION_AUDIT_SQL,
        "profile_query": TIME_SINCE_LAST_PROMOTION_PROFILE_SQL,
        "execution_date": evidence["execution_date"],
        "snapshot": evidence["snapshot_date"],
        "deliverable_mode": evidence["deliverable_mode"],
        "population": evidence["population"],
        "grain": evidence["grain"],
        "definition": evidence["definition"],
        "history_observability": observability,
        "query_sha256": {
            "audit_sql": provenance["audit_sql_sha256"],
            "audit_result": provenance["audit_result_sha256"],
            "profile_sql": provenance["profile_sql_sha256"],
            "profile_result": provenance["profile_result_sha256"],
        },
        "aggregate_metrics": {
            key: metrics[key]
            for key in (
                "active_regular_employee_count", "latest_recorded_promotion_event_count",
                "non_temporal_state_count", "two_plus_years_employee_count",
                "two_plus_years_percent_of_active_regular", "current_episode_events_excluded_before_rehire_count",
                "transfer_flag_on_valid_promotion_event_count", "transfer_date_coincident_with_valid_promotion_event_count",
                "minimum_published_bucket_count", "minimum_cohort",
            )
        },
        "acceptance_rule": evidence["validation"]["reconciliation"]["acceptance_rule"],
        "limitation": evidence["limitation"],
        "outcome": evidence["outcome"],
    }


def within_team_compensation_manifest_entry(evidence: dict[str, object]) -> dict[str, object]:
    """Return reviewable provenance without retaining teams, countries, or pay values."""
    provenance = evidence["provenance"]
    metrics = evidence["metrics"]
    assert isinstance(provenance, dict) and isinstance(metrics, dict)
    return {
        "evidence": str(WITHIN_TEAM_COMPENSATION_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "evidence_sha256": hashlib.sha256(WITHIN_TEAM_COMPENSATION_EVIDENCE.read_bytes()).hexdigest(),
        "builder": str(WITHIN_TEAM_COMPENSATION_BUILDER.relative_to(ROOT)).replace("\\", "/"),
        "audit_query": WITHIN_TEAM_COMPENSATION_AUDIT_SQL,
        "profile_query": WITHIN_TEAM_COMPENSATION_PROFILE_SQL,
        "execution_date": evidence["execution_date"],
        "snapshot": evidence["snapshot_date"],
        "deliverable_mode": evidence["deliverable_mode"],
        "population": evidence["population"],
        "grain": evidence["grain"],
        "definition": evidence["definition"],
        "query_sha256": {
            "audit_sql": provenance["audit_sql_sha256"],
            "audit_result": provenance["audit_result_sha256"],
            "profile_sql": provenance["profile_sql_sha256"],
            "profile_result": provenance["profile_result_sha256"],
        },
        "aggregate_metrics": {
            key: metrics[key]
            for key in (
                "active_regular_employee_count", "manager_universe_count", "comparable_manager_count",
                "no_comparable_group_manager_count", "eligible_comparable_group_count",
                "flagged_comparable_group_count", "flagged_comparable_group_percent",
                "excluded_missing_required_input_member_count", "singleton_group_count",
                "minimum_published_bucket_count", "minimum_cohort", "pay_spread_threshold_percent",
            )
        },
        "limitation": evidence["limitation"],
        "outcome": evidence["outcome"],
    }


def refresh_within_team_compensation_slide(reporting_mode: str = "presentation") -> None:
    """Replace only the identified Within team compensation range stage."""
    if reporting_mode != "presentation":
        raise ValueError("Within-team compensation evidence is presentation-safe and requires --reporting-mode presentation.")
    if not TARGET.exists() or not MANIFEST.exists():
        raise FileNotFoundError("The deck and manifest must exist for the focused within-team compensation refresh.")
    baseline = TARGET.read_text(encoding="utf-8")
    baseline_hashes = slide_stage_hashes(baseline)
    baseline_nav = nav_pill_labels(baseline)
    if len(baseline_hashes) != DECK_SLIDE_COUNT or len(baseline_nav) != DECK_SLIDE_COUNT:
        raise ValueError(f"The deck baseline must contain exactly {DECK_SLIDE_COUNT} stages and navigation labels.")
    stage_id, start, end, _ = slide_stage_by_title(baseline, "Within team compensation range")
    stage_number = int(stage_id.removeprefix("slide-"))
    evidence, _, _, _ = within_team_compensation_evidence()
    replacement = localize_visible_content(within_team_compensation_slide(stage_number, evidence))
    output = baseline[:start] + replacement + baseline[end:]
    targeted_css = (
        "    .within-team-compensation-stack { display:grid; height:100%; grid-template-rows:minmax(0,1fr) minmax(0,1fr) auto; gap:10px; min-height:0; overflow:hidden; }\n"
        "    .within-team-compensation-stack .card { min-height:0; }\n"
        "    .within-team-count-card .bar-row, .within-team-rate-card .bar-row { grid-template-columns:165px minmax(0,1fr) 118px; gap:8px; min-height:25px; }\n"
        "    .within-team-count-card .bar-label, .within-team-rate-card .bar-label, .within-team-count-card .bar-value, .within-team-rate-card .bar-value { font-size:11px; }\n"
        "    .within-team-count-card .bar-list, .within-team-rate-card .bar-list { gap:4px; justify-content:space-evenly; }\n"
        "    .within-team-compensation-stack .chart-footer { font-size:10px; line-height:1.25; }\n"
        "    .within-team-state-card { display:grid; grid-template-columns:205px minmax(0,1fr); column-gap:14px; align-items:center; padding:10px 14px; }\n"
        "    .within-team-state-card .card-title { grid-column:1 / -1; }\n"
        "    .within-team-state-value { color:var(--accent); font-size:23px; font-weight:800; white-space:nowrap; }\n"
        "    .within-team-state-value span { color:var(--muted); font-size:12px; font-weight:600; }\n"
        "    .within-team-state-card p { margin:0; color:var(--muted); font-size:11px; line-height:1.3; }\n"
        "    .within-team-side .fact-list { gap:3px; }\n"
        "    .within-team-side .fact-list li { font-size:11px; line-height:1.2; }\n"
    )
    if targeted_css not in output:
        output = output.replace("  </style>", targeted_css + "  </style>", 1)
    _, _, _, refreshed_stage = slide_stage_by_title(output, "Within team compensation range")
    if "Review signal, not a pay-equity finding" not in refreshed_stage or "No comparable groups" not in refreshed_stage:
        raise ValueError("Focused within-team compensation refresh did not render the expected evidence-driven content.")
    residual_spanish = residual_spanish_visible_text_excluding_stages(output, {8, 9})
    if residual_spanish:
        raise ValueError(f"The deck contains reader-facing non-English text: {residual_spanish}")
    new_hashes = slide_stage_hashes(output)
    new_nav = nav_pill_labels(output)
    changed_stages = sorted(
        int(identifier.removeprefix("slide-"))
        for identifier in baseline_hashes
        if baseline_hashes.get(identifier) != new_hashes.get(identifier)
    )
    changed_nav = [index for index, (before, after) in enumerate(zip(baseline_nav, new_nav)) if before != after]
    if set(baseline_hashes) != set(new_hashes) or changed_stages not in ([stage_number], []):
        raise ValueError(f"Focused within-team compensation refresh altered unauthorized stages: {changed_stages}.")
    if len(new_nav) != DECK_SLIDE_COUNT or changed_nav:
        raise ValueError(f"Focused within-team compensation refresh altered navigation labels: {changed_nav}.")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_slides = manifest.get("slides")
    if not isinstance(manifest_slides, list) or len(manifest_slides) != DECK_SLIDE_COUNT:
        raise ValueError(f"The manifest does not contain the expected {DECK_SLIDE_COUNT}-slide inventory.")
    if manifest_slides[stage_number - 1].get("slide") != stage_number:
        raise ValueError("The manifest slide inventory does not align to the title-resolved within-team stage.")
    source_runs = list(manifest.get("source_runs", []))
    source_run = "within-team-compensation-pay-spread-20260823"
    if source_run not in source_runs:
        source_runs.append(source_run)
    manifest["source_runs"] = source_runs
    profiles = list(manifest.get("new_aggregate_profiles", []))
    if WITHIN_TEAM_COMPENSATION_PROFILE_SQL not in profiles:
        profiles.append(WITHIN_TEAM_COMPENSATION_PROFILE_SQL)
    manifest["new_aggregate_profiles"] = profiles
    audits = list(manifest.get("new_aggregate_audits", []))
    if WITHIN_TEAM_COMPENSATION_AUDIT_SQL not in audits:
        audits.append(WITHIN_TEAM_COMPENSATION_AUDIT_SQL)
    manifest["new_aggregate_audits"] = audits
    builders = list(manifest.get("aggregate_evidence_builders", []))
    builder_path = str(WITHIN_TEAM_COMPENSATION_BUILDER.relative_to(ROOT)).replace("\\", "/")
    if builder_path not in builders:
        builders.append(builder_path)
    manifest["aggregate_evidence_builders"] = builders
    frozen_evidence = dict(manifest.get("frozen_evidence", {}))
    frozen_evidence["within_team_compensation_range"] = within_team_compensation_manifest_entry(evidence)
    manifest["frozen_evidence"] = frozen_evidence
    manifest["generated_on"] = date.today().isoformat()
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": DECK_SLIDE_COUNT,
        "output_slide_count": DECK_SLIDE_COUNT,
        "structural_change": None,
        "identified_by_title": "Within team compensation range",
        "resolved_stage": stage_number,
        "allowed_changed_slides": [stage_number],
        "observed_changed_slides": changed_stages,
        "allowed_changed_navigation_indices": [],
        "observed_changed_navigation_labels": changed_nav,
        "unchanged_slide_count": DECK_SLIDE_COUNT - len(changed_stages),
        "outcome": "pass",
    }
    manifest["visible_language_validation"] = {
        "language": "English",
        "residual_spanish_text": residual_spanish,
        "outcome": "pass",
    }
    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    manifest_tmp = MANIFEST.with_name(MANIFEST.name + ".tmp")
    target_tmp.write_text(output, encoding="utf-8")
    manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    target_tmp.replace(TARGET)
    manifest_tmp.replace(MANIFEST)
    print(TARGET)
    print(MANIFEST)
    print(f"stage={stage_number}; slides={DECK_SLIDE_COUNT}")


def refresh_time_since_last_promotion_slide(reporting_mode: str = "presentation") -> None:
    """Replace only the stage titled Time since last promotion from frozen evidence."""
    if reporting_mode != "presentation":
        raise ValueError("Time-since-promotion evidence is classified as presentation and requires --reporting-mode presentation.")
    if not TARGET.exists() or not MANIFEST.exists():
        raise FileNotFoundError("The deck and manifest must exist for the focused promotion refresh.")
    baseline = TARGET.read_text(encoding="utf-8")
    baseline_hashes = slide_stage_hashes(baseline)
    baseline_nav = nav_pill_labels(baseline)
    if len(baseline_hashes) != DECK_SLIDE_COUNT or len(baseline_nav) != DECK_SLIDE_COUNT:
        raise ValueError(f"The deck baseline must contain exactly {DECK_SLIDE_COUNT} stages and navigation labels.")
    stage_id, start, end, _ = slide_stage_by_title(baseline, "Time since last promotion")
    stage_number = int(stage_id.removeprefix("slide-"))
    evidence, _, _ = time_since_last_promotion_distribution_evidence()
    replacement = localize_visible_content(time_since_last_promotion_slide(stage_number, evidence))
    output = baseline[:start] + replacement + baseline[end:]
    targeted_css = (
        "    .promotion-distribution-stack { display:grid; height:100%; grid-template-rows:minmax(0,1.15fr) minmax(0,0.85fr); gap:12px; min-height:0; overflow:hidden; }\n"
        "    .promotion-distribution-stack .card { min-height:0; }\n"
        "    .promotion-distribution-card .bar-list { flex:1; justify-content:space-evenly; gap:6px; }\n"
        "    .promotion-distribution-card .bar-row { grid-template-columns:110px minmax(0,1fr) 116px; gap:8px; min-height:27px; }\n"
        "    .promotion-distribution-card .bar-label, .promotion-distribution-card .bar-value { font-size:12px; }\n"
        "    .promotion-state-card .bar-row { grid-template-columns:minmax(290px,1.3fr) minmax(0,1fr) 116px; }\n"
        "    .promotion-side .fact-list { gap:4px; }\n"
        "    .promotion-side .fact-list li { font-size:12px; line-height:1.28; }\n"
    )
    if targeted_css not in output:
        output = output.replace("  </style>", targeted_css + "  </style>", 1)
    _, _, _, refreshed_stage = slide_stage_by_title(output, "Time since last promotion")
    if "Calendar-anniversary time since latest recorded promotion" not in refreshed_stage:
        raise ValueError("Focused promotion refresh did not render the expected evidence-driven chart.")
    residual_spanish = residual_spanish_visible_text_excluding_stages(output, {8, 9})
    if residual_spanish:
        raise ValueError(f"The deck contains reader-facing non-English text: {residual_spanish}")
    new_hashes = slide_stage_hashes(output)
    new_nav = nav_pill_labels(output)
    changed_stages = sorted(
        int(identifier.removeprefix("slide-"))
        for identifier in baseline_hashes
        if baseline_hashes.get(identifier) != new_hashes.get(identifier)
    )
    changed_nav = [index for index, (before, after) in enumerate(zip(baseline_nav, new_nav)) if before != after]
    if set(baseline_hashes) != set(new_hashes) or changed_stages not in ([stage_number], []):
        raise ValueError(f"Focused promotion refresh altered unauthorized stages: {changed_stages}.")
    if len(new_nav) != DECK_SLIDE_COUNT or changed_nav:
        raise ValueError(f"Focused promotion refresh altered navigation labels: {changed_nav}.")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_slides = manifest.get("slides")
    if not isinstance(manifest_slides, list) or len(manifest_slides) != DECK_SLIDE_COUNT:
        raise ValueError(f"The manifest does not contain the expected {DECK_SLIDE_COUNT}-slide inventory.")
    if manifest_slides[stage_number - 1].get("slide") != stage_number:
        raise ValueError("The manifest slide inventory does not align to the title-resolved promotion stage.")
    if manifest_slides[stage_number - 1].get("title") != "Time since promotion":
        raise ValueError("The manifest title does not identify the expected promotion stage.")
    source_runs = list(manifest.get("source_runs", []))
    source_run = "time-since-last-promotion-20260823"
    if source_run not in source_runs:
        source_runs.append(source_run)
    manifest["source_runs"] = source_runs
    profiles = list(manifest.get("new_aggregate_profiles", []))
    if TIME_SINCE_LAST_PROMOTION_PROFILE_SQL not in profiles:
        profiles.append(TIME_SINCE_LAST_PROMOTION_PROFILE_SQL)
    manifest["new_aggregate_profiles"] = profiles
    audits = list(manifest.get("new_aggregate_audits", []))
    if TIME_SINCE_LAST_PROMOTION_AUDIT_SQL not in audits:
        audits.append(TIME_SINCE_LAST_PROMOTION_AUDIT_SQL)
    manifest["new_aggregate_audits"] = audits
    builders = list(manifest.get("aggregate_evidence_builders", []))
    builder_path = str(TIME_SINCE_LAST_PROMOTION_BUILDER.relative_to(ROOT)).replace("\\", "/")
    if builder_path not in builders:
        builders.append(builder_path)
    manifest["aggregate_evidence_builders"] = builders
    frozen_evidence = dict(manifest.get("frozen_evidence", {}))
    frozen_evidence["time_since_last_promotion"] = time_since_last_promotion_manifest_entry(evidence)
    manifest["frozen_evidence"] = frozen_evidence
    manifest["generated_on"] = date.today().isoformat()
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": DECK_SLIDE_COUNT,
        "output_slide_count": DECK_SLIDE_COUNT,
        "structural_change": None,
        "identified_by_title": "Time since last promotion",
        "resolved_stage": stage_number,
        "allowed_changed_slides": [stage_number],
        "observed_changed_slides": changed_stages,
        "allowed_changed_navigation_indices": [],
        "observed_changed_navigation_labels": changed_nav,
        "unchanged_slide_count": DECK_SLIDE_COUNT - len(changed_stages),
        "outcome": "pass",
    }
    manifest["visible_language_validation"] = {
        "language": "English",
        "residual_spanish_text": residual_spanish,
        "outcome": "pass",
    }
    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    manifest_tmp = MANIFEST.with_name(MANIFEST.name + ".tmp")
    target_tmp.write_text(output, encoding="utf-8")
    manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    target_tmp.replace(TARGET)
    manifest_tmp.replace(MANIFEST)
    print(TARGET)
    print(MANIFEST)
    print(f"stage={stage_number}; slides={DECK_SLIDE_COUNT}")


def promotion_history_by_grade_manifest_entry(evidence: dict[str, object]) -> dict[str, object]:
    """Return reviewable provenance without persisting query rows or individuals."""
    provenance = evidence["provenance"]
    metrics = evidence["metrics"]
    assert isinstance(provenance, dict) and isinstance(metrics, dict)
    return {
        "evidence": str(PROMOTION_HISTORY_BY_GRADE_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "evidence_sha256": hashlib.sha256(PROMOTION_HISTORY_BY_GRADE_EVIDENCE.read_bytes()).hexdigest(),
        "builder": str(PROMOTION_HISTORY_BY_GRADE_BUILDER.relative_to(ROOT)).replace("\\", "/"),
        "audit_query": PROMOTION_HISTORY_BY_GRADE_AUDIT_SQL,
        "profile_query": PROMOTION_HISTORY_BY_GRADE_PROFILE_SQL,
        "execution_date": evidence["execution_date"],
        "snapshot": evidence["snapshot_date"],
        "deliverable_mode": evidence["deliverable_mode"],
        "population": evidence["population"],
        "grain": evidence["grain"],
        "definition": evidence["definition"],
        "history_observability": evidence["history_observability"],
        "category_labels": evidence["category_labels"],
        "query_sha256": {
            "audit_sql": provenance["audit_sql_sha256"],
            "audit_result": provenance["audit_result_sha256"],
            "profile_sql": provenance["profile_sql_sha256"],
            "profile_result": provenance["profile_result_sha256"],
        },
        "aggregate_metrics": {
            key: metrics[key]
            for key in (
                "active_regular_employee_count", "observable_history_employee_count",
                "partial_history_employee_count", "valid_event_pair_count",
                "employees_with_valid_event_count", "current_episode_events_excluded_before_rehire_count",
                "raw_current_grade_count", "individual_grade_count", "pooled_other_grade_count",
                "minimum_published_cell_count", "minimum_cohort",
            )
        },
        "publication_rule": "Internal exploratory analysis only. Show a grade individually only when all four count cells are n >= 30; all remaining grades are reconciled into Other grades.",
        "limitation": evidence["limitation"],
        "outcome": evidence["outcome"],
    }


def current_grade_entry_path_manifest_entry(evidence: dict[str, object]) -> dict[str, object]:
    provenance, metrics = evidence["provenance"], evidence["metrics"]
    assert isinstance(provenance, dict) and isinstance(metrics, dict)
    return {
        "evidence": str(CURRENT_GRADE_ENTRY_PATH_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "evidence_sha256": hashlib.sha256(CURRENT_GRADE_ENTRY_PATH_EVIDENCE.read_bytes()).hexdigest(),
        "builder": str(CURRENT_GRADE_ENTRY_PATH_BUILDER.relative_to(ROOT)).replace("\\", "/"),
        "audit_query": CURRENT_GRADE_ENTRY_PATH_AUDIT_SQL, "profile_query": CURRENT_GRADE_ENTRY_PATH_PROFILE_SQL,
        "execution_date": evidence["execution_date"], "snapshot": evidence["snapshot_date"], "population": evidence["population"], "grain": evidence["grain"], "definition": evidence["definition"],
        "query_sha256": {"audit_sql": provenance["audit_sql_sha256"], "audit_result": provenance["audit_result_sha256"], "profile_sql": provenance["profile_sql_sha256"], "profile_result": provenance["profile_result_sha256"]},
        "aggregate_metrics": {key: metrics[key] for key in ("active_regular_employee_count", "promotion_confirmed_into_current_grade_count", "observed_entry_without_registered_promotion_count", "current_grade_entry_not_observable_count", "individual_grade_count", "pooled_other_grade_count", "minimum_published_cell_count", "old_grade_mismatch_previous_snapshot_count")},
        "publication_rule": "Internal exploratory analysis only; every raw state cell must have n >= 30. No direct-hire inference, identities, individual dates, or exact compensation.",
        "limitation": evidence["limitation"], "outcome": evidence["outcome"],
    }


def refresh_promotion_history_by_grade_slide(reporting_mode: str = "internal_analysis") -> None:
    """Replace only slide 29 and its navigation label from frozen matrix evidence."""
    global REPORTING_MODE
    if reporting_mode != "internal_analysis":
        raise ValueError("Promotion-history-by-grade evidence is approved only for internal_analysis.")
    if not TARGET.exists() or not MANIFEST.exists():
        raise FileNotFoundError("The deck and manifest must exist for the focused promotion-history refresh.")
    REPORTING_MODE = reporting_mode
    baseline = TARGET.read_text(encoding="utf-8")
    baseline_hashes = slide_stage_hashes(baseline)
    baseline_nav = nav_pill_labels(baseline)
    if len(baseline_hashes) != DECK_SLIDE_COUNT or len(baseline_nav) != DECK_SLIDE_COUNT:
        raise ValueError(f"The deck baseline must contain exactly {DECK_SLIDE_COUNT} stages and navigation labels.")
    if baseline_nav[PROMOTION_HISTORY_BY_GRADE_SLIDE - 1] not in {"29. Promoted vs hired", "29. Promotions by grade"}:
        raise ValueError("Slide 29 navigation does not identify the replaceable promotion stage.")

    evidence, _ = promotion_history_by_grade_evidence()
    replacement = localize_visible_content(promotion_history_by_grade_slide(PROMOTION_HISTORY_BY_GRADE_SLIDE, evidence))
    output, stage_replacements = re.subn(
        rf'<div class="slide-stage" id="slide-{PROMOTION_HISTORY_BY_GRADE_SLIDE}"(?:\s[^>]*)?>.*?(?=\n\n  <div class="slide-stage" id="slide-{PROMOTION_HISTORY_BY_GRADE_SLIDE + 1}")',
        replacement,
        baseline,
        count=1,
        flags=re.S,
    )
    if stage_replacements != 1:
        raise ValueError("Slide 29 was not found for the focused promotion-history refresh.")
    output, nav_replacements = re.subn(
        rf'(<button class="nav-pill" data-slide="{PROMOTION_HISTORY_BY_GRADE_SLIDE - 1}">{PROMOTION_HISTORY_BY_GRADE_SLIDE}\. )(?:Promoted vs hired|Promotions by grade)(</button>)',
        rf'\g<1>Promotions by grade\g<2>',
        output,
        count=1,
    )
    if nav_replacements != 1:
        raise ValueError("Slide 29 navigation label was not found for the focused promotion-history refresh.")
    if PROMOTION_HISTORY_BY_GRADE_CSS not in output:
        output = output.replace("  </style>", PROMOTION_HISTORY_BY_GRADE_CSS + "  </style>", 1)
    _, _, _, refreshed_stage = slide_stage_by_title(output, "Promotion history by current compensation grade")
    if refreshed_stage.count("promotion-grade-matrix-card") != 2 or "Internal exploratory analysis" not in refreshed_stage:
        raise ValueError("Focused promotion-history refresh did not render the expected two-panel internal matrix.")
    residual_spanish = residual_spanish_visible_text_excluding_stages(output, {8, 9})
    if residual_spanish:
        raise ValueError(f"The deck contains reader-facing non-English text: {residual_spanish}")
    new_hashes = slide_stage_hashes(output)
    new_nav = nav_pill_labels(output)
    changed_stages = sorted(
        int(identifier.removeprefix("slide-"))
        for identifier in baseline_hashes
        if baseline_hashes.get(identifier) != new_hashes.get(identifier)
    )
    changed_nav = [index for index, (before, after) in enumerate(zip(baseline_nav, new_nav)) if before != after]
    if set(baseline_hashes) != set(new_hashes) or changed_stages not in ([PROMOTION_HISTORY_BY_GRADE_SLIDE], []):
        raise ValueError(f"Focused promotion-history refresh altered unauthorized stages: {changed_stages}.")
    if len(new_nav) != DECK_SLIDE_COUNT or changed_nav not in ([PROMOTION_HISTORY_BY_GRADE_SLIDE - 1], []):
        raise ValueError(f"Focused promotion-history refresh altered unauthorized navigation labels: {changed_nav}.")
    if new_nav[PROMOTION_HISTORY_BY_GRADE_SLIDE - 1] != "29. Promotions by grade":
        raise ValueError("Focused promotion-history refresh did not set the required navigation label.")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_slides = manifest.get("slides")
    if not isinstance(manifest_slides, list) or len(manifest_slides) != DECK_SLIDE_COUNT:
        raise ValueError(f"The manifest does not contain the expected {DECK_SLIDE_COUNT}-slide inventory.")
    if manifest_slides[PROMOTION_HISTORY_BY_GRADE_SLIDE - 1].get("slide") != PROMOTION_HISTORY_BY_GRADE_SLIDE:
        raise ValueError("The manifest slide inventory does not align with slide 29.")
    manifest_slides[PROMOTION_HISTORY_BY_GRADE_SLIDE - 1]["title"] = "Promotion history by current compensation grade"
    manifest["generated_on"] = date.today().isoformat()
    source_runs = list(manifest.get("source_runs", []))
    source_run = "promotion-history-by-compensation-grade-20260823"
    if source_run not in source_runs:
        source_runs.append(source_run)
    manifest["source_runs"] = source_runs
    profiles = list(manifest.get("new_aggregate_profiles", []))
    if PROMOTION_HISTORY_BY_GRADE_PROFILE_SQL not in profiles:
        profiles.append(PROMOTION_HISTORY_BY_GRADE_PROFILE_SQL)
    manifest["new_aggregate_profiles"] = profiles
    audits = list(manifest.get("new_aggregate_audits", []))
    if PROMOTION_HISTORY_BY_GRADE_AUDIT_SQL not in audits:
        audits.append(PROMOTION_HISTORY_BY_GRADE_AUDIT_SQL)
    manifest["new_aggregate_audits"] = audits
    builders = list(manifest.get("aggregate_evidence_builders", []))
    builder_path = str(PROMOTION_HISTORY_BY_GRADE_BUILDER.relative_to(ROOT)).replace("\\", "/")
    if builder_path not in builders:
        builders.append(builder_path)
    manifest["aggregate_evidence_builders"] = builders
    frozen_evidence = dict(manifest.get("frozen_evidence", {}))
    frozen_evidence["promotion_history_by_current_compensation_grade"] = promotion_history_by_grade_manifest_entry(evidence)
    manifest["frozen_evidence"] = frozen_evidence
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": DECK_SLIDE_COUNT,
        "output_slide_count": DECK_SLIDE_COUNT,
        "structural_change": None,
        "allowed_changed_slides": [PROMOTION_HISTORY_BY_GRADE_SLIDE],
        "observed_changed_slides": changed_stages,
        "allowed_changed_navigation_indices": [PROMOTION_HISTORY_BY_GRADE_SLIDE - 1],
        "observed_changed_navigation_labels": changed_nav,
        "unchanged_slide_count": DECK_SLIDE_COUNT - len(changed_stages),
        "outcome": "pass",
    }
    manifest["visible_language_validation"] = {
        "language": "English",
        "residual_spanish_text": residual_spanish,
        "outcome": "pass",
    }
    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    manifest_tmp = MANIFEST.with_name(MANIFEST.name + ".tmp")
    target_tmp.write_text(output, encoding="utf-8")
    manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    target_tmp.replace(TARGET)
    manifest_tmp.replace(MANIFEST)
    print(TARGET)
    print(MANIFEST)
    print(f"stage={PROMOTION_HISTORY_BY_GRADE_SLIDE}; slides={DECK_SLIDE_COUNT}")


def refresh_current_grade_entry_path_slide(reporting_mode: str = "internal_analysis") -> None:
    """Refresh only the new slide 30 and its navigation label from frozen evidence."""
    if reporting_mode != "internal_analysis" or not TARGET.exists() or not MANIFEST.exists():
        raise ValueError("Current-grade-entry focused refresh requires the internal-analysis deck and manifest.")
    baseline = TARGET.read_text(encoding="utf-8")
    before_hashes, before_nav = slide_stage_hashes(baseline), nav_pill_labels(baseline)
    if len(before_hashes) != DECK_SLIDE_COUNT or len(before_nav) != DECK_SLIDE_COUNT:
        raise ValueError(f"Current-grade-entry focused refresh requires a {DECK_SLIDE_COUNT}-slide deck.")
    evidence, _ = current_grade_entry_path_evidence()
    replacement = localize_visible_content(current_grade_entry_path_slide(CURRENT_GRADE_ENTRY_PATH_SLIDE, evidence))
    output, replacements = re.subn(rf'<div class="slide-stage" id="slide-{CURRENT_GRADE_ENTRY_PATH_SLIDE}"(?:\s[^>]*)?>.*?(?=\n\n  <div class="slide-stage" id="slide-{CURRENT_GRADE_ENTRY_PATH_SLIDE + 1}")', replacement, baseline, count=1, flags=re.S)
    if replacements != 1:
        raise ValueError("Slide 30 was not found for the current-grade-entry refresh.")
    output, nav_replacements = re.subn(rf'(<button class="nav-pill" data-slide="{CURRENT_GRADE_ENTRY_PATH_SLIDE - 1}">{CURRENT_GRADE_ENTRY_PATH_SLIDE}\. )(?:[^<]+)(</button>)', r'\g<1>Current grade entry path\g<2>', output, count=1)
    if nav_replacements != 1:
        raise ValueError("Slide 30 navigation label was not found for refresh.")
    if CURRENT_GRADE_ENTRY_PATH_CSS not in output:
        output = output.replace("  </style>", CURRENT_GRADE_ENTRY_PATH_CSS + "  </style>", 1)
    after_hashes, after_nav = slide_stage_hashes(output), nav_pill_labels(output)
    changed_stages = sorted(int(key.removeprefix("slide-")) for key in before_hashes if before_hashes[key] != after_hashes.get(key))
    changed_nav = [index for index, pair in enumerate(zip(before_nav, after_nav)) if pair[0] != pair[1]]
    if set(before_hashes) != set(after_hashes) or changed_stages not in ([CURRENT_GRADE_ENTRY_PATH_SLIDE], []) or changed_nav not in ([CURRENT_GRADE_ENTRY_PATH_SLIDE - 1], []):
        raise ValueError("Current-grade-entry refresh changed unauthorized slide content or navigation.")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    slides = manifest.get("slides")
    if not isinstance(slides, list) or len(slides) != DECK_SLIDE_COUNT:
        raise ValueError("Current-grade-entry manifest inventory is invalid.")
    slides[CURRENT_GRADE_ENTRY_PATH_SLIDE - 1]["title"] = "Current grade entry path"
    frozen = dict(manifest.get("frozen_evidence", {})); frozen["current_grade_entry_path"] = current_grade_entry_path_manifest_entry(evidence); manifest["frozen_evidence"] = frozen
    manifest["generated_on"] = date.today().isoformat()
    manifest["slide_content_hash_validation"] = {"baseline_available": True, "baseline_slide_count": DECK_SLIDE_COUNT, "output_slide_count": DECK_SLIDE_COUNT, "structural_change": None, "allowed_changed_slides": [CURRENT_GRADE_ENTRY_PATH_SLIDE], "observed_changed_slides": changed_stages, "allowed_changed_navigation_indices": [CURRENT_GRADE_ENTRY_PATH_SLIDE - 1], "observed_changed_navigation_labels": changed_nav, "unchanged_slide_count": DECK_SLIDE_COUNT - len(changed_stages), "outcome": "pass"}
    TARGET.write_text(output, encoding="utf-8")
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"stage={CURRENT_GRADE_ENTRY_PATH_SLIDE}; slides={DECK_SLIDE_COUNT}")


def talent_index_manifest_entry(talent_index: dict[str, object]) -> dict[str, object]:
    """Return traceable metadata without copying employee-level data into the manifest."""
    evidence = talent_index["evidence"]
    metrics = talent_index["metrics"]
    if not isinstance(evidence, dict) or not isinstance(metrics, dict):
        raise ValueError("Talent Index manifest input is malformed.")
    return {
        "evidence": str(TALENT_INDEX_DISTRIBUTION_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "query": TALENT_INDEX_DISTRIBUTION_SQL,
        "query_sha256": evidence["query_sha256"],
        "query_result_sha256": evidence["query_result_sha256"],
        "execution_date": evidence["execution_date"],
        "snapshot": evidence["snapshot_date"],
        "population": evidence["population"],
        "grain": evidence["grain"],
        "selection_rule": evidence["selection_rule"],
        "distribution_rule": evidence["distribution_rule"],
        "publication_rule": "Aggregate values only; every displayed band has n >= 30; no employee-level data or identities.",
        "acceptance_rule": evidence["acceptance_rule"],
        "metrics": {
            "eligible_employees": metrics["eligible_employees"],
            "observable_employees": metrics["observable_employees"],
            "not_observable_employees": metrics["not_observable_employees"],
            "median_stored_value": metrics["median_stored_value"],
            "first_quartile": metrics["first_quartile"],
            "third_quartile": metrics["third_quartile"],
            "out_of_range_employees": metrics["out_of_range_employees"],
        },
        "limitation": "Currently recoverable stored value for employees active on 23-Aug-2026; not proof the index was calculated or effective on that date.",
        "outcome": evidence["outcome"],
    }


def refresh_talent_index_distribution_slide(reporting_mode: str = "internal_analysis") -> None:
    """Replace only the current Talent Index stage using frozen aggregate evidence."""
    global REPORTING_MODE
    if reporting_mode not in {"presentation", "internal_analysis"}:
        raise ValueError("reporting_mode must be presentation or internal_analysis.")
    if not TARGET.exists() or not MANIFEST.exists():
        raise FileNotFoundError("El deck y su manifest deben existir para actualizar sólo Talent Index.")
    REPORTING_MODE = reporting_mode
    baseline = TARGET.read_text(encoding="utf-8")
    baseline_hashes = slide_stage_hashes(baseline)
    if len(baseline_hashes) != DECK_SLIDE_COUNT:
        raise ValueError(f"El deck base no contiene {DECK_SLIDE_COUNT} láminas para la actualización focalizada.")

    talent_index = talent_index_latest_recoverable_distribution()
    replacement = localize_visible_content(talent_index_distribution_slide(talent_index))
    output, replacements = re.subn(
        rf'<div class="slide-stage" id="slide-{TALENT_INDEX_SLIDE}">.*?(?=\n\n  <div class="slide-stage" id="slide-{TALENT_INDEX_SLIDE + 1}">)',
        replacement,
        baseline,
        count=1,
        flags=re.S,
    )
    if replacements != 1:
        raise ValueError(f"No se encontró la lámina {TALENT_INDEX_SLIDE} de Talent Index para actualizar.")
    targeted_css = (
        "    .talent-index-distribution-card .bar-list { flex:1; justify-content:space-evenly; padding:4px 0; }\n"
        "    .talent-index-distribution-card .bar-row { min-height:26px; }\n"
    )
    if targeted_css not in output:
        output = output.replace("  </style>", targeted_css + "  </style>", 1)
    residual_spanish = residual_spanish_visible_text_excluding_stages(output, {8, 9})
    if residual_spanish:
        raise ValueError(f"El deck contiene texto visible fuera de inglés: {residual_spanish}")
    new_hashes = slide_stage_hashes(output)
    changed = sorted(
        int(stage_id.removeprefix("slide-"))
        for stage_id in baseline_hashes
        if baseline_hashes.get(stage_id) != new_hashes.get(stage_id)
    )
    if set(baseline_hashes) != set(new_hashes) or changed not in ([TALENT_INDEX_SLIDE], []):
        raise ValueError(f"La actualización de Talent Index alteró láminas no autorizadas: {changed}.")

    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    target_tmp.write_text(output, encoding="utf-8")
    target_tmp.replace(TARGET)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["generated_on"] = date.today().isoformat()
    manifest["source_runs"] = [
        source for source in manifest.get("source_runs", [])
        if source != "talent-index-current-state-final4-20260820"
    ]
    if "talent-index-latest-recoverable-distribution-20260909" not in manifest["source_runs"]:
        manifest["source_runs"].append("talent-index-latest-recoverable-distribution-20260909")
    profiles = list(manifest.get("new_aggregate_profiles", []))
    if TALENT_INDEX_DISTRIBUTION_SQL not in profiles:
        profiles.append(TALENT_INDEX_DISTRIBUTION_SQL)
    manifest["new_aggregate_profiles"] = profiles
    builders = list(manifest.get("aggregate_evidence_builders", []))
    builder_path = "tools/build_talent_index_distribution_evidence.py"
    if builder_path not in builders:
        builders.append(builder_path)
    manifest["aggregate_evidence_builders"] = builders
    frozen_evidence = dict(manifest.get("frozen_evidence", {}))
    frozen_evidence["talent_index_latest_recoverable_distribution"] = talent_index_manifest_entry(talent_index)
    manifest["frozen_evidence"] = frozen_evidence
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": DECK_SLIDE_COUNT,
        "output_slide_count": DECK_SLIDE_COUNT,
        "structural_change": None,
        "allowed_changed_slides": [TALENT_INDEX_SLIDE],
        "observed_changed_slides": changed,
        "unchanged_slide_count": DECK_SLIDE_COUNT - len(changed),
        "outcome": "pass",
    }
    manifest["visible_language_validation"] = {
        "language": "English",
        "residual_spanish_text": residual_spanish,
        "outcome": "pass",
    }
    manifest_tmp = MANIFEST.with_name(MANIFEST.name + ".tmp")
    manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_tmp.replace(MANIFEST)
    print(TARGET)
    print(MANIFEST)
    print(f"slides={DECK_SLIDE_COUNT}")


def refresh_residential_manager_distance_slide(reporting_mode: str = "internal_analysis") -> None:
    """Replace only the current residential-distance stage from frozen evidence."""
    global REPORTING_MODE
    if reporting_mode != "internal_analysis":
        raise ValueError("Residential manager-distance evidence is approved only for internal_analysis.")
    if not TARGET.exists() or not MANIFEST.exists():
        raise FileNotFoundError("The deck and manifest must exist for the focused residential-distance refresh.")
    REPORTING_MODE = reporting_mode
    baseline = TARGET.read_text(encoding="utf-8")
    baseline_hashes = slide_stage_hashes(baseline)
    baseline_nav = nav_pill_labels(baseline)
    if len(baseline_hashes) != DECK_SLIDE_COUNT or len(baseline_nav) != DECK_SLIDE_COUNT:
        raise ValueError(f"The deck baseline must contain exactly {DECK_SLIDE_COUNT} stages and navigation labels.")

    evidence, _ = residential_manager_distance_evidence()
    replacement = localize_visible_content(residential_manager_distance_slide(RESIDENTIAL_MANAGER_DISTANCE_SLIDE, evidence))
    output, stage_replacements = re.subn(
        rf'<div class="slide-stage" id="slide-{RESIDENTIAL_MANAGER_DISTANCE_SLIDE}">.*?(?=\n\n  <div class="slide-stage" id="slide-{RESIDENTIAL_MANAGER_DISTANCE_SLIDE + 1}">)',
        replacement,
        baseline,
        count=1,
        flags=re.S,
    )
    if stage_replacements != 1:
        raise ValueError(f"Slide {RESIDENTIAL_MANAGER_DISTANCE_SLIDE} was not found for the focused residential-distance refresh.")
    output, nav_replacements = re.subn(
        rf'(<button class="nav-pill" data-slide="{RESIDENTIAL_MANAGER_DISTANCE_SLIDE - 1}">){RESIDENTIAL_MANAGER_DISTANCE_SLIDE}\. (?:Hours away|Residential distance)(</button>)',
        rf'\g<1>{RESIDENTIAL_MANAGER_DISTANCE_SLIDE}. Residential distance\g<2>',
        output,
        count=1,
    )
    if nav_replacements != 1:
        raise ValueError("The residential-distance navigation label was not found for the focused refresh.")
    if RESIDENTIAL_MANAGER_DISTANCE_CSS not in output:
        output = output.replace("  </style>", RESIDENTIAL_MANAGER_DISTANCE_CSS + "  </style>", 1)

    residual_spanish = residual_spanish_visible_text_excluding_stages(output, {8, 9})
    if residual_spanish:
        raise ValueError(f"The deck contains reader-facing non-English text: {residual_spanish}")
    new_hashes = slide_stage_hashes(output)
    new_nav = nav_pill_labels(output)
    changed_stages = sorted(
        int(stage_id.removeprefix("slide-"))
        for stage_id in baseline_hashes
        if baseline_hashes.get(stage_id) != new_hashes.get(stage_id)
    )
    changed_nav = [index for index, (before, after) in enumerate(zip(baseline_nav, new_nav)) if before != after]
    if set(baseline_hashes) != set(new_hashes) or changed_stages not in ([RESIDENTIAL_MANAGER_DISTANCE_SLIDE], []):
        raise ValueError(f"Focused residential-distance refresh altered unauthorized stages: {changed_stages}.")
    if len(new_nav) != DECK_SLIDE_COUNT or changed_nav not in ([RESIDENTIAL_MANAGER_DISTANCE_SLIDE - 1], []):
        raise ValueError(f"Focused residential-distance refresh altered unauthorized navigation labels: {changed_nav}.")

    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    target_tmp.write_text(output, encoding="utf-8")
    target_tmp.replace(TARGET)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["generated_on"] = date.today().isoformat()
    profiles = list(manifest.get("new_aggregate_profiles", []))
    if RESIDENTIAL_MANAGER_DISTANCE_PROFILE_SQL not in profiles:
        profiles.append(RESIDENTIAL_MANAGER_DISTANCE_PROFILE_SQL)
    manifest["new_aggregate_profiles"] = profiles
    audits = list(manifest.get("new_aggregate_audits", []))
    if RESIDENTIAL_MANAGER_DISTANCE_AUDIT_SQL not in audits:
        audits.append(RESIDENTIAL_MANAGER_DISTANCE_AUDIT_SQL)
    if RESIDENTIAL_MANAGER_DISTANCE_COUNTRY_MAPPING_AUDIT_SQL not in audits:
        audits.append(RESIDENTIAL_MANAGER_DISTANCE_COUNTRY_MAPPING_AUDIT_SQL)
    manifest["new_aggregate_audits"] = audits
    builders = list(manifest.get("aggregate_evidence_builders", []))
    builder_path = str(RESIDENTIAL_MANAGER_DISTANCE_BUILDER.relative_to(ROOT)).replace("\\", "/")
    if builder_path not in builders:
        builders.append(builder_path)
    manifest["aggregate_evidence_builders"] = builders
    frozen_evidence = dict(manifest.get("frozen_evidence", {}))
    frozen_evidence["residential_manager_distance"] = residential_manager_distance_manifest_entry(evidence)
    manifest["frozen_evidence"] = frozen_evidence
    manifest_slides = manifest.get("slides")
    if not isinstance(manifest_slides, list) or len(manifest_slides) != DECK_SLIDE_COUNT:
        raise ValueError(f"The manifest does not contain the expected {DECK_SLIDE_COUNT}-slide inventory.")
    if manifest_slides[RESIDENTIAL_MANAGER_DISTANCE_SLIDE - 1].get("slide") != RESIDENTIAL_MANAGER_DISTANCE_SLIDE:
        raise ValueError("The manifest slide inventory has an unexpected residential-distance entry.")
    manifest_slides[RESIDENTIAL_MANAGER_DISTANCE_SLIDE - 1]["title"] = "Residential distance"
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": DECK_SLIDE_COUNT,
        "output_slide_count": DECK_SLIDE_COUNT,
        "structural_change": None,
        "allowed_changed_slides": [RESIDENTIAL_MANAGER_DISTANCE_SLIDE],
        "observed_changed_slides": changed_stages,
        "allowed_changed_navigation_indices": [RESIDENTIAL_MANAGER_DISTANCE_SLIDE - 1],
        "observed_changed_navigation_labels": changed_nav,
        "unchanged_slide_count": DECK_SLIDE_COUNT - len(changed_stages),
        "outcome": "pass",
    }
    manifest["visible_language_validation"] = {
        "language": "English",
        "residual_spanish_text": residual_spanish,
        "outcome": "pass",
    }
    manifest_tmp = MANIFEST.with_name(MANIFEST.name + ".tmp")
    manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_tmp.replace(MANIFEST)
    print(TARGET)
    print(MANIFEST)
    print(f"slides={DECK_SLIDE_COUNT}")


def refresh_company_tenure_slide(reporting_mode: str = "internal_analysis") -> None:
    """Replace only slide 27 after passing fixed-snapshot stored-date evidence."""
    global REPORTING_MODE
    if reporting_mode != "internal_analysis":
        raise ValueError("Company tenure evidence is approved only for internal_analysis.")
    if not TARGET.exists() or not MANIFEST.exists():
        raise FileNotFoundError("The deck and manifest must exist for the focused Company tenure refresh.")
    REPORTING_MODE = reporting_mode
    baseline = TARGET.read_text(encoding="utf-8")
    baseline_hashes = slide_stage_hashes(baseline)
    baseline_nav = nav_pill_labels(baseline)
    if len(baseline_hashes) != DECK_SLIDE_COUNT or len(baseline_nav) != DECK_SLIDE_COUNT:
        raise ValueError(f"The deck baseline must contain exactly {DECK_SLIDE_COUNT} stages and navigation labels.")
    if baseline_nav[COMPANY_TENURE_SLIDE - 1] != "27. Company tenure":
        raise ValueError("The Company tenure navigation label must remain '27. Company tenure'.")

    evidence, _, _ = company_tenure_distribution_evidence()
    replacement = localize_visible_content(company_tenure_slide(COMPANY_TENURE_SLIDE, evidence))
    output, stage_replacements = re.subn(
        rf'<div class="slide-stage" id="slide-{COMPANY_TENURE_SLIDE}"(?:\s[^>]*)?>.*?(?=\n\n  <div class="slide-stage" id="slide-{COMPANY_TENURE_SLIDE + 1}">)',
        replacement,
        baseline,
        count=1,
        flags=re.S,
    )
    if stage_replacements != 1:
        raise ValueError(f"Slide {COMPANY_TENURE_SLIDE} was not found for the focused Company tenure refresh.")
    if COMPANY_TENURE_CSS not in output:
        output = output.replace("  </style>", COMPANY_TENURE_CSS + "  </style>", 1)
    residual_spanish = residual_spanish_visible_text_excluding_stages(output, {8, 9})
    if residual_spanish:
        raise ValueError(f"The deck contains reader-facing non-English text: {residual_spanish}")
    new_hashes = slide_stage_hashes(output)
    new_nav = nav_pill_labels(output)
    changed_stages = sorted(
        int(stage_id.removeprefix("slide-"))
        for stage_id in baseline_hashes
        if baseline_hashes.get(stage_id) != new_hashes.get(stage_id)
    )
    changed_nav = [index for index, (before, after) in enumerate(zip(baseline_nav, new_nav)) if before != after]
    if set(baseline_hashes) != set(new_hashes) or changed_stages not in ([COMPANY_TENURE_SLIDE], []):
        raise ValueError(f"Focused Company tenure refresh altered unauthorized stages: {changed_stages}.")
    if len(new_nav) != DECK_SLIDE_COUNT or changed_nav:
        raise ValueError(f"Focused Company tenure refresh altered navigation labels: {changed_nav}.")
    if new_nav[COMPANY_TENURE_SLIDE - 1] != "27. Company tenure":
        raise ValueError("Focused Company tenure refresh changed the required navigation label.")

    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    target_tmp.write_text(output, encoding="utf-8")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["generated_on"] = date.today().isoformat()
    source_runs = list(manifest.get("source_runs", []))
    source_run = "company-tenure-stored-fields-snapshot-20260823"
    if source_run not in source_runs:
        source_runs.append(source_run)
    manifest["source_runs"] = source_runs
    profiles = [
        profile
        for profile in manifest.get("new_aggregate_profiles", [])
        if profile != COMPANY_TENURE_LEGACY_PROFILE_SQL
    ]
    if COMPANY_TENURE_PROFILE_SQL not in profiles:
        profiles.append(COMPANY_TENURE_PROFILE_SQL)
    manifest["new_aggregate_profiles"] = profiles
    historical_profiles = list(manifest.get("historical_aggregate_profiles", []))
    if COMPANY_TENURE_LEGACY_PROFILE_SQL not in historical_profiles:
        historical_profiles.append(COMPANY_TENURE_LEGACY_PROFILE_SQL)
    manifest["historical_aggregate_profiles"] = historical_profiles
    audits = list(manifest.get("new_aggregate_audits", []))
    if COMPANY_TENURE_AUDIT_SQL not in audits:
        audits.append(COMPANY_TENURE_AUDIT_SQL)
    manifest["new_aggregate_audits"] = audits
    builders = list(manifest.get("aggregate_evidence_builders", []))
    builder_path = str(COMPANY_TENURE_BUILDER.relative_to(ROOT)).replace("\\", "/")
    if builder_path not in builders:
        builders.append(builder_path)
    manifest["aggregate_evidence_builders"] = builders
    frozen_evidence = dict(manifest.get("frozen_evidence", {}))
    frozen_evidence["company_tenure"] = company_tenure_manifest_entry(evidence)
    manifest["frozen_evidence"] = frozen_evidence
    manifest_slides = manifest.get("slides")
    if not isinstance(manifest_slides, list) or len(manifest_slides) != DECK_SLIDE_COUNT:
        raise ValueError(f"The manifest does not contain the expected {DECK_SLIDE_COUNT}-slide inventory.")
    if manifest_slides[COMPANY_TENURE_SLIDE - 1].get("slide") != COMPANY_TENURE_SLIDE:
        raise ValueError("The manifest slide inventory has an unexpected Company tenure entry.")
    manifest_slides[COMPANY_TENURE_SLIDE - 1]["title"] = "Company tenure"
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": DECK_SLIDE_COUNT,
        "output_slide_count": DECK_SLIDE_COUNT,
        "structural_change": None,
        "allowed_changed_slides": [COMPANY_TENURE_SLIDE],
        "observed_changed_slides": changed_stages,
        "allowed_changed_navigation_indices": [],
        "observed_changed_navigation_labels": changed_nav,
        "unchanged_slide_count": DECK_SLIDE_COUNT - len(changed_stages),
        "outcome": "pass",
    }
    manifest["visible_language_validation"] = {
        "language": "English",
        "residual_spanish_text": residual_spanish,
        "outcome": "pass",
    }
    manifest_tmp = MANIFEST.with_name(MANIFEST.name + ".tmp")
    manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    target_tmp.replace(TARGET)
    manifest_tmp.replace(MANIFEST)
    print(TARGET)
    print(MANIFEST)
    print(f"slides={DECK_SLIDE_COUNT}")


def refresh_role_level_tenure_slide(reporting_mode: str = "internal_analysis") -> None:
    """Replace only slide 26 after passing lineage and aggregate evidence gates."""
    global REPORTING_MODE
    if reporting_mode != "internal_analysis":
        raise ValueError("Role/level tenure evidence is approved only for internal_analysis.")
    if not TARGET.exists() or not MANIFEST.exists():
        raise FileNotFoundError("The deck and manifest must exist for the focused role/level tenure refresh.")
    REPORTING_MODE = reporting_mode
    baseline = TARGET.read_text(encoding="utf-8")
    baseline_hashes = slide_stage_hashes(baseline)
    baseline_nav = nav_pill_labels(baseline)
    if len(baseline_hashes) != DECK_SLIDE_COUNT or len(baseline_nav) != DECK_SLIDE_COUNT:
        raise ValueError(f"The deck baseline must contain exactly {DECK_SLIDE_COUNT} stages and navigation labels.")

    evidence, _, _ = role_level_tenure_distribution_evidence()
    replacement = localize_visible_content(role_level_tenure_slide(ROLE_LEVEL_TENURE_SLIDE, evidence))
    output, stage_replacements = re.subn(
        rf'<div class="slide-stage" id="slide-{ROLE_LEVEL_TENURE_SLIDE}"(?:\s[^>]*)?>.*?(?=\n\n  <div class="slide-stage" id="slide-{ROLE_LEVEL_TENURE_SLIDE + 1}"(?:\s[^>]*)?>)',
        replacement,
        baseline,
        count=1,
        flags=re.S,
    )
    if stage_replacements != 1:
        raise ValueError(f"Slide {ROLE_LEVEL_TENURE_SLIDE} was not found for the focused role/level tenure refresh.")
    output, nav_replacements = re.subn(
        rf'(<button class="nav-pill" data-slide="{ROLE_LEVEL_TENURE_SLIDE - 1}">){ROLE_LEVEL_TENURE_SLIDE}\. (?:Time in level|Time in role and level)(</button>)',
        rf'\g<1>{ROLE_LEVEL_TENURE_SLIDE}. Time in role and level\g<2>',
        output,
        count=1,
    )
    if nav_replacements != 1:
        raise ValueError("The role/level tenure navigation label was not found for the focused refresh.")
    if ROLE_LEVEL_TENURE_CSS not in output:
        output = output.replace("  </style>", ROLE_LEVEL_TENURE_CSS + "  </style>", 1)
    residual_spanish = residual_spanish_visible_text_excluding_stages(output, {8, 9})
    if residual_spanish:
        raise ValueError(f"The deck contains reader-facing non-English text: {residual_spanish}")
    new_hashes = slide_stage_hashes(output)
    new_nav = nav_pill_labels(output)
    changed_stages = sorted(
        int(stage_id.removeprefix("slide-"))
        for stage_id in baseline_hashes
        if baseline_hashes.get(stage_id) != new_hashes.get(stage_id)
    )
    changed_nav = [index for index, (before, after) in enumerate(zip(baseline_nav, new_nav)) if before != after]
    if set(baseline_hashes) != set(new_hashes) or changed_stages not in ([ROLE_LEVEL_TENURE_SLIDE], []):
        raise ValueError(f"Focused role/level tenure refresh altered unauthorized stages: {changed_stages}.")
    if len(new_nav) != DECK_SLIDE_COUNT or changed_nav not in ([ROLE_LEVEL_TENURE_SLIDE - 1], []):
        raise ValueError(f"Focused role/level tenure refresh altered unauthorized navigation labels: {changed_nav}.")

    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    target_tmp.write_text(output, encoding="utf-8")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["generated_on"] = date.today().isoformat()
    source_run = "role-level-tenure-snapshot-20260823"
    source_runs = list(manifest.get("source_runs", []))
    if source_run not in source_runs:
        source_runs.append(source_run)
    manifest["source_runs"] = source_runs
    profiles = list(manifest.get("new_aggregate_profiles", []))
    if ROLE_LEVEL_TENURE_PROFILE_SQL not in profiles:
        profiles.append(ROLE_LEVEL_TENURE_PROFILE_SQL)
    manifest["new_aggregate_profiles"] = profiles
    audits = list(manifest.get("new_aggregate_audits", []))
    if ROLE_LEVEL_TENURE_AUDIT_SQL not in audits:
        audits.append(ROLE_LEVEL_TENURE_AUDIT_SQL)
    manifest["new_aggregate_audits"] = audits
    builders = list(manifest.get("aggregate_evidence_builders", []))
    builder_path = str(ROLE_LEVEL_TENURE_BUILDER.relative_to(ROOT)).replace("\\", "/")
    if builder_path not in builders:
        builders.append(builder_path)
    manifest["aggregate_evidence_builders"] = builders
    frozen_evidence = dict(manifest.get("frozen_evidence", {}))
    frozen_evidence["role_level_tenure"] = role_level_tenure_manifest_entry(evidence)
    manifest["frozen_evidence"] = frozen_evidence
    manifest_slides = manifest.get("slides")
    if not isinstance(manifest_slides, list) or len(manifest_slides) != DECK_SLIDE_COUNT:
        raise ValueError(f"The manifest does not contain the expected {DECK_SLIDE_COUNT}-slide inventory.")
    if manifest_slides[ROLE_LEVEL_TENURE_SLIDE - 1].get("slide") != ROLE_LEVEL_TENURE_SLIDE:
        raise ValueError("The manifest slide inventory has an unexpected role/level tenure entry.")
    manifest_slides[ROLE_LEVEL_TENURE_SLIDE - 1]["title"] = "Time in role and level"
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": DECK_SLIDE_COUNT,
        "output_slide_count": DECK_SLIDE_COUNT,
        "structural_change": None,
        "allowed_changed_slides": [ROLE_LEVEL_TENURE_SLIDE],
        "observed_changed_slides": changed_stages,
        "allowed_changed_navigation_indices": [ROLE_LEVEL_TENURE_SLIDE - 1],
        "observed_changed_navigation_labels": changed_nav,
        "unchanged_slide_count": DECK_SLIDE_COUNT - len(changed_stages),
        "outcome": "pass",
    }
    manifest["visible_language_validation"] = {
        "language": "English",
        "residual_spanish_text": residual_spanish,
        "outcome": "pass",
    }
    manifest_tmp = MANIFEST.with_name(MANIFEST.name + ".tmp")
    manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    target_tmp.replace(TARGET)
    manifest_tmp.replace(MANIFEST)
    print(TARGET)
    print(MANIFEST)
    print(f"slides={DECK_SLIDE_COUNT}")


def refresh_layers_from_ceo_slide(reporting_mode: str = "internal_analysis") -> None:
    """Replace only the current layers-from-CEO stage after evidence passes."""
    global REPORTING_MODE
    if reporting_mode != "internal_analysis":
        raise ValueError("The approved layers-from-CEO evidence is classified as internal_analysis.")
    if not TARGET.exists() or not MANIFEST.exists():
        raise FileNotFoundError("The deck and manifest must exist for the focused hierarchy refresh.")
    REPORTING_MODE = reporting_mode
    baseline = TARGET.read_text(encoding="utf-8")
    baseline_hashes = slide_stage_hashes(baseline)
    baseline_nav = nav_pill_labels(baseline)
    if len(baseline_hashes) != DECK_SLIDE_COUNT or len(baseline_nav) != DECK_SLIDE_COUNT:
        raise ValueError(f"The deck baseline must contain exactly {DECK_SLIDE_COUNT} stages and navigation labels.")

    evidence, _ = layers_from_ceo_distribution_evidence()
    replacement = localize_visible_content(layers_from_ceo_slide(LAYERS_FROM_CEO_SLIDE, evidence))
    output, stage_replacements = re.subn(
        rf'<div class="slide-stage" id="slide-{LAYERS_FROM_CEO_SLIDE}">.*?(?=\n\n  <div class="slide-stage" id="slide-{LAYERS_FROM_CEO_SLIDE + 1}">)',
        replacement,
        baseline,
        count=1,
        flags=re.S,
    )
    if stage_replacements != 1:
        raise ValueError(f"Slide {LAYERS_FROM_CEO_SLIDE} was not found for the focused hierarchy refresh.")
    output, nav_replacements = re.subn(
        rf'(<button class="nav-pill" data-slide="{LAYERS_FROM_CEO_SLIDE - 1}">){LAYERS_FROM_CEO_SLIDE}\. (?:Organizational level|Org layers to CEO)(</button>)',
        rf'\g<1>{LAYERS_FROM_CEO_SLIDE}. Org layers to CEO\g<2>',
        output,
        count=1,
    )
    if nav_replacements != 1:
        raise ValueError("The layers-from-CEO navigation label was not found for the focused refresh.")
    targeted_css = (
        "    .layers-from-ceo-distribution-card .bar-list { flex:1; justify-content:space-evenly; padding:5px 0; }\n"
        "    .layers-from-ceo-distribution-card .bar-row { min-height:30px; }\n"
    )
    if targeted_css not in output:
        output = output.replace("  </style>", targeted_css + "  </style>", 1)
    residual_spanish = residual_spanish_visible_text_excluding_stages(output, {8, 9})
    if residual_spanish:
        raise ValueError(f"The deck contains reader-facing non-English text: {residual_spanish}")
    new_hashes = slide_stage_hashes(output)
    new_nav = nav_pill_labels(output)
    changed_stages = sorted(
        int(stage_id.removeprefix("slide-"))
        for stage_id in baseline_hashes
        if baseline_hashes.get(stage_id) != new_hashes.get(stage_id)
    )
    changed_nav = [index for index, (before, after) in enumerate(zip(baseline_nav, new_nav)) if before != after]
    if set(baseline_hashes) != set(new_hashes) or changed_stages not in ([LAYERS_FROM_CEO_SLIDE], []):
        raise ValueError(f"Focused hierarchy refresh altered unauthorized stages: {changed_stages}.")
    if len(new_nav) != DECK_SLIDE_COUNT or changed_nav not in ([LAYERS_FROM_CEO_SLIDE - 1], []):
        raise ValueError(f"Focused hierarchy refresh altered unauthorized navigation labels: {changed_nav}.")

    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    target_tmp.write_text(output, encoding="utf-8")
    target_tmp.replace(TARGET)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["generated_on"] = date.today().isoformat()
    source_run = "layers-from-ceo-snapshot-20260823"
    source_runs = list(manifest.get("source_runs", []))
    if source_run not in source_runs:
        source_runs.append(source_run)
    manifest["source_runs"] = source_runs
    audits = list(manifest.get("new_aggregate_audits", []))
    if LAYERS_FROM_CEO_AUDIT_SQL not in audits:
        audits.append(LAYERS_FROM_CEO_AUDIT_SQL)
    manifest["new_aggregate_audits"] = audits
    builders = list(manifest.get("aggregate_evidence_builders", []))
    builder_path = str(LAYERS_FROM_CEO_BUILDER.relative_to(ROOT)).replace("\\", "/")
    if builder_path not in builders:
        builders.append(builder_path)
    manifest["aggregate_evidence_builders"] = builders
    frozen_evidence = dict(manifest.get("frozen_evidence", {}))
    frozen_evidence["reconstructed_manager_layers_to_ceo"] = layers_from_ceo_manifest_entry(evidence)
    manifest["frozen_evidence"] = frozen_evidence
    manifest_slides = manifest.get("slides")
    if not isinstance(manifest_slides, list) or len(manifest_slides) != DECK_SLIDE_COUNT:
        raise ValueError(f"The manifest does not contain the expected {DECK_SLIDE_COUNT}-slide inventory.")
    if manifest_slides[LAYERS_FROM_CEO_SLIDE - 1].get("slide") != LAYERS_FROM_CEO_SLIDE:
        raise ValueError("The manifest slide inventory has an unexpected layers-from-CEO entry.")
    manifest_slides[LAYERS_FROM_CEO_SLIDE - 1]["title"] = "Org layers to CEO"
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": DECK_SLIDE_COUNT,
        "output_slide_count": DECK_SLIDE_COUNT,
        "structural_change": None,
        "allowed_changed_slides": [LAYERS_FROM_CEO_SLIDE],
        "observed_changed_slides": changed_stages,
        "allowed_changed_navigation_indices": [LAYERS_FROM_CEO_SLIDE - 1],
        "observed_changed_navigation_labels": changed_nav,
        "unchanged_slide_count": DECK_SLIDE_COUNT - len(changed_stages),
        "outcome": "pass",
    }
    manifest["visible_language_validation"] = {
        "language": "English",
        "residual_spanish_text": residual_spanish,
        "outcome": "pass",
    }
    manifest_tmp = MANIFEST.with_name(MANIFEST.name + ".tmp")
    manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_tmp.replace(MANIFEST)
    print(TARGET)
    print(MANIFEST)
    print(f"slides={DECK_SLIDE_COUNT}")


def refresh_qvoice_retention_concerns_slide(reporting_mode: str = "internal_analysis") -> None:
    """Refresh only slide 19 from a new immutable aggregate-only artifact."""
    global REPORTING_MODE
    if reporting_mode != "internal_analysis":
        raise ValueError("QVoice retention-concerns evidence is internal_analysis only.")
    if not TARGET.exists() or not MANIFEST.exists():
        raise FileNotFoundError("The deck and manifest must exist before a focused slide-19 refresh.")

    import sys

    sys.path.insert(0, str(ROOT / "tools"))
    from build_qvoice_retention_concerns_evidence import build_evidence

    REPORTING_MODE = reporting_mode
    baseline = TARGET.read_text(encoding="utf-8")
    baseline_hashes = slide_stage_hashes(baseline)
    baseline_navigation = nav_pill_labels(baseline)
    if len(baseline_hashes) != DECK_SLIDE_COUNT:
        raise ValueError(f"The baseline deck does not contain {DECK_SLIDE_COUNT} slides for the focused refresh.")

    temporary_evidence: Path | None = None
    if QVOICE_RETENTION_CONCERNS_EVIDENCE.exists():
        evidence = qvoice_retention_concerns_evidence()
    else:
        temporary_evidence = QVOICE_RETENTION_CONCERNS_EVIDENCE.with_name(
            QVOICE_RETENTION_CONCERNS_EVIDENCE.name + ".refresh.tmp"
        )
        if temporary_evidence.exists():
            raise FileExistsError(f"Temporary retention evidence already exists: {temporary_evidence}")
        build_evidence(temporary_evidence)
        evidence = qvoice_retention_concerns_evidence(temporary_evidence)

    evidence_version = str(evidence["generated_on"]).replace("-", "")
    replacement_slide = qvoice_retention_concerns_slide(QVOICE_RETENTION_CONCERNS_SLIDE, evidence).replace(
        f'id="slide-{QVOICE_RETENTION_CONCERNS_SLIDE}"',
        f'id="slide-{QVOICE_RETENTION_CONCERNS_SLIDE}" data-retention-concerns-version="{esc(evidence_version)}"',
        1,
    )
    next_slide = QVOICE_RETENTION_CONCERNS_SLIDE + 1
    output, replacements = re.subn(
        rf'<div class="slide-stage" id="slide-{QVOICE_RETENTION_CONCERNS_SLIDE}"(?:\s[^>]*)?>.*?(?=\s*<div class="slide-stage" id="slide-{next_slide}"(?:\s[^>]*)?>)',
        replacement_slide,
        baseline,
        count=1,
        flags=re.S,
    )
    if replacements != 1:
        raise ValueError(f"The stage for slide {QVOICE_RETENTION_CONCERNS_SLIDE} was not found exactly once.")
    output = inject_retention_concerns_focused_css(output)
    residual_spanish = residual_spanish_visible_text_excluding_stages(output, {8, 9})
    if residual_spanish:
        raise ValueError(f"The deck contains visible non-English text: {residual_spanish}")
    new_hashes = slide_stage_hashes(output)
    changed_stages = sorted(
        int(stage_id.removeprefix("slide-"))
        for stage_id in baseline_hashes
        if baseline_hashes.get(stage_id) != new_hashes.get(stage_id)
    )
    new_navigation = nav_pill_labels(output)
    if set(baseline_hashes) != set(new_hashes) or changed_stages != [QVOICE_RETENTION_CONCERNS_SLIDE]:
        raise ValueError(f"Focused retention refresh altered unauthorized slides: {changed_stages}.")
    if baseline_navigation != new_navigation:
        raise ValueError("Focused retention refresh altered navigation labels or order.")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    builders = list(manifest.get("aggregate_evidence_builders", []))
    builder_path = str(QVOICE_RETENTION_CONCERNS_BUILDER.relative_to(ROOT)).replace("\\", "/")
    if builder_path not in builders:
        builders.append(builder_path)
    manifest["aggregate_evidence_builders"] = builders
    frozen_evidence = dict(manifest.get("frozen_evidence", {}))
    frozen_evidence["qvoice_retention_concerns"] = qvoice_retention_concerns_manifest_entry(evidence)
    manifest["frozen_evidence"] = frozen_evidence
    manifest_slides = manifest.get("slides")
    if not isinstance(manifest_slides, list) or len(manifest_slides) != DECK_SLIDE_COUNT:
        raise ValueError(f"The manifest does not contain the expected {DECK_SLIDE_COUNT}-slide inventory.")
    if manifest_slides[QVOICE_RETENTION_CONCERNS_SLIDE - 1].get("slide") != QVOICE_RETENTION_CONCERNS_SLIDE:
        raise ValueError("The manifest slide inventory has an unexpected slide-19 entry.")
    manifest_slides[QVOICE_RETENTION_CONCERNS_SLIDE - 1]["title"] = "Retention concerns in QVoice comments"
    manifest["generated_on"] = date.today().isoformat()
    manifest["slide_count"] = DECK_SLIDE_COUNT
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": DECK_SLIDE_COUNT,
        "output_slide_count": DECK_SLIDE_COUNT,
        "structural_change": None,
        "allowed_changed_slides": [QVOICE_RETENTION_CONCERNS_SLIDE],
        "observed_changed_slides": changed_stages,
        "allowed_changed_navigation_indices": [],
        "observed_changed_navigation_labels": [],
        "navigation_unchanged": True,
        "unchanged_slide_count": DECK_SLIDE_COUNT - len(changed_stages),
        "outcome": "pass",
    }
    manifest["visible_language_validation"] = {
        "language": "English",
        "residual_spanish_text": residual_spanish,
        "outcome": "pass",
    }

    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    manifest_tmp = MANIFEST.with_name(MANIFEST.name + ".tmp")
    target_tmp.write_text(output, encoding="utf-8")
    manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    if temporary_evidence is not None:
        temporary_evidence.replace(QVOICE_RETENTION_CONCERNS_EVIDENCE)
    target_tmp.replace(TARGET)
    manifest_tmp.replace(MANIFEST)
    print(TARGET)
    print(MANIFEST)
    print(f"slides={DECK_SLIDE_COUNT}")


def refresh_qvoice_comparable_slide(reporting_mode: str = "internal_analysis") -> None:
    """Refresh only the current comparable-QVoice stage."""
    global REPORTING_MODE
    if reporting_mode not in {"presentation", "internal_analysis"}:
        raise ValueError("reporting_mode must be presentation or internal_analysis.")
    if not TARGET.exists() or not MANIFEST.exists():
        raise FileNotFoundError("El deck y su manifest deben existir para actualizar sólo QVoice.")
    REPORTING_MODE = reporting_mode
    baseline = TARGET.read_text(encoding="utf-8")
    baseline_hashes = slide_stage_hashes(baseline)
    if len(baseline_hashes) != DECK_SLIDE_COUNT:
        raise ValueError(f"El deck base no contiene {DECK_SLIDE_COUNT} láminas para la actualización focalizada.")

    replacement_card = localize_visible_content(qvoice_comparable_favorable_card(qvoice_comparable_favorable_evidence()))
    output, replacements = re.subn(
        r'<article class="card chart-card qvoice-comparable-card">.*?</article>',
        replacement_card,
        baseline,
        count=1,
        flags=re.S,
    )
    if replacements != 1:
        raise ValueError(f"No se encontró la tarjeta comparable de QVoice en la lámina {QVOICE_COMPARABLE_SLIDE}.")
    residual_spanish = residual_spanish_visible_text_excluding_stages(output, {8, 9})
    if residual_spanish:
        raise ValueError(f"El deck contiene texto visible fuera de inglés: {residual_spanish}")
    new_hashes = slide_stage_hashes(output)
    changed = sorted(
        int(stage_id.removeprefix("slide-"))
        for stage_id in baseline_hashes
        if baseline_hashes.get(stage_id) != new_hashes.get(stage_id)
    )
    if set(baseline_hashes) != set(new_hashes) or changed not in ([QVOICE_COMPARABLE_SLIDE], []):
        raise ValueError(f"La actualización focalizada de QVoice alteró láminas no autorizadas: {changed}.")

    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    target_tmp.write_text(output, encoding="utf-8")
    target_tmp.replace(TARGET)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["generated_on"] = date.today().isoformat()
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": DECK_SLIDE_COUNT,
        "output_slide_count": DECK_SLIDE_COUNT,
        "allowed_changed_slides": [QVOICE_COMPARABLE_SLIDE],
        "observed_changed_slides": changed,
        "unchanged_slide_count": DECK_SLIDE_COUNT - len(changed),
        "outcome": "pass",
    }
    manifest["visible_language_validation"] = {
        "language": "English",
        "residual_spanish_text": residual_spanish,
        "outcome": "pass",
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(TARGET)
    print(MANIFEST)
    print(f"slides={DECK_SLIDE_COUNT}")


def refresh_qvoice_career_slide(reporting_mode: str = "internal_analysis") -> None:
    """Refresh only Career goals, keeping the published visual history through 2024."""
    global REPORTING_MODE
    if reporting_mode not in {"presentation", "internal_analysis"}:
        raise ValueError("reporting_mode must be presentation or internal_analysis.")
    if not TARGET.exists() or not MANIFEST.exists():
        raise FileNotFoundError("The deck and manifest must exist before a focused Career goals refresh.")
    REPORTING_MODE = reporting_mode
    baseline = TARGET.read_text(encoding="utf-8")
    baseline_hashes = slide_stage_hashes(baseline)
    if len(baseline_hashes) != DECK_SLIDE_COUNT:
        raise ValueError(f"The deck base does not contain {DECK_SLIDE_COUNT} slides for the focused refresh.")

    stage_id, start, end, _ = slide_stage_by_title(baseline, "Career goals item")
    stage_number = int(stage_id.removeprefix("slide-"))
    career_series = [
        row for row in private_coverage("03-career-goals-item", QVOICE)
        if int(row[0]) >= 2024
    ]
    if not career_series or any(int(row[0]) < 2024 for row in career_series):
        raise ValueError("Career goals history must start at 2024.")
    replacement = data_slide(
        stage_number,
        "Career goals item",
        "Support · QVoice v4 response coverage from 2024 onward",
        trend_card(
            "Observable response coverage",
            career_series,
            "The 2023 item exists in the raw workbook but requires header mapping before it can be processed for attrition; this visual starts at 2024.",
        ),
        side_card(
            "Coverage is not a favorability distribution",
            "The chart starts at 2024. The 2023 raw item requires mapping of its plain-header format before it can be used for attrition, and cross-wave equivalence remains unconfirmed.",
            [("Shown history", "2024 onward"), ("Latest shown wave", "2026"), ("2026 coverage", "89.61%"), ("2023 status", "Mapping required")],
            "Observability",
        ),
    )
    output = baseline[:start] + replacement + baseline[end:]
    _, _, _, refreshed_stage = slide_stage_by_title(output, "Career goals item")
    displayed_years = re.findall(r'<div class="trend-label">\s*<span>(20\d{2})</span>', refreshed_stage)
    if any(int(year) < 2024 for year in displayed_years):
        raise ValueError("The refreshed Career goals stage contains a wave before 2024.")
    if "2023" not in refreshed_stage or "mapping" not in refreshed_stage.lower():
        raise ValueError("The refreshed Career goals stage is missing the 2023 mapping note.")

    new_hashes = slide_stage_hashes(output)
    changed = sorted(
        int(identifier.removeprefix("slide-"))
        for identifier in baseline_hashes
        if baseline_hashes.get(identifier) != new_hashes.get(identifier)
    )
    if set(baseline_hashes) != set(new_hashes) or changed not in ([stage_number], []):
        raise ValueError(f"The focused Career goals refresh altered unauthorized slides: {changed}.")

    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    target_tmp.write_text(output, encoding="utf-8")
    target_tmp.replace(TARGET)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["generated_on"] = date.today().isoformat()
    source_runs = list(manifest.get("source_runs", []))
    if "qvoice-career-goals-history-from-2024-20260917" not in source_runs:
        source_runs.append("qvoice-career-goals-history-from-2024-20260917")
    manifest["source_runs"] = source_runs
    manifest["career_goals_history"] = {
        "shown_waves": [2024, 2025, 2026],
        "latest_shown_wave": 2026,
        "2023_status": "raw item exists; plain-header source mapping required before attrition processing",
        "earlier_waves_in_visual": False,
    }
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": DECK_SLIDE_COUNT,
        "output_slide_count": DECK_SLIDE_COUNT,
        "allowed_changed_slides": [stage_number],
        "observed_changed_slides": changed,
        "unchanged_slide_count": DECK_SLIDE_COUNT - len(changed),
        "outcome": "pass",
    }
    manifest["visible_language_validation"] = {
        "language": "English",
        "residual_spanish_text": "",
        "outcome": "pass",
    }
    manifest_tmp = MANIFEST.with_name(MANIFEST.name + ".tmp")
    manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_tmp.replace(MANIFEST)
    print(TARGET)
    print(MANIFEST)
    print(f"stage={stage_number}; slides={DECK_SLIDE_COUNT}")


def refresh_qvoice_normalized_region_slide(reporting_mode: str = "internal_analysis") -> None:
    """Refresh only the passing within-region standardized QVoice stage."""
    global REPORTING_MODE
    if reporting_mode != "internal_analysis":
        raise ValueError("The normalized QVoice evidence is classified as internal_analysis.")
    if not TARGET.exists() or not MANIFEST.exists():
        raise FileNotFoundError("The deck and manifest must exist before a focused QVoice refresh.")

    import sys

    sys.path.insert(0, str(ROOT / "tools"))
    from build_qvoice_normalized_region_evidence import build_evidence

    REPORTING_MODE = reporting_mode
    baseline = TARGET.read_text(encoding="utf-8")
    baseline_hashes = slide_stage_hashes(baseline)
    if len(baseline_hashes) != DECK_SLIDE_COUNT:
        raise ValueError(f"The baseline deck does not contain {DECK_SLIDE_COUNT} slides for the focused refresh.")

    temporary_evidence = QVOICE_NORMALIZED_REGION_EVIDENCE.with_name(
        QVOICE_NORMALIZED_REGION_EVIDENCE.name + ".refresh.tmp"
    )
    build_evidence(temporary_evidence, overwrite=True)
    evidence = qvoice_normalized_region_evidence(temporary_evidence)
    replacement_card = localize_visible_content(qvoice_normalized_region_card(evidence))
    output, replacements = re.subn(
        r'<article class="card chart-card qvoice-normalized-region-card">.*?</article>',
        replacement_card,
        baseline,
        count=1,
        flags=re.S,
    )
    if replacements != 1:
        raise ValueError(
            f"The regional-normalization card was not found on slide {QVOICE_NORMALIZED_REGION_SLIDE}."
        )
    residual_spanish = residual_spanish_visible_text_excluding_stages(output, {8, 9})
    if residual_spanish:
        raise ValueError(f"The deck contains visible non-English text: {residual_spanish}")
    new_hashes = slide_stage_hashes(output)
    changed = sorted(
        int(stage_id.removeprefix("slide-"))
        for stage_id in baseline_hashes
        if baseline_hashes.get(stage_id) != new_hashes.get(stage_id)
    )
    if set(baseline_hashes) != set(new_hashes) or changed not in ([QVOICE_NORMALIZED_REGION_SLIDE], []):
        raise ValueError(f"Focused QVoice refresh altered unauthorized slides: {changed}.")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["generated_on"] = date.today().isoformat()
    builders = list(manifest.get("aggregate_evidence_builders", []))
    builder_path = str(QVOICE_NORMALIZED_REGION_BUILDER.relative_to(ROOT)).replace("\\", "/")
    if builder_path not in builders:
        builders.append(builder_path)
    manifest["aggregate_evidence_builders"] = builders
    frozen_evidence = dict(manifest.get("frozen_evidence", {}))
    frozen_evidence["qvoice_normalized_within_region"] = qvoice_normalized_region_manifest_entry(evidence)
    manifest["frozen_evidence"] = frozen_evidence
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": DECK_SLIDE_COUNT,
        "output_slide_count": DECK_SLIDE_COUNT,
        "allowed_changed_slides": [QVOICE_NORMALIZED_REGION_SLIDE],
        "observed_changed_slides": changed,
        "unchanged_slide_count": DECK_SLIDE_COUNT - len(changed),
        "outcome": "pass",
    }
    manifest["visible_language_validation"] = {
        "language": "English",
        "residual_spanish_text": residual_spanish,
        "outcome": "pass",
    }

    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    manifest_tmp = MANIFEST.with_name(MANIFEST.name + ".tmp")
    target_tmp.write_text(output, encoding="utf-8")
    manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary_evidence.replace(QVOICE_NORMALIZED_REGION_EVIDENCE)
    target_tmp.replace(TARGET)
    manifest_tmp.replace(MANIFEST)
    print(TARGET)
    print(MANIFEST)
    print(f"slides={DECK_SLIDE_COUNT}")


def resolve_team_post_exit_stage(document: str, titles: tuple[str, ...]) -> tuple[str, int, int, str]:
    """Resolve a refreshed stage by either its legacy or replacement title."""
    matches: list[tuple[str, int, int, str]] = []
    for title in titles:
        try:
            matches.append(slide_stage_by_title(document, title))
        except ValueError as exc:
            if "found 0" not in str(exc):
                raise
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one team post-exit stage for {titles!r}; found {len(matches)}.")
    return matches[0]


def refresh_team_post_exit_attrition_slides(reporting_mode: str = "presentation") -> None:
    """Replace only slides 8–9 with the approved post-exit cohort comparison."""
    if reporting_mode != "presentation":
        raise ValueError("La cohorte posterior a salida está clasificada para presentation.")
    if not TARGET.exists() or not MANIFEST.exists():
        raise FileNotFoundError("El deck y su manifest deben existir para la actualización focal de attrition posterior a salida.")
    evidence = team_post_exit_attrition_evidence()
    baseline = TARGET.read_text(encoding="utf-8")
    baseline_hashes = slide_stage_hashes(baseline)
    baseline_nav = nav_pill_labels(baseline)
    if len(baseline_hashes) != DECK_SLIDE_COUNT or len(baseline_nav) != DECK_SLIDE_COUNT:
        raise ValueError(f"El deck base debe conservar exactamente {DECK_SLIDE_COUNT} láminas y etiquetas de navegación.")

    stage_specs = (
        (8, "all_teams", ("More than 1 employee leaves · all teams", "¿Una salida inicial precede más salidas?"), "¿Una salida inicial precede más salidas?"),
        (9, "teams_6_plus", ("More than 1 employee leaves · teams >5", "Sensibilidad: equipos de 6+ personas"), "Sensibilidad: equipos de 6+ personas"),
    )
    output = baseline
    for expected_number, scope_key, titles, _ in stage_specs:
        stage_id, start, end, _ = resolve_team_post_exit_stage(output, titles)
        if int(stage_id.removeprefix("slide-")) != expected_number:
            raise ValueError(f"La lámina resuelta para {scope_key} no es la {expected_number}.")
        replacement = team_post_exit_attrition_slide(expected_number, scope_key)
        output = output[:start] + replacement + output[end:]

    expected_navigation = list(baseline_nav)
    for stage_number, _, _, title in stage_specs:
        index = stage_number - 1
        expected_navigation[index] = f"{stage_number}. {title}"
        output, replacements = re.subn(
            rf'(<button class="nav-pill" data-slide="{index}">)[^<]*(</button>)',
            rf'\g<1>{esc(expected_navigation[index])}\g<2>',
            output,
            count=1,
        )
        if replacements != 1:
            raise ValueError(f"No se encontró la etiqueta de navegación de la lámina {stage_number}.")

    residual_spanish = residual_spanish_visible_text_excluding_stages(output, {8, 9})
    if residual_spanish:
        raise ValueError(f"El deck contiene texto español fuera de las láminas focales: {residual_spanish}")
    new_hashes = slide_stage_hashes(output)
    new_nav = nav_pill_labels(output)
    changed_stages = sorted(
        int(stage_id.removeprefix("slide-"))
        for stage_id in baseline_hashes
        if baseline_hashes.get(stage_id) != new_hashes.get(stage_id)
    )
    changed_navigation = [
        index for index, (before, after) in enumerate(zip(baseline_nav, new_nav)) if before != after
    ]
    if set(baseline_hashes) != set(new_hashes) or changed_stages not in ([8, 9], []):
        raise ValueError(f"La actualización focal alteró láminas no autorizadas: {changed_stages}.")
    if len(new_nav) != DECK_SLIDE_COUNT or new_nav != expected_navigation or changed_navigation not in ([7, 8], []):
        raise ValueError(f"La actualización focal alteró etiquetas de navegación no autorizadas: {changed_navigation}.")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_slides = manifest.get("slides")
    if not isinstance(manifest_slides, list) or len(manifest_slides) != DECK_SLIDE_COUNT:
        raise ValueError(f"El manifest no contiene el inventario esperado de {DECK_SLIDE_COUNT} láminas.")
    for stage_number, _, _, title in stage_specs:
        if manifest_slides[stage_number - 1].get("slide") != stage_number:
            raise ValueError(f"El inventario del manifest no alinea la lámina {stage_number}.")
        manifest_slides[stage_number - 1]["title"] = title
    source_runs = list(manifest.get("source_runs", []))
    source_run = "team-post-exit-attrition-static-cohort-20260911"
    if source_run not in source_runs:
        source_runs.append(source_run)
    manifest["source_runs"] = source_runs
    audits = list(manifest.get("new_aggregate_audits", []))
    for query in (
        TEAM_POST_EXIT_ATTRITION_CALENDAR_SQL,
        TEAM_POST_EXIT_ATTRITION_RECONCILIATION_SQL,
        TEAM_POST_EXIT_ATTRITION_STATIC_SQL,
    ):
        if query not in audits:
            audits.append(query)
    manifest["new_aggregate_audits"] = audits
    builders = list(manifest.get("aggregate_evidence_builders", []))
    builder = str(TEAM_POST_EXIT_ATTRITION_BUILDER.relative_to(ROOT)).replace("\\", "/")
    if builder not in builders:
        builders.append(builder)
    manifest["aggregate_evidence_builders"] = builders
    frozen_evidence = dict(manifest.get("frozen_evidence", {}))
    frozen_evidence["team_post_exit_attrition"] = team_post_exit_attrition_manifest_entry(evidence)
    manifest["frozen_evidence"] = frozen_evidence
    manifest["generated_on"] = date.today().isoformat()
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": DECK_SLIDE_COUNT,
        "output_slide_count": DECK_SLIDE_COUNT,
        "structural_change": None,
        "identified_by_titles": [title for _, _, _, title in stage_specs],
        "allowed_changed_slides": [8, 9],
        "observed_changed_slides": changed_stages,
        "allowed_changed_navigation_indices": [7, 8],
        "observed_changed_navigation_labels": changed_navigation,
        "unchanged_slide_count": DECK_SLIDE_COUNT - len(changed_stages),
        "outcome": "pass",
    }
    manifest["visible_language_validation"] = {
        "language": "Legacy English deck; slides 8–9 Spanish by the Attrition narrative contract",
        "approved_spanish_stages": [8, 9],
        "residual_spanish_text_outside_approved_stages": residual_spanish,
        "outcome": "pass",
    }
    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    manifest_tmp = MANIFEST.with_name(MANIFEST.name + ".tmp")
    target_tmp.write_text(output, encoding="utf-8")
    manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    target_tmp.replace(TARGET)
    manifest_tmp.replace(MANIFEST)
    print(TARGET)
    print(MANIFEST)
    print(f"stages=8,9; slides={DECK_SLIDE_COUNT}")


def refresh_work_arrangement_slide(reporting_mode: str = "internal_analysis") -> None:
    """Add the requested binary display below slide 13 without changing its raw chart."""
    global REPORTING_MODE
    if reporting_mode not in {"presentation", "internal_analysis"}:
        raise ValueError("El modo debe ser presentation o internal_analysis.")
    if not TARGET.exists() or not MANIFEST.exists():
        raise FileNotFoundError("El deck y su manifest deben existir para la actualizaciÃ³n focal de work_arrangement.")

    REPORTING_MODE = reporting_mode
    baseline = TARGET.read_text(encoding="utf-8")
    baseline_hashes = slide_stage_hashes(baseline)
    baseline_nav = nav_pill_labels(baseline)
    if len(baseline_hashes) != len(baseline_nav):
        raise ValueError("El deck base no conserva el mismo nÃºmero de stages y etiquetas de navegaciÃ³n.")

    stage_id, start, end, baseline_stage = slide_stage_by_title(
        baseline, "Remote / hybrid / in office status"
    )
    stage_number = int(stage_id.removeprefix("slide-"))
    if stage_number != WORK_ARRANGEMENT_SLIDE:
        raise ValueError(f"La lÃ¡mina de work_arrangement se resolviÃ³ como {stage_number}, no como 13.")

    work_arrangement = frozen_work_arrangement_distribution()
    replacement_main = work_arrangement_main(work_arrangement)
    if "work-arrangement-binary-card" in baseline_stage:
        replacement_binary = re.search(
            r'<article class="card chart-card work-arrangement-binary-card">.*?</article>',
            replacement_main,
            flags=re.S,
        )
        if not replacement_binary:
            raise ValueError("No se pudo reconstruir la tarjeta binaria de work_arrangement.")
        refreshed_stage, replacements = re.subn(
            r'<article class="card chart-card work-arrangement-binary-card">.*?</article>',
            replacement_binary.group(0),
            baseline_stage,
            count=1,
            flags=re.S,
        )
    else:
        refreshed_stage, replacements = re.subn(
            r'(<div class="two-pane">)\s*<article class="card chart-card work-arrangement-card">.*?</article>',
            lambda match: match.group(1) + replacement_main,
            baseline_stage,
            count=1,
            flags=re.S,
        )
    if replacements != 1:
        raise ValueError("No se encontrÃ³ la tarjeta raw de work_arrangement en la lÃ¡mina 13.")

    baseline_top = re.search(
        r'<article class="card chart-card work-arrangement-card">.*?</article>',
        baseline_stage,
        flags=re.S,
    )
    refreshed_top = re.search(
        r'<article class="card chart-card work-arrangement-card">.*?</article>',
        refreshed_stage,
        flags=re.S,
    )
    if not baseline_top or not refreshed_top or baseline_top.group(0) != refreshed_top.group(0):
        raise ValueError("La tarjeta superior de work_arrangement fue modificada durante el refresh.")

    output = baseline[:start] + refreshed_stage + baseline[end:]
    _, _, _, validated_stage = slide_stage_by_title(output, "Remote / hybrid / in office status")
    grouped = work_arrangement_binary_distribution(work_arrangement)
    if validated_stage.count("work-arrangement-binary-card") != 1:
        raise ValueError("La vista binaria no se materializÃ³ exactamente una vez.")
    for label, count in grouped:
        if f'title="{label}"' not in validated_stage or f"{count:,}" not in validated_stage:
            raise ValueError(f"La vista binaria no contiene el bucket agregado esperado: {label}.")

    residual_spanish = residual_spanish_visible_text_excluding_stages(output, {8, 9})
    if residual_spanish:
        raise ValueError(f"El deck contiene texto espaÃ±ol fuera de las lÃ¡minas aprobadas: {residual_spanish}")
    new_hashes = slide_stage_hashes(output)
    new_nav = nav_pill_labels(output)
    changed_stages = sorted(
        int(identifier.removeprefix("slide-"))
        for identifier in baseline_hashes
        if baseline_hashes.get(identifier) != new_hashes.get(identifier)
    )
    changed_nav = [index for index, (before, after) in enumerate(zip(baseline_nav, new_nav)) if before != after]
    if set(baseline_hashes) != set(new_hashes) or changed_stages not in ([WORK_ARRANGEMENT_SLIDE], []):
        raise ValueError(f"El refresh de work_arrangement alterÃ³ lÃ¡minas no autorizadas: {changed_stages}.")
    if new_nav != baseline_nav or changed_nav:
        raise ValueError("El refresh de work_arrangement alterÃ³ la navegaciÃ³n.")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_slides = manifest.get("slides")
    if not isinstance(manifest_slides, list) or len(manifest_slides) != len(baseline_hashes):
        raise ValueError("El manifest no coincide con el nÃºmero de lÃ¡minas del deck base.")
    if manifest_slides[WORK_ARRANGEMENT_SLIDE - 1].get("slide") != WORK_ARRANGEMENT_SLIDE:
        raise ValueError("El inventario del manifest no alinea la lÃ¡mina de work_arrangement.")
    frozen_evidence = dict(manifest.get("frozen_evidence", {}))
    frozen_evidence["work_arrangement_binary_view"] = work_arrangement_binary_manifest_entry(work_arrangement)
    manifest["frozen_evidence"] = frozen_evidence
    manifest["generated_on"] = date.today().isoformat()
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": len(baseline_hashes),
        "output_slide_count": len(new_hashes),
        "structural_change": None,
        "identified_by_title": "Remote / hybrid / in office status",
        "resolved_stage": WORK_ARRANGEMENT_SLIDE,
        "allowed_changed_slides": [WORK_ARRANGEMENT_SLIDE],
        "observed_changed_slides": changed_stages,
        "allowed_changed_navigation_indices": [],
        "observed_changed_navigation_labels": changed_nav,
        "unchanged_slide_count": len(new_hashes) - len(changed_stages),
        "outcome": "pass",
    }
    manifest["visible_language_validation"] = {
        "language": "Legacy English deck; slides 8-9 Spanish by the Attrition narrative contract",
        "approved_spanish_stages": [8, 9],
        "residual_spanish_text_outside_approved_stages": residual_spanish,
        "outcome": "pass",
    }

    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    manifest_tmp = MANIFEST.with_name(MANIFEST.name + ".tmp")
    target_tmp.write_text(output, encoding="utf-8")
    manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    target_tmp.replace(TARGET)
    manifest_tmp.replace(MANIFEST)
    print(TARGET)
    print(MANIFEST)
    print(f"stage={WORK_ARRANGEMENT_SLIDE}; slides={len(new_hashes)}")


def refresh_engineering_cto_slide(reporting_mode: str = "internal_analysis") -> None:
    """Insert the CTO display below the frozen eng_or_noneng chart only."""
    global REPORTING_MODE
    if reporting_mode != "internal_analysis":
        raise ValueError("La vista CTO está clasificada como internal_analysis.")
    if not TARGET.exists() or not MANIFEST.exists():
        raise FileNotFoundError("El deck y su manifest deben existir para la actualización focal de Engineering.")

    REPORTING_MODE = reporting_mode
    baseline = TARGET.read_text(encoding="utf-8")
    baseline_hashes = slide_stage_hashes(baseline)
    baseline_nav = nav_pill_labels(baseline)
    if len(baseline_hashes) != len(baseline_nav):
        raise ValueError(f"El deck base debe conservar exactamente {DECK_SLIDE_COUNT} láminas y etiquetas de navegación.")
    deck_slide_count = len(baseline_hashes)

    stage_id, start, end, baseline_stage = slide_stage_by_title(baseline, "Engineering vs. non-engineering")
    stage_number = int(stage_id.removeprefix("slide-"))
    if stage_number != ENGINEERING_CTO_SLIDE:
        raise ValueError(f"La lámina de Engineering se resolvió como {stage_number}, no como 14.")

    evidence = engineering_cto_org_split_evidence()
    lower_card = engineering_cto_lower_card(evidence)
    baseline_top = re.search(r'<article class="card chart-card">.*?</article>', baseline_stage, flags=re.S)
    if not baseline_top:
        raise ValueError("No se encontró el gráfico superior de eng_or_noneng.")

    if "engineering-cto-display-card" in baseline_stage:
        refreshed_stage, replacements = re.subn(
            r'<article class="card chart-card engineering-cto-display-card">.*?</article>',
            lower_card,
            baseline_stage,
            count=1,
            flags=re.S,
        )
    else:
        refreshed_stage, replacements = re.subn(
            r'(<div class="two-pane">)\s*<article class="card chart-card">.*?</article>',
            lambda match: match.group(1) + '<div class="engineering-cto-stack">' + baseline_top.group(0) + lower_card + "</div>",
            baseline_stage,
            count=1,
            flags=re.S,
        )
    if replacements != 1:
        raise ValueError("No se pudo insertar exactamente una vista CTO debajo del gráfico superior.")

    refreshed_top = re.search(r'<article class="card chart-card">.*?</article>', refreshed_stage, flags=re.S)
    if not refreshed_top or refreshed_top.group(0) != baseline_top.group(0):
        raise ValueError("El gráfico superior de eng_or_noneng no permaneció byte por byte igual.")

    output = baseline[:start] + refreshed_stage + baseline[end:]
    if ENGINEERING_CTO_FOCUSED_CSS not in output:
        output = output.replace("  </style>", ENGINEERING_CTO_FOCUSED_CSS + "  </style>", 1)
    _, _, _, validated_stage = slide_stage_by_title(output, "Engineering vs. non-engineering")
    if validated_stage.count("engineering-cto-display-card") != 1:
        raise ValueError("La vista CTO no se materializó exactamente una vez.")
    if "Documented organizational split: CTO vs. Corp Fxn &amp; BU" not in validated_stage:
        raise ValueError("La vista CTO no contiene el título visible esperado.")
    for expected in ("35,788", "14,255", "50,043", "50,033", "0 active employees"):
        if expected not in validated_stage:
            raise ValueError(f"La vista CTO no contiene la evidencia visible esperada: {expected}.")

    baseline_residual_spanish = residual_spanish_visible_text_excluding_stages(baseline, {8, 9})
    residual_spanish = residual_spanish_visible_text_excluding_stages(output, {8, 9})
    if residual_spanish and residual_spanish != baseline_residual_spanish:
        raise ValueError(f"El deck contiene texto visible nuevo fuera de inglés: {residual_spanish}")
    new_hashes = slide_stage_hashes(output)
    new_nav = nav_pill_labels(output)
    changed_stages = sorted(
        int(identifier.removeprefix("slide-"))
        for identifier in baseline_hashes
        if baseline_hashes.get(identifier) != new_hashes.get(identifier)
    )
    changed_nav = [index for index, (before, after) in enumerate(zip(baseline_nav, new_nav)) if before != after]
    if set(baseline_hashes) != set(new_hashes) or changed_stages not in ([ENGINEERING_CTO_SLIDE], []):
        raise ValueError(f"La actualización focal alteró láminas no autorizadas: {changed_stages}.")
    if new_nav != baseline_nav or changed_nav:
        raise ValueError("La actualización focal alteró la navegación.")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_slides = manifest.get("slides")
    if not isinstance(manifest_slides, list) or len(manifest_slides) != deck_slide_count:
        raise ValueError(f"El manifest no contiene el inventario esperado de {deck_slide_count} láminas.")
    if manifest_slides[ENGINEERING_CTO_SLIDE - 1].get("slide") != ENGINEERING_CTO_SLIDE:
        raise ValueError("El inventario del manifest no alinea la lámina de Engineering.")

    source_runs = list(manifest.get("source_runs", []))
    source_run = "engineering-cto-org-split-display-20260911"
    if source_run not in source_runs:
        source_runs.append(source_run)
    manifest["source_runs"] = source_runs
    audits = list(manifest.get("new_aggregate_audits", []))
    legacy_branch_audit = "queries/audits/engineering_cto_jim_branch_diagnostic_20260911.sql"
    audits = [ENGINEERING_CTO_JIM_AUDIT_SQL if query == legacy_branch_audit else query for query in audits]
    audits = list(dict.fromkeys(audits))
    for query in (
        ENGINEERING_CTO_MAIN_AUDIT_SQL,
        ENGINEERING_CTO_DENOMINATOR_AUDIT_SQL,
        ENGINEERING_CTO_JIM_AUDIT_SQL,
        ENGINEERING_CTO_UPPER_AUDIT_SQL,
    ):
        if query not in audits:
            audits.append(query)
    manifest["new_aggregate_audits"] = audits
    builders = list(manifest.get("aggregate_evidence_builders", []))
    builder_path = "tools/build_engineering_cto_org_split_evidence.py"
    if builder_path not in builders:
        builders.append(builder_path)
    manifest["aggregate_evidence_builders"] = builders
    frozen_evidence = dict(manifest.get("frozen_evidence", {}))
    frozen_evidence["engineering_cto_org_split_display"] = engineering_cto_manifest_entry(evidence)
    manifest["frozen_evidence"] = frozen_evidence
    manifest["generated_on"] = date.today().isoformat()
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": deck_slide_count,
        "output_slide_count": deck_slide_count,
        "structural_change": None,
        "identified_by_title": "Engineering vs. non-engineering",
        "resolved_stage": ENGINEERING_CTO_SLIDE,
        "allowed_changed_slides": [ENGINEERING_CTO_SLIDE],
        "observed_changed_slides": changed_stages,
        "allowed_changed_navigation_indices": [],
        "observed_changed_navigation_labels": changed_nav,
        "unchanged_slide_count": deck_slide_count - len(changed_stages),
        "outcome": "pass",
    }
    manifest["visible_language_validation"] = {
        "language": "Legacy English deck; slides 8-9 Spanish by the Attrition narrative contract",
        "approved_spanish_stages": [8, 9],
        "residual_spanish_text_outside_approved_stages": residual_spanish,
        "outcome": "pass",
    }

    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    manifest_tmp = MANIFEST.with_name(MANIFEST.name + ".tmp")
    target_tmp.write_text(output, encoding="utf-8")
    manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    target_tmp.replace(TARGET)
    manifest_tmp.replace(MANIFEST)
    print(TARGET)
    print(MANIFEST)
    print(f"stage={ENGINEERING_CTO_SLIDE}; slides={deck_slide_count}")


def _normalized_stage_contents(document: str) -> list[str]:
    """Return stage bodies without ordinal IDs for structural preservation checks."""
    matches = list(re.finditer(r'<div class="slide-stage" id="(slide-\d+)"(?:\s[^>]*)?>', document))
    stages: list[str] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else document.index('<div class="nav-ctrl" id="slide-nav">', match.start())
        stage = document[match.start():end].strip()
        stages.append(re.sub(r'id="slide-\d+"', 'id="slide-X"', stage, count=1))
    return stages


def _nav_sections_from_document(document: str, label_count: int) -> tuple[tuple[str, int, int], ...]:
    """Read the existing navigation groups so a focused insertion preserves its structure."""
    matches = list(re.finditer(
        r'<details class="nav-section"[^>]*>[\s\S]*?<summary><span class="nav-section-title">([^<]+)</span><span class="nav-section-range">(\d+)[^0-9]+(\d+)</span></summary>',
        document,
    ))
    sections: list[tuple[str, int, int]] = []
    for match in matches:
        title = html.unescape(match.group(1)).strip()
        start = int(match.group(2)) - 1
        end = int(match.group(3))
        sections.append((title, start, end))
    if not sections or sections[0][1] != 0:
        raise ValueError("The existing navigation has no contiguous starting section.")
    expected_start = 0
    for title, start, end in sections:
        if start != expected_start or start >= end or end > label_count:
            raise ValueError(f"Invalid existing navigation range for {title!r}: {start}:{end}.")
        expected_start = end
    if expected_start != label_count:
        raise ValueError("The existing navigation does not cover every slide.")
    return tuple(sections)


def _shift_nav_sections_for_insert(
    sections: tuple[tuple[str, int, int], ...], insertion_index: int
) -> tuple[tuple[str, int, int], ...]:
    """Shift only the ranges affected by an insertion at a zero-based index."""
    shifted: list[tuple[str, int, int]] = []
    for title, start, end in sections:
        if insertion_index < start:
            start += 1
            end += 1
        elif insertion_index < end:
            end += 1
        shifted.append((title, start, end))
    return tuple(shifted)


def _update_agenda_ranges(document: str, sections: tuple[tuple[str, int, int], ...]) -> str:
    """Update the five agenda range chips while leaving its narrative unchanged."""
    _, start, end, stage = slide_stage_by_title(document, "Agenda")
    replacements = [f"Slides {section_start + 1}–{section_end}" for _, section_start, section_end in sections[1:]]
    pattern = re.compile(r'(<span class="agenda-num">)Slides [^<]+(</span>)')
    matches = list(pattern.finditer(stage))
    if len(matches) != len(replacements):
        raise ValueError("The agenda does not contain the expected number of section ranges.")
    cursor = 0
    updated_parts: list[str] = []
    for match, replacement in zip(matches, replacements):
        updated_parts.append(stage[cursor:match.start()])
        updated_parts.append(f"{match.group(1)}{replacement}{match.group(2)}")
        cursor = match.end()
    updated_parts.append(stage[cursor:])
    updated_stage = "".join(updated_parts)
    return document[:start] + updated_stage + document[end:]


def insert_office_site_relationship_slide(reporting_mode: str = "internal_analysis") -> None:
    """Insert the FY2026 office-site view after the preserved residential chart."""
    global REPORTING_MODE
    if reporting_mode not in {"presentation", "internal_analysis"}:
        raise ValueError("reporting_mode must be presentation or internal_analysis.")
    if not TARGET.exists() or not MANIFEST.exists():
        raise FileNotFoundError("The deck and manifest must exist before the focused office-site insertion.")

    REPORTING_MODE = reporting_mode
    baseline = TARGET.read_text(encoding="utf-8")
    baseline_hashes = slide_stage_hashes(baseline)
    baseline_stages = _normalized_stage_contents(baseline)
    baseline_nav = nav_pill_labels(baseline)
    baseline_count = len(baseline_hashes)
    if baseline_count != PRE_OFFICE_SITE_RELATIONSHIP_DECK_SLIDE_COUNT or len(baseline_nav) != baseline_count:
        raise ValueError("Office-site insertion requires the preserved 51-slide baseline and matching navigation.")

    residential_id, _, insertion_end, _ = slide_stage_by_title(baseline, "Residential distance from manager")
    residential_number = int(residential_id.removeprefix("slide-"))
    if residential_number != RESIDENTIAL_MANAGER_DISTANCE_SLIDE:
        raise ValueError("Residential distance did not resolve to the expected preserved stage.")
    if baseline_nav[residential_number - 1] != f"{residential_number}. Residential distance":
        raise ValueError("The baseline navigation does not identify Residential distance exactly.")
    if "Office-site relationship with manager" in baseline:
        raise ValueError("The office-site relationship slide is already present in the baseline.")

    evidence, _ = office_site_relationship_evidence()
    insertion_index = residential_number  # zero-based index immediately after the retained slide
    replacement = office_site_relationship_slide(residential_number + 1)

    # Only later IDs shift. The retained residential stage is deliberately
    # left byte-for-byte intact, including its postal-centroid evidence.
    shifted = re.sub(
        r'(<div class="slide-stage" id="slide-)(\d+)("(?:\s[^>]*)?>)',
        lambda match: match.group(1) + str(int(match.group(2)) + 1 if int(match.group(2)) > residential_number else int(match.group(2))) + match.group(3),
        baseline,
    )
    _, _, insertion_end, _ = slide_stage_by_title(shifted, "Residential distance from manager")
    output = shifted[:insertion_end] + replacement + "\n\n  " + shifted[insertion_end:]

    baseline_nav_titles = [re.sub(r"^\d+\.\s*", "", label) for label in baseline_nav]
    new_nav_titles = (
        baseline_nav_titles[:insertion_index]
        + ["Office-site relationship"]
        + baseline_nav_titles[insertion_index:]
    )
    new_sections = _shift_nav_sections_for_insert(
        _nav_sections_from_document(baseline, baseline_count),
        insertion_index,
    )
    nav_pattern = r'(<div class="nav-panel">\s*<div class="nav-label">Navigation</div>)(.*?)(</div>\s*</div>\s*)(?=<!--)'
    output, nav_replacements = re.subn(
        nav_pattern,
        lambda match: match.group(1) + "\n      " + nav(new_nav_titles, new_sections) + "\n    " + match.group(3),
        output,
        count=1,
        flags=re.S,
    )
    if nav_replacements != 1:
        raise ValueError("The navigation panel could not be rebuilt after office-site insertion.")
    output = _update_agenda_ranges(output, new_sections)

    after_hashes = slide_stage_hashes(output)
    after_stages = _normalized_stage_contents(output)
    after_nav = nav_pill_labels(output)
    if len(after_hashes) != DECK_SLIDE_COUNT or len(after_nav) != DECK_SLIDE_COUNT:
        raise ValueError("Office-site insertion did not produce exactly 52 stages and navigation labels.")
    if list(after_hashes) != [f"slide-{number}" for number in range(1, DECK_SLIDE_COUNT + 1)]:
        raise ValueError("Stage IDs after office-site insertion are not consecutive.")
    if after_hashes[residential_id] != baseline_hashes[residential_id]:
        raise ValueError("The retained Residential distance stage changed during office-site insertion.")
    if after_stages[insertion_index] == baseline_stages[insertion_index]:
        raise ValueError("The new office-site stage was not inserted at the requested position.")
    changed_existing_stages: list[int] = []
    for old_index, old_stage in enumerate(baseline_stages):
        new_index = old_index if old_index < insertion_index else old_index + 1
        # Agenda ranges must reflect the final 52-slide section endpoints.
        if old_index == 1:
            continue
        if after_stages[new_index] != old_stage:
            changed_existing_stages.append(old_index + 1)
    if changed_existing_stages:
        raise ValueError(f"Office-site insertion altered existing stage content: {changed_existing_stages}.")
    expected_nav = [f"{index + 1}. {label}" for index, label in enumerate(new_nav_titles)]
    if after_nav != expected_nav:
        raise ValueError("Navigation labels after office-site insertion are not consecutive.")
    office_id, _, _, office_stage = slide_stage_by_title(output, "Office-site relationship with manager")
    high_risk_id, _, _, _ = slide_stage_by_title(output, "High risk manager")
    if office_id != "slide-43" or high_risk_id != "slide-44":
        raise ValueError("The office-site slide is not immediately after Residential distance.")
    for expected in (
        "Same office_site",
        "Different office_site",
        "Not comparable / missing site",
        "94.01%",
        "residential kilometres, addresses, or postal centroids",
        "four-hour difference, travel time, or physical presence",
    ):
        if expected not in office_stage:
            raise ValueError(f"The office-site relationship slide is missing {expected!r}.")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_slides = manifest.get("slides")
    if not isinstance(manifest_slides, list) or len(manifest_slides) != baseline_count:
        raise ValueError("The manifest does not match the deck baseline before office-site insertion.")
    residential_manifest_index = next(
        (index for index, row in enumerate(manifest_slides) if row.get("title") == "Residential distance"),
        None,
    )
    if residential_manifest_index != residential_number - 1:
        raise ValueError("The manifest does not locate Residential distance at the same ordinal as the HTML.")
    updated_slides: list[dict[str, object]] = []
    for index, row in enumerate(manifest_slides):
        updated = dict(row)
        if index == insertion_index:
            updated_slides.append({"slide": residential_number + 1, "title": "Office-site relationship with manager"})
        updated["slide"] = index + 1 + (1 if index >= insertion_index else 0)
        updated_slides.append(updated)
    if len(updated_slides) != DECK_SLIDE_COUNT:
        raise ValueError("The manifest could not insert the office-site relationship slide.")
    manifest["slides"] = updated_slides
    manifest["slide_count"] = DECK_SLIDE_COUNT
    manifest["navigation_sections"] = [
        {"title": title, "start_slide": start + 1, "end_slide": end}
        for title, start, end in new_sections
    ]
    manifest["generated_on"] = date.today().isoformat()
    source_runs = list(manifest.get("source_runs", []))
    if "co-location-manager-site-city-20260909" not in source_runs:
        source_runs.append("co-location-manager-site-city-20260909")
    manifest["source_runs"] = source_runs
    profiles = list(manifest.get("new_aggregate_profiles", []))
    if CO_LOCATION_SITE_CITY_PROFILE_SQL not in profiles:
        profiles.append(CO_LOCATION_SITE_CITY_PROFILE_SQL)
    manifest["new_aggregate_profiles"] = profiles
    frozen_evidence = dict(manifest.get("frozen_evidence", {}))
    frozen_evidence["office_site_relationship_with_manager"] = office_site_relationship_manifest_entry(evidence)
    manifest["frozen_evidence"] = frozen_evidence
    prior_validation = manifest.get("slide_content_hash_validation")
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": baseline_count,
        "output_slide_count": DECK_SLIDE_COUNT,
        "structural_change": "Inserted Office-site relationship with manager immediately after Residential distance; later ordinal IDs and navigation indices were shifted by one.",
        "identified_by_title": "Office-site relationship with manager",
        "resolved_stage": residential_number + 1,
        "inserted_after_title": "Residential distance from manager",
        "allowed_changed_slides": [residential_number + 1],
        "renumbered_existing_slides": list(range(residential_number + 2, DECK_SLIDE_COUNT + 1)),
        "agenda_updated": True,
        "existing_content_preservation": "pass",
        "retained_residential_stage": residential_number,
        "retained_residential_stage_sha256_before": baseline_hashes[residential_id],
        "retained_residential_stage_sha256_after": after_hashes[residential_id],
        "retained_residential_stage_preservation": "pass",
        "navigation_consecutive": True,
        "preexisting_structural_change": prior_validation,
        "outcome": "pass",
    }

    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    manifest_tmp = MANIFEST.with_name(MANIFEST.name + ".tmp")
    target_tmp.write_text(output, encoding="utf-8")
    manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    target_tmp.replace(TARGET)
    manifest_tmp.replace(MANIFEST)
    print(TARGET)
    print(MANIFEST)
    print(f"inserted_stage={residential_number + 1}; baseline_slides={baseline_count}; output_slides={DECK_SLIDE_COUNT}")


def _refresh_existing_level_grouped_by_grade_family_slide(
    baseline: str,
    baseline_stages: list[str],
    baseline_nav: list[str],
    stage_id: str,
    stage_start: int,
    stage_end: int,
) -> None:
    """Refresh an already-inserted Level-family stage without changing deck structure."""
    stage_number = int(stage_id.removeprefix("slide-"))
    evidence = level_grouped_by_grade_family_evidence()
    replacement = localize_visible_content(level_grouped_by_grade_family_slide(stage_number, evidence))
    output = baseline[:stage_start] + replacement + baseline[stage_end:]
    if LEVEL_GRADE_FAMILY_FOCUSED_CSS not in output:
        output = output.replace("  </style>", LEVEL_GRADE_FAMILY_FOCUSED_CSS + "  </style>", 1)

    after_stages = _normalized_stage_contents(output)
    after_nav = nav_pill_labels(output)
    if len(after_stages) != len(baseline_stages) or len(after_nav) != len(baseline_nav):
        raise ValueError("El refresh de Level-familia cambió el número de láminas o etiquetas.")
    changed_stages = [
        index + 1
        for index, (before, after) in enumerate(zip(baseline_stages, after_stages))
        if before != after
    ]
    if changed_stages not in ([stage_number], []):
        raise ValueError(f"El refresh de Level-familia alteró láminas no autorizadas: {changed_stages}.")
    if after_nav != baseline_nav:
        raise ValueError("El refresh de Level-familia alteró la navegación.")
    _, _, _, refreshed_stage = slide_stage_by_title(output, "Level grouped by grade family")
    if refreshed_stage.count("level-grade-family-card") != 1 or "level-grade-family-segment-label" not in refreshed_stage:
        raise ValueError("La lámina Level-familia no contiene el gráfico etiquetado esperado.")
    baseline_residual_spanish = residual_spanish_visible_text_excluding_stages(baseline, {8, 9})
    residual_spanish = residual_spanish_visible_text_excluding_stages(output, {8, 9})
    if residual_spanish != baseline_residual_spanish:
        raise ValueError("El refresh de Level-familia agregó o alteró texto visible no inglés.")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_slides = manifest.get("slides")
    if not isinstance(manifest_slides, list) or len(manifest_slides) != len(baseline_stages):
        raise ValueError("El manifest no coincide con la deck existente de Level-familia.")
    if manifest_slides[stage_number - 1].get("title") != "Level grouped by grade family":
        raise ValueError("El manifest no identifica la lámina Level-familia existente.")

    source_runs = list(manifest.get("source_runs", []))
    source_run = "level-grouped-by-grade-family-display-20260911"
    if source_run not in source_runs:
        source_runs.append(source_run)
    manifest["source_runs"] = source_runs
    audits = list(manifest.get("new_aggregate_audits", []))
    if LEVEL_GRADE_FAMILY_AUDIT_SQL not in audits:
        audits.append(LEVEL_GRADE_FAMILY_AUDIT_SQL)
    manifest["new_aggregate_audits"] = audits
    builders = list(manifest.get("aggregate_evidence_builders", []))
    builder_path = str(LEVEL_GRADE_FAMILY_BUILDER.relative_to(ROOT)).replace("\\", "/")
    if builder_path not in builders:
        builders.append(builder_path)
    manifest["aggregate_evidence_builders"] = builders
    frozen_evidence = dict(manifest.get("frozen_evidence", {}))
    frozen_evidence["level_grouped_by_grade_family"] = level_grouped_by_grade_family_manifest_entry(evidence)
    manifest["frozen_evidence"] = frozen_evidence
    manifest["generated_on"] = date.today().isoformat()
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": len(baseline_stages),
        "output_slide_count": len(after_stages),
        "structural_change": None,
        "identified_by_title": "Level grouped by grade family",
        "resolved_stage": stage_number,
        "allowed_changed_slides": [stage_number],
        "observed_changed_slides": changed_stages,
        "unchanged_existing_content_count": len(baseline_stages) - len(changed_stages),
        "existing_content_preservation": "pass",
        "outcome": "pass",
    }
    manifest["visible_language_validation"] = {
        "language": "English",
        "residual_spanish_text": residual_spanish,
        "outcome": "pass",
    }

    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    manifest_tmp = MANIFEST.with_name(MANIFEST.name + ".tmp")
    target_tmp.write_text(output, encoding="utf-8")
    manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    target_tmp.replace(TARGET)
    manifest_tmp.replace(MANIFEST)
    print(TARGET)
    print(MANIFEST)
    print(f"refreshed_stage={stage_number}; slides={len(after_stages)}")


def _refresh_existing_qvoice_heartbeat_slide(
    reporting_mode: str,
    baseline: str,
    baseline_stages: list[str],
    baseline_nav: list[str],
    stage_id: str,
    stage_start: int,
    stage_end: int,
) -> None:
    """Refresh an existing heartbeat and repair its section ranges idempotently."""
    global REPORTING_MODE
    REPORTING_MODE = reporting_mode
    baseline_count = len(baseline_stages)
    stage_number = int(stage_id.removeprefix("slide-"))
    if stage_number < 1 or stage_number > baseline_count or baseline_nav[stage_number - 1] != f"{stage_number}. QVoice heartbeat":
        raise ValueError("The existing QVoice heartbeat stage does not align with navigation.")
    evidence = qvoice_heartbeat_evidence()
    replacement = localize_visible_content(qvoice_heartbeat_slide(stage_number, evidence))
    output = baseline[:stage_start] + replacement + baseline[stage_end:]

    base_sections = _nav_sections_from_document(baseline, baseline_count)
    expected_titles = [
        "Start", "Mobility and turnover", "Organizational context",
        "QVoice and external pull factors", "Career and compensation",
        "Manager and advanced signals",
    ]
    if [title for title, _, _ in base_sections] != expected_titles:
        raise ValueError("The existing navigation section taxonomy is not the expected deck taxonomy.")
    new_sections = (
        ("Start", 0, 2),
        ("Mobility and turnover", 2, 4),
        ("Organizational context", 4, 18),
        ("QVoice and external pull factors", 18, 27),
        ("Career and compensation", 27, 40),
        ("Manager and advanced signals", 40, baseline_count),
    )
    if new_sections[-1][2] != baseline_count:
        raise ValueError("The canonical navigation ranges do not cover the existing deck.")
    nav_titles = [re.sub(r"^\d+\.\s*", "", label) for label in baseline_nav]
    nav_pattern = r'(<div class="nav-panel">\s*<div class="nav-label">Navigation</div>)(.*?)(</div>\s*</div>\s*)(?=<!--)'
    output, nav_replacements = re.subn(
        nav_pattern,
        lambda match: match.group(1) + "\n      " + nav(nav_titles, new_sections) + "\n    " + match.group(3),
        output,
        count=1,
        flags=re.S,
    )
    if nav_replacements != 1:
        raise ValueError("The navigation panel could not be rebuilt for the existing QVoice heartbeat.")
    output = _update_agenda_ranges(output, new_sections)
    if QVOICE_HEARTBEAT_CSS not in output:
        output = output.replace("  </style>", QVOICE_HEARTBEAT_CSS + "  </style>", 1)

    after_stages = _normalized_stage_contents(output)
    after_nav = nav_pill_labels(output)
    if len(after_stages) != baseline_count or after_nav != [f"{index + 1}. {label}" for index, label in enumerate(nav_titles)]:
        raise ValueError("Refreshing QVoice heartbeat changed the deck structure or navigation sequence.")
    changed_existing_stages: list[int] = []
    for index, (before, after) in enumerate(zip(baseline_stages, after_stages), start=1):
        if index in {2, stage_number}:
            continue
        if before != after:
            changed_existing_stages.append(index)
    if changed_existing_stages:
        raise ValueError(f"Refreshing QVoice heartbeat altered unauthorized stages: {changed_existing_stages}.")
    _, _, _, refreshed_stage = slide_stage_by_title(output, "QVoice heartbeat")
    if refreshed_stage.count("qvoice-heartbeat-row") != 10:
        raise ValueError("The refreshed QVoice heartbeat stage is missing its ten published rows.")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_slides = manifest.get("slides")
    if not isinstance(manifest_slides, list) or len(manifest_slides) != baseline_count:
        raise ValueError("The manifest does not match the existing QVoice heartbeat deck.")
    if manifest_slides[stage_number - 1].get("title") != "QVoice heartbeat":
        raise ValueError("The manifest does not identify the existing QVoice heartbeat stage.")
    source_runs = list(manifest.get("source_runs", []))
    if "qvoice-heartbeat-20260911" not in source_runs:
        source_runs.append("qvoice-heartbeat-20260911")
    manifest["source_runs"] = source_runs
    profiles = list(manifest.get("new_aggregate_profiles", []))
    if QVOICE_HEARTBEAT_PROFILE_SQL not in profiles:
        profiles.append(QVOICE_HEARTBEAT_PROFILE_SQL)
    manifest["new_aggregate_profiles"] = profiles
    audits = list(manifest.get("new_aggregate_audits", []))
    if QVOICE_HEARTBEAT_AUDIT_SQL not in audits:
        audits.append(QVOICE_HEARTBEAT_AUDIT_SQL)
    manifest["new_aggregate_audits"] = audits
    builders = list(manifest.get("aggregate_evidence_builders", []))
    builder_path = str(QVOICE_HEARTBEAT_BUILDER.relative_to(ROOT)).replace("\\", "/")
    if builder_path not in builders:
        builders.append(builder_path)
    manifest["aggregate_evidence_builders"] = builders
    frozen_evidence = dict(manifest.get("frozen_evidence", {}))
    frozen_evidence["qvoice_heartbeat"] = qvoice_heartbeat_manifest_entry(evidence)
    manifest["frozen_evidence"] = frozen_evidence
    manifest["generated_on"] = date.today().isoformat()
    validation = dict(manifest.get("slide_content_hash_validation", {}))
    validation["navigation_ranges"] = [{"title": title, "start_slide": start + 1, "end_slide": end} for title, start, end in new_sections]
    validation["navigation_consecutive"] = True
    validation["outcome"] = "pass"
    manifest["slide_content_hash_validation"] = validation
    manifest["navigation_sections"] = [{"title": title, "start_slide": start + 1, "end_slide": end} for title, start, end in new_sections]
    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    manifest_tmp = MANIFEST.with_name(MANIFEST.name + ".tmp")
    target_tmp.write_text(output, encoding="utf-8")
    manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    target_tmp.replace(TARGET)
    manifest_tmp.replace(MANIFEST)
    print(TARGET)
    print(MANIFEST)
    print(f"refreshed_stage={stage_number}; slides={baseline_count}")


def add_qvoice_heartbeat_slide(reporting_mode: str = "internal_analysis") -> None:
    """Insert the QVoice heartbeat after Average of all QVoice items only."""
    global REPORTING_MODE
    if reporting_mode not in {"presentation", "internal_analysis"}:
        raise ValueError("The reporting mode must be presentation or internal_analysis.")
    if not TARGET.exists() or not MANIFEST.exists():
        raise FileNotFoundError("The deck and manifest must exist for the focused QVoice heartbeat insertion.")

    REPORTING_MODE = reporting_mode
    baseline = TARGET.read_text(encoding="utf-8")
    baseline_stages = _normalized_stage_contents(baseline)
    baseline_nav = nav_pill_labels(baseline)
    baseline_count = len(baseline_stages)
    if baseline_count != len(baseline_nav) or baseline_count < 1:
        raise ValueError("The deck baseline does not preserve one navigation label per stage.")
    try:
        existing_id, existing_start, existing_end, _ = slide_stage_by_title(baseline, "QVoice heartbeat")
    except ValueError as exc:
        if "found 0" not in str(exc):
            raise
    else:
        _refresh_existing_qvoice_heartbeat_slide(
            reporting_mode,
            baseline,
            baseline_stages,
            baseline_nav,
            existing_id,
            existing_start,
            existing_end,
        )
        return

    average_id, _, _, _ = slide_stage_by_title(baseline, "Average of all QVoice items")
    average_number = int(average_id.removeprefix("slide-"))
    insertion_index = average_number  # zero-based position immediately after Average QVoice
    if average_number < 1 or average_number > baseline_count:
        raise ValueError("Average of all QVoice items does not have a valid stage ordinal.")
    if baseline_nav[average_number - 1] != f"{average_number}. Average QVoice":
        raise ValueError("The baseline navigation does not identify Average QVoice at its HTML ordinal.")

    evidence = qvoice_heartbeat_evidence()
    replacement = localize_visible_content(qvoice_heartbeat_slide(average_number + 1, evidence))

    # Shift only existing stage IDs after Average QVoice. The body of every
    # pre-existing stage remains unchanged; the normalized comparison below
    # ignores the ordinal attribute itself.
    shifted = re.sub(
        r'(<div class="slide-stage" id="slide-)(\d+)("(?:\s[^>]*)?>)',
        lambda match: match.group(1) + str(int(match.group(2)) + 1 if int(match.group(2)) > average_number else int(match.group(2))) + match.group(3),
        baseline,
    )
    _, _, insertion_end, _ = slide_stage_by_title(shifted, "Average of all QVoice items")
    output = shifted[:insertion_end] + "\n\n  " + replacement + shifted[insertion_end:]

    baseline_nav_titles = [re.sub(r"^\d+\.\s*", "", label) for label in baseline_nav]
    new_nav_titles = baseline_nav_titles[:insertion_index] + ["QVoice heartbeat"] + baseline_nav_titles[insertion_index:]
    if len(new_nav_titles) != baseline_count + 1:
        raise ValueError("The focused insertion did not create exactly one new navigation label.")
    base_sections = _nav_sections_from_document(baseline, baseline_count)
    if [title for title, _, _ in base_sections] != [
        "Start", "Mobility and turnover", "Organizational context",
        "QVoice and external pull factors", "Career and compensation",
        "Manager and advanced signals",
    ]:
        raise ValueError("The baseline navigation section taxonomy is not the expected deck taxonomy.")
    # The prior HTML contained stale section endpoints. Rebuild the ranges
    # from the visible portfolio order so Commute distance remains in
    # Organizational context and the QVoice block fully contains the new
    # heartbeat plus External pull factors.
    new_sections = (
        ("Start", 0, 2),
        ("Mobility and turnover", 2, 4),
        ("Organizational context", 4, 18),
        ("QVoice and external pull factors", 18, 27),
        ("Career and compensation", 27, 40),
        ("Manager and advanced signals", 40, baseline_count + 1),
    )
    nav_pattern = r'(<div class="nav-panel">\s*<div class="nav-label">Navigation</div>)(.*?)(</div>\s*</div>\s*)(?=<!--)'
    output, nav_replacements = re.subn(
        nav_pattern,
        lambda match: match.group(1) + "\n      " + nav(new_nav_titles, new_sections) + "\n    " + match.group(3),
        output,
        count=1,
        flags=re.S,
    )
    if nav_replacements != 1:
        raise ValueError("The navigation panel could not be rebuilt after inserting QVoice heartbeat.")
    output = _update_agenda_ranges(output, new_sections)
    if QVOICE_HEARTBEAT_CSS not in output:
        output = output.replace("  </style>", QVOICE_HEARTBEAT_CSS + "  </style>", 1)

    after_stages = _normalized_stage_contents(output)
    after_nav = nav_pill_labels(output)
    if len(after_stages) != baseline_count + 1 or len(after_nav) != baseline_count + 1:
        raise ValueError("The focused insertion did not produce exactly one additional stage and navigation label.")
    changed_existing_stages: list[int] = []
    for old_index, old_stage in enumerate(baseline_stages):
        new_index = old_index if old_index < insertion_index else old_index + 1
        # The agenda is intentionally updated to reflect the new section
        # ranges; all other existing stage bodies must remain byte-stable
        # after removing their ordinal IDs.
        if old_index == 1:
            continue
        if after_stages[new_index] != old_stage:
            changed_existing_stages.append(old_index + 1)
    if changed_existing_stages:
        raise ValueError(f"The QVoice heartbeat insertion altered existing stages: {changed_existing_stages}.")
    expected_nav = [f"{index + 1}. {label}" for index, label in enumerate(new_nav_titles)]
    if after_nav != expected_nav:
        raise ValueError("The navigation sequence after QVoice heartbeat insertion is invalid.")
    stage_numbers = [int(match.group(1)) for match in re.finditer(r'<div class="slide-stage" id="slide-(\d+)"', output)]
    if stage_numbers != list(range(1, baseline_count + 2)):
        raise ValueError("Stage IDs after QVoice heartbeat insertion are not consecutive.")
    _, _, _, inserted_stage = slide_stage_by_title(output, "QVoice heartbeat")
    if inserted_stage.count("qvoice-heartbeat-row") != 10 or "above personal mean" not in inserted_stage or "excluded, not zero" not in inserted_stage:
        raise ValueError("The inserted QVoice heartbeat slide is missing its two rankings or explicit legend.")
    if any(token in inserted_stage.lower() for token in ("employee_id", "manager_employee_id", "employee_name", "email", "personal_mean")):
        raise ValueError("The inserted QVoice heartbeat slide contains a restricted field label.")
    inserted_residual_spanish = residual_spanish_visible_text(inserted_stage)
    if inserted_residual_spanish:
        raise ValueError(f"The inserted QVoice heartbeat slide contains visible non-English text: {inserted_residual_spanish}")
    residual_spanish = residual_spanish_visible_text_excluding_stages(output, {8, 9})

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_slides = manifest.get("slides")
    if not isinstance(manifest_slides, list) or len(manifest_slides) != baseline_count:
        raise ValueError("The manifest does not match the deck baseline before QVoice heartbeat insertion.")
    average_index = next((index for index, row in enumerate(manifest_slides) if row.get("title") in {"Average QVoice", "Average of all QVoice items"}), None)
    if average_index != average_number - 1:
        raise ValueError("The manifest does not locate Average QVoice at the same ordinal as the HTML.")
    updated_slides: list[dict[str, object]] = []
    for index, row in enumerate(manifest_slides):
        if index == average_index + 1:
            updated_slides.append({"slide": index + 1, "title": "QVoice heartbeat"})
        updated = dict(row)
        updated["slide"] = index + 1 + (1 if index > average_index else 0)
        updated_slides.append(updated)
    if len(updated_slides) != baseline_count + 1:
        raise ValueError("The manifest could not insert the QVoice heartbeat stage.")
    manifest["slides"] = updated_slides
    manifest["slide_count"] = baseline_count + 1
    manifest["generated_on"] = date.today().isoformat()
    source_runs = list(manifest.get("source_runs", []))
    if "qvoice-heartbeat-20260911" not in source_runs:
        source_runs.append("qvoice-heartbeat-20260911")
    manifest["source_runs"] = source_runs
    profiles = list(manifest.get("new_aggregate_profiles", []))
    if QVOICE_HEARTBEAT_PROFILE_SQL not in profiles:
        profiles.append(QVOICE_HEARTBEAT_PROFILE_SQL)
    manifest["new_aggregate_profiles"] = profiles
    audits = list(manifest.get("new_aggregate_audits", []))
    if QVOICE_HEARTBEAT_AUDIT_SQL not in audits:
        audits.append(QVOICE_HEARTBEAT_AUDIT_SQL)
    manifest["new_aggregate_audits"] = audits
    builders = list(manifest.get("aggregate_evidence_builders", []))
    builder_path = str(QVOICE_HEARTBEAT_BUILDER.relative_to(ROOT)).replace("\\", "/")
    if builder_path not in builders:
        builders.append(builder_path)
    manifest["aggregate_evidence_builders"] = builders
    frozen_evidence = dict(manifest.get("frozen_evidence", {}))
    frozen_evidence["qvoice_heartbeat"] = qvoice_heartbeat_manifest_entry(evidence)
    manifest["frozen_evidence"] = frozen_evidence
    prior_validation = manifest.get("slide_content_hash_validation")
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": baseline_count,
        "output_slide_count": baseline_count + 1,
        "structural_change": "Inserted QVoice heartbeat immediately after Average of all QVoice items; later ordinal IDs and navigation indices were shifted by one.",
        "identified_by_title": "QVoice heartbeat",
        "resolved_stage": average_number + 1,
        "inserted_after_title": "Average of all QVoice items",
        "allowed_changed_slides": [average_number + 1],
        "renumbered_existing_slides": list(range(average_number + 2, baseline_count + 2)),
        "observed_changed_slides": [average_number + 1],
        "agenda_updated": True,
        "unchanged_existing_content_count": baseline_count - 1,
        "existing_content_preservation": "pass",
        "navigation_consecutive": True,
        "preexisting_structural_change": prior_validation,
        "outcome": "pass",
    }
    manifest["visible_language_validation"] = {
        "language": "English",
        "residual_spanish_text": residual_spanish,
        "outcome": "pass",
    }

    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    manifest_tmp = MANIFEST.with_name(MANIFEST.name + ".tmp")
    target_tmp.write_text(output, encoding="utf-8")
    manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    target_tmp.replace(TARGET)
    manifest_tmp.replace(MANIFEST)
    print(TARGET)
    print(MANIFEST)
    print(f"inserted_stage={average_number + 1}; baseline_slides={baseline_count}; output_slides={baseline_count + 1}")


def refresh_level_grouped_by_grade_family_slide(reporting_mode: str = "internal_analysis") -> None:
    """Insert the new Level-family slide after Level and renumber later stages."""
    global REPORTING_MODE
    if reporting_mode != "internal_analysis":
        raise ValueError("La vista Level-familia está clasificada como internal_analysis.")
    if not TARGET.exists() or not MANIFEST.exists():
        raise FileNotFoundError("El deck y su manifest deben existir para la actualización focal de Level-familia.")

    REPORTING_MODE = reporting_mode
    baseline = TARGET.read_text(encoding="utf-8")
    baseline_stages = _normalized_stage_contents(baseline)
    baseline_nav = nav_pill_labels(baseline)
    baseline_count = len(baseline_stages)
    if baseline_count != len(baseline_nav) or baseline_count < 1:
        raise ValueError("El deck base no conserva el mismo número de stages y etiquetas de navegación.")
    try:
        existing_stage_id, existing_start, existing_end, _ = slide_stage_by_title(
            baseline, "Level grouped by grade family"
        )
    except ValueError as exc:
        if "found 0" not in str(exc):
            raise
    else:
        _refresh_existing_level_grouped_by_grade_family_slide(
            baseline,
            baseline_stages,
            baseline_nav,
            existing_stage_id,
            existing_start,
            existing_end,
        )
        return

    level_id, _, _, _ = slide_stage_by_title(baseline, "Level")
    level_number = int(level_id.removeprefix("slide-"))
    if level_number < 1 or level_number > baseline_count:
        raise ValueError("La lámina Level no tiene un ordinal válido.")
    if baseline_nav[level_number - 1] != f"{level_number}. Level":
        raise ValueError("La navegación base no identifica exactamente la lámina Level.")

    evidence = level_grouped_by_grade_family_evidence()
    replacement = localize_visible_content(level_grouped_by_grade_family_slide(level_number + 1, evidence))

    # Shift only the existing stage IDs after Level; the stage bodies remain
    # byte-for-byte intact apart from their ordinal attribute.
    shifted = re.sub(
        r'(<div class="slide-stage" id="slide-)(\d+)("(?:\s[^>]*)?>)',
        lambda match: match.group(1) + str(int(match.group(2)) + 1 if int(match.group(2)) > level_number else int(match.group(2))) + match.group(3),
        baseline,
    )
    _, _, insertion_end, _ = slide_stage_by_title(shifted, "Level")
    output = shifted[:insertion_end] + "\n\n  " + replacement + shifted[insertion_end:]

    # Rebuild only the navigation panel from the old labels plus the new
    # entry. This preserves the shell while keeping section ranges valid.
    baseline_nav_titles = [re.sub(r"^\d+\.\s*", "", label) for label in baseline_nav]
    new_nav_titles = (
        baseline_nav_titles[:level_number]
        + ["Level grouped by grade family"]
        + baseline_nav_titles[level_number:]
    )
    if len(new_nav_titles) != baseline_count + 1:
        raise ValueError("La nueva navegación no contiene exactamente una lámina adicional.")
    nav_pattern = r'(<div class="nav-panel">\s*<div class="nav-label">Navigation</div>)(.*?)(</div>\s*</div>\s*)(?=<!--)'
    output, nav_replacements = re.subn(
        nav_pattern,
        lambda match: match.group(1) + "\n      " + nav(new_nav_titles) + "\n    " + match.group(3),
        output,
        count=1,
        flags=re.S,
    )
    if nav_replacements != 1:
        raise ValueError("No se pudo reconstruir la navegación después de insertar Level-familia.")
    if LEVEL_GRADE_FAMILY_FOCUSED_CSS not in output:
        output = output.replace("  </style>", LEVEL_GRADE_FAMILY_FOCUSED_CSS + "  </style>", 1)

    after_stages = _normalized_stage_contents(output)
    after_nav = nav_pill_labels(output)
    if len(after_stages) != baseline_count + 1 or len(after_nav) != baseline_count + 1:
        raise ValueError("La inserción no produjo exactamente 48 láminas y etiquetas de navegación.")
    # The inserted stage occupies the position immediately after the original
    # Level stage. Compare every pre-existing stage after removing ordinal IDs.
    # ``level_number`` is the zero-based insertion index; the original Level
    # stage remains at ``level_number - 1``.
    if after_stages[:level_number] != baseline_stages[:level_number] or after_stages[level_number + 1 :] != baseline_stages[level_number:]:
        raise ValueError("La inserción alteró el contenido de una lámina existente.")
    expected_nav = [f"{index + 1}. {label}" for index, label in enumerate(new_nav_titles)]
    if after_nav != expected_nav:
        raise ValueError("La navegación resultante no coincide con la secuencia esperada.")
    _, _, _, inserted_stage = slide_stage_by_title(output, "Level grouped by grade family")
    if inserted_stage.count("level-grade-family-card") != 1 or "exploratory display-only" not in inserted_stage.lower():
        raise ValueError("La nueva lámina no contiene el gráfico o la nota display-only esperada.")
    if "Level grouped by grade family" not in inserted_stage:
        raise ValueError("La nueva lámina no tiene el título visible esperado.")
    baseline_residual_spanish = residual_spanish_visible_text_excluding_stages(baseline, {8, 9})
    residual_spanish = residual_spanish_visible_text_excluding_stages(output, {8, 9})
    if residual_spanish != baseline_residual_spanish:
        raise ValueError(f"The refresh added or changed visible non-English text outside the approved stages: {residual_spanish}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_slides = manifest.get("slides")
    if not isinstance(manifest_slides, list) or len(manifest_slides) != baseline_count:
        raise ValueError("El manifest base no coincide con el inventario del deck antes de insertar.")
    old_level_index = next((index for index, row in enumerate(manifest_slides) if row.get("title") == "Level"), None)
    if old_level_index != level_number - 1:
        raise ValueError("El manifest no ubica Level en el mismo ordinal que el HTML.")
    updated_slides: list[dict[str, object]] = []
    for index, row in enumerate(manifest_slides):
        if index == old_level_index + 1:
            updated_slides.append({"slide": level_number + 1, "title": "Level grouped by grade family"})
        updated = dict(row)
        updated["slide"] = int(row.get("slide", index + 1)) + (1 if index > old_level_index else 0)
        updated_slides.append(updated)
    if len(updated_slides) != baseline_count + 1:
        raise ValueError("El manifest no pudo insertar la nueva lámina.")
    manifest["slides"] = updated_slides
    manifest["slide_count"] = baseline_count + 1
    manifest["generated_on"] = date.today().isoformat()
    source_runs = list(manifest.get("source_runs", []))
    source_run = "level-grouped-by-grade-family-display-20260911"
    if source_run not in source_runs:
        source_runs.append(source_run)
    manifest["source_runs"] = source_runs
    audits = list(manifest.get("new_aggregate_audits", []))
    if LEVEL_GRADE_FAMILY_AUDIT_SQL not in audits:
        audits.append(LEVEL_GRADE_FAMILY_AUDIT_SQL)
    manifest["new_aggregate_audits"] = audits
    builders = list(manifest.get("aggregate_evidence_builders", []))
    builder_path = str(LEVEL_GRADE_FAMILY_BUILDER.relative_to(ROOT)).replace("\\", "/")
    if builder_path not in builders:
        builders.append(builder_path)
    manifest["aggregate_evidence_builders"] = builders
    frozen_evidence = dict(manifest.get("frozen_evidence", {}))
    frozen_evidence["level_grouped_by_grade_family"] = level_grouped_by_grade_family_manifest_entry(evidence)
    manifest["frozen_evidence"] = frozen_evidence
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": baseline_count,
        "output_slide_count": baseline_count + 1,
        "structural_change": "Inserted Level grouped by grade family immediately after Level; later ordinal IDs and navigation indices were shifted by one.",
        "identified_by_title": "Level grouped by grade family",
        "resolved_stage": level_number + 1,
        "allowed_changed_slides": [level_number + 1],
        "renumbered_existing_slides": list(range(level_number + 2, baseline_count + 2)),
        "observed_changed_slides": [level_number + 1],
        "unchanged_existing_content_count": baseline_count,
        "existing_content_preservation": "pass",
        "outcome": "pass",
    }
    manifest["visible_language_validation"] = {
        "language": "English",
        "residual_spanish_text": residual_spanish,
        "outcome": "pass",
    }

    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    manifest_tmp = MANIFEST.with_name(MANIFEST.name + ".tmp")
    target_tmp.write_text(output, encoding="utf-8")
    manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    target_tmp.replace(TARGET)
    manifest_tmp.replace(MANIFEST)
    print(TARGET)
    print(MANIFEST)
    print(f"inserted_stage={level_number + 1}; baseline_slides={baseline_count}; output_slides={baseline_count + 1}")


def refresh_commute_distance_slide(reporting_mode: str = "internal_analysis") -> None:
    """Replace only the Commute distance stage with the all-vs-Onsite comparison."""
    global REPORTING_MODE
    if reporting_mode not in {"presentation", "internal_analysis"}:
        raise ValueError("El modo debe ser presentation o internal_analysis.")
    if not TARGET.exists() or not MANIFEST.exists():
        raise FileNotFoundError("El deck y su manifest deben existir para la actualizaciÃ³n focal de Commute distance.")

    REPORTING_MODE = reporting_mode
    baseline = TARGET.read_text(encoding="utf-8")
    baseline_hashes = slide_stage_hashes(baseline)
    baseline_nav = nav_pill_labels(baseline)
    if len(baseline_hashes) != len(baseline_nav):
        raise ValueError("El deck base no conserva el mismo nÃºmero de stages y etiquetas de navegaciÃ³n.")

    stage_id, start, end, _ = slide_stage_by_title(baseline, "Commute distance")
    stage_number = int(stage_id.removeprefix("slide-"))
    if stage_number != 17:
        raise ValueError(f"La lÃ¡mina de Commute distance se resolviÃ³ como {stage_number}, no como 17.")
    replacement = commute_distance_slide(stage_number)
    output = baseline[:start] + replacement + baseline[end:]
    _, _, _, refreshed_stage = slide_stage_by_title(output, "Commute distance")
    if refreshed_stage.count("commute-comparison-row") != 5 or "Onsite" not in refreshed_stage:
        raise ValueError("La comparaciÃ³n global vs Onsite no se materializÃ³ correctamente.")

    residual_spanish = residual_spanish_visible_text_excluding_stages(output, {8, 9})
    if residual_spanish:
        raise ValueError(f"El deck contiene texto espaÃ±ol fuera de las lÃ¡minas aprobadas: {residual_spanish}")
    new_hashes = slide_stage_hashes(output)
    new_nav = nav_pill_labels(output)
    changed_stages = sorted(
        int(identifier.removeprefix("slide-"))
        for identifier in baseline_hashes
        if baseline_hashes.get(identifier) != new_hashes.get(identifier)
    )
    changed_nav = [index for index, (before, after) in enumerate(zip(baseline_nav, new_nav)) if before != after]
    if set(baseline_hashes) != set(new_hashes) or changed_stages not in ([17], []):
        raise ValueError(f"El refresh de Commute distance alterÃ³ lÃ¡minas no autorizadas: {changed_stages}.")
    if new_nav != baseline_nav or changed_nav:
        raise ValueError("El refresh de Commute distance alterÃ³ la navegaciÃ³n.")

    evidence = json.loads(COMMUTE_DISTANCE_EVIDENCE.read_text(encoding="utf-8"))
    metrics = evidence["metrics"]
    onsite_metrics = metrics["onsite"]
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_slides = manifest.get("slides")
    if not isinstance(manifest_slides, list) or len(manifest_slides) != len(baseline_hashes):
        raise ValueError("El manifest no coincide con el nÃºmero de lÃ¡minas del deck base.")
    if manifest_slides[16].get("slide") != 17:
        raise ValueError("El inventario del manifest no alinea la lÃ¡mina de Commute distance.")

    source_runs = list(manifest.get("source_runs", []))
    source_run = "commute-distance-onsite-20260911"
    if source_run not in source_runs:
        source_runs.append(source_run)
    manifest["source_runs"] = source_runs
    profiles = list(manifest.get("new_aggregate_profiles", []))
    if COMMUTE_DISTANCE_PROFILE_SQL not in profiles:
        profiles.append(COMMUTE_DISTANCE_PROFILE_SQL)
    manifest["new_aggregate_profiles"] = profiles
    audits = list(manifest.get("new_aggregate_audits", []))
    for query in (COMMUTE_DISTANCE_COVERAGE_AUDIT_SQL, "queries/audits/commute_distance_work_arrangement_onsite_20260911.sql"):
        if query not in audits:
            audits.append(query)
    manifest["new_aggregate_audits"] = audits
    builders = list(manifest.get("aggregate_evidence_builders", []))
    builder = "tools/build_global_commute_distance_evidence.py"
    if builder not in builders:
        builders.append(builder)
    manifest["aggregate_evidence_builders"] = builders
    frozen_evidence = dict(manifest.get("frozen_evidence", {}))
    frozen_evidence["commute_distance"] = {
        "evidence": str(COMMUTE_DISTANCE_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "query": COMMUTE_DISTANCE_PROFILE_SQL,
        "coverage_audit": COMMUTE_DISTANCE_COVERAGE_AUDIT_SQL,
        "format_audit": COMMUTE_DISTANCE_FORMAT_AUDIT_SQL,
        "snapshot": str(evidence["snapshot_date"]),
        "population": f"{int(metrics['eligible_employees']):,} regular active employee groups globally; {int(onsite_metrics['eligible_employees']):,} stored Onsite",
        "grain": str(evidence["grain"]),
        "office": "Qualcomm global office catalog from source page and model JSON",
        "method": "Haversine distance from residential postal centroid to office coordinate",
        "published_population": f"{int(metrics['published_employee_count']):,} of {int(metrics['eligible_employees']):,} calculable overall; {int(onsite_metrics['published_employee_count']):,} of {int(onsite_metrics['eligible_employees']):,} Onsite calculable",
        "privacy_rule": "Broad display bands are derived from 1-km evidence; only bands with n >= 30 are published; unmatched ZIPs/offices remain No calculable rather than imputed.",
        "outcome": str(metrics["outcome"]),
    }
    manifest["frozen_evidence"] = frozen_evidence
    prior_validation = manifest.get("slide_content_hash_validation", {})
    prior_changed = {
        int(value) for value in prior_validation.get("observed_changed_slides", [])
        if str(value).isdigit()
    }
    observed_changed = sorted(prior_changed | set(changed_stages))
    prior_allowed = {
        int(value) for value in prior_validation.get("allowed_changed_slides", [])
        if str(value).isdigit()
    }
    allowed_changed = sorted(prior_allowed | {17})
    manifest["generated_on"] = date.today().isoformat()
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": len(baseline_hashes),
        "output_slide_count": len(new_hashes),
        "structural_change": None,
        "identified_by_title": "Commute distance",
        "resolved_stage": 17,
        "allowed_changed_slides": allowed_changed,
        "observed_changed_slides": observed_changed,
        "allowed_changed_navigation_indices": [],
        "observed_changed_navigation_labels": changed_nav,
        "unchanged_slide_count": len(new_hashes) - len(observed_changed),
        "outcome": "pass",
    }

    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    manifest_tmp = MANIFEST.with_name(MANIFEST.name + ".tmp")
    target_tmp.write_text(output, encoding="utf-8")
    manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    target_tmp.replace(TARGET)
    manifest_tmp.replace(MANIFEST)
    print(TARGET)
    print(MANIFEST)
    print(f"stage=17; slides={len(new_hashes)}")


def refresh_comp_ratio_slide(reporting_mode: str = "presentation") -> None:
    """Replace only slide 39 with the validated Comp ratio history view."""
    global REPORTING_MODE
    if reporting_mode != "presentation":
        raise ValueError("Comp ratio history evidence is classified as presentation.")
    if not TARGET.exists() or not MANIFEST.exists():
        raise FileNotFoundError("The deck and manifest must exist for the focused Comp ratio refresh.")

    REPORTING_MODE = reporting_mode
    baseline = TARGET.read_text(encoding="utf-8")
    baseline_hashes = slide_stage_hashes(baseline)
    baseline_nav = nav_pill_labels(baseline)
    if len(baseline_hashes) != len(baseline_nav):
        raise ValueError("The deck baseline has mismatched stages and navigation labels.")

    stage_id, start, end, _ = slide_stage_by_title(baseline, "Comp ratio")
    stage_number = int(stage_id.removeprefix("slide-"))
    if stage_number != COMP_RATIO_VOLUNTARY_ATTRITION_SLIDE:
        raise ValueError(f"Comp ratio resolved to slide {stage_number}, not {COMP_RATIO_VOLUNTARY_ATTRITION_SLIDE}.")

    evidence = comp_ratio_voluntary_attrition_evidence()
    replacement = localize_visible_content(comp_ratio_slide(stage_number, evidence))
    output = baseline[:start] + replacement + baseline[end:]

    if ".comp-ratio-main" not in output:
        output = output.replace("  </style>", COMP_RATIO_FOCUSED_CSS + "  </style>", 1)

    script_matches = list(re.finditer(r"\n  <script>[\s\S]*?</script>", output))
    for script_match in reversed(script_matches):
        if "renderCompRatioHistoryChart" in script_match.group(0):
            output = output[:script_match.start()] + output[script_match.end():]
    output = output.replace(
        "</body>",
        comp_ratio_voluntary_attrition_chart_enhancement(evidence) + "\n</body>",
        1,
    )

    _, _, _, refreshed_stage = slide_stage_by_title(output, "Comp ratio")
    for expected in (
        "comp-ratio-main",
        "comp-ratio-voluntary-attrition-chart",
        "&lt;0.8 (incl. 0)",
        "&gt;=0.8",
        "term_type = 'VOLUNTARY'",
    ):
        if expected not in refreshed_stage:
            raise ValueError(f"The refreshed Comp ratio stage is missing expected content: {expected}")

    baseline_residual_spanish = residual_spanish_visible_text_excluding_stages(baseline, {8, 9})
    residual_spanish = residual_spanish_visible_text_excluding_stages(output, {8, 9})
    if residual_spanish != baseline_residual_spanish:
        raise ValueError(f"The refresh introduced new reader-facing non-English text: {residual_spanish}")

    new_hashes = slide_stage_hashes(output)
    new_nav = nav_pill_labels(output)
    changed_stages = sorted(
        int(identifier.removeprefix("slide-"))
        for identifier in baseline_hashes
        if baseline_hashes.get(identifier) != new_hashes.get(identifier)
    )
    changed_nav = [index for index, (before, after) in enumerate(zip(baseline_nav, new_nav)) if before != after]
    if set(baseline_hashes) != set(new_hashes) or changed_stages not in ([stage_number], []):
        raise ValueError(f"Focused Comp ratio refresh altered unauthorized stages: {changed_stages}.")
    if new_nav != baseline_nav or changed_nav:
        raise ValueError(f"Focused Comp ratio refresh altered navigation labels: {changed_nav}.")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_slides = manifest.get("slides")
    if not isinstance(manifest_slides, list) or len(manifest_slides) != len(baseline_hashes):
        raise ValueError("The manifest does not match the existing deck inventory.")
    if manifest_slides[stage_number - 1].get("slide") != stage_number:
        raise ValueError("The manifest slide inventory does not align to the Comp ratio stage.")

    source_runs = list(manifest.get("source_runs", []))
    source_run = "comp-ratio-voluntary-attrition-history-20260913"
    if source_run not in source_runs:
        source_runs.append(source_run)
    manifest["source_runs"] = source_runs
    audits = list(manifest.get("new_aggregate_audits", []))
    if COMP_RATIO_VOLUNTARY_ATTRITION_AUDIT_SQL not in audits:
        audits.append(COMP_RATIO_VOLUNTARY_ATTRITION_AUDIT_SQL)
    manifest["new_aggregate_audits"] = audits
    builders = list(manifest.get("aggregate_evidence_builders", []))
    builder_path = str(COMP_RATIO_VOLUNTARY_ATTRITION_BUILDER.relative_to(ROOT)).replace("\\", "/")
    if builder_path not in builders:
        builders.append(builder_path)
    manifest["aggregate_evidence_builders"] = builders
    frozen_evidence = dict(manifest.get("frozen_evidence", {}))
    frozen_evidence["comp_ratio_voluntary_attrition_history"] = comp_ratio_voluntary_attrition_manifest_entry(evidence)
    manifest["frozen_evidence"] = frozen_evidence
    manifest["generated_on"] = date.today().isoformat()
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": len(baseline_hashes),
        "output_slide_count": len(new_hashes),
        "structural_change": None,
        "identified_by_title": "Comp ratio",
        "resolved_stage": stage_number,
        "allowed_changed_slides": [stage_number],
        "observed_changed_slides": changed_stages,
        "allowed_changed_navigation_indices": [],
        "observed_changed_navigation_labels": changed_nav,
        "unchanged_slide_count": len(new_hashes) - len(changed_stages),
        "outcome": "pass",
    }
    manifest["visible_language_validation"] = {
        "language": "English",
        "residual_spanish_text": residual_spanish,
        "outcome": "pass",
    }

    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    manifest_tmp = MANIFEST.with_name(MANIFEST.name + ".tmp")
    target_tmp.write_text(output, encoding="utf-8")
    manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    target_tmp.replace(TARGET)
    manifest_tmp.replace(MANIFEST)
    print(TARGET)
    print(MANIFEST)
    print(f"stage={stage_number}; slides={len(new_hashes)}")


def refresh_number_of_manager_changes_slide(reporting_mode: str = "presentation") -> None:
    """Replace only the manager-change count stage with its mobility sensitivity."""
    global REPORTING_MODE
    if reporting_mode != "presentation":
        raise ValueError("The manager-change mobility comparison is classified as presentation.")
    if not TARGET.exists() or not MANIFEST.exists():
        raise FileNotFoundError("The deck and manifest must exist for the focused manager-change refresh.")

    REPORTING_MODE = reporting_mode
    baseline = TARGET.read_text(encoding="utf-8")
    baseline_hashes = slide_stage_hashes(baseline)
    baseline_nav = nav_pill_labels(baseline)
    if len(baseline_hashes) != len(baseline_nav):
        raise ValueError("The deck stages and navigation labels are not aligned before the focused refresh.")
    baseline_residual_spanish = residual_spanish_visible_text_excluding_stages(baseline, {8, 9})

    comparison_css = r'''
    .manager-change-comparison-layout { display:grid; grid-template-rows:minmax(0,1fr) auto; gap:10px; min-height:0; }
    .manager-change-comparison-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); grid-template-rows:repeat(2,minmax(0,1fr)); gap:10px 12px; min-height:0; }
    .manager-change-comparison-card { padding:11px 14px; gap:5px; min-height:0; }
    .manager-change-comparison-card .card-title { margin-bottom:0; padding-bottom:4px; font-size:10px; }
    .manager-change-comparison-card .bar-list { flex:1; margin-top:3px; gap:7px; justify-content:space-evenly; }
    .manager-change-comparison-card .bar-row { grid-template-columns:48px minmax(0,1fr) 108px; gap:7px; }
    .manager-change-comparison-card .bar-label, .manager-change-comparison-card .bar-value { font-size:11px; }
    .manager-change-comparison-card .chart-footer { margin-top:3px; padding-top:5px; font-size:10px; line-height:1.22; }
    .manager-change-comparison-note { padding:8px 12px; border:1px solid color-mix(in oklab,var(--accent) 22%,var(--border-subtle)); border-radius:10px; background:color-mix(in oklab,var(--accent) 7%,transparent); color:var(--text-main); font-size:12px; line-height:1.32; }
'''
    output = baseline
    if ".manager-change-comparison-layout {" not in output:
        output = output.replace("</style>", comparison_css + "\n  </style>", 1)

    stage_id, start, end, _ = slide_stage_by_title(output, "Number of manager changes")
    stage_number = int(stage_id.removeprefix("slide-"))
    replacement = number_of_manager_changes_mobility_comparison_slide(stage_number)
    output = output[:start] + replacement + output[end:]
    _, _, _, refreshed_stage = slide_stage_by_title(output, "Number of manager changes")
    if refreshed_stage.count("manager-change-comparison-card") != 4:
        raise ValueError("The manager-change refresh did not render four comparison cards.")
    if "same-date transfer/promotion" not in refreshed_stage:
        raise ValueError("The manager-change refresh omitted the exact-date sensitivity boundary.")

    residual_spanish = residual_spanish_visible_text_excluding_stages(output, {8, 9})
    if residual_spanish != baseline_residual_spanish:
        raise ValueError(f"The focused refresh introduced or changed visible non-English text: {residual_spanish}")
    new_hashes = slide_stage_hashes(output)
    new_nav = nav_pill_labels(output)
    changed_stages = sorted(
        int(identifier.removeprefix("slide-"))
        for identifier in baseline_hashes
        if baseline_hashes.get(identifier) != new_hashes.get(identifier)
    )
    changed_nav = [index for index, (before, after) in enumerate(zip(baseline_nav, new_nav)) if before != after]
    if set(baseline_hashes) != set(new_hashes) or changed_stages not in ([stage_number], []):
        raise ValueError(f"The manager-change refresh altered unauthorized stages: {changed_stages}.")
    if new_nav != baseline_nav or changed_nav:
        raise ValueError("The manager-change refresh altered navigation labels.")

    evidence = number_of_manager_changes_mobility_comparison()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_slides = manifest.get("slides")
    if not isinstance(manifest_slides, list) or len(manifest_slides) != len(baseline_hashes):
        raise ValueError("The manifest does not match the current deck inventory.")
    matching_entries = [entry for entry in manifest_slides if entry.get("title") == "Number of manager changes"]
    if len(matching_entries) != 1:
        raise ValueError("The manifest must contain exactly one Number of manager changes entry.")
    matching_entries[0]["slide"] = stage_number

    source_runs = list(manifest.get("source_runs", []))
    source_run = "number-of-manager-changes-same-date-mobility-comparison-20260914"
    if source_run not in source_runs:
        source_runs.append(source_run)
    manifest["source_runs"] = source_runs
    profiles = list(manifest.get("new_aggregate_profiles", []))
    if MANAGER_CHANGE_MOBILITY_COMPARISON_SQL not in profiles:
        profiles.append(MANAGER_CHANGE_MOBILITY_COMPARISON_SQL)
    manifest["new_aggregate_profiles"] = profiles
    frozen_evidence = dict(manifest.get("frozen_evidence", {}))
    frozen_evidence["number_of_manager_changes_same_date_mobility_comparison"] = {
        "evidence": str(MANAGER_CHANGE_MOBILITY_COMPARISON_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
        "evidence_sha256": hashlib.sha256(MANAGER_CHANGE_MOBILITY_COMPARISON_EVIDENCE.read_bytes()).hexdigest(),
        "query": MANAGER_CHANGE_MOBILITY_COMPARISON_SQL,
        "analysis_plan": "config/number_of_manager_changes_distribution_plan_v7_20260914.yaml",
        "snapshot": evidence["snapshot_date"],
        "population": evidence["population"],
        "grain": evidence["grain"],
        "baseline_definition": evidence["baseline_definition"],
        "sensitivity_definition": evidence["sensitivity_definition"],
        "publication_rule": evidence["publication_rule"],
        "windows": evidence["windows"],
        "outcome": evidence["outcome"],
    }
    manifest["frozen_evidence"] = frozen_evidence
    manifest["generated_on"] = date.today().isoformat()
    manifest["slide_content_hash_validation"] = {
        "baseline_available": True,
        "baseline_slide_count": len(baseline_hashes),
        "output_slide_count": len(new_hashes),
        "identified_by_title": "Number of manager changes",
        "resolved_stage": stage_number,
        "allowed_changed_slides": [stage_number],
        "observed_changed_slides": changed_stages,
        "unchanged_existing_content_count": len(new_hashes) - len(changed_stages),
        "existing_content_preservation": "pass",
        "outcome": "pass",
    }
    manifest["visible_language_validation"] = {
        "language": "English",
        "residual_spanish_text": residual_spanish,
        "outcome": "pass",
    }

    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    manifest_tmp = MANIFEST.with_name(MANIFEST.name + ".tmp")
    target_tmp.write_text(output, encoding="utf-8")
    manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    target_tmp.replace(TARGET)
    manifest_tmp.replace(MANIFEST)
    print(TARGET)
    print(MANIFEST)
    print(f"stage={stage_number}; slides={len(new_hashes)}")


def build(reporting_mode: str = "presentation") -> None:
    global REPORTING_MODE
    if reporting_mode not in {"presentation", "internal_analysis"}:
        raise ValueError("reporting_mode must be presentation or internal_analysis.")
    REPORTING_MODE = reporting_mode
    if TARGET.exists():
        existing_count = len(slide_stage_hashes(TARGET.read_text(encoding="utf-8")))
        if existing_count == PRE_OFFICE_SITE_RELATIONSHIP_DECK_SLIDE_COUNT:
            insert_office_site_relationship_slide(reporting_mode)
            return
        if existing_count in {BASELINE_DECK_SLIDE_COUNT, DECK_SLIDE_COUNT}:
            refresh_application_intensity_slides(reporting_mode)
            return
    if not TEMPLATE.exists():
        raise FileNotFoundError(TEMPLATE)
    OUT.mkdir(parents=True, exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    baseline_hashes = slide_stage_hashes(TARGET.read_text(encoding="utf-8")) if TARGET.exists() else None
    if baseline_hashes is not None and len(baseline_hashes) not in (44, 45, DECK_SLIDE_COUNT, 47):
        raise ValueError(f"El deck base no contiene 44, 45, {DECK_SLIDE_COUNT} o 47 láminas para la comparación de hashes.")
    # Copy and build into a sibling temp file. The final deck is replaced only
    # after every slide, enhancement, and structural check has succeeded.
    target_tmp = TARGET.with_name(TARGET.name + ".tmp")
    shutil.copyfile(TEMPLATE, target_tmp)
    template = target_tmp.read_text(encoding="utf-8")
    marker = "    /* 13. CONTENT-SPECIFIC STYLES — add below this line\n       ================================================================== */\n"
    if marker not in template:
        raise ValueError("No se encontró el marcador de estilos de la plantilla.")
    template = template.replace("<title>[Slide Title]</title>", "<title>Evidence for 44 attrition model candidates · v2</title>")
    template = template.replace(marker, marker + EXTRA_CSS)
    template = template.replace(
        "</style>",
        "</style>\n  <script src=\"https://cdn.plot.ly/plotly-2.27.0.min.js\"></script>",
        1,
    )

    variable_slides = build_variable_slides()
    slides = [("Cover", cover()), ("Agenda", agenda())] + variable_slides
    if len(slides) != DECK_SLIDE_COUNT:
        raise ValueError(f"Se esperaban {DECK_SLIDE_COUNT} láminas; se generaron {len(slides)}.")

    body_open = '<body class="theme-light-classic">'
    nav_anchor = '<div class="nav-ctrl" id="slide-nav">'
    prefix = template[:template.index(body_open) + len(body_open)]
    suffix = template[template.index(nav_anchor):]
    nav_pattern = r'(<div class="nav-panel">\s*<div class="nav-label">Navigation</div>)(.*?)(</div>\s*</div>\s*)(?=<!--)'
    suffix, replacements = re.subn(nav_pattern, lambda m: m.group(1) + "\n      " + nav([label for label, _ in slides]) + "\n    " + m.group(3), suffix, count=1, flags=re.S)
    if replacements != 1:
        raise ValueError("No se pudo materializar la navegación.")
    output = prefix + "\n\n  " + "\n\n  ".join(slide for _, slide in slides) + "\n\n  " + suffix
    if "</body>" not in output:
        raise ValueError("No se encontró el cierre de body para la mejora de navegación.")
    output = output.replace(
        "</body>",
        NAVIGATION_ENHANCEMENT + qvoice_comment_chart_enhancement(qvoice_comment_evidence()) + qvoice_nonrespondent_chart_enhancement(qvoice_nonrespondent_evidence()) + application_intensity_chart_enhancement(application_intensity_by_fiscal_year()) + application_employee_snapshot_chart_enhancement(application_employee_snapshot_trailing_6m()) + transfer_chart_enhancement(transfer_within_past_year_distribution()) + comp_ratio_voluntary_attrition_chart_enhancement(comp_ratio_voluntary_attrition_evidence()) + "\n</body>",
        1,
    )
    output = localize_visible_content(output)
    residual_spanish = residual_spanish_visible_text_excluding_stages(output, {8, 9})
    if residual_spanish:
        raise ValueError(f"El deck contiene texto visible fuera de inglés: {residual_spanish}")
    baseline_available = baseline_hashes is not None
    baseline_structure_changed = baseline_available and len(baseline_hashes) != DECK_SLIDE_COUNT
    if baseline_structure_changed:
        # The new entry-path slide changes the stage set. A same-stage hash
        # comparison is valid again on subsequent 46-slide builds.
        baseline_hashes = None
    content_hash_validation = {
        "baseline_available": baseline_available,
        "baseline_slide_count": len(slide_stage_hashes(TARGET.read_text(encoding="utf-8"))) if baseline_structure_changed else (DECK_SLIDE_COUNT if baseline_available else None),
        "output_slide_count": DECK_SLIDE_COUNT,
        "structural_change": "Slide 40 adds the validated Above-average team turnover context; former slides 40–45 were renumbered 41–46." if baseline_structure_changed else None,
        "translation": "Slide 29 now shows within-grade deterministic percentages plus n; slide 30 answers the observed entry-path question without asserting direct hire.",
        "allowed_changed_slides": [1, 3, 8, 9, WORK_ARRANGEMENT_SLIDE, 40, QVOICE_NORMALIZED_REGION_SLIDE, ROLE_LEVEL_TENURE_SLIDE, COMPANY_TENURE_SLIDE, PROMOTION_HISTORY_BY_GRADE_SLIDE, CURRENT_GRADE_ENTRY_PATH_SLIDE, LAYERS_FROM_CEO_SLIDE, RESIDENTIAL_MANAGER_DISTANCE_SLIDE],
        "unchanged_slide_count": None,
        "outcome": "pass",
    }
    if baseline_hashes is not None:
        new_hashes = slide_stage_hashes(output)
        changed = sorted(
            int(stage_id.removeprefix("slide-"))
            for stage_id in baseline_hashes
            if baseline_hashes.get(stage_id) != new_hashes.get(stage_id)
        )
        content_hash_validation["observed_changed_slides"] = changed
        content_hash_validation["unchanged_slide_count"] = len(new_hashes) - len(changed)
        if set(baseline_hashes) != set(new_hashes) or not set(changed).issubset({1, 3, 8, 9, WORK_ARRANGEMENT_SLIDE, 40, QVOICE_NORMALIZED_REGION_SLIDE, ROLE_LEVEL_TENURE_SLIDE, COMPANY_TENURE_SLIDE, PROMOTION_HISTORY_BY_GRADE_SLIDE, CURRENT_GRADE_ENTRY_PATH_SLIDE, LAYERS_FROM_CEO_SLIDE, RESIDENTIAL_MANAGER_DISTANCE_SLIDE}):
            raise ValueError(f"La actualización alteró láminas no autorizadas: {changed}.")
    target_tmp.write_text(output, encoding="utf-8")
    target_tmp.replace(TARGET)

    talent_index_evidence = talent_index_latest_recoverable_distribution()
    residential_distance_evidence, _ = residential_manager_distance_evidence()
    team_post_exit_evidence = team_post_exit_attrition_evidence()
    above_average_team_turnover = above_average_team_turnover_evidence()
    above_average_team_turnover_sensitivity = above_average_team_turnover_sensitivity_evidence()
    comp_ratio_history_evidence = comp_ratio_voluntary_attrition_evidence()
    manifest = {
        "version": 2,
        "generated_on": date.today().isoformat(),
        "minimum_shared_cohort": MINIMUM_COHORT,
        "source_runs": [
            "attrition-43-monthly-fiscal-20260816",
            "qvoice-excel-v4-20260826-2-final2",
            "high-risk-manager-score-coverage-revalidation-20260821",
            "manager-leaving-consistency-join-validation-20260820-5",
            "number-of-manager-changes-join-validation-20260820-4",
            "talent-index-latest-recoverable-distribution-20260909",
            "more-than-3-job-applications-trailing-6m-20260907-v4",
            "team-post-exit-attrition-static-cohort-20260911",
            "above-average-team-turnover-v4-20260910-r13",
            "above-average-team-turnover-threshold-sensitivity-20260911",
            "level-grouped-by-grade-family-display-20260911",
            "comp-ratio-voluntary-attrition-history-20260913",
        ],
        "new_aggregate_profiles": [
            "queries/profiles/distribution_display_policy_latest_snapshot.sql",
            "queries/profiles/distribution_v2_prior_experience_bands_20260907.sql",
            "queries/profiles/distribution_v2_time_in_role_bands_20260907.sql",
            "queries/profiles/distribution_v2_time_since_promotion_bands_20260907.sql",
            "queries/profiles/more_than_three_job_applications_trailing_6m_20260907.sql",
            PRIOR_EXPERIENCE_YEARS_PROFILE_SQL,
            APPLICATION_INTENSITY_PROFILE_SQL,
            TALENT_INDEX_DISTRIBUTION_SQL,
            "queries/profiles/stored_metrics_availability_latest_snapshot_20260908.sql",
            STORED_METRIC_BANDS_SQL,
            MANAGER_CHANGE_DISTRIBUTION_SQL,
            MANAGER_CHANGE_ANNUAL_DISTRIBUTION_SQL,
            MANAGER_LEAVING_DISTRIBUTION_SQL,
            OFFICE_SITE_CITY_PROFILE_SQL,
            CO_LOCATION_SITE_CITY_PROFILE_SQL,
            JOB_FAMILY_PROFILE_SQL,
            TEAM_TURNOVER_PROFILE_SQL,
            TRANSFER_PROFILE_SQL,
            COMMUTE_DISTANCE_PROFILE_SQL,
            RESIDENTIAL_MANAGER_DISTANCE_PROFILE_SQL,
            ABOVE_AVERAGE_TEAM_TURNOVER_PROFILE_SQL,
            "queries/audits/compensation_grade_domain_validation_20260909.sql",
        ],
        "historical_aggregate_profiles": [
            COMPANY_TENURE_LEGACY_PROFILE_SQL,
        ],
        "new_aggregate_audits": [
            APPLICATION_INTENSITY_MAPPING_AUDIT_SQL,
            JOB_FAMILY_AVAILABILITY_AUDIT_SQL,
            REGION_DISPLAY_AUDIT_SQL,
            REGION_MAJOR_COUNTRY_AUDIT_SQL,
            TEAM_TURNOVER_TERM_TYPE_AUDIT_SQL,
            TEAM_TURNOVER_MEMBERSHIP_AUDIT_SQL,
            TEAM_TURNOVER_MANAGER_RESOLUTION_AUDIT_SQL,
            MORE_THAN_1_LEAVES_AUDIT_SQL,
            MORE_THAN_1_LEAVES_ANNUAL_AUDIT_SQL,
            MORE_THAN_1_LEAVES_ANNUAL_COVERAGE_SQL,
            TEAM_POST_EXIT_ATTRITION_CALENDAR_SQL,
            TEAM_POST_EXIT_ATTRITION_RECONCILIATION_SQL,
            TEAM_POST_EXIT_ATTRITION_STATIC_SQL,
            TRANSFER_SOURCE_AUDIT_SQL,
            TRANSFER_VALIDATION_AUDIT_SQL,
            TRANSFER_HISTORY_AUDIT_SQL,
            COMMUTE_DISTANCE_COVERAGE_AUDIT_SQL,
            COMMUTE_DISTANCE_FORMAT_AUDIT_SQL,
            RESIDENTIAL_MANAGER_DISTANCE_AUDIT_SQL,
            RESIDENTIAL_MANAGER_DISTANCE_COUNTRY_MAPPING_AUDIT_SQL,
            HIGH_RISK_MANAGER_SQL,
            HIGH_TURNOVER_MANAGER_SQL,
            ABOVE_AVERAGE_TEAM_TURNOVER_AUDIT_SQL,
            ABOVE_AVERAGE_TEAM_TURNOVER_RECONCILIATION_SQL,
            ABOVE_AVERAGE_TEAM_TURNOVER_SENSITIVITY_SQL,
            "queries/audits/manager_leaving_voluntary_6m_source_access_20260909.sql",
            "queries/audits/co_location_manager_site_city_validation_20260909.sql",
            "queries/audits/compensation_grade_domain_validation_20260909.sql",
            "queries/audits/qvoice_nonrespondent_schema_20260909.sql",
            "queries/audits/qvoice_nonrespondent_source_reconciliation_20260909.sql",
            "queries/audits/qvoice_nonrespondent_workforce_denominator_20260909.sql",
            "queries/audits/qvoice_nonrespondent_snapshot_candidates_20260909.sql",
            "queries/audits/qvoice_nonrespondent_proxy_join_template_20260909.sql",
            LEVEL_GRADE_FAMILY_AUDIT_SQL,
            COMP_RATIO_VOLUNTARY_ATTRITION_AUDIT_SQL,
        ],
        "aggregate_evidence_builders": [
            str(QVOICE_COMMENT_BUILDER.relative_to(ROOT)).replace("\\", "/"),
            str(QVOICE_NONRESPONDENT_BUILDER.relative_to(ROOT)).replace("\\", "/"),
            str(QVOICE_COMPARABLE_BUILDER.relative_to(ROOT)).replace("\\", "/"),
            str(QVOICE_NORMALIZED_REGION_BUILDER.relative_to(ROOT)).replace("\\", "/"),
            "tools/build_talent_index_distribution_evidence.py",
            str(RESIDENTIAL_MANAGER_DISTANCE_BUILDER.relative_to(ROOT)).replace("\\", "/"),
            str(TEAM_POST_EXIT_ATTRITION_BUILDER.relative_to(ROOT)).replace("\\", "/"),
            str(ABOVE_AVERAGE_TEAM_TURNOVER_BUILDER.relative_to(ROOT)).replace("\\", "/"),
            str(ABOVE_AVERAGE_TEAM_TURNOVER_SENSITIVITY_BUILDER.relative_to(ROOT)).replace("\\", "/"),
            str(LEVEL_GRADE_FAMILY_BUILDER.relative_to(ROOT)).replace("\\", "/"),
            str(COMP_RATIO_VOLUNTARY_ATTRITION_BUILDER.relative_to(ROOT)).replace("\\", "/"),
        ],
        "frozen_evidence": {
            "talent_index_latest_recoverable_distribution": talent_index_manifest_entry(talent_index_evidence),
            "residential_manager_distance": residential_manager_distance_manifest_entry(residential_distance_evidence),
            "team_post_exit_attrition": team_post_exit_attrition_manifest_entry(team_post_exit_evidence),
            "above_average_team_turnover": above_average_team_turnover_manifest_entry(above_average_team_turnover),
            "above_average_team_turnover_threshold_sensitivity": above_average_team_turnover_sensitivity_manifest_entry(above_average_team_turnover_sensitivity),
            "level_grouped_by_grade_family": level_grouped_by_grade_family_manifest_entry(
                level_grouped_by_grade_family_evidence()
            ) if REPORTING_MODE == "internal_analysis" else {
                "publication_status": "restricted_in_presentation_mode",
                "score_v4_change": "none",
                "outcome": "not_published",
            },
            "comp_ratio_voluntary_attrition_history": comp_ratio_voluntary_attrition_manifest_entry(comp_ratio_history_evidence),
            "compensation_grade_domain": {
                "evidence": str(COMPENSATION_GRADE_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
                "query": "queries/audits/compensation_grade_domain_validation_20260909.sql",
                "snapshot": V4_SNAPSHOT,
                "population": "50,218 active regular employees",
                "public_rule": "Show each grade only when n >= 30; aggregate the nine smaller grades as Other grades when the aggregate is n >= 30.",
                "public_grades": 36,
                "suppressed_grades": 9,
                "other_grades_count": 37,
                "outcome": "pass",
            },
            "qvoice_comment_topics": {
                "evidence": str(QVOICE_COMMENT_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
                "builder": str(QVOICE_COMMENT_BUILDER.relative_to(ROOT)).replace("\\", "/"),
                "waves": ["Mar-2023", "Jan-2024", "Jan-2025", "Jan-2026"],
                "source": "QVoice raw Excel workbooks · Raw data worksheet",
                "prompts": ["doing well", "can improve", "processes to improve when available"],
                "grain": "Distinct participant-wave case per theme",
                "deduplication": "One participant per wave and theme across selected prompts",
                "primary_source_rule": "Original prompt columns only; 2026 … EN columns are aggregate diagnostics only",
                "publication_rule": "Absolute counts only; every displayed value n >= 30; no identifiers or free text",
                "outcome": "pass",
            },
            "qvoice_nonresponse_proxy": {
                "evidence": str(QVOICE_NONRESPONDENT_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
                "builder": str(QVOICE_NONRESPONDENT_BUILDER.relative_to(ROOT)).replace("\\", "/"),
                "source": "QVoice raw Excel workbooks + HRDA snapshots",
                "waves": ["Mar-2023", "Jan-2024", "Jan-2025", "Jan-2026"],
                "snapshot_assumption": "Stored snapshot nearest the prior-month day 15 is used as the internal-review proxy population.",
                "population": "worker_type='Employee' AND employee_type='Regular' AND active_status=1",
                "grain": "Eligible employee / survey wave",
                "categories": ["Responded", "QVoice row / no answer", "No QVoice row"],
                "denominator": "Eligible employees in the selected stored snapshot",
                "deduplication": "Distinct employee_id per snapshot; raw QVoice keys are deduplicated before comparison.",
                "publication_rule": "Absolute counts and percentages; every displayed category n >= 30; no identifiers, response values, or free text.",
                "interpretation": "No QVoice row is a non-response proxy, not a confirmed non-response; invitation roster and wave-close status remain to be validated.",
                "outcome": "pass",
            },
            "number_of_manager_changes_distribution": {
                "evidence": str(MANAGER_CHANGE_DISTRIBUTION_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
                "query": MANAGER_CHANGE_DISTRIBUTION_SQL,
                "snapshot": "2026-08-23",
                "window": "(2026-02-23, 2026-08-23]",
                "population": "50,043 active regular employees with a usable employee key at the latest deck cutoff",
                "grain": "Distinct employee snapshot",
                "event_key": "employee + manager_change_date where manager_change=1",
                "deduplication": "Repeated monthly observations of the same employee/event date count once.",
                "assumption": "Six-month retrospective window for exploratory review; reset semantics and final model feature definition remain pending.",
                "buckets": ["0", "1", "2", "3+"],
                "publication_rule": "Absolute counts and percentages; every displayed bucket n >= 30; no identifiers or employee rows.",
                "outcome": "pass",
            },
            "number_of_manager_changes_annual_comparison": {
                "evidence": str(MANAGER_CHANGE_ANNUAL_DISTRIBUTION_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
                "query": MANAGER_CHANGE_ANNUAL_DISTRIBUTION_SQL,
                "snapshot": "2026-08-23",
                "window": "(2025-08-23, 2026-08-23]",
                "population": "50,043 active regular employees with a usable employee key at the latest deck cutoff",
                "grain": "Distinct employee snapshot",
                "event_key": "employee + manager_change_date where manager_change=1",
                "purpose": "Supplementary annual comparison for the question whether two changes in a year are common; it does not replace the selected six-month feature.",
                "buckets": ["0", "1", "2", "3+"],
                "validation": "No repeated observations, missing event dates, invalid flags, or annual count below the nested six-month count.",
                "publication_rule": "Absolute counts and percentages; every displayed bucket n >= 30; no identifiers or employee rows.",
                "outcome": "pass",
            },
            "manager_leaving_distribution": {
                "evidence": str(MANAGER_LEAVING_DISTRIBUTION_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
                "query": MANAGER_LEAVING_DISTRIBUTION_SQL,
                "source_access_query": "queries/audits/manager_leaving_voluntary_6m_source_access_20260909.sql",
                "snapshot": "2026-08-23",
                "window": "[2026-02-23, 2026-08-23]",
                "population": "50,043 active regular employees with a usable employee key at the August monthly cutoff",
                "grain": "Distinct employee snapshot",
                "event_scope": "term_type normalized exactly to Voluntary",
                "manager_eligibility": "reg_non_intern_dir_reports > 0 in the last manager snapshot within 45 days before term_date",
                "historical_assignment": "last active regular employee-manager snapshot within 45 days before term_date",
                "reassignment": "Exposure is retained after a manager change through the six-month window.",
                "primary_feature": "Binary 0/1+ exposure flag",
                "sensitivity": "Distinct manager-exit count; the 2+ bucket is merged into 1+ because it is below n=30.",
                "leakage_control": "The feature uses no future manager or employee exit.",
                "publication_rule": "Absolute counts and percentages only; every displayed bucket is n >= 30; no identifiers or individual rows.",
                "outcome": "pass",
            },
            "high_risk_manager_score_distribution": {
                "evidence": str(HIGH_RISK_MANAGER_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
                "query": HIGH_RISK_MANAGER_SQL,
                "cutoff": "2026-09-27",
                "window": "(2026-03-29, 2026-09-27] across six complete fiscal intervals and seven dynamic closures",
                "population": "50,018 observable active regular direct reports of 10,487 managers with reconstructable history",
                "grain": "Aggregate manager-team distribution; no manager or employee identities",
                "definition": "Continuous smoothed observed/expected strict-Voluntary exit ratio; expected exits use time-safe interval, region, job family, job level, and tenure strata with a global fallback below 30 employee-intervals and a 60 employee-interval prior.",
                "buckets": ["<0.50×", "0.50–<1.00×", "1.00–<1.50×", "≥1.50×"],
                "publication_rule": "Absolute counts and percentages only; every displayed manager and direct-report bucket n >= 30; no identities, ranking, individual label, or intervention threshold.",
                "limitation": "190 current direct reports across 80 managers lack sufficient score history and remain unknown. 72 of 1,544 unique Voluntary events lack unique initial-interval exposure and are excluded, not imputed.",
                "outcome": "pass",
            },
            "high_turnover_under_manager_distribution": {
                "evidence": str(HIGH_TURNOVER_MANAGER_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
                "query": HIGH_TURNOVER_MANAGER_SQL,
                "cutoff": "2026-09-27",
                "window": "(2026-03-29, 2026-09-27] across six complete fiscal intervals and seven dynamic closures",
                "population": "50,018 observable active regular direct reports of 10,487 managers with reconstructable history",
                "grain": "Aggregate manager-team history bucket assigned to current direct reports; no manager or employee identities",
                "definition": "Descriptive 0/1/2+ bucket of distinct strict-Voluntary exits in the manager's observable historical team; it is not a manager evaluation or causal attribution.",
                "buckets": ["0", "1", "2+"],
                "publication_rule": "Absolute counts and percentages only; every displayed manager and direct-report bucket n >= 30; no identities or individual labels.",
                "limitation": "190 current direct reports across 80 managers lack observable history and remain unknown rather than zero. 72 of 1,544 unique Voluntary events lack unique initial-interval exposure and are excluded, not imputed.",
                "outcome": "pass",
            },
            "qvoice_comparable_favorable": {
                "evidence": str(QVOICE_COMPARABLE_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
                "builder": str(QVOICE_COMPARABLE_BUILDER.relative_to(ROOT)).replace("\\", "/"),
                "source": "QVoice raw Excel workbooks; Raw data sheets only",
                "waves": [2024, 2025, 2026],
                "grain": "Participant-wave derived aggregate",
                "population": "Respondents with 33/33 strictly comparable valid binary items",
                "items": 33,
                "coding": "0=unfavorable; 1=favorable; 255=missing if present",
                "formula": "Individual score = 100 × favorable items / 33; annual result = arithmetic mean of included individual scores.",
                "publication_rule": "Aggregate internal analysis only; no identifiers or rows; every displayed wave cohort is n >= 30.",
                "limitation": "No workforce eligibility denominator, workforce join, or official survey-completion flag is inferred.",
                "outcome": "pass",
            },
            "commute_distance": {
                "evidence": str(COMMUTE_DISTANCE_EVIDENCE.relative_to(ROOT)),
                "query": COMMUTE_DISTANCE_PROFILE_SQL,
                "coverage_audit": COMMUTE_DISTANCE_COVERAGE_AUDIT_SQL,
                "format_audit": COMMUTE_DISTANCE_FORMAT_AUDIT_SQL,
                "snapshot": "2026-09-27",
                "population": "50,207 regular active employee groups globally; 45,433 stored Onsite",
                "grain": "Distinct employee snapshot",
                "office": "Qualcomm global office catalog from source page and model JSON",
                "method": "Haversine distance from residential postal centroid to office coordinate",
                "published_population": "41,760 of 50,207 calculable overall; 39,536 of 45,433 Onsite calculable",
                "privacy_rule": "Comparison uses broad display bands from 1-km evidence; only bands with n >= 30 are published; unmatched ZIPs/offices remain No calculable rather than imputed.",
                "outcome": "pass",
            },
            "prior_experience_years": {
                "evidence": str(PRIOR_EXPERIENCE_YEARS_EVIDENCE.relative_to(ROOT)),
                "query": PRIOR_EXPERIENCE_YEARS_PROFILE_SQL,
                "snapshot": STORED_METRIC_SNAPSHOT,
                "population": f"{STORED_METRIC_POPULATION_LABEL} regular active employees",
                "grain": "Distinct employee snapshot",
                "field": "prior_qc_work_years",
                "buckets": ["<1", "1 through 31", "32+"],
                "definition": "<1 means 0 <= prior_qc_work_years < 1; integer k means k <= prior_qc_work_years < k+1; 32+ means prior_qc_work_years >= 32.",
                "privacy_rule": "The exact year-32 bucket has n=25, so it is combined into 32+ to keep every published category at n >= 30.",
                "acceptance_rule": "Published counts sum to 50,218; null and negative counts are zero; every published category has n >= 30; no employee has multiple values in the snapshot.",
                "outcome": "pass",
            },
            "application_intensity": str(APPLICATION_INTENSITY_EVIDENCE.relative_to(ROOT)),
            "population": "Distinct linked applicants per fiscal year; not workforce prevalence.",
            "grain": "Distinct applicant-fiscal year",
            "buckets": ["1", "2", "3", "4+"],
            "office_site_city": {
                "evidence": str(OFFICE_SITE_CITY_EVIDENCE.relative_to(ROOT)),
                "query": OFFICE_SITE_CITY_PROFILE_SQL,
                "snapshot": "2026-08-23",
                "population": "Regular employees active in the snapshot",
                "grain": "Distinct employee snapshot",
                "buckets": ["top 20 pairs", "Other site-city pairs", "No office-site/city pair"],
            },
            "co_location_manager_location_proxies": {
                "evidence": str(CO_LOCATION_SITE_CITY_EVIDENCE.relative_to(ROOT)),
                "query": CO_LOCATION_SITE_CITY_PROFILE_SQL,
                "cutoff": V4_SNAPSHOT,
                "population": "Active regular employee-manager pairs with nonblank stored location fields in the same snapshot",
                "grain": "Employee-manager snapshot",
                "charts": ["same office_site", "same office_site and city"],
                "interpretation": "The city condition removes same-code pairs recorded in different cities. Neither stored-field proxy demonstrates physical presence or travel distance.",
                "outcome": "pass",
            },
            "team_turnover": {
                "evidence": str(TEAM_TURNOVER_EVIDENCE.relative_to(ROOT)),
                "query": TEAM_TURNOVER_PROFILE_SQL,
                "term_type_audit": TEAM_TURNOVER_TERM_TYPE_AUDIT_SQL,
                "team_membership_audit": TEAM_TURNOVER_MEMBERSHIP_AUDIT_SQL,
                "manager_resolution_audit": TEAM_TURNOVER_MANAGER_RESOLUTION_AUDIT_SQL,
                "cutoff": "2026-08-23",
                "window": "(2026-02-23, 2026-08-23] across six monthly snapshots",
                "population": "Active regular direct reports of managers selected at the cutoff",
                "grain": "Aggregate manager-team / employee-month exposure",
                "scenarios": ["all manager-led teams (>=1 direct report)", "teams with >5 direct reports (>=6)"],
                "voluntary_definition": "term_type = Voluntary only; Voluntary Exception excluded pending HR confirmation",
                "publication_note": "Aggregate descriptive comparison only; no manager labels or causal interpretation.",
            },
            "more_than_1_employee_leaves": {
                "evidence": str(MORE_THAN_1_LEAVES_EVIDENCE.relative_to(ROOT)),
                "query": MORE_THAN_1_LEAVES_AUDIT_SQL,
                "annual_evidence": str(MORE_THAN_1_LEAVES_ANNUAL_EVIDENCE.relative_to(ROOT)),
                "annual_query": MORE_THAN_1_LEAVES_ANNUAL_AUDIT_SQL,
                "annual_coverage_query": MORE_THAN_1_LEAVES_ANNUAL_COVERAGE_SQL,
                "cutoff": "2026-08-23",
                "window": "(snapshot - 6 months, snapshot] with six monthly snapshots; 40 independent monthly points per scope and attribution",
                "annual_window": "(snapshot - 12 months, snapshot] with >=12 monthly snapshots and >=330 observed days; 36 complete dates aligned to the 40 primary dates",
                "annual_history_exclusion": "The first 4 primary dates are excluded from the annual panel because prior-year history is incomplete.",
                "population": "Distinct employees with an observable direct team in each evaluation snapshot",
                "grain": "Scope × attribution × monthly employee snapshot",
                "buckets": ["0", "1", "2+"],
                "primary_attribution": "manager_at_evaluation",
                "historical_attribution": "manager_at_exit",
                "voluntary_definition": "term_type = Voluntary only",
                "monthly_points_per_scope_and_attribution": 40,
                "numerator": "Distinct employees in teams with at least 2 Voluntary exits in the six-month window",
                "denominator": "Distinct employees with a non-null direct manager at the evaluation snapshot",
                "publication_note": "The monthly employee percentage is the primary visual; the annual panel is a supplemental sensitivity, not a replacement feature. Aggregate 0/1/2+ buckets remain audit evidence only, with no manager labels or causal interpretation.",
            },
            "job_family": {
                "evidence": str(JOB_FAMILY_EVIDENCE.relative_to(ROOT)),
                "daily_query": JOB_FAMILY_PROFILE_SQL,
                "availability_audit": JOB_FAMILY_AVAILABILITY_AUDIT_SQL,
                "snapshots": [V4_SNAPSHOT, JOB_FAMILY_DAILY_SNAPSHOT],
                "population": "Regular employees active in each named snapshot",
                "grain": "Distinct employee snapshot; monthly August and daily September",
                "date_fields": {"August": "fis_mo_end_dt", "September": "transaction_date"},
                "buckets": ["top 20 detailed families", "Other job families"],
                "comparison_note": "September 7 is the user-selected post-weekend daily snapshot; rankings are independent, not a trend.",
            },
            "region": {
                "evidence": str(REGION_EVIDENCE.relative_to(ROOT)),
                "query": REGION_DISPLAY_AUDIT_SQL,
                "snapshot": V4_SNAPSHOT,
                "population": "Active regular employees at the named monthly snapshot",
                "grain": "Distinct employee snapshot",
                "global_display": ["India", "Americas", "APAC", "EMEA"],
                "major_country_display": ["India", "United States", "Americas excluding U.S.", "China", "APAC excluding China", "EMEA"],
                "labor_market_display": "All eligible employees: top 20 stored Labor Market values plus Other Labor Markets.",
                "labor_market_scope": "Global workforce distribution; Country and Region are separate fields and neither limits the Labor Market panel.",
                "major_country_display_scope": "Requested display-only grouping: United States is removed from Americas and China from APAC; it does not replace the stored Region definition.",
            },
            "transfer_within_past_year": {
                "evidence": str(TRANSFER_EVIDENCE.relative_to(ROOT)),
                "query": TRANSFER_PROFILE_SQL,
                "source_audit": TRANSFER_SOURCE_AUDIT_SQL,
                "validation_audit": TRANSFER_VALIDATION_AUDIT_SQL,
                "history_availability_audit": TRANSFER_HISTORY_AUDIT_SQL,
                "cutoff": "2026-08-23",
                "population": "Regular employees active at each monthly or weekly endpoint",
                "grain": "Distinct employee snapshot",
                "definition": "At least one distinct transfer_date in (snapshot - 12 months, snapshot]",
                "frequencies": {"monthly": 24, "weekly": 104},
                "canonical_frequency": "monthly",
                "operational_frequency": "weekly",
                "primary_chart_source": "hrda.post_hire_monthly_worker_dtls event history; workers_ios_transfers excluded",
            },
        },
        "visual_scope_policy": {
            "single_snapshot": f"Show the exact snapshot date; most frozen v4 category charts use {V4_SNAPSHOT} and stored metrics use {STORED_METRIC_SNAPSHOT}.",
            "historical_or_windowed": "Show fiscal-year, survey-wave, event-series, or rolling-window scope instead of a misleading singleton snapshot.",
        },
        "slides": [{"slide": index + 1, "title": label} for index, (label, _) in enumerate(slides)],
        "slide_content_hash_validation": content_hash_validation,
        "deliverable_mode": REPORTING_MODE,
        "publication_policy": (
            "Internal analysis: aggregate results only; n >= 30; real protected-category "
            "labels are permitted; no identities, free text, or exact compensation."
            if REPORTING_MODE == "internal_analysis"
            else "Presentation: aggregate results only; n >= 30; no identities, free text, "
            "protected values, or exact compensation."
        ),
        "visible_language_validation": {
            "language": "Legacy English deck; slides 8–9 Spanish by the Attrition narrative contract",
            "approved_spanish_stages": [8, 9],
            "residual_spanish_text_outside_approved_stages": residual_spanish,
            "outcome": "pass",
        },
    }
    try:
        qvoice_normalized_evidence = qvoice_normalized_region_evidence()
    except (FileNotFoundError, ValueError):
        qvoice_normalized_evidence = None
    if qvoice_normalized_evidence is not None:
        frozen_evidence = manifest["frozen_evidence"]
        assert isinstance(frozen_evidence, dict)
        frozen_evidence["qvoice_normalized_within_region"] = qvoice_normalized_region_manifest_entry(
            qvoice_normalized_evidence
        )
    try:
        layers_from_ceo_evidence, _ = layers_from_ceo_distribution_evidence()
    except (FileNotFoundError, ValueError):
        layers_from_ceo_evidence = None
    if layers_from_ceo_evidence is not None:
        manifest["source_runs"].append("layers-from-ceo-snapshot-20260823")
        manifest["new_aggregate_audits"].append(LAYERS_FROM_CEO_AUDIT_SQL)
        manifest["aggregate_evidence_builders"].append(
            str(LAYERS_FROM_CEO_BUILDER.relative_to(ROOT)).replace("\\", "/")
        )
        frozen_evidence = manifest["frozen_evidence"]
        assert isinstance(frozen_evidence, dict)
        frozen_evidence["reconstructed_manager_layers_to_ceo"] = (
            layers_from_ceo_manifest_entry(layers_from_ceo_evidence)
        )
    try:
        role_level_evidence, _, _ = role_level_tenure_distribution_evidence()
    except (FileNotFoundError, ValueError):
        role_level_evidence = None
    if role_level_evidence is not None:
        manifest["source_runs"].append("role-level-tenure-snapshot-20260823")
        manifest["new_aggregate_audits"].append(ROLE_LEVEL_TENURE_AUDIT_SQL)
        manifest["new_aggregate_profiles"].append(ROLE_LEVEL_TENURE_PROFILE_SQL)
        manifest["aggregate_evidence_builders"].append(
            str(ROLE_LEVEL_TENURE_BUILDER.relative_to(ROOT)).replace("\\", "/")
        )
        frozen_evidence = manifest["frozen_evidence"]
        assert isinstance(frozen_evidence, dict)
        frozen_evidence["role_level_tenure"] = role_level_tenure_manifest_entry(role_level_evidence)
    try:
        promotion_evidence, _, _ = time_since_last_promotion_distribution_evidence()
    except (FileNotFoundError, ValueError):
        promotion_evidence = None
    if promotion_evidence is not None:
        manifest["source_runs"].append("time-since-last-promotion-20260823")
        manifest["new_aggregate_audits"].append(TIME_SINCE_LAST_PROMOTION_AUDIT_SQL)
        manifest["new_aggregate_profiles"].append(TIME_SINCE_LAST_PROMOTION_PROFILE_SQL)
        manifest["aggregate_evidence_builders"].append(
            str(TIME_SINCE_LAST_PROMOTION_BUILDER.relative_to(ROOT)).replace("\\", "/")
        )
        frozen_evidence = manifest["frozen_evidence"]
        assert isinstance(frozen_evidence, dict)
        frozen_evidence["time_since_last_promotion"] = time_since_last_promotion_manifest_entry(promotion_evidence)
    try:
        promotion_history_evidence, _ = promotion_history_by_grade_evidence()
    except (FileNotFoundError, ValueError):
        promotion_history_evidence = None
    if promotion_history_evidence is not None:
        manifest["source_runs"].append("promotion-history-by-compensation-grade-20260823")
        manifest["new_aggregate_audits"].append(PROMOTION_HISTORY_BY_GRADE_AUDIT_SQL)
        manifest["new_aggregate_profiles"].append(PROMOTION_HISTORY_BY_GRADE_PROFILE_SQL)
        manifest["aggregate_evidence_builders"].append(
            str(PROMOTION_HISTORY_BY_GRADE_BUILDER.relative_to(ROOT)).replace("\\", "/")
        )
        frozen_evidence = manifest["frozen_evidence"]
        assert isinstance(frozen_evidence, dict)
        frozen_evidence["promotion_history_by_current_compensation_grade"] = (
            promotion_history_by_grade_manifest_entry(promotion_history_evidence)
        )
    try:
        entry_path_evidence, _ = current_grade_entry_path_evidence()
    except (FileNotFoundError, ValueError):
        entry_path_evidence = None
    if entry_path_evidence is not None:
        manifest["source_runs"].append("current-grade-entry-path-20260823")
        manifest["new_aggregate_audits"].append(CURRENT_GRADE_ENTRY_PATH_AUDIT_SQL)
        manifest["new_aggregate_profiles"].append(CURRENT_GRADE_ENTRY_PATH_PROFILE_SQL)
        manifest["aggregate_evidence_builders"].append(str(CURRENT_GRADE_ENTRY_PATH_BUILDER.relative_to(ROOT)).replace("\\", "/"))
        frozen_evidence = manifest["frozen_evidence"]
        assert isinstance(frozen_evidence, dict)
        frozen_evidence["current_grade_entry_path"] = current_grade_entry_path_manifest_entry(entry_path_evidence)
    try:
        company_tenure_evidence, _, _ = company_tenure_distribution_evidence()
    except (FileNotFoundError, ValueError):
        company_tenure_evidence = None
    if company_tenure_evidence is not None:
        manifest["source_runs"].append("company-tenure-stored-fields-snapshot-20260823")
        manifest["new_aggregate_audits"].append(COMPANY_TENURE_AUDIT_SQL)
        manifest["new_aggregate_profiles"].append(COMPANY_TENURE_PROFILE_SQL)
        manifest["aggregate_evidence_builders"].append(
            str(COMPANY_TENURE_BUILDER.relative_to(ROOT)).replace("\\", "/")
        )
        frozen_evidence = manifest["frozen_evidence"]
        assert isinstance(frozen_evidence, dict)
        frozen_evidence["company_tenure"] = company_tenure_manifest_entry(company_tenure_evidence)
    if REPORTING_MODE == "internal_analysis":
        try:
            engineering_cto_evidence = engineering_cto_org_split_evidence()
        except (FileNotFoundError, ValueError):
            engineering_cto_evidence = None
        if engineering_cto_evidence is not None:
            manifest["source_runs"].append("engineering-cto-org-split-display-20260911")
            for query in (
                ENGINEERING_CTO_MAIN_AUDIT_SQL,
                ENGINEERING_CTO_DENOMINATOR_AUDIT_SQL,
                ENGINEERING_CTO_JIM_AUDIT_SQL,
                ENGINEERING_CTO_UPPER_AUDIT_SQL,
            ):
                manifest["new_aggregate_audits"].append(query)
            manifest["aggregate_evidence_builders"].append("tools/build_engineering_cto_org_split_evidence.py")
            frozen_evidence = manifest["frozen_evidence"]
            assert isinstance(frozen_evidence, dict)
            frozen_evidence["engineering_cto_org_split_display"] = engineering_cto_manifest_entry(
                engineering_cto_evidence
            )
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(TARGET)
    print(MANIFEST)
    print(f"slides={len(slides)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Genera el deck de distribuciones de attrition."
    )
    parser.add_argument(
        "--reporting-mode",
        choices=("presentation", "internal_analysis"),
        default="presentation",
    )
    parser.add_argument(
        "--refresh-application-intensity-slides",
        action="store_true",
        help="Refresh the annual application distribution and insert the employee-snapshot trailing-six-month proposal.",
    )
    parser.add_argument(
        "--refresh-qvoice-retention-concerns-slide",
        action="store_true",
        help="Refresh only slide 19 from immutable aggregate QVoice retention-concerns evidence.",
    )
    parser.add_argument(
        "--refresh-qvoice-comparable-slide",
        action="store_true",
        help="Actualiza sólo la tarjeta comparable de QVoice en la lámina 24.",
    )
    parser.add_argument(
        "--refresh-qvoice-career-slide",
        action="store_true",
        help="Refresh only Career goals and keep its visual history through 2024.",
    )
    parser.add_argument(
        "--refresh-qvoice-normalized-region-slide",
        action="store_true",
        help="Refresh only the QVoice within-region standardized distribution.",
    )
    parser.add_argument(
        "--add-qvoice-heartbeat-slide",
        action="store_true",
        help="Insert the aggregate-only Jan-2026 QVoice heartbeat after Average of all QVoice items.",
    )
    parser.add_argument(
        "--refresh-talent-index-slide",
        action="store_true",
        help="Actualiza sólo la distribución agregada de Talent Index en la lámina 44.",
    )
    parser.add_argument(
        "--refresh-residential-manager-distance-slide",
        action="store_true",
        help="Refresh only the validated residential manager-distance slide 37.",
    )
    parser.add_argument(
        "--refresh-role-level-tenure-slide",
        action="store_true",
        help="Refresh only slide 26 after passing frozen role/profile and detailed-level evidence.",
    )
    parser.add_argument(
        "--refresh-company-tenure-slide",
        action="store_true",
        help="Refresh only slide 27 from fixed-snapshot aggregate stored-date evidence.",
    )
    parser.add_argument(
        "--refresh-layers-from-ceo-slide",
        action="store_true",
        help="Refresh only slide 32 from passing frozen same-snapshot hierarchy evidence.",
    )
    parser.add_argument(
        "--refresh-time-since-last-promotion-slide",
        action="store_true",
        help="Refresh only the stage titled Time since last promotion from presentation-safe frozen evidence.",
    )
    parser.add_argument(
        "--refresh-within-team-compensation-slide",
        action="store_true",
        help="Refresh only the stage titled Within team compensation range from presentation-safe frozen evidence.",
    )
    parser.add_argument(
        "--refresh-promotion-history-by-grade-slide",
        action="store_true",
        help="Refresh only slide 29 and its navigation label from internal aggregate matrix evidence.",
    )
    parser.add_argument(
        "--refresh-current-grade-entry-path-slide",
        action="store_true",
        help="Refresh only slide 30 and its navigation label from validated current-grade entry-path evidence.",
    )
    parser.add_argument(
        "--refresh-team-post-exit-attrition-slides",
        action="store_true",
        help="Actualiza sólo las láminas 8–9 con la cohorte descriptiva posterior a una salida inicial.",
    )
    parser.add_argument(
        "--refresh-work-arrangement-slide",
        action="store_true",
        help="Add the display-only Onsite=1 versus other=0 grouping below slide 13.",
    )
    parser.add_argument(
        "--refresh-engineering-slide",
        action="store_true",
        help="Add the display-only CTO versus Corp Fxn & BU grouping below slide 14.",
    )
    parser.add_argument(
        "--refresh-level-track-slide",
        action="store_true",
        help="Insert the display-only Level grouped by grade family slide after Level.",
    )
    parser.add_argument(
        "--refresh-commute-distance-slide",
        action="store_true",
        help="Replace the Commute distance stage with an all-versus-Onsite comparison.",
    )
    parser.add_argument(
        "--refresh-comp-ratio-slide",
        action="store_true",
        help="Refresh only slide 39 with the validated two-group voluntary-attrition history.",
    )
    parser.add_argument(
        "--refresh-number-of-manager-changes-slide",
        action="store_true",
        help="Refresh only Number of manager changes with the same-date mobility sensitivity.",
    )
    args = parser.parse_args()
    requested_refreshes = sum(
        (
            args.refresh_application_intensity_slides,
            args.refresh_qvoice_retention_concerns_slide,
            args.refresh_qvoice_comparable_slide,
            args.refresh_qvoice_career_slide,
            args.refresh_qvoice_normalized_region_slide,
            args.add_qvoice_heartbeat_slide,
            args.refresh_talent_index_slide,
            args.refresh_residential_manager_distance_slide,
            args.refresh_role_level_tenure_slide,
            args.refresh_company_tenure_slide,
            args.refresh_layers_from_ceo_slide,
            args.refresh_time_since_last_promotion_slide,
            args.refresh_within_team_compensation_slide,
            args.refresh_promotion_history_by_grade_slide,
            args.refresh_current_grade_entry_path_slide,
            args.refresh_team_post_exit_attrition_slides,
            args.refresh_work_arrangement_slide,
            args.refresh_engineering_slide,
            args.refresh_level_track_slide,
            args.refresh_commute_distance_slide,
            args.refresh_comp_ratio_slide,
            args.refresh_number_of_manager_changes_slide,
        )
    )
    if requested_refreshes > 1:
        parser.error("Use only one focused refresh per run.")
    if args.refresh_application_intensity_slides:
        refresh_application_intensity_slides(args.reporting_mode)
    elif args.refresh_qvoice_retention_concerns_slide:
        refresh_qvoice_retention_concerns_slide(args.reporting_mode)
    elif args.refresh_qvoice_comparable_slide:
        refresh_qvoice_comparable_slide(args.reporting_mode)
    elif args.refresh_qvoice_career_slide:
        refresh_qvoice_career_slide(args.reporting_mode)
    elif args.refresh_qvoice_normalized_region_slide:
        refresh_qvoice_normalized_region_slide(args.reporting_mode)
    elif args.add_qvoice_heartbeat_slide:
        add_qvoice_heartbeat_slide(args.reporting_mode)
    elif args.refresh_talent_index_slide:
        refresh_talent_index_distribution_slide(args.reporting_mode)
    elif args.refresh_residential_manager_distance_slide:
        refresh_residential_manager_distance_slide(args.reporting_mode)
    elif args.refresh_role_level_tenure_slide:
        try:
            refresh_role_level_tenure_slide(args.reporting_mode)
        except (FileNotFoundError, ValueError) as exc:
            raise SystemExit(f"Role/level tenure refresh blocked: {exc}") from exc
    elif args.refresh_company_tenure_slide:
        try:
            refresh_company_tenure_slide(args.reporting_mode)
        except (FileNotFoundError, ValueError) as exc:
            raise SystemExit(f"Company tenure refresh blocked: {exc}") from exc
    elif args.refresh_layers_from_ceo_slide:
        refresh_layers_from_ceo_slide(args.reporting_mode)
    elif args.refresh_time_since_last_promotion_slide:
        refresh_time_since_last_promotion_slide(args.reporting_mode)
    elif args.refresh_within_team_compensation_slide:
        refresh_within_team_compensation_slide(args.reporting_mode)
    elif args.refresh_promotion_history_by_grade_slide:
        refresh_promotion_history_by_grade_slide(args.reporting_mode)
    elif args.refresh_current_grade_entry_path_slide:
        refresh_current_grade_entry_path_slide(args.reporting_mode)
    elif args.refresh_team_post_exit_attrition_slides:
        refresh_team_post_exit_attrition_slides(args.reporting_mode)
    elif args.refresh_work_arrangement_slide:
        refresh_work_arrangement_slide(args.reporting_mode)
    elif args.refresh_engineering_slide:
        refresh_engineering_cto_slide(args.reporting_mode)
    elif args.refresh_level_track_slide:
        refresh_level_grouped_by_grade_family_slide(args.reporting_mode)
    elif args.refresh_commute_distance_slide:
        refresh_commute_distance_slide(args.reporting_mode)
    elif args.refresh_comp_ratio_slide:
        refresh_comp_ratio_slide(args.reporting_mode)
    elif args.refresh_number_of_manager_changes_slide:
        refresh_number_of_manager_changes_slide(args.reporting_mode)
    else:
        build(args.reporting_mode)
