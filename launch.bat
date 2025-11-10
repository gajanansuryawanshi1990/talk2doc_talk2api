@echo off
REM Talk2Doc & Talk2API Launcher
REM Double-click this file to run the launcher

cd /d "%~dp0"
powershell.exe -ExecutionPolicy Bypass -File "launch.ps1"
pause
