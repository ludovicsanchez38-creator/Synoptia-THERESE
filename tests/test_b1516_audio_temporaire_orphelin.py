"""B-1516 : un arrêt brutal pendant une transcription laissait l'audio de
l'utilisatrice dans le dossier temporaire du système.

Les routes de dictée et de synthèse écrivent un fichier temporaire, effacé
en fin de route ; un moteur tué entre-temps le laissait, sans nom qui le
rattache à THÉRÈSE, dans un dossier que Windows ne purge pas. Les fichiers
portent désormais un préfixe, et le démarrage efface ceux qui restent.
"""

import os
import time
from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_la_dictee_locale_ecrit_un_fichier_prefixe(client, monkeypatch):
    from app.routers.voice import PREFIXE_AUDIO_TEMPORAIRE
    from app.services import voice_local

    chemins: list[str] = []
    monkeypatch.setattr(voice_local, "active_whisper_model", lambda: "small", raising=False)
    monkeypatch.setattr(voice_local, "stt_available", lambda: True, raising=False)
    monkeypatch.setattr(voice_local, "get_setup_state", lambda: {"state": "done"}, raising=False)
    monkeypatch.setattr(voice_local, "transcribe_local", lambda chemin, **_: chemins.append(chemin) or "Bonjour")

    reponse = await client.post("/api/voice/local/transcribe", files={"audio": ("rec.webm", b"RIFF....", "audio/webm")})
    assert reponse.status_code == 200, reponse.text
    assert chemins and Path(chemins[0]).name.startswith(PREFIXE_AUDIO_TEMPORAIRE)
    assert not Path(chemins[0]).exists()


def test_le_demarrage_efface_les_audios_orphelins_et_rien_d_autre(tmp_path: Path):
    from app.routers.voice import PREFIXE_AUDIO_TEMPORAIRE, effacer_les_audios_orphelins

    (tmp_path / f"{PREFIXE_AUDIO_TEMPORAIRE}abc.webm").write_bytes(b"voix")
    (tmp_path / f"{PREFIXE_AUDIO_TEMPORAIRE}def.wav").write_bytes(b"voix")
    (tmp_path / "autre-appli.webm").write_bytes(b"x")
    # B-1645 : seuls les audios d'au moins une heure sont des orphelins.
    il_y_a_deux_heures = time.time() - 2 * 3600
    for chemin in tmp_path.iterdir():
        os.utime(chemin, (il_y_a_deux_heures, il_y_a_deux_heures))

    assert effacer_les_audios_orphelins(tmp_path) == 2
    assert [p.name for p in tmp_path.iterdir()] == ["autre-appli.webm"]
