# Cycle 20, lot diff-3

**État après la passe 4 : 2 confirmés, 6 rejetés, 2 règles à trancher. B-2020 est retiré du lot, reporté.** La section « Remédiation de la relecture, passe 4 » fait foi pour le résultat livré ; les comptes rendus précédents restent historiques.

Travail réalisé le 16 novembre 2026, uniquement dans l’arbre `gpt-c20-diff-3`, branche `gpt/c20-diff-3`. HEAD initial et final : `4dfc79d1568d123d7b517113a984b75baca84fc0`. L’arbre était propre au départ. Aucun commit, aucune tentative de `git add`, aucun push. Les trois tests ajoutés et les quatre composants corrigés restent non commités.

Les candidats ont été examinés dans l’ordre demandé. Bilan : **3 confirmés, 6 rejetés, 1 règle à trancher**. Les huit cas des trois nouveaux fichiers de test ont échoué avant leur correctif, sur les assertions décrites ci-dessous. Aucun test existant n’a été modifié.

## Tableau des candidats

La colonne du rouge remplace le hash du commit conformément à la particularité de cette exécution. Les noms paramétrés correspondent aux noms des tests Vitest ; les valeurs exécutées sont indiquées dans les preuves détaillées.

| ID | Verdict | Test ou vérification (`chemin::nom`) | Rouge observé | Correctif |
| --- | --- | --- | --- | --- |
| B-1895 | `rejete` | `src/frontend/scripts-recette/recette-r5-memoire.mjs::build` | Sans objet : compilation réussie, charte présente dans le CSS produit | Sans objet |
| B-1896 | `rejete` | `src/frontend/src/components/chat/ChatInput.memoireAccord.r2.test.tsx::le signal serveur demande l’accord puis reprend la même source sans doublon utilisateur` | Sans objet : le marqueur technique est caché, la description des fiches est déjà affichée | Sans objet |
| B-2015 | `regle_a_trancher` | `src/frontend/src/components/memory/AgentMemoryPanel.r5.test.tsx::confirme l’effacement, reprend le focus après Échap et masque les traces en démo` | Sans objet : le périmètre du masquage des métadonnées n’est pas fixé | Sans objet |
| B-2016 | `confirme` | `src/frontend/src/components/Aide.erreurs.c20.test.tsx::B-2016 : un échec du PDF propose de vérifier le lecteur PDF uniquement` et `::B-2016 : un échec de la page sécurité propose de vérifier le navigateur uniquement` | `Error: expect(element).not.toHaveTextContent()` ; les deux erreurs mentionnaient le lecteur PDF et le navigateur | non commité |
| B-2017 | `rejete` | `src/frontend/src/components/llm/GuidePremierServiceIA.test.tsx::rend l’installation locale accessible même avant la détection d’Ollama` ; sonde temporaire de conservation de l’ouverture décrite ci-dessous | Sans objet : gestes conservés après deux causes de nouveau rendu | Sans objet |
| B-2018 | `rejete` | `src/frontend/scripts-recette/recette-r5-memoire.mjs::build` | Sans objet : même constat que B-1895, même parcours de compilation valide | Sans objet |
| B-2019 | `rejete` | `src/frontend/src/components/chat/ChatInput.memoireAccord.r2.test.tsx::le signal serveur demande l’accord puis reprend la même source sans doublon utilisateur` | Sans objet : même constat que B-1896, description française présente | Sans objet |
| B-2020 | `regle_a_trancher` | Neuf reproductions R4.1 à R4.8 exécutées avant retrait ; sources conservées dans `/tmp/diff-3-r4-reproductions/` | Huit constats de la relecture confirmés ; lignes d’échec ci-dessous, passe 4 | retiré du lot, reporté |
| B-2021 | `confirme` | `src/frontend/src/components/memory/AgentMemoryPanel.origineVide.c20.test.tsx::B-2021 : distingue une recherche par origine sans résultat de la mémoire vide (%s)` | `Error: Unable to find an element with the text: Aucune fiche ne correspond à ta recherche.. This could be because the text is broken up by multiple elements. In this case, you can provide a function for your text matcher to make your matcher more flexible.` | non commité |
| B-2022 | `rejete` | `src/frontend/src/lib/catalogueModeles.openrouter.r19b.test.ts::retire le préfixe des modèles du catalogue et conserve les inconnus` et `::B-1097 : decorer formate aussi le modèle absent du catalogue %s` | Sans objet : nom dérivé d’un identifiant fictif, conforme au contrat existant | Sans objet |

**B-2020 : retiré du lot, reporté.** Preuve : les constats 1 à 8 de la quatrième relecture décrivent des pertes de brouillons et de pièces, une file hors conversation ou hors ordre, une navigation périmée et trois défauts de priorité ou d’isolation du focus. Les reproductions de la passe 4 les confirment.

## Rejets et règle à trancher

### B-1895 et B-2018 : le relatif est utilisé après copie

`src/frontend/scripts-recette/recette-r5-memoire.mjs:9-18` calcule la racine du dépôt, copie `entry.tsx`, `index.html` et `style.css` dans `.recette-r5/ui`, puis compile depuis ce répertoire. À cet endroit, `../../src/frontend/src/styles/globals.css` et `../../src/frontend/src` désignent bien la feuille et l’arbre de production. Modifier les chemins en fonction du répertoire de stockage des fixtures casserait ce parcours.

Exécution réelle, sans serveur : `node src/frontend/scripts-recette/recette-r5-memoire.mjs`, code de sortie 0. Le CSS compilé contient `--color-bg`, `--color-text`, `--color-accent-cyan`, `.bg-surface` et `.text-text`. Cette vérification porte sur la sortie de compilation. Les artefacts temporaires ont ensuite été déplacés vers `/tmp/diff-3-recette-output`, sans modification des fixtures. Log : `/tmp/diff-3-recette.log`.

### B-1896 et B-2019 : identifiant interne et description française coexistent

`MEMORY_CARDS_CATEGORY` vaut le marqueur technique `memory_cards_r2_v1` (`src/frontend/src/lib/consent.ts:116`). Les deux parcours de production du chat transmettent déjà une description lisible à côté de ce marqueur :

- `src/frontend/src/components/chat/ChatInput.tsx:687-690` : « tes fiches mémoire utiles, renvoyées avec chaque échange où la mémoire est activée » ;
- `src/frontend/src/components/chat/ChatInput.tsx:903-907` : « tes fiches mémoire utiles avec chaque échange où la mémoire est activée ».

Le filtre du dialogue retire uniquement le marqueur. Aucun appelant de production ne fournit une liste réduite à ce seul marqueur. L’Atelier ne transmet pas de fiches mémoire via ce composant. Le contrat est décrit dans `docs/plans/2026-10-21-r2-memoire-fiches.md:75` et le test R2 exige à la fois la mention des fiches et l’absence du marqueur brut (`ChatInput.memoireAccord.r2.test.tsx:93-94`). Les trois tests de ce fichier passent avant correction de B-2020 et dans la porte finale. La liste de données n’a pas été modifiée.

### B-2015 : quelle confidentialité pour les métadonnées en démonstration ?

Le rendu conserve effectivement l’issue, la date/heure et l’indication d’annulation (`src/frontend/src/components/memory/ActivityMemoryBranch.tsx:65-66,78`). Le masque systématique porte sur les textes libres (`:41`). Les dates et états restent également affichés dans les fiches (`AgentMemoryPanel.tsx:136,144-148`). Le test R5 protège le titre et les actions ; il ne fixe aucune règle pour ces métadonnées. Le contrat général de démonstration précise lui-même un périmètre partiel (`src/frontend/src/components/settings/modeDemoPerimetre.test.tsx:29-62`).

**Question à trancher :** le mode démonstration doit-il masquer aussi les dates, issues et états du journal, même sans texte permettant d’identifier une personne ?

- Option A : conserver ces métadonnées pour montrer le fonctionnement du journal, en annonçant explicitement cette limite du masque.
- Option B : masquer ou remplacer par des valeurs fictives les dates, issues et états, de façon cohérente dans le journal et les fiches.

**Recommandation :** option B pour une démonstration filmée, afin de ne pas révéler l’activité réelle par ses heures, échecs ou corrections. Cette extension de périmètre doit être décidée avant d’écrire un test qui la rendrait obligatoire. Aucun changement sur B-2015.

### B-2017 : un rendu ne réapplique pas une prop inchangée

Les deux attributs `open` sont aux lignes 21 et 32 de `GuidePremierServiceIA.tsx`. Avec le même fournisseur, React ne les réécrit pas après le geste natif de l’utilisateur. Une sonde comportementale a fermé Claude, ouvert Ollama, déclenché la vérification avec un rendu parent (`retesting=true`), puis simulé un échec d’ouverture du navigateur produisant un rendu local. Les deux sections ont conservé leur état à chaque étape. Les deux tests existants et cette sonde passent : 3/3.

Sonde exécutée : `GuidePremierServiceIA.verification.c20.test.tsx::B-2017 : conserve les deux gestes sur les sections après un rendu parent et une erreur locale`. Elle a ensuite été déplacée vers `/tmp/diff-3-GuidePremierServiceIA.verification.c20.test.tsx` afin de ne laisser aucun changement pour ce rejet. Résultat : `/tmp/diff-3-b2017.json`. Un changement effectif de fournisseur peut changer les attributs ; aucune preuve n’établit que ce choix initial serait incorrect.

### B-2022 : le mot vient de l’identifiant du modèle

`src/frontend/src/lib/catalogueModeles.ts:66-101` forme le nom à partir de l’identifiant externe, avec ses séparateurs, sa version et son fournisseur. Le mot `modele` vient de la donnée fictive `inconnu/modele-1-2`, et non d’un libellé français ajouté par l’interface. Les noms ne font pas l’objet d’une correction orthographique automatique. Le moteur utilise le même contrat (`src/backend/app/services/modeles_catalogue.py:451-471`). Les 16 cas de `catalogueModeles.openrouter.r19b.test.ts` passent, y compris le maintien des noms locaux. Aucun nom arbitraire de modèle n’a été réécrit pour satisfaire cet exemple de test.

## Confirmations, rouges et corrections

### B-2016

Chemin de production vérifié avant correction : `Aide` est monté dans `WelcomeStep.tsx:87`, `SettingsModal.tsx:927` et `ConversationCanvasPrototype.tsx:2132`.

Le nouveau fichier seul a donné **0 passé, 2 échoués**. Ligne d’échec pour chaque cas :

```text
Error: expect(element).not.toHaveTextContent()
```

Pour le PDF, le texte interdit était `navigateur`. Pour la page sécurité, le texte interdit était `PDF`. Texte reçu dans les deux cas : `L’ouverture a échoué. Vérifie qu’un lecteur PDF et un navigateur sont installés, puis réessaie.` Les erreurs d’ouverture sont simulées ; aucun lecteur ni navigateur externe n’est appelé par les tests.

Correction : chaque action fournit son propre message d’erreur à `ouvrir`. Les tests vérifient également que la nouvelle tentative efface l’erreur et rappelle la bonne action. Les nouveaux tests, `Aide.test.tsx` et `Aide.palette.test.tsx` donnent **6 passés, 0 échoué**. Preuves : `/tmp/diff-3-b2016-rouge.{log,json}` et `/tmp/diff-3-b2016-vert.json`.

### B-2020

Chemin de production vérifié avant correction : `ChatInput.tsx:1688` et `AgentSession.tsx:736` montent `CloudConsentDialog`.

Le nouveau fichier seul a donné **0 passé, 4 échoués** :

```text
B-2020 : place le focus sur Annuler et isole le fond du dialogue modal
Error: expect(element).toHaveFocus()
B-2020 : boucle Tab et Maj+Tab, y compris pendant l’enregistrement
Error: expect(element).toHaveFocus()
B-2020 : Échap annule sans envoi et rend le focus au déclencheur (occupé : false)
AssertionError: expected "vi.fn()" to be called 1 times, but got 0 times
B-2020 : Échap annule sans envoi et rend le focus au déclencheur (occupé : true)
AssertionError: expected "vi.fn()" to be called 1 times, but got 0 times
```

Le focus restait sur « Envoyer la demande » à l’ouverture, puis sur « Autoriser et envoyer » après Tab. Échap n’appelait jamais l’annulation.

Correction : fenêtre modale portée dans `document.body` pour sortir des conteneurs de mise en page, couche `Z_LAYER.MODAL`, couleurs existantes, focus explicite sur Annuler et réutilisation de `useDialogFocusTrap` pour Tab, Maj+Tab, Échap, isolation du fond et retour au déclencheur. L’annulation reste disponible pendant l’enregistrement, conformément au comportement existant de l’Atelier.

L’isolation du fond a fait échouer trois tests existants de l’Atelier pendant la mise au point : `annuler ou ne pas obtenir l’acquittement bloque et explique le refus`, `ne démarre pas après profil pendant l’acquittement` et `ne démarre pas après destination pendant l’acquittement`, avec `Error: Unable to find role="alert"`. L’erreur d’enregistrement se trouvait hors de la fenêtre. Elle est transmise au dialogue et affichée à l’intérieur. La version initiale de ce bilan affirmait à tort que sa cause restait après fermeture : l’annulation la remplaçait par le message générique. Sa conservation est corrigée et vérifiée dans la remédiation de la relecture, passe 1, constat 4 ci-dessous. Aucun test existant n’a été affaibli. L’assertion nouvelle d’isolation examine l’ancêtre inerte du déclencheur, puisque le portail isole le conteneur de l’application.

Les quatre nouveaux cas et les intégrations R2 du chat et T4 de l’Atelier donnent **13 passés, 0 échoué**. Preuves : `/tmp/diff-3-b2020-rouge.{log,json}`, `/tmp/diff-3-b2020-vert.json` pour l’itération intermédiaire, `/tmp/diff-3-b2020-vert-v2.json` pour le vert.

### B-2021

Chemin de production vérifié avant correction : `PrototypeUnifiedViewCanvas.tsx:12,92` importe puis monte `AgentMemoryPanel` dans la vue `agent_memory`.

Le nouveau fichier seul a donné **0 passé, 2 échoués**, pour les origines `inconnue` et `documents`. Ligne d’échec dans les deux cas :

```text
Error: Unable to find an element with the text: Aucune fiche ne correspond à ta recherche.. This could be because the text is broken up by multiple elements. In this case, you can provide a function for your text matcher to make your matcher more flexible.
```

Le test vérifie d’abord l’accueil vide, applique uniquement le filtre d’origine, contrôle les paramètres envoyés au service simulé, puis exige le message de recherche vide. Il contrôle également le retour à l’accueil vide après suppression du filtre.

Correction minimale : ajout de `origine` à la condition du message d’absence de résultats. Le nouveau fichier et les quatre fichiers voisins `AgentMemoryPanel.{r2,r5,t9,t10}.test.tsx` donnent **14 passés, 0 échoué**. Preuves : `/tmp/diff-3-b2021-rouge.{log,json}` et `/tmp/diff-3-b2021-vert.json`.

## Portes finales

| Porte | Exécutés / passés | Échoués / erreurs | Ignorés | Détail |
| --- | --- | --- | --- | --- |
| Pytest ciblé | 7 / 7 | 0 / 0 | 0 | Voisin du parcours d’accord modifié : `tests/test_t4_consentement_moteur.py` ; XML effectivement relu |
| Vitest ciblé | 116 / 116 | 0 | 0 | 35 fichiers, dont 8 nouveaux cas de régression ; au plus 3 workers |
| Ruff | Contrôle terminé, sortie 0 | 0 | Sans objet | `All checks passed!` |
| TypeScript | Contrôle terminé, sortie 0 | 0 | Sans objet | Aucun diagnostic |
| ESLint | Contrôle terminé, sortie 0 | 0 | Sans objet | 27 avertissements dans 22 fichiers non modifiés ; aucun dans les composants modifiés |
| `git diff --check` | Contrôle terminé, sortie 0 | 0 | Sans objet | Aucun défaut d’espacement |

**Noms des échecs aux portes finales : aucun.** Aucune suite complète n’a été lancée. Aucun appel à un fournisseur LLM ou service en ligne, aucun serveur lancé sur les ports interdits, aucune utilisation du profil `~/.therese` ni de `.app-loop/`.

Commande backend exécutée depuis la racine :

```sh
OLLAMA_BASE_URL=http://127.0.0.1:9 .venv/bin/python -m pytest tests/test_t4_consentement_moteur.py -q -p no:cacheprovider --timeout=120 --junitxml=/tmp/diff-3-pytest.xml
.venv/bin/python -m ruff check --no-fix src/backend tests
```

Commandes frontend exécutées depuis `src/frontend` :

```sh
npx vitest run \
  src/components/Aide.erreurs.c20.test.tsx src/components/Aide.test.tsx \
  src/components/prototype/Aide.palette.test.tsx \
  src/components/shared/CloudConsentDialog.clavier.c20.test.tsx \
  src/components/atelier/AgentSession*.test.tsx \
  src/components/chat/ChatInput.test.tsx \
  src/components/chat/ChatInput.commandeFichier.b1521.test.tsx \
  src/components/chat/ChatInput.accordOllamaCloud.b1158.test.tsx \
  src/components/chat/ChatInput.memoireAccord.r2.test.tsx \
  src/components/chat/ChatInput.ollamaDistant.t4.test.tsx \
  src/components/memory/AgentMemoryPanel*.test.tsx \
  src/hooks/useDialogFocusTrap*.test.tsx \
  src/components/llm/GuidePremierServiceIA.test.tsx \
  src/lib/catalogueModeles.openrouter.r19b.test.ts \
  src/components/settings/modeDemoPerimetre.test.tsx \
  src/components/memory/ActivityMemoryBranch.confidentialite.r5.test.tsx \
  --maxWorkers=3 --no-cache --configLoader runner \
  --reporter=json --outputFile=/tmp/diff-3-vitest.json
npx tsc --noEmit
npm run lint
```

Le lancement initial de Vitest avec son chargeur par défaut a été refusé avant collecte : `EPERM: operation not permitted` lors de l’écriture dans `node_modules/.vite-temp`. Ce répertoire dépend du lien vers le dépôt principal. `--configLoader runner --no-cache` permet les mêmes tests en évitant cette écriture partagée. Aucun fichier de configuration n’a été modifié. Pour les prochains lots soumis à la même contrainte, regrouper ces options dans une commande locale de test éviterait de répéter ce contournement.

Résultats relus : `/tmp/diff-3-pytest.xml`, `/tmp/diff-3-vitest.json`, `/tmp/diff-3-ruff.log`, `/tmp/diff-3-tsc.log`, `/tmp/diff-3-lint.log`.

## Limite de vérification visuelle

La compilation de la recette prouve le chargement de la charte. Le focus, l’isolation, les actions et les textes sont vérifiés au rendu DOM par Vitest. Une tentative de capture locale du dialogue a toutefois échoué : Chrome sans interface s’arrête avec le code 134 dans le bac à sable ; le navigateur de contrôle indique `The browser access host is unavailable`. Aucune capture exploitable n’a été obtenue. Le rendu visuel de la fenêtre modale, notamment en petite largeur, reste à inspecter par l’orchestrateur. Il ne fait pas partie des preuves acquises.

## Remédiation de la relecture, passe 1

État vérifié le 16 novembre 2026 : branche `gpt/c20-diff-3`, HEAD `3337a0f3730148db4ecff60b3336b2283d6b2836`, arbre propre avant intervention. Les sections précédentes relatent le lot initial, avant son intégration par l’orchestrateur. Cette passe traite exclusivement les quatre constats de la relecture. Tous sont confirmés. Les modifications de cette passe restent non commitées, sans `git add`, sans changement de l’index ni du HEAD.

### Constat 1, P1 : raccourcis et demande d’accord périmée

Tests écrits et exécutés avant correction, séparément :

- `src/frontend/src/components/shared/CloudConsentDialog.clavier.c20.test.tsx`, sélection `-t 'R1.1 : bloque'` : **1 échec**, les 4 cas antérieurs exclus par cette sélection. Le vrai dialogue est associé au vrai hook des raccourcis ; huit raccourcis sont exercés depuis Annuler, puis la navigation est vérifiée après fermeture.
- Nouveau fichier `src/frontend/src/components/chat/ChatInput.accordContexte.c20r1.test.tsx`, exécuté seul : **16 échecs**. Les quatre parcours, message, commande documentaire, signal mémoire et recherche approfondie, sont testés avec changement de conversation ou de texte, avant le clic ou entre le clic et l’envoi différé. Le brouillon de B est identique à celui de A pour tester la garde de conversation indépendamment du texte. Les stores, l’autosauvegarde et le composeur sont réels ; les services d’envoi et d’accord sont simulés.

Lignes d’échec recopiées des résultats :

```text
R1.1 : bloque les raccourcis globaux tant que l’accord est ouvert
AssertionError: expected "vi.fn()" to not be called at all, but actually been called 8 times
R1.1 : refuse un accord périmé, parcours message et documents (8 cas)
AssertionError: expected "vi.fn()" to be called +0 times, but got 1 times
R1.1 : refuse un accord périmé, parcours mémoire (4 cas)
AssertionError: expected "vi.fn()" to be called 1 times, but got 2 times
R1.1 : refuse un accord périmé, parcours recherche (4 cas)
AssertionError: expected "vi.fn()" to not be called at all, but actually been called 1 times
```

Correction : `useKeyboardShortcuts` reconnaît aussi les modales `alertdialog`. Chaque demande dans `ChatInput` capture le texte et la conversation concernés. Ils sont relus avant l’enregistrement de l’accord et à nouveau avant l’envoi différé. Un contexte différent ou un composeur démonté empêche l’envoi. Le texte reste disponible. L’exception permettant la palette depuis les Réglages reste couverte par ses tests existants.

Appelants relus après correction : raccourcis de `ConversationCanvasPrototype`, montage du composeur dans `PrototypeChatSurface`, trois producteurs de `pendingCloudConsent` et reprise différée par `confirmCloudConsent`. Nouveaux tests et voisins : **84 passés, 0 échec**. Preuves : `/tmp/diff-3-r1-1-clavier-rouge.{log,json}`, `/tmp/diff-3-r1-1-contexte-rouge.{log,json}`, `/tmp/diff-3-r1-1-vert.{log,json}`.

### Constat 2, P1 : accord reçu derrière la palette

Nouveau fichier `src/frontend/src/components/shared/CloudConsentDialog.empilement.c20r1.test.tsx`, exécuté seul avant correction : **2 échecs**, accord au repos et occupé. Le test monte la vraie palette de `ConversationCanvasPrototype`, puis reçoit un accord. Tailwind compile en mémoire les classes de position et les couches de production ; les z-index calculés, l’isolation, Tab, Maj+Tab, Échap et les deux retours de focus sont contrôlés.

Ligne d’échec dans les deux cas :

```text
AssertionError: expected 50 to be greater than 80
```

Correction minimale : couche nommée `Z_LAYER.CLOUD_CONSENT`, niveau 85, utilisée par `CloudConsentDialog`. L’accord reçu après la palette passe devant elle ; le piège existant peut alors l’isoler et rendre le focus à la recherche après annulation. Aucun changement du hook partagé de piégeage.

Appelants relus après correction : rendus de `CloudConsentDialog` dans le chat et l’Atelier, couche et piège de la palette, comparaison des couches dans `isolateOutsideDialog`. Nouveaux tests et voisins : **85 passés, 0 échec**. Preuves : `/tmp/diff-3-r1-2-rouge.{log,json}` et `/tmp/diff-3-r1-2-vert.{log,json}`. Cette preuve porte sur le DOM et le CSS calculé ; elle ne remplace pas une inspection native du rendu.

### Constat 3, P2 : retour du focus dans l’Atelier

Extension de `src/frontend/src/components/atelier/AgentSession.consentement.t4.test.tsx`, exécutée seule avec `-t 'R1.3'` : **4 échecs** avant correction, 6 cas antérieurs exclus par la sélection. Les cas couvrent Annuler et Échap, avant et pendant l’acquittement. La première confirmation est effectivement démontée ; la mission ne démarre pas, le texte est conservé et le champ doit reprendre le focus.

Ligne d’échec dans les quatre cas :

```text
Error: expect(element).toHaveFocus()
```

Correction : `annulerAccord` programme le retour au champ stable de la mission après sa réactivation et le retrait de l’isolation. La référence devient nulle si la session est démontée entre-temps.

Appelants relus après correction : boutons Retour et Annuler, pile Échap de l’accord, réactivation du champ, garde de génération de l’acquittement et montage de la session dans `AtelierPanel`. Tous les fichiers `AgentSession*.test.tsx` et `CloudConsentDialog*.test.tsx` : **37 passés, 0 échec**. Preuves : `/tmp/diff-3-r1-3-rouge.{log,json}` et `/tmp/diff-3-r1-3-vert.{log,json}`.

### Constat 4, P3 : cause du refus après fermeture

Extension de `src/frontend/src/components/atelier/AgentSession.accordMoteur.test.tsx`, exécutée seule avec `-t 'R1.4'` : **2 échecs** avant correction, 5 cas antérieurs exclus par la sélection. Un refus explicite du moteur est affiché dans le dialogue, puis Annuler ou Échap doit conserver exactement sa cause dans l’alerte de la session.

Ligne d’échec dans les deux cas :

```text
Error: expect(element).toHaveTextContent()
```

Reçu : `La mission n’a pas démarré. Donne ton accord pour lancer cet agent.` Attendu : `La mission n’a pas démarré : ton accord n’a pas été enregistré par le moteur. Le profil a changé. Reviens au profil concerné avant de réessayer.`

Choix : conserver la cause, utile pour comprendre le refus. `annulerAccord` ne produit le message générique que lorsqu’aucune erreur n’est déjà présente. L’ancienne affirmation du bilan est corrigée pour dater honnêtement ce comportement de la présente passe.

Appelants relus après correction : remise à zéro de l’erreur au prochain `confirmSend`, rendu unique de l’alerte dans le dialogue ou dans la session, et mêmes chemins d’annulation que le constat 3. Tous les fichiers `AgentSession*.test.tsx` et `CloudConsentDialog*.test.tsx` : **39 passés, 0 échec**. Preuves : `/tmp/diff-3-r1-4-rouge.{log,json}` et `/tmp/diff-3-r1-4-vert.{log,json}`.

### Portes de cette passe

| Porte | Résultat effectivement relu |
| --- | --- |
| Pytest ciblé | **7/7**, 0 échec, 0 erreur, 0 ignoré ; `/tmp/diff-3-r1.xml` parsé et relu |
| Vitest ciblé et voisins | **168/168 dans 35 fichiers**, dont **25 nouveaux cas**, 0 échec, 0 ignoré ; 163 dans le lot principal et 5 dans les deux voisins de la palette/Réglages |
| Ruff | Sortie 0, `All checks passed!` |
| TypeScript | Sortie 0, aucun diagnostic final |
| ESLint | Sortie 0, 0 erreur, 27 avertissements existants dans 22 fichiers |
| Diff et index | `git diff --check` sans défaut ; aucun changement indexé et HEAD inchangé |

TypeScript a d’abord relevé un retour manquant dans le nouveau double de `grantCloudConsent` (`TS2345`). Le double renvoie maintenant un `CloudGrant` fictif conforme à son type ; les 16 cas concernés ont été rejoués et passent. Aucun test existant n’a été affaibli. Le seul avertissement ESLint dans un fichier de production touché concerne `initialSkillId` dans un effet préexistant de `ChatInput`, comparé à HEAD et laissé intact.

Les décomptes finaux ne cumulent pas les relectures successives des mêmes tests. Les rouges connus cités par l’orchestrateur ne figurent pas dans la sélection. Aucune suite complète, aucun réseau, aucun appel de fournisseur LLM, aucun serveur, aucun usage des ports interdits, de `~/.therese` ou de `.app-loop/`. Aucune commande `rm`, aucun dépôt annexe ni bundle. Le backend utilise un dossier jetable créé sous `/tmp` et le frontend utilise des doubles de services.

Commandes backend depuis la racine :

```sh
PYTHONDONTWRITEBYTECODE=1 OLLAMA_BASE_URL=http://127.0.0.1:9 \
  THERESE_DATA_DIR="$(mktemp -d /tmp/diff-3-r1-data.XXXXXX)" \
  .venv/bin/python -m pytest tests/test_t4_consentement_moteur.py \
  -q -p no:cacheprovider --timeout=120 --junitxml=/tmp/diff-3-r1.xml
RUFF_CACHE_DIR=/tmp/diff-3-r1-ruff-cache .venv/bin/python -m ruff check --no-fix src/backend tests
```

Commandes frontend depuis `src/frontend` :

```sh
npm_config_offline=true VITE_THERESE_BACKEND_PORT=9 npx vitest run \
  src/components/shared/CloudConsentDialog*.test.tsx \
  src/components/atelier/AgentSession*.test.tsx \
  src/components/chat/ChatInput.accordContexte.c20r1.test.tsx \
  src/components/chat/ChatInput.test.tsx \
  src/components/chat/ChatInput.commandeFichier.b1521.test.tsx \
  src/components/chat/ChatInput.accordOllamaCloud.b1158.test.tsx \
  src/components/chat/ChatInput.memoireAccord.r2.test.tsx \
  src/components/chat/ChatInput.memoirePieces.b1837.test.tsx \
  src/components/chat/ChatInput.ollamaDistant.t4.test.tsx \
  src/components/chat/ChatInput.brouillonParConversation.b1377.test.tsx \
  src/hooks/useKeyboardShortcuts*.test.ts \
  src/hooks/useDialogFocusTrap*.test.tsx \
  src/components/prototype/ConversationCanvasPrototype.palette.focus.test.tsx \
  src/components/prototype/PanneauxNonModaux.test.tsx \
  --maxWorkers=3 --no-cache --configLoader runner \
  --reporter=json --outputFile=/tmp/diff-3-r1-vitest.json
npm_config_offline=true VITE_THERESE_BACKEND_PORT=9 npx vitest run \
  src/hooks/useKeyboardShortcuts.rechercheReglages.r6.test.tsx \
  src/components/prototype/ConversationCanvasPrototype.palette.raccourcis.test.tsx \
  --maxWorkers=3 --no-cache --configLoader runner \
  --reporter=json --outputFile=/tmp/diff-3-r1-vitest-reglages.json
npm_config_offline=true npx tsc --noEmit
npm run lint
```

Les options `--configLoader runner --no-cache` évitent toute écriture dans le `node_modules` partagé. Les tests ont été lancés avec au plus trois workers, puis les autres portes successivement. Résultats relus : `/tmp/diff-3-r1-pytest.log`, `/tmp/diff-3-r1.xml`, `/tmp/diff-3-r1-ruff.log`, `/tmp/diff-3-r1-vitest.json`, `/tmp/diff-3-r1-vitest-reglages.json`, `/tmp/diff-3-r1-contexte-final.json`, `/tmp/diff-3-r1-tsc.log` et `/tmp/diff-3-r1-lint.log`.

## Remédiation de la relecture, passe 2

Intervention du 17 novembre 2026 dans le même arbre. HEAD initial : `ba465a0ab1dbda6169112e9282533f9d3bcb061f`, branche `gpt/c20-diff-3`. Les fichiers suivis étaient propres ; les liens locaux `.venv` et `src/frontend/node_modules` étaient déjà non suivis et n'ont pas été modifiés. Aucun commit, aucun ajout à l'index, aucun dépôt annexe ni bundle.

### Constat 1, P1 : demandes conservées pendant les attentes

Ajout de huit cas `R2.1` dans `src/frontend/src/components/chat/ChatInput.accordAttentes.c20r2.test.tsx`, lancés seuls avec `-t R2.1` avant correction : **8 échecs**. Ils suspendent `previewVariables` au premier envoi et après accord, les deux attentes de persistance pour le message et la recherche, puis le premier événement des deux flux. B contient volontairement le même texte qu'A : l'identité doit protéger à elle seule sa conversation et son brouillon.

Lignes d'échec relevées :

```text
R2.1 : garde la conversation pendant previewVariables (premier envoi)
Error: expect(element).not.toBeInTheDocument()
R2.1 : garde la conversation pendant previewVariables (reprise après accord)
AssertionError: expected "vi.fn()" to not be called at all, but actually been called 1 times
R2.1 : garde la conversation pendant 'attendrePersistance' / 'assurerConversationPersistee'
AssertionError: expected "vi.fn()" to not be called at all, but actually been called 1 times
R2.1 : préserve B quand le premier événement arrive après la bascule (message)
AssertionError: expected [ { role: 'user', …(3) }, …(1) ] to have a length of +0 but got 2
R2.1 : préserve B quand le premier événement arrive après la bascule (recherche)
Error: expect(element).toHaveValue(Demande fictive A)
```

Correction : le premier geste capture la demande, que la confirmation transmet explicitement à la reprise. L'identité et le composeur sont contrôlés après les attentes, avant le flux et avant son premier acquittement. La recherche conserve désormais aussi le brouillon jusqu'à cet acquittement. Un flux ou un échec tardif ne remplit pas la conversation devenue courante.

Appelants relus : boutons, Entrée, reprise différée, file d'attente, chargement des agents, persistance du rattachement, reprise mémoire et gestion des erreurs du flux. Les cas nouveaux et voisins des constats 1 et 5 ont donné **73/73** après correction. Preuves : `/tmp/diff-3-r2-1-rouge.{log,json}`, `/tmp/diff-3-r2-1-5-vert.{log,json}`.

### Constat 2, P1 : menu de commandes derrière l'accord

Deux cas `R2.2` montent le vrai composeur, le vrai menu et le vrai dialogue, en message et en recherche. Quatre autres cas dans `SlashCommandsMenu.modale.c20r2.test.tsx` vérifient directement Tab, Entrée et les deux flèches, puis le retour du menu à un fonctionnement normal après fermeture de la modale. Exécution seule avec `-t R2.2` : **6 échecs** avant correction, tous avec cette ligne :

```text
AssertionError: expected "vi.fn()" to not be called at all, but actually been called 1 times
```

Le menu est fermé avant chaque ouverture d'accord et désactivé tant que celui-ci existe. Son écouteur global laisse les touches aux modales et respecte les événements déjà consommés. Appelants relus : seul montage de production du menu dans `ChatInput`, gestion clavier du composeur et pile Échap. Nouveaux tests et voisins : **34/34**. Preuves : `/tmp/diff-3-r2-2-{rouge,vert}.{log,json}`.

### Constat 3, P1 : pièces jointes, finalité et destination

Huit cas `R2.3`, exécutés seuls avant correction : **8 échecs**. Le premier utilise le vrai hook de dépôt avec les événements Tauri simulés ; les autres couvrent le retrait et le remplacement de pièces, les deux changements de finalité issus des variables, et le changement de destination pendant les variables ou la persistance du message/de la recherche.

```text
R2.3 : le vrai dépôt Tauri ignore B.png pendant l’accord pour A.png
AssertionError: expected [ 'A.png', 'B.png' ] to deeply equal [ 'A.png' ]
R2.3 : retrait, remplacement, changement de finalité et de destination
AssertionError: expected "vi.fn()" to not be called at all, but actually been called 1 times
```

Correction : dépôt désactivé pendant la modale, avec garde supplémentaire du callback commun au sélecteur natif. La demande conserve les pièces et la destination initiales ; les reprises vérifient leur égalité, l'origine d'une demande mémoire et la finalité après résolution des variables. Les chemins envoyés viennent de cet instantané. Une demande invalidée est signalée sans effacer le brouillon.

Appelants relus : dépôt Tauri, sélecteurs natif et navigateur, retrait et copie de fichiers, indexation, reprise documentaire/mémoire. Les huit cas et leurs voisins donnent **64/64**. La première mise au point du test avait effacé le double de `matchMedia` avec `resetAllMocks` ; `clearAllMocks` conserve ce double. Le rouge cité ci-dessus a été relancé après cette correction du banc de test. Preuves : `/tmp/diff-3-r2-3-{rouge,vert}.{log,json}`.

### Constat 4, P1 : intégration absente et migrations

Le constat est confirmé dans l'arbre reçu : `git log HEAD..c20/integration` contient encore `2dd3d2b1`, `9eb74c5d`, `fcf446a5`, `75498edd`. La référence d'intégration vaut `75498edd9d40b0aeb14f8c02787a56b4dea27a28`. L'annonce d'un rebase déjà effectué ne correspond donc pas à cet état.

Les deux tests d'intégration `test_c20_b1888_transaction_activites.py` et `test_c20_b1889_notes_heritees.py` ont d'abord été rétablis seuls, puis exécutés sans leurs corrections : **2 échecs**, XML effectivement parsé.

```text
test_reconstruction_preserve_la_transaction_appelante
AssertionError: La transaction de l’appelant a été validée.
test_note_rattachee_preservee_si_evenement_sans_projet
AssertionError: assert None == 'projet-existant'
```

Le contenu des quatre commits a été reporté par un patch de travail local, sans index, en conservant les corrections et les tests de diff-3. Les treize fichiers de tests absents sont rétablis, ainsi que les modifications de production et le bilan du lot migrations. Les deux régressions SQL citées sont corrigées par le contenu d'intégration : aucune reconstruction dans une transaction appelante et aucune migration de note tant que le rendez-vous n'a pas de projet. Les appelants de migration dans `database.py`, la provenance, les refus de mémoire, la vérification des clés, les dialogues de l'Atelier et des factures ont été relus. Premier contrôle des migrations et de leurs voisins : **203/203**, XML relu.

**Limite d'historique : aucun rebase Git n'a été effectué.** Le répertoire Git de ce worktree est hors de l'arbre autorisé et protégé en écriture ; le rebase modifierait aussi les commits, alors que la consigne impose de laisser les changements non commités. Le contenu est réconcilié, mais l'orchestrateur doit encore remettre l'historique sur `c20/integration` avant de commiter. HEAD et l'index restent inchangés. La comparaison finale confirme 22 fichiers identiques à l'intégration et deux fichiers de l'Atelier conservant aussi les correctifs précédents de diff-3. Preuves : `/tmp/diff-3-r2-4-{rouge,vert}.{log,xml}`, `/tmp/diff-3-r2-integration.patch`.

### Constat 5, P2 : adoption de l'identité serveur

Trois cas `R2.5` ont d'abord échoué : adoption serveur avant confirmation du message et de la recherche, puis explication d'une vraie péremption. La relecture de `useConversationSync` a conduit à un quatrième test, lui aussi rouge avant son correctif, sur le rafraîchissement de la liste après adoption.

```text
R2.5 : conserve l’accord après adoption serveur (message / recherche)
AssertionError: expected "vi.fn()" to be called 1 times, but got 0 times
R2.5 : explique pourquoi une demande devenue périmée ne part pas
AssertionError: expected [] to deeply equal ArrayContaining{…}
R2.5 : garde l’identité adoptée lors du rafraîchissement de la liste serveur
AssertionError: expected "vi.fn()" to be called 1 times, but got 0 times
```

`updateConversationId` conserve maintenant l'identité locale, et `setConversations` la préserve pendant la synchronisation. Les gardes utilisent cette identité stable ; les demandes réellement périmées affichent « Demande à confirmer à nouveau ». Appelants relus : adoption au premier événement, persistance de projet, synchronisation et remplacement de la liste. Le double du test existant `ChatInput.rattachement.test.tsx` appelle désormais la vraie méthode d'adoption, sans changer ses assertions. Aucun test existant n'a été affaibli. Les modifications de deux tests importées d'intégration sont conservées telles quelles.

Preuves : `/tmp/diff-3-r2-5-rouge.{log,json}`, `/tmp/diff-3-r2-5-liste-rouge.{log,json}`, `/tmp/diff-3-r2-1-5-vert.{log,json}`. Les nouveaux fichiers frontend ajoutent **26 cas** au total : 8 pour le constat 1, 6 pour le constat 2, 8 pour le constat 3 et 4 pour le constat 5.

La relecture finale a également renforcé les deux cas du premier acquittement du constat 1 : une bascule à cet instant préservait B, mais la garde d'identité court-circuitait encore la notification de péremption. Les deux cas ont échoué seuls sur `AssertionError: expected [] to deeply equal ArrayContaining{…}`, puis l'ordre des gardes a été corrigé, aussi pour une erreur reçue avant acquittement. Le rejeu des cas concernés et des voisins donne **48/48**. Aucun cas supplémentaire n'est compté. Preuves : `/tmp/diff-3-r2-5-acquittement-rouge.{log,json}` et `/tmp/diff-3-r2-acquittement-vert.{log,json}`.

### Portes finales de la passe 2

| Porte | Résultat |
| --- | --- |
| Pytest ciblé | **584/584 dans 22 fichiers**, 0 échec, 0 erreur, 0 ignoré ; XML parsé et relu ; lanceur adapté ci-dessous |
| Vitest ciblé et voisins | **417/417 dans 112 fichiers**, 0 échec, 0 ignoré, au plus 3 workers |
| Ruff | Sortie 0, `All checks passed!` |
| TypeScript | Sortie 0 après restriction de la finalité du chat à `llm` ou `documents` |
| ESLint | Sortie 0, **0 erreur, 27 avertissements existants** |
| Diff et index | `git diff --check` sans défaut ; index vide, HEAD inchangé |

TypeScript avait signalé `TS2322: Type 'CloudPurpose' is not assignable to type '"llm" | "documents" | undefined'` : la reprise mémoire pouvait désormais porter le type général des accords, qui comprend aussi la voix. Le type des demandes du chat est restreint aux deux finalités réellement transmises par cette API, sans assertion de type forcée. Les 26 cas du fichier d'attentes et de ses voisins mémoire ont été rejoués après cette correction et passent. Les décomptes de la porte ne cumulent pas ces relectures.

La commande Pytest standard s'est bloquée à l'entrée du premier client asynchrone, après les 203 premiers cas, sans produire de XML. Elle a été interrompue. Une sonde indépendante de THÉRÈSE, réduite à `asyncio.run` et `asyncio.to_thread`, a reproduit le blocage de fermeture et ce diagnostic :

```text
DEBUG:asyncio:Fail to write a null byte into the self-pipe socket
PermissionError: [Errno 1] Operation not permitted
```

Un `sitecustomize.py` uniquement sous `/tmp/diff-3-r2-polling` borne à **1 ms** l'attente de `selectors.EpollSelector.select`, pour reprendre les callbacks de threads malgré ce réveil interdit par le bac à sable. Aucun socket réseau n'est ajouté, aucune assertion ni fixture n'est remplacée. La sonde puis le premier test bloqué terminent avec ce lanceur ; le XML de ce diagnostic contient **1 test passé**. La porte complète ciblée a ensuite donné **584 tests passés en 557,098 secondes** avec ce même réglage temporaire. L'orchestrateur peut l'omettre sur une machine où le réveil asyncio fonctionne normalement.

Commandes backend depuis la racine (22 fichiers ciblés) :

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/diff-3-r2-polling \
  OLLAMA_BASE_URL=http://127.0.0.1:9 \
  THERESE_DATA_DIR="$(mktemp -d /tmp/diff-3-r2-data.XXXXXX)" \
  .venv/bin/python -m pytest \
  tests/test_c20_b1888_transaction_activites.py tests/test_c20_b1889_notes_heritees.py \
  tests/test_c20_b1890_activites_sans_contact.py tests/test_c20_b1891_reparation_transaction.py \
  tests/test_c20_b1893_provenance_sans_marque.py tests/test_c20_b2009_motifs_ambigus.py \
  tests/test_c20_b2010_limite_cle.py tests/test_c20_b2011_cle_sans_espace.py \
  tests/test_activity_migration.py tests/test_b1153_migration_colonnes.py \
  tests/test_b1153_rejeu_astra_v2.py tests/test_b1140_migration_sans_verrou.py \
  tests/test_r5_6_journal.py tests/test_r5_9_notes.py tests/test_c19d_b1088_securite_memoire.py \
  tests/test_r2_2_protection.py tests/test_t4_3_provenance_documents.py \
  tests/test_t4_4_historique_documents.py tests/test_t4_5_provenance_differee.py \
  tests/test_t4_7_provenance.py tests/test_b1348_verification_cle.py \
  tests/test_t4_consentement_moteur.py \
  -q -p no:cacheprovider --timeout=120 --junitxml=/tmp/diff-3-r2.xml
RUFF_CACHE_DIR=/tmp/diff-3-r2-ruff-cache .venv/bin/python -m ruff check --no-fix src/backend tests
```

Commandes frontend depuis `src/frontend` :

```sh
npm_config_offline=true VITE_THERESE_BACKEND_PORT=9 npx vitest run \
  src/components/chat/ChatInput*.test.tsx src/components/chat/SlashCommandsMenu*.test.tsx \
  src/components/shared/CloudConsentDialog*.test.tsx src/components/atelier/AgentSession*.test.tsx \
  src/components/invoices/InvoiceForm*.test.tsx src/hooks/useDialogFocusTrap*.test.tsx \
  src/hooks/useAutosave*.test.ts src/hooks/useConversationSync*.test.ts \
  src/hooks/useConversationSync*.test.tsx src/stores/chatStore*.test.ts \
  src/lib/rattachementConversation.test.ts src/lib/identiteConversation.test.ts \
  --maxWorkers=3 --no-cache --configLoader runner \
  --reporter=json --outputFile=/tmp/diff-3-r2-vitest.json
npm_config_offline=true npx tsc --noEmit
npm run lint
```

Aucun lancement de suite complète, aucun réseau ni fournisseur LLM, aucun serveur, aucun usage des ports interdits, de `~/.therese` ou de `.app-loop/`. Aucune commande `rm`. Les tests utilisent des doubles de services et des données temporaires sous `/tmp` ; les dépendances partagées restent en lecture seule. Les rouges connus cités dans la demande ne font pas partie de la sélection.

**Échecs aux portes finales : aucun.** Résultats effectivement relus : `/tmp/diff-3-r2.xml`, `/tmp/diff-3-r2-pytest-final.log`, `/tmp/diff-3-r2-vitest.json`, `/tmp/diff-3-r2-types-vert.json`, `/tmp/diff-3-r2-acquittement-vert.json`, `/tmp/diff-3-r2-ruff.log`, `/tmp/diff-3-r2-tsc.log`, `/tmp/diff-3-r2-lint.log`. Les tentatives interrompues du lanceur standard ne sont pas comptées comme des portes réussies.

## Remédiation de la relecture, passe 3

Intervention du 17 novembre 2026. HEAD reçu : `c84748159b50ff04edba225653600e7279012966`, branche `gpt/c20-diff-3`. Les fichiers suivis étaient propres ; les liens `.venv` et `src/frontend/node_modules` étaient déjà non suivis. Aucun commit, aucun `git add`, aucun dépôt annexe ni bundle. Les six constats sont confirmés ; la limite sur le rebase d'historique est détaillée au constat 6.

### Constat 1, P1 : demande en vol et brouillon suivant

Six cas `R3.1` ajoutés dans `ChatInput.accordAttentes.c20r2.test.tsx` : message et recherche, saisie conservée ou mise en file avant le premier événement, puis mise en file pendant la persistance préalable. Les quatre premiers cas ont échoué seuls avant correction ; la relecture des appelants a conduit aux deux cas de persistance, également exécutés seuls et rouges avant leur correction.

```text
AssertionError: expected [] to deeply equal [ 'Demande fictive A' ]
AssertionError: expected [] to deeply equal [ Array(1) ]
AssertionError: expected [ 'Demande suivante' ] to deeply equal [ 'Demande fictive A', …(1) ]
AssertionError: expected [ 'Demande suivante' ] to deeply equal [ …(2) ]
```

La demande est validée avec son brouillon avant préparation. Une fois le traitement lancé, les attentes de persistance contrôlent toujours la conversation et la destination, mais le champ peut porter le tour suivant. Au premier événement, l'instantané envoyé crée les bulles ; seul le brouillon encore égal au texte envoyé est vidé, et seules les pièces envoyées sont retirées. La file se vide ensuite normalement.

Appelants relus : envoi par bouton/Entrée, file et reprise différée, acquittement du message/de la recherche, persistance et adoption de l'identité serveur, autosauvegarde et arrêt. Premier groupe voisin : **47/47** ; après ajout de la persistance : **58/58**. Preuves : `/tmp/diff-3-r3-1-{rouge,vert}.{log,json}` et `/tmp/diff-3-r3-1-persistance-{rouge,vert}.{log,json}`.

### Constat 2, P1 : bascule après acquittement

Quatre cas `R3.2` ajoutés dans le même fichier, tous rouges seuls avant correction : message/recherche, événement suivant/exception du flux, avec un texte sans ponctuation encore en tampon.

```text
AssertionError: expected '' to be 'Texte encore en tampon\n\n*(interromp…' // Object.is equality
AssertionError: expected 'Texte encore en tampon' to be 'Texte encore en tampon\n\n*(interromp…' // Object.is equality
```

Lors de la détection de la bascule, le message d'origine reçoit le texte accumulé et la mention `*(interrompu)*`, avec `isStreaming: false`, avant l'abandon du flux. Le minuteur est arrêté ; une navigation reçue dans ce flux est abandonnée aussi. Le même traitement couvre une exception après bascule. Le brouillon et les messages de la conversation affichée restent intacts.

Appelants relus : action « Voir » dans `actionsStore`, `loadConversation`, mise à jour des messages par identifiant dans toutes les conversations, arrêt et gestion des erreurs. Groupe voisin : **39/39**. Preuves : `/tmp/diff-3-r3-2-{rouge,vert}.{log,json}`.

### Constat 3, P2 : finalité recalculée après accord mémoire

Trois cas `R3.3` ajoutés : changements `llm → documents` et `documents → llm` après accord mémoire, puis témoin où l'accord mémoire porte légitimement une autre finalité que la demande inchangée. Exécutés seuls avant correction : **2 échecs, 1 passé**. Les tests `R2.3` sur l'accord initial sont conservés sans modification.

```text
AssertionError: expected "vi.fn()" to be called 1 times, but got 2 times
```

`requestPurpose` conserve la finalité calculée avant l'accord, indépendamment de `purpose`, qui peut venir de la demande d'accord mémoire. Les deux résolutions de la demande sont comparées. Un changement suspend la reprise et explique qu'il faut confirmer à nouveau ; l'envoi explicite suivant propose l'accord adapté, puis reprend la même source serveur sans doublon utilisateur. Une finalité mémoire distincte reste transmise quand la demande n'a pas changé.

Appelants relus : accord initial, confirmation différée, réception de `memory_consent_required`, reprise par `resume_message_id`, contrat de `memory_card_purpose` et garde documentaire du moteur. Groupe voisin : **82/82**. Preuves : `/tmp/diff-3-r3-3-{rouge,vert}.{log,json}`.

### Constat 4, P2 : priorité clavier et ouverture tardive du projet

Deux cas `R3.4` ajoutés à `CloudConsentDialog.empilement.c20r1.test.tsx`, avec le vrai `ProjectModal` et les classes Tailwind compilées, accord disponible ou occupé. Ils ouvrent le projet après l'accord et vérifient le focus, l'isolation, Tab, Maj+Tab et Échap. Les deux échouaient seuls avant correction :

```text
Error: expect(element).toHaveFocus()
```

Le champ du projet recevait le focus. La pile conserve maintenant les éléments des dialogues : le focus initial et le pilotage clavier suivent leur ordre visuel, avec le même comparateur de couche et d'ordre DOM que l'isolation. Une fenêtre inscrite plus tard mais située derrière ne prend plus la priorité.

Appelants relus : `CloudConsentDialog`, `ProjectModal`, pièges imbriqués et panneaux sans piégeage clavier. Les tests des deux ordres d'ouverture, du hook, du projet et de l'Atelier passent : **117/117**. Preuves : `/tmp/diff-3-r3-4-{rouge,vert}.{log,json}`.

### Constat 5, P2 : sélection native pendant l'accord

Un cas `R3.5` suspend le vrai parcours du sélecteur natif simulé pendant une réponse, fait arriver l'accord mémoire, puis rend la sélection. Rouge seul avant correction :

```text
AssertionError: expected [] to deeply equal ArrayContaining{…}
```

Le callback commun signale maintenant « Fichier à sélectionner à nouveau » et invite à terminer l'accord avant de sélectionner de nouveau le fichier. La sélection ne modifie pas la demande sous accord. Le test vérifie également l'absence d'indexation ou d'envoi du fichier, puis la réussite d'une nouvelle sélection après l'accord.

Appelants relus : sélecteur natif, entrée navigateur, dépôt Tauri désactivé sous la modale, indexation et affichage des notifications. Groupe voisin : **37/37**. Preuves : `/tmp/diff-3-r3-5-{rouge,vert}.{log,json}`.

Ces cinq constats ajoutent **16 cas frontend**, dont **15 rouges constatés avant correction et un témoin de comportement à conserver**. Aucun test existant n'a été affaibli.

### Constat 6, P2 : apports du lot bancs absents

La référence locale `c20/integration` valait `a498d9d3` à l'entrée. `git rev-list --left-right --count c20/integration...HEAD` donnait `6 6`, malgré l'annonce d'un arbre déjà rebasé. Les six commits absents sont `62c9f998`, `c82f199c`, `6c4609e5`, `16a025b3`, `d57e9d40`, `a498d9d3`.

Les deux fichiers B-1851/B-1852 ont été rétablis d'abord, puis leurs **7 contre-épreuves** exécutées seules sans les corrections : **7 échecs**, XML parsé et relu. Chacune présentait cette ligne :

```text
Failed: DID NOT RAISE <class 'AssertionError'>
```

Le contenu des **24 fichiers** de ces six commits a ensuite été reporté dans l'arbre de travail. Ils sont identiques octet pour octet à `a498d9d3`, y compris le bilan du lot bancs. La frontière exige de nouveau un événement d'erreur et contrôle récursivement tous les champs ; les contre-épreuves d'attribution et les autres corrections du lot sont restaurées intégralement. Les apports de diff-3 sont conservés. Appelants relus : frontière des fournisseurs, attribution du chat, clôture des Actions, persistance différée, garde des parcours et recette à faux curl.

**Limite d'historique : aucun rebase Git effectué.** Le répertoire Git est protégé en écriture et la consigne interdit de modifier les commits ou l'index. L'orchestrateur devra rebaser l'historique avant son commit. Pendant cette intervention, la référence partagée a encore avancé jusqu'à `c127023a` avec quatre commits du lot instrument ; ceux-ci ne font pas partie des six commits bancs visés par cette relecture. Cette passe reste limitée aux constats reçus et à la référence d'entrée `a498d9d3`.

Preuve rouge : `/tmp/diff-3-r3-6-rouge.{log,xml}`. Les vérifications finales reprennent les fichiers B-1851/B-1852 entiers et leurs voisins.

### Conditions des portes de la passe 3

Le lanceur Pytest standard s'est arrêté de progresser après 14 cas, sans XML final, à l'entrée des tests utilisant le client asynchrone. Il a été interrompu. Une sonde `asyncio.run(asyncio.to_thread(...))` indépendante a également dépassé cinq secondes. Comme à la passe 2, `/tmp/diff-3-r3-polling/sitecustomize.py` borne l'attente d'`EpollSelector.select` à 1 ms pour pallier le réveil local interdit ; la même sonde termine alors. Aucun test, fixture, assertion ni code de production n'est remplacé par ce lanceur.

La première porte avec ce lanceur comptait **123 passés et 1 échec de dépendance** (`test_b2029_couverture.py`) ; Vitest avait **396 assertions passées et 1 fichier non chargé** (`b1854-garde-parcours.test.ts`). Il manquait `@playwright/test`. Ses archives et celles de `playwright` et `playwright-core`, version **1.58.2**, ont été lues dans le cache npm local et extraites uniquement dans le `node_modules` ignoré de cet arbre. Aucun téléchargement, script d'installation ou navigateur lancé. Le test B-2029 seul repasse ensuite (**1/1**, XML relu), et les deux portes ciblées sont rejouées avec cette dépendance disponible.

Les tests de garde simulent les URL : aucun port interdit n'est contacté. Le fichier Node est lancé uniquement sur le test de garde concerné ; les parcours navigateur et les cas utilisant des chemins hors du périmètre autorisé ne sont pas lancés. Le lanceur Node utilise `--experimental-test-isolation=none` pour éviter le canal de communication entre processus interdit dans ce bac.

### Portes finales de la passe 3

| Porte | Résultat |
| --- | --- |
| Pytest ciblé | **124/124 dans 15 fichiers**, 0 échec, 0 erreur, 0 ignoré ; `/tmp/diff-3-r3.xml` parsé et relu |
| Garde hors réseau du processus Pytest | **0 tentative de connexion** |
| Vitest ciblé et voisins | **398/398 dans 95 fichiers**, dont les 16 nouveaux cas ; 0 échec, 0 ignoré ; sortie 0, `success: true` |
| Garde Node de couverture | **1/1**, cas nommé dans le TAP, sans navigateur |
| Ruff | Sortie 0, `All checks passed!` |
| TypeScript | Sortie 0, aucun diagnostic |
| ESLint | Sortie 0, **0 erreur, 27 avertissements existants**, aucune correction de lint étrangère au lot |
| Diff, index et HEAD | `git diff --check` sans défaut ; index inchangé ; HEAD toujours `c84748159b50ff04edba225653600e7279012966` |

Les quatre cas Ollama et la recette `.deb` cités comme rouges connus passent avec les corrections restaurées du lot bancs. Les tests de bac à sable B-1153/B-1191 ne font pas partie de la sélection. **Aucun rouge restant dans les portes exécutées.** Les décomptes finaux ne cumulent pas les rejeux intermédiaires.

Commandes backend, depuis la racine :

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/diff-3-r3-polling \
  OLLAMA_BASE_URL=http://127.0.0.1:9 THERESE_DATA_DIR=/tmp/diff-3-r3-data \
  .venv/bin/python -m pytest \
  tests/test_b1851_preuve_frontiere.py tests/test_b1852_preuve_attribution.py \
  tests/test_frontiere_erreurs.py tests/test_pluriel_fournisseur.py \
  tests/test_lot14_frontiere_erreurs.py tests/test_actions_traitement.py \
  tests/test_b2033_charges.py tests/test_r3_4_ollama.py tests/test_b1806_banc_ollama.py \
  tests/test_securite_f2_recette_deb.py tests/test_b1807_recette_deb.py \
  tests/test_b2029_couverture.py tests/test_t4_consentement_moteur.py \
  tests/test_r2_2_protection.py tests/test_r2_3_outil.py \
  -q -p no:cacheprovider -p tests.bancs_sans_reseau --timeout=120 \
  --junitxml=/tmp/diff-3-r3.xml
RUFF_CACHE_DIR=/tmp/diff-3-r3-ruff-cache .venv/bin/python -m ruff check --no-fix src/backend tests
node --experimental-test-isolation=none --test \
  --test-name-pattern='^la garde autorise les lectures' tests/couverture/couverture-ecran.test.mjs
```

Commande frontend depuis `src/frontend` ; les options du chargeur évitent les écritures dans les dépendances partagées :

```sh
npm_config_offline=true VITE_THERESE_BACKEND_PORT=9 npx vitest run \
  src/components/chat/ChatInput*.test.tsx src/components/shared/CloudConsentDialog*.test.tsx \
  src/hooks/useDialogFocusTrap*.test.tsx src/hooks/useFileDrop*.test.ts src/hooks/useFileDrop*.test.tsx \
  src/components/memory/ProjectModal*.test.tsx src/components/ui/DialogShell*.test.tsx \
  src/components/atelier/AgentSession*.test.tsx src/components/calendar/CalendarPanel*.test.tsx \
  src/components/chat/MessageBubble*.test.tsx src/lib/chatPersistence*.test.ts \
  src/lib/debouncedStorage*.test.ts src/lib/consent*.test.ts src/stores/chatStore*.test.ts \
  src/stores/actionsStore.resultatDansUneConversation.test.ts src/test/b1854-garde-parcours.test.ts \
  --maxWorkers=3 --no-cache --configLoader runner \
  --reporter=json --outputFile=/tmp/diff-3-r3-vitest.json
npm_config_offline=true npx tsc --noEmit
npm_config_offline=true npm run lint
```

Résultats finaux effectivement relus : `/tmp/diff-3-r3.xml`, `/tmp/diff-3-r3-pytest.log`, `/tmp/diff-3-r3-vitest.json`, `/tmp/diff-3-r3-node.log`, `/tmp/diff-3-r3-ruff.log`, `/tmp/diff-3-r3-tsc.log`, `/tmp/diff-3-r3-lint.log`. Aucun lancement de suite complète, aucun réseau ni fournisseur LLM, aucun serveur, aucun usage de `~/.therese` ou de `.app-loop/`, aucune commande `rm`. Tous les changements destinés à l'orchestrateur restent non commités.

## Remédiation de la relecture, passe 4

Intervention du 17 novembre 2026 dans le seul arbre `gpt-c20-diff-3`, branche `gpt/c20-diff-3`. HEAD reçu : `c731e992ec36b409107b187f7bc3c1eff9ba1816`. Référence locale `c20/integration` : `5e1ca36cb43b2666d9a569e4c2e7160af5225366`. Les fichiers suivis étaient propres ; les liens `.venv` et `src/frontend/node_modules` étaient déjà non suivis.

### Décision pour chacun des huit constats

**Option (b) pour les huit constats : retrait complet de B-2020 et de ses remédiations.** Le candidat ne se limite plus au clavier de l’accord : ses modifications coordonnent le composeur, la file, l’identité des conversations, les accords et la pile des modales. Les défauts confirmés demandent notamment de définir l’ordre des reprises et de gérer deux états distincts de saisie. Aucun correctif simple et prouvé ne couvre cet ensemble. La règle de la quatrième passe conduit donc au retrait du candidat entier, y compris pour les défauts de focus ; aucun sous-correctif de B-2020 n’est conservé. B-2016 et B-2021 restent inchangés.

| Constat | Issue | Preuve du relecteur rejouée avant retrait |
| --- | --- | --- |
| 1, P1 | **(b)** `regle_a_trancher`<br>retiré du lot, reporté | Message mis en file dans A, `loadConversation('B')` comme l’action « Voir », puis arrêt du flux A : second envoi dans B et brouillon enregistré de B supprimé. |
| 2, P1 | **(b)** `regle_a_trancher`<br>retiré du lot, reporté | Nouveau texte saisi avant le premier événement `memory_consent_required` : le champ reprend la demande précédente, même après confirmation. |
| 3, P1 | **(b)** `regle_a_trancher`<br>retiré du lot, reporté | Seconde demande en file avant l’accord mémoire : le second appel part alors que l’accord est affiché, sans décision. |
| 4, P1 | **(b)** `regle_a_trancher`<br>retiré du lot, reporté | Deux cas : saisie A → B → A, puis retrait et nouvel ajout de `A.png` avant acquittement ; le nouveau texte ou la nouvelle pièce disparaît. |
| 5, P1 | **(b)** `regle_a_trancher`<br>retiré du lot, reporté | Action de navigation reçue pour A, passage à B puis fin normale de l’itérateur SSE sans autre événement : l’événement de navigation est exécuté. |
| 6, P1 | **(b)** `regle_a_trancher`<br>retiré du lot, reporté | Vrai `DialogShell` en `relative z-10` dans un parent modal `fixed z-50` : focus derrière l’aide et Échap reçu par le parent. |
| 7, P1 | **(b)** `regle_a_trancher`<br>retiré du lot, reporté | Une modale avec `isolateBackground: true` s’ouvre derrière le vrai accord porté dans `body` : l’`alertdialog` devient inerte, `aria-hidden` et perd le focus. |
| 8, P2 | **(b)** `regle_a_trancher`<br>retiré du lot, reporté | Vrai `ProjectModal` ouvert après l’accord : après fermeture effective de celui-ci, le projet est visible mais le focus reste sur le déclencheur du fond. |

Le retrait ne résout pas les défauts présents dans l’état d’intégration ; il reporte le candidat avec ces preuves, conformément à l’option (b). Aucun constat n’est rejeté comme faux ou écarté pour appartenance à un autre lot. Aucun fichier d’un autre lot n’est repris.

### Tests écrits et rouges observés avant retrait

Les tests R4 ont été ajoutés aux deux fichiers de test de B-2020, avant toute modification de production. Chaque constat a été exécuté séparément par `-t '^R4\.<numéro> :'`, dans un processus Vitest distinct, `--maxWorkers=3 --no-cache --configLoader runner`. Le constat 4 comprend deux cas. Résultat : **9 tests exécutés, 9 échecs reproduisant les constats**, sans test existant modifié ni affaibli pendant cette reproduction. Les autres cas des fichiers étaient exclus par le filtre.

Sources complètes conservées avant retrait :

- `/tmp/diff-3-r4-reproductions/ChatInput.accordAttentes.c20r2.test.tsx` : R4.1 à R4.5 ;
- `/tmp/diff-3-r4-reproductions/CloudConsentDialog.empilement.c20r1.test.tsx` : R4.6 à R4.8.

Ces sources utilisent les vrais composants et hooks ; les échanges serveur et Tauri sont simulés en mémoire. Le scénario 6 utilise le vrai `DialogShell` et un parent reprenant les options d’isolation et le positionnement de `SettingsModal`. Les classes Tailwind sont compilées en mémoire. Le scénario 8 utilise le vrai `ProjectModal`, avec `listContacts` simulé.

Lignes d’échec recopiées depuis les rapports, avant retrait :

```text
R4.1 : la file de A ne part pas dans B après le chargement Voir puis l’arrêt
AssertionError: expected "vi.fn()" to be called 1 times, but got 2 times
AssertionError: expected null to be 'Brouillon enregistré de B' // Object.is equality

R4.2 : le premier événement d’accord mémoire conserve le brouillon suivant
Error: expect(element).toHaveValue(Brouillon suivant)

R4.3 : la file attend la décision mémoire puis reprend après la première demande
AssertionError: expected "vi.fn()" to be called 1 times, but got 2 times

R4.4 : un nouvel ajout identique reste après acquittement (texte)
Error: expect(element).toHaveValue(Demande fictive A)
R4.4 : un nouvel ajout identique reste après acquittement (pièce)
Error: expect(received).toBeInTheDocument()

R4.5 : la fermeture normale sans événement après bascule abandonne la navigation
AssertionError: expected "vi.fn()" to not be called at all, but actually been called 1 times

R4.6 : le vrai DialogShell imbriqué garde le focus et Échap devant son parent
Error: expect(element).toHaveFocus()
AssertionError: expected "vi.fn()" to be called 1 times, but got 0 times

R4.7 : une modale isolante tardive épargne l’alertdialog au-dessus
AssertionError: expected <div …(3)><div …(5)>…(3)</div></div> to be null
Error: expect(element).toHaveFocus()

R4.8 : le vrai ProjectModal récupère le focus à la fermeture de l’accord
Error: expect(element).toContainElement(element)
```

Preuves : `/tmp/diff-3-r4-{1,2,3,4,5,6,7,8}-rouge.log` et les huit rapports `.json`, tous relus. Les tests du candidat, reproductions comprises, quittent ensuite le lot avec son code de production : ils ne sont pas comptés dans la porte verte de l’état final.

### Retrait et relecture des appelants

Le retrait applique **l’inverse des seuls hunks de diff-3** sur les 16 chemins de B-2020, après `git apply --reverse --check`. Aucun fichier n’a été recopié depuis `c20/integration`, aucun rebase ni changement de l’index effectué. La liste des chemins est conservée dans `/tmp/diff-3-r4-b2020-fichiers.txt` et l’écart annulé dans `/tmp/diff-3-r4-b2020-ecart.patch`.

Les huit fichiers de production revenus à l’intégration sont `AgentSession.tsx`, `ChatInput.tsx`, `SlashCommandsMenu.tsx`, `CloudConsentDialog.tsx`, `useDialogFocusTrap.ts`, `useKeyboardShortcuts.ts`, `chatStore.ts` et `z-layers.ts`. Les trois tests préexistants `AgentSession.accordMoteur.test.tsx`, `AgentSession.consentement.t4.test.tsx` et `ChatInput.rattachement.test.tsx` retrouvent exactement leur contenu d’intégration. Les cinq fichiers de tests créés pour B-2020 sont retirés : `ChatInput.accordAttentes.c20r2.test.tsx`, `ChatInput.accordContexte.c20r1.test.tsx`, `SlashCommandsMenu.modale.c20r2.test.tsx`, `CloudConsentDialog.clavier.c20.test.tsx` et `CloudConsentDialog.empilement.c20r1.test.tsx`.

Vérification après retrait : `git diff --exit-code c20/integration -- <les 16 chemins>` réussit, sans sortie. L’écart du lot avec l’intégration se limite désormais au bilan, à `Aide.tsx` et son test B-2016, ainsi qu’à `AgentMemoryPanel.tsx` et son test B-2021.

Appelants relus après retrait : rendu et confirmation de l’accord dans `ChatInput` et `AgentSession`, reprise mémoire et file, références de l’identité dans le store, raccourcis et menu slash, usage du hook par `DialogShell` et `ProjectModal`. Les options et propriétés supprimées avec le candidat ne laissent pas de référence résiduelle dans ces appelants. Les tests voisins couvrent ces parcours, l’autosauvegarde, la synchronisation des conversations, la navigation et les deux candidats conservés.

### Portes de la passe 4

| Porte | Résultat final |
| --- | --- |
| Pytest ciblé | **18/18 dans 3 fichiers**, 0 échec, 0 erreur, 0 ignoré ; `/tmp/diff-3-r4.xml` parsé et ses 18 cas effectivement relus |
| Garde hors réseau de Pytest | **0 tentative de connexion** |
| Vitest ciblé et voisins | **318/318 dans 89 fichiers**, 0 échec, 0 ignoré ; rapport JSON relu, `success: true`, sortie 0 |
| Ruff | Sortie 0, `All checks passed!` |
| TypeScript | Sortie 0, aucun diagnostic |
| ESLint | Sortie 0, **0 erreur, 27 avertissements existants** ; aucune correction étrangère au périmètre |
| Retrait de B-2020 | **16/16 chemins sans écart avec `c20/integration`**, production et tests |
| Diff, index et HEAD | `git diff --check` sans défaut, index inchangé, HEAD toujours `c731e992ec36b409107b187f7bc3c1eff9ba1816` |

Le lancement Pytest standard n’a produit aucun résultat ni XML et a été interrompu (sortie 130). Une sonde indépendante `asyncio.run(asyncio.to_thread(...))`, bornée à six secondes, a expiré elle aussi (sortie 124). Le lanceur temporaire `/tmp/diff-3-r4-polling/sitecustomize.py` borne `EpollSelector.select` à 1 ms ; la même sonde termine alors (sortie 0). Ce contournement du réveil système bloqué, déjà rencontré aux passes précédentes, ne remplace aucune assertion, fixture ou fonction de production. Seul le rejeu terminé avec XML est compté dans la porte Pytest.

Commandes backend depuis la racine ; Ruff a été lancé après la lecture du XML :

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/diff-3-r4-polling \
  OLLAMA_BASE_URL=http://127.0.0.1:9 THERESE_DATA_DIR=/tmp/diff-3-r4-data \
  .venv/bin/python -m pytest \
  tests/test_t4_consentement_moteur.py tests/test_r2_2_protection.py tests/test_r2_3_outil.py \
  -q -p no:cacheprovider -p tests.bancs_sans_reseau --timeout=120 \
  --junitxml=/tmp/diff-3-r4.xml
RUFF_CACHE_DIR=/tmp/diff-3-r4-ruff-cache .venv/bin/python -m ruff check --no-fix src/backend tests
```

Commandes frontend depuis `src/frontend`, avec dépendances locales et chargeur évitant les écritures dans le `node_modules` partagé :

```sh
npm_config_offline=true VITE_THERESE_BACKEND_PORT=9 npx vitest run \
  src/components/chat/ChatInput*.test.tsx src/components/chat/SlashCommandsMenu*.test.tsx \
  src/components/atelier/AgentSession*.test.tsx src/components/memory/ProjectModal*.test.tsx \
  src/hooks/useDialogFocusTrap*.test.tsx src/hooks/useKeyboardShortcuts*.test.ts \
  src/hooks/useKeyboardShortcuts*.test.tsx src/hooks/useAutosave*.test.ts \
  src/hooks/useConversationSync*.test.ts src/hooks/useConversationSync*.test.tsx \
  src/stores/chatStore*.test.ts src/lib/clientActions.test.ts \
  src/lib/identiteConversation.test.ts src/lib/rattachementConversation.test.ts \
  src/components/Aide*.test.tsx src/components/prototype/Aide.palette.test.tsx \
  src/components/memory/AgentMemoryPanel*.test.tsx \
  --maxWorkers=3 --no-cache --configLoader runner \
  --reporter=default --reporter=json --outputFile=/tmp/diff-3-r4-vitest.json
npm_config_offline=true npx tsc --noEmit
npm_config_offline=true npm run lint
```

**Aucun rouge restant dans les portes de l’état livré.** Les neuf rouges de reproduction sont des preuves du candidat retiré, pas des tests laissés en échec dans le lot. Aucun rouge connu de l’orchestrateur n’est inclus dans cette sélection. Les rapports finaux relus sont `/tmp/diff-3-r4.xml`, `/tmp/diff-3-r4-pytest.log`, `/tmp/diff-3-r4-vitest.json`, `/tmp/diff-3-r4-vitest.log`, `/tmp/diff-3-r4-ruff.log`, `/tmp/diff-3-r4-tsc.log` et `/tmp/diff-3-r4-lint.log`.

Aucune suite complète, aucun réseau ni fournisseur LLM, aucun serveur ou port interdit, aucun usage de `~/.therese` ni de `.app-loop/`, aucune commande `rm`. Aucun commit, `git add`, dépôt annexe, bundle ou rebase. Les modifications de retrait et le bilan restent non commités pour l’orchestrateur.
