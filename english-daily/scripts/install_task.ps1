# 注册/更新「英语每日一句」的 Windows 计划任务。
# 触发方式：
#   1) 每天 07:30（电脑开着时）
#   2) 每次登录后 2 分钟（电脑关了一夜，早上开机登录就会补推）
# 两个触发谁先到都行，run.py 内部按日期去重，一天只会推一条。

param(
    [string]$Time = "07:30",
    [string]$TaskName = "EnglishDaily"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$bat  = Join-Path $PSScriptRoot "run_daily.bat"

if (-not (Test-Path $bat)) {
    Write-Host "[!] 找不到 $bat" -ForegroundColor Red
    exit 1
}

$done = $false
try {
    $action   = New-ScheduledTaskAction -Execute $bat -WorkingDirectory $root
    $daily    = New-ScheduledTaskTrigger -Daily -At $Time
    $logon    = New-ScheduledTaskTrigger -AtLogOn
    $logon.Delay = "PT2M"

    # 对笔记本很关键：允许用电池跑、错过会补跑、能唤醒
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -WakeToRun `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

    Register-ScheduledTask -TaskName $TaskName -Action $action `
        -Trigger @($daily, $logon) -Settings $settings `
        -Description "每天推送一句英语，脚本按日期去重" -Force | Out-Null
    $done = $true

    Write-Host "[OK] 任务 $TaskName 已就绪" -ForegroundColor Green
    Write-Host "     - 每天 $Time 触发（电脑开着时）"
    Write-Host "     - 每次登录后 2 分钟触发（关机一夜，早上开机就补推）"
    Write-Host "     - 已开启：电池供电也跑、错过会补跑、可唤醒电脑"
} catch {
    Write-Host "[!] 高级注册方式不可用：$($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "    改用 schtasks 兜底（会建两个任务，效果一样）……"
}

if (-not $done) {
    schtasks /Create /TN $TaskName /TR "`"$bat`"" /SC DAILY /ST $Time /F | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[X] 创建失败，请右键本文件 -> 以管理员身份运行。" -ForegroundColor Red
        exit 1
    }
    schtasks /Create /TN "${TaskName}_Logon" /TR "`"$bat`"" /SC ONLOGON /F | Out-Null

    Write-Host "[OK] 已用兜底方式创建两个任务：" -ForegroundColor Green
    Write-Host "     - $TaskName         每天 $Time"
    Write-Host "     - ${TaskName}_Logon  每次登录"
    Write-Host "[i] 「电池供电也运行」这次没设置上，建议手动补一下：" -ForegroundColor Yellow
    Write-Host "    任务计划程序 -> $TaskName -> 属性 -> 条件 -> 取消勾选「只有在计算机使用交流电源时才启动此任务」"
}

Write-Host ""
Write-Host " 查看： schtasks /Query /TN $TaskName /V /FO LIST"
Write-Host " 删除： schtasks /Delete /TN $TaskName /F"