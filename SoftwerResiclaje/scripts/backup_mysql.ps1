$ErrorActionPreference = "Stop"

foreach ($name in @("DB_NAME", "DB_USER", "DB_PASSWORD")) {
    if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name))) {
        throw "Define la variable de entorno $name antes de ejecutar el respaldo."
    }
}

$backupDir = Join-Path $PSScriptRoot "..\backups"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outputFile = Join-Path $backupDir ("{0}_{1}.sql" -f $env:DB_NAME, $stamp)
$port = if ($env:DB_PORT) { $env:DB_PORT } else { "3306" }
$hostName = if ($env:DB_HOST) { $env:DB_HOST } else { "127.0.0.1" }
$dumpArgs = @(
    "--single-transaction", "--routines", "--events", "--default-character-set=utf8mb4",
    "--host=$hostName", "--port=$port", "--user=$($env:DB_USER)", $env:DB_NAME
)

$env:MYSQL_PWD = $env:DB_PASSWORD
try {
    & mysqldump @dumpArgs | Set-Content -LiteralPath $outputFile -Encoding utf8
} finally {
    Remove-Item Env:MYSQL_PWD -ErrorAction SilentlyContinue
}
if ($LASTEXITCODE -ne 0) {
    Remove-Item -LiteralPath $outputFile -ErrorAction SilentlyContinue
    throw "mysqldump terminó con código $LASTEXITCODE."
}
Write-Output "Respaldo creado: $outputFile"
