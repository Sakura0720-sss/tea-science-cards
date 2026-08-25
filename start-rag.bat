@echo off
cd /d D:\BMCY\tea-rag
.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
