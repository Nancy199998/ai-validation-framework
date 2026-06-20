# AI Validation Framework - Pre-Publish Audit
# Run from the repo root: C:\AI-project\validation-framework
# Purpose: catch API keys, local paths, and temp files BEFORE first commit/push.
#
# Usage:
#   cd C:\AI-project\validation-framework
#   powershell -ExecutionPolicy Bypass -File pre-publish-audit.ps1

Write-Host "=== AI Validation Framework - Pre-Publish Audit ===" -ForegroundColor Cyan
Write-Host ""

$failed = $false

# 1. Is this even a git repo yet, and has anything been committed?
if (-not (Test-Path ".git")) {
    Write-Host "[INFO] No .git folder found yet - this is a clean check before first init." -ForegroundColor Yellow
} else {
    Write-Host "[INFO] .git folder found." -ForegroundColor Gray
}

# 2. Scan tracked + untracked files (everything that WOULD be added) for API key patterns
Write-Host ""
Write-Host "--- 2. Scanning for API keys / secrets ---" -ForegroundColor Cyan

$keyPatterns = @(
    'AIza[0-9A-Za-z\-_]{35}',          # Google API key
    'sk-ant-[0-9A-Za-z\-_]{20,}',       # Anthropic key
    'sk-[0-9A-Za-z]{20,}',              # OpenAI-style key
    'GOOGLE_API_KEY\s*=\s*["\047][^"\047]+["\047]',
    'ANTHROPIC_API_KEY\s*=\s*["\047][^"\047]+["\047]',
    'api[_-]?key["\047]?\s*[:=]\s*["\047][A-Za-z0-9\-_]{16,}["\047]'
)

Write-Host "[INFO] Enumerating files (excluding venv folders)..." -ForegroundColor Gray

$excludeDirs = @('venv', 'venv311', '.git', '__pycache__', 'node_modules', 'chroma_db')
$excludeExtensions = @('.png', '.jpg', '.jpeg', '.pdf', '.pyc')

$filesToScan = New-Object System.Collections.Generic.List[System.IO.FileInfo]
$dirQueue = New-Object System.Collections.Generic.Queue[System.IO.DirectoryInfo]
$dirQueue.Enqueue([System.IO.DirectoryInfo]::new((Get-Location).Path))

while ($dirQueue.Count -gt 0) {
    $currentDir = $dirQueue.Dequeue()
    try {
        foreach ($item in $currentDir.EnumerateFileSystemInfos()) {
            if ($item -is [System.IO.DirectoryInfo]) {
                if ($excludeDirs -notcontains $item.Name) {
                    $dirQueue.Enqueue($item)
                }
            } elseif ($item -is [System.IO.FileInfo]) {
                if ($excludeExtensions -notcontains $item.Extension.ToLower()) {
                    $filesToScan.Add($item)
                }
            }
        }
    } catch {
        # skip dirs we can't read (permissions etc.)
    }
}

Write-Host "[INFO] Found $($filesToScan.Count) files to scan." -ForegroundColor Gray
Write-Host "[INFO] Found $($filesToScan.Count) files to scan." -ForegroundColor Gray

$keyHits = @()
foreach ($f in $filesToScan) {
    try {
        $content = Get-Content $f.FullName -Raw -ErrorAction Stop
    } catch { continue }
    foreach ($pattern in $keyPatterns) {
        if ($content -match $pattern) {
            $keyHits += [PSCustomObject]@{ File = $f.FullName; Pattern = $pattern }
        }
    }
}

if ($keyHits.Count -gt 0) {
    Write-Host "[FAIL] Possible API keys found:" -ForegroundColor Red
    $keyHits | Format-Table -AutoSize
    $failed = $true
} else {
    Write-Host "[PASS] No API key patterns found in scanned files." -ForegroundColor Green
}

# 3. .env files present and NOT gitignored?
Write-Host ""
Write-Host "--- 3. Checking .env handling ---" -ForegroundColor Cyan
$envFiles = $filesToScan | Where-Object { $_.Name -like ".env*" }

if ($envFiles) {
    foreach ($e in $envFiles) {
        Write-Host "  Found: $($e.FullName)" -ForegroundColor Yellow
    }
    if (Test-Path ".gitignore") {
        $gi = Get-Content ".gitignore" -Raw
        if ($gi -notmatch '(^|\n)\.env') {
            Write-Host "[FAIL] .env file(s) exist but '.env' is NOT in .gitignore." -ForegroundColor Red
            $failed = $true
        } else {
            Write-Host "[PASS] .env is covered by .gitignore." -ForegroundColor Green
        }
    } else {
        Write-Host "[FAIL] .env file(s) exist but there is no .gitignore at all." -ForegroundColor Red
        $failed = $true
    }
} else {
    Write-Host "[INFO] No .env files found in repo tree." -ForegroundColor Gray
}

# 4. Hardcoded local Windows paths (the C:\AI-project\... leak pattern we saw in checkpoint_T002.json)
Write-Host ""
Write-Host "--- 4. Scanning for hardcoded local paths ---" -ForegroundColor Cyan

$pathPatterns = @(
    'C:\\\\?Users\\\\?[A-Za-z0-9_\-]+',
    'C:\\\\?AI-project\\\\?[A-Za-z0-9_\\\-]*',
    '[A-Za-z]:\\\\[A-Za-z0-9_\\\- ]+\\\\[A-Za-z0-9_\\\- ]+'
)

$pathHits = @()
foreach ($f in $filesToScan) {
    try {
        $lines = Get-Content $f.FullName -ErrorAction Stop
    } catch { continue }
    $lineNum = 0
    foreach ($line in $lines) {
        $lineNum++
        foreach ($pattern in $pathPatterns) {
            if ($line -match $pattern) {
                $pathHits += [PSCustomObject]@{ File = $f.FullName; Line = $lineNum; Match = $matches[0] }
                break
            }
        }
    }
}

if ($pathHits.Count -gt 0) {
    Write-Host "[WARN] Possible hardcoded local paths found. Review each match below (test fixture paths may be fine; absolute C drive user paths are not)." -ForegroundColor Yellow
    $pathHits | Format-Table -AutoSize
} else {
    Write-Host "[PASS] No obvious hardcoded local Windows paths found." -ForegroundColor Green
}

# 5. Temp / checkpoint / cache files that shouldn't ship
Write-Host ""
Write-Host "--- 5. Checking for temp/checkpoint/cache artifacts ---" -ForegroundColor Cyan

$tempNamePatterns = @("checkpoint_*.json", "*.tmp", "*.bak", "test_ragas.py", "*.log", "*.pyc", "*.sqlite3")
$tempHits = $filesToScan | Where-Object {
    $name = $_.Name
    ($tempNamePatterns | Where-Object { $name -like $_ }).Count -gt 0
}
# Also flag chroma_db / __pycache__ directories explicitly (these are dirs, not files)
$tempDirHits = Get-ChildItem -Path "." -Recurse -Directory -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -in @("chroma_db", "__pycache__") -and $_.FullName -notmatch '\\venv311?\\' }
if ($tempDirHits) {
    foreach ($d in $tempDirHits) {
        Write-Host "  Directory: $($d.FullName)" -ForegroundColor Yellow
    }
}

if ($tempHits.Count -gt 0) {
    Write-Host "[WARN] Temp/checkpoint/cache files found - confirm these are gitignored or intentionally kept as evidence:" -ForegroundColor Yellow
    $tempHits | Select-Object FullName | Format-Table -AutoSize
} else {
    Write-Host "[PASS] No stray temp/checkpoint/cache files found." -ForegroundColor Green
}

# 6. venv folders accidentally inside the repo
Write-Host ""
Write-Host "--- 6. Checking virtual environments aren't tracked ---" -ForegroundColor Cyan
$venvDirs = @("venv", "venv311") | Where-Object { Test-Path $_ }
if ($venvDirs) {
    if (Test-Path ".gitignore") {
        $gi = Get-Content ".gitignore" -Raw
        foreach ($v in $venvDirs) {
            if ($gi -notmatch [regex]::Escape($v)) {
                Write-Host "[FAIL] '$v' exists but is not in .gitignore." -ForegroundColor Red
                $failed = $true
            } else {
                Write-Host "[PASS] '$v' is gitignored." -ForegroundColor Green
            }
        }
    } else {
        Write-Host "[FAIL] venv folder(s) exist but there is no .gitignore." -ForegroundColor Red
        $failed = $true
    }
} else {
    Write-Host "[INFO] No venv folders found at repo root (fine if they live elsewhere)." -ForegroundColor Gray
}

# 7. If already a git repo, double-check what's actually staged/tracked right now
Write-Host ""
Write-Host "--- 7. Git status (what would actually be committed) ---" -ForegroundColor Cyan
if (Test-Path ".git") {
    git status --short
} else {
    Write-Host "[INFO] Not a git repo yet - run 'git init' and re-run this script before your first commit." -ForegroundColor Gray
}

Write-Host ""
if ($failed) {
    Write-Host "=== RESULT: FAIL - fix the items above before pushing publicly ===" -ForegroundColor Red
} else {
    Write-Host "=== RESULT: PASS - no hard blockers found. Review WARN items manually. ===" -ForegroundColor Green
}
