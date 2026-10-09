# Pointer for this Windows laptop. Real iPhone / Mac / Linux setup runs on those OSes.

Write-Host "Appi setups for other operating systems:"
Write-Host ""
Write-Host "  Linux:  copy the repo, then:  bash scripts/setup-linux.sh"
Write-Host "  macOS:  copy the repo, then:  bash scripts/setup-macos.sh"
Write-Host "  iPhone: copy the repo to a Mac with Xcode, then:  bash scripts/setup-ios.sh"
Write-Host ""
Write-Host "This Windows PC cannot compile an iOS IPA, macOS .app, or Linux .deb."
Write-Host "The working assistant today is Windows: dist\windows\Appi\Appi.exe or python -m app.main serve"
exit 0
