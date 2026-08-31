# Dubai Land Department Analytics - Power BI exact build manual

Three pages, three questions. Canvas 1280 x 720 (default 16:9). Every visual
lists: type, fields, filters, formatting, title, and Position (X, Y) /
Size (W, H) - set them in Format visual > General > Properties.

Color code (used everywhere): green #1B7A52 = healthy/delivered,
yellow #E3B341 = watch, orange #C4562A = risk, light green #86D0AC = neutral.

---

## 0. Prerequisites (do once)

1. Load the five CSVs from `powerbi/data/` (Get Data > Text/CSV > Load).
2. Model view - create relationships (drag column to column):
   - FactTransactions[quarter_start] -> DimDate[quarter_start]
   - FactProjects[developer] -> DimDeveloper[developer]
   - FactProjects[area_name_en] -> DimArea[area_name_en]
3. Select DimDate > Table tools > Mark as date table > quarter_start.
4. View > Themes > Browse for themes > `theme.json`.
5. View > tick Snap to grid.
6. Create every measure in `measures.dax` (top to bottom, on the table named
   in each section header). Then set formats (Measure tools ribbon):
   - Percent (1 decimal): Growth vs Prior Quarter, At-Risk Share,
     Delivery Rate, Sales Value YoY %
   - 2 decimals: Mortgage to Sales Ratio, Mortgage to Sales Latest Q
   - Whole number, thousands separator: all unit/project counts
7. Sort labels: click DimDate[period_label] in the Data pane > Column tools >
   Sort by column > year_quarter_sort (needed anywhere period_label is used).
8. Rename pages (double-click tabs): `1 · Market Health`,
   `2 · Delivery & Trust`, `3 · Money Flow`.

---

## Page 1 - Is the market healthy?

Build order: headline > cards > charts > strip.

**1. Headline (Text box)** - Insert > Text box. Pos (16, 8) Size (1000 x 36).
Font 14. Text:
`Record sales, financed with equity: mortgage registrations are 0.23x of sales value, down from 1.3x in 2016.`

**2-7. Six KPI cards** - Card visual. All: Y 52, H 110, W 198.
Format each: Category label Off; Title On.
| # | X | Field (measure) | Title |
|---|---|---|---|
| 2 | 16 | Sales Value Latest Q | Sales value · latest quarter |
| 3 | 226 | Growth vs Prior Quarter | Growth vs prior reported quarter |
| 4 | 436 | Mortgage to Sales Latest Q | Mortgage / sales value |
| 5 | 646 | Pipeline Units | Off-plan pipeline (units) |
| 6 | 856 | At-Risk Share | Pipeline <30% built |
| 7 | 1066 | Stalled Projects | Stalled projects |
Tip: build card 2, then Ctrl+C / Ctrl+V and swap the field for the rest.

**8. Sales trend (Line chart)** - Pos (16, 174) Size (690 x 260).
X-axis: DimDate[quarter_start] (choose the bare field, not Date Hierarchy).
Y-axis: Sales Value. Y-axis title Off.
Title: `Sales value at record levels (2024 not published)`

**9. Pipeline credibility (Stacked column)** - Pos (718, 174) Size (546 x 260).
X-axis: FactProjects[end_year]. Y-axis: Pipeline Units.
Legend: FactProjects[progress_band].
Visual filter: end_year >= 2024.
Columns > Colors: `<30% built` #C4562A · `30-70% built` #E3B341 ·
`>70% built` #1B7A52. Axis titles Off.
Title: `Most units promised for 2026-2028 are <30% built`

**10. Credit profile (Area chart)** - Pos (16, 446) Size (690 x 236).
X-axis: DimDate[quarter_start]. Y-axis: Mortgage to Sales Ratio.
Analytics pane (magnifier) > Y-Axis Constant Line > On > Value 1 >
Data label On, text `mortgages = sales`.
Title: `The market deleveraged: 1.3x to 0.23x`

**11. Pipeline builders (Stacked bar)** - Pos (718, 446) Size (546 x 236).
Y-axis: FactProjects[developer]. X-axis: Pipeline Units.
Visual filter: developer > Top N > 10 > By value: Pipeline Units.
Bar color #1B7A52. Axis titles Off.
Title: `Who is building the pipeline`

**12. (Optional) Inventory split (100% stacked bar)** - Pos (16, 648)
Size (690 x 40). Values: Total Units. Legend: FactProjects[is_offplan].
Title Off, Legend Off, Data labels On.

**13. Source strip (Text box)** - Pos (16, 692) Size (1248 x 20). Font 9, grey:
`Source: Dubai Land Department open data via Dubai Pulse · 2024 not published in the source dataset · Off-plan = registered, not yet finished`

---

## Page 2 - Will promised supply arrive, and who can you trust?

**1. Slicer: Developer** - Slicer visual. Field DimDeveloper[developer].
Slicer settings > Style: Dropdown. Pos (16, 8) Size (220 x 46).
**2. Slicer: Community** - copy slicer, field FactProjects[area_name_en].
Pos (248, 8) Size (220 x 46).

**3-6. Four KPI cards** - Y 8, H 96, W 190. Category label Off.
| # | X | Field | Title |
|---|---|---|---|
| 3 | 486 | Overdue Projects | Projects past promised date |
| 4 | 688 | Overdue Units | Units overdue |
| 5 | 890 | Stalled Projects | Stalled projects |
| 6 | 1092 | Stalled Units | Units in stalled projects |

**7. Developer risk map (Scatter chart)** - Pos (16, 120) Size (740 x 300).
X-axis: DimDeveloper[avg_completion]. Y-axis: DimDeveloper[delivered_rate].
Size: total_units. Details (Values/Play axis area): developer.
Legend: reliability_tier.
Visual filter: n_projects >= 10.
Title: `Top-right you can trust; bottom-left you can't`

**8. Most reliable (Stacked bar)** - Pos (768, 120) Size (496 x 144).
Y-axis: DimDeveloper[developer]. X-axis: reliability_score.
Filters: n_projects >= 10; developer > Top N > 10 by reliability_score.
Color #1B7A52. Axis titles Off. Title: `Most reliable developers`

**9. Least reliable (Stacked bar)** - copy #8. Pos (768, 276) Size (496 x 144).
Change Top N to Bottom 10. Color #C4562A. Title: `Least reliable developers`

**10. Delivery watchlist (Table)** - Pos (16, 432) Size (880 x 268).
Columns (in order): master_project_en, area_name_en, developer,
percent_completed, no_of_units, months_overdue.
Visual filter: is_overdue = True. Sort: no_of_units descending.
percent_completed dropdown (in Values well) > Conditional formatting >
Data bars. Title: `Overdue projects, largest first`

**11. Overdue map (Map)** - Pos (908, 432) Size (356 x 268).
Latitude: DimArea[latitude]. Longitude: DimArea[longitude].
Bubble size: DimArea[overdue_units].
Title: `Where the overdue units sit`

---

## Page 3 - Where is the money going?

**1. Slicer: property type** - Dropdown slicer,
FactTransactions[property_type]. Pos (16, 8) Size (300 x 46).

**2. Value by type (Line chart)** - Pos (16, 66) Size (620 x 300).
X: DimDate[quarter_start]. Y: Sales Value. Legend: property_type.
Title: `Apartments and villas now drive sales value`

**3. Price signal (Line chart)** - Pos (652, 66) Size (620 x 300).
X: DimDate[quarter_start]. Y: Avg Ticket. Legend: property_type.
Title: `Villas repriced sharply; apartments flat near AED 2M`

**4. Mix shift (100% stacked column)** - Pos (16, 378) Size (620 x 300).
X: DimDate[quarter_start]. Y: Sales Value. Legend: property_type.
Title: `Land speculation gave way to end-user product`

**5. Seasonality (Clustered column)** - Pos (652, 378) Size (620 x 300).
X: DimDate[quarter_number]. Y: Avg Sales Value by Quarter No.
Bar color #1B7A52. Title: `Q4 is consistently the strongest quarter`

---

## Final QA checklist

- [ ] Every % KPI shows as a percentage, not 0.74.
- [ ] Line charts run 2016 -> 2025 left to right, no scrollbar.
- [ ] Page 1 stacked columns show orange dominating 2026-2028.
- [ ] Page 2: selecting a developer in the slicer filters cards, watchlist
      and map together.
- [ ] Page 2 scatter: hover a bubble shows developer name + numbers.
- [ ] No visual shows an axis title that repeats the chart title.
- [ ] Titles read as insights, not metric names.
- [ ] Source strip present on page 1.
- [ ] Save as DubaiLandAnalytics.pbix (keep out of git, or add *.pbix
      to .gitignore).
