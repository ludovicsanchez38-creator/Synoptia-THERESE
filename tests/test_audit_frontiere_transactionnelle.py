"""B-028 — le journal d'audit rendait durable la session de l'appelant.

02/09/2026. `AuditService.log` faisait `await self.session.commit()` sur la
session REÇUE au constructeur (audit.py:86-88, :122-124). Journaliser une
action validait donc, au passage, tout ce que l'appelant avait encore en
attente : un `rollback()` postérieur n'annulait plus rien.

Le couplage est latent — les douze appelants recensés commitent avant de
journaliser — mais `data.py:415` porte déjà un commit explicite ajouté « sinon
le journal n'est pas visible », signe que la frontière gênait.

Fermeture retenue : la SAVEPOINT (`session.begin_nested()`), première des deux
options proposées par la reproduction. Le contrat réel a été MESURÉ, pas
supposé : le pilote pysqlite n'émet `BEGIN` que devant un DML, si bien qu'une
savepoint posée sans transaction ouverte vaut `BEGIN` et son `RELEASE` vaut
`COMMIT`. L'entrée est donc INDÉPENDANTE quand l'appelant n'a rien en attente
(le cas des douze appelants recensés, et donc aucun changement observable pour
eux), et SOLIDAIRE de sa transaction dès qu'il a du travail en cours — le seul
cas où la question se pose. Les deux branches sont verrouillées ci-dessous. Le journal écrit et rend visible SON
entrée, sans jamais décider du sort de la transaction de l'appelant. Le choix
de la session dédiée a été écarté : les deux points d'entrée de session
(`get_session`, `get_session_context`) commitent au démontage, l'entrée est
donc bien durable en production ; ouvrir une SECONDE connexion écrivante face
à un appelant qui tient déjà le verrou SQLite (mono-écrivain, `busy_timeout`
5 s) aurait créé un mode d'échec neuf — le journal cassant la requête qu'il
journalise.
"""

from __future__ import annotations

import pytest
from sqlmodel import select


@pytest.mark.asyncio
async def test_le_journal_ne_rend_pas_durable_le_travail_en_attente(db_session):
    """Le défaut, tel que reproduit : un brouillon jamais commité survit."""
    from app.models import database as db_module
    from app.models.entities import Contact
    from app.services.audit import AuditAction, log_activity

    brouillon = Contact(display_name="BROUILLON B-028 jamais validé")
    db_session.add(brouillon)
    cle = brouillon.id

    await log_activity(
        db_session,
        AuditAction.CONTACT_CREATED,
        resource_type="contact",
        resource_id="une-autre-ressource",
    )

    await db_session.rollback()

    async with db_module.AsyncSessionLocal() as verif:
        trouve = (
            await verif.execute(select(Contact).where(Contact.id == cle))
        ).scalar_one_or_none()

    assert trouve is None, (
        f"le contact brouillon {cle} a été rendu durable par le commit du "
        "journal d'audit, malgré le rollback de l'appelant "
        f"(display_name={trouve.display_name!r})" if trouve else ""
    )


@pytest.mark.asyncio
async def test_l_entree_de_journal_est_visible_de_l_appelant(db_session):
    """Verrou : ne pas fermer la fuite en cessant d'écrire."""
    from app.services.audit import ActivityLog, AuditAction, log_activity

    entree = await log_activity(
        db_session,
        AuditAction.CONTACT_CREATED,
        resource_type="contact",
        resource_id="ressource-visible",
    )

    assert entree.id is not None, "l'entrée rendue n'a pas d'identifiant"
    lues = (
        await db_session.execute(
            select(ActivityLog).where(ActivityLog.resource_id == "ressource-visible")
        )
    ).scalars().all()
    assert len(lues) == 1, f"entrée non lisible dans la session appelante : {lues}"


@pytest.mark.asyncio
async def test_l_entree_de_journal_est_durable_quand_l_appelant_commite(db_session):
    """Verrou : le journal suit le sort de ce qu'il journalise, et le suit vraiment."""
    from app.models import database as db_module
    from app.models.entities import Contact
    from app.services.audit import ActivityLog, AuditAction, log_activity

    contact = Contact(display_name="Contact B-028 validé")
    db_session.add(contact)

    await log_activity(
        db_session,
        AuditAction.CONTACT_CREATED,
        resource_type="contact",
        resource_id=contact.id,
    )
    await db_session.commit()

    async with db_module.AsyncSessionLocal() as verif:
        journaux = (
            await verif.execute(
                select(ActivityLog).where(ActivityLog.resource_id == contact.id)
            )
        ).scalars().all()
        garde = (
            await verif.execute(select(Contact).where(Contact.id == contact.id))
        ).scalar_one_or_none()

    assert len(journaux) == 1, f"entrée de journal perdue au commit : {journaux}"
    assert garde is not None, "le contact validé a disparu"


@pytest.mark.asyncio
async def test_sans_travail_en_attente_l_entree_est_independante(db_session):
    """Le contrat MESURÉ, pas supposé : rien en attente, donc rien à attendre.

    pysqlite n'ouvre une transaction que devant un DML. Sans travail en cours,
    la savepoint vaut `BEGIN` et son `RELEASE` vaut `COMMIT` : l'entrée est
    durable tout de suite, exactement comme avant ce lot. C'est ce qui rend le
    correctif sans effet observable pour les douze appelants actuels — et ce
    qui garde son sens au commit explicite de `data.py:415`.
    """
    from app.models import database as db_module
    from app.services.audit import ActivityLog, AuditAction, log_activity

    await log_activity(
        db_session,
        AuditAction.CONTACT_CREATED,
        resource_type="contact",
        resource_id="rien-en-attente",
    )
    await db_session.rollback()

    async with db_module.AsyncSessionLocal() as verif:
        lues = (
            await verif.execute(
                select(ActivityLog).where(ActivityLog.resource_id == "rien-en-attente")
            )
        ).scalars().all()

    assert len(lues) == 1, (
        "l'entrée de journal n'a pas survécu au rollback d'un appelant qui "
        "n'avait rien en attente : le journal a perdu une trace qu'il gardait "
        "avant ce lot"
    )
