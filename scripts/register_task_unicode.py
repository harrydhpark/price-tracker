# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import base64

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BAT_PATH = os.path.join(ROOT_DIR, "scripts", "auto_survey_scheduler.bat")

ps_script = f"""
$TaskName = "LGE_TV_Price_Tracker_Weekly"
$TaskDescription = "Runs automated live TV price survey across European 11 countries and Australia every Tuesday at 02:00 AM KST."
$WorkingDir = @'
{ROOT_DIR}
'@
$BatPath = @'
{BAT_PATH}
'@

try {{
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
}} catch {{}}

$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Tuesday -At 02:00AM
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$BatPath`"" -WorkingDirectory $WorkingDir
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 3) `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 15)

$RegisteredTask = Register-ScheduledTask `
    -TaskName $TaskName `
    -Description $TaskDescription `
    -Trigger $Trigger `
    -Action $Action `
    -Settings $Settings `
    -ErrorAction Stop

Write-Host "SUCCESS: $($RegisteredTask.TaskName)"
"""

encoded = base64.b64encode(ps_script.encode("utf-16le")).decode("ascii")
res = subprocess.run(["powershell.exe", "-NoProfile", "-EncodedCommand", encoded], capture_output=True, text=True, encoding="utf-8", errors="replace")
print("STDOUT:", res.stdout.strip())
if res.stderr:
    print("STDERR:", res.stderr.strip())
sys.exit(res.returncode)
