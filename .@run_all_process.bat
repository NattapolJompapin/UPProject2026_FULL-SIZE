@echo off
title UPDENSITY SYSTEM

echo ===============================
echo START UPDENSITY SYSTEM
echo ===============================

REM ---------- 1. Express Server ----------
start "Express Server" cmd /k "cd /d ""%~dp0JSServer"" && node server.js"

REM ---------- 2. React Dashboard ----------
start "React Dashboard" cmd /k "cd /d ""%~dp0Dashboard React"" && npm start"

REM ---------- 3. Central API (FastAPI) ----------
start "Central API" cmd /k "cd /d ""%~dp0UPDensity_ProgramPackage"" && call venv\Scripts\activate.bat && cd central && python -m uvicorn main:app --host 0.0.0.0 --port 3001"

REM ---------- 4. Edge Camera ----------
start "Edge Camera" cmd /k "cd /d ""%~dp0UPDensity_ProgramPackage"" && call venv\Scripts\activate.bat && cd edge && python edge_multi0.py"

echo.
echo ===============================
echo SYSTEM STARTED
echo ===============================
echo.
echo Press ESC to stop ALL services and close...
echo.

REM ---------- WAIT FOR ESC ----------
powershell -NoProfile -Command "$Host.UI.RawUI.FlushInputBuffer(); while ($true) { if ([Console]::KeyAvailable) { $key = [Console]::ReadKey($true); if ($key.Key -eq 'Escape') { break } } Start-Sleep -Milliseconds 50 }"

REM =====================================
REM STOP ALL PROJECT SERVICES
REM =====================================
echo.
echo Stopping all services...
powershell -NoProfile -Command "$names=@('Express Server','React Dashboard','Central API','Edge Camera'); foreach($name in $names){ Get-Process cmd -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq $name } | ForEach-Object { taskkill /PID $_.Id /T /F } }"

echo.
echo All services stopped.
timeout /t 1 /nobreak >nul
exit