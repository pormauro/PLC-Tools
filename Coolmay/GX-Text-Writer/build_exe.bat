@echo off
setlocal
title Build GX Text Writer V3
where py >nul 2>nul
if errorlevel 1 ( echo No encuentro Python py & pause & exit /b 1 )
if not exist .venv py -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m PyInstaller --onefile --windowed --clean --name GX_Text_Writer_V3 gx_text_writer_gui_v3.py
echo Listo: dist\GX_Text_Writer_V3.exe
pause
