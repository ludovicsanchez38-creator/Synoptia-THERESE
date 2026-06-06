# Brief vérification finale Syn - Thérèse 0.20.0 (mode humain)

> Dernier palier avant la release `0.20.0` (gros bump 0.13.2 → 0.20.0, aboutissement de la revue produit). Vérification indépendante, en conditions réelles, devant l'app.

## Contexte

- **Repo** : `Synoptia-THERESE`, branche **`chantier-revue-produit`** (NE PAS tester `main`, c'est l'ancienne 0.13.2).
- Deux passes de personas + un test exhaustif (un persona « Claire Fontaine » sur 25 zones) ont déjà tourné côté Mac. Tous les bugs trouvés sont corrigés (régression backend au vert). On veut un **regard humain neuf** sur l'app réelle.
- **Fournisseur LLM** : utilise **Mistral** (clé fournie dans le hub, ligne à supprimer après l'avoir configurée). C'est volontaire : valider le chemin cloud réel (appels d'outils, RAG, souveraineté) avec un vrai modèle.

## Mise en route

Tu es sur **Ubuntu (pas Tauri)** : test **dans le navigateur**, comme tes 2e regards précédents (cf. `docs/revue-produit/syn-2e-regard-navigateur.md`).

1. Récupère la branche : `git fetch && git checkout chantier-revue-produit && git pull`.
2. Lance le backend puis le frontend : `make dev-backend` (uvicorn :17293) puis `make dev-frontend` (Vite :1420).
3. Ouvre **http://localhost:1420** dans le navigateur.
4. Réglages → fournisseur **Mistral**, colle la clé fournie dans le hub, choisis un modèle.
5. **Supprime ensuite la ligne du hub contenant la clé.**

## À vérifier (mode humain, on clique vraiment)

Coche, et pour chaque KO note l'étape + ce qui s'est passé.

### Confiance / souveraineté
- [ ] « Où sont mes données, même pour le traitement ? » → réponse factuelle (stockage 100 % local, distinction stockage/traitement), **sans bluff**.
- [ ] Badge **local/cloud** présent sur chaque réponse (ici cloud avec Mistral).
- [ ] Juridique : « clause de pénalités de retard » → cite **L441-10** (pas L441-6) ; « franchise TVA » → **293 B**. Sur une question hors corpus → `[à confirmer sur Légifrance]`, pas d'invention.

### CRM / facturation
- [ ] Crée 2 contacts (un chaud, un froid) avec des **notes** → scores **divergents**, notes **persistées** et relues.
- [ ] Profil émetteur (SIRET, NDA, code APE) renseigné → garde-fou : **facture bloquée sans identité** émettrice, débloquée une fois rempli.
- [ ] PDF facture conforme (profil propagé). Devise **CAD** : mentions FR (40 EUR / L441-10) **absentes**, ligne générique à la place.
- [ ] Liste et création de factures/tâches : **pas de latence/redirection** anormale.

### Anti-hallucination
- [ ] « Donne-moi le suivi de [contact] » → lit la **vraie fiche** (pas d'invention).
- [ ] Sans calendrier connecté : « mes rendez-vous » → dit l'**absence**, n'invente pas.
- [ ] Quick-add sur calendrier **local** → message clair (création via formulaire), pas d'erreur « compte introuvable ».
- [ ] RGPD : anonymise un contact → la fiche **ne remonte plus** en recherche (fantôme vectoriel purgé).

### Documents / Board / divers
- [ ] « Génère un programme de formation en Word » → **vrai fichier** téléchargeable.
- [ ] Board de décision : délibération à 5 conseillers cohérente.
- [ ] Signature mail : écran d'édition par compte fonctionne.
- [ ] Navigation : vues content-swap (Mémoire, CRM, Email, Calendrier, Indexation), Échap, palette ⌘K.

## Compte rendu

- Poste ton **verdict** (GO / NO-GO + liste des KO) dans le hub (`type: info`, scope `Synoptia-THERESE`) ou en direct à Ludo sur Telegram.
- Si NO-GO : décris précisément chaque bug (étape, attendu, observé) pour qu'on corrige avant la release.
