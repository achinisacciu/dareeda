param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Root
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $Root)) {
    Write-Error "Percorso non trovato: $Root"
    exit 1
}

$testFiles = Get-ChildItem -Path $Root -Recurse -File |
    Where-Object { $_.Name -like "test_*.py" -or $_.Name -eq "conftest.py" }

if (-not $testFiles) {
    Write-Host "Nessun file di test trovato."
    exit 0
}

$results = foreach ($file in $testFiles) {
    $content = Get-Content $file.FullName -Raw

    $assertCount        = ([regex]::Matches($content, '(?m)\bassert\b')).Count
    $pytestRaisesCount  = ([regex]::Matches($content, 'pytest\.raises\(')).Count
    $mockPatchCount     = ([regex]::Matches($content, '\b(mock|patch|MagicMock|AsyncMock|monkeypatch)\b')).Count
    $fixtureUseCount    = ([regex]::Matches($content, '@pytest\.fixture|\bfixture\b')).Count
    $parametrizeCount   = ([regex]::Matches($content, '@pytest\.mark\.parametrize')).Count
    $skipXfailCount     = ([regex]::Matches($content, '@pytest\.mark\.(skip|xfail)|pytest\.(skip|xfail)\(')).Count
    $printCount         = ([regex]::Matches($content, '(?m)\bprint\(')).Count
    $testFuncCount      = ([regex]::Matches($content, '(?m)^\s*def\s+test_')).Count
    $bareExceptCount    = ([regex]::Matches($content, '(?m)^\s*except\s*:')).Count
    $onlyHappyPathHints = ([regex]::Matches($content, 'status_code\s*==\s*200|assert\s+response|assert\s+result\s+is\s+not\s+None')).Count
    $callOnlyHints      = ([regex]::Matches($content, 'assert_.*called|called_once|called_once_with|assert_called')).Count
    $todoHints          = ([regex]::Matches($content, 'TODO|FIXME|placeholder|dummy|fake')).Count

    $riskFlags = @()

    if ($file.Name -like "test_*.py" -and $testFuncCount -gt 0 -and $assertCount -eq 0 -and $pytestRaisesCount -eq 0) {
        $riskFlags += "NO_ASSERTS"
    }

    if ($mockPatchCount -gt ($assertCount * 2) -and $mockPatchCount -ge 6) {
        $riskFlags += "HEAVY_MOCKING"
    }

    if ($callOnlyHints -gt 0 -and $assertCount -le ($callOnlyHints + 1)) {
        $riskFlags += "TESTS_CALLS_NOT_OUTPUTS"
    }

    if ($onlyHappyPathHints -ge 2 -and $pytestRaisesCount -eq 0) {
        $riskFlags += "MOSTLY_HAPPY_PATH"
    }

    if ($skipXfailCount -gt 0) {
        $riskFlags += "HAS_SKIP_OR_XFAIL"
    }

    if ($bareExceptCount -gt 0) {
        $riskFlags += "BARE_EXCEPT"
    }

    if ($todoHints -gt 0) {
        $riskFlags += "TODO_OR_DUMMY_HINTS"
    }

    [PSCustomObject]@{
        File           = $file.FullName
        Tests          = $testFuncCount
        Asserts        = $assertCount
        Raises         = $pytestRaisesCount
        Mocks          = $mockPatchCount
        Fixtures       = $fixtureUseCount
        Parametrize    = $parametrizeCount
        SkipXfail      = $skipXfailCount
        PrintCalls     = $printCount
        BareExcept     = $bareExceptCount
        HappyPathHints = $onlyHappyPathHints
        CallOnlyHints  = $callOnlyHints
        TodoHints      = $todoHints
        Flags          = ($riskFlags -join ",")
    }
}

$results |
    Sort-Object @{Expression = { if ($_.Flags) { 0 } else { 1 } } }, @{Expression = "Mocks"; Descending = $true}, @{Expression = "Asserts"; Ascending = $true} |
    Format-Table -AutoSize

"`n--- FILE SOSPETTI ---"
$results |
    Where-Object { $_.Flags -ne "" } |
    Sort-Object File |
    Format-Table File, Tests, Asserts, Mocks, Raises, Flags -AutoSize

"`n--- FILE CON POCHI ASSERT ---"
$results |
    Where-Object { $_.Tests -gt 0 -and $_.Asserts -le 2 } |
    Sort-Object Asserts, File |
    Format-Table File, Tests, Asserts, Mocks, Flags -AutoSize

"`n--- FILE PIU MOCKATI ---"
$results |
    Sort-Object Mocks -Descending |
    Select-Object -First 15 |
    Format-Table File, Tests, Asserts, Mocks, Flags -AutoSize

$csvPath = Join-Path (Get-Location) "test-audit-summary.csv"
$results | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8

Write-Host "`nReport CSV salvato in: $csvPath"
