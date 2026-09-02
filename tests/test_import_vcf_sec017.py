"""B-054 : l'import VCF doit neutraliser comme le fait déjà l'import CSV.

Les deux routes d'import VCF (`/api/crm/import/vcf` et
`/api/memory/contacts/import`) reconstruisaient la boucle d'ingestion à la
main et posaient les valeurs de `parse_vcf` directement dans `Contact(...)`,
sans jamais passer par la neutralisation SEC-017 que sept autres routes
d'import appliquent. Résultat : un `=HYPERLINK(...)` importé par VCF
redevenait une formule active à l'export CSV de l'utilisateur, et le plafond
de longueur des notes était ignoré.
"""

import csv
import io

import pytest
from app.services.crm_import import FIELD_MAX_LENGTHS
from httpx import AsyncClient

FORMULE = '=HYPERLINK("http://evil/x")'
ORGANISATION = "@SUM(1+1)"
NOTE_LONGUE = "N" * 6000


def _vcf(email: str) -> bytes:
    return (
        "BEGIN:VCARD\r\n"
        "VERSION:3.0\r\n"
        f"N:{FORMULE};Prenom;;;\r\n"
        f"FN:Prenom {FORMULE}\r\n"
        f"ORG:{ORGANISATION}\r\n"
        f"EMAIL:{email}\r\n"
        f"NOTE:{NOTE_LONGUE}\r\n"
        "END:VCARD\r\n"
    ).encode("utf-8")


def _csv(email: str) -> bytes:
    tampon = io.StringIO()
    graveur = csv.writer(tampon, lineterminator="\r\n")
    graveur.writerow(["first_name", "last_name", "company", "email", "notes"])
    graveur.writerow(["Prenom", FORMULE, ORGANISATION, email, NOTE_LONGUE])
    return tampon.getvalue().encode("utf-8")


async def _relire(client: AsyncClient, email: str) -> dict:
    reponse = await client.get("/api/memory/contacts?limit=200")
    assert reponse.status_code == 200, reponse.text
    contacts = reponse.json()
    if isinstance(contacts, dict):
        contacts = contacts.get("contacts", contacts.get("items", []))
    trouves = [c for c in contacts if c.get("email") == email]
    assert trouves, f"contact {email} introuvable après import"
    return trouves[0]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "route",
    ["/api/crm/import/vcf", "/api/memory/contacts/import"],
)
async def test_import_vcf_neutralise_comme_le_csv(client: AsyncClient, route: str):
    """Le même contenu, importé en VCF ou en CSV, doit être stocké pareil."""
    email_vcf = "rp05-vcf@example.test"
    email_csv = "rp05-csv@example.test"

    reponse = await client.post(
        route,
        files={"file": ("contacts.vcf", _vcf(email_vcf), "text/vcard")},
    )
    assert reponse.status_code == 200, reponse.text

    reponse = await client.post(
        "/api/crm/import/contacts",
        files={"file": ("contacts.csv", _csv(email_csv), "text/csv")},
    )
    assert reponse.status_code == 200, reponse.text

    par_vcf = await _relire(client, email_vcf)
    par_csv = await _relire(client, email_csv)

    for champ in ("last_name", "company"):
        assert par_vcf[champ] == par_csv[champ], (
            f"{champ} : le chemin VCF ne neutralise pas comme le chemin CSV "
            f"(VCF={par_vcf[champ]!r} / CSV={par_csv[champ]!r})"
        )
        assert par_vcf[champ].startswith("'"), (
            f"{champ} : préfixe de formule conservé tel quel ({par_vcf[champ]!r})"
        )

    assert len(par_vcf["notes"] or "") == FIELD_MAX_LENGTHS["notes"], (
        "notes : plafond SEC-017 ignoré sur le chemin VCF "
        f"({len(par_vcf['notes'] or '')} caractères)"
    )
    assert len(par_vcf["notes"] or "") == len(par_csv["notes"] or "")


@pytest.mark.asyncio
async def test_import_vcf_retire_les_octets_nuls(client: AsyncClient):
    """Un octet nul ne doit jamais atteindre la base par le chemin VCF."""
    email = "rp05-nul@example.test"
    charge = (
        "BEGIN:VCARD\r\n"
        "VERSION:3.0\r\n"
        "N:Dupont;Jean;;;\r\n"
        f"EMAIL:{email}\r\n"
        "NOTE:avant\x00apres\r\n"
        "END:VCARD\r\n"
    ).encode("utf-8")

    reponse = await client.post(
        "/api/crm/import/vcf",
        files={"file": ("contacts.vcf", charge, "text/vcard")},
    )
    assert reponse.status_code == 200, reponse.text

    contact = await _relire(client, email)
    assert "\x00" not in (contact["notes"] or ""), "octet nul stocké tel quel"
