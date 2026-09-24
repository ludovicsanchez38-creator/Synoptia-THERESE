# P-096 : brouillons personnalisés en lot (design V4)

Décision de Ludo, 24/09/2026 (salle de décision, geste val-2026-09-23-01) :
« FAIRE AUTREMENT : brouillons personnalisés en lot, aucun envoi, fusion par
les Variables V1, aperçu par destinataire, lever l'ambiguïté du bouton
Écrire. » Suggestion S1 du testeur Dr_logic-3D.

Historique : V1 (24/09 matin) NO-GO, 5 P1 et 27 P2 ou P3 ; V2 NO-GO, 1 P1 et
22 P2 ou P3 (`docs/plans/revues/2026-09-24-p096-revue-v2.md`). Les onze
questions produit ont été tranchées par délégation de Ludo le 24/09
(`docs/plans/2026-09-24-arbitrages-par-delegation.md`), toutes selon la
recommandation. La V3 intégrait ces choix et les 23 constats de la V2 ; sa
revue (`docs/plans/revues/2026-09-24-p096-revue-v3.md`, NO-GO, 1 P1 et 16 P2
ou P3) est intégrée dans cette V4 (second tableau en fin de document). Aucun
code avant un GO de revue adverse.

## Promesse

- N brouillons dans la boîte connectée, un par contact choisi, objet et corps
  fusionnés par contact. **Rien n'est envoyé** : l'envoi reste un geste de
  l'utilisateur dans sa messagerie, brouillon par brouillon.
- **Le lot n'écrit aucun corps personnalisé** (décision 5) : le moteur garde
  le modèle NON résolu (jetons compris) dans l'en-tête du lot, jusqu'à la fin
  du lot plus 30 jours, pour pouvoir reprendre ; jamais un objet ou un corps
  fusionné pour un contact. Un brouillon **ouvert ensuite dans THÉRÈSE**
  entre dans le cache des messages comme tout message (sans lien au contact,
  donc hors de la suppression ou de l'anonymisation d'une fiche) : c'est dit
  dans l'aide de l'étape Création.
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
  espaces retirés) ; un second contact à la même adresse est **bloqué**
  (« adresse en double »), avec « Retirer du lot ». Le moteur rend des
  identifiants, jamais des noms, dans ses motifs de blocage et de refus.
- Plafond (décision 10) : 50 contacts par lot, constante serveur unique lue
  par l'écran, testée à 50 et 51.
- **Déjà écrit il y a moins de 24 h** (décision 6) : éléments de lot `créé`
  ou `incertain` de moins de 24 h, par contact ET par adresse normalisée ;
  les envois faits hors lot ne comptent pas (dit à l'écran) ; contact décoché
  par défaut, recochable.

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
  résolus séparément, chacun sous les bornes de `resolve_text` : 20 jetons
  par partie (`variables_service.py:284-307`) ; au-delà, **lot** refusé. Le
  corps **résolu** de plus de 60 000 caractères (`variables_service.py:
  323-327`, une Variable liste peut le faire dépasser) : lot refusé à
  l'aperçu, les Variables étant les mêmes pour tous.
- Jeton inconnu ou mal formé : lot refusé avec la liste des jetons. La règle
  de `jetonsMalFormes` (`/^[\p{L}\p{N}_\- ]{1,40}$/u`, variables.ts:120) est
  réécrite en Python sans `\p{L}` : `1 <= len(c) <= 40 and all(ch.isalnum()
  or ch in "_- " for ch in c)`, plus les exclusions `{{…}}`, `{action:` et
  blocs de code ; **un jeu de cas commun** (fichier JSON de cas partagé) est lu
  par les tests Python et Vitest.
- Empreinte d'aperçu : hachage des tuples triés (id, prénom, nom, entreprise,
  adresse normalisée, stage, scope) des contacts du lot, plus `account_id`,
  révision des Variables et hachage du modèle. Un aperçu
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
- `GET …/batch/{batch_id}` : état par contact, en identifiants (le masque de
  démo est appliqué par l'écran) ; « fiche supprimée » pour un élément dont
  le contact n'existe plus.
- `POST …/batch/{batch_id}/reprendre` : sans charge ; relit le modèle de
  l'en-tête ; **revalide tout comme à la création** (proposabilité, blocages,
  doublons d'adresse, préfixe `contact_`, empreinte recalculée sur les mêmes
  contacts et comparée à celle de l'en-tête) : un écart donne 409 « l'aperçu
  n'est plus à jour » et l'écran rouvre l'Aperçu sur les contacts restants ;
  puis, sous le verrou du lot, remet explicitement les échecs réessayables à
  `non_tenté` et relance. Refus 409 si un travail du lot est actif ; cause
  `compte_absent` si le compte a été déconnecté (l'écran remplace
  « Reprendre » par « Compte déconnecté »).
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
  `deposer(demande)` asynchrone ; **un `_run_imap_operation` par dépôt**,
  qui reçoit désormais l'exécuteur à utiliser ; **un exécuteur à un fil par
  SESSION**, abandonné avec elle (`shutdown(wait=False,
  cancel_futures=True)`) : un fil bloqué sur un dépôt expiré ne retarde pas la
  session suivante ; un dépôt dont la fonction n'a jamais démarré reste
  `non_tenté` ; dossier Brouillons résolu et vérifié
  (`folder.exists`) avant la boucle ; APPEND avec le drapeau `\Draft`. Après
  un délai dépassé ou une erreur réseau, la session est abandonnée et rouverte
  (trois échecs réseau consécutifs arrêtent le lot). Gmail : séquentiel, un
  appel par dépôt. Test, avec un vrai fil bloqué sur
  un `threading.Event` : dépôt n° 3 expiré, le n° 4 part sur une session
  neuve.
- **Causes, par code** : `auth`, `quota`, `reseau_avant_envoi`, `incertain`,
  `adresse_invalide`, `champ_invalide`, `dossier_introuvable`, `autre`.
  - Réessayable = échec **prouvé avant l'envoi** (connexion refusée, DNS,
    401, 429 ; 403 `rateLimitExceeded` de Gmail traité comme 429).
  - Toute erreur **après** l'envoi (délai de lecture, coupure, 5xx) =
    `incertain`, exclu de la reprise, consigne « vérifie tes Brouillons ».
    Gmail : un chemin propre au lot, sans toucher aux 15 autres appels de
    `_request`, lève une exception dédiée qui porte le statut, la raison
    (`error.errors[0].reason` : `rateLimitExceeded` n'est pas
    `insufficientPermissions`), « avant ou après l'envoi » et l'exception
    `httpx` en `__cause__` ; le corps d'erreur du fournisseur ne va pas au
    journal.
  - `auth` et `dossier_introuvable` arrêtent le lot et remettent l'élément en
    `non_tenté` (rien n'a été déposé) ; `autre` (exception imprévue) arrête le
    lot, élément `incertain`.
  - Journal : `type(e).__name__` et `contact_id`, jamais l'objet, le corps ni
    l'adresse.
- **Message-ID et recherche** : `<hachage opaque(batch_id,
  contact_id)@domaine du compte>`, posé sur chaque brouillon (champ ajouté au
  contrat commun `SendEmailRequest`, `_message_du_brouillon` et
  `_encoder_message`). `chercher_brouillon(message_id)` est ajouté aux deux
  fournisseurs (IMAP `SEARCH HEADER Message-ID`, Gmail `q=rfc822msgid:` sur
  les brouillons). **Avant toute reprise**, chaque élément `incertain` ou
  `non_tenté` d'un lot qui a déjà tourné est cherché : trouvé = `créé`, absent
  = `non_tenté`. Vérification, avant de coder, que Gmail `drafts.create`
  conserve l'en-tête ; sinon, pour Gmail, l'incertain reste exclu de la
  reprise, consigne « vérifie tes Brouillons ».
- **Redémarrage** : fonction dédiée appelée dans le lifespan après
  `recuperer_taches_orphelines`, **dans son propre `try`** (celui des
  travaux est fail-open, `main.py:217-233`) : tout élément `en_cours` devient
  `incertain`. Filet : le GET d'un lot dont le dernier travail est
  `interrupted` fait la même bascule.
- **Conservation** (décision 8) : « fin du lot » = fin de son dernier
  travail, quel que soit l'état final (terminé, échec, annulé, interrompu,
  bascule du démarrage comprise). `purge_apres` est **réécrit à chaque fin**
  et vidé au lancement d'une reprise. Une purge dédiée, lancée au démarrage
  et une fois par jour de session, supprime en-têtes et éléments échus, sans
  jamais toucher un lot dont un travail est actif ; un en-tête sans élément
  (tous partis avec leurs fiches) part avec son dernier élément. Éléments
  d'un contact supprimés à la suppression et à l'anonymisation de la fiche
  (`memory.py`, `rgpd.py:224-233`, `rgpd_auto.py:196-206`). Le modèle de
  l'en-tête suit le régime des conversations : purge totale et export,
  aucun nettoyage par fiche (dit dans l'aide de l'étape Modèle).
- **Export RGPD** (constat V3 n° 13) : l'export global inclut en-têtes et
  éléments ; l'export d'un contact inclut ses éléments (lot, date, statut),
  sans `adresse_hash`.
- **Lot en cours face aux gestes destructeurs** (P1 de la revue V3) : la
  **restauration** et la **purge totale** refusent (409 « un lot de
  brouillons est en cours ») tant qu'un travail `brouillons_lot` est actif ;
  l'écran propose d'arrêter le lot (annulation coopérative : le dépôt en
  cours finit) puis de relancer le geste. Le verrou de maintenance ne compte
  que les requêtes HTTP (`maintenance.py:30-58`) : c'est ce contrôle,
  AVANT `maintenance_mode.begin()` et `close_db()`, qui empêche le lot
  d'écrire dans une base en cours d'extraction. La **déconnexion d'un
  compte** arrête d'abord les lots de ce compte (même annulation), et son
  en-tête est purgé aussitôt (son modèle ne sert plus). Une sauvegarde prise
  pendant un lot garde des éléments `non_tenté` dont le brouillon peut
  exister : la recherche par Message-ID avant reprise les reclasse. Tests :
  restauration, purge totale et déconnexion IMAP pendant le 2e dépôt d'un lot
  de 5 ; reprise après déconnexion.
- **Migration** : modèles SQLModel avec `UniqueConstraint` et index ;
  révision Alembic `down_revision = "a7b8c9d0e1f2"` ; mise à jour de
  `ALEMBIC_HEAD_REVISION` (`database.py:617`) ; extension de la preuve de
  schéma dans `ensure_alembic_stamp` par `tables_de_brouillons_lot()` sur le
  patron de `tables_de_planning` (`database.py:630-636`) ; test de montée
  depuis une base à l'ancienne tête.
- « Aucun envoi » testé en profondeur : espions sur `aiosmtplib.send`,
  `aiosmtplib.SMTP.connect`, `smtplib.SMTP.__init__` (le lot n'a aucune raison
  d'ouvrir du SMTP), `GmailService.send_message`, toute URL contenant `/send`,
  `send_message` des deux fournisseurs.

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
- Compte rendu : état du lot dans un store **non persisté** (seul `batch_id`
  peut l'être ; aucun aperçu fusionné ne va sur le disque de la webview),
  rechargeable par `GET …/batch/{id}` ; `entity_id` ajouté au type
  `Traitement` de l'écran (le moteur l'envoie déjà, `traitements.py:287`) ; sur les lignes `brouillons_lot` du panneau Travaux, un
  bouton « Voir le compte rendu » ouvre le canevas e-mail en mode compte
  rendu pour cet `entity_id` ; « Reprendre » quand des éléments le
  permettent.
- **Saisie en cours** : le panneau passe par `useAbandonDeSaisie` (pile
  d'Échap, registre, question) ; `collapseScenarioPanel` et
  `rangerPourLAccueil` consultent le registre, **ainsi que l'effet qui
  referme le canevas quand le store ne désigne plus de vue**
  (`ConversationCanvasPrototype.tsx:1173-1182`) ; l'état du panneau
  (contacts cochés, modèle, étape) vit dans un store non persisté qui survit
  au démontage du canevas, de sorte qu'un rétrécissement de la fenêtre
  (`:1345-1347`, geste sans question possible) ne perd rien. La garde se
  retire après le 202. Tests : fermeture, Échap, retour à l'accueil,
  fermeture du chat ouvert à côté, rétrécissement de la fenêtre.
- **Mode démo** (masque **côté écran** : le moteur ignore la démo) : une
  table de masquage **propre au panneau** (jamais un remplacement de la table
  globale, `useDemoMask.ts:33-34`) ; l'aperçu rend par contact les valeurs
  substituées, que l'écran masque exactement, quelle que soit leur longueur,
  puis le texte entier (modèle et Variables compris) passe AUSSI par la table
  globale (`maskText`) ; `maskContact` sur chaque ligne ; « Créer » et
  « Reprendre » visibles mais inactifs, avec la raison. Test : lot ouvert en démo, puis un message du chat qui cite
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

## Correspondance avec la revue V3

| Constat V3 | Traitement V4 |
|---|---|
| 1 (P1) lot pendant une restauration | restauration et purge totale refusent (409) tant qu'un lot tourne, arrêt proposé ; recherche par Message-ID avant reprise |
| 2 déconnexion, purge, compte absent | déconnexion arrête les lots du compte, en-tête purgé ; cause `compte_absent` ; tests |
| 3 reprise sans revalidation | reprise revalide tout, empreinte comparée, échecs réessayables remis sous verrou |
| 4 conservation sans mécanisme | fin = fin du dernier travail, `purge_apres` réécrit, purge dédiée qui épargne les lots actifs |
| 5 fil unique par lot | un exécuteur par session, abandonné avec elle ; test avec un vrai fil bloqué |
| 6 Message-ID sans usage | champ au contrat commun, `chercher_brouillon` pour les deux fournisseurs |
| 7 contrat de `_request` | chemin propre au lot, raison du 403 gardée, corps d'erreur hors journal |
| 8 deux fermetures sans question | effet de fermeture et rétrécissement couverts, état en store non persisté |
| 9 démo incomplète | masque côté écran dit, table globale après la table du panneau, « Reprendre » inactif, identifiants seuls dans les refus |
| 10 « aucun corps en base » trop absolu | promesse reformulée, cache des messages dit |
| 11 bornes réelles | 20 jetons par partie, corps résolu au-delà de 60 000 caractères refusé à l'aperçu |
| 12 espion SMTP incomplet | espions `aiosmtplib.SMTP.connect` et `smtplib.SMTP.__init__` |
| 13 export RGPD | export global et export d'un contact ; régime du modèle dit |
| 14 `try` fail-open au démarrage | `try` propre, filet au GET |
| 15 `entity_id` et store persisté | type complété, store non persisté |
| 16 choix de signature dans l'empreinte | retiré |
| 17 règles floues | adresse en double = contact bloqué ; « déjà écrit » = créé ou incertain, hors envois hors lot |

