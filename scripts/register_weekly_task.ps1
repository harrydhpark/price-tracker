# -*- coding: utf-8 -*-
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$TaskName = "LGE_TV_Price_Tracker_Weekly"
$TaskDescription = "Runs automated live TV price survey across European 11 countries and Australia, syncs workbooks, evaluates quality gates, and deploys updated dashboards to Firebase Hosting every Tuesday at 02:00 AM KST."
$WorkingDir = "d:\TV 유럽영업\15. AX Task\2026 AX 실행과제\04. Price Tracker"
$BatPath = "$WorkingDir\scripts\auto_survey_scheduler.bat"

Write-Host "======================================================="
Write-Host " Windows Task Scheduler Registration: $TaskName"
Write-Host " Target Batch : $BatPath"
Write-Host " Schedule     : Every Tuesday at 02:00 AM KST"
Write-Host "======================================================="

# Unregister previous task if exists
try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
} catch {}

# Create Trigger: Weekly on Tuesday at 02:00 AM
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Tuesday -At 02:00AM

# Create Action
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$BatPath`"" -WorkingDirectory $WorkingDir

# Create Settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
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

    Write-Host "`n✅ [SUCCESS] Windows Scheduled Task '$TaskName' successfully registered!"
    Write-Host "  • State    : $($RegisteredTask.State)"
    Write-Host "  • Trigger  : Weekly on Tuesday at 02:00 AM"
    Write-Host "  • Next Run : $((Get-ScheduledTaskInfo -TaskName $TaskName).NextRunTime)"
} catch {
    Write-Warning "PowerShell Register-ScheduledTask encountered: $_"
    Write-Host "Falling back to schtasks.exe..."
    $cmd = "schtasks.exe /create /tn `"$TaskName`" /tr `"$BatPath`" /sc weekly /d TUE /st 02:00 /f"
    Invoke-Expression $cmd
}
