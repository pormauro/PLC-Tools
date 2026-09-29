@echo off
setlocal
python -m PyInstaller --noconfirm --onefile --windowed --name GX_Text_Writer_V3_1 gx_text_writer_gui_v3_1.py
echo.
echo EXE generado en dist\GX_Text_Writer_V3_1.exe
pause
