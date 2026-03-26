@echo off
title DAREEDA — Backend
cd /d %~dp0..
call .venv\Scripts\activate.bat
cd backend
uvicorn main:app --reload --port 8000
