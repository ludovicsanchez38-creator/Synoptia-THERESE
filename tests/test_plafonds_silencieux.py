"""Plafonds atteints en silence — lot F (revue 30/08/2026, grok-lechelle).

Un plafond sans le dire est un faux résultat : l'utilisateur croit tout voir.
"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Conversation, Message


class TestF1ConversationMessagesPlusRecents:
    """GET .../messages prenait les plus anciens : l'écran montrait le début,
    le modèle voyait la fin (BUG-031, 50 derniers). Au 151e, plus aucun
    recouvrement. Reouvrir le fil écrasait le store sur cette fenêtre morte.
    """

    @pytest.mark.asyncio
    async def test_limite_renvoie_les_plus_recents_dans_l_ordre_chrono(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        conv = Conversation(title="Fil long")
        db_session.add(conv)
        await db_session.commit()
        base = datetime(2026, 8, 30, 10, 0, tzinfo=UTC)
        for i in range(5):
            db_session.add(
                Message(
                    conversation_id=conv.id,
                    role="user" if i % 2 == 0 else "assistant",
                    content=f"msg-{i}",
                    created_at=base + timedelta(seconds=i),
                )
            )
        await db_session.commit()

        resp = await client.get(
            f"/api/chat/conversations/{conv.id}/messages",
            params={"limit": 3},
        )
        assert resp.status_code == 200
        contents = [m["content"] for m in resp.json()]
        # Les 3 plus récents, affichés du plus ancien au plus récent de la
        # fenêtre — pas le début du fil.
        assert contents == ["msg-2", "msg-3", "msg-4"], contents


class TestF5ImapTransmetLeJetonDePage:
    """IMAP ignorait page_token : coller le jeton à la main restait page 1."""

    def _account(self):
        from types import SimpleNamespace

        return SimpleNamespace(
            email="t@example.org",
            imap_password="enc",
            imap_host="imap.example.org",
            imap_port=993,
            smtp_host="smtp.example.org",
            smtp_port=465,
            smtp_use_tls=True,
            provider="imap",
        )

    @pytest.mark.asyncio
    async def test_le_jeton_arrive_au_provider(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from unittest.mock import AsyncMock, MagicMock

        from app.routers import email as email_router

        fake = MagicMock()
        fake.resolve_folder_for_label = AsyncMock(return_value="INBOX")
        fake.list_messages = AsyncMock(return_value=([], "50"))
        monkeypatch.setattr(email_router, "get_email_provider", lambda **kw: fake)
        monkeypatch.setattr(email_router, "decrypt_value", lambda v: "pw")

        await email_router._list_messages_imap(
            self._account(), 50, None, None, page_token="50"
        )

        assert fake.list_messages.await_args.kwargs.get("page_token") == "50"
