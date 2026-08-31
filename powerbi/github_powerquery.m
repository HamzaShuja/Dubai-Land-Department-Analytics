// ============================================================
// Power Query: load a model table straight from GitHub.
// Home > Get Data > Blank Query > Advanced Editor > paste this,
// set TableName, rename the query to match. Repeat per table
// (or duplicate the query). Refresh then always pulls main.
// After loading, set column types: quarter_start/dates as Date,
// numeric columns as Decimal/Whole Number, flags as True/False.
// ============================================================
let
    BaseUrl = "https://raw.githubusercontent.com/HamzaShuja/Dubai-Land-Department-Analytics/main/powerbi/data/",
    TableName = "FactProjects",   // FactTransactions / FactProjects / DimDeveloper / DimArea / DimDate
    Source = Csv.Document(Web.Contents(BaseUrl & TableName & ".csv"),
                          [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true])
in
    Promoted
