#!/usr/bin/env python3
"""B-1111 : préparer un manifeste updater sûr avant toute publication."""

import argparse
import copy
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit


def nettoyer_manifeste(manifeste: dict) -> dict:
    """Retire les alias .deb et refuse tout autre générique Linux non AppImage."""
    resultat = copy.deepcopy(manifeste)
    plateformes = resultat.get("platforms")
    if not isinstance(plateformes, dict):
        raise ValueError("Le manifeste doit contenir platforms")
    for cible, paquet in list(plateformes.items()):
        if not re.fullmatch(r"linux-[^-]+", cible):
            continue
        url = paquet.get("url", "") if isinstance(paquet, dict) else ""
        chemin = unquote(urlsplit(url).path).lower()
        if chemin.endswith(".deb"):
            del plateformes[cible]
        elif not chemin.endswith(".appimage"):
            raise ValueError(f"{cible} doit désigner un AppImage ; publication refusée")
    return resultat


def construire_manifeste(release: dict, signatures: Path, version: str) -> dict:
    """Assemble les trois cibles de la matrice release, sans alias Linux .deb.

    Les builds publient seulement les artefacts. Un job unique assemble le
    manifeste après la matrice pour éviter toute publication transitoire ou
    perte d'une plateforme par concurrence entre les builds.
    """
    plateformes = {}
    assets = {asset["name"]: asset for asset in release["assets"]}
    cibles = {
        ".app.tar.gz": ("darwin-aarch64", "darwin-aarch64-app"),
        ".exe": ("windows-x86_64", "windows-x86_64-nsis"),
        ".msi": ("windows-x86_64", "windows-x86_64-msi"),
        ".deb": ("linux-x86_64-deb",),
    }
    for extension, noms in cibles.items():
        paquets = [a for nom, a in assets.items() if nom.endswith(extension)]
        if len(paquets) != 1:
            raise ValueError(f"Un unique artefact {extension} est requis par la matrice release")
        asset = paquets[0]
        signature = signatures / (asset["name"] + ".sig")
        if signature.name not in assets or not signature.is_file() or not signature.read_text().strip():
            raise ValueError(f"Signature manquante pour {asset['name']}")
        url = re.sub(
            r"/download/untagged-[^/]+/", f"/download/{quote(release['tagName'], safe='')}/", asset["url"],
        )
        for cible in noms:
            plateformes[cible] = {"url": url, "signature": signature.read_text().strip()}
    return nettoyer_manifeste({
        "version": version, "notes": release.get("body") or "",
        "pub_date": release.get("publishedAt") or datetime.now(timezone.utc).isoformat(),
        "platforms": plateformes,
    })


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifeste", type=Path)
    parser.add_argument("--release-assets", type=Path)
    parser.add_argument("--signatures", type=Path)
    parser.add_argument("--version")
    args = parser.parse_args()
    try:
        if args.release_assets:
            if not args.signatures or not args.version:
                parser.error("--release-assets exige --signatures et --version")
            resultat = construire_manifeste(json.loads(args.release_assets.read_text()), args.signatures, args.version)
        else:
            resultat = nettoyer_manifeste(json.loads(args.manifeste.read_text()))
        # Toutes les validations précèdent l'écriture, y compris en mode nettoyage.
        args.manifeste.write_text(json.dumps(resultat, ensure_ascii=False, indent=2) + "\n")
    except (OSError, ValueError, TypeError, KeyError) as erreur:
        parser.exit(1, f"Manifeste updater refusé : {erreur}\n")


if __name__ == "__main__":
    main()
