@echo off
echo ========================================================
echo Starting SnapClass AI Attendance and Landing Page Servers
echo ========================================================

start "SnapClass - Landing Page" cmd /k "python landing\app.py"
start "SnapClass - AI Attendance App" cmd /k "python -m streamlit run app.py"

echo.
echo Landing Page:   http://localhost:5002
echo AI Attendance:  http://localhost:8501
echo ========================================================
