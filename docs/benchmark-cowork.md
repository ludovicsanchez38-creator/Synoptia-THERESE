# Benchmark Cowork (Anthropic)

> Document généré pour THÉRÈSE v2
> Date : 21 janvier 2026

## Statut

🟢 Complété

---

## 1. Vue d'ensemble

### Qu'est-ce que Cowork ?

**Cowork** est un agent desktop lancé par Anthropic le **12 janvier 2026**. C'est essentiellement "Claude Code pour le reste du travail" - une interface simplifiée qui permet à Claude d'accéder aux fichiers locaux et d'exécuter des tâches autonomes.

### Positionnement

- **Cible** : Utilisateurs non-techniques (vs Claude Code pour les devs)
- **Promesse** : Un "collègue virtuel" qui travaille sur vos fichiers pendant que vous faites autre chose
- **Tagline implicite** : "Déléguez vos tâches répétitives à Claude"

### Disponibilité

| Date | Accès | Prix |
|------|-------|------|
| 12 janv. 2026 | Claude Max uniquement | $100-200/mois |
| 16 janv. 2026 | Étendu à Claude Pro | $20/mois |
| À venir | Windows | - |

**Plateforme** : macOS uniquement (utilise Apple Virtualization Framework)

### Origine

Anthropic a remarqué que les utilisateurs de Claude Code "forçaient" l'outil de coding à faire des tâches non-coding. Cowork est né de ce constat. Fait remarquable : **4 ingénieurs ont construit Cowork en ~10 jours** en utilisant Claude Code lui-même.

---

## 2. Fonctionnalités détaillées

### 2.1 Accès aux fichiers locaux

| Champ | Description |
|-------|-------------|
| **Nom** | File System Access |
| **Description** | L'utilisateur désigne un dossier, Claude peut lire/modifier/créer des fichiers dedans |
| **Déclencheur** | Configuration initiale + instructions via chat |
| **Output** | Fichiers modifiés, nouveaux fichiers créés, fichiers organisés |
| **Limitation** | Sandbox isolé, pas d'accès au système complet |

**Formats supportés** : PDF, DOCX, TXT, MD, images, CSV, etc.

### 2.2 Exécution autonome

| Champ | Description |
|-------|-------------|
| **Nom** | Autonomous Task Execution |
| **Description** | Claude travaille en autonomie sur des tâches multi-étapes |
| **Déclencheur** | Instruction utilisateur ("organise mes téléchargements") |
| **Output** | Tâche complétée, rapport de ce qui a été fait |
| **Limitation** | Peut tourner pendant des heures, consomme beaucoup de tokens |

**Cas d'usage typiques** :
- Renommer et trier des fichiers
- Extraire données d'images (reçus → spreadsheet)
- Rédiger un rapport à partir de notes dispersées
- Traiter plusieurs tâches en parallèle

### 2.3 Intégration navigateur (Claude in Chrome)

| Champ | Description |
|-------|-------------|
| **Nom** | Browser Automation |
| **Description** | Couplé avec l'extension Chrome, Claude peut naviguer le web |
| **Déclencheur** | Tâches nécessitant accès web |
| **Output** | Actions web (remplir formulaires, extraire données) |
| **Limitation** | Requiert l'extension Chrome séparée |

### 2.4 Connecteurs (Data Connectors)

| Champ | Description |
|-------|-------------|
| **Nom** | Integrations |
| **Description** | Connexion à des services tiers |
| **Déclencheur** | Configuration dans les settings |
| **Output** | Accès aux données des services connectés |
| **Limitation** | GSuite non supporté, connecteurs parfois instables |

**Connecteurs disponibles** : Asana, Notion, Gmail (buggy)

### 2.5 Skills (création de documents)

| Champ | Description |
|-------|-------------|
| **Nom** | Skills |
| **Description** | Templates pour améliorer création de documents/présentations |
| **Déclencheur** | Demande de création de document |
| **Output** | Documents mieux formatés |
| **Limitation** | Set initial limité |

---

## 3. Architecture technique

### Stack

```
┌─────────────────────────────────────────┐
│           Claude Desktop App            │
│              (macOS only)               │
├─────────────────────────────────────────┤
│         VZVirtualMachine (VM)           │
│      Apple Virtualization Framework     │
├─────────────────────────────────────────┤
│     Custom Linux Root Filesystem        │
│         (sandbox isolé)                 │
├─────────────────────────────────────────┤
│           Claude Agent SDK              │
│         (même base que Claude Code)     │
├─────────────────────────────────────────┤
│         Claude Opus 4.5 API             │
│      (extended thinking 64K tokens)     │
└─────────────────────────────────────────┘
```

### Sécurité (modèle déclaré)

- **Scoped Access** : Claude n'accède qu'aux dossiers explicitement partagés
- **Human-in-the-Loop** : Validation requise pour actions à haut risque (suppressions massives, communications externes)
- **VM Isolation** : Exécution dans une machine virtuelle isolée
- **Network Restricted** : Requêtes réseau bloquées (sauf API Anthropic)

---

## 4. Parcours utilisateur type

```
1. Installation
   └─ Télécharger Claude Desktop (macOS)
   └─ S'abonner à Claude Pro ($20) ou Max ($100-200)

2. Configuration
   └─ Activer Cowork dans les settings
   └─ Désigner un dossier de travail
   └─ (Optionnel) Connecter services tiers

3. Première utilisation
   └─ Donner une instruction : "Organise mes téléchargements"
   └─ Claude analyse le dossier
   └─ Claude propose un plan
   └─ Claude exécute (peut prendre du temps)
   └─ Résultats visibles dans le dossier

4. Usage quotidien
   └─ Déposer des fichiers dans le dossier partagé
   └─ Donner des instructions via chat
   └─ Laisser Claude travailler en autonomie
   └─ Revenir voir les résultats
```

**Time to first value** : ~5-10 minutes (installation + config + première tâche)

---

## 5. Forces à répliquer

### 5.1 Accès fichiers local-first
L'approche "désigne un dossier, je travaille dedans" est intuitive et rassurante côté vie privée.

### 5.2 Autonomie longue durée
Pouvoir lancer une tâche et revenir plus tard est un vrai différenciateur vs chat classique.

### 5.3 Sub-agents parallèles
Cowork peut créer des sous-agents qui travaillent en parallèle, chacun avec son propre contexte. Permet des tâches plus larges sans saturer le contexte.

### 5.4 Interface simplifiée
Pas de terminal, pas de code. Interface chat familière.

### 5.5 Intégration desktop native
System tray, raccourcis, expérience native macOS.

---

## 6. Faiblesses à exploiter

### 6.1 PAS DE MÉMOIRE PERSISTANTE ⭐

> "Cowork does not have memory retention. Once you close a session, the context is gone. It does not remember your file structure from yesterday."

**C'est LE différenciateur majeur pour THÉRÈSE.**

- Pas de mémoire entre sessions
- Pas d'apprentissage des préférences utilisateur
- Doit réexpliquer le contexte à chaque fois
- Pas de "connaissance" des clients, projets, contacts

### 6.2 Pas de synchronisation

- Desktop only (pas de web, pas de mobile)
- Pas de sync entre appareils
- Pas de partage de sessions/artifacts

### 6.3 Consommation tokens excessive

> "Reddit users have colorfully described the token usage as a 'wood chipper'."

- Une simple tâche peut générer des milliers de tokens
- Loop planning → executing → checking → replanning
- Coût imprévisible pour l'utilisateur

### 6.4 Stabilité limitée

- "The 30-Minute Wall" : sessions qui dégradent après ~30 min
- Application devient sluggish
- Connecteurs Gmail buggy

### 6.5 macOS only

- Pas de Windows (annoncé "coming soon")
- Exclut une grande partie des utilisateurs potentiels

### 6.6 Incompatibilités

- Pas de GSuite
- Projects, chat sharing, artifact sharing ne fonctionnent pas
- Pas de switch entre Cowork et chat normal mid-conversation

### 6.7 Prix élevé pour un "research preview"

- $20-200/mois pour un produit en preview
- Rapport coût/valeur questionnable

---

## 7. Vulnérabilités de sécurité connues

### Files API Exfiltration (critique)

**Source** : [PromptArmor - 15 janvier 2026](https://www.promptarmor.com/resources/claude-cowork-exfiltrates-files)

**Le problème** :
- Un attaquant peut cacher des instructions malveillantes dans un document (.docx)
- Instructions invisibles (police 1pt, blanc sur blanc)
- Quand Cowork analyse le fichier, l'injection se déclenche
- Le fichier peut exfiltrer des données vers l'API Anthropic (seul domaine autorisé)

**Détails techniques** :
- La VM bloque les requêtes réseau SAUF vers l'API Anthropic
- L'attaque utilise un curl vers l'API file upload d'Anthropic
- Fonctionne même sur Claude Opus 4.5 (le plus capable)

**Statut** : Vulnérabilité connue depuis octobre 2025 (Claude Code), non corrigée au lancement de Cowork.

**Réponse Anthropic** : "We've built sophisticated defenses against prompt injections, but agent safety is still an active area of development."

### Implication pour THÉRÈSE

- Opportunité de faire mieux en sécurité
- Ne pas faire confiance aveugle aux fichiers uploadés
- Sandboxing strict + validation des actions sensibles

---

## 8. Retours utilisateurs

### Positifs

- "Game-changer" pour l'organisation de fichiers
- "7 jours de travail en 15 minutes" (cas optimiste)
- Efficace pour les tâches répétitives et les gros datasets
- "Smart product approach" - déverrouille Claude Code pour le grand public

### Négatifs

- **Suppression accidentelle** : Un utilisateur a perdu 11GB de fichiers
- **Complexité cachée** : "It feels like AGI until you try to use it"
- **Pas adapté au workflow cloud** : "If your life is Google Drive, Notion, Slack... you don't have 'a folder' the way Cowork wants"
- **Sécurité** : "Not fair to tell regular non-programmer users to watch out for 'suspicious actions that may indicate prompt injection'"

### HackerNews (scepticisme)

- "3 months ago, Skills were the next big thing. In 3 months there will be yet another new Anthropic positioning."
- Fatigue des annonces successives

---

## 9. Opportunités pour THÉRÈSE

### 9.1 Mémoire persistante (différenciateur #1)

Ce que THÉRÈSE doit faire mieux :
- Souvenir des contacts/clients (mini-CRM)
- Souvenir des projets en cours
- Souvenir des préférences utilisateur
- Apprentissage progressif du contexte métier
- Recherche dans l'historique des conversations

### 9.2 Souveraineté des données

- 100% local (pas de VM cloud)
- Pas de dépendance à l'API Anthropic pour le stockage
- RGPD-friendly (export/suppression facile)
- Transparence sur ce qui est envoyé au LLM

### 9.3 UX pensée solopreneur

- Pas besoin d'un "dossier" physique
- Intégration Google Drive/Notion native
- Vue CRM contacts intégrée
- Dashboard projets

### 9.4 Stabilité et prévisibilité

- Pas de "30-minute wall"
- Coûts prévisibles (ou usage local)
- Sessions qui persistent

### 9.5 Cross-platform dès le départ

- macOS + Windows + Linux
- (Optionnel) Progressive web app

### 9.6 Sécurité renforcée

- Validation stricte des fichiers uploadés
- Pas d'exécution automatique de commandes depuis fichiers
- Audit log des actions
- Confirmation explicite pour actions sensibles

### 9.7 Marché français

- Interface et docs en français
- Compréhension du contexte business français (TVA, URSSAF, etc.)
- Support/communauté francophone

---

## 10. Tableau comparatif Cowork vs THÉRÈSE (cible)

| Critère | Cowork | THÉRÈSE (cible) |
|---------|--------|-----------------|
| **Mémoire persistante** | ❌ Non | ✅ Oui |
| **Plateforme** | macOS only | Cross-platform |
| **Données** | VM cloud | 100% local |
| **Prix** | $20-200/mois | À définir (freemium?) |
| **Langue** | Anglais | Français natif |
| **Intégrations** | Limitées, buggy | Google Drive, Notion |
| **Vue CRM** | ❌ Non | ✅ Oui |
| **Stabilité** | 30-min wall | Stable |
| **Sécurité fichiers** | Vulnérable | Renforcée |
| **Open source** | ❌ Non | À définir |

---

## 11. Sources

- [VentureBeat - Anthropic launches Cowork](https://venturebeat.com/technology/anthropic-launches-cowork-a-claude-desktop-agent-that-works-in-your-files-no)
- [TechCrunch - Anthropic's new Cowork tool](https://techcrunch.com/2026/01/12/anthropics-new-cowork-tool-offers-claude-code-without-the-code/)
- [Simon Willison - First impressions of Claude Cowork](https://simonwillison.net/2026/Jan/12/claude-cowork/)
- [PromptArmor - Claude Cowork Exfiltrates Files](https://www.promptarmor.com/resources/claude-cowork-exfiltrates-files)
- [The Register - Anthropic's Files API vulnerability](https://www.theregister.com/2026/01/15/anthropics_claude_bug_cowork/)
- [Claude Help Center - Getting Started with Cowork](https://support.claude.com/en/articles/13345190-getting-started-with-cowork)
- [Claude Help Center - Using Cowork Safely](https://support.claude.com/en/articles/13364135-using-cowork-safely)
- [HackerNews - First impressions of Claude Cowork](https://news.ycombinator.com/item?id=46612919)

---

## 12. Conclusion

Cowork est un produit prometteur mais immature. Son **absence de mémoire persistante** est une faiblesse majeure que THÉRÈSE peut exploiter comme différenciateur principal.

Les autres opportunités (souveraineté, cross-platform, stabilité, sécurité, marché français) sont des avantages compétitifs secondaires mais significatifs.

**Recommandation** : Positionner THÉRÈSE comme "Cowork + mémoire + souveraineté" avec une UX premium pensée pour les solopreneurs français.

---

*Document généré le 21 janvier 2026*
*THÉRÈSE v2 - Synoptïa*
