"""
Les routes email d'un compte IMAP ne parlent pas de jeton Google.

Trois constats du persona « robustesse API », deuxième passage (RB2-001,
RB2-002 et RB2-003), tous sur un compte créé par `POST
/api/email/auth/imap-setup`, qui n'a donc jamais eu de jeton OAuth.

**B-172, la branche IMAP absente de cinq routes.** `modify_message`,
`delete_message`, `create_label`, `update_label` et `delete_label` appelaient
`get_gmail_service_for_account` sans regarder `account.provider`, là où leurs
voisines (`get_message`, `send_email`, `create_draft`, `list_labels`) testent
`provider == "imap"`. Résultat : étoiler un message, le supprimer ou créer un
dossier rendait 401 « Access token expired or invalid » - on demandait de
reconnecter un compte Google inexistant.

**B-173, la garde à moitié posée.** La branche IMAP de `GET /api/email/labels`
appelait `list_folders()` sans try/except, quand `_list_messages_imap` encadre
le sien. Un serveur injoignable rendait donc 500 « Une erreur inattendue s'est
produite, reessaie » sur la liste des dossiers, et 502 « Erreur IMAP: [Errno
61] Connection refused » sur la liste des messages - le même incident, nommé
d'un côté, muet de l'autre.

**B-174, une saisie fautive présentée comme une panne du serveur.** Le jeton
de pagination IMAP est un entier (un décalage). `page_token=abc` traversait la
route jusqu'à `int(page_token)` dans le provider, et la `ValueError` ressortait
en 502 « Erreur IMAP: invalid literal for int() with base 10: 'abc' » : le
texte brut d'une exception Python devant l'utilisateur, et un diagnostic qui
l'envoie chez son fournisseur de messagerie. Les bornes voisines de la même
route (`max_results`) rendent, elles, 422.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.email.base_provider import EmailFolderDTO


async def _poser_compte_imap(client) -> str:
    """Le compte est créé par la route que l'utilisateur emprunte vraiment
    (`POST /api/email/auth/imap-setup`), donc sans le moindre jeton OAuth -
    c'est la précondition exacte de RB2-001."""
    reponse = await client.post(
        "/api/email/auth/imap-setup",
        json={
            "email": "rb2@example.invalid",
            "password": "mot-de-passe",
            "imap_host": "127.0.0.1",
            "imap_port": 9,
            "smtp_host": "127.0.0.1",
            "smtp_port": 9,
        },
    )
    assert reponse.status_code == 200, reponse.text
    return reponse.json()["id"]


class TestLesCinqRoutesEmpruntentLaBrancheImap:
    @pytest.mark.asyncio
    async def test_etoiler_un_message(self, client):
        compte = await _poser_compte_imap(client)
        provider = MagicMock()
        provider.modify_message = AsyncMock(
            return_value=MagicMock(id="msg1", labels=["STARRED"])
        )

        with (
            patch("app.routers.email.get_email_provider", return_value=provider),
            patch("app.routers.email.decrypt_value", return_value="secret"),
        ):
            reponse = await client.put(
                f"/api/email/messages/msg1?account_id={compte}",
                json={"add_label_ids": ["STARRED"]},
            )

        assert reponse.status_code == 200, (
            "étoiler un message IMAP passe par Gmail : "
            f"{reponse.status_code} {reponse.text[:200]}"
        )
        assert provider.modify_message.await_count == 1
        assert provider.modify_message.await_args.kwargs["mark_starred"] is True

    @pytest.mark.asyncio
    async def test_marquer_lu_et_non_lu(self, client):
        compte = await _poser_compte_imap(client)
        provider = MagicMock()
        provider.modify_message = AsyncMock(
            return_value=MagicMock(id="msg1", labels=[])
        )

        with (
            patch("app.routers.email.get_email_provider", return_value=provider),
            patch("app.routers.email.decrypt_value", return_value="secret"),
        ):
            reponse = await client.put(
                f"/api/email/messages/msg1?account_id={compte}",
                json={"remove_label_ids": ["UNREAD"]},
            )

        assert reponse.status_code == 200, reponse.text
        assert provider.modify_message.await_args.kwargs["mark_read"] is True

    @pytest.mark.asyncio
    async def test_supprimer_un_message(self, client):
        compte = await _poser_compte_imap(client)
        provider = MagicMock()
        provider.delete_message = AsyncMock(return_value=None)

        with (
            patch("app.routers.email.get_email_provider", return_value=provider),
            patch("app.routers.email.decrypt_value", return_value="secret"),
        ):
            reponse = await client.delete(
                f"/api/email/messages/msg1?account_id={compte}"
            )

        assert reponse.status_code == 200, (
            f"supprimer un message IMAP passe par Gmail : {reponse.text[:200]}"
        )
        assert provider.delete_message.await_count == 1

    @pytest.mark.asyncio
    async def test_creer_un_dossier(self, client):
        compte = await _poser_compte_imap(client)
        provider = MagicMock()
        # `MagicMock(name=...)` nomme le mock au lieu de poser l'attribut :
        # on rend le vrai DTO du provider.
        provider.create_folder = AsyncMock(
            return_value=EmailFolderDTO(
                id="Clients", name="Clients", type="user", path="Clients"
            )
        )

        with (
            patch("app.routers.email.get_email_provider", return_value=provider),
            patch("app.routers.email.decrypt_value", return_value="secret"),
        ):
            reponse = await client.post(
                f"/api/email/labels?account_id={compte}", json={"name": "Clients"}
            )

        assert reponse.status_code == 200, (
            f"créer un dossier IMAP passe par Gmail : {reponse.text[:200]}"
        )
        assert provider.create_folder.await_count == 1
        assert reponse.json()["name"] == "Clients"

    @pytest.mark.asyncio
    async def test_supprimer_un_dossier(self, client):
        compte = await _poser_compte_imap(client)
        provider = MagicMock()
        provider.delete_folder = AsyncMock(return_value=None)

        with (
            patch("app.routers.email.get_email_provider", return_value=provider),
            patch("app.routers.email.decrypt_value", return_value="secret"),
        ):
            reponse = await client.delete(
                f"/api/email/labels/Clients?account_id={compte}"
            )

        assert reponse.status_code == 200, (
            f"supprimer un dossier IMAP passe par Gmail : {reponse.text[:200]}"
        )
        assert provider.delete_folder.await_count == 1

    @pytest.mark.asyncio
    async def test_renommer_un_dossier_refuse_en_nommant_imap(self, client):
        compte = await _poser_compte_imap(client)
        provider = MagicMock()

        with (
            patch("app.routers.email.get_email_provider", return_value=provider),
            patch("app.routers.email.decrypt_value", return_value="secret"),
        ):
            reponse = await client.put(
                f"/api/email/labels/Clients?account_id={compte}",
                json={"name": "Clients 2026"},
            )

        assert reponse.status_code == 501, (
            "renommer un dossier IMAP doit être refusé en le disant, pas "
            f"demander un jeton Google : {reponse.status_code} {reponse.text[:200]}"
        )
        message = reponse.json().get("message", "")
        assert "IMAP" in message, (
            f"le refus ne nomme pas IMAP : {message}"
        )
        assert "token" not in message.lower(), (
            f"le refus parle encore d'un jeton OAuth : {message}"
        )


class TestUnServeurInjoignableEstNomme:
    @pytest.mark.asyncio
    async def test_la_liste_des_dossiers_nomme_la_panne(self, client):
        compte = await _poser_compte_imap(client)
        provider = MagicMock()
        provider.list_folders = AsyncMock(
            side_effect=ConnectionRefusedError(61, "Connection refused")
        )

        with (
            patch("app.routers.email.get_email_provider", return_value=provider),
            patch("app.routers.email.decrypt_value", return_value="secret"),
        ):
            reponse = await client.get(f"/api/email/labels?account_id={compte}")

        assert reponse.status_code == 502, (
            "un serveur IMAP injoignable rend une erreur qui n'apprend rien "
            f"sur la liste des dossiers : {reponse.status_code} {reponse.text[:200]}"
        )
        assert "IMAP" in reponse.json().get("message", ""), reponse.text[:200]

    @pytest.mark.asyncio
    async def test_un_delai_depasse_se_dit_aussi(self, client):
        compte = await _poser_compte_imap(client)
        provider = MagicMock()
        provider.list_folders = AsyncMock(side_effect=TimeoutError("trop long"))

        with (
            patch("app.routers.email.get_email_provider", return_value=provider),
            patch("app.routers.email.decrypt_value", return_value="secret"),
        ):
            reponse = await client.get(f"/api/email/labels?account_id={compte}")

        assert reponse.status_code == 504, (
            f"le délai dépassé n'est pas distingué : {reponse.status_code}"
        )


class TestLeJetonDePaginationEstUneSaisieCliente:
    @pytest.mark.asyncio
    async def test_un_jeton_non_numerique_est_refuse_en_422(self, client):
        """Seul `decrypt_value` est simulé : le VRAI provider IMAP est
        construit, et sa conversion `int(page_token)` est synchrone, avant
        toute connexion. Le test ne touche donc pas le réseau, et le défaut
        est bien celui de la route."""
        compte = await _poser_compte_imap(client)

        with patch("app.routers.email.decrypt_value", return_value="secret"):
            reponse = await client.get(
                f"/api/email/messages?account_id={compte}&page_token=abc&max_results=5"
            )

        assert reponse.status_code == 422, (
            "une saisie cliente fautive est présentée comme une panne du "
            f"serveur de messagerie : {reponse.status_code} {reponse.text[:250]}"
        )
        message = reponse.text
        assert "invalid literal" not in message, (
            f"le texte brut d'une exception Python part au client : {message[:250]}"
        )

    @pytest.mark.asyncio
    async def test_un_jeton_negatif_est_refuse_aussi(self, client):
        compte = await _poser_compte_imap(client)

        with patch("app.routers.email.decrypt_value", return_value="secret"):
            reponse = await client.get(
                f"/api/email/messages?account_id={compte}&page_token=-3"
            )

        assert reponse.status_code == 422, (
            f"un décalage négatif est accepté : {reponse.status_code}"
        )

    @pytest.mark.asyncio
    async def test_un_chiffre_unicode_est_refuse(self, client):
        """`"²".isdigit()` vaut True, `int("²")` lève. Une garde écrite avec
        `isdigit` laisserait donc passer exactement le 502 d'origine."""
        compte = await _poser_compte_imap(client)

        with patch("app.routers.email.decrypt_value", return_value="secret"):
            reponse = await client.get(
                f"/api/email/messages?account_id={compte}&page_token=%C2%B2"
            )

        assert reponse.status_code == 422, (
            f"un chiffre Unicode contourne la garde : {reponse.status_code} "
            f"{reponse.text[:200]}"
        )
        assert "invalid literal" not in reponse.text, reponse.text[:200]

    @pytest.mark.asyncio
    async def test_un_jeton_demesure_est_refuse(self, client):
        """Au-delà de 4300 chiffres, `int()` refuse aussi ; et un décalage
        géant ferait chercher offset + max_results messages au serveur."""
        compte = await _poser_compte_imap(client)

        with patch("app.routers.email.decrypt_value", return_value="secret"):
            reponse = await client.get(
                f"/api/email/messages?account_id={compte}&page_token={'1' * 5000}"
            )

        assert reponse.status_code == 422, (
            f"un jeton de 5000 chiffres passe : {reponse.status_code} "
            f"{reponse.text[:200]}"
        )
        assert "Exceeds the limit" not in reponse.text, reponse.text[:200]

    @pytest.mark.asyncio
    async def test_un_jeton_valide_atteint_le_provider(self, client):
        compte = await _poser_compte_imap(client)
        provider = MagicMock()
        provider.list_messages = AsyncMock(return_value=([], None))

        with (
            patch("app.routers.email.get_email_provider", return_value=provider),
            patch("app.routers.email.decrypt_value", return_value="secret"),
        ):
            reponse = await client.get(
                f"/api/email/messages?account_id={compte}&page_token=50"
            )

        assert reponse.status_code == 200, reponse.text[:250]
        assert provider.list_messages.await_args.kwargs["page_token"] == "50"
