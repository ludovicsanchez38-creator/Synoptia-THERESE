"""L'aide annonce le chemin RÉEL d'une capacité, pas le plus long.

Depuis le 26/08/2026, « Décider » est une puce de l'accueil : l'aide qui
enverrait encore l'utilisateur dans « Plus d'outils » lui ferait faire un
détour, et le manifeste mentirait par omission sur les portes existantes.
C'est la classe de défaut que le manifeste 0.44 devait supprimer.
"""

from app.services.capacites import acces_principal
from app.services.chat_actions import available_actions_text


class TestAideAnnonceLEtabli:
    def test_le_board_est_annonce_par_l_accueil(self) -> None:
        lignes = available_actions_text().split("\n")

        assert any(
            "Accueil" in ligne and "Décision" in ligne for ligne in lignes
        ), "l'aide n'annonce pas le chemin de l'accueil pour le Board"

    def test_le_board_n_est_plus_annonce_comme_range_au_tiroir(self) -> None:
        lignes = available_actions_text().split("\n")

        assert not any(
            "Plus d'outils" in ligne and "Décision" in ligne for ligne in lignes
        ), "l'aide envoie encore au tiroir alors qu'une puce existe à l'accueil"

    def test_les_autres_capacites_du_tiroir_gardent_leur_chemin(self) -> None:
        """Le changement ne doit valoir QUE pour le Board."""
        lignes = available_actions_text().split("\n")

        for nom in ("Connecteurs", "Images", "Calculateurs"):
            assert any(
                "Plus d'outils" in ligne and nom in ligne for ligne in lignes
            ), f"{nom} a perdu son chemin d'aide"

    def test_l_acces_principal_du_board_est_l_etabli(self) -> None:
        principal = acces_principal("board")

        assert principal is not None
        assert principal["binding"]["registre"] == "scenario"
        assert principal["binding"]["scenarioId"] == "board"
