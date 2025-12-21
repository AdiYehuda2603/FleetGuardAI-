@echo off
chcp 65001 >nul
echo ========================================
echo 🚛 FleetGuard - הפעלת המערכת המלאה
echo ========================================
echo.

cd /d "%~dp0"

echo [שלב 1/4] בדיקת התקנת Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python לא מותקן! אנא התקן Python 3.8+ מ-https://python.org
    pause
    exit /b 1
)
echo ✅ Python מותקן
echo.

echo [שלב 2/4] בדיקת התקנת תלויות...
python -c "import streamlit; import pandas; import crewai" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  חלק מהתלויות חסרות. מתקין...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ שגיאה בהתקנת תלויות
        pause
        exit /b 1
    )
)
echo ✅ כל התלויות מותקנות
echo.

echo [שלב 3/4] בדיקת קיום מסד נתונים...
if not exist "data\database\fleet.db" (
    echo ⚠️  מסד נתונים לא נמצא. יוצר נתוני דמו...
    python generate_data.py
    if errorlevel 1 (
        echo ❌ שגיאה ביצירת נתונים
        pause
        exit /b 1
    )
    echo ✅ נתונים נוצרו בהצלחה
) else (
    echo ✅ מסד נתונים קיים
)
echo.

echo [שלב 4/4] מפעיל את הדשבורד...
echo.
echo 🌐 הדשבורד יפתח בדפדפן ב: http://localhost:8501
echo.
echo 💡 טיפ: אם הדפדפן לא נפתח אוטומטית, פתח ידנית את הכתובת למעלה
echo.
echo ⏸️  כדי לעצור את השרת, לחץ Ctrl+C
echo.

streamlit run main.py

pause

