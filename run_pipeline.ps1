# KPCL Forecasting App - Run Full ML Pipeline
# Run from project root: .\run_pipeline.ps1

$PROJECT_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $PROJECT_ROOT

function Invoke-Step {
    param([string]$Label, [string]$Script)
    Write-Host ""
    Write-Host "--------------------------------------------" -ForegroundColor Cyan
    Write-Host "  $Label" -ForegroundColor Cyan
    Write-Host "--------------------------------------------" -ForegroundColor Cyan
    # Determine which python to use
    $PYTHON_CMD = "python"
    if (Test-Path "$PROJECT_ROOT\myenv\Scripts\python.exe") {
        $PYTHON_CMD = "$PROJECT_ROOT\myenv\Scripts\python.exe"
    }

    & $PYTHON_CMD $Script
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: $Label failed (exit code $LASTEXITCODE)" -ForegroundColor Red
        Write-Host "Pipeline stopped. Fix the error and re-run." -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host "  DONE: $Label" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  KPCL Forecasting - Full ML Pipeline" -ForegroundColor Cyan
Write-Host "  Started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan

Invoke-Step "Step 1/10: Data Preparation"                 "src/data/data_preparation.py"
Invoke-Step "Step 2/10: MSTL Decomposition Analysis"      "src/visualization/mstl_analysis.py"
Invoke-Step "Step 3/10: Classic ML Model Comparison"      "src/modeling/compare_classic_ml_rmse.py"
Invoke-Step "Step 4/10: Train Champion Classic ML"        "src/modeling/train_forecast_classic_ml.py"
Invoke-Step "Step 5/10: Time Series Model Comparison"     "src/modeling/compare_models_rmse.py"
Invoke-Step "Step 6/10: Auto-SARIMA Training"             "src/modeling/train_forecast_autosarima.py"
Invoke-Step "Step 7/10: Validate Classic ML"              "src/forecast_validation/validate_classic_ml.py"
Invoke-Step "Step 8/10: Validate Auto-SARIMA"            "src/forecast_validation/validate_autosarima_model.py"
Invoke-Step "Step 9/10: Final Forecast - TS & SARIMA"     "src/modeling/train_forecast_all_models.py"
Invoke-Step "Step 10/10: Global Validation Summary"       "src/forecast_validation/validate_all_models.py"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  PIPELINE COMPLETE!" -ForegroundColor Green
Write-Host "  Finished: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "  Now run .\start.ps1 to launch the app." -ForegroundColor White
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
