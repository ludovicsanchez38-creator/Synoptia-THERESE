"""B-1194 : read_file borne en octets ce qu'il charge et rend au modèle.

MAX_LIGNES_LUES ne borne que les lignes : un fichier sans saut de ligne passait
entier. Mesure du reproducteur : une commande confinée crée en un instant un
fichier creux de 64 Mio dans le dépôt, read_file le rendait entier
(67 108 864 caractères) au modèle.
"""

import pytest


@pytest.mark.asyncio
async def test_un_fichier_geant_sans_saut_de_ligne_est_tronque(tmp_path):
    from app.services.agents.tools import MAX_OCTETS_LUS, AgentToolExecutor

    with open(tmp_path / "journal.log", "wb") as f:
        f.truncate(64 * 1024 * 1024)  # fichier creux : 64 Mio, quelques octets sur disque

    resultat = await AgentToolExecutor(str(tmp_path)).read_file("journal.log")

    assert len(resultat) <= MAX_OCTETS_LUS + 200, len(resultat)
    assert "tronqué" in resultat[-200:], resultat[-200:]


@pytest.mark.asyncio
async def test_temoin_petit_fichier_lu_entier(tmp_path):
    from app.services.agents.tools import AgentToolExecutor

    (tmp_path / "notes.md").write_text("a\nb\n", encoding="utf-8")
    assert await AgentToolExecutor(str(tmp_path)).read_file("notes.md") == "a\nb\n"


@pytest.mark.asyncio
async def test_les_fins_de_ligne_windows_sont_normalisees(tmp_path):
    """B-1200 : lire en octets ne doit pas rendre les CRLF que read_text
    normalisait (régression vue sur la CI Windows)."""
    from app.services.agents.tools import AgentToolExecutor

    (tmp_path / "notes.md").write_bytes(b"a\r\nb\r\n")
    assert await AgentToolExecutor(str(tmp_path)).read_file("notes.md") == "a\nb\n"


@pytest.mark.asyncio
async def test_la_coupe_en_lignes_dit_aussi_la_coupe_en_octets(tmp_path):
    """B-1200 : quand les deux bornes jouent, le total de lignes annoncé ne
    porte que sur la partie lue ; le modèle doit le savoir."""
    from app.services.agents.tools import MAX_OCTETS_LUS, AgentToolExecutor

    (tmp_path / "long.log").write_bytes(b"x\n" * (MAX_OCTETS_LUS // 2 + 1000))
    resultat = await AgentToolExecutor(str(tmp_path)).read_file("long.log", max_lines=10)
    assert "tronqué à 10 lignes" in resultat
    assert "octets" in resultat.splitlines()[-1], resultat.splitlines()[-1]
