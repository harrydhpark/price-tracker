# -*- coding: utf-8 -*-
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$TaskName = "LGE_TV_Price_Tracker_Daily"
$LegacyTaskName = "LGE_TV_Price_Tracker_Weekly"
$TaskDescription = "Runs automated live TV price survey across European 15 countries and Australia, syncs workbooks, evaluates quality gates, and deploys updated dashboards to Firebase Hosting every day at 05:00 AM KST."
$WorkingDir = (Resolve-Path "$PSScriptRoot\..").Path
$BatPath = Join-Path $WorkingDir "scripts\auto_survey_scheduler.bat"

Write-Host "======================================================="
Write-Host " Windows Task Scheduler Registration: $TaskName"
Write-Host " Target Batch : $BatPath"
Write-Host " Schedule     : Every day at 05:00 AM KST"
Write-Host "======================================================="

# Unregister previous / legacy tasks if exists
try {
    Unregister-ScheduledTask -TaskName $LegacyTaskName -Confirm:$false -ErrorAction SilentlyContinue
} catch {}
try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
} catch {}

# Create Trigger: Daily at 05:00 AM
$Trigger = New-ScheduledTaskTrigger -Daily -At 05:00AM

# Create Action
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$BatPath`"" -WorkingDirectory $WorkingDir

# Create Settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 15)

# Register Task for current user
try {
    $RegisteredTask = Register-ScheduledTask `
        -TaskName $TaskName `
        -Description $TaskDescription `
        -Trigger $Trigger `
        -Action $Action `
        -Settings $Settings `
        -ErrorAction Stop

    Write-Host "`n [SUCCESS] Windows Scheduled Task '$TaskName' successfully registered!"
    Write-Host "  * State    : $($RegisteredTask.State)"
    Write-Host "  * Trigger  : Daily at 05:00 AM"
    Write-Host "  * Next Run : $((Get-ScheduledTaskInfo -TaskName $TaskName).NextRunTime)"
} catch {
    Write-Warning "PowerShell Register-ScheduledTask encountered: $_"
    Write-Host "Falling back to schtasks.exe..."
    $cmd = "schtasks.exe /create /tn `"$TaskName`" /tr `"$BatPath`" /sc daily /st 05:00 /f"
    Invoke-Expression $cmd
}
