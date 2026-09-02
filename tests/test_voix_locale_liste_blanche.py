"""B-105 : le champ `voice` d'une requête devient un chemin disque.

`POST /api/voice/tts` accepte un `voice` libre (`TTSRequest.voice`), et
`synthesize_local` en fait `voices_dir() / f"{voice}.onnx"` sans jamais le
valider. `download_piper_voice`, lui, applique DÉJÀ une liste blanche
(`_PIPER_VOICE_URLS`) : un voisin immédiat pose la règle, celui-ci ne la
balaie pas.

Conséquence : un `voice` porteur de `../` fait charger par Piper un fichier
`.onnx` situé HORS du dossier des voix - donc n'importe quel modèle ONNX
déposé sur la machine, exécuté par le moteur d'inférence.
"""
import sys
import types

import pytest


@pytest.fixture
def piper_factice(monkeypatch, tmp_path):
    """Piper simulé : on enregistre le chemin réellement chargé."""
    from app.services import voice_local

    charges: list[str] = []

    class _VoixFactice:
        @staticmethod
        def load(chemin):
            charges.append(str(chemin))
            return _VoixFactice()

        def synthesize_wav(self, texte, wav):
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(22050)
            wav.writeframes(b"\x00\x00")

    module = types.ModuleType("piper")
    module.PiperVoice = _VoixFactice
    monkeypatch.setitem(sys.modules, "piper", module)
    monkeypatch.setattr(voice_local, "tts_available", lambda: True)

    dossier_voix = tmp_path / "voices"
    dossier_voix.mkdir()
    monkeypatch.setattr(voice_local, "voices_dir", lambda: dossier_voix)
    return charges, dossier_voix


def test_un_nom_de_voix_traversant_ne_charge_rien(piper_factice, tmp_path):
    """Le cœur de B-105 : `../` sort du dossier des voix."""
    from app.services.voice_local import synthesize_local

    charges, dossier_voix = piper_factice
    dehors = tmp_path / "voices" / ".." / "dehors"
    dehors.mkdir(parents=True, exist_ok=True)
    (dehors / "malveillant.onnx").write_bytes(b"ONNX")

    with pytest.raises(RuntimeError) as erreur:
        synthesize_local("bonjour", str(tmp_path / "sortie.wav"),
                         voice="../dehors/malveillant")

    assert charges == [], (
        f"Piper a chargé un fichier hors du dossier des voix : {charges}"
    )
    assert "inconnue" in str(erreur.value).lower(), (
        "le refus doit dire que la voix n'est pas connue, pas qu'elle est "
        f"absente (message obtenu : {erreur.value})"
    )


def test_une_voix_hors_liste_blanche_est_refusee(piper_factice, tmp_path):
    """Même sans `../` : seules les voix du catalogue sont chargeables."""
    from app.services.voice_local import synthesize_local

    charges, dossier_voix = piper_factice
    (dossier_voix / "voix-deposee-a-la-main.onnx").write_bytes(b"ONNX")

    with pytest.raises(RuntimeError):
        synthesize_local("bonjour", str(tmp_path / "sortie.wav"),
                         voice="voix-deposee-a-la-main")

    assert charges == []


def test_la_voix_officielle_fonctionne_toujours(piper_factice, tmp_path):
    """Verrou inverse : durcir ne doit pas casser la synthèse réelle."""
    from app.services.voice_local import DEFAULT_PIPER_VOICE, synthesize_local

    charges, dossier_voix = piper_factice
    (dossier_voix / f"{DEFAULT_PIPER_VOICE}.onnx").write_bytes(b"ONNX")

    sortie = str(tmp_path / "sortie.wav")
    assert synthesize_local("bonjour", sortie, voice=DEFAULT_PIPER_VOICE) == sortie
    assert charges == [str(dossier_voix / f"{DEFAULT_PIPER_VOICE}.onnx")]


def test_la_presence_d_une_voix_suit_la_meme_liste_blanche(piper_factice):
    """`tts_voice_downloaded` construit le MÊME chemin : jumeau du défaut."""
    from app.services.voice_local import DEFAULT_PIPER_VOICE, tts_voice_downloaded

    _charges, dossier_voix = piper_factice
    dehors = dossier_voix.parent / "dehors"
    dehors.mkdir(exist_ok=True)
    (dehors / "malveillant.onnx").write_bytes(b"ONNX")
    (dossier_voix / f"{DEFAULT_PIPER_VOICE}.onnx").write_bytes(b"ONNX")

    assert tts_voice_downloaded("../dehors/malveillant") is False
    assert tts_voice_downloaded(DEFAULT_PIPER_VOICE) is True
