# FleetGuard AI - Interactive System Runner
# PowerShell script for easy system testing and demonstration

Write-Host ""
Write-Host "######################################################################" -ForegroundColor Cyan
Write-Host "# FleetGuard AI - Multi-Agent Fleet Management System" -ForegroundColor Cyan
Write-Host "# Interactive Demo & Testing Environment" -ForegroundColor Cyan
Write-Host "######################################################################" -ForegroundColor Cyan
Write-Host ""

function Show-Menu {
    Write-Host "===============================================" -ForegroundColor Yellow
    Write-Host "   FLEETGUARD AI - MAIN MENU" -ForegroundColor Yellow
    Write-Host "===============================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. " -ForegroundColor Green -NoNewline
    Write-Host "Run Full System (Crew 1 + Crew 2)"
    Write-Host "   -> Complete pipeline: Data Analysis + ML Model Training"
    Write-Host ""

    Write-Host "2. " -ForegroundColor Green -NoNewline
    Write-Host "Run Individual Agents"
    Write-Host "   -> Test specific agents (D, E, F) separately"
    Write-Host ""

    Write-Host "3. " -ForegroundColor Green -NoNewline
    Write-Host "Validate Data Contract"
    Write-Host "   -> Check data against schema (52 validation checks)"
    Write-Host ""

    Write-Host "4. " -ForegroundColor Green -NoNewline
    Write-Host "Fleet Management"
    Write-Host "   -> Add/retire vehicles, add test invoices"
    Write-Host ""

    Write-Host "5. " -ForegroundColor Green -NoNewline
    Write-Host "View Reports & Status"
    Write-Host "   -> See latest results and model performance"
    Write-Host ""

    Write-Host "6. " -ForegroundColor Green -NoNewline
    Write-Host "Run Test Suite"
    Write-Host "   -> Complete integration test (like we just did)"
    Write-Host ""

    Write-Host "0. " -ForegroundColor Red -NoNewline
    Write-Host "Exit"
    Write-Host ""
    Write-Host "===============================================" -ForegroundColor Yellow
}

function Run-FullSystem {
    Write-Host ""
    Write-Host "==> Running Full System Pipeline..." -ForegroundColor Cyan
    Write-Host ""

    $startTime = Get-Date
    python src/crew_flow.py
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds

    Write-Host ""
    Write-Host "[SUCCESS] System completed in $([math]::Round($duration, 2)) seconds" -ForegroundColor Green
    Write-Host ""
    Write-Host "Generated files:" -ForegroundColor Yellow
    Write-Host "  - reports/flow_summary.md"
    Write-Host "  - reports/flow_execution_report.json"
    Write-Host "  - models/model.pkl (ML model)"
    Write-Host "  - reports/evaluation_report.md"
    Write-Host ""

    Read-Host "Press Enter to continue"
}

function Run-IndividualAgents {
    Write-Host ""
    Write-Host "===============================================" -ForegroundColor Yellow
    Write-Host "   SELECT AGENT TO RUN" -ForegroundColor Yellow
    Write-Host "===============================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "D. Agent D - Feature Engineer (creates 15 ML features)"
    Write-Host "E. Agent E - Model Trainer (trains & saves best model)"
    Write-Host "F. Agent F - Model Evaluator (evaluates model performance)"
    Write-Host "C. Crew 2 - Full Pipeline (D -> E -> F)"
    Write-Host "B. Back to main menu"
    Write-Host ""

    $choice = Read-Host "Select agent"

    switch ($choice.ToUpper()) {
        "D" {
            Write-Host ""
            Write-Host "==> Running Agent D (Feature Engineer)..." -ForegroundColor Cyan
            python src/agents/feature_engineer_agent.py
            Write-Host ""
            Write-Host "Output: data/processed/features.csv" -ForegroundColor Green
        }
        "E" {
            Write-Host ""
            Write-Host "==> Running Agent E (Model Trainer)..." -ForegroundColor Cyan
            python src/agents/model_trainer_agent.py
            Write-Host ""
            Write-Host "Output: models/model.pkl" -ForegroundColor Green
        }
        "F" {
            Write-Host ""
            Write-Host "==> Running Agent F (Model Evaluator)..." -ForegroundColor Cyan
            python src/agents/model_evaluator_agent.py
            Write-Host ""
            Write-Host "Output: reports/evaluation_report.md" -ForegroundColor Green
        }
        "C" {
            Write-Host ""
            Write-Host "==> Running Crew 2 (Full ML Pipeline)..." -ForegroundColor Cyan
            python src/crews/data_scientist_crew.py
            Write-Host ""
            Write-Host "Output: reports/crew2_report.json" -ForegroundColor Green
        }
        "B" {
            return
        }
        default {
            Write-Host "Invalid choice" -ForegroundColor Red
        }
    }

    Read-Host "Press Enter to continue"
}

function Validate-Contract {
    Write-Host ""
    Write-Host "==> Running Dataset Contract Validation..." -ForegroundColor Cyan
    Write-Host ""

    python src/utils/contract_validator.py

    Write-Host ""
    Write-Host "Validation report: reports/contract_validation_report.json" -ForegroundColor Green
    Write-Host ""

    Read-Host "Press Enter to continue"
}

function Fleet-Management {
    Write-Host ""
    Write-Host "===============================================" -ForegroundColor Yellow
    Write-Host "   FLEET MANAGEMENT" -ForegroundColor Yellow
    Write-Host "===============================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Replace Vehicle (retire old + add new)"
    Write-Host "2. Add Test Invoices (add 20 random invoices)"
    Write-Host "3. View Fleet Status"
    Write-Host "B. Back to main menu"
    Write-Host ""

    $choice = Read-Host "Select option"

    switch ($choice) {
        "1" {
            Write-Host ""
            Write-Host "==> Replacing Vehicle..." -ForegroundColor Cyan
            python scripts/replace_vehicle.py
        }
        "2" {
            Write-Host ""
            Write-Host "==> Adding 20 Test Invoices..." -ForegroundColor Cyan
            python scripts/add_test_invoices.py
        }
        "3" {
            Write-Host ""
            Write-Host "==> Fleet Status:" -ForegroundColor Cyan
            python -c "from src.database_manager import DatabaseManager; db = DatabaseManager(); v = db.get_fleet_overview(); print(f'Total vehicles: {len(v)}'); print(f'Active: {len(v[v[\"status\"]==\"active\"])}'); print(f'Retired: {len(v[v[\"status\"]==\"retired\"])}'); inv = db.get_all_invoices(); print(f'Total invoices: {len(inv)}')"
        }
        "B" {
            return
        }
        default {
            Write-Host "Invalid choice" -ForegroundColor Red
        }
    }

    Read-Host "Press Enter to continue"
}

function View-Reports {
    Write-Host ""
    Write-Host "===============================================" -ForegroundColor Yellow
    Write-Host "   REPORTS & STATUS" -ForegroundColor Yellow
    Write-Host "===============================================" -ForegroundColor Yellow
    Write-Host ""

    # Check latest flow summary
    if (Test-Path "reports/flow_summary.md") {
        Write-Host "Latest Flow Execution:" -ForegroundColor Cyan
        Get-Content "reports/flow_summary.md" -Head 10
        Write-Host ""
    }

    # Check model metadata
    if (Test-Path "models/model_metadata.json") {
        Write-Host "Latest Model Performance:" -ForegroundColor Cyan
        $metadata = Get-Content "models/model_metadata.json" | ConvertFrom-Json
        Write-Host "  Model Type: $($metadata.model_name)" -ForegroundColor Green
        Write-Host "  R2 Score: $($metadata.test_r2)" -ForegroundColor Green
        Write-Host "  RMSE: $($metadata.rmse)" -ForegroundColor Green
        Write-Host "  MAE: $($metadata.mae)" -ForegroundColor Green
        Write-Host ""
    }

    # Check contract validation
    if (Test-Path "reports/contract_validation_report.json") {
        Write-Host "Latest Contract Validation:" -ForegroundColor Cyan
        $validation = Get-Content "reports/contract_validation_report.json" | ConvertFrom-Json
        Write-Host "  Status: $($validation.summary.status)" -ForegroundColor $(if ($validation.summary.status -eq "PASSED") { "Green" } else { "Red" })
        Write-Host "  Checks: $($validation.summary.total_checks)" -ForegroundColor Green
        Write-Host "  Errors: $($validation.summary.total_errors)" -ForegroundColor $(if ($validation.summary.total_errors -eq 0) { "Green" } else { "Red" })
        Write-Host ""
    }

    Write-Host ""
    Write-Host "Available Reports:" -ForegroundColor Yellow
    Write-Host "  - reports/flow_summary.md"
    Write-Host "  - reports/evaluation_report.md"
    Write-Host "  - reports/contract_validation_report.json"
    Write-Host "  - TEST_REPORT.md (full integration test)"
    Write-Host ""

    $openReport = Read-Host "Open a report? (flow/eval/contract/test/N)"

    switch ($openReport.ToLower()) {
        "flow" { notepad "reports/flow_summary.md" }
        "eval" { notepad "reports/evaluation_report.md" }
        "contract" { notepad "reports/contract_validation_report.json" }
        "test" { notepad "TEST_REPORT.md" }
        default { }
    }
}

function Run-TestSuite {
    Write-Host ""
    Write-Host "==> Running Complete Integration Test..." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "This will:" -ForegroundColor Yellow
    Write-Host "  1. Replace a vehicle (retire old + add new)"
    Write-Host "  2. Run full system pipeline"
    Write-Host "  3. Validate data contract"
    Write-Host "  4. Generate test report"
    Write-Host ""

    $confirm = Read-Host "Continue? (Y/N)"

    if ($confirm -eq "Y" -or $confirm -eq "y") {
        Write-Host ""
        Write-Host "[STEP 1/4] Replacing vehicle..." -ForegroundColor Cyan
        python scripts/replace_vehicle.py

        Write-Host ""
        Write-Host "[STEP 2/4] Running full system..." -ForegroundColor Cyan
        python src/crew_flow.py

        Write-Host ""
        Write-Host "[STEP 3/4] Validating contract..." -ForegroundColor Cyan
        python src/utils/contract_validator.py

        Write-Host ""
        Write-Host "[STEP 4/4] Test complete!" -ForegroundColor Green
        Write-Host ""
        Write-Host "See TEST_REPORT.md for full details" -ForegroundColor Yellow
    }

    Read-Host "Press Enter to continue"
}

# Main loop
do {
    Clear-Host
    Show-Menu
    $choice = Read-Host "Select option"

    switch ($choice) {
        "1" { Run-FullSystem }
        "2" { Run-IndividualAgents }
        "3" { Validate-Contract }
        "4" { Fleet-Management }
        "5" { View-Reports }
        "6" { Run-TestSuite }
        "0" {
            Write-Host ""
            Write-Host "Thank you for using FleetGuard AI!" -ForegroundColor Green
            Write-Host ""
            exit
        }
        default {
            Write-Host ""
            Write-Host "Invalid choice, please try again" -ForegroundColor Red
            Start-Sleep -Seconds 2
        }
    }
} while ($true)
