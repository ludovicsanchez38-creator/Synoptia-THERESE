**COCO : la direction 2 est le bon socle, mais le dépôt n’est pas prêt pour un vote de validation.** La cohérence visuelle avance davantage que les parcours, les états et la fiabilité de la comparaison.

Audit en lecture seule : fichiers imposés lus, captures inspectées, 110 paires de contraste recalculées sans écriture. Les notes évaluent les propositions ; aucune recette native multiplateforme n’a été effectuée.

**1. Regard UX/UI : 66/100**

Le tableau des devis permet de retrouver rapidement un client, un montant et une échéance, tandis que la décision présente enfin sa synthèse avant les avis. L’accès aux fonctions et plusieurs détails de lecture empêchent encore cette clarté de devenir une expérience utilisable.

1. **L’utilisateur doit encore deviner où aller et ce qui va se passer.** Dans `accueil-d2-clair.png`, « Commencer » ne précise pas l’action, et « l’essentiel / le minimum » oppose deux notions presque synonymes. L’assemblage range aussi agenda, contacts, projets et devis sous le même bouton « Fichiers » : [assemble.py:10](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/docs/da/2026-09-05-propositions/maquettes/assemble.py:10>). **Correction :** nommer le geste prioritaire, par exemple « Préparer la relance de Claire », rendre les filtres explicites et faire déboucher le rail sur des destinations nommées, avec une indication du domaine courant.

2. **Le plancher de 14 px est annoncé mais contourné.** À la taille normale, les badges de statut font 12 px et les actions du composeur 13 px : [base.css:86](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/docs/da/2026-09-05-propositions/maquettes/da/base.css:86>), [base.css:109](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/docs/da/2026-09-05-propositions/maquettes/da/base.css:109>). « Impayée » ou « Préparer un rendez-vous » portent pourtant une information essentielle. **Correction :** appliquer 14 px par défaut aux actions et statuts déterminants ; réserver 12 px aux métadonnées secondaires, puis vérifier les trois tailles utilisateur.

3. **L’agenda ne tient pas ses différentes vues.** La capture supplémentaire `agenda-d2-mois.png` montre des événements étirés sur presque toute la fenêtre. La cause est présente dans [agenda.html:14](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/docs/da/2026-09-05-propositions/maquettes/_fragments/agenda.html:14>) : `.evt` impose un positionnement absolu également aux puces du mois. **Correction :** limiter ce placement à la semaine, remettre les événements du mois dans le flux des cellules et répartir les rendez-vous simultanés en colonnes sans masquer leurs informations.

**À garder absolument :** les montants alignés et la séparation visuelle envoi/paiement/échéance de `devis-d2-clair.png` ; les contacts hors pipeline accessibles dans `contacts-d2-clair.png` ; la synthèse placée en premier dans `decision-d2-clair.png`.

**2. Regard artiste : 58/100**

La direction 2 possède une palette cohérente et une hiérarchie stable entre les écrans présentés. Sa composition principale reste cependant celle d’un assistant conversationnel générique, et les variantes apportent surtout un traitement de surface.

1. **La signature reste concentrée dans les couleurs.** Dans `accueil-d2-clair.png`, salutation centrée dans une colonne, avatar « T », étoile et grand composeur constituent l’essentiel de l’identité. **Correction :** composer l’accueil autour du travail engagé : dossier client, pièce concernée, prochaine échéance et proposition de THÉRÈSE reliés visuellement. Donner à cet ensemble une forme reconnaissable qui se retrouve dans les autres écrans.

2. **La direction 3 ajoute trop de cadre pour trop peu de sens.** Dans `accueil-d3-clair.png` et `decision-d3-clair.png`, fond navy, carte intérieure, bordures et couture s’empilent ; le texte dispose de moins de largeur. [d3.css:4](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/docs/da/2026-09-05-propositions/maquettes/da/d3.css:4>) ajoute effectivement un second conteneur avec marge intérieure. **Correction :** réserver une région navy compacte à un travail préparé par THÉRÈSE, avec son état clairement nommé. Employer la couture sur un seul bord utile ; faire suivre brièvement ce repère jusqu’à la tâche créée, avec un équivalent fixe en mouvement réduit.

3. **Le spécimen ne permet pas de juger correctement les variantes.** Les captures `socle-d2-clair.png` et `socle-d3-clair.png` sont visuellement identiques dans la partie montrée. En D1, le spécimen « Bonjour Marie » demande une graisse 800 alors qu’Instrument Serif est embarqué en 400 : [socle.html:34](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/docs/da/2026-09-05-propositions/maquettes/_fragments/socle.html:34>), [base.css:7](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/docs/da/2026-09-05-propositions/maquettes/da/base.css:7>). **Correction :** employer exactement les composants et graisses des écrans réels ; montrer, sur le socle, une même séquence humaine/THÉRÈSE dans chaque direction.

**À garder absolument :** le cyan uni des actions principales, les quatre accents de domaine visibles dans le nuancier, Jakarta pour les titres fonctionnels. Le serif limité aux grands titres éditoriaux par [d1.css:4](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/docs/da/2026-09-05-propositions/maquettes/da/d1.css:4>) reste une exploration recevable.

**3. Regard pragmatique : 52/100**

L’extraction des jetons et l’assemblage des fragments constituent une base de travail réutilisable ; j’ai vérifié que `tokens.css` correspond à l’extraction actuelle de `globals.css`. Le dépôt sous-représente toutefois le travail d’interaction et ne fournit pas encore un instrument d’arbitrage suffisamment fiable.

1. **Les états sont montrés, mais les parcours ne sont pas démontrés.** « Commencer » n’a pas de gestionnaire ; les scripts affichent principalement des variantes selon `?etat=…`. Les instructions de déplacement clavier du pipeline ne sont accompagnées d’aucun traitement clavier : [accueil.html:20](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/docs/da/2026-09-05-propositions/maquettes/_fragments/accueil.html:20>), [contacts.html:92](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/docs/da/2026-09-05-propositions/maquettes/_fragments/contacts.html:92>). **Correction :** réaliser un parcours local complet, avec navigation, ouverture, confirmation et retour du focus. Les 10 à 18 jours affichés doivent rester une estimation de cadrage jusqu’au découpage des composants et interactions.

2. **Le comparateur peut produire une validation ambiguë.** Six captures référencées sont absentes ; l’« avant » est redimensionné à la largeur choisie, sans recréer le viewport correspondant ; le vote mémorise `0.66.1`, mais aucune révision propre aux maquettes. Le choix du socle n’encadre pas les directions votées ensuite : [build.py:59](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/docs/da/2026-09-05-propositions/build.py:59>), [build.py:66](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/docs/da/2026-09-05-propositions/build.py:66>). **Correction :** réparer les références, distinguer capture historique et comparaison à dimensions identiques, enregistrer la révision DA et la configuration complète, puis signaler tout vote incompatible avec le socle retenu.

3. **Le contraste élevé est écrasé par les variantes.** [d1.css:2](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/docs/da/2026-09-05-propositions/maquettes/da/d1.css:2>) remet le papier malgré le contraste élevé ; [d3.css:3](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/docs/da/2026-09-05-propositions/maquettes/da/d3.css:3>) redéfinit les couleurs dans son sous-arbre. La cascade et les calculs donnent **1,20:1** pour l’accent cyan sur papier en D1, et **6,14:1** pour l’erreur sur surface en D3, sous les 7:1 demandés. **Correction :** rendre le contraste élevé prioritaire partout et tester les combinaisons direction × thème × contraste sur les styles calculés.

**À garder absolument :** l’extraction automatique des jetons, les fragments communs, les dimensions de viewport explicites et la mention « Plus tard conserve l’existant ». Ces choix réduisent le coût de correction et clarifient le périmètre.

**4. Regard contradicteur : 40/100**

Les propositions font l’effort de représenter des données métier et des situations dégradées. Plusieurs contradictions rendent pourtant leurs recommandations et leurs indicateurs moins crédibles que leur présentation ne le suggère.

1. **Le scénario partagé se contredit.** L’accueil annonce samedi 5 septembre, l’agenda affiche vendredi 5 ; la facture de juillet reste « à envoyer » alors que le tableau l’annonce envoyée le 28 juillet ; Garage Benali figure dans « Devis envoyé » avec « Brouillon, non envoyé ». Ces contradictions sont visibles dans `accueil-d2-clair.png`, `agenda-d2-clair.png`, `devis-d2-clair.png` et `contacts-d2-clair.png`. **Correction :** alimenter tous les écrans avec un jeu de données commun, incluant dates, relations et transitions de statut ; calculer les compteurs depuis ces données.

2. **La décision partielle cite un avis qui n’a pas été rendu.** [decision.html:72](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/docs/da/2026-09-05-propositions/maquettes/_fragments/decision.html:72>) remplace la carte du contradicteur par un échec, mais conserve « Ce que les cinq avis ont en commun », son argument et les divergences. **Correction :** produire une synthèse correspondant réellement aux quatre avis disponibles, identifier l’avis manquant et présenter les tâches proposées à relire avant leur création.

3. **La présentation donne une autorité excessive aux données simulées.** « Moteur local actif 14 ms » est écrit en dur dans [_coque.html:4](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/docs/da/2026-09-05-propositions/maquettes/da/_coque.html:4>) ; la marge de 31 % n’expose aucun calcul ; « En local, rien ne quitte ton ordinateur » dépasse ce que prouve cette maquette : [parametres.html:47](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/docs/da/2026-09-05-propositions/maquettes/_fragments/parametres.html:47>). **Correction :** identifier les données de démonstration dans le comparateur, rendre les hypothèses chiffrées consultables et limiter les messages de confiance aux propriétés effectivement vérifiées.

**À garder absolument :** l’erreur d’agenda qui précise quelles sources manquent dans [accueil.html:37](</Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/docs/da/2026-09-05-propositions/maquettes/_fragments/accueil.html:37>) ; la distinction entre clé refusée et service indisponible dans `parametres-d2-sombre-invalide.png`. Ce sont des bases utiles pour construire la confiance.

**Synthèse : 54/100**, moyenne des quatre regards.

Les cinq corrections avant présentation à Ludo :

1. **Unifier le scénario et les états**, notamment les dates, les factures envoyées, les étapes commerciales et la décision partielle.
2. **Rendre un parcours métier complet utilisable**, depuis l’alerte d’accueil jusqu’au travail préparé, à sa validation et au retour contextualisé.
3. **Corriger l’accessibilité réelle**, avec les textes essentiels à 14 px par défaut, les combinaisons de contraste, le clavier et le focus.
4. **Fiabiliser le dépôt de preuve**, en réparant l’agenda mensuel, les captures absentes et la traçabilité des votes ; qualifier aussi 800×600, les grands textes et les listes longues.
5. **Donner à D2 une composition propre**, fondée sur les dossiers, leurs pièces et les actions proposées, puis éprouver cette signature sur accueil, devis et décision.

**Oui, D2 est le bon socle.** Ses jetons partagés, ses titres fonctionnels et ses tableaux donnent une base cohérente à prolonger.

Pour qu’un dirigeant de TPE cesse de dire « on dirait Claude ou ChatGPT », il manque surtout une expérience reconnaissable du travail suivi : ouvrir Claire Roux, retrouver la facture précise, comprendre l’alerte, relire une relance préparée et retrouver ensuite sa trace. Cette continuité doit avoir sa propre composition visuelle, avec un repère discret qui accompagne les changements d’état. **La signature de THÉRÈSE doit devenir visible dans ce qu’elle relie et fait avancer.**

