"""BUG-B : message de synchro CRM actionnable quand la feuille est vide.

Quand l'utilisateur connecte Google sans renseigner d'ID, Thérèse crée une feuille
vide et la synchro remonte 0 element, sans explication. On guide vers l'option
'feuille existante'.
"""

from app.services.crm_sync import build_sync_message


def test_message_normal_quand_elements_synchronises():
    msg = build_sync_message(5, has_errors=False)
    assert "5" in msg
    assert "vide" not in msg.lower()


def test_message_vide_guide_vers_feuille_existante():
    msg = build_sync_message(0, has_errors=False)
    low = msg.lower()
    assert "vide" in low
    # doit expliquer comment pointer vers une feuille existante
    assert "identifiant" in low or "id de la feuille" in low
    assert "synchron" in low  # invite a resynchroniser


def test_message_zero_avec_erreurs_nest_pas_le_message_feuille_vide():
    # 0 element MAIS des erreurs => c'est un echec, pas une feuille vide.
    msg = build_sync_message(0, has_errors=True)
    assert "vide" not in msg.lower()
