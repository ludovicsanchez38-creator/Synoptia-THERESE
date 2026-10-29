"""Accords cloud locaux : journal append-only, vérifié juste avant l'envoi."""
import json
from datetime import UTC, datetime
from threading import RLock
from typing import Any

from app.models.database import get_sync_session
from app.models.entities import CloudConsent
from app.services.error_handler import ErreurPourEcran
from sqlmodel import select

_VERROU = RLock()
TEXT_VERSION = "3"


def historique() -> list[dict[str, Any]]:
    with get_sync_session() as session:
        return [row.model_dump() for row in session.exec(select(CloudConsent).order_by(CloudConsent.id)).all()]


def _dernier(session, purpose: str, provider: str):
    return session.exec(select(CloudConsent).where(
        CloudConsent.purpose == purpose, CloudConsent.provider == provider.strip().lower()
    ).order_by(CloudConsent.id.desc())).first()


def accord_valide(purpose: str, provider: str, categories: tuple[str, ...] = ()) -> bool:
    try:
        with get_sync_session() as session:
            row = _dernier(session, purpose, provider)
            return bool(row and row.granted and set(categories) <= set(json.loads(row.data_categories)))
    except Exception:
        # Une base inaccessible ne vaut jamais accord.
        return False


def enregistrer_accord(purpose: str, provider: str, granted: bool, text_version: str,
                       categories: list[str], event_id: str | None = None,
                       occurred_at: str | None = None) -> None:
    now = datetime.now(UTC).isoformat()
    with _VERROU, get_sync_session() as session:
        if event_id and session.exec(select(CloudConsent).where(CloudConsent.event_id == event_id)).first():
            return
        session.add(CloudConsent(event_id=event_id, purpose=purpose, provider=provider.strip().lower(),
            granted=granted, text_version=text_version, occurred_at=occurred_at or now, recorded_at=now,
            data_categories=json.dumps(categories, ensure_ascii=False), source="interface"))
        session.commit()


def importer_accords(grants: list[dict[str, Any]]) -> None:
    """Reprise v2 sans écraser une décision du moteur, notamment un retrait."""
    with _VERROU, get_sync_session() as session:
        for grant in grants:
            purpose, provider = grant['purpose'], grant['provider'].strip().lower()
            if _dernier(session, purpose, provider) is not None:
                continue
            session.add(CloudConsent(purpose=purpose, provider=provider, granted=True,
                text_version="2", occurred_at=grant['timestamp'],
                recorded_at=datetime.now(UTC).isoformat(), source="reprise-interface-v2",
                data_categories=json.dumps(grant.get('dataCategories') or [], ensure_ascii=False)))
            session.flush()
        session.commit()


def accords_courants() -> list[dict[str, Any]]:
    latest = {(r['purpose'], r['provider']): r for r in historique()}
    return [dict(purpose=r['purpose'], provider=r['provider'], timestamp=r['occurred_at'],
                 dataCategories=json.loads(r['data_categories']), textVersion=r['text_version'])
            for r in latest.values() if r['granted']]


def exiger_accord(purpose: str, provider: str) -> None:
    if not accord_valide(purpose, provider):
        raise ErreurPourEcran(
            f"Ton accord « {purpose} » pour {provider} est nécessaire. "
            "Autorise cet envoi dans THÉRÈSE avant de réessayer."
        )


def verifier_envoi_llm(config: Any, context: Any) -> None:
    from app.services.memory_card_context import destination_cloud

    destination = destination_cloud(config)
    if destination is None:
        return
    if getattr(context, 'accord_board', False) is True:
        exiger_accord('llm', 'board')
        return
    # L'écran documents décrit aussi le message et le contexte accompagnant.
    if not (accord_valide('llm', destination) or accord_valide('documents', destination)):
        exiger_accord('llm', destination)
    if getattr(context, 'contient_documents', False) is True:
        exiger_accord('documents', destination)
