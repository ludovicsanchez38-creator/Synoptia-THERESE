"""B-1887 : une signature valide doit aussi correspondre au signataire attendu."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_la_garde_authenticode_controle_le_certificat_signataire():
    script = (ROOT / "scripts/verify_windows_signing.ps1").read_text(encoding="utf-8")
    assert "Get-AuthenticodeSignature" in script
    assert "$signature.Status" in script and "$signature.TimeStamperCertificate" in script
    assert "$signature.SignerCertificate" in script, (
        "aucun contrôle de l'identité du signataire, seulement statut et horodatage"
    )
