"""Accords cloud locaux : journal append-only, vérifié juste avant l'envoi."""
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any

from app.models.database import get_sync_session
from app.models.entities import CloudConsent
from sqlmodel import Session, col, select

# Import relatif, comme les fournisseurs pour `.base` : mypy nomme ce fichier
# `backend.app.services…` et verrait `app.services.error_handler` comme Any,
# donc une classe mère inconnue pour AccordEnvoiRequis. Même module à l'exécution.
from .error_handler import ErreurPourEcran

_VERROU = RLock()
TEXT_VERSION = "3"


def _journal_restauration() -> Path:
    from app.config import settings
    # Hors des entrées autorisées des archives : une sauvegarde ne le remplace pas.
    if settings.data_dir is None:
        raise ErreurPourEcran('Le dossier de tes données est indisponible. Redémarre THÉRÈSE avant de réessayer.')
    return Path(settings.data_dir) / 'accords-restauration.json'


def _ecrire_journal_restauration(contenu: dict[str, Any]) -> None:
    journal = _journal_restauration()
    temporaire = journal.with_suffix('.tmp')
    with temporaire.open('w', encoding='utf-8') as fichier:
        json.dump(contenu, fichier, ensure_ascii=False)
        fichier.flush()
        os.fsync(fichier.fileno())
    temporaire.replace(journal)


def _restauration_en_attente() -> bool:
    journal = _journal_restauration()
    return journal.exists() and bool(json.loads(journal.read_text(encoding='utf-8'))['pending'])


def preparer_restauration() -> None:
    """Figer les décisions avant de remplacer la base ; conserver un essai interrompu."""
    with _VERROU:
        if not _restauration_en_attente():
            _ecrire_journal_restauration({'pending': True, 'history': historique()})


def terminer_restauration() -> None:
    """Les décisions présentes avant restauration priment sur celles de l'archive."""
    with _VERROU:
        if not _restauration_en_attente():
            return
        precedentes = json.loads(_journal_restauration().read_text(encoding='utf-8'))['history']
        actuelles = {(r['purpose'], r['provider']): r for r in precedentes}
        now = datetime.now(UTC).isoformat()
        with get_sync_session() as session:
            restaurees = session.exec(select(CloudConsent).order_by(col(CloudConsent.id))).all()
            connues = {(r.purpose, r.provider) for r in restaurees}
            ids = {r.event_id for r in restaurees if r.event_id}
            for row in precedentes:
                if row['event_id'] and row['event_id'] in ids:
                    continue
                session.add(CloudConsent(**{k: v for k, v in row.items() if k != 'id'}))
            # Append-only : une décision de restauration clôt chaque couple.
            # Un accord venu uniquement de l'archive exige un nouveau geste.
            for purpose, provider in connues | actuelles.keys():
                row = actuelles.get((purpose, provider))
                session.add(CloudConsent(
                    purpose=purpose, provider=provider, granted=bool(row and row['granted']),
                    text_version=row['text_version'] if row else TEXT_VERSION,
                    occurred_at=row['occurred_at'] if row else now, recorded_at=now,
                    data_categories=row['data_categories'] if row else '[]', source='restauration',
                ))
            session.commit()
        # Une interruption avant cet acquittement bloque les envois et permet la reprise.
        _ecrire_journal_restauration({'pending': False})


def historique() -> list[dict[str, Any]]:
    with get_sync_session() as session:
        return [row.model_dump() for row in session.exec(select(CloudConsent).order_by(col(CloudConsent.id))).all()]


def _dernier(session: Session, purpose: str, provider: str) -> CloudConsent | None:
    return session.exec(select(CloudConsent).where(
        CloudConsent.purpose == purpose, CloudConsent.provider == provider.strip().lower()
    ).order_by(col(CloudConsent.id).desc())).first()


def accord_valide(purpose: str, provider: str, categories: tuple[str, ...] = ()) -> bool:
    try:
        if _restauration_en_attente():
            return False
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
        decision = CloudConsent(event_id=event_id, purpose=purpose, provider=provider.strip().lower(),
            granted=granted, text_version=text_version, occurred_at=occurred_at or now, recorded_at=now,
            data_categories=json.dumps(categories, ensure_ascii=False), source="interface")
        if _restauration_en_attente():
            if granted:
                exiger_accord(purpose, provider)  # refus expliqué tant que la reprise n'est pas terminée
            journal = json.loads(_journal_restauration().read_text(encoding='utf-8'))
            if not event_id or not any(r['event_id'] == event_id for r in journal['history']):
                journal['history'].append(decision.model_dump())
                _ecrire_journal_restauration(journal)
        if event_id and session.exec(select(CloudConsent).where(CloudConsent.event_id == event_id)).first():
            return
        session.add(decision)
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


def retirer_tous_accords() -> None:
    """L'effacement couvre aussi les décisions d'une restauration interrompue."""
    with _VERROU:
        decisions = historique()
        if _restauration_en_attente():
            decisions += json.loads(_journal_restauration().read_text(encoding='utf-8'))['history']
        for purpose, provider in {(r['purpose'], r['provider']) for r in decisions}:
            enregistrer_accord(purpose, provider, False, TEXT_VERSION, [])


def accords_courants() -> list[dict[str, Any]]:
    if _restauration_en_attente():
        return []
    latest = {(r['purpose'], r['provider']): r for r in historique()}
    return [dict(purpose=r['purpose'], provider=r['provider'], timestamp=r['occurred_at'],
                 dataCategories=json.loads(r['data_categories']), textVersion=r['text_version'])
            for r in latest.values() if r['granted']]


class AccordEnvoiRequis(ErreurPourEcran):
    """Un refus d'envoi ne doit jamais être masqué par un repli fonctionnel."""


def exiger_accord(purpose: str, provider: str) -> None:
    try:
        en_attente = _restauration_en_attente()
    except Exception:
        en_attente = True
    if en_attente:
        raise AccordEnvoiRequis(
            "Les accords n’ont pas pu être rétablis après la restauration. Aucun envoi cloud n’est autorisé. "
            "Relance la restauration de ta sauvegarde pour reprendre cette étape."
        )
    if not accord_valide(purpose, provider):
        raise AccordEnvoiRequis(
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
    if (getattr(context, 'contient_documents', False) is True
            or any(getattr(m, 'contient_documents', None) is not False or getattr(m, 'images', None)
                   for m in [*(getattr(context, 'messages', None) or []),
                             *(getattr(context, 'memory_original_messages', None) or [])])):
        exiger_accord('documents', destination)
    demande = getattr(context, 'memory_request', None)
    if isinstance(demande, dict) and getattr(context, 'memory_used', None):
        if not accord_valide(demande['purpose'], destination, ('memory_cards_r2_v1',)):
            from app.services.memory_card_context import AccordFichesRequis
            raise AccordFichesRequis(destination, demande['purpose'])
