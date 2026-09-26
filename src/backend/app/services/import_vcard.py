"""Import de contacts depuis un fichier vCard (.vcf), commun aux deux portes.

B-1381 (persona Nathalie, cycle 13) : le Pipeline (`/api/crm/import/vcf`) et
Contacts (`/api/memory/contacts/import`) avaient chacun leur copie de l'import,
avec deux règles de doublon (e-mail seul d'un côté, e-mail puis prénom et nom
de l'autre) et deux jeux de messages, dont un sans accents. Les deux routes
délèguent ici : une règle, un bilan.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from app.models.entities import Contact
from app.services.import_service import parse_vcf_avec_ecarts, resume_des_ecarts
from app.services.scoring import calculate_base_score
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

logger = logging.getLogger(__name__)

TAILLE_MAX_OCTETS = 1_000_000
CHAMPS_IMPORTES = ("first_name", "last_name", "company", "phone", "address", "notes")


class ImportRefuse(ValueError):
    """Le fichier est refusé avant toute écriture ; le message va à l'écran."""


def verifier_le_fichier(nom_du_fichier: str | None, contenu: bytes) -> None:
    if not nom_du_fichier or not nom_du_fichier.lower().endswith(".vcf"):
        raise ImportRefuse("Le fichier doit être au format .vcf")
    if len(contenu) > TAILLE_MAX_OCTETS:
        raise ImportRefuse("Fichier trop volumineux (max 1 Mo)")


async def _fiche_existante(session: AsyncSession, carte: dict[str, Any]) -> Contact | None:
    """Même personne : même e-mail, sinon mêmes prénom et nom."""
    if carte.get("email"):
        trouvee = (
            await session.execute(select(Contact).where(Contact.email == carte["email"]).limit(1))
        ).scalar_one_or_none()
        if trouvee:
            return trouvee
    if carte.get("first_name") and carte.get("last_name"):
        return (
            await session.execute(
                select(Contact)
                .where(Contact.first_name == carte["first_name"], Contact.last_name == carte["last_name"])
                .limit(1)
            )
        ).scalar_one_or_none()
    return None


async def importer_des_vcard(
    session: AsyncSession,
    nom_du_fichier: str | None,
    contenu: bytes,
    *,
    mettre_a_jour: bool,
) -> dict[str, Any]:
    verifier_le_fichier(nom_du_fichier, contenu)
    try:
        cartes, ecartees, nb_cartes = parse_vcf_avec_ecarts(contenu)
    except Exception as e:
        logger.error("Erreur parsing VCF: %s", e)
        # B-552 : le texte brut de vobject (anglais, numéro de ligne interne)
        # ne traverse pas jusqu'à l'écran.
        raise ImportRefuse(
            "Fichier VCF invalide : il ne respecte pas le format vCard attendu. "
            "Vérifie qu'il s'agit bien d'un export de contacts."
        ) from e

    bilan: dict[str, Any] = {
        "created": 0, "updated": 0, "deja_a_jour": 0, "skipped": 0,
        "courriels_gardes": 0, "total": nb_cartes, "ecartees": ecartees,
    }
    if not cartes:
        bilan["message"] = (
            f"Aucun contact importé, {resume_des_ecarts(ecartees)}" if ecartees
            else "Aucun contact trouvé dans le fichier"
        )
        return bilan

    a_indexer: list[Contact] = []
    for carte in cartes:
        existante = await _fiche_existante(session, carte)
        if existante is None:
            fiche = Contact(
                first_name=carte.get("first_name", ""),
                last_name=carte.get("last_name", ""),
                company=carte.get("company"),
                email=carte.get("email"),
                phone=carte.get("phone"),
                address=carte.get("address"),
                notes=carte.get("notes"),
            )
            # B-1382 : une fiche neuve reçoit le score de base.
            fiche.score = calculate_base_score(fiche)
            session.add(fiche)
            a_indexer.append(fiche)
            bilan["created"] += 1
        elif not mettre_a_jour:
            bilan["skipped"] += 1
        else:
            changements = {
                champ: carte[champ]
                for champ in CHAMPS_IMPORTES
                if carte.get(champ) and getattr(existante, champ) != carte[champ]
            }
            # B-1658 : une carte retrouvée par le nom apporte son courriel s'il
            # manque à la fiche ; un courriel différent ne l'écrase pas, il se dit.
            courriel = carte.get("email")
            if courriel and not existante.email:
                changements["email"] = courriel
            elif courriel and existante.email.strip().lower() != courriel.strip().lower():
                bilan["courriels_gardes"] += 1
            if not changements:
                # nathalie-04 : une fiche identique n'est pas « mise à jour ».
                bilan["deja_a_jour"] += 1
                continue
            for champ, valeur in changements.items():
                setattr(existante, champ, valeur)
            existante.updated_at = datetime.now(UTC)
            session.add(existante)
            a_indexer.append(existante)
            bilan["updated"] += 1

    await session.commit()
    # B-1180 : chaque fiche créée ou modifiée rejoint l'index sémantique.
    from app.routers.memory import indexer_fiches_en_arriere_plan

    indexer_fiches_en_arriere_plan(a_indexer)
    logger.info(
        "Import vCard : %s créés, %s mis à jour, %s déjà à jour, %s ignorés",
        bilan["created"], bilan["updated"], bilan["deja_a_jour"], bilan["skipped"],
    )

    morceaux = [f"{bilan['created']} contact(s) créé(s)"]
    if bilan["updated"]:
        morceaux.append(f"{bilan['updated']} mis à jour")
    if bilan["deja_a_jour"]:
        morceaux.append(f"{bilan['deja_a_jour']} déjà à jour")
    if bilan["skipped"]:
        morceaux.append(f"{bilan['skipped']} doublon(s) ignoré(s)")
    if bilan["courriels_gardes"]:
        morceaux.append(
            f"{bilan['courriels_gardes']} fiche(s) gardent leur courriel, différent de celui de la carte"
        )
    # B-1380 : l'écarté se dit.
    if ecartees:
        morceaux.append(resume_des_ecarts(ecartees))
    bilan["message"] = ", ".join(morceaux)
    return bilan
