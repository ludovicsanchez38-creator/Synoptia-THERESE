# Appelé par Tauri pour l'exe, le sidecar, le désinstalleur NSIS et les installeurs.
# Le module est installé par l'action officielle Microsoft épinglée dans release.yml.
param([Parameter(Mandatory = $true)][string]$Path)
$ErrorActionPreference = 'Stop'
Import-Module TrustedSigning -RequiredVersion 0.5.8
$params = @{
    Endpoint = $env:AZURE_SIGNING_ENDPOINT
    CodeSigningAccountName = $env:AZURE_SIGNING_ACCOUNT
    CertificateProfileName = $env:AZURE_CERTIFICATE_PROFILE
    Files = (Resolve-Path -LiteralPath $Path).Path
    FileDigest = 'SHA256'
    TimestampRfc3161 = 'http://timestamp.acs.microsoft.com'
    TimestampDigest = 'SHA256'
    ExcludeEnvironmentCredential = $false
    ExcludeWorkloadIdentityCredential = $true
    ExcludeManagedIdentityCredential = $true
    ExcludeSharedTokenCacheCredential = $true
    ExcludeVisualStudioCredential = $true
    ExcludeVisualStudioCodeCredential = $true
    ExcludeAzureCliCredential = $true
    ExcludeAzurePowerShellCredential = $true
    ExcludeAzureDeveloperCliCredential = $true
    ExcludeInteractiveBrowserCredential = $true
}
Invoke-TrustedSigning @params
if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { throw 'Échec de la signature Microsoft' }
$signature = Get-AuthenticodeSignature -LiteralPath $Path
if ($signature.Status -ne 'Valid' -or -not $signature.TimeStamperCertificate) {
    throw 'Signature Authenticode invalide ou sans horodatage'
}
