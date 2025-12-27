@echo off
chcp 65001 >nul
cls
echo ========================================
echo 🚛 FleetGuard - הפעלה שקטה (ללא אזהרות)
echo ========================================
echo.

cd /d "%~dp0"

set STREAMLIT_LOGGER_LEVEL=error
set PYTHONWARNINGS=ignore

python -m streamlit run main.py --logger.level=error --server.headless=true 2>nul

pause








