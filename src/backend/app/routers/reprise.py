"""Routes authentifiées de secours, sans session SQL."""
import asyncio
import logging

from app.config import settings
from app.services.reprise_auto import lister_copies, restaurer_copie
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, StrictBool

router = APIRouter(prefix='/api/reprise', tags=['reprise'])
logger = logging.getLogger(__name__)
_verrou = asyncio.Lock()


def exiger_reprise(request: Request):
    if not getattr(request.app.state, 'reprise_donnees', None):
        raise HTTPException(409, 'La restauration automatique est réservée à un démarrage en échec.')


@router.get('/copies')
async def copies(request: Request):
    exiger_reprise(request)
    return {'copies': await asyncio.to_thread(lister_copies, settings.data_dir)}


class Restauration(BaseModel):
    copie: str
    confirmer: StrictBool = False


@router.post('/restaurer')
async def restaurer(demande: Restauration, request: Request):
    exiger_reprise(request)
    if not demande.confirmer:
        raise HTTPException(400, 'Confirme la restauration de cette copie.')
    if _verrou.locked() or getattr(request.app.state, 'reprise_terminee', False):
        raise HTTPException(409, 'Une restauration est en cours ou attend le redémarrage.')
    async with _verrou:
        # Ne pas libérer le verrou si le client ferme la fenêtre : le travail
        # dans le fil doit finir avant toute nouvelle tentative.
        tache = asyncio.create_task(asyncio.to_thread(
            restaurer_copie, settings.data_dir, settings.db_path, demande.copie,
        ))
        try:
            try:
                abri = await asyncio.shield(tache)
            except asyncio.CancelledError:
                abri = await tache
                request.app.state.reprise_terminee = True
                raise
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        except Exception as exc:
            logger.exception('Restauration automatique en échec')
            raise HTTPException(500, "La copie n’a pas pu être restaurée. Les fichiers mis de côté sont conservés dans backups/reprises. Tu peux choisir une autre copie.") from exc
        request.app.state.reprise_terminee = True
        return {'redemarrage_requis': True, 'base_mise_de_cote': str(abri)}
