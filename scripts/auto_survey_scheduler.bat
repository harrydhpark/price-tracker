@echo off
chcp 65001 > nul
setlocal

pushd "%~dp0.."
set "ROOT_DIR=%CD%"

if not exist logs mkdir logs

set "ACTION=%~1"
if "%ACTION%"=="" set "ACTION=nightly"

echo ======================================================= >> logs\scheduler_bat.log
echo [SCHEDULER BAT] Action: %ACTION% at %date% %time% >> logs\scheduler_bat.log
echo [SCHEDULER BAT] ROOT_DIR: "%ROOT_DIR%" >> logs\scheduler_bat.log
echo ======================================================= >> logs\scheduler_bat.log

set "PYTHON_EXE=%ROOT_DIR%\python_env\python.exe"
if not exist "%PYTHON_EXE%" (
    echo [ERROR] python_env\python.exe not found at "%PYTHON_EXE%" >> logs\scheduler_bat.log
    popd
    exit /b 1
)

if /i "%ACTION%"=="canary" goto :DO_CANARY
if /i "%ACTION%"=="proposal" goto :DO_PROPOSAL
if /i "%ACTION%"=="nightly" goto :DO_NIGHTLY
if /i "%ACTION%"=="all" goto :DO_ALL

echo [ERROR] Unknown action "%ACTION%". Options: nightly, canary, proposal, all >> logs\scheduler_bat.log
popd
exit /b 1

:DO_CANARY
echo [SCHEDULER] Running Morning Daily Canary Monitor... >> logs\scheduler_bat.log
"%PYTHON_EXE%" scripts\verify\daily_canary.py >> logs\scheduler_bat.log 2>&1
set EXIT_CODE=%ERRORLEVEL%
goto :END

:DO_PROPOSAL
echo [SCHEDULER] Running Weekly Improvement Proposal Engine... >> logs\scheduler_bat.log
"%PYTHON_EXE%" scripts\verify\improvement_engine.py >> logs\scheduler_bat.log 2>&1
set EXIT_CODE=%ERRORLEVEL%
goto :END

:DO_NIGHTLY
echo [SCHEDULER] Running Full Nightly Survey Pipeline (Hard Halt Gate Policy)... >> logs\scheduler_bat.log
set STEALTH_FAST=1
"%PYTHON_EXE%" scripts\run_full_survey_pipeline.py --stealth-fast >> logs\scheduler_bat.log 2>&1
set EXIT_CODE=%ERRORLEVEL%
goto :END

:DO_ALL
echo [SCHEDULER] Running Canary -> Nightly Survey -> Proposal Engine... >> logs\scheduler_bat.log
"%PYTHON_EXE%" scripts\verify\daily_canary.py >> logs\scheduler_bat.log 2>&1
"%PYTHON_EXE%" scripts\run_full_survey_pipeline.py --stealth-fast >> logs\scheduler_bat.log 2>&1
set EXIT_CODE=%ERRORLEVEL%
"%PYTHON_EXE%" scripts\verify\improvement_engine.py >> logs\scheduler_bat.log 2>&1
goto :END

:END
echo [SCHEDULER BAT] Completed %ACTION% with Exit Code: %EXIT_CODE% at %date% %time% >> logs\scheduler_bat.log
echo ======================================================= >> logs\scheduler_bat.log

popd
exit /b %EXIT_CODE%
