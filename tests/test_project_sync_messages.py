"""D4 : ce que l'écran apprend quand la synchro de dossier échoue.

Dr_logic, 25/08 : « la synchro de dossier me donne un message peu explicite ».
Le sidecar montrait un HTTP 500 provoqué par un `OverflowError` SQLite sur
l'identifiant de volume Windows (BUG-172, corrigé en 0.47).

Reste la frontière d'erreurs posée en 0.48 : à la limite de l'écran, seuls des
messages localisés passent, jamais le texte technique d'une exception. Le
routeur de synchro recopiait encore l'exception dans le `detail` — un
traceback SQLite ou un `OverflowError` serait parti droit à l'utilisateur.
"""
import pytest
from app.routers import project_sync
from app.services import project_sync_service as svc
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_une_panne_inattendue_ne_livre_pas_son_texte_technique(monkeypatch):
    async def _explose(*args, **kwargs):
        raise OverflowError("Python int too large to convert to SQLite INTEGER")

    monkeypatch.setattr(svc, "definir_racine", _explose)

    with pytest.raises(HTTPException) as capture:
        await project_sync.definir_racine(
            "projet-a", project_sync.RacineRequest(chemin="/un/dossier")
        )

    assert capture.value.status_code == 500
    detail = str(capture.value.detail)
    assert "OverflowError" not in detail
    assert "SQLite" not in detail
    assert "int too large" not in detail
    # Et il reste utile : il situe l'échec et dit quoi faire.
    assert "racine" in detail.lower() or "dossier" in detail.lower()


@pytest.mark.asyncio
async def test_un_refus_metier_garde_son_explication(monkeypatch):
    """400 et 409 portent des messages écrits pour l'utilisateur : ils passent."""
    async def _refuse(*args, **kwargs):
        raise svc.ErreurRacine("Cette racine appartient déjà à un autre projet.")

    monkeypatch.setattr(svc, "definir_racine", _refuse)

    with pytest.raises(HTTPException) as capture:
        await project_sync.definir_racine(
            "projet-a", project_sync.RacineRequest(chemin="/un/dossier")
        )

    assert capture.value.status_code == 400
    assert "appartient déjà" in str(capture.value.detail)
