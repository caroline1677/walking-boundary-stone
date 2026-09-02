param(
  [Parameter(Mandatory = $true)][string]$Text,
  [Parameter(Mandatory = $true)][string]$Output
)

Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.SpeechSynthesis.SpeechSynthesizer, Windows.Media.SpeechSynthesis, ContentType = WindowsRuntime]

function Await-WinRT {
  param($Operation, [Type]$ResultType)
  $method = ([System.WindowsRuntimeSystemExtensions].GetMethods() |
    Where-Object {
      $_.Name -eq 'AsTask' -and
      $_.IsGenericMethod -and
      $_.GetParameters().Count -eq 1
    })[0].MakeGenericMethod($ResultType)
  $task = $method.Invoke($null, @($Operation))
  $task.Wait()
  return $task.Result
}

$synth = [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::new()
$voice = [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices |
  Where-Object { $_.DisplayName -eq 'Microsoft Kangkang' } |
  Select-Object -First 1

if (-not $voice) {
  throw 'Microsoft Kangkang Chinese male voice is not installed.'
}

$synth.Voice = $voice
$stream = Await-WinRT $synth.SynthesizeTextToStreamAsync($Text) ([Windows.Media.SpeechSynthesis.SpeechSynthesisStream])
$netStream = [System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($stream)
$fileStream = [IO.File]::Create($Output)
$netStream.CopyTo($fileStream)
$fileStream.Dispose()
$netStream.Dispose()
$stream.Dispose()
$synth.Dispose()
