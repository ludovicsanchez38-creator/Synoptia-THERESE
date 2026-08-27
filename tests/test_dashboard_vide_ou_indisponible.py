"""« Rien à afficher » et « on n'a pas pu savoir » sont deux choses.

Trouvé le 27/08/2026 pendant l'audit UX. `get_setup_status` initialise
chaque indicateur à False, puis tente de le renseigner dans un `try`. Si la
lecture échoue — base verrouillée, corruption, migration en cours —, l'échec
part au journal et le False sort tel quel.

L'écran affiche alors « connecte ton calendrier » à quelqu'un dont le
calendrier EST connecté. Il va reconfigurer un service qui marche, et n'y
comprendra rien. Une panne présentée comme un état vide est pire qu'une
panne annoncée : elle envoie l'utilisateur réparer ce qui n'est pas cassé.

Le correctif est additif : les vérifications qui n'ont pas abouti sont
NOMMÉES dans la réponse, sans changer les champs existants.
"""

import pytest
from httpx import AsyncClient


class TestUnePanneNeSeDeguisePasEnVide:
    @pytest.mark.asyncio
    async def test_le_cas_nominal_ne_signale_rien_d_indisponible(
        self, client: AsyncClient
    ) -> None:
        reponse = await client.get("/api/dashboard/setup-status")

        assert reponse.status_code == 200
        corps = reponse.json()
        assert corps["indisponibles"] == []

    @pytest.mark.asyncio
    async def test_une_lecture_qui_echoue_est_nommee(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """La panne doit être DITE, pas convertie en « non configuré »."""
        from app.routers import dashboard

        async def lecture_en_panne(*a, **k):
            raise RuntimeError("database is locked")

        monkeypatch.setattr(dashboard, "_lire_a_un_calendrier", lecture_en_panne)

        reponse = await client.get("/api/dashboard/setup-status")

        assert reponse.status_code == 200
        corps = reponse.json()
        assert "calendrier" in corps["indisponibles"], (
            "une lecture en échec doit être signalée, pas rendue comme un False"
        )
        # et le champ historique reste présent, pour ne rien casser
        assert corps["has_calendar"] is False

    @pytest.mark.asyncio
    async def test_les_autres_verifications_survivent_a_une_panne_isolee(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.routers import dashboard

        async def lecture_en_panne(*a, **k):
            raise RuntimeError("database is locked")

        monkeypatch.setattr(dashboard, "_lire_a_un_calendrier", lecture_en_panne)

        corps = (await client.get("/api/dashboard/setup-status")).json()

        assert "has_email" in corps and "billing_complete" in corps
        assert corps["indisponibles"] == ["calendrier"]


class TestLaCleIaSuitLaMemeRegle:
    """Trois vérifications sur quatre, ce n'est pas une règle.

    `_has_any_llm_key` absorbait ses erreurs de lecture et retombait sur
    False, sans jamais signaler l'échec — alors que le calendrier, l'email et
    la facturation le font depuis le correctif. La mise en route demandait
    donc de configurer une clé DÉJÀ configurée, exactement le défaut qu'on
    venait de fermer ailleurs. Relevé par la revue du 27/08/2026.
    """

    @pytest.mark.asyncio
    async def test_une_lecture_de_cle_en_echec_est_nommee(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.routers import dashboard

        async def lecture_en_panne(*a, **k):
            raise RuntimeError("database is locked")

        monkeypatch.setattr(dashboard, "_lire_a_une_cle_ia", lecture_en_panne)

        corps = (await client.get("/api/dashboard/setup-status")).json()

        assert "cle_ia" in corps["indisponibles"]
        assert corps["has_llm_key"] is False

    @pytest.mark.asyncio
    async def test_une_preference_de_fournisseur_illisible_est_nommee(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Le premier correctif avait DÉPLACÉ le défaut, pas fermé.

        J'avais retiré le `try/except` qui masquait la lecture des clés en
        base, mais deux autres subsistaient dans la même fonction. Une
        préférence de fournisseur illisible retombait donc encore sur un
        `False` muet. Trouvé par la sonde de la revue, qui a exécuté le cas
        au lieu de lire le code.

        Le test d'Ollama, lui, garde son silence : son absence est le cas
        NORMAL d'une installation cloud, pas une panne.
        """
        from app.routers import dashboard

        async def lecture_en_panne(*a, **k):
            raise RuntimeError("preference table unreadable")

        monkeypatch.setattr(dashboard, "_lire_preference_ollama", lecture_en_panne)

        corps = (await client.get("/api/dashboard/setup-status")).json()

        assert "cle_ia" in corps["indisponibles"]

    @pytest.mark.asyncio
    async def test_sans_cle_mais_sans_panne_rien_n_est_signale(
        self, client: AsyncClient
    ) -> None:
        """Ne pas confondre « pas de clé » avec « on n'a pas pu savoir »."""
        corps = (await client.get("/api/dashboard/setup-status")).json()

        assert "cle_ia" not in corps["indisponibles"]
