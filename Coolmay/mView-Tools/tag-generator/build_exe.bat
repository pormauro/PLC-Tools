@echo off
setlocal
cd /d "%~dp0"
py -m pip install -r requirements.txt
py -m pip install pyinstaller
py -m PyInstaller --noconfirm --clean --onefile --windowed --name MView_Tag_Generator app.py
echo.
echo EXE: %CD%\dist\MView_Tag_Generator.exe
pause
