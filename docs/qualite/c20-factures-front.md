# Cycle 20, lot factures-front

Branche `grok/c20-factures-front`, base `cd287fb3` (v0.83.0-alpha, merge PR #108).
Chaque candidat confirmé a d'abord un test de comportement rouge, commité seul, puis le plus petit correctif.

Aucune règle métier n'est restée ouverte : pas de `regle_a_trancher`.

## Verdicts

| id | verdict | test | commit du rouge | commit du correctif |
| --- | --- | --- | --- | --- |
| B-1864 | confirme | `src/frontend/src/components/invoices/InvoiceForm.actionsRapides.b1864.test.tsx::Marquer comme payée confirme 300,00 € et enregistre le prix avant le paiement` | `5a0a212c` | `406caf36` |
| B-1865 | confirme | `src/frontend/src/components/invoices/InvoiceForm.origineAutreClient.b1865.test.tsx::envoie un avoir sans la facture de l’ancien client` | `0221e28d` | `2ee6dc24` |
| B-1866 | confirme | `src/frontend/src/components/invoices/InvoicesPanel.fermetureSaisie.b1866.test.tsx::Fermer pose la question et garde la saisie` | `fba1dfc6` | `1f450538` |
| B-1867 | rejete | `src/frontend/src/components/prototype/InvoiceConversationCard.test.tsx::demande confirmation et ignore un double clic avant de créer le devis brouillon` | aucun | aucun |
| B-1977 | rejete | `src/frontend/src/styles/globals.css:443-461` et `src/frontend/src/hooks/useAccessibilityRoot.test.tsx` | aucun | aucun |
| B-1978 | confirme | `src/frontend/src/components/atelier/AgentSession.placeholder.b1978.test.tsx::demande de décrire la tâche` | `a15c5aac` | `085cb292` |
| B-1979 | confirme | `src/frontend/src/components/atelier/SessionList.accents.b1979.test.tsx::rafraîchir, nouvelle tâche et lancer une tâche portent les accents` | `c226e081` | `dc8664c3` |
| B-1980 | confirme | `src/frontend/src/components/invoices/InvoicesPanel.nomDialogue.b1980.test.tsx::le dialogue s’appelle Devis et factures` | `59c09bf0` | `e4e66b46` |
| B-1981 | confirme | `src/frontend/src/components/invoices/InvoiceForm.focusConversion.b1981.test.tsx::Tab depuis Convertir reste dans le dialogue` | `31b75051` | `7e06235e` |
| B-1982 | confirme | `src/frontend/src/components/invoices/InvoicesPanel.squelette.b1982.test.tsx::compte autant de cases que d’en-têtes` | `b8f6b4df` | `e4d0fe1c`, puis `f68a869c` |
| B-1983 | confirme | `src/frontend/src/components/prototype/InvoiceConversationCard.legendes.b1983.test.tsx::affiche Qté et Prix HT hors de l’en-tête masqué` | `a7acd2b3` | `3a329c35` |
| B-1984 | confirme | `src/frontend/src/components/prototype/InvoiceConversationCard.miseAJour.b1984.test.tsx::distingue la création et la mise à jour` | `16cf69bb` | `dd980ea2` |
| B-1985 | confirme | `src/frontend/src/components/prototype/InvoiceConversationCard.apercu.b1985.test.tsx::annonce les six lignes visibles quand il y en a davantage` | `9ab2e5d7` | `c2b360da` |
| B-1986 | confirme | `src/frontend/src/components/onboarding/SecurityStep.phrase.b1986.test.tsx::accepte l’envoi de ces données, pas seulement des messages` | `0628929f` | `66a7f107`, puis `e29ad984` |
| B-1987 | rejete | `tests/test_routers_invoices.py::TestInvoicesCRUD::test_delete_invoice` | aucun | aucun |

Le fichier B-1864 contient aussi : `%s confirme le montant saisi et l’enregistre avant le statut` (Accepter, Refuser), `Convertir enregistre le prix saisi avant de créer la facture`, `une sauvegarde refusée empêche de marquer payée`, `une ligne vidée n’ouvre pas la confirmation de paiement`.

Le fichier B-1866 contient aussi `le fond pose la question et garde la saisie` et `un formulaire intact se ferme avec le panneau`.

## Rejets

B-1867. Les deux fieldset de `InvoiceConversationCard.tsx` (lignes 564 et 602) portent `disabled={confirmationSnapshot !== null}`. Le test existant, lignes 174 à 176, attend `toBeDisabled` sur le client, la description et le prix, et il est vert : jsdom applique `disabled` malgré la classe Tailwind `contents`. Aucun test de comportement rouge n'a pu être écrit dans ce moteur. L'incertitude restante est celle des navigateurs, où un fieldset en `display: contents` peut laisser les contrôles actifs. `BoardConversationCard.tsx` garde le même motif.

B-1977. La pastille de `SessionList.tsx:236` garde `animate-pulse`. `globals.css:443-461` force `animation-duration: 0.01ms` et `animation-iteration-count: 1` sous `prefers-reduced-motion: reduce` et sous `html[data-reduce-motion="true"]`. `useAccessibilityRoot` pose cet attribut (test du hook). La barre de progression est déjà masquée quand `reduceMotion` est vrai (`SessionList.tsx:262`).

B-1987. `delete_invoice` (`src/backend/app/routers/invoices.py:1027`) renvoie `Invoice deleted successfully`, et `tests/test_routers_invoices.py:392` exige `deleted` ou `successfully`. `confirmDeleteInvoice` (`InvoicesPanel.tsx:194`) ignore ce retour. Aucune notification de succès n'est affichée. Seul le `catch` (lignes 200 à 211) montre une phrase, et elle vient de `error.message` ou du repli français. L'anglais du succès n'atteint pas l'écran. L'API et le pytest restent en place.

## Tests voisins alignés, sans les affaiblir

`InvoicesPanel.da.test.tsx` figeait `grid-cols-7` et sept barres, soit la colonne en trop de B-1982. `f68a869c` le passe à six pistes. Le reste du cas (un seul Réessayer, trois vides distincts) est inchangé.

`SecurityStep.test.tsx`, dans `66a7f107`, ne cherche plus la seule formule « messages et le contexte utile ». Il exige encore `mes messages, le contexte utile`, et aussi `ces données soient envoyées à OpenAI`.

`SecurityStep.consentement.test.tsx`, dans `e29ad984`, accorde « envoyées » au féminin de « ces données ». L'espace exigé par B-242 entre le nom du fournisseur et « pour » reste, ainsi que l'interdiction de `Mistralpour` et `Anthropicpour`.

`InvoiceConversationCard.retoucheSansDoublon.b1412.test.tsx`, dans `dd980ea2`, clique « Confirmer la mise à jour » au second passage. L'assertion d'identifiant de la facture reste.

## Portée d'exécution

`InvoicesPanel` est monté en production par `PrototypeUnifiedViewCanvas.tsx:97` avec `standalone`. Le mode modal (`standalone` faux, défaut du composant) reste du code vivant du même fichier. Le correctif de fermeture s'y applique. La coque actuelle n'ouvre pas ce modal.

`InvoiceForm` est rendu par `InvoicesPanel`. `InvoiceConversationCard` est atteint par `ConversationCanvasPrototype.tsx`. `SecurityStep` est monté par `OnboardingWizard`. `AgentSession` est monté par `AtelierPanel`.

`SessionList` est exporté par `src/frontend/src/components/atelier/index.ts` et couvert par ses tests. Aucun écran de production ne l'importe. Les accents de B-1979 sont ceux du composant canonique.

Le formulaire d'avoir remet `factureOrigineId` à vide quand le client change (B-1865). Le contrôle serveur de la facture d'origine ne vérifie pas que cette facture appartient au client envoyé. Un autre client d'API peut encore transmettre un `converted_from_id` d'un autre client.

## Portes

Mesurées dans cet arbre, après les correctifs et l'alignement des tests voisins. `.venv` et `node_modules` sont les liens vers le dépôt principal.

Pytest (`OLLAMA_BASE_URL=http://127.0.0.1:9`, `tests/` hors `tests/e2e`, junit `/tmp/factures-front-pytest.xml`) : 6606 tests, 6549 passés, 6 échecs, 0 erreur, 51 ignorés.

Échecs :

- `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[True-True]`
- `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[True-False]`
- `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[False-True]`
- `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[False-False]`
- `tests.test_securite_f2_recette_deb::test_la_recette_deb_lit_son_fichier_prive_pour_creer_un_document`
- `tests.test_typage_lot_confidentialite::test_les_quatre_diagnostics_du_lot_confidentialite_ne_reviennent_pas`

Les cinq premiers sont la référence connue de cette machine, antérieure au lot. Le sixième vient de la colorisation mypy : la session injecte `FORCE_COLOR`, donc la chaîne attendue ` error:` n'est plus contiguë. Rejoué seul sans `FORCE_COLOR` ni `NO_COLOR`, il passe. Aucun fichier backend n'a été modifié par le lot.

Ruff (`src/backend` et `tests`, `--no-fix`) : tout passe.

Vitest (`npm run test -- --run` depuis la racine, 15:17) : 935 fichiers passés, 4052 tests passés, 0 échec.

TypeScript (`npx tsc --noEmit` depuis `src/frontend`) : sortie vide, succès. Le `tsc` lancé par erreur à la racine du dépôt n'est pas le compilateur du frontend.

ESLint (`npm run lint`, seuil `--max-warnings 27`) : 0 erreur, 27 avertissements, succès. L'avertissement `loadInvoices` de `InvoicesPanel` est antérieur au lot.
