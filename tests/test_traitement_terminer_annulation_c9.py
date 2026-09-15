"""B-811 (cycle 9) : « Arrêter la réponse » annule la tâche du flux. Sous
BaseHTTPMiddleware (anyio), l'annulation est à niveau : chaque await de la tâche
relève CancelledError. `terminer()` appelé dans le `finally` était donc
interrompu et l'état terminal jamais écrit : le traitement restait
« cancel_requested », badge « 1 en cours » pendant 28 minutes."""
from __future__ import annotations

import asyncio

import pytest
from app.services import traitements
from app.services.traitements import TraitementHandle


async def _annuler_a_niveau(tache: asyncio.Task) -> None:
    """Rejoue l'annulation à chaque tour de boucle, comme un cancel scope anyio."""
    while not tache.done():
        tache.cancel()
        await asyncio.sleep(0.001)


def _poser_une_ecriture_lente(monkeypatch, etats: list[str], ecrit: asyncio.Event) -> None:
    async def faux_ecrire(self, etat, *, error):
        await asyncio.sleep(0.03)
        etats.append(etat)
        ecrit.set()

    monkeypatch.setattr(TraitementHandle, "_ecrire_etat_terminal", faux_ecrire)


async def _flux_annule(handle: TraitementHandle) -> None:
    try:
        await asyncio.sleep(10)
    finally:
        await handle.terminer("cancelled")


@pytest.mark.asyncio
async def test_l_etat_terminal_s_ecrit_sous_une_annulation_a_niveau(monkeypatch) -> None:
    ecrit = asyncio.Event()
    etats: list[str] = []
    _poser_une_ecriture_lente(monkeypatch, etats, ecrit)

    tache = asyncio.create_task(_flux_annule(TraitementHandle("t-1")))
    await asyncio.sleep(0.005)
    harceleur = asyncio.create_task(_annuler_a_niveau(tache))
    with pytest.raises(asyncio.CancelledError):
        await tache
    await harceleur

    await asyncio.wait_for(ecrit.wait(), timeout=1)
    assert etats == ["cancelled"]


@pytest.mark.asyncio
async def test_temoin_sans_shield_l_ecriture_est_perdue(monkeypatch) -> None:
    """Contrôle positif : sans le shield, le défaut d'origine se reproduit."""
    ecrit = asyncio.Event()
    etats: list[str] = []
    _poser_une_ecriture_lente(monkeypatch, etats, ecrit)
    monkeypatch.setattr(traitements.asyncio, "shield", lambda coro: coro)

    tache = asyncio.create_task(_flux_annule(TraitementHandle("t-2")))
    await asyncio.sleep(0.005)
    harceleur = asyncio.create_task(_annuler_a_niveau(tache))
    with pytest.raises(asyncio.CancelledError):
        await tache
    await harceleur

    await asyncio.sleep(0.1)
    assert etats == []
