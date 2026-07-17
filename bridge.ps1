<#
.SYNOPSIS
  A4S 协作桥 — 连接本地 Claude Code 与传感前锋服务器
.DESCRIPTION
  一键 pull → 显示待处理 task → push 结果
  每台机器有自己的标识，只显示分配给自己的 task。
#>

param(
  [Parameter(Position=0)]
  [ValidateSet("pull","push","status","task")]
  [string]$Action = "pull",

  [Parameter(Position=1)]
  [string]$TaskFile = "",

  [Parameter(Position=2)]
  [string]$Message = ""
)

# ========== 配置区 ==========
# 修改这里的机器标识（WS=公司台式, LP=笔记本, HM=家里台式）
$MACHINE_NAME = "WS"
$MACHINE_LABEL = switch ($MACHINE_NAME) {
  "WS" { "🏢 公司台式" }
  "LP" { "💻 笔记本" }
  "HM" { "🏠 家里台式" }
  default { "❓ 未知" }
}

$REPO_PATH = Split-Path -Parent $MyInvocation.MyCommand.Path
$TASKS_DIR = Join-Path $REPO_PATH "tasks"

# ========== 颜色输出 ==========
function Write-Info  { Write-Host "ℹ️  $($args)" -ForegroundColor Cyan }
function Write-Ok    { Write-Host "✅ $($args)" -ForegroundColor Green }
function Write-Warn  { Write-Host "⚠️  $($args)" -ForegroundColor Yellow }
function Write-Error { Write-Host "❌ $($args)" -ForegroundColor Red }
function Write-Title { Write-Host ""
  Write-Host "══════════════════════════════════════════════" -ForegroundColor Magenta
  Write-Host "  $($args)" -ForegroundColor Magenta
  Write-Host "══════════════════════════════════════════════" -ForegroundColor Magenta
}

# ========== 功能函数 ==========

function Git-Pull {
  Write-Info "从 GitHub 拉取最新..."
  Set-Location $REPO_PATH
  $result = git pull origin master 2>&1 | Out-String
  if ($LASTEXITCODE -eq 0) {
    Write-Ok "拉取成功"
    return $true
  } else {
    Write-Error "拉取失败: $result"
    return $false
  }
}

function Git-Push {
  param([string]$Msg)
  Write-Info "推送到 GitHub..."
  Set-Location $REPO_PATH
  git add -A 2>&1 | Out-Null
  git status --short 2>&1 | Out-String | Write-Host -ForegroundColor Gray
  $commitMsg = if ($Msg) { $Msg } else { "[$MACHINE_NAME] $(Get-Date -Format 'yyyy-MM-dd HH:mm') 自动提交" }
  git commit -m $commitMsg 2>&1 | Out-String | Write-Host -ForegroundColor Gray
  $result = git push origin master 2>&1 | Out-String
  if ($LASTEXITCODE -eq 0) {
    Write-Ok "推送成功"
    return $true
  } else {
    Write-Error "推送失败: $result"
    return $false
  }
}

function Show-MyTasks {
  Write-Title "$MACHINE_LABEL — 待处理 Task"

  $tasks = @(Get-ChildItem "$TASKS_DIR\*.md" -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match "^T\d+-(WS|LP|HM|ALL)-" })

  if ($tasks.Count -eq 0) {
    Write-Host "  暂无任务" -ForegroundColor Gray
    return
  }

  foreach ($t in $tasks) {
    $content = Get-Content $t.FullName -Raw
    $statusMatch = [regex]::Match($content, '状态:\s*(\S+)')
    $status = if ($statusMatch.Success) { $statusMatch.Groups[1].Value } else { "未知" }
    $prioMatch = [regex]::Match($content, '优先级:\s*(\S+)')
    $prio = if ($prioMatch.Success) { $prioMatch.Groups[1].Value } else { "" }
    $descMatch = [regex]::Match($content, '## 任务描述\s*\n(.+?)(?=\n##|\z)')
    $desc = if ($descMatch.Success) { $descMatch.Groups[1].Value.Trim() } else { "无描述" }

    $statusColor = switch ($status) {
      "⏳" { "Yellow" }
      "✅" { "Green" }
      "🔄" { "Cyan" }
      "❌" { "Red" }
      default { "Gray" }
    }

    Write-Host ""
    Write-Host "  $($t.BaseName)  [$(if ($prio) { $prio } else { '' })]" -ForegroundColor White
    Write-Host "  状态: " -NoNewline; Write-Host "$status" -ForegroundColor $statusColor
    Write-Host "  描述: $desc" -ForegroundColor Gray
    Write-Host ""
  }
}

function Show-Task {
  param([string]$FileName)
  $taskPath = Join-Path $TASKS_DIR $FileName
  if (-not (Test-Path $taskPath)) {
    # 尝试前缀匹配
    $matches = Get-ChildItem "$TASKS_DIR\$FileName*.md" -ErrorAction SilentlyContinue
    if ($matches.Count -eq 0) {
      Write-Error "找不到 task: $FileName"
      return
    }
    $taskPath = $matches[0].FullName
  }
  Get-Content $taskPath | Write-Host
}

# ========== 主逻辑 ==========

switch ($Action) {
  "pull" {
    Write-Title "A4S 协作桥 — $MACHINE_LABEL"
    if (Git-Pull) {
      Show-MyTasks
    }
    Write-Host ""
    Write-Info "用法:"
    Write-Host "  .\bridge.ps1 pull              ← 拉取最新 + 看 task" -ForegroundColor Gray
    Write-Host "  .\bridge.ps1 push '提交说明'    ← 推送结果" -ForegroundColor Gray
    Write-Host "  .\bridge.ps1 task T001          ← 查看具体 task 内容" -ForegroundColor Gray
    Write-Host "  .\bridge.ps1 status             ← 查看仓库状态" -ForegroundColor Gray
  }

  "push" {
    Git-Push -Msg $Message
  }

  "status" {
    Set-Location $REPO_PATH
    git status
  }

  "task" {
    Show-Task -FileName $TaskFile
  }
}
