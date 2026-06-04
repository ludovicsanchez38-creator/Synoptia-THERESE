# Revue produit Thérèse Desktop — État des lieux

**Date** : 2026-06-04 · **Périmètre** : Thérèse Desktop (Server traité plus tard) · **Cible** : solopreneur / TPE
**Méthode** : cartographie lecture seule par 10 agents parallèles (tout le front + back), recoupée avec `docs/benchmark-ux.md` (vision d'origine, jan. 2026), le dump Discord live des testeurs, le backlog UltraJury et les rapports de release.

## 1. Carte des fonctionnalités
| Cluster | Rôle | Maturité |
|---|---|---|
| Onboarding + "Ma journée" | Install → profil → provider → 1er message → dashboard | Solide, sorties fragiles |
| Chat (cœur) | Converser, créer entités, lancer actions/commandes | Solide, ambigu (naturel vs slash vs déterministe) |
| Mémoire + fichiers | Contacts/projets/recherche sémantique Qdrant | **Fragmentée** |
| CRM + Facturation | Pipeline, scoring, devis/factures | Partiel, **déconnecté** |
| Email + Agenda + Tâches | Productivité en fenêtres-panels | Partiel, **agenda Google-only** |
| Board + Atelier + Actions | 5 conseillers, swarm dev, actions multi-étapes | Riches mais **îlots sans retour chat** |
| Réglages + Providers + MCP | Config LLM, clés, MCP | Friction n°1 testeurs |
| Capacités annexes | Images, voix, navigateur, calculatrices, skills Office | **Largement invisibles** |
| Navigation / architecture | Comment tout se relie | **Émergente, pas pensée** |

## 2. Diagnostic central (triangulé sur plusieurs clusters)
Le problème n'est pas un manque de fonctions, mais la **cohérence des liens** et la **confiance**.

- **A. Mémoire dédoublée, CRM à part.** Deux instances de "Mémoire" non synchronisées (sidebar ⌘M vs fenêtre séparée) ; un contact créé dans l'une n'apparaît pas dans l'autre. Et Mémoire ≠ CRM : deux stockages de contacts sans pont → doublons.
- **B. L'IA annonce des choses qui n'ont pas eu lieu.** "Contact créé" mais absent, créations de projets en rafale (32/49/110, Dr_logic), "résultat inséré dans le chat" mais rien. Écart capacités affichées / réellement utilisables (UltraJury 69/100).
- **C. Navigation incohérente.** Email/Agenda/Tâches/CRM/Factures = fenêtres macOS séparées ; Board/Atelier/Actions/Réglages = modaux/tiroirs. Trois hiérarchies d'Échap concurrentes, pas de routage central.
- **D. Fonctions orphelines ou invisibles.** "Bibliothèque de prompts" sans écouteur branché (clic = rien) ; calculatrices ROI/ICE/RICE, navigateur, skills Office, génération d'image : présents mais introuvables. Board délibère mais il faut recopier la synthèse à la main.

## 3. Vision d'origine vs réalité
`benchmark-ux.md` visait : calme, keyboard-first, command palette ⌘K, mémoire VISIBLE, CRM au premier plan, "surtout pas trop d'options visibles". La réalité a dérivé vers l'inverse. Le cap existe déjà, il a été dilué.

## 4. Feedback testeurs
- **Corrigé récemment** : Ollama macOS/onboarding, défaut mistral-nemo, clé Gemini AQ (release v0.13.2), encodage UTF-8 Windows, Actions "résultat inséré".
- **Ouvert structurant** : créations CRM en masse / faux succès (bloquant confiance), export VCF KO, agenda non-Google cassé via chat, commandes déterministes peu fiables, ~20 `except` muets, RGPD in-app absent, pas de fallback provider runtime, ton vous/tu incohérent, accessibilité.
- **Top demandes** : STT/TTS 100% local, vrai tunnel de vente CRM (lead→client→SAV), commandes structurées fiables et découvrables.

## Cap retenu
> Thérèse n'a pas besoin de plus de fonctions. Elle a besoin qu'on relie celles qui existent en parcours fiables, qu'on unifie Mémoire/CRM, qu'on rende l'IA honnête sur ce qu'elle fait, et qu'on revienne au calme keyboard-first de la vision d'origine.
