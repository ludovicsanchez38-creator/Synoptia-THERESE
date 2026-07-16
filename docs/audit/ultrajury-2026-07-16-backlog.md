# Backlog UltraJury - THÉRÈSE

**Date : 16 juillet 2026 | Score global : 75/100 | Application : desktop Tauri + React + FastAPI**

**Répartition : 18 stories - P0 : 4 | P1 : 10 | P2 : 3 | P3 : 1**

Périmètre : uniquement les problèmes réels confirmés (Importants, Mineurs, angles morts Phase 3). Les points classés [INCERTAIN] par l'audit (IA Act art.50, écart de version 0.32.1/v0.40, reproductibilité de build, session_token) ne génèrent pas de story dédiée, ils sont notés en marge quand un correctif voisin les touche.

---

## Récapitulatif

| # | Titre | Epic | P | Effort | Dép. |
|---|-------|------|---|--------|------|
| US-001 | Authentifier l'API locale et fermer le fail-open | Sécurité & Conformité | P0 | M | - |
| US-002 | Restreindre la capability fs de la webview et fermer l'exfiltration | Sécurité & Conformité | P0 | M | - |
| US-003 | Chiffrer les sauvegardes et protéger la clé de chiffrement | Sécurité & Conformité | P0 | M | - |
| US-004 | Consentement cloud complet et honoré (voix, fournisseur, failover) | Sécurité & Conformité | P0 | L | - |
| US-005 | Émettre un token MCP à portée réduite pour les agents | Sécurité & Conformité | P1 | L | US-001 |
| US-006 | Isoler tous les chemins ~/.therese entre espaces | Sécurité & Conformité | P1 | M | - |
| US-007 | Rendre l'effacement des données complet (droit à l'oubli) | Sécurité & Conformité | P1 | M | US-003 |
| US-008 | Fournir la transparence RGPD in-app | Sécurité & Conformité | P1 | M | - |
| US-009 | Piéger le focus de toutes les modales et étendre le scan axe | Accessibilité & Inclusion | P1 | L | - |
| US-010 | Corriger les contrastes AA du thème clair via les tokens | Accessibilité & Inclusion | P1 | M | - |
| US-011 | Optimiser la performance frontend (cold-start et saisie) | Performance & Optimisation | P2 | L | - |
| US-012 | Corriger les accents et harmoniser le tutoiement | Expérience Utilisateur | P1 | M | - |
| US-013 | Clarifier la navigation de la coque et le premier lancement | Expérience Utilisateur | P2 | M | - |
| US-014 | Rendre le runtime résilient (respawn, timeouts, retry) | Infrastructure & Fiabilité | P1 | M | - |
| US-015 | Signer et notariser les installeurs | Infrastructure & Fiabilité | P1 | L | - |
| US-016 | Fiabiliser et durcir la chaîne CI/CD | Infrastructure & Fiabilité | P1 | L | - |
| US-017 | Extraire un ChatOrchestrator et assainir le cœur backend | Qualité & Maintenabilité | P2 | XL | - |
| US-018 | Réduire la dette de fond (typage, exceptions, code mort) | Qualité & Maintenabilité | P3 | L | US-010 |

---

## Sécurité & Conformité

### US-001 - Authentifier l'API locale et fermer le fail-open
**Epic** : Sécurité & Conformité | **Priorité** : P0 | **Effort** : M
**Axes / Source** : Sécurité (Important 5) ; CR7 (angle mort, token en paramètre d'URL).

*En tant que responsable sécurité, je veux que l'API locale exige un secret et refuse par défaut, afin qu'un autre utilisateur de la machine ne puisse pas récupérer le token ni piloter les données du propriétaire.*

Critères d'acceptation :
- [ ] `GET /api/auth/token` exige un secret partagé lu depuis le fichier 0600 (ou l'endpoint est supprimé au profit d'un handshake par fichier).
- [ ] Le middleware d'auth est fail-closed : si `expected` est `None`, toutes les requêtes sont refusées (plus de passe-droit quand l'état du token est absent).
- [ ] Le token n'est plus accepté en paramètre `?token=` d'URL et n'est plus émis dans le `src` des `<img>` (le DOM de la webview ne contient plus le token).
- [ ] Un test vérifie qu'un client localhost non porteur du secret reçoit un 401 sur toutes les routes protégées.

Notes : `src/backend/app/main.py:529-532, 562-599, 589` ; `src/frontend/src/services/api/images.ts:51`. Le masquage de logs (`logging_config.py:17-40`) reste en filet mais ne suffit pas.

### US-002 - Restreindre la capability fs de la webview et fermer l'exfiltration
**Epic** : Sécurité & Conformité | **Priorité** : P0 | **Effort** : M
**Axes / Source** : Sécurité (Important 1, Mineurs CSP/emails/executor) ; CR2 (read-dir/stat sous-scopés) ; CR7 (dotfiles, `requireLiteralLeadingDot`).

*En tant que responsable sécurité, je veux que la webview n'accède qu'à ~/.therese et ne dispose d'aucun canal d'exfiltration passif, afin qu'une injection de contenu ne puisse pas lire les clés SSH, la clé de chiffrement ni exfiltrer de données.*

Critères d'acceptation :
- [ ] Les scopes `fs:allow-read-file`, `fs:allow-read-text-file`, `fs:allow-read-dir`, `fs:allow-stat` sont limités à `$HOME/.therese/**` (plus `$DOWNLOAD/**` pour l'export), la description de la capability reflète les scopes réels.
- [ ] Les sélections de fichiers arbitraires passent par le backend validé (`path_security.py`) et non par le plugin fs.
- [ ] `requireLiteralLeadingDot` est réglé pour que le glob ne matche plus les dotfiles (`~/.ssh/id_rsa`, `~/.therese/.encryption_key`).
- [ ] La CSP `img-src` est restreinte (`self data:` plus hôtes nécessaires) et `withGlobalTauri:false` est évalué avec import explicite de l'API.
- [ ] Les images distantes des emails sont bloquées par défaut avec opt-in "afficher les images" (`sanitizeEmailHtml`).

Notes : `capabilities/default.json:43-77, 151-177` ; `tauri.conf.json:13, 31, 69` ; `src/frontend/src/lib/sanitizeEmailHtml.ts:25-33`. Documenter la blocklist regex de `code_executor.py:45-70` comme défense secondaire, la validation AST restant la source de vérité.

### US-003 - Chiffrer les sauvegardes et protéger la clé de chiffrement
**Epic** : Sécurité & Conformité | **Priorité** : P0 | **Effort** : M
**Axes / Source** : Sécurité (Important 2) ; CR6 (backups conservant DB chiffrée + clé).

*En tant qu'utilisateur de THÉRÈSE, je veux que mes sauvegardes ne contiennent jamais la clé en clair à côté de la base, afin qu'un dossier ~/.therese ou une archive synchronisée sur un cloud ne soit pas équivalent à une base en clair.*

Critères d'acceptation :
- [ ] L'archive de backup `.tar.gz` est chiffrée par une passphrase utilisateur (câblage du `_derive_key_from_password` PBKDF2 déjà présent) OU exclut `.encryption_key`, la restauration n'étant alors autorisée que via le Keychain de la même machine.
- [ ] Le fichier `.encryption_key` n'est plus embarqué en clair dans l'archive de sauvegarde.
- [ ] Le flux de restauration est adapté et testé (backup chiffré restauré avec succès, backup sans passphrase refusé proprement).

Notes : `src/backend/app/services/encryption.py:181-196` ; `src/backend/app/routers/data.py` (backup ~623-720, restore 760-799, cible '.encryption_key' 694-698).

### US-004 - Consentement cloud complet et honoré (voix, fournisseur, failover)
**Epic** : Sécurité & Conformité | **Priorité** : P0 | **Effort** : L
**Axes / Source** : Conformité (Important 2) ; CR6 (angles morts : transcription vocale sans gate, bascule circuit breaker inter-fournisseurs).

*En tant que responsable de la conformité, je veux qu'aucune donnée ne parte vers un sous-traitant non consenti sur aucun canal, afin de respecter la spécificité du consentement (art.4-11 / art.7) sur le texte, la voix et les bascules automatiques.*

Critères d'acceptation :
- [ ] La transcription vocale déclenche le même modal de consentement cloud que le texte avant tout envoi à Groq (`transcribeAudio` vérifie `getCloudConsent()`).
- [ ] Le gate compare le fournisseur courant à celui consenti (`getCloudConsent()?.provider === currentProvider`) et re-déclenche le consentement à tout changement de fournisseur.
- [ ] À l'ouverture d'un circuit breaker, le failover se restreint à un fournisseur cloud déjà consenti, sinon bascule sur Ollama local (mode zéro-cloud, dernier recours existant) ; aucune donnée n'atteint un vendeur non consenti à l'insu du gate frontend.
- [ ] L'enregistrement de consentement nomme le fournisseur réellement utilisé.

Notes : `src/frontend/src/services/api/voice.ts:15, 89, 119-129` ; `src/frontend/src/hooks/useVoiceRecorder.ts:139` ; `src/frontend/src/components/chat/ChatInput.tsx:413-415, 660-662` ; `src/frontend/src/lib/consent.ts:38-46` ; `src/backend/app/services/llm.py:549-628`.

### US-005 - Émettre un token MCP à portée réduite pour les agents
**Epic** : Sécurité & Conformité | **Priorité** : P1 | **Effort** : L
**Axes / Source** : Sécurité (Important 4).

*En tant que responsable sécurité, je veux que le pont MCP reçoive un token restreint plutôt que le token maître, afin qu'un agent LLM sujet à prompt-injection ne dispose pas d'un accès total à l'API locale (CRM, emails, fichiers, config).*

Critères d'acceptation :
- [ ] L'agent spawné reçoit un token dérivé à scopes réduits (whitelist des ~8 routes MCP), distinct du token de session maître.
- [ ] La durée de vie du token dérivé est liée à la session de l'agent.
- [ ] Un test vérifie qu'un appel hors whitelist avec ce token est refusé.

Notes : `src/backend/app/routers/agents.py:1028-1046` ; `src/backend/app/services/mcp_therese_server.py:31`. La portée réelle dépend de la topologie de déploiement OpenClaw (agents même-utilisateur vs serveur MCP tiers), à valider côté configuration.

### US-006 - Isoler tous les chemins ~/.therese entre espaces
**Epic** : Sécurité & Conformité | **Priorité** : P1 | **Effort** : M
**Axes / Source** : Sécurité (Important 3), Architecture (Important 3), Produit (Important 2) ; CR7 (fallback PDF factures), CR8 (cache singleton THERESE.md).

*En tant qu'utilisateur exploitant plusieurs espaces isolés, je veux que documents, contexte et fichiers de sortie suivent settings.data_dir, afin qu'aucun contenu ni configuration ne fuite d'un espace vers l'espace par défaut.*

Critères d'acceptation :
- [ ] Tous les `Path.home()/'.therese'` en dur sont remplacés par `Path(settings.data_dir)` : `files.py:298`, `llm.py:157`, `logging_config.py:122`, fallback `invoice_pdf.py:52` et `invoices.py:48`.
- [ ] Le cache singleton `load_therese_md` (`_therese_md_content`) est invalidé quand data_dir change en cours de process.
- [ ] Une garde CI interdit toute nouvelle occurrence de `~/.therese` en dur dans le backend.
- [ ] Un test de non-régression par service écrit avec un data_dir custom et vérifie l'absence d'écriture dans l'espace par défaut.

Notes : convergence forte (5 axes pointent les mêmes lignes). Vérifié comme corrects et à ne pas modifier : `browser_agent.py:91`, `tool_installer.py:54` (déjà en data_dir malgré docstrings trompeuses).

### US-007 - Rendre l'effacement des données complet (droit à l'oubli)
**Epic** : Sécurité & Conformité | **Priorité** : P1 | **Effort** : M
**Axes / Source** : Conformité (Important 1, Mineurs) ; CR6 (backups survivant à delete_all avec PII).

*En tant que responsable de la conformité, je veux que "Supprimer toutes mes données" efface réellement les PII, afin que l'UI ("toutes tes données ont été supprimées") soit honnête et que le droit à l'oubli (art.17) soit tenu.*

Critères d'acceptation :
- [ ] L'anonymisation et `delete_all` scrubbent le champ `details.name` des entrées `ActivityLog` (ne conserver qu'action + resource_id) ou purgent les logs au-delà de la durée légale.
- [ ] Les sauvegardes locales sont purgées ou l'utilisateur se voit proposer explicitement leur purge lors d'un reset intégral (plus de restore silencieux ressuscitant des contacts "effacés").
- [ ] La clé localStorage `therese-cloud-consent` est retirée lors de `delete_all`.

Notes : `src/backend/app/routers/memory.py:416, 718` ; `src/backend/app/routers/data.py:488-489, 622-626` ; `src/backend/app/routers/rgpd.py:236-245` ; `src/frontend/src/lib/consent.ts:8` ; `src/frontend/src/components/settings/PrivacyTab.tsx:124-132`. Coordonner avec US-003 (traitement des archives de backup).

### US-008 - Fournir la transparence RGPD in-app
**Epic** : Sécurité & Conformité | **Priorité** : P1 | **Effort** : M
**Axes / Source** : Conformité (Important 3, Mineur liste sous-traitants).

*En tant qu'utilisateur mairie ou association, je veux accéder in-app à l'identité du responsable de traitement et à mes voies de recours, afin d'avoir la transparence exigée (art.13/14) pour un logiciel distribué à des tiers.*

Critères d'acceptation :
- [ ] Une politique de confidentialité et des mentions légales (responsable, coordonnées, canal d'exercice des droits) sont accessibles depuis l'onglet Confidentialité ou À propos.
- [ ] Une vue unique "sous-traitants" liste chaque destinataire (nom, finalité, données transmises), Groq inclus, cohérente entre onboarding et onglet Confidentialité.

Notes : `src/frontend/src/components/settings/PrivacyTab.tsx:189-193` ; `AboutTab.tsx` ; `src/frontend/src/components/onboarding/SecurityStep.tsx:57-61, 174`.

---

## Accessibilité & Inclusion

### US-009 - Piéger le focus de toutes les modales et étendre le scan axe
**Epic** : Accessibilité & Inclusion | **Priorité** : P1 | **Effort** : L
**Axes / Source** : Accessibilité (Important 1, Mineurs 1-2) ; CR4 (angle mort : liste focus-trap incomplète).

*En tant qu'utilisateur au clavier ou de lecteur d'écran, je veux être amené dans chaque modale et ne pas tabuler derrière l'overlay, afin de confirmer une action payante sans piège de focus (WCAG 2.4.3 / 2.1.2).*

Critères d'acceptation :
- [ ] `ExternalActionConfirmation` (confirmation des actions externes/payantes, prioritaire) utilise `useDialogFocusTrap` : focus déplacé à l'ouverture, Escape géré, Tab contenu, focus restauré à la fermeture.
- [ ] Les modales oubliées par le premier inventaire sont couvertes : `CommandPalette.tsx:190` (Cmd+K), `EmailSetupWizard.tsx:93`, `InvoiceForm.tsx:408`.
- [ ] Les panneaux overlay (Board, Tasks, Email, Calendar, CRM, Invoices, Projects, Tools, PanelContainer) sont enveloppés dans `DialogShell` ou piégés avec `isolateBackground:true`.
- [ ] `createFocusTrap` / `createRovingTabindex` (code mort legacy) sont supprimés de `lib/accessibility.ts:97-224`.
- [ ] Le scan axe-core couvre désormais `ConversationCanvasPrototype` (état d'accueil) et `ExternalActionConfirmation`.

Notes : `src/frontend/src/components/app/ExternalActionConfirmation.tsx:66` ; panneaux dans `components/{board,tasks,email,calendar,crm,invoices,memory,settings,chat}` ; `src/frontend/src/test/a11y.test.tsx:141-169`. Pattern déjà éprouvé sur 20 surfaces.

### US-010 - Corriger les contrastes AA du thème clair via les tokens
**Epic** : Accessibilité & Inclusion | **Priorité** : P1 | **Effort** : M
**Axes / Source** : Accessibilité (Important 2), Frontend (Important 1).

*En tant qu'utilisateur en thème clair (mode par défaut), je veux des messages d'erreur et des états sélectionnés lisibles, afin de percevoir les informations critiques au seuil AA 4.5:1.*

Critères d'acceptation :
- [ ] `text-accent-cyan` (#22D3EE, ratio ~1.8:1) est remplacé par `text-accent` (#0F8FB3) dans l'onglet Accessibilité (chips lignes 56, 110 ; encart raccourcis 181-182), la teinte `bg-accent-cyan/10` étant conservée.
- [ ] `text-red-400` / `red-500` du texte d'erreur (ratio ~2.3:1) sont remplacés par `text-error` / `border-error` (#B91C1C) dans les composants concernés (`EmailPanel.tsx:390, 639`, `FormField.tsx:39, 58`, plus ~41 fichiers atelier/tasks/crm/guided).
- [ ] Le test de contrat de thème, aujourd'hui limité à `components/prototype`, est étendu à l'ensemble de `src/components` et couvre l'accent-comme-texte.

Notes : `src/frontend/src/components/settings/AccessibilityTab.tsx:56, 110, 181-182` ; `src/frontend/src/styles/globals.css:29, 44`.

---

## Performance & Optimisation

### US-011 - Optimiser la performance frontend (cold-start et saisie)
**Epic** : Performance & Optimisation | **Priorité** : P2 | **Effort** : L
**Axes / Source** : Performance (Mineurs 1-3) ; CR1 (angle mort : re-render de la coque, EmailList faussement virtualisée) ; CR8 (vendor-markdown statique).

*En tant qu'utilisateur, je veux un démarrage plus léger et une saisie fluide, afin de ne pas subir de jank à chaque frappe ni un bundle surdimensionné au cold-start.*

Critères d'acceptation :
- [ ] `advisors-bg.png` (2,5 Mo) est converti en WebP ou recompressé (oxipng/pngquant), cible <400 Ko.
- [ ] `build.esbuild.drop=['console']` est ajouté dans `vite.config.ts` (supprime les 63 console.* du bundle et le spam de `probeHealth` toutes les 2s au splash).
- [ ] `manualChunks` passe en fonction `(id => ...)` pour réellement isoler react/react-dom, ou le choix mono-chunk desktop est assumé et documenté.
- [ ] Le composer est extrait dans un composant mémoïsé : une frappe ne re-render plus l'intégralité de `ConversationCanvasPrototype` ni les panneaux ouverts.
- [ ] La règle de transition globale `*` (`globals.css:355-360`) est ciblée sur des classes utilitaires précises (supprime les recalculs de style parasites au survol).
- [ ] La docstring "virtualized" trompeuse d'`EmailList.tsx:4` est corrigée (ou la virtualisation réellement mise en place).

Notes : `src/frontend/src/assets/board/advisors-bg.png` ; `AdvisorArcLayout.tsx:21` ; `vite.config.ts:36-53` ; `SplashScreen.tsx` ; `ConversationCanvasPrototype.tsx:668, 1371-1372`. `MessageBubble` (seul composant memo, syntax-highlighter tree-shakeable) est déjà bien optimisé, à préserver.

---

## Expérience Utilisateur

### US-012 - Corriger les accents et harmoniser le tutoiement
**Epic** : Expérience Utilisateur | **Priorité** : P1 | **Effort** : M
**Axes / Source** : Contenu (Importants 1-2, Mineurs) ; CR4 (angle mort : famille d'accents au-delà de "tache", alt marque).

*En tant qu'utilisateur francophone, je veux un français impeccable et une voix cohérente, afin que le standard Synoptïa tienne sur tous les écrans réels.*

Critères d'acceptation :
- [ ] `tache/taches` deviennent `tâche/tâches` dans le sous-système Atelier/Tâches (~14 chaînes visibles).
- [ ] La famille d'accents manquants est corrigée partout : `specialise` -> spécialisé, `Selectionne(r/z)` -> Sélectionne(r/z), `Decris` -> Décris, `correspond a` / `message a` -> à (dont `AgentChat.tsx:190`, `InvoiceForm.tsx:491`).
- [ ] Le tutoiement est harmonisé sur les surfaces qui vouvoient (synchro CRM/Sheets, Atelier), front et back : "Connectez-vous" -> "Connecte-toi", "votre compte" -> "ton compte", etc.
- [ ] Les apostrophes courbes et le caractère "…" sont normalisés ; l'`alt` de la marque est unifié en "THÉRÈSE" accentué.

Notes : `src/frontend/src/components/atelier/{AgentCatalog.tsx:210, AgentSession.tsx:559, AgentChat.tsx:190,257,360, SessionList.tsx}` ; `tasks/TasksPanel.tsx:126` ; `chat/ShortcutsModal.tsx:50` ; `settings/CRMSyncPanel.tsx:205,218,345` ; `src/backend/app/routers/crm.py:1215,1264` ; `GuidedPrompts.tsx:445`. Les libellés hybrides (Board, Studio, Follow-ups) restent à trancher via une charte terminologique (voir US-013).

### US-013 - Clarifier la navigation de la coque et le premier lancement
**Epic** : Expérience Utilisateur | **Priorité** : P2 | **Effort** : M
**Axes / Source** : Produit (Important 1, Mineurs) ; Frontend (Mineurs prefers-color-scheme, navigator.platform) ; CR1 (contrainte WKWebView documentée).

*En tant qu'utilisateur, je veux un point d'entrée clair et un premier lancement aligné sur mon système, afin de ne pas hésiter entre deux "Rechercher" ni ouvrir l'app en thème clair quand mon OS est en sombre.*

Critères d'acceptation :
- [ ] Les deux boutons "Rechercher" sont distingués explicitement ("Rechercher dans THÉRÈSE" vs "Rechercher une conversation"), le Capability Center devenant le lanceur canonique.
- [ ] Le thème initial est dérivé de `matchMedia('(prefers-color-scheme: dark)')` tant que l'utilisateur n'a pas choisi, avec écoute des changements.
- [ ] Un helper `isMac` unique est réutilisé pour ⌘K/Ctrl+K, en conservant `navigator.platform` (seul fiable sous WKWebView Tauri macOS, contrainte documentée `OnboardingWizard.tsx:48`) plutôt que `navigator.userAgentData`.
- [ ] L'accroche "souveraine" est qualifiée ("tes données restent locales, l'inférence passe par le fournisseur de ton choix, option 100% locale") ; le mur de risques d'onboarding passe en divulgation progressive.

Notes : `src/frontend/src/components/prototype/ConversationCanvasPrototype.tsx:1077-1096, 1088` ; `CapabilityCenter.tsx:529` ; `src/frontend/src/stores/accessibilityStore.ts:61` ; `App.tsx` ; `WelcomeStep.tsx:57` ; `SecurityStep.tsx:120-170`. Trancher aussi le libellé public de version (0.32.1 vs v0.40) avant GA.

---

## Infrastructure & Fiabilité

### US-014 - Rendre le runtime résilient (respawn, timeouts, retry)
**Epic** : Infrastructure & Fiabilité | **Priorité** : P1 | **Effort** : M
**Axes / Source** : Résilience (Importants 1-2, Mineurs 1-2) ; CR6 (angle mort : `response.json()` sans garde).

*En tant qu'utilisateur, je veux que l'app se répare et n'attende jamais indéfiniment, afin qu'un crash du sidecar ou un backend bloqué ne rende pas l'application inutilisable sans feedback.*

Critères d'acceptation :
- [ ] Sur `CommandEvent::Terminated` avec code inattendu (hors shutdown volontaire), le sidecar est relancé avec garde max-retries/backoff (ex. 3 essais, fenêtre anti-crash-loop) et un événement affiche "Redémarrage du moteur..." côté UI.
- [ ] `request<T>` et `apiFetch` sont enveloppés dans `AbortSignal.timeout` (ex. 30s pour le CRUD), l'`AbortError` étant mappé sur une `ApiError` claire ("le serveur met trop de temps à répondre").
- [ ] Un watchdog d'inactivité optionnel abort le flux SSE après N secondes sans chunk.
- [ ] Le décorateur `with_retry` (aujourd'hui code mort) décore les callsites HTTP externes non-LLM (sync Sheets, IMAP, calendar) ou est supprimé.
- [ ] Le chemin succès de `request<T>` gère une réponse 200 à corps vide ou non-JSON sans erreur non mappée.

Notes : `src/frontend/src-tauri/src/lib.rs:363-419` ; `src/frontend/src/services/api/core.ts:107-154` ; `src/frontend/src/services/api/chat.ts:159-187` ; `src/backend/app/services/error_handler.py:124-195`.

### US-015 - Signer et notariser les installeurs
**Epic** : Infrastructure & Fiabilité | **Priorité** : P1 | **Effort** : L
**Axes / Source** : DevOps (Important 1) ; CR2 (synergie hardened runtime).

*En tant que release manager, je veux des installeurs signés et notarisés, afin que les utilisateurs d'un produit vendu comme souverain ne se heurtent pas à Gatekeeper, SmartScreen et aux faux positifs Defender sur le sidecar PyInstaller.*

Critères d'acceptation :
- [ ] macOS : signature Developer ID + notarytool, avec `signingIdentity` et un fichier `entitlements` réel dans le bloc `bundle.macOS` (active le hardened runtime, remplace le codesign ad-hoc).
- [ ] Windows : signature Authenticode / Azure Trusted Signing dans le job build.
- [ ] Les notes de release ne renvoient plus le contournement (`xattr -cr`, exclusion antivirus) à l'utilisateur.

Notes : `.github/workflows/release.yml:168-172, 274-275` ; `src/frontend/src-tauri/tauri.conf.json:49-62`. Un seul chantier ferme le trou Gatekeeper et durcit l'app au niveau OS.

### US-016 - Fiabiliser et durcir la chaîne CI/CD
**Epic** : Infrastructure & Fiabilité | **Priorité** : P1 | **Effort** : L
**Axes / Source** : DevOps (Importants 2-3, Mineurs) ; CR2 (cargo audit, SAST) ; CR3 (angles morts : artefacts trackés, seeds en skip silencieux, tests skip) ; Résilience (Mineur 3), Qualité (Mineur couverture).

*En tant que release manager, je veux une CI qui exécute réellement les tests et verrouille la supply-chain, afin qu'aucune régression de bout en bout ni dérive de dépendance ne passe inaperçue.*

Critères d'acceptation :
- [ ] Un job Playwright E2E est exécuté en CI (ou en nocturne) ; l'e2e Python n'est plus ignoré en silence.
- [ ] Les fixtures de seed ne font plus de `pytest.skip` en cascade : si le seed casse, les suites CRM/RGPD/factures/agenda/tâches échouent au lieu de se sauter (plus de CI verte sans assertion exécutée).
- [ ] Les 115 artefacts Playwright (`test-results/`, `playwright-report/`, captures d'échec) sont retirés du suivi git et ajoutés au `.gitignore`.
- [ ] `scripts/check-app-version-sync.py` est branché dans un job CI.
- [ ] Un seuil de couverture (`--cov-fail-under` pytest + seuil vitest) est configuré ; le chemin de récupération du circuit breaker (OPEN -> HALF_OPEN -> CLOSED) est couvert par un test unitaire.
- [ ] Supply-chain : actions GitHub épinglées par SHA, `.github/dependabot.yml` ajouté, `cargo audit` et un SAST (CodeQL/semgrep) exécutés, bloc `concurrency` sur release.yml, `permissions: contents: read` sur ci.yml, génération SBOM/provenance.

Notes : `.github/workflows/ci.yml:60, 120-158, 186, 202-238` ; `release.yml:3-11, 37-49` ; `tests/e2e/conftest.py:372, 399, 422` ; `Makefile:96-98` ; `src/backend/app/services/circuit_breaker.py:101-174`. Envisager un projet Playwright `toHaveScreenshot` incluant le viewport minimal 800x600.

---

## Qualité & Maintenabilité

### US-017 - Extraire un ChatOrchestrator et assainir le cœur backend
**Epic** : Qualité & Maintenabilité | **Priorité** : P2 | **Effort** : XL
**Axes / Source** : Architecture (Importants 1-2-4, Mineurs) ; Qualité (Important 2) ; CR8 (synergie : N+1 et scan de noms sur le hot-path).

*En tant que développeur mainteneur, je veux que l'orchestration tool-calling et le streaming vivent dans un service testable, afin de sortir `chat.py` de l'état de god-object et de rendre le chemin critique relisable et modifiable sans régression.*

Critères d'acceptation :
- [ ] L'orchestration (`send_message` ~550 l., `_do_stream_response` ~500 l., `_execute_tools_and_continue` ~390 l.) est extraite dans un service `ChatOrchestrator` ; le routeur ne garde que validation d'entrée et appel service.
- [ ] Les 8 classes de résultat inline (`chat.py:1808-1924`) sont remplacées par le dataclass canonique `ToolCallResult` via un helper `_run_builtin_tool(coro)` (supprime ~100 l. dupliquées et les `import time` répétés).
- [ ] `ensure_valid_access_token` est déplacé de `routers/email.py` vers `services/` (corrige l'inversion de dépendance service -> routeur de `workspace_tools.py:367, 408`).
- [ ] La règle ruff C901 est réactivée avec un seuil sur le module refactorisé.
- [ ] Le scan de noms contacts/projets (`chat.py:379`, 2000+2000 lignes par extraction) est mémoïsé dans l'orchestrateur ; les N+1 des syncs sont batch-fetchés via `select(...).where(id.in_(ids))`.

Notes : `src/backend/app/routers/chat.py:379, 562-2090, 1808-1924` ; `src/backend/app/services/mcp_service.py:196` ; `src/backend/app/services/workspace_tools.py:367, 408` ; N+1 : `crm_sync.py:224,261,269`, `calendar.py:225,644,1387`, `notification_service.py:135`, `rgpd_auto.py:148`, `data.py:1092,1141`. Occasion de remonter les imports au niveau module et de traiter le versioning d'API en îlot (`main.py:665-723`).

### US-018 - Réduire la dette de fond (typage, exceptions, code mort)
**Epic** : Qualité & Maintenabilité | **Priorité** : P3 | **Effort** : L
**Axes / Source** : Qualité (Importants 1-3, Mineurs) ; Frontend (Important 2, Mineurs any/lint).

*En tant que développeur mainteneur, je veux des garde-fous de typage et de lint réellement contraignants et sans code mort, afin que la CI détecte les vrais défauts et ne bascule pas au rouge au moindre ajout.*

Critères d'acceptation :
- [ ] La baseline mypy (997/999) est abaissée par paliers : les conteneurs vides sont annotés (`signals: dict[str, Any] = {}`), les mismatches réels résorbés (`email_classifier_v2.py:276-313`, `context.py:42-69`).
- [ ] Les `except Exception` (317, seuil BLE001) sont restreints aux exceptions attendues avec journalisation contextuelle, reprise du nettoyage US-101.
- [ ] Les fichiers parasites sont retirés du suivi git : `{` (0 octet) et `test_validation_bug.py` (transformé en vrai test ou supprimé) ; le cas limite `main.py:466` (field vide quand `loc==('body',)`) est corrigé.
- [ ] Les primitives de formulaire mortes (`Input/FormField/Select/Textarea.tsx`) sont soit adoptées par migration progressive des champs bruts avec couleurs alignées sur les tokens (voir US-010), soit retirées et le pattern retenu documenté.
- [ ] Les 5 avertissements `react-hooks/exhaustive-deps` et la duplication de migration `invoices.currency` (`database.py:32, 117`) sont résolus ; `no-explicit-any` est réactivé progressivement (65 `any` hors tests).

Notes : `pyproject.toml:101, 109-111` ; `.github/workflows/ci.yml:186` ; `src/frontend/eslint.config.js:19` ; `package.json:13` ; composants form dans `src/frontend/src/components/ui/`. Dépend de US-010 pour l'alignement des tokens de couleur.

---

## Sprint 0 (P0 uniquement)

Objectif : colmater tout accès non authentifié et toute donnée exposée avant d'aller plus loin.

| # | Titre | Effort |
|---|-------|--------|
| US-001 | Authentifier l'API locale et fermer le fail-open | M |
| US-002 | Restreindre la capability fs de la webview et fermer l'exfiltration | M |
| US-003 | Chiffrer les sauvegardes et protéger la clé de chiffrement | M |
| US-004 | Consentement cloud complet et honoré (voix, fournisseur, failover) | L |

Synergie Sprint 0 : US-002 (scope fs à ~/.therese + blocage dotfiles) supprime aussi la capacité de la webview à lire la clé `.encryption_key`, ce qui renforce US-003 en fermant la chaîne d'exfiltration de la clé.

---

## Roadmap

| Sprint | Stories | Objectif |
|--------|---------|----------|
| Sprint 0 | US-001, US-002, US-003, US-004 | Stopper les fuites de données et l'accès non authentifié (P0) |
| Sprint 1 | US-006, US-007, US-008, US-005, US-014 | Isolation multi-espaces, conformité RGPD (oubli, transparence, token MCP) et robustesse runtime |
| Sprint 2 | US-009, US-010, US-012, US-015, US-016 | Accessibilité (focus, contrastes), français impeccable, signature installeurs et CI honnête |
| Sprint 3 | US-011, US-013, US-017, US-018 | Performance frontend, finition UX, refactor du cœur backend et dette de fond |

Note de séquencement : US-006 (isolation ~/.therese) est le point de convergence de 5 axes et un prérequis de confiance ; le traiter tôt en Sprint 1 débloque la valeur "souveraine" du produit. US-017 (refactor XL) est placé en Sprint 3 mais fournit le point d'ancrage naturel pour la mémoïsation et le batch-fetch (US-011), à coordonner si les deux tombent dans la même itération.