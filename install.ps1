<#
.SYNOPSIS
    lingxi-skills 安装脚本（Windows PowerShell）
.DESCRIPTION
    将指定技能或全部技能安装到目标目录。
    默认安装到 WPS 灵犀技能目录，支持 --target 自定义路径供其他 Agent 使用。
.EXAMPLE
    .\install.ps1 docx                              # 安装到灵犀默认目录
    .\install.ps1 docx --target D:\my-agent\skills  # 安装到自定义目录
    .\install.ps1 --cat content                      # 安装整个分类
    .\install.ps1 --all                             # 安装全部
    .\install.ps1 --list                            # 列出所有可用技能
    .\install.ps1 --uninstall docx                   # 卸载指定技能
#>

param(
    [Parameter(Position=0, ValueFromRemainingArguments=$true)]
    [string[]]$Args2,

    [switch]$All,
    [switch]$List,
    [switch]$Categories,
    [switch]$Uninstall,
    [switch]$Update,
    [string]$Cat,
    [string]$Target
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 安装目标目录：优先 --target，其次灵犀默认路径
$defaultDir = Join-Path $env:APPDATA "WPS 灵犀\serverdir\skills"
$targetDir = if ($Target) { 
    $Target 
} elseif (Test-Path $defaultDir) { 
    $defaultDir 
} else { 
    Join-Path $scriptDir "installed"  # fallback：仓库内的 installed/ 目录
}

# 分类目录名（排除文件和隐藏目录，且自身不含 SKILL.md）
$catDirs = @(Get-ChildItem -Path $scriptDir -Directory |
    Where-Object { $_.Name -notin @(".git",".github","installed") -and (Test-Path (Join-Path $_.FullName "SKILL.md")) -eq $false } |
    Select-Object -ExpandProperty Name)

function Write-OK($msg)    { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Info($msg)  { Write-Host "  [..] $msg" -ForegroundColor Cyan }
function Write-Warn($msg)  { Write-Host "  [!!] $msg" -ForegroundColor Yellow }
function Write-Err($msg)   { Write-Host "  [XX] $msg" -ForegroundColor Red }

# 扫描所有技能：返回 @{ name="xxx"; category="yyy"; sourceDir="..." }
function Get-AvailableSkills {
    $result = @()
    foreach ($cat in $catDirs) {
        $catPath = Join-Path $scriptDir $cat
        Get-ChildItem -Path $catPath -Directory |
            Where-Object { $_.Name -notlike ".*" -and (Test-Path (Join-Path $_.FullName "SKILL.md")) } |
            ForEach-Object {
                $result += @{
                    name      = $_.Name
                    category  = $cat
                    sourceDir = $_.FullName
                }
            }
    }
    return $result | Sort-Object { $_.name }
}

# 显示分类
if ($Categories) {
    Write-Host "`n技能分类：`n" -ForegroundColor White
    $all = Get-AvailableSkills
    foreach ($cat in $catDirs) {
        $count = @($all | Where-Object { $_.category -eq $cat }).Count
        Write-Host "  $cat ($count)" -ForegroundColor Yellow
        $all | Where-Object { $_.category -eq $cat } | ForEach-Object {
            Write-Host "    $($_.name)"
        }
    }
    Write-Host "`n共 $($all.Count) 个技能`n"
    exit 0
}

# 显示所有技能
if ($List) {
    Write-Host "`n可用技能：`n" -ForegroundColor White
    $all = Get-AvailableSkills
    foreach ($cat in $catDirs) {
        Write-Host "[$cat]" -ForegroundColor Yellow
        $all | Where-Object { $_.category -eq $cat } | ForEach-Object {
            Write-Host "  $($_.name)"
        }
    }
    Write-Host "`n共 $($all.Count) 个技能`n"
    exit 0
}

# 确认目标目录
Write-Info "安装目标: $targetDir"
if (-not (Test-Path $targetDir)) {
    $create = Read-Host "  目录不存在，是否创建? (Y/n)"
    if ($create -ne "n") {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        Write-OK "已创建 $targetDir"
    } else {
        Write-Err "取消安装"
        exit 1
    }
}

# 确定要操作的技能
$all = Get-AvailableSkills
$skillMap = @{}
$all | ForEach-Object { $skillMap[$_.name] = $_ }

$skillList = @()

if ($Cat) {
    if ($catDirs -notcontains $Cat) {
        Write-Err "分类 '$Cat' 不存在"
        Write-Info "可用分类: $($catDirs -join ', ')"
        exit 1
    }
    $skillList = @($all | Where-Object { $_.category -eq $Cat })
    Write-Info "将安装分类 '$Cat' 下的 $($skillList.Count) 个技能"
} elseif ($All) {
    $skillList = $all
} else {
    foreach ($s in $Args2) {
        if ($s.StartsWith("--")) { continue }
        if ($skillMap.ContainsKey($s)) {
            $skillList += $skillMap[$s]
        } else {
            Write-Err "技能 '$s' 不存在"
            Write-Info "运行 .\install.ps1 --list 查看所有可用技能"
            exit 1
        }
    }
}

if ($skillList.Count -eq 0) {
    Write-Host "用法：" -ForegroundColor White
    Write-Host "  .\install.ps1 <技能名>                           安装到灵犀默认目录"
    Write-Host "  .\install.ps1 <技能名> --target <目录>             安装到自定义目录"
    Write-Host "  .\install.ps1 --cat <分类名>                      安装整个分类"
    Write-Host "  .\install.ps1 --all                              安装全部技能"
    Write-Host "  .\install.ps1 --all --target <目录>                全部安装到自定义目录"
    Write-Host "  .\install.ps1 --list                              列出所有可用技能"
    Write-Host "  .\install.ps1 --categories                        列出分类及技能"
    Write-Host "  .\install.ps1 --uninstall <技能>                   卸载指定技能"
    Write-Host "  .\install.ps1 --update <技能>                      更新已安装技能"
    exit 0
}

# 执行安装/卸载
if ($Uninstall) {
    foreach ($s in $skillList) {
        $dest = Join-Path $targetDir $s.name
        if (Test-Path $dest) {
            Remove-Item -Path $dest -Recurse -Force
            Write-OK "已卸载 $($s.name)"
        } else {
            Write-Warn "$($s.name) 未安装，跳过"
        }
    }
} else {
    $installed = 0
    $skipped = 0
    foreach ($s in $skillList) {
        $dest = Join-Path $targetDir $s.name
        if ((Test-Path $dest) -and -not $Update) {
            Write-Warn "$($s.name) 已存在，跳过（使用 --update 覆盖）"
            $skipped++
            continue
        }
        if (Test-Path $dest) { Remove-Item -Path $dest -Recurse -Force }
        Copy-Item -Path $s.sourceDir -Destination $dest -Recurse -Force
        Write-OK "$($s.name)$(if ($Update) { ' (已更新)' })"
        $installed++
    }
    Write-Host "`n安装完成: $installed 个$(if ($skipped) { "，跳过 $skipped 个" })" -ForegroundColor White
}
