"""
J4 (31/07/2026) - Le bouton Aide envoyait sa demande au modèle.

Le bouton Aide de la coque envoie littéralement le texte `/aide`
(`ConversationCanvasPrototype.tsx:1289`). Or le parseur d'actions ne reconnaît
que l'enveloppe `{action: aide}` (`chat_actions.py:233`) : `/aide` n'est pas
une enveloppe, donc le texte partait au LLM comme une question ordinaire.

Ce que voyait l'utilisateur : une réponse inventée, variable d'un modèle à
l'autre, parfois fausse sur les capacités réelles de l'application — au lieu de
l'aide dérivée du code (`available_actions_text()`), qui est la seule à jour.
Avec un fournisseur lent, il payait même des tokens pour ça.

Le menu des commandes présente le vocabulaire en `/` : c'est ce que les gens
tapent. La reconnaissance doit se faire là, pas seulement dans l'enveloppe.
"""
import pytest


class TestLaCommandeAideRepondLocalement:
    def test_slash_aide_est_reconnu(self):
        from app.services.chat_actions import parse_action_message

        action = parse_action_message("/aide")

        assert action is not None, (
            "/aide part au LLM : le bouton Aide de l'interface produit une "
            "réponse inventée au lieu de l'aide dérivée du code"
        )
        assert action.kind == "help"

    @pytest.mark.parametrize("saisie", ["/aide", "/AIDE", "  /aide  ", "/aidé"])
    def test_tolerance_de_saisie(self, saisie):
        """Même tolérance que l'enveloppe : casse, accents, espaces."""
        from app.services.chat_actions import parse_action_message

        action = parse_action_message(saisie)
        assert action is not None and action.kind == "help", saisie

    def test_l_enveloppe_historique_marche_toujours(self):
        from app.services.chat_actions import parse_action_message

        action = parse_action_message("{action: aide}")
        assert action is not None and action.kind == "help"

    @pytest.mark.parametrize(
        "saisie",
        [
            "/aide moi à rédiger ce courrier",
            "/facture",
            "Peux-tu m'aider ?",
            "/",
        ],
    )
    def test_le_reste_continue_d_aller_au_modele(self, saisie):
        """Garde-fou : ne pas confisquer des messages qui ne sont pas la commande.

        « /aide moi à rédiger » est une vraie demande adressée au modèle, pas
        un appel à la fiche d'aide.
        """
        from app.services.chat_actions import parse_action_message

        assert parse_action_message(saisie) is None, saisie
