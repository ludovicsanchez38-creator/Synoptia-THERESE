#!/usr/bin/env python3
"""Notes du brouillon de release, selon que les installeurs sont signés ou non.

MACOS_SIGNE et WINDOWS_SIGNE (« true » ou « false ») sont calculés dans
release.yml à partir de la seule présence des secrets. Sans signature, les
textes sont exactement ceux des releases précédentes.
"""
import argparse
import os
from pathlib import Path

COMMUNES = (
    "- **IMPORTANT (depuis 0.23)** : au premier lancement, ta base de données est chiffrée (SQLCipher). "
    "Une version antérieure à 0.23 ne pourra plus la lire : ne reviens pas en arrière après ce premier lancement. "
    "Tes backups (Paramètres → Données) contiennent tout ce qu'il faut pour restaurer, y compris la clé - "
    "protège ces fichiers comme la base elle-même.",
    "- **Mises à jour automatiques (depuis 0.23)** : l'app vérifie les nouvelles versions au lancement puis "
    "toutes les 6 h et propose l'installation en un clic.",
)
MACOS = {
    True: "- **macOS** : app signée par son éditeur et notarisée par Apple. Ouvre le DMG, glisse THÉRÈSE dans "
          "Applications, puis lance-la normalement.",
    False: "- **macOS** : Clic droit → Ouvrir → Confirmer (app non signée). Si le backend ne démarre pas, ouvre le "
           "Terminal et lance : `xattr -cr /Applications/THERESE.app` puis relance l'app.",
}
WINDOWS = {
    True: "- **Windows** : installeur signé par son éditeur. Si SmartScreen affiche encore « Windows a protégé "
          "votre ordinateur », vérifie que l'éditeur indiqué est bien le nôtre, puis « Informations "
          "complémentaires » → « Exécuter quand même ».",
    False: "- **Windows** : Exclure l'app de l'antivirus si faux positif PyInstaller",
}
LINUX = "- **Linux** : Installer avec `sudo dpkg -i therese_*.deb`"


def oui(value):
    return str(value or '').strip().lower() == 'true'


def body(tag, macos_signe, windows_signe):
    lines = [f'## THÉRÈSE {tag}', '', 'Installeurs disponibles ci-dessous.', '', '### Notes',
             *COMMUNES, MACOS[bool(macos_signe)], WINDOWS[bool(windows_signe)], LINUX]
    return '\n'.join(lines) + '\n'


def body_from_env(values=os.environ):
    return body(values['RELEASE_TAG'], oui(values.get('MACOS_SIGNE')), oui(values.get('WINDOWS_SIGNE')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sortie', type=Path, required=True)
    args = parser.parse_args()
    args.sortie.parent.mkdir(parents=True, exist_ok=True)
    args.sortie.write_text(body_from_env(), encoding='utf-8')


if __name__ == '__main__':
    main()
