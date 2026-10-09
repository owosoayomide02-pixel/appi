Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
Write-Output 'TTS_ENGINE_OK'
