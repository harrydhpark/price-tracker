@echo off
chcp 65001 > nul
setlocal

pushd "%~dp0.."
set "ROOT_DIR=%CD%"

if not exist logs mkdir logs

echo ======================================================= >> logs\scheduler_bat.log
echo [SCHEDULER BAT] Triggered at %date% %time% >> logs\scheduler_bat.log
echo [SCHEDULER BAT] ROOT_DIR: "%ROOT_DIR%" >> logs\scheduler_bat.log
echo ======================================================= >> logs\scheduler_bat.log

set "PYTHON_EXE=%ROOT_DIR%\python_env\python.exe"
if not exist "%PYTHON_EXE%" (
    echo [ERROR] python_env\python.exe not found at "%PYTHON_EXE%" >> logs\scheduler_bat.log
    popd
    exit /b 1
)

set STEALTH_FAST=1
"%PYTHON_EXE%" scripts\run_full_survey_pipeline.py --stealth-fast --allow-partial >> logs\scheduler_bat.log 2>&1
set EXIT_CODE=%ERRORLEVEL%

echo [SCHEDULER BAT] Completed with Exit Code: %EXIT_CODE% at %date% %time% >> logs\scheduler_bat.log
echo ======================================================= >> logs\scheduler_bat.log

popd
exit /b %EXIT_CODE%
