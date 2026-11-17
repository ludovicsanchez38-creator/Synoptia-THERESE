"""La réserve d'agenda suit les dates, les heures et la demande du tour."""

import pytest
from app.models.entities import Message
from app.services.providers.base import StreamEvent
from sqlmodel import select

from tests.test_b1797_agenda_sans_outil import MENTION, _texte
from tests.test_r2_3_outil import fournisseur  # noqa: F401

HORAIRES = "- 09h : Réunion fictive\n- 14h : Entretien fictif"


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True], ids=["sans_flux", "flux"])
@pytest.mark.parametrize(("contenu", "converti", "mention_attendue"), [
    (
        "- 09:00 Réunion client\n- 14:00 Entretien",
        "- 09:00 Réunion client\n- 14:00 Entretien",
        True,
    ),
    (
        "- 09h Réunion client\n- 14h Entretien",
        "- 09h Réunion client\n- 14h Entretien",
        True,
    ),
    (
        "- **09:00** Réunion client\n- **14:00** Entretien",
        "- **09:00** Réunion client\n- **14:00** Entretien",
        True,
    ),
    (
        "| Heure | Rendez-vous |\n| --- | --- |\n"
        "| 09:00 | Réunion client |\n| 14:00 | Entretien |",
        "- Heure : 09:00 | Rendez-vous : Réunion client\n"
        "- Heure : 14:00 | Rendez-vous : Entretien",
        True,
    ),
    (
        "| Rendez-vous | Horaire |\n| --- | --- |\n"
        "| Réunion client | 9h |\n| Entretien | 14h |",
        "- Rendez-vous : Réunion client | Horaire : 9h\n"
        "- Rendez-vous : Entretien | Horaire : 14h",
        True,
    ),
    (
        "- 3h30 de préparation\n- 2h15 de trajet",
        "- 3h30 de préparation\n- 2h15 de trajet",
        False,
    ),
    (
        "| Durée | Activité |\n| --- | --- |\n"
        "| 3h | Préparation |\n| 2h | Trajet |",
        "- Durée : 3h | Activité : Préparation\n"
        "- Durée : 2h | Activité : Trajet",
        False,
    ),
    (
        "| **Durée** | Activité |\n| --- | --- |\n"
        "| 3h | Préparation |\n| 2h | Trajet |",
        "- **Durée** : 3h | Activité : Préparation\n"
        "- **Durée** : 2h | Activité : Trajet",
        False,
    ),
    (
        "| Durées | Activité |\n| --- | --- |\n"
        "| 3h | Préparation |\n| 2h | Trajet |",
        "- Durées : 3h | Activité : Préparation\n"
        "- Durées : 2h | Activité : Trajet",
        False,
    ),
    (
        "| Activité | _Durées_ |\n| --- | --- |\n"
        "| Préparation | 3h |\n| Trajet | 2h |",
        "- Activité : Préparation | _Durées_ : 3h\n"
        "- Activité : Trajet | _Durées_ : 2h",
        False,
    ),
    (
        "| Activité | **DURÉES** |\n| --- | --- |\n"
        "| Préparation | 3h |\n| Trajet | 2h |",
        "- Activité : Préparation | **DURÉES** : 3h\n"
        "- Activité : Trajet | **DURÉES** : 2h",
        False,
    ),
    (
        "| **Durées** | Horaire |\n| --- | --- |\n"
        "| 3h | 09:00 |\n| 2h | 14:00 |",
        "- **Durées** : 3h | Horaire : 09:00\n"
        "- **Durées** : 2h | Horaire : 14:00",
        True,
    ),
    (
        "* **Durée** : 3h\n* **Durée** : 2h",
        "* **Durée** : 3h\n* **Durée** : 2h",
        False,
    ),
    (
        "* **Horaire** : 09:00\n* **Horaire** : 14:00",
        "* **Horaire** : 09:00\n* **Horaire** : 14:00",
        True,
    ),
    (
        "- Réunion client : 09:00–10:00\n- Entretien : 14:00–15:00",
        "- Réunion client : 09:00–10:00\n- Entretien : 14:00–15:00",
        True,
    ),
    (
        "| Rendez-vous | Horaire |\n| --- | --- |\n"
        "| Réunion client | 09:00–10:00 |\n| Entretien | 14:00–15:00 |",
        "- Rendez-vous : Réunion client | Horaire : 09:00–10:00\n"
        "- Rendez-vous : Entretien | Horaire : 14:00–15:00",
        True,
    ),
    (
        "| Horaire | Rendez-vous |\n| --- | --- |\n"
        "| **09h-10h** | Réunion client |\n| **14h-15h** | Entretien |",
        "- Horaire : **09h-10h** | Rendez-vous : Réunion client\n"
        "- Horaire : **14h-15h** | Rendez-vous : Entretien",
        True,
    ),
    (
        "1. Réunion client : 09:00\n2. Entretien : 14:00",
        "1. Réunion client : 09:00\n2. Entretien : 14:00",
        True,
    ),
    (
        "1) Réunion client : 09:00\n2) Entretien : 14:00",
        "1) Réunion client : 09:00\n2) Entretien : 14:00",
        True,
    ),
    (
        "1. Durée : 3h\n2. Durée : 2h",
        "1. Durée : 3h\n2. Durée : 2h",
        False,
    ),
    (
        "| Rendez-vous | Horaire |\n| --- | --- |\n"
        "| Réunion client | **09:00**–**10:00** |\n"
        "| Entretien | **14:00**–**15:00** |",
        "- Rendez-vous : Réunion client | Horaire : **09:00**–**10:00**\n"
        "- Rendez-vous : Entretien | Horaire : **14:00**–**15:00**",
        True,
    ),
    (
        "| Horaire | Rendez-vous |\n| --- | --- |\n"
        "| **09:00**–**10:00** | Réunion client |\n"
        "| **14:00**–**15:00** | Entretien |",
        "- Horaire : **09:00**–**10:00** | Rendez-vous : Réunion client\n"
        "- Horaire : **14:00**–**15:00** | Rendez-vous : Entretien",
        True,
    ),
    (
        "| Rendez-vous | Horaire |\n| --- | --- |\n"
        "| Réunion client | __09:00__–__10:00__ |\n"
        "| Entretien | __14:00__–__15:00__ |",
        "- Rendez-vous : Réunion client | Horaire : __09:00__–__10:00__\n"
        "- Rendez-vous : Entretien | Horaire : __14:00__–__15:00__",
        True,
    ),
], ids=["heures_sans_separateur", "heures_h_sans_separateur", "heures_en_gras",
        "tableau_heure_en_premier", "tableau_heure_en_second", "durees_avec_minutes",
        "tableau_de_durees", "duree_gras", "durees_pluriel", "durees_italique",
        "durees_gras_pluriel", "durees_et_horaires", "duree_gras_puce_etoile",
        "horaire_gras_puce_etoile", "plages_apres_libelle", "tableau_plages_en_second",
        "tableau_plages_en_premier_gras", "liste_numerotee_point",
        "liste_numerotee_parenthese", "liste_numerotee_durees",
        "tableau_plages_bornes_gras_second", "tableau_plages_bornes_gras_premier",
        "tableau_plages_bornes_gras_soulignes"])
async def test_horaires_et_tableaux_sans_separateur_conservent_la_reserve(
    client, db_session, fournisseur, contenu, converti, mention_attendue, stream  # noqa: F811
):
    class Modele:
        async def stream(self, *args, **kwargs):
            yield StreamEvent(type="text", content=contenu)
            yield StreamEvent(type="done", stop_reason="end_turn")

    fournisseur[0]._provider = Modele()
    reponse = await client.post("/api/chat/send", json={
        "message": "Lis mon agenda de demain", "include_memory": False, "stream": stream,
    })
    attendu = (contenu if stream else converti) + ("\n\n" + MENTION if mention_attendue else "")
    assert _texte(reponse, stream) == attendu
    messages = (await db_session.execute(select(Message))).scalars().all()
    assert [message.content for message in messages if message.role == "assistant"] == [attendu]


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True], ids=["sans_flux", "flux"])
@pytest.mark.parametrize(("demande", "mention_attendue"), [
    ("Explique comment je consulte mon agenda demain", False),
    ("Rédige un résumé de la liste de mes rendez-vous de demain", False),
    ("Rédige une liste de mes rendez-vous demain", False),
    ("Rédige une longue liste de mes rendez-vous de demain", False),
    ("Rédige une courte et claire liste de mes rendez-vous de demain", False),
    ("Écris une brève et utile liste de mes rendez-vous demain", False),
    ("Rédige une très courte et claire liste de mes rendez-vous demain", False),
    ("Rédige une courte et très claire liste de mes rendez-vous demain", False),
    ("Rédige une courte et claire et structurée liste de mes rendez-vous demain", False),
    ("Rédige une liste précise de mes rendez-vous demain", False),
    ("Rédige une liste pour mon agenda de demain", False),
    ("Rédige une liste concernant mon agenda de demain", False),
    ("Rédige une note et liste mes rendez-vous de demain", True),
    ("Rédige une note et enfin liste mes rendez-vous de demain", True),
    ("Rédige une note et à présent liste mes rendez-vous de demain", True),
    ("Rédige une note et enfin liste rapidement mes rendez-vous de demain", True),
    ("Rédige une note et à présent liste mon agenda de demain", True),
    ("Rédige une note et demain liste mes rendez-vous", True),
    ("Rédige une note et lundi liste mes rendez-vous", True),
    ("Rédige une note et rapidement liste mes rendez-vous de demain", True),
    ("Rédige une note et très rapidement liste mes rendez-vous de demain", True),
    ("Rédige une note et après liste mes rendez-vous de demain", True),
    ("Rédige une note et vite liste mes rendez-vous de demain", True),
    ("Rédige une note et de suite liste mes rendez-vous de demain", True),
    ("Explique comment, demain, je consulte mon agenda et rédige un mail", False),
    ("Explique comment j'ai consulté mon agenda lundi", False),
    ("Explique comment Marie consulte mon agenda demain", False),
    ("Explique comment, demain, Marie consulte mon agenda", False),
    ("Explique la phrase “Consulte mon agenda demain”", False),
    ("Explique la phrase « Consulte mon agenda demain »", False),
    ('Explique la phrase "Consulte mon agenda demain"', False),
    ("Explique la phrase ‘Consulte mon agenda demain’", False),
    ("Explique la phrase 'Consulte mon agenda demain'", False),
    ("Explique ‘Consulte mon agenda demain, c’est urgent’", False),
    ("Explique 'Consulte mon agenda demain, c'est urgent'", False),
    ("Résume « Consulte mon agenda demain »", False),
    ("Explique “Consulte mon agenda demain”, puis lis mon agenda lundi", True),
    ("Résume « Consulte mon agenda demain », puis lis mon agenda lundi", True),
    ("Explique “Bonjour”, puis lis mon agenda lundi", True),
    ("Explique « Bonjour », puis lis « mon agenda » demain", True),
    ("Explique “Bonjour”, puis liste “mes rendez-vous” demain", True),
    ("Lis « mon agenda » demain et explique « Bonjour »", True),
    ("Explique « Bonjour », puis lis mon agenda pour « demain »", True),
    ("Explique « Bonjour », puis peux-tu lire « mon agenda » lundi ?", True),
    ("Explique « demain », puis lis mon agenda", False),
    ("Explique « Bonjour » puis résume « Consulte mon agenda demain »", False),
    ("« Consulte mon agenda demain » : explique cette phrase", False),
    ("Explique la liste « Consulte mon agenda demain »", False),
    ("Résume une liste « Consulte mon agenda demain »", False),
    ("Explique comment je consulte « puis lis mon agenda demain »", False),
    ("Explique comment Marie consulte « puis lis mon agenda demain »", False),
    ("Explique comment, demain, Marie consulte « puis lis mon agenda demain »", False),
    ("Explique comment Marie consulte son agenda, puis consulte « mon agenda » demain", True),
    ("Explique “Consulte mon agenda demain”, puis lis mon agenda", False),
    ("Résume « Ajoute un rendez-vous demain », puis consulte mon agenda lundi", True),
    ("Explique comment je consulte mon agenda demain, puis lis mon agenda demain", True),
    ("Explique comment lire mon agenda, puis demain consulte mon agenda.", True),
    ("Explique comment lire mon agenda, puis consulte mon agenda demain.", True),
    ("Explique comment lire mon agenda, ensuite demain consulte mon agenda.", True),
    ("Explique comment lire mon agenda, ensuite consulte mon agenda demain.", True),
    ("Rédige une liste, puis consulte mon agenda demain", True),
    ("Rédige un mail, puis liste mes rendez-vous de demain", True),
    ("Rédige une note puis liste mes rendez-vous de demain", True),
    ("Consulte mon agenda demain et explique comment je consulte mon agenda", True),
    ("D'abord consulte mon agenda demain et rédige un mail", True),
    ("Pour demain lis mon agenda puis rédige un mail", True),
    ("Après avoir consulté mon agenda demain, rédige un mail", True),
    ("Rédige un mail après avoir consulté mon agenda demain", True),
    ("S'il te plaît consulte mon agenda demain et rédige un mail", True),
], ids=["explication_je", "liste_nominale", "liste_a_rediger", "liste_avec_adjectif",
        "liste_adjectifs_coordonnes", "liste_adjectifs_coordonnes_breve",
        "liste_adjectifs_coordonnes_tres", "liste_adjectifs_et_tres",
        "liste_trois_adjectifs_coordonnes", "liste_adjectif_apres_nom",
        "liste_pour_agenda", "liste_concernant_agenda", "note_et_liste_verbale",
        "note_et_enfin_liste_verbale",
        "note_et_a_present_liste_verbale", "note_et_enfin_liste_rapidement",
        "note_et_a_present_liste_agenda",
        "note_et_demain_liste_verbale", "note_et_lundi_liste_verbale", "note_et_rapidement_liste_verbale",
        "note_et_tres_rapidement_liste_verbale", "note_et_apres_liste_verbale",
        "note_et_vite_liste_verbale", "note_et_de_suite_liste_verbale",
        "explication_et_redaction", "explication_passee", "explication_tiers",
        "explication_tiers_avec_incise", "citation_guillemets_courbes",
        "citation_guillemets_francais", "citation_guillemets_droits",
        "citation_simples_courbes", "citation_simples_droits",
        "citation_courbe_avec_apostrophe", "citation_droite_avec_apostrophe", "resume_citation",
        "citation_puis_lecture", "resume_citation_puis_lecture", "citation_neutre_puis_lecture",
        "citation_puis_objet_agenda_cite", "citation_puis_objet_rdv_cite",
        "objet_agenda_cite_puis_explication",
        "citation_puis_date_citee", "citation_puis_peux_tu_lire_agenda_cite",
        "citation_date_puis_lecture_sans_date", "deux_citations_expliquees",
        "citation_avant_explication",
        "citation_liste_expliquee", "citation_liste_resumee", "citation_apres_je_consulte",
        "citation_apres_marie_consulte", "citation_apres_marie_avec_incise",
        "citation_apres_explication_de_marie_et_lecture",
        "citation_date_seule", "citation_action_puis_lecture", "explication_puis_lecture",
        "explication_puis_demain_lecture", "explication_puis_lecture_demain",
        "explication_ensuite_demain_lecture", "explication_ensuite_lecture_demain",
        "redaction_puis_lecture",
        "redaction_puis_liste", "redaction_note_puis_liste", "lecture_puis_explication",
        "lecture_d_abord", "lecture_apres_repere", "lecture_prealable", "lecture_avant_redaction",
        "lecture_politesse"])
async def test_explication_ou_redaction_seule_ne_demande_pas_la_lecture(
    client, db_session, fournisseur, demande, mention_attendue, stream  # noqa: F811
):
    class Modele:
        async def stream(self, *args, **kwargs):
            yield StreamEvent(type="text", content=HORAIRES)
            yield StreamEvent(type="done", stop_reason="end_turn")

    fournisseur[0]._provider = Modele()
    reponse = await client.post("/api/chat/send", json={
        "message": demande, "include_memory": False, "stream": stream,
    })
    attendu = HORAIRES + ("\n\n" + MENTION if mention_attendue else "")
    assert _texte(reponse, stream) == attendu
    messages = (await db_session.execute(select(Message))).scalars().all()
    assert [message.content for message in messages if message.role == "assistant"] == [attendu]


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True], ids=["sans_flux", "flux"])
@pytest.mark.parametrize(("demande", "contenu", "mention_attendue"), [
    ("Mon agenda, point 1.2", HORAIRES, False),
    ("Mon agenda, point 2.10", HORAIRES, False),
    ("Mon agenda au 32/13/2026 ?", HORAIRES, False),
    ("Mon agenda au 2026-02-31 ?", HORAIRES, False),
    ("Lis mon agenda de demain", "- 3h de préparation\n- 2h de trajet", False),
    ("Lis mon agenda de demain", "- 3h\n- 2h", False),
    ("Lis mon agenda de demain et rédige un mail", HORAIRES, True),
    ("Rédige un mail, puis consulte mon planning de lundi", HORAIRES, True),
    ("Peux-tu lire mon agenda demain et rédiger un mail ?", HORAIRES, True),
    ("Explique comment lire mon agenda demain et rédige un mail", HORAIRES, False),
    ("Rédige un mail pour mon agenda de demain", HORAIRES, False),
    ("Mon agenda du 01/12/2026 ?", HORAIRES, True),
    ("Mon agenda du 01.12.2026 ?", HORAIRES, True),
    ("Mon agenda du 2026-12-01 ?", HORAIRES, True),
    ("Lis mon agenda de demain", "- Départ à 3h\n- Retour à 2h", True),
    ("Lis mon agenda de demain", "- À 14h, trajet de 3h\n- À 16h, séance de 2h", True),
], ids=[
    "point_decimal", "point_decimal_deux_chiffres", "date_invalide", "date_iso_invalide",
    "durees", "durees_seules", "lecture_puis_redaction", "redaction_puis_lecture",
    "lire_puis_rediger", "explication_et_redaction", "redaction_seule",
    "date_barres", "date_points", "date_iso", "heures_a",
    "horaires_et_durees",
])
async def test_la_mention_suit_les_reperes_reels_et_la_lecture_demandee(
    client, db_session, fournisseur, demande, contenu, mention_attendue, stream  # noqa: F811
):
    class Modele:
        async def stream(self, *args, **kwargs):
            yield StreamEvent(type="text", content=contenu)
            yield StreamEvent(type="done", stop_reason="end_turn")

    fournisseur[0]._provider = Modele()
    reponse = await client.post("/api/chat/send", json={
        "message": demande, "include_memory": False, "stream": stream,
    })
    attendu = contenu + ("\n\n" + MENTION if mention_attendue else "")
    assert _texte(reponse, stream) == attendu
    messages = (await db_session.execute(select(Message))).scalars().all()
    assert [message.content for message in messages if message.role == "assistant"] == [attendu]
