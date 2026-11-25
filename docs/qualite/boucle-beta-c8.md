# THÉRÈSE 0.85.0 · Cycle 8

La construction à blanc `45663607380` a construit et vérifié macOS. L’inventaire natif a arrêté Linux et Windows sur quatre empreintes hors catalogue. Le relevé `45670187545` a fourni les quatre fichiers à examiner.

- **Linux**. `libmvec.so.1` correspond octet pour octet au membre de `libc6 2.35-0ubuntu3.18` pour Jammy amd64. La notice est identique. Les index Ubuntu signés et le `.dsc` concordent sur les quatre fichiers du paquet source `glibc`. L’assemblage sans cache vérifie 11 fichiers source de bibliothèque système, soit 23 314 008 octets. Le schéma actuel autorise une seule révision Linux par nom. [Preuve Linux](../../licenses/system-linux/evidence-v0820.json)
- **Windows**. Les trois DLL relues portent la version `14.52.37029.0` et proviennent des dossiers VC145 CRT et OpenMP x64 du redistribuable MSVC `14.52.37025`. Les signatures Microsoft et leurs horodatages ont été vérifiés. Les dispositions applicables aux DLL concordent avec la décision `val-2026-11-06-24`. [Preuve Windows](../../licenses/system-windows/evidence-v0830.json)

Les tests ont rougi avec les entrées précédentes et repassé après restauration des entrées relues. La garde exige toujours les empreintes exactes et, sous Linux, l’identité du paquet. Le rapport `RENDU-C8.md` accompagne le bundle avec les résumés de la ronde et de la porte de release. La seconde construction à blanc reste à faire sur les runners.
