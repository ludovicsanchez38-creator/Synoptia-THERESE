# Cycle 20, lot front-chat

Branche `grok/c20-front-chat`, base `cd287fb3` (v0.83.0-alpha). Chaque `confirme` a un test de comportement rouge, commité seul, puis le plus petit correctif. Rien n'a été poussé.

## Verdicts

| id | verdict | test (chemin::nom) | commit du rouge | commit du correctif |
| --- | --- | --- | --- | --- |
| B-1837 | confirme | `src/frontend/src/components/chat/ChatInput.memoirePieces.b1837.test.tsx`::`remet les fichiers dans le champ et les renvoie avec la reprise` | `51cf8d17` | `2c8e1042` |
| B-1838 | confirme | `src/frontend/src/components/email/EmailCompose.delai.b1838.test.tsx`::`abandonne l’appel encore en cours au bout de 35 s et garde le brouillon` ; `…`::`désarme le délai quand l’envoi finit avant lui` | `56aa62f0` | `9fec62cc` |
| B-1917 | confirme | `src/frontend/src/components/chat/EntitySuggestion.survol.b1917.test.tsx`::`B-1917 : Tout ignorer change de couleur au survol` | `e02c6040` | `2a367112` |
| B-1918 | confirme | `src/frontend/src/components/chat/MessageBubble.prose.b1918.test.tsx`::`B-1918 : le paragraphe suit l’encre de la charte et le bandeau de code reste sombre` | `ddc90289` | `68c8d2d9` |
| B-1919 | confirme | `src/frontend/src/components/chat/MessageBubble.noms.b1919.test.tsx`::`B-1919 : Enregistrer l'image et Copier l'image ont un aria-label` ; `…`::`B-1919 : Copier le message a un aria-label` | `35e3d885` | `87553ab1` |
| B-1920 | confirme | `src/frontend/src/components/chat/PanelContainer.repli.b1920.test.tsx`::`B-1920 : le repli des panneaux annonce le chargement` | `9af2a071` | `d8b0ea9a` |
| B-1921 | rejete | Preuve déjà en place : `src/frontend/src/components/crm/CRMPanel.tsx` lignes 180-181, même accord que `src/frontend/src/components/files/FileBrowser.tsx` lignes 553-554 et `src/frontend/src/components/files/FileBrowser.compteAccentue.b1450.test.tsx`::`dit « 0 élément »` | aucun | aucun |
| B-1922 | confirme | `src/frontend/src/components/crm/CRMPanel.focus.b1922.test.tsx`::`B-1922 : Nouveau contact prend le focus et le garde` ; `…`::`B-1922 : Nouvelle activité prend le focus et le garde` | `7c57f13c` | `b84c712d` |
| B-1923 | regle_a_trancher | aucun | aucun | aucun |
| B-1924 | confirme | `src/frontend/src/components/email/EmailDetail.etoile.b1924.test.tsx`::`B-1924 : l’étoile se nomme, puis dit qu’on peut la retirer` | `ab77950d` | `0e27c202` |
| B-1925 | confirme | `src/frontend/src/components/email/EmailDetail.copie.b1925.test.tsx`::`B-1925 : l’en-tête affiche les destinataires en copie` ; `…`::`B-1925 : sans copie, la ligne Cc est absente` | `2983bb34` | `6587fd7c` |
| B-1926 | confirme | `src/frontend/src/components/files/FileBrowser.indexNom.b1926.test.tsx`::`B-1926 : Indexer ce fichier a un aria-label` ; `…`::`B-1926 : Réindexer ce fichier a un aria-label` | `03a9565b` | `4ae8bc9d` |
| B-1927 | rejete | Preuve déjà en place : `src/frontend/src/components/files/FileBrowser.tsx` lignes 553-554 (commentaire B-1450, « 0 élément », « 3 éléments ») et `src/frontend/src/components/files/FileBrowser.compteAccentue.b1450.test.tsx`::`dit « 0 élément »` | aucun | aucun |
| B-1928 | confirme | `src/frontend/src/components/memory/MemoryPanel.fermer.b1928.test.tsx`::`B-1928 : le tiroir nomme sa fermeture` | `0f34cf50` | `0544edba` |
| B-1929 | confirme | `src/frontend/src/components/memory/MemoryPanel.rgpd.b1929.test.tsx`::`B-1929 : la base %s s’écrit « %s »` (consentement, contrat, interet_legitime, obligation_legale) | `5cb1af8d` | `94be7226` |
| B-1930 | confirme | `src/frontend/src/components/memory/MemoryPanel.nomDialogue.b1930.test.tsx`::`B-1930 : l’export nomme la fiche comme la liste` ; `…`::`B-1930 : le renouvellement nomme la fiche comme la liste` ; `…`::`B-1930 : sans entreprise, le dialogue retombe sur l’e-mail` | `e6720aaa` | `0b72c005` |
| B-1931 | confirme | `src/frontend/src/components/memory/MemoryPanel.initiales.b1931.test.tsx`::`B-1931 : la puce reprend l’entreprise` ; `…`::`B-1931 : sans entreprise, la puce reprend l’e-mail` | `a693b8d2` | `3e004650` |

Le correctif B-1838 ajoute un `AbortSignal` à `sendEmail`. `EmailCompose.test.tsx` et `EmailDetail.replyTo.test.tsx` attendaient exactement deux arguments : ils ont été alignés sur ce contrat dans `9fec62cc`, sans en assouplir l'assertion.

## Règle à trancher

### B-1923

`EmailCompose.tsx` lignes 351-354 rend le bouton « Joindre » en permanence, `disabled`, sans `title` et sans action. Aucun envoi de pièce jointe n'existe à côté. Ni le code ni la documentation ne disent si ce contrôle doit rester, disparaître, ou devenir réel.

- A. Le cacher tant que les pièces jointes n'existent pas. Recommandation : un bouton toujours inactif ressemble à une panne.
- B. Le laisser désactivé et lui donner un titre qui explique l'absence de pièces jointes.
- C. Implémenter les pièces jointes. C'est hors de ce lot.

## Rejets

B-1921 et B-1927 suivent l'accord déjà verrouillé par B-1450 : le pluriel n'est ajouté que si le compte est supérieur à 1. « 0 contact », « 0 projet » et « 0 élément » sont donc le comportement voulu. Le français courant mettrait 0 au pluriel. Changer l'un sans l'autre casserait le test `dit « 0 élément »`.

## Portes

Commandes lancées dans cet arbre, après le dernier correctif `3e004650`.

- pytest : `OLLAMA_BASE_URL=http://127.0.0.1:9 .venv/bin/python -m pytest tests/ --ignore=tests/e2e -q -p no:cacheprovider --timeout=120 --junitxml=/tmp/front-chat-pytest.xml`. Exit 1. 6549 passés, 6 échoués, 51 ignorés, 6606 au total. Échecs :
  - `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[True-True]`
  - `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[True-False]`
  - `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[False-True]`
  - `tests.test_r3_4_ollama::test_refus_a_lecran_meme_sans_fiches[False-False]`
  - `tests.test_securite_f2_recette_deb::test_la_recette_deb_lit_son_fichier_prive_pour_creer_un_document`
  - `tests.test_typage_lot_confidentialite::test_les_quatre_diagnostics_du_lot_confidentialite_ne_reviennent_pas`
- Les cinq premiers sont la référence connue de ce Mac, hors lot. Le sixième cherche la chaîne ` error:` dans la sortie de mypy. Le shell de la porte colore cette sortie, donc la chaîne est absente alors que mypy a bien tourné. Relancé seul, sans variable de couleur : 1 passé. Le diff `cd287fb3..3e004650` ne contient aucun fichier Python.
- ruff : `.venv/bin/python -m ruff check --no-fix src/backend tests`. Exit 0. `All checks passed!`
- vitest : `npm run test -- --run` (depuis la racine, le script entre dans `src/frontend`). Exit 0. 4058 passés, 0 échoué, 937 fichiers.
- tsc : `cd src/frontend && npx tsc --noEmit`. Exit 0. 0 erreur.
- eslint : `cd src/frontend && npm run lint`. Exit 0. 0 erreur, 27 avertissements, sous le plafond `--max-warnings 27`.

## Incertitudes

- B-1838 : `apiFetch` coupe déjà un `fetch` encore sans réponse au bout de 30 s. Le délai de 35 s coupe le cas où le corps reste pendu après les en-têtes, et il empêche le rejet orphelin.
- B-1928 : `MemoryPanel.tsx` est monté en production. Le canevas (`PrototypeUnifiedViewCanvas`) ne le monte qu'en `standalone`. La branche du bouton X du tiroir (`isOpen`, hors standalone) est l'API publique du composant et elle est couverte par le test. Elle n'est pas atteinte par ce canevas.
- B-1921 et B-1927 : l'accord « 0 au singulier » reste celui de B-1450. Le passer au pluriel demanderait une décision sur tout le dépôt, pas seulement ces deux écrans.
