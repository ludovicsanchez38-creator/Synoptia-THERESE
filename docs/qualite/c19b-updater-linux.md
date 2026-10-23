# B-1111 — contrôle du contenu AppImage dans le plugin updater

Le lock de THÉRÈSE reste sur `tauri-plugin-updater 2.10.0`. Il n'est pas
modifié dans C19-B : cette machine ne dispose ni de Cargo ni de rustc.

La première version publiée qui contrôle le contenu avant de toucher
l'AppImage installé est **2.14.0**, publiée le 14 octobre 2026.
La [release officielle](https://github.com/tauri-apps/plugins-workspace/releases/tag/updater-v2.14.0)
et le [correctif f2af373b](https://github.com/tauri-apps/plugins-workspace/commit/f2af373b6a04b11c1c06fea7bad8636b3cada5a3)
documentent cette protection.

Dans les tags officiels 2.10.0, 2.11.0, 2.12.0 et
[2.13.0](https://github.com/tauri-apps/plugins-workspace/blob/updater-v2.13.0/plugins/updater/src/updater.rs),
`install_appimage` ne vérifie pas ELF. Dans
[2.14.0, lignes 1137–1149](https://github.com/tauri-apps/plugins-workspace/blob/updater-v2.14.0/plugins/updater/src/updater.rs#L1137),
le contrôle précède la création des répertoires temporaires et la manipulation
du binaire installé : un contenu brut qui n'est pas ELF est refusé avec
`InvalidUpdaterFormat`. Le chemin compressé gzip est traité séparément et
nécessite la fonctionnalité `zip` du plugin. Un ELF arbitraire n'est pas une
preuve qu'un fichier est un AppImage valide ; la signature reste nécessaire.

Depuis la racine du dépôt, en CI ou sur le Mac équipé de Rust :

```bash
cargo update --manifest-path src/frontend/src-tauri/Cargo.toml -p tauri-plugin-updater --precise 2.14.0
cargo check --locked --manifest-path src/frontend/src-tauri/Cargo.toml
```

Faire relire le lock généré et compiler les trois cibles de release. Ces
commandes n'ont pas été exécutées ici. Aucune validation d'installation Rust
N vers N+1 n'est revendiquée.

La recette Linux du plugin, à exécuter sur un binaire jetable avec le vrai
plugin mis à niveau, doit couvrir au moins ces dix contenus :

| Contenu | Vérification attendue |
| --- | --- |
| Archive `.deb` commençant par `!<arch>` | Refus, exécutable installé inchangé |
| Archive RPM | Refus, exécutable installé inchangé |
| Page HTML renvoyée par un miroir | Refus, exécutable installé inchangé |
| JSON de réponse d'erreur | Refus, exécutable installé inchangé |
| Fichier vide | Refus, exécutable installé inchangé |
| En-tête ELF tronqué | Pas d'installation réussie revendiquée |
| AppImage ELF valide signé | Installation et redémarrage à qualifier |
| AppImage avec signature invalide | Refus avant installation |
| AppImage gzip, fonctionnalité `zip` activée | Extraction et installation à qualifier |
| AppImage gzip, fonctionnalité `zip` désactivée | Refus avant modification de l'installation |

Ces dix cas sont une recette restante, **pas dix essais Rust exécutés**.
L'audit des sources est distinct des tests pytest du manifeste et des tests
Vitest du bandeau, qui s'exécutent localement avec des doubles.
