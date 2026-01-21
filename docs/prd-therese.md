# PRD - THÉRÈSE v2

> Document généré par l'agent PM (BMAD)
> Date : 21 janvier 2026

## Statut

🟢 Complété

---

## 1. Executive Summary

**Problème** : Les assistants IA desktop (Cowork) n'ont pas de mémoire persistante. Chaque session repart à zéro. L'utilisateur doit réexpliquer son contexte, ses clients, ses projets à chaque fois.

**Solution** : THÉRÈSE est une assistante desktop souveraine avec **mémoire persistante**. Elle connaît tes clients, tes projets, tes préférences - même hors ligne. Toutes les données restent sur ta machine.

**Différenciateurs** :
1. **Mémoire persistante** (Cowork n'en a pas)
2. **100% souverain** (données locales, RGPD-friendly)
3. **UX premium** pensée solopreneur français

**Cible** : Solopreneurs et TPE français qui jonglent entre prospection, delivery et admin.

**Tagline** : "Ta mémoire, tes données, ton business."

---

## 2. Persona principal

### Ludo, 40 ans - Consultant IA/automation

```yaml
profile:
  nom: Ludo
  âge: 40 ans
  localisation: Manosque, France
  structure: SARL-U (solo)
  secteur: Conseil IA, automation, formation

parcours:
  - Ex-directeur d'agence bancaire (10 ans)
  - Reconversion entrepreneur 2025
  - Formateur international Office/SharePoint

contexte_travail:
  journée_type:
    - Prospection LinkedIn (matin)
    - Delivery clients (journée)
    - Admin/compta (soir)
  outils_actuels:
    - Google Workspace (ERP maison)
    - Claude Pro/Code (IA principale)
    - n8n (automation)
    - Airtable/Notion (données)
  nb_clients_actifs: 5-10
  nb_prospects: ~30
```

### Frustrations actuelles

| Frustration | Impact | Fréquence |
|-------------|--------|-----------|
| Répéter le contexte à Claude à chaque session | Perte de temps, friction | Quotidien |
| Contexte client dispersé (mails, docs, notes) | Réponses génériques | À chaque RDV |
| Pas d'assistant qui "connaît" le business | Opportunités ratées | Permanent |
| Dépendance cloud (vie privée, coûts API) | Risque souveraineté | Continu |

### Ce qu'il veut

> "Je veux UN assistant qui sait tout de mon business. Mes clients, mes projets, mes tarifs, mes préférences. Qui me reconnaît quand j'ouvre l'app, pas un chatbot amnésique."

### Jobs to be done

1. **Quand** je prépare un RDV client, **je veux** avoir tout le contexte (historique, projets, notes) **pour** être pertinent et pro
2. **Quand** je reçois une demande entrante, **je veux** qualifier rapidement le prospect **pour** répondre vite et bien
3. **Quand** je travaille sur un livrable, **je veux** retrouver mes fichiers et conversations liées **pour** être efficace
4. **Quand** je voyage ou suis offline, **je veux** accéder à mon historique **pour** rester productif

---

## 3. User Stories MVP

### 3.1 Must-Have (v1.0) - MVP Release

| ID | Story | Priorité |
|----|-------|----------|
| **US-001** | En tant que Ludo, je veux discuter avec THÉRÈSE pour obtenir de l'aide sur mes tâches quotidiennes | P0 |
| **US-002** | En tant que Ludo, je veux que THÉRÈSE se souvienne de mes clients et projets sans que je répète tout | P0 |
| **US-003** | En tant que Ludo, je veux que THÉRÈSE accède à mes fichiers locaux pour les analyser | P0 |
| **US-004** | En tant que Ludo, je veux voir le contexte/mémoire actif pour savoir ce que THÉRÈSE "sait" | P0 |
| **US-005** | En tant que Ludo, je veux que mes données restent sur ma machine | P0 |
| **US-006** | En tant que Ludo, je veux utiliser des raccourcis clavier pour être efficace | P0 |
| **US-007** | En tant que Ludo, je veux une interface dark mode premium, pas un chat générique | P0 |

### 3.2 Should-Have (v1.1) - Fast Follow

| ID | Story | Priorité |
|----|-------|----------|
| **US-101** | En tant que Ludo, je veux créer/éditer/supprimer des éléments de mémoire manuellement | P1 |
| **US-102** | En tant que Ludo, je veux rechercher dans ma mémoire (clients, projets, conversations) | P1 |
| **US-103** | En tant que Ludo, je veux exporter/backup ma mémoire pour sécuriser mes données | P1 |
| **US-104** | En tant que Ludo, je veux des rappels et suivis de tâches | P1 |
| **US-105** | En tant que Ludo, je veux connecter mon Google Drive pour analyser mes docs cloud | P1 |

### 3.3 Nice-to-Have (v2.0) - Future

| ID | Story | Priorité |
|----|-------|----------|
| **US-201** | En tant que Ludo, je veux utiliser un LLM 100% local (offline mode) | P2 |
| **US-202** | En tant que Ludo, je veux une vue CRM de mes contacts avec historique enrichi | P2 |
| **US-203** | En tant que Ludo, je veux déclencher des automatisations n8n depuis THÉRÈSE | P2 |
| **US-204** | En tant que Ludo, je veux synchroniser ma mémoire entre plusieurs machines | P2 |
| **US-205** | En tant que Ludo, je veux partager des "skills" THÉRÈSE avec d'autres utilisateurs | P2 |

---

## 4. Fonctionnalités MVP détaillées

### 4.1 Chat intelligent (US-001)

```yaml
feature: Chat Core
description: Interface de conversation principale avec le LLM
composants:
  - Zone d'input avec markdown support
  - Affichage messages (user/assistant)
  - Streaming des réponses en temps réel
  - Support markdown/code blocks dans les réponses
  - Copier/coller facile (bouton sur chaque message)
  - Historique session (scroll up)

interactions:
  - Entrée = envoyer message
  - ⌘+K = command palette
  - ⌘+N = nouvelle conversation
  - ⌘+/ = raccourcis clavier
  - Shift+Enter = nouvelle ligne

ux:
  - Max 80ch width pour lisibilité
  - Typing indicator pendant génération
  - Smooth scroll auto vers nouveau message
```

### 4.2 Mémoire persistante (US-002, US-004)

```yaml
feature: Persistent Memory
description: THÉRÈSE se souvient entre les sessions

entités_mémoire:
  contacts:
    - Nom, prénom, entreprise
    - Email, téléphone
    - Notes libres
    - Historique interactions
    - Tags (client, prospect, partenaire)

  projets:
    - Nom, description
    - Client associé
    - Statut (en cours, terminé, en attente)
    - Budget/tarif
    - Fichiers liés
    - Notes et conversations

  préférences:
    - Ton de communication
    - Formats préférés
    - Outils utilisés
    - Contraintes (horaires, tarifs)

stockage:
  structured_data: SQLite (contacts, projets, metadata)
  semantic_search: Qdrant (embeddings conversations/notes)
  working_context: CLAUDE.md (session active)

extraction_auto:
  - Détection noms/entreprises mentionnés
  - Extraction dates et montants
  - Identification projets évoqués
  - Suggestion "Ajouter à la mémoire ?"

ui:
  - Panneau latéral "Contexte actif"
  - Badges entités dans le chat
  - Preview mémoire au hover
  - ⌘+M = toggle panneau mémoire
```

### 4.3 Accès fichiers (US-003)

```yaml
feature: Local File Access
description: Analyser et indexer les fichiers locaux

formats_supportés:
  lecture:
    - PDF (extraction texte)
    - DOCX, DOC
    - TXT, MD
    - Images (OCR basique)
    - CSV, XLSX (tableau)

interactions:
  - Drag & drop sur le chat
  - Bouton "Joindre fichier"
  - File browser intégré
  - Chat: "Résume ce PDF", "Extrait les contacts de ce doc"

indexation:
  - Option "Ajouter à la mémoire"
  - Extraction metadata (titre, date, auteur)
  - Chunking intelligent
  - Embedding et stockage Qdrant

sécurité:
  - Sandbox Tauri (accès limité au dossier choisi)
  - Pas d'upload vers le cloud
  - Fichiers restent sur disque
```

### 4.4 UX Premium (US-006, US-007)

```yaml
feature: Premium Dark UI
description: Interface élégante et efficace

design_system:
  tokens:
    background: "#0B1226"
    surface: "#131B35"
    text_primary: "#E6EDF7"
    text_muted: "#B6C7DA"
    accent_cyan: "#22D3EE"
    accent_magenta: "#E11D8D"

  typography:
    font_sans: "Inter, system-ui"
    font_mono: "JetBrains Mono"

  effects:
    glassmorphism: "backdrop-blur-xl bg-white/5"
    glow: "shadow-[0_0_20px_rgba(34,211,238,0.15)]"
    border: "border border-white/10"

raccourcis_clavier:
  global:
    - ⌘+K: Command palette
    - ⌘+N: Nouvelle conversation
    - ⌘+M: Toggle mémoire
    - ⌘+,: Settings
    - ⌘+Q: Quitter
    - Ctrl+Space: Activer THÉRÈSE (global)

  chat:
    - Enter: Envoyer
    - Shift+Enter: Nouvelle ligne
    - ⌘+↑: Message précédent
    - Escape: Annuler

  navigation:
    - ⌘+1: Chat
    - ⌘+2: Mémoire
    - ⌘+3: Fichiers
    - ⌘+4: Settings

animations:
  - Fade-in messages (200ms)
  - Typing indicator pulsing
  - Hover glow sur boutons
  - Slide-in panneau mémoire
  - Ripple sur click

accessibilité:
  - WCAG 2.1 AA minimum
  - Contraste 7:1 texte principal
  - Navigation clavier complète
  - Screen reader support
  - Reduced motion option
```

### 4.5 Souveraineté données (US-005)

```yaml
feature: Data Sovereignty
description: 100% local, RGPD-friendly

architecture:
  stockage: "$HOME/.therese/" (macOS/Linux) ou "%APPDATA%/therese" (Windows)
  base_sqlite: "therese.db"
  vectors_qdrant: "qdrant_data/"
  config: "config.toml"

api_llm:
  - Clé API Claude fournie par l'utilisateur
  - Seules les requêtes LLM sortent
  - Pas de télémétrie, pas d'analytics cloud
  - Option Mistral API (EU) ou Ollama (100% local)

rgpd:
  - Export complet (JSON/SQLite)
  - Suppression totale (dossier)
  - Pas de données envoyées à Synoptïa
  - Audit log des actions (optionnel)

offline_mode:
  v1: Non (requiert API)
  v2: Oui avec Ollama (LLM local)
```

---

## 5. Hors scope MVP

| Fonctionnalité | Raison exclusion | Version cible |
|----------------|------------------|---------------|
| Application mobile | Desktop-first, complexité | v3.0+ |
| Collaboration multi-utilisateurs | Cas d'usage différent | v3.0+ |
| LLM 100% local (Ollama) | Complexité, perf variable | v2.0 |
| Intégrations tierces (sauf fichiers) | Focus core value | v1.1+ |
| Automatisations n8n intégrées | Scope trop large | v2.0 |
| Vue CRM complète | MVP = mémoire contacts simple | v2.0 |
| Synchronisation multi-device | Complexité cloud | v2.5 |
| Marketplace skills | Écosystème à construire | v3.0 |
| Voice input/output | Accessibilité secondaire | v2.0 |
| Plugin system | Architecture à stabiliser | v2.0 |

---

## 6. Stack technique

### 6.1 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                      THÉRÈSE Desktop                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐    ┌─────────────────────────────────────┐ │
│  │   Tauri 2.0     │    │        React 19 Frontend            │ │
│  │   (Rust shell)  │◄──►│  - Chat UI                          │ │
│  │   - File access │    │  - Memory Panel                     │ │
│  │   - System tray │    │  - File Browser                     │ │
│  │   - Shortcuts   │    │  - Settings                         │ │
│  │   - Packaging   │    │  - Command Palette                  │ │
│  └────────┬────────┘    └─────────────────┬───────────────────┘ │
│           │                               │                      │
│           └───────────────┬───────────────┘                      │
│                          IPC                                     │
│           ┌───────────────▼───────────────┐                      │
│           │    Python FastAPI Backend     │                      │
│           │    (sidecar process)          │                      │
│           │    - Memory service           │                      │
│           │    - File processing          │                      │
│           │    - LLM orchestration        │                      │
│           └───────────────┬───────────────┘                      │
│                           │                                      │
│  ┌────────────────────────┼────────────────────────┐            │
│  │                        │                        │            │
│  ▼                        ▼                        ▼            │
│ ┌──────────┐      ┌──────────────┐      ┌─────────────────┐    │
│ │  SQLite  │      │    Qdrant    │      │    LLM API      │    │
│ │ (struct) │      │  (vectors)   │      │ Claude/Mistral  │    │
│ └──────────┘      └──────────────┘      └─────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Choix technologiques

| Couche | Technologie | Justification |
|--------|-------------|---------------|
| **Desktop Shell** | Tauri 2.0 | Bundle léger (5-10 Mo), Rust perf, accès filesystem natif |
| **Frontend** | React 19 + TypeScript | Écosystème riche, Ludo connaît, hot reload |
| **Styling** | TailwindCSS 4 | Rapid prototyping, dark mode natif |
| **State** | Zustand | Simple, performant, pas de boilerplate |
| **Backend** | Python FastAPI | Écosystème IA riche, Ludo connaît |
| **Package Manager** | UV | Rapide, moderne, standards Python |
| **DB Structured** | SQLite | Embarqué, backup facile, standards SQL |
| **DB Vectors** | Qdrant | Performance, self-hosted, hybrid search |
| **LLM Primary** | Claude API | Meilleur rapport qualité/prix, Ludo fan |
| **LLM Fallback** | Mistral API | EU-based, backup, souveraineté |
| **LLM Local** | Ollama (v2) | 100% offline possible |
| **Animations** | Framer Motion | Micro-interactions fluides |
| **Components** | Radix UI | Accessible, unstyled, composable |
| **Icons** | Lucide | Open source, cohérent |

### 6.3 Communication IPC

```yaml
frontend_to_backend:
  protocol: HTTP (localhost:8765)
  format: JSON
  endpoints:
    - POST /chat/send
    - GET /memory/search
    - POST /memory/create
    - GET /files/list
    - POST /files/analyze

backend_to_frontend:
  streaming: Server-Sent Events (SSE)
  events:
    - chat.token (streaming response)
    - memory.updated
    - file.processed

tauri_commands:
  - open_file_dialog
  - read_file
  - get_system_info
  - show_notification
  - toggle_window
```

---

## 7. Métriques de succès

### 7.1 Métriques produit

| Métrique | Cible MVP | Cible v1.1 | Mesure |
|----------|-----------|------------|--------|
| **Time to First Value** | < 3 min | < 2 min | Temps setup → premier message utile |
| **Sessions/semaine** | 5+ | 10+ | Analytics local |
| **Taux rétention J7** | > 40% | > 50% | Utilisateurs actifs J7 / J1 |
| **Mémoire utilisée** | > 50% ajoutent | > 70% | Utilisateurs avec 5+ entités |
| **NPS** | > 30 | > 40 | Survey in-app (optionnel) |

### 7.2 Métriques techniques

| Métrique | Cible | Mesure |
|----------|-------|--------|
| **Latence chat** | < 500ms (hors LLM) | P95 |
| **Latence mémoire search** | < 200ms | P95 |
| **Bundle size** | < 50 Mo | Package final |
| **Memory footprint** | < 300 Mo RAM | Usage moyen |
| **Startup time** | < 2s | Cold start |
| **Crash rate** | < 1% | Sessions avec crash |

### 7.3 Métriques business

| Métrique | Cible Y1 | Mesure |
|----------|----------|--------|
| **Téléchargements** | 1 000+ | GitHub releases |
| **Utilisateurs actifs mensuels** | 200+ | Opt-in analytics |
| **Conversions (si freemium)** | 5% | Upgrade rate |
| **Feedback positifs** | > 80% | Surveys |

---

## 8. Risques et mitigations

### 8.1 Risques produit

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| UX pas assez différenciante | Moyen | Élevé | Tests utilisateurs early, itérations rapides, inspiration Linear/Superhuman |
| Mémoire trop complexe | Élevé | Moyen | Progressive disclosure, onboarding guidé, defaults intelligents |
| Adoption limitée (niche FR) | Moyen | Moyen | Communauté LinkedIn existante, early adopters connus, English docs v2 |
| Cowork ajoute la mémoire | Faible | Élevé | Différenciation UX + souveraineté + marché FR |

### 8.2 Risques techniques

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Performance Qdrant local | Moyen | Moyen | Benchmarks early, fallback SQLite FTS, quantization |
| Dépendance API Claude | Élevé | Moyen | Architecture LLM-agnostic, Mistral fallback, Ollama roadmap |
| Tauri 2.0 instabilités | Faible | Moyen | Pin version stable, Electron fallback ready |
| Cross-platform bugs | Moyen | Moyen | CI/CD multi-OS, beta testers Windows/Linux |

### 8.3 Risques business

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Temps dev sous-estimé | Élevé | Moyen | MVP minimal, cuts scope agressif, stories bien découpées |
| Coûts API Claude | Moyen | Faible | Clé utilisateur, pas de subsidizing, monitoring usage |
| Support/maintenance | Moyen | Moyen | Self-service docs, communauté Discord/Slack, FAQ automatisée |

---

## 9. Roadmap

### Phase 1 : MVP (v1.0) - 8 semaines

```
Sprint 1-2 : Infrastructure
├── Tauri + React setup
├── FastAPI backend
├── SQLite + Qdrant
└── Communication IPC

Sprint 3-4 : Chat Core
├── Interface chat
├── Intégration Claude API
├── Streaming responses
└── Historique session

Sprint 5-6 : Mémoire
├── Schema entités
├── Indexation Qdrant
├── Recherche hybride
├── Panneau contexte UI

Sprint 7-8 : Fichiers + Polish
├── File browser
├── Lecture PDF/DOCX
├── Thème dark
├── Raccourcis clavier
├── Onboarding
```

### Phase 2 : v1.1 - 4 semaines

- CRUD mémoire complet
- Recherche avancée
- Export/backup
- Google Drive (optionnel)
- Bug fixes

### Phase 3 : v2.0 - 8 semaines

- Ollama support (100% local)
- Vue CRM contacts
- Graph relations
- Intégrations (Notion, n8n)

---

## 10. Wireframes

### 10.1 Layout principal

```
┌──────────────────────────────────────────────────────────────────┐
│  ● ● ●   THÉRÈSE                                    ⌘K  👤  ⚙️  │
├──────────┬───────────────────────────────────────────┬───────────┤
│          │                                           │           │
│  Conv.   │           Zone de Chat                    │  Contexte │
│  ────    │                                           │  ─────────│
│  > RDV   │  ┌─────────────────────────────────┐     │           │
│    client│  │ Ludo                            │     │  📋 Actif │
│          │  │ Prépare-moi le brief pour      │     │           │
│  > Factu │  │ le RDV avec Célia demain       │     │  Célia G. │
│          │  └─────────────────────────────────┘     │  ├ FORGER │
│  > Idées │                                           │  └ 580€   │
│          │  ┌─────────────────────────────────┐     │           │
│          │  │ 🤖 THÉRÈSE                      │     │  Pierre H.│
│          │  │                                 │     │  ├ FORGER │
│          │  │ Bien sûr ! Voici le brief      │     │  └ En cours│
│          │  │ pour Célia...                  │     │           │
│          │  │                                 │     │  ─────────│
│          │  │ **Célia Galas**                │     │  📂 Fichier│
│          │  │ - Consultante management       │     │  brief.pdf │
│          │  │ - Session FORGER du 15/01     │     │           │
│          │  │ - Objectif: automatiser...    │     │           │
│          │  │                                 │     │           │
│          │  └─────────────────────────────────┘     │           │
│          │                                           │           │
│          ├───────────────────────────────────────────┤           │
│          │  Message THÉRÈSE...              📎 ➤   │           │
└──────────┴───────────────────────────────────────────┴───────────┘
```

### 10.2 Command Palette (⌘K)

```
┌────────────────────────────────────────────────────┐
│  🔍 Que veux-tu faire ?                           │
├────────────────────────────────────────────────────┤
│                                                    │
│  📝 Actions récentes                              │
│  ├─ Résumer le brief Célia                        │
│  └─ Créer devis Pierre                            │
│                                                    │
│  👥 Contacts                                       │
│  ├─ Célia Galas                                   │
│  ├─ Pierre Heninger                               │
│  └─ + Ajouter contact                             │
│                                                    │
│  📁 Fichiers                                       │
│  ├─ Ouvrir un fichier...                          │
│  └─ Fichiers récents                              │
│                                                    │
│  ⚙️ Paramètres                                    │
│  ├─ Clé API                                       │
│  └─ Préférences                                   │
│                                                    │
│  ──────────────────────────────────────────────── │
│  ⌘N Nouvelle conv.  ⌘M Mémoire  ⌘, Settings     │
└────────────────────────────────────────────────────┘
```

---

## 11. Annexes

### A. Personas secondaires

**Marie, 35 ans - Freelance marketing**
- Gère 15 clients actifs
- Besoin : centraliser les briefs et guidelines
- Pain : oublie les spécificités de chaque client

**Thomas, 45 ans - Artisan plombier**
- 3 salariés, gestion admin lourde
- Besoin : aide devis et relances
- Pain : technophobe mais motivé

### B. Inspirations UX

- **Linear** : Command palette, keyboard-first
- **Superhuman** : Speed, raccourcis, feedback
- **Arc Browser** : Glassmorphism, dark mode
- **Raycast** : Activation globale, extensions
- **Notion** : Slash commands, blocs

### C. Références documents

- [docs/benchmark-cowork.md](./benchmark-cowork.md) - Analyse Cowork
- [docs/benchmark-memoire.md](./benchmark-memoire.md) - État de l'art mémoire IA
- [docs/benchmark-ux.md](./benchmark-ux.md) - Patterns UX

---

## 12. Changelog

| Version | Date | Changements |
|---------|------|-------------|
| 1.0 | 21/01/2026 | Version initiale |

---

*Document généré le 21 janvier 2026*
*THÉRÈSE v2 - Synoptïa*
*"Ta mémoire, tes données, ton business."*
