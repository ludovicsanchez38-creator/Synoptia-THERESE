"""
Une trace peut en annuler une autre (tranche B du 29/08).

Les notes de Ludo se corrigent en permanence : 17 des 120 notes importées
portent une rétractation (« CORRECTION de ma note de ce matin », « CORRIGE LA
NOTE DE 15h40 DU MÊME JOUR, qui disait FORGER »). Rien dans le modèle ne
portait ça : la note fausse et sa correction partaient au modèle à égalité, et
s'affichaient avec la même icône.

Ce n'est pas un moteur de versions. C'est un statut et un pointeur.
"""
import json

import pytest
from app.models.entities import Activity, Contact
from app.services.memory_tools import execute_memory_tool
from sqlalchemy.ext.asyncio import AsyncSession


async def _contact_avec_correction(session: AsyncSession) -> tuple[Contact, Activity, Activity]:
    c = Contact(first_name="Nathalie", last_name="Esmieu")
    session.add(c)
    await session.commit()
    fausse = Activity(contact_id=c.id, type="note", title="Seance FORGER calee",
                      description="FORGER 490 EUR")
    session.add(fausse)
    await session.commit()
    correction = Activity(contact_id=c.id, type="note",
                          title="CORRECTION : c'est PROPULSER et non FORGER",
                          description="Pack V2 regenere, 2 490 EUR")
    session.add(correction)
    await session.commit()
    return c, fausse, correction


@pytest.mark.asyncio
async def test_une_trace_naît_en_vigueur(db_session: AsyncSession):
    c = Contact(first_name="Test", last_name="Statut")
    db_session.add(c)
    await db_session.commit()
    a = Activity(contact_id=c.id, type="note", title="Une note")
    db_session.add(a)
    await db_session.commit()

    assert a.statut == "en_vigueur"
    assert a.remplace_id is None


@pytest.mark.asyncio
async def test_l_annulation_se_pose_par_l_api(client, db_session: AsyncSession):
    """Un champ que personne ne peut écrire ne sert à rien.

    C'est la leçon de `next_follow_up` ce matin : le champ existait, aucune
    route ne le posait, et la fonctionnalité était inutilisable.
    """
    c, fausse, correction = await _contact_avec_correction(db_session)
    id_fausse, id_correction = fausse.id, correction.id

    reponse = await client.patch(
        f"/api/crm/activities/{id_fausse}",
        json={"statut": "annulee", "remplace_par_id": id_correction},
    )
    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["statut"] == "annulee"
    assert reponse.json()["remplace_id"] == id_correction


@pytest.mark.asyncio
async def test_le_modele_voit_qu_une_trace_est_annulee(db_session: AsyncSession):
    c, fausse, correction = await _contact_avec_correction(db_session)
    fausse.statut = "annulee"
    fausse.remplace_id = correction.id
    db_session.add(fausse)
    await db_session.commit()

    charge = json.loads(await execute_memory_tool("read_contact", {"query": "Esmieu"}, db_session))
    traces = charge["contacts"][0]["traces"]

    annulees = [t for t in traces if t.get("statut") == "annulee"]
    assert len(annulees) == 1, "la trace annulée doit rester visible, marquée"
    assert "FORGER" in (annulees[0].get("texte") or "")
    assert "annulee" in charge["consigne"].lower() or "annulée" in charge["consigne"].lower(), (
        "la consigne doit dire au modèle de ne pas s'appuyer sur une trace annulée"
    )


@pytest.mark.asyncio
async def test_une_trace_annulee_ne_pese_pas_comme_une_autre(db_session: AsyncSession):
    """Elle reste lisible, mais elle ne doit pas occuper la fenêtre des récentes.

    Les cinq dernières activités partent au modèle : si deux annulées les
    remplissent, la correction qui compte tombe hors champ.
    """
    c = Contact(first_name="Fenetre", last_name="Glissante")
    db_session.add(c)
    await db_session.commit()
    for i in range(6):
        db_session.add(Activity(contact_id=c.id, type="note", title=f"Annulee {i}",
                                statut="annulee"))
    await db_session.commit()
    db_session.add(Activity(contact_id=c.id, type="note", title="LA correction qui compte"))
    await db_session.commit()

    charge = json.loads(await execute_memory_tool("read_contact", {"query": "Glissante"}, db_session))
    traces = charge["contacts"][0]["traces"]

    titres = [t.get("titre") for t in traces]
    assert "LA correction qui compte" in titres, (
        "une correction en vigueur ne doit pas être chassée par des traces annulées"
    )


@pytest.mark.asyncio
async def test_un_statut_invente_est_refuse(client, db_session: AsyncSession):
    """Sans cette garde, n'importe quelle chaîne devient un statut, et le
    filtre `statut == 'en_vigueur'` cesse silencieusement de voir la trace."""
    c, fausse, _ = await _contact_avec_correction(db_session)
    id_fausse = fausse.id

    reponse = await client.patch(
        f"/api/crm/activities/{id_fausse}", json={"statut": "peut-etre"}
    )

    assert reponse.status_code == 400, reponse.text


@pytest.mark.asyncio
async def test_une_trace_ne_s_annule_pas_elle_meme(client, db_session: AsyncSession):
    """Un pointeur circulaire ferait dire à l'interface qu'une trace est
    remplacée par elle-même."""
    c, fausse, _ = await _contact_avec_correction(db_session)
    id_fausse = fausse.id

    reponse = await client.patch(
        f"/api/crm/activities/{id_fausse}",
        json={"statut": "annulee", "remplace_par_id": id_fausse},
    )

    assert reponse.status_code == 400, reponse.text


@pytest.mark.asyncio
async def test_remettre_en_vigueur_efface_le_pointeur(client, db_session: AsyncSession):
    """Sinon la fiche garde un lien vers un remplaçant caduc."""
    c, fausse, correction = await _contact_avec_correction(db_session)
    id_fausse, id_correction = fausse.id, correction.id

    await client.patch(
        f"/api/crm/activities/{id_fausse}",
        json={"statut": "annulee", "remplace_par_id": id_correction},
    )
    # Le client renvoie les DEUX champs, comme le ferait une interface qui
    # poste son formulaire entier. C'est le cas qui distingue : sans la garde,
    # le pointeur survit à la remise en vigueur.
    remise = await client.patch(
        f"/api/crm/activities/{id_fausse}",
        json={"statut": "en_vigueur", "remplace_par_id": id_correction},
    )

    assert remise.json()["remplace_id"] is None, (
        "remise en vigueur : le pointeur vers le remplaçant doit disparaître"
    )


@pytest.mark.asyncio
async def test_la_liste_des_activites_rend_le_statut(client, db_session: AsyncSession):
    """La chaîne entière, pas une surface.

    Le modèle voit le statut, la route d'annulation le pose — mais si la LISTE
    ne le rend pas, la timeline ne peut pas barrer la trace, et l'écran
    continue d'afficher la note fausse comme les autres.
    """
    c, fausse, correction = await _contact_avec_correction(db_session)
    id_c, id_fausse, id_correction = c.id, fausse.id, correction.id

    await client.patch(
        f"/api/crm/activities/{id_fausse}",
        json={"statut": "annulee", "remplace_par_id": id_correction},
    )

    listee = await client.get(f"/api/crm/activities?contact_id={id_c}")
    assert listee.status_code == 200, listee.text
    par_id = {a["id"]: a for a in listee.json()}

    assert par_id[id_fausse]["statut"] == "annulee"
    assert par_id[id_fausse]["remplace_id"] == id_correction
    assert par_id[id_correction]["statut"] == "en_vigueur"
