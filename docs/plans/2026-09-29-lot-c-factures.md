# Lot C, 29 septembre 2026 : numérotation et sort d'une facture émise

Vérification lue le 29 septembre 2026 sur les pages officielles citées. Seul le texte affiché est repris. Rien n'est complété de mémoire.

## Ce que disent les textes

### Numéro de facture

Article 242 nonies A, I, 7° de l'annexe II au CGI, version en vigueur depuis le 1er janvier 2025 (décret n° 2024-1195 du 21 décembre 2024).

https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000050811276

> 7° Un numéro unique basé sur une séquence chronologique et continue ; la numérotation peut être établie dans ces conditions par séries distinctes lorsque les conditions d'exercice de l'activité de l'assujetti le justifient ; l'assujetti doit faire des séries distinctes un usage conforme à leur justification initiale ;

L'article liste les mentions des factures. Il ne parle pas des devis.

BOI-TVA-DECLA-30-20-20-10, identifiant `BOI-TVA-DECLA-30-20-20-10-20131018`, publication du 18 octobre 2013, section II-A. Page lue :

https://bofip.impots.gouv.fr/bofip/140-PGP.html/identifiant=BOI-TVA-DECLA-30-20-20-10-20131018

- § 70 : « Le 7° du I de l'article 242 nonies A de l'annexe II au CGI prévoit que la facture doit comporter un numéro unique basé sur une séquence chronologique et continue. »
- § 90 : pour chaque série, la numérotation propre est admise à trois conditions : « que la numérotation soit effectuée chronologiquement au fur et à mesure de l'émission des factures » ; « qu'elle soit continue » ; « que le dispositif retenu au sein de l'entreprise garantisse que deux factures émises la même année ne puissent pas porter le même numéro ».

Le mot « rupture » n'est pas dans cet article, ni dans le 7°. Il figure dans un autre commentaire, sur un autre objet : le champ `EcritureNum` du fichier des écritures comptables, BOI-CF-IOR-60-40-20-20170607 (page PDF lue, publication du 7 juin 2017) :

https://bofip.impots.gouv.fr/bofip/9028-PGP.html/identifiant=BOI-CF-IOR-60-40-20-20170607

> La numérotation dans le champ « ecriturenum » doit être croissante dans le temps et ne pas comporter de rupture.

Ce paragraphe ne règle pas le numéro de facture. Le lot s'appuie sur « continue » et sur « au fur et à mesure de l'émission », pas sur ce mot.

### Facture déjà émise que l'on veut annuler

Article 289 du CGI, version en vigueur depuis le 31 décembre 2023.

https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000048827413

- I, 4 : « L'assujetti doit conserver un double de toutes les factures émises. »
- I, 5 : « Tout document ou message qui modifie la facture initiale, émise en application de cet article, et qui fait référence à la facture initiale de façon spécifique et non équivoque est assimilé à une facture. Il doit comporter l'ensemble des mentions prévues au II. »
- V : « L'authenticité de l'origine, l'intégrité du contenu et la lisibilité de la facture doivent être assurées à compter de son émission et jusqu'à la fin de sa période de conservation. »

BOI-TVA-DECLA-30-20-20-20, identifiant `BOI-TVA-DECLA-30-20-20-20-20220119`, publication du 19 janvier 2022, section V. Page lue :

https://bofip.impots.gouv.fr/bofip/142-PGP.html/identifiant=BOI-TVA-DECLA-30-20-20-20-20220119

- § 190 : l'article 272 du CGI subordonne l'imputation ou la restitution de la TVA, lorsque les ventes ou services sont ensuite résiliés ou annulés, « à la justification, auprès de l'administration, de la rectification de la facture initiale ».
- § 210 : « Dans le cas de ventes résiliées ou annulées, en totalité ou en partie, ou de rabais, remises ou ristournes consentis par la personne qui réalise les opérations taxables, la rectification des factures s'entend généralement soit de l'envoi d'une facture nouvelle annulant et remplaçant la précédente, soit, selon des usages commerciaux établis de longue date, de l'envoi d'une note d'avoir. »
- § 220 : la facture rectificative ou la note d'avoir fait référence explicite à la facture initiale (numéro et date).
- § 240 : la facture nouvelle qui annule et remplace « doit porter la référence exacte à la facture initiale et la mention expresse de l'annulation de celle-ci ».
- § 260 : la note d'avoir porte référence à la facture initiale et indique le montant hors taxes du rabais ainsi que la TVA correspondante, lorsque l'émetteur veut imputer ou se faire restituer la TVA.

## Ce que ces pages ne disent pas

Elles ne disent pas que la seule voie est la facture d'avoir. Le § 210 ouvre deux documents : la facture nouvelle qui annule et remplace, et la note d'avoir. Le § 240 appelle « mention expresse de l'annulation » ce qui figure sur la facture de remplacement. L'annulation n'est donc pas interdite. Elle passe par un nouveau document, qui cite la facture initiale. La facture initiale reste : le I, 4 de l'article 289 en exige un double, le V en exige l'intégrité à compter de l'émission, et le document rectificatif la cite par son numéro.

Elles ne disent pas qu'un statut logiciel « Annulée », à lui seul, rectifie la facture. Aucune de ces pages ne décrit un changement de statut. Un passage à « Annulée » qui sort la pièce de l'encours sans facture de remplacement et sans note d'avoir ne réalise pas la rectification des § 190 et 210.

Elles ne disent pas « sans rupture » pour le numéro de facture. Elles disent « continue », au fur et à mesure de l'émission.

## Design retenu

### Séries FACT- et AV-

L'article 242 nonies A, I, 7° admet des séries distinctes « lorsque les conditions d'exercice de l'activité de l'assujetti le justifient », et il demande un usage conforme à cette justification initiale. Le § 90 rappelle, pour chaque série, la chronologie au fil des émissions, la continuité, et l'absence de doublon la même année. Aucune des pages lues ne dit qu'une note d'avoir et une facture forment, à elles seules, deux conditions d'exercice. L'article 289, I, 5 assimile le document qui modifie la facture initiale à une facture.

THÉRÈSE a une activité et un établissement. Sur les pages lues, le 7° n'établit pas la justification de deux séries `FACT-` et `AV-`. Les deux séries sont conservées. Les changer demanderait une décision humaine. Ce point s'arrête là.

### B-1615, numéro et date à l'émission

Le § 90 place la numérotation au moment de l'émission, et la veut continue. La date imprimée suit ce moment : à l'émission, elle devient la date du jour. Un brouillon n'est pas une facture émise. Lui donner un numéro `FACT-` ou `AV-`, puis le supprimer, retire un numéro de la série.

- Une facture ou un avoir créé en brouillon reçoit un jeton unique hors série, préfixe `PROV-`. Ce jeton n'entre pas dans le calcul du prochain `FACT-` ou `AV-`.
- Le numéro définitif est posé à toute première transition d'une pièce provisoire vers un statut émis (`sent`, `paid`, `overdue`), y compris après l'annulation du brouillon, par `PUT` ou par « marquer payée ». Un brouillon annulé reste un brouillon annulé, sans numéro définitif.
- À cette émission, la date d'émission devient la date du jour, sur la même horloge que l'année du numéro. L'échéance est décalée du même nombre de jours. Une pièce déjà émise ne voit pas sa date reculée quand elle passe de envoyée à payée.
- L'écran, le PDF, la carte de facturation, les livrables, le brief du jour et la confirmation de paiement affichent « Brouillon, numéro à l'émission » ou le numéro définitif renvoyé. Ils n'impriment pas le jeton `PROV-`.
- Le devis garde `DEV-` dès la création. L'article 242 nonies A et la section II-A du BOI-TVA-DECLA-30-20-20-10 visent la facture.

Migration, sans réécriture des lignes déjà en base. Un brouillon qui porte déjà un numéro de série (`FACT-…` ou `AV-…`) le garde à l'émission s'il est encore le dernier de sa série, préfixe et année. S'il ne l'est plus, l'émission lui donne le numéro suivant. L'ancien numéro n'est pas attribué à une autre pièce. Supprimer un tel brouillon est refusé : le supprimer ferait retomber le maximum, et la pièce suivante reprendrait ce numéro. On ne renumérote pas les autres pièces pour boucher un trou. Les brouillons `PROV-` n'occupent pas la série : les supprimer ne décale pas le prochain numéro.

### B-1671, pas de statut « Annulée » sur une pièce émise

Le correctif demandé (refuser `cancelled`, message qui dit d'émettre un avoir, retirer « Annulée » du sélecteur d'une facture émise) est retenu comme choix de produit, plus étroit que le § 210.

Le § 210 admet aussi une facture nouvelle qui annule et remplace. Cette seconde voie n'est pas construite dans ce lot. Le message à l'écran indique l'avoir, parce que c'est le document rectificatif que l'application sait déjà émettre, et parce que le lot le demande. Le message dit aussi, pour un avoir, qu'une facture rectificative reste une voie.

- `PUT` avec `cancelled` sur une facture déjà émise répond 409 : « Une facture émise ne s'annule pas. Pour l'annuler, émets un avoir. » La pièce reste à son statut.
- Le même garde vaut pour un avoir déjà émis. Le I, 5 de l'article 289 l'assimile à une facture. Le `PUT` répond 409 : « Un avoir émis ne s'annule pas. Pour l'annuler, émets un avoir inverse ou une facture rectificative. » Un brouillon d'avoir reste annulable.
- Un devis reste annulable : les textes cités ne le visent pas. Un brouillon de facture, qui n'est pas émis, peut encore passer à « Annulée » sans prendre de numéro.
- Le sélecteur d'une facture ou d'un avoir déjà émis ne propose plus « Annulée ». Une pièce dont le statut enregistré est déjà annulé affiche cette valeur. Dès qu'on en choisit une autre, « Annulée » sort de la liste.
- Un avoir ne cite comme origine qu'une facture déjà émise, à la création, à la conversion et à l'émission. Le § 220 demande la référence de la facture initiale, son numéro et sa date. Un brouillon `PROV-` ne peut pas servir d'origine, et le PDF ne l'imprime pas.

## Incertain

La page BOFiP de la numérotation porte la date de publication du 18 octobre 2013. Aucune date de fin n'apparaissait sur la page lue. Une version plus récente, si elle existe sous un autre identifiant, n'a pas été trouvée. Le § 140 est cité par la revue pour la date de délivrance ; son libellé verbatim n'est pas recopié dans la section des textes lus ci-dessus.

La facture de remplacement du § 240 n'a pas d'écran dans ce lot. Quelqu'un qui voudrait annuler et remplacer en un seul document ne le peut pas ici ; il émet un avoir, ou il lit le message qui nomme la facture rectificative sans pouvoir la composer dans le formulaire.

Un brouillon historique encore dernier de sa série garde son numéro à l'émission, y compris si l'année écrite dans ce numéro et la date du jour ne coïncident pas. La date d'émission, elle, est recalée sur le jour de l'émission.

La justification des séries `FACT-` et `AV-` reste ouverte : le 7° ne la fournit pas sur les pages lues, et la série n'a pas été changée.
