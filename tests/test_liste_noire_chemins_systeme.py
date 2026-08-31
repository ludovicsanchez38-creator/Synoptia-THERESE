"""La liste noire des répertoires système doit vraiment refuser.

Trouvé le 31/08/2026 par la boucle d'amélioration, puis confirmé en appelant
la fonction : `validate_file_path("/etc/passwd")` renvoyait le chemin au lieu
de lever. La liste noire compare des préfixes littéraux (`/etc`, `/var`) au
chemin APRÈS `resolve()`. Or sur macOS `/etc` se résout en `/private/etc` et
`/var` en `/private/var` : plus aucune entrée ne peut correspondre.

La protection était donc inerte sur la plateforme de développement et de
livraison principale, et aucun test ne la couvrait. Celui qui semblait le
faire, `test_garde_path_traversal.py`, porte sur une autre fonction.
"""

import pytest
from app.services.path_security import DENIED_ABSOLUTE_PATHS, validate_file_path


@pytest.mark.parametrize(
    "cible",
    ["/etc/passwd", "/etc/hosts", "/var/log/system.log", "/usr/bin/env"],
)
def test_un_fichier_systeme_est_refuse(cible: str):
    """Le refus doit primer, mais seulement sur un fichier qui existe.

    31/08, apres un echec de CI : `validate_file_path` verifie l'existence
    AVANT la liste noire, et `/var/log/system.log` n'existe que sur macOS.
    Sur Linux le test recevait donc FileNotFoundError au lieu du refus. Un
    chemin propre a une plateforme n'a rien a faire dans un test qui tourne
    sur les deux : on ignore ce qui est absent ici.
    """
    from pathlib import Path as _Path

    if not _Path(cible).exists():
        pytest.skip(f"{cible} absent de cette plateforme")
    with pytest.raises(PermissionError):
        validate_file_path(cible, None)


@pytest.mark.parametrize("racine", DENIED_ABSOLUTE_PATHS)
def test_chaque_racine_interdite_est_refusee_sous_sa_forme_resolue(racine: str):
    """Le refus ne doit pas dépendre de la façon d'écrire le chemin.

    `/etc` et `/private/etc` désignent le même répertoire sur macOS : refuser
    l'un et autoriser l'autre ne protège de rien.
    """
    from pathlib import Path

    chemin = Path(racine)
    if not chemin.exists():
        pytest.skip(f"{racine} absent de cette plateforme")
    resolu = chemin.resolve()
    with pytest.raises(PermissionError):
        validate_file_path(str(chemin), None)
    if str(resolu) != racine:
        with pytest.raises(PermissionError):
            validate_file_path(str(resolu), None)


def test_un_fichier_ordinaire_reste_autorise(tmp_path):
    """Aucun sur-blocage : la correction ne doit pas fermer le cas normal."""
    fichier = tmp_path / "note.md"
    fichier.write_text("# Titre", encoding="utf-8")
    assert validate_file_path(str(fichier), None) == fichier.resolve()
