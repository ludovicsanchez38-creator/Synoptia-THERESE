"""La sonde de santé peut ouvrir Qdrant même quand les services sont ignorés."""

import os
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
BACKEND = RACINE / "src" / "backend"


def test_arret_ferme_qdrant_ouvert_par_la_sante_en_mode_test(tmp_path: Path) -> None:
    """Exercer le vrai lifespan dans un processus isolé des fixtures pytest.

    Les fixtures de la suite remplacent le lifespan et simulent Qdrant. Le
    processus fils utilise seulement des données jetables et un transport ASGI
    interne, sans ouvrir de port ni lancer les services externes.
    """
    donnees = tmp_path / "donnees"
    home_test = tmp_path / "home"
    home_test.mkdir()
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "TMPDIR": str(tmp_path),
        "HOME": str(home_test),
        "XDG_CACHE_HOME": str(home_test / "cache"),
        "XDG_CONFIG_HOME": str(home_test / "config"),
        "XDG_DATA_HOME": str(home_test / "share"),
        "THERESE_SKIP_SERVICES": "1",
        "THERESE_DATA_DIR": str(donnees),
        "DATA_DIR": str(donnees),
        "DB_PATH": str(donnees / "therese.db"),
        "QDRANT_PATH": str(donnees / "qdrant"),
        "THERESE_DB_KEY": "ad" * 32,
        "PORT": "17394",
        "PYTHONPATH": str(BACKEND),
    }
    scenario = """
import asyncio
import importlib
from pathlib import Path

import httpx
from app.config import settings
from app.main import app, lifespan

qdrant = importlib.import_module("app.services.qdrant")
donnees = Path(settings.data_dir)
assert donnees == Path(__import__("os").environ["THERESE_DATA_DIR"])
assert settings.db_path == donnees / "therese.db"
assert settings.qdrant_path == donnees / "qdrant"
assert settings.port == 17394

async def verifier():
    async with lifespan(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            reponse = await client.get("/health")
        assert reponse.status_code == 200, reponse.text
        assert reponse.json()["services"]["qdrant"] is True, reponse.text
        assert qdrant._qdrant_service is not None
        assert qdrant._qdrant_service._client is not None
        print("QDRANT_OPENED=1", flush=True)
    assert qdrant._qdrant_service is None, "Qdrant reste ouvert au shutdown"
    print("QDRANT_CLOSED=1", flush=True)

asyncio.run(verifier())
"""
    resultat = subprocess.run(
        [sys.executable, "-c", scenario],
        cwd=RACINE,
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )

    assert resultat.returncode == 0, (
        f"Processus fils: code {resultat.returncode}\n"
        f"stdout:\n{resultat.stdout}\nstderr:\n{resultat.stderr}"
    )
    assert "QDRANT_OPENED=1" in resultat.stdout
    assert "QDRANT_CLOSED=1" in resultat.stdout
    assert "Exception ignored in: <function QdrantClient.__del__" not in resultat.stderr
