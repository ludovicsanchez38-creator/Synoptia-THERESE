"""BUG-162 — « Connexion Google expirée » qui disparaît au redémarrage suivant.

Un testeur voyait un message d'erreur Google sur son calendrier. Le lendemain,
sans rien faire, il avait disparu.

Un des producteurs est une course d'horloge. Le jeton d'accès Google vit 3600
secondes, et le rafraîchissement ne se déclenchait qu'à `maintenant >= expiry`,
soit une marge nulle. Un jeton considéré comme encore valide localement peut
donc être déjà refusé par Google : le temps du trajet réseau suffit, et la
moindre dérive d'horloge de la machine élargit la fenêtre.

L'appel repart alors en 401, que l'interface traduit en « reconnecte ton
compte » — alors que le compte est parfaitement valide et que le simple fait de
relancer plus tard résout tout.

Une marge d'anticipation supprime la course et absorbe une dérive raisonnable.
"""
from datetime import UTC, datetime, timedelta

import pytest


class TestUnJetonPresqueExpireEstRafraichiAvantUsage:
    @pytest.mark.asyncio
    async def test_un_jeton_expirant_dans_trente_secondes_est_rafraichi(
        self, monkeypatch
    ):
        """Trente secondes, c'est moins que le trajet aller-retour vers Google."""
        from app.models.entities import EmailAccount
        from app.routers import email as email_router

        compte = EmailAccount(
            email="test@exemple.fr",
            provider="gmail",
            access_token="jeton-presque-expire",
            refresh_token="jeton-de-rafraichissement",
            token_expiry=datetime.now(UTC).replace(tzinfo=None) + timedelta(seconds=30),
        )

        compte.client_id = "identifiant-client"
        compte.client_secret = "secret-client"

        rafraichissements: list[str] = []

        class FauxServiceOAuth:
            async def refresh_access_token(self, *_args, **_kwargs):
                rafraichissements.append("appele")
                return {"access_token": "jeton-tout-neuf", "expires_in": 3600}

        monkeypatch.setattr(email_router, "get_oauth_service", FauxServiceOAuth)

        session_factice = _SessionFactice()
        await email_router.ensure_valid_access_token(compte, session_factice)

        assert rafraichissements, (
            "un jeton qui expire dans 30 secondes part tel quel : Google peut "
            "le refuser en route, et l'utilisateur lit « reconnecte ton compte » "
            "alors que son compte est valide"
        )

    @pytest.mark.asyncio
    async def test_un_jeton_encore_confortable_n_est_pas_rafraichi(self, monkeypatch):
        """Verrou : ne pas rafraîchir à chaque appel, ce serait du gaspillage."""
        from app.models.entities import EmailAccount
        from app.routers import email as email_router

        compte = EmailAccount(
            email="test@exemple.fr",
            provider="gmail",
            access_token="jeton-valide",
            refresh_token="jeton-de-rafraichissement",
            token_expiry=datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=30),
        )

        compte.client_id = "identifiant-client"
        compte.client_secret = "secret-client"

        rafraichissements: list[str] = []

        class FauxServiceOAuth:
            async def refresh_access_token(self, *_args, **_kwargs):
                rafraichissements.append("appele")
                return {"access_token": "jeton-tout-neuf", "expires_in": 3600}

        monkeypatch.setattr(email_router, "get_oauth_service", FauxServiceOAuth)

        await email_router.ensure_valid_access_token(compte, _SessionFactice())

        assert not rafraichissements


class _SessionFactice:
    """Session minimale : seuls commit et refresh sont exercés par cette route."""

    async def commit(self) -> None:
        return None

    async def refresh(self, _objet) -> None:
        return None

    def add(self, _objet) -> None:
        return None
