$taskName = 'XMAPP-DB-CACHE'
$scriptPath = 'C:\Users\Administrator\.openclaw\workspace\DjangoBlog\deploy\start-local-db-cache.ps1'

$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-ExecutionPolicy Bypass -File `"$scriptPath`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -RunLevel Highest -LogonType Interactive

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Force
Get-ScheduledTask -TaskName $taskName | Select-Object TaskName,State
