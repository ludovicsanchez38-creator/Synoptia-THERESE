Excellent! Maintenant je vais générer les user stories complètes en me basant sur tous les fichiers que j'ai examinés:

## **USER STORIES - MODULE EMAIL THÉRÈSE v2**

Basé sur l'analyse du code source (frontend + backend), voici les user stories du module Email:

```markdown
### US-100 : Afficher la liste des emails avec priorités
**En tant que** solopreneur
**Je veux** voir la liste de mes emails avec un badge de priorité visuel
**Afin de** identifier rapidement les messages urgents

**Critères d'acceptation :**
- [ ] Chaque email affiche un emoji de priorité (🔴 urgent/🟠 important/🟢 normal)
- [ ] Badge contient le score de priorité sur hover
- [ ] Les emails non lus sont visuellement distincts (fond légèrement visible)
- [ ] Emails non lus affichent leur sender en gras
- [ ] L'icône étoile ⭐ indique les emails marqués "Favoris" (STARRED)
- [ ] Icône trombone visible si pièce jointe présente
- [ ] Date formatée (Hier, Mardi, 21 mars...)
- [ ] Bouton Supprimer visible au hover sur chaque email

**Composants :** EmailList.tsx, EmailPriorityBadge.tsx
**data-testid :** [À ajouter si nécessaire]

---

### US-101 : Rechercher et filtrer les emails
**En tant que** solopreneur
**Je veux** rechercher mes emails par contenu/sujet et filtrer par label
**Afin de** retrouver rapidement les messages pertinents

**Critères d'acceptation :**
- [ ] Barre de recherche en haut de la liste
- [ ] Appui sur Enter déclenche la recherche (ou auto-search avec délai)
- [ ] Filtre par label (Inbox, Brouillon, Envoyés, Poubelle, labels perso)
- [ ] Labels affichent le nombre de messages non lus en badge
- [ ] Recherche vide affiche tous les emails

**Composants :** EmailList.tsx, EmailPanel.tsx
**data-testid :** [À ajouter]

---

### US-102 : Consulter les détails d'un email
**En tant que** solopreneur
**Je veux** ouvrir un email et voir son contenu complet
**Afin de** lire et répondre au message

**Critères d'acceptation :**
- [ ] Clic sur email affiche le détail dans le panel droit
- [ ] Sujet affiché en titre avec badge priorité
- [ ] En-tête : From/To/Date formaté en français
- [ ] Corps HTML sanitisé (DOMPurify) sans scripts XSS
- [ ] Email automatiquement marqué comme lu
- [ ] Bouton retour (chevron left) referme le détail
- [ ] Boutons actions : Star, Supprimer

**Composants :** EmailDetail.tsx
**data-testid :** [À ajouter]

---

### US-103 : Rédiger un nouveau message
**En tant que** solopreneur
**Je veux** composer un email avec tous les champs classiques
**Afin de** envoyer des messages professionnels

**Critères d'acceptation :**
- [ ] Champ "À" avec support listes d'emails séparées par virgule
- [ ] Champ "Cc" et "Cci" masqués par défaut, affichés au clic "Cc/Cci"
- [ ] Champ "Objet" obligatoire
- [ ] Zone de texte pour le corps
- [ ] Support HTML optionnel (checkbox ou détection)
- [ ] Bouton "Envoyer" envoie immédiatement via API
- [ ] Bouton "Sauvegarder brouillon" crée un DRAFT dans Gmail
- [ ] Bouton "Joindre" désactivé (pré-implémentation)
- [ ] Confirmation avant abandon si contenu saisi
- [ ] Affichage des erreurs (pas de destinataire, etc.)

**Composants :** EmailCompose.tsx, emailStore.ts
**data-testid :** [À ajouter]

---

### US-104 : Envoyer un email avec CC et BCC
**En tant que** solopreneur
**Je veux** ajouter des destinataires en copie ou copie cachée
**Afin de** respecter les protocoles professionnels

**Critères d'acceptation :**
- [ ] Toggle "Cc/Cci" déroule les champs CC et BCC
- [ ] Champ CC accepte listes d'emails
- [ ] Champ BCC accepte listes d'emails
- [ ] API `/api/email/messages` accepte paramètres cc et bcc
- [ ] Emails CC/BCC ne sont envoyés que si liste non vide

**Composants :** EmailCompose.tsx
**data-testid :** [À ajouter]

---

### US-105 : Répondre à un email
**En tant que** solopreneur
**Je veux** répondre simplement à un message ou à tous les destinataires
**Afin de** poursuivre la conversation

**Critères d'acceptation :**
- [ ] Bouton "Répondre" pré-remplit le destinataire du sender
- [ ] Bouton "Répondre à tous" inclut tous les To + From
- [ ] Subject pré-rempli avec "Re: ..."
- [ ] Ouvre le composeur EmailCompose
- [ ] Historique du message pas inclus (c'est optionnel)

**Composants :** EmailDetail.tsx, EmailCompose.tsx
**data-testid :** [À ajouter]

---

### US-106 : Transférer un email
**En tant que** solopreneur
**Je veux** transférer un message à d'autres destinataires
**Afin de** partager des informations reçues

**Critères d'acceptation :**
- [ ] Bouton "Transférer" ouvre le composeur
- [ ] Subject pré-rempli "Fwd: ..."
- [ ] Corps contient en-tête du message original formaté
- [ ] Destinataires vides (à remplir manuellement)

**Composants :** EmailDetail.tsx, EmailCompose.tsx
**data-testid :** [À ajouter]

---

### US-107 : Marquer/dé-marquer un email en favori
**En tant que** solopreneur
**Je veux** marquer un email comme "Favori" (anciennes "Suivis")
**Afin de** créer une liste personnalisée de messages importants

**Critères d'acceptation :**
- [ ] Icône étoile cliquable dans EmailDetail
- [ ] Un clic ajoute label STARRED à Gmail
- [ ] Un second clic retire le label STARRED
- [ ] Star remplit de jaune si marqué
- [ ] Star vide de jaune si non marqué
- [ ] Label "Favoris" apparaît dans la liste des labels

**Composants :** EmailDetail.tsx, EmailList.tsx
**data-testid :** [À ajouter]

---

### US-108 : Afficher un badge de priorité avec score
**En tant que** solopreneur
**Je veux** voir un badge visuel qui indique la priorité et le score de chaque email
**Afin de** trier rapidement mes emails par importance

**Critères d'acceptation :**
- [ ] Badge 🔴 (high) pour les emails urgents/critiques
- [ ] Badge 🟠 (medium) pour les emails importants
- [ ] Badge 🟢 (low) pour les emails normaux/newsletters
- [ ] Score visible au hover (0-100)
- [ ] Affichage du texte "Urgent/Important/Normal" optionnel
- [ ] Les emails non classés n'affichent pas de badge (null)

**Composants :** EmailPriorityBadge.tsx, EmailList.tsx, EmailDetail.tsx
**data-testid :** [À ajouter]

---

### US-109 : Générer une réponse intelligente par IA
**En tant que** solopreneur
**Je veux** générer un brouillon de réponse automatique via IA
**Afin de** rédiger plus rapidement mes réponses professionnelles

**Critères d'acceptation :**
- [ ] Bouton "Générer une réponse" (icône Sparkles) ouvert dans EmailDetail
- [ ] Modal affiche 2 sections de paramètres : Ton et Longueur
- [ ] Ton : Formel / Amical / Neutre (3 boutons)
- [ ] Longueur : Court (2-3 phrases) / Moyen (1 paragraphe) / Détaillé (2-3 paragraphes)
- [ ] Zone textarea affiche le brouillon généré
- [ ] Bouton "Régénérer" relance avec même paramètres
- [ ] Bouton "Utiliser" remplit le composeur et ouvre EmailCompose
- [ ] Auto-génération au premier ouverture du modal
- [ ] Signature automatique avec nom de l'utilisateur

**Composants :** ResponseGeneratorModal.tsx, EmailDetail.tsx
**data-testid :** [À ajouter]

---

### US-110 : Paramétrer signature HTML email
**En tant que** solopreneur
**Je veux** ajouter une signature HTML personnalisée à mes emails
**Afin de** renforcer mon branding professionnel

**Critères d'acceptation :**
- [ ] Endpoint `PATCH /api/email/signature` accepte signature_html
- [ ] Signature auto-ajoutée à chaque email envoyé
- [ ] Support HTML (logo, couleurs, liens, mise en page)
- [ ] Sanitisation du HTML côté frontend
- [ ] Storage chiffré côté backend

**Composants :** [À implémenter - Settings Email]
**data-testid :** [À ajouter]

---

### US-111 : Configurer email via Gmail OAuth
**En tant que** solopreneur
**Je veux** connecter mon compte Gmail via OAuth Google sécurisé
**Afin de** utiliser THÉRÈSE sans partager mon mot de passe

**Critères d'acceptation :**
- [ ] Wizard affiche bouton "Gmail OAuth" (Recommandé)
- [ ] Étape 2 : Guide étape-à-étape pour créer un projet Google Cloud
- [ ] Étape 3 : Champs Client ID et Client Secret
- [ ] Validation des credentials contre l'API Google
- [ ] Bouton "Continuer" redirige vers OAuth consent Google
- [ ] Callback gère le code d'autorisation
- [ ] Tokens (access + refresh) chiffrés Fernet en DB
- [ ] Account créé avec email et scopes
- [ ] Support MCP Google Workspace (auto-détecte credentials)

**Composants :** EmailSetupWizard.tsx, GuideStep.tsx, CredentialsStep.tsx, VerifyStep.tsx
**data-testid :** [À ajouter]

---

### US-112 : Configurer email via SMTP/IMAP
**En tant que** solopreneur
**Je veux** connecter mon email via SMTP/IMAP classique
**Afin de** utiliser n'importe quel fournisseur (OVH, Gandi, etc.)

**Critères d'acceptation :**
- [ ] Wizard affiche bouton "SMTP Classique"
- [ ] Formulaire : Email / Mot de passe (app password)
- [ ] Dropdown providers avec configs pré-remplies (Gmail, OVH, Gandi, etc.)
- [ ] Champs IMAP host/port et SMTP host/port modifiables
- [ ] Bouton "Tester la connexion" avant de sauvegarder
- [ ] Mot de passe chiffré Fernet en DB
- [ ] Account créé après succès du test
- [ ] Gestion erreurs : serveur invalide, credentials, ports bloqués

**Composants :** SmtpConfigStep.tsx, EmailSetupWizard.tsx
**data-testid :** [À ajouter]

---

### US-113 : Découvrir le wizard de configuration email
**En tant que** solopreneur
**Je veux** parcourir un wizard guidé et intuitif pour configurer mon email
**Afin de** ne pas être bloqué par des questions techniques

**Critères d'acceptation :**
- [ ] Wizard affiché automatiquement si aucun compte email configuré
- [ ] Étape 1 : Choix du provider (Gmail OAuth vs SMTP)
- [ ] Étape 2 : Guide ou formulaire selon le choix
- [ ] Étape 3/4 : Credentials et vérification
- [ ] Progress bar visible en haut du wizard
- [ ] Bouton "Retour" pour revenir aux étapes précédentes
- [ ] Fermeture au clic X ou après succès
- [ ] Support MCP Google Workspace : auto-remplissage de credentials

**Composants :** EmailSetupWizard.tsx, ChoiceStep.tsx, GuideStep.tsx, CredentialsStep.tsx, VerifyStep.tsx, SmtpConfigStep.tsx
**data-testid :** [À ajouter]

---

### US-114 : Gérer plusieurs comptes email
**En tant que** solopreneur avec plusieurs emails
**Je veux** ajouter et basculer entre plusieurs comptes email
**Afin de** centraliser tous mes emails dans THÉRÈSE

**Critères d'acceptation :**
- [ ] Bouton "Ajouter un compte" dans le menu Account
- [ ] Dropdown pour changer de compte actif
- [ ] Chaque compte a son propre cache de messages et labels
- [ ] API retourne tous les comptes dans `/api/email/auth/status`
- [ ] Un seul compte sélectionné à la fois
- [ ] Messages refiltrés au changement de compte

**Composants :** EmailPanel.tsx, emailStore.ts
**data-testid :** [À ajouter]

---

### US-115 : Déconnecter un compte email
**En tant que** solopreneur
**Je veux** supprimer un compte email configuré dans THÉRÈSE
**Afin de** retirer l'accès ou changer de fournisseur

**Critères d'acceptation :**
- [ ] Menu "..." sur chaque compte affiche option "Déconnecter"
- [ ] Confirmation avant suppression
- [ ] DELETE `/api/email/auth/disconnect/{accountId}`
- [ ] Tokens supprimés de la base
- [ ] Gmail : révocation du access_token auprès de Google
- [ ] Account retiré du store

**Composants :** EmailPanel.tsx, emailStore.ts
**data-testid :** [À ajouter]

---

### US-116 : Gérer la réautorisation OAuth expirée
**En tant que** solopreneur
**Je veux** être notifié et réautoriser si mon token Gmail expirela
**Afin de** ne pas perdre l'accès à mes emails

**Critères d'acceptation :**
- [ ] Détection automatique token expiré (compare expiry > now)
- [ ] Refresh token appelé automatiquement (refresh_access_token)
- [ ] Si refresh échoue : bannière rouge "Connexion Gmail expirée"
- [ ] Bouton "Reconnecter" dans la bannière
- [ ] POST `/api/email/auth/reauthorize/{accountId}` relance OAuth flow
- [ ] Fallback : cherche credentials stockés sur account ou MCP

**Composants :** EmailPanel.tsx, EmailList.tsx, emailStore.ts
**data-testid :** [À ajouter]

---

### US-117 : Afficher les labels et filtrer par label
**En tant que** solopreneur
**Je veux** voir tous mes labels et filtrer la liste par label
**Afin de** organiser mes emails par catégorie

**Critères d'acceptation :**
- [ ] Sidebar affiche tous les labels (Inbox, Brouillon, Envoyés, Poubelle, personnalisés)
- [ ] Labels système : badge "Système" (gris)
- [ ] Labels personnalisés : éditable et supprimable
- [ ] Clic sur label filtre les emails
- [ ] Label sélectionné surligné visuellement
- [ ] Badge compte les non-lus par label
- [ ] Bouton "+" permet de créer un label personnalisé

**Composants :** EmailPanel.tsx, emailStore.ts
**data-testid :** [À ajouter]

---

### US-118 : Créer un label personnalisé
**En tant que** solopreneur
**Je veux** créer un label personnalisé pour organiser mes emails
**Afin de** classer mes emails selon ma logique

**Critères d'acceptation :**
- [ ] Bouton "Créer un label" dans le panel des labels
- [ ] Dialog simple : nom du label
- [ ] POST `/api/email/labels` crée le label
- [ ] Label apparaît immédiatement dans la liste
- [ ] Peut être appliqué à des emails après creation

**Composants :** EmailPanel.tsx
**data-testid :** [À ajouter]

---

### US-119 : Supprimer ou archiver un email
**En tant que** solopreneur
**Je veux** supprimer ou archiver un email
**Afin de** nettoyer ma boîte de réception

**Critères d'acceptation :**
- [ ] Icône corbeille au hover sur chaque email (EmailList)
- [ ] Clic appelle DELETE `/api/email/messages/{messageId}?account_id=...`
- [ ] Email retiré du store immédiatement
- [ ] Bouton Supprimer aussi visible dans EmailDetail
- [ ] Support du paramètre `permanent=false` (soft delete / Trash)
- [ ] Erreur auth affichée en bannière si échec

**Composants :** EmailList.tsx, EmailDetail.tsx
**data-testid :** [À ajouter]

---

### US-120 : Classification intelligente des emails
**En tant que** solopreneur
**Je veux** que chaque email soit automatiquement classé par importance
**Afin de** ne pas manquer les messages critiques

**Critères d'acceptation :**
- [ ] POST `/api/email/messages/{id}/classify` retourne priorité + score + category
- [ ] Priorités : high (🔴) / medium (🟠) / low (🟢)
- [ ] Catégories : Transactional / Administrative / Business / Promotional / Newsletter
- [ ] Scoring multi-facteur : sender, keywords, attachments, time-sensitivity
- [ ] Classification en arrière-plan (ne bloque pas le refresh)
- [ ] Emails déjà classés stockent le cache (cached=true)
- [ ] Forceage de re-classification possible

**Composants :** EmailList.tsx, email_classifier_v2.py
**data-testid :** [À ajouter]

---

### US-121 : Panel email en mode modal ou sidebar
**En tant que** solopreneur
**Je veux** ouvrir le panel email en modal (fullscreen) ou sidebar collapsible
**Afin de** avoir la flexibilité de travailler avec d'autres panneaux

**Critères d'acceptation :**
- [ ] Mode modal : layer fixe couvrant l'app, fermable avec X
- [ ] Mode sidebar : intégré dans le layout principal
- [ ] Toggle button pour ouvrir/fermer
- [ ] État persistant (localStorage via Zustand)
- [ ] Z-index approprié pour éviter chevauchements

**Composants :** EmailPanel.tsx, emailStore.ts
**data-testid :** [À ajouter]

---

### US-122 : Synchroniser les emails en arrière-plan
**En tant que** solopreneur
**Je veux** que mes emails se synchronisent automatiquement en arrière-plan
**Afin de** toujours avoir les messages les plus récents

**Critères d'acceptation :**
- [ ] Polling automatique toutes les 5-10 min (configurable)
- [ ] Indicateur "Mise à jour..." visible au top de la liste
- [ ] Erreur réseau non-bloquante si cache disponible
- [ ] Bouton Refresh manual
- [ ] Retry automatique en cas d'erreur (max 3 tentatives)

**Composants :** EmailList.tsx, EmailPanel.tsx
**data-testid :** [À ajouter]

---

### US-123 : Afficher le statut de connexion email
**En tant que** solopreneur
**Je veux** voir l'état de la connexion email (connecté, erreur, reconnecter)
**Afin de** savoir si je dois configurer/reconnecter un compte

**Critères d'acceptation :**
- [ ] Bannière verte : "Email connecté (user@example.com)"
- [ ] Bannière rouge : "Connexion Gmail expirée - Reconnecter"
- [ ] Bannière orange : "Erreur réseau - Réessai..."
- [ ] Bouton "Reconnecter" si token expiré
- [ ] Icône statut : ✓ / ⚠ / ✗

**Composants :** EmailPanel.tsx
**data-testid :** [À ajouter]

---

### US-124 : Supporter les pièces jointes (future)
**En tant que** solopreneur
**Je veux** télécharger et envoyer des pièces jointes
**Afin de** partager des fichiers par email

**Critères d'acceptation :**
- [ ] Icône trombone dans EmailCompose (actuellement désactivée)
- [ ] Clic ouvre sélecteur de fichiers
- [ ] Support max 25 MB par pièce (limite Gmail)
- [ ] Affichage des pièces jointes dans EmailDetail
- [ ] Icône trombone dans EmailList si pièces présentes

**Composants :** EmailCompose.tsx, EmailDetail.tsx, EmailList.tsx
**data-testid :** [À ajouter]

---

### US-125 : Lier un email à un contact CRM
**En tant que** solopreneur utilisant le CRM
**Je veux** lier un email à un contact ou une opportunité CRM
**Afin de** centraliser la communication dans mon pipeline

**Critères d'acceptation :**
- [ ] Bouton "Lier au CRM" ou dropdown dans EmailDetail
- [ ] Sélection du contact/opportunité
- [ ] POST `/api/email/messages/{id}/link-contact` sauvegarde la relation
- [ ] Email apparaît dans la timeline du contact
- [ ] Contexte CRM inclus dans email_response_generator

**Composants :** EmailDetail.tsx
**data-testid :** [À ajouter]

---

### US-126 : Obtenir des statistiques email
**En tant que** solopreneur
**Je veux** voir des stats : combien d'emails urgents, non lus, par catégorie
**Afin de** avoir une vue d'ensemble de ma boîte

**Critères d'acceptation :**
- [ ] GET `/api/email/messages/stats?account_id=...` retourne high/medium/low/total_unread/total
- [ ] Affichage optionnel : dashboard ou badge dans le header
- [ ] Mise à jour après chaque refresh

**Composants :** EmailPanel.tsx
**data-testid :** [À ajouter]

---

### US-127 : Valider les credentials OAuth avant envoi
**En tant que** développeur
**Je veux** que les credentials Google soient validés avant la création du compte
**Afin de** éviter les erreurs d'authentification

**Critères d'acceptation :**
- [ ] POST `/api/email/setup/validate` vérifie client_id + client_secret
- [ ] Retourne validation_result pour chaque champ
- [ ] Wizard bloque "Continuer" si invalide

**Composants :** CredentialsStep.tsx, email_setup_assistant.py
**data-testid :** [À ajouter]

---

### US-128 : Générer un guide de configuration Gmail
**En tant que** solopreneur
**Je veux** un guide étape-à-étape pour créer les credentials Google
**Afin de** ne pas être bloqué par des jargon technique

**Critères d'acceptation :**
- [ ] Wizard demande : "Avez-vous un projet Google Cloud existant ?"
- [ ] POST `/api/email/setup/guide` génère instructions IA
- [ ] Guide incluant : création projet, OAuth consent, scope permissions
- [ ] Rendu markdown ou HTML dans GuideStep

**Composants :** GuideStep.tsx, email_setup_assistant.py
**data-testid :** [À ajouter]

---

### US-129 : Listing des providers email pré-configurés
**En tant que** solopreneur SMTP
**Je veux** avoir accès à une liste de fournisseurs pré-configurés (OVH, Gandi, etc.)
**Afin de** ne pas avoir à chercher les paramètres IMAP/SMTP

**Critères d'acceptation :**
- [ ] GET `/api/email/providers` retourne liste de providers
- [ ] Chaque provider : nom, imap_host, imap_port, smtp_host, smtp_port
- [ ] SmtpConfigStep affiche dropdown avec providers populaires
- [ ] Sélection auto-remplit les champs IMAP/SMTP

**Composants :** SmtpConfigStep.tsx, provider_factory.py
**data-testid :** [À ajouter]

---

### US-130 : Marquer comme non-lu / lu
**En tant que** solopreneur
**Je veux** marquer manuellement un email comme lu ou non-lu
**Afin de** gérer mon flux de travail

**Critères d'acceptation :**
- [ ] Automatiquement marqué comme lu au clic sur EmailList
- [ ] Bouton toggle "Marquer comme non-lu" dans EmailDetail optionnel
- [ ] API : PUT `/api/email/messages/{id}` avec removeLabelIds=['UNREAD']

**Composants :** EmailDetail.tsx, EmailList.tsx
**data-testid :** [À ajouter]
```

---

## **RÉSUMÉ FONCTIONNALITÉS**

| Fonctionnalité | Status | Frontend | Backend |
|---|---|---|---|
| Liste emails avec priorités | ✓ | EmailList.tsx | classifier_v2.py |
| Détails email + actions | ✓ | EmailDetail.tsx | email.py |
| Composeur (To/Cc/Cci) | ✓ | EmailCompose.tsx | email.py |
| Réponse/Transfert | ✓ | EmailDetail.tsx | email.py |
| Favoris (Starred) | ✓ | EmailDetail.tsx, EmailList.tsx | email.py |
| Génération IA de réponses | ✓ | ResponseGeneratorModal.tsx | email_response_generator.py |
| Classification intelligente | ✓ | EmailList.tsx | email_classifier_v2.py |
| Badges priorité (high/medium/low) | ✓ | EmailPriorityBadge.tsx | classifier_v2.py |
| Wizard OAuth Gmail | ✓ | EmailSetupWizard.tsx | email.py |
| Wizard SMTP/IMAP | ✓ | SmtpConfigStep.tsx | email.py |
| Signature HTML | Partiel | - | schemas_email.py |
| Gestion tokens expiré | ✓ | EmailPanel.tsx | email.py |
| Plusieurs comptes | ✓ | emailStore.ts | email.py |
| Pièces jointes | Désactivé | EmailCompose.tsx | Futur |
| Lien CRM | Futur | - | - |

Tous les fichiers examinés se trouvent dans :
- **Frontend** : `/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/email/`
- **Backend** : `/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/`
- **Store** : `/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/stores/emailStore.ts`
- **API** : `/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/services/api/email.ts`