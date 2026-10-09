Add-Type -AssemblyName System.Speech
$e = New-Object System.Speech.Recognition.SpeechRecognitionEngine
try {
  $e.SetInputToDefaultAudioDevice()
  Write-Output 'SR_MIC_OK'
} catch {
  Write-Output ("SR_UNAVAILABLE: " + $_.Exception.Message)
}
