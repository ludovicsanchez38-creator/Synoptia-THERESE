"""BUG-171 — un échec de brouillon sans cause, et un faux brouillon.

Le testeur : « La génération du brouillon a échoué. Tu peux écrire la réponse
manuellement. » Sa réaction : « c'est amusant de préciser tu peux écrire la
réponse manuellement, sans déconner ! » Il a raison : l'interface transforme une
panne technique en conseil évident.

La revue a montré que le défaut est en amont, et qu'il est pire. Le générateur
n'échoue pas : il ATTRAPE l'échec du modèle et renvoie un brouillon fabriqué —
« Je reviens vers vous rapidement » — avec un HTTP 200. L'utilisateur reçoit donc
un texte qu'aucune IA n'a écrit, sans jamais savoir que la génération a échoué.
Il peut l'envoyer tel quel à son client.

Entre un échec annoncé et un faux succès, l'échec annoncé est toujours
préférable.

Second point, de confidentialité : l'erreur brute d'un fournisseur contient
parfois une URL, un nom d'hôte, voire un fragment de clé. Elle ne doit pas
atterrir telle quelle à l'écran ; la cause est traduite, le détail va au journal.
"""
import pytest


class TestUnEchecNeProduitPasUnFauxBrouillon:
    @pytest.mark.asyncio
    async def test_l_echec_du_modele_est_signale_et_non_maquille(self, monkeypatch):
        """Le cœur du bug : un texte inventé présenté comme une réponse."""
        from app.services import email_response_generator as module

        class ServiceEnPanne:
            config = type(
                "C", (), {"provider": type("P", (), {"value": "ollama"})(), "model": "x"}
            )()

            async def generate_content(self, *args, **kwargs):
                raise RuntimeError("connection refused")

        monkeypatch.setattr(
            module, "get_llm_service", lambda: ServiceEnPanne(), raising=False
        )

        with pytest.raises(module.GenerationImpossible):
            await module.EmailResponseGenerator.generate_response(
                subject="Devis",
                from_name="Client",
                from_email="client@exemple.fr",
                body="Bonjour, pouvez-vous me faire un devis ?",
            )

    @pytest.mark.asyncio
    async def test_le_texte_de_repli_a_disparu(self):
        """Verrou : la phrase fabriquée ne doit plus exister dans le code."""
        import inspect

        from app.services import email_response_generator as module

        source = inspect.getsource(module)

        assert "Je reviens vers vous rapidement" not in source, (
            "le brouillon fabriqué est toujours là : un échec du modèle peut "
            "encore être envoyé à un client comme s'il avait été rédigé"
        )


class TestLaCauseEstDiteSansExposerLaTechnique:
    @pytest.mark.parametrize(
        "brute,attendu",
        [
            ("connection refused", "joindre"),
            ("401 Unauthorized: invalid api key sk-abc123", "clé"),
            ("Read timed out after 30s", "trop de temps"),
            ("does not support tools", "modèle"),
        ],
    )
    def test_chaque_cause_connue_devient_une_phrase_utile(self, brute, attendu):
        from app.services.email_response_generator import cause_lisible

        message = cause_lisible(brute)

        assert attendu in message.lower(), (
            f"« {brute} » devient « {message} », qui n'aide pas l'utilisateur"
        )

    def test_aucun_secret_ne_traverse(self):
        """Une clé d'API dans une erreur ne doit jamais s'afficher."""
        from app.services.email_response_generator import cause_lisible

        message = cause_lisible("401 Unauthorized: invalid api key sk-proj-SECRET42")

        assert "sk-proj-SECRET42" not in message
        assert "SECRET42" not in message

    def test_une_cause_inconnue_reste_prudente(self):
        """Ne pas deviner : dire qu'on ne sait pas, et où regarder."""
        from app.services.email_response_generator import cause_lisible

        message = cause_lisible("erreur interne 0x8007 inconnue au bataillon")

        assert "0x8007" not in message, "le détail brut ne doit pas s'afficher"
        assert len(message) > 20
