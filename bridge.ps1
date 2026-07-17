<#
.SYNOPSIS
  A4S Collaboration Bridge
.DESCRIPTION
  Connect local Claude Code with the Sensing Vanguard server.
  One command to pull, show tasks, and push results.
#>

param(
  [Parameter(Position=0)]
  [string]$Action = "pull",

  [Parameter(Position=1)]
  [string]$TaskFile = "",

  [Parameter(Position=2)]
  [string]$Message = ""
)

# ========== Configuration ==========
# Machine ID: WS=Company Desktop, LP=Laptop, HM=Home Desktop
$MACHINE_NAME = "WS"

$REPO_PATH = Split-Path -Parent $MyInvocation.MyCommand.Path
$TASKS_DIR = Join-Path $REPO_PATH "tasks"

# ========== Machine labels ==========
$MACHINE_LABEL = switch ($MACHINE_NAME) {
  "WS" { "[WS] Company Desktop" }
  "LP" { "[LP] Laptop" }
  "HM" { "[HM] Home Desktop" }
  default { "[??] Unknown" }
}

# ========== Utility functions ==========
function Write-Info  { Write-Host "[i] $($args)" -ForegroundColor Cyan }
function Write-Ok    { Write-Host "[OK] $($args)" -ForegroundColor Green }
function Write-Warn  { Write-Host "[!] $($args)" -ForegroundColor Yellow }
function Write-Error { Write-Host "[X] $($args)" -ForegroundColor Red }
function Write-Sep   { Write-Host ("="*55) -ForegroundColor Magenta }
function Write-Title { Write-Host ""; Write-Sep; Write-Host "  $($args)" -ForegroundColor Magenta; Write-Sep }

# ========== Git operations ==========
function Git-Pull {
  Write-Info "Pulling latest from GitHub..."
  Set-Location $REPO_PATH
  $result = git pull origin master 2>&1 | Out-String
  if ($LASTEXITCODE -eq 0) {
    Write-Ok "Pull successful"
    return $true
  } else {
    Write-Error "Pull failed: $result"
    return $false
  }
}

function Git-Push {
  param([string]$Msg)
  Write-Info "Pushing to GitHub..."
  Set-Location $REPO_PATH
  git add -A 2>&1 | Out-Null
  $changes = git status --short 2>&1 | Out-String
  if ($changes.Trim()) {
    Write-Host $changes -ForegroundColor Gray
  } else {
    Write-Warn "No changes to commit"
    return $true
  }
  $commitMsg = if ($Msg) { $Msg } else { "[$MACHINE_NAME] $(Get-Date -Format 'yyyy-MM-dd HH:mm') auto commit" }
  git commit -m $commitMsg 2>&1 | Out-String | Write-Host -ForegroundColor Gray
  $result = git push origin master 2>&1 | Out-String
  if ($LASTEXITCODE -eq 0) {
    Write-Ok "Push successful"
    return $true
  } else {
    Write-Error "Push failed: $result"
    return $false
  }
}

function Show-MyTasks {
  Write-Title "$MACHINE_LABEL -- Pending Tasks"

  $pattern = "^T\d+-($MACHINE_NAME|ALL)-"
  $tasks = @(Get-ChildItem "$TASKS_DIR\*.md" -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match $pattern })

  if ($tasks.Count -eq 0) {
    Write-Host "  (no pending tasks)" -ForegroundColor Gray
    return
  }

  foreach ($t in $tasks) {
    $content = Get-Content $t.FullName -Raw
    $statusMatch = [regex]::Match($content, 'Status:\s*(\S+)')
    $status = if ($statusMatch.Success) { $statusMatch.Groups[1].Value } else { "unknown" }
    $prioMatch = [regex]::Match($content, 'Priority:\s*(\S+)')
    $prio = if ($prioMatch.Success) { $prioMatch.Groups[1].Value } else { "" }
    $descMatch = [regex]::Match($content, '## Description\s*\n(.+?)(?=\n## |\z)', [System.Text.RegularExpressions.RegexOptions]::Singleline)
    $desc = if ($descMatch.Success) { $descMatch.Groups[1].Value.Trim() } else { "(no description)" }

    Write-Host ""
    Write-Host "  $($t.BaseName) [$prio]" -ForegroundColor White
    Write-Host "  Status: $status"
    Write-Host "  $desc" -ForegroundColor Gray
    Write-Host ""
  }
}

function Show-Task {
  param([string]$FileName)
  $taskPath = Join-Path $TASKS_DIR $FileName
  if (-not (Test-Path $taskPath)) {
    $matches = Get-ChildItem "$TASKS_DIR\$FileName*.md" -ErrorAction SilentlyContinue
    if ($matches.Count -eq 0) {
      Write-Error "Task not found: $FileName"
      return
    }
    $taskPath = $matches[0].FullName
  }
  Get-Content $taskPath | Write-Host
}

# ========== Main ==========
switch ($Action) {
  "pull" {
    Write-Title "A4S Collaboration Bridge -- $MACHINE_LABEL"
    if (Git-Pull) {
      Show-MyTasks
    }
    Write-Host ""
    Write-Info "Usage:"
    Write-Host "  .\bridge.ps1 pull              - Pull latest + show tasks" -ForegroundColor Gray
    Write-Host "  .\bridge.ps1 push 'message'     - Push results" -ForegroundColor Gray
    Write-Host "  .\bridge.ps1 task T001          - Show task details" -ForegroundColor Gray
    Write-Host "  .\bridge.ps1 status             - Show git status" -ForegroundColor Gray
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
