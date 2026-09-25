"""B-1318 : INDEX_SEMAPHORE (asyncio, de module) se lie à la boucle de sa
première attente disputée, comme les verrous de B-1297 et B-1306. Chaque test
a sa boucle : disputé dans un test, il faisait lever « bound to a different
event loop » dans le suivant. Les deux tests se suivent à dessein.
Lecteur β, passe 6."""

import asyncio

import pytest


async def _disputer():
    from app.services import indexation

    semaphore = indexation.INDEX_SEMAPHORE
    places = semaphore._value
    for _ in range(places):
        await semaphore.acquire()
    attente = asyncio.create_task(semaphore.acquire())
    await asyncio.sleep(0)
    semaphore.release()
    await attente
    for _ in range(places):
        semaphore.release()


@pytest.mark.asyncio
async def test_1_dispute_le_semaphore_dans_sa_boucle():
    await _disputer()


@pytest.mark.asyncio
async def test_2_le_dispute_dans_une_autre_boucle():
    await _disputer()
