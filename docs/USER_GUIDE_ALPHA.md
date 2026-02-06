# THÉRÈSE v2 - Guide Utilisateur Alpha

> **Version** : Alpha v3.7 - Février 2026
> **Éditeur** : Synoptïa (Ludovic Sanchez)
> **Contact** : ludo@synoptia.fr

---

## Bienvenue, testeur alpha !

**THÉRÈSE** est un assistant IA souverain conçu pour les solopreneurs et TPE français. Son ambition : te donner un copilote intelligent qui comprend ton métier, retient tes contacts et projets, et t'accompagne au quotidien - le tout en gardant tes données chez toi.

**"Ta mémoire, tes données, ton business."**

### Ce que tu testes

Tu as entre les mains une version **alpha**. Cela signifie :

- Des **bugs sont attendus** (et c'est normal !)
- Certaines fonctionnalités sont encore en cours de finition
- Tes retours sont **précieux** pour améliorer le produit

### Comment remonter un problème

Tu as trois options (la première est recommandée) :

1. **Discord** (recommandé) : mentionne `@Thérèse bug : [description du problème]` dans le salon **#bugs**. Le bot crée automatiquement un thread dédié et te demande des précisions.
2. **GitHub Issues** : ouvre une [issue](https://github.com/ludovicsanchez38-creator/Synoptia-THERESE/issues/new?template=bug_report.md) avec le template de bug report
3. **Email** : envoie un message à **ludo@synoptia.fr** avec le sujet `[THÉRÈSE Alpha] Bug`

### Le cycle de correction

1. Tu signales un bug sur Discord
2. **Thérèse** (bot Discord) crée un thread et prépare une fiche
3. Chaque nuit à 2h, **Zézette** (bot développeuse) lit les fiches, code les corrections, et push sur GitHub
4. Le matin, une nouvelle build est disponible dans **#changelog**
5. Tu peux vérifier que le bug est corrigé

---

## Installation et premier lancement

### Installation simple (recommandée)

1. Télécharge l'installeur depuis les [GitHub Releases](https://github.com/ludovicsanchez38-creator/Synoptia-THERESE/releases) :
   - **macOS** : fichier `.dmg`
   - **Windows** : fichier `.exe`
2. Double-clique sur le fichier téléchargé pour lancer l'installation. C'est tout !

> **macOS** : l'application n'est pas encore signée (certificat Apple). Au premier lancement : clic droit > **Ouvrir** > **Confirmer**. macOS retiendra ton choix pour les lancements suivants.

> **Windows** : si SmartScreen affiche un avertissement, clique sur **"Plus d'infos"** puis **"Exécuter quand même"**.

### Installation depuis les sources (développeurs)

Si tu souhaites compiler le projet toi-même, consulte le guide technique : [docs/GETTING_STARTED.md](GETTING_STARTED.md).

### Onboarding

Au premier lancement, un **wizard de configuration** te guide en 6 étapes :

1. **Bienvenue** - Présentation de THÉRÈSE
2. **Profil** - Ton nom, entreprise, rôle (import possible depuis un fichier CLAUDE.md)
3. **LLM** - Choix du provider IA et clé API
4. **Sécurité** - Information sur les connexions cloud et les risques associés
5. **Dossier de travail** - Répertoire local pour tes fichiers
6. **Terminé** - Résumé de ta configuration

---

## Fonctionnalités testables

### 1. Chat IA (multi-provider LLM)

Le coeur de THÉRÈSE : une conversation fluide avec un LLM de ton choix.

**Providers supportés** :

| Provider | Modèles | Clé API requise |
|----------|---------|-----------------|
| **Anthropic** | Claude Opus 4.5, Sonnet 4.5, Haiku 4.5 | `sk-ant-...` |
| **OpenAI** | GPT-5.2, GPT-4o, o3 | `sk-...` |
| **Gemini** | Gemini 3 Pro, 3 Flash, 2.5 Pro, 2.5 Flash | `AIza...` |
| **Mistral** | Mistral Large, Codestral, Mistral Small | Clé Mistral |
| **Grok** | Grok 3, Grok 3 Fast | `xai-...` |
| **Ollama** | Tous les modèles locaux installés | Aucune (100% local) |

**Ce que tu peux tester** :
- Envoyer des messages et observer le **streaming** (réponse mot par mot)
- Changer de provider/modèle dans **Paramètres** (icône engrenage)
- Les **commandes slash** : tape `/` dans le champ de saisie pour voir la liste
  - `/contact` - Mentionner ou créer un contact
  - `/projet` - Mentionner ou créer un projet
  - `/recherche` - Chercher dans la mémoire
  - `/fichier [chemin]` - Inclure le contenu d'un fichier dans le contexte
  - `/résumé` - Résumer la conversation en cours
  - `/tâches` - Extraire les tâches de la conversation
  - `/email` - Rédiger un email
  - `/rdv` - Préparer un rendez-vous

---

### 2. Mémoire (contacts et projets)

THÉRÈSE retient tes contacts, tes projets et les informations importantes.

**Ce que tu peux tester** :
- **Ajouter un contact** : ouvre l'espace de travail (`Cmd+M` sur macOS / `Ctrl+M` sur Windows), onglet Contacts, bouton "+"
- **Ajouter un projet** : onglet Projets, bouton "+"
- **Extraction automatique d'entités** : parle d'une personne ou d'un projet dans le chat, THÉRÈSE détecte les entités et te propose de les sauvegarder (bandeau sous le message)
- **Injection automatique du contexte** : quand tu poses une question sur un contact ou un projet connu, THÉRÈSE injecte les informations pertinentes dans sa réponse
- **Recherche hybride** : la recherche combine recherche sémantique (embeddings Qdrant) et recherche par mots-clés
- **Portée (scope)** : les entités peuvent être globales, liées à un projet, ou liées à une conversation

---

### 3. Skills Office (génération de documents)

THÉRÈSE génère des fichiers Office professionnels directement depuis le chat.

**Formats disponibles** :

| Skill | Format | Description |
|-------|--------|-------------|
| **Document Word** | `.docx` | Rapports, guides, procédures - style Synoptïa |
| **Présentation PPT** | `.pptx` | Slides 16:9 avec dark theme |
| **Tableur Excel** | `.xlsx` | Tableaux avec formules, multi-onglets |

**Comment tester** :
1. Sur l'écran d'accueil, clique sur **Produire**
2. Choisis **Document Word**, **Présentation PPT** ou **Tableur Excel**
3. Décris ce que tu veux dans le prompt (ex: "Crée une présentation de 10 slides sur les tendances IA 2026")
4. THÉRÈSE génère le fichier - tu peux le **télécharger** directement

**Note technique** : les modèles puissants (Claude, GPT) utilisent la génération par code Python (meilleure qualité). Les modèles plus légers (Ollama, Gemini Flash) utilisent un pipeline Markdown avec conversion automatique.

---

### 4. Guided Prompts (écran d'accueil)

L'écran d'accueil propose 4 catégories d'actions guidées avec des prompts pré-remplis.

| Catégorie | Icône | Options |
|-----------|-------|---------|
| **Produire** | Sparkles | Email pro, Post LinkedIn, Proposition commerciale, Document Word, Présentation PPT, Tableur Excel, Image IA GPT, Image IA Gemini |
| **Comprendre** | Brain | Fichier Excel, Document PDF, Site web, Marché, Outil IA, Concept, Best practices |
| **Organiser** | GitBranch | Réunion, Projet, Semaine, Objectifs, Workflow |
| **Personnaliser** | Plus | Créer une commande, Créer une skill, Créer une automatisation |

Clique sur une catégorie, puis choisis une sous-option. Le prompt se pré-remplit dans le champ de saisie - tu n'as plus qu'à compléter les `[placeholders]` et envoyer.

---

### 5. Board de Décision (Cmd+D / Ctrl+D)

Pour tes décisions stratégiques, convoque un **board de 5 conseillers IA**. Chaque conseiller a une personnalité et un angle d'analyse distincts :

| Conseiller | Rôle | Provider préféré |
|------------|------|-----------------|
| L'Analyste | Données, chiffres, ROI, métriques | Anthropic (Claude) |
| Le Stratège | Vision long terme, positionnement | OpenAI (GPT) |
| L'Avocat du Diable | Contre-arguments, risques | Anthropic (Claude) |
| Le Pragmatique | Faisabilité, actions concrètes | Mistral |
| Le Visionnaire | Innovation, tendances futures | Gemini |

**Comment tester** :
1. Appuie sur `Cmd+D` sur macOS / `Ctrl+D` sur Windows (ou utilise la palette de commandes)
2. Pose ta question stratégique (ex: "Dois-je lancer une formation en ligne à 490 euros ?")
3. Ajoute un contexte optionnel
4. Lance la délibération
5. Observe chaque conseiller répondre en streaming
6. Lis la **synthèse** avec les points de consensus, divergences et recommandation finale

**Note** : si un provider n'est pas configuré (pas de clé API), le conseiller utilise automatiquement ton provider par défaut.

L'historique des décisions est sauvegardé et consultable.

---

### 6. Calculateurs financiers et décisionnels

Accessibles via l'API, ces calculateurs aident à la prise de décision chiffrée :

| Calculateur | Formule | Usage |
|-------------|---------|-------|
| **ROI** | (Gain - Investissement) / Investissement x 100 | Évaluer le rendement d'un investissement |
| **ICE** | Impact x Confidence x Ease | Prioriser des idées/tâches (score 1-10 par critère) |
| **RICE** | (Reach x Impact x Confidence%) / Effort | Prioriser des fonctionnalités produit |
| **NPV** | -Investissement + somme(CF / (1+r)^t) | Valeur actuelle nette d'un projet |
| **Break-even** | Coûts fixes / (Prix - Coût variable) | Seuil de rentabilité en unités |

Chaque calculateur retourne le résultat chiffré et une **interprétation en français**.

---

### 7. Recherche Web

THÉRÈSE peut chercher des informations actuelles sur le web pour répondre à tes questions.

**Comportement selon le provider** :
- **Gemini** : utilise le Google Search Grounding nativement
- **Autres providers** (Claude, GPT, Mistral, Grok) : utilisent un tool DuckDuckGo (gratuit, sans clé API)

**Activation** : Paramètres -> LLM -> Toggle "Recherche Web"

**Ce que tu peux tester** : pose une question d'actualité (ex: "Quelles sont les dernières annonces d'Apple ?") et observe THÉRÈSE chercher sur le web avant de répondre.

---

### 8. Transcription vocale (dictée)

Dicte tes messages au lieu de les taper. THÉRÈSE utilise **Groq Whisper** (modèle whisper-large-v3-turbo) pour transcrire l'audio en texte français.

**Configuration requise** :
- Clé API Groq (gratuite sur [console.groq.com](https://console.groq.com))
- À configurer dans Paramètres -> LLM -> Transcription vocale (préfixe `gsk_`)

**Comment tester** :
1. Clique sur le bouton **micro** à droite du champ de saisie
2. Parle (le bouton pulse en rouge pendant l'enregistrement)
3. Clique à nouveau pour arrêter
4. Le texte transcrit apparaît dans le champ de saisie

**Limitation** : la dictée vocale n'est **pas disponible** dans l'application desktop Tauri (restriction WebView). Elle fonctionne en mode web (`http://localhost:1420` dans un navigateur).

---

### 9. Génération d'images

THÉRÈSE génère des images via deux providers :

| Provider | Modèle | Résolutions | Clé API |
|----------|--------|-------------|---------|
| **GPT Image 1.5** | gpt-image-1.5 | 1024x1024, 1536x1024, 1024x1536 | Clé OpenAI (séparée de celle du LLM) |
| **Nano Banana Pro** | gemini-3-pro-image-preview | 1K, 2K, 4K | Clé Gemini (séparée de celle du LLM) |

**Comment tester** :
1. Écran d'accueil -> **Produire** -> **Image IA (GPT)** ou **Image IA (Gemini)**
2. Décris l'image souhaitée
3. Télécharge le résultat

**Configuration** : Paramètres -> section "Génération d'images" - les clés API pour les images sont séparées de celles du chat LLM.

---

### 10. MCP Tools (connexion à des services externes)

Le **Model Context Protocol** (MCP) permet à THÉRÈSE de se connecter à des services tiers. Le LLM peut appeler ces tools automatiquement pendant la conversation.

**19 presets disponibles** organisés en 8 catégories :

| Catégorie | Presets |
|-----------|---------|
| **Essentiels** | Filesystem, Fetch, Time |
| **Productivité** | Google Workspace, Notion, Airtable, Todoist, Trello |
| **Recherche** | Brave Search, Perplexity |
| **Marketing** | Brevo |
| **CRM & Ventes** | HubSpot CRM, Pipedrive |
| **Finance** | Stripe |
| **Communication** | WhatsApp Business |
| **Avancé** | Sequential Thinking, Slack, Playwright |

**Comment tester** :
1. Paramètres -> onglet **Tools**
2. Installe un preset (ex: Filesystem pour la gestion de fichiers, aucune clé requise)
3. Démarre le serveur MCP
4. Dans le chat, le LLM peut maintenant utiliser ces tools automatiquement

**Sécurité** : les clés API des serveurs MCP sont chiffrées (Fernet AES-128-CBC + HMAC) et stockées dans `~/.therese/mcp_servers.json`. Sur macOS, la clé de chiffrement est protégée par le Keychain.

---

### 11. CRM Sync (synchronisation Google Sheets)

THÉRÈSE peut synchroniser tes données CRM depuis un Google Sheets.

**Ce qui est synchronisé** :
- **Clients** : ID, Nom, Entreprise, Email, Téléphone, Source, Stage, Score, Tags
- **Projets** : ID, Client lié, Nom, Description, Statut, Budget
- **Livrables** : ID, Projet lié, Titre, Description, Statut, Date d'échéance

**Configuration** : Paramètres -> Données -> Synchronisation CRM -> renseigne ton Spreadsheet ID.

---

### 12. Panneaux auxiliaires (fenêtres séparées)

THÉRÈSE ouvre certains panneaux dans des **fenêtres indépendantes** (la fenêtre de chat reste intacte) :

| Panneau | Raccourci macOS | Raccourci Windows | Description |
|---------|----------------|-------------------|-------------|
| **Email** | `Cmd+E` | `Ctrl+E` | Intégration Gmail |
| **Calendrier** | `Cmd+Shift+C` | `Ctrl+Shift+C` | Google Calendar |
| **Tâches** | `Cmd+T` | `Ctrl+T` | Kanban de tâches |
| **Factures** | `Cmd+I` | `Ctrl+I` | Gestion de factures |
| **CRM Pipeline** | `Cmd+P` | `Ctrl+P` | Vue pipeline CRM |

**Note** : ces panneaux sont fonctionnels en mode standalone. Les données sont persistées via localStorage et se rechargent instantanément à la réouverture.

---

## Raccourcis clavier

### Chat

| Raccourci macOS | Raccourci Windows | Action |
|----------------|-------------------|--------|
| `Entrée` | `Entrée` | Envoyer le message |
| `Shift+Entrée` | `Shift+Entrée` | Nouvelle ligne |
| `Cmd+N` | `Ctrl+N` | Nouvelle conversation |
| `Cmd+Suppr` | `Ctrl+Suppr` | Effacer la conversation |

### Navigation

| Raccourci macOS | Raccourci Windows | Action |
|----------------|-------------------|--------|
| `Cmd+K` | `Ctrl+K` | Palette de commandes |
| `Cmd+/` | `Ctrl+/` | Afficher les raccourcis clavier |
| `Cmd+B` | `Ctrl+B` | Sidebar conversations |
| `Cmd+M` | `Ctrl+M` | Espace de travail (mémoire) |
| `Échap` | `Échap` | Fermer le panneau actif |

### Fonctionnalités

| Raccourci macOS | Raccourci Windows | Action |
|----------------|-------------------|--------|
| `Cmd+D` | `Ctrl+D` | Board de décision |
| `Cmd+E` | `Ctrl+E` | Email (Gmail) |
| `Cmd+T` | `Ctrl+T` | Tâches (Kanban) |
| `Cmd+I` | `Ctrl+I` | Factures |
| `Cmd+P` | `Ctrl+P` | CRM Pipeline |

### Outils

| Raccourci macOS | Raccourci Windows | Action |
|----------------|-------------------|--------|
| `Cmd+Shift+C` | `Ctrl+Shift+C` | Calendrier (Google Calendar) |
| `Cmd+Shift+P` | `Ctrl+Shift+P` | Nouveau projet |
| `Cmd+Shift+F` | `Ctrl+Shift+F` | Rechercher en mémoire |

### Fichiers

| Raccourci macOS | Raccourci Windows | Action |
|----------------|-------------------|--------|
| `Cmd+O` | `Ctrl+O` | Ouvrir un fichier |
| `Cmd+Shift+O` | `Ctrl+Shift+O` | Ouvrir un dossier |
| `Cmd+S` | `Ctrl+S` | Sauvegarder |

---

## Limitations connues (version alpha)

### Application desktop

- **Dictée vocale non disponible dans l'app Tauri** : c'est une limitation du WebView macOS. La dictée fonctionne en mode web via un navigateur (`http://localhost:1420`).
- **Pas de code signing macOS** : au premier lancement du `.app`, macOS affiche un avertissement Gatekeeper ("application non vérifiée"). Pour l'ouvrir : clic droit -> Ouvrir, puis confirmer.
- **Pas de notifications push** : les notifications ne sont pas encore implémentées.
- **Le build Tauri nécessite Xcode CLI tools (macOS)** : installe-les avec `xcode-select --install` avant de compiler. Sur Windows, il faut Visual Studio Build Tools.

### Fonctionnalités

- **Email Gmail** : nécessite une configuration OAuth Google (voir Paramètres > Email).
- **Panneaux Email et Calendrier** : nécessitent une configuration OAuth Google fonctionnelle.
- **Ollama** : nécessite qu'Ollama soit installé et lancé localement (`ollama serve`).
- **MCP Servers** : certains presets nécessitent des packages npm globaux. En cas d'erreur au démarrage, vérifie que `npx` est dans ton PATH.

### Performance

- **Premier embedding** : le chargement initial du modèle d'embeddings (nomic-embed-text) prend quelques secondes.
- **Gros fichiers** : l'indexation de fichiers volumineux peut prendre du temps (chunking par blocs de 1000 caractères).

---

## Comment remonter un bug

Pour nous aider à corriger rapidement, merci de fournir les informations suivantes :

### 1. Étapes pour reproduire

Décris précisément ce que tu as fait, étape par étape. Par exemple :
> 1. J'ai ouvert l'application
> 2. J'ai tapé "Crée un document Word sur le marketing digital"
> 3. J'ai cliqué sur Envoyer
> 4. Le spinner tourne indéfiniment sans résultat

### 2. Comportement attendu vs comportement observé

> **Attendu** : un fichier .docx est généré et téléchargeable
> **Observé** : erreur 500 dans la console, aucun fichier créé

### 3. Environnement technique

Merci de préciser :
- **Provider LLM** utilisé (ex: Anthropic Claude Opus 4.5)
- **Modèle** exact (ex: `claude-opus-4-5-20251101`)
- **Version OS** (ex: macOS 15.3 ou Windows 11 24H2)
- **Mode** : app Tauri ou navigateur web ?

### 4. Captures d'écran et logs

- Une **capture d'écran** de l'erreur (si visible à l'écran)
- Les **logs backend** si possibles (dans le terminal où tourne uvicorn)
- Les **logs console navigateur** (clic droit -> Inspecter -> Console)

### Modèle de rapport de bug

```
## Bug : [titre court]

**Étapes** :
1. ...
2. ...
3. ...

**Attendu** : ...
**Observé** : ...

**Provider LLM** : [provider] / [modèle]
**OS** : [ex: macOS 15.3 ou Windows 11 24H2]
**Mode** : Tauri / Web

**Logs** :
[copier-coller les erreurs ici]

**Capture** :
[joindre si possible]
```

---

## FAQ rapide

**Q : Où sont stockées mes données ?**
R : Tout est local dans `~/.therese/` (base SQLite, embeddings Qdrant, images générées, backups).

**Q : Mes conversations sont-elles envoyées quelque part ?**
R : Uniquement au provider LLM que tu as choisi (Anthropic, OpenAI, etc.) pour obtenir les réponses. Si tu utilises Ollama, tout reste 100% local.

**Q : Comment changer de provider LLM ?**
R : Paramètres (icône engrenage) -> onglet LLM -> sélectionne un autre provider et renseigne ta clé API.

**Q : Comment exporter mes données ?**
R : Paramètres -> onglet Données. Tu peux exporter tes conversations (JSON ou Markdown) ou toutes tes données (export RGPD).

**Q : Le board de décision utilise plusieurs LLMs en même temps ?**
R : Oui ! Chaque conseiller a un provider préféré. Si le provider n'est pas configuré, il utilise ton provider par défaut. Plus tu configures de providers, plus les avis seront diversifiés.

**Q : THÉRÈSE fonctionne sur Windows ?**
R : Oui ! Télécharge le `.exe` depuis les [GitHub Releases](https://github.com/ludovicsanchez38-creator/Synoptia-THERESE/releases). Les raccourcis utilisent `Ctrl` au lieu de `Cmd`.

**Q : J'ai une idée d'amélioration, où la proposer ?**
R : Partage ton idée sur le salon **#suggestions** sur Discord, ou envoie un email à ludo@synoptia.fr.

---

Merci de participer à cette phase alpha ! Tes retours font la différence.

**Synoptïa** - "Humain d'abord, IA en soutien."
