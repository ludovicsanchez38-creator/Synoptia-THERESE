param([Parameter(Mandatory = $true)][string[]]$Roots)
$ErrorActionPreference = 'Stop'
$count = 0
foreach ($root in $Roots) {
    foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File) {
        if ($file.Extension -notin @('.exe', '.dll', '.pyd', '.msi')) { continue }
        $signature = Get-AuthenticodeSignature -LiteralPath $file.FullName
        if ($signature.Status -ne 'Valid' -or -not $signature.TimeStamperCertificate) {
            throw "Signature absente, invalide ou sans horodatage : $($file.Name)"
        }
        $count++
    }
}
if ($count -eq 0) { throw 'Aucun fichier signé trouvé' }
Write-Host "$count fichiers accessibles vérifiés ; les DLL/.pyd internes au onefile restent hors couverture."
