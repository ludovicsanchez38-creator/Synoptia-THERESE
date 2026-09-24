# P-096 : brouillons personnalisés en lot (design V2)

Décision de Ludo, 24/09/2026 (salle de décision, geste val-2026-09-23-01) :
« FAIRE AUTREMENT : brouillons personnalisés en lot, aucun envoi, fusion par
les Variables V1, aperçu par destinataire, lever l'ambiguïté du bouton
Écrire. » Suggestion S1 du testeur Dr_logic-3D.

Historique : V1 du 24/09 matin, relecture adverse NO-GO (5 P1, 23 P2 et P3,
tous vérifiés dans le code, rapport conservé hors dépôt). Cette V2 reprend
toutes les corrections ; ce qui relève d'une décision produit est isolé en
fin de document.

## Promesse

- N brouillons dans la boîte connectée, un par contact choisi, objet et corps
  fusionnés par contact. **Rien n'est envoyé** : l'envoi reste un geste de
  l'utilisateur dans sa messagerie, brouillon par brouillon.
- Le lot n'écrit aucun objet ni corps dans la base de THÉRÈSE (la table des
  éléments du lot ne garde que des identifiants et des codes). Un brouillon
  ouvert ensuite dans THÉRÈSE suit le cache ordinaire des messages.
- Pas de suivi d'ouverture, pas de désinscription (rien n'est envoyé).

## Données : qui est proposable

- Route dédiée `GET /api/email/drafts/batch/candidats?q=&etiquette=&offset=`,
  filtrée côté serveur, avec compteurs exacts : proposables, sans adresse,
  exclus (et pourquoi). Le moteur réapplique ces règles aux identifiants
  reçus.
- Proposable : portée globale, `stage` différent de « archive », adresse
  unique valide (`adresse_unique_valide`, B-1074). Règles RGPD : voir « À
  trancher ».
- Plafond : 50 contacts par lot, constante serveur unique lue par l'écran,
  testée à 50 et 51.

## Fusion

- Champs du contact dans un espace de noms à part, pour ne jamais écraser une
  Variable de l'utilisateur : `{contact_prenom}`, `{contact_nom}`,
  `{contact_entreprise}`, `{contact_email}` (compatibles `[a-z0-9_]`).
- Avant `resolve_text` : jetons du modèle qui sont des champs du contact et
  dont la valeur nettoyée est vide = contact **bloqué** (jamais « Bonjour , »).
  Seules des valeurs non vides, nettoyées, sont passées.
- Objet : `\r`, `\n` et caractères de contrôle des valeurs remplacés par une
  espace, `list_mode` inline, longueur maximale après fusion 250 caractères.
  Corps : texte brut (`html: false`), bornes V1 par appel (20 jetons, 60 000
  caractères), objet et corps résolus séparément.
- Jeton inconnu restant, ou jeton mal formé (`{prénom}`, `{Prenom}`, règle de
  `jetonsMalFormes` portée au moteur) : le **lot entier** est refusé avec la
  liste des jetons. Pas de syntaxe de repli en V1.
- Empreinte d'aperçu : révision des Variables + max(`updated_at`) des
  contacts + hachage du modèle. La création la renvoie ; un aperçu périmé
  donne 409 « l'aperçu n'est plus à jour ».

## Moteur

- `POST …/batch/preview` : sans effet ; par contact, objet et corps résolus ou
  motif de blocage ; empreinte.
- `POST …/batch` (`account_id`, `batch_id`, `contact_ids`, `subject`,
  `body`, `empreinte`) : revalide tout, écrit les éléments du lot, lance la
  tâche de fond et répond **202** `{task_id, batch_id}` sans attendre.
- `GET …/batch/{batch_id}` : état par contact (lu par l'écran, masqué en démo).
- `POST …/batch/{batch_id}/reprendre` : relance les seuls `non_tenté` et
  échecs réessayables.
- Table `brouillons_lot_items` (migration Alembic) : `batch_id`,
  `contact_id`, `statut` (non_tenté, en_cours, créé, échec, incertain,
  refusé), `draft_id`, `cause_code`, `maj` ; UNIQUE(`batch_id`,
  `contact_id`) ; ni objet ni corps.
- Réservation avant chaque appel au fournisseur : UPDATE conditionnel
  non_tenté vers en_cours (une ligne, sinon on saute). Un second lancement du
  même lot est refusé si un travail `brouillons_lot` est actif pour ce
  `batch_id` (verrou asyncio par lot). Test : deux POST simultanés.
- Travail du registre `brouillons_lot`, `entity_id = batch_id`, adaptateur
  `AnnulationCooperative` : le drapeau est lu avant chaque contact, le
  brouillon en cours finit et s'enregistre, fin CANCELLED « 7 créés, 5 non
  tentés ». Libellé, étape et erreur du travail ne portent que des compteurs
  (jamais un nom : le panneau Travaux n'est pas masqué).
- Fournisseur : `create_drafts(demandes)` ouvre UNE session IMAP, résout le
  dossier Brouillons une fois et dépose en boucle ; Gmail en séquentiel.
  Arrêt au premier échec d'authentification, de quota ou de dossier, et après
  3 échecs réseau consécutifs ; le reste passe `non_tenté`. Sur 429 Gmail, un
  seul nouvel essai, attente croissante.
- Causes classées par code, chacune avec un libellé écrit : auth, quota,
  réseau, délai_incertain, adresse_invalide, champ_invalide,
  dossier_introuvable. Seuls réseau et quota sont réessayables. Journal :
  `type(e).__name__` et `contact_id`, jamais l'objet, le corps ni l'adresse.
- Délai dépassé = **incertain** (le brouillon peut exister), exclu de la
  reprise, avec la consigne « vérifie tes Brouillons ». Message-ID déterministe
  par (`batch_id`, `contact_id`) posé sur chaque brouillon ; la recherche par
  Message-ID avant reprise d'un incertain est une suite possible, hors V1.
- Redémarrage : un élément `en_cours` devient `incertain`.
- « Aucun envoi » testé en profondeur : espions sur `aiosmtplib.send`,
  `GmailService.send_message`, toute URL contenant `/send`, et `send_message`
  des deux fournisseurs.

## Écran

- Dans « Nouveau message » (rédaction libre), groupe radio « Un destinataire »
  / « Plusieurs contacts (un brouillon chacun) ». Titre de section
  « Brouillon » en rédaction libre, « Modèle du lot » en mode plusieurs.
- Assistant à une étape visible à la fois (Contacts, Modèle, Aperçu,
  Création, Compte rendu) ; focus sur le titre de l'étape à chaque changement.
- Contacts : `fieldset` + `legend`, recherche, étiquette, cases ; plafond
  expliqué, cases en `aria-disabled` au-delà ; compteur annoncé en
  `aria-live="polite"`.
- Modèle : aide qui liste les quatre champs du contact ; `jetonsMalFormes`
  en direct.
- Aperçu : « Aperçu pour <nom masqué> (1 / 12) », précédent et suivant nommés
  par le destinataire, annonce polie ; contacts bloqués listés avec
  « Retirer du lot » et « Retirer les N bloqués ». Mention « sans
  signature » (voir « À trancher »).
- Création : confirmation **fail-closed**, dans le panneau (pas
  `requestExternalAction`, fail-open par conception) : « 12 brouillons seront
  créés dans la boîte … ; rien ne sera envoyé ». Test sans fournisseur de
  confirmation : aucun POST.
- Compte rendu : état du lot dans un store, rechargeable par
  `GET …/batch/{id}` ; entrée « Voir le compte rendu » depuis Travaux ; un
  lot des dernières 24 h qui a déjà créé un brouillon pour un des contacts
  choisis est signalé au lancement.
- Saisie en cours : le panneau s'inscrit dans `saisieEnCours` dès qu'un
  contact est coché ou le modèle modifié (B-978).
- Mode démo : `maskContact` sur chaque ligne (liste, bloqués, en-tête
  d'aperçu, compte rendu), `populateMap` sur les contacts du lot avant tout
  `maskText` du texte résolu, fiches d'entreprise comprises (B-1075) ;
  bouton « Créer » visible mais inactif, avec la raison (patron de
  `ProjectModal`, `fieldset disabled`).

## Tests prévus

Moteur : résolution (espace de noms, "", "  ", None, homonyme de Variable),
contact bloqué, lot refusé sur jeton inconnu ou mal formé, objet assaini,
bornes, plafond 50/51, 202, deux POST simultanés, réservation, reprise des
seuls réessayables, incertain exclu, annulation coopérative, redémarrage,
aucun envoi (espions profonds), candidats filtrés et compteurs, empreinte
périmée. Écran : bascule, assistant au clavier de bout en bout, plafond,
aperçu navigable et annoncé, bloqués, confirmation fail-closed, compte rendu
rechargé, masque démo arrivé directement par « Écrire », nom de « Écrire ».

## Réponses aux questions de la V1

1. Champ vide : blocage, sans syntaxe de repli (elle ne serait ni résolue ni
   signalée aujourd'hui).
2. Plafond : 50, constante serveur unique.
3. Délai : pas de délai fixe ; une session IMAP par lot et un disjoncteur.
4. Survie à la fermeture : oui, par la réponse 202, la table des éléments et
   le compte rendu relisible hors du panneau.

## À trancher par Ludo

1. **Libellé visible du verbe de l'établi.** Recommandé : « Écrire un e-mail »
   visible (les pastilles passent à la ligne), repris dans la palette et dans
   le titre de la surface (E3 étendu au nom accessible). Alternative : garder
   « Écrire » et ajouter « un e-mail » au seul nom accessible et à l'infobulle.
2. **Signature.** THÉRÈSE ne l'ajoute qu'à l'envoi. Ajouter la signature texte
   du compte à chaque brouillon, ou afficher « sans signature » dans l'aperçu ?
3. **RGPD.** Contacts à exclure ou à signaler : archivés (exclus par défaut,
   recommandé), consentement expiré, base légale vide. Bloquer ou seulement
   avertir ? Portée : globale seule en V1 (recommandé) ?
4. **Espace de noms `{contact_prenom}`** : décidé ici pour ne jamais écraser
   une Variable de l'utilisateur ; plus long à taper que `{prenom}`. À
   confirmer.

## Revue de la V2 (24/09/2026) : NO-GO, V3 au cycle 13

Relecture adverse par un rôle Claude séparé (Codex et Grok indisponibles),
rapport complet dans `docs/plans/revues/2026-09-24-p096-revue-v2.md`.
Un P1 bloque : la reprise d'un lot arrêté n'a rien pour recréer les
brouillons, puisque le moteur ne garde ni l'objet, ni le corps, ni le compte.
Les autres constats (P2 et P3) sont techniques et seront repris dans la V3 :
une session IMAP avec un dépôt par appel, « incertain » pour toute erreur
survenue après l'envoi, préfixe `contact_` réservé, table de masquage propre
au panneau, garde de saisie branchée sur la fermeture et Échap, `batch_id`
généré par le moteur, migration Alembic complète, purge des éléments.

Le code n'est pas commencé : la règle maison est de faire accepter le design
avant d'écrire le code.

### Décisions supplémentaires pour Ludo (en plus des quatre ci-dessus)

5. **Conservation du modèle pour la reprise.** (a) Le moteur garde le modèle
   non résolu (jetons compris) jusqu'à la fin du lot, plus quelques jours ;
   la promesse « aucun corps en base » devient « aucun corps personnalisé en
   base ». (b) Ou « Reprendre » exige que l'écran renvoie le modèle ; après
   un redémarrage, il faut le recoller. Recommandé : (a), plus simple à vivre.
6. **Signalement « déjà écrit il y a moins de 24 h ».** Bloquer le contact ou
   seulement avertir ? Recommandé : avertir, contact décoché par défaut.
7. **Trace sur la fiche.** Un brouillon créé laisse-t-il une activité sur la
   fiche contact (et met-il à jour la dernière interaction) ? Recommandé :
   non tant qu'il n'est pas envoyé.
8. **Durée de conservation des éléments du lot.** Recommandé : 30 jours,
   comme les travaux, et effacement à la suppression ou à l'anonymisation du
   contact.
9. **Saisie en ligne d'un champ manquant.** La V1 la proposait, la V2 l'a
   retirée sans le dire. Recommandé : non en V1, le contact reste bloqué avec
   un lien vers sa fiche.
10. **Signature, options réelles.** Il n'existe pas de signature texte, seule
    une signature HTML. Trois choix : sans signature ; signature HTML
    convertie en texte (images et liens perdus) ; corps en HTML avec
    échappement des champs. Recommandé : sans signature, dit dans l'aperçu.
11. **Réponses de la V1 à confirmer.** Blocage d'un champ vide sans repli
    (une fiche d'entreprise sans prénom est alors bloquée dès que le modèle
    contient `{contact_prenom}`), et plafond de 50 par lot : ce sont des
    recommandations du relecteur, pas encore des décisions.
