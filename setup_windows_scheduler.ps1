# Study Pilot - Windows Task Scheduler Daily Sync Setup
# This registers a daily task in Windows Task Scheduler to run Moodle sync every 24 hours.

$TaskName = "StudyPilot_Moodle_DailySync"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$PythonExe = Join-Path $ScriptDir "backend\.venv\Scripts\python.exe"
$SyncScript = Join-Path $ScriptDir "backend\run_sync.py"

if (-not (Test-Path $PythonExe)) {
    Write-Error "Python virtual environment not found at $PythonExe. Please ensure backend/.venv is set up."
    exit 1
}

Write-Host "Registering daily Moodle check task: $TaskName"
Write-Host "Python: $PythonExe"
Write-Host "Script: $SyncScript"

# Define Action
$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$SyncScript`" sync --trigger scheduled" -WorkingDirectory $ScriptDir

# Define Trigger: Daily at 04:00 AM
$Trigger = New-ScheduledTaskTrigger -Daily -At "04:00 AM"

# Define Settings: allow wake-to-run, retry on failure
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register or update task
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Study Pilot 24-hour automatic Moodle monitor" -Force

Write-Host "`nTask '$TaskName' registered successfully in Windows Task Scheduler!" -ForegroundColor Green
Write-Host "It will automatically run every day at 04:00 AM independently of the web dashboard."
