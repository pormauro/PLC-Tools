param(
    [int]$WaitSeconds = 60,
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$root = [System.Windows.Automation.AutomationElement]::RootElement
$deadline = [DateTime]::UtcNow.AddSeconds($WaitSeconds)

# English text confirmed in GX Works2 manuals/current UI.
# Spanish variants are intentionally narrow; add a new variant only after observing it.
$checkboxPatterns = @(
    '(?i)^When processing ends,\s*close this window automatically\.?$',
    '(?i)^When processing ends,\s*the window is automatically close\.?$',
    '(?i)^Al finalizar el procesamiento,\s*cerrar esta ventana autom[aá]ticamente\.?$'
)

function Test-NameMatch {
    param([string]$Name, [string[]]$Patterns)
    foreach ($pattern in $Patterns) {
        if ($Name -match $pattern) {
            return $true
        }
    }
    return $false
}

while ([DateTime]::UtcNow -lt $deadline) {
    $windows = $root.FindAll(
        [System.Windows.Automation.TreeScope]::Children,
        [System.Windows.Automation.Condition]::TrueCondition
    )

    foreach ($window in $windows) {
        $title = $window.Current.Name
        if ($title -notmatch '(?i)Write to PLC|Escribir.*PLC') {
            continue
        }

        $elements = $window.FindAll(
            [System.Windows.Automation.TreeScope]::Descendants,
            [System.Windows.Automation.Condition]::TrueCondition
        )

        foreach ($element in $elements) {
            if ($element.Current.ControlType -ne [System.Windows.Automation.ControlType]::CheckBox) {
                continue
            }

            $name = $element.Current.Name
            if (-not (Test-NameMatch -Name $name -Patterns $checkboxPatterns)) {
                continue
            }

            $patternObj = $null
            if (-not $element.TryGetCurrentPattern(
                [System.Windows.Automation.TogglePattern]::Pattern,
                [ref]$patternObj
            )) {
                throw "GX Works2 auto-close checkbox found, but TogglePattern is unavailable."
            }

            $toggle = [System.Windows.Automation.TogglePattern]$patternObj
            if ($toggle.Current.ToggleState -ne [System.Windows.Automation.ToggleState]::On) {
                $toggle.Toggle()
            }

            if (-not $Quiet) {
                Write-Host "GX Works2 Write-to-PLC auto-close: ON"
            }
            exit 0
        }
    }

    Start-Sleep -Milliseconds 200
}

throw "GX Works2 Write-to-PLC auto-close checkbox was not found within $WaitSeconds seconds."
