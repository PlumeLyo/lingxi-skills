<#
.SYNOPSIS
    lingxi-skills 安装脚本（Windows PowerShell）
.DESCRIPTION
    将指定技能或全部技能安装到 WPS 灵犀技能目录。
.EXAMPLE
    .\install.ps1 docx                  # 安装单个技能
    .\install.ps1 docx pptx xlsx       # 安装多个技能
    .\install.ps1 --all                 # 安装全部
    .\install.ps1 --list                # 列出所有可用技能
    .\install.ps1 --uninstall docx      # 卸载指定技能
    .\install.ps1 --update              # 更新已安装的技能（覆盖）
#>

param(
    [Parameter(Position=0, ValueFromRemainingArguments=$true)]
    [string[]]$Skills,

    [switch]$All,
    [switch]$List,
    [switch]$Uninstall,
    [switch]$Update
)

$ErrorActionPreference = "Stop"

# 目标技能目录
$targetDir = Join-Path $env:APPDATA "WPS 灵犀\serverdir\skills"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-OK($msg)    { Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Info($msg)  { Write-Host "[..] $msg" -ForegroundColor Cyan }
function Write-Warn($msg)  { Write-Host "[!!] $msg" -ForegroundColor Yellow }
function Write-Err($msg)   { Write-Host "[XX] $msg" -ForegroundColor Red }

# 获取所有可用技能（排除 .git 和脚本文件）
function Get-AvailableSkills {
    Get-ChildItem -Path $scriptDir -Directory |
        Where-Object { $_.Name -ne ".git" -and $_.Name -ne ".github" } |
        Select-Object -ExpandProperty Name | Sort-Object
}

# 显示所有技能
if ($List) {
    Write-Host "`n可用技能：`n" -ForegroundColor White
    Get-AvailableSkills | ForEach-Object { Write-Host "  $_" }
    Write-Host "`n共 $(@(Get-AvailableSkills).Count) 个技能`n"
    exit 0
}

# 验证目标目录
if (-not (Test-Path $targetDir)) {
    $create = Read-Host "技能目录不存在: $targetDir`n是否创建? (Y/n)"
    if ($create -ne "n") {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        Write-OK "已创建 $targetDir"
    } else {
        Write-Err "取消安装"
        exit 1
    }
}

# 确定要操作的技能列表
$available = Get-AvailableSkills
$skillList = @()

if ($All) {
    $skillList = $available
} else {
    foreach ($s in $Skills) {
        if ($s.StartsWith("--")) { continue }
        if ($available -contains $s) {
            $skillList += $s
        } else {
            Write-Err "技能 '$s' 不存在"
            Write-Info "运行 .\install.ps1 --list 查看所有可用技能"
            exit 1
        }
    }
}

if ($skillList.Count -eq 0) {
    Write-Host "用法：" -ForegroundColor White
    Write-Host "  .\install.ps1 <技能名>          安装指定技能"
    Write-Host "  .\install.ps1 <技能1> <技能2>    安装多个技能"
    Write-Host "  .\install.ps1 --all              安装全部技能"
    Write-Host "  .\install.ps1 --list             列出所有可用技能"
    Write-Host "  .\install.ps1 --uninstall <技能>  卸载指定技能"
    Write-Host "  .\install.ps1 --update           更新已安装技能（覆盖）"
    exit 0
}

# 执行安装/卸载
if ($Uninstall) {
    foreach ($s in $skillList) {
        $dest = Join-Path $targetDir $s
        if (Test-Path $dest) {
            Remove-Item -Path $dest -Recurse -Force
            Write-OK "已卸载 $s"
        } else {
            Write-Warn "$s 未安装，跳过"
        }
    }
} else {
    $installed = 0
    $skipped = 0
    foreach ($s in $skillList) {
        $src = Join-Path $scriptDir $s
        $dest = Join-Path $targetDir $s

        if ((Test-Path $dest) -and -not $Update) {
            Write-Warn "$s 已存在，跳过（使用 --update 覆盖）"
            $skipped++
            continue
        }

        if (Test-Path $dest) { Remove-Item -Path $dest -Recurse -Force }
        Copy-Item -Path $src -Destination $dest -Recurse -Force
        Write-OK "$s$(if ($Update) { ' (已更新)' } else { '' })"
        $installed++
    }
    Write-Host "`n安装完成: $installed 个$(if ($skipped) { "，跳过 $skipped 个" })" -ForegroundColor White
}
