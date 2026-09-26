"""B-1641 : l'anonymisation automatique exige un préavis donné au moins
30 jours avant. Les tests qui visent l'anonymisation elle-même posent ce
préavis ancien pour chaque fiche de la base (pas un test)."""

from datetime import UTC, datetime, timedelta

from sqlmodel import select


async def preavis_ancien_pour_tous(session) -> None:
    from app.models.entities import Contact, Notification

    for (identifiant,) in (await session.execute(select(Contact.id))).all():
        session.add(Notification(
            title="Purge RGPD programmée", message="préavis donné", type="warning", source="rgpd_purge",
            action_url=f"/crm/contacts/{identifiant}",
            created_at=datetime.now(UTC) - timedelta(days=31),
        ))
    await session.commit()
