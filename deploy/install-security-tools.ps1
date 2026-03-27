param(
    [switch]$WithGitleaks
)

$ErrorActionPreference = 'Stop'

Write-Host "[setup] Installing Python security tools via uv tool..."

$tools = @('bandit', 'pip-audit')
foreach ($t in $tools) {
    try {
        uv tool install $t | Out-Host
        Write-Host "[ok] installed: $t"
    }
    catch {
        Write-Host "[warn] install failed for $t : $($_.Exception.Message)"
    }
}

if ($WithGitleaks) {
    Write-Host "[setup] Trying to install gitleaks..."

    $installed = $false

    if (Get-Command gitleaks -ErrorAction SilentlyContinue) {
        Write-Host "[ok] gitleaks already installed"
        $installed = $true
    }

    if (-not $installed -and (Get-Command winget -ErrorAction SilentlyContinue)) {
        try {
            winget install --id Gitleaks.Gitleaks -e --accept-package-agreements --accept-source-agreements
            $installed = $true
            Write-Host "[ok] gitleaks installed by winget"
        }
        catch {
            Write-Host "[warn] winget install gitleaks failed"
        }
    }

    if (-not $installed -and (Get-Command choco -ErrorAction SilentlyContinue)) {
        try {
            choco install gitleaks -y
            $installed = $true
            Write-Host "[ok] gitleaks installed by choco"
        }
        catch {
            Write-Host "[warn] choco install gitleaks failed"
        }
    }

    if (-not $installed) {
        Write-Host "[warn] gitleaks not installed. Please install manually: https://github.com/gitleaks/gitleaks"
    }
}

Write-Host "[setup] Verifying tools..."
$check = @('bandit', 'pip-audit', 'gitleaks')
foreach ($c in $check) {
    if (Get-Command $c -ErrorAction SilentlyContinue) {
        Write-Host ("[ok] " + $c)
    }
    else {
        Write-Host ("[skip] " + $c + " not found")
    }
}

Write-Host "[done] security tool setup complete"
