# Mises à jour automatiques (updater Tauri) — US-007

THÉRÈSE se met à jour toute seule via le plugin updater de Tauri 2, **sans
certificat de signature de code** (Apple Developer ID / Windows Authenticode).
Les artefacts de mise à jour sont signés par une clé **minisign** dédiée
(différente d'un certificat d'éditeur : elle prouve juste que la mise à jour
vient bien de nous, elle ne supprime pas l'avertissement Gatekeeper / SmartScreen
au premier lancement).

## Comment ça marche

```
tag v* poussé
   │
   ▼
GitHub Actions (release.yml)
   ├─ build 3 OS (macOS .app.tar.gz, Windows NSIS .zip, Linux .deb)
   ├─ --config src-tauri/updater-ci.conf.json → createUpdaterArtifacts=true
   │    (activé SEULEMENT en CI : les builds locaux `make build` ne sont pas
   │     impactés et n'ont pas besoin de la clé)
   ├─ génère les .sig signés avec la clé privée
   └─ tauri-action assemble et publie latest.json (asset de la release)
   │
   ▼
/release-therese (skill, local)
   └─ télécharge latest.json de la release et le rsync vers
      ubuntu@54.37.230.8:/var/www/synoptia.fr/therese/alpha/latest.json
   │
   ▼
App installée
   └─ UpdateBanner interroge https://synoptia.fr/therese/alpha/latest.json
      vérifie la signature avec la clé PUBLIQUE (dans tauri.conf.json),
      télécharge et installe.
```

L'endpoint est sur **synoptia.fr** et pas sur `releases/latest/download/` parce
que GitHub fait pointer `/releases/latest/` uniquement sur la dernière release
**stable** (ni draft, ni prerelease). Toutes les versions THÉRÈSE étant des
`-alpha` (prerelease), cette URL renvoyait toujours un 404 : c'était la cause du
canal de mise à jour cassé.

## Clés

- **Clé publique** : committée dans `src/frontend/src-tauri/tauri.conf.json`
  (`plugins.updater.pubkey`). Publique par nature.
- **Clé privée + mot de passe** : générées hors du dépôt, dans
  `~/.therese-signing/` sur le Mac de Ludo :
  - `~/.therese-signing/therese-updater.key` (clé privée chiffrée)
  - `~/.therese-signing/password.txt` (mot de passe de la clé)
  - `~/.therese-signing/therese-updater.key.pub` (copie de la clé publique)

> **À sauvegarder précieusement.** Si la clé privée OU le mot de passe sont
> perdus, on ne peut plus signer de mises à jour vérifiables par les apps déjà
> installées : il faudrait régénérer une paire, changer la `pubkey`, et les
> utilisateurs devraient réinstaller à la main. Garder une copie chiffrée hors
> du Mac (gestionnaire de mots de passe / coffre).

## Secrets GitHub à poser (PRÉREQUIS avant la prochaine release)

Tant que ces deux secrets ne sont pas posés, le build de release **échoue
volontairement et tôt** (job `preflight`), avec un message clair. C'est normal :
en CI, `--config src-tauri/updater-ci.conf.json` active `createUpdaterArtifacts`,
qui exige la clé privée au moment du bundling. (Les builds locaux ne chargent pas
ce `--config`, donc ils ne sont pas concernés.)

Depuis le Mac, dans le dépôt :

```bash
gh secret set TAURI_SIGNING_PRIVATE_KEY \
  --repo ludovicsanchez38-creator/Synoptia-THERESE \
  < ~/.therese-signing/therese-updater.key

gh secret set TAURI_SIGNING_PRIVATE_KEY_PASSWORD \
  --repo ludovicsanchez38-creator/Synoptia-THERESE \
  < ~/.therese-signing/password.txt
```

(ou Settings → Secrets and variables → Actions → New repository secret).

## Limites connues (sans certificat de signature de code)

- **macOS** : la mise à jour s'installe, mais l'app reste seulement signée
  ad-hoc (pas notarisée). Au premier lancement d'une version mise à jour,
  Gatekeeper peut encore demander une confirmation. La notarisation
  (suppression de l'avertissement) nécessite un compte Apple Developer — c'est
  la 2ᵉ moitié d'US-007, volontairement reportée.
- **Windows** : l'updater NSIS fonctionne. SmartScreen peut encore avertir tant
  qu'il n'y a pas de certificat Authenticode.
- **Linux** : pas d'auto-update. Le bundle `.deb` n'est pas un format updater
  Tauri (seul l'AppImage le serait). Les utilisateurs Linux mettent à jour via
  `sudo dpkg -i`. Aucun artefact updater Linux n'est généré, c'est attendu.

## Test bout-en-bout N → N+1

1. Poser les 2 secrets (ci-dessus).
2. Release `vN` via `/release-therese`, installer l'app `vN`.
3. Release `vN+1` via `/release-therese` (latest.json publié sur synoptia.fr).
4. Ouvrir l'app `vN` : sous 5 s puis toutes les 6 h, `UpdateBanner` doit
   proposer `vN+1`. Cliquer « Installer maintenant » → téléchargement →
   « Redémarrer pour installer ».
