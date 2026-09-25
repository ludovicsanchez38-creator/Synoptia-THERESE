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

