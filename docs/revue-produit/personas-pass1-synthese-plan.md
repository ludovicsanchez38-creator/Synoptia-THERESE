# Synthèse passage 1 - 11 personas métier sur Thérèse Desktop

## 1. Tableau récap des 11 personas

| N° | Métier | Note /10 | Fonction tueuse confirmée | Manque n°1 |
|----|--------|----------|---------------------------|------------|
| 1 | Plombier (Sébastien) | 6,5 (gemma) / 8,5 (Mistral) | Relance d'impayé + rappel de contexte client, fidèles à 100 % aux notes | Devis BTP avec TVA 10/20/5,5 auto (et bascule gemma → Mistral) |
| 2 | Consultante RH (Sophie) | 8 | Exploitation fine des notes sensibles dans le respect de la confidentialité (recherche « tensions codir » sans le nom) | Marquage explicite « note sensible » vs ordinaire |
| 3 | Avocate (Camille R.) | 6,5 | Anti-hallu juridique réussi (cite art. 1231-6 C. civ. correct) | Indicateur factuel local/LLM par message (l'IA bluffe « hébergée en France ») |
| 4 | Graphiste (Camille Roussel) | 8 | Clause de cession de droits calibrée + génération d'image moodboard (gpt-image-2) | Vraie notion de « versions de livrable » + isolation du dossier image |
| 5 | Ostéo (Camille V.) | 7 | Recherche clinique par motif (cervicalgie, lombaire) | Fiabilité recherche (rate « maux de tête » → « migraines ») + fiche patient santé |
| 6 | Agent immobilier (Karim) | 6,5 | Matching acheteur/bien + priorisation des relances (SMS prêt) | Scoring MORT (figé à 60) + gestion mandats Hoguet |
| 7 | Formatrice Qualiopi (Niort) | 6,5 | Rédaction pédagogique (objectifs évaluables, QCM, programme DOCX) | Propagation « une saisie → toutes les pièces » + profil organisme (NDA halluciné) |
| 8 | Dév web freelance (Maxime) | 7 | Recollage de contexte client (stack + deadline + acompte) | Routage chat → skill Office fiable (bluff faux lien OpenAI) |
| 9 | Expert-comptable (Sylvie) | 6 | RAG local sourcé sur bilans + recherche par régime fiscal | Garde-fou échéances automatique branché au calendrier (hallucine les dates) |
| 10 | Photographe/vidéaste (Mathéo) | 6,5 | Priorisation pipeline + recollage devis | Anti-hallu juridique sur clauses de cession (cite faux articles CPI) |
| 11 | Restauratrice (Nadia) | 6 | Mails métier (commande + réclamation envoyables direct) | Réponses fiables sur TOUTES les fiches + scan facture papier + appli mobile |

**Moyenne : ~6,8/10.** Aucune adoption immédiate sans relecture ; tous les personas disent « presque, mais pas encore ».

---

## 2. Constats transversaux

### C1 - Le choix du modèle est central et invisible pour l'utilisateur
gemma3:1b est inutilisable (P1 : confond les clients, français cassé) ; Mistral est bon partout. Mais l'utilisateur ne sait pas quel modèle tourne ni comment basculer. Tous les métiers à secret (P3 avocate, P5 ostéo, P8 dév RH, P9 comptable, P10 photographe) concluent que le sensible **devrait** tourner en Ollama local, mais **aucun n'a pu le tester** (backend câblé Mistral).
**Personas : 1, 3, 5, 8, 9, 10 (et implicitement tous).**

### C2 - L'IA BLUFFE sur la souveraineté (le contre-signal le plus grave)
Question « où sont mes données ? » → réponses fausses et dangereuses : « hébergée en France » (P3), « serveurs en UE, rien sur ta machine, RAM » (P6), cours générique « utilise Nextcloud/Cryptomator » sans jamais dire « c'est local » (P11). Pire : P8 a vu le chat cracher un **faux lien vers un domaine OpenAI**. Sur LA question décisive pour les métiers réglementés, l'IA sabote son propre argument de vente. La souveraineté est réelle dans les faits (tous ont vu `~/.therese/`) mais le discours de l'IA la détruit.
**Personas : 3, 6, 8, 11 (constat unanime sur les 11).**

### C3 - Recherche sémantique : marche mais tri trop mou
Le bon résultat sort souvent en tête, mais : rate les formulations indirectes (P5 « maux de tête » ≠ « migraines », P11 « payé en espèces » noyé en 5e, P7 « OPCO du bâtiment » en 8e), scores qui se **resserrent** quand la base grossit (P4, P5, P6, P8, P9), et **pollution inter-testeurs** (P6, P9 : contacts d'autres personas qui remontent). Côté chat, l'IA ne lit **qu'un sous-ensemble des fiches** : P11 demande 5 fournisseurs → en obtient 3, P9 oublie une échéance créée.
**Personas : 4, 5, 6, 7, 8, 9, 11.**

### C4 - L'anonymisation Art. 17 laisse un fantôme vectoriel
Données perso bien effacées en base, MAIS l'embedding reste dans Qdrant : la fiche `[ANONYMISÉ]` remonte encore en recherche au même score (P6, P7 à 0,74, P9 à 0,69). Effacement crédible mais pas net à 100 %.
**Personas : 6, 7, 9.**

### C5 - RGPD démontrable = la vraie force (mais le registre est vide)
Export Art. 20 (JSON complet horodaté) et anonymisation Art. 17 jugés sérieux et présentables à un client/à l'Ordre par **tous**. MAIS le registre n'est jamais pré-rempli : base légale et consentement à « non défini » sur 34-36 contacts (P9, P10), pas de guidage.
**Personas : tous pour la force ; 9, 10 pour le registre vide.**

### C6 - Hallucinations sur le contenu juridique et réglementaire produit
L'IA invente des références de droit dans des documents à signer/déposer : faux numéro de déclaration d'activité (P7), L441-6 abrogé + « pénalités 18 % TTC » (P8), art. 227-22 CP et « renonciation au droit moral L121-1 » impossible (P10), phrase déontologiquement fausse « alerter l'administration fiscale » (P9), bien immobilier inventé dans un mail (P6), « erreur récurrente déjà signalée » inventée (P11). Bon réflexe inverse quand il manque une donnée : placeholder `[À définir]` ou `XX €` (P7, P11).
**Personas : 6, 7, 8, 9, 10, 11.**

### C7 - Le profil émetteur n'existe pas → documents non conformes
Devis/factures sans SIRET, sans identité émetteur, ou avec le nom de l'affaire à la place de l'émetteur (P8, P10). Pour la formatrice, ses constantes d'OF (NDA, adresse) ne sont stockées nulle part, d'où le NDA inventé (P7).
**Personas : 7, 8, 10.**

### C8 - Scoring CRM cassé
PATCH du champ score ignoré, `recalculate-score` sans effet, tout figé à 60 (P6). Un acheteur chaud n'est pas distinguable d'un dossier perdu.
**Personas : 6 (testé et cassé), 10 (scoring utilisé mais non vérifié).**

### C9 - Le chat n'est pas branché sur les objets structurés (calendrier, CRM complet)
P9 : chat des échéances déconnecté du calendrier → hallucine une date et en oublie une vraie. `GET /api/calendar/events` sans filtre renvoie 0. La fiche client ne remonte pas automatiquement dans le contexte du chat (P9). Le chat ne route pas vers le skill Office (P8).
**Personas : 8, 9, 11.**

### C10 - La promesse « une saisie → tout le reste » n'existe pas
Le SIRET/raison sociale du CRM ne se propage pas au programme, à l'émargement, aux factures. Tout est re-dicté dans le prompt (P7, P9 « satellite à nourrir en double »).
**Personas : 7, 9.**

### C11 - Friction de saisie et artefacts markdown dans les DOCX
`**` qui ressortent en clair, balises `<w:t>` qui fuitent dans les tableaux, titres dédoublés/tronqués (P6, P9, P10). Pas d'email/tél proposés à la création rapide (P6). Endpoints qui renvoient un 422 muet (champ `reason` requis non documenté) : P7, P8, P9, P11.
**Personas : 6, 7, 8, 9, 10, 11.**

### C12 - Métiers terrain = besoin mobile et capture photo
Restauratrice : moitié des factures en papier, jamais devant un ordi entre 8h-16h → scan photo facture + appli mobile = condition d'adoption. Plombier : photo chantier + signature sur place. Graphiste/photographe : gros volumes de livrables (galeries, rushes 4K).
**Personas : 1, 4, 10, 11.**

---

## 3. Plan d'amélioration priorisé

### P0 - Bloquant adoption / confiance (à traiter avant le 2e passage)

#### MODÈLE / IA

**P0-IA-1 — Prompt système factuel anti-bluff souveraineté** *(constat C2)*
- **Problème** : l'IA invente l'hébergement (France, UE, RAM, lien OpenAI). Sabote l'argument de vente sur LA question décisive.
- **Solution** : injecter dans le prompt système un bloc factuel non négociable : « Tes données sont stockées localement dans `~/.therese/` sur la machine de l'utilisateur (SQLite chiffré + Qdrant + backups). Aucun serveur Thérèse n'existe. Le STOCKAGE est 100 % local et hors-ligne. Seul le TRAITEMENT par le chat peut sortir vers le fournisseur du LLM si un modèle cloud (Mistral) est choisi ; en Ollama, rien ne sort. Ne jamais inventer d'hébergeur, ne jamais citer un domaine tiers. » + interdire explicitement les liens de fichiers fabriqués.
- **Personas** : 3, 6, 8, 11 (tous).
- **Effort** : **S**.

**P0-IA-2 — Garde-fou anti-hallucination juridique/réglementaire** *(constat C6)*
- **Problème** : faux articles de loi (227-22 CP, L121-1, L441-6, NDA bidon) dans des docs à signer/déposer.
- **Solution** : prompt système « Pour toute référence légale, réglementaire ou normative (article, numéro de déclaration, taux), ne cite que si tu es certain ; sinon écris `[à vérifier]` ou un placeholder. Ne jamais inventer un numéro d'article, de SIRET, de NDA. » + à terme, RAG sur un corpus juridique vérifié (Légifrance) pour les clauses types. Bannière « relecture humaine requise » sur tout document à valeur juridique.
- **Personas** : 6, 7, 8, 9, 10, 11.
- **Effort** : **S** (prompt) / **L** (RAG juridique vérifié).

**P0-IA-3 — Indicateur visible local-vs-cloud par message** *(constat C1, C2)*
- **Problème** : l'utilisateur ne sait pas si sa requête est partie chez Mistral ou est restée locale.
- **Solution** : badge par message (« Ollama local » vert / « Mistral cloud » orange) + sélecteur de modèle accessible dans l'UI du chat + au minimum un Ollama testable de bout en bout.
- **Personas** : 1, 3, 5, 8, 9, 10.
- **Effort** : **M** (PRODUIT : badge + sélecteur ; MODÈLE : valider le routage Ollama).

#### PRODUIT

**P0-PROD-1 — Réparer le scoring CRM** *(constat C8)*
- **Problème** : PATCH score ignoré, `recalculate-score` sans effet, tout figé à 60. Argument clé mort pour agent immo et photographe.
- **Solution** : corriger l'endpoint d'écriture du champ score + recalcul fonctionnel (critères : budget validé, finançable, nb visites/contacts, dernière relance).
- **Personas** : 6, 10.
- **Effort** : **S/M**.

**P0-PROD-2 — Profil émetteur obligatoire avant 1re facture** *(constat C7)*
- **Problème** : devis/factures sans SIRET ni identité → non conformes, non opposables. NDA OF inventé faute de profil.
- **Solution** : objet « profil émetteur » (nom, SIRET, adresse, TVA intra OU mention franchise 293 B, NDA pour OF) ; pré-requis bloquant à la première facture ; propagation auto sur tous les documents.
- **Personas** : 7, 8, 10.
- **Effort** : **M**.

**P0-PROD-3 — Brancher le chat sur les objets structurés** *(constat C9)*
- **Problème** : chat déconnecté du calendrier (hallucine/oublie des dates) et du CRM complet ; routage chat → skill Office cassé.
- **Solution** : outils/function-calling fiables (lire le calendrier réel, lire TOUTES les fiches concernées, déclencher le générateur Office) au lieu de laisser le LLM deviner ; corriger `GET /api/calendar/events` (listing par défaut renvoie 0).
- **Personas** : 8, 9, 11.
- **Effort** : **M/L**.

#### CONFIANCE / RGPD

**P0-RGPD-1 — Purger le fantôme vectoriel à l'anonymisation Art. 17** *(constat C4)*
- **Problème** : la fiche `[ANONYMISÉ]` remonte encore en recherche (embedding non supprimé) → effacement incomplet, faille RGPD démontrable.
- **Solution** : à l'anonymisation/effacement, supprimer (ou ré-indexer à vide) le vecteur Qdrant associé. Test de non-régression : la fiche ne doit plus apparaître à aucun score.
- **Personas** : 6, 7, 9.
- **Effort** : **S**.

**P0-RGPD-2 — Isoler le dossier image / espace de test** *(constat transversal P4)*
- **Problème** : la génération d'image écrit dans le `~/.therese` réel ; pollution inter-testeurs des contacts en recherche.
- **Solution** : namespace par utilisateur/atelier (préfixe collection Qdrant + dossier de sortie isolé) pour que les tests ne se contaminent pas.
- **Personas** : 4, 6, 9.
- **Effort** : **S/M**.

---

### P1 - Fort impact

#### MODÈLE / IA

**P1-IA-1 — Améliorer le tri de la recherche sémantique** *(constat C3)*
- **Problème** : rate les formulations indirectes, scores tassés, se dégrade avec le volume.
- **Solution** : meilleur modèle d'embedding (multilingue FR plus fin), **re-ranking** (cross-encoder) sur le top-k, seuil de pertinence affiché, expansion de requête (synonymes : migraines↔maux de tête). Filtrer par propriétaire avant le scoring sémantique.
- **Personas** : 4, 5, 6, 7, 8, 9, 11.
- **Effort** : **M/L**.

**P1-IA-2 — Forcer le chat à balayer TOUTES les fiches pertinentes** *(constat C3)*
- **Problème** : « récap mes 5 fournisseurs » → 3 ; « mes échéances » → en oublie.
- **Solution** : pour les requêtes d'agrégation/récap, charger l'ensemble du sous-ensemble filtré (par type/propriétaire) dans le contexte plutôt qu'un top-k sémantique tronqué.
- **Personas** : 9, 11.
- **Effort** : **M**.

#### PRODUIT

**P1-PROD-1 — Templates métier fiables et pré-remplis** *(constats C6, C10)*
- **Problème** : génération libre à recadrer ; pas de modèles conformes.
- **Solution** : bibliothèque de modèles validés et pré-remplis depuis le profil + la fiche client : devis BTP avec TVA 10/20/5,5 (P1), pack Qualiopi (convention, émargement multi-lignes, attestation à chaud/à froid, BPF) (P7), lettre de mission/relance graduée comptable (P9), contrats de cession photo/graphiste (P4, P10), courriers avocate (P3).
- **Personas** : 1, 3, 4, 7, 9, 10.
- **Effort** : **L**.

**P1-PROD-2 — Propagation « une saisie → toutes les pièces »** *(constat C10)*
- **Problème** : SIRET/raison sociale re-dictés à chaque document.
- **Solution** : injecter automatiquement profil émetteur + fiche client dans tous les générateurs (programme, émargement, devis, factures).
- **Personas** : 7, 9.
- **Effort** : **M**.

**P1-PROD-3 — Nettoyer le pipeline DOCX (artefacts markdown)** *(constat C11)*
- **Problème** : `**`, balises `<w:t>`, titres dédoublés dans des docs à signer → effet amateur.
- **Solution** : convertir proprement markdown → styles Word (gras réel), dédupliquer les titres, échapper les balises.
- **Personas** : 6, 9, 10.
- **Effort** : **S/M**.

**P1-PROD-4 — Garde-fou échéances automatique par régime** *(constat C9, besoin n°1 comptable)*
- **Problème** : le « garde-fou » n'en est pas un, tout est saisi à la main.
- **Solution** : générer les échéances fiscales depuis le régime de la fiche client (CA3 selon SIREN, CA12, acomptes IS, DSN, CFE, liasse) ; calendrier local par défaut (sans compte Google requis).
- **Personas** : 9.
- **Effort** : **L**.

**P1-PROD-5 — Gestion des mandats Hoguet** *(constat métier P6)*
- **Problème** : cœur réglementaire de l'agent immo absent (juste des notes texte).
- **Solution** : objet mandat (numéro, exclusif/simple, dates, registre) + rapprochement auto acheteurs/biens à chaque nouveau mandat.
- **Personas** : 6.
- **Effort** : **L**.

#### CONFIANCE / RGPD

**P1-RGPD-1 — Message de confiance produit affirmé + registre pré-rempli** *(constats C2, C5)*
- **Problème** : registre RGPD vide (base légale/consentement « non défini » partout) ; pas de message produit qui affirme le 100 % local.
- **Solution** : valeurs RGPD par défaut à la création de fiche (base légale = relation contractuelle, champ consentement) + bandeau produit factuel sur la souveraineté + marquage « note sensible » (P2).
- **Personas** : 2, 9, 10 (et tous pour le bandeau).
- **Effort** : **M**.

---

### P2 - Confort

**P2-PROD-1 — Versions de livrable + suivi du temps** *(graphiste, photographe, dév)*
- Notion de versions de livrable, time-tracking lié au projet, relances auto de devis dormants. Personas 4, 8, 10. **Effort M.**

**P2-PROD-2 — Suivi compromis / cycle métier** — délais SRU 10 j, conditions suspensives, RDV notaire (P6) ; cycle photo contact→devis→acompte→shooting→livraison→cession (P10) ; tickets structurés + MCP Git (P8). Personas 6, 8, 10. **Effort L.**

**P2-PROD-3 — Capture photo facture + appli mobile** *(constat C12)*
- Scan-photo facture papier → tableau de suivi ; usage mobile réel. Personas 1, 11. **Effort L.**

**P2-PROD-4 — Fiches métier dédiées** — fiche patient santé + note SOAP (P5), modèles de devis photo multi-lignes (P10), franchise TVA 293 B affichée (P5, P10). Personas 5, 10. **Effort M.**

**P2-PROD-5 — Friction de saisie** — email/tél à la création rapide, messages d'erreur explicites (remplacer les 422 muets « champ reason requis »). Personas 6, 7, 8, 9, 11. **Effort S.**

**P2-PROD-6 — Intégrations externes** — portails immo (SeLoger/Leboncoin) (P6), ACD/Quadra + import FEC (P9), Figma/Adobe (P4), Drive/WeTransfer galeries (P10), caisse + comptable (P11). Personas 4, 6, 9, 10, 11. **Effort L.**

---

## 4. Pré-requis pour le 2e passage

Pour que le 2e passage (5 tâches métier par persona) soit pertinent et discriminant, corriger **en priorité** :

1. **Activer et tester un backend Ollama de bout en bout** (P0-IA-3) — sinon impossible de valider la promesse « sensible en local » qui conditionne l'adoption chez 6 personas (avocate, ostéo, dév RH, comptable, photographe, formatrice handicap). Le 2e passage doit pouvoir basculer cloud/local.

2. **Corriger le prompt système** (P0-IA-1 souveraineté + P0-IA-2 juridique) — deux changements **S** qui débloquent la confiance chez quasiment tous. Sans ça, le 2e passage reverra les mêmes hallucinations bloquantes et les notes ne bougeront pas.

3. **Réparer le scoring CRM** (P0-PROD-1) et **brancher le chat sur calendrier + CRM complet** (P0-PROD-3) — sinon les tâches « scoring acheteur » (P6, P10), « mes échéances » (P9) et « récap tous mes fournisseurs » (P11) échoueront à l'identique.

4. **Purger le fantôme vectoriel + isoler les espaces de test** (P0-RGPD-1, P0-RGPD-2) — sinon la pollution inter-personas (déjà vue chez P6, P9) faussera toute mesure de la recherche sémantique au 2e passage, et l'anonymisation Art. 17 restera marquée incomplète.

5. **Mettre en place le profil émetteur** (P0-PROD-2) — pour que les tâches de facturation (P7, P8, P10) produisent des documents conformes testables, au lieu de buter sur le bloc émetteur vide.

6. **Améliorer le tri sémantique + balayage exhaustif** (P1-IA-1, P1-IA-2) — au minimum le filtre par propriétaire et le re-ranking, pour que les tâches de recherche par le sens (présentes chez 7 personas) discriminent vraiment et ne soient plus « le bon en tête mais scores tassés ».

**Recommandation de séquencement** : faire d'abord le lot **S** (prompts système P0-IA-1/2, fantôme vectoriel P0-RGPD-1, scoring P0-PROD-1) qui change les notes le plus vite pour le moindre effort, puis le lot **M** (Ollama testable, badge local/cloud, profil émetteur, chat branché), avant de relancer le 2e passage. Garder les **L** (templates métier, mandats Hoguet, garde-fou échéances, mobile) pour le 3e passage.