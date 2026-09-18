Add-Type -AssemblyName System.Speech
$e = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$e.SetInputToDefaultAudioDevice()
$gb = New-Object System.Speech.Recognition.GrammarBuilder
$gb.Append('Appi')
$e.LoadGrammar((New-Object System.Speech.Recognition.Grammar($gb)))
Write-Output 'GRAMMAR_APPI_OK'
