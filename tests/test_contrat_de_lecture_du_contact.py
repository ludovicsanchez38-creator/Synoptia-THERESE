"""
Le contrat de lecture d'une fiche (tranche A du 29/08).

Le problème mesuré sur les vraies données de Ludo : `read_contact` envoyait au
modèle le bloc `notes` de la fiche ET les cinq dernières activités À ÉGALITÉ,
en présentant le tout comme « la fiche complète ». Or le bloc `notes` contient
un résumé écrit à la main qui dit encore « FORGER 490 € » alors qu'une note du
27/08 dit « PROPULSER, 2 490 € ».

Le modèle recevait donc un état périmé, sans rien pour le distinguer d'un fait.

Le contrat : ce que l'application a réellement posé (`etat_courant`) est séparé
de ce qui a été écrit à un moment donné (`traces`). Tant que rien n'a été posé,
`etat_courant` est vide, et la consigne interdit de trancher.
"""
import json

import pytest
from app.models.entities import Activity, Contact
from app.services.memory_tools import execute_memory_tool
from sqlalchemy.ext.asyncio import AsyncSession


async def _fiche(session: AsyncSession, **kw) -> Contact:
    c = Contact(first_name="Nathalie", last_name="Esmieu", **kw)
    session.add(c)
    await session.commit()
    return c


async def _lire(session: AsyncSession, requete: str) -> dict:
    return json.loads(await execute_memory_tool("read_contact", {"query": requete}, session))


@pytest.mark.asyncio
async def test_le_resume_manuscrit_n_est_pas_un_etat(db_session: AsyncSession):
    """Le coeur de la tranche : le bloc `notes` cesse d'être présenté comme un fait."""
    await _fiche(db_session, notes="FORGER 490 EUR, seance calee au 24/08")

    fiche = (await _lire(db_session, "Esmieu"))["contacts"][0]

    assert fiche["etat_courant"] is None, (
        "rien n'a été posé par l'application : elle ne doit affirmer aucun état"
    )
    assert "notes" not in fiche, "le bloc manuscrit ne doit plus voyager comme un champ de fiche"
    assert any("FORGER" in (t.get("texte") or "") for t in fiche["traces"]), (
        "il reste lisible, mais comme une trace datée, pas comme la vérité"
    )


@pytest.mark.asyncio
async def test_deux_traces_contradictoires_restent_deux_traces(db_session: AsyncSession):
    c = await _fiche(db_session, notes="FORGER 490 EUR")
    db_session.add(Activity(contact_id=c.id, type="note",
                            title="CORRECTION : c'est PROPULSER et non FORGER",
                            description="Pack V2 regenere, 2 490 EUR"))
    await db_session.commit()

    fiche = (await _lire(db_session, "Esmieu"))["contacts"][0]

    textes = " ".join((t.get("texte") or "") + (t.get("titre") or "") for t in fiche["traces"])
    assert "FORGER" in textes and "PROPULSER" in textes, "les deux doivent rester lisibles"
    assert fiche["etat_courant"] is None, "l'application ne tranche pas entre deux traces"


@pytest.mark.asyncio
async def test_la_consigne_interdit_d_affirmer(db_session: AsyncSession):
    """La consigne part avec la donnée : sans elle, le modèle tranchera quand même."""
    await _fiche(db_session, notes="FORGER 490 EUR")

    charge = await _lire(db_session, "Esmieu")

    consigne = charge.get("consigne", "")
    assert "etat_courant" in consigne
    assert "traces" in consigne
    for mot in ("n'affirme", "contradictoires", "dis-le"):
        assert mot.lower() in consigne.lower(), f"la consigne doit contenir « {mot} »"


@pytest.mark.asyncio
async def test_les_champs_reellement_poses_restent_des_faits(db_session: AsyncSession):
    """Ce que l'application A posé n'est pas une trace : c'est un fait."""
    await _fiche(db_session, email="nathalie@exemple.fr", company="Esmieu Formation")

    fiche = (await _lire(db_session, "Esmieu"))["contacts"][0]

    assert fiche["email"] == "nathalie@exemple.fr"
    assert fiche["company"] == "Esmieu Formation"
