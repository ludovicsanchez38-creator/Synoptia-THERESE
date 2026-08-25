# Audit complet THÉRÈSE

**Date** : 25 août 2026
**Version audité** : 0.47.0-alpha (code local, `Synoptia-THERESE`)
**Auteur** : Grok (lecture du code, de la doc interne, des captures, des audits existants, plus recherche UX 2025-2026)
**Destinataire** : Ludo / Synoptïa
**Périmètre** : produit, technique, UX/UI, parcours humain. Aucune modification de code.

---

## 1. Verdict en une page

THÉRÈSE est devenue une **suite desktop souveraine** là où la promesse d’origine était **une assistante**. Le moteur est sérieux. L’expérience humaine, elle, est encore trop lourde pour le public visé (solopreneur, TPE, mairie, association).

Ce qui est vrai et rare :

- Les données vivent sur la machine (`~/.therese/`), base chiffrée AES-256, clés dans le trousseau.
- Le chat, les contacts, l’email, l’agenda, les devis PDF, les tâches existent vraiment, pas seulement en maquette.
- Depuis 0.46-0.47, l’app a arrêté de mentir sur l’arrêt : un traitement en cours se voit, s’arrête (ou dit honnêtement « arrêt demandé »), et ne se déclare plus terminé trop tôt.
- L’interface unifiée de 0.40 (conversation + canevas à droite) est la bonne architecture.

Ce qui bloque le travail humain :

- Trop de portes pour les mêmes gestes. Chat naturel, slash, `{action: …}`, Capacités (30 cartes), palette ⌘K, vues embarquées, overlays Board/Atelier.
- Un vocabulaire d’ingénieur au premier lancement : LLM, provider, MCP, Qdrant, Groq, sidecar, fencing.
- Deux produits encore collés : cartes « parcours » d’un côté, panels complets de l’autre. Le fichier principal s’appelle toujours `ConversationCanvasPrototype.tsx` alors qu’il **est** la production.
- Des jobs métier incomplets présentés comme complets : facture sans envoi (501), atelier documentaire sans corpus indexé, navigateur Playwright non packagé.
- Un onboarding en 6 étapes avant le premier message utile.

**Note globale (alpha, public TPE) : 6,5 / 10.**
Ingénierie et souveraineté : 8. Clarté et allègement du travail humain : 5. Cohérence de l’interface : 6.

**Recommandation** : geler les nouvelles fonctions. Relier, nommer, cacher, finir les 5 jobs du quotidien. Revenir au calme du benchmark UX de janvier 2026 (Linear, Superhuman, « surtout pas trop d’options visibles »).

---

## 2. Ce que THÉRÈSE est aujourd’hui

### 2.1 Promesse

Tagline lue partout : *Humain d’abord, IA en soutien.*
Tagline PRD (janvier 2026) : *Ta mémoire, tes données, ton business.*

Cible : solopreneurs et TPE français qui jonglent entre prospection, delivery et admin. Persona d’origine : Ludo, consultant solo, Manosque.

### 2.2 Stack

| Couche | Choix |
|---|---|
| Desktop | Tauri 2.0 (Rust) |
| Frontend | React 19, TypeScript, Tailwind 4, Zustand, Framer Motion |
| Backend | FastAPI, SQLModel, SQLite/SQLCipher, Qdrant |
| LLM | Anthropic, OpenAI, Gemini, Mistral, Grok, Infomaniak, DeepSeek, Ollama, plus 4 compatibles OpenAI |
| Packaging | Sidecar PyInstaller + installeurs macOS / Windows / Linux (non signés OS) |

### 2.3 Surface réelle (pas le marketing)

- **35 routers** backend montés.
- **241 composants TSX**, **31 stores**, **37 fichiers de routes**.
- **11 vues** métier : chat, home, memory, crm, email, calendar, tasks, invoices, files, projects, documents.
- **30 cartes** dans le Centre de capacités.
- **11 capacités** seulement dans le manifeste honnête `capacites.json` (dont 3 partielles).
- Le README promet encore 18 skills, Board, Atelier agents, MCP, images, voix.

La coque de production est `ConversationCanvasPrototype`. Après splash et onboarding, `App.tsx` ne monte plus l’ancien layout. Le mode classic a été retiré en 0.42. Les anciens panels (email, factures, mémoire…) survivent comme **vues embarquées**.

Accueil tel qu’il s’affiche (capture `therese-hero.png`) :

- Rail gauche très mince (nouvelle conversation, recherche, historique, projets, aide, profil).
- « Bonjour Ludo » + brief du jour.
- Puces de parcours : priorités, contact, emails, rendez-vous, devis, décision, mission.
- Composeur : « Demande à Thérèse d’organiser, créer ou agir… »
- Badge « Interface unifiée », bouton « Contrôle des données », ⌘K.

C’est beau, calme, lisible. Le problème n’est pas le premier écran. C’est tout ce qui s’ouvre derrière, et le chemin pour y arriver.

---

## 3. Audit produit

### 3.1 Jobs to be done (PRD) vs réalité

Le PRD posait 4 jobs. Voici où on en est.

| Job | État | Commentaire |
|---|---|---|
| Préparer un RDV avec le vrai contexte | Partiel | Agenda local + Google + CalDAV existent. Le canevas « meeting » est le bon pattern. Le chat a déjà menti (fausse expiration, fuseau, jour civil UTC). |
| Qualifier une demande entrante | Partiel | Email lu, brouillon confirmé, jamais d’envoi silencieux : excellent. CRM à part. Un contact Mémoire n’est pas forcément le même objet que le prospect CRM. |
| Retrouver fichiers et conversations liés à un livrable | Fragile | Indexation réelle (Qdrant). A gelé toute l’app (BUG-155). L’atelier documentaire **ne s’appuie pas** sur les documents indexés. |
| Travailler hors ligne | Conditionnel | Ollama oui, si le modèle a les tools. Un modèle local sans outils ne crée ni contact, ni RDV, ni document (BUG-169). Premier lancement : embeddings ~250 Mo. |

Le job implicite n°5, « sortir un devis et se faire payer », est le plus TPE et le plus incomplet : PDF oui, envoi depuis la vue = 501.

### 3.2 Ce qui marche vraiment pour un solopreneur

1. **Discuter** avec un modèle au choix, historique, streaming, badge local/cloud.
2. **Retenir un contact / un projet** en local.
3. **Lire les mails** et préparer une réponse sous confirmation.
4. **Poser un rendez-vous** (surtout en calendrier local, sans console Google).
5. **Produire un PDF de devis / facture** conforme, mentions FR, devises.
6. **Voir la journée** (quand le brief est alimenté).
7. **Savoir qu’un traitement long tourne** (0.46-0.47) et l’arrêter sans mensonge.

C’est déjà un produit. Cinq gestes. Le reste est soit un îlot (Board, Katia/Zézette, 19 MCP), soit une promesse partielle.

### 3.3 Feature theater (présent, peu utile au quotidien TPE)

- Board de 5 conseillers (coût, plusieurs clés, peu de lendemain).
- Atelier agents Katia/Zézette (git, tests, OpenClaw). Public contributeur, pas TPE.
- 19 presets MCP (HubSpot, Stripe, WhatsApp Business, Playwright…).
- Browser automation annoncé, extra e2e **jamais packagé**.
- Calculateurs ROI / ICE / RICE / NPV.
- Variables, commands v3, escalation de coûts.
- Images GPT/Gemini (clés séparées).
- Sync CRM Google Sheets (reste d’un ERP perso).
- project.sync (rsync + SHA-256) : excellent pour Dr_logic, opaque pour les autres.

### 3.4 Honnêteté d’exécution : le vrai progrès 2026

Les bugs qui ont cassé la confiance, puis ont été corrigés, disent plus que n’importe quelle roadmap :

- Stop cosmétique : l’UI abortait, le fournisseur facturait, un outil pouvait encore créer un contact.
- Faux brouillon mail HTTP 200 : « Je reviens vers vous rapidement ».
- Faux timeout profil : profil écrit, embedding 19 s, l’humain croit l’install ratée (Jérôme, AMD E1-7010).
- Gel total à l’indexation.
- « Connexion expirée » calendrier en boucle.

Le chantier traitements 0.46-0.47 pose enfin le contrat : *passé le point de non-retour, un geste d’écriture se termine entier ou consigne son échec, jamais à moitié.* C’est exactement le genre de fondation dont l’UX a besoin. Il ne réduit pas le nombre de portes. Il rend plus honnête une maison trop grande.

### 3.5 Souveraineté : vraie, à conditionner

Vrai : pas de serveur Synoptïa, SQLCipher, Fernet + trousseau, sauvegardes à passphrase, consentement cloud par finalité et fournisseur, pixels traceurs bloqués.

À dire clairement à l’utilisateur :

- Dès qu’un modèle cloud est choisi, le **contexte** (mails lus par outils, extraits de fichiers, contacts) part chez le fournisseur.
- Ollama est le seul chemin 100 % local, et il a des prérequis (machine, modèle avec tools).
- L’installeur n’est pas notarié : Gatekeeper / SmartScreen au premier lancement. Pour une TPE, ça ressemble à un virus.

### 3.6 Dette qui touche encore l’humain

- 11 tests Windows hors gate alors que plusieurs testeurs sont sur Win10.
- Guide utilisateur daté juin 2026 (fenêtres séparées, « pas de notifications » alors que `/api/notifications` existe).
- Changelog public arrêté à 0.40 alors que 0.47 est taguée.
- `chat.py` : ~3400 lignes. `ConversationCanvasPrototype.tsx` : 1834. `ChatInput.tsx` : 1404.
- Starlette 1.2.1 épinglé (CVE connues), bump reporté.
- CSRF `/api/shutdown` accepté (local, mais réel).
- Deux « Atelier » : documents et agents.

---

## 4. Audit UX / UI

Méthode : heuristiques de Nielsen, test de l’établi (Nielsen, juillet 2026), parcours premier usage, densité des réglages, accessibilité, vocabulaire. Recoupé avec l’audit UI/UX du 16 juillet 2026 (fable + sol, ~50 findings) et la revue produit du 4 juin.

### 4.1 Heuristiques Nielsen appliquées

| Heuristique | Note | Constat |
|---|---|---|
| 1. Visibilité du statut | 7 | Traitements 0.46, sidecar banner, streaming. Brief du jour encore pauvre quand la donnée manque (« Rien d’urgent »). |
| 2. Correspondance monde réel | 4 | LLM, MCP, Qdrant, provider, fencing, skills. Un artisan dit « mes clients », pas « mémoire persistante ». |
| 3. Contrôle et liberté | 7 | Échap, confirmation avant envoi mail, Arrêter. Fermer le canevas a déjà annulé un Board en silence (SOLUX-02, juillet). Contrats 0.47 meilleurs. |
| 4. Cohérence et standards | 4 | Mémoire / Contacts / CRM. Calendrier / Agenda. Paramètres / Réglages. Atelier × 2. ⌘ vs Ctrl. « Core Features » en anglais dans les raccourcis. |
| 5. Prévention d’erreurs | 6 | Confirmations outils, fencing mutateurs. Confirmations parfois validables alors que les champs restent éditables (B3, juillet). |
| 6. Reconnaissance plutôt que rappel | 3 | La boîte vide force à inventer. 30 capacités, slash, actions, palette : l’utilisateur doit *se souvenir* du bon levier. |
| 7. Flexibilité (novice / expert) | 5 | Mode Contributeur cache Outils / Agents / Avancé : bonne idée. L’onboarding, lui, expose déjà le cockpit. |
| 8. Design esthétique et minimal | 6 | Premier écran réussi (clair, aéré, typo soignée). Derrière : 9 onglets de réglages, 30 cartes, double composeur. |
| 9. Aide à la récupération | 6 | Causes lisibles depuis 0.43.4. Toasts. Import VCF encore en `alert()` natif. |
| 10. Aide et documentation | 4 | `/aide`, Capacités, guide alpha périmé. Trois catalogues qui ne se recouvrent pas. |

### 4.2 Test de l’établi (workbench test)

Jakob Nielsen, juillet 2026 : *un primo-arrivant peut-il finir la tâche principale avec uniquement ce qui est visible au premier chargement, sans ouvrir un tiroir ?*

Tâche principale d’un solopreneur THÉRÈSE : **répondre à un client (lire le mail, retrouver le contexte, rédiger, éventuellement poser un RDV ou un devis).**

Au premier écran on a : un brief vide, 7 puces, une boîte. Pour arriver au mail il faut :

1. passer l’onboarding (clé API, parfois Ollama, parfois mot de passe d’application Gmail ou console GCP) ;
2. cliquer « Consulter mes emails » **ou** écrire la phrase magique **ou** ouvrir Capacités **ou** ⌘E ;
3. si le compte n’est pas branché, un wizard ;
4. basculer éventuellement vers la « vue complète » (panel classic embarqué).

L’établi échoue. La tâche principale n’est pas sur le banc. Elle est dans trois tiroirs.

### 4.3 Parcours premier lancement

Six étapes : Bienvenue, Profil, LLM, Sécurité, Dossier, Terminé.

Friction observée dans le code :

- L’étape LLM mélange cloud, local, tools, timeouts, URL Qwen.
- La sécurité (risques cloud / MCP / Groq) arrive **après** la saisie de la clé.
- Vocabulaire : « LLMs Cloud », « Serveurs MCP », « Qdrant ».
- Échap sur l’onboarding **ferme la fenêtre**, pas seulement le wizard.
- Si le backend ne répond pas 5 fois, l’onboarding est sauté (garde anti-perte de données, compréhensible, mais l’utilisateur atterrit sans boussole).
- Rien n’explique Capacités, Board, Atelier, Traitements.

Un TPE veut : nom, une IA qui marche, un premier message. Le reste (SIRET, MCP, effort de raisonnement) va au tiroir.

### 4.4 Deux composeurs, deux voix

| | Accueil unifié | Chat réel |
|---|---|---|
| Placeholder | « Demande à Thérèse d’organiser, créer ou agir… » | « Comment puis-je t’aider ? » |
| Pièces jointes | non | oui, indexation obligatoire |
| Slash / actions | non | oui |
| Capacités | bouton | HomeCommands (Produire / Comprendre / Organiser) |
| Envoi | ouvre le chat | stream |

L’utilisateur apprend un outil, puis se retrouve dans un autre. Jakob’s Law : on arrive avec les habitudes de Claude / ChatGPT (sidebar + un seul champ). Ici le champ change de contrat selon l’écran.

### 4.5 Densité des Paramètres

Commentaire dans le code : « 8 onglets → 6 ». Réalité : **9 ids**.

Standard : Profil, IA, Services, Accessibilité, Confidentialité, À propos.
Contributeur : + Outils, Agents, Avancé.

L’onglet IA à lui seul (655 lignes) : providers, clés, modèles, Ollama, Groq, 3 providers d’images, Brave, extraction d’entités. C’est un cockpit d’infra, pas un écran TPE.

### 4.6 Vocabulaire : la carte n’est pas le territoire

Même objet, plusieurs noms :

- Accueil / Brief du jour / Mes priorités / skipDashboard « Ne pas afficher l’Accueil » (ce skip ouvre le chat, pas l’ancien dashboard).
- Mémoire / Contacts / « Ouvrir la Mémoire » décrit comme Contacts.
- Calendrier / Agenda / meeting.
- Factures / Devis / facturation.
- Atelier documentaire / Atelier d’agents / Confier une mission / Review (anglais).
- Paramètres / Réglages / Contrôle des données / Trust Center.
- Traitements (longs) vs Tâches (métier) : deux mots proches, deux mondes.

« Produire un document » (skills Office) et « Rédiger un document » (atelier) sont deux produits. Un humain les confond.

### 4.7 Accessibilité (chantier encore ouvert)

Déjà en place : skip link, focus trap sur beaucoup de modales, thème, contraste élevé, reduced-motion, `MotionConfig`, annonce lecteur d’écran des nouveaux messages.

Encore vu en juillet et toujours structurel :

- cibles < 44 px (bouton fermer Atelier 28 px) ;
- contraste texte secondaire parfois sous 4,5:1 ;
- onglets Réglages : pattern tablist incomplet à l’époque ;
- taille de texte parfois sans effet réel sur le `rem` racine (à revérifier depuis US-013) ;
- raccourcis : groupe Fichiers vide, titres anglais, ⌘ affiché hors Mac (en partie corrigé).

Pour une diffusion large (mairies, associations, lecteurs d’écran), c’est un lot dédié, pas un polish.

### 4.8 Direction artistique

La DA (navy, cyan, magenta, glass) est documentée. La capture actuelle est **claire**, aérée, presque Linear/Notion. Écart avec `RULES-DESIGN.md` qui décrit encore un dark glassmorphism agressif. Le thème clair actuel est plus TPE, plus « bureau », moins « dashboard crypto ». À figer : **une** DA, tokens, plus de couleurs Tailwind brutes pour les statuts (déjà en cours de migration).

Le personnage (atlas, portraits Board) donne une identité. Attention à ne pas en faire un masque : l’humain doit voir la **source** (agenda réel, mail réel) avant le sourire de l’avatar. Le footer de l’accueil le dit déjà : « Thérèse affiche les sources reçues et confirme les effets externes. » Garder cette phrase comme loi, pas comme légende.

---

## 5. Recherche UX : comment faciliter le travail humain

Sources lues (2025-2026), pas de mémoire d’avant janvier 2025 pour l’actu :

1. Jakob Nielsen, *Progressive Disclosure: From Training Wheels to Week-Long AI Agents*, 9 juillet 2026.
2. Microsoft Design, *UX design for agents*, 11 avril 2025.
3. *ADEPTS: A Capability Framework for Human-Centered Agent Design*, arXiv 2507.15885, juillet 2025.
4. UX Tigers roundup, 13 juillet 2026 (chat → artefact, Slow AI).
5. Desisle, *AI SaaS UX Playbook*, juillet 2026 (confiance, 3 couches de divulgation).
6. *Copilot Ergonomics*, IEEE Computer, novembre 2025 (brouillon par défaut, Undo, journal de décision).
7. O’Reilly Radar, *Interfaces That Build Themselves*, juillet 2025.
8. Vision interne THÉRÈSE : `docs/benchmark-ux.md` (Linear, Superhuman, Arc, Notion), revue produit juin 2026.

### 5.1 Progressive disclosure (Nielsen 2026)

Principe : **3 contrôles sur l’établi, le reste dans un tiroir étiqueté.** Deux niveaux, pas quatre. On cache des *tâches rares*, pas des *personnes* (« mode débutant »). La plupart des gens sont des « perpetual intermediates » (Cooper) : ils apprennent assez pour bosser, puis s’arrêtent.

Appliqué à THÉRÈSE, l’établi du solopreneur :

1. **Parler** (un seul champ, toujours le même).
2. **Aujourd’hui** (ce qui mérite attention, sourcé).
3. **Agir** (mail, RDV, devis) avec confirmation.

Tiroir unique, label honnête : **Outils avancés** (MCP, agents, Board, calculateurs, variables, images, sync Sheets).

Règles Nielsen à coller au mur :

- 80 % des tâches sans ouvrir le tiroir.
- Jamais cacher l’info de décision (prix, cloud, envoi, suppression) au niveau 1.
- Réponses IA : verdict en 1 paragraphe, raisonnement / sources derrière un triangle.
- Agent long : contrat avant lancement (durée, coût, ce qu’il ne fera pas), miettes de sens pendant, interruption seulement si blocage, briefing de 30 s au retour.
- Un agent qui raconte 60 appels d’outils est aussi inutilisable qu’un écran à 60 interrupteurs. Un agent qui cache le journal est intrustworthy. Destination sur le banc, itinéraire dans le tiroir.

THÉRÈSE 0.46 a déjà le **journal** (Traitements). Il manque le **contrat avant** et le **briefing au retour**.

### 5.2 Microsoft : l’agent au service de l’humain

Principes utiles ici :

- **Relier, pas remplacer.** THÉRÈSE doit ramener Ludo vers ses clients, pas le coller dans un chat.
- **Accessible et parfois invisible.** Tourner en fond, nudger quand un devis expire, se taire sinon.
- **Nudger plutôt que notifier.** Une pastille « 3 relances » sur l’accueil > une pluie de toasts.
- **Incertitude visible.** « Je n’ai pas ton agenda » (déjà en 0.20) est meilleur qu’une invention. Généraliser.
- **Statut toujours visible.** Le panneau Traitements va dans ce sens.
- **Éléments familiers.** Micro = dictée. Pas « sidecar ».

### 5.3 ADEPTS (6 capacités face utilisateur)

Actuation, Disambiguation, Evaluation, Personalization, Transparency, Safety.

Traduction THÉRÈSE :

| ADEPTS | Aujourd’hui | Cible |
|---|---|---|
| Actuation | Outils nombreux, confirmations inégales | Un geste = un effet visible dans le canevas |
| Disambiguation | Le modèle devine, parfois en masse (32 contacts) | « Tu parles de Martin Dupont (Acme) ou Martin Leroy ? » |
| Evaluation | Board isolé | Évaluer **dans** le job (ce devis, ce mail) |
| Personalization | THERESE.md, profil, skipDashboard | Ton, clients, tarifs **visibles** (« ce que je sais de toi ») |
| Transparency | Manifeste 11 capacités vs 30 cartes | Un seul catalogue, maturité affichée |
| Safety | Consentement cloud, fencing | Même langage au premier écran |

### 5.4 Du chat vers l’artefact (UX Tigers 2026)

Les utilisateurs veulent **prolonger le livrable**, pas relire le fil. Canvas ChatGPT, Documents Claude, Notion : le document est le centre, l’IA est le collaborateur sur le bord.

THÉRÈSE a déjà le split conversation + canevas. C’est le bon pattern. Il faut l’assumer jusqu’au bout :

- Mail : le message est l’artefact, le chat commente.
- Devis : le formulaire/PDF est l’artefact.
- Document long : l’atelier (trame + sections) est l’artefact. Le chat ne doit plus recracher 800 mots.

Loi de copilot (IEEE 2025) : **appliquer en brouillon, publier explicitement, Undo partout.** THÉRÈSE le fait déjà pour l’envoi mail. L’étendre au devis, au RDV, à la création de contact.

### 5.5 Charge cognitive

Hick : le temps de choix croît avec log2(n+1). 7 puces + 30 capacités + slash + ⌘K + 11 vues = décision chère à chaque geste.

Loi de Jakob : copier les habitudes (Claude / ChatGPT / Mail.app), pas réinventer « Interface unifiée » comme badge. Le badge dit à l’équipe « on a migré ». Il ne dit rien à l’utilisateur.

Calm technology (Weiser, repris par Microsoft) : la tech disparaît. Un artisan qui ouvre THÉRÈSE le matin doit voir **3 choses à faire**, pas un centre de capacités.

### 5.6 Ce que Linear / Superhuman font et que THÉRÈSE visait déjà

`benchmark-ux.md` (janvier 2026) était juste :

- ⌘K colonne vertébrale ;
- peu d’options visibles ;
- mémoire **visible** ;
- undo ;
- animations utiles, pas décoratives.

La revue du 4 juin le constatait : *le cap existe, il a été dilué.* Les 0.40-0.47 ont unifié la fenêtre et durci la vérité. Ils n’ont pas taillé.

---

## 6. Diagnostic central

Le problème n’est plus « il manque une fonction ». Il est **trois fois le même** depuis juin :

1. **Trop de liens, trop de noms.** L’humain ne sait pas par quelle porte entrer.
2. **Confiance encore fragile** sur les bords (jobs partiels, docs en retard, Windows, signature).
3. **Premier usage d’ingénieur** pour un produit qui se dit humain d’abord.

La vision d’origine tenait en une phrase : *un assistant qui connaît mon business, données chez moi, interface calme.*
Le code 0.47 tient en une autre : *une suite mail + CRM + facture + RAG + agents + MCP, honnête sur l’exécution, trop grande à habiter.*

---

## 7. Recommandations (priorisées)

Rien de tout ça n’est du code. C’est un cap. À valider avant d’implémenter.

### P0. Geler. Finir. Relier.

Pas de nouveau module (pas de n8n, pas de 20e MCP, pas de 6e conseiller) tant que les 5 jobs du quotidien ne sont pas bouclés **et trouvables**.

Jobs à boucler :

1. Répondre à un mail (compte branché en 2 minutes, IMAP d’abord, Gmail ensuite).
2. Retrouver un client et ce qu’on s’est dit.
3. Préparer / poser un RDV.
4. Sortir un devis PDF **et** le joindre / l’envoyer sous confirmation (aujourd’hui 501).
5. Demander « qu’est-ce qui mérite mon attention ? » et obtenir une **curation**, pas un agenda brut.

### P1. Un établi, un tiroir

**Écran 1 (toujours) :**

- Un champ unique, même placeholder partout.
- Brief du jour sourcé (relances, échéances, RDV à enjeu). Vide honnête si rien n’est branché : « Branche tes mails pour que je te prépare la journée » + un bouton.
- 4 actions max, verbes métier : Écrire, Retrouver, Préparer, Facturer.

**Tiroir « Plus d’outils »** (un seul, label fixe, même place) :

Board, Atelier agents, MCP, calculateurs, images, variables, sync Sheets, project.sync.

Les 30 cartes Capacités deviennent le contenu du tiroir, pas le menu d’accueil. Le manifeste à 11 capacités devient **la vérité de l’établi**.

### P2. Onboarding en 90 secondes

1. Comment t’appelles-tu ?
2. Comment je t’aide ? (cloud avec clé **ou** Ollama, deux cartes, langage humain : « Sur tes serveurs » / « Uniquement sur cet ordinateur »).
3. Premier message. Le reste (SIRET, dossier, MCP, Groq) se propose **après**, dans le contexte du premier job (« Pour faire un devis, j’ai besoin de ton SIRET »).

La sécurité cloud se dit **avant** d’envoyer la première requête, en une phrase, pas en écran Qdrant.

### P3. Un mot par chose

Proposition de lexique utilisateur (à figer dans RULES + UI) :

| Interne | Utilisateur |
|---|---|
| memory | Contacts |
| crm | Pipeline |
| calendar | Agenda |
| invoices | Devis et factures |
| documents | Documents |
| files | Fichiers |
| processing-tasks | Activités en cours |
| tasks | Tâches |
| Atelier agents | Améliorer THÉRÈSE (mode avancé) |
| Atelier documentaire | Rédiger un document |
| Board | Décision |
| Capacités | (disparaît de l’accueil, devient le tiroir) |
| LLM / provider | Service d’IA |
| MCP | Connecteurs (avancé) |

Interdit à l’écran standard : sidecar, fencing, Qdrant, generation_id, tools, BYOK.

### P4. Une surface par job, plus de double

Aujourd’hui : carte canevas **et** `onOpenClassic` vers le panel. Choisir.

Recommandation : le canevas **est** la vue. Le panel classic meurt ou devient le même composant. « Vue complète » est un aveu que le canevas est un jouet.

Renommer `ConversationCanvasPrototype` → `AppShell` (quand on touchera au code). Le mot prototype dans la prod ment à l’équipe.

### P5. Mémoire visible

Le différenciateur PRD. Toujours trop caché.

- Panneau durable « Ce que THÉRÈSE sait » : profil, 5 derniers contacts, projets ouverts, sources.
- Badge sur un message : « s’appuie sur la fiche Martin · Acme », pas une hallucination.
- Un seul objet Contact (Mémoire = CRM), clé de voûte déjà identifiée en juin (P4 revue produit).

### P6. Réponses en couches

Toute sortie modèle :

1. Verdict / livrable (court).
2. Pourquoi, en 2 lignes.
3. Sources / raisonnement / code, pliés.

Les 800 mots dans le fil sont de la charge. L’artefact (brouillon mail, PDF, section de document) porte le volume.

### P7. Contrats d’agent (Slow AI)

Avant Board, Atelier, deep-research, indexation lourde :

- « Ça peut prendre 2 à 8 minutes. Coût estimé. Je n’enverrai rien, je n’effacerai rien. »

Pendant : miettes (« 3 conseillers ont répondu, synthèse en cours »), pas 60 tool calls.

Après : briefing 30 s. Arrêter garde le partiel quand c’est possible (déjà amorcé en 0.46).

### P8. Accessibilité et Windows comme critères de sortie

- Lot WCAG : cibles 44 px, contraste AA, focus, labels, pas d’anglais orphelin.
- Tests Windows **dans** la gate CI. Les testeurs alpha sont là.
- Signature / notarisation : sans ça, le premier geste d’un maire est « l’ordi dit que c’est dangereux ».

### P9. Doc utilisateur = le produit

Le guide alpha et le changelog public sont en retard d’un trimestre. Un testeur qui les lit habite une autre app (fenêtres séparées, 0.40). Tant que la doc mente, l’UX mente.

### P10. Mesure

Instrumenter 5 tâches, 5 personnes TPE, sans toi dans la pièce :

1. Premier message utile.
2. Brancher un mail IMAP.
3. Retrouver un contact créé hier.
4. Préparer un devis.
5. Comprendre ce qui tourne (Traitements) et l’arrêter.

Succès = fini sans ouvrir le tiroir, sans Discord. C’est le workbench test chiffré.

---

## 8. Feuille de route suggérée (sans coder)

### 30 jours : calme

- Lexique unique, balayage des libellés (écran + raccourcis + `/aide`).
- Accueil : 4 actions métier, Capacités sorties du premier écran.
- Onboarding raccourci (même si le vieux wizard reste en code, un flag suffit à tester).
- Guide + changelog alignés sur 0.47.
- Cacher Board / Agents / MCP / calculateurs derrière « Plus d’outils » (mode Contributeur élargi, pas seulement 3 onglets Réglages).

### 60 jours : jobs

- Contact unique Mémoire/CRM.
- Envoi devis sous confirmation (finir le 501) ou retirer le verbe « envoyer » partout.
- Brief du jour curaté (relances + échéances + RDV à enjeu), règle déjà validée par toi en juillet (B1).
- Un composeur unique.
- Contrat avant deep-research / Board / indexation.

### 90 jours : établi durable

- Canevas = vue, plus de double classic.
- « Ce que THÉRÈSE sait » visible.
- Lot WCAG + CI Windows.
- Notarisation.
- Réponses en 3 couches dans le chat.

Critère de fin : un primo-arrivant TPE, machine moyenne, sort un devis et répond à un mail le jour 1, sans lire Discord.

---

## 9. Mon avis (franc)

THÉRÈSE a le fond que 90 % des copilotes n’ont pas : local, chiffré, français, métier (devis, SIRET, mails), et depuis août une **honnêteté d’exécution** rare. L’équipe (toi, Zézette, les revues adversariales, les testeurs Dr_logic / Jérôme / lcjp) a traité la confiance technique avec une rigueur de logiciel critique.

L’UX n’a pas eu le même régime minceur. Chaque bug testeur a ajouté un panneau, un badge, un mode, un mot. Le résultat est une maison d’architecte avec trop de portes. L’humain d’abord, dans les faits, passe encore après le contributeur.

Le plus grand levier n’est pas une nouvelle IA. C’est **enlever**. Cacher n’est pas appauvrir : Nielsen le rappelle, un clic de plus pour l’expert coûte moins cher que la confusion du novice. Et l’expert TPE, 80 % du temps, est un novice de *cette* fonction-là.

Si je ne devais retenir qu’une phrase pour la suite :

> THÉRÈSE ouvre sur trois choses (parler, aujourd’hui, agir). Tout le reste a un tiroir, un nom français, et ne ment jamais sur ce qu’il a fait.

C’est déjà dans ton ADN (`benchmark-ux.md`, revue juin, manifeste 0.44, traitements 0.46). Il reste à s’y tenir, y compris quand une idée d’agent est excitante.

---

## 10. Sources

### Code et doc internes (extraits)

- `README.md`, `CLAUDE.md`, `docs/prd-therese.md`, `docs/benchmark-ux.md`
- `docs/rules/RULES-DESIGN.md`
- `docs/revue-produit/00-etat-des-lieux.md`, `01-pistes-priorisees.md`
- `docs/migration-v0.40/AUDIT-UIUX-20260716.md`
- `docs/releases/v0.46.0-alpha.md`, `v0.47.0-alpha.md`
- `docs/plans/2026-08-13-manifeste-capacites-design.md`, `2026-08-24-traitements-047-design.md`
- `src/frontend/src/App.tsx` (coque = prototype)
- `src/frontend/src/components/prototype/ConversationCanvasPrototype.tsx` (1834 lignes)
- `src/frontend/src/components/prototype/CapabilityCenter.tsx` (30 cartes)
- `src/backend/app/data/capacites.json` (11 capacités, 3 partielles)
- `src/frontend/src/stores/navigationStore.ts` (`APP_VIEWS`)
- `src/frontend/src/components/settings/SettingsModal.tsx` (9 onglets)
- `src/frontend/src/components/onboarding/OnboardingWizard.tsx` (6 étapes)
- Capture `assets/screenshots/therese-hero.png`

### Recherche UX

- Nielsen, J. (9 juillet 2026). *Progressive Disclosure: From Training Wheels to Week-Long AI Agents*. https://jakobnielsenphd.substack.com/p/progressive-disclosure
- Microsoft Design (11 avril 2025). *UX design for agents*. https://microsoft.design/articles/ux-design-for-agents/
- Zamfirescu-Pereira et al. (2025). *ADEPTS*. arXiv:2507.15885
- UX Tigers (13 juillet 2026). *UX Roundup: AI Agents Change Workflows*. https://www.uxtigers.com/post/ux-roundup-20260713
- Desisle (27 juillet 2026). *The AI SaaS UX Playbook*. https://www.desisle.com/resources/ai-saas-ux-playbook
- Bouzoukas, K. (26 novembre 2025). *Copilot Ergonomics*. IEEE Computer Society
- O’Reilly Radar (31 juillet 2025). *Interfaces That Build Themselves*

---

*Fin du rapport. Aucun fichier du dépôt n’a été modifié. Prochaine étape possible, si tu valides : un plan d’implémentation P0-P2 (lexique, établi, onboarding) découpé en tickets, sans nouvelle fonction.*
