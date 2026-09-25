# Questions pour Ludo après les revues des huit RFC (25/09/2026)

Les huit RFC des grandes propositions (P-105 à P-110, P-121, P-125) sont
revenues NO-GO de la revue adverse (`docs/plans/revues/2026-09-25-revue-rfc-*.md`).
Aucune ne sera codée avant d'avoir été reprise. Les questions ci-dessous sont
celles que le code ne tranche pas ; chacune porte une recommandation, que tu
peux accepter d'un « oui » global ou corriger une par une.

## P-105 : alerte quand un mail touche une tâche

1. Le chantier « mise au repos des écritures de fond » attend ton arbitrage ;
   sans lui, la relève automatique toutes les 30 minutes ne peut pas partir.
   **Recommandation** : le valider, et livrer d'abord le rapprochement au geste
   (à l'ouverture du Courrier) sans relève de fond.
2. L'interrupteur « désactivé par défaut » coupe-t-il aussi le rapprochement
   à l'ouverture du Courrier ? **Recommandation** : non, il ne coupe que la
   relève de fond ; au geste, le rapprochement est local et visible.
3. Sur un compte IMAP, « Pas lié » ne vaut que pour un message tant que les
   fils ne sont pas reconstitués. **Recommandation** : reconstituer les fils
   (en-têtes `In-Reply-To` et `References`) avant de livrer.
4. Durée de conservation des rapprochements écartés et des silences.
   **Recommandation** : 90 jours, purgés avec la fiche à l'anonymisation.
5. Fuseau et jours fériés. **Recommandation** : fuseau du système, jours
   fériés français exclus.
6. L'alerte apparaît-elle aussi dans « Cette semaine » ? **Recommandation** :
   oui, une ligne, sans relève supplémentaire.

## P-106 : lire et exporter des formats structurés

7. Personne ne peut encore saisir durées et dépendances : l'export du planning
   serait vide. **Recommandation** : commencer par la lecture des fichiers de
   Dr_logic (cartes mentales, BPMN) ; l'export attend la saisie du planning.
8. Un document lu par l'assistante en cours de conversation part sous l'accord
   du chat. **Recommandation** : exiger l'accord « documents » dès qu'un outil
   de lecture de fichier est offert à un modèle en ligne.
9. Où ranger la copie d'une carte modifiée ? **Recommandation** : dans un
   dossier de THÉRÈSE, jamais à côté de l'originale (elle serait réindexée).

## P-107 : un périmètre d'action visible

10. Le journal des validations. **Recommandation** : outil, date, oui ou non,
    empreinte salée, jamais le contenu ; 12 mois ; effacé par « Effacer toutes
    mes données ».
11. Le Centre de confiance dit-il ce qui sort d'après ta configuration réelle ?
    **Recommandation** : oui, comme la ligne d'état livrée par P-118.
12. Le pont qui ouvre contacts, e-mails et factures aux agents de l'Atelier
    apparaît-il au périmètre avec un interrupteur ? **Recommandation** : oui.
13. « Retirer un outil » vaut-il aussi pour les agents et l'Atelier ?
    **Recommandation** : oui, partout, et l'écran le dit.

## P-108 : reprendre son travail sur une autre machine

14. Même version exigée des deux côtés ? **Recommandation** : oui ; une
    archive d'une version plus récente est refusée (« mets cette machine à
    jour d'abord »).
15. Les connecteurs (MCP) arrivent-ils actifs ? **Recommandation** : non,
    désactivés et listés « à réactiver » avec leur commande.
16. Combien d'états « d'avant relais » garder ? **Recommandation** : les trois
    derniers.
17. L'alerte « tes données sont dans un dossier synchronisé » part-elle avant
    le reste ? **Recommandation** : oui, c'est le lot le moins cher et le plus
    urgent.

## P-109 : conversation vocale

18. Conversation neuve à chaque session vocale, ou conversation ouverte ?
    **Recommandation** : conversation neuve (pas de documents ni de projet
    embarqués sans le voir).
19. En mode hybride, l'accord pour le modèle en ligne est-il demandé au
    démarrage de la session ? **Recommandation** : oui, une fois, avant la
    première parole.
20. Les dictées déjà conservées chez les testeurs (défaut B-1424, corrigé le
    25/09) sont-elles purgées à la mise à jour ? **Recommandation** : oui, au
    premier démarrage de la version corrigée, et dit dans les notes de version.
21. Espace comme arrêt ? **Recommandation** : non ; Échap et le grand bouton
    seulement (Espace active déjà les boutons).

## P-110 : un Word reçu par mail, intégré à un site PHP

22. Git exigé d'un bénévole sous Windows ? **Recommandation** : non ; une voie
    sans git (copie avant et après, différence calculée par THÉRÈSE).
23. Le site lu par l'Atelier peut-il partir chez un fournisseur en ligne ?
    **Recommandation** : seulement après masquage des fichiers de mots de
    passe ; sinon Atelier local.
24. Sécurité du site : relecture du bénévole ou contrôle bloquant ?
    **Recommandation** : contrôle automatique bloquant avant fusion (aucun
    `<?` ajouté hors gabarit), plus la relecture.
25. Signalement des données personnelles dès le premier lot ?
    **Recommandation** : oui, dans l'aperçu.

## P-121 : un seul formulaire de devis

26. Arrondi d'une ligne au demi-centime (aujourd'hui l'écran dit 3,13 et le
    serveur 3,12 pour 2,5 × 1,25 €). **Recommandation** : arrondi commercial
    (3,125 donne 3,13) partout, serveur compris, en centimes entiers.
27. Règles plus strictes (échéance, validité) sur les pièces déjà
    enregistrées ? **Recommandation** : non, seulement à la création ou quand
    le champ est modifié.
28. Le taux 0 suit-il le régime du profil ? **Recommandation** : oui
    (franchise : « TVA non applicable, art. 293 B du CGI »).
29. Un devis envoyé ou accepté peut-il être retouché depuis Facturer ?
    **Recommandation** : non, refus côté serveur comme à l'écran.

## P-125 : la réponse se termine en fond

30. Combien de réponses de fond en même temps en ligne ? **Recommandation** :
    deux, les suivantes en file avec mention.
31. Pendant une réponse de fond, purge et restauration ? **Recommandation** :
    elles arrêtent d'office les réponses en cours, en le disant (défaut B-1425
    en cours de reproduction sur le même sujet).
32. Pièces jointes d'une réponse de fond qui échoue ? **Recommandation** :
    gardées sur la conversation d'origine, jamais déposées ailleurs.

## Hors RFC, en attente de toi

- P-132 moitié 2 : vocabulaire unique pipeline et prestation, étape « Perdu ».
- P-104 : cinq décisions.
- P-136, P-138, P-139, P-148 : au portail.
- B-1416 : en-têtes de l'export tableur sans accents (liés à l'aller-retour de
  l'import).
- B-1427 : barres de défilement presque invisibles (1,1:1) ; les rendre
  lisibles change l'aspect de toute l'application.
- B-1436 (recette, lot 1) : sans boîte branchée, ouvrir l'écran Email lance
  l'assistant de connexion par-dessus, son voile cache « Retour » et il faut
  deux Échap pour revenir. L'ouverture d'office est un choix ancien (BUG-037).
  **Recommandation** : ne plus l'ouvrir d'office ; l'écran montre
  « Configurer un compte », et « Brancher mes mails » de l'Accueil ouvre
  l'assistant directement. La rédaction dirait aussi, avant la confirmation,
  qu'aucune boîte n'est branchée (B-1435).
- P-149 à P-151 (recette, lot 1) : relance de fiche dans « Relances et
  alertes » avec « faite », projet d'une tâche depuis son formulaire (le filtre
  projet existe mais rien ne pose le projet), personne liée visible sur la
  tâche. **Recommandation** : oui aux trois.
- Recette, lot 3 : les documents produits par THÉRÈSE (présentation,
  tableur) se terminent par « Généré par THERESE - Synoptia ». Le slogan
  « Synoptia - L'entrepreneur augmenté » a été retiré de la page de titre
  (B-1453). **Recommandation** : retirer aussi ce pied, ou le rendre
  facultatif dans le profil d'export : le document est celui de
  l'utilisatrice.
- P-152 à P-155 (recette, lots 2 et 3) : explication du score au clavier,
  livrable depuis le projet, avoir lié à sa facture d'origine, date réelle
  d'un paiement. **Recommandation** : oui aux quatre.
- Recette, lot 4 : les variables (`{nom}`) ne montrent jamais le texte
  substitué avant l'envoi ; l'écran l'annonce (« le moteur les remplace à
  l'envoi »), la grille demandait une substitution visible. **Recommandation** :
  un aperçu du message final sous le composeur, par la route
  `/api/variables/preview` qui existe déjà.
- Recette, lot 4 : Décision s'ouvre en mode Cloud même quand le service
  configuré est Ollama et qu'aucun accord cloud n'est donné.
  **Recommandation** : Souverain par défaut quand Ollama est le service
  choisi (même esprit que P-111).


---

## Décisions du 25/09/2026 (tranchées sur délégation de Ludo)

Ludo : « Décide les 36 questions sauf lesquelles non négociable ». Chaque
recommandation ci-dessus est retenue telle quelle, avec les précisions
suivantes :

- **P-105** : 1 chantier « mise au repos des écritures de fond » validé ;
  livrer d'abord le rapprochement au geste. 2 l'interrupteur ne coupe que la
  relève de fond. 3 fils IMAP reconstitués avant livraison. 4 90 jours. 5
  fuseau du système, fériés français exclus. 6 une ligne dans « Cette
  semaine ».
- **P-106** : 7 lecture des fichiers de Dr_logic d'abord, export après la
  saisie du planning. 8 accord « documents » exigé dès qu'un outil de lecture
  de fichier est offert à un modèle en ligne. 9 copie dans un dossier de
  THÉRÈSE.
- **P-107** : 10 outil, date, oui ou non, empreinte salée, jamais le
  contenu ; 12 mois ; effacé par « Effacer toutes mes données ». 11 d'après
  la configuration réelle. 12 le pont des agents au périmètre, avec
  interrupteur. 13 retrait partout, dit à l'écran.
- **P-108** : 14 même version exigée, refus sinon. 15 connecteurs importés
  désactivés. 16 trois états d'avant relais. 17 l'alerte « dossier
  synchronisé » part en premier.
- **P-109** : 18 conversation neuve. 19 accord au démarrage de la session.
  21 Échap et le grand bouton seulement.
- **P-110** : 22 voie sans git. 23 masquage des fichiers de mots de passe,
  sinon Atelier local. 24 contrôle automatique bloquant plus relecture. 25
  signalement des données personnelles dès le premier lot.
- **P-121** : 26 arrondi commercial au demi-centime supérieur, en centimes
  entiers, serveur et écran (B-1428). 27 règles plus strictes à la création
  ou au changement du champ. 28 taux 0 selon le régime du profil. 29 devis
  envoyé ou accepté non retouchable.
- **P-125** : 30 deux réponses de fond, file au-delà. 31 purge et
  restauration arrêtent d'office les réponses (B-1425). 32 pièces jointes
  gardées sur la conversation d'origine.
- **P-104** : nom « fil de travail » ; un niveau de variantes ; minuteur
  manuel en phase 1 ; plusieurs projets par fil, une conversation dans un
  seul fil ; la carte « Reprendre » n'apparaît à l'Accueil que s'il y a un
  fil en cours, sans bloc permanent (« trop d'interfaces », 27/08).
- **P-132 moitié 2** : un seul vocabulaire d'avancement (celui du pipeline),
  étape terminale « Perdu », exclue des prospects en cours.
- **P-136** : avertissement non bloquant ; la règle légale est relevée à la
  source au moment du code. **P-138** : oui, avec la date réelle (P-155).
  **P-139** : oui (`sent_at`), il remplace « Envoi non tracé » (B-1449).
- **P-148 à P-155** : acceptées.
- **B-1416** : en-têtes d'export accentués et libellés d'étape ; l'import
  accepte les deux formes (B-1418 replie déjà les accents).
- **B-1427** : pouce de défilement relevé à 3:1 sur les deux thèmes.
- **B-1436 et B-1435** : l'assistant e-mail ne s'ouvre plus d'office ;
  « Brancher mes mails » l'ouvre ; la rédaction dit avant la confirmation
  qu'aucune boîte n'est branchée.
- **Variables** : aperçu du message final sous le composeur.
- **Décision** : Souverain par défaut quand Ollama est le service choisi.

### Réservées à Ludo (non négociables pour moi)

1. **Q20, les dictées déjà conservées chez les testeurs** : les effacer
   d'office à la mise à jour, c'est supprimer définitivement des fichiers sur
   leurs machines, et l'annoncer dans les notes de version et sur Discord.
   Recommandation : oui, mais c'est ton geste. Le correctif B-1424 empêche
   déjà toute nouvelle accumulation.
2. **Le pied « Généré par THERESE - Synoptia »** sur les documents des
   utilisatrices : c'est ta marque et ta communication. Recommandation : le
   retirer, ou le rendre facultatif.
