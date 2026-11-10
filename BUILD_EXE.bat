@echo off
title Build Mushy Cute Corner Waybill Generator
cd /d "%~dp0"
echo Installing required packages...
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo Installation failed. Check your Python installation and internet connection.
  pause
  exit /b 1
)
echo.
echo Building Windows EXE...
py -m PyInstaller --noconfirm --clean --onefile --windowed --name "MushyWaybill" waybill.py
if errorlevel 1 (
  echo.
  echo Build failed.
  pause
  exit /b 1
)
echo.
echo SUCCESS! Your EXE is here:
echo %CD%\dist\MushyWaybill.exe
pause
