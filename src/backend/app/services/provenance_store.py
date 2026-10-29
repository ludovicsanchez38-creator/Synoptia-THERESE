"""Lien local entre une génération et ses métadonnées techniques."""

import json
from typing import Any

from app.models.entities import AIGeneration
from fastapi import HTTPException
from sqlmodel import col, select


def ajouter_generation(
    session: Any, kind: str, owner_id: str, champs: dict[str, str], generation_id: str | None = None
) -> str:
    provider, model = champs["fournisseur_modele"].split("/", 1)
    record = AIGeneration(
        kind=kind,
        owner_id=owner_id,
        provider=provider,
        model=model,
        created_at=champs["date"],
        provenance=json.dumps(champs, ensure_ascii=False),
    )
    if generation_id:
        record.id = generation_id
    session.add(record)
    return record.id


async def provenance_mail(
    session: Any, generation_id: str | None, account_id: str
) -> dict[str, str] | None:
    if not generation_id:
        return None
    record = await session.get(AIGeneration, generation_id)
    if not record or record.kind != "email" or record.owner_id != account_id:
        raise HTTPException(422, "La provenance de ce brouillon IA est introuvable pour ce compte.")
    return json.loads(record.provenance)


async def provenance_sections(session: Any, section_ids: list[str]) -> dict[str, str] | None:
    records = (
        (
            await session.execute(
                select(AIGeneration)
                .where(AIGeneration.kind == "section", col(AIGeneration.owner_id).in_(section_ids))
                .order_by(col(AIGeneration.created_at))
            )
        )
        .scalars()
        .all()
    )
    if not records:
        return None
    champs = json.loads(records[-1].provenance)
    champs["fournisseur_modele"] = ",".join(sorted({f"{r.provider}/{r.model}" for r in records}))
    return champs
