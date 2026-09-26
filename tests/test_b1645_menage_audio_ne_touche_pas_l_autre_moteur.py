"""B-1645 : le ménage des audios au démarrage (B-1516) vidait le dossier
temporaire partagé.

Tous les moteurs THÉRÈSE d'un même compte écrivent leurs dictées dans le
même dossier temporaire, sous le même préfixe. Un second moteur qui démarre
(application et moteur de travail, ou relance pendant qu'un autre tourne)
effaçait donc la dictée qu'un premier moteur était en train de transcrire.

Seuls les audios assez anciens pour ne plus appartenir à un travail en cours
sont désormais effacés.
"""

from __future__ import annotations

import os
import time


def test_une_dictee_en_cours_d_un_autre_moteur_survit_au_demarrage(tmp_path):
    from app.routers.voice import PREFIXE_AUDIO_TEMPORAIRE, effacer_les_audios_orphelins

    en_cours = tmp_path / f"{PREFIXE_AUDIO_TEMPORAIRE}en-cours.webm"
    en_cours.write_bytes(b"voix")
    oubliee = tmp_path / f"{PREFIXE_AUDIO_TEMPORAIRE}oubliee.webm"
    oubliee.write_bytes(b"voix")
    il_y_a_deux_heures = time.time() - 2 * 3600
    os.utime(oubliee, (il_y_a_deux_heures, il_y_a_deux_heures))

    assert effacer_les_audios_orphelins(tmp_path) == 1
    assert en_cours.exists(), "la dictée en cours d'un autre moteur a été effacée"
    assert not oubliee.exists()
