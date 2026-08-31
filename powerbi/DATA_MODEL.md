# Data Model - Dubai Land Department Analytics

Star schema with two fact tables and three dimensions. Built from the CSVs in `powerbi/data/`.

## Tables

**FactProjects** (grain: one row per project)
project_id, master_project_en, area_name_en, developer, project_status, project_type_en, percent_completed, no_of_units, no_of_buildings, no_of_villas, no_of_lands, total_assets, project_start_date, project_end_date, start_year, end_year, planned_duration_days, is_ready, is_offplan, is_delivered, is_overdue, is_zombie, months_overdue, progress_band, cohort_median_completion, vs_cohort_pts

**FactTransactions** (grain: one row per quarter x property type x transaction group)
quarter_start, year, quarter_number, period_label, property_type, transaction_group, value_aed, txn_count

**DimDate**
quarter_start, year, quarter_number, period_label, year_quarter_sort

**DimDeveloper**
developer, n_projects, total_units, delivered_rate, avg_completion, overdue_projects, overdue_units, overdue_share, reliability_score, reliability_tier

**DimArea**
area_name_en, n_projects, total_units, offplan_units, overdue_units, avg_completion, delivery_rate, latitude, longitude

## Relationships

| From | To | Key | Cardinality |
|---|---|---|---|
| FactTransactions | DimDate | quarter_start | many-to-one |
| FactProjects | DimDeveloper | developer | many-to-one |
| FactProjects | DimArea | area_name_en | many-to-one |

FactProjects and FactTransactions are not related to each other. There is no bridge
between the two fact tables because they sit at different grains (project lifecycle
vs. quarterly market activity) and share no common dimension key: FactProjects
carries `end_year`, not `quarter_start`, and DimDate is a transaction-time table only.
Cross-filtering between the two fact tables is intentionally not supported.

Do not mark DimDate as the model's date table. It's quarter-grain (one row per
quarter), so Power BI's date-table certification requires a row for every
calendar day and will reject it with a "date column has gaps" error. The
`Sales Value YoY %` measure gets the same result without a certified date
table by comparing on `year_quarter_sort` (year*10 + quarter_number, offset
by -10 for one year back) instead of using `DATEADD`.

## Verification

Checked against `powerbi/BUILD_GUIDE.md` (step 3, model setup) and the header rows
of the five CSVs in `powerbi/data/`. Both match the relationships and columns above.
