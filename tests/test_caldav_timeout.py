"""US-008 (RES5-a) : le client CalDAV doit avoir un timeout.

Sans timeout, un serveur CalDAV distant qui ne répond pas fait pendre
l'opération indéfiniment (le chemin local valide déjà ses fuseaux, mais le
CalDAV distant n'avait aucune borne)."""
from app.services.calendar.caldav_provider import CalDAVProvider


def test_caldav_client_a_un_timeout():
    provider = CalDAVProvider(
        url="https://caldav.example.com", username="u", password="p"
    )
    client = provider._get_client()
    assert getattr(client, "timeout", None) is not None
    assert client.timeout > 0
