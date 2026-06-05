# Comptes rendus personas — passage 1 (P6-P11, sur Mistral)

> Chaque persona a piloté Thérèse via l'API (backend local, LLM mistral-small-latest). P1-P5 sont dans l'historique de session ; voir aussi `personas-pass1-synthese-plan.md`.


## Persona 6 — Agent immobilier indépendant (agent commercial / mandataire), Aix-en-Provence - « Karim Belkacem » — **6.5/10**

**Tâches exécutées** : Tâche 1 - CRM vendeurs : créé 2 mandats (Sophie Reynaud T3 Cardinale 329k exclusif ; Olivetti maison Puyricard 595k mandat simple) avec notes riches (prix, net vendeur, type de mandat Hoguet, dispo) ; Tâche 2 - CRM acheteurs + scoring : créé 3 acheteurs (Mercier très chaud, Fournier tiède, Vasseur froid) ; tentative de scoring manuel ÉCHOUÉE (PATCH ignore le champ score, recalculate-score sans effet, tous figés à 60) ; Tâche 3 - Matching par recherche hybride + chat IA : la recherche sémantique classe bien Mercier/Fournier en tête pour le T3 et Vasseur/Olivetti pour la maison ; le chat IA croise budgets et critères et classe les 3 acheteurs sans erreur ni invention ; Tâche 4 - Activités + priorisation : loggé un appel sur Mercier et une note sur Vasseur (horodatées) ; le chat IA donne un ordre de relance 1-2-3 pertinent avec actions concrètes et même un SMS prêt à copier ; Tâche 6 - Skills Office DOCX : compte rendu de visite généré, 8 sections, 100% fidèle aux données (prix, surface, réserve salle de bain, prix d'entrée 318k) ; Tâche 7 - Skills Office XLSX : tableau de commission avec tous les calculs exacts (13160 TTC, 10966,67 HT, 2193,33 TVA, 315840 net vendeur) ; Tâche 8 - Email : brouillon de mail sans pression pour Fournier (bon ton) MAIS bien immobilier inventé de toutes pièces ; Tâche 9 - RGPD : export Art. 20 de Mercier (dossier complet et lisible) + anonymisation Art. 17 de Vasseur (nom/email/tél/notes effacés, passé en archive)

**Extraits IA observés** : Matching (impeccable) : « Julien Mercier : Budget 300 000-340 000 EUR, recherche un T3 en centre-ville ou quartier historique. Pertinent - Budget aligné, cible géographique exacte. [...] Antoine Vasseur : recherche une maison avec jardin. Non pertinent - Type de bien et budget incompatibles. » | Souveraineté (HALLUCINATION GRAVE) : « Tes échanges [...] ne sont PAS stockés sur ta machine. Les données sont [...] en mémoire vive (RAM) [...] Les interactions transitent via des serveurs sécurisés (hébergés en Union Européenne) » - alors que mon therese.db de 17 Mo est physiquement sur mon disque et qu'il n'existe aucun serveur Thérèse.

**Ce qui marche** :
- Le matching acheteur/bien : recherche sémantique + chat IA croisent budget et critères et sortent le bon profil en tête, fidèle à 100% à mes fiches, zéro invention. C'est LA fonction qui me ferait gagner des ventes
- La priorisation des relances : l'IA me dit qui rappeler en priorité et pourquoi, avec l'argument commercial exact (net vendeur, dispo) pioché dans mes notes, et un SMS de relance prêt à envoyer
- Le compte rendu de visite DOCX : 8 sections, complet, fidèle, réutilisable après une petite retouche d'en-tête
- Le tableau de commission XLSX : calculs honoraires/TVA/net vendeur tous exacts, présentable à un vendeur tel quel
- Le RGPD opérationnel : export Art. 20 (dossier client portable complet) et anonymisation Art. 17 (données réellement effacées, fiche archivée) - sérieux et démontrable à un client tatillon
- La preuve concrète du local : je vois mon therese.db, mon dossier qdrant, mes backups et ma clé de chiffrement dans ~/.therese/ - je comprends où sont mes données sans être informaticien

**Ce qui bloque** :
- Le scoring est MORT : impossible de noter un acheteur (PATCH du champ score ignoré, recalculate-score sans effet) - tous mes acheteurs restent à 60, un acheteur chaud n'est pas distingué d'un dossier perdu. C'est censé être un argument clé de l'outil pour mon métier
- L'IA hallucine GRAVEMENT sur la souveraineté : quand je lui demande où sont mes données, Mistral invente des serveurs en UE et prétend que rien n'est stocké sur ma machine - l'inverse de la réalité. Sur LA question la plus sensible pour un agent soumis à la loi Hoguet, c'est dangereux de s'y fier
- Le mail à Fournier a inventé un bien immobilier complet (T4 80 m² Mazarin 365k) qui n'existe pas dans ma base - à ne JAMAIS envoyer sans relecture
- Fuite de contexte : l'IA a ressorti spontanément 'le handicap de Karim Belhaj', une donnée d'un autre dossier qui n'est pas le mien
- La fiche anonymisée [ANONYMISÉ] remonte encore en tête de la recherche sémantique (embedding non purgé), même si les données perso sont bien effacées
- Friction de saisie : pas d'email/téléphone proposés à la création rapide, et les markdown ** ressortent en clair dans le DOCX (titre dupliqué)

**Ce qui manque** :
- Une vraie gestion des mandats : numéro de mandat, exclusif/simple, dates, registre Hoguet, carte T - le cœur réglementaire de mon métier est absent (juste des notes texte)
- Un scoring acheteur qui fonctionne et reflète la chaleur réelle (budget validé, finançable, nb visites, dernière relance)
- Un rapprochement automatique acheteurs/biens déclenché à chaque nouveau mandat ('voici les 3 acheteurs qui matchent')
- Le suivi du compromis : délais SRU 10 jours, conditions suspensives, rendez-vous notaire
- Le lien avec les portails (SeLoger, Leboncoin) et l'import des mandats sans ressaisie
- Un vrai message de confiance produit qui affirme noir sur blanc le 100% local - puisque l'IA, elle, dit le contraire

**Confiance (souveraineté+RGPD)** : Confiance RÉELLE dans le local : OUI, mais pas grâce à l'IA - grâce à ce que j'ai vu de mes yeux. Mes données sont physiquement dans ~/.therese/ (therese.db 17 Mo, qdrant, backups, clé de chiffrement en -rw-------), tout sur ma machine, consultable hors connexion par nature. Export Art. 20 : crédible (dossier client complet et lisible). Anonymisation Art. 17 : crédible (nom/email/tél/notes effacés, fiche archivée), réserve = l'embedding de recherche n'est pas purgé. GROS BÉMOL : quand on DEMANDE à l'IA où sont les données, elle ment (serveurs UE, RAM, rien sur la machine). Donc la souveraineté est réelle dans les faits mais le discours de l'IA la sabote. Pour un pro Hoguet/RGPD, il faut s'appuyer sur la preuve disque, jamais sur la parole du chatbot.

**Verdict** : Pas encore, mais j'y reviendrai vite : le matching acheteur/bien et la priorisation des relances sont déjà bluffants et fidèles à mes notes, le RGPD est sérieux et mes données sont vraiment chez moi. Ce qui me retient aujourd'hui, c'est un scoring mort, l'absence de gestion de mandats Hoguet, et surtout une IA qui hallucine sur ma souveraineté et invente des biens dans mes mails - donc rien ne part au client sans que je relise. Réglez le scoring, ajoutez les mandats et calmez les inventions de l'IA, et je quitte mon Excel et mon Apimo sans regret, à 25-35 euros par mois.


## Persona 7 — Formatrice indépendante / micro-organisme de formation Qualiopi (bureautique et IA pour TPE-artisans), Niort — **6.5/10**

**Tâches exécutées** : CRM : 3 fiches créées avec notes riches (Atelier Boréal/Hervé Castaing SIRET+budget+OPCO+PSH, stagiaire malentendant Karim Belhaj, cabinet comptable Nadia Lefranc) ; Chat pédago (Mistral) : 4 objectifs pédagogiques évaluables + QCM 6 questions avec corrigé pour formation Copilot artisans 2 jours ; Chat + Mémoire : recall du dossier Atelier Boréal uniquement à partir de mes notes (test anti-hallucination) ; Recherche hybride par le sens, sans citer de nom (handicap auditif, OPCO bâtiment, confidentialité données) ; Skills Office : feuille d'émargement XLSX Qualiopi (xlsx-pro) + programme de formation DOCX 8 sections daté (docx-pro) ; RGPD : export Art. 20 (portabilité JSON) de Karim Belhaj + anonymisation Art. 17 d'une fiche jetable, avec vérification de la disparition en recherche ; Souveraineté : inspection du stockage physique ~/.therese (SQLite + Qdrant local, clés chiffrées 600) + tableau de bord /api/rgpd/stats

**Extraits IA observés** : "Programme DOCX, section accessibilité : 'Pour un stagiaire malentendant : supports écrits systématiques, utilisation de [...] sous-titrage automatique' + 'Référent handicap : Nom : [À définir par l'organisme de formation]' (bon réflexe : placeholder au lieu d'inventer). MAIS émargement XLSX : 'Organisme de formation | Atelier Boréal' (faux, c'est le client) et 'Numéro de déclaration d'activité | 75750354300010' (NDA halluciné, jamais fourni).

**Ce qui marche** :
- La rédaction pédagogique est le vrai point fort : 4 objectifs avec verbes d'action observables (Rédiger/Automatiser/Générer/Optimiser), QCM cohérent et thématisé menuiserie, corrigés justes. Format directement présentable à un auditeur Qualiopi.
- Le programme DOCX est conforme et exploitable à 80% : 8 sections, programme DATÉ (indicateur Qualiopi), modalités d'évaluation détaillées (QCM + mise en situation + grille), section accessibilité PSH avec aménagements concrets pour mon malentendant. TVA juste (6400 HT -> 7680 TTC).
- Le recall mémoire est précis et fidèle à 100% à mes notes, zéro broderie : il me fait gagner le recollage de contexte avant un appel client.
- L'export RGPD Art. 20 est sérieux : JSON structuré complet (contact + activités + projets + tâches + champs base légale/consentement/expiration), horodaté. Présentable tel quel à un stagiaire qui demande ses données.
- La souveraineté du stockage est vérifiable de mes propres yeux sans être informaticienne : tout dans ~/.therese sur mon disque, clés chiffrées en 600, sauvegardes locales, aucun dossier cloud.

**Ce qui bloque** :
- Hallucinations sur pièce réglementaire : sur l'émargement XLSX il a mis Atelier Boréal comme 'organisme de formation' (c'est le CLIENT, l'OF c'est moi) et a INVENTÉ un numéro de déclaration d'activité que je n'ai jamais donné. Sur une pièce d'audit, un NDA bidon = non-conformité directe. Inacceptable sans relecture.
- Petites affirmations fausses dans le programme : 'formateur certifié Microsoft' (je ne le suis pas) et confusion 'attestation = certification Qualiopi'. À corriger avant envoi OPCO.
- Anonymisation Art. 17 incomplète : la fiche devient bien [ANONYMISÉ] (nom/email/notes vidés) MAIS le vecteur d'embedding de l'ancienne note traîne encore dans Qdrant, donc la fiche fantôme remonte toujours en recherche sémantique au même score (0.74). Effacement pas net à 100%.
- L'émargement n'a généré que la ligne formateur, sans les 4 lignes stagiaires vides numérotées attendues.
- Premier appel anonymisation rejeté (VALIDATION_ERROR) car il fallait un corps {reason}, pas évident sans regarder le schéma.

**Ce qui manque** :
- Le 'une saisie -> toutes les pièces' n'existe pas vraiment : le SIRET/raison sociale du CRM ne se propage PAS automatiquement au programme et à l'émargement, je dois tout redicter dans le prompt. C'était ma fonction tueuse espérée.
- Pas de modèles Qualiopi prêts à l'emploi et fiables (convention bipartite, attestation à chaud/à froid, BPF) : il faut tout décrire à la main et relire pour les hallucinations.
- Mes constantes d'OF (mon nom, mon NDA, mon adresse) ne sont stockées nulle part comme identité formateur, d'où le NDA inventé. Un profil 'organisme' réutilisable manque cruellement.
- Pas de suivi des dates butoir OPCO ni de relances automatiques, ni de gestion structurée des PSH/aménagements (juste du texte libre).
- Le classement de la recherche sémantique manque de tranchant : le résultat le plus pertinent métier (Hervé/Constructys pour 'OPCO du bâtiment') ressort 8e, noyé sous des fiches non pertinentes.

**Confiance (souveraineté+RGPD)** : Confiance élevée sur le stockage : 100% local vérifié de mes yeux (~/.therese, SQLite + Qdrant, clés chiffrées 600, sauvegardes locales), je comprends où sont mes données sans être technicienne. Export Art. 20 crédible et démontrable à un stagiaire. Anonymisation Art. 17 réelle mais imparfaite (vecteur résiduel dans l'index). Réserve sur le chat : ici en Mistral (API européenne, acceptable, mieux qu'un US, mais appel sortant) - le vrai hors-ligne total supposerait de basculer sur Ollama, que je n'ai pas testé. Pour mes données handicap/SIRET au repos : oui, elles restent chez moi.

**Verdict** : Je l'adopte à l'essai, mais pas encore en confiance aveugle : la rédaction pédagogique et le programme DOCX me font gagner un temps réel (80% du brouillon contre une page blanche, à 800 €/jour ça se rentabilise vite), et la souveraineté locale répond enfin à mon angoisse RGPD sur les données handicap. Mais tant qu'il hallucine mon numéro de déclaration d'activité sur une feuille d'émargement et qu'il n'y a pas de propagation 'une saisie -> toutes les pièces' ni de profil organisme fiable, je devrai tout relire ligne à ligne avant l'audit - donc je le garde comme assistant de rédaction, pas comme générateur de mon dossier Qualiopi clé en main.


## Persona 8 — Développeur web freelance (Node.js / React / Laravel), Nantes - « Maxime Berthier » — **7/10**

**Tâches exécutées** : CRM : création de 3 clients (Agence Pixel & Co en Livraison, Boulangerie Lefort en Proposition, MediStaff RH en Découverte) avec notes riches (specs, stack, budgets, tickets) ; Recherche hybride sémantique : 3 requêtes par le sens ('pointage', 'application de gestion des horaires du personnel', 'migration de site vers nouvel hébergeur') pour vérifier le RAG sur mes notes ; Chat Mistral : recollage de contexte projet Lefort + identification du ticket bloquant Pixel & Co + croisement multi-contacts pour trouver le client à données RH sensibles ; Factures : devis V1 Lefort (DEV-2026-001, 2400 HT/2880 TTC) + devis V2 scénario périmètre +1 page (DEV-2026-002, 2700 HT/3240 TTC), génération PDF local + inspection visuelle ; Skills Office : demande XLSX suivi jours facturés + rédaction d'une clause CGV freelance via le chat ; RGPD : export Art. 20 complet de MediStaff (contact/activités/projets/tâches) + anonymisation Art. 17 d'un contact jetable avec vérification de la disparition ; Souveraineté : inspection physique de ~/.therese/ (SQLite 16 Mo, Qdrant local, clé de chiffrement, PDF, backups) pour vérifier le 100% local plutôt que le croire

**Extraits IA observés** : ["Recollage Lefort (excellent) : 'Stack : WordPress + Elementor. Migration OVH → o2switch, 6 pages, formulaire RGPD. Livraison 15/07/2026. Budget 2 400 € HT. Acompte 30% = 720 € HT. Prochaine action : envoyer le devis détaillé à Julien Lefort.' — calcul d'acompte juste, zéro hallucination.", "Bluff XLSX (grave) : le chat a inventé un faux lien de téléchargement vers 'https://files.oaiusercontent.com/file-6XJQZ1zQ...' (domaine OpenAI !) avec signature SAS Azure tronquée par '...'. Aucun fichier réel généré (rien de neuf dans ~/.therese/outputs/, tout date de février/mars)."]

**Ce qui marche** :
- Le recollage de contexte client est la vraie tueuse : en une question, Mistral me ressort stack + périmètre + deadline + budget + acompte calculé, fidèle à 100% à mes notes, exploitable tel quel. C'est exactement le 'reprendre un dossier en 30 secondes' que je cherche.
- Zéro hallucination sur les données métier : tickets ouverts Pixel & Co (3, bloquant = pagination CSV) et identification du client RH sensible (MediStaff, badgeuse/horaires/congés) sont pile mes notes, pas du générique.
- Souveraineté VÉRIFIABLE, pas marketing : tout est physiquement dans ~/.therese/ (vraie base SQLite 16 Mo que je peux ouvrir, Qdrant local pour les embeddings, .encryption_key en chmod 600, PDF dans invoices/). Je peux le prouver, c'est mon critère n°1.
- Factures : numérotation propre (DEV-2026-001/002), totaux justes au centime (2400/480/2880 et 2700/540/3240), devis V2 recréé en une requête, PDF propre avec mentions légales présentes (net 30j, intérêts de retard, indemnité 40 €).
- RGPD solide : export Art. 20 structuré et complet (contact + activités + projets + tâches + horodatage), anonymisation Art. 17 qui transforme la fiche en coquille [ANONYMISÉ] en gardant l'ID (bon choix pour ne pas casser les factures liées), motif d'effacement journalisé. Modèle de données pensé conformité (champs rgpd_base_legale, consentement, expiration nativement).

**Ce qui bloque** :
- Bluff du chat sur la génération de fichiers : demande de XLSX → Mistral fabrique un faux lien OpenAI/Azure au lieu de router vers le vrai skill Office. AUCUN fichier produit. Pour un outil 'souverain', citer un domaine OpenAI dans la réponse est le pire contre-signal possible. Éliminatoire sur ce geste.
- Bloc ÉMETTEUR vide sur le PDF de devis : pas de nom, pas de SIRET, pas d'adresse, pas de TVA intracommunautaire. Un devis sans identité de l'émetteur n'est pas conforme ni opposable. Il faut configurer le profil (/api/config/profile), ce n'est pas guidé.
- Erreur juridique dans les CGV : le chat cite l'article L441-6 du Code de commerce (abrogé/renuméroté L441-10 depuis 2019) et mélange 'pénalités 18% TTC/an' (les pénalités ne sont pas soumises à TVA). Texte utile mais à relire, pas signable en l'état.
- 422 muet sur l'anonymisation : l'endpoint a refusé ma première requête avec 'Données invalides' sans dire que le champ 'reason' était requis. Un non-technicien abandonne là.
- Scores de recherche sémantique tassés : sur 'application de gestion des horaires', le bon contact (MediStaff 0.66) sort 2e derrière un contact sans rapport (0.67), tout le monde entre 0.62 et 0.67. Ça marche, mais le tri discrimine mal.

**Ce qui manque** :
- Un vrai suivi de tickets : statuts, priorités, lien commit/PR/issue. Là mes 'tickets' ne vivent que dans une note texte, pas dans un objet structuré.
- MCP Git réellement branchable : je voulais brancher mon Gitea/GitHub pour remonter de vrais tickets dans Thérèse (presets MCP annoncés), je n'ai pas pu le tester ni le confirmer en fonctionnel.
- Profil émetteur pré-rempli et imposé : impossible de sortir un devis conforme sans bloc émetteur, ça devrait être un pré-requis bloquant à la première facture.
- Routage fiable chat → skill Office : le chat doit DÉCLENCHER le générateur de fichier réel, pas inventer un lien. Tant que ce n'est pas câblé, la génération de docs passe par l'UI Skills, pas par le chat.
- Time-tracking et récurrence de facturation pour un freelance (jours facturés liés au projet, relance d'impayés automatique, multi-devises).

**Confiance (souveraineté+RGPD)** : Élevée et, fait rare, vérifiable. J'ai ouvert ~/.therese/ : vraie base SQLite de 16 Mo, Qdrant local, clé de chiffrement en chmod 600, PDF et backups sur disque. Rien ne part dans une boîte noire, je le PROUVE au lieu de le croire, c'est exactement ce que j'exige. Export Art. 20 complet et anonymisation Art. 17 crédibles et démontrables à un client. Modèle de données pensé RGPD nativement. UNE réserve sérieuse : le chat a craché un faux lien vers un domaine OpenAI, donc avec un LLM externe (Mistral) configuré, des données PARTENT bien chez le fournisseur du modèle au moment du chat. Le 'souverain' est vrai pour le STOCKAGE, mais pour le traitement par l'IA il faut basculer sur Ollama local (que je n'ai pas pu valider ici, le backend de test étant câblé Mistral). Pour les specs d'un client RH, je n'utiliserais le chat qu'en mode Ollama, jamais en Mistral.

**Verdict** : Je l'adopte en test sérieux mais pas encore en prod, parce que le socle local + le recollage de contexte + le RGPD vérifiable valent vraiment le coup pour un freelance qui hait la paperasse et se méfie des SaaS, mais tant que le chat invente des liens OpenAI au lieu de générer mes fichiers, et tant qu'un devis sort sans mon SIRET, je ne lui confie pas mes vrais clients ni ma facturation.


## Persona 9 — Expert-comptable / comptable solo (« Sylvie Roncalli », Valence, 34 clients TPE/libéraux/SCI) — **6/10**

**Tâches exécutées** : Tâche 1 - Création des 4 clients fictifs (Durand Menuiserie réel normal TVA 24, Lefèvre Kiné BNC 2035, SCI Les Tilleuls IS TVA trimestrielle, Auto Pneus 26 réel simplifié CA12) avec notes riches régime + échéance ; Tâche 2 - Recherche hybride sémantique : retrouvé le bon client par le sens sans le nom (menuisier réel normal -> Durand 0.74 en tête ; TVA trimestrielle -> SCI Les Tilleuls 0.71 ; profession libérale sans TVA -> Lefèvre 0.68) ; Tâche 3 - CRM/pipeline : 2 prospects créés (EURL Mistral Plomberie Découverte, Boulangerie Pain & Co Proposition) + activité 'appel du 04/06' datée et horodatée ; Tâche 4 - Calendrier garde-fou échéances : création d'un calendrier local + 3 échéances de juin (TVA Durand 24/06, acompte IS SCI 15/06, relance FEC Auto Pneus 10/06) ; Tâche 5 - Skills Office XLSX : tableau de bord portefeuille généré et téléchargé, vérifié dans Excel (4 clients + TOTAL honoraires 11 600 exact) ; Tâche 6 - Skills Office DOCX : courrier de relance pièces manquantes Durand généré (38 Ko) + brouillon chat préalable ; Tâche 7 - Chat + échéances fiscales (anti-bluff) : dates liasse IS 31/12 (2 mai 2026) et TVA mensuelle CA3 (24 juin) demandées avec consigne de citer la source ; Tâche 8 - RAG local : indexation d'un faux bilan + lettre de mission Durand, question sur total bilan/CA/résultat/honoraires ; Tâche 9 - RGPD : export Art. 20 (JSON portabilité complet) + anonymisation Art. 17 sur Cabinet Lefèvre + vérification du résidu, inspection du stockage physique ~/.therese/

**Extraits IA observés** : RAG bilan (fidèle, sourcé) : « Total actif : 160 750 EUR / Total passif : 160 750 EUR / Chiffre d'affaires 2024 : 312 600 EUR / Résultat net comptable 2024 : 27 400 EUR / Honoraires : 4 200 EUR HT. Sources : Fichier bilan-durand-2024.txt, Fichier lettre-mission-durand.txt » -- tous chiffres exacts, sources nommées, zéro hallucination. // Chat calendrier (défaillant) : « 12 juin 2026 : Échéance déclaration 2035 pour Claire Lefèvre (BNC) » -- date INVENTÉE (n'est pas au calendrier, et la 2035 c'est en mai), et il a OUBLIÉ l'échéance FEC du 10/06 réellement créée.

**Ce qui marche** :
- Recherche hybride par le sens : je retrouve 'le menuisier en réel normal' ou 'qui est en TVA trimestrielle' sans taper le nom, le bon client ressort toujours en tête. C'est exactement ce qui me sort du mille-feuille Excel/post-it
- RAG local sur mes documents : réponse 100% fidèle au bilan indexé (total 160 750, CA 312 600, résultat 27 400, honoraires 4 200 HT), avec citation explicite des deux fichiers sources. Aucun bluff. Parfait pour préparer un RDV client
- XLSX tableau de bord portefeuille : directement présentable, 4 clients avec régimes corrects et TOTAL honoraires calculé juste (11 600), zéro retouche nécessaire
- Courrier de relance (chat et DOCX) : structure pro, ton courtois mais ferme, lien intelligent avec l'échéance TVA du 24/06, placeholders propres et signalés
- Export RGPD Art. 20 : JSON clair et complet (contact + activités + projets + tâches + horodatage), montrable à un client ou à l'Ordre
- Anonymisation Art. 17 : sérieuse et vérifiable, nom/société -> [ANONYMISÉ] et notes (email + données financières) purgées à None
- Souveraineté tangible : tout vit dans ~/.therese/ (therese.db SQLite 17 Mo + dossier qdrant + backups + clé Fernet en 600). Je peux le montrer, le sauvegarder, le chiffrer sans être informaticienne
- CRM : activité d'appel datée et horodatée correctement, pipeline avec stades

**Ce qui bloque** :
- Garde-fou échéances DÉFAILLANT (mon besoin n°1) : le chat n'est PAS branché sur le calendrier. Quand je demande mes échéances de la semaine, il a inventé une date (12/06 Lefèvre, qui n'existe pas) et oublié une échéance réellement créée (10/06 Auto Pneus FEC). Sur des dates fiscales, une hallucination est inacceptable, ça me dessert au lieu de me rassurer
- Calendrier mal agrégé : GET /api/calendar/events sans filtre renvoie 0 alors que les 3 événements existent bien si je filtre par calendar_id. Le listing par défaut est cassé
- Calendrier exige par défaut un compte Google ('account_id requis pour Google Calendar') : il a fallu créer manuellement un calendrier local d'abord, contre-intuitif pour qui veut du 100% local
- Le chat échéances fiscales ne cite AUCUNE source malgré ma consigne explicite, et affirme la date TVA '24 juin' sans préciser qu'elle dépend du SIREN/département. Dates justes mais affirmées sèchement = piège pour un confrère pressé
- DOCX : titre dédoublé et tronqué en 1re ligne, balises markdown ** restées brutes (pas converties en gras Word), et une phrase déontologiquement fausse à retirer ('Alerter l'administration fiscale en cas de retard') que je n'ai jamais demandée
- Anonymisation Art. 17 : la donnée personnelle disparaît bien, mais le 'fantôme' vectoriel reste indexé dans Qdrant (l'enregistrement [ANONYMISÉ] ressort encore en recherche à 0.69) -- pas ré-indexé
- Recherche hybride polluée par les contacts des autres testeurs et scores serrés (0.74 vs 0.67) : le bon est premier mais le tri manque de franchise

**Ce qui manque** :
- Garde-fou échéances AUTOMATIQUE par régime fiscal : générer seul les dates TVA (CA3 selon SIREN, CA12, acomptes IS, DSN, CFE, liasse) à partir du régime saisi sur la fiche client. Aujourd'hui je dois tout saisir à la main, le 'garde-fou' n'en est pas un
- Connexion à mon logiciel de prod (ACD/Quadra) et import FEC : sans ça, Thérèse reste un satellite à nourrir en double
- Pré-remplissage RGPD : sur 36 contacts, les 36 sont en base_legale 'non défini' et 0 consentement. Le cadre existe mais n'est ni guidé ni pré-rempli, donc mon registre est vide
- Modèles métier prêts à l'emploi (lettre de mission conforme, attestation, relance graduée) plutôt qu'une génération libre à recadrer
- Brancher le chat sur le calendrier réel pour que 'liste mes échéances' lise la base et n'hallucine pas
- Liaison chat <-> CRM : que la fiche client (notes, activités, échéances) remonte automatiquement dans le contexte sans que je re-tape tout

**Confiance (souveraineté+RGPD)** : Confiance plutôt bonne sur le local, c'est mon critère n°1 et là Thérèse marque des points. Les données vivent dans ~/.therese/ (SQLite therese.db + Qdrant + backups + clé Fernet chiffrée), répertoire que je peux ouvrir, montrer et sauvegarder moi-même. L'export Art. 20 (JSON complet) et l'anonymisation Art. 17 (nom + notes purgés, vérifié par re-export) sont RÉELS et démontrables à un client ou à l'Ordre, pas cosmétiques. Le RAG et la recherche tournent en local. Réserves honnêtes : (1) je n'ai pas pu prouver le hors-ligne strict dans ce test (chat Mistral = appel API externe, donc dès que j'utilise le chat la requête sort ; pour du 100% local sur du sensible il faudrait basculer Ollama, que je n'ai pas testé ici) ; (2) le fantôme vectoriel d'un contact anonymisé reste dans l'index ; (3) le registre RGPD (base légale, consentement) n'est pas pré-rempli. Donc : souveraineté du stockage = oui et vérifiable ; mais le 'rien ne sort jamais' dépend du LLM choisi, et ça, déontologiquement, je dois le maîtriser à 100%.

**Verdict** : Pas encore, mais pas loin. Je l'adopte le jour où le garde-fou d'échéances devient automatique et fiable (calage par régime fiscal + chat branché sur le calendrier sans hallucination) et où le sensible peut tourner en Ollama hors-ligne prouvé. Aujourd'hui la recherche par le sens, le RAG sourcé sur mes bilans, le tableau de bord XLSX et le RGPD local exportable/effaçable me bluffent vraiment ; mais une IA qui invente une date d'échéance fiscale, déontologiquement, je ne peux pas m'y fier les yeux fermés. À 6/10 et autour de 25 EUR/mois en complément d'ACD, je teste sérieusement la prochaine version.


## Persona 10 — Photographe / vidéaste freelance (mariage, corporate, immobilier) - EI au réel, Aix-en-Provence — **6.5/10**

**Tâches exécutées** : CRM pipeline événementiel : 3 affaires créées avec stages (mariage Lefèvre/proposition, film corporate Atelier Mistral/découverte, portraits Cabinet Roumieux/signature) + scoring 95 sur le mariage ; Recherche hybride par le sens : 3 requêtes sans le nom (cérémonie abbaye + mineurs, film de marque entreprise, plus gros budget) pour tester la sémantique sur mes notes ; Chat IA - récupération d'info de presta : 'combien devisé pour le mariage Lefèvre et délai de livraison ?' (réponse depuis mes notes) ; Chat IA - conseil métier : priorisation de mes 3 affaires + plan d'action en 3 points pour la semaine ; Chat IA - conseil juridique : règles du droit à l'image des mineurs en France pour border ma clause ; Skills Office DOCX : génération d'un contrat de cession de droits à l'image réutilisable (usage privé couple vs portfolio photographe + clause mineurs) ; Facturation : devis mariage 2400€ (franchise TVA 293B, 3 lignes) + facture d'acompte 30% (720€) avec PDF conforme stocké localement ; RGPD : export Art. 20 du contact Camille Lefèvre (JSON portabilité complet) + anonymisation Art. 17 d'un contact démo (avec vérif de disparition en recherche) ; Souveraineté : inspection du stockage local ~/.therese/ (SQLite, PDF factures, qdrant, clé de chiffrement) + stats RGPD

**Extraits IA observés** : Conseil priorisation (excellent) : « Priorité à relancer : Mariage Lefèvre. Pourquoi ? Panier le plus élevé (2400€). Délai serré. Risque de perte si confirmation tardive. » | Contrat de cession (bonne structure mais erreur de droit) : « Pas de droit moral : Le Photographe renonce à revendiquer la paternité des Images (article L121-1 du CPI) » — FAUX, le L121-1 rend justement le droit moral inaliénable, on ne peut pas y renoncer.

**Ce qui marche** :
- Le chat retrouve l'info exacte de mes prestas depuis mes notes (2400€ TTC + livraison 6 semaines), zéro hallucination sur les chiffres - exactement le 'combien j'avais facturé le mariage X ?' que je cherche
- Le conseil de priorisation pipeline est bluffant : Mistral raisonne juste (plus gros panier en proposition = risque de perte) et sort un plan d'action concret utilisable tel quel
- Recherche par le sens efficace sur requêtes ciblées : 'cérémonie abbaye + mineurs à anonymiser' sort Camille Lefèvre en tête (0.73), 'film de marque entreprise' sort Sophie Granier en tête (0.76)
- Le contrat de cession DOCX a une vraie ossature pro (préambule, définitions, tableau usage/durée/territoire, distinction privé/portfolio, clause mineurs double consentement + floutage) - très au-dessus de mon Word bricolé
- Factures propres : numérotation séparée DEV-xxx/FACT-xxx, acompte 30% calculé juste (720€), franchise TVA 293B affichée, indemnité recouvrement 40€, PDF directement présentable
- RGPD crédible : anonymisation Art. 17 vide vraiment nom/email/tél/notes, le contact ne remonte plus par son contenu, et la raison de l'effacement est tracée - rassurant pour visages et mineurs
- Souveraineté lisible : je vois physiquement mes données dans ~/.therese/ (base SQLite, PDF, embeddings, clé de chiffrement, backups), sans être informaticien

**Ce qui bloque** :
- Hallucinations juridiques répétées, éliminatoires sur mon métier : article 227-22 CP cité à tort pour le droit à l'image (c'est la corruption de mineurs), et dans le contrat 'renonciation au droit moral L121-1 CPI' qui est juridiquement impossible et inversé. Je ne peux PAS signer ça en l'état
- Balises <w:t> qui fuitent dans les cellules du tableau du contrat DOCX (artefact markdown->Word) : ça fait amateur dans un document à signer
- Le endpoint PDF de facture ne renvoie pas le binaire mais un chemin local - mon devis DEV-2026-003 ne s'est pas matérialisé en PDF côté API (le fichier de facture existe bien sur disque, mais l'aller-retour est confus)
- L'émetteur de la facture affiche le nom de l'affaire ('Mariage Camille & Yanis') au lieu de mon identité 'Mathéo Vasseur photographe', et il manque mon SIRET : à paramétrer avant tout envoi réel
- La recherche sémantique sur requête abstraite ('mon plus gros budget de l'année') patine et remonte des contacts d'autres dossiers - le tri est bruité quand la base contient beaucoup de contacts

**Ce qui manque** :
- Devis multi-lignes typés photo prêts à l'emploi (forfait reportage + frais déplacement + cession de droits en ligne séparée), avec acompte/solde gérés nativement comme un cycle
- Gestion des gros volumes de livrables : lien Drive/WeTransfer, suivi des galeries (800 photos, rushes 4K 200 Go), où est quel livrable - le coeur de ma douleur, absent
- Pipeline calé sur le cycle photo (contact -> devis -> acompte -> shooting -> livraison -> cession) avec relances automatiques, plutôt qu'un pipeline CRM générique
- Planning de tournage / shotlist et modèles de mails récurrents (relance validation de planches, livraison)
- Un garde-fou anti-hallucination juridique : sur les clauses de cession et le droit à l'image, l'IA devrait citer la loi de façon vérifiée ou dire qu'elle n'est pas sûre, pas inventer des numéros d'articles
- Pré-remplissage RGPD : la base légale et le consentement ne se renseignent pas tout seuls (34 contacts en 'non défini'), un champ consentement par défaut à la création de fiche aiderait

**Confiance (souveraineté+RGPD)** : Élevée sur la souveraineté, correcte sur le RGPD. Local : OUI, je vois mes fichiers dans ~/.therese/ (SQLite + PDF + embeddings qdrant + clé de chiffrement), tout est sur ma machine, rien d'envoyé dans un cloud américain pour le stockage. Export Art. 20 : OUI, crédible (JSON complet et structuré, contact+activités+projets+tâches+horodatage, remettable à un client). Anonymisation Art. 17 : OUI, nette (nom->[ANONYMISÉ], email/tél/notes vidés, disparition de la recherche, raison tracée). 'Je comprends où sont mes données' : OUI. Réserves : le chat IA, lui, passe par l'API Mistral (cloud, donc mes formulations partent dehors quand je discute - à basculer sur Ollama local pour le vraiment sensible), et le registre RGPD reste vide tant que je ne saisis pas la base légale/consentement (34/34 'non défini').

**Verdict** : Pas encore tout de suite, mais presque : je l'adopterais demain pour mon pipeline, mes devis/factures d'acompte et mon coffre-fort local RGPD qui me rassure vraiment pour les visages et les mineurs. Ce qui me retient, c'est que l'IA hallucine des articles de loi dans mes contrats de cession (227-22, renonciation au droit moral L121-1) : tant que je ne peux pas signer un contrat les yeux fermés sans repasser derrière un juriste, ma fonctionnalité tueuse reste à moitié bridée. Corrigez les citations juridiques et le tableau DOCX, et je passe à 8/10 et je paie 15-20€/mois sans hésiter.


## Persona 11 — Restauratrice / commerçante de proximité (Nadia Berthier, bistrot-épicerie « Le Comptoir de Nadia », Annecy) — **6/10**

**Tâches exécutées** : Tâche 1 - Création des 5 fiches fournisseurs (Metro, Pomona, Vincent Roux maraîcher, Cave de Talloires, Boulangerie Favre) avec notes riches (jours de livraison, mini de commande, conditions de paiement) ; Tâche 2 - Chat contextuel : « lesquels me livrent le mercredi ? » + demande de récap complet des jours de livraison ; Tâche 3 - Mail de commande à Pomona pour samedi (8 kg filet de bœuf, 5 kg crevettes, 3 kg beurre) ; Tâche 4 - Mail de réclamation à Metro (4 packs d'eau manquants sur le BL-2026-0488, demande d'avoir) ; Tâche 5 - Génération du tableau XLSX « Suivi factures fournisseurs juin 2026 » (5 lignes + total) ; Tâche 8/recherche hybride - Recherche sémantique des fournisseurs par le sens (sans citer le nom) ; Tâche 9 - RGPD complet : question à Thérèse sur le stockage, export Art. 20 + anonymisation Art. 17 d'une cliente fidélité fictive (Carole Dubois, carte 0421)

**Extraits IA observés** : Mail réclamation Metro (exploitable tel quel) : « Le bon de livraison n° BL-2026-0488, livré mardi 2 juin 2026, présente une anomalie : 4 packs d'eau gazeuse sont manquants... Je vous demande... de m'adresser un avoir pour le montant correspondant... soit XX €... À défaut, je me réserve le droit de réévaluer nos relations commerciales. » | Réponse RGPD décevante (3e personne floue, générique) : « Stockage physique : Fichier local sur ton appareil... Option cloud : si tu utilises Google Sheets ou Airtable... Utilise un outil hébergé en UE (ex : Nextcloud, Odoo local, ou un tableur chiffré comme Cryptomator). » — elle ne dit jamais clairement « tes données sont dans Thérèse, sur ton ordi, rien ne part ».

**Ce qui marche** :
- Les mails métier sont mon coup de cœur : commande à Pomona et réclamation à Metro générés propres, ton juste (cordial pour la commande, ferme mais correct pour la réclamation), numéro de BL repris exactement, demande d'avoir claire. Envoyables quasi tels quels, c'est ça qui me ferait gagner 1h par semaine
- Le tableau XLSX de suivi des factures est généré avec un total juste (1 718,25 €, calcul exact) et téléchargeable. C'est mon cauchemar du dimanche soir réglé
- L'export RGPD Art. 20 est du sérieux : un vrai fichier complet avec toutes les infos de ma cliente, son historique et les champs de consentement, horodaté. Si une cliente me demande ce que j'ai sur elle, je lui sors ça
- L'anonymisation Art. 17 fonctionne vraiment : après coup le nom, la carte fidélité 0421, l'allergie, tout est remplacé par [ANONYMISÉ] ou effacé. Je peux répondre à un « supprimez-moi » et le prouver
- Quand l'IA ne sait pas un montant, elle met « XX € » au lieu d'inventer un chiffre. Ça, ça inspire confiance
- Recherche par le sens correcte sur 3 cas sur 4 : « poisson et viande fraîche » → Pomona en tête, « les vins de la carte » → Cave de Talloires, « producteur de légumes du marché » → Vincent Roux net devant

**Ce qui bloque** :
- La réponse à « qui me livre le mercredi ? » est fausse : elle me sort Vincent Roux (juste) MAIS Metro (faux, c'est mardi/jeudi) et OUBLIE Pomona qui livre bien le mercredi. Pour quelqu'un qui passe ses commandes, une info de livraison à moitié fausse, c'est dangereux
- Quand je demande le récap de mes 5 fournisseurs, elle n'en ressort que 3 : Pomona (mon principal frais) et la Cave de Talloires disparaissent. L'IA ne regarde pas toutes mes fiches, juste celles que sa recherche fait remonter
- L'anonymisation a planté la première fois (erreur de validation) parce qu'il fallait obligatoirement une « raison » dans la requête. Pour une non-informaticienne, un bouton qui échoue sans expliquer, c'est anxiogène
- La recherche « fournisseur payé en espèces » rate complètement : Vincent Roux (la bonne réponse) est noyé en 5e position, des contacts qui ne sont pas à moi passent devant. Les scores sont tous tassés, le tri par pertinence est faible
- Petit excès de zèle de l'IA : dans la réclamation Metro elle a inventé « erreur récurrente (déjà signalée précédemment) » alors que je n'ai jamais dit ça

**Ce qui manque** :
- Le scan-photo d'une facture papier (le cageot du livreur) directement vers le tableau de suivi : c'est LE geste qui changerait ma vie, je reçois la moitié de mes factures en papier
- Un vrai récap « qui je dois relancer / payer aujourd'hui » qui croise les échéances et les commandes en attente, sorti tout seul, sans que je le demande
- La gestion des stocks et des minimums de commande automatiques (alerte quand il faut recommander pour le week-end)
- Un lien avec mon logiciel de caisse et avec mon comptable, pour ne pas tout ressaisir
- Que l'IA aille lire TOUTES mes fiches fournisseurs quand je pose une question, pas seulement quelques-unes ; sur 5 fournisseurs je veux 5 réponses fiables
- Une vraie utilisation sur téléphone, parce qu'entre 8h et 16h je ne suis jamais assise devant un ordinateur

**Confiance (souveraineté+RGPD)** : Mitigée mais plutôt rassurante côté outils, décevante côté discours. Les outils RGPD sont CRÉDIBLES et concrets : l'export Art. 20 sort un vrai fichier complet et horodaté, et l'anonymisation Art. 17 efface réellement les données (nom, carte fidélité, allergie remplacés par [ANONYMISÉ] ou vidés). Ça je l'ai vu de mes yeux, c'est du solide, pas du décor. EN REVANCHE, quand j'ai posé la question simple « où sont MES données, est-ce que ça part chez les Américains ? », l'IA m'a répondu un cours général sur le RGPD (« utilise Nextcloud, Cryptomator, vérifie que ton hébergeur est dans l'UE ») au lieu de m'affirmer clairement « tes données sont dans Thérèse, sur ton ordinateur, rien ne part ». Pour une non-informaticienne qui a justement peur du cloud, c'est raté : l'IA ne défend pas le « 100 % local » de son propre produit. Bon point : le LLM utilisé est Mistral, un modèle français, ça me parle. Mais « je comprends où sont mes données » → non, pas grâce à la réponse de l'IA, seulement grâce au fait que les exports fonctionnent en local.

**Verdict** : Pas encore tout à fait, mais j'y suis presque : je l'adopterais à 6/10 surtout pour les mails (commande + réclamation envoyables direct) et le tableau de factures, qui me feraient vraiment gagner mon heure du dimanche soir. Ce qui me retient : l'IA se trompe sur mes jours de livraison et oublie des fournisseurs quand je l'interroge, et surtout elle ne me dit pas clairement que mes données restent chez moi alors que c'est tout ce que je veux entendre. Réglez le scan des factures papier, fiabilisez les réponses sur TOUS mes fournisseurs, et donnez-moi une vraie appli sur le téléphone, et là je signe à 12-15 €/mois sans hésiter.
