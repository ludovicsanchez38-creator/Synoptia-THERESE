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
    """Le refus doit primer, qu'il s'agisse d'un fichier present ou absent.

    Historique : ce test contournait par un `pytest.skip` le fait que
    `validate_file_path` verifiait l'existence AVANT la liste noire
    (`/var/log/system.log` n'existe que sur macOS, la CI Linux recevait donc
    FileNotFoundError au lieu du refus). Le contournement masquait le defaut
    au lieu de le corriger : B-037 remet l'existence en dernier, le skip n'a
    donc plus lieu d'etre et le refus vaut sur les deux plateformes.
    """
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


# ============================================================
# B-037 : la liste noire doit primer sur la vérification d'existence
# ============================================================


@pytest.mark.parametrize(
    "cible",
    [
        "/etc/absent_xyz_b037",
        "/usr/absent_xyz_b037",
        "/var/db/absent_xyz_b037",
        "~/.ssh/id_absent_b037",
        "~/.aws/credentials_absent_b037",
    ],
)
def test_la_liste_noire_prime_sur_lexistence(cible: str):
    """Un chemin interdit ABSENT doit être refusé comme un chemin interdit présent.

    Trouvé le 02/09/2026 : l'existence était vérifiée AVANT les trois gardes.
    Deux erreurs différentes distinguaient donc « existe mais interdit » de
    « n'existe pas » à l'intérieur même de la zone interdite - un oracle
    d'existence qui permet d'énumérer ~/.ssh sans jamais lire un fichier.
    """
    with pytest.raises(PermissionError):
        validate_file_path(cible, None)


def test_un_motif_sensible_absent_est_refuse_sans_dire_qu_il_manque(tmp_path):
    """Même règle pour la garde par motif de nom, y compris hors zone système.

    Le dossier temporaire échappe volontairement à la liste des racines
    système : la garde éprouvée ici est donc bien celle des motifs de fichiers
    (`*.pem`), pas celle des répertoires.
    """
    with pytest.raises(PermissionError):
        validate_file_path(str(tmp_path / "cle_absente_b037.pem"), None)


@pytest.mark.parametrize(
    "cible",
    ["/etc/absent_xyz_b037", "~/.ssh/id_absent_b037"],
)
def test_le_refus_ne_divulgue_pas_le_chemin_resolu(cible: str):
    """Le message d'un refus ne dit rien du système de fichiers.

    La branche précoce rendait `Fichier non trouvé : /Users/<utilisateur>/...`,
    divulguant le chemin absolu résolu et le nom du dossier personnel.
    """
    from pathlib import Path

    with pytest.raises(PermissionError) as capture:
        validate_file_path(cible, None)
    message = str(capture.value)
    assert str(Path.home()) not in message
    assert "absent_xyz_b037" not in message
    assert "id_absent_b037" not in message
