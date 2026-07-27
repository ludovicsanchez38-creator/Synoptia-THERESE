"""
Triage Discord 25/07/2026 - « syntaxe de création de variable peu intuitif ».

Le testeur écrivait le nom entre guillemets ou avec des accents. La réponse se
contentait de rappeler la grammaire abstraite, sans montrer la commande juste.
Elle propose désormais la commande corrigée.
"""


class TestMessageSyntaxeVariable:
    def test_le_nom_entre_guillemets_recoit_la_commande_corrigee(self):
        from app.services.chat_actions import _parse_variable_body as parse_chat_action

        action = parse_chat_action('variable creer "priorite" "haute"')

        assert action is not None
        assert action.var_op == "erreur"
        assert '{action: variable creer priorite "haute"}' in action.var_message

    def test_un_nom_accentue_recoit_sa_version_sans_accents(self):
        from app.services.chat_actions import _parse_variable_body as parse_chat_action

        action = parse_chat_action('variable creer priorité "haute"')

        assert action is not None
        assert action.var_op == "erreur"
        assert '{action: variable creer priorite "haute"}' in action.var_message

    def test_un_nom_avec_espaces_est_propose_en_underscore(self):
        from app.services.chat_actions import _parse_variable_body as parse_chat_action

        action = parse_chat_action('variable creer ma priorite "haute"')

        assert action is not None
        assert action.var_op == "erreur"
        assert "ma_priorite" in action.var_message

    def test_une_commande_valide_reste_valide(self):
        from app.services.chat_actions import _parse_variable_body as parse_chat_action

        action = parse_chat_action('variable creer priorite "haute"')

        assert action is not None
        assert action.var_op == "creer"
        assert action.var_name == "priorite"
        assert action.var_value == "haute"
