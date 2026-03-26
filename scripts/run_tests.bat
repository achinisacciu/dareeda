@echo off
title DAREEDA — Tests
cd /d %~dp0..
call .venv\Scripts\activate.bat
pytest backend/tests -v
pause
