<#
.SYNOPSIS
  A4S Collaboration Bridge — multi-project task orchestrator
.DESCRIPTION
  Unified task hub for all A4S projects.
  Pull tasks from the A4S repo, switch to any project, and push results.
#>

param(
  [Parameter(Position=0)]
  [string]$Action = "pull",

  [Parameter(Position=1)]
  [string]$Arg1 = "",

  [Parameter(Position=2)]
  [string]$Arg2 = ""
)

# ========== Configuration ==========
# Machine ID: WS=Company Desktop, LP=Laptop, HM=Home Desktop
$MACHINE_NAME = "WS"

$REPO_PATH = Split-Path -Parent $MyInvocation.MyCommand.Path
$TASKS_DIR = Join-Path $REPO_PATH "tasks"
$PARENT_DIR = Split-Path -Parent $REPO_PATH

# ========== Project registry ==========
$PROJECTS = @{
  "a4s"  = @{ Path = $REPO_PATH; Remote = "origin"; Label = "A4S Chem-Lab" }
  "labvla" = @{ Path = Join-Path $PARENT_DIR "labvla-mujoco"; Remote = "origin"; Label = "LabVLA-MuJoCo" }
}
$CURRENT_PROJECT = "a4s"

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
  param([string]$Proj = "a4s")
  $p = $PROJECTS[$Proj]
  if (-not (Test-Path $p.Path)) {
    Write-Error "Project path not found: $($p.Path)"
    return $false
  }
  Write-Info "Pulling $($p.Label)..."
  Set-Location $p.Path
  $result = git pull $p.Remote main 2>&1 | Out-String
  if ($LASTEXITCODE -eq 0) {
    Write-Ok "$($p.Label) up to date"
    return $true
  } else {
    # Try master branch
    $result = git pull $p.Remote master 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0) {
      Write-Ok "$($p.Label) up to date"
      return $true
    }
    Write-Error "Pull failed: $result"
    return $false
  }
}

function Git-Push {
  param([string]$Proj = "a4s", [string]$Msg = "")
  $p = $PROJECTS[$Proj]
  Set-Location $p.Path
  Write-Info "Pushing to $($p.Label)..."
  git add -A 2>&1 | Out-Null
  $changes = git status --short 2>&1 | Out-String
  if ($changes.Trim()) {
    Write-Host "Changes:" -ForegroundColor Gray
    Write-Host $changes -ForegroundColor Gray
  } else {
    Write-Warn "No changes to commit in $($p.Label)"
    return $true
  }
  $commitMsg = if ($Msg) { $Msg } else { "[$MACHINE_NAME] $(Get-Date -Format 'yyyy-MM-dd HH:mm') auto commit" }
  git commit -m $commitMsg 2>&1 | Out-String | Write-Host -ForegroundColor Gray
  $result = git push $p.Remote main 2>&1 | Out-String
  if ($LASTEXITCODE -eq 0) {
    Write-Ok "Pushed to $($p.Label)"
    return $true
  }
  $result = git push $p.Remote master 2>&1 | Out-String
  if ($LASTEXITCODE -eq 0) {
    Write-Ok "Pushed to $($p.Label)"
    return $true
  }
  Write-Error "Push failed: $result"
  return $false
}

# ========== Task display ==========
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
    $projMatch = [regex]::Match($content, 'Project:\s*(\S+)')
    $proj = if ($projMatch.Success) { $projMatch.Groups[1].Value } else { "a4s" }
    $descMatch = [regex]::Match($content, '## Description\s*\n(.+?)(?=\n## |\z)', [System.Text.RegularExpressions.RegexOptions]::Singleline)
    $desc = if ($descMatch.Success) { $descMatch.Groups[1].Value.Trim() } else { "(no description)" }

    $projLabel = if ($PROJECTS.ContainsKey($proj)) { $PROJECTS[$proj].Label } else { $proj }

    Write-Host ""
    Write-Host "  $($t.BaseName) [$prio]" -ForegroundColor White
    Write-Host "  Project: $projLabel  |  Status: $status"
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
    Write-Title "A4S Bridge -- $MACHINE_LABEL"
    Git-Pull "a4s"
    Show-MyTasks
    Write-Host ""
    Write-Info "Commands:"
    Write-Host "  pull              - Pull A4S + show my tasks" -ForegroundColor Gray
    Write-Host "  push 'msg'        - Push A4S changes" -ForegroundColor Gray
    Write-Host "  push labvla 'msg' - Push LabVLA changes" -ForegroundColor Gray
    Write-Host "  go labvla         - cd to LabVLA project" -ForegroundColor Gray
    Write-Host "  go a4s            - cd back to A4S" -ForegroundColor Gray
    Write-Host "  task T001         - Show task details" -ForegroundColor Gray
    Write-Host "  status            - Show git status" -ForegroundColor Gray
    Write-Host "  projects          - List all projects" -ForegroundColor Gray
  }

  "push" {
    if ($Arg1 -and $PROJECTS.ContainsKey($Arg1)) {
      Git-Push -Proj $Arg1 -Msg $Arg2
    } elseif ($Arg1) {
      Git-Push -Proj "a4s" -Msg $Arg1
    } else {
      Git-Push -Proj "a4s"
    }
  }

  "go" {
    if ($PROJECTS.ContainsKey($Arg1)) {
      $p = $PROJECTS[$Arg1]
      if (Test-Path $p.Path) {
        Set-Location $p.Path
        Write-Ok "Switched to $($p.Label) -- $(Get-Location)"
        Write-Host "  Tip: Git commands apply to this project now" -ForegroundColor Gray
      } else {
        Write-Error "Path not found: $($p.Path)"
      }
    } else {
      Write-Error "Unknown project: $Arg1. Available: $($PROJECTS.Keys -join ', ')"
    }
  }

  "status" {
    param([string]$Proj = "a4s")
    if ($Arg1 -and $PROJECTS.ContainsKey($Arg1)) { $Proj = $Arg1 }
    $p = $PROJECTS[$Proj]
    Set-Location $p.Path
    Write-Title "$($p.Label) Status"
    git status
  }

  "task" {
    Show-Task -FileName $Arg1
  }

  "projects" {
    Write-Title "Registered Projects"
    foreach ($key in $PROJECTS.Keys) {
      $p = $PROJECTS[$key]
      $exists = if (Test-Path $p.Path) { "OK" } else { "NOT FOUND" }
      Write-Host "  $key".PadRight(12) -NoNewline
      Write-Host "$($p.Label)".PadRight(25) -NoNewline
      Write-Host "[$exists]" -ForegroundColor $(if ($exists -eq "OK") { "Green" } else { "Red" })
    }
  }

  default {
    Write-Info "Usage:"
    Write-Host "  .\bridge.ps1 pull              - Pull tasks" -ForegroundColor Gray
    Write-Host "  .\bridge.ps1 push 'message'    - Push results" -ForegroundColor Gray
    Write-Host "  .\bridge.ps1 push labvla 'msg' - Push LabVLA changes" -ForegroundColor Gray
    Write-Host "  .\bridge.ps1 go labvla         - Switch to LabVLA" -ForegroundColor Gray
    Write-Host "  .\bridge.ps1 task T001         - Show task" -ForegroundColor Gray
    Write-Host "  .\bridge.ps1 projects          - List projects" -ForegroundColor Gray
  }
}
