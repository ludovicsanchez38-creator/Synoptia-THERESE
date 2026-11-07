"""F-2 : une ancienne ouverture du fichier ne doit pas révéler le nouveau jeton."""

import os
import stat
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import app.main as main
import pytest


@pytest.mark.skipif(os.name != "posix", reason="Les descripteurs et ACL Windows nécessitent un poste Windows.")
@pytest.mark.parametrize("recuperation", [False, True], ids=["normal", "recuperation"])
async def test_le_demarrage_coupe_l_acces_d_un_descripteur_deja_ouvert(tmp_path, monkeypatch, recuperation):
    from app.models import database
    from app.routers import data, voice
    from app.services import copie_auto, http_client, task_registry, traitements

    monkeypatch.setenv("THERESE_SKIP_SERVICES", "1")
    monkeypatch.setattr(main.settings, "data_dir", tmp_path)
    monkeypatch.setattr(main.settings, "db_path", tmp_path / "therese.db")
    monkeypatch.setattr(copie_auto, "copier_avant_demarrage", lambda *args, **kwargs: None)
    monkeypatch.setattr(main, "init_db", AsyncMock(
        side_effect=RuntimeError("base simulée indisponible") if recuperation else None,
    ))
    monkeypatch.setattr(database, "apply_adhoc_migrations", lambda *args: None)
    monkeypatch.setattr(main, "close_db", AsyncMock())
    monkeypatch.setattr(main, "close_qdrant", AsyncMock())
    monkeypatch.setattr(http_client, "close_http_client", AsyncMock())
    monkeypatch.setattr(data, "effacer_les_dechiffrements_interrompus", lambda: None)
    monkeypatch.setattr(voice, "effacer_les_audios_orphelins", lambda: None)
    monkeypatch.setattr(task_registry, "recuperer_taches_orphelines", AsyncMock(return_value=0))
    monkeypatch.setattr(task_registry, "recuperer_missions_orphelines", AsyncMock(return_value=0))
    monkeypatch.setattr(traitements, "purger_les_terminees", AsyncMock(return_value=0))

    @asynccontextmanager
    async def session_simulee():
        yield AsyncMock()

    monkeypatch.setattr(database, "get_session_context", session_simulee)
    monkeypatch.setattr(main.secrets, "token_urlsafe", lambda taille: "nouveau-jeton-factice")
    for attribut in ("session_token", "reprise_donnees", "reprise_terminee"):
        monkeypatch.setattr(main.app.state, attribut, None, raising=False)
    chemin = tmp_path / ".session_token"
    chemin.write_text("ancien-jeton-factice", encoding="utf-8")
    chemin.chmod(0o644)

    # Ouvert avant la mise à jour, comme peut le faire un autre compte du poste.
    with chemin.open("r", encoding="utf-8") as ancien_descripteur:
        async with main.lifespan(main.app):
            assert chemin.read_text(encoding="utf-8") == "nouveau-jeton-factice"
            assert stat.S_IMODE(chemin.stat().st_mode) == 0o600
            assert main.app.state.session_token == "nouveau-jeton-factice"
            assert ancien_descripteur.read() == "ancien-jeton-factice"
            assert os.fstat(ancien_descripteur.fileno()).st_ino != chemin.stat().st_ino


def test_un_echec_de_publication_ne_remplace_pas_le_jeton_existant(tmp_path, monkeypatch):
    chemin = tmp_path / ".session_token"
    chemin.write_text("ancien-jeton-factice", encoding="utf-8")

    def publication_refusee(*args):
        raise PermissionError("Publication du fichier privé refusée")

    monkeypatch.setattr(main.os, "replace", publication_refusee)
    with pytest.raises(PermissionError, match="Publication du fichier privé refusée"):
        main._ecrire_jeton_prive(chemin, "nouveau-jeton-factice")
    assert chemin.read_text(encoding="utf-8") == "ancien-jeton-factice"
    assert list(tmp_path.iterdir()) == [chemin]
