# Persistent local wake-word listener. Prints LISTENING then WAKE.
# Audio stays on this machine. Does not stream to the cloud.
param(
  [string]$WakeWord = "Appi",
  [string]$Culture = ""
)

Add-Type -AssemblyName System.Speech
try {
  if ($Culture) {
    $engine = New-Object System.Speech.Recognition.SpeechRecognitionEngine (New-Object System.Globalization.CultureInfo $Culture)
  } else {
    $engine = New-Object System.Speech.Recognition.SpeechRecognitionEngine
  }
} catch {
  $engine = New-Object System.Speech.Recognition.SpeechRecognitionEngine
}
try {
  $engine.SetInputToDefaultAudioDevice()
} catch {
  [Console]::Error.WriteLine("UNAVAILABLE " + $_.Exception.Message)
  exit 1
}
$builder = New-Object System.Speech.Recognition.GrammarBuilder
$builder.Append($WakeWord)
$engine.LoadGrammar((New-Object System.Speech.Recognition.Grammar($builder)))
$engine.InitialSilenceTimeout = [TimeSpan]::FromSeconds(8)
$engine.EndSilenceTimeout = [TimeSpan]::FromSeconds(0.4)
[Console]::Out.WriteLine("LISTENING")
[Console]::Out.Flush()
while ($true) {
  $result = $engine.Recognize()
  if ($result -ne $null -and $result.Text -and ($result.Text -match $WakeWord)) {
    [Console]::Out.WriteLine("WAKE")
    [Console]::Out.Flush()
  }
}
