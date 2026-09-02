"""Un secret ne doit pas traverser la trace d'une exception.

Le filtre de journalisation masque `record.msg` et `record.args`. La trace
d'exception, elle, est formatée séparément et échappait au masquage.

Or les messages d'erreur des fournisseurs contiennent parfois la requête, donc
l'en-tête d'autorisation, donc la clé. Sur un poste de bureau, ces journaux sont
lus, copiés et collés dans un rapport de bug — c'est même exactement ce que font
nos testeurs quand ils rapportent une panne.
"""
import logging

import pytest


class _EvenementFini:
    """Double minimal de StreamEvent : clôt la continuation du fournisseur."""

    type = "done"
    content = ""
    tool_call = None
    stop_reason = "end_turn"
    assistant_content_brut = None


def _journaliser_avec_secret(formatter: logging.Formatter) -> str:
    """Provoque une vraie exception porteuse d'un secret, et la formate."""
    from app.core.logging_config import SecretMaskingFilter

    try:
        raise RuntimeError("401 Unauthorized: api key sk-proj-SECRET42 rejected")
    except RuntimeError:
        import sys

        record = logging.LogRecord(
            name="essai",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="Échec de génération",
            args=(),
            exc_info=sys.exc_info(),
        )
        SecretMaskingFilter().filter(record)
        return formatter.format(record)


class TestUnSecretNeTraversePasLesJournaux:
    def test_le_format_json_masque_la_trace(self):
        from app.core.logging_config import JSONFormatter

        sortie = _journaliser_avec_secret(JSONFormatter())

        assert "sk-proj-SECRET42" not in sortie, (
            "la clé d'API traverse la trace d'exception : elle finira dans un "
            "rapport de bug collé sur Discord"
        )

    def test_le_format_console_masque_aussi(self):
        """Le testeur copie la sortie du sidecar, pas le fichier de journal."""
        from app.core.logging_config import ReadableFormatter

        sortie = _journaliser_avec_secret(ReadableFormatter())

        assert "sk-proj-SECRET42" not in sortie

    def test_la_trace_reste_exploitable(self):
        """Masquer ne doit pas rendre le diagnostic impossible."""
        from app.core.logging_config import JSONFormatter

        sortie = _journaliser_avec_secret(JSONFormatter())

        assert "RuntimeError" in sortie, "le type d'erreur a disparu"
        assert "401" in sortie, "le code d'erreur a disparu, on ne diagnostique plus rien"


class TestLeMasquageNeRendPasLesJournauxIllisibles:
    """Régression introduite puis corrigée le 24/08/2026.

    Le motif des clés brutes n'avait pas de frontière gauche : il attrapait le
    « sk- » au MILIEU des mots. « task-scheduler started » devenait
    « ta***MASKED*** started », « disk-space-warning » disparaissait.

    Un journal illisible ne protège personne : il empêche seulement de
    diagnostiquer. C'est le contraire du but recherché.
    """

    @pytest.mark.parametrize(
        "texte_ordinaire",
        [
            "task-scheduler started",
            "disk-space-warning",
            "password validation failed",
            "mask-space test",
            "ask-user-confirmation",
            "risk-assessment done",
        ],
    )
    def test_un_texte_ordinaire_reste_intact(self, texte_ordinaire):
        from app.core.logging_config import _mask_secrets

        assert _mask_secrets(texte_ordinaire) == texte_ordinaire, (
            "du texte ordinaire est masqué : les journaux deviennent illisibles "
            "et le diagnostic impossible"
        )

    @pytest.mark.parametrize(
        "secret",
        [
            "sk-proj-abcdefghijklmnop",
            "sk-ant-api03-abcdefghijkl",
            "xai-abcdefghijklmnopqrstuvwx",
            "AIzaSyAbcdefghijklmnopqrstuvwxyz12",
            "gsk_abcdefghijklmnopqrst",
            "ya29.a0ARrdaM-abcdefghijklmnopqrstuvwxyz012345",
        ],
    )
    def test_une_vraie_cle_est_toujours_masquee(self, secret):
        """Le verrou inverse : ne pas devenir si prudent qu'on ne masque plus."""
        from app.core.logging_config import _mask_secrets

        assert _mask_secrets(secret) == "***MASKED***"


class TestLeJournalNePortePasCeQueLudoEcrit:
    """Passe 4 : les arguments d'outils partaient au journal AVANT la
    carte. Annuler ne retirait pas la ligne. _mask_secrets connaissait
    sk-/xai-/AIza/Bearer, pas ya29. ni un corps de mail."""

    def test_un_jeton_google_est_masque(self):
        from app.core.logging_config import _mask_secrets

        jeton = "ya29.a0ARrdaM-abcdefghijklmnopqrstuvwxyz012345"
        assert jeton not in _mask_secrets(f"Authorization: {jeton}")
        assert "***MASKED***" in _mask_secrets(jeton)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "outil, arguments, canaris",
        [
            # Chemin « outil sensible mis en attente » (chat.py, log de la carte).
            (
                "send_email",
                {
                    "to": "marie.dupont@exemple.fr",
                    "subject": "Objet CANARI-OBJET du dossier",
                    "body": "Corps CANARI-CORPS : le mot de passe IMAP de Marie",
                },
                ["marie.dupont@exemple.fr", "CANARI-OBJET", "CANARI-CORPS"],
            ),
            # Chemin « outil exécuté » (log Executing tool), classé lecture seule
            # donc sans carte : c'est l'autre site, et il fuyait de la même façon.
            (
                "search_emails",
                {"query": "CANARI-REQUETE dossier Martin", "limit": 5},
                ["CANARI-REQUETE"],
            ),
        ],
    )
    async def test_la_boucle_d_outils_ne_journalise_pas_la_valeur_des_arguments(
        self, monkeypatch, caplog, outil, arguments, canaris
    ):
        """B-013 : garde de COMPORTEMENT, pas de texte source.

        L'ancienne version lisait `chat.py` et exigeait l'absence de deux
        chaînes littérales. Un code qui fuit réellement sous une autre forme
        (`logger.info("... %s", tc.arguments)`, f-string, repr) passait, et un
        fichier VIDE passait aussi. On exécute donc la vraie boucle d'outils
        avec des valeurs témoins et on exige leur absence du journal, quelle
        que soit la forme d'écriture du log.

        Le NOM de l'outil doit rester : masquer ne doit pas rendre le
        diagnostic impossible.
        """
        import logging
        from unittest.mock import MagicMock

        import app.routers.chat as chat_mod
        from app.routers.chat import _execute_tools_and_continue
        from app.services.llm import ToolCall

        async def _execute_muet(*args, **kwargs):
            return "OK"

        monkeypatch.setattr(chat_mod, "execute_workspace_tool", _execute_muet)

        class _LLMMuet:
            async def continue_with_tool_results(
                self, context, assistant_content, tool_calls, tool_results, tools,
                prior_turns=None, assistant_content_brut=None,
            ):
                yield _EvenementFini()

        tc = ToolCall(id="t-canari", name=outil, arguments=arguments)

        with caplog.at_level(logging.DEBUG):
            _ = [
                chunk
                async for chunk in _execute_tools_and_continue(
                    _LLMMuet(), None, None, "", [tc], [], "conv-canari", 3,
                    session=MagicMock(),
                )
            ]

        # Ni le message formaté, ni les arguments bruts du LogRecord.
        journal = "\n".join(
            f"{record.getMessage()} || {record.args!r}" for record in caplog.records
        )
        for canari in canaris:
            assert canari not in journal, (
                f"la valeur d'argument « {canari} » atterrit dans le journal : "
                "un rapport de bug collé sur Discord l'emporte"
            )
        assert outil in journal, (
            "le nom de l'outil a disparu du journal : plus rien de diagnosticable"
        )
