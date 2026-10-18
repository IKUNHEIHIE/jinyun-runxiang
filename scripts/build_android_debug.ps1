param([string]$ApiUrl = 'http://127.0.0.1:8000/api')
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$appRoot = Join-Path $repoRoot 'user-web'
$apiUri = [Uri]$ApiUrl
if (!$apiUri.IsAbsoluteUri -or $apiUri.Scheme -notin @('http','https')) { throw 'API URL must be absolute HTTP(S).' }
if ($apiUri.Scheme -eq 'http' -and $apiUri.Host -notin @('127.0.0.1','localhost','10.0.2.2')) { throw 'Non-local servers must use HTTPS.' }
$sdkCandidates = @($env:ANDROID_HOME, $env:ANDROID_SDK_ROOT, 'D:\Android\Sdk', (Join-Path $env:LOCALAPPDATA 'Android\Sdk')) | Where-Object { $_ -and (Test-Path -LiteralPath (Join-Path $_ 'platform-tools\adb.exe')) }
if (!$sdkCandidates) { throw 'Install Android SDK and set ANDROID_HOME.' }
$jdkCandidates = @($env:JAVA_HOME)
if (Test-Path -LiteralPath 'D:\Android\Jdk21') { $jdkCandidates += Get-ChildItem -LiteralPath 'D:\Android\Jdk21' -Directory | ForEach-Object { $_.FullName } }
$chosenJdk = $null
foreach ($candidate in $jdkCandidates) {
  if (!$candidate -or !(Test-Path -LiteralPath (Join-Path $candidate 'bin\java.exe'))) { continue }
  # Java writes its version to stderr. Capture it directly so Windows
  # PowerShell 5.1 does not turn a successful version check into an error.
  $javaInfo = New-Object System.Diagnostics.ProcessStartInfo
  $javaInfo.FileName = Join-Path $candidate 'bin\java.exe'
  $javaInfo.Arguments = '-version'
  $javaInfo.UseShellExecute = $false
  $javaInfo.CreateNoWindow = $true
  $javaInfo.RedirectStandardOutput = $true
  $javaInfo.RedirectStandardError = $true
  $javaCheck = [System.Diagnostics.Process]::Start($javaInfo)
  $versionOutput = $javaCheck.StandardError.ReadToEnd() + $javaCheck.StandardOutput.ReadToEnd()
  $javaCheck.WaitForExit()
  $javaCheck.Dispose()
  if ($versionOutput -match 'version "21[.]') { $chosenJdk = $candidate; break }
}
if (!$chosenJdk) { throw 'A JDK 21 installation is required. Set JAVA_HOME to JDK 21.' }
$previousLocation = Get-Location
$previousJava = $env:JAVA_HOME; $previousAndroid = $env:ANDROID_HOME; $previousApi = $env:VITE_API_BASE_URL
try {
  $env:JAVA_HOME = $chosenJdk; $env:ANDROID_HOME = $sdkCandidates[0]; $env:VITE_API_BASE_URL = $ApiUrl
  Set-Location -LiteralPath $appRoot
  & node scripts/patch-capacitor.mjs
  if ($LASTEXITCODE -ne 0) { throw 'Android safe-area compatibility patch failed.' }
  & npx vue-tsc --noEmit
  if ($LASTEXITCODE -ne 0) { throw 'Client type check failed.' }
  & npx vite build --mode android
  if ($LASTEXITCODE -ne 0) { throw 'Client build failed.' }
  & npx cap sync android
  if ($LASTEXITCODE -ne 0) { throw 'Android synchronization failed.' }
  Set-Location -LiteralPath (Join-Path $appRoot 'android')
  & .\gradlew.bat :app:clean assembleDebug --console=plain
  if ($LASTEXITCODE -ne 0) { throw 'Android build failed.' }
  $artifactDirectory = Join-Path $repoRoot '.local\android\artifacts'
  New-Item -ItemType Directory -Path $artifactDirectory -Force | Out-Null
  $artifact = Join-Path $artifactDirectory 'jinyun-runxiang-debug.apk'
  Copy-Item -LiteralPath (Join-Path $appRoot 'android\app\build\outputs\apk\debug\app-debug.apk') -Destination $artifact -Force
  Get-FileHash -LiteralPath $artifact -Algorithm SHA256
  Write-Output "APK: $artifact"
  Write-Output 'Loopback development: adb -s emulator-5554 reverse tcp:8000 tcp:8000 before launch.'
} finally {
  Set-Location $previousLocation
  $env:JAVA_HOME = $previousJava; $env:ANDROID_HOME = $previousAndroid; $env:VITE_API_BASE_URL = $previousApi
}
