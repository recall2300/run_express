<#
.SYNOPSIS
    Windows 로그온 시 WSL 배포판을 자동으로 기동시켜, 그 안의 run-express
    systemd 서비스가 함께 올라오도록 작업 스케줄러 항목을 등록한다.

.DESCRIPTION
    WSL2 배포판은 Windows 부팅만으로는 시작되지 않는다. 로그온 시점에
    'wsl.exe -d <배포판> -e /bin/true' 를 한 번 실행해 배포판을 깨우면
    systemd 가 기동되고, enable 해 둔 run-express 서비스가 자동 실행된다.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\wsl_autostart.ps1
    powershell -ExecutionPolicy Bypass -File scripts\wsl_autostart.ps1 -Distro Ubuntu-24.04
    powershell -ExecutionPolicy Bypass -File scripts\wsl_autostart.ps1 -Remove
#>
[CmdletBinding()]
param(
    [string]$Distro   = "Ubuntu",
    [string]$TaskName = "RunExpress-WSL-Autostart",
    [switch]$Remove
)

$ErrorActionPreference = "Stop"

if ($Remove) {
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "[OK] 작업 '$TaskName' 을 삭제했습니다." -ForegroundColor Green
    } catch {
        Write-Host "[정보] 삭제할 작업이 없습니다: $TaskName" -ForegroundColor Yellow
    }
    return
}

# 1) 배포판 존재 확인
$distros = (& wsl.exe --list --quiet) -replace "`0", "" |
           ForEach-Object { $_.Trim() } |
           Where-Object { $_ -ne "" }

if ($distros -notcontains $Distro) {
    Write-Host "[오류] '$Distro' 배포판을 찾을 수 없습니다." -ForegroundColor Red
    Write-Host "설치된 배포판:" -ForegroundColor Yellow
    $distros | ForEach-Object { Write-Host "  - $_" }
    Write-Host ""
    Write-Host "설치: wsl --install -d Ubuntu" -ForegroundColor Cyan
    exit 1
}

# 2) 작업 등록 (로그온 30초 후 배포판 기동)
$action = New-ScheduledTaskAction -Execute "wsl.exe" `
                                  -Argument "-d $Distro -e /bin/true"

$trigger = New-ScheduledTaskTrigger -AtLogOn
$trigger.Delay = "PT30S"

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
                                         -DontStopIfGoingOnBatteries `
                                         -StartWhenAvailable `
                                         -ExecutionTimeLimit ([TimeSpan]::Zero)

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
                                        -LogonType Interactive `
                                        -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName `
                       -Action $action `
                       -Trigger $trigger `
                       -Settings $settings `
                       -Principal $principal `
                       -Description "로그온 시 WSL($Distro) 을 기동해 run-express 서비스를 자동 실행" `
                       -Force | Out-Null

Write-Host "[OK] 작업 '$TaskName' 을 등록했습니다. (배포판: $Distro)" -ForegroundColor Green
Write-Host ""
Write-Host "지금 바로 시험 실행:  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Cyan
Write-Host "등록 해제:            powershell -File scripts\wsl_autostart.ps1 -Remove" -ForegroundColor Cyan
