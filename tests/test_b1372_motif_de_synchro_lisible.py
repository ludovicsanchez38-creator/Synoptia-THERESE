"""B-1372 (persona Hugo, cycle 13) : le motif d'un fichier écarté par la
synchronisation était illisible : « Fichier enregistre mais AUCUN chunk indexe :
il n'apparaitra pas dans les recherches. Format non extractible, fichier vide ou
protege ? » (sans accents, « chunk », une question au lieu d'un conseil).
"""

from app.services.project_sync_service import EtatOperation, etat_pour_une_indexation


def test_le_motif_est_en_francais_et_dit_quoi_faire():
    etat, motif = etat_pour_une_indexation(chunk_count=0)
    assert etat == EtatOperation.OBSOLETE
    assert motif
    assert "chunk" not in motif.lower()
    assert "n'apparaîtra pas dans les recherches" in motif
    assert "relance la synchronisation" in motif
    assert "?" not in motif
