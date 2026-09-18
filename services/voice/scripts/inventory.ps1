Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$voices = @()
foreach ($v in $synth.GetInstalledVoices()) {
  $i = $v.VoiceInfo
  $voices += [ordered]@{
    name = $i.Name
    culture = $i.Culture.Name
    gender = $i.Gender.ToString()
    enabled = [bool]$v.Enabled
  }
}
$recognizers = @()
foreach ($r in [System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers()) {
  $recognizers += [ordered]@{
    id = $r.Id
    name = $r.Name
    culture = $r.Culture.Name
  }
}
@{ voices = $voices; recognizers = $recognizers } | ConvertTo-Json -Compress -Depth 4
