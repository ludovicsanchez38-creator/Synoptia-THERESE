# Claire, coach professionnelle en solo : trace de la campagne

> Campagne c13, 25/09/2026. Instrument : Playwright MCP, viewport 1280×800, DPR 1, fr-FR, thème clair.
> Frontend http://127.0.0.1:1420, moteur jetable http://127.0.0.1:17393 (v0.75.0), base vierge au départ.
> Garde d'environnement à 09:30 : `{ visible: "visible", horloge: 2036.43 }`, viewport 1280×800, DPR 1, fr-FR. Stockage purgé (3 clés localStorage, 0 sessionStorage, 0 base IndexedDB), puis rechargement.
> Note d'instrument : la racine des fichiers de Playwright est `~` ; la première capture est partie dans `~/docs/…`, je l'ai déplacée dans le dossier de la campagne et le dossier vide est à la Corbeille. Toutes les captures suivantes passent par un chemin absolu.
> Garde rejouée après le rechargement de 09:53 (simulation du « lendemain ») : `{ visible: "visible", horloge: 644.932 }`.
> Console au chargement : dix « [API] IPC échoué, retry n/10 » puis « Fallback port 17393 (mode dev) » : attendu hors Tauri, non retenu.

## Mon impression (première personne, cinq à dix lignes)

J'ai tout fait en local, et c'est vrai : rien n'est sorti de ma machine, le badge « Local » me le dit à chaque réponse et la page de confidentialité est honnête, jusqu'à m'avouer ce qui n'est pas chiffré. Mais pour y arriver, j'ai dû chercher le choix local tout en bas d'une liste de quatorze services en ligne, et on m'a d'abord proposé un modèle marqué en rouge.
Le plus pénible, c'est de ne jamais savoir si c'est enregistré : ma facturation l'était, mais rien ne me l'a dit et l'Accueil m'a redemandé de la remplir jusqu'au rechargement.
Mes clientes existent, mes séances aussi, mais elles ne se parlent pas : la fiche d'Hélène ne montre ni sa séance ni la note que j'y ai « ajoutée », et chercher « Hélène » me rend tout le carnet ou rien du tout selon l'écran.
J'ai trouvé mes contacts en cinq gestes, et la note de séance par hasard sous « Préparer » ; « Écrire » voulait dire e-mail.
Le devis et la facture sont beaux et justes, avec mon SIRET et mon adresse, mais ma facture dit « TVA incluse » avec une TVA à zéro, ses conditions sont sans accents, et la liste affirme que j'ai envoyé un devis que je n'ai jamais envoyé.
Trop de mots de technicien (tokens, prompt, mutation, MCP, score_change) : à chacun, j'ai hésité.

## Parcours (un bloc par parcours)

### 1. Mise en route : configurer THÉRÈSE sur une base vierge, en local, avec mon profil et mes infos de facturation

Préconditions : base vierge (`GET /api/chat/conversations` = `[]`), stockage du navigateur purgé, Ollama local avec `gemma4-tia:latest` et `qwen3:8b`.
Gestes comptés : 14 clics et 2 saisies de formulaire pour finir l'assistant, puis 3 gestes (carte, défilement, Enregistrer) pour la facturation.

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 1.1 | Ouverture de l'app | Un accueil qui me dit quoi faire | Assistant en 6 étapes, l'Accueil derrière est `inert` et `aria-hidden` (vérifié). Focus sur le titre masqué « Configuration initiale de Thérèse ». Mots « provider IA » et « Multi-LLM » non expliqués | 01-miseenroute-accueil.png | observation (jargon, voir claire-13) |
| 1.2 | « Commencer la configuration » | Étape Profil | Étape 2 sur 6. La mention « stockées localement dans /tmp/therese-demo-c13/data et ne quittent jamais ta machine » est en 12 px, et le même écran dit plus bas « injectées dans le contexte de l'IA ». Aucun champ adresse ni SIRET | 02-miseenroute-profil-vide.png | bug_candidate (claire-07), proposal (claire-09) |
| 1.3 | Je remplis nom, surnom, entreprise « Claire Exemple Coaching », rôle, e-mail de démo, ville, contexte | Champs acceptés | Champs remplis sans erreur | 03-miseenroute-profil-rempli.png | ok |
| 1.4 | « Continuer » | Choisir un service d'IA, idéalement local | 14 services, Claude (cloud) présélectionné « Recommandé - Excellent coding et français ». L'option locale Ollama est la 14e sur 14, à 1 238 px de haut pour une fenêtre de 800 : invisible sans défiler. Descriptions pleines de jargon (« Contexte 1M tokens », « co-développé avec Cursor, 500k contexte », « Sonar », « clé API ») | 04-miseenroute-serviceia.png | proposal (claire-02) |
| 1.5 | Je défile et je choisis « Ollama (Local) » | Le modèle local proposé, avec un feu vert | `gemma4-tia:latest` présélectionné, et juste en dessous un bandeau rouge « RAM déconseillée, environ 8,3 Gio requis pour un plafond de 8 Gio » | 05-miseenroute-ollama-choisi.png | bug_candidate (claire-01) |
| 1.6 | J'essaie l'autre modèle, `qwen3:8b` | Voir si c'est mieux | Bandeau vert « RAM compatible, environ 6,9 Gio ». L'application m'avait donc proposé d'office le modèle qu'elle déconseille. Je reviens à `gemma4-tia:latest` (consigne de la mission) | 06-miseenroute-qwen-essai.png | bug_candidate (claire-01) |
| 1.7 | « Continuer » | Étape Sécurité, lue depuis le haut | L'étape s'ouvre défilée de 188 px (défilement hérité de l'étape précédente) : le titre « Sécurité et confidentialité » est caché sous le bandeau d'étapes, je tombe directement sur « Important : les agents IA peuvent exécuter des commandes… via les tools ». Les deux boutons du bas sont collés aux bords du dialogue, pas comme aux étapes précédentes | 07-miseenroute-securite.png | bug_candidate (claire-03, claire-04) |
| 1.8 | Je déplie « Services d'IA cloud » | Savoir ce qui part | Texte clair : les messages vont chez le fournisseur, ne pas y mettre de données clients. Encadré rassurant « Parcours local sans consentement cloud » | 08-miseenroute-securite-cloud-deplie.png | ok |
| 1.9 | Je déplie « Transcription vocale » | Savoir si ma dictée reste locale | Le texte se déplie dans une liste interne de 280 px qui ne défile pas vers lui : je lis « L'audio est envoyé à Groq pour transcription, sauf si la dictée locale (Whisper) est » puis c'est coupé. Il faut défiler une seconde zone pour lire la fin. J'apprends au passage que la dictée part en ligne par défaut | 09-miseenroute-securite-voix-deplie.png | bug_candidate (claire-05) |
| 1.10 | « J'ai compris, continuer » | Étape Dossier | « Aucun dossier configuré » affiché en bandeau d'avertissement alors que je n'ai rien fait encore | 10-miseenroute-dossier.png | observation |
| 1.11 | « Sélectionner un dossier » | Le Finder s'ouvre | Hors Tauri le sélecteur natif ne peut pas s'ouvrir ; message lisible « La fenêtre de choix du dossier ne s'est pas ouverte. Redémarre THÉRÈSE, puis réessaie. » Console : `Ouverture du sélecteur de dossier impossible: TypeError: Cannot read properties of undefined (reading 'invoke')` | 11-miseenroute-dossier-clic.png | angle mort d'instrument (non retenu) |
| 1.12 | « Passer » | Récapitulatif et bouton final | Récapitulatif « Profil : Claire », « ollama / gemma4-tia:latest », « Dossier : Non configuré ». Le bouton « Commencer » est à 851 px, sous le bas du dialogue (776) et de la fenêtre (800) : il faut défiler dans le dialogue pour finir | 12-miseenroute-termine.png, 13-miseenroute-termine-defile.png | bug_candidate (claire-04) |
| 1.13 | « Commencer » | Mon espace | « Bonjour Claire. », espace « Claire Exemple Coaching ». Rail à icônes seules (infobulles système `title` uniquement). Carte « Mise en route : Compléter le profil de facturation » | 14-miseenroute-accueil-apres.png | ok |
| 1.14 | Survol de l'icône « ? » du rail | Aide | C'est « Plus d'outils » : un point d'interrogation pour « plus d'outils », je l'aurais pris pour l'aide | 15-miseenroute-survol-plusdoutils.png | observation |
| 1.15 | Clic « Compléter le profil de facturation » | Les champs SIRET et adresse | Paramètres s'ouvre sur Profil, en haut : je vois mon identité ; la section « Profil émetteur des factures » est à 711 px, sous le pied du dialogue | 16-miseenroute-facturation-ouvert.png | bug_candidate (claire-10) |
| 1.16 | Je défile, je saisis l'adresse de démo et le SIRET de démo 999 888 779 00009 | Champs acceptés | Acceptés. Les exemples grisés (« 123 456 789 », « FR 00 123 456 789 », « 0000Z ») ressemblent à des valeurs déjà remplies | 17-miseenroute-facturation-rempli.png | observation |
| 1.17 | « Enregistrer » | Un « c'est enregistré » visible | Rien ne change à l'écran. `POST /api/config/profile` 200 (requête 1038), `GET /api/invoices/billing/profile-status` rend `{"is_complete":true,"missing":[]}`. Le message « Profil enregistré » existe mais s'affiche dans la carte d'identité, hors de la zone visible (60-96 px pour une zone visible de 130 à 670), et disparaît en 3 s | 18-miseenroute-facturation-enregistre.png, 19-miseenroute-facturation-confirmation-hors-vue.png | bug_candidate (claire-11) |
| 1.18 | Échap | Retour à l'Accueil, carte « facturation » disparue | Échap ferme et rend le focus à la carte (anneau visible, bien). Mais la carte « Compléter le profil de facturation » est toujours là, 4 s plus tard aussi ; `setup-status` n'a pas été relu depuis la requête 941 (avant l'enregistrement), alors que l'API répond `billing_complete: true` | 20-miseenroute-accueil-apres-facturation.png | bug_candidate (claire-12) |
| 1.19 | Rail « Conversations » | Tiroir conforme à l'API | « Aucune conversation », conforme à `GET /api/chat/conversations` = `[]`. Focus dans le champ de recherche | 21-miseenroute-tiroir-conversations-vide.png | ok |

Arbre d'accessibilité : pendant l'assistant, focus sur le titre du dialogue, étape annoncée « Étape n sur 6, … » ; à l'Accueil, rail nommé (« Accueil », « Nouvelle conversation », « Conversations », « Projets », « Paramètres », « Plus d'outils », « Ouvrir le profil »).
Console du parcours : une seule erreur, celle du sélecteur natif (1.11, attendue hors Tauri) ; dix « IPC échoué, retry » au chargement (attendus hors Tauri).
Réseau du parcours : toutes les requêtes vont vers 127.0.0.1 ; filtre « hôte autre que 127.0.0.1 ou localhost » : zéro requête. `GET /api/config/llm/models/anthropic` est un catalogue statique côté moteur (`config.py` l. 1500), pas un appel à Anthropic.

### 2. Mes clients : créer trois contacts, les retrouver, en modifier un, comprendre où ils vivent

Préconditions : parcours 1 fait, carnet vide.
Gestes pour atteindre l'écran Contacts depuis l'Accueil : 5 (« Plus d'outils », recherche « clients » sans résultat, recherche « contacts », carte « Contacts », « Ouvrir Contacts »). Aucune entrée « Contacts » dans le rail ni sur l'Accueil.

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 2.1 | Rail « Plus d'outils » (icône « ? ») | Une liste où je trouve mes clients | Un dialogue titré « Capacités » (le bouton disait « Plus d'outils »), 30 capacités en 6 intentions, étiquettes « PARCOURS » / « VUE » non expliquées. Rien sur les clients dans « Organiser mon quotidien » | 22-contacts-plusdoutils.png | observation |
| 2.2 | Je tape « clients » | Mes clients | « Aucune capacité trouvée. Essaie avec le résultat souhaité, par exemple « devis » ou « analyser ». » | 23-contacts-recherche-clients.png | proposal (claire-15) |
| 2.3 | Je tape « contacts » | Contacts | 2 résultats : Contacts, Projets | 24-contacts-recherche-contacts.png | ok |
| 2.4 | Carte « Contacts » | Mon carnet, avec un bouton pour ajouter | Une vue « Bonjour Claire. » + un panneau « Contacts et contexte, lecture seule ». Quatre boutons « Ouvrir Contacts » identiques à l'écran, aucun « Ajouter ». Le titre de page reste « Bonjour Claire. » | 25-contacts-vue-vide.png | bug_candidate (claire-14) |
| 2.5 | « Ouvrir Contacts » | Le carnet | Écran « Contacts » : Importer (.vcf), Exporter, Nouveau contact ; filtres « Tout / Global / Projet / Conv. » ; état vide clair avec action | 26-contacts-ecran-contacts.png | ok |
| 2.6 | « Nouveau contact » | Un formulaire simple | Prénom, Nom, Entreprise (exemple grisé « Synoptïa »), Email, Téléphone, Adresse, Notes, Tags. Aucun choix de périmètre | 27-contacts-formulaire-vide.png | observation |
| 2.7 | Je crée Hélène Ménard-Lefèvre (accents, trait d'union), téléphone, adresse, notes, tags | Créée, accents intacts | Ligne ajoutée, pas de message. API : prénom et nom intacts, `scope: "global"`, `scope_id: null`. Badge ambre « RGPD ? » sur la ligne | 28-contacts-helene-rempli.png, 29-contacts-helene-cree.png | ok (observation sur « RGPD ? », claire-19) |
| 2.8 | Je crée Julien Garnier (Atelier Garnier) et Sophie Durand | Trois lignes | Trois lignes, du plus récent au plus ancien | 30-contacts-julien-rempli.png, 31-contacts-trois-crees.png | ok |
| 2.9 | Recherche « helene » (sans accent) | Hélène seule | Les trois fiches, Hélène en tête. `POST /api/memory/search` rend les trois avec des scores 0,568 / 0,536 / 0,518 | 32-contacts-recherche-sans-accent.png | bug_candidate (claire-16) |
| 2.10 | Recherche « Zorro » | Rien | Rien (il y a donc un seuil) | 33-contacts-recherche-nom-inexistant.png | ok |
| 2.11 | Recherche « Durand » | Sophie seule | Sophie seule | 34-contacts-recherche-durand.png | ok |
| 2.12 | Recherche « Hélène » (avec accent) | Hélène seule | Encore les trois fiches | 35-contacts-recherche-avec-accent.png | bug_candidate (claire-16) |
| 2.13 | Clic sur « Sophie Durand » | Voir sa fiche | Ouvre directement « Modifier le contact » | 36-contacts-fiche-sophie.png | observation (claire-18) |
| 2.14 | J'ajoute téléphone, adresse, note, tags ; « Mettre à jour » | Modifié | Dialogue refermé, pas de message ; API : champs à jour | 37-contacts-sophie-mise-a-jour.png | ok |
| 2.15 | Clic sur le chevron « › » d'Hélène | Une fiche détaillée | Le chevron n'est pas un bouton ; le bouton du nom recouvre toute la ligne (`before:absolute before:inset-0`), donc même formulaire de modification | (trace de clic Playwright : « button Hélène Ménard-Lefèvre … intercepts pointer events ») | observation (claire-18) |
| 2.16 | Filtre « Projet » | Comprendre où vivent mes clients | « Aucun contact dans le périmètre « Projet ». » + « Voir tous les périmètres ». Rien n'explique ce qu'est un périmètre ni comment y ranger quelqu'un ; aucune ligne n'affiche le sien | 38-contacts-filtre-projet.png | proposal (claire-17) |
| 2.17 | « Voir tous les périmètres » puis « Retour » | Revenir d'où je viens | Retour à la vue de lecture, rafraîchie (« 3 contacts dans la mémoire locale »), focus restitué sur « Ouvrir Contacts » | 39-contacts-apres-retour.png | ok |
| 2.18 | Clic sur Hélène dans cette vue | Sa fiche | Fiche de lecture dans le panneau : e-mail, téléphone, notes, étiquettes. L'adresse saisie n'y figure pas, ni le périmètre ; le nom est tronqué « Hélène Ménard-Lefè… » dans la colonne | 40-contacts-fiche-helene-lecture.png | observation (claire-18) |

Arbre d'accessibilité : liste nommée « Périmètre des contacts », boutons « Supprimer Hélène Ménard-Lefèvre » et « Actions RGPD » nommés ; « Retour » est annoncé « Revenir à la conversation unifiée » (jargon interne) ; focus sur le titre « Contacts » à l'ouverture.
Console du parcours : aucune nouvelle erreur. Réseau : toutes les requêtes vers 127.0.0.1, toutes en 200 (liste enregistrée dans `captures/claire/reseau-apres-parcours2.txt`) ; la seule ligne sans statut (n° 125) est une requête coupée par le rechargement du début.

### 3. Mes séances : poser deux séances cette semaine, les retrouver depuis la fiche de la cliente

Préconditions : trois contacts ; agenda local « Mon calendrier », aucun agenda en ligne.
Gestes : Accueil → « Ouvrir Agenda » (2) ; par séance : « Nouveau rendez-vous », saisie, « Enregistrer », « Confirmer la création » (4). Revenir à la fiche de la cliente depuis l'Agenda : 4 gestes.

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 3.1 | Accueil, « Ouvrir Agenda » | L'agenda | Vue Mois, septembre 2026, aujourd'hui (25) marqué ; mention « Agenda local « Mon calendrier » · aucun agenda en ligne branché » | 41-agenda-ouvert.png | ok |
| 3.2 | « Nouveau rendez-vous » | Formulaire | Formulaire en place du calendrier. Heures proposées 09:46-10:46 (l'heure courante, non arrondie). Participants = adresses e-mail libres, sans lien avec mes contacts | 42-agenda-formulaire-vide.png | observation (claire-21) |
| 3.3 | Séance d'Hélène, vendredi 25, 16 h-17 h, cabinet, description, son e-mail en participant | Accepté | Rempli | 43-agenda-seance-helene-rempli.png | ok |
| 3.4 | « Enregistrer » | Enregistré | Aperçu « Confirmer la création de l'événement » : clair et honnête (« Cet agenda local les enregistre mais ne peut pas leur envoyer d'invitation : préviens-les toi-même »). Dates en « 2026-09-25 16:00 » alors que le formulaire affichait « 25/09/2026 » ; lignes « Fournisseur : local », « Compte : Compte local » | 44-agenda-seance-helene-enregistree.png | observation (claire-21) |
| 3.5 | « Confirmer la création » | Confirmation | Le détail de l'événement s'affiche (vendredi 25 septembre 2026, 16:00-17:00, lieu, « 1 participant helene.menard@exemple.test ») : je sais que c'est enregistré | 45-agenda-seance-helene-confirmee.png | ok |
| 3.6 | Séance de Sophie, samedi 26, 10 h-11 h, visio, mêmes gestes | Enregistrée | Enregistrée ; vue Semaine « du 21 au 27 septembre 2026 » : la séance de Sophie apparaît ; celle d'Hélène à 16 h est sous le pli (défilement) | 46-agenda-seance-sophie-rempli.png, 47-agenda-semaine-deux-seances.png | ok |
| 3.7 | Vérification API | Deux séances aux bonnes heures | `GET /api/calendar/events` : `2026-09-25T16:00:00`-`17:00` et `2026-09-26T10:00:00`-`11:00`, participants conservés | (sortie curl citée dans la trace) | ok |
| 3.8 | En-tête « Rechercher », je tape « Hélène » | Ma cliente et ses séances | Dialogue « Rechercher dans Thérèse » : « 0 résultat », « Aucune capacité trouvée ». Cette recherche ne connaît que les commandes et capacités | 48-agenda-recherche-globale-helene.png | proposal (claire-20) |
| 3.9 | « Plus d'outils », « contacts », carte « Contacts », Hélène | Sa fiche, avec ses séances | Fiche de lecture : e-mail, téléphone, notes, étiquettes. Aucune séance. L'API `GET /api/memory/contacts/{id}/fiche` n'en contient pas non plus (seulement la note et un changement de score) | 49-agenda-retour-vers-contacts.png | proposal (claire-20) |

Arbre d'accessibilité : titre « Agenda » focalisé à l'ouverture, groupe « Vue de l'agenda » (Jour, Semaine, Mois pressé, Liste), boutons nommés « Période précédente », « Synchroniser l'agenda », « Importer un fichier .ics » ; les cases du mois sont des `generic` (non annoncées comme jours cliquables).
Console : aucune nouvelle erreur. Réseau : uniquement 127.0.0.1.

### 4. Compte rendu : l'écrire après la séance, le retrouver le lendemain

Préconditions : séance d'Hélène posée ; modèle local `gemma4-tia:latest`.
Gestes : « Écrire » (fausse piste, 2), chat (saisie + envoi, 2), attente 3 min 54 s ; « Sauvegarder comme raccourci » (fausse piste, 2) ; rechargement ; tiroir et recherche (3) ; puis « Préparer » → note de rendez-vous (4).

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 4.1 | Accueil, puce « Écrire » | Écrire un document | Panneau « Écrire un message », « Brouillon de réponse », « Aucun compte email connecté » : « Écrire » veut dire écrire un e-mail | 50-compterendu-ecrire.png | proposal (claire-22) |
| 4.2 | Je ferme et je tape ma demande dans le composeur (notes de séance) | Envoyer au chat | Saisie visible ; la puce « Écrire » reste enfoncée ; le bouton d'envoi s'appelle « Poursuivre dans le chat » | 51-compterendu-demande-saisie.png | ok |
| 4.3 | Envoi | Réponse, et savoir si c'est local | Conversation créée ; sélecteur « gemma4-tia:latest » avec badge « local » (infobulle « le traitement reste sur ta machine ») ; « Avec un modèle local, cela peut prendre plusieurs minutes. » ; icône Travaux à 1 | 52-compterendu-envoi-en-cours.png | ok |
| 4.4 | J'attends | Un signe de progression | Seulement un curseur clignotant pendant 3 min 31 s ; le journal du moteur montre l'appel d'outil `read_contact` à 09:52:22, rien à l'écran ne le dit | 53-compterendu-attente-30s.png, 54-compterendu-outil-contact.png | observation (claire-23) |
| 4.5 | Réponse | Un compte rendu propre | Arrivé à 09:52:45 (3 min 54 s, 1 662 tokens à 7,1 tok/s d'après le journal). Contenu fidèle à mes notes. Vouvoiement alors que l'application me tutoie ; en-tête « Compte rendu de séance Cliente : … Date : … Heure : … » tassé sur deux lignes ; pied « Local · 15652 tokens » | 55-compterendu-reponse.png | observation (claire-23) |
| 4.6 | « Sauvegarder comme raccourci » (le seul « sauvegarder » visible) | Ranger mon compte rendu | Dialogue « Créer une commande » (raccourci de prompt) : « Prompt / Contenu », « Icône (emoji) », catégorie « General » sans accent, aperçu et description avec les balises Markdown brutes « ** », et « Afficher sur la page d'accueil » coché d'office : mes notes confidentielles seraient affichées sur l'Accueil. J'annule | 56-compterendu-sauvegarder-raccourci.png | bug_candidate (claire-24) |
| 4.7 | Rechargement (« le lendemain ») | Retrouver mon travail | Accueil à jour : carte « Mise en route » disparue, puce « Facturer » apparue, séance d'Hélène reliée à « 1 contact CRM » | 57-compterendu-lendemain-accueil.png | ok |
| 4.8 | Tiroir « Conversations » | Mon compte rendu | Une conversation « Rédige le compte rendu de ma … », 2 messages, aperçu « Voici une proposition de compte rendu… » ; conforme à `GET /api/chat/conversations` (1 conversation, titre `Rédige le compte rendu de ma séance de 16 h avec H...`, 2 messages) | 58-compterendu-tiroir-lendemain.png | ok |
| 4.9 | Recherche « Hélène » dans le tiroir | La conversation | « Aucune conversation trouvée », alors que l'aperçu affiché juste avant contient « Hélène Ménard-Lefèvre » | 59-compterendu-recherche-tiroir-helene.png | bug_candidate (claire-25) |
| 4.10 | Recherche « compte rendu » | La conversation | Trouvée | 60-compterendu-recherche-tiroir-titre.png | ok |
| 4.11 | J'ouvre la conversation | Intacte | Intacte, badge « Local » conservé | 61-compterendu-rouvert-lendemain.png | ok |
| 4.12 | Puce « Préparer » | (je tente ma chance) | « Préparer un rendez-vous » : mes deux séances, la séance d'Hélène reliée à sa fiche par l'e-mail, et « Ajouter une note de rendez-vous… ajoutée au CRM du contact choisi après confirmation » : exactement ce qu'il me fallait, sous un verbe d'avant-séance | 62-compterendu-preparer.png | proposal (claire-22) |
| 4.13 | Je colle mon compte rendu, « Vérifier la note », « Confirmer l'ajout » | Rangé chez Hélène | Étape de vérification claire, puis « Note enregistrée dans l'historique CRM du contact. » ; l'historique affiche la note, mais aussi « Score: 50 → 85 », « score_change », « Raison: initial_creation » | 63-compterendu-note-verifier.png, 64-compterendu-note-ajoutee.png | bug_candidate (claire-26) |
| 4.14 | « Retrouver », fiche d'Hélène | Voir ma note de séance | La fiche ne montre que « Notes mémorisées » (la note d'origine) : la note de séance n'y est pas. L'API la contient (`GET /api/crm/activities?contact_id=…` : type `note`, titre « Note rendez-vous : Séance Hélène Ménard-Lefèvre ») | 65-compterendu-fiche-apres-note.png, 66-compterendu-fiche-helene-sans-note.png | bug_candidate (claire-27) |

Arbre d'accessibilité : pendant la génération, bouton « Arrêter la réponse » présent, champ « Message à THÉRÈSE » (« Ajouter un message à la file… ») ; le badge « Local » porte l'infobulle « Réponse locale (Ollama) : le traitement est resté sur ta machine. D'autres échanges peuvent sortir (recherche web, mise à jour, comptes raccordés). » ; « Note enregistrée… » est un `role="status"`.
Console : aucune erreur depuis le rechargement. Réseau : aucune requête hors 127.0.0.1 ; la génération passe par le moteur local, qui appelle Ollama en local (`/api/ps` : `gemma4-tia:latest` chargé, contexte 8192).

### 5. Facturer : un devis puis une facture pour Hélène, vérifier les PDF

Préconditions : profil de facturation complet (adresse et SIRET de démonstration), trois contacts.
Gestes : puce « Facturer », « Préparer un devis », saisie, « Enregistrer le brouillon », « Confirmer le brouillon » (5) ; « Ouvrir Devis et factures », « PDF » (2) ; clic sur la ligne, « Convertir en facture », « Convertir » (3) ; « PDF » (1).

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 5.1 | Puce « Facturer » | Faire un devis | Carte « Facturer un client, 0 document enregistré », deux boutons voisins « Nouveau devis » et « Préparer un devis » | 67-facturer-ouvert.png | ok |
| 5.2 | « Préparer un devis » | Formulaire | Panneau « Nouveau devis brouillon », Hélène présélectionnée, échéance et validité en double (25/10 et 30 jours). La ligne déborde : TVA « 20% » coupée au bord, bouton « Supprimer la ligne 1 » hors du panneau ; quantité (« 1 ») et prix (« 0 ») sans étiquette visible. TVA par défaut 20 % | 68-facturer-preparer-devis.png | bug_candidate (claire-28) |
| 5.3 | Ligne « Accompagnement individuel, séance d'une heure », 4 × 90 €, TVA 0 % (pas de numéro de TVA), notes | Totaux justes | HT 360 €, TVA 0 €, TTC 360 € ; description tronquée « Accompagnement indivi » ; « Enregistrer le brouillon » sous le pli | 69-facturer-devis-rempli.png | ok (troncature notée dans claire-28) |
| 5.4 | « Enregistrer le brouillon » | Enregistré | Confirmation en ligne : destinataire, montant, échéance, « crée un document local, ne génère aucun PDF et n'envoie rien » | 70-facturer-devis-enregistrer.png | ok |
| 5.5 | « Confirmer le brouillon » | Confirmation | « DEV-2026-001 enregistré comme brouillon. Aucun PDF n'a été généré et aucun email n'a été envoyé. » ; la carte de gauche passe à « 1 document enregistré ». Le formulaire reste rempli avec « Enregistrer le brouillon » actif (doublon possible, non essayé pour ne pas polluer la base) | 71-facturer-devis-confirme.png | observation |
| 5.6 | « Ouvrir Devis et factures » | La liste | DEV-2026-001, Brouillon, 360 €, actions « PDF » et « Supprimer ». Aucune action « transformer en facture » sur la ligne | 72-facturer-ecran-devis-factures.png | ok |
| 5.7 | « PDF » | Le PDF | Hors Tauri l'ouverture est impossible ; message « PDF généré. Fichier disponible : /tmp/therese-demo-c13/data/invoices/DEV-2026-001.pdf ». PDF lu : émetteur « Claire Exemple Coaching, 8 place de la Démonstration, 69002 Lyon, SIRET 999 888 779 00009 », destinataire « Hélène Ménard-Lefèvre, 3 rue des Écoles, 69003 Lyon », ligne et totaux justes. Mais « Mentions légales : TVA incluse selon les taux en vigueur » avec une TVA à 0 %, et « Paiement à réception de facture, net à 30 jours » | 73-facturer-devis-pdf-clic.png ; PDF copié dans le scratchpad | bug_candidate (claire-30) |
| 5.8 | Clic sur la ligne du devis | Détail | Dialogue « Modifier DEV-2026-001 », un autre formulaire que celui du panneau (colonnes étiquetées, TVA « 0% (exonéré… » tronquée, description coupée) ; boutons « Accepter », « Refuser », « Convertir en facture » | 74-facturer-devis-detail.png | observation (claire-31) |
| 5.9 | « Convertir en facture » | Confirmation | « Convertir en facture ? … Conditions : 30 jours, virement bancaire. Mentions legales : ajoutees automatiquement » (sans accents) | 75-facturer-convertir-clic.png | bug_candidate (claire-31) |
| 5.10 | « Convertir » | Une facture | Notification « Facture FACT-2026-001 créée à partir du devis DEV-2026-001 ». Dans la liste, le devis affiche « Envoyé le 25/09/2026 » alors que je ne l'ai jamais envoyé ; l'API dit `status: converted`, `sent_at: null` | 76-facturer-facture-creee.png | bug_candidate (claire-29) |
| 5.11 | « PDF » de la facture | Une facture propre | Émetteur, SIRET, adresse, cliente : justes. Conditions de paiement sans accents (« Date d'echeance », « une penalite de 11.62% annuel sera appliquee », « indemnite », « exigee », « anticipe », « neant ») et même mention « TVA incluse selon les taux en vigueur » malgré la TVA à 0 % | 77-facturer-facture-pdf.png ; FACT-2026-001.pdf lu | bug_candidate (claire-30) |

Arbre d'accessibilité : lignes de devis nommées (« Description ligne 1 », « Quantité ligne 1 », « Prix HT ligne 1 », « TVA ligne 1 ») ; statut « DEV-2026-001 enregistré comme brouillon… » annoncé (`role="status"`) ; bouton « PDF » annoncé « Générer et ouvrir le PDF ».
Console : `[INFO] PDF generated but local opening is unavailable: TypeError: Cannot read properties of undefined (reading 'invoke')` (attendu hors Tauri, repli affiché). Réseau : uniquement 127.0.0.1.
Non couvert : l'état « bloqué » (profil incomplet) ; je ne l'ai pas provoqué, pour ne pas vider le SIRET des personas suivants.

### 6. Confiance : savoir où vont mes données, vérifier que mes notes restent locales

Préconditions : modèle local actif, un compte rendu produit par le chat, une note de séance, un devis et une facture.
Gestes : « Contrôle des données » (1), « Confidentialité » (1), Échap × 2 ; rail « Paramètres », onglet « Service d'IA » (2).

| Étape | Geste | Attendu | Observé | Capture | Classement |
|---|---|---|---|---|---|
| 6.1 | En-tête « Contrôle des données » | Ce qui part de ma machine, maintenant | Un panneau titré « Centre de confiance » (autre nom que le bouton) : cinq rubriques génériques (« Données », « Modèles », « Traitement externe »…). Rien ne dit « ton modèle actuel est local ». Jargon : « une mutation (envoi, rendez-vous, recherche web, contact, document, outil MCP) », « Le Board… cherchent encore sans carte », « trousseau système » | 78-confiance-controle-donnees.png | proposal (claire-32) |
| 6.2 | « Confidentialité » | La page de confidentialité | Paramètres s'ouvre sur « Sécurité et confidentialité », mais le « Centre de confiance » reste ouvert par-dessus et masque la moitié droite du texte (« …dans ton dossier utilisateur : bas », « laisse… ») | 79-confiance-confidentialite.png | bug_candidate (claire-33) |
| 6.3 | Je lis (texte relevé dans l'arbre) | Une réponse honnête | Honnête et précis : données métier chiffrées (SQLCipher) ; « Deux endroits ne sont pas chiffrés : l'index Qdrant, qui contient en clair… les notes de tes contacts, et le stockage local de cette interface, où sont conservés tes conversations… » ; « Avec un modèle local (Ollama), le contenu de tes conversations ne part chez aucun fournisseur de modèle » ; recherche web vers DuckDuckGo même en local ; « Aucune télémétrie ». « Aucun consentement cloud accordé ». Mais « Dictée cloud (Groq) : non autorisée. La dictée reste possible en 100 % local. » et, plus bas, « La voix locale n'est pas embarquée dans cette version de THÉRÈSE. Mets l'application à jour pour en profiter. » Ces phrases importantes sont en 12 px | 79-confiance-confidentialite.png (arbre d'accessibilité cité) | bug_candidate (claire-35) |
| 6.4 | Échap | Fermer le panneau du dessus | Échap ferme Paramètres (la couche du dessous, celle que je lisais) et laisse le « Centre de confiance » ; il faut un second Échap. Focus rendu à « Confidentialité » puis à « Contrôle des données » | 80-confiance-apres-echap.png | bug_candidate (claire-34) |
| 6.5 | Paramètres, onglet « Service d'IA » | Confirmer le local | « En local, rien ne quitte ton ordinateur. » ; carte « Ollama (Local) · Actif · gemma4-tia:latest · 2 modèles installés » ; « Ollama connecté (http://localhost:11434) ». Grille compacte où l'option locale est visible d'emblée (contrairement à l'assistant) | 81-confiance-parametres-service-ia.png | ok |
| 6.6 | Vérification réseau et moteur | Rien ne sort | Navigateur : zéro requête vers un hôte autre que 127.0.0.1 ou localhost sur toute la session (filtre « tout hôte autre que 127.0.0.1 ou localhost », ressources statiques comprises). Moteur (pid 97943, `uvicorn … --host 127.0.0.1 --port 17393`) : aucune connexion TCP non locale au moment du relevé (`lsof -a -p 97943 -iTCP`) ; seul outil appelé pendant le compte rendu : `read_contact`. Le compte rendu porte le badge « Local » | (sorties citées) | ok |

Console du parcours : aucune erreur nouvelle ; sur toute la session, une seule erreur (sélecteur de dossier natif, attendue hors Tauri) et une information (ouverture de PDF indisponible hors Tauri).
Réseau : aucune requête hors machine.


## Constats numérotés

**claire-01, bug_candidate, mineure : le modèle local présélectionné est celui que l'écran déconseille.**
Étapes : base vierge, assistant, étape 3 « Service d'IA », choisir « Ollama (Local) ». Attendu : l'assistant propose d'office un modèle compatible avec la machine, ou au moins pas celui qu'il signale en rouge. Observé : `gemma4-tia:latest` est présélectionné avec « RAM déconseillée, environ 8,3 Gio requis, pour un plafond de 8 Gio » ; `qwen3:8b`, installé, est « RAM compatible, environ 6,9 Gio ». Preuve : 05-miseenroute-ollama-choisi.png, 06-miseenroute-qwen-essai.png. Fichier lu : `src/frontend/src/components/onboarding/LLMStep.tsx` l. 265-273 (et l'effet l. 248-253) : premier modèle local capable d'outils, sans consulter la mesure de RAM affichée juste en dessous.

**claire-02, proposal : pour une utilisatrice qui veut rester locale, le choix local n'est pas proposé, il est caché.**
Étape 3, 14 services, Claude (cloud) présélectionné et « Recommandé - Excellent coding et français » ; Ollama (Local) 14e sur 14, à 1 238 px (fenêtre 800 px). Pour une coach, « coding » ne veut rien dire, et le seul choix qui tient la promesse « Données locales » de l'étape 1 est au fond de la liste. Piste : une question d'abord (« Mes données restent sur ma machine » / « J'utilise un service en ligne »), ou Ollama en tête quand il est détecté. Preuve : 04-miseenroute-serviceia.png, mesure `{ rang: 14, total: 14, ollamaTop: 1238 }`.

**claire-03, bug_candidate, mineure : l'étape Sécurité s'ouvre défilée, son titre est caché.**
Étapes : à l'étape 3, défiler jusqu'à Ollama, « Continuer ». Attendu : l'étape 4 s'ouvre en haut. Observé : le conteneur `flex-1 overflow-y-auto` garde `scrollTop = 188` ; le titre « Sécurité et confidentialité » est à 38 px, sous le bandeau d'étapes (24-150 px). Preuve : 07-miseenroute-securite.png et mesure DOM.

**claire-04, bug_candidate, mineure : le pied de l'assistant n'est pas le même d'une étape à l'autre, et le bouton final est hors écran.**
Étapes 2, 3 et 5 : « Retour » en lien texte à gauche, bouton pilule à droite, pied fixe. Étape 4 : deux gros boutons collés aux bords du dialogue (Retour l=305 pour un dialogue l=304, bas à 775 pour 776). Étape 6 : le pied défile avec le contenu, « Commencer » est à 851-887 px, sous le bas du dialogue (776) et de la fenêtre (800). Attendu (grille, cohérence) : mêmes boutons au même endroit, action finale visible. Preuve : 02, 07, 12 et 13 ; mesures DOM.

**claire-05, bug_candidate, mineure : le texte de « Transcription vocale » se déplie hors de vue.**
Étape 4, déplier « Transcription vocale » (dernier élément d'une liste interne `max-h-[280px] overflow-y-auto`). Observé : l'explication est coupée à « … sauf si la dictée locale (Whisper) est » ; il faut défiler la liste interne, dans un dialogue qui défile déjà. C'est justement l'information qui dit que la dictée part en ligne par défaut. Preuve : 09-miseenroute-securite-voix-deplie.png.

**claire-07, bug_candidate, moyenne : « ne quittent jamais ta machine » est une promesse absolue, écrite petit, et fausse dès qu'un service cloud est choisi.**
Étape 2, sous le titre : « Ces informations sont stockées localement dans /tmp/therese-demo-c13/data et ne quittent jamais ta machine. » (12 px, gris), puis dans le même écran « Ces informations sont injectées dans le contexte de l'IA ». Le service cloud est présélectionné à l'étape suivante. Le profil est injecté dans le prompt système quel que soit le fournisseur (`src/backend/app/services/llm.py` l. 506-510, `_get_system_prompt_with_identity` → `get_cached_profile`). Attendu : une phrase vraie dans les deux cas (« restent sur ta machine avec un modèle local ; avec un service en ligne, elles accompagnent tes demandes »), lisible (grille : rien d'important sous 14 px). Preuve : 02-miseenroute-profil-vide.png, mesure `12px | rgb(82, 97, 120)`, `src/frontend/src/components/onboarding/ProfileStep.tsx` l. 173.

**claire-09, proposal : l'assistant ne demande ni adresse ni SIRET.**
Je voulais tout régler d'un coup. L'assistant s'arrête à l'identité ; la facturation se complète après, par une carte de l'Accueil, puis un défilement dans Paramètres. Piste : un volet optionnel « Je facture avec THÉRÈSE » à l'étape Profil. Preuve : 02, 14, 16.

**claire-10, bug_candidate, mineure : « Compléter le profil de facturation » n'ouvre pas la facturation.**
Accueil, carte « Mise en route : Compléter le profil de facturation ». Attendu : arriver sur les champs SIRET et adresse. Observé : Paramètres > Profil s'ouvre en haut, sur l'identité ; le titre « Profil émetteur des factures » est à 711 px, sous le pied du dialogue. Preuve : 16-miseenroute-facturation-ouvert.png, mesure `{ avant: 711 }`.

**claire-11, bug_candidate, moyenne : je ne sais pas si ma facturation est enregistrée.**
Paramètres > Profil, défiler jusqu'à la facturation, remplir, « Enregistrer ». Attendu : une confirmation là où je regarde. Observé : rien de visible ; le `role="status"` « Profil enregistré » est rendu dans la carte d'identité, à 60-96 px, hors de la zone défilante visible (130-670), et retiré après 3 s. L'enregistrement a pourtant réussi (`POST /api/config/profile` 200, `profile-status` complet). Preuve : 18, 19 ; `src/frontend/src/components/settings/ProfileTab.tsx` l. 326-331 (message dans la première `Carte`) et `SettingsModal.tsx` l. 593-594 (délai 3 s).

**claire-12, bug_candidate, moyenne : l'Accueil me demande encore de compléter une facturation que je viens de compléter.**
Suite de claire-11 : Échap, retour à l'Accueil. Observé : la carte « Compléter le profil de facturation » reste affichée (vérifié 4 s plus tard). L'API répond `{"billing_complete":true}` sur `GET /api/dashboard/setup-status`, mais l'écran ne l'a pas relu : dernière requête `setup-status` n° 941, avant l'enregistrement n° 1038. Preuve : 20-miseenroute-accueil-apres-facturation.png, liste réseau filtrée.

**claire-13, proposal : le vocabulaire de la mise en route est celui d'un développeur.**
« provider IA », « Multi-LLM » (étape 1) ; « Importer THÉRÈSE.md » (étape 2) ; « tokens », « contexte 1M », « co-développé avec Cursor », « Sonar », « clé API », « coding » (étape 3) ; « agents IA », « tools », « Connecteurs » avec une icône de terminal (étape 4) ; « ollama / gemma4-tia:latest » (étape 6) ; « Moteur actif 8ms » dans l'en-tête. Chacun de ces mots me fait douter. Preuve : 01, 02, 04, 07, 12, 14.

**claire-14, bug_candidate, mineure : la carte « Contacts » ouvre une vue sans titre juste et sans moyen d'ajouter.**
Étapes : « Plus d'outils », chercher « contacts », carte « Contacts ». Attendu (grille) : le titre dit où je suis, les boutons disent ce qu'ils font. Observé : titre de page « Bonjour Claire. », quatre boutons identiques « Ouvrir Contacts » (deux dans la carte, deux dans le panneau), mention « Lecture seule », aucun « Ajouter ». Il m'a fallu 5 gestes pour atteindre le carnet, et le rail n'a aucune entrée « Contacts » alors que le lexique en fait un objet principal. Preuve : 25-contacts-vue-vide.png, arbre d'accessibilité (4 × `button "Ouvrir Contacts"`).

**claire-15, proposal : la recherche de capacités ne connaît pas « clients ».**
Une coach dit « mes clients », pas « mes contacts ». « clients » → « Aucune capacité trouvée ». Piste : synonymes (clients, clientes, carnet, fiches). Preuve : 23-contacts-recherche-clients.png.

**claire-16, bug_candidate, moyenne : chercher un prénom rend tout le carnet.**
Étapes : trois contacts (Hélène Ménard-Lefèvre, Julien Garnier, Sophie Durand), écran Contacts, taper « helene » ou « Hélène ». Attendu : Hélène seule (un nom est une recherche exacte, pas une ressemblance). Observé : les trois fiches, dans les deux cas ; « Durand » filtre bien, « Zorro » rend vide. Réponse de `POST /api/memory/search` pour « helene » : scores 0,568 (Hélène), 0,536 (Julien), 0,518 (Sophie), tous au-dessus du seuil. Avec quinze clients, la recherche par prénom ne servira à rien. Preuve : 32, 35 ; requête réseau n° 1085 (corps de réponse cité) ; `src/backend/app/routers/memory.py` l. 479-484 (`score_threshold=0.5` en phase sémantique).

**claire-17, proposal : je ne sais pas où vivent mes clients.**
Le formulaire ne propose aucun périmètre, la liste n'en affiche aucun (l'API dit `global`), le filtre « Projet » répond « Aucun contact dans le périmètre « Projet » » sans dire comment y ranger quelqu'un, « Conv. » est abrégé, « périmètre » n'est expliqué nulle part. Piste : un badge de périmètre par ligne et une phrase d'aide sous les filtres. Preuve : 27, 31, 38.

**claire-18, observation : deux écrans de contacts qui ne réagissent pas pareil.**
Sur l'écran « Contacts », cliquer un nom (ou son chevron « › », décoratif et recouvert par le bouton du nom) ouvre « Modifier le contact » ; dans le panneau « Retrouver un contact », cliquer le même nom ouvre une fiche de lecture. Cette fiche montre e-mail, téléphone, notes et étiquettes, mais pas l'adresse que j'ai saisie, et tronque « Hélène Ménard-Lefè… ». Preuve : 36, 40 ; trace du clic Playwright sur le chevron.

**claire-19, observation : petits signaux inquiétants ou étrangers sur les fiches.**
Badge ambre « RGPD ? » sur chaque contact, expliqué seulement au survol (« Base légale RGPD non définie pour ce contact ») ; exemple grisé « Synoptïa » dans le champ Entreprise ; aucune confirmation après « Créer » ou « Mettre à jour » (seule la liste change). Preuve : 27, 29, 37.

**claire-20, proposal : une séance n'est reliée à rien, ni à la cliente ni à la recherche.**
Je pose une séance avec l'e-mail d'Hélène en participant ; ensuite, ni sa fiche (panneau « Contacts et contexte » ou formulaire de modification) ni la recherche de l'en-tête (« Hélène » → « 0 résultat ») ne me la montrent. Pour une coach, la fiche cliente sans ses séances n'a pas de sens. Pistes : relier un participant à un contact existant, afficher « Prochaines séances » sur la fiche, faire chercher la barre « Rechercher » dans les contacts et les rendez-vous. Il faut aussi 4 gestes pour revenir à la fiche depuis l'Agenda (au-delà de mes trois). Preuve : 45, 48, 49 ; réponse de `/api/memory/contacts/3a591cf0-…/fiche` (aucun événement).

**claire-21, observation : petites aspérités du formulaire de rendez-vous.**
Heures par défaut non arrondies (09:46-10:46) ; format de date différent entre le formulaire (« 25/09/2026 ») et l'aperçu de confirmation (« 2026-09-25 16:00 ») ; lignes techniques « Fournisseur : local » et « Compte : Compte local » ; une confirmation supplémentaire pour un agenda purement local, alors que le composeur promet la confirmation « avant tout envoi ou modification externe ». Preuve : 42, 44.

**claire-22, proposal : les verbes de l'établi ne disent pas ce qu'ils ouvrent.**
« Écrire » ouvre un brouillon d'e-mail, pas un document ; « Préparer » ouvre la préparation d'un rendez-vous, qui contient pourtant l'action d'après-séance « Ajouter une note de rendez-vous », rattachée à la fiche. Je l'ai trouvée par hasard, après deux fausses pistes. Pistes : « Écrire un e-mail », et une entrée « Après la séance : compte rendu » sur la séance elle-même (Agenda) et sur l'Accueil. Preuve : 50, 62.

**claire-23, observation : l'attente locale est muette et la réponse change de ton.**
3 min 54 s de curseur clignotant ; l'appel d'outil `read_contact` (journal, 09:52:22) n'est pas montré. L'avertissement « cela peut prendre plusieurs minutes » est juste et rassurant. La réponse vouvoie alors que l'application tutoie, et le pied affiche « 15652 tokens » (infobulle « Coût estimé de cette requête API… ») pour un modèle local gratuit. Preuve : 52 à 55, journal du moteur.

**claire-24, bug_candidate, mineure : « Sauvegarder comme raccourci » montre du Markdown brut et publie mes notes sur l'Accueil par défaut.**
Étapes : réponse du chat, survol, « Sauvegarder comme raccourci ». Observé : description et « Réponse capturée » avec les balises « **Compte rendu de séance** **Cliente :** … » en clair ; case « Afficher sur la page d'accueil » cochée d'office alors que le contenu est un compte rendu confidentiel ; catégorie « General » sans accent. Pour moi, « Sauvegarder » voulait dire « ranger mon compte rendu ». Preuve : 56-compterendu-sauvegarder-raccourci.png, arbre d'accessibilité (textbox « Description » : « …Hélène Ménard-Lefèvre.**Compte rendu »).

**claire-25, bug_candidate, moyenne : le tiroir ne trouve pas une conversation par le nom de la cliente.**
Étapes : envoyer une demande de plus de 50 caractères où le nom arrive après le 50e (« Rédige le compte rendu de ma séance de 16 h avec Hélène Ménard-Lefèvre… »), recharger, tiroir « Conversations », chercher « Hélène ». Attendu : la conversation. Observé : « Aucune conversation trouvée », alors que l'aperçu affiché sous le titre contient « Hélène Ménard-Lefèvre ». Cause lue : le titre est la demande coupée à 50 caractères (`src/backend/app/routers/chat.py` l. 1261, `Conversation(title=request.message[:50])`) et le filtre du tiroir ne regarde que le titre (`src/frontend/src/components/prototype/PrototypeConversationDrawer.tsx` l. 164-174). Preuve : 59, 60 ; `GET /api/chat/conversations` (titre `…de 16 h avec H...`).

**claire-26, bug_candidate, mineure : l'historique CRM affiche des identifiants internes.**
Après l'ajout de la note, « Historique CRM disponible » montre « Score: 50 → 85 », « 25/09/2026 · score_change », « Raison: initial_creation ». Attendu (grille, lexique) : des mots en français sans jargon. Preuve : 62, 64 ; `GET /api/crm/activities` (`score_change | Score: 50 → 85 | Raison: initial_creation`).

**claire-27, bug_candidate, moyenne : la note de séance « ajoutée au CRM du contact » n'apparaît pas sur la fiche du contact.**
Étapes : « Préparer », séance d'Hélène, « Ajouter une note de rendez-vous », vérifier, confirmer (« Note enregistrée dans l'historique CRM du contact. ») ; puis « Retrouver », Hélène. Attendu : la note de séance visible sur sa fiche « Contacts et contexte ». Observé : seule « Notes mémorisées » (la note saisie à la création) ; la note de séance n'est visible que dans le panneau « Préparer » de ce rendez-vous. L'API l'a bien (`note | Note rendez-vous : Séance Hélène Ménard-Lefèvre`). Le lendemain, depuis la fiche de ma cliente, je ne retrouve pas mon compte rendu. Preuve : 64, 66 ; `GET /api/crm/activities?contact_id=3a591cf0-…`.

**claire-28, bug_candidate, mineure : la ligne du devis déborde du panneau « Facturer ».**
Étapes : puce « Facturer », « Préparer un devis ». Observé à 1280×800 : le conteneur défilant fait 550 px de contenu pour 517 px visibles ; la TVA de la ligne va de 1 179 à 1 265 px, le bouton « Supprimer la ligne 1 » de 1 273 à 1 305 px pour un panneau qui s'arrête à 1 280 : il est invisible sans défilement horizontal. Quantité et prix n'ont pas d'étiquette visible (seulement « 1 » et « 0 ») et la description est tronquée. Preuve : 68, 69 ; mesures DOM.

**claire-29, bug_candidate, moyenne : après conversion, le devis se dit « Envoyé le 25/09/2026 » alors qu'il n'a jamais été envoyé.**
Étapes : devis brouillon, « Convertir en facture », « Convertir ». Attendu : l'écran ne prétend pas un envoi qui n'a pas eu lieu. Observé : colonne « Envoi » du devis « Envoyé le 25/09/2026 », alors que l'API rend `status: converted`, `sent_at: null`. Cause lue : `src/frontend/src/components/invoices/presentationFacture.ts` l. 67 construit « Envoyé le <date d'émission> » (sans lire `sent_at`), et la branche des devis l. 100-117 l'affiche pour tout statut autre que brouillon et annulé, y compris `converted`, `accepted`, `refused` et `expired`. Preuve : 76 ; réponse de `GET /api/invoices/`.

**claire-30, bug_candidate, moyenne : les PDF remis à la cliente portent une mention de TVA fausse et des conditions sans accents.**
Étapes : devis puis facture à TVA 0 % (pas de numéro de TVA), « PDF ». Observé sur les deux PDF : « Mentions légales : TVA incluse selon les taux en vigueur » alors que toutes les lignes sont à 0 % ; la mention d'exonération « TVA non applicable, art. 293 B du CGI » n'apparaît pas. Le moteur la connaît (`tva_applicable`, `src/backend/app/models/entities.py` l. 808) mais aucun écran ne permet de déclarer la franchise (`tva_applicable` n'apparaît que dans `src/frontend/src/services/api/invoices.ts`). Sur la facture, le bloc des conditions est sans accents (« Date d'echeance », « penalite… appliquee », « indemnite… exigee », « anticipe : neant », `src/backend/app/routers/invoices.py` l. 916-936), avec « 11.62% » au point décimal. Sur le devis, « Paiement à réception de facture, net à 30 jours » se contredit. C'est le document juridique que ma cliente reçoit. Preuve : textes extraits des PDF DEV-2026-001 et FACT-2026-001, rendus visuels relus.

**claire-31, bug_candidate, mineure : deux formulaires de devis différents, et une confirmation sans accents.**
Le devis se crée dans le panneau « Facturer » (lignes sans étiquettes, TVA « 0% ») et se modifie dans « Modifier DEV-2026-001 » (colonnes étiquetées, TVA « 0% (exonéré) ») : même objet, deux présentations. La confirmation de conversion affiche « Mentions legales : ajoutees automatiquement » (`src/frontend/src/components/invoices/InvoiceForm.tsx` l. 877). Preuve : 68, 74, 75.

**claire-32, proposal : le « Centre de confiance » ne répond pas à ma question.**
Je veux savoir, maintenant, si mes notes partent quelque part. Le panneau donne des principes généraux, sous un autre nom que le bouton (« Contrôle des données » → « Centre de confiance »), avec « mutation », « outil MCP », « Board », « sans carte », « trousseau système ». Piste : une ligne d'état en tête (« Ton assistante répond en local avec gemma4-tia. Rien ne sort, sauf la recherche web si tu l'acceptes. »). Preuve : 78.

**claire-33, bug_candidate, mineure : « Confidentialité » ouvre Paramètres sous le « Centre de confiance », qui en masque le texte.**
Étapes : « Contrôle des données », « Confidentialité ». Attendu : la page de confidentialité lisible. Observé : le panneau « Centre de confiance » (x 904-1 264) reste au-dessus du dialogue Paramètres (x 64-1 216) ; le paragraphe « Tes données métier sont stockées… » (x 359-1 153) est coupé ; au point x=1000 de ce paragraphe, l'élément visible appartient au « Centre de confiance ». Preuve : 79 ; mesure DOM (`elementAuPoint1000: "Centre de confiance"`).

**claire-34, bug_candidate, mineure : Échap ferme la couche du dessous.**
Suite de claire-33 : Échap ferme Paramètres, que je lisais, et laisse le « Centre de confiance » qui le couvrait. Attendu (grille) : Échap ferme ce qui est au-dessus. Preuve : 80 ; liste des dialogues après Échap : `["Centre de confiance"]`.

**claire-35, bug_candidate, mineure : la page de confidentialité se contredit sur la dictée locale.**
Même page : « Dictée cloud (Groq) : non autorisée. La dictée reste possible en 100 % local. » (`src/frontend/src/components/settings/PrivacyTab.tsx` l. 466-469, sans condition) et « La voix locale n'est pas embarquée dans cette version de THÉRÈSE. Mets l'application à jour pour en profiter. » (`VoiceLocalSection.tsx` l. 120-123, quand `stt_available` est faux). L'assistant, lui, disait que la dictée part chez Groq « sauf si la dictée locale (Whisper) est choisie dans Paramètres > Confidentialité ». Vu sur le moteur de développement : sur l'application installée `stt_available` peut valoir vrai, mais la première phrase reste inconditionnelle. Ces informations sont en 12 px. Preuve : 09, 79 ; arbre d'accessibilité de l'onglet.

Numérotation : claire-06 et claire-08 n'existent pas (fusionnés en cours de route dans claire-04 et claire-07).

## Transitions couvertes et angles morts

**Transitions couvertes** (toutes capturées, 81 captures) :
- Assistant de mise en route : Bienvenue → Profil → Service d'IA (choix Ollama, changement de modèle aller-retour) → Sécurité (deux dépliages) → Dossier (échec du sélecteur natif, « Passer ») → Terminé (défilement) → Accueil.
- Accueil → carte « Compléter le profil de facturation » → Paramètres > Profil → Enregistrer → Échap → Accueil (état périmé) → rechargement (état à jour).
- Accueil → « Plus d'outils » → recherche de capacité (échec « clients », succès « contacts ») → vue « Contacts et mémoire » → « Ouvrir Contacts » → création × 3 → recherches × 4 → modification → filtre « Projet » → « Voir tous les périmètres » → « Retour » → fiche de lecture.
- Accueil → « Ouvrir Agenda » → création de deux rendez-vous avec confirmation → vue Semaine → recherche de l'en-tête → retour aux contacts (4 gestes).
- Accueil → « Écrire » → chat → envoi → attente locale (3 min 54 s) → réponse → « Sauvegarder comme raccourci » (annulé) → rechargement → tiroir → recherches × 2 → réouverture → « Préparer » → note de rendez-vous (vérifier, confirmer) → « Retrouver » → fiche.
- Accueil → « Facturer » → devis brouillon (enregistrer, confirmer) → « Devis et factures » → PDF → détail → conversion → PDF de la facture.
- « Contrôle des données » → « Confidentialité » → Échap × 2 → Paramètres > Service d'IA ; relevé réseau navigateur et moteur.

**Angles morts** :
- Tauri absent (navigateur) : sélecteur de dossier natif et ouverture du PDF non testables ; les infobulles système (`title`) du rail ne sont pas visibles sur les captures.
- Instrument : `browser_wait_for` avec un temps rendait la main trop tôt ; l'attente de la réponse locale a été mesurée par le journal du moteur (boucle shell), pas par l'outil.
- Non provoqués pour ne pas abîmer la base partagée : facturation bloquée par un profil incomplet, doublon de devis par un second « Enregistrer le brouillon », suppression.
- Non parcourus : thème sombre, navigation entière au clavier (seuls Échap et le retour de focus sont testés), dictée (micro), recherche web, atelier documentaire (aucun écran ne me l'a proposé), vue Liste de l'agenda, pipeline.
- Sortie réseau du moteur : relevé ponctuel (`lsof`) et lecture du journal, pas une capture continue.
- La contradiction sur la voix locale (claire-35) est vue sur le moteur de développement ; à revérifier dans l'application installée.

**Données laissées en place pour Hugo, Nathalie et Zoé** : profil « Claire Exemple », « Claire Exemple Coaching », adresse « 8 place de la Démonstration, 69002 Lyon », SIRET 999 888 779 00009 ; modèle `ollama / gemma4-tia:latest` ; contacts Hélène Ménard-Lefèvre, Julien Garnier (Atelier Garnier), Sophie Durand ; séances du 25/09 16 h (Hélène) et du 26/09 10 h (Sophie) dans « Mon calendrier » ; une conversation de compte rendu ; une note CRM sur Hélène ; devis DEV-2026-001 (converti) et facture FACT-2026-001 (brouillon), PDF dans `/tmp/therese-demo-c13/data/invoices/`.

**Bilan** : 33 constats avec preuve (21 bug_candidate, 8 proposal, 4 observation) ; aucun constat écarté faute de preuve ; deux faits écartés comme angles morts d'instrument (sélecteur de dossier, ouverture du PDF).

## Tokens consommés (si connus)

Environ 460 000 tokens de contexte (compteur de session : 15 000 000 au départ, environ 14 540 000 à la fin de la trace).
