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
