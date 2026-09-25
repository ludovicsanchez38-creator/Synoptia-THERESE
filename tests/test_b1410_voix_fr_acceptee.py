"""B-1410 (relevé à la lecture du code par la RFC P-109, reproduit ici) :
l'interface envoie `voice: "fr"` à `POST /api/voice/tts`
(`services/api/voice.ts`, `synthesizeSpeech(text, voice = 'fr')`), mais la liste
blanche des voix ne connaît que `fr_FR-siwis-medium` : « Générer l'audio
local » de l'espace Voix échouait à chaque fois (« Voix Piper inconnue : fr »).
Aucun test ne le voyait : l'interface simule la fonction, et les tests du
serveur envoyaient une requête sans `voice`.

La langue seule désigne la voix par défaut de cette langue. La liste blanche
de B-105 reste la seule porte vers un fichier `.onnx`.
"""

from __future__ import annotations

import pytest
from app.services.error_handler import ErreurPourEcran
from app.services.voice_local import DEFAULT_PIPER_VOICE, _voix_du_catalogue


def test_la_langue_seule_designe_la_voix_par_defaut():
    assert _voix_du_catalogue("fr") == DEFAULT_PIPER_VOICE


def test_un_nom_complet_reste_accepte():
    assert _voix_du_catalogue("fr_FR-siwis-medium") == "fr_FR-siwis-medium"


@pytest.mark.parametrize("voix", ["../../etc/x", "en", "fr/../../x", ""])
def test_la_liste_blanche_de_b105_tient(voix):
    with pytest.raises(ErreurPourEcran):
        _voix_du_catalogue(voix)
