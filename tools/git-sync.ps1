<#
.SYNOPSIS
    一键同步 PPCU_TestBench 项目到 GitHub
.DESCRIPTION
    自动执行 git add → commit → push (通过代理)
.PARAMETER Message
    提交信息。不传则自动生成时间戳信息。
.PARAMETER DryRun
    仅显示要执行的操作，不实际运行。
.EXAMPLE
    ./tools/git-sync.ps1 -Message "feat: 完成 M1 通信层"
#>
param(
    [string]$Message = "",
    [switch]$DryRun
)

if (-not $Message) {
    $Message = "sync: auto update at $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
}

Write-Host "`n  git-sync: $Message`n" -ForegroundColor Cyan

if (-not $DryRun) {
    git add -A
    git commit --allow-empty -m "$Message"
    git -c http.proxy=http://127.0.0.1:17897 -c https.proxy=http://127.0.0.1:17897 push
}

Write-Host "`n  Done." -ForegroundColor Green
