param(
    [Parameter(Mandatory = $true)][string[]]$Roots,
    # Facultatif (variable de dépôt EDITEUR_WINDOWS_ATTENDU) : nom de l'organisation
    # validée par Microsoft, tel qu'il apparaît dans le champ O= du certificat.
    [string]$ExpectedPublisher = ''
)
$ErrorActionPreference = 'Stop'
$count = 0
$subjects = @{}
foreach ($root in $Roots) {
    foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File) {
        if ($file.Extension -notin @('.exe', '.dll', '.pyd', '.msi')) { continue }
        $signature = Get-AuthenticodeSignature -LiteralPath $file.FullName
        if ($signature.Status -ne 'Valid' -or -not $signature.TimeStamperCertificate) {
            throw "Signature absente, invalide ou sans horodatage : $($file.Name)"
        }
        $subject = $signature.SignerCertificate.Subject
        if ($ExpectedPublisher -and ($subject -notmatch ('(^|,\s*)O="?' + [regex]::Escape($ExpectedPublisher) + '"?(,|$)'))) {
            throw "Éditeur inattendu pour $($file.Name) : $subject"
        }
        $subjects[$subject] = $true
        $count++
    }
}
if ($count -eq 0) { throw 'Aucun fichier signé trouvé' }
# Le sujet d'un certificat de signature est public (il s'affiche dans Windows).
foreach ($subject in $subjects.Keys) { Write-Host "Signataire : $subject" }
Write-Host "$count fichiers accessibles vérifiés ; les DLL/.pyd internes au onefile restent hors couverture."
