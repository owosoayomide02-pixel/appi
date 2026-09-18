param(
  [Parameter(Mandatory=$true)][string]$Text,
  [string]$Voice = "",
  [string]$Gender = ""
)
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
if ($Voice) {
  try {
    $s.SelectVoice($Voice)
  } catch {
    foreach ($v in $s.GetInstalledVoices()) {
      if ($v.VoiceInfo.Name -like "*$Voice*") {
        $s.SelectVoice($v.VoiceInfo.Name)
        break
      }
    }
  }
} elseif ($Gender) {
  $g = [System.Speech.Synthesis.VoiceGender]::NotSet
  if ($Gender -match '^(?i)f') { $g = [System.Speech.Synthesis.VoiceGender]::Female }
  elseif ($Gender -match '^(?i)m') { $g = [System.Speech.Synthesis.VoiceGender]::Male }
  if ($g -ne [System.Speech.Synthesis.VoiceGender]::NotSet) {
    $s.SelectVoiceByHints($g)
  }
}
$s.Speak($Text)
