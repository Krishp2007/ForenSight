# ForenSight — Register auto-start on Windows login
# Run ONCE as Administrator: right-click → Run as Administrator

$root       = "d:\ForenSight\ForenSight"
$scriptPath = "$root\start-all.ps1"
$taskName   = "ForenSight_AutoStart"

# Remove old task if it exists
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

$action  = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"$scriptPath`""

# Trigger: when any user logs on
$trigger = New-ScheduledTaskTrigger -AtLogOn

# Run as current user, no password required
$principal = New-ScheduledTaskPrincipal `
    -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive `
    -RunLevel Highest

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0) `   # no timeout
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable $true

Register-ScheduledTask `
    -TaskName  $taskName `
    -Action    $action `
    -Trigger   $trigger `
    -Principal $principal `
    -Settings  $settings `
    -Description "Auto-start ForenSight API, frontend, and Docker on login" `
    -Force

Write-Host "Task '$taskName' registered." -ForegroundColor Green
Write-Host "ForenSight will now start automatically every time you log in." -ForegroundColor Cyan
Write-Host "To remove: Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false" -ForegroundColor Gray
