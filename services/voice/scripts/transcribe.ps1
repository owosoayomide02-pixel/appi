param(
  [int]$Seconds = 10,
  [string]$Culture = "",
  [string]$CommandsFile = ""
)
Add-Type -AssemblyName System.Speech

function New-Engine {
  param([string]$CultureName)
  if ($CultureName) {
    return New-Object System.Speech.Recognition.SpeechRecognitionEngine (New-Object System.Globalization.CultureInfo $CultureName)
  }
  return New-Object System.Speech.Recognition.SpeechRecognitionEngine
}

try {
  $e = New-Engine -CultureName $Culture
} catch {
  $e = New-Object System.Speech.Recognition.SpeechRecognitionEngine
}

try {
  $e.SetInputToDefaultAudioDevice()
} catch {
  Write-Output '{"ok":false,"error":"no microphone"}'
  exit 0
}

$e.InitialSilenceTimeout = [TimeSpan]::FromSeconds([Math]::Min(6, [Math]::Max(2, $Seconds / 2)))
$e.BabbleTimeout = [TimeSpan]::FromSeconds(4)
$e.EndSilenceTimeout = [TimeSpan]::FromSeconds(1.1)
$e.EndSilenceTimeoutAmbiguous = [TimeSpan]::FromSeconds(1.5)

if (-not $CommandsFile) {
  $CommandsFile = Join-Path $PSScriptRoot "commands.txt"
}
$loaded = 0
if (Test-Path $CommandsFile) {
  $choices = New-Object System.Speech.Recognition.Choices
  Get-Content -Path $CommandsFile | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#")) {
      [void]$choices.Add($line)
      $loaded++
    }
  }
  if ($loaded -gt 0) {
    $builder = New-Object System.Speech.Recognition.GrammarBuilder
    $builder.Append($choices)
    $commandGrammar = New-Object System.Speech.Recognition.Grammar $builder
    $commandGrammar.Name = "appi-commands"
    $commandGrammar.Priority = 127
    $e.LoadGrammar($commandGrammar)
  }
}

$dictation = New-Object System.Speech.Recognition.DictationGrammar
$dictation.Name = "dictation"
$dictation.Priority = 0
$e.LoadGrammar($dictation)

$r = $e.Recognize([TimeSpan]::FromSeconds($Seconds))
if ($r -eq $null -or -not $r.Text) {
  Write-Output '{"ok":false,"text":"","confidence":0}'
  exit 0
}
$conf = 0
try { $conf = [double]$r.Confidence } catch { $conf = 0 }
$source = "dictation"
if ($r.Grammar -and $r.Grammar.Name) { $source = $r.Grammar.Name }
$payload = [ordered]@{
  ok = $true
  text = $r.Text
  confidence = $conf
  source = $source
}
$payload | ConvertTo-Json -Compress
