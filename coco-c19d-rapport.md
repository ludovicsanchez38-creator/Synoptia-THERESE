# COCO — C19-D, interface, UX et accessibilité

Branche `boucle/c12-visuel`, base `f01582fa` (0.79.0). Rapport préparé dans le seul dossier autorisé à l’écriture. Le chemin demandé sous `/home/synoptia/staging/therese-c19-campagne-2026-10-23/` est extérieur : aucune copie n’y a été écrite.

Les 47 fiches complètes et les 46 entrées de reproduction correspondantes ont été lues, ainsi que toutes les captures citées pour ce lot. B-1112 n’a pas d’entrée autonome dans `rapport.json` : sa reproduction est la note de B-1075. Le relevé de départ est conservé dans [.c19d/fiches.json.txt](.c19d/fiches.json.txt).

Les corrections sont couvertes par un test rouge conservé avant modification, puis un test vert. Les logs intermédiaires ratés restent archivés ; les liens de chaque défaut pointent vers les preuves retenues. Certaines exécutions groupées contiennent aussi des tests historiques en échec : les tests du défaut, identifiés par son numéro, sont ceux à comparer. Les logs ciblés et les contrôles finaux permettent de distinguer ces cas.

Aucune dépendance installée, aucun fournisseur d’IA appelé, aucune pile ou port de recette démarré. Les tests remplacent les API et les modèles. Les jeux pytest et les fichiers temporaires sont dirigés vers `.c19d/tmp/`. Le petit plugin pytest local laisse imprimer le résumé avant la sortie forcée qu’effectuait trop tôt le `conftest.py` existant ; le fichier partagé n’est pas modifié.

## Limites et décisions laissées ouvertes

- **B-1068** : les commandes ne sont plus imbriquées. La poignée, l’ouverture et la suppression restent trois commandes accessibles. Imposer un seul arrêt de tabulation demanderait une convention de navigation entre elles ; aucune navigation nouvelle n’a été choisie sans décision produit.
- **B-1077** : le PDF traduit `overdue` en « En retard ». La validité métier d’un avoir en retard reste ouverte ; la route et les statuts permis ne sont pas changés.
- **Mesures visuelles** : jsdom ne mesure ni les largeurs ni les pixels. Les contraintes de classes/structure sont testées pour B-1052, B-1053, B-1072, B-1079, B-1084 et B-1093 ; les mesures Chrome indiquées ci-dessous restent à faire. Les noms natifs de Fichiers exigent aussi une vérification Tauri.
- **B-1102** : la fonction réelle du relevé est exécutée sous Vitest avec des contrôles DOM et des snapshots accessibles doubles. Le test Chromium supplémentaire n’a pas pu démarrer car `@playwright/test` n’est pas installé dans les dépendances accessibles ici ; rien n’a été installé. La confirmation du nom calculé dans Chrome reste demandée.
- Constats annexes des notes, hors des 47 références : la hauteur de « Tout ignorer » (B-1061), les espaces des milliers des montants du prototype (B-1082) et le sort métier des avoirs en retard sont signalés, sans correction supplémentaire inventée.
- B-1056 : la reproduction réfutait l’absence d’Échap ; le défaut corrigé concerne le focus et le nom de la croix. B-1093 : le focus global et les paragraphes étaient déjà lisibles ; seuls les écarts mesurés du bouton sont corrigés. B-1102 : le SVG titré était déjà nommé ; la correction couvre notamment l’image avec `alt`.

Le regroupement final des compléments dans leurs commits de défaut a conservé exactement le même arbre Git, après les contrôles : [preuve](.c19d/preuves/regroupement-commits.log).

## Défauts

### B-1088

- Cause : Recherche de secrets par sous-chaîne, mots métier ambigus et compactage de toute la phrase en IBAN.
- Reproduction : confirme. Attendu : Un message professionnel ordinaire devient une fiche ; un refus dit ce qui l'a provoqué.
- Correctif : Bornes des identifiants et variantes camelCase/majuscules, contexte des mots ambigus, formats bancaires par pays avec ponctuation et motif sans valeur sensible ; token_limits et corpus historique conservés.
- Rouge : [sortie B-1088-rouge](.c19d/preuves/B-1088-rouge.log). Vert : [sortie B-1088-securite-finale-vert](.c19d/preuves/B-1088-securite-finale-vert.log).
- Commit : `c3a8ccdc` (B-1088).
- À mesurer/rejouer dans Chrome : Pas de mesure de mise en page ; vérifier le motif de refus dans la fiche.

### B-1075

- Cause : Le capteur clavier saisissait le conteneur ; le raccourci global ignorait defaultPrevented.
- Reproduction : confirme. Attendu : En vue Colonnes, une tâche s'ouvre au clavier comme à la souris.
- Correctif : Bouton de titre natif et poignée nommée ; respect des touches consommées par le glisser.
- Rouge : [sortie B-1075-B-1112-rouge](.c19d/preuves/B-1075-B-1112-rouge.log). Vert : [sortie rejeux-interface](.c19d/preuves/rejeux-interface.log).
- Commit : `eaec3f7e` (B-1075 B-1112).
- À mesurer/rejouer dans Chrome : Vérifier les déplacements entre colonnes et le focus après annulation.

### B-1112

- Cause : Le capteur clavier saisissait le conteneur ; le raccourci global ignorait defaultPrevented.
- Reproduction : note de B-1075 et observation de la fiche B-1112.
- Correctif : Bouton de titre natif et poignée nommée ; respect des touches consommées par le glisser.
- Rouge : [sortie B-1075-B-1112-rouge](.c19d/preuves/B-1075-B-1112-rouge.log). Vert : [sortie rejeux-interface](.c19d/preuves/rejeux-interface.log).
- Commit : `eaec3f7e` (B-1075 B-1112).
- À mesurer/rejouer dans Chrome : Vérifier les déplacements entre colonnes et le focus après annulation.

### B-1064

- Cause : La branche sans document affichait toujours un chargement.
- Reproduction : confirme. Attendu : Un échec de chargement affiche un message et un geste de reprise.
- Correctif : Message annoncé et bouton Réessayer qui rappelle openDocument.
- Rouge : [sortie priorites-interface-rouge](.c19d/preuves/priorites-interface-rouge.log). Vert : [sortie rejeux-interface](.c19d/preuves/rejeux-interface.log).
- Commit : `61e7c298` (B-1064).
- À mesurer/rejouer dans Chrome : Contrôler le rendu du message après une erreur 500.

### B-1079

- Cause : Une rangée flex sans retour comprimait les actions avec la confirmation abandon.
- Reproduction : confirme. Attendu : Le pied de la modale garde des boutons lisibles quand l'invite « Abandonner les modifications ? » apparaît.
- Correctif : Pied avec retour et espacement ; confirmation sur ligne entière et groupes non comprimés.
- Rouge : [sortie priorites-interface-rouge](.c19d/preuves/priorites-interface-rouge.log). Vert : [sortie client-et-pied-factures-vert](.c19d/preuves/client-et-pied-factures-vert.log).
- Commit : `3d7f1b5f` (B-1079).
- À mesurer/rejouer dans Chrome : Mesurer à 1280 et 1024 px, avec facture émise modifiée : aucun libellé de bouton coupé.

### B-1073

- Cause : La mention promettait une confirmation universelle absente de plusieurs surfaces.
- Reproduction : confirme. Attendu : La mention permanente du composeur ne promet pas plus que ce que l'application reconnaît ailleurs.
- Correctif : Phrase descriptive limitée aux cartes de la conversation, sans changement du comportement.
- Rouge : [sortie B-1073-rouge](.c19d/preuves/B-1073-rouge.log). Vert : [sortie B-1073-vert](.c19d/preuves/B-1073-vert.log).
- Commit : `ba5cd342` (B-1073).
- À mesurer/rejouer dans Chrome : Lisibilité de la mention sous le composeur.

### B-1049

- Cause : Icône nommée seulement par title ; raison cachée dans le title d’un bouton désactivé.
- Reproduction : confirme. Attendu : Bouton icône seule avec aria-label (règle du projet) et type="button".
- Correctif : Type et aria-label explicites ; raison visible reliée par aria-describedby.
- Rouge : [sortie interface-lot2-rouge-valide](.c19d/preuves/interface-lot2-rouge-valide.log). Vert : [sortie contrats-et-clavier-vert](.c19d/preuves/contrats-et-clavier-vert.log).
- Commit : `3a17508b` (B-1049 B-1050).
- À mesurer/rejouer dans Chrome : Lire le motif au clavier ; contrôler la disposition avec un long motif.

### B-1050

- Cause : Icône nommée seulement par title ; raison cachée dans le title d’un bouton désactivé.
- Reproduction : confirme. Attendu : Le motif d'indisponibilité du mode Souverain est lisible et annoncé (texte visible ou aria-describedby), y compris au clavier.
- Correctif : Type et aria-label explicites ; raison visible reliée par aria-describedby.
- Rouge : [sortie interface-lot2-rouge-valide](.c19d/preuves/interface-lot2-rouge-valide.log). Vert : [sortie contrats-et-clavier-vert](.c19d/preuves/contrats-et-clavier-vert.log).
- Commit : `3a17508b` (B-1049 B-1050).
- À mesurer/rejouer dans Chrome : Lire le motif au clavier ; contrôler la disposition avec un long motif.

### B-1051

- Cause : Libellés dissociés des textarea et six couleurs fixes dans chaque logo.
- Reproduction : confirme. Attendu : Libellés associés aux zones de texte (htmlFor/id) et nom accessible contenant le texte visible (WCAG 2.5.3).
- Correctif : Paires htmlFor/id ; noms issus des libellés ; couleurs de texte et agents du thème.
- Rouge : [sortie interface-lot2-rouge-valide](.c19d/preuves/interface-lot2-rouge-valide.log). Vert : [sortie validation-board-libelles](.c19d/preuves/validation-board-libelles.log).
- Commit : `06c5062d` (B-1051 B-1052).
- À mesurer/rejouer dans Chrome : Mesurer le contraste des deux logos en clair et sombre. Le test de choix Souverain préexistant échouait déjà dans la sortie rouge.

### B-1052

- Cause : Libellés dissociés des textarea et six couleurs fixes dans chaque logo.
- Reproduction : confirme. Attendu : Le logo du Board reste lisible dans les deux thèmes (couleurs issues des jetons).
- Correctif : Paires htmlFor/id ; noms issus des libellés ; couleurs de texte et agents du thème.
- Rouge : [sortie interface-lot2-rouge-valide](.c19d/preuves/interface-lot2-rouge-valide.log). Vert : [sortie validation-board-libelles](.c19d/preuves/validation-board-libelles.log).
- Commit : `06c5062d` (B-1051 B-1052).
- À mesurer/rejouer dans Chrome : Mesurer le contraste des deux logos en clair et sombre. Le test de choix Souverain préexistant échouait déjà dans la sortie rouge.

### B-1053

- Cause : Pistes blanches sur fond clair ; progression et erreur sans sémantique annoncée.
- Reproduction : confirme. Attendu : Anneau et piste de progression visibles sur le fond du thème par défaut (clair), couleurs de la charte uniquement.
- Correctif : Jetons pour anneau et piste, titre de couleur unie, progressbar et live region, erreur alert.
- Rouge : [sortie interface-lot2-rouge-valide](.c19d/preuves/interface-lot2-rouge-valide.log). Vert : [sortie splash-vert](.c19d/preuves/splash-vert.log).
- Commit : `b7055286` (B-1053 B-1055).
- À mesurer/rejouer dans Chrome : Visibilité des pistes en clair et sombre ; annonce du démarrage avec lecteur d’écran.

### B-1055

- Cause : Pistes blanches sur fond clair ; progression et erreur sans sémantique annoncée.
- Reproduction : confirme. Attendu : Erreur fatale dans une région live (role=alert), barre de progression exposée (role=progressbar, aria-valuenow), message d'étape annoncé.
- Correctif : Jetons pour anneau et piste, titre de couleur unie, progressbar et live region, erreur alert.
- Rouge : [sortie interface-lot2-rouge-valide](.c19d/preuves/interface-lot2-rouge-valide.log). Vert : [sortie splash-vert](.c19d/preuves/splash-vert.log).
- Commit : `b7055286` (B-1053 B-1055).
- À mesurer/rejouer dans Chrome : Visibilité des pistes en clair et sombre ; annonce du démarrage avec lecteur d’écran.

### B-1056

- Cause : Modale aria-modal sans piège de focus ; croix sans nom.
- Reproduction : confirme. Attendu : Bouton de fermeture nommé ; dialogue aria-modal qui reçoit le focus et le piège.
- Correctif : Hook useDialogFocusTrap existant et nom explicite pour la croix.
- Rouge : [sortie interface-lot2-rouge-valide](.c19d/preuves/interface-lot2-rouge-valide.log). Vert : [sortie rejeux-commandes-et-instrument](.c19d/preuves/rejeux-commandes-et-instrument.log).
- Commit : `386d4128` (B-1056).
- À mesurer/rejouer dans Chrome : Parcours Tab et retour au déclencheur dans la coque.

### B-1057

- Cause : Classe magenta inexistante et texte de décompte sans accents.
- Reproduction : confirme. Attendu : La pastille du projet détecté a un fond teinté, comme celle du contact (bg-agent-cyan/20).
- Correctif : Jeton accent-magenta et décompte français accentué.
- Rouge : [sortie interface-lot2-rouge-valide](.c19d/preuves/interface-lot2-rouge-valide.log). Vert : [sortie contrats-et-clavier-vert](.c19d/preuves/contrats-et-clavier-vert.log).
- Commit : `796b4ac3` (B-1057 B-1058).
- À mesurer/rejouer dans Chrome : Contrôler le fond teinté de la pastille dans les deux thèmes.

### B-1058

- Cause : Classe magenta inexistante et texte de décompte sans accents.
- Reproduction : confirme. Attendu : « J'ai détecté une entité » / « J'ai détecté N entités ».
- Correctif : Jeton accent-magenta et décompte français accentué.
- Rouge : [sortie interface-lot2-rouge-valide](.c19d/preuves/interface-lot2-rouge-valide.log). Vert : [sortie contrats-et-clavier-vert](.c19d/preuves/contrats-et-clavier-vert.log).
- Commit : `796b4ac3` (B-1057 B-1058).
- À mesurer/rejouer dans Chrome : Contrôler le fond teinté de la pastille dans les deux thèmes.

### B-1061

- Cause : Actions identiques et confiance sans association.
- Reproduction : confirme. Attendu : Boutons icône seule avec aria-label propre à l'entité et type="button" ; pourcentage relié à l'entité.
- Correctif : Noms propres à chaque entité, type button et description de confiance liée.
- Rouge : [sortie interface-lot2-rouge-valide](.c19d/preuves/interface-lot2-rouge-valide.log). Vert : [sortie contrats-et-clavier-vert](.c19d/preuves/contrats-et-clavier-vert.log).
- Commit : `a288b6e5` (B-1061).
- À mesurer/rejouer dans Chrome : Parcours avec un lecteur d’écran lorsque plusieurs entités sont proposées.

### B-1062

- Cause : Croix sans noms et segments uniquement visuels.
- Reproduction : confirme. Attendu : Chaque bouton de fermeture icône seule porte un aria-label.
- Correctif : Noms distincts sur trois fermetures ; aria-pressed sur filtre et type d’activité.
- Rouge : [sortie interface-lot2-rouge-valide](.c19d/preuves/interface-lot2-rouge-valide.log). Vert : [sortie contrats-et-clavier-vert](.c19d/preuves/contrats-et-clavier-vert.log).
- Commit : `1e4cb084` (B-1062 B-1063).
- À mesurer/rejouer dans Chrome : Vérifier aussi le formulaire Nouvelle activité et le panneau non standalone, non atteints pendant la reproduction.

### B-1063

- Cause : Croix sans noms et segments uniquement visuels.
- Reproduction : confirme. Attendu : Les segments exposent l'état choisi (aria-pressed, comme le primitif Segments).
- Correctif : Noms distincts sur trois fermetures ; aria-pressed sur filtre et type d’activité.
- Rouge : [sortie interface-lot2-rouge-valide](.c19d/preuves/interface-lot2-rouge-valide.log). Vert : [sortie contrats-et-clavier-vert](.c19d/preuves/contrats-et-clavier-vert.log).
- Commit : `1e4cb084` (B-1062 B-1063).
- À mesurer/rejouer dans Chrome : Vérifier aussi le formulaire Nouvelle activité et le panneau non standalone, non atteints pendant la reproduction.

### B-1084

- Cause : Le bloc pre était sans contrainte et son code gardait le style en ligne.
- Reproduction : confirme. Attendu : Un bloc de code s'affiche en bloc, avec défilement ou retour à la ligne maîtrisés.
- Correctif : pre limité en largeur et défilant ; code de bloc distinct de la puce en ligne.
- Rouge : [sortie interface-lot2-rouge-valide](.c19d/preuves/interface-lot2-rouge-valide.log). Vert : [sortie contrats-et-clavier-vert](.c19d/preuves/contrats-et-clavier-vert.log).
- Commit : `355ac937` (B-1084).
- À mesurer/rejouer dans Chrome : À 420 px, vérifier la ligne longue et l’absence de débordement de la page.

### B-1045

- Cause : Les cinq gabarits HTML ne déclaraient pas leur langue.
- Reproduction : confirme. Attendu : Les pages HTML de retour OAuth, rédigées en français, déclarent <html lang="fr">.
- Correctif : lang=fr et titres THÉRÈSE accentués.
- Rouge : [sortie moteur-lot2-rouge-valide](.c19d/preuves/moteur-lot2-rouge-valide.log). Vert : [sortie moteur-lot2-vert](.c19d/preuves/moteur-lot2-vert.log).
- Commit : `7be64dfa` (B-1045).
- À mesurer/rejouer dans Chrome : Retour OAuth manquant et refusé sans connexion réelle.

### B-1047

- Cause : Les chaînes étaient enregistrées sans accents.
- Reproduction : confirme. Attendu : Titres et messages de notification accentués : « Facture impayée », « Relance échue », « prévue », « Tâche en retard », « RDV demain à ».
- Correctif : Titres et messages français accentués.
- Rouge : [sortie moteur-lot2-rouge-valide](.c19d/preuves/moteur-lot2-rouge-valide.log). Vert : [sortie moteur-lot2-vert](.c19d/preuves/moteur-lot2-vert.log).
- Commit : `cf6b7950` (B-1047).
- À mesurer/rejouer dans Chrome : Lire les quatre familles de notifications dans le centre.

### B-1048

- Cause : La signature du PPTX ne reprenait pas les accents demandés.
- Reproduction : confirme. Attendu : La diapositive de fin du repli écrit « Généré par THÉRÈSE - Synoptïa », comme la consigne du même fichier.
- Correctif : Signature THÉRÈSE et Synoptïa.
- Rouge : [sortie B-1048-B-1092-rouge](.c19d/preuves/B-1048-B-1092-rouge.log). Vert : [sortie moteur-lot2-vert](.c19d/preuves/moteur-lot2-vert.log).
- Commit : `9a700b44` (B-1048).
- À mesurer/rejouer dans Chrome : Ouvrir la dernière diapositive du PPTX de repli.

### B-1077

- Cause : Entrée overdue manquante dans la table des avoirs.
- Reproduction : confirme. Attendu : Un avoir en retard sort sur le PDF avec un libellé français.
- Correctif : Libellé En retard ; aucune modification des statuts autorisés.
- Rouge : [sortie moteur-lot2-rouge-valide](.c19d/preuves/moteur-lot2-rouge-valide.log). Vert : [sortie moteur-lot2-vert](.c19d/preuves/moteur-lot2-vert.log).
- Commit : `f243790f` (B-1077).
- À mesurer/rejouer dans Chrome : Vérifier le PDF. La validité métier du retard d’un avoir reste à décider.

### B-1092

- Cause : Le moteur envoyait une chaîne sans accents.
- Reproduction : confirme. Attendu : Message accentué : « Aucune donnée trouvée ».
- Correctif : Aucune donnée trouvée dans l’aperçu.
- Rouge : [sortie B-1048-B-1092-rouge](.c19d/preuves/B-1048-B-1092-rouge.log). Vert : [sortie moteur-lot2-vert](.c19d/preuves/moteur-lot2-vert.log).
- Commit : `48eb20eb` (B-1092).
- À mesurer/rejouer dans Chrome : Aperçu d’un CSV vide.

### B-1099

- Cause : Le message /projet rendait le code interne active.
- Reproduction : confirme. Attendu : La réponse de /projet nomme le statut retenu en français.
- Correctif : Le message dit actif ; le stockage reste active.
- Rouge : [sortie moteur-lot2-rouge-valide](.c19d/preuves/moteur-lot2-rouge-valide.log). Vert : [sortie moteur-lot2-vert](.c19d/preuves/moteur-lot2-vert.log).
- Commit : `5f9b0646` (B-1099).
- À mesurer/rejouer dans Chrome : Message /projet avec statut inconnu, sans fournisseur réel.

### B-1046

- Cause : Un tiret entre chiffres devenait toujours un point ; préfixes et graphies étaient conservés.
- Reproduction : confirme. Attendu : « grok-4.20-0309-reasoning » s'affiche avec sa version et sans la date d'identifiant prise pour une décimale (par exemple « Grok 4.20 Reasoning »).
- Correctif : Retrait des dates et espaces de noms, versions séparées des tailles B et graphies de marque ; snapshot régénéré hors ligne.
- Rouge : [sortie moteur-lot2-rouge-valide](.c19d/preuves/moteur-lot2-rouge-valide.log). Vert : [sortie moteur-final-definitif](.c19d/preuves/moteur-final-definitif.log).
- Commit : `14838543` (B-1046 B-1097).
- À mesurer/rejouer dans Chrome : Vérifier les noms dans les trois sélecteurs ; aucune liste de modèles ni requête fournisseur modifiée.

### B-1097

- Cause : Un tiret entre chiffres devenait toujours un point ; préfixes et graphies étaient conservés.
- Reproduction : confirme. Attendu : Noms de modèles bien formés : « Gemini 3.1 Pro », « Llama 4 Maverick », « DeepSeek V4 Pro », « Ministral 8B », sans date d'identifiant.
- Correctif : Retrait des dates et espaces de noms, versions séparées des tailles B et graphies de marque ; snapshot régénéré hors ligne.
- Rouge : [sortie moteur-lot2-rouge-valide](.c19d/preuves/moteur-lot2-rouge-valide.log). Vert : [sortie moteur-final-definitif](.c19d/preuves/moteur-final-definitif.log).
- Commit : `14838543` (B-1046 B-1097).
- À mesurer/rejouer dans Chrome : Vérifier les noms dans les trois sélecteurs ; aucune liste de modèles ni requête fournisseur modifiée.

### B-1065

- Cause : Le bouton ~ était nommé Dossier racine alors qu’il ouvre le répertoire personnel.
- Reproduction : confirme. Attendu : Le bouton « ~ » porte le même nom que l'autre bouton qui ouvre le répertoire personnel, et un nom qui contient le texte visible.
- Correctif : Nom Répertoire personnel (~), cohérent avec la destination et le texte visible.
- Rouge : [sortie contrats-affines-base-rouge](.c19d/preuves/contrats-affines-base-rouge.log). Vert : [sortie contrats-et-clavier-vert](.c19d/preuves/contrats-et-clavier-vert.log).
- Commit : `946af404` (B-1065).
- À mesurer/rejouer dans Chrome : Vérifier la destination dans Tauri ; navigateur limité aux noms des contrôles désactivés.

### B-1067

- Cause : Le bandeau RGPD disait bientot.
- Reproduction : confirme. Attendu : « expirent bientôt ».
- Correctif : Le bandeau dit bientôt.
- Rouge : [sortie contrats-affines-base-rouge](.c19d/preuves/contrats-affines-base-rouge.log). Vert : [sortie contrats-et-clavier-vert](.c19d/preuves/contrats-et-clavier-vert.log).
- Commit : `b6ec337e` (B-1067).
- À mesurer/rejouer dans Chrome : Lire le bandeau avec un contact puis plusieurs.

### B-1069

- Cause : Le title attribuait à Échap une fermeture alors que la touche revient en arrière.
- Reproduction : confirme. Attendu : L'infobulle du bouton de fermeture décrit ce que fait Échap.
- Correctif : Infobulle Fermer, sans promesse de raccourci.
- Rouge : [sortie interface-lot3-rouge](.c19d/preuves/interface-lot3-rouge.log). Vert : [sortie contrats-et-clavier-vert](.c19d/preuves/contrats-et-clavier-vert.log).
- Commit : `13de6707` (B-1069).
- À mesurer/rejouer dans Chrome : Sous Linux et Windows, Échap à l’étape 2 doit rester un retour à l’étape 1.

### B-1071

- Cause : Le nom accessible ne contenait pas le texte Retour.
- Reproduction : confirme. Attendu : Le nom accessible du bouton contient son libellé visible « Retour » (WCAG 2.5.3).
- Correctif : Nom Retour à l’écran précédent.
- Rouge : [sortie interface-lot3-rouge](.c19d/preuves/interface-lot3-rouge.log). Vert : [sortie contrats-et-clavier-vert](.c19d/preuves/contrats-et-clavier-vert.log).
- Commit : `9f93fa31` (B-1071).
- À mesurer/rejouer dans Chrome : Tester la commande vocale Retour et le retour de focus.

### B-1072

- Cause : left-16 plaçait le tiroir à 64 px contre un rail de 56 px.
- Reproduction : confirme. Attendu : Sous xl, le tiroir commence au bord du rail (56 px).
- Correctif : left-14 sous xl.
- Rouge : [sortie interface-lot3-rouge](.c19d/preuves/interface-lot3-rouge.log). Vert : [sortie contrats-et-clavier-vert](.c19d/preuves/contrats-et-clavier-vert.log).
- Commit : `9ab441c0` (B-1072).
- À mesurer/rejouer dans Chrome : Mesurer l’écart à 1024 et 1279 px, puis à 1280 px.

### B-1074

- Cause : La croix de THERESE.md était sans nom.
- Reproduction : confirme. Attendu : Bouton de fermeture de la modale THERESE.md nommé.
- Correctif : Type button et nom Fermer l’aperçu THERESE.md.
- Rouge : [sortie interface-lot3-rouge](.c19d/preuves/interface-lot3-rouge.log). Vert : [sortie contrats-et-clavier-vert](.c19d/preuves/contrats-et-clavier-vert.log).
- Commit : `e5e29c4c` (B-1074).
- À mesurer/rejouer dans Chrome : Lire les deux commandes de fermeture de l’aperçu.

### B-1080

- Cause : PDF et Supprimer étaient identiques pour toutes les lignes.
- Reproduction : confirme. Attendu : Boutons PDF et Supprimer nommés par la pièce, comme le bouton du client (libelleAccessiblePiece).
- Correctif : Le nom de chaque action reprend le libellé accessible complet de la pièce.
- Rouge : [sortie interface-lot3-rouge](.c19d/preuves/interface-lot3-rouge.log). Vert : [sortie contrats-et-clavier-vert](.c19d/preuves/contrats-et-clavier-vert.log).
- Commit : `e0455d08` (B-1080).
- À mesurer/rejouer dans Chrome : Rotor des boutons avec deux pièces du même client.

### B-1085

- Cause : Erreur et confirmation utilisaient Calendrier, contrairement au champ.
- Reproduction : confirme. Attendu : Le message d'erreur emploie le mot du champ (« Agenda »).
- Correctif : Messages cohérents avec Agenda.
- Rouge : [sortie interface-lot3-rouge](.c19d/preuves/interface-lot3-rouge.log). Vert : [sortie contrats-et-clavier-vert](.c19d/preuves/contrats-et-clavier-vert.log).
- Commit : `c4e2e635` (B-1085).
- À mesurer/rejouer dans Chrome : Absence d’agenda puis carte de confirmation d’un rendez-vous.

### B-1087

- Cause : Le nom accessible et le title disaient tache.
- Reproduction : confirme. Attendu : « Relancer cette tâche ».
- Correctif : Relancer cette tâche dans les deux attributs.
- Rouge : [sortie interface-lot3-rouge](.c19d/preuves/interface-lot3-rouge.log). Vert : [sortie contrats-et-clavier-vert](.c19d/preuves/contrats-et-clavier-vert.log).
- Commit : `b6a2a725` (B-1087).
- À mesurer/rejouer dans Chrome : Lire la commande sans lancer de tâche ni de modèle.

### B-1076

- Cause : Label sans htmlFor et aria-label différent du texte visible.
- Reproduction : confirme. Attendu : Libellé associé au curseur et nom accessible contenant « Durée de rétention ».
- Correctif : Paire label/input ; le nom accessible reprend la durée visible.
- Rouge : [sortie interface-lot3-rouge](.c19d/preuves/interface-lot3-rouge.log). Vert : [sortie B-1076-isole-vert](.c19d/preuves/B-1076-isole-vert.log).
- Commit : `adb44d05` (B-1076).
- À mesurer/rejouer dans Chrome : Nom annoncé pour 12, 36 et 60 mois.

### B-1068

- Cause : Le conteneur sortable à rôle bouton englobait ouvrir et supprimer.
- Reproduction : confirme. Attendu : Aucune commande interactive imbriquée dans un élément de rôle bouton ; un arrêt de tabulation par carte.
- Correctif : Poignée indépendante ; le pointeur saisit toujours le corps ; commandes sœurs au clavier.
- Rouge : [sortie interface-lot3-rouge](.c19d/preuves/interface-lot3-rouge.log). Vert : [sortie rejeux-interface](.c19d/preuves/rejeux-interface.log).
- Commit : `f8d7f21c` (B-1068).
- À mesurer/rejouer dans Chrome : Rejouer le glisser et la suppression. Trois commandes restent tabulables ; imposer un arrêt unique demanderait une convention de navigation à décider.

### B-1081

- Cause : La carte affichait invoice.status brut.
- Reproduction : confirme. Attendu : Le statut actuel s'affiche en français dans la confirmation.
- Correctif : Libellé français partagé et accordé selon le type.
- Rouge : [sortie interface-lot3-rouge](.c19d/preuves/interface-lot3-rouge.log). Vert : [sortie rejeux-interface](.c19d/preuves/rejeux-interface.log).
- Commit : `424d4f7d` (B-1081).
- À mesurer/rejouer dans Chrome : Confirmation Envoyée → Payée et devis Envoyé → Accepté.

### B-1082

- Cause : Taux affichés avec un point et statuts masculins pour les factures.
- Reproduction : confirme. Attendu : Taux de TVA écrits « 5,5 % » comme dans le formulaire classique.
- Correctif : Notation française avec espace avant % dans détail et sélection ; même fonction de statut que la confirmation.
- Rouge : [sortie interface-lot3-rouge](.c19d/preuves/interface-lot3-rouge.log). Vert : [sortie rejeux-interface](.c19d/preuves/rejeux-interface.log).
- Commit : `db1f694d` (B-1082 B-1083).
- À mesurer/rejouer dans Chrome : Relire les taux fractionnaires et les statuts sur carte et détail.

### B-1083

- Cause : Taux affichés avec un point et statuts masculins pour les factures.
- Reproduction : confirme. Attendu : Statut accordé au féminin pour une facture (« Envoyée », « Payée »), comme InvoiceForm.
- Correctif : Notation française avec espace avant % dans détail et sélection ; même fonction de statut que la confirmation.
- Rouge : [sortie interface-lot3-rouge](.c19d/preuves/interface-lot3-rouge.log). Vert : [sortie rejeux-interface](.c19d/preuves/rejeux-interface.log).
- Commit : `db1f694d` (B-1082 B-1083).
- À mesurer/rejouer dans Chrome : Relire les taux fractionnaires et les statuts sur carte et détail.

### B-1086

- Cause : toFixed et suffixe collé formaient une notation anglaise.
- Reproduction : confirme. Attendu : Notation française des jetons (« 15,0 K »).
- Correctif : Décimale française et espace avant K, entrée, sortie et total.
- Rouge : [sortie interface-lot3-rouge](.c19d/preuves/interface-lot3-rouge.log). Vert : [sortie rejeux-interface](.c19d/preuves/rejeux-interface.log).
- Commit : `425b3120` (B-1086).
- À mesurer/rejouer dans Chrome : Vérifier l’espacement avec un total de plusieurs millions de jetons.

### B-1091

- Cause : aria-controls pointait vers une explication démontée.
- Reproduction : confirme. Attendu : aria-controls ne désigne que des identifiants présents, comme pour B-357 et B-768 déjà corrigés.
- Correctif : Référence présente seulement lorsque le contenu est déplié.
- Rouge : [sortie interface-lot3-rouge](.c19d/preuves/interface-lot3-rouge.log). Vert : [sortie rejeux-interface](.c19d/preuves/rejeux-interface.log).
- Commit : `0269ede0` (B-1091).
- À mesurer/rejouer dans Chrome : Inspecter replié puis déplié et relire l’aide.

### B-1093

- Cause : Bouton artisanal sans survol ni style désactivé et avec padding de 12 px.
- Reproduction : confirme. Attendu : Bouton conforme au bouton secondaire de la charte (survol, padding 16 px, état désactivé distinct).
- Correctif : Primitive Button existante, secondaire, taille md. Paragraphes déjà lisibles conservés.
- Rouge : [sortie interface-lot3-rouge](.c19d/preuves/interface-lot3-rouge.log). Vert : [sortie contrats-et-clavier-vert](.c19d/preuves/contrats-et-clavier-vert.log).
- Commit : `3eb5614b` (B-1093).
- À mesurer/rejouer dans Chrome : Padding 16 px, survol et état désactivé en démonstration.

### B-1094

- Cause : Le catch remplaçait la liste illisible par [] et affichait le vide.
- Reproduction : confirme. Attendu : Une lecture en échec ne s'affiche pas comme un vide.
- Correctif : État de lecture séparé ; aucune affirmation de vide en échec ; une erreur d’ajout ne masque pas une liste lue.
- Rouge : [sortie interface-lot3-rouge](.c19d/preuves/interface-lot3-rouge.log). Vert : [sortie rejeux-interface](.c19d/preuves/rejeux-interface.log).
- Commit : `23ad97cf` (B-1094).
- À mesurer/rejouer dans Chrome : Erreur 500, liste vraiment vide puis changement de projet.

### B-1096

- Cause : Les spans truncate n’avaient pas de title.
- Reproduction : confirme. Attendu : Un libellé tronqué reste lisible en entier, comme le pose B-1160 pour les travaux (title).
- Correctif : Title complet sur les lignes ouvrables et les simples textes ; nom déjà masqué par l’hôte conservé.
- Rouge : [sortie interface-lot3-rouge](.c19d/preuves/interface-lot3-rouge.log). Vert : [sortie contrats-et-clavier-vert](.c19d/preuves/contrats-et-clavier-vert.log).
- Commit : `8cf03c85` (B-1096).
- À mesurer/rejouer dans Chrome : Survol des trois familles à nom long ; lecteur d’écran et démonstration.

### B-1102

- Cause : Le calcul via textContent omettait notamment les images avec alt.
- Reproduction : confirme. Attendu : L'instrument de couverture retient le nom accessible calculé par le navigateur.
- Correctif : Le relevé tire le nom de la même signature accessible que la relocalisation ; suppression du calcul artisanal.
- Rouge : [sortie B-1102-rouge-valide](.c19d/preuves/B-1102-rouge-valide.log). Vert : [sortie rejeux-commandes-et-instrument](.c19d/preuves/rejeux-commandes-et-instrument.log).
- Commit : `3be60614` (B-1102).
- À mesurer/rejouer dans Chrome : Vérifier en Chrome les boutons image, SVG titré et vide ; le SVG était déjà correctement nommé.

## Rejeux inventés après correction

Les entrées exactes figurent dans les tests paramétrés. Les listes ci-dessous identifient les dix scénarios de chaque changement de logique ; les valeurs bancaires et jetons sont des exemples de test, jamais des identifiants de l’utilisatrice.

| Correctif | Dix entrées/scénarios après correction | Preuve |
|---|---|---|
| B-1088 | « Secrétariat général : appeler Léa jeudi » ; « Je vous prie de trouver le devis joint » ; « Paul est parti en congés lundi » ; « Diagnostic de performance énergétique du local » ; « Traitement de la commande 678 » ; IBAN belge ; IBAN néerlandais ; mot de passe factice ; `api_key` factice ; `refresh_token` factice | `test_rejeu_apres_correctif` dans `tests/test_c19d_b1088_securite_memoire.py` |
| B-1075 et B-1112 | Appeler Luc ; Préparer la visite ; Lire le devis ; Commander les tuiles ; Réserver la salle ; Relancer Léa ; Vérifier les plans ; Revoir le budget ; Ranger le dossier ; Confirmer la livraison. Pour chacune : Entrée ouvre, poignée saisit, Échap annule sans quitter. | `TaskKanban.c19d.test.tsx` |
| B-1064 | Erreur réseau ; Réponse 500 ; Réponse 502 ; Document supprimé ; Accès refusé ; Délai dépassé ; Service indisponible ; Réponse illisible ; Connexion interrompue ; Lecture interrompue. Pour chacune : message, absence de chargement permanent et reprise réussie. | `DocumentWorkspace.c19d.test.tsx` |
| B-1056 | Résumer ce courrier ; Relire le devis ; Préparer un rendez-vous ; Expliquer la facture ; Classer cette note ; Lister les travaux ; Traduire le paragraphe ; Comparer les offres ; Rédiger une relance ; Préparer la visite. Focus reçu et Échap ferme la seule commande. | `PanelContainer.b1726.test.tsx` |
| B-1068 | Terrasse ; Charpente ; Cuisine ; Bureau ; Jardin ; Façade ; Salon ; Garage ; Atelier ; Grenier. Ouverture distincte de la poignée pour chaque nom. | `ProjectsKanban.test.tsx` |
| B-1046 et B-1097 | `grok-4.21-0412-reasoning` ; `grok-4.21-0412-non-reasoning` ; `google/gemini-4.2-flash` ; `meta-llama/llama-5-scout` ; `deepseek-v5-chat` ; `ministral-12b-2610` ; `claude-sonnet-5-7-20261022` ; `openai/gpt-7-mini` ; `qwen-4-3b` ; `minimax-m3` | `test_c19d_b1046_1097.py` |
| B-1077 | OVERDUE/avoir ; overdue entouré d’espaces/avoir ; draft/avoir ; sent/avoir ; paid/avoir ; cancelled/avoir ; overdue/facture ; sent/facture ; sent/devis ; accepted/devis | `test_c19d_b1077.py` |
| B-1081 et B-1083 | sent/facture ; paid/facture ; cancelled/facture ; sent/devis ; accepted/devis ; refused/devis ; expired/devis ; sent/avoir ; paid/avoir ; draft/facture | `InvoiceConversationCard.test.tsx` |
| B-1082 | TVA 0 ; 2,1 ; 5,5 ; 10 ; 20 ; 4,5 ; 7,7 ; 8,1 ; 12,25 ; 19,6 % | `InvoiceConversationCard.test.tsx` |
| B-1086 | 0 ; 100 ; 999 ; 1 000 ; 1 550 ; 12 000 ; 28 345 ; 100 000 ; 1 234 567 ; 9 999 999 jetons | `LimitsTab.cycle6.test.tsx` |
| B-1091 | Dix montages et cycles ouvrir/replier, sans identifiant absent ; libellés premier à dixième dans le test. | `B-1091.test.tsx` |
| B-1094 | Projets terrasse ; grange ; atelier ; toiture ; cuisine ; salon ; jardin ; bureau ; garage ; cave. Une erreur de lecture ne devient jamais un vide. | `ProjectDeliverablesSection.p153.test.tsx` |
| B-1102 | Ouvrir Léa ; Fermer « Projet » ; Revenir à l’accueil ; Sauver le devis ; Lire une note ; Copier un lien ; nom avec guillemets ; nom avec barre oblique inverse ; Accès à l’Agenda ; nom sur deux lignes. Le snapshot prime sur l’`alt` différent. | `B-1102.test.js` |

Les autres corrections changent un texte constant, un jeton, une classe ou une association ARIA et conservent les règles et les gestes existants.

Le test national ajouté après le premier correctif a révélé un cas italien encore manquant : [rouge](.c19d/preuves/B-1088-integration-et-pays.log). Les groupes sont désormais décrits explicitement et les dix pays passent : [vert](.c19d/preuves/B-1088-integration-et-pays-vert.log).

Deux gardes supplémentaires ont ensuite signalé des régressions du premier ajustement : quatre identifiants/exception (`smtpToken`, `clientSecret`, `SMTPTOKEN`, `token_limits`) échouaient ([rouge identifiants](.c19d/preuves/B-1088-identifiants-rouge.log)), puis la ponctuation des coordonnées n’était pas entièrement préservée ([rouge séparateurs](.c19d/preuves/B-1088-separateurs-rouge.log)). Les identifiants et les séparateurs sont corrigés ; les preuves initiales ne sont pas remplacées. Deux nouveaux rejeux de dix entrées figurent dans `test_rejeu_identifiants_apres_ajustement` et `test_rejeu_separateurs_apres_correctif` : cinq secrets ou IBAN factices refusés et cinq libellés professionnels admis par série. Le [contrôle de sécurité final](.c19d/preuves/B-1088-securite-finale-vert.log) inclut les tests de protection historiques.

Les assertions B-1065 et B-1067 ont été affinées pour viser le nom calculé et le fragment affiché, puis rejouées sur la base : [rouge de confirmation](.c19d/preuves/contrats-affines-base-rouge.log). Les contraintes de rendu restent à mesurer dans Chrome.

B-1088 reçoit en plus sept créations réelles de fiches via le service et les dix formats nationaux déjà filtrés, dont une représentation Unicode. Le corpus historique de protection est rejoué : mots de passe, clés, jetons, cartes bancaires et catégories sensibles restent refusés. Le refus nomme une catégorie sans réafficher sa valeur.

## Contrôles

- [sortie moteur-livraison-definitive](.c19d/preuves/moteur-livraison-definitive.log) : 263 passed, 4 warnings in 86.67s (0:01:26) ; Code de sortie : 0
- [sortie moteur-final-livre](.c19d/preuves/moteur-final-livre.log) : 249 passed, 4 warnings in 114.37s (0:01:54) ; Code de sortie : 0
- [sortie moteur-final-definitif](.c19d/preuves/moteur-final-definitif.log) : 234 passed, 4 warnings in 215.76s (0:03:35) ; Code de sortie : 0
- [sortie moteur-final](.c19d/preuves/moteur-final.log) : 131 passed, 4 warnings in 92.72s (0:01:32)
- [sortie moteur-routers-import-notifications](.c19d/preuves/moteur-routers-import-notifications.log) : 34 passed, 4 warnings in 50.48s ; Code de sortie : 0
- [sortie B-1088-integration-et-pays-vert](.c19d/preuves/B-1088-integration-et-pays-vert.log) : 56 passed, 4 warnings in 28.61s ; Code de sortie : 0
- [sortie B-1088-securite-finale-vert](.c19d/preuves/B-1088-securite-finale-vert.log) : 85 passed, 4 warnings in 11.13s ; Code de sortie : 0
- [sortie rejeux-interface](.c19d/preuves/rejeux-interface.log) : Test Files  8 passed (8) ; Tests  119 passed (119)
- [sortie rejeux-commandes-et-instrument](.c19d/preuves/rejeux-commandes-et-instrument.log) : Test Files  2 passed (2) ; Tests  25 passed (25) ; Code de sortie : 0
- [sortie contrats-et-clavier-vert](.c19d/preuves/contrats-et-clavier-vert.log) : Test Files  20 passed (20) ; Tests  52 passed (52)
- [sortie validation-board-libelles](.c19d/preuves/validation-board-libelles.log) : Test Files  1 passed (1) ; Tests  2 passed | 3 skipped (5) ; Code de sortie : 0
- [sortie splash-vert](.c19d/preuves/splash-vert.log) : Test Files  1 passed (1) ; Tests  4 passed (4)
- [sortie factures-gardes-vert](.c19d/preuves/factures-gardes-vert.log) : Test Files  3 passed (3) ; Tests  31 passed (31) ; Code de sortie : 0
- [sortie navigation-et-poignees-vert](.c19d/preuves/navigation-et-poignees-vert.log) : Test Files  1 failed | 4 passed (5) ; Tests  1 failed | 20 passed (21) ; Code de sortie : 1
- [sortie frontend-c19d-final](.c19d/preuves/frontend-c19d-final.log) : Test Files  31 passed (31) ; Tests  143 passed | 31 skipped (174) ; Code de sortie : 0
- [sortie gardes-du-controle-complet-vert](.c19d/preuves/gardes-du-controle-complet-vert.log) : Test Files  7 passed (7) ; Tests  38 passed (38) ; Code de sortie : 0
- [sortie tsc-final-definitif](.c19d/preuves/tsc-final-definitif.log) : Code de sortie : 0
- [sortie eslint-final-definitif](.c19d/preuves/eslint-final-definitif.log) : ✖ 27 problems (0 errors, 27 warnings) ; Code de sortie : 0
- [sortie ruff-livraison-definitive](.c19d/preuves/ruff-livraison-definitive.log) : All checks passed! ; Code de sortie : 0
- [sortie vitest-complet](.c19d/preuves/vitest-complet.log) : Test Files  10 failed | 871 passed (881) ; Tests  14 failed | 3651 passed (3665) ; Code de sortie : 1
- [sortie vitest-complet-final](.c19d/preuves/vitest-complet-final.log) : Test Files  2 failed | 879 passed (881) ; Tests  3 failed | 3673 passed (3676) ; Code de sortie : 1
- [sortie dates-pool-processus](.c19d/preuves/dates-pool-processus.log) : Test Files  1 passed (1) ; Tests  6 passed (6) ; Code de sortie : 0
- [sortie dates-pool-threads](.c19d/preuves/dates-pool-threads.log) : Test Files  1 failed (1) ; Tests  2 failed | 4 passed (6) ; Code de sortie : 1

Les sorties finales ne sont déclarées réussies que lorsque leur code de sortie est connu. Le premier passage complet a terminé **881 fichiers** : **3 651 tests réussis et 14 échecs**. Onze échecs venaient des anciennes attentes de libellé, de nom ou de position. Ces gardes sont mises à jour et leur reprise passe : [38 tests verts](.c19d/preuves/gardes-du-controle-complet-vert.log).

Les trois autres résultats varient suivant le contexte : choix Souverain du Board, assistant de commande de l’accueil et retour de l’assistant e-mail. Une archive intégrale de f01582fa a passé les six tests correspondants lors d’un premier passage, puis a échoué sur Board et accueil lors d’un second, sans correctifs du lot ([premier passage](.c19d/preuves/base-trois-tests-hors-lot.log), [rejeu de la base](.c19d/preuves/base-trois-tests-hors-lot-rejeu.log)). L’assistant e-mail passe aussi isolément dans l’arbre corrigé ([preuve](.c19d/preuves/email-hors-lot-isole.log)). Ces observations signalent une instabilité de test ; elles ne suffisent pas à en attribuer la cause. Le passage complet reste distinct des reprises ciblées et n’est pas déclaré vert par déduction.

Le passage complet final avec quatre threads a terminé **881 fichiers** : **3 673 tests réussis et 3 échecs** (3 676 tests). Le test e-mail B-329 échoue encore dans ce passage. Les deux autres échecs sont dans `civilDate.joursCouverts.test.ts`, fichier et code d’agenda inchangés : le changement de fuseau durant le test échoue avec des threads. Le même fichier exécuté seul reproduit exactement **2 échecs et 4 réussites** avec des threads, puis **6 réussites** en processus séparés, mode par défaut du projet ([threads](.c19d/preuves/dates-pool-threads.log), [processus](.c19d/preuves/dates-pool-processus.log)). Le contrôle complet final est donc **rouge** ; les reprises isolées ne le remplacent pas.

## Historique demandé

Commande : `git log --oneline f01582fa..HEAD`, capturée après les 39 commits de correctifs et avant le commit de remise du rapport.

```text
3be60614 fix(couverture): retenir le nom du snapshot accessible (B-1102)
8cf03c85 fix(projets): rendre les noms tronqués consultables en entier (B-1096)
23ad97cf fix(livrables): distinguer la panne du vide (B-1094)
3eb5614b fix(memoire): employer le bouton secondaire pour modifier le profil (B-1093)
0269ede0 fix(pipeline): référencer uniquement une explication présente (B-1091)
425b3120 fix(consommation): afficher les jetons en notation française (B-1086)
db1f694d fix(factures): franciser la TVA et accorder les statuts des cartes (B-1082 B-1083)
424d4f7d fix(factures): traduire le statut actuel de la confirmation (B-1081)
f8d7f21c fix(projets): séparer la poignée des commandes de la carte (B-1068)
adb44d05 fix(confidentialite): associer le curseur de rétention à son libellé (B-1076)
b6a2a725 fix(atelier): accentuer le nom de la relance (B-1087)
c4e2e635 fix(agenda): employer Agenda dans le formulaire (B-1085)
e0455d08 fix(factures): identifier les actions par leur pièce (B-1080)
e5e29c4c fix(profil): nommer la croix de l’aperçu des consignes (B-1074)
9ab441c0 fix(conversations): aligner le tiroir sur le rail (B-1072)
9f93fa31 fix(navigation): inclure Retour dans le nom accessible (B-1071)
13de6707 fix(installation): retirer le faux raccourci de fermeture (B-1069)
b6ec337e fix(contacts): accentuer le bandeau de rétention (B-1067)
946af404 fix(fichiers): nommer le répertoire personnel du fil d’Ariane (B-1065)
14838543 fix(modeles): séparer les dates des versions et respecter les noms (B-1046 B-1097)
5f9b0646 fix(projets): annoncer en français le statut retenu (B-1099)
48eb20eb fix(import): accentuer le message du tableur vide (B-1092)
f243790f fix(pdf): traduire le retard des avoirs (B-1077)
9a700b44 fix(presentations): accentuer la signature du repli (B-1048)
cf6b7950 fix(notifications): accentuer les messages générés (B-1047)
7be64dfa fix(oauth): déclarer le français dans les pages de retour (B-1045)
355ac937 fix(markdown): faire défiler les blocs de code (B-1084)
1e4cb084 fix(pipeline): nommer les fermetures et annoncer les filtres actifs (B-1062 B-1063)
a288b6e5 fix(conversation): identifier les actions des entités détectées (B-1061)
796b4ac3 fix(conversation): corriger la pastille projet et les accents (B-1057 B-1058)
386d4128 fix(commandes): piéger le focus et nommer la fermeture (B-1056)
b7055286 fix(demarrage): rendre les pistes visibles et annoncer la progression (B-1053 B-1055)
06c5062d fix(decision): associer les libellés et adapter les logos au thème (B-1051 B-1052)
3a17508b fix(decision): nommer la vérification et expliquer le mode indisponible (B-1049 B-1050)
ba5cd342 fix(conversation): limiter la mention aux cartes de confirmation (B-1073)
3d7f1b5f fix(factures): laisser respirer le pied de formulaire (B-1079)
61e7c298 fix(documents): afficher les erreurs de lecture avec une reprise (B-1064)
eaec3f7e fix(taches): séparer ouverture et glisser au clavier (B-1075 B-1112)
c3a8ccdc fix(memoire): corriger les faux positifs et expliquer les refus (B-1088)
```
