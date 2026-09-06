param([Parameter(Mandatory=$true)][int]$Port)
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$lib = 'C:\Program Files\Microsoft Power BI Desktop\bin'
foreach ($dll in @('Microsoft.AnalysisServices.Server.Core.dll','Microsoft.AnalysisServices.Server.Tabular.dll','Microsoft.PowerBI.Tabular.dll','Microsoft.PowerBI.AdomdClient.dll')) {
    [System.Reflection.Assembly]::LoadFrom((Join-Path $lib $dll)) | Out-Null
}
$server = New-Object Microsoft.AnalysisServices.Tabular.Server
$server.Connect("localhost:$Port")
$db = $server.Databases | Where-Object { $_.Model.Tables.Contains('InventoryCurrent') } | Select-Object -First 1
if (-not $db) { throw 'Inventory model not found on this port' }
$connection = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection("Data Source=localhost:$Port;Initial Catalog=$($db.Name)")
$connection.Open()
function Query([string]$Dax) {
    $command = $connection.CreateCommand()
    $command.CommandText = $Dax
    $reader = $command.ExecuteReader()
    $rows = @()
    while ($reader.Read()) {
        $row = [ordered]@{}
        for ($i=0; $i -lt $reader.FieldCount; $i++) { $row[$reader.GetName($i)] = $reader.GetValue($i) }
        $rows += [pscustomobject]$row
    }
    $reader.Close()
    return $rows
}
$totals = Query 'EVALUATE ROW("Fisico", [Stock fisico], "Reservado", [Stock reservado], "Disponible", [Stock disponible], "Valor", [Valor inventario UM], "Conciliacion", [Control conciliacion], "Cierre", [Stock cierre mensual], "Movimientos", COUNTROWS(InventoryMovements))'
$expected = @{ '[Fisico]'=61276; '[Reservado]'=4846; '[Disponible]'=56430; '[Valor]'=109630923.09; '[Conciliacion]'=0; '[Cierre]'=61276; '[Movimientos]'=307802 }
foreach ($key in $expected.Keys) {
    if ([decimal]$totals.$key -ne [decimal]$expected[$key]) { throw "Unexpected $key : $($totals.$key)" }
}
$byWarehouse = Query 'EVALUATE SUMMARIZECOLUMNS(Warehouse[WarehouseName], "Control", [Control conciliacion])'
if (@($byWarehouse).Count -ne 9 -or @($byWarehouse | Where-Object { $_.'[Control]' -ne 0 }).Count) { throw 'Warehouse filter/reconciliation failed' }
$byCategory = Query 'EVALUATE SUMMARIZECOLUMNS(Product[CategoryName], "Control", [Control conciliacion])'
if (@($byCategory).Count -ne 5 -or @($byCategory | Where-Object { $_.'[Control]' -ne 0 }).Count) { throw 'Category filter/reconciliation failed' }
$monthly = Query 'EVALUATE SUMMARIZECOLUMNS(''Calendario Base''[YearMonth], "Stock", [Stock cierre mensual])'
if (@($monthly).Count -ne 12) { throw 'Expected 12 nonblank month-end balances' }
$csv = Import-Csv -LiteralPath (Join-Path $repo 'data\prepared\InventoryMonthly.csv')
foreach ($row in $monthly) {
    $month = $row.'Calendario Base[YearMonth]'
    $sum = ($csv | Where-Object { $_.Date.StartsWith($month) } | Measure-Object -Property OnHand -Sum).Sum
    if ([decimal]$row.'[Stock]' -ne [decimal]$sum) { throw "Month-end mismatch: $month" }
}
$counts = foreach ($table in $db.Model.Tables) {
    $escaped = $table.Name.Replace("'", "''")
    $result = Query "EVALUATE ROW(`"Rows`", COUNTROWS('$escaped'))"
    [pscustomobject]@{Table=$table.Name;Rows=$result.'[Rows]'}
}
$manifest = Get-Content -LiteralPath (Join-Path $repo 'data\prepared\manifest.json') -Raw | ConvertFrom-Json
foreach ($count in $counts) {
    $expectedRows = $manifest.rows.PSObject.Properties[$count.Table]
    if ($expectedRows -and $count.Rows -ne $expectedRows.Value) { throw "Row count mismatch: $($count.Table)" }
}
$measures = foreach ($measure in $db.Model.Tables['Medidas DAX'].Measures) {
    $name = $measure.Name.Replace(']', ']]')
    $result = Query "EVALUATE ROW(`"Value`", [$name])"
    [pscustomobject]@{Measure=$measure.Name;Value=$result.'[Value]'}
}
$report = [ordered]@{status='passed';tables=$db.Model.Tables.Count;relationships=$db.Model.Relationships.Count;totals=$totals;row_counts=$counts;measures=$measures;monthly=$monthly;warehouse_reconciliation=$byWarehouse;category_reconciliation=$byCategory}
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $repo 'docs\validacion-powerbi.json') -Encoding UTF8
$totals | Format-List
Write-Output 'Live DAX checks passed: totals, 12 months, 9 warehouses and 5 categories.'
$connection.Close()
$server.Disconnect()
