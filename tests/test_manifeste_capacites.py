"""Manifeste de capacités — le versant backend du contrat (0.44).

Le manifeste est un fichier JSON CANONIQUE, partagé entre le frontend et le
sidecar. Ce choix vient d'une contrainte du pipeline de release : le sidecar
PyInstaller est construit AVANT que Node ne soit installé et que le frontend ne
soit bâti. Un fichier généré depuis le TypeScript ne serait donc jamais vu par
le sidecar — c'est pourquoi la source est neutre et vit sous `app/data/`, que
`backend.spec` embarque déjà.

Ces tests garantissent que le backend peut réellement le lire, en développement
comme dans l'application packagée, et que ce qu'il décrit correspond à ce que le
backend sait faire.
"""
import json

import pytest


def _charger():
    from app.services.capacites import charger_manifeste

    return charger_manifeste()


class TestLeSidecarSaitLireLeManifeste:
    def test_le_fichier_est_trouve_par_un_chemin_relatif_au_module(self):
        """Jamais le répertoire courant : sous PyInstaller il n'a rien à voir.

        Le sidecar est lancé par Tauri, dont le répertoire courant est celui de
        l'application, pas celui du backend. Un chemin relatif au CWD marcherait
        en développement et échouerait une fois packagé.
        """
        manifeste = _charger()

        assert manifeste["capacites"], "manifeste vide ou introuvable"

    def test_le_schema_est_versionne(self):
        """Sans version de schéma, une évolution casse en silence."""
        assert _charger()["schema"] >= 1

    def test_le_fichier_est_embarque_dans_le_binaire(self):
        """Garde de packaging : `backend.spec` doit emporter `app/data`.

        Sans cette ligne, le manifeste existe en développement et disparaît
        dans l'application livrée aux testeurs — le pire des deux mondes.
        """
        from pathlib import Path

        spec = Path(__file__).resolve().parents[1] / "src" / "backend" / "backend.spec"
        contenu = spec.read_text(encoding="utf-8")

        # Le chemin est composé avec `os.path.join`, donc jamais présent en
        # toutes lettres. Chercher « app/data » ferait échouer ce test sur un
        # fichier parfaitement correct — première version de ce test.
        assert '"app", "data"' in contenu, (
            "le dossier app/data n'est plus embarqué : le manifeste existerait "
            "en développement et disparaîtrait dans l'application livrée"
        )


class TestLeManifesteDitVraiSurLaNavigation:
    def test_chaque_destination_du_chat_correspond_a_une_capacite(self):
        """Le point de départ du chantier.

        La table des destinations du backend et le manifeste décrivent les mêmes
        vues. Quand elles divergent, une vue devient inatteignable par
        `{action: ouvrir …}` et invisible de `/aide` — c'est très exactement ce
        qui est arrivé à la vue « Fichiers », celle qui porte l'indexation.
        """
        from app.services.chat_actions import NAVIGATION_TARGETS

        manifeste = _charger()
        actions_du_manifeste = {
            p["binding"]["actionId"]
            for p in manifeste["points_entree"]
            if p["binding"]["registre"] in ("action", "raccourci")
        }

        orphelines = {
            action_id
            for action_id, _ in NAVIGATION_TARGETS.values()
            if action_id not in actions_du_manifeste
        }

        assert orphelines == set(), (
            f"le backend sait ouvrir {orphelines} mais le manifeste ne les décrit "
            "pas : ces destinations resteront absentes de toute aide dérivée"
        )

    def test_aucune_capacite_de_navigation_n_est_absente_du_backend(self):
        """L'inverse : une capacité décrite mais que le chat ne sait pas ouvrir."""
        from app.services.chat_actions import NAVIGATION_TARGETS

        manifeste = _charger()
        actions_backend = {action_id for action_id, _ in NAVIGATION_TARGETS.values()}

        # Seules les capacités qui déclarent une vue sont concernées : une
        # capacité sans vue (un réglage, par exemple) n'a pas à être ouvrable.
        capacites_avec_vue = {
            capacite
            for p in manifeste["points_entree"]
            if p["binding"]["registre"] == "vue"
            for capacite in p["capacites"]
        }

        manquantes = []
        for capacite in capacites_avec_vue:
            actions = {
                p["binding"]["actionId"]
                for p in manifeste["points_entree"]
                if capacite in p["capacites"] and p["binding"]["registre"] == "action"
            }
            if actions and not (actions & actions_backend):
                manquantes.append(capacite)

        assert manquantes == [], (
            f"les capacités {manquantes} ont une vue et une action, mais le chat "
            "ne sait pas les ouvrir"
        )


class TestLeContratEstRespecteParLesDonnees:
    def test_aucun_identifiant_en_double(self):
        manifeste = _charger()

        ids = [c["id"] for c in manifeste["capacites"]]
        assert len(set(ids)) == len(ids)

        entrees = [p["id"] for p in manifeste["points_entree"]]
        assert len(set(entrees)) == len(entrees)

    def test_aucun_identifiant_retire_n_est_reutilise(self):
        """Un identifiant retiré est réservé à vie.

        Le réutiliser ferait réapparaître une capacité morte dans un catalogue
        déjà publié, sous un nom qui ne lui correspond plus.
        """
        manifeste = _charger()
        vivants = {c["id"] for c in manifeste["capacites"]}
        reserves = set(manifeste.get("identifiants_reserves", []))

        assert vivants & reserves == set()

    def test_chaque_point_d_entree_vise_une_capacite_connue(self):
        manifeste = _charger()
        connues = {c["id"] for c in manifeste["capacites"]}

        inconnues = {
            capacite
            for p in manifeste["points_entree"]
            for capacite in p["capacites"]
            if capacite not in connues
        }

        assert inconnues == set()

    def test_les_limites_connues_sont_ecrites_pour_un_humain(self):
        """Une limite tue est un piège ; une limite en jargon est inutile."""
        manifeste = _charger()

        for capacite in manifeste["capacites"]:
            for limite in capacite.get("limites", []):
                assert len(limite) > 20, f"limite trop laconique : {limite}"
                assert limite[0].isupper(), f"limite non rédigée : {limite}"

    def test_le_json_reste_lisible_a_la_main(self):
        """C'est un fichier qu'on édite : il doit rester relisible."""
        from app.services.capacites import CHEMIN_MANIFESTE

        brut = CHEMIN_MANIFESTE.read_text(encoding="utf-8")
        json.loads(brut)  # lève si invalide

        assert "\n" in brut, "manifeste minifié : illisible en revue de diff"


@pytest.mark.parametrize("champ", ["id", "famille", "textes", "maturite", "audience"])
def test_chaque_capacite_porte_les_champs_obligatoires(champ):
    for capacite in _charger()["capacites"]:
        assert champ in capacite, f"« {capacite.get('id')} » sans champ {champ}"


class TestLAideEstDeriveeDuManifeste:
    """Premier consommateur visible du manifeste (0.44).

    La réponse de `/aide` énumérait des expressions brutes — `{action: ouvrir
    memoire}` — sans jamais dire ce qu'on ouvre ni à quoi ça sert. Un nouvel
    utilisateur y lisait une liste d'identifiants, pas une aide.

    Le manifeste porte précisément ce qui manquait : le nom lisible et la
    description de chaque capacité. L'aide les affiche désormais, DÉRIVÉS du
    manifeste — la table des cibles reste l'autorité sur ce qui s'exécute, le
    manifeste devient l'autorité sur ce qui se dit. Ajouter une capacité au
    manifeste enrichit l'aide sans toucher une seconde liste.
    """

    def test_chaque_destination_porte_son_nom_lisible(self):
        from app.services.capacites import capacites, texte
        from app.services.chat_actions import available_actions_text

        aide = available_actions_text()

        for capacite in capacites():
            a_une_vue = any(
                p["binding"]["registre"] == "vue"
                for p in _points_de(capacite)
            )
            if not a_une_vue:
                continue
            nom = texte(capacite, "nom")
            assert nom in aide, (
                f"l'aide ne nomme pas « {nom} » : l'utilisateur voit une "
                "expression brute sans savoir ce qu'elle ouvre"
            )

    def test_aucune_destination_existante_n_est_perdue(self):
        """Le verrou de migration : dériver ne doit rien faire disparaître."""
        from app.services.chat_actions import NAVIGATION_TARGETS, available_actions_text

        aide = available_actions_text()

        # Une cible par action (les alias comme « factures/facturation »
        # partagent la même action : une seule doit apparaître, comme avant).
        actions_affichees = set()
        for cible, (action_id, _) in NAVIGATION_TARGETS.items():
            if f"ouvrir {cible}" in aide:
                actions_affichees.add(action_id)

        toutes_les_actions = {a for a, _ in NAVIGATION_TARGETS.values()}
        perdues = toutes_les_actions - actions_affichees
        assert perdues == set(), (
            f"les destinations {perdues} ont disparu de l'aide à la migration"
        )

    def test_les_productions_et_variables_restent_annoncees(self):
        """L'aide ne se réduit pas à la navigation : le reste survit."""
        from app.services.chat_actions import available_actions_text

        aide = available_actions_text()

        assert "produire" in aide
        assert "variable" in aide


def _points_de(capacite):
    from app.services.capacites import points_entree

    ids = set(capacite.get("entrees", []))
    return [p for p in points_entree() if p["id"] in ids]


@pytest.fixture(autouse=True)
def _purger_le_cache_du_manifeste():
    """Le cache est un état de module : chaque test repart du fichier réel.

    Sans cette purge, un test qui monkeypatche le chemin laisse son manifeste
    aux tests suivants — la dissociation même que l'empreinte doit détecter.
    """
    from app.services.capacites import charger_manifeste

    charger_manifeste.cache_clear()
    yield
    charger_manifeste.cache_clear()


class TestLEmpreinteDetecteLesGenerationsDivergentes:
    """Le manifeste vit en deux exemplaires : bundle frontend et binaire sidecar.

    Ils viennent du même fichier canonique, mais rien ne garantit qu'un
    frontend et un sidecar packagés à des moments différents en portent la
    même version. Le design V2 l'exige : « un frontend et un sidecar issus de
    deux générations différentes doivent le dire, pas diverger en silence ».

    L'empreinte rend la divergence détectable : le frontend interroge le
    backend au démarrage et compare avec la sienne.
    """

    def test_l_empreinte_derive_du_contenu(self, tmp_path, monkeypatch):
        from app.services import capacites as module

        fichier = tmp_path / "capacites.json"
        fichier.write_text(
            '{"schema": 1, "capacites": [{"id": "a", "entrees": []}], "points_entree": []}',
            encoding="utf-8",
        )
        monkeypatch.setattr(module, "CHEMIN_MANIFESTE", fichier)
        module.charger_manifeste.cache_clear()

        premiere = module.empreinte_manifeste()
        fichier.write_text(
            '{"schema": 1, "capacites": [{"id": "b", "entrees": []}], "points_entree": []}',
            encoding="utf-8",
        )
        module.charger_manifeste.cache_clear()
        seconde = module.empreinte_manifeste()

        assert premiere != seconde, (
            "l'empreinte ne change pas quand le contenu change : elle ne "
            "détecterait jamais une divergence de génération"
        )
        assert len(premiere) >= 16, "empreinte trop courte pour être fiable"

    def test_un_manifeste_illisible_a_une_empreinte_dite(self, tmp_path, monkeypatch):
        """Fail-open cohérent avec le chargement : signaler, pas planter."""
        from app.services import capacites as module

        monkeypatch.setattr(module, "CHEMIN_MANIFESTE", tmp_path / "absent.json")
        module.charger_manifeste.cache_clear()

        assert module.empreinte_manifeste() == "absent"

        casse = tmp_path / "casse.json"
        casse.write_text("{pas du json", encoding="utf-8")
        monkeypatch.setattr(module, "CHEMIN_MANIFESTE", casse)
        module.charger_manifeste.cache_clear()

        assert module.empreinte_manifeste() == "absent", (
            "un manifeste illisible doit produire une empreinte sentinelle "
            "explicite, pas une exception au démarrage"
        )

    @pytest.mark.asyncio
    async def test_le_backend_expose_schema_et_empreinte(self, client):
        """C'est la moitié backend du contrôle ; le frontend compare."""
        reponse = await client.get("/api/config/capacites")

        assert reponse.status_code == 200
        corps = reponse.json()
        assert corps["schema"] >= 1
        assert len(corps["empreinte"]) >= 16
        assert corps["nombre_capacites"] > 0
