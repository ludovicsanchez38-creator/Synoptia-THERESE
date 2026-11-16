# Cycle 20, lot diff-3

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
| B-2020 | `confirme` | `src/frontend/src/components/shared/CloudConsentDialog.clavier.c20.test.tsx::B-2020 : place le focus sur Annuler et isole le fond du dialogue modal` ; trois autres cas clavier dans ce fichier | `Error: expect(element).toHaveFocus()` ; `AssertionError: expected "vi.fn()" to be called 1 times, but got 0 times` | non commité |
| B-2021 | `confirme` | `src/frontend/src/components/memory/AgentMemoryPanel.origineVide.c20.test.tsx::B-2021 : distingue une recherche par origine sans résultat de la mémoire vide (%s)` | `Error: Unable to find an element with the text: Aucune fiche ne correspond à ta recherche.. This could be because the text is broken up by multiple elements. In this case, you can provide a function for your text matcher to make your matcher more flexible.` | non commité |
| B-2022 | `rejete` | `src/frontend/src/lib/catalogueModeles.openrouter.r19b.test.ts::retire le préfixe des modèles du catalogue et conserve les inconnus` et `::B-1097 : decorer formate aussi le modèle absent du catalogue %s` | Sans objet : nom dérivé d’un identifiant fictif, conforme au contrat existant | Sans objet |

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
