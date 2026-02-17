# =============================================================================
# Real-Time BI Copilot — Setup Script (Windows PowerShell)
# =============================================================================

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " Real-Time BI Copilot - Setup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Check Python
Write-Host "`n[1/7] Checking Python version..." -ForegroundColor Yellow
$pythonCmd = $null
foreach ($cmd in @("python3", "python")) {
    try {
        $version = & $cmd --version 2>&1
        if ($version -match "3\.(1[1-9]|[2-9]\d)") {
            $pythonCmd = $cmd
            Write-Host "  Found: $cmd ($version)"
            break
        }
    } catch { }
}

if (-not $pythonCmd) {
    Write-Host "  ERROR: Python 3.11+ required." -ForegroundColor Red
    exit 1
}

# 2. Virtual environment
Write-Host "`n[2/7] Creating virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    & $pythonCmd -m venv venv
    Write-Host "  Created: ./venv"
} else {
    Write-Host "  Already exists: ./venv"
}

& .\venv\Scripts\Activate.ps1

# 3. Dependencies
Write-Host "`n[3/7] Installing dependencies..." -ForegroundColor Yellow
pip install --upgrade pip -q
pip install -r requirements.txt -q
Write-Host "  Dependencies installed."

# 4. Environment
Write-Host "`n[4/7] Setting up environment..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
    Write-Host "  Created .env from template."
} else {
    Write-Host "  .env already exists."
}

# 5. Sample data
Write-Host "`n[5/7] Generating sample data..." -ForegroundColor Yellow
$env:PYTHONPATH = "."
python data/sample_data_generator.py

# 6. Verify
Write-Host "`n[6/7] Verifying installation..." -ForegroundColor Yellow
python -c "
import duckdb
con = duckdb.connect('./data/database.duckdb')
tables = con.execute('SHOW TABLES').fetchall()
print(f'  Database OK: {len(tables)} tables found')
con.close()
"

# 7. Done
Write-Host "`n[7/7] Setup complete!" -ForegroundColor Green
Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host " Next Steps:" -ForegroundColor Cyan
Write-Host " 1. Edit .env with your ANTHROPIC_API_KEY"
Write-Host " 2. streamlit run streamlit-app/app.py"
Write-Host "=========================================" -ForegroundColor Cyan
