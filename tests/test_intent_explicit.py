"""
BUG-137 (11/07/2026, Dr_logic) : THÉRÈSE générait des fichiers alors que
l'utilisateur voulait seulement NOMMER un document. Racine : la détection
d'intention par MOTS-CLÉS forçait un skill de génération sur des phrases
ordinaires (« créer.*document »).

Règle produit posée avec le testeur : toute action à effet de bord exige une
demande EXPLICITE - {action: produire ...} (déterministe), {{action: skill}}
(forçage), le sélecteur UI, ou l'outil generate_document au jugement du
modèle (consigne resserrée). La détection par mots-clés est SUPPRIMÉE.
"""
from app.services.skills.intent_detector import resolve_skill_from_message


class TestPlusDeDetectionParMotsCles:
    def test_phrase_ordinaire_ne_force_plus_un_skill(self):
        for message in (
            "Crée un document nommé rapport, on le remplira plus tard",
            "je veux préparer une présentation la semaine prochaine",
            "peux-tu faire un rapport sur la situation ?",
            "on doit produire un guide d'utilisation un jour",
        ):
            skill_id, fmt, cleaned = resolve_skill_from_message(message)
            assert skill_id is None, f"mots-clés ont forcé {skill_id} sur : {message}"
            assert cleaned == message

    def test_forcage_explicite_conserve(self):
        skill_id, _fmt, cleaned = resolve_skill_from_message(
            "{{action: docx-pro}} Rapport sur les ventes"
        )
        assert skill_id == "docx-pro"
        assert "{{action" not in cleaned

    def test_skill_explicite_ui_conserve(self):
        skill_id, _fmt, cleaned = resolve_skill_from_message(
            "n'importe quoi", explicit_skill_id="xlsx-pro"
        )
        assert skill_id == "xlsx-pro"
        assert cleaned == "n'importe quoi"
