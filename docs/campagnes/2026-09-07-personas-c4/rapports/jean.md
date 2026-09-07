# Jean, dirigeant d'une TPE de cinq personnes : trace de la campagne

> Campagne « chaque écran, chaque persona », cycle 4, 07/09/2026.
> Frontend `http://localhost:1420` (worktree `Synoptia-THERESE-repair`), moteur `http://127.0.0.1:17393`,
> `THERESE_DATA_DIR=/tmp/therese-demo-c4`, base vierge, viewport 1280×800, DPR 1, locale fr-FR,
> thème clair puis contraste élevé pour la seconde moitié du parcours.

## Écart d'instrument (à lire avant les constats)

Le serveur MCP Playwright annoncé (`mcp__plugin_playwright_playwright__*`) **n'était pas exposé**
à cette session. Il a été remplacé par **Playwright Node piloté en CDP** : un lanceur
`chromium.launchPersistentContext` (headless, 1280×800, fr-FR, `colorScheme: light`,
`--remote-debugging-port=9222`) reste vivant pendant tout le parcours et porte les écouteurs
`console`, `pageerror`, `requestfailed`, `response >= 400` et `download` ; chaque geste se
connecte par `connectOverCDP` sur le même onglet. Même moteur (chromium-1208) que le MCP absent.
Cet écart relève du contexte de mesure, sans rapport avec le comportement de l'application.

**Garde d'environnement, avant le premier geste** :
`({ visible: document.visibilityState, horloge: document.timeline.currentTime })`
→ `{"visible":"visible","horloge":16522}`. Document visible, horloge d'animation non nulle : parcours autorisé.
Purge exécutée ensuite (`localStorage` 3 clés → vidé, `sessionStorage`, `indexedDB.databases()`),
rechargement, contrôle après recharge : `{"visible":"visible","horloge":3524}`.

**Décision assumée sur le modèle** : à l'étape « Service d'IA » j'ai d'abord choisi Ollama local
(`gemma4-tia:latest`) puis, pour éprouver la transition demandée, je suis revenu en arrière et j'ai
cliqué « Configurer plus tard ». Aucune clé cloud n'a été saisie à aucun moment. Aucune donnée réelle :
profil « Jean Démo / jean@exemple.test », contact « Camille », phrase secrète de sauvegarde de démonstration.

## Mon impression

J'ai lu chaque écran, c'est mon métier de me méfier. Et pour une fois, j'ai été rassuré par le texte :
la rubrique Confidentialité est la plus honnête que j'aie lue dans un logiciel. Elle dit ce qui est chiffré,
elle dit ce qui ne l'est **pas** (l'index Qdrant, le stockage local de l'interface), elle dit que la
recherche web part chez DuckDuckGo même en modèle local, et elle avoue que le Board et l'Atelier cherchent
encore sans me demander. Personne n'écrit ça pour se faire bien voir. La sauvegarde refuse de se lancer
sans phrase secrète et me prévient que sans elle je ne restaure rien : bon réflexe.

Ce qui m'a gêné tient en trois points. D'abord, j'ai cliqué « Configurer plus tard », le récapitulatif m'a
répondu « À configurer plus tard », et pourtant un fournisseur était bel et bien enregistré depuis mon
passage précédent : ici c'était Ollama, donc sans danger, mais le même chemin avec une clé cloud me
ferait croire que rien n'est branché alors que tout le serait. Ensuite, quand j'active « Contraste élevé »,
l'application passe en fond noir alors que le bouton « Clair » reste coché : je n'ai pas demandé à changer
de thème, et l'écran continue de me dire le contraire de ce qu'il affiche. Enfin, dans un logiciel qui se
présente comme souverain, je dois défiler devant treize fournisseurs cloud, dont un déjà coché et marqué
« Recommandé », pour trouver l'option locale en quatorzième position.

Le reste est propre : la fiche contact vide est refusée avec la bonne phrase, l'export me rend un JSON
lisible, et le Centre de confiance raconte la même chose que les Paramètres.

## Parcours

### Mise en route : lire chaque étape, refuser la clé cloud, terminer

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 1 | Purge du stockage, rechargement | assistant à l'étape 1 sur 6 | « Bienvenue sur THÉRÈSE », 6 pastilles d'étapes, `progressbar` annoncée | `01` | ok |
| 2 | « Commencer la configuration » | étape 2, Profil | Profil, mention « stockées localement dans `~/.therese/` », un seul champ obligatoire (Nom complet *) | `02` | voir jean-05 |
| 3 | Saisie du profil de démonstration | champs conservés | ok | `03` | ok |
| 4 | « Continuer » | étape 3, Service d'IA | 14 fournisseurs ; **Claude (Anthropic) déjà coché** et marqué « Recommandé » ; Ollama (Local) en 14ᵉ et dernière position ; « Continuer » désactivé sans clé | `04` | voir jean-P1 |
| 5 | Choix « Ollama (Local) » | option locale sélectionnable sans clé | `gemma4-tia:latest` choisi seul, alerte honnête « RAM déconseillée : environ 8,3 Gio requis, pour un plafond de 8 Gio » ; « Continuer » devient actif | `05` | ok |
| 6 | « Continuer » | étape 4, Sécurité | 5 rubriques de risque, lien externe, et **aucune case de consentement** : « Parcours local sans consentement cloud / Ollama traite les messages sur cette machine » | `06` | ok |
| 7 | « Retour », puis choix « Mistral AI » sans clé | retour à l'étape 3 | ok, « Continuer » redevient désactivé | `07` | ok |
| 8 | « Configurer plus tard » | étape 4 sans fournisseur | « Aucun fournisseur cloud n'est activé pour le moment. Un accord distinct sera demandé au premier usage cloud réel » | `08` | ok, **transition (a) 1/2** |
| 9 | « J'ai compris, continuer » | étape 5, Dossier | « Aucun dossier configuré » | `09` | ok |
| 10 | « Sélectionner un dossier » | ouverture du sélecteur | message calme et actionnable : « La fenêtre de choix du dossier ne s'est pas ouverte. Redémarre THÉRÈSE, puis réessaie. » (console : `TypeError: Cannot read properties of undefined (reading 'invoke')` - IPC Tauri absent hors application empaquetée) | `10` | limite d'instrument, pas un défaut |
| 11 | « Passer » | étape 6, récapitulatif | **« Service d'IA : À configurer plus tard »**, pastille neutre, **aucune coche verte, aucun nom de fournisseur cloud** ; « Dossier de travail : Non configuré » | `11` | **transition (a) conforme** |
| 12 | « Commencer » | accueil | « Bonjour Jean. », brief vide expliqué (« Aucune priorité détectée », actions de mise en route) | `12` | ok |

### Composeur sans modèle actif (transition c)

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 13 | « Nouvelle conversation » | bandeau « Choisis d'abord un modèle », envoi bloqué | **aucun bandeau** ; sélecteur de modèle affichant `gemma4-tia:latest` et l'étiquette « local » | `13` | voir angle mort (c) |
| 14 | Saisie « Bonjour, où sont stockées mes données ? » | bouton d'envoi désactivé | `Envoyer le message` **actif** (`isDisabled() === false`) | `14` | voir angle mort (c) |

Contrôle moteur au même instant : `GET /api/config/llm` → `{"provider":"ollama","model":"gemma4-tia:latest","available":true}`.

### Paramètres, lus rubrique par rubrique

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 15 | Ouverture des Paramètres | rubriques visibles | 6 onglets seulement ; mention « Masquées ici : Outils, Agents, Avancé » sous le bouton « Mode Contributeur » | `15` | ok |
| 16 | Onglet IA | **aucun fournisseur préconfiguré** | **aucun radio cloud coché** (Claude non coché, contrairement à la mise en route) ; Ollama (Local) actif, « Ollama connecté (http://localhost:11434) », 2 modèles, effort « Auto », alerte RAM répétée | `16` | **transition (d) conforme** |
| 17 | Onglet Confidentialité | expliquer ce qui est local | texte complet et vérifiable : SQLCipher AES-256 ; **« Deux endroits ne sont pas chiffrés : l'index Qdrant… et le stockage local de cette interface »** ; « Aucune télémétrie ni mesure d'audience » ; recherche web qui part même en local ; Board/Atelier qui cherchent sans carte | `17`, `18` | ok, remarquable |
| 19-20 | « Exporter toutes mes données » | export lisible | « Export global enregistré. » (sans chemin ni volumétrie) ; le fichier téléchargé par l'interface n'a pas pu être récupéré par mon instrument (échec du `saveAs` en CDP), j'ai donc lu la charge utile de `GET /api/data/export` → 2 349 o, `app_version 0.67.0`, `data_format_version 1.4`, profil + 28 collections | `19`, `20` | voir jean-P5 |
| 21 | « Créer une sauvegarde » sans phrase secrète | refus expliqué | « Choisis une passphrase pour chiffrer la sauvegarde. Conserve-la : elle est indispensable pour restaurer. » | `21` | ok |
| 22-23 | Phrase secrète de démonstration puis création | archive chiffrée locale | « Sauvegarde complète chiffrée créée localement. » ; entrée `therese_backup_20260907_214849 · 0,9 Mo` ; sur disque : `therese_backup_20260907_214849.tar.gz.enc` (mode 600) + son manifeste | `22`, `23` | ok, voir jean-P4 |
| 24-25 | Mode Contributeur puis onglet Avancé | dossier de données | « Stockage des données : tes données sont stockées localement sur ta machine » ; « Dossier de travail : Non configuré » ; compteurs 0/0/0/0 ; **aucun chemin absolu nulle part** | `24`, `25` | voir jean-P2 |
| 26-27 | « Limites & Consommation » | coûts et plafonds | 0 token, 0,00 $, budget 50 $, note honnête « les tarifs sont publiés en dollars » ; **encart « Indicateurs IA (US-ESC-01) »** | `26`, `27` | jean-03 |
| 28-29 | « Performance », puis « À propos » | version, mise à jour | version 0.67.0, phase Alpha, Discord, « Vérifier les mises à jour » | `28`, `29` | ok |
| 30 | Onglet Accessibilité | réglages lisibles | thème Clair coché, taille moyenne, interrupteurs animations / contraste / raccourcis | `30` | ok |

### Contraste élevé, puis rejeu des Paramètres

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 31 | Interrupteur « Contraste élevé » | contraste renforcé **du thème clair** | toute l'application bascule en **fond noir** ; `data-theme` reste `light`, radio « Clair » reste `aria-checked=true`, `--color-background: #000000`, `body` en `rgb(0,0,0)` sur `rgb(255,255,255)` | `31`, `35` | jean-02 |
| 32-34 | Rejeu IA / Confidentialité / Avancé en contraste élevé | lisibilité | lisible, chaque bouton et chaque onglet reçoit une bordure (règle `[data-high-contrast="true"] button, a { border: 1px solid currentColor }`) ; aucun texte tronqué ni chevauchement relevé à 1280×800 | `32`, `33`, `34` | ok |

### Contacts : création vide, puis prénom seul (transition e)

> Captures `36` à `45` : le contraste élevé est resté actif, conformément à ma fiche (thème clair pour la première moitié du parcours, contraste élevé pour la seconde). Le fond noir de ces captures est donc voulu.

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 36 | « Plus d'outils » | tiroir des capacités | 30 capacités, 6 familles | `36` | ok |
| 37b | Clic sur le libellé « Contacts » du tiroir | ouvrir les Contacts | aucun effet (le libellé cliqué n'était pas la surface interactive) | `37b` | observation |
| 37 | ⌘K puis « contact » | destinations proposées | 6 résultats, dont « Ouvrir les Contacts ⌘M », « Rechercher dans les Contacts », « Ajouter un contact » | `37-palette` | ok |
| 38 | « Ouvrir les Contacts » | vue Contacts vide | titre « Contacts », filtres Tout/Global/Projet/Conv., **« Aucun contact »** | `38` | ok |
| 39 | « Nouveau contact » | formulaire | 8 champs, **aucun marqué obligatoire** | `39` | ok |
| 40 | « Créer » sur formulaire entièrement vide | refus lisible | **« Le prénom ou le nom est requis »**, boîte maintenue ouverte, **aucune requête réseau émise** | `40` | **transition (e) conforme** |
| 41-42 | Prénom « Camille » seul, « Créer » | création acceptée | fiche créée, affichée « Camille » avec pastille ambre « RGPD ? » ; contrôle moteur `GET /api/memory/contacts` → 1 fiche, `last_name: null`, `score: 50`, `stage: "contact"`, `rgpd_base_legale: null`, `rgpd_consentement: false` | `41`, `42` | **transition (e) conforme** |
| 43-44 | Clic sur la ligne, puis menu « Actions RGPD » | renseigner la base légale | le formulaire d'édition **ne contient aucun champ RGPD** ; le menu propose « Exporter (Art. 20) », « Renouveler consentement », « Anonymiser (Art. 17) », **rien pour définir la base légale** que la pastille signale absente (`title="Base légale RGPD non définie pour ce contact"`) | `43`, `44` | jean-P3 |

### Centre de confiance

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 45 | Bouton « Contrôle des données » de la barre haute | comprendre ce qui est local | 5 rubriques (Données, Modèles, Traitement externe, Coûts et limites, RGPD) ; **même aveu que la rubrique Confidentialité** sur le Board et l'Atelier qui cherchent sans carte ; deux raccourcis vers Confidentialité et Paramètres | `45` | ok |

### Console et réseau, relevés en fin de parcours

- **1 seule erreur de console** sur toute la session : `Ouverture du sélecteur de dossier impossible: TypeError: Cannot read properties of undefined (reading 'invoke')` (21:44:20) - IPC Tauri absent hors application empaquetée, limite d'instrument.
- 2 avertissements au démarrage : `Tentative 1/5 échouée: ApiError: Impossible de contacter le serveur` (`App.tsx:77` et `:91`), suivis de `[API] IPC échoué, retry 10/10…` puis `[API] Fallback port 17393 (mode dev)`. Repli qui fonctionne, mais dix tentatives bruyantes avant lui.
- Réseau : **aucune réponse ≥ 400**. Deux `net::ERR_ABORTED` sur `/api/config/onboarding-complete` et `/api/config/stats`, tous deux au moment d'un rechargement de page (requêtes annulées par la navigation).
- Contrôle « écran = API » : `GET /api/chat/conversations` → **0**, alors que le tiroir Conversations affiche **1** entrée « Nouvelle conversation · 07 sept., 23:44 · 0 message ». Voir jean-04.

## Constats numérotés

### jean-01 - « Configurer plus tard » n'annule pas un fournisseur déjà enregistré, et le récapitulatif l'ignore
`bug_candidate` · sévérité **P2**

**Préconditions** : base vierge, mise en route à l'étape « Service d'IA ».
**Étapes rejouables** : (1) choisir un fournisseur et cliquer **Continuer** ; (2) à l'étape Sécurité, cliquer **Retour** ; (3) cliquer **Configurer plus tard** ; (4) terminer la mise en route et lire le récapitulatif, puis ouvrir une conversation.
**Attendu** : « Configurer plus tard » signifie qu'aucun service d'IA n'est en place ; le récapitulatif et le composeur disent la même chose que ce qui est enregistré.
**Observé** : le récapitulatif annonce « Service d'IA : À configurer plus tard » (capture `11`) alors que la préférence `llm_provider` est restée écrite côté moteur.

**Preuve** : l'export de portabilité, relu après coup, horodate l'écriture, et deux autres horodatages mesurés l'encadrent.

```
{'key': 'llm_provider', 'value': 'ollama', 'category': 'llm', 'created_at': '2026-09-07T21:43:31.799575'}
{'key': 'llm_model',    'value': 'gemma4-tia:latest',        'created_at': '2026-09-07T21:43:31.800319'}
{'key': 'onboarding_completed', 'value': 'true',             'updated_at': '2026-09-07T21:44:48.134926'}
```

La préférence est écrite à 21:43:31, au clic sur « Continuer » avec Ollama. L'erreur de console du sélecteur de dossier est horodatée 21:44:20, donc après « Configurer plus tard » et après « J'ai compris, continuer ». La mise en route est marquée terminée à 21:44:48, au clic sur « Commencer », juste après la lecture du récapitulatif. Entre ces deux bornes, la préférence n'a jamais été retirée : elle porte toujours le même `created_at` et aucun `updated_at` postérieur.

**Fichiers suspectés, lus** : `src/frontend/src/components/onboarding/LLMStep.tsx`. `handleContinue()` appelle `await api.setLLMConfig(...)`, écriture persistante ; le bouton « Configurer plus tard » est un simple `onClick={() => onNext(null)}` et ne repasse jamais par le moteur pour défaire ce qui a été écrit. `OnboardingWizard.tsx:86` ne fait que poser l'état d'écran (`setConfiguredProvider(null)`, `setLlmSkipped(true)`).

**Pourquoi c'est P2 pour moi** : le fournisseur resté en place est ici local, donc sans fuite. La même suite de gestes avec un service cloud me ferait lire « À configurer plus tard » alors que ma clé serait déjà au coffre : `handleSaveApiKey()` (même fichier, ligne 183) appelle `await api.setApiKey(selectedProvider, apiKeyInput)` avant même que je clique « Continuer », et « Configurer plus tard » ne défait pas davantage cette écriture. C'est exactement l'information que je viens vérifier dans ce récapitulatif.

### jean-02 - « Contraste élevé » remplace le thème sans le dire, et le thème affiché ment
`bug_candidate` · sévérité **P2**

**Préconditions** : thème « Clair » sélectionné.
**Étapes rejouables** : Paramètres > Accessibilité > interrupteur « Contraste élevé ».
**Attendu** : ce que la ligne promet, « Augmente le contraste pour une meilleure lisibilité », sur le thème que j'ai choisi ; ou, à défaut, un avertissement disant que le thème va changer.
**Observé** : toute l'application passe en fond noir, sans annonce ; le radio « Clair » reste coché et l'attribut du document reste `light`.

**Preuve** (mesure dans la page, capture `35`) :

```
{"theme":"light","hc":"true","bodyBg":"rgb(0, 0, 0)","bodyColor":"rgb(255, 255, 255)",
 "varBg":"#000000","varText":"#FFFFFF"}
radio « Clair » coché ? true
```

Captures `31` (accessibilité), `32` (IA), `33` (Confidentialité), `34` (Avancé) : toutes en fond noir.

**Fichier suspecté (lu)** : `src/frontend/src/styles/globals.css:551` - le bloc `[data-high-contrast="true"]` pose un fond noir **par conception** (le commentaire du 30/08 le dit explicitement : « Ce bloc pose un fond NOIR »). Ce qui reste défectueux tient au sélecteur de thème, qui continue d'annoncer « Clair » comme actif alors qu'aucun texte ne prévient que le contraste élevé prend le pas sur le thème.

### jean-03 - Un identifiant interne d'exigence est affiché à l'utilisateur
`bug_candidate` · sévérité **P3**

**Étapes rejouables** : Paramètres > Mode Contributeur > Avancé > « Limites & Consommation », faire défiler jusqu'en bas.
**Attendu** : un titre en français métier, comme partout ailleurs dans cet écran.
**Observé** : l'encart s'intitule **« Indicateurs IA (US-ESC-01) »**. La référence de user story est visible à l'écran (capture `27`, texte confirmé par le relevé de l'onglet).
**Contexte atténuant** : cet encart vit dans l'onglet Avancé, masqué tant que « Mode Contributeur » n'est pas activé. Un utilisateur ordinaire ne le voit pas.

### jean-04 - Le tiroir Conversations affiche une conversation que le moteur ne connaît pas
`bug_candidate` · sévérité **P3**

**Étapes rejouables** : depuis une base vierge, cliquer « Nouvelle conversation » sans envoyer de message, puis ouvrir le tiroir Conversations.
**Attendu** (contrôle imposé par le protocole) : `GET /api/chat/conversations` rend ce que le tiroir affiche.
**Observé** : le tiroir liste « Nouvelle conversation · 07 sept., 23:44 · 0 message » ; `GET /api/chat/conversations` avec le jeton de session rend `[]`, soit 0 conversation.
**Nuance honnête** : la conversation n'est probablement persistée qu'au premier envoi, ce qui est un choix défendable. Ce qui me gêne en tant qu'utilisateur, c'est qu'une entrée datée dans une liste d'historique n'existe nulle part côté données ; rien à l'écran ne la distingue d'une conversation enregistrée.

### jean-05 - La mise en route annonce un dossier de données qui n'est pas celui utilisé
`bug_candidate` · sévérité **P3** (conditionnel, voir la réserve)

**Étapes rejouables** : mise en route, étape 2 « Profil ».
**Attendu** : le chemin annoncé est celui où les fichiers atterrissent.
**Observé** : « Ces informations sont stockées localement dans **`~/.therese/`** et ne quittent jamais ta machine » (capture `02`), alors que cette instance écrit dans `/tmp/therese-demo-c4/` - la sauvegarde chiffrée créée à l'étape 22 s'y trouve : `/tmp/therese-demo-c4/backups/therese_backup_20260907_214849.tar.gz.enc`.
**Réserve** : l'écart n'apparaît que lorsque `THERESE_DATA_DIR` est défini, ce qui n'est pas le cas d'un utilisateur ordinaire. Je le signale parce que la phrase est écrite en dur et parce que c'est la seule phrase de toute l'application qui donne un chemin.

### jean-06 - Une pastille verte de fin d'étape sur une étape non configurée
`observation` (preuve visuelle, effet limité)

Dans le fil des 6 étapes, « Service d'IA » porte une coche verte dès qu'on l'a traversée, y compris après « Configurer plus tard » (captures `09`, `11`). Le récapitulatif, lui, est correct (« À configurer plus tard »). La coche du fil dit « fait », le récapitulatif dit « à faire » : deux vocabulaires pour le même état, sur le même écran.

## Propositions pour le portail humain (pas des défauts)

- **jean-P1 - l'option souveraine est la quatorzième.** À la mise en route comme dans les Paramètres, la liste des services d'IA commence par Claude (Anthropic), coché d'avance et étiqueté « Recommandé », et se termine par « Ollama (Local) - 100 % local, aucune clé API requise ». Il faut défiler devant treize services cloud pour atteindre le seul qui ne fait rien sortir de la machine, dans une application qui s'annonce « souveraine » dès son écran de bienvenue. Capture `04`.
- **jean-P2 - aucun chemin absolu du dossier de données.** Confidentialité dit « ton dossier utilisateur », Avancé affiche « Dossier de travail : Non configuré » et quatre compteurs, et rien ne me donne le chemin exact ni un bouton pour l'ouvrir. C'est la première chose que je veux voir avant de confier quoi que ce soit. Capture `25`.
- **jean-P3 - la pastille « RGPD ? » signale un manque qu'on ne peut pas combler.** Elle porte l'infobulle « Base légale RGPD non définie pour ce contact », mais ni le formulaire d'édition ni le menu « Actions RGPD » (Exporter Art. 20 / Renouveler consentement / Anonymiser Art. 17) ne permettent de renseigner cette base légale, alors que le champ existe côté moteur (`rgpd_base_legale`, visible dans `GET /api/memory/contacts`). Captures `43`, `44`.
- **jean-P4 - la liste des sauvegardes ne dit pas où elles sont.** « therese_backup_20260907_214849 · 0.9 Mo » avec « Restaurer » et « Supprimer », sans dossier ni bouton « Révéler ». Pour une archive que je suis censé conserver, c'est court. Capture `23`.
- **jean-P5 - « Export global enregistré. » ne dit ni où, ni combien.** Ni chemin, ni nombre d'éléments exportés. Le contenu, lui, est bon (28 collections, version de format `1.4`).
- **jean-P6 - dix tentatives bruyantes avant le repli au démarrage.** `[API] IPC échoué, retry 10/10…` puis `[API] Fallback port 17393 (mode dev)`, précédés de deux `Tentative 1/5 échouée: Impossible de contacter le serveur`. Invisible à l'écran, mais c'est ce que verra le premier testeur qui ouvre la console.

## Ce que j'ai trouvé juste, et qui mérite d'être protégé

- La rubrique Confidentialité nomme **ce qui n'est pas chiffré** (index Qdrant, stockage local de l'interface) et **ce qui sort quand même** (recherche web même en modèle local ; Board, recherche approfondie et Atelier qui cherchent sans carte de confirmation). Captures `17`, `18`.
- L'étape Sécurité ne réclame **aucun consentement cloud** quand le parcours est local, et le dit avec des mots différents selon le cas : « Ollama traite les messages sur cette machine » (capture `06`) contre « Aucun fournisseur cloud n'est activé pour le moment » (capture `08`).
- La sauvegarde refuse de partir sans phrase secrète, et prévient que sans elle la restauration est impossible (capture `21`).
- La fiche contact vide est refusée avec la bonne phrase et **sans appeler le serveur** (capture `40`).
- Le choix d'un modèle Ollama affiche une alerte de RAM chiffrée et laisse quand même décider (capture `05`).
- L'échec du sélecteur de dossier produit un message calme et actionnable au lieu d'une trace technique (capture `10`).

## Transitions couvertes et angles morts

| Transition demandée | Résultat |
|---|---|
| **(a)** « Configurer plus tard » puis récapitulatif : ni fournisseur cloud, ni coche verte | **couverte - conforme.** Étape Sécurité : « Aucun fournisseur cloud n'est activé pour le moment » (capture `08`) ; récapitulatif : « Service d'IA - À configurer plus tard », pastille neutre, aucun nom de fournisseur (capture `11`). Réserve distincte : ce que le récapitulatif annonce ne correspond pas à ce qui est enregistré côté moteur → jean-01. |
| **(b)** Cocher le consentement à l'étape Sécurité, revenir changer de fournisseur, vérifier que la case est décochée | **NON couverte - angle mort assumé.** La case n'existe que si un fournisseur cloud est **activé** : `const cloudEnabled = provider !== null && provider !== 'ollama'` puis `{cloudEnabled ? <label>…<input type="checkbox" id="security-consent"…` (`SecurityStep.tsx:77` et `:178-182`). Activer un fournisseur cloud exige une clé API, que je n'ai pas le droit de saisir. Les deux variantes **sans** case ont été photographiées (`06` avec Ollama, `08` après « Configurer plus tard »). |
| **(c)** Composeur sans modèle actif : explication + envoi bloqué ; ouvrir les Paramètres depuis le bandeau ; observer le bandeau pendant que les Paramètres sont ouverts | **NON couverte - angle mort d'environnement.** Un Ollama tourne sur cette machine (`/api/config/llm` → `available: true`), donc un modèle est toujours actif : aucun bandeau, envoi autorisé (captures `13`, `14`). La branche corrigée existe bien dans le code, y compris sa variante « réglages déjà ouverts » (`ChatInput.tsx:1109-1131`, `data-testid="chat-model-unavailable"`, bouton « Ouvrir les réglages IA » remplacé par « Les réglages sont ouverts : choisis un modèle dans l'onglet IA. »), mais je ne l'ai pas vue à l'écran et je ne la déclare donc ni bonne ni mauvaise. **Reproduction possible** : machine sans Ollama, ou moteur démarré avec un `OLLAMA_BASE_URL` mort (par exemple `http://127.0.0.1:9`), de sorte que `/api/config/llm` rende `available: false`. À noter : le moteur répondait déjà `provider: ollama, available: true` **avant** mon premier geste de mise en route, donc le modèle actif du composeur ne découle pas de la préférence non annulée du constat jean-01. |
| **(d)** Paramètres > IA : aucun fournisseur préconfiguré à mon insu | **couverte - conforme.** Aucun radio cloud n'est coché (capture `16`), contrairement à l'écran de mise en route où Claude l'est. Le seul fournisseur actif est Ollama local, annoncé explicitement : « Ollama connecté (http://localhost:11434) », « 2 modèle(s) disponible(s) ». Rien de cloud, rien de silencieux. |
| **(e)** Contacts : fiche entièrement vide, puis fiche avec seulement un prénom | **couverte - conforme.** Vide → refus « Le prénom ou le nom est requis », sans requête réseau (capture `40`). Prénom seul → acceptée et créée (capture `42`, `GET /api/memory/contacts` : 1 fiche `first_name: "Camille"`, `last_name: null`). |

**Autres angles morts de cette session** :

- **Fichiers (objectif 5 de ma fiche)** : non couvert. Le dossier de travail ne peut pas être choisi hors application empaquetée (IPC Tauri absent, capture `10`), donc ni l'entrée dans un sous-dossier, ni l'indexation d'un document, ni la question « que dit le document X ? » dans le chat.
- **Paramètres > Sécurité** (objectif 3) : cette rubrique n'existe pas comme onglet. Ce qui s'en rapproche est réparti entre l'étape Sécurité de la mise en route, l'onglet Confidentialité et le Centre de confiance, tous trois photographiés.
- **Aucun message n'a été envoyé dans le chat** : le budget de captures était atteint et l'objectif restant (question sur un document) dépendait des Fichiers, indisponibles.
- **Rubriques Services, Outils, Agents** : non ouvertes, faute de budget.
- **Focus non relevé** : l'arbre d'accessibilité a été résumé par son contenu et ses rôles à chaque étape, mais `document.activeElement` n'a jamais été mesuré. Je ne peux donc rien affirmer sur l'élément focalisé après chaque transition.
- **46 fichiers de captures** pour 45 étapes numérotées : `37b-tiroir-clic-contacts-sans-effet.png` s'ajoute à la série, il garde la trace d'un clic sans effet dans le tiroir.
- Aucun envoi réel, aucune clé, aucune donnée réelle, aucun `POST /api/shutdown`, aucune suppression de données, aucune écriture hors de `captures/jean/` et de ce fichier.

## Tokens consommés

Non instrumenté côté application (les compteurs de « Limites & Consommation » sont restés à 0 : aucun appel de modèle n'a été déclenché). Côté session d'agent, environ **200 000 tokens** consommés sur le budget alloué, sans mesure exacte disponible.
