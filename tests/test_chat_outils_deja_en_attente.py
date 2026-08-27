"""D1, trou jumeau : l'agenda pouvait lui aussi produire deux cartes.

Un message mixte (« note ça, [rdv: demain 14h avec Paul] ») prépare la
création d'agenda par la commande déterministe : sa carte de confirmation est
relayée au flux (chat.py, relais de `pending_confirmations`). Le même flux
appelle ensuite le modèle AVEC `create_calendar_event` toujours dans sa liste
d'outils, et un contexte qui lui dit que l'action n'est pas exécutée. Le
modèle rappelle l'outil : seconde carte pour le même rendez-vous.

L'empreinte d'action ne couvre pas ce cas (la carte inline porte une clé
`_confirmation_destination` que l'appel du modèle n'a pas). Le verrou correct
est en amont : un outil sensible dont une action attend DÉJÀ validation ne
doit pas être proposé au modèle pour ce tour.
"""
import pathlib

from app.routers.chat import retirer_outils_deja_en_attente


def _outil(nom):
    return {"type": "function", "function": {"name": nom}}


def _noms(outils):
    return [o["function"]["name"] for o in outils]


def test_un_outil_dont_une_action_attend_validation_nest_pas_propose():
    outils = [_outil("create_calendar_event"), _outil("read_emails")]
    restants = retirer_outils_deja_en_attente(
        outils, [{"tool_name": "create_calendar_event", "confirmation_id": "c1"}]
    )
    assert _noms(restants) == ["read_emails"]


def test_les_autres_outils_restent_disponibles():
    """Ne jamais couper tout l'outillage : le modèle doit encore lire, chercher."""
    outils = [_outil("create_calendar_event"), _outil("read_emails"), _outil("web_search")]
    restants = retirer_outils_deja_en_attente(
        outils, [{"tool_name": "create_calendar_event", "confirmation_id": "c1"}]
    )
    assert set(_noms(restants)) == {"read_emails", "web_search"}


def test_sans_confirmation_en_attente_la_liste_est_intacte():
    outils = [_outil("create_calendar_event"), _outil("send_email")]
    assert retirer_outils_deja_en_attente(outils, []) is outils
    assert retirer_outils_deja_en_attente(outils, None) is outils


def test_un_outil_expose_via_mcp_est_reconnu_malgre_son_prefixe():
    """BUG-121 : '{serveur}__create_calendar_event' est le même outil."""
    outils = [_outil("agenda__create_calendar_event"), _outil("read_emails")]
    restants = retirer_outils_deja_en_attente(
        outils, [{"tool_name": "create_calendar_event", "confirmation_id": "c1"}]
    )
    assert _noms(restants) == ["read_emails"]


def test_une_entree_malformee_ne_retire_rien():
    """Fail-open : on ne prive pas le modèle d'un outil sur une donnée douteuse."""
    outils = [_outil("create_calendar_event")]
    restants = retirer_outils_deja_en_attente(outils, [{"confirmation_id": "c1"}])
    assert _noms(restants) == ["create_calendar_event"]


def test_le_filtre_est_reellement_branche_dans_le_flux():
    """Anti-fonction-morte : ce chantier a déjà livré une autorité sans appelant."""
    source = pathlib.Path("src/backend/app/routers/chat.py").read_text()
    appels = source.count("retirer_outils_deja_en_attente(")
    assert appels >= 2, "défini mais jamais appelé dans le flux"
