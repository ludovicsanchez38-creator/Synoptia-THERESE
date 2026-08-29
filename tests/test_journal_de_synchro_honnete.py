"""
Le journal de synchro ne dit pas « fait » quand le catalogue refusera le fichier.

Campagne cinq personas, finding d'Aude. L'indexation se déclarait
`etat: "fait"`, `erreur: null`, avec un `indexed_at` horodaté — et produisait
`chunk_count: 0` sur les trois fichiers du dossier Vermeer, Qdrant restant à
un seul point. En parallèle, `search_files` rendait `{"found": false}` sur le
nom exact du fichier.

Aude a testé et ÉCARTÉ l'hypothèse du périmètre : en `memory_scope: "all"`,
même résultat. Elle constate les deux ruptures sans affirmer laquelle cause
l'autre.

Deux décisions du plan 0.56, dans cet ordre :

- On ne touche PAS au filtre `chunk_count > 0` de `search_files`
  (`memory_tools.py:1085`). Un fichier sans chunk n'est pas lisible : le
  catalogue a raison de le cacher. `chunk_count = 0` est un état honnête en
  base.
- **Le mensonge est le journal.** Dire `FAIT` pour un fichier que le catalogue
  refusera, c'est la couche d'exécution qui affirme un succès sans le geste —
  le motif de toute la campagne.
"""

import pytest


class TestUnFichierSansChunkNestPasFait:
    @pytest.mark.asyncio
    async def test_zero_chunk_ne_se_consigne_pas_fait(self, db_session):
        from app.services.project_sync_service import EtatOperation, etat_pour_une_indexation

        etat, erreur = etat_pour_une_indexation(chunk_count=0)

        assert etat is not EtatOperation.FAIT, (
            "« fait » pour un fichier que `search_files` refusera : le journal "
            "affirme un succès que le catalogue contredit"
        )
        assert erreur, "l'état doit porter sa cause, pas rester muet"
        assert "chunk" in erreur.lower() or "indexé" in erreur.lower()

    @pytest.mark.asyncio
    async def test_un_fichier_indexe_reste_fait(self, db_session):
        from app.services.project_sync_service import (
            EtatOperation,
            etat_pour_une_indexation,
        )

        etat, erreur = etat_pour_une_indexation(chunk_count=12)

        assert etat is EtatOperation.FAIT
        assert erreur is None

    @pytest.mark.asyncio
    async def test_le_catalogue_garde_son_filtre(self):
        """On ne rend pas visible un fichier illisible pour faire plaisir au journal."""
        from pathlib import Path

        source = Path("src/backend/app/services/memory_tools.py").read_text(
            encoding="utf-8"
        )
        assert "FileMetadata.chunk_count > 0" in source, (
            "le filtre du catalogue est délibéré : un fichier sans chunk n'est "
            "pas lisible, le cacher est honnête"
        )
