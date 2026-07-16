# UltraJury - Rapport d Audit THERESE

- **Projet** : THÉRÈSE (app desktop Tauri 2, React/TS + sidecar FastAPI Python)
- **Type** : Fullstack desktop, 11 axes évalués (SEO hors périmètre)
- **Date** : 16 juillet 2026
- **Score global** : 75/100
- **Audit précédent** : 70,5/100 (9 juin 2026) - **Delta : +4,5**

## Tableau des scores

| Axe | Brute | Ajustée | Poids | Pondéré |
|-----|-------|---------|-------|---------|
| Performance | 80 | 79 | 10.87% | 8.59 |
| Securite | 75 | 75 | 10.87% | 8.15 |
| Accessibilite | 78 | 76 | 8.7% | 6.61 |
| Architecture | 74 | 74 | 13.04% | 9.65 |
| Frontend | 76 | 75 | 10.87% | 8.15 |
| DevOps | 77 | 76 | 8.7% | 6.61 |
| Qualite Code | 71 | 69 | 10.87% | 7.5 |
| Resilience | 80 | 78 | 7.61% | 5.94 |
| Conformite | 74 | 71 | 7.61% | 5.4 |
| Produit | 80 | 80 | 5.43% | 4.34 |
| Contenu | 74 | 74 | 5.43% | 4.02 |
| **TOTAL** | | | **100%** | **75** |

## Radar

```
Performance    ████████░░  79
Sécurité       ████████░░  75
Accessibilité  ████████░░  76
Architecture   ███████░░░  74
Frontend       ████████░░  75
DevOps         ████████░░  76
Qualité Code   ███████░░░  69
Résilience     ████████░░  78
Conformité     ███████░░░  71
Produit        ████████░░  80
Contenu        ███████░░░  74
```

## Top 10 recommandations

| Recommandation | Impact | Effort | Axes | Priorité |
|---|---|---|---|---|
| 1. Restreindre la capability Tauri `fs` à `$HOME/.therese/**` et couper le match des dotfiles (`requireLiteralLeadingDot`) : ferme la lecture de `~/.ssh/id_rsa`, `~/.aws/credentials`, `.encryption_key` par la webview | Fort | Faible | Sécurité | P0 |
| 2. Router les chemins `~/.therese` codés en dur via `settings.data_dir` (`files.py:298`, `llm.py:157`) : corrige la fuite de documents et de persona entre espaces isolés | Fort | Faible | Sécurité, Architecture, Produit | P0 |
| 3. Rendre l auth fail-closed (refuser si `expected` est None) et protéger `/api/auth/token` par secret fichier 0600 (`main.py:529-599`) | Fort | Faible | Sécurité | P0 |
| 4. Chiffrer l archive de backup (PBKDF2 déjà présent), exclure/protéger `.encryption_key`, et purger les backups au `delete_all` : aujourd hui backup = base en clair et restore ressuscite des PII effacées | Fort | Moyen | Sécurité, Conformité | P0 |
| 5. Émettre un token MCP à portée réduite (scopes/whitelist de routes) pour les agents spawns, distinct du token maître (`agents.py:1035`) | Fort | Moyen | Sécurité | P1 |
| 6. Rendre le consentement cloud spécifique au sous-traitant et l appliquer à la voix (Groq) et au failover du circuit breaker : les données partent aujourd hui vers un vendeur non consenti | Fort | Moyen | Conformité, Résilience | P1 |
| 7. Respawn du sidecar Python après crash (max-retries + backoff anti-crash-loop), `lib.rs:363-419` : un seul crash rend l app inutilisable, message UI trompeur | Fort | Moyen | Résilience | P1 |
| 8. Ajouter un timeout (`AbortSignal.timeout`) au client HTTP CRUD (`core.ts:107-154`) : un backend bloqué fige toutes les vues jusqu à ~300 s | Moyen | Faible | Résilience | P1 |
| 9. Piéger le focus des modales `aria-modal` (prioritaire : `ExternalActionConfirmation` sur actions payantes, `CommandPalette`, +13) et corriger le contraste AA du texte d erreur/cyan en thème clair | Moyen | Moyen | Accessibilité, Frontend | P2 |
| 10. Chaîne CI : signature/notarisation macOS/Windows, brancher Playwright e2e et `check-app-version-sync.py` en CI | Moyen | Moyen | DevOps | P2 |

## Matrice Impact x Effort

**Quick wins (fort levier, effort faible)**
- Capability `fs` scopée (P0), chemins `data_dir` (P0), auth fail-closed (P0), timeout HTTP CRUD (P1)
- `build.esbuild.drop=['console']` (perf, coupe le spam de `probeHealth`), contraste via tokens `text-error`/`text-accent`
- Brancher `version-check` et Playwright en CI

**Planifier (effort moyen)**
- Chiffrer backup + purge au `delete_all`, token MCP à portée réduite, respawn sidecar
- Consentement cloud spécifique (provider/voix/failover), piège de focus des modales, signature/notarisation

**Long terme (structurel)**
- Extraire un `ChatOrchestrator` de `chat.py` (2419 l., fonctions >500 l.) et réactiver C901
- Résorber la dette de typage (mypy 997/999) et les 317 `except Exception`
- Adopter réellement les primitives de formulaire mortes, transparence RGPD in-app + liste des sous-traitants
- Batch-fetch des N+1, recompresser `advisors-bg.png` (2,5 Mo), harmoniser accents et registre tu/vous

## Problèmes critiques (action immédiate)

Aucun défaut n a été classé Critique par les experts. Cinq points Importants de sécurité et de données doivent néanmoins être soldés avant toute mise à disposition large (GA) :

1. **Capability `fs` sur `$HOME/**`** : sous injection de contenu, la webview lit clés SSH, credentials AWS et la clé de chiffrement ; `requireLiteralLeadingDot:false` rend le vol des dotfiles concret et contourne `path_security.py`.
2. **Clé de chiffrement à côté des données** : `.encryption_key` est sauvegardée dans le `data_dir` et incluse dans l archive `.tar.gz` ; un backup synchronisé sur un cloud équivaut à une base en clair.
3. **Auth fail-open + `/api/auth/token` exposé** : sur machine multi-utilisateurs, un autre utilisateur local récupère le token en HTTP puis pilote toute l API.
4. **Token MCP maître transmis aux agents** : un agent LLM autonome (sujet au prompt-injection) obtient un accès total à l API locale (CRM, mails, fichiers, config).
5. **Consentement cloud non spécifique** : changement de provider, transcription vocale Groq et bascule serveur du circuit breaker envoient des données à un sous-traitant non consenti (RGPD art. 7). Le `delete_all` laisse par ailleurs des PII récupérables dans les backups et les logs d audit (art. 17).

## Plan d action

**Semaine 1 (quick wins)**
- Scoper la capability `fs` à `~/.therese/**` et couper le match dotfiles
- Router `files.py:298` et `llm.py:157` via `settings.data_dir`
- Auth fail-closed + protection `/api/auth/token`, timeout HTTP CRUD
- Contraste par tokens, `drop console`, brancher `version-check` et Playwright en CI

**Semaine 2-3 (structurel)**
- Chiffrer les backups + purge au `delete_all` + scrub des logs d audit
- Token MCP à portée réduite, respawn du sidecar avec garde anti-crash-loop
- Consentement cloud spécifique (provider, voix, failover), piège de focus des modales
- Signature/notarisation des installeurs macOS/Windows

**Mois 2+ (fond)**
- Extraire `ChatOrchestrator` de `chat.py` + réactiver C901, réduire la baseline mypy et les `except Exception`
- Adopter les primitives de formulaire, transparence RGPD in-app + liste consolidée des sous-traitants
- Batch-fetch des N+1, recompression `advisors-bg.png`, harmonisation accents et registre

## Résumé exécutif

THÉRÈSE progresse à 75/100 (+4,5 depuis le 9 juin), portée par un socle produit et résilience solides et sans aucun défaut classé critique. Les priorités tiennent en quelques correctifs peu coûteux à fort levier : resserrer la capability `fs` et les chemins `~/.therese` en dur, fermer le fail-open d auth et chiffrer les backups, aligner le consentement cloud sur le sous-traitant réellement sollicité. Le chantier de fond reste le god-object `chat.py` et la dette de typage/lint, à traiter progressivement sans bloquer la GA une fois les points sécurité et données soldés.