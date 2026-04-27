param(
    [string]$AllureHome = "allure-2.32.0"
)

$pluginSource = Join-Path $PSScriptRoot "..\plugins\etl-metrics-dashboard-plugin"
$pluginTarget = Join-Path (Resolve-Path $AllureHome) "plugins\etl-metrics-dashboard-plugin"

if (-not (Test-Path $pluginSource)) {
    Write-Error "Plugin source not found: $pluginSource"
    exit 1
}

if (-not (Test-Path $AllureHome)) {
    Write-Error "Allure directory not found: $AllureHome"
    exit 1
}

if (Test-Path $pluginTarget) {
    Remove-Item $pluginTarget -Recurse -Force
}

Copy-Item $pluginSource $pluginTarget -Recurse -Force
Write-Host "Installed plugin to: $pluginTarget"
