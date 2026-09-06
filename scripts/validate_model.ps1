param([string]$PowerBIBin = 'C:\Program Files\Microsoft Power BI Desktop\bin')
$ErrorActionPreference = 'Stop'
foreach ($name in @('Microsoft.AnalysisServices.Server.Core.dll', 'Microsoft.AnalysisServices.Server.Tabular.dll', 'Microsoft.PowerBI.Tabular.dll')) {
    [System.Reflection.Assembly]::LoadFrom((Join-Path $PowerBIBin $name)) | Out-Null
}
$repo = Split-Path $PSScriptRoot -Parent
$model = Join-Path $repo 'Informe stock.SemanticModel\definition'
$db = [Microsoft.AnalysisServices.Tabular.TmdlSerializer]::DeserializeDatabaseFromFolder($model)
if ($db.Model.Tables.Count -ne 15 -or $db.Model.Relationships.Count -ne 17) { throw 'Unexpected model structure' }
$db.Model.Tables | Select-Object Name, @{N='Columns';E={$_.Columns.Count}}, @{N='Measures';E={$_.Measures.Count}}
Write-Output 'TMDL deserialization passed: 15 tables and 17 relationships. This does not process data or evaluate DAX.'
