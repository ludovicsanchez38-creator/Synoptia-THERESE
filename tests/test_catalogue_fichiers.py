"""Le catalogue des fichiers indexés : `search_files`.

Trois signalements pointaient le même manque : le modèle n'a aucun outil pour
atteindre les fichiers indexés (BUG-160 « je ne dispose d'aucun outil
permettant de lire ce fichier », BUG-148 « je n'ai pas d'outil de recherche
pour les documents locaux », D6 « les documents indexés » qui menait aux
factures).

Le catalogue interroge la table `files` — un nom de fichier est un lookup, pas
une question de similarité : la recherche vectorielle porte sur le CONTENU des
fragments, et le nom n'y est même pas.

La cloison est le cœur de cet outil. Elle ne recopie pas celle des contacts :
là où un appel sans périmètre les laisse tous passer, ici il ne rend que les
documents généraux. Un dossier client de mille fichiers ne se déverse pas
parce qu'une conversation n'est pas encore enregistrée.
"""
import json
from datetime import UTC, datetime, timedelta

import pytest
from app.models.entities import FileMetadata
from app.services.memory_tools import execute_memory_tool


async def _fichier(
    db_session,
    *,
    nom: str,
    scope: str = "global",
    scope_id: str | None = None,
    chunks: int = 3,
    chemin: str | None = None,
    indexe_le: datetime | None = None,
) -> str:
    fichier = FileMetadata(
        path=chemin or f"/depot/{scope}/{nom}",
        name=nom,
        extension="." + nom.rsplit(".", 1)[-1] if "." in nom else "",
        size=1024,
        chunk_count=chunks,
        scope=scope,
        scope_id=scope_id,
        indexed_at=indexe_le,
    )
    db_session.add(fichier)
    await db_session.commit()
    return fichier.id


async def _chercher(db_session, query=None, **perimetre) -> dict:
    arguments = {"query": query} if query is not None else {}
    brut = await execute_memory_tool("search_files", arguments, db_session, **perimetre)
    return json.loads(brut)


class TestLaCloison:
    """Ce que chaque périmètre laisse voir, et surtout ce qu'il cache."""

    @pytest.mark.asyncio
    async def test_sans_perimetre_seuls_les_documents_generaux_sortent(self, db_session):
        """Différence assumée avec les contacts : ici, l'absence ferme.

        `_perimetre_de_conversation` rend (None, None) quand la conversation
        n'est pas encore en base. Recopier la branche des contacts — aucune
        cloison — verserait le dossier d'un client au premier appel.
        """
        await _fichier(db_session, nom="general.txt")
        await _fichier(db_session, nom="client.html", scope="project", scope_id="p-a")

        r = await _chercher(db_session)

        assert {d["nom"] for d in r["documents"]} == {"general.txt"}

    @pytest.mark.asyncio
    async def test_un_projet_voit_ses_fichiers_et_les_generaux(self, db_session):
        await _fichier(db_session, nom="general.txt")
        await _fichier(db_session, nom="site.html", scope="project", scope_id="p-a")
        await _fichier(db_session, nom="voisin.html", scope="project", scope_id="p-b")

        r = await _chercher(db_session, scope="project", scope_id="p-a")

        assert {d["nom"] for d in r["documents"]} == {"general.txt", "site.html"}

    @pytest.mark.asyncio
    async def test_une_piece_jointe_d_une_autre_conversation_reste_invisible(
        self, db_session
    ):
        await _fichier(db_session, nom="a_moi.pdf", scope="conversation", scope_id="c-1")
        await _fichier(db_session, nom="a_elle.pdf", scope="conversation", scope_id="c-2")

        r = await _chercher(db_session, scope="global", conversation_id="c-1")

        assert {d["nom"] for d in r["documents"]} == {"a_moi.pdf"}

    @pytest.mark.asyncio
    async def test_tous_les_projets_ouvre_les_dossiers_pas_les_conversations(
        self, db_session
    ):
        await _fichier(db_session, nom="site.html", scope="project", scope_id="p-a")
        await _fichier(db_session, nom="prive.pdf", scope="conversation", scope_id="c-9")

        r = await _chercher(db_session, scope="all", conversation_id="c-1")

        assert {d["nom"] for d in r["documents"]} == {"site.html"}

    @pytest.mark.asyncio
    async def test_un_fichier_dont_l_indexation_a_echoue_n_est_pas_consultable(
        self, db_session
    ):
        """`chunk_count = 0` : la ligne existe, l'index vectoriel est vide."""
        await _fichier(db_session, nom="casse.html", chunks=0)

        r = await _chercher(db_session)

        assert r["documents"] == []


class TestRetrouverParLeNom:
    @pytest.mark.asyncio
    async def test_le_nom_tape_a_la_main_trouve_le_fichier(self, db_session):
        """« fichier index » doit trouver « Fichier-index.html ».

        Personne ne tape les tirets d'un nom de fichier de mémoire.
        """
        await _fichier(db_session, nom="Fichier-index.html")

        r = await _chercher(db_session, "fichier index")

        assert [d["nom"] for d in r["documents"]] == ["Fichier-index.html"]

    @pytest.mark.asyncio
    async def test_le_nom_exact_passe_devant_les_homonymes_partiels(self, db_session):
        """Un dossier de site a des centaines de fichiers contenant « index ».

        Le fichier cherché est le PLUS ANCIEN indexé : dans un dossier de mille
        pages, il est passé au début du parcours. Trier par date le rejetterait
        hors des vingt-cinq lignes affichées, et le modèle conclurait qu'il
        n'existe pas. Seul le rang par exactitude du nom le remonte.
        """
        vieux = datetime.now(UTC) - timedelta(days=30)
        await _fichier(db_session, nom="index.html", indexe_le=vieux)
        # Des concurrents qui contiennent RÉELLEMENT la requête une fois les
        # séparateurs retirés — sinon le filtre les écarte et le tri n'a rien
        # à départager, ce qui rendrait ce test complaisant.
        for i in range(30):
            await _fichier(
                db_session,
                nom=f"ancien-index.html.{i}",
                indexe_le=datetime.now(UTC) - timedelta(minutes=i),
                chemin=f"/depot/global/ancien-index-{i}.html",
            )

        r = await _chercher(db_session, "index.html")

        assert r["documents"][0]["nom"] == "index.html"

    @pytest.mark.asyncio
    async def test_les_jokers_sql_ne_sont_pas_des_jokers(self, db_session):
        """Sans échappement, « % » rendrait le dossier entier."""
        await _fichier(db_session, nom="rapport.md")

        r = await _chercher(db_session, "%")

        assert r["documents"] == []

    @pytest.mark.asyncio
    async def test_le_total_est_dit_meme_quand_l_affichage_est_borne(self, db_session):
        for i in range(40):
            await _fichier(db_session, nom=f"page-{i:03d}.html")

        r = await _chercher(db_session)

        assert r["total"] == 40
        assert r["affiches"] == 25
        assert len(r["documents"]) == 25


class TestCeQuiNeSortJamais:
    @pytest.mark.asyncio
    async def test_aucun_chemin_absolu_dans_la_reponse(self, db_session):
        await _fichier(
            db_session, nom="secret.html", chemin="/Users/ludo/Clients/AlphaCorp/secret.html"
        )

        r = await _chercher(db_session)

        assert "/Users/ludo" not in json.dumps(r)
        assert "AlphaCorp" not in json.dumps(r)

    @pytest.mark.asyncio
    async def test_deux_homonymes_restent_distincts(self, db_session):
        un = await _fichier(db_session, nom="index.html", chemin="/d/src/index.html")
        deux = await _fichier(db_session, nom="index.html", chemin="/d/blog/index.html")

        r = await _chercher(db_session, "index.html")

        identifiants = {d["id"] for d in r["documents"]}
        assert identifiants == {un, deux}

    @pytest.mark.asyncio
    async def test_les_documents_hors_de_portee_sont_comptes_jamais_nommes(
        self, db_session
    ):
        await _fichier(db_session, nom="general.txt")
        await _fichier(db_session, nom="client.html", scope="project", scope_id="p-a")

        r = await _chercher(db_session, scope="global")

        assert r["hors_perimetre"] == 1
        assert "client.html" not in json.dumps(r)

    @pytest.mark.asyncio
    async def test_rien_hors_de_portee_rien_a_signaler(self, db_session):
        await _fichier(db_session, nom="site.html", scope="project", scope_id="p-a")

        r = await _chercher(db_session, scope="project", scope_id="p-a")

        assert "hors_perimetre" not in r


class TestLireUnFichier:
    """`read_file` : le second temps, celui qui répond vraiment.

    Trouver le fichier ne suffit pas. « Décris-moi la structure de
    Fichier-index.html » demande son contenu — et la recherche vectorielle ne
    sait pas le rendre, puisqu'elle compare la question au CONTENU des
    fragments et que le nom du fichier n'est même pas vectorisé.

    L'endpoint HTTP qui lit un fichier ne filtre, lui, que sur l'identifiant :
    aucune cloison. Cet outil-ci ne peut pas se le permettre.
    """

    @pytest.mark.asyncio
    async def test_lit_un_fichier_du_perimetre(self, db_session, tmp_path):
        page = tmp_path / "Fichier-index.html"
        page.write_text("<html><body><h1>Sommaire</h1></body></html>", encoding="utf-8")
        identifiant = await _fichier(
            db_session, nom="Fichier-index.html", chemin=str(page)
        )

        brut = await execute_memory_tool(
            "read_file", {"file_id": identifiant}, db_session
        )
        r = json.loads(brut)

        assert r["found"] is True
        assert "Sommaire" in r["contenu"]
        assert r["nom"] == "Fichier-index.html"

    @pytest.mark.asyncio
    async def test_refuse_un_fichier_hors_du_perimetre(self, db_session, tmp_path):
        """Le refus dit la cloison, sans révéler ce qu'il y a derrière."""
        page = tmp_path / "client.html"
        page.write_text("<html>secret</html>", encoding="utf-8")
        identifiant = await _fichier(
            db_session, nom="client.html", scope="project", scope_id="p-a", chemin=str(page)
        )

        brut = await execute_memory_tool(
            "read_file", {"file_id": identifiant}, db_session, scope="global"
        )
        r = json.loads(brut)

        assert r["found"] is False
        assert "secret" not in brut
        assert "client.html" not in brut
        # Et il oriente : c'est le geste qui débloque, pas une fin de non-recevoir.
        assert "rattach" in json.dumps(r).lower()

    @pytest.mark.asyncio
    async def test_un_identifiant_inconnu_et_un_hors_perimetre_se_ressemblent(
        self, db_session, tmp_path
    ):
        """Sinon le refus devient un oracle : « ce fichier existe ailleurs »."""
        page = tmp_path / "client.html"
        page.write_text("<html>secret</html>", encoding="utf-8")
        cache = await _fichier(
            db_session, nom="client.html", scope="project", scope_id="p-a", chemin=str(page)
        )

        refuse = json.loads(
            await execute_memory_tool("read_file", {"file_id": cache}, db_session, scope="global")
        )
        inconnu = json.loads(
            await execute_memory_tool(
                "read_file", {"file_id": "00000000-0000-0000-0000-000000000000"},
                db_session, scope="global",
            )
        )

        assert refuse["message"] == inconnu["message"]

    @pytest.mark.asyncio
    async def test_refuse_un_fichier_dont_l_indexation_a_echoue(self, db_session, tmp_path):
        page = tmp_path / "casse.html"
        page.write_text("<html></html>", encoding="utf-8")
        identifiant = await _fichier(
            db_session, nom="casse.html", chunks=0, chemin=str(page)
        )

        r = json.loads(
            await execute_memory_tool("read_file", {"file_id": identifiant}, db_session)
        )

        assert r["found"] is False

    @pytest.mark.asyncio
    async def test_un_fichier_disparu_du_disque_le_dit(self, db_session):
        identifiant = await _fichier(
            db_session, nom="parti.html", chemin="/nulle/part/parti.html"
        )

        r = json.loads(
            await execute_memory_tool("read_file", {"file_id": identifiant}, db_session)
        )

        assert r["found"] is False
        assert "introuvable" in json.dumps(r).lower() or "disque" in json.dumps(r).lower()

    @pytest.mark.asyncio
    async def test_un_contenu_long_est_borne_et_le_dit(self, db_session, tmp_path):
        page = tmp_path / "long.txt"
        page.write_text("a" * 25000, encoding="utf-8")
        identifiant = await _fichier(db_session, nom="long.txt", chemin=str(page))

        r = json.loads(
            await execute_memory_tool("read_file", {"file_id": identifiant}, db_session)
        )

        assert len(r["contenu"]) <= 10_000
        assert r["tronque"] is True

    @pytest.mark.asyncio
    async def test_un_chemin_deguise_en_identifiant_est_refuse(self, db_session):
        """`file_id` est un identifiant, jamais une porte vers le disque.

        Ce test ancre le CONTRAT, pas la garde : la requête cloisonnée
        refuserait de toute façon, puisqu'aucune ligne ne porte un tel
        identifiant. La garde explicite reste une ceinture, au cas où la
        recherche changerait un jour de forme — le sabotage la retire sans
        faire échouer ce test, et c'est dit ici plutôt que sous-entendu.
        """
        r = json.loads(
            await execute_memory_tool(
                "read_file", {"file_id": "../../etc/passwd"}, db_session
            )
        )

        assert r["found"] is False


class TestLesAccentsEtLePoids:
    """Relevé par la relecture : deux pièges d'usage réel."""

    @pytest.mark.asyncio
    async def test_un_nom_accentue_se_retrouve_sans_accent(self, db_session):
        """`lower()` de SQLite est ASCII : « École.pdf » restait introuvable.

        Personne ne tape les accents d'un nom de fichier, et surtout pas la
        majuscule accentuée.
        """
        await _fichier(db_session, nom="École-Élémentaire.pdf")

        r = await _chercher(db_session, "ecole elementaire")

        assert [d["nom"] for d in r["documents"]] == ["École-Élémentaire.pdf"]

    @pytest.mark.asyncio
    async def test_un_fichier_trop_lourd_est_refuse_avant_d_etre_lu(
        self, db_session, tmp_path
    ):
        """Lire quarante mégaoctets pour en garder dix mille caractères.

        La taille est connue en base : la refuser AVANT l'extraction évite de
        parser un PDF entier pour jeter presque tout — et évite le gel que D5
        vient de corriger ailleurs.
        """
        page = tmp_path / "enorme.pdf"
        page.write_text("x" * 100, encoding="utf-8")
        fichier = FileMetadata(
            path=str(page), name="enorme.pdf", extension=".pdf",
            size=60 * 1024 * 1024, chunk_count=5, scope="global",
        )
        db_session.add(fichier)
        await db_session.commit()

        r = json.loads(
            await execute_memory_tool("read_file", {"file_id": fichier.id}, db_session)
        )

        assert r["found"] is False
        # Le message de la garde, pas celui de l'échec d'extraction : sans
        # cette distinction, le test passait même la garde retirée.
        assert "trop volumineux pour être lu ici" in r["message"]
