# FleetGuard - הפעלת המערכת המלאה (PowerShell)
# Encoding: UTF-8

# הגדרת encoding ל-UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🚛 FleetGuard - הפעלת המערכת המלאה" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# מעבר לתיקיית הפרויקט
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($scriptPath) {
    Set-Location $scriptPath
} else {
    # אם לא מצליח, נסה את הנתיב הנוכחי
    $scriptPath = Get-Location
}
Write-Host "📁 תיקיית עבודה: $scriptPath" -ForegroundColor Gray
Write-Host ""

# שלב 1: בדיקת Python
Write-Host "[שלב 1/4] בדיקת התקנת Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python מותקן: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python לא מותקן! אנא התקן Python 3.8+ מ-https://python.org" -ForegroundColor Red
    Read-Host "לחץ Enter כדי לצאת"
    exit 1
}
Write-Host ""

# שלב 2: בדיקת תלויות
Write-Host "[שלב 2/4] בדיקת התקנת תלויות..." -ForegroundColor Yellow
$modulesCheck = python -c "import streamlit; import pandas; import crewai" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  חלק מהתלויות חסרות. מתקין..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ שגיאה בהתקנת תלויות" -ForegroundColor Red
        Read-Host "לחץ Enter כדי לצאת"
        exit 1
    }
    Write-Host "✅ תלויות הותקנו בהצלחה" -ForegroundColor Green
} else {
    Write-Host "✅ כל התלויות מותקנות" -ForegroundColor Green
}
Write-Host ""

# שלב 3: בדיקת מסד נתונים
Write-Host "[שלב 3/4] בדיקת קיום מסד נתונים..." -ForegroundColor Yellow
if (-not (Test-Path "data\database\fleet.db")) {
    Write-Host "⚠️  מסד נתונים לא נמצא. יוצר נתוני דמו..." -ForegroundColor Yellow
    python generate_data.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ שגיאה ביצירת נתונים" -ForegroundColor Red
        Read-Host "לחץ Enter כדי לצאת"
        exit 1
    }
    Write-Host "✅ נתונים נוצרו בהצלחה" -ForegroundColor Green
} else {
    Write-Host "✅ מסד נתונים קיים" -ForegroundColor Green
}
Write-Host ""

# שלב 4: הפעלת הדשבורד
Write-Host "[שלב 4/4] מפעיל את הדשבורד..." -ForegroundColor Yellow
Write-Host ""
Write-Host "🌐 הדשבורד יפתח בדפדפן ב: http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 טיפ: אם הדפדפן לא נפתח אוטומטית, פתח ידנית את הכתובת למעלה" -ForegroundColor Yellow
Write-Host ""
Write-Host "⏸️  כדי לעצור את השרת, לחץ Ctrl+C" -ForegroundColor Yellow
Write-Host ""

# הפעלת Streamlit עם דיכוי אזהרות
try {
    $env:STREAMLIT_LOGGER_LEVEL = "error"
    python -m streamlit run main.py --logger.level=error --server.headless=true
} catch {
    Write-Host "❌ שגיאה בהפעלת Streamlit" -ForegroundColor Red
    Write-Host "נסה להריץ ידנית: python -m streamlit run main.py" -ForegroundColor Yellow
    Read-Host "לחץ Enter כדי לצאת"
    exit 1
}

