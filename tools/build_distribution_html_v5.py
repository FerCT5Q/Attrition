"""Build V5 as a chart-first revision of the V4 evidence deck.

V5 deliberately starts from the reviewed V2 HTML and reproduces the approved
V4 evidence overlays.  It removes the narrative card on the right of each
content slide, expands the visual area, moves a short plain-language reading
into the subtitle, displays percentages and rates with one decimal, and keeps
counts as whole numbers.  Slides for unavailable external sources or empty
charts are omitted.

No employee-level data is read or rendered.  V2 and V3 are source artifacts
and are never modified by this builder.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import unicodedata
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "distribution"
EVIDENCE_DIR = OUT / "json"
V2 = OUT / "attrition-43-variable-distributions-v2.html"
V3 = OUT / "attrition-43-variable-distributions-v3.html"
V4 = OUT / "attrition-43-variable-distributions-v4.html"
V2_MANIFEST = EVIDENCE_DIR / "attrition-43-variable-distributions-v2-manifest.json"
EVIDENCE = EVIDENCE_DIR / "attrition-43-variable-distributions-v3.six-month-attrition-evidence-20260914.json"
COMMUTE_EVIDENCE = EVIDENCE_DIR / "commute-distance-onsite-six-month-attrition-evidence-20260917.json"
TEMPLATE = Path(r"C:\Users\fcarranz\.codex\skills\html-slide-generator\templates\fullscreen\base-fullscreen.html")
TARGET = OUT / "attrition-43-variable-distributions-v5.html"
MANIFEST = EVIDENCE_DIR / "attrition-43-variable-distributions-v5-manifest.json"

MINIMUM_COHORT = 30
MATURE_FIRST_SNAPSHOT = "2024-03-24"
MATURE_LAST_SNAPSHOT = "2026-02-22"
EXPECTED_SLIDE_COUNT = 50
EXPECTED_REMOVED_RIGHT_PANELS = 46


# These slides do not contain a usable, presentation-ready visualization.
# Keep their original IDs absent rather than renumbering the retained stage
# elements, because several slide-specific CSS rules depend on those IDs.
EXCLUDED_SLIDES: dict[str, str] = {
    "externalpullfactors": "External sources are not enabled.",
    "attritionvoluntaryanualporviadeentradaalgradeytenure": "The charts are empty because the required history is unavailable.",
}


# The index is the visible chart-card position within the V2 slide.  A panel
# omitted from this mapping intentionally remains byte-for-byte V2 content.
PANEL_METRICS: dict[str, dict[int, str]] = {
    "location": {0: "country"},
    "officesiteandcity": {0: "office_site", 1: "office_site_city"},
    "jobfamily": {0: "job_family", 1: "job_family"},
    "region": {0: "region", 1: "region_country_split", 2: "labor_market"},
    "gender": {0: "gender"},
    "remotehybridinofficestatus": {0: "work_arrangement", 1: "work_arrangement_binary"},
    "engineeringvsnonengineering": {0: "engineering"},
    "yearsofexperiencepriortoqualcomm": {0: "prior_experience_years"},
    # The original-hire proxy has different bands from the approved historical
    # rate.  Only the latest hire / rehire panel is eligible.
    "companytenure": {1: "company_tenure"},
    "level": {0: "level_grouped", 1: "management_level", 2: "job_level"},
    "compensationgrade": {0: "compensation_grade"},
    # The current comp-ratio band chart is horizontal, even though its
    # companion historical six-month chart already lives on the same slide.
    "compratio": {0: "comp_ratio_band"},
}


# Some V2 charts are vertical annual-prevalence charts.  Their bars are years,
# whereas the approved V3 rate is by the stored 0/1 flag, so overlaying a rate
# on each year would be semantically wrong.  Keep the V2 chart unchanged and
# present the approved flag-level rates as an orange inline summary instead.
SUMMARY_METRICS: dict[str, dict[str, Any]] = {
    "rehire": {
        "metric": "rehire",
        "chart_card_index": 0,
        "label": "Six-month voluntary attrition by flag",
        "category_order": ("Not rehire (0)", "Rehire (1)"),
    },
    "managerchange": {
        "metric": "manager_change",
        "chart_card_index": 0,
        "label": "Six-month voluntary attrition by flag",
        "category_order": ("No manager change (0)", "Manager change (1)"),
    },
}


# These V2 charts resemble distribution charts but V3 explicitly did not
# approve a time-safe outcome join or a governed temporal definition for
# them.  A neutral status makes that boundary visible without fabricating an
# attrition number.
UNAVAILABLE_ATTRITION_SLIDES: dict[str, str] = {
    "averageofallqvoiceitems": (
        "No publishable rate: the QVoice respondent-only score does not have "
        "an approved time-aligned link to voluntary exits."
    ),
    "qvoiceheartbeat": (
        "No publishable rate: QVoice items do not have an approved time-aligned "
        "link to voluntary exits."
    ),
    "timeincurrentjobprofilevscurrentdetailedlevel": (
        "No publishable rate: these stored dates do not define an approved HRIS "
        "career-tenure measure."
    ),
}


# Reader-facing titles remain close to the canonical variable names.  The
# subtitle does the explanatory work: it states the main reading in plain
# English so every slide can stand on its own for a non-technical audience.
PLAIN_LANGUAGE_HEADINGS: dict[str, tuple[str, str]] = {
    "evidencefor44attritionmodelcandidates": (
        "Evidence for 44 attrition model candidates",
        "A visual review of 44 possible inputs and the evidence available for each one",
    ),
    "agenda": (
        "Agenda",
        "The review moves from employee activity to workforce, survey, pay, and manager signals",
    ),
    "appliedtoajob": (
        "Applied to a job",
        "How many different jobs linked applicants applied to during each fiscal year",
    ),
    "appliedtoajobemployeesnapshottrailingsixmonths": (
        "Applied to a job — trailing six months",
        "Applications found in the prior six months; missing coverage remains Unknown",
    ),
    "transferwithinpastyear": (
        "Transfer within the past year",
        "Employees with a transfer in the prior year, shown monthly and weekly",
    ),
    "location": (
        "Location",
        "Where active employees are located and the historical attrition rate for each country group",
    ),
    "officesiteandcity": (
        "Office site and city",
        "Employee distribution by office site and by office-site and city combination",
    ),
    "teamturnover": (
        "Team turnover",
        "Voluntary exits as a share of average team size during the same six-month period",
    ),
    "unasalidainicialprecedemassalidas": (
        "Does one team departure precede more departures?",
        "Attrition after one team departure compared with teams without a recent departure",
    ),
    "sensibilidadequiposde6pluspersonas": (
        "Sensitivity check: teams with 6+ employees",
        "The same comparison limited to teams with at least 6 employees",
    ),
    "jobfamily": (
        "Job family",
        "Workforce distribution by job family before and after the reorganization",
    ),
    "region": (
        "Region",
        "Three geographic views: Region, country split, and labor market",
    ),
    "gender": (
        "Gender",
        "An anonymized view of workforce composition and attrition for fairness review",
    ),
    "remotehybridinofficestatus": (
        "Work arrangement",
        "Recorded work arrangements and a simplified two-group comparison",
    ),
    "engineeringvsnonengineering": (
        "Engineering vs. non-engineering",
        "The recorded engineering category compared with an organization-based grouping",
    ),
    "rehire": (
        "Rehire",
        "Recorded rehire categories over time and their historical attrition",
    ),
    "yearsofexperiencepriortoqualcomm": (
        "Experience before Qualcomm",
        "Employees grouped by completed years of experience before joining Qualcomm",
    ),
    "annualvoluntaryattritionbypriorexperience": (
        "Annual voluntary attrition by prior experience",
        "Annual voluntary attrition across prior-experience groups; the comparison is descriptive",
    ),
    "commutedistance": (
        "Commute distance",
        "Six-month attrition across estimated commute-distance groups for onsite employees",
    ),
    "rtohybridcommentinqvoice": (
        "RTO and hybrid comments in QVoice",
        "How often RTO and hybrid topics appeared in selected QVoice comments",
    ),
    "retentionconcernsinqvoicecomments": (
        "Retention concerns in QVoice comments",
        "The retention-related improvement themes mentioned most often in selected comments",
    ),
    "nonrespondents": (
        "QVoice participation coverage",
        "The share of the workforce linked to a QVoice response in each survey wave",
    ),
    "intenttostayitems": (
        "Intent to Stay items",
        "Availability of the two Intent to Stay questions across survey waves",
    ),
    "careergoalsitem": (
        "Career goals item",
        "Availability of the career-goals question across survey waves",
    ),
    "averageofallqvoiceitems": (
        "Average of comparable QVoice items",
        "Distribution of the comparable 33-question score among complete respondents",
    ),
    "qvoiceheartbeat": (
        "QVoice heartbeat",
        "Questions above or below each respondent's own average response",
    ),
    "standardizednormalizedwithinregion": (
        "QVoice scores standardized within region",
        "Regional scores compared with each region's own average for that survey year",
    ),
    "externalpullfactors": (
        "External pull factors",
        "Why external labor-market signals remain outside the model for now",
    ),
    "timeincurrentjobprofilevscurrentdetailedlevel": (
        "Time in job profile vs. detailed level",
        "Two approximate views of time in role based on different recorded start dates",
    ),
    "attritionvoluntaryanualporviadeentradaalgradeytenure": (
        "Annual attrition by grade-entry path and tenure",
        "Incomplete history prevents a reliable comparison by grade-entry path and tenure",
    ),
    "companytenure": (
        "Company tenure",
        "Two views of service time: original hire and latest hire or rehire",
    ),
    "timesincelastpromotion": (
        "Time since last promotion",
        "Time since the latest recorded promotion and the share with usable history",
    ),
    "promotionhistorybycurrentcompensationgrade": (
        "Promotion history by current compensation grade",
        "How recorded promotion history varies across current compensation grades",
    ),
    "howemployeesreachedtheircurrentcompensationgrade": (
        "How employees reached their current compensation grade",
        "What the available history shows about entry into the current grade",
    ),
    "level": (
        "Level",
        "Workforce distribution across three related but different level fields",
    ),
    "levelgroupedbygradefamily": (
        "Level grouped by grade family",
        "How Level groups are composed across compensation-grade families",
    ),
    "reconstructedmanagerlayerstoceo": (
        "Manager layers to the CEO",
        "The number of manager links between employees and the approved CEO position",
    ),
    "compensationgrade": (
        "Compensation grade",
        "Active employees by compensation grade, with small groups combined",
    ),
    "compratio": (
        "Comp ratio",
        "Employee distribution by comp ratio and the related historical attrition trend",
    ),
    "withinteamcompensationrange": (
        "Within-team compensation range",
        "Wide pay ranges in comparable teams and the number of groups available for review",
    ),
    "colocationwithmanager": (
        "Co-location with manager",
        "How often employees and managers share the same recorded site or site and city",
    ),
    "residentialdistancefrommanager": (
        "Residential distance from manager",
        "Estimated residential distance between employees and managers, shown in distance groups",
    ),
    "officesiterelationshipwithmanager": (
        "Office-site relationship with manager",
        "Employee and manager office-site relationships across monthly workforce records",
    ),
    "highriskmanager": (
        "Manager observed-to-expected exit ratio",
        "Managers grouped by the ratio of observed to expected voluntary exits",
    ),
    "highturnoverunderthisperson": (
        "Recent team exits under the current manager",
        "Employees grouped by recent voluntary exits under their current manager",
    ),
    "aboveaverageteamturnover": (
        "Above-average team turnover",
        "Employees with enough manager history to classify team turnover",
    ),
    "managerleaving": (
        "Manager leaving",
        "Employees recently exposed to a manager's voluntary departure",
    ),
    "managerchange": (
        "Manager change",
        "Manager-change events by year and the related historical attrition comparison",
    ),
    "numberofmanagerchanges": (
        "Number of manager changes",
        "Recent manager-change counts under four definitions",
    ),
    "talentindex": (
        "Talent index",
        "Distribution of the latest available talent-index values among active employees",
    ),
    "majorinflectionpoints": (
        "Major inflection points",
        "Recorded employee changes and why no rule yet defines a major change",
    ),
    "etfields": (
        "ET fields",
        "How often the ET hierarchy fields are populated; they are not confirmed career levels",
    ),
}


# Slides with dense or technical narrative receive a shorter reading guide.
# The chart, values, category labels, and privacy rules remain unchanged.
PLAIN_LANGUAGE_PANELS: dict[str, dict[str, Any]] = {
    "appliedtoajob": {
        "badge": "Internal aggregate analysis",
        "heading": "What this chart counts",
        "summary": "Each linked applicant is counted once per fiscal year and grouped by the number of unique requisitions they applied to.",
        "facts": (
            ("Population", "Applicants found in the application records, not the full workforce"),
            ("Period", "FY2022 through FY2026 year to date"),
            ("Buckets", "1, 2, 3, or 4+ unique requisitions"),
            ("Privacy", "Aggregate counts only; no applicant records are shown"),
        ),
        "bottom_line": "Use this slide to understand application intensity among linked applicants. It cannot estimate how many employees made no application.",
    },
    "appliedtoajobemployeesnapshottrailingsixmonths": {
        "badge": "Exploratory analysis",
        "heading": "Missing coverage stays Unknown",
        "summary": "For each monthly workforce snapshot, the chart looks back six months for linked applications. Missing source coverage is not treated as zero applications.",
        "facts": (
            ("Latest publishable date", "26-Jul-2026"),
            ("Population", "49,652 active regular employee snapshots"),
            ("Application coverage", "9.68%"),
            ("Unknown", "90.32% because zero and missing coverage cannot be separated"),
        ),
        "bottom_line": "This is useful for exploration, but it is not ready for production or individual decisions.",
    },
    "officesiteandcity": {
        "badge": "Aggregate distribution",
        "heading": "Two different location views",
        "summary": "Office site is a stored site code. The site-city label is created only for this display by combining office site and city.",
        "facts": (
            ("Population", "50,043 active regular employees on 23-Aug-2026"),
            ("Left chart", "Stored office-site codes"),
            ("Right chart", "Derived office-site and city pairs"),
            ("Missing data", "Shown separately when either field is blank"),
        ),
        "bottom_line": "Use the two charts as different levels of location detail, not as interchangeable fields.",
    },
    "teamturnover": {
        "badge": "Exploratory aggregate analysis",
        "heading": "How the rate is calculated",
        "summary": "Managers are selected at the August cutoff. Voluntary exits over the prior six months are divided by the average team size across those same months.",
        "facts": (
            ("All teams", "3.11 voluntary exits per 100 average direct reports"),
            ("Teams with more than 5 reports", "2.98 per 100"),
            ("Difference", "0.13 percentage points"),
            ("Exit rule", "Voluntary exits only; assigned to the manager before the exit"),
        ),
        "bottom_line": "This describes team history. It is not a manager rating or a causal result.",
    },
    "unasalidainicialprecedemassalidas": {
        "badge": "Descriptive association",
        "heading": "What is being compared",
        "summary": "The chart follows employees who remained after one recent team departure and compares them with similar-size teams that had no recent departure.",
        "facts": (
            ("Follow-up", "Six monthly checkpoints from Apr-2026 to Sep-2026"),
            ("Starting groups", "1,461 exposed employees and 41,617 comparison employees"),
            ("Six-month result", "4.88% versus 2.88%, a 2.00-point difference"),
            ("Source", "HRDA events reconciled across two sources"),
        ),
        "bottom_line": "This recent cohort shows an association. It does not prove contagion, causation, manager performance, or individual risk.",
    },
    "sensibilidadequiposde6pluspersonas": {
        "badge": "Descriptive association",
        "heading": "A check focused on larger teams",
        "summary": "This repeats the prior analysis but keeps only teams with at least six employees at the starting date.",
        "facts": (
            ("Follow-up", "Six monthly checkpoints from Apr-2026 to Sep-2026"),
            ("Starting groups", "978 exposed employees and 20,155 comparison employees"),
            ("Six-month result", "5.74% versus 2.91%, a 2.83-point difference"),
            ("Change from prior slide", "Teams with 1–5 employees are excluded"),
        ),
        "bottom_line": "The pattern remains descriptive and is based on one recent cohort; it is not evidence of causation.",
    },
    "jobfamily": {
        "badge": "Two separate snapshots",
        "heading": "Do not read this as a trend",
        "summary": "The panels show different dates around a job-family reorganization. Each panel ranks its own largest categories.",
        "facts": (
            ("August", "50,033 active regular employees in the monthly snapshot"),
            ("September", "50,214 active regular employees in the daily snapshot"),
            ("Display", "Top 20 categories plus Other in each panel"),
            ("Pending", "The official detail-to-group mapping still needs confirmation"),
        ),
        "bottom_line": "Compare the overall shape, not individual rows as if they were a stable one-to-one mapping.",
    },
    "region": {
        "badge": "Three geographic views",
        "heading": "Each chart answers a different question",
        "summary": "The first chart uses the stored Region field. The second separates the U.S. and China for display. Labor Market is a separate source field.",
        "facts": (
            ("Population", "50,043 active regular employees on 23-Aug-2026"),
            ("Stored Region", "India, Americas, APAC, and EMEA"),
            ("Alternative view", "U.S. and China shown separately"),
            ("Labor Market", "Top 20 values plus Other; no missing values"),
        ),
        "bottom_line": "The alternative split is a presentation view and does not replace the stored Region field.",
    },
    "remotehybridinofficestatus": {
        "badge": "Exploratory grouping",
        "heading": "The source has more than three labels",
        "summary": "The upper chart keeps the original work-arrangement categories. The lower chart compares Onsite with every other value.",
        "facts": (
            ("Population", "50,033 employees in the latest snapshot"),
            ("Detailed view", "Top 10 stored labels, Other, and missing"),
            ("Two-group view", "Onsite versus all other or missing values"),
            ("Status", "No approved Remote, Hybrid, and In-office mapping exists"),
        ),
        "bottom_line": "Use the detailed source labels for interpretation; the binary view is exploratory only.",
    },
    "yearsofexperiencepriortoqualcomm": {
        "badge": "Internal aggregate analysis",
        "heading": "Completed years before Qualcomm",
        "summary": "Each bar represents a completed-year interval from the stored prior-experience value.",
        "facts": (
            ("Population", "50,218 active regular employees on 27-Sep-2026"),
            ("Coverage", "100%"),
            ("Bands", "Less than 1 year, years 1–31, and 32+ years"),
            ("Privacy", "The year-32 group had 25 employees and was combined into 32+"),
        ),
        "bottom_line": "The stored value is usable for description, but its business formula and rounding rules still need confirmation.",
    },
    "annualvoluntaryattritionbypriorexperience": {
        "badge": "Descriptive association",
        "heading": "How to read the annual rates",
        "summary": "For each experience band, annual voluntary exits are divided by average monthly active headcount in that band.",
        "facts": (
            ("Period", "FY2021 through FY2025"),
            ("Bands", "Fixed before reviewing the results"),
            ("Population", "Active regular employees in monthly workforce snapshots"),
            ("Coverage rule", "Every published cell contains at least 30 employees"),
        ),
        "bottom_line": "Differences between bands are descriptive. They do not prove causation or predict an individual's departure.",
    },
    "commutedistance": {
        "badge": "Approximate geographic measure",
        "heading": "Distance, not commute time",
        "summary": "Distance is the straight-line distance between a postal-code centroid and the listed office coordinate.",
        "facts": (
            ("Population", "50,207 eligible employees on 27-Sep-2026"),
            ("Distance available", "41,760 employees, or 83.2%"),
            ("Onsite comparison", "39,536 of 45,433 Onsite employees have a calculable distance"),
            ("Not measured", "Road route, travel time, or actual commuting behavior"),
        ),
        "bottom_line": "Use this as broad geographic context only.",
    },
    "rtohybridcommentinqvoice": {
        "badge": "Internal aggregate analysis",
        "heading": "Topic mentions, not sentiment",
        "summary": "The chart counts how many respondents mentioned an RTO or hybrid topic in open-text feedback. Comment text is not shown.",
        "facts": (
            ("Survey waves", "Mar-2023, Jan-2024, Jan-2025, and Jan-2026"),
            ("Latest wave", "15,351 respondents with comments"),
            ("Counting rule", "One respondent per wave and topic; topics may overlap"),
            ("Privacy", "Aggregate counts only; no comments or identities"),
        ),
        "bottom_line": "A mention does not show positive or negative sentiment, agreement, or attrition risk.",
    },
    "retentionconcernsinqvoicecomments": {
        "badge": "Internal aggregate analysis",
        "heading": "What respondents mentioned for improvement",
        "summary": "The bars show common improvement themes in the Jan-2026 comments selected for this analysis.",
        "facts": (
            ("Denominator", "13,862 respondents with at least one selected improvement comment"),
            ("Percentages", "Themes can overlap, so they do not add to 100%"),
            ("Privacy", "Only aggregate themes with at least 30 respondents are shown"),
            ("Comparison limit", "The 2025 and 2026 waves include an additional prompt"),
        ),
        "bottom_line": "Themes are descriptive and do not identify sentiment, causation, or individual attrition risk.",
    },
    "nonrespondents": {
        "badge": "Participation proxy",
        "heading": "A missing row is not confirmed non-response",
        "summary": "Each survey wave is compared with a prior-month workforce snapshot used as an eligibility approximation.",
        "facts": (
            ("Responded", "A survey row contains at least one answer"),
            ("No answer", "A survey row exists but checked answer fields are blank"),
            ("No row", "The employee is absent from the raw survey keys"),
            ("Pending", "Invitation eligibility and final wave-close status"),
        ),
        "bottom_line": "Use this as a source-reconciliation view, not as a final response-rate measure.",
    },
    "averageofallqvoiceitems": {
        "badge": "Respondent-only comparison",
        "heading": "A consistent 33-item score",
        "summary": "The trend includes only respondents with valid answers to all 33 favorable items shared across the 2024–2026 waves.",
        "facts": (
            ("Score", "Percent favorable across the 33 common items"),
            ("Population", "Complete respondents, not the full workforce"),
            ("Trend", "Average individual score by survey wave"),
            ("Distribution", "Each bar totals 100% of included respondents"),
        ),
        "bottom_line": "The score supports comparison among complete respondents only; it is not a workforce-wide perception estimate.",
    },
    "qvoiceheartbeat": {
        "badge": "Restricted aggregate analysis",
        "heading": "Relative to each person's own answers",
        "summary": "An item is marked above or below when it differs from the same respondent's average across valid 1–5 responses.",
        "facts": (
            ("Wave", "Jan-2026"),
            ("Items", "53 questions; at least 38 valid answers required"),
            ("Eligible respondents", "37,605"),
            ("Absolute context", "Responses 4–5 are shown separately as favorable"),
        ),
        "bottom_line": "This is not an absolute sentiment score, a time trend, or an individual attrition score.",
    },
    "standardizednormalizedwithinregion": {
        "badge": "Internal aggregate analysis",
        "heading": "Relative standing within the same region and year",
        "summary": "Each respondent's 33-item score is compared with respondents in the same stored Region and survey wave.",
        "facts": (
            ("Population", "Respondents with all 33 common items"),
            ("Reference group", "Same Region and survey wave, with at least 30 respondents"),
            ("Scale", "Zero is the group average; positive values are above it"),
            ("Limit", "Respondent-only; no approved workforce or attrition link"),
        ),
        "bottom_line": "Use this to compare relative position within a peer group, not absolute sentiment across regions.",
    },
    "externalpullfactors": {
        "badge": "Not available",
        "heading": "Why these candidates remain outside the model",
        "summary": "The three external ideas do not yet have an approved provider, data contract, or reliable link to the workforce and date being modeled.",
        "facts": (
            ("Candidates", "Three external signals; none is integrated"),
            ("Current baseline", "Internal HR data and selected QVoice measures"),
            ("Future test", "Compare value on the same population and future period"),
            ("Guardrail", "No scraping or identity matching without explicit approval"),
        ),
        "bottom_line": "Keep these signals out of the baseline until governance and time alignment are approved.",
    },
    "timeincurrentjobprofilevscurrentdetailedlevel": {
        "badge": "Exploratory approximation",
        "heading": "Two dates, two different measures",
        "summary": "The left chart uses the stored job-profile start date. The right chart uses the stored detailed-level entry date.",
        "facts": (
            ("Population", "50,043 active regular employees on 23-Aug-2026"),
            ("Rehire adjustment", "The later of the stored start date and latest hire or rehire date is used"),
            ("Coverage", "Both calculations are available for the full displayed population"),
            ("Not used", "The time_in_role field does not calculate either chart"),
        ),
        "bottom_line": "These are useful approximations, not an approved HRIS definition of career tenure.",
    },
    "attritionvoluntaryanualporviadeentradaalgradeytenure": {
        "badge": "No publishable historical rate",
        "heading": "The required tenure history is missing",
        "summary": "The historical records do not contain the job-profile start date needed to place employees and exits into tenure bands.",
        "facts": (
            ("Period checked", "FY2021 through FY2025"),
            ("Missing start dates", "2,405,034 of 2,405,034 active employee snapshots"),
            ("Voluntary exits", "12,631; none can be assigned to a publishable tenure band"),
            ("Result", "The empty charts reflect unavailable evidence, not a zero attrition rate"),
        ),
        "bottom_line": "Do not interpret the blank result as no attrition. The historical measure cannot be calculated reliably.",
    },
    "timesincelastpromotion": {
        "badge": "Aggregate recorded history",
        "heading": "Latest recorded promotion only",
        "summary": "The duration starts at the latest valid promotion recorded during the employee's current period of employment.",
        "facts": (
            ("Population", "50,043 active regular employees on 23-Aug-2026"),
            ("Dated promotion available", "23,180 employees"),
            ("No duration shown", "26,863 employees; this does not mean never promoted"),
            ("History limit", "Reliable event history begins on 23-Oct-2016"),
        ),
        "bottom_line": "The chart describes recorded events and incomplete history; it does not evaluate promotion policy or attrition causes.",
    },
    "promotionhistorybycurrentcompensationgrade": {
        "badge": "Internal aggregate analysis",
        "heading": "Recorded promotions within the current employment period",
        "summary": "Each row shows the share of employees in a current grade with zero, one, or two or more recorded promotion events.",
        "facts": (
            ("Population", "50,043 active regular employees on 23-Aug-2026"),
            ("Observable history", "38,776 employees"),
            ("Partial history", "11,267 employment periods began before reliable event history"),
            ("Recorded promotion", "23,180 employees have at least one valid event"),
        ),
        "bottom_line": "These are recorded events, not a complete career history or a classification of how employees were hired.",
    },
    "howemployeesreachedtheircurrentcompensationgrade": {
        "badge": "Internal aggregate analysis",
        "heading": "What can be observed about entry into the current grade",
        "summary": "A promotion is confirmed only when a registered promotion date matches the latest observed move into the current grade.",
        "facts": (
            ("Population", "50,043 active regular employees on 23-Aug-2026"),
            ("Promotion confirmed", "19,669 employees"),
            ("Entry observed without a registered promotion", "7,604 employees"),
            ("Entry not observable", "22,770 employees"),
        ),
        "bottom_line": "An observed entry without a promotion record does not mean the employee was hired directly into the grade.",
    },
    "level": {
        "badge": "Three related fields",
        "heading": "The fields are not synonyms",
        "summary": "Level grouped is the main senior-to-junior hierarchy. Management level is a compact support field, and job level contains separate R, T, and P families.",
        "facts": (
            ("Primary view", "Level grouped"),
            ("Management level", "Does not by itself prove people-management responsibility"),
            ("Job level", "Families are ranked by size because they are not one common ladder"),
            ("Date", "23-Aug-2026 workforce snapshot"),
        ),
        "bottom_line": "Use each field for its own purpose and do not substitute one for another.",
    },
    "levelgroupedbygradefamily": {
        "badge": "Exploratory display",
        "heading": "Grade family adds context to Level",
        "summary": "Each Level band is split by the first character of compensation grade to show its internal mix.",
        "facts": (
            ("Population", "50,043 active regular employees on 23-Aug-2026"),
            ("Primary variable", "Level grouped"),
            ("Added context", "Compensation-grade prefix"),
            ("Privacy", "Every visible combination contains at least 30 employees"),
        ),
        "bottom_line": "The grade prefix is a display aid, not an official career track or replacement for Level.",
    },
    "reconstructedmanagerlayerstoceo": {
        "badge": "Validated aggregate hierarchy",
        "heading": "Number of manager links to the CEO",
        "summary": "The approved CEO root is layer 0, a direct report is layer 1, and each additional manager link adds one layer.",
        "facts": (
            ("Population", "50,043 active regular employees on 23-Aug-2026"),
            ("Root check", "One approved root; 100% of chains converge"),
            ("Maximum search", "25 manager links"),
            ("Privacy", "No employee, manager, or CEO identity is displayed"),
        ),
        "bottom_line": "This is reporting-line depth reconstructed within one workforce snapshot.",
    },
    "compratio": {
        "badge": "Descriptive historical comparison",
        "heading": "The 0.8 split is exploratory",
        "summary": "The lower chart compares six-month voluntary attrition for stored comp-ratio values below 0.8 versus values at or above 0.8.",
        "facts": (
            ("History", "68 complete monthly snapshots from Jul-2020 through Feb-2026"),
            ("Pooled rates", "2.85% below 0.8 and 3.02% at or above 0.8"),
            ("Difference", "−0.17 percentage points"),
            ("Pending", "The stored metric's formula and source history are not confirmed"),
        ),
        "bottom_line": "The comparison does not show that anyone is underpaid and does not produce an individual prediction.",
    },
    "withinteamcompensationrange": {
        "badge": "Aggregate review signal",
        "heading": "How a comparable group is defined",
        "summary": "Direct reports are compared only when they share a manager, country, compensation grade, and currency.",
        "facts": (
            ("Comparable group", "At least two employees with complete pay data"),
            ("Review signal", "Highest FTE-adjusted base pay is at least 10% above the lowest"),
            ("Managers with comparable groups", "7,780"),
            ("Managers without comparable groups", "2,803, shown separately"),
        ),
        "bottom_line": "This identifies groups for review. It is not a pay-equity finding and does not account for tenure or performance.",
    },
    "residentialdistancefrommanager": {
        "badge": "Approximate aggregate measure",
        "heading": "Postal-centroid distance, not an address",
        "summary": "The distance is calculated between the employee's and manager's postal-code centroids in the same workforce snapshot.",
        "facts": (
            ("Eligible pairs", "49,556"),
            ("Calculable distance", "42,615 pairs, or 86.0%"),
            ("Not calculable", "6,941 eligible pairs"),
            ("Not measured", "Home address, road route, travel time, or office distance"),
        ),
        "bottom_line": "Shared or nearby centroids do not prove that two people live or work in the same place.",
    },
    "highriskmanager": {
        "badge": "Aggregate historical context",
        "heading": "How to read the ratio",
        "summary": "The ratio compares observed voluntary exits with the number expected from the team's historical workforce mix.",
        "facts": (
            ("Ratio of 1", "Observed exits are close to expected exits"),
            ("Above 1", "More exits than expected; below 1 means fewer"),
            ("Coverage", "10,487 managers and 50,018 direct reports"),
            ("Insufficient history", "80 managers and 190 direct reports remain separate"),
        ),
        "bottom_line": "The ratio is not a manager ranking, performance label, or approved action threshold.",
    },
    "highturnoverunderthisperson": {
        "badge": "Aggregate historical context",
        "heading": "Team history shown as 0, 1, or 2+ exits",
        "summary": "Each active employee is placed in the bucket for their current manager's observable voluntary-exit history.",
        "facts": (
            ("Period", "Six fiscal intervals through 27-Sep-2026"),
            ("Coverage", "50,018 direct reports under 10,487 observable managers"),
            ("History unavailable", "190 direct reports under 80 managers; not assigned to zero"),
            ("Exit rule", "Distinct voluntary exits with a unique starting-team assignment"),
        ),
        "bottom_line": "The buckets describe recent team context. They do not evaluate managers or establish causation.",
    },
    "aboveaverageteamturnover": {
        "badge": "Restricted aggregate context",
        "heading": "Most employees remain Unknown",
        "summary": "The flag is calculated only when the current manager has enough observable team history.",
        "facts": (
            ("Population", "50,206 current direct reports"),
            ("Eligible history", "4,445 direct reports; 45,761 remain Unknown"),
            ("Flag rule", "Manager rate is at least 1.3 times the 9.71% benchmark"),
            ("Minimum history", "18 months, average team size of 4+, and at least 2 voluntary exits"),
        ),
        "bottom_line": "This is an experimental team-context signal, not a manager evaluation, causal claim, or production feature.",
    },
    "managerleaving": {
        "badge": "Aggregate historical exposure",
        "heading": "Use the yes/no flag",
        "summary": "The flag identifies active employees whose manager had a qualifying voluntary exit during the prior six months.",
        "facts": (
            ("Population", "50,043 active regular employees on 23-Aug-2026"),
            ("Exposed", "1.69% had at least one qualifying manager exit"),
            ("Reassignment", "The exposure remains even when the employee has a new manager"),
            ("Repeated exposure", "Too rare to publish separately, so the binary flag is preferred"),
        ),
        "bottom_line": "This measures historical exposure and is not an evaluation of the former or current manager.",
    },
    "talentindex": {
        "badge": "Aggregate stored values",
        "heading": "Latest recoverable value, not a confirmed effective date",
        "summary": "For each active employee, the chart uses the value from the highest stored talent-index cycle that can be recovered.",
        "facts": (
            ("Active workforce", "50,043 employees on 23-Aug-2026"),
            ("Value available", "39,647 employees, or 79.23%"),
            ("Unavailable", "10,396 employees"),
            ("Median and middle 50%", "56.4; range 22.7 to 67.5"),
        ),
        "bottom_line": "The chart describes stored values; it does not confirm the formula or when each value became effective.",
    },
    "majorinflectionpoints": {
        "badge": "Definition still needed",
        "heading": "Change events exist, but 'major' is undefined",
        "summary": "HRDA records manager, cost center, job family, location, and transfer changes.",
        "facts": (
            ("Observable inputs", "Five dated change-event types"),
            ("Missing rule", "What makes a change important enough to count"),
            ("Overlap issue", "Several fields may change during one reorganization"),
            ("Needed", "A time window, overlap rule, and weighting method"),
        ),
        "bottom_line": "No combined variable should be shown until the business definition is approved.",
    },
    "etfields": {
        "badge": "Support fields",
        "heading": "Hierarchy references, not career levels",
        "summary": "The ET fields appear to point to levels in an organizational hierarchy. Their acronym and business meaning are not confirmed.",
        "facts": (
            ("Date", "23-Aug-2026 workforce snapshot"),
            ("Observable fields", "ET1 through ET10"),
            ("Not publishable", "ET11"),
            ("Privacy", "Leader values and identities remain hidden"),
        ),
        "bottom_line": "Do not interpret ET1–ET11 as expert-track career levels without an approved definition.",
    },
    "transferwithinpastyear": {
        "badge": "Validated rolling measure",
        "heading": "One measure shown at two frequencies",
        "summary": "Both charts count employees with at least one documented transfer during the previous 12 months.",
        "facts": (
            ("Monthly view", "24 complete workforce snapshots; use this frequency for modeling"),
            ("Weekly view", "104 complete Sunday checkpoints; use this view for monitoring"),
            ("Average count", "About 746 employees in either view"),
            ("Source decision", "The separate IOS transfer source is not used in the primary measure"),
        ),
        "bottom_line": "Monthly and weekly results describe the same rolling definition and should not be added together.",
    },
    "location": {
        "badge": "Aggregate distribution",
        "heading": "Country is the only location field on this slide",
        "summary": "The bars show where active regular employees are located by country.",
        "facts": (
            ("Date", "23-Aug-2026"),
            ("Population", "50,033 active regular employees"),
            ("Display", "Top 20 countries plus all remaining countries"),
            ("Orange values", "Historical six-month voluntary attrition where publishable"),
        ),
        "bottom_line": "Use the next slide for office-site and city detail.",
    },
    "gender": {
        "badge": "Protected aggregate data",
        "heading": "Anonymized for fairness review",
        "summary": "The chart preserves aggregate evidence while hiding the meaning of the stored category codes.",
        "facts": (
            ("Period", "FY2020 through FY2026"),
            ("Display", "Anonymous categories only"),
            ("Minimum group size", "30 employee records"),
            ("Permitted use", "Restricted fairness review; no targeting"),
        ),
        "bottom_line": "This protected field is not intended for operational decisions about individuals.",
    },
    "engineeringvsnonengineering": {
        "badge": "Two related views",
        "heading": "The views are not interchangeable",
        "summary": "The upper chart shows the stored engineering flag. The lower chart shows a separate organization-based grouping.",
        "facts": (
            ("Stored-field population", "50,033 employees"),
            ("Organization-view population", "50,043 employees"),
            ("Difference", "The two current universes differ by 10 employees"),
            ("Pending", "The official mapping behind the stored field still needs confirmation"),
        ),
        "bottom_line": "Use each view as labeled; the organization split does not replace the stored engineering field.",
    },
    "rehire": {
        "badge": "Source definition changes over time",
        "heading": "Treat the two historical periods separately",
        "summary": "The rehire flag and the recorded rehire date do not provide the same historical coverage.",
        "facts": (
            ("Field", "is_rehire"),
            ("Related date", "rehire_date"),
            ("Source break", "23-Oct-2022"),
            ("Orange summary", "Six-month voluntary attrition for rehire and non-rehire groups"),
        ),
        "bottom_line": "Do not combine results across the source change until the two definitions are harmonized.",
    },
    "intenttostayitems": {
        "badge": "Coverage check",
        "heading": "The items are present, but meaning still needs validation",
        "summary": "The chart shows whether the relevant survey answers are available in each wave.",
        "facts": (
            ("Latest wave", "2026"),
            ("2026 coverage", "96.99%"),
            ("Items", "Q4 and Q12"),
            ("Pending", "Scale direction and an approved workforce link"),
        ),
        "bottom_line": "Coverage alone does not prove that the items are comparable or ready for attrition analysis.",
    },
    "careergoalsitem": {
        "badge": "Coverage check",
        "heading": "Coverage is not favorability",
        "summary": "The chart shows whether a career-goals response is available from 2024 onward, not whether the response is positive or negative.",
        "facts": (
            ("Latest shown wave", "2026"),
            ("2026 coverage", "89.61%"),
            ("2023 status", "Raw item exists; header mapping required"),
            ("Shown history", "2024 onward"),
        ),
        "bottom_line": "The 2023 item must be mapped before attrition processing; do not interpret response coverage as a favorable-score distribution.",
    },
    "companytenure": {
        "badge": "Two stored-date measures",
        "heading": "Original service and latest service are different",
        "summary": "The left chart starts at original hire. The right chart starts at the latest hire or rehire date.",
        "facts": (
            ("Date", "23-Aug-2026"),
            ("Population", "50,043 active regular employees"),
            ("Coverage", "Both dates are available for the full displayed population"),
            ("Bands", "The same tenure bands are used in both charts"),
        ),
        "bottom_line": "Choose the tenure definition that matches the business question; the two measures are not substitutes.",
    },
    "compensationgrade": {
        "badge": "Protected aggregate distribution",
        "heading": "Grade detail without pay values",
        "summary": "The chart shows stored compensation grades for active employees and combines small grades into Other.",
        "facts": (
            ("Date", "23-Aug-2026"),
            ("Population", "50,218 employees"),
            ("Displayed", "36 grades plus Other"),
            ("Privacy", "Nine small grades are pooled; no pay values are shown"),
        ),
        "bottom_line": "Use the chart for aggregate grade structure only.",
    },
    "colocationwithmanager": {
        "badge": "Location-field comparison",
        "heading": "A site match is not physical co-location",
        "summary": "The first chart compares office site. The second also requires the stored city to match.",
        "facts": (
            ("Office-site match", "Both employee and manager have the same nonblank office-site code"),
            ("Site and city match", "Both stored fields match"),
            ("FY2026 result", "94.01% falls to 90.09% when city is also required"),
            ("Limit", "The data does not show actual physical presence"),
        ),
        "bottom_line": "Adding city gives a stricter assigned-location comparison, not proof that two people work together in person.",
    },
    "officesiterelationshipwithmanager": {
        "badge": "Aggregate office-site comparison",
        "heading": "Assigned site relationship only",
        "summary": "Employee and manager office-site values are compared within the same monthly workforce record.",
        "facts": (
            ("Period", "11 FY2026 monthly snapshots through 23-Aug-2026"),
            ("Total", "525,633 employee-manager snapshots"),
            ("Comparable pairs", "488,355, or 92.9%"),
            ("Same site among comparable pairs", "94.01%"),
        ),
        "bottom_line": "This does not measure residential distance, travel time, time zone, or physical presence.",
    },
    "managerchange": {
        "badge": "Annual event distribution",
        "heading": "An event flag, not a lifetime count",
        "summary": "Each point shows the share and number of employee records with a manager-change event in that year.",
        "facts": (
            ("Field", "manager_change"),
            ("Coverage", "100%"),
            ("Timing", "The related date keeps the event aligned to the correct period"),
            ("Orange summary", "Six-month voluntary attrition for records with and without the flag"),
        ),
        "bottom_line": "Use the next slide when the question is how many manager changes occurred in a recent window.",
    },
}


# Literal replacements cover chart labels, tooltips, badges, and captions that
# sit outside the standard title/subtitle and side-panel structure.
PLAIN_LANGUAGE_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("Association descriptive", "Descriptive association"),
    ("Asociación descriptiva", "Descriptive association"),
    ("¿Una salida inicial precede más salidas?", "Does one team departure precede more departures?"),
    ("Cohorte índice: 29 mar 2026 · seguimiento de 6 cierres hasta 27 sep 2026 · todos los equipos", "Starting cohort: 29-Mar-2026 · six monthly checkpoints through 27-Sep-2026 · all teams"),
    ("Sensibilidad: equipos de 6+ personas", "Sensitivity check: teams with 6+ employees"),
    ("Misma cohorte y método · equipos con 6 o más integrantes al cierre índice", "Same cohort and method · teams with at least 6 employees at the starting date"),
    ("Incidencia acumulada de attrition Voluntary tras una salida inicial", "Cumulative voluntary attrition after an initial team departure"),
    ("Todos los equipos: incidencia acumulada Voluntary a seis meses para equipos expuestos y referencia ajustada", "All teams: six-month cumulative voluntary attrition for exposed and comparison teams"),
    ("Equipos de 6+ personas: incidencia acumulada Voluntary a seis meses para equipos expuestos y referencia ajustada", "Teams with 6+ employees: six-month cumulative voluntary attrition for exposed and comparison teams"),
    ("equipo tras una salida inicial única a 6 meses", "team after one initial departure"),
    ("equipos sin salida reciente, ajustados a 6 meses", "similar-size teams with no recent departure"),
    ("diferencia descriptiva al cierre de 6 meses", "descriptive difference at six months"),
    ("<strong>Lectura:</strong> se sigue a integrantes que permanecían en el equipo índice; se censuran cambio de manager, salida no Voluntary o pérdida de observación. Todos los puntos publicados tienen n en riesgo ≥ 30.", "<strong>How to read:</strong> We follow employees who remained in the starting team. Follow-up ends after a manager change, a non-voluntary exit, or loss of observation. Every published point has at least 30 employees still being followed."),
    ("%{x} meses tras el índice", "%{x} months after the starting date"),
    ("Incidencia acumulada: %{y:.2f}%", "Cumulative attrition: %{y:.2f}%"),
    ("n en riesgo: %{customdata[0]:,}", "Employees still followed: %{customdata[0]:,}"),
    ("Hazard mensual: %{customdata[1]:.2f}%", "Monthly exit rate: %{customdata[1]:.2f}%"),
    ("Salidas Voluntary: %{customdata[2]:,}", "Voluntary exits: %{customdata[2]:,}"),
    ("Equipo tras una salida inicial única", "Team after one initial departure"),
    ("Equipos sin salida reciente, ajustados", "Similar-size teams with no recent departure"),
    ("HRDA · eventos reconciliados en dos fuentes", "HRDA · events reconciled across two sources"),
    ("Meses desde la salida índice", "Months since the initial departure"),
    ("'Índice'", "'Start'"),
    ("Incidencia acumulada Voluntary", "Cumulative voluntary attrition"),
    ("Tasa anual de salida Voluntary por banda de experiencia almacenada", "Annual voluntary attrition rate by stored experience band"),
    ("Tasa anual de salida Voluntary por banda de experiencia previa", "Annual voluntary attrition rate by prior-experience band"),
    ("Tasa = salidas Voluntary atribuidas a la última banda válida previa a la terminación ÷ headcount activo mensual promedio de la banda × 100. Las barras son tasas agregadas; el detalle emergente muestra eventos y denominadores.", "Rate = voluntary exits assigned to the last valid pre-exit band divided by average monthly active headcount in that band. Bars show aggregate rates; hover details show exits and the denominator."),
    ("FY2021–FY2025 · asociación descriptiva · cinco años fiscales completos", "FY2021–FY2025 · descriptive association · five complete fiscal years"),
    ("FY2021–FY2025 · cinco años fiscales completos · asociación descriptiva", "FY2021–FY2025 · five complete fiscal years · descriptive association"),
    ("Attrition Voluntary anual por vía de entrada al grade y tenure", "Annual attrition by grade-entry path and tenure"),
    ("Attrition Voluntary anual por tenure con promoción confirmada al grade actual", "Annual voluntary attrition by tenure after a confirmed promotion into the current grade"),
    ("Attrition Voluntary anual por tenure con entrada observada sin promoción registrada", "Annual voluntary attrition by tenure after an observed grade entry without a registered promotion"),
    ("Bandas fijas: &lt;1 · 1–&lt;2 · 2–&lt;4 · 4–&lt;5 · ≥5 años. Las barras sólo aparecen cuando la celda cumple la regla de publicación.", "Fixed bands: &lt;1, 1–&lt;2, 2–&lt;4, 4–&lt;5, and 5+ years. A bar appears only when the group meets the publication rule."),
    ("Bandas fijas: &lt;2 · 2–&lt;3 · 3–&lt;4 · ≥4 años. Esta vía es un proxy observable, no una etiqueta de contratación.", "Fixed bands: &lt;2, 2–&lt;3, 3–&lt;4, and 4+ years. This is observable history, not a hiring classification."),
    ("Sin tasa publicable en FY2021–FY2025", "No publishable rate for FY2021–FY2025"),
    ("Total mostrado:", "Total shown:"),
    (
        "Limit: The annual distribution above is descriptive, not a workforce rate. It does not confirm zero applications, and the linked applicant feed is not assumed to have identical lineage or scope to the historical source.",
        "Limit: This describes linked applicants, not the full workforce. It cannot identify employees with zero applications or prove that both application sources cover the same population.",
    ),
    (
        "Window: (snapshot − 6 months, snapshot] · all four buckets have n ≥ 30 and reconcile exactly to the denominator.",
        "Window: the six months ending on the workforce date. All four displayed groups meet the minimum size and add to the full population.",
    ),
    (
        "Total shown: 50,033 . Exploratory grouping only: Onsite = 1; every other stored value, including No work arrangement, = 0. This does not change the raw field, variable definition, or assessment score.",
        "Total shown: 50,033. This exploratory view compares Onsite with every other or missing value. It does not change the source field or assessment score.",
    ),
    (
        "Total shown: 50,043 . Display-only grouping based on the documented CTO branches; same current active Regular Employee universe (50,043) with no RF360 filter. The documented leader-A branch has 0 active employees in this snapshot. The frozen upper eng_or_noneng chart remains 50,033; the current universe differs by 10. This does not replace eng_or_noneng or change the v4 score.",
        "Organization view: 50,043 active regular employees. One documented branch has no active employees. The stored-field chart covers 50,033 employees, so the totals differ by 10. Neither view replaces the other.",
    ),
    (
        "Reference score: 100 × favorable items / 33 . Each Region × wave uses its own population mean and population standard deviation; no regional labels or individual scores are displayed.",
        "Reference score: percent favorable across 33 items. Each region and survey year is centered on its own average; regional labels and individual scores are not shown.",
    ),
    (
        "Recommended use: Exclude all three from the internal baseline. The model plan permits them only as a separate external challenger after source approval, a data contract, prediction-time availability, and the required governed crosswalk are validated.",
        "Recommended use: keep all three outside the internal baseline. Test them separately only after the source, contract, workforce match, and timing are approved.",
    ),
    (
        "Total shown: 50,043 . Percent and n use 50,043 active regular employees. Depth buckets run from shallowest to deepest; rare endpoints are pooled into contiguous n ≥ 30 bands.",
        "Total shown: 50,043. Bands run from fewer to more manager links. Rare depths are combined so every displayed group has at least 30 employees.",
    ),
    (
        "68 complete monthly snapshots from 2020-07-26 through 2026-02-22. Each point uses strict term_type = 'VOLUNTARY' exits in the six months after the snapshot; pooled n counts employee-snapshot rows. Descriptive association only, not individual prediction.",
        "The trend uses 68 complete monthly workforce dates from Jul-2020 through Feb-2026. Each point measures voluntary exits during the following six months. It is descriptive, not an individual prediction.",
    ),
    (
        "Total shown: 10,487 . Plain-language reading: 1 means approximately as expected; above 1 has more exits than expected and below 1 has fewer. Each bar shows the percentage and n of observable managers; it shows no identities, rankings, or intervention threshold.",
        "Total shown: 10,487 managers. A ratio near 1 means exits were close to expected; above 1 means more and below 1 means fewer. No identities, rankings, or action threshold are shown.",
    ),
    (
        "Total shown: 50,018 . Plain-language reading: this is not an average. First, people who exited in six months are counted by team (0/1/2+); then each current direct report is shown in their team's bucket. The 2+ bucket describes historical context, not a manager evaluation or causal attribution.",
        "Total shown: 50,018 direct reports. Each person is placed in the 0, 1, or 2+ bucket for their current manager's recent team exits. The result is context, not a manager evaluation.",
    ),
    (
        "HRDA records manager, cost center, job family, location, and transfer changes. It does not define whether one event is material, whether simultaneous changes are one reorganization, or how long a change remains relevant.",
        "Five dated change types are available, but there is no approved rule for importance, overlap, or how long a change should remain relevant.",
    ),
    (
        "Total shown: 50,043 . Snapshot 2026-08-23. All dated manager-change events meeting the time-safe rule.",
        "Total shown: 50,043. Counts include manager changes dated within the stated lookback window and known by 23-Aug-2026.",
    ),
)


@dataclass(frozen=True)
class PanelAudit:
    slide_title: str
    slide_id: str
    chart_card_index: int
    metric: str
    rows: int
    rate_rows: int
    suppressed_or_unmatched_rows: int


@dataclass(frozen=True)
class CommuteBand:
    """A publishable, aggregate-only distance band for the dedicated slide."""

    category: str
    lower_km: float
    upper_km: float | None
    employee_snapshot_count: int
    average_monthly_onsite_employee_snapshots: int
    voluntary_exits: int
    attrition_rate_percent: float


@dataclass(frozen=True)
class CommuteAttritionEvidence:
    """Only the safe, presentation-ready fields used by the V4 renderer."""

    bands: tuple[CommuteBand, ...]
    baseline_employee_snapshot_count: int
    baseline_voluntary_exits: int
    baseline_attrition_rate_percent: float
    matched_distance_coverage_percent: float
    snapshot_count: int
    first_snapshot_date: str
    last_snapshot_date: str
    profile_query: str
    country_partitions_query: str
    audit_query: str
    acceptance_rule: str


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_commute_attrition_evidence(path: Path) -> CommuteAttritionEvidence:
    """Validate and reduce the commute artifact to fields safe for a shared slide.

    The source artifact documents the aggregate methodology, including hashed-query
    provenance.  The HTML renderer receives only the band label, aggregate counts,
    and rate needed for the chart; it never receives postal values, hashes, or
    employee-level fields.
    """
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("outcome") != "pass":
        raise ValueError("La evidencia de commute distance debe tener outcome pass.")
    if raw.get("deliverable_mode") != "presentation":
        raise ValueError("La evidencia de commute distance debe ser apta para presentation.")

    outcome_contract = raw.get("outcome_contract")
    if not isinstance(outcome_contract, dict):
        raise ValueError("Falta el contrato de outcome para commute distance.")
    if "ONSITE" not in str(outcome_contract.get("population", "")).upper():
        raise ValueError("La población de commute distance debe limitarse a Onsite.")
    if "VOLUNTARY" not in str(outcome_contract.get("target", "")).upper():
        raise ValueError("El outcome de commute distance debe ser Voluntary.")

    audit = raw.get("audit_metrics")
    if not isinstance(audit, dict):
        raise ValueError("Faltan métricas de auditoría para commute distance.")
    snapshot_count = int(audit.get("snapshot_count", 0))
    first_snapshot_date = str(audit.get("first_snapshot_date", ""))
    last_snapshot_date = str(audit.get("last_snapshot_date", ""))
    if (
        snapshot_count != 24
        or first_snapshot_date != MATURE_FIRST_SNAPSHOT
        or last_snapshot_date != MATURE_LAST_SNAPSHOT
    ):
        raise ValueError("La ventana de commute distance debe reconciliar 24 snapshots maduros.")

    coverage = raw.get("coverage")
    baseline = raw.get("baseline")
    if not isinstance(coverage, dict) or not isinstance(baseline, dict):
        raise ValueError("Faltan cobertura o baseline para commute distance.")
    matched_distance_coverage_percent = float(
        coverage.get("matched_distance_coverage_percent_of_eligible_onsite", -1)
    )
    if not 70 <= matched_distance_coverage_percent <= 100:
        raise ValueError("La cobertura de distancia Onsite no cumple la regla de publicación.")

    baseline_employee_snapshot_count = int(baseline.get("employee_snapshot_count", 0))
    baseline_voluntary_exits = int(baseline.get("voluntary_exits", 0))
    baseline_attrition_rate_percent = float(baseline.get("attrition_rate_percent", -1))
    if (
        baseline_employee_snapshot_count < MINIMUM_COHORT
        or baseline_voluntary_exits < MINIMUM_COHORT
        or not 0 <= baseline_attrition_rate_percent <= 100
    ):
        raise ValueError("El baseline de commute distance no es publicable.")
    calculated_baseline_rate = 100 * baseline_voluntary_exits / baseline_employee_snapshot_count
    if abs(calculated_baseline_rate - baseline_attrition_rate_percent) > 0.005:
        raise ValueError("La tasa baseline de commute distance no reconcilia con sus agregados.")

    raw_bands = raw.get("bands")
    if not isinstance(raw_bands, list) or len(raw_bands) != 31:
        raise ValueError("Commute distance debe contener exactamente las 31 bandas publicables esperadas.")
    allowed_band_fields = {
        "category",
        "lower_km",
        "upper_km",
        "employee_snapshot_count",
        "average_monthly_onsite_employee_snapshots",
        "voluntary_exits",
        "attrition_rate_percent",
        "lift_vs_matched_distance_baseline",
        "snapshot_window_count",
    }
    required_band_fields = allowed_band_fields - {"lift_vs_matched_distance_baseline"}
    bands: list[CommuteBand] = []
    seen_categories: set[str] = set()
    previous_lower = -1.0
    for index, raw_band in enumerate(raw_bands):
        if not isinstance(raw_band, dict):
            raise ValueError("Una banda de commute distance no es un objeto agregado.")
        unknown = set(raw_band).difference(allowed_band_fields)
        missing = required_band_fields.difference(raw_band)
        if unknown or missing:
            raise ValueError("La banda de commute distance contiene campos no permitidos o incompletos.")
        category = str(raw_band["category"])
        lower_km = float(raw_band["lower_km"])
        raw_upper = raw_band["upper_km"]
        upper_km = None if raw_upper is None else float(raw_upper)
        employee_snapshot_count = int(raw_band["employee_snapshot_count"])
        average_monthly_onsite_employee_snapshots = int(
            raw_band["average_monthly_onsite_employee_snapshots"]
        )
        voluntary_exits = int(raw_band["voluntary_exits"])
        attrition_rate_percent = float(raw_band["attrition_rate_percent"])
        if not category or category in seen_categories or lower_km <= previous_lower:
            raise ValueError("Las bandas de commute distance deben ser únicas y estar ordenadas.")
        if lower_km < 0 or (upper_km is not None and upper_km <= lower_km):
            raise ValueError("Los límites de distancia no son válidos.")
        if index < len(raw_bands) - 1 and upper_km is None:
            raise ValueError("Sólo la banda final puede ser abierta.")
        if (
            employee_snapshot_count < MINIMUM_COHORT
            or voluntary_exits < MINIMUM_COHORT
            or average_monthly_onsite_employee_snapshots < 1
            or not 0 <= attrition_rate_percent <= 100
        ):
            raise ValueError("Una banda de commute distance no cumple el mínimo de publicación.")
        calculated_rate = 100 * voluntary_exits / employee_snapshot_count
        if abs(calculated_rate - attrition_rate_percent) > 0.005:
            raise ValueError("Una tasa por banda de commute distance no reconcilia con sus agregados.")
        if int(raw_band["snapshot_window_count"]) != snapshot_count:
            raise ValueError("Una banda de commute distance no cubre toda la ventana de snapshots.")
        bands.append(
            CommuteBand(
                category=category,
                lower_km=lower_km,
                upper_km=upper_km,
                employee_snapshot_count=employee_snapshot_count,
                average_monthly_onsite_employee_snapshots=average_monthly_onsite_employee_snapshots,
                voluntary_exits=voluntary_exits,
                attrition_rate_percent=attrition_rate_percent,
            )
        )
        seen_categories.add(category)
        previous_lower = lower_km
    if bands[0].lower_km != 0 or bands[-1].upper_km is not None or bands[-1].category != "30+ km":
        raise ValueError("Las bandas de commute distance deben ir de 0–<1 km a 30+ km.")
    if sum(band.employee_snapshot_count for band in bands) != baseline_employee_snapshot_count:
        raise ValueError("Las exposiciones de las bandas no reconcilian con el baseline de commute distance.")
    if sum(band.voluntary_exits for band in bands) != baseline_voluntary_exits:
        raise ValueError("Las salidas de las bandas no reconcilian con el baseline de commute distance.")

    query = raw.get("query")
    if not isinstance(query, dict):
        raise ValueError("Falta la procedencia de consultas de commute distance.")
    profile_query = str(query.get("profile", ""))
    country_partitions_query = str(query.get("country_partitions", ""))
    audit_query = str(query.get("audit", ""))
    if not all((profile_query, country_partitions_query, audit_query)):
        raise ValueError("La evidencia de commute distance no conserva las tres consultas requeridas.")

    return CommuteAttritionEvidence(
        bands=tuple(bands),
        baseline_employee_snapshot_count=baseline_employee_snapshot_count,
        baseline_voluntary_exits=baseline_voluntary_exits,
        baseline_attrition_rate_percent=baseline_attrition_rate_percent,
        matched_distance_coverage_percent=matched_distance_coverage_percent,
        snapshot_count=snapshot_count,
        first_snapshot_date=first_snapshot_date,
        last_snapshot_date=last_snapshot_date,
        profile_query=profile_query,
        country_partitions_query=country_partitions_query,
        audit_query=audit_query,
        acceptance_rule=str(raw.get("acceptance_rule", "")),
    )


def find_matching_tag(text: str, tag: str, open_start: int) -> int:
    """Return the first character after the matching element opened at open_start."""
    token_pattern = re.compile(rf"</?{re.escape(tag)}\b[^>]*>", re.IGNORECASE)
    depth = 0
    for token in token_pattern.finditer(text, open_start):
        value = token.group(0)
        if value.lower().startswith("</"):
            depth -= 1
            if depth == 0:
                return token.end()
        elif not value.rstrip().endswith("/>"):
            depth += 1
    raise ValueError(f"No se encontró el cierre de <{tag}>.")


def replace_class_text(fragment: str, tag: str, class_name: str, value: str) -> str:
    """Replace the contents of one simple text element identified by class."""
    pattern = re.compile(
        rf'(<{tag}\b[^>]*\bclass="[^"]*\b{re.escape(class_name)}\b[^"]*"[^>]*>).*?(</{tag}>)',
        flags=re.I | re.S,
    )
    rendered, count = pattern.subn(lambda match: match.group(1) + esc(value) + match.group(2), fragment, count=1)
    if count != 1:
        raise ValueError(f"Could not replace {tag}.{class_name} in slide copy.")
    return rendered


def compact_source_panel(article: str) -> str:
    """Keep source traceability while removing technical prose from the main reading path."""
    source_match = re.search(
        r"<dt>(?:Data origin|Fuente)</dt><dd>(.*?)</dd>",
        article,
        flags=re.I | re.S,
    )
    table_match = re.search(
        r"<dt>(?:Table / asset|Tabla)</dt><dd>(.*?)</dd>",
        article,
        flags=re.I | re.S,
    )
    if not source_match and not table_match:
        return ""

    rows: list[str] = []
    if source_match:
        rows.append(f"<dt>Data source</dt><dd>{source_match.group(1)}</dd>")
    if table_match:
        rows.append(f"<dt>Source table or file</dt><dd>{table_match.group(1)}</dd>")
    return (
        '<section class="provenance-panel">'
        '<div class="provenance-title">Source details</div>'
        f'<dl class="provenance-grid">{"".join(rows)}</dl>'
        "</section>"
    )


def render_plain_language_panel(opening: str, original_article: str, spec: dict[str, Any]) -> str:
    facts = "".join(
        f"<li><strong>{esc(label)}:</strong> {esc(value)}</li>"
        for label, value in spec["facts"]
    )
    badge_class = str(spec.get("badge_class", "badge-info"))
    return (
        opening
        + '<div class="card-title">How to read this slide</div>'
        + f'<span class="badge {esc(badge_class)}">{esc(spec["badge"])}</span>'
        + f'<h3>{esc(spec["heading"])}</h3>'
        + f'<p>{esc(spec["summary"])}</p>'
        + f'<ul class="fact-list">{facts}</ul>'
        + f'<p class="scope-note"><strong>Bottom line:</strong> {esc(spec["bottom_line"])}</p>'
        + compact_source_panel(original_article)
        + "</article>"
    )


def replace_side_copy(stage: str, spec: dict[str, Any]) -> str:
    match = re.search(
        r'<article\b[^>]*\bclass="[^"]*\bside-copy\b[^"]*"[^>]*>',
        stage,
        flags=re.I,
    )
    if not match:
        raise ValueError(f"Slide {stage_title(stage)!r} does not contain its expected side-copy panel.")
    end = find_matching_tag(stage, "article", match.start())
    article = stage[match.start() : end]
    replacement = render_plain_language_panel(match.group(0), article, spec)
    return stage[: match.start()] + replacement + stage[end:]


def remove_side_copy_panels(stage: str) -> tuple[str, int]:
    """Remove narrative right-hand cards so the visual can use the full slide."""
    pattern = re.compile(
        r'<article\b[^>]*\bclass="[^"]*\bside-copy\b[^"]*"[^>]*>',
        flags=re.I,
    )
    removed = 0
    while match := pattern.search(stage):
        end = find_matching_tag(stage, "article", match.start())
        stage = stage[: match.start()] + stage[end:]
        removed += 1
    return stage, removed


def add_grade_tenure_empty_states(stage: str) -> str:
    """Explain the intentionally empty charts on the unpublished grade-tenure slide."""
    replacements = {
        '<div id="current-grade-entry-path-tenure-promotion-chart" class="current-grade-entry-path-tenure-chart" aria-label="Annual voluntary attrition by tenure after a confirmed promotion into the current grade"></div>': (
            '<div id="current-grade-entry-path-tenure-promotion-chart" class="current-grade-entry-path-tenure-chart" '
            'aria-label="No publishable annual attrition rate for confirmed promotion into the current grade">'
            '<div class="v5-empty-state"><strong>No chart is available</strong>'
            '<span>Historical job-profile start dates are incomplete.</span></div></div>'
        ),
        '<div id="current-grade-entry-path-tenure-observed-chart" class="current-grade-entry-path-tenure-chart" aria-label="Annual voluntary attrition by tenure after an observed grade entry without a registered promotion"></div>': (
            '<div id="current-grade-entry-path-tenure-observed-chart" class="current-grade-entry-path-tenure-chart" '
            'aria-label="No publishable annual attrition rate for observed grade entry without a registered promotion">'
            '<div class="v5-empty-state"><strong>No chart is available</strong>'
            '<span>The available history cannot support a reliable annual rate.</span></div></div>'
        ),
    }
    for old, new in replacements.items():
        if old not in stage:
            raise ValueError("No se encontró un contenedor vacío esperado en la lámina de grade-entry path.")
        stage = stage.replace(old, new, 1)
    return stage


def simplify_title_slide(stage: str) -> str:
    pattern = re.compile(r'(<div class="deck-hero"><div>\s*<h1>.*?</h1>\s*<p>).*?(</p>)', flags=re.S)
    replacement = (
        "This deck explains 44 possible inputs for an attrition model. "
        "Voluntary attrition means an employee chose to leave. Blue values show group size; "
        "orange values show the historical six-month rate when the evidence meets the publication rules."
    )
    stage, count = pattern.subn(lambda match: match.group(1) + replacement + match.group(2), stage, count=1)
    if count != 1:
        raise ValueError("Could not simplify the title-slide introduction.")
    return stage


def simplify_agenda_slide(stage: str) -> str:
    replacements = (
        ("Mobility and turnover", "Applications, mobility, and team turnover"),
        ("Source events and pending derivations.", "What employees applied for, transfers, and team exits."),
        ("Organizational context", "Workforce and organization context"),
        ("Location, job family, levels, experience, and team flag.", "Location, job family, experience, and workforce structure."),
        ("QVoice and external pull factors", "QVoice"),
        ("Survey observability and third-party sources not yet enabled.", "What the survey can support across response coverage and comparable scores."),
        ("Alternative definitions, bands, and privacy.", "Tenure, promotions, levels, and aggregate pay context."),
        ("Manager and advanced signals", "Manager context and support fields"),
        ("Coverage, attribution, and pending rules.", "Manager history, talent index, change events, and hierarchy fields."),
        ("Slides 20–28", "Slides 20–27"),
        ("Slides 29–41", "Slides 28–39"),
        ("Slides 42–52", "Slides 40–50"),
        (
            "Distribution = direct field or publishable raw domain; observability = source coverage; no chart = formula, mapping, hierarchy, or source is not yet defined.",
            "Blue shows how the population is distributed. Orange shows six-month voluntary attrition when an exact, privacy-safe rate is available. A dash means unavailable, not zero.",
        ),
    )
    for old, new in replacements:
        stage = stage.replace(old, new)
    return stage


def apply_plain_language_copy(stage: str, original_title_key: str) -> str:
    for old, new in PLAIN_LANGUAGE_REPLACEMENTS:
        stage = stage.replace(old, new)

    heading = PLAIN_LANGUAGE_HEADINGS.get(original_title_key)
    if heading is None:
        raise ValueError(f"Missing plain-language heading for slide {stage_title(stage)!r}.")
    stage = replace_class_text(stage, "h2", "slide-title-text", heading[0])
    stage = replace_class_text(stage, "p", "slide-subtitle", heading[1])

    if original_title_key == "evidencefor44attritionmodelcandidates":
        stage = simplify_title_slide(stage)
    elif original_title_key == "agenda":
        stage = simplify_agenda_slide(stage)

    return stage


def rewrite_navigation(document: str, stages: list[str]) -> str:
    """Rebuild navigation after filtering slides, with consecutive positions."""
    titles = [stage_title(stage) for stage in stages]
    sections = (
        ("Start", 0, 2),
        ("Applications, mobility, and team turnover", 2, 5),
        ("Workforce and organization context", 5, 19),
        ("QVoice", 19, 27),
        ("Career and compensation", 27, 39),
        ("Manager context and support fields", 39, 50),
    )
    if len(titles) != EXPECTED_SLIDE_COUNT:
        raise ValueError(f"La navegaciÃ³n V5 requiere {EXPECTED_SLIDE_COUNT} lÃ¡minas; recibiÃ³ {len(titles)}.")

    section_markup: list[str] = []
    for section_number, (label, start, end) in enumerate(sections, start=1):
        if start >= end or end > len(titles):
            raise ValueError(f"Rango invÃ¡lido en la secciÃ³n de navegaciÃ³n {label!r}.")
        pills = []
        for index in range(start, end):
            active = " pill-active" if index == 0 else ""
            pills.append(
                f'<button class="nav-pill{active}" data-slide="{index}">'
                f'{index + 1}. {esc(titles[index])}</button>'
            )
        range_label = str(start + 1) if end == start + 1 else f"{start + 1}–{end}"
        open_attribute = " open" if section_number == 1 else ""
        section_markup.append(
            f'<details class="nav-section" data-section="{section_number}"{open_attribute}>'
            f'<summary><span class="nav-section-title">{esc(label)}</span>'
            f'<span class="nav-section-range">{range_label}</span></summary>'
            f'<div class="nav-section-slides">{"".join(pills)}</div></details>'
        )

    nav_start = document.find('<div class="nav-ctrl" id="slide-nav">')
    if nav_start < 0:
        raise ValueError("No se encontrÃ³ la navegaciÃ³n V2.")
    nav_end = find_matching_div(document, nav_start)
    replacement = (
        '<div class="nav-ctrl" id="slide-nav">'
        '<div class="nav-tab">Slides</div>'
        '<div class="nav-panel"><div class="nav-label">Navigation</div>'
        + "".join(section_markup)
        + "</div></div>"
    )
    return document[:nav_start] + replacement + document[nav_end:]


def find_matching_div(text: str, open_start: int) -> int:
    return find_matching_tag(text, "div", open_start)


def stage_title(stage: str) -> str:
    match = re.search(r'<h2 class="slide-title-text">(.*?)</h2>', stage, flags=re.S)
    if not match:
        raise ValueError("Una lámina no tiene título visible.")
    return html.unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip()


def normal(value: object) -> str:
    """Normalize visible category labels without changing their reader-facing form."""
    text = html.unescape(str(value)).replace("Ã‚", "").replace("Â", "")
    text = (
        text.replace("–", "-")
        .replace("—", "-")
        .replace("−", "-")
        .replace("·", " ")
        .replace("â€“", "-")
        .replace("â€”", "-")
        .replace("âˆ’", "-")
        .replace("Â·", " ")
    )
    # V2 sometimes prefixes an ordinary category with an ordinal such as
    # ``1 - India``.  Do not remove the lower bound of a true range such as
    # ``6–<10 years``: its upper-bound marker is semantically material.
    text = re.sub(r"^\s*\d+\s*-\s*(?!<)", "", text)
    # Preserve inequality and open-ended band operators.  They distinguish,
    # for example, ``<1`` from exactly ``1`` and ``32+`` from exactly ``32``.
    text = text.replace("<", "lt").replace(">", "gt").replace("+", "plus")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(character for character in text if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", "", text.lower())


ONE_DECIMAL_VALUE_CLASSES = {
    "application-snapshot-bar-value",
    "entry-path-segment",
    "entry-path-total",
    "level-grade-family-legend-item",
    "level-grade-family-segment-label",
    "level-grade-family-total",
    "promotion-grade-total",
    "qvoice-favorable-value",
    "qvoice-stack-label",
    "retention-mini-value",
    "retention-theme-value",
    "trend-count",
    "trend-percent",
    "v4-inline-attrition-rate",
    "within-team-state-value",
}

ONE_DECIMAL_NARRATIVE_CLASSES = {
    "application-intensity-period-note",
    "application-intensity-publication-note",
    "application-snapshot-trend-note",
    "chart-footer",
    "commute-attrition-chart-note",
    "manager-change-comparison-note",
    "qvoice-heartbeat-intro",
    "retention-footnote",
    "transfer-footnote",
}


def format_numeric_text(value: str, *, include_plain_integers: bool) -> str:
    """Format rates to one decimal and counts as integers, preserving dates and years."""
    protected: list[str] = []

    def protect(match: re.Match[str]) -> str:
        protected.append(match.group(0))
        return f"__V5_PROTECTED_{len(protected) - 1}__"

    value = re.sub(r"\b\d{1,2}-[A-Za-z]{3}-(?:19|20)\d{2}\b", protect, value)
    value = re.sub(r"\b(?:19|20)\d{2}-\d{2}-\d{2}\b", protect, value)
    value = re.sub(r"\bFY(?:19|20)\d{2}\b", protect, value)
    value = re.sub(r"(?<![\d.])(?:19|20)\d{2}(?!\d)", protect, value)

    number_pattern = re.compile(r"(?<![A-Za-z0-9_])(?P<number>[−-]?\d[\d,]*(?:\.\d+)?)(?P<percent>%?)(?![A-Za-z0-9_])")

    def replace_number(match: re.Match[str]) -> str:
        raw = match.group("number")
        percent = match.group("percent")
        should_format = include_plain_integers or bool(percent) or "." in raw or "," in raw
        if not should_format:
            return match.group(0)
        normalized = raw.replace("−", "-").replace(",", "")
        try:
            decimals = 1 if percent or "." in raw else 0
            rendered = f"{float(normalized):,.{decimals}f}"
        except ValueError:
            return match.group(0)
        if raw.startswith("−"):
            rendered = rendered.replace("-", "−", 1)
        return rendered + percent

    value = number_pattern.sub(replace_number, value)
    for index, original in enumerate(protected):
        value = value.replace(f"__V5_PROTECTED_{index}__", original)
    return value


def format_numeric_elements(document: str) -> str:
    """Apply semantic numeric formatting to visible values without touching labels or dates."""
    opening_pattern = re.compile(r"<(?P<tag>div|span|td|small|p)\b(?P<attrs>[^>]*)>", flags=re.I)
    rendered: list[str] = []
    position = 0
    while match := opening_pattern.search(document, position):
        tag = match.group("tag").lower()
        class_match = re.search(r'\bclass="([^"]*)"', match.group("attrs"), flags=re.I)
        classes = set(class_match.group(1).split()) if class_match else set()
        is_value = (
            tag in {"td", "small"}
            or "bar-value" in classes
            or bool(classes & ONE_DECIMAL_VALUE_CLASSES)
            or any(name.endswith(("-value", "-count", "-percent", "-rate", "-total")) for name in classes)
        )
        if "v4-inline-attrition-summary-rate" in classes:
            is_value = False
        is_narrative = bool(classes & ONE_DECIMAL_NARRATIVE_CLASSES)
        if not is_value and not is_narrative:
            rendered.append(document[position : match.end()])
            position = match.end()
            continue

        end = find_matching_tag(document, tag, match.start())
        fragment = document[match.start() : end]
        fragment = re.sub(
            r"(?<=>)([^<]+)(?=<)",
            lambda text_match: format_numeric_text(
                text_match.group(1),
                include_plain_integers=is_value,
            ),
            fragment,
        )
        rendered.append(document[position : match.start()])
        rendered.append(fragment)
        position = end
    rendered.append(document[position:])
    return "".join(rendered)


def format_visible_numeric_text(document: str) -> str:
    """Normalize percentages, decimal measures, and comma-separated counts in all visible text."""
    protected_blocks: list[str] = []

    def protect_block(match: re.Match[str]) -> str:
        protected_blocks.append(match.group(0))
        return f"__V5_BLOCK_{len(protected_blocks) - 1}__"

    visible = re.sub(r"(?is)<(?:script|style)\b.*?</(?:script|style)>", protect_block, document)
    visible = re.sub(
        r"(?<=>)([^<]+)(?=<)",
        lambda match: format_numeric_text(
            match.group(1),
            include_plain_integers="%" in match.group(1),
        ),
        visible,
    )
    for index, block in enumerate(protected_blocks):
        visible = visible.replace(f"__V5_BLOCK_{index}__", block)
    return visible


def format_visible_numeric_attributes(document: str) -> str:
    """Normalize numbers exposed through titles and accessibility labels."""
    attribute_pattern = re.compile(r'\b(?P<name>title|aria-label)="(?P<value>[^"]*)"', flags=re.I)

    def replace_attribute(match: re.Match[str]) -> str:
        value = match.group("value")
        formatted = format_numeric_text(
            value,
            include_plain_integers="%" in value or "n=" in value.lower(),
        )
        return f'{match.group("name")}="{formatted}"'

    return attribute_pattern.sub(replace_attribute, document)


def format_plotly_numbers(document: str) -> str:
    """Use one decimal for rates and integer formatting for Plotly counts."""
    document = document.replace(".toFixed(2)", ".toFixed(1)")
    document = document.replace(":.2f}", ":.1f}")
    document = document.replace("tickformat: '.2f'", "tickformat: '.1f'")
    document = re.sub(
        r"(?<!tickformat: '\.1f', )ticksuffix: '%'",
        "tickformat: '.1f', ticksuffix: '%'",
        document,
    )
    return document


def format_numeric_display(document: str) -> str:
    document = format_numeric_elements(document)
    document = format_visible_numeric_text(document)
    document = format_visible_numeric_attributes(document)
    document = format_plotly_numbers(document)
    return document


def category_key(metric: str, category: object) -> str:
    """Return a conservative reconciliation key for one approved metric."""
    key = normal(category)
    aliases = {
        "sinofficesite": "noofficesite",
        "sinparofficesiteciudad": "noofficesitecitypair",
        "sinofficesitecitypair": "noofficesitecitypair",
        "sinmodalidad": "noworkarrangement",
    }
    key = aliases.get(key, key)

    if metric == "gender":
        # V2 intentionally keeps protected labels anonymous.  This mapping is
        # used only internally to attach the already-approved aggregate rate.
        return {"categorya": "f", "categoryb": "m"}.get(key, key)
    if metric == "company_tenure":
        # Units differ only by language (years / años).  Boundaries must still
        # match exactly; e.g., 2–<3 never matches the V3 2–<4 band.
        return re.sub(r"(?:years?|anos?)$", "", key)
    return key


def extract_stages(document: str) -> tuple[str, list[str], str]:
    first_stage = document.find('<div class="slide-stage"')
    nav_start = document.find('<div class="nav-ctrl" id="slide-nav">')
    if first_stage < 0 or nav_start < 0:
        raise ValueError("V2 no contiene el contrato esperado de láminas y navegación.")
    matches = list(re.finditer(r'<div class="slide-stage" id="slide-\d+"(?:\s[^>]*)?>', document))
    if not matches:
        raise ValueError("V2 no contiene láminas numeradas.")
    stages: list[str] = []
    for position, match in enumerate(matches):
        end = matches[position + 1].start() if position + 1 < len(matches) else nav_start
        stages.append(document[match.start() : end])
    return document[:first_stage], stages, document[nav_start:]


def stage_id(stage: str) -> str:
    match = re.match(r'<div class="slide-stage" id="(slide-\d+)"', stage)
    if not match:
        raise ValueError("Una lámina no tiene un ID consecutivo.")
    return match.group(1)


def article_classes(article: str) -> list[str]:
    opening = re.match(r"<article\b(?P<attrs>[^>]*)>", article, flags=re.I)
    if not opening:
        raise ValueError("No se pudo leer la apertura de una tarjeta.")
    class_match = re.search(r'\bclass="([^"]*)"', opening.group("attrs"), flags=re.I)
    return class_match.group(1).split() if class_match else []


def chart_cards(stage: str) -> list[tuple[int, int, str]]:
    cards: list[tuple[int, int, str]] = []
    pattern = re.compile(r"<article\b[^>]*>", re.I)
    position = 0
    while match := pattern.search(stage, position):
        end = find_matching_tag(stage, "article", match.start())
        fragment = stage[match.start() : end]
        if "chart-card" in article_classes(fragment):
            cards.append((match.start(), end, fragment))
        position = end
    return cards


def bar_rows(card: str) -> list[tuple[int, int, str]]:
    rows: list[tuple[int, int, str]] = []
    pattern = re.compile(r'<div\b[^>]*\bclass="[^"]*\bbar-row\b[^"]*"[^>]*>', re.I)
    position = 0
    while match := pattern.search(card, position):
        end = find_matching_div(card, match.start())
        rows.append((match.start(), end, card[match.start() : end]))
        position = end
    return rows


def visible_label(row: str) -> str:
    match = re.search(r'<div\b[^>]*\bclass="[^"]*\bbar-label\b[^"]*"[^>]*>(.*?)</div>', row, flags=re.I | re.S)
    if not match:
        raise ValueError("Una fila de barras no tiene etiqueta de categoría.")
    return html.unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip()


def evidence_index(payload: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    indexed: dict[str, dict[str, dict[str, Any]]] = {}
    for raw_row in payload["rows"]:
        row = dict(raw_row)
        metric = str(row["metric"])
        for field in ("employee_count", "employee_snapshot_count", "voluntary_exits"):
            if int(row[field]) < MINIMUM_COHORT:
                raise ValueError(f"La evidencia contiene una cohorte no publicable para {metric!r}.")
        key = category_key(metric, row["category"])
        if key in indexed.setdefault(metric, {}):
            raise ValueError(f"Categoría duplicada tras normalizar {metric!r}: {row['category']!r}.")
        indexed[metric][key] = row
    return indexed


def append_rate(row: str, rate: str | None) -> str:
    """Keep V2's value and append a positioned, compact orange rate."""
    row, class_count = re.subn(
        r'\bclass="([^"]*\bbar-row\b[^"]*)"',
        lambda match: f'class="{match.group(1)} v4-inline-attrition-row"',
        row,
        count=1,
    )
    if class_count != 1:
        raise ValueError("No se pudo marcar una fila V4 de distribución.")

    value_open = re.search(r'<div\b[^>]*\bclass="[^"]*\bbar-value\b[^"]*"[^>]*>', row, flags=re.I)
    if not value_open:
        raise ValueError("Una fila de barras no tiene valor de distribución.")
    value_end = find_matching_div(row, value_open.start())
    if rate is None:
        markup = (
            '<span class="v4-inline-attrition-rate v4-inline-attrition-unavailable" '
            'title="No publishable exact-match rate; the dash does not mean zero." '
            'aria-label="Six-month voluntary attrition rate not publishable">—</span>'
        )
    else:
        markup = (
            f'<span class="v4-inline-attrition-rate" '
            f'title="Six-month voluntary attrition: {esc(rate)}" '
            f'aria-label="Six-month voluntary attrition: {esc(rate)}">{esc(rate)}</span>'
        )
    close_start = value_end - len("</div>")
    return row[:close_start] + markup + row[close_start:]


def decorate_card(card: str, metric: str, indexed: dict[str, dict[str, dict[str, Any]]]) -> tuple[str, int, int, int]:
    if metric not in indexed:
        raise ValueError(f"No hay evidencia V3 para la métrica {metric!r}.")
    source_rows = bar_rows(card)
    if not source_rows:
        raise ValueError(f"El panel asignado a {metric!r} no tiene filas horizontales de distribución.")

    rendered: list[str] = []
    position = 0
    rate_rows = 0
    dash_rows = 0
    for start, end, source_row in source_rows:
        label = visible_label(source_row)
        evidence_row = indexed[metric].get(category_key(metric, label))
        rate = None if evidence_row is None else f"{float(evidence_row['attrition_rate_percent']):.1f}%"
        if rate is None:
            dash_rows += 1
        else:
            rate_rows += 1
        rendered.append(card[position:start])
        rendered.append(append_rate(source_row, rate))
        position = end
    rendered.append(card[position:])
    return "".join(rendered), len(source_rows), rate_rows, dash_rows


def summary_markup(spec: dict[str, Any], indexed: dict[str, dict[str, dict[str, Any]]]) -> tuple[str, int]:
    """Render approved 0/1 flag rates without relabeling vertical year bars."""
    metric = str(spec["metric"])
    if metric not in indexed:
        raise ValueError(f"No hay evidencia V3 para el resumen {metric!r}.")

    chips: list[str] = []
    for category in spec["category_order"]:
        evidence_row = indexed[metric].get(category_key(metric, category))
        if evidence_row is None:
            raise ValueError(f"Falta la categoría {category!r} para el resumen {metric!r}.")
        rate = f"{float(evidence_row['attrition_rate_percent']):.1f}%"
        chips.append(
            '<span class="v4-inline-attrition-summary-rate" '
            f'title="Six-month voluntary attrition · {esc(category)}: {esc(rate)}">'
            f'<span class="v4-inline-attrition-summary-category">{esc(category)}</span> {esc(rate)}</span>'
        )

    return (
        '<div class="v4-inline-attrition-summary" '
        'aria-label="Six-month voluntary attrition rates by flag">'
        f'<span class="v4-inline-attrition-summary-label">{esc(spec["label"])}:</span>'
        + "".join(chips)
        + "</div>",
        len(chips),
    )


def append_summary_to_card(card: str, spec: dict[str, Any], indexed: dict[str, dict[str, dict[str, Any]]]) -> tuple[str, int]:
    """Insert an attrition summary under the source card title."""
    title_open = re.search(r'<div\b[^>]*\bclass="[^"]*\bcard-title\b[^"]*"[^>]*>', card, flags=re.I)
    if not title_open:
        raise ValueError("Una tarjeta de resumen no tiene título.")
    title_end = find_matching_div(card, title_open.start())
    markup, rate_count = summary_markup(spec, indexed)
    return card[:title_end] + markup + card[title_end:], rate_count


def decorate_stage_summary(
    stage: str,
    spec: dict[str, Any],
    indexed: dict[str, dict[str, dict[str, Any]]],
) -> tuple[str, int]:
    """Apply one flag-level attrition summary to a selected V2 chart card."""
    source_cards = chart_cards(stage)
    card_index = int(spec["chart_card_index"])
    if card_index >= len(source_cards):
        raise ValueError(f"La lámina {stage_title(stage)!r} no contiene la tarjeta de resumen {card_index}.")
    start, end, source_card = source_cards[card_index]
    decorated, rate_count = append_summary_to_card(source_card, spec, indexed)
    return stage[:start] + decorated + stage[end:], rate_count


def add_stage_marker(
    stage: str,
    *,
    class_name: str = "v4-inline-attrition-marker",
    label: str = "6-MONTH VOLUNTARY ATTRITION",
    title: str = "Historical voluntary-exit rate during the six months after each workforce snapshot.",
) -> str:
    heading_start = stage.find('<div class="slide-heading">')
    if heading_start < 0:
        raise ValueError(f"La lámina {stage_title(stage)!r} no tiene encabezado V2.")
    heading_end = find_matching_div(stage, heading_start)
    marker = (
        f'<span class="{esc(class_name)}" title="{esc(title)}">{esc(label)}</span>'
    )
    close_start = heading_end - len("</div>")
    return stage[:close_start] + marker + stage[close_start:]


def decorate_stage(
    stage: str,
    panel_metrics: dict[int, str],
    indexed: dict[str, dict[str, dict[str, Any]]],
) -> tuple[str, list[PanelAudit]]:
    source_cards = chart_cards(stage)
    missing = sorted(set(panel_metrics).difference(range(len(source_cards))))
    if missing:
        raise ValueError(f"La lámina {stage_title(stage)!r} no contiene panel(es) V2 {missing}.")

    rendered: list[str] = []
    audits: list[PanelAudit] = []
    position = 0
    title = stage_title(stage)
    identifier = stage_id(stage)
    for card_index, (start, end, source_card) in enumerate(source_cards):
        rendered.append(stage[position:start])
        if card_index not in panel_metrics:
            rendered.append(source_card)
        else:
            metric = panel_metrics[card_index]
            decorated, rows, rate_rows, dash_rows = decorate_card(source_card, metric, indexed)
            rendered.append(decorated)
            audits.append(
                PanelAudit(
                    slide_title=title,
                    slide_id=identifier,
                    chart_card_index=card_index,
                    metric=metric,
                    rows=rows,
                    rate_rows=rate_rows,
                    suppressed_or_unmatched_rows=dash_rows,
                )
            )
        position = end
    rendered.append(stage[position:])
    return "".join(rendered), audits


def month_label(iso_date: str) -> str:
    """Use a compact, reader-friendly month label without exposing raw dates."""
    return date.fromisoformat(iso_date).strftime("%b-%Y")


def render_commute_attrition_stage(evidence: CommuteAttritionEvidence) -> str:
    """Replace V2 slide 19 with a dedicated, safe attrition comparison."""
    return (
        '<div class="slide-stage" id="slide-19" data-v4-commute-attrition="true" data-v5-chart-first="true">'
        '<div class="slide-heading">'
        '<div><h2 class="slide-title-text">Estimated commute distance and voluntary attrition</h2>'
        '<p class="slide-subtitle">Six-month attrition across estimated commute-distance groups for onsite employees</p></div>'
        '<span class="v4-inline-attrition-marker" '
        'title="Historical voluntary-exit rate during the six months after each workforce snapshot.">'
        '6-MONTH VOLUNTARY ATTRITION</span></div>'
        '<div class="two-pane commute-attrition-layout v5-full-width-visual">'
        '<article class="card chart-card commute-attrition-card">'
        '<div class="card-title">Six-month voluntary attrition by estimated distance</div>'
        '<div id="commute-attrition-chart" class="commute-attrition-chart" '
        'role="img" aria-label="Line chart of six-month voluntary attrition by estimated one-kilometre commute-distance band for Onsite employees."></div>'
        '<p class="commute-attrition-chart-note"><strong>Reading the chart:</strong> Each dot is a 1 km band; '
        f'the dotted line is the {evidence.baseline_attrition_rate_percent:.1f}% rate across all matched-distance Onsite observations. '
        'The final dot groups 30 km and above. Hover over a dot for its exact band and aggregate volume.</p>'
        '</article></div></div>'
    )


def render_commute_attrition_script(evidence: CommuteAttritionEvidence) -> str:
    """Create the theme-aware Plotly renderer from aggregate-only band fields."""
    rows = [
        {
            "band": band.category,
            "lower_km": band.lower_km,
            "average_monthly_onsite_population": band.average_monthly_onsite_employee_snapshots,
            "voluntary_exits": band.voluntary_exits,
            "attrition_rate_percent": band.attrition_rate_percent,
        }
        for band in evidence.bands
    ]
    rows_json = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    baseline_json = json.dumps(evidence.baseline_attrition_rate_percent)
    script = r'''
  <script>
    (function () {
      var rows = __COMMUTE_ROWS__;
      var baseline = __COMMUTE_BASELINE__;
      var chart = document.getElementById('commute-attrition-chart');
      var stage = document.getElementById('slide-19');

      function isVisible() {
        return Boolean(stage) && window.getComputedStyle(stage).display !== 'none';
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

      function renderCommuteAttritionChart() {
        if (!chart || !isVisible()) return;
        if (!window.Plotly) {
          chart.innerHTML = '<p class="commute-attrition-fallback"><strong>Chart unavailable.</strong> '
            + 'The published overall six-month voluntary attrition rate is ' + baseline.toFixed(1) + '%.</p>';
          return;
        }
        var colors = themeColors();
        var trace = {
          x: rows.map(function (row) { return row.lower_km; }),
          y: rows.map(function (row) { return row.attrition_rate_percent; }),
          customdata: rows.map(function (row) {
            return [row.band, row.average_monthly_onsite_population, row.voluntary_exits];
          }),
          mode: 'lines+markers',
          type: 'scatter',
          name: 'Voluntary attrition',
          line: { color: colors.accent, width: 3 },
          marker: { color: colors.accent, size: 7, line: { color: colors.surface, width: 1 } },
          hovertemplate: '<b>%{customdata[0]}</b><br>Six-month voluntary attrition: <b>%{y:.1f}%</b>'
            + '<br>Average Onsite population per month: %{customdata[1]:,.0f}'
            + '<br>Voluntary exits: %{customdata[2]:,.0f}<extra></extra>'
        };
        Plotly.react(chart, [trace], {
          height: 570,
          plot_bgcolor: 'rgba(0,0,0,0)',
          paper_bgcolor: 'rgba(0,0,0,0)',
          font: { family: colors.font, color: colors.text },
          hoverlabel: { font: { family: colors.font }, bgcolor: colors.surface, bordercolor: colors.border },
          margin: { t: 22, r: 18, b: 52, l: 58 },
          showlegend: false,
          shapes: [{
            type: 'line', xref: 'paper', x0: 0, x1: 1, yref: 'y', y0: baseline, y1: baseline,
            line: { color: colors.muted, width: 1.5, dash: 'dot' }
          }],
          annotations: [{
            xref: 'paper', x: 0.99, yref: 'y', y: baseline, yshift: 8, xanchor: 'right',
            text: 'Overall rate ' + baseline.toFixed(1) + '%', showarrow: false,
            font: { family: colors.font, size: 10, color: colors.muted },
            bgcolor: 'rgba(0,0,0,0)'
          }],
          xaxis: {
            title: { text: 'Estimated straight-line distance band', font: { family: colors.font, size: 11, color: colors.muted } },
            range: [-0.5, 30.5], tickvals: [0, 5, 10, 15, 20, 25, 30],
            ticktext: ['0–<1', '5–<6', '10–<11', '15–<16', '20–<21', '25–<26', '30+'],
            tickfont: { family: colors.font, size: 10, color: colors.muted },
            showgrid: false, zeroline: false, fixedrange: true
          },
          yaxis: {
            title: { text: 'Six-month attrition', font: { family: colors.font, size: 11, color: colors.muted } },
            range: [0, 4.6], tickvals: [0, 1, 2, 3, 4], tickformat: '.1f', ticksuffix: '%',
            tickfont: { family: colors.font, size: 10, color: colors.muted },
            gridcolor: colors.border, zerolinecolor: colors.border, fixedrange: true
          }
        }, { responsive: false, displayModeBar: false });
      }

      function scheduleRender() {
        window.requestAnimationFrame(function () {
          window.requestAnimationFrame(renderCommuteAttritionChart);
        });
      }

      if (stage) {
        new MutationObserver(function (records) {
          if (records.some(function (record) { return record.attributeName === 'style'; })) scheduleRender();
        }).observe(stage, { attributes: true, attributeFilter: ['style'] });
      }
      new MutationObserver(function (records) {
        if (records.some(function (record) { return record.attributeName === 'class'; })) scheduleRender();
      }).observe(document.body, { attributes: true, attributeFilter: ['class'] });
      if (isVisible()) scheduleRender();
    })();
  </script>
'''
    return script.replace("__COMMUTE_ROWS__", rows_json).replace("__COMMUTE_BASELINE__", baseline_json)


V4_CSS = r"""
    /* V4: compact six-month attrition values inline with V2 distributions. */
    .v4-inline-attrition-marker { display:inline-flex; align-items:center; flex:0 0 auto; min-height:22px; margin-left:12px; padding:3px 8px; border:1px solid color-mix(in oklab,#f97316 34%,var(--border-subtle)); border-radius:var(--radius-pill); background:color-mix(in oklab,#f97316 14%,transparent); color:#c2410c; font-size:10px; font-weight:800; letter-spacing:.07em; line-height:1; white-space:nowrap; }
    .v4-inline-attrition-unavailable-marker { display:inline-flex; align-items:center; flex:0 0 auto; min-height:22px; margin-left:12px; padding:3px 8px; border:1px solid var(--border-subtle); border-radius:var(--radius-pill); background:color-mix(in oklab,var(--text-muted) 9%,transparent); color:var(--text-muted); font-size:10px; font-weight:800; letter-spacing:.06em; line-height:1; white-space:nowrap; }
    .v4-inline-attrition-row { position:relative; min-width:0; padding-right:60px; }
    .v4-inline-attrition-rate { position:absolute; top:50%; right:0; min-width:54px; transform:translateY(-50%); color:#c2410c; font:inherit; font-weight:800; font-variant-numeric:tabular-nums; line-height:1; text-align:right; white-space:nowrap; }
    .v4-inline-attrition-unavailable { color:var(--text-muted); font-weight:700; }
    .v4-inline-attrition-summary { display:flex; align-items:center; flex-wrap:wrap; gap:4px 7px; margin:1px 0 2px; color:#c2410c; font-size:10px; font-weight:800; line-height:1.2; font-variant-numeric:tabular-nums; }
    .v4-inline-attrition-summary-label { color:#c2410c; letter-spacing:.04em; text-transform:uppercase; white-space:nowrap; }
    .v4-inline-attrition-summary-rate { display:inline-flex; align-items:baseline; gap:3px; padding:2px 5px; border:1px solid color-mix(in oklab,#f97316 30%,var(--border-subtle)); border-radius:var(--radius-pill); background:color-mix(in oklab,#f97316 12%,transparent); color:#c2410c; white-space:nowrap; }
    .v4-inline-attrition-summary-category { color:var(--text-main); font-weight:700; }
    body.theme-dark-royal .v4-inline-attrition-marker, body.theme-dark-carbon .v4-inline-attrition-marker, body.theme-dark-royal .v4-inline-attrition-rate, body.theme-dark-carbon .v4-inline-attrition-rate { color:#fdba74; }
    body.theme-dark-royal .v4-inline-attrition-summary, body.theme-dark-carbon .v4-inline-attrition-summary, body.theme-dark-royal .v4-inline-attrition-summary-label, body.theme-dark-carbon .v4-inline-attrition-summary-label, body.theme-dark-royal .v4-inline-attrition-summary-rate, body.theme-dark-carbon .v4-inline-attrition-summary-rate { color:#fdba74; }
    .location-card .v4-inline-attrition-row, .job-family-card .v4-inline-attrition-row, .labor-market-card .v4-inline-attrition-row, .region-display-stack .v4-inline-attrition-row { padding-right:52px; }
    .location-card .v4-inline-attrition-rate, .job-family-card .v4-inline-attrition-rate, .labor-market-card .v4-inline-attrition-rate, .region-display-stack .v4-inline-attrition-rate { min-width:47px; }
    .prior-experience-card .v4-inline-attrition-row, .compensation-grade-card .v4-inline-attrition-row, .level-support-card .v4-inline-attrition-row { padding-right:50px; }
    .prior-experience-card .v4-inline-attrition-rate, .compensation-grade-card .v4-inline-attrition-rate, .level-support-card .v4-inline-attrition-rate { min-width:45px; }
    #slide-40 .within-team-compensation-stack { display:grid; grid-template-rows:minmax(0,1fr) minmax(0,1fr) auto; gap:8px; min-height:0; overflow:hidden; }
    #slide-40 .within-team-compensation-stack > .card { height:auto; min-height:0; padding:10px 12px; gap:5px; }
    #slide-40 .within-team-compensation-stack .bar-list { gap:4px; }
    #slide-40 .within-team-compensation-stack .bar-row { min-height:20px; }
    #slide-40 .within-team-compensation-stack .chart-footer { margin-top:auto; padding-top:5px; font-size:10px; line-height:1.2; }
    #slide-40 .within-team-state-card { display:grid; grid-template-columns:auto 1fr; align-items:center; gap:10px; }
    #slide-40 .within-team-state-card .card-title { grid-column:1 / -1; }
    #slide-40 .within-team-state-card p { margin:0; font-size:11px; line-height:1.25; }
    #slide-19 .commute-attrition-card { padding:12px 14px; gap:7px; }
    #slide-19 .commute-attrition-card .card-title { margin-bottom:0; padding-bottom:4px; }
    #slide-19 .commute-attrition-chart { width:100%; height:570px; flex:0 0 570px; min-height:570px; }
    #slide-19 .commute-attrition-chart-note { margin:0; padding-top:1px; color:var(--text-muted); font-size:11px; line-height:1.32; }
    #slide-19 .commute-attrition-fallback { margin:auto 8px; color:var(--text-main); font-size:14px; line-height:1.45; }
    #slide-19 .commute-attrition-side-copy { gap:8px; }
    #slide-19 .commute-attrition-side-copy .fact-list { gap:5px; }
    #slide-19 .commute-attrition-side-copy .scope-note { margin-top:2px; }
    @media (max-width:900px) { .v4-inline-attrition-marker, .v4-inline-attrition-unavailable-marker { display:none; } }
"""


V5_CSS = r"""
    /* V5: chart-first layout. Narrative side cards are removed from the HTML. */
    .slide-subtitle { font-size:14px; line-height:1.3; }
    .two-pane,
    .prior-experience-annual-layout,
    .commute-attrition-layout,
    .current-grade-entry-path-tenure-layout {
      grid-template-columns:minmax(0,1fr);
      gap:0;
    }
    .two-pane > :only-child,
    .current-grade-entry-path-tenure-layout > :only-child { width:100%; min-width:0; }
    .two-pane > .chart-card .bar-list { flex:1; justify-content:space-evenly; }
    .side-copy { display:none !important; }
    #slide-19 .commute-attrition-chart { height:620px; flex-basis:620px; min-height:620px; }
    #slide-19 .commute-attrition-chart-note { font-size:12px; }
"""


def inject_v4_css(document: str) -> str:
    marker = "    /* 13. CONTENT-SPECIFIC STYLES"
    position = document.find(marker)
    if position < 0:
        raise ValueError("La fuente V2 no conserva el bloque de estilos específicos.")
    style_end = document.find("</style>", position)
    if style_end < 0:
        raise ValueError("La fuente V2 no tiene cierre de estilos.")
    return document[:style_end] + "\n" + V4_CSS + "\n" + V5_CSS + "\n" + document[style_end:]


def inject_commute_attrition_script(document: str, evidence: CommuteAttritionEvidence) -> str:
    """Place the chart renderer after V2's navigation and theme scripts."""
    if 'src="https://cdn.plot.ly/plotly-2.27.0.min.js"' not in document:
        raise ValueError("V2 no conserva Plotly, requerido para la gráfica de commute distance.")
    body_end = document.rfind("</body>")
    if body_end < 0:
        raise ValueError("La fuente V2 no tiene cierre de body para el renderer de commute distance.")
    return document[:body_end] + render_commute_attrition_script(evidence) + document[body_end:]


def validate_output(
    document: str,
    source: str,
    audits: list[PanelAudit],
    summary_rate_count: int,
    available_stage_ids: set[str],
    unavailable_stage_ids: set[str],
    excluded_stage_ids: set[str],
    commute_evidence: CommuteAttritionEvidence,
    removed_side_panels: int,
) -> None:
    source_ids = re.findall(r'<div class="slide-stage"[^>]*\bid="(slide-\d+)"', source)
    output_ids = re.findall(r'<div class="slide-stage"[^>]*\bid="(slide-\d+)"', document)
    expected_ids = [identifier for identifier in source_ids if identifier not in excluded_stage_ids]
    if output_ids != expected_ids or len(output_ids) != EXPECTED_SLIDE_COUNT:
        raise ValueError(
            f"V5 debe conservar {EXPECTED_SLIDE_COUNT} láminas en orden y omitir sólo las fuentes externas o gráficas vacías."
        )
    if len(excluded_stage_ids) != len(EXCLUDED_SLIDES):
        raise ValueError("V5 no omitió exactamente las láminas configuradas.")

    def nav_ids(value: str) -> list[str]:
        nav_start = value.find('<div class="nav-ctrl" id="slide-nav">')
        nav_end = value.find('<div class="side-controls" id="theme-selector">', nav_start)
        if nav_start < 0 or nav_end < 0:
            raise ValueError("Falta la navegación o el selector de tema requerido.")
        return re.findall(r'<button class="nav-pill(?: pill-active)?" data-slide="(\d+)"', value[nav_start:nav_end])

    expected_nav_ids = [str(index) for index in range(EXPECTED_SLIDE_COUNT)]
    if nav_ids(document) != expected_nav_ids:
        raise ValueError("La navegación V5 debe usar índices consecutivos de 0 a 49.")
    _, rendered_stages, _ = extract_stages(document)
    commute_stages = [stage for stage in rendered_stages if stage_id(stage) == "slide-19"]
    if len(commute_stages) != 1:
        raise ValueError("V5 debe conservar una única lámina slide-19.")
    commute_stage = commute_stages[0]
    if "data-v4-commute-attrition=\"true\"" not in commute_stage:
        raise ValueError("La lámina de commute distance no fue reemplazada por su vista de attrition.")
    if "commute-distance-comparison-card" in commute_stage:
        raise ValueError("La distribución V2 de commute distance no debe coexistir con la vista de attrition.")
    if stage_title(commute_stage) != "Estimated commute distance and voluntary attrition":
        raise ValueError("La lámina de commute distance no tiene el título explicativo esperado.")
    if commute_stage.count('id="commute-attrition-chart"') != 1:
        raise ValueError("La lámina de commute distance no tiene exactamente una gráfica de attrition.")
    if f"{commute_evidence.baseline_attrition_rate_percent:.1f}%" not in commute_stage:
        raise ValueError("La lámina de commute distance no muestra la tasa baseline.")
    if 'var rows = ' not in document or 'renderCommuteAttritionChart' not in document:
        raise ValueError("Falta el renderer Plotly de commute distance.")
    expected_panels = sum(len(panels) for panels in PANEL_METRICS.values())
    if len(audits) != expected_panels:
        raise ValueError(f"V5 debe actualizar {expected_panels} paneles horizontales; se actualizaron {len(audits)}.")
    def rendered_class_count(class_name: str) -> int:
        return sum(
            class_name in match.group(1).split()
            for match in re.finditer(r'\bclass="([^"]*)"', document, flags=re.I)
        )

    expected_rows = sum(audit.rows for audit in audits)
    if rendered_class_count("v4-inline-attrition-row") != expected_rows:
        raise ValueError("No todas las filas de los paneles V5 recibieron una celda de attrition.")
    if rendered_class_count("v4-inline-attrition-rate") != expected_rows:
        raise ValueError("No todas las filas V5 tienen tasa o guion de attrition.")
    if rendered_class_count("v4-inline-attrition-marker") != len(available_stage_ids):
        raise ValueError("Cada lámina modificada debe tener un único marcador naranja de attrition.")
    if rendered_class_count("v4-inline-attrition-summary") != len(SUMMARY_METRICS):
        raise ValueError("Falta un resumen de attrition para un gráfico vertical elegible.")
    if rendered_class_count("v4-inline-attrition-summary-rate") != summary_rate_count:
        raise ValueError("Las tasas de los resúmenes verticales no reconcilian.")
    if rendered_class_count("v4-inline-attrition-unavailable-marker") != len(unavailable_stage_ids):
        raise ValueError("Las láminas sin tasa aprobada no tienen su marca de disponibilidad.")
    if "v3-rate-" in document or "v3-companion" in document:
        raise ValueError("V5 no debe heredar gráficos o estilos compañeros de V3.")
    if removed_side_panels != EXPECTED_REMOVED_RIGHT_PANELS:
        raise ValueError(
            f"V5 debía retirar {EXPECTED_REMOVED_RIGHT_PANELS} paneles laterales de las láminas conservadas; "
            f"retiró {removed_side_panels}."
        )
    if re.search(r'<article\b[^>]*\bclass="[^"]*\bside-copy\b', document, flags=re.I):
        raise ValueError("V5 todavía contiene un panel narrativo lateral.")
    if ".toFixed(2)" in document or ":.2f}" in document:
        raise ValueError("V5 conserva porcentajes o tasas de gráfico con más de un decimal.")
    if "minimumFractionDigits: 1" in document or re.search(r"customdata\[[012]\]:,\.1f", document):
        raise ValueError("V5 conserva conteos de Plotly con decimales.")
    display_scope = re.sub(r"(?is)<(?:script|style)\b.*?</(?:script|style)>", " ", document)
    visible_text = html.unescape(re.sub(r"<[^>]+>", " ", display_scope))
    attribute_text = " ".join(
        html.unescape(match.group(1))
        for match in re.finditer(r'(?:title|aria-label)="([^"]*)"', display_scope, flags=re.I)
    )
    for label, value in (("texto visible", visible_text), ("atributos visibles", attribute_text)):
        percentages = re.findall(r"(?<![\d.])\d+(?:\.\d+)?%", value)
        invalid_percentages = [token for token in percentages if not re.fullmatch(r"\d+\.\d%", token)]
        if invalid_percentages:
            raise ValueError(f"V5 conserva porcentajes sin exactamente un decimal en {label}: {invalid_percentages[:5]}.")
        count_decimal_patterns = (
            r"\bn\s*=\s*\d[\d,]*\.\d+",
            r"[·/]\s*(?:n\s*=\s*)?\d[\d,]*\.\d+(?!%)",
            r"\d[\d,]*\.\d+\s+(?:employees|employee-snapshots|respondents|cases|managers|exits|applicants|reports|teams|records)\b",
            r"Total shown:\s*\d[\d,]*\.\d+",
        )
        if any(re.search(pattern, value, flags=re.I) for pattern in count_decimal_patterns):
            raise ValueError(f"V5 conserva al menos un conteo con decimales en {label}.")
    if "v5-empty-state" in document or "No chart is available" in document:
        raise ValueError("V5 todavía contiene un aviso de gráfica vacía.")
    rendered_titles = {stage_title(stage) for stage in rendered_stages}
    if {"External pull factors", "Annual attrition by grade-entry path and tenure"} & rendered_titles:
        raise ValueError("V5 todavía contiene una lámina excluida.")
    if "grid-template-columns:minmax(0,1fr);" not in document:
        raise ValueError("V5 no contiene la regla de visualización a ancho completo.")
    if '<div class="side-controls" id="theme-selector">' not in document:
        raise ValueError("V5 no conserva el selector de temas requerido.")
    if '<div class="nav-ctrl" id="slide-nav">' not in document:
        raise ValueError("V5 no conserva la navegación requerida.")
    if '<div class="nav-tab">Slides</div>' not in document:
        raise ValueError("V5 no conserva la pestaña lateral de navegación.")


def build(overwrite: bool) -> None:
    required = (V2, V3, V4, V2_MANIFEST, EVIDENCE, COMMUTE_EVIDENCE, TEMPLATE)
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Faltan insumos V5: " + ", ".join(missing))
    if TARGET.exists() and not overwrite:
        raise FileExistsError(f"Ya existe {TARGET}; use --overwrite únicamente para regenerar V5.")

    # The HTML skill requires the canonical template to be the initial output
    # artifact.  The V2 deck is layered only after the template contract is
    # copied and checked.
    OUT.mkdir(parents=True, exist_ok=True)
    temporary_target = TARGET.with_name(TARGET.name + ".tmp")
    shutil.copyfile(TEMPLATE, temporary_target)
    copied_template = temporary_target.read_text(encoding="utf-8")
    if '<div class="side-controls" id="theme-selector">' not in copied_template:
        raise ValueError("La plantilla fullscreen no conserva el selector de temas.")

    v2_before = sha256(V2)
    v3_before = sha256(V3)
    v4_before = sha256(V4)
    evidence_hash = sha256(EVIDENCE)
    commute_evidence_hash = sha256(COMMUTE_EVIDENCE)
    source = V2.read_text(encoding="utf-8")
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    commute_evidence = load_commute_attrition_evidence(COMMUTE_EVIDENCE)
    if evidence.get("deliverable_mode") != "internal_analysis" or evidence.get("outcome") != "pass":
        raise ValueError("La evidencia V3 debe ser internal_analysis y outcome pass.")
    if evidence.get("row_count") != len(evidence.get("rows", [])):
        raise ValueError("La evidencia V3 no reconcilia su número de filas.")

    indexed = evidence_index(evidence)
    prefix, source_stages, suffix = extract_stages(source)
    modified_stages: list[str] = []
    audits: list[PanelAudit] = []
    summary_rate_count = 0
    configured_slides: set[str] = set()
    available_stage_ids: set[str] = set()
    unavailable_stage_ids: set[str] = set()
    excluded_stage_ids: set[str] = set()
    excluded_stage_titles: list[str] = []
    removed_side_panels = 0
    for stage in source_stages:
        title_key = normal(stage_title(stage))
        if title_key in EXCLUDED_SLIDES:
            excluded_stage_ids.add(stage_id(stage))
            excluded_stage_titles.append(stage_title(stage))
            continue
        panel_metrics = PANEL_METRICS.get(title_key, {})
        summary_spec = SUMMARY_METRICS.get(title_key)
        unavailable_reason = UNAVAILABLE_ATTRITION_SLIDES.get(title_key)
        decorated = stage

        if title_key == "commutedistance":
            if stage_id(stage) != "slide-19":
                raise ValueError("Commute distance debe conservar el ID slide-19.")
            source_side_panels = len(
                re.findall(r'<article\b[^>]*\bclass="[^"]*\bside-copy\b[^"]*"[^>]*>', stage, flags=re.I)
            )
            if source_side_panels != 1:
                raise ValueError("La lámina de commute distance debe contener un panel lateral de origen.")
            removed_side_panels += source_side_panels
            decorated = render_commute_attrition_stage(commute_evidence)
            available_stage_ids.add(stage_id(decorated))
            modified_stages.append(decorated)
            continue

        if panel_metrics:
            decorated, stage_audits = decorate_stage(decorated, panel_metrics, indexed)
            audits.extend(stage_audits)
            configured_slides.add(title_key)

        if summary_spec is not None:
            decorated, stage_summary_rate_count = decorate_stage_summary(decorated, summary_spec, indexed)
            summary_rate_count += stage_summary_rate_count

        if panel_metrics or summary_spec is not None:
            decorated = add_stage_marker(decorated)
            available_stage_ids.add(stage_id(decorated))
        elif unavailable_reason is not None:
            decorated = add_stage_marker(
                decorated,
                class_name="v4-inline-attrition-unavailable-marker",
                label="6-MONTH ATTRITION · NOT AVAILABLE",
                title=unavailable_reason,
            )
            unavailable_stage_ids.add(stage_id(decorated))

        decorated = apply_plain_language_copy(decorated, title_key)
        decorated, removed = remove_side_copy_panels(decorated)
        removed_side_panels += removed
        modified_stages.append(decorated)

    expected_slides = set(PANEL_METRICS)
    if configured_slides != expected_slides:
        raise ValueError(f"No se localizaron todas las láminas V2 configuradas: {sorted(expected_slides - configured_slides)}.")
    if "slide-19" not in available_stage_ids:
        raise ValueError("No se localizó la lámina de commute distance para su vista de attrition.")

    document = prefix + "\n\n  " + "\n\n  ".join(modified_stages) + "\n\n  " + suffix
    document = rewrite_navigation(document, modified_stages)
    document = inject_v4_css(document)
    document = inject_commute_attrition_script(document, commute_evidence)
    document = format_numeric_display(document)
    document, title_count = re.subn(
        r"<title>.*?</title>",
        "<title>Evidence for 44 attrition model candidates · V5</title>",
        document,
        count=1,
        flags=re.S,
    )
    if title_count != 1:
        raise ValueError("No se pudo actualizar el título del documento V5.")
    validate_output(
        document,
        source,
        audits,
        summary_rate_count,
        available_stage_ids,
        unavailable_stage_ids,
        excluded_stage_ids,
        commute_evidence,
        removed_side_panels,
    )
    temporary_target.write_text(document, encoding="utf-8")
    temporary_target.replace(TARGET)

    if sha256(V2) != v2_before:
        raise ValueError("V2 cambió durante la generación de V5.")
    if sha256(V3) != v3_before:
        raise ValueError("V3 cambió durante la generación de V5.")
    if sha256(V4) != v4_before:
        raise ValueError("V4 cambió durante la generación de V5.")

    manifest = {
        "version": 5,
        "generated_on": date.today().isoformat(),
        "deliverable_mode": "presentation",
        "objective": (
            "Crear una versión visual V5 de la presentación: retirar los paneles narrativos derechos, "
            "ampliar los gráficos, resumir cada lámina en un subtítulo breve y mostrar las métricas "
            "con porcentajes y tasas a un decimal y conteos enteros. También se omiten las láminas "
            "de fuentes externas no habilitadas y de gráficas vacías, sin cambiar la evidencia agregada "
            "ni generar predicciones individuales."
        ),
        "source_deck": {
            "path": str(V2.relative_to(ROOT)).replace("\\", "/"),
            "sha256": v2_before,
            "preserved": True,
        },
        "v3_preserved": {"path": str(V3.relative_to(ROOT)).replace("\\", "/"), "sha256": v3_before},
        "v4_reference": {"path": str(V4.relative_to(ROOT)).replace("\\", "/"), "sha256": v4_before, "preserved": True},
        "base_template": str(TEMPLATE),
        "six_month_evidence": {
            "path": str(EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": evidence_hash,
            "query": evidence.get("query"),
            "history": f"24 snapshots maduros: {MATURE_FIRST_SNAPSHOT} a {MATURE_LAST_SNAPSHOT}",
            "outcome": evidence.get("outcome"),
            "publication_rule": evidence.get("publication_rule"),
        },
        "commute_distance_attrition": {
            "path": str(COMMUTE_EVIDENCE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": commute_evidence_hash,
            "deliverable_mode": "presentation",
            "slide_id": "slide-19",
            "visual": "Gráfica dedicada de línea con 31 bandas de 1 km y baseline punteado; no es un overlay de la distribución V2.",
            "population": "Employee-snapshots de empleados regulares activos con work_arrangement=ONSITE y distancia calculable.",
            "history": f"{commute_evidence.snapshot_count} snapshots mensuales: {commute_evidence.first_snapshot_date} a {commute_evidence.last_snapshot_date}",
            "distance_coverage_percent": commute_evidence.matched_distance_coverage_percent,
            "baseline": {
                "employee_snapshot_count": commute_evidence.baseline_employee_snapshot_count,
                "voluntary_exits": commute_evidence.baseline_voluntary_exits,
                "attrition_rate_percent": commute_evidence.baseline_attrition_rate_percent,
            },
            "published_bands": len(commute_evidence.bands),
            "publication_rule": commute_evidence.acceptance_rule,
            "query_provenance": {
                "profile": commute_evidence.profile_query,
                "country_partitions": commute_evidence.country_partitions_query,
                "audit": commute_evidence.audit_query,
            },
            "limitations": "Proxy geográfico por centroides; no mide ruta, tiempo de traslado ni commute observado. La asociación es descriptiva, no causal ni predictiva a nivel individual.",
        },
        "visual_rule": {
            "layout": "Se eliminan los 47 paneles narrativos derechos de las láminas conservadas y el contenido visual ocupa todo el ancho disponible.",
            "subtitle": "Cada lámina usa un resumen breve y no técnico que explica qué muestra el visual.",
            "numeric_format": "Los porcentajes y las tasas visibles se muestran con un decimal; los conteos se muestran como enteros. Fechas, años, categorías e identificadores conservan su formato natural.",
            "distribution": "Se conserva el valor de distribución y las barras azules.",
            "attrition": "Se conserva la tasa porcentual naranja a la derecha.",
            "vertical_or_annual": "Las tasas aprobadas por flag se muestran como resumen naranja, sin atribuirlas erróneamente a barras anuales.",
            "commute_distance": "La lámina 19 reemplaza la comparación de distribución V2 por tasas de attrition Voluntary de seis meses en bandas Onsite de 1 km, con baseline punteado.",
            "unavailable": "— indica que no existe tasa publicable o reconciliable; no equivale a cero.",
            "unavailable_marker": "Las visualizaciones sin join temporal o definición aprobada muestran una marca neutral de no estimable, sin inventar tasas.",
            "excluded": "Se retiran las láminas de fuentes externas no habilitadas y de gráficas vacías. No hay nuevas láminas, lift, causalidad ni predicciones individuales.",
        },
        "excluded_slides": [
            {"slide_id": identifier, "title": title, "reason": EXCLUDED_SLIDES[normal(title)]}
            for identifier, title in zip(sorted(excluded_stage_ids, key=lambda value: int(value.split("-")[1])), excluded_stage_titles)
        ],
        "panel_audits": [asdict(audit) for audit in audits],
        "summary": {
            "slides": EXPECTED_SLIDE_COUNT,
            "modified_slides": len(available_stage_ids | unavailable_stage_ids),
            "slides_with_publishable_attrition": len(available_stage_ids),
            "slides_marked_no_estimate": len(unavailable_stage_ids),
            "modified_horizontal_panels": len(audits),
            "inline_rows": sum(audit.rows for audit in audits),
            "inline_rates": sum(audit.rate_rows for audit in audits) + summary_rate_count,
            "summary_rates": summary_rate_count,
            "inline_dashes": sum(audit.suppressed_or_unmatched_rows for audit in audits),
            "dedicated_attrition_charts": 1,
            "dedicated_commute_distance_bands": len(commute_evidence.bands),
            "removed_right_panels": removed_side_panels,
        },
        "privacy": {
            "minimum_distinct_employee_cohort": MINIMUM_COHORT,
            "minimum_employee_snapshot_exposure": MINIMUM_COHORT,
            "minimum_voluntary_events": MINIMUM_COHORT,
            "prohibited": ["employee rows", "IDs", "names", "emails", "addresses", "free text", "exact compensation"],
        },
        "validation": {
            "v2_unchanged_sha256": v2_before,
            "v3_unchanged_sha256": v3_before,
            "v4_unchanged_sha256": v4_before,
            "stage_count": EXPECTED_SLIDE_COUNT,
            "new_slides": 0,
            "removed_slides": len(excluded_stage_ids),
            "removed_right_panels": removed_side_panels,
            "percentage_decimals": 1,
            "count_decimals": 0,
            "commute_distance_band_count": len(commute_evidence.bands),
            "commute_distance_outcome": "pass",
            "outcome": "pass",
        },
    }
    manifest["visual_rule"]["layout"] = (
        f"Se eliminan los {removed_side_panels} paneles narrativos derechos de las laminas conservadas "
        "y el contenido visual ocupa todo el ancho disponible."
    )
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(TARGET)
    print(MANIFEST)
    print(
        f"slides={EXPECTED_SLIDE_COUNT}; removed_slides={len(excluded_stage_ids)}; "
        f"modified_slides={len(available_stage_ids | unavailable_stage_ids)}; "
        f"panels={len(audits)}; removed_side_panels={removed_side_panels}; rows={sum(audit.rows for audit in audits)}; "
        f"summary_rates={summary_rate_count}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Construye V5: deck visual sin paneles laterales, porcentajes a un decimal y conteos enteros."
    )
    parser.add_argument("--overwrite", action="store_true", help="Permite regenerar la salida V5 existente.")
    build(parser.parse_args().overwrite)
