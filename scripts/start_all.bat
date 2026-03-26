@echo off
title DAREEDA — Avvio
start "DAREEDA Backend"  cmd /c "%~dp0start_backend.bat"
timeout /t 3 /nobreak >nul
start "DAREEDA Frontend" cmd /c "%~dp0start_frontend.bat"
echo.
echo  DAREEDA avviato.
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:5173
echo  Docs API: http://localhost:8000/docs
echo.
pause
