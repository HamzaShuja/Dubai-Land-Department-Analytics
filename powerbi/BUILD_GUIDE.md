# Power BI Build Guide - Dubai Land Department Analytics

A 5-page executive dashboard assembled from the star schema in `data/`.
Everything hard (cleaning, translation, feature engineering, scoring) is
pre-computed; this build is pure assembly, roughly one hour.

## 0. Setup (10 min)

1. **Data**: run `python -m realestate.powerbi_export` (or use the committed
   CSVs in `powerbi/data/`). In Power BI Desktop: Get Data > Text/CSV, load
   all five files. Alternatively use `github_powerquery.m` to load them
   straight from the GitHub repo so Refresh always pulls the latest.
2. **Theme**: View > Themes > Browse for themes > `theme.json`.
3. **Model** (Model view, drag to connect):
   - FactTransactions[quarter_start]  ->  DimDate[quarter_start]  (many-to-one)
   - FactProjects[developer]          ->  DimDeveloper[developer]
   - FactProjects[area_name_en]       ->  DimArea[area_name_en]
   - Do NOT mark DimDate as a date table. It's quarter-grain (one row per
     quarter, not one per day), so Power BI will reject it with a "date
     column has gaps" error, it expects a row for every calendar day.
     Time intelligence uses `year_quarter_sort` instead (see
     `Sales Value YoY %` in measures.dax), so no certified date table
     is needed.
4. **Measures**: New measure for each block in `measures.dax` (create on the
   table named in the section header). Format currency measures as
   `"AED" #,0,,.0B`, ratios as percentages, counts with thousands separators.

## KPI dictionary

Every KPI answers a stakeholder question. Definition = exactly what is
measured; the DAX lives in measures.dax.

| KPI | Definition | Question it answers |
|---|---|---|
| Sales Value Latest Q | AED value of sales registrations, most recent reported quarter | How big is the market right now? |
| Growth vs Prior Quarter | Change vs the previous reported quarter (2024 is unpublished, so plain YoY is undefined) | Is momentum building or fading? |
| Mortgage to Sales Ratio | Registered mortgage value / sales value, per quarter | How leveraged is the market? (1.3x in 2016 -> ~0.23x now: equity-driven) |
| Avg Ticket | Sales value / number of deals, by property type | Where are prices moving? (villas repricing, apartments flat) |
| Pipeline Units | Units in off-plan (not finished) projects | How much supply is promised? |
| At-Risk Share | Off-plan units in projects <30% built / pipeline units | How much of that promise is credible? |
| Overdue Projects / Units | Off-plan projects past their registered end date | Where are delivery promises already broken? |
| Stalled (zombie) | Overdue AND <30% built | Which projects realistically will not deliver as planned? |
| Delivery Rate | Delivered projects / all tracked projects | Base rate of delivery in this market |
| Reliability Score | 0-100 per developer: 40% delivered rate + 30% avg completion + 30% inverse overdue share (10+ projects only) | Which developers can a buyer trust? |
| Cohort benchmark | Median completion of projects started the same year | Is a project ahead of or behind its peers? |

## Report structure: three pages, three questions

Pages are organised by the question they answer, not by data table.

1. **Is the market healthy?** - executive summary (cards + trend + pipeline
   credibility + inventory mix + top pipeline developers).
2. **Will promised supply arrive, and who can you trust?** - the
   due-diligence page (overdue watchlist, reliability ranking, risk-map
   scatter, overdue-by-area map, developer/area slicers).
3. **Where is the money going?** - market deep dive (value by type, avg
   ticket, mix shift, credit profile trend).

## Page 1 - Is the market healthy?

- **KPI cards**: Sales Value Latest Q, Growth vs Prior Quarter,
  Mortgage to Sales Latest Q, Pipeline Units, At-Risk Share, Stalled Projects.
- **Line**: Sales Value by DimDate[quarter_start] (continuous axis).
- **Stacked column**: Pipeline Units by end_year, legend progress_band
  (<30% #C4562A, 30-70% #E3B341, >70% #1B7A52), end_year >= 2024.
- **Donut**: Total Units by is_offplan (Off-plan vs Ready).
- **Bar**: Pipeline Units by developer, Top 10.
- **Headline text box** + source/coverage strip.

## Page 2 - Will promised supply arrive, and who can you trust?

Page-level filter: none (slicers do the work).

- **Slicers (top)**: DimDeveloper[developer], FactProjects[area_name_en].
- **KPI cards**: Overdue Projects, Overdue Units, Stalled Projects, Stalled Units.
- **Scatter (risk map)**: x = DimDeveloper[avg_completion],
  y = DimDeveloper[delivered_rate], size = total_units, details = developer,
  color = reliability_tier. Filter n_projects >= 10.
- **Bar pair**: reliability_score by developer - Top 10 (green #1B7A52) and
  Bottom 10 (orange #C4562A), n_projects >= 10.
- **Matrix (watchlist)**: master_project_en, area_name_en, developer,
  percent_completed (data bars), no_of_units, months_overdue; visual filter
  is_overdue = True; sort by no_of_units desc.
- **Map**: DimArea latitude/longitude, bubble size = overdue_units.

## Page 3 - Where is the money going?

- **Line**: Sales Value by quarter_start, legend property_type.
- **Line**: Avg Ticket by quarter_start, legend property_type.
- **100% stacked column**: Sales Value by quarter_start, legend property_type.
- **Area**: Mortgage to Sales Ratio by quarter_start, constant line y = 1
  ("mortgages = sales value").
- **Slicer**: property_type.
- Callout text: the villa-repricing and deleveraging takeaways.

## Publishing

File > Publish > your workspace, or for a public portfolio link use
"Publish to web" (Settings in the Power BI service). The dataset is public
government data, so public embedding is appropriate.
