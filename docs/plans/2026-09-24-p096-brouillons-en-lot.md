# P-096 : brouillons personnalisés en lot (design V3)

Décision de Ludo, 24/09/2026 (salle de décision, geste val-2026-09-23-01) :
« FAIRE AUTREMENT : brouillons personnalisés en lot, aucun envoi, fusion par
les Variables V1, aperçu par destinataire, lever l'ambiguïté du bouton
Écrire. » Suggestion S1 du testeur Dr_logic-3D.

Historique : V1 (24/09 matin) NO-GO, 5 P1 et 27 P2 ou P3 ; V2 NO-GO, 1 P1 et
22 P2 ou P3 (`docs/plans/revues/2026-09-24-p096-revue-v2.md`). Les onze
questions produit ont été tranchées par délégation de Ludo le 24/09
(`docs/plans/2026-09-24-arbitrages-par-delegation.md`), toutes selon la
recommandation. Cette V3 intègre ces choix et chacun des 23 constats de la V2
(tableau de correspondance en fin de document). Aucun code avant un GO de
revue adverse.

## Promesse

- N brouillons dans la boîte connectée, un par contact choisi, objet et corps
  fusionnés par contact. **Rien n'est envoyé** : l'envoi reste un geste de
  l'utilisateur dans sa messagerie, brouillon par brouillon.
- **Aucun corps personnalisé en base** (décision 5) : le moteur garde le
  modèle NON résolu (jetons compris) dans l'en-tête du lot, jusqu'à la fin du
  lot plus 30 jours, pour pouvoir reprendre ; jamais un objet ou un corps
  fusionné pour un contact.
- Pas de signature ajoutée (décisions 2, 10, 11) : l'aperçu dit « sans
  signature ». Pas de trace sur la fiche contact tant que le brouillon n'est
  pas envoyé (décision 7). Pas de suivi d'ouverture, pas de désinscription.

## Données : qui est proposable

- Route dédiée `GET /api/email/drafts/batch/candidats?q=&etiquette=&offset=`,
  filtrée côté serveur, avec compteurs exacts : proposables, sans adresse,
  exclus (et pourquoi). Le moteur réapplique ces règles aux identifiants
  reçus, à la prévisualisation comme à la création.
- Proposable (décision 3) : portée globale seule en V1, `stage` différent de
  « archive », adresse unique valide (`adresse_unique_valide`, B-1074).
  Consentement expiré ou base légale vide : **signalés** dans la liste et
  l'aperçu, sans blocage.
- **Une adresse, un brouillon** : l'adresse est normalisée (minuscules,
  espaces retirés) ; un second contact à la même adresse est refusé à la
  validation (« adresse en double avec <contact masqué> »).
- Plafond (décision 10) : 50 contacts par lot, constante serveur unique lue
  par l'écran, testée à 50 et 51.
- **Déjà écrit il y a moins de 24 h** (décision 6) : signalé par contact ET
  par adresse normalisée, contact décoché par défaut, recochable.

## Fusion

- Champs du contact dans un espace de noms à part (décision 4) :
  `{contact_prenom}`, `{contact_nom}`, `{contact_entreprise}`,
  `{contact_email}`. **Le préfixe `contact_` est réservé** dans
  `variables_service.validate_name` : une Variable `contact_*` n'est plus
  créable ; si une telle Variable existe déjà, le lot est refusé tant qu'elle
  existe (message qui la nomme).
- À l'étape Modèle, avertissement quand le modèle contient `{prenom}`,
  `{nom}`, `{entreprise}` ou `{email}` : « veux-tu dire {contact_prenom} ? »
  (sinon la Variable de l'utilisateur se résoudrait en silence dans les N
  brouillons).
- Avant `resolve_text` : jetons du modèle qui sont des champs du contact et
  dont la valeur nettoyée est vide = contact **bloqué**, sans repli ni saisie
  en ligne (décisions 9 et 11 ; une fiche d'entreprise sans prénom est donc
  bloquée dès que le modèle contient `{contact_prenom}`), avec un lien vers sa
  fiche.
- Objet : le MODÈLE et les valeurs sont assainis (`\r`, `\n`, caractères de
  contrôle remplacés par une espace), `list_mode` inline ; objet fusionné de
  plus de 250 caractères = **contact** bloqué « objet trop long ».
- Corps : texte brut (`html: false`), `list_mode` bloc ; objet et corps
  résolus séparément. Plus de 20 jetons ou plus de 60 000 caractères au
  modèle = **lot** refusé.
- Jeton inconnu ou mal formé : lot refusé avec la liste des jetons. La règle
  de `jetonsMalFormes` (`/^[\p{L}\p{N}_\- ]{1,40}$/u`, variables.ts:120) est
  réécrite en Python sans `\p{L}` : `1 <= len(c) <= 40 and all(ch.isalnum()
  or ch in "_- " for ch in c)`, plus les exclusions `{{…}}`, `{action:` et
  blocs de code ; **un jeu de cas commun** (fichier JSON de cas partagé) est lu
  par les tests Python et Vitest.
- Empreinte d'aperçu : hachage des tuples triés (id, prénom, nom, entreprise,
  adresse normalisée, stage, scope) des contacts du lot, plus `account_id`,
  choix de signature, révision des Variables et hachage du modèle. Un aperçu
  périmé donne 409 « l'aperçu n'est plus à jour » (une fiche modifiée par
  import, dont `updated_at` peut reculer, change bien l'empreinte).

## Moteur

- `POST …/batch/preview` : sans effet ; par contact, objet et corps résolus ou
  motif de blocage ; empreinte.
- `POST …/batch` (`account_id`, `contact_ids`, `subject`, `body`,
  `empreinte`) : revalide tout ; **le moteur génère `batch_id` (UUID)** ;
  écrit l'en-tête et les éléments ; lance le travail ; répond **202**
  `{task_id, batch_id}`. Aucun identifiant de lot n'est accepté de l'écran.
- En-tête `brouillons_lot` : `batch_id` (clé), `account_id`, `created_at`,
  `total`, modèle non résolu (objet et corps, jetons compris), hachage du
  modèle, empreinte, `purge_apres` (fin du lot plus 30 jours).
- Éléments `brouillons_lot_items` : `batch_id`, `contact_id`, `adresse_hash`
  (pour le signalement 24 h par adresse), `statut` (non_tenté, en_cours,
  créé, échec, incertain, refusé), `draft_id`, `cause_code`, `maj` ;
  UNIQUE(`batch_id`, `contact_id`) ; index (`contact_id`, `maj`) et
  (`adresse_hash`, `maj`) ; ni objet ni corps.
- `GET …/batch/{batch_id}` : état par contact (masqué en démo ; « fiche
  supprimée » pour un élément dont le contact n'existe plus).
- `POST …/batch/{batch_id}/reprendre` : sans charge ; relit le modèle de
  l'en-tête ; relance les seuls `non_tenté` et échecs réessayables ; refus
  409 si un travail du lot est actif.
- **Chaque lancement ou reprise = un nouveau `ProcessingTask`** du registre
  `brouillons_lot`, `entity_id = batch_id` (un identifiant de travail n'est
  jamais réutilisé, `traitements.py:181-182`).
- Réservation avant chaque dépôt : UPDATE conditionnel non_tenté vers
  en_cours (une ligne, sinon on saute). Verrou asyncio par lot. Tests : deux
  POST simultanés ; même POST après la fin du lot (nouveau lot, pas de
  réécriture).
- Annulation coopérative (`AnnulationCooperative`) : drapeau lu avant chaque
  dépôt ; le dépôt en cours finit et s'enregistre ; fin CANCELLED « 7 créés,
  5 non tentés ». Libellé, étape et erreur du travail ne portent que des
  compteurs.
- **Session de dépôt** : `ouvrir_session_brouillons()` rend un objet à
  `deposer(demande)` asynchrone ; **un `_run_imap_operation` par dépôt**, sur
  un exécuteur à un seul fil par lot ; dossier Brouillons résolu et vérifié
  (`folder.exists`) avant la boucle ; APPEND avec le drapeau `\Draft`. Après
  un délai dépassé ou une erreur réseau, la session est abandonnée et rouverte
  (trois échecs réseau consécutifs arrêtent le lot). Gmail : séquentiel, un
  appel par dépôt. Test : dépôt n° 3 expiré, le n° 4 part sur une session
  neuve.
- **Causes, par code** : `auth`, `quota`, `reseau_avant_envoi`, `incertain`,
  `adresse_invalide`, `champ_invalide`, `dossier_introuvable`, `autre`.
  - Réessayable = échec **prouvé avant l'envoi** (connexion refusée, DNS,
    401, 429 ; 403 `rateLimitExceeded` de Gmail traité comme 429).
  - Toute erreur **après** l'envoi (délai de lecture, coupure, 5xx) =
    `incertain`, exclu de la reprise, consigne « vérifie tes Brouillons ».
    Gmail remonte l'exception `httpx` d'origine (plus la chaîne « Gmail API
    request failed », qui confondait délai et 500).
  - `auth` et `dossier_introuvable` arrêtent le lot et remettent l'élément en
    `non_tenté` (rien n'a été déposé) ; `autre` (exception imprévue) arrête le
    lot, élément `incertain`.
  - Journal : `type(e).__name__` et `contact_id`, jamais l'objet, le corps ni
    l'adresse.
- **Message-ID** : `<hachage opaque(batch_id, contact_id)@domaine du compte>`,
  jamais les identifiants en clair (vérification, avant de coder, que Gmail
  `drafts.create` le conserve ; sinon le champ n'est pas posé et la reprise
  d'un incertain reste manuelle).
- **Redémarrage** : fonction dédiée appelée dans le lifespan juste après
  `recuperer_taches_orphelines` (`main.py:219-229`) : tout élément `en_cours`
  devient `incertain`.
- **Conservation** (décision 8) : éléments et en-têtes purgés 30 jours après
  la fin du lot, avec les travaux (`traitements.py:376-393`) ; éléments d'un
  contact supprimés à la suppression et à l'anonymisation de la fiche
  (`memory.py`, `rgpd.py:224-233`, `rgpd_auto.py:196-206`) ; purge totale
  (« Effacer toutes mes données ») : les deux tables.
- **Migration** : modèles SQLModel avec `UniqueConstraint` et index ;
  révision Alembic `down_revision = "a7b8c9d0e1f2"` ; mise à jour de
  `ALEMBIC_HEAD_REVISION` (`database.py:617`) ; extension de la preuve de
  schéma dans `ensure_alembic_stamp` par `tables_de_brouillons_lot()` sur le
  patron de `tables_de_planning` (`database.py:630-636`) ; test de montée
  depuis une base à l'ancienne tête.
- « Aucun envoi » testé en profondeur : espions sur `aiosmtplib.send`,
  `GmailService.send_message`, toute URL contenant `/send`, `send_message` des
  deux fournisseurs.

## Écran

- Verbe de l'établi (décision 1) : libellé visible « Écrire un e-mail »,
  repris dans la palette et le titre de la surface.
- Dans « Nouveau message », groupe radio « Un destinataire » / « Plusieurs
  contacts (un brouillon chacun) ». Titre « Brouillon » ou « Modèle du lot ».
- Assistant à une étape visible à la fois (Contacts, Modèle, Aperçu,
  Création, Compte rendu) ; focus sur le titre de l'étape à chaque changement.
- Contacts : `fieldset` + `legend`, recherche, étiquette, cases ; plafond
  expliqué, cases en `aria-disabled` au-delà ; compteur en
  `aria-live="polite"` ; signalements RGPD et « déjà écrit il y a moins de
  24 h » sur la ligne.
- Modèle : aide qui liste les quatre champs du contact ; `jetonsMalFormes` en
  direct ; avertissement « veux-tu dire {contact_prenom} ? ».
- Aperçu : « Aperçu pour <nom masqué> (1 / 12) », précédent et suivant nommés
  par le destinataire, annonce polie ; « sans signature » ; contacts bloqués
  listés avec « Retirer du lot » et « Retirer les N bloqués », et un lien vers
  la fiche.
- Création : confirmation **dans le panneau**, fail-closed : « 12 brouillons
  seront créés dans la boîte … ; rien ne sera envoyé ». Test : aucun POST ne
  part avant le clic sur « Confirmer » du panneau (ni par Entrée dans le
  modèle, ni par double clic). Progression annoncée par paliers ; à l'arrêt,
  l'écran dit que les brouillons déjà créés restent dans la boîte.
- Compte rendu : état du lot dans un store, rechargeable par
  `GET …/batch/{id}` ; sur les lignes `brouillons_lot` du panneau Travaux, un
  bouton « Voir le compte rendu » ouvre le canevas e-mail en mode compte
  rendu pour cet `entity_id` ; « Reprendre » quand des éléments le
  permettent.
- **Saisie en cours** : le panneau passe par `useAbandonDeSaisie` (pile
  d'Échap, registre, question) ; `collapseScenarioPanel` et
  `rangerPourLAccueil` consultent le registre ; la garde se retire après le
  202 (le lot vit alors dans le store). Test : cocher un contact, fermer le
  panneau, la question apparaît ; même chose par Échap et par le retour à
  l'accueil.
- **Mode démo** : une table de masquage **propre au panneau** (jamais un
  remplacement de la table globale, `useDemoMask.ts:33-34`) ; l'aperçu rend
  par contact les valeurs substituées et l'écran masque exactement ces
  valeurs, quelle que soit leur longueur (un nom de deux lettres compris) ;
  `maskContact` sur chaque ligne ; bouton « Créer » visible mais inactif,
  avec la raison. Test : lot ouvert en démo, puis un message du chat qui cite
  un contact hors lot, toujours masqué.

## Tests prévus

Moteur : résolution (espace de noms, "", "  ", None, homonyme de Variable),
préfixe `contact_` réservé et Variable existante, contact bloqué, objet trop
long (contact), 21 jetons (lot), jeton inconnu ou mal formé (jeu de cas
commun), adresse en double, plafond 50/51, `batch_id` généré, 202, deux POST
simultanés, même POST après la fin, réservation, reprise des seuls
réessayables sans charge, incertain exclu, `ReadTimeout` Gmail et coupure
IMAP après APPEND classés incertain, auth et dossier remettent en non_tenté,
session rouverte après délai, drapeau `\Draft`, annulation coopérative,
redémarrage, purge à 30 jours et à la suppression ou l'anonymisation d'un
contact, montée Alembic, empreinte (fiche importée, contact ajouté, compte
changé), aucun envoi (espions profonds). Écran : bascule, assistant au clavier
de bout en bout, plafond, avertissement `{prenom}`, aperçu navigable et
annoncé, bloqués et lien vers la fiche, confirmation sans POST anticipé,
compte rendu rechargé et ouvert depuis Travaux, garde de saisie (fermeture,
Échap, accueil), masque démo propre au panneau, nom « Écrire un e-mail ».

## Correspondance avec la revue V2

| Constat V2 | Traitement V3 |
|---|---|
| 1 (P1) reprise sans modèle | en-tête `brouillons_lot` avec le modèle non résolu (décision 5), `reprendre` sans charge |
| 2 session IMAP et réservation | `ouvrir_session_brouillons` / `deposer`, un appel par dépôt, session rouverte |
| 3 réessayable après envoi | réessayable = prouvé avant l'envoi ; après = incertain ; exception httpx d'origine |
| 4 préfixe `contact_` | réservé dans `validate_name`, Variable existante refuse le lot, avertissement `{prenom}` |
| 5 table de masquage | table propre au panneau, valeurs substituées masquées quelle que soit la longueur |
| 6 garde de saisie | `useAbandonDeSaisie`, fermeture, Échap et accueil consultent le registre |
| 7 `batch_id` de l'écran | généré par le moteur |
| 8 migration | quatre gestes écrits (modèle, révision, tête épinglée, preuve de schéma) et test de montée |
| 9 décisions manquantes | tranchées par délégation (onze décisions) |
| 10 redémarrage | fonction dédiée dans le lifespan |
| 11 empreinte | tuples des contacts, compte, signature, Variables, modèle |
| 12 bornes | objet trop long = contact ; jetons ou taille = lot ; modèle assaini ; `list_mode` écrits |
| 13 causes | `autre`, 403 `rateLimitExceeded`, `folder.exists` avant la boucle, auth et dossier en non_tenté |
| 14 relance et Travaux | nouveau travail par lancement, bouton « Voir le compte rendu » |
| 15 conservation | 30 jours, suppression et anonymisation, index |
| 16 `\p{L}` en Python | réécriture sans `\p{L}` et jeu de cas commun |
| 17 signature texte | sans signature (décisions 2 et 10) |
| 18 Message-ID | hachage opaque, vérification Gmail avant de coder |
| 19 archivés et portée | décision 3, écrite une seule fois |
| 20 test sans fournisseur | remplacé par « aucun POST avant Confirmer » |
| 21 reliquats V1 | drapeau `\Draft`, progression par paliers, brouillons restants dits à l'arrêt |
| 22 même adresse | une adresse, un brouillon ; signalement 24 h par adresse |
| 23 comptes inexacts | historique corrigé en tête |
