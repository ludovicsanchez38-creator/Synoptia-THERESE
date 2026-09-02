"""La liste noire des répertoires système doit vraiment refuser.

Trouvé le 31/08/2026 par la boucle d'amélioration, puis confirmé en appelant
la fonction : `validate_file_path("/etc/passwd")` renvoyait le chemin au lieu
de lever. La liste noire compare des préfixes littéraux (`/etc`, `/var`) au
chemin APRÈS `resolve()`. Or sur macOS `/etc` se résout en `/private/etc` et
`/var` en `/private/var` : plus aucune entrée ne peut correspondre.

La protection était donc inerte sur la plateforme de développement et de
livraison principale, et aucun test ne la couvrait. Celui qui semblait le
faire, `test_garde_path_traversal.py`, porte sur une autre fonction.

B-255 (02/09/2026) : le même fichier était rouge sur windows-latest (run
33668043946, huit échecs), pour DEUX causes distinctes.
1. Les racines n'étaient que POSIX. Sous Windows `Path("/etc/hosts").resolve()`
   donne `C:\\etc\\hosts`, qui ne désigne aucun répertoire système.
2. Plus profond : la comparaison écrivait le séparateur en dur
   (`startswith(racine + "/")`). Sous Windows, `C:\\etc\\hosts` ne commence
   jamais par `C:\\etc/` — aucun FICHIER sous une racine interdite ne pouvait
   donc correspondre, seule la racine elle-même par égalité. C'est pourquoi
   `test_chaque_racine_interdite_...` passait pendant que ses enfants
   échouaient, et pourquoi ajouter des racines Windows SANS corriger ce point
   les aurait laissées inertes.

D'où la forme de ce fichier : les cibles réelles sont choisies par plateforme
(elles s'exécutent pour de vrai sur le runner Windows), et ce qui n'est pas
exécutable ici — la branche Windows de la construction des racines, la
comparaison de chemins Windows — se vérifie sur n'importe quel OS via
`PureWindowsPath` et un environnement simulé.
"""

import os
from pathlib import Path, PurePosixPath, PureWindowsPath

import pytest
from app.services.path_security import DENIED_ABSOLUTE_PATHS, validate_file_path

_SOUS_WINDOWS = os.name == "nt"

# Fichiers système qui existent sur la plateforme courante (ou qui pourraient
# exister) : le refus doit tomber avant toute question d'existence.
CIBLES_SYSTEME_PRESENTES = (
    [
        r"C:\Windows\System32\drivers\etc\hosts",
        r"C:\Windows\System32\config",
        r"C:\Windows\explorer.exe",
    ]
    if _SOUS_WINDOWS
    else ["/etc/passwd", "/etc/hosts", "/var/log/system.log", "/usr/bin/env"]
)

# Chemins ABSENTS à l'intérieur de la zone interdite (B-037).
CIBLES_SYSTEME_ABSENTES = (
    [
        r"C:\Windows\absent_xyz_b255",
        r"C:\Windows\System32\absent_xyz_b255",
        r"C:\ProgramData\absent_xyz_b255",
    ]
    if _SOUS_WINDOWS
    else ["/etc/absent_xyz_b037", "/usr/absent_xyz_b037", "/var/db/absent_xyz_b037"]
)

# Ces deux-là valent sur les deux plateformes : la garde du home compare un
# chemin RELATIF au home, elle n'a jamais dépendu du séparateur ni des racines
# système. Preuve : sur le run Windows rouge, aucun des cas `~/` n'échouait.
CIBLES_HOME_ABSENTES = ["~/.ssh/id_absent_b037", "~/.aws/credentials_absent_b037"]


@pytest.mark.parametrize("cible", CIBLES_SYSTEME_PRESENTES)
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


@pytest.mark.parametrize("cible", CIBLES_SYSTEME_ABSENTES + CIBLES_HOME_ABSENTES)
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


@pytest.mark.parametrize("cible", [CIBLES_SYSTEME_ABSENTES[0], CIBLES_HOME_ABSENTES[0]])
def test_le_refus_ne_divulgue_pas_le_chemin_resolu(cible: str):
    """Le message d'un refus ne dit rien du système de fichiers.

    La branche précoce rendait `Fichier non trouvé : /Users/<utilisateur>/...`,
    divulguant le chemin absolu résolu et le nom du dossier personnel.
    """
    with pytest.raises(PermissionError) as capture:
        validate_file_path(cible, None)
    message = str(capture.value)
    assert str(Path.home()) not in message
    # Le nom demandé ne doit pas revenir dans le message : le confirmer, c'est
    # déjà répondre « ce chemin-là, je l'ai regardé ».
    assert Path(cible).name not in message


# ============================================================
# B-255 : les deux causes du rouge Windows, vérifiables depuis n'importe quel OS
# ============================================================


def test_les_racines_windows_sortent_de_lenvironnement():
    """Branche `nt` de la construction des racines, simulée depuis un Mac.

    Rouge avant B-255 : la fonction n'existait pas, il n'y avait qu'une liste
    POSIX littérale.
    """
    from app.services.path_security import _racines_systeme

    racines = _racines_systeme(
        "nt", {"SystemRoot": r"C:\Windows", "ProgramData": r"C:\ProgramData"}
    )

    assert r"C:\Windows" in racines
    assert r"C:\Windows\System32" in racines
    assert r"C:\ProgramData" in racines
    # Une racine POSIX ne protège rien sous Windows : `C:\etc` n'est pas
    # `/etc`. La garder donnerait l'illusion d'une couverture.
    assert "/etc" not in racines


def test_un_windows_installe_ailleurs_est_suivi():
    """`SystemRoot` fait foi : une installation hors `C:` reste couverte."""
    from app.services.path_security import _racines_systeme

    racines = _racines_systeme(
        "nt", {"SystemRoot": r"D:\WinNT", "ProgramData": r"E:\Donnees\ProgramData"}
    )

    assert r"D:\WinNT" in racines
    assert r"D:\WinNT\System32" in racines
    assert r"E:\Donnees\ProgramData" in racines
    # Les valeurs par défaut restent : un environnement déplacé ne rouvre pas
    # le dossier Windows d'origine.
    assert r"C:\Windows" in racines


def test_windir_et_systemroot_ne_font_qu_une_racine():
    """Le cas ORDINAIRE d'un Windows : les deux variables disent la même chose.

    `windir` et `SystemRoot` valent tous deux `C:\\Windows` sur une machine
    standard, à la casse près. Sans dédoublonnage insensible à la casse, la
    liste porterait trois fois la même racine — sans faille, mais la garde
    deviendrait illisible et la troisième variable, jamais éprouvée.
    """
    from app.services.path_security import _racines_systeme

    racines = _racines_systeme("nt", {"SystemRoot": r"C:\Windows", "windir": r"C:\WINDOWS"})

    assert r"C:\Windows" in racines
    assert [r for r in racines if r.casefold() == r"c:\windows"] == [r"C:\Windows"]
    assert [r for r in racines if r.casefold() == r"c:\windows\system32"] == [
        r"C:\Windows\System32"
    ]


def test_un_environnement_windows_vide_garde_les_racines_par_defaut():
    """Une variable absente ne relâche jamais la garde."""
    from app.services.path_security import _racines_systeme

    racines = _racines_systeme("nt", {})

    assert r"C:\Windows" in racines
    assert r"C:\Windows\System32" in racines
    assert r"C:\ProgramData" in racines


def test_une_racine_windows_degeneree_est_ecartee():
    """`SystemRoot=C:\\` interdirait le disque entier : ce n'est plus une garde.

    Une garde qui refuse tout est une panne, pas une protection : le cas est
    écarté, les racines par défaut suffisent.
    """
    from app.services.path_security import _racines_systeme

    racines = _racines_systeme("nt", {"SystemRoot": "C:\\", "ProgramData": "  "})

    assert "C:" not in racines
    assert r"C:\Windows" in racines


def test_les_racines_posix_restent_celles_dunix():
    """L'autre branche ne bouge pas : la plateforme principale est intouchée."""
    from app.services.path_security import DENIED_ABSOLUTE_PATHS_POSIX, _racines_systeme

    assert _racines_systeme("posix", {}) == tuple(DENIED_ABSOLUTE_PATHS_POSIX)


def test_la_liste_resolue_demande_les_racines_de_la_plateforme(monkeypatch):
    """Le lien entre les deux fonctions : `_racines_interdites` ne code plus
    aucune liste en dur, elle demande celle de la plateforme courante.

    Simuler la bascule en monkeypatchant `os.name` lui-même est impossible
    ici : `pathlib.Path()` choisit sa saveur sur `os.name`, et un `"nt"`
    simulé fait lever `cannot instantiate 'WindowsPath' on your system` à la
    première résolution (constaté en écrivant ce test). Le point d'injection
    est donc la fonction, pas la variable — la branche Windows elle-même est
    couverte par les quatre tests de `_racines_systeme` ci-dessus.

    Rouge avant B-255 : `_racines_systeme` n'existait pas, la liste POSIX
    était lue en dur quelle que soit la plateforme.
    """
    from app.services import path_security as ps

    appels: list[tuple[str, bool]] = []

    def faux_racines(nom_os: str, environnement) -> tuple[str, ...]:
        appels.append((nom_os, environnement is os.environ))
        return ("/racine_simulee_b255",)

    monkeypatch.setattr(ps, "_racines_systeme", faux_racines)
    ps._racines_interdites.cache_clear()
    try:
        racines = ps._racines_interdites()
    finally:
        # Le cache est partagé par tout le processus : le laisser peuplé de
        # racines simulées ferait mentir chaque test suivant.
        ps._racines_interdites.cache_clear()

    # La plateforme ET l'environnement VIVANTS sont transmis : une liste
    # figée à l'import ne suivrait pas un `SystemRoot` déplacé.
    assert appels == [(os.name, True)]
    assert "/racine_simulee_b255" in racines


@pytest.mark.parametrize(
    "cible",
    [
        r"C:\Windows\System32\drivers\etc\hosts",
        r"C:\Windows\System32",
        r"C:\Windows",
        # La casse ne distingue pas deux chemins Windows.
        r"c:\windows\system32\config\SAM",
    ],
)
def test_un_chemin_windows_sous_une_racine_est_reconnu(cible: str):
    """Le séparateur ne doit plus être écrit en dur.

    Rouge avant B-255 : la comparaison `startswith(racine + "/")` rendait faux
    sur chacun de ces chemins, donc laissait passer tout le contenu de
    `C:\\Windows`.
    """
    from app.services.path_security import _sous_une_racine

    assert _sous_une_racine(PureWindowsPath(cible), [PureWindowsPath(r"C:\Windows")])


@pytest.mark.parametrize(
    "cible",
    [
        # Le voisin de nom, jumeau Windows de `/etcetera` face à `/etc`.
        r"C:\WindowsApps\jeu.exe",
        r"C:\Users\jean\Documents\note.md",
        r"D:\Windows\autre.txt",
    ],
)
def test_un_voisin_de_racine_windows_nest_pas_reconnu(cible: str):
    """Comparer des composants, pas des préfixes de chaîne : pas de sur-blocage."""
    from app.services.path_security import _sous_une_racine

    assert not _sous_une_racine(PureWindowsPath(cible), [PureWindowsPath(r"C:\Windows")])


def test_le_voisin_de_nom_posix_reste_autorise():
    """Le jumeau POSIX de la garde ci-dessus : `/etcetera` n'est pas `/etc`."""
    from app.services.path_security import _sous_une_racine

    racines = [PurePosixPath("/etc")]
    assert _sous_une_racine(PurePosixPath("/etc/hosts"), racines)
    assert not _sous_une_racine(PurePosixPath("/etcetera/hosts"), racines)
