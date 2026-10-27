"""Vérifier une clé d'IA au moment où on l'enregistre (B-1348, boucle DQ).

Audit bêta du 27/10/2026 (A2-23) : une clé fausse s'affichait « configurée » et
l'échec n'arrivait qu'au premier message, sans geste de réparation. On demande
au fournisseur la liste de ses modèles, avec la clé : aucune génération, aucune
donnée de l'utilisateur, aucun coût. Les adresses sont celles de la sonde du
Board (`board._SONDES`).

La clé ne sort jamais de cette fonction, et le corps des réponses non plus :
il sert seulement à classer (frontière 0.48).
"""
from __future__ import annotations

import logging
from typing import Any

import httpx
from app.services.board import _SONDES

logger = logging.getLogger(__name__)

ETATS = ("acceptee", "refusee", "non_rattachee", "paiement", "limite", "injoignable",
         "non_verifiable", "incertaine")


def creer_client() -> httpx.AsyncClient:
    """Point d'injection des tests."""
    return httpx.AsyncClient()


def _requete(fournisseur: str, cle: str) -> tuple[str, dict[str, str], dict[str, Any]]:
    url, mode = _SONDES[fournisseur]
    if mode == "bearer":
        return url, {"Authorization": f"Bearer {cle}"}, {}
    if mode == "x-api-key":
        return url, {"x-api-key": cle, "anthropic-version": "2023-06-01"}, {"limit": 1}
    return url, {"x-goog-api-key": cle}, {"pageSize": 1}


async def verifier_cle(fournisseur: str, cle: str | None, client: httpx.AsyncClient) -> str:
    """Rend l'un des ETATS ; ne lève jamais."""
    if not cle or fournisseur not in _SONDES:
        return "non_verifiable"
    url, entetes, parametres = _requete(fournisseur, cle)
    try:
        reponse = await client.get(url, headers=entetes, params=parametres, timeout=8.0)
    except httpx.TransportError as e:
        logger.info("Vérification de clé %s : fournisseur injoignable (%s)", fournisseur, type(e).__name__)
        return "injoignable"
    except Exception as e:  # noqa: BLE001 - une vérification ne casse jamais l'enregistrement
        logger.info("Vérification de clé %s impossible (%s)", fournisseur, type(e).__name__)
        return "injoignable"
    code = reponse.status_code
    corps = reponse.text[:2000] if code >= 400 else ""
    if code == 200:
        return "acceptee"
    if code in (401, 403):
        return "refusee"
    if code == 400 and "not scoped to a workspace" in corps:
        return "non_rattachee"
    if code == 400 and fournisseur == "gemini" and "API_KEY_INVALID" in corps:
        return "refusee"
    if code == 402:
        return "paiement"
    if code == 429:
        return "limite"
    logger.info("Vérification de clé %s : réponse inattendue %s", fournisseur, code)
    return "incertaine"


def message_verification(etat: str, nom: str) -> str:
    """La phrase pour l'écran, avec le geste quand il y en a un."""
    return {
        "acceptee": f"Clé acceptée par {nom}.",
        "refusee": (
            f"{nom} refuse cette clé. Vérifie que tu as copié toute la clé, sans espace, "
            "et qu'elle n'a pas été supprimée ou n'a pas expiré."
        ),
        "non_rattachee": (
            "Ta clé Claude n'est rattachée à aucun espace de travail. Dans la Console "
            "Claude, crée une clé rattachée à un espace (par exemple « Default Workspace »)."
        ),
        "paiement": f"{nom} signale un problème de paiement sur ce compte : vérifie la facturation.",
        "limite": f"Clé acceptée par {nom}, qui limite pour l'instant le nombre de requêtes.",
        "injoignable": (
            f"Impossible de joindre {nom} pour vérifier la clé. Elle est enregistrée et sera "
            "vérifiée à ton premier message."
        ),
        "non_verifiable": "Clé enregistrée. Elle sera vérifiée à ton premier message.",
        "incertaine": (
            f"Clé enregistrée, mais {nom} a répondu de façon inattendue. Elle sera vérifiée "
            "à ton premier message."
        ),
    }.get(etat, "Clé enregistrée.")
