"""Fiches locales : transactions courtes, périmètres serveur, aucun index externe."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import UTC, datetime
from typing import Any

from app.models.database import get_session_context
from app.models.entities import Contact, MemoryCard, MemoryCardUse, Message, Project
from app.services.cloisonnement import cloison_contacts, souvenirs_globaux_visibles
from sqlalchemy import or_, text
from sqlmodel import col, select

KINDS = ('preference', 'fait', 'decision', 'correction')


class RefusMemoire(Exception):
    def __init__(self, message: str, status: int = 422, card_id: str | None = None):
        super().__init__(message)
        self.status = status
        self.card_id = card_id


def normaliser(texte: str) -> str:
    nfkc = unicodedata.normalize('NFKC', texte).casefold()
    return ''.join(c for c in unicodedata.normalize('NFD', nfkc)
                   if unicodedata.category(c) not in ('Mn', 'Cf'))


# Corpus v1 : pluriels non lemmatisés ; liste explicite et stable.
MOTS_VIDES = frozenset(['les', 'des', 'une', 'avec', 'dans', 'pour', 'que', 'qui', 'est', 'sont', 'sur', 'par', 'aux', 'ses', 'ces', 'cette', 'comme', 'plus', 'mais', 'pas', 'mon', 'mes', 'tes', 'vos', 'nous', 'vous', 'elle', 'lui', 'moi', 'toi', 'veut'])


def mots(texte: str) -> set[str]:
    return {m for m in re.findall(r'[^\W_]+', normaliser(texte)) if len(m) >= 3 and m not in MOTS_VIDES}


def presenter(fiche: MemoryCard) -> dict[str, Any]:
    return fiche.model_dump(mode='json', exclude={'search_text', 'dedup_key'})


async def autorisees(session: Any, scope: str, scope_id: str | None,
                     conversation_id: str | None = None) -> list[MemoryCard]:
    if scope not in ('global', 'project', 'all') or (scope == 'project' and not scope_id):
        return []
    if scope == 'project' and not await session.get(Project, scope_id):
        return []
    requete = select(MemoryCard)
    if scope != 'all':
        requete = requete.where(or_(MemoryCard.scope == 'global',
            (MemoryCard.scope == 'project') & (MemoryCard.scope_id == scope_id))
            if scope == 'project' else MemoryCard.scope == 'global')
    contacts = set((await session.execute(cloison_contacts(
        select(Contact.id), scope, scope_id, conversation_id))).scalars().all())
    fiches = (await session.execute(requete)).scalars().all()
    resultat = []
    for f in fiches:
        profil = f.kind in ('preference', 'correction') and not f.contact_id and not f.project_id and f.scope == 'global'
        if f.contact_id and f.contact_id not in contacts:
            continue
        if f.project_id and scope != 'all' and f.project_id != scope_id:
            continue
        if f.scope == 'global' and not profil and not f.contact_id and not f.project_id and not souvenirs_globaux_visibles(scope):
            continue
        resultat.append(f)
    return resultat


async def lire_pour_chat(requete: str, scope: str, scope_id: str | None,
                         conversation_id: str | None = None) -> list[dict[str, Any]]:
    async with get_session_context() as session:
        fiches = [f for f in await autorisees(session, scope, scope_id, conversation_id) if f.state == 'active']
        termes = mots(requete)
        def rang(f: MemoryCard) -> tuple[Any, ...]:
            return (f.kind not in ('preference', 'correction'),
                    not bool(f.project_id and f.project_id == scope_id),
                    -len(termes & mots(f.search_text)), -f.updated_at.timestamp(), f.id)
        return [presenter(f) for f in sorted(fiches, key=rang)
                if f.kind in ('preference', 'correction') or termes & mots(f.search_text)
                or (f.project_id and f.project_id == scope_id)]


async def lister(*, query: str = '', kind: str | None = None, state: str = 'active',
                 offset: int = 0, limit: int = 50) -> dict[str, Any]:
    async with get_session_context() as session:
        requete = select(MemoryCard).where(MemoryCard.state == state)
        if kind:
            requete = requete.where(MemoryCard.kind == kind)
        for terme in mots(query):
            requete = requete.where(col(MemoryCard.search_text).contains(terme, autoescape=True))
        lignes = list((await session.execute(requete.order_by(col(MemoryCard.updated_at).desc(), MemoryCard.id))).scalars().all())
        return {'items': [presenter(f) for f in lignes[offset:offset + limit]], 'total': len(lignes)}


async def _liens(session: Any, f: MemoryCard, automatique: bool, scope: str, scope_id: str | None,
                 conversation_id: str | None) -> None:
    for identifiant in (f.scope_id, f.project_id):
        if identifiant and not await session.get(Project, identifiant):
            raise RefusMemoire('Ce dossier est introuvable.', 404)
        if automatique and identifiant and (scope != 'project' or identifiant != scope_id):
            raise RefusMemoire('Ce dossier est hors du périmètre de cet échange.', 403)
    if f.contact_id:
        requete = select(Contact).where(Contact.id == f.contact_id)
        if automatique:
            requete = cloison_contacts(requete, scope, scope_id, conversation_id)
        if not (await session.execute(requete)).scalars().first():
            raise RefusMemoire('Ce contact est hors du périmètre de cet échange.', 403)


def _cle(f: MemoryCard) -> str:
    return hashlib.sha256(json.dumps([f.scope, f.scope_id or '', f.kind, f.contact_id or '',
                                      f.project_id or '', f.subject], ensure_ascii=False).encode()).hexdigest()


async def ecrire(donnees: dict[str, Any], *, automatique: bool = False,
                 scope: str = 'global', scope_id: str | None = None,
                 conversation_id: str | None = None, message_id: str | None = None,
                 contexte: Any = None) -> dict[str, Any]:
    # Même loquet et même collection de gestes que purge/restauration, CRUD inclus.
    from app.services.memory_tools import _proteger_le_geste

    async def geste() -> str:
        try:
            async with get_session_context() as session:
                await session.execute(text('BEGIN IMMEDIATE'))
                if contexte is not None and contexte.annulation_observee():
                    raise RefusMemoire('Écriture mémoire arrêtée.', 409)
                resultat = await _ecrire(session, donnees, automatique=automatique,
                    scope=scope, scope_id=scope_id, conversation_id=conversation_id, message_id=message_id)
                await session.commit()
                return json.dumps({'card': resultat})
        except RefusMemoire as erreur:
            return json.dumps({'refus': str(erreur), 'status': erreur.status, 'card_id': erreur.card_id})
    resultat = json.loads(await _proteger_le_geste(geste()))
    if 'card' not in resultat:
        raise RefusMemoire(resultat.get('refus') or resultat.get('error') or 'Écriture mémoire indisponible.',
                           resultat.get('status', 409), resultat.get('card_id'))
    return resultat['card']


async def _ecrire(session: Any, donnees: dict[str, Any], *, automatique: bool, scope: str,
                  scope_id: str | None, conversation_id: str | None, message_id: str | None) -> dict[str, Any]:
    existante = await session.get(MemoryCard, donnees['id']) if donnees.get('id') else None
    if donnees.get('id') and not existante:
        raise RefusMemoire('Cette fiche est introuvable.', 404)
    if automatique:
        if scope not in ('global', 'project', 'all'):
            raise RefusMemoire('Périmètre mémoire indisponible.', 403)
        autorisees_chat = await autorisees(session, scope, scope_id, conversation_id)
        if existante and existante.id not in {f.id for f in autorisees_chat}:
            raise RefusMemoire('Cette fiche est hors du périmètre de cet échange.', 403)
        source = await session.get(Message, message_id) if message_id else None
        if not source or source.role != 'user' or source.conversation_id != conversation_id:
            raise RefusMemoire('Une source utilisateur vérifiable est nécessaire.')
    if existante and donnees.get('version') != existante.version:
        raise RefusMemoire('Cette fiche a changé. Recharge-la avant de la modifier.', 409)
    f = existante or MemoryCard(kind=donnees.get('kind', ''), subject='', title='', content='',
                                author='therese' if automatique else 'utilisateur')
    champs = ('kind', 'subject', 'title', 'content', 'reason', 'contact_id', 'project_id')
    if not automatique:
        champs += ('scope', 'scope_id', 'state', 'conversation_id', 'message_id')
    for champ in champs:
        if champ in donnees:
            setattr(f, champ, donnees[champ])
    if automatique:
        f.scope = 'project' if scope == 'project' else 'global'
        f.scope_id = scope_id if scope == 'project' else None
        f.conversation_id, f.message_id = conversation_id, message_id
    f.subject = normaliser(f.subject.strip())
    if f.kind not in KINDS or f.state not in ('active', 'archivee') or f.scope not in ('global', 'project'):
        raise RefusMemoire('Type ou portée de fiche invalide.')
    if (f.scope == 'project') != bool(f.scope_id):
        raise RefusMemoire('Choisis un dossier pour cette portée.')
    if not f.subject or len(f.subject) > 120 or not f.title.strip() or not f.content.strip():
        raise RefusMemoire('Sujet, titre et contenu sont nécessaires.')
    if len(f.title) > 120 or len(f.content) > 1200 or len(f.reason) > 600 or (f.kind == 'decision' and not f.reason.strip()):
        raise RefusMemoire('Cette fiche dépasse les limites ou la décision manque de raison.')
    await _liens(session, f, automatique, scope, scope_id, conversation_id)
    cle = _cle(f)
    doublon = (await session.execute(select(MemoryCard).where(MemoryCard.dedup_key == cle))).scalars().first()
    if doublon and doublon.id != f.id:
        raise RefusMemoire('Une fiche correspond déjà à ce sujet. Ouvre-la pour la modifier.', 409, doublon.id)
    f.dedup_key = cle
    f.last_author = 'therese' if automatique else 'utilisateur'
    f.protected = bool(f.protected or existante or f.kind == 'correction')
    f.search_text = normaliser(f'{f.title} {f.content}')
    f.updated_at = datetime.now(UTC)
    if existante:
        f.version += 1
    session.add(f)
    await session.flush()
    return presenter(f)


async def effacer_liees(session: Any, *, contact_id: str | None = None, project_id: str | None = None) -> int:
    clause = (MemoryCard.contact_id == contact_id) if contact_id else or_(
        MemoryCard.project_id == project_id, (MemoryCard.scope == 'project') & (MemoryCard.scope_id == project_id))
    lignes = (await session.execute(select(MemoryCard).where(clause))).scalars().all()
    for f in lignes:
        await _effacer(session, f)
    return len(lignes)


async def _effacer(session: Any, fiche: MemoryCard) -> None:
    usages = (await session.execute(select(MemoryCardUse).where(MemoryCardUse.card_id == fiche.id))).scalars().all()
    for usage in usages:
        usage.blocked = True
        session.add(usage)
    await session.delete(fiche)


async def effacer(card_id: str, version: int) -> None:
    from app.services.memory_tools import _proteger_le_geste

    async def geste() -> str:
        async with get_session_context() as session:
            await session.execute(text('BEGIN IMMEDIATE'))
            f = await session.get(MemoryCard, card_id)
            if not f:
                return json.dumps({'success': True})
            if f.version != version:
                raise RefusMemoire('Cette fiche a changé. Recharge-la.', 409)
            await _effacer(session, f)
            await session.commit()
            return json.dumps({'success': True})
    resultat = json.loads(await _proteger_le_geste(geste()))
    if not resultat.get('success'):
        raise RefusMemoire(resultat['error'], 409)
