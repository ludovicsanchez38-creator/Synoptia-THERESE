"""B-1380 (persona Nathalie, cycle 13) : l'import vCard écartait des cartes
sans le dire, même dans son total.

Un fichier de deux cartes, dont une sans N ni FN (entreprise et e-mail seuls),
répondait `{"created": 0, "updated": 1, "total": 1}` : la carte disparaissait
avant tout comptage (`import_service.parse_vcf`, `continue  # Pas de nom,
skip`). Une adresse jugée douteuse était vidée en silence. C'est la ligne rouge
de Nathalie : un import qui dit « terminé » sans dire ce qui a été écarté.
"""

import pytest

FICHIER = (
    "BEGIN:VCARD\r\nVERSION:3.0\r\nN:Leroy;Marc;;;\r\nFN:Marc Leroy\r\n"
    "EMAIL:marc@@exemple\r\nEND:VCARD\r\n"
    "BEGIN:VCARD\r\nVERSION:3.0\r\nORG:Sans Nom SARL\r\n"
    "EMAIL:contact@sansnom.example\r\nEND:VCARD\r\n"
).encode("utf-8")


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["/api/crm/import/vcf", "/api/memory/contacts/import"])
async def test_l_import_compte_et_nomme_ce_qu_il_ecarte(client, route):
    reponse = await client.post(route, files={"file": ("prospects.vcf", FICHIER, "text/vcard")})
    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()

    assert corps["total"] == 2, "le total compte les cartes du fichier, pas seulement celles gardées"
    assert corps["created"] == 1
    assert any("sans nom" in e for e in corps["ecartees"]), corps
    assert any("marc@@exemple" in e for e in corps["ecartees"]), corps
    assert "1 carte écartée" in corps["message"]
    assert "adresse e-mail" in corps["message"]


def test_parse_vcf_garde_son_contrat():
    from app.services.import_service import parse_vcf

    contacts = parse_vcf(FICHIER)
    assert [c["last_name"] for c in contacts] == ["Leroy"]
    assert contacts[0]["email"] is None
