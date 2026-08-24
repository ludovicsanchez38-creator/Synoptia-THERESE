"""Un secret ne doit pas traverser la trace d'une exception.

Le filtre de journalisation masque `record.msg` et `record.args`. La trace
d'exception, elle, est formatée séparément et échappait au masquage.

Or les messages d'erreur des fournisseurs contiennent parfois la requête, donc
l'en-tête d'autorisation, donc la clé. Sur un poste de bureau, ces journaux sont
lus, copiés et collés dans un rapport de bug — c'est même exactement ce que font
nos testeurs quand ils rapportent une panne.
"""
import logging


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
