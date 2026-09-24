# P-096 : brouillons personnalisés en lot (design V1, à contester avant code)

Décision de Ludo, 24/09/2026 (salle de décision, geste val-2026-09-23-01) :
« FAIRE AUTREMENT : brouillons personnalisés en lot, aucun envoi, fusion par
les Variables V1, aperçu par destinataire, lever l'ambiguïté du bouton
Écrire. » Suggestion S1 du testeur Dr_logic-3D (publipostage).

## Ce que la fonctionnalité fait, et ce qu'elle ne fait pas

- Elle crée N brouillons dans la boîte connectée, un par contact choisi, avec
  un objet et un corps fusionnés par contact.
- Elle n'envoie RIEN. L'envoi reste un geste de l'utilisateur, brouillon par
  brouillon, dans sa messagerie. Aucun envoi de masse dans le produit
  (irréversibilité, RGPD, délivrabilité d'une boîte personnelle).
- Elle ne suit pas l'ouverture, n'ajoute pas de lien de désinscription, ne
  garde aucune copie des brouillons hors de la boîte de l'utilisateur.

## Entrée

Dans le panneau « Nouveau message » (rédaction libre, verbe Écrire), un
choix en tête : « Un destinataire » (défaut, comportement actuel inchangé) ou
« Plusieurs contacts (un brouillon chacun) ».

Verbe de l'établi : « Écrire » devient « Écrire un e-mail » dans son nom
accessible et son infobulle ; le libellé visible reste « Écrire » si la
largeur des cinq verbes l'exige (à trancher à l'écran, 1280 et 800 px).
Le test E3 (verbe ↔ titre de surface) est mis à jour en conséquence.

## Parcours

1. **Choisir les contacts.** Liste des contacts qui ont une adresse e-mail,
   recherche et filtre par étiquette, cases à cocher, compteur « 12
   contacts choisis ». Plafond : 50 par lot. Un contact sans adresse n'est
   pas proposable (dit en une ligne sous la liste : « 4 contacts sans
   adresse ne sont pas proposés »).
2. **Écrire le modèle.** Objet et corps, avec les champs du contact :
   `{prenom}`, `{nom}`, `{entreprise}`, `{email}`, affichés en aide sous le
   corps, plus les Variables V1 de l'utilisateur. Les champs du contact
   priment sur une variable homonyme. `{{prenom}}` reste un littéral
   (règle V1).
3. **Aperçu par destinataire.** « Aperçu pour Jeanne Martin (1 / 12) » avec
   précédent et suivant ; le texte affiché est résolu PAR LE MOTEUR, par la
   même fonction qu'à la création (règle V1 : même fonction pour l'aperçu et
   l'exécution). Un champ vide chez un contact (ex. `{entreprise}`) le
   bloque : il apparaît dans une liste « 3 contacts à compléter ou à
   retirer » ; jamais de brouillon « Bonjour , ».
4. **Créer.** Bouton « Créer 12 brouillons ». Confirmation (même mécanisme
   que les autres actions externes, `requestExternalAction`) : « 12
   brouillons seront créés dans la boîte ludo@… ; rien ne sera envoyé ».
5. **Compte rendu.** Le travail est suivi dans « Travaux » (type
   `brouillons_lot`, annulable entre deux brouillons, progression n / N).
   À la fin : « 11 brouillons créés, 1 en échec » avec la cause par contact,
   et « Réessayer les échecs » qui ne relance QUE les contacts en échec.

## Moteur

- `POST /api/email/drafts/batch/preview` : `{account_id, contact_ids,
  subject, body}` → par contact : objet et corps résolus, champs manquants.
  Aucun effet.
- `POST /api/email/drafts/batch` : mêmes champs + `batch_id` (généré par
  l'écran). Revalide tout (contacts existants, adresse présente, plafond 50,
  champs manquants = refus du contact, bornes V1 : 20 jetons, 60 000
  caractères). Crée les brouillons un par un par le fournisseur du compte
  (`create_draft` IMAP ou Gmail, chemins existants), dans un travail du
  registre. Rend `{created: [{contact_id, draft_id}], failed: [{contact_id,
  cause}]}`, causes passées par `message_pour_ecran`.
- Anti-doublon : le registre du travail garde `(batch_id, contact_id) →
  draft_id` ; une relance du même lot saute les contacts déjà créés.
- Résolution : `resolve_text` de `variables_service`, avec
  `{**variables_utilisateur, **champs_du_contact}`.

## Données personnelles

- Les noms et adresses des contacts ne quittent pas la machine, sauf vers la
  boîte de l'utilisateur (création des brouillons, comme aujourd'hui).
- Mode démo : aperçu et compte rendu passent par `maskText` ; la création
  est désactivée en démo (comme la suppression dans les fiches).
- Journal : identifiants de contacts et de brouillons, jamais le corps.

## Tests prévus

- Moteur : résolution par contact (champs du contact prioritaires, littéral
  `{{…}}`), contact sans adresse refusé, champ vide bloquant, plafond 50,
  anti-doublon d'une relance, échec partiel rendu par contact, aucune route
  d'envoi appelée (espion sur `send`).
- Écran : bascule un / plusieurs, sélection et plafond, aperçu navigable,
  contacts bloqués listés, confirmation avant création, compte rendu et
  relance des seuls échecs, masque démo, nom accessible « Écrire un e-mail ».

## Questions ouvertes pour le relecteur

1. Bloquer un contact au champ vide, ou proposer une valeur de repli par
   champ (« {prenom|Madame, Monsieur} ») ? V1 propose le blocage, plus sûr.
2. Plafond de 50 : suffisant pour une TPE, assez bas pour les quotas Gmail ?
3. Faut-il un délai entre deux créations (quotas du fournisseur) ?
4. Le travail doit-il survivre à la fermeture du panneau (oui : registre) ?
