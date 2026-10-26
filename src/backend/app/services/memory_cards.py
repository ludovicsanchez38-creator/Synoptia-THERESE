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
from sqlalchemy import func, or_, text
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import col, select

KINDS = ('preference', 'fait', 'decision', 'correction')


class RefusMemoire(Exception):
    # `detail` n'est lu que par le modèle (résultat de l'outil) : le message
    # affiché reste le même d'un essai à l'autre.
    def __init__(self, message: str, status: int = 422, card_id: str | None = None,
                 detail: str | None = None):
        super().__init__(message)
        self.status = status
        self.card_id = card_id
        self.detail = detail


def _sans_source(texte: str, manquants: set[str], nombres_seuls: set[str],
                 negations_seules: list[tuple[str, str]]) -> str:
    """B-1104 : nomme ce qui manque aux sources, dans la graphie du modèle."""
    vus: dict[str, str] = {}
    for jeton in re.findall(r'[^\W_]+', texte):
        if normaliser(jeton) in manquants and normaliser(jeton) not in vus:
            vus[normaliser(jeton)] = jeton
    graphie = {normaliser(j): j for j in re.findall(r'[^\W_]+', texte)}
    elements = [*vus.values(), *sorted(nombres_seuls - set(vus.values())),
                *(f'{marqueur} {graphie.get(mot, mot)}' for marqueur, mot in negations_seules)]
    liste = ', '.join(f'« {e} »' for e in elements[:8])
    return ('Sans source dans le message ni dans la fiche : ' + liste + ('…' if len(elements) > 8 else '.')
            + ' Retire-les, ou reprends les mots du message ; la raison est facultative.')


def normaliser(texte: str) -> str:
    nfkc = unicodedata.normalize('NFKC', texte).casefold()
    return ''.join(c for c in unicodedata.normalize('NFD', nfkc)
                   if unicodedata.category(c) not in ('Mn', 'Cf'))


# Corpus v1 : pluriels non lemmatisés ; liste explicite et stable.
MOTS_VIDES = frozenset(['les', 'des', 'une', 'avec', 'dans', 'pour', 'que', 'qui', 'est', 'sont', 'sur', 'par', 'aux', 'ses', 'ces', 'cette', 'comme', 'plus', 'mais', 'pas', 'mon', 'mes', 'tes', 'vos', 'nous', 'vous', 'elle', 'lui', 'moi', 'toi', 'veut'])


def mots(texte: str) -> set[str]:
    return {m for m in re.findall(r'[^\W_]+', normaliser(texte)) if m.isdigit() or (len(m) >= 3 and m not in MOTS_VIDES)}


def nombres(*textes: str) -> set[str]:
    # Lus champ par champ (deux champs collés fabriqueraient « 30 500 ») ; un
    # moins qui ne suit ni lettre ni chiffre fait partie du nombre (« -5 » n'autorise
    # pas « 5 ») ; « A-15 », « 10-12 » et les dates gardent leurs nombres positifs.
    motif = r'(?:(?<![^\W_])[-\u2212])?(?:\d{1,3}(?:[ \u00a0\u202f\u2009]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?)'
    return {re.sub(r'[\u00a0\u202f\u2009]', ' ', n).replace('\u2212', '-')
            for texte in textes for n in re.findall(motif, texte or '')}


def negations(texte: str) -> set[tuple[str, str]]:
    # Polarité = (marqueur, mot visé). En fin de proposition, la négation
    # porte sur le mot précédent (« ne répond pas »), jamais la phrase suivante.
    petits_mots = {'de', 'd', 'du', 'des', 'la', 'le', 'les', 'l', 'un', 'une', 'en', 'y'}
    resultat = set()
    for proposition in re.split(r'[.!?;\n]', normaliser(texte)):
        jetons = re.findall(r'[^\W_]+', proposition)
        for index, jeton in enumerate(jetons):
            # B-1142 : comparatifs et ajouts affirmatifs. « ne… plus de »
            # reste négatif ; « de plus en plus » et « le plus » ne le sont pas.
            if jeton == 'plus' and (
                jetons[max(0, index - 1):index] in (['en'], ['le'], ['la'], ['les'])
                or jetons[index:index + 3] == ['plus', 'en', 'plus']
                or (jetons[index + 1:index + 2] == ['de']
                    and not {'ne', 'n'} & set(jetons[:index]))
            ):
                continue
            if jeton in {'pas', 'jamais', 'plus', 'aucun', 'aucune', 'sans', 'ni'}:
                vise = next((mot for mot in jetons[index + 1:] if mot not in petits_mots), None)
                if vise is None:
                    vise = next((mot for mot in reversed(jetons[:index])
                                 if mot not in petits_mots | {'ne', 'n'}), None)
                if vise is not None:
                    resultat.add((jeton, vise))
    return resultat


def date_utc(valeur: datetime) -> datetime:
    # SQLite rend les DateTime sans zone ; leur convention de stockage est UTC.
    return valeur.replace(tzinfo=UTC) if valeur.tzinfo is None else valeur.astimezone(UTC)


def presenter(fiche: MemoryCard) -> dict[str, Any]:
    resultat = fiche.model_dump(mode='json', exclude={'search_text', 'dedup_key'})
    for champ in ('created_at', 'updated_at'):
        resultat[champ] = date_utc(getattr(fiche, champ)).isoformat()
    return resultat


async def autorisees(session: Any, scope: str, scope_id: str | None,
                     conversation_id: str | None = None) -> list[MemoryCard]:
    if scope not in ('global', 'project', 'all') or (scope == 'project' and not scope_id):
        return []
    if scope == 'project' and not await session.get(Project, scope_id):
        return []
    requete = select(MemoryCard)
    if scope != 'all':
        requete = requete.where(or_(col(MemoryCard.scope) == 'global',
            (col(MemoryCard.scope) == 'project') & (col(MemoryCard.scope_id) == scope_id))
            if scope == 'project' else col(MemoryCard.scope) == 'global')
    contacts = set((await session.execute(cloison_contacts(
        select(col(Contact.id)), scope, scope_id, conversation_id))).scalars().all())
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
        def liee(f: MemoryCard) -> bool:
            # Les contacts ont déjà passé la cloison dans autorisees.
            return bool(f.contact_id or (scope == 'project' and scope_id and (
                f.project_id == scope_id or (f.scope == 'project' and f.scope_id == scope_id))))

        def rang(f: MemoryCard) -> tuple[Any, ...]:
            return (f.kind not in ('preference', 'correction'),
                    not liee(f),
                    -len(termes & mots(f.search_text)), -date_utc(f.updated_at).timestamp(), f.id)
        return [presenter(f) for f in sorted(fiches, key=rang)
                if f.kind in ('preference', 'correction') or termes & mots(f.search_text)
                or liee(f)]


async def lister(*, query: str = '', kind: str | None = None, state: str = 'active',
                 offset: int = 0, limit: int = 50, scope: str | None = None,
                 scope_id: str | None = None) -> dict[str, Any]:
    async with get_session_context() as session:
        requete = select(MemoryCard).where(col(MemoryCard.state) == state)
        if kind:
            requete = requete.where(col(MemoryCard.kind) == kind)
        if scope:
            requete = requete.where(col(MemoryCard.scope) == scope)
        if scope_id:
            requete = requete.where(or_(col(MemoryCard.scope_id) == scope_id, col(MemoryCard.project_id) == scope_id))
        for terme in mots(query):
            requete = requete.where(col(MemoryCard.search_text).contains(terme, autoescape=True))
        total = (await session.execute(select(func.count()).select_from(requete.subquery()))).scalar_one()
        lignes = (await session.execute(requete.order_by(col(MemoryCard.updated_at).desc(), col(MemoryCard.id)).offset(offset).limit(limit))).scalars().all()
        return {'items': [presenter(f) for f in lignes], 'total': total}


async def _liens(session: Any, f: MemoryCard, automatique: bool, scope: str, scope_id: str | None,
                 conversation_id: str | None) -> None:
    for identifiant in (f.scope_id, f.project_id):
        if identifiant and not await session.get(Project, identifiant):
            raise RefusMemoire('Ce dossier est introuvable.', 404)
        if automatique and identifiant and (scope != 'project' or identifiant != scope_id):
            raise RefusMemoire('Ce dossier est hors du périmètre de cet échange.', 403)
    if f.contact_id:
        requete = select(Contact).where(col(Contact.id) == f.contact_id)
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
                 contexte: Any = None, generation_attendue: int | None = None) -> dict[str, Any]:
    # Même loquet et même collection de gestes que purge/restauration, CRUD inclus.
    from app.services.memory_tools import _proteger_le_geste, generation_des_donnees
    generation = generation_des_donnees() if generation_attendue is None else generation_attendue

    async def geste() -> str:
        try:
            async with get_session_context() as session:
                await session.execute(text('BEGIN IMMEDIATE'))
                if generation != generation_des_donnees():
                    raise RefusMemoire('Tes données ont changé pendant cette demande. Aucune fiche écrite.', 409)
                if contexte is not None and contexte.annulation_observee():
                    raise RefusMemoire('Écriture mémoire arrêtée.', 409)
                resultat = await _ecrire(session, donnees, automatique=automatique,
                    scope=scope, scope_id=scope_id, conversation_id=conversation_id, message_id=message_id)
                if contexte is not None and contexte.annulation_observee():
                    raise RefusMemoire('Écriture mémoire arrêtée.', 409)
                await session.commit()
                return json.dumps({'card': resultat})
        except SQLAlchemyError:
            return json.dumps({'refus': 'La fiche n’a pas pu être enregistrée. Réessaie.', 'status': 409})
        except RefusMemoire as erreur:
            return json.dumps({'refus': str(erreur), 'status': erreur.status, 'card_id': erreur.card_id,
                               'detail': erreur.detail})
    resultat = json.loads(await _proteger_le_geste(geste()))
    if 'card' not in resultat:
        raise RefusMemoire(resultat.get('refus') or resultat.get('error') or 'Écriture mémoire indisponible.',
                           resultat.get('status', 409), resultat.get('card_id'), resultat.get('detail'))
    return dict(resultat['card'])


async def _ecrire(session: Any, donnees: dict[str, Any], *, automatique: bool, scope: str,
                  scope_id: str | None, conversation_id: str | None, message_id: str | None) -> dict[str, Any]:
    from app.services.memory_card_security import message_refus
    for champ in ("title", "content", "reason", "subject", "kind", "state"):
        if champ in donnees and not isinstance(donnees[champ], str):
            raise RefusMemoire("Les champs de la fiche doivent être du texte.")
    if refus := message_refus([donnees.get(champ, '') for champ in ('title', 'content', 'reason', 'subject')]):
        raise RefusMemoire(refus)
    if automatique:
        source_verifiee = await session.get(Message, message_id) if message_id else None
        if not source_verifiee or source_verifiee.role != 'user' or source_verifiee.conversation_id != conversation_id:
            raise RefusMemoire('Une source utilisateur vérifiable est nécessaire.')
    cle_usage = None
    if automatique and message_id:
        cle_usage = hashlib.sha256((message_id + json.dumps(donnees, sort_keys=True, ensure_ascii=False)).encode()).hexdigest()
        usages_source = (await session.execute(select(MemoryCardUse).where(MemoryCardUse.message_id == message_id))).scalars().all()
        if any(u.blocked for u in usages_source):
            raise RefusMemoire('Ce tour a déjà été traité puis effacé. Une nouvelle demande est nécessaire.', 409)
        usage = await session.get(MemoryCardUse, cle_usage)
        if usage:
            actuelle = await session.get(MemoryCard, usage.card_id)
            if actuelle:
                visibles = await autorisees(session, scope, scope_id, conversation_id)
                if actuelle.id not in {f.id for f in visibles}:
                    raise RefusMemoire('Cette fiche est hors du périmètre de cet échange.', 403)
                return presenter(actuelle) | {'receipt': {'id': usage.card_id, 'version': usage.version, 'operation': usage.operation}}
            raise RefusMemoire('Cette fiche a été effacée.', 409)
    existante = await session.get(MemoryCard, donnees['id']) if donnees.get('id') else None
    if donnees.get('id') and not existante:
        raise RefusMemoire('Cette fiche est introuvable.', 404)
    source_content = ""
    source = None
    if automatique:
        if scope not in ('global', 'project', 'all'):
            raise RefusMemoire('Périmètre mémoire indisponible.', 403)
        autorisees_chat = await autorisees(session, scope, scope_id, conversation_id)
        if existante and existante.id not in {f.id for f in autorisees_chat}:
            raise RefusMemoire('Cette fiche est hors du périmètre de cet échange.', 403)
        source = await session.get(Message, message_id) if message_id else None
        if not source or source.role != 'user' or source.conversation_id != conversation_id:
            raise RefusMemoire('Une source utilisateur vérifiable est nécessaire.')
        source_content = source.content
        if refus := message_refus(source_content):
            raise RefusMemoire(refus)
        # Une correction peut conserver les faits de la fiche autorisée.
        # Aucun mot nouveau hors de ces deux sources n'est accepté.
        provenance = source.content
        if existante:
            provenance += f' {existante.title} {existante.content} {existante.reason}'
        champs_factuels = [str(donnees.get(k, getattr(existante, k, ''))) for k in ('content', 'reason')]
        factuel = ' '.join(champs_factuels)
        # B-1142 : la fin du contenu ne prend jamais la raison pour complément,
        # ni dans la proposition ni dans la fiche précédente.
        anciennes = negations(existante.content) | negations(existante.reason) if existante else set()
        nouvelles: set[tuple[str, str]] = set().union(*(negations(champ) for champ in champs_factuels))
        source_negations = negations(source.content)
        mots_message = set(re.findall(r'[^\W_]+', normaliser(source.content)))
        # Un titre résume librement ; seuls ses nombres doivent avoir une source.
        manquants = mots(factuel) - mots(provenance)
        nombres_seuls = nombres(*(str(donnees.get(k, getattr(existante, k, ''))) for k in ('content', 'reason')),
                                str(donnees.get('title', ''))) - nombres(
            source.content, *((existante.title, existante.content, existante.reason) if existante else ()))
        # B-1142 : citer le mot ne suffit pas à sourcer sa négation. Un retrait
        # exige au contraire une affirmation dans le message. À la création
        # aussi, un fait repris du message ne doit pas perdre sa négation.
        ajouts = nouvelles - anciennes - source_negations
        retraits = {p for p in anciennes - nouvelles if p[1] not in mots_message
                    or any(n[1] == p[1] for n in source_negations)}
        mots_factuels = set(re.findall(r'[^\W_]+', normaliser(factuel)))
        omissions = {p for p in source_negations - nouvelles if p[1] in mots_factuels}
        negations_seules = sorted(ajouts | retraits | omissions)
        if manquants or nombres_seuls or negations_seules:
            raise RefusMemoire('Cette fiche doit reprendre uniquement une information donnée dans ton message.',
                               detail=_sans_source(f"{factuel} {donnees.get('title', '')}", manquants,
                                                  nombres_seuls, negations_seules))
    if existante and donnees.get('version') != existante.version:
        raise RefusMemoire('Cette fiche a changé. Recharge-la avant de la modifier.', 409)
    f = existante or MemoryCard(kind=donnees.get('kind', ''), subject='', title='', content='',
                                author='therese' if automatique else 'utilisateur')
    champs: tuple[str, ...] = ('kind', 'subject', 'title', 'content', 'reason', 'contact_id', 'project_id')
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
    if refus := message_refus([f.title, f.content, f.reason, f.subject]):
        raise RefusMemoire(refus)
    if automatique:
        protegees = (await session.execute(select(MemoryCard).where(col(MemoryCard.protected) == True))).scalars().all()  # noqa: E712
        contacts_projet = {c.id: c.scope_id for c in (await session.execute(select(Contact).where(col(Contact.scope) == 'project'))).scalars().all()}
        for protegee in protegees:
            if _recouvre(f, protegee, contacts_projet):
                raise RefusMemoire('Cette fiche est protégée par ta correction. Tu peux la modifier dans Mémoire.',
                                   409, protegee.id if protegee.id in {c.id for c in autorisees_chat} else None)
        if not existante and f.kind == 'correction':
            # B-1114 : une correction sans id créait une seconde fiche active à
            # côté de celle qu'elle corrige. Renvoi vers l'UNIQUE fiche active
            # visible du même sujet dont contact et dossier recouvrent ceux de
            # la correction (Astra : la fiche d'Alice ne vise pas Bernard).
            cibles = [c for c in autorisees_chat if c.state == 'active' and c.subject == f.subject
                      and _recouvre(f, c, contacts_projet)]
            if len(cibles) == 1:
                cible = cibles[0]
                raise RefusMemoire('Cette correction doit modifier la fiche existante, pas en créer une seconde.', 409,
                                   cible.id, f'Fiche « {cible.title} » : id {cible.id}, version {cible.version}.')
    cle = _cle(f)
    doublon = (await session.execute(select(MemoryCard).where(col(MemoryCard.dedup_key) == cle))).scalars().first()
    if doublon and doublon.id != f.id:
        visible = not automatique or doublon.id in {c.id for c in autorisees_chat}
        raise RefusMemoire('Une fiche correspond déjà à ce sujet. Ouvre-la pour la modifier.', 409,
            doublon.id if visible else None,
            f'Fiche « {doublon.title} » : id {doublon.id}, version {doublon.version}.' if visible else None)
    f.dedup_key = cle
    f.last_author = 'therese' if automatique else 'utilisateur'
    f.protected = bool(f.protected or not automatique or existante or f.kind == 'correction'
        or (automatique and re.search(r'corrig|remplac|en fait|ne refais|plutot|rectifi', normaliser(source_content))))
    f.search_text = normaliser(f'{f.title} {f.content}')
    f.updated_at = datetime.now(UTC)
    if existante:
        f.version += 1
    session.add(f)
    await session.flush()
    resultat = presenter(f)
    if automatique and cle_usage:
        assert source is not None
        operation = 'modification' if existante else 'creation'
        usage = MemoryCardUse(id=cle_usage, message_id=message_id, card_id=f.id,
                              version=f.version, operation=operation)
        session.add(usage)
        receipt = {'id': f.id, 'version': f.version, 'operation': operation}
        extra = json.loads(source.extra_data or '{}')
        recus = extra.setdefault('memory_receipts', [])
        if receipt not in recus:
            recus.append(receipt)
        source.extra_data = json.dumps(extra)
        session.add(source)
        resultat['receipt'] = receipt
    return resultat


async def effacer_liees(session: Any, *, contact_id: str | None = None, project_id: str | None = None) -> int:
    clause = clause_du_contact(contact_id) if contact_id else or_(
        col(MemoryCard.project_id) == project_id, (col(MemoryCard.scope) == 'project') & (col(MemoryCard.scope_id) == project_id))
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


def _recouvre(a: MemoryCard, b: MemoryCard, contacts: dict[str, str | None] | None = None) -> bool:
    """Absence de lien = recouvrement possible ; deux projets distincts = fermés."""
    pa = a.scope_id if a.scope == 'project' else a.project_id
    pb = b.scope_id if b.scope == 'project' else b.project_id
    if contacts:
        pa = pa or contacts.get(a.contact_id or '')
        pb = pb or contacts.get(b.contact_id or '')
    if pa and pb and pa != pb:
        return False
    return not (a.contact_id and b.contact_id and a.contact_id != b.contact_id)


async def rendre_la_main(card_id: str, version: int) -> dict[str, Any]:
    from app.services.memory_tools import _proteger_le_geste

    async def geste() -> str:
        async with get_session_context() as session:
            await session.execute(text('BEGIN IMMEDIATE'))
            f = await session.get(MemoryCard, card_id)
            if not f:
                raise RefusMemoire('Cette fiche est introuvable.', 404)
            if f.version != version:
                raise RefusMemoire('Cette fiche a changé. Recharge-la.', 409)
            f.protected = False
            f.version += 1
            f.last_author = 'utilisateur'
            f.updated_at = datetime.now(UTC)
            session.add(f)
            await session.commit()
            return json.dumps({'card': presenter(f)})
    resultat = json.loads(await _proteger_le_geste(geste()))
    if 'card' not in resultat:
        raise RefusMemoire(resultat['error'], 409)
    return dict(resultat['card'])


def clause_du_contact(contact_id: str) -> Any:
    projets = select(col(Project.id)).where(col(Project.contact_id) == contact_id)
    return or_(col(MemoryCard.contact_id) == contact_id, col(MemoryCard.project_id).in_(projets),
               col(MemoryCard.scope_id).in_(projets))
