"""
Les routes IMAP ne recopient jamais le texte d'une exception à l'écran.

**B-253.** `docs/rules/RULES-DESIGN.md` §« Frontière d'erreurs » : à la limite
de l'écran (SSE, notification, HTTP, `task.error`), seuls les messages
localisés passent - jamais `str(e)` brut ; le technique va aux logs. Huit
routes de `app/routers/email.py` recopiaient pourtant le texte de l'exception
dans le `detail` du 502 (`detail=f"Erreur IMAP: {e}"`), si bien qu'un chemin
absolu du poste, un identifiant interne ou un fragment de configuration du
serveur de messagerie partaient tels quels dans le corps de la réponse.

La parité demandée par B-173 (« la même erreur nommée des deux côtés ») n'est
pas en cause : elle est tenue par un message localisé identique. C'est le
`{e}` qui viole la règle.

Chaque cas ci-dessous fait lever au provider IMAP une exception portant un
témoin (un chemin absolu et un code interne), puis exige les DEUX moitiés du
contrat : le témoin est absent du corps de la réponse, et il est présent dans
les journaux - un correctif qui se contenterait de tout taire échouerait donc
aussi.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Le témoin ressemble à ce qui fuyait vraiment : un chemin absolu du poste de
# l'utilisateur, plus un jeton interne reconnaissable.
TEMOIN = "/Users/ludo/.therese/imap.log ligne 42 : TEMOIN-TECHNIQUE-0xdeadbeef"


async def _poser_compte_imap(client) -> str:
    """Compte créé par la route que l'utilisateur emprunte vraiment, donc sans
    le moindre jeton OAuth."""
    reponse = await client.post(
        "/api/email/auth/imap-setup",
        json={
            "email": "b253@example.invalid",
            "password": "mot-de-passe",
            "imap_host": "127.0.0.1",
            "imap_port": 9,
            "smtp_host": "127.0.0.1",
            "smtp_port": 9,
        },
    )
    assert reponse.status_code == 200, reponse.text
    return reponse.json()["id"]


# (nom lisible, méthode du provider qui lève, verbe HTTP, gabarit d'URL, corps)
ROUTES_IMAP = [
    ("lister les messages", "list_messages", "get", "/api/email/messages", None),
    ("lire un message", "get_message", "get", "/api/email/messages/msg1", None),
    (
        "enregistrer un brouillon",
        "create_draft",
        "post",
        "/api/email/messages/draft",
        {"to": ["dest@example.invalid"], "subject": "objet", "body": "corps"},
    ),
    (
        "étoiler un message",
        "modify_message",
        "put",
        "/api/email/messages/msg1",
        {"add_label_ids": ["STARRED"], "remove_label_ids": []},
    ),
    ("supprimer un message", "delete_message", "delete", "/api/email/messages/msg1", None),
    ("lister les dossiers", "list_folders", "get", "/api/email/labels", None),
    (
        "créer un dossier",
        "create_folder",
        "post",
        "/api/email/labels",
        {"name": "Archives 2026"},
    ),
    ("supprimer un dossier", "delete_folder", "delete", "/api/email/labels/lbl1", None),
]


@pytest.mark.parametrize(
    "libelle,methode,verbe,gabarit,corps",
    ROUTES_IMAP,
    ids=[cas[1] for cas in ROUTES_IMAP],
)
@pytest.mark.asyncio
async def test_aucune_route_imap_ne_recopie_le_texte_de_l_exception(
    client, caplog, libelle, methode, verbe, gabarit, corps
):
    compte = await _poser_compte_imap(client)
    provider = MagicMock()
    setattr(provider, methode, AsyncMock(side_effect=RuntimeError(TEMOIN)))

    url = f"{gabarit}?account_id={compte}"
    with (
        patch("app.routers.email.get_email_provider", return_value=provider),
        patch("app.routers.email.decrypt_value", return_value="secret"),
        caplog.at_level("ERROR", logger="app.routers.email"),
    ):
        appel = getattr(client, verbe)
        reponse = await (appel(url, json=corps) if corps is not None else appel(url))

    assert reponse.status_code == 502, (
        f"{libelle} : la panne du serveur n'est plus nommée en 502 - "
        f"{reponse.status_code} {reponse.text[:200]}"
    )
    assert TEMOIN not in reponse.text, (
        f"{libelle} : le texte brut de l'exception atteint l'écran - "
        f"{reponse.text[:250]}"
    )
    assert "IMAP" in reponse.json().get("message", ""), (
        f"{libelle} : l'écran n'apprend plus que la panne vient du serveur IMAP - "
        f"{reponse.text[:200]}"
    )
    assert TEMOIN in caplog.text, (
        f"{libelle} : le détail technique a disparu des journaux au lieu d'y "
        "être renvoyé - on ne peut plus diagnostiquer la panne"
    )
