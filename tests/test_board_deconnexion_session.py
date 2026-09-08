"""
B-653 (ronde B, D3) : quand le client coupe le flux SSE d'une délibération
(« Annuler et fermer »), la session SQLAlchemy du générateur se fermait DANS
le scope annulé par BaseHTTPMiddleware : la fermeture de la connexion aiosqlite
recevait un CancelledError, la connexion restait hors du pool, et une requête
ultérieure échouait en « no active connection ». Les ressources de la session
sont désormais remises à la clôture détachée, exécutée hors du scope annulé.
"""
import asyncio
from unittest.mock import AsyncMock

from app.routers.board import _clore_apres_deconnexion


class _ServiceSansPersistance:
    _persistance_en_cours = None


async def _porteur_termine() -> None:
    return None


async def test_la_cloture_detachee_libere_la_session_apres_le_porteur():
    porteur = asyncio.create_task(_porteur_termine())
    ressources = AsyncMock()
    ordre: list[str] = []
    ressources.aclose.side_effect = lambda: ordre.append("aclose")

    async def decision_sauvee() -> bool:
        ordre.append("decision")
        return False

    await _clore_apres_deconnexion(
        porteur, _ServiceSansPersistance(), None, decision_sauvee, ressources
    )

    ressources.aclose.assert_awaited_once()
    assert ordre == ["aclose"], "sans handle, rien à trancher, mais la session est rendue"


async def test_la_session_est_rendue_meme_si_la_cloture_du_traitement_echoue():
    porteur = asyncio.create_task(_porteur_termine())
    ressources = AsyncMock()

    class _HandleCasse:
        id = "t-1"

        async def terminer(self, *_a, **_k):
            raise RuntimeError("base injoignable")

    async def decision_sauvee() -> bool:
        raise RuntimeError("base injoignable")

    await _clore_apres_deconnexion(
        porteur, _ServiceSansPersistance(), _HandleCasse(), decision_sauvee, ressources
    )
    ressources.aclose.assert_awaited_once()


async def test_une_fermeture_qui_echoue_ne_fait_pas_tomber_la_cloture():
    porteur = asyncio.create_task(_porteur_termine())
    ressources = AsyncMock()
    ressources.aclose.side_effect = RuntimeError("connexion déjà morte")

    async def decision_sauvee() -> bool:
        return False

    await _clore_apres_deconnexion(
        porteur, _ServiceSansPersistance(), None, decision_sauvee, ressources
    )
    ressources.aclose.assert_awaited_once()
