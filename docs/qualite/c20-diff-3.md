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

L’isolation du fond a fait échouer trois tests existants de l’Atelier pendant la mise au point : `annuler ou ne pas obtenir l’acquittement bloque et explique le refus`, `ne démarre pas après profil pendant l’acquittement` et `ne démarre pas après destination pendant l’acquittement`, avec `Error: Unable to find role="alert"`. L’erreur d’enregistrement se trouvait hors de la fenêtre. Elle est maintenant transmise au dialogue et affichée à l’intérieur ; après fermeture, elle reste dans la vue. Aucun de ces tests n’a été affaibli. L’assertion nouvelle d’isolation examine l’ancêtre inerte du déclencheur, puisque le portail isole le conteneur de l’application.

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
