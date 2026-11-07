"""F-2 : le jeton privé ne doit pas être livré à un autre compte du poste."""

import os
import stat
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import app.main as main
import httpx
import pytest
from app.models.database import get_session
from app.routers import data

JETON = "jeton-factice-f2"
EXPORT = {"contacts": [{"name": "Contact factice"}], "messages": ["Message factice"]}


@pytest.fixture
def export_simule(monkeypatch):
    """Exercer les vrais middlewares et routes, sans base ni réseau."""
    monkeypatch.setattr(main.app.state, "session_token", JETON, raising=False)
    monkeypatch.setattr(main.app.state, "auth_disabled", False, raising=False)
    monkeypatch.setattr(main.app.state, "reprise_donnees", None, raising=False)
    session = AsyncMock()

    async def session_simulee():
        yield session

    monkeypatch.setattr(
        main.app, "dependency_overrides",
        {**main.app.dependency_overrides, get_session: session_simulee},
    )
    monkeypatch.setattr(data, "log_activity", AsyncMock())
    assembler = Mock(return_value=EXPORT)
    monkeypatch.setattr(data, "_assembler_export_rgpd", assembler)
    return assembler


@pytest.mark.parametrize(
    "origine",
    [None, "tauri://localhost", "http://tauri.localhost", "https://tauri.localhost"],
    ids=["sans-origine", "tauri", "tauri-http", "tauri-https"],
)
@pytest.mark.parametrize("jeton_fourni", [None, "jeton-autre-compte"], ids=["sans-jeton", "faux-jeton"])
async def test_un_autre_compte_ne_peut_obtenir_le_jeton_puis_exporter(export_simule, origine, jeton_fourni):
    entetes = {}
    if origine:
        entetes["Origin"] = origine
    if jeton_fourni:
        entetes["X-Therese-Token"] = jeton_fourni
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=main.app), base_url="http://127.0.0.1:17293",
    ) as client:
        amorcage = await client.get("/api/auth/token", headers=entetes)
        jeton_obtenu = amorcage.json().get("token")
        export = await client.get(
            "/api/data/export",
            headers={"X-Therese-Token": jeton_obtenu} if jeton_obtenu else {},
        )

    assert export.status_code == 401
    assert amorcage.status_code == 401
    assert JETON not in amorcage.text
    assert "Contact factice" not in export.text
    export_simule.assert_not_called()


async def test_le_client_qui_connait_le_jeton_prive_garde_acces_a_l_export(export_simule):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=main.app), base_url="http://127.0.0.1:17293",
        headers={"X-Therese-Token": JETON},
    ) as client:
        amorcage = await client.get("/api/auth/token", headers={"Origin": "tauri://localhost"})
        export = await client.get("/api/data/export")

    assert amorcage.status_code == 200
    assert amorcage.json()["token"] == JETON
    assert export.status_code == 200
    assert export.json() == EXPORT
    export_simule.assert_called_once_with()


@pytest.mark.parametrize("fichier_existant", [False, True], ids=["creation", "ancien-fichier-permissif"])
@pytest.mark.skipif(os.name != "posix", reason="Les ACL Windows se vérifient sur un poste Windows.")
async def test_le_fichier_est_prive_avant_l_ecriture_du_jeton(tmp_path, monkeypatch, fichier_existant):
    """Le vrai démarrage de récupération doit protéger le secret dès sa création."""
    from app.services import copie_auto

    jeton_path = tmp_path / ".session_token"
    if fichier_existant:
        jeton_path.write_text("ancien-jeton-factice", encoding="utf-8")
        os.chmod(jeton_path, 0o644)
    monkeypatch.setattr(main.settings, "data_dir", tmp_path)
    monkeypatch.setattr(main.settings, "db_path", tmp_path / "therese.db")
    monkeypatch.setattr(copie_auto, "copier_avant_demarrage", lambda *args, **kwargs: None)
    monkeypatch.setattr(main, "init_db", AsyncMock(side_effect=RuntimeError("base simulée indisponible")))
    monkeypatch.setattr(main, "close_db", AsyncMock())
    monkeypatch.setattr(main.secrets, "token_urlsafe", lambda taille: JETON)
    for attribut in ("session_token", "reprise_donnees", "reprise_terminee"):
        monkeypatch.setattr(main.app.state, attribut, None, raising=False)

    observations = []
    chmod_original = os.chmod

    def observer_chmod(chemin, mode, *args, **kwargs):
        if Path(chemin) == jeton_path:
            observations.append((
                stat.S_IMODE(jeton_path.stat().st_mode),
                JETON in jeton_path.read_text(encoding="utf-8"),
            ))
        return chmod_original(chemin, mode, *args, **kwargs)

    monkeypatch.setattr(main.os, "chmod", observer_chmod)
    masque_original = os.umask(0o022)
    try:
        async with main.lifespan(main.app):
            assert jeton_path.read_text(encoding="utf-8") == JETON
            assert stat.S_IMODE(jeton_path.stat().st_mode) == 0o600
    finally:
        os.umask(masque_original)

    assert observations
    assert all(not secret_present or mode & 0o077 == 0 for mode, secret_present in observations)
