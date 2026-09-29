@echo off
cd /d "%~dp0"
py -m pip install pyinstaller
py -m PyInstaller --noconfirm --clean --onefile --windowed --name MView_SCA_Toolkit app.py
echo.
echo EXE: %CD%\dist\MView_SCA_Toolkit.exe
pause
