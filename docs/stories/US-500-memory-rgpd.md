Parfait! Maintenant je vais compiler les user stories complètes:

## User Stories - Modules Mémoire et RGPD

J'ai parcouru tous les fichiers pertinents du projet THÉRÈSE. Voici les user stories reconstructites pour les modules **Mémoire** (contacts, projets, recherche sémantique) et **RGPD** (export, anonymisation, suppression):

---

### US-500 : Créer un nouveau contact en mémoire
**En tant que** solopreneur/TPE
**Je veux** ajouter rapidement un nouveau contact à ma mémoire
**Afin de** centraliser les informations de mes clients et prospects

**Critères d'acceptation :**
- [ ] Le formulaire modal permet de remplir : prénom, nom, entreprise, email, téléphone, notes, tags
- [ ] Validation : prénom OU nom requis
- [ ] Validation email : format valide si fourni
- [ ] Tags séparés par des virgules, stockés en JSON
- [ ] Contact créé avec stage par défaut (CRM)
- [ ] Score initial calculé automatiquement
- [ ] Embedding généré automatiquement dans Qdrant pour recherche sémantique
- [ ] Audit log enregistré (CONTACT_CREATED)

**Composants :** 
- src/frontend/src/components/memory/ContactModal.tsx
- src/backend/app/routers/memory.py (POST /contacts)
- src/backend/app/services/qdrant.py

**data-testid :** N/A (pas de testid dans ContactModal)

---

### US-501 : Modifier un contact existant
**En tant que** solopreneur/TPE
**Je veux** mettre à jour les informations d'un contact
**Afin de** garder ma base de contacts à jour

**Critères d'acceptation :**
- [ ] Modal s'ouvre en mode édition avec les données existantes
- [ ] Tous les champs (prénom, nom, entreprise, email, téléphone, notes, tags) sont modifiables
- [ ] Validation identique à la création
- [ ] Timestamp updated_at mis à jour
- [ ] last_interaction mis à jour
- [ ] Score recalculé si champs pertinents modifiés (email, phone, company, stage, source)
- [ ] Embedding Qdrant re-généré avec les nouvelles données
- [ ] Audit log enregistré (CONTACT_UPDATED) avec liste des champs modifiés

**Composants :** 
- src/frontend/src/components/memory/ContactModal.tsx
- src/backend/app/routers/memory.py (PATCH /contacts/{contact_id})
- src/backend/app/services/scoring.py

**data-testid :** N/A

---

### US-502 : Supprimer un contact avec cascade optionnel
**En tant que** solopreneur/TPE
**Je veux** supprimer un contact et optionnellement ses projets et fichiers associés
**Afin de** nettoyer ma mémoire des contacts obsolètes

**Critères d'acceptation :**
- [ ] Modal de confirmation affiche le nom du contact
- [ ] Bouton de suppression présent dans ContactModal
- [ ] Paramètre cascade=true supprime aussi : projects liés, fichiers avec scope=contact
- [ ] Embedding supprimé de Qdrant
- [ ] Audit log enregistré (CONTACT_DELETED) avec détails cascade
- [ ] Suppression immédiate visible dans la liste

**Composants :** 
- src/frontend/src/components/memory/ContactModal.tsx (bouton Supprimer ligne 321)
- src/backend/app/routers/memory.py (DELETE /contacts/{contact_id})

**data-testid :** N/A

---

### US-503 : Lister tous les contacts avec pagination
**En tant que** solopreneur/TPE
**Je veux** voir la liste de tous mes contacts
**Afin de** y accéder rapidement

**Critères d'acceptation :**
- [ ] Endpoint retourne 50 contacts max par défaut (limit, offset queryable)
- [ ] Triés par updated_at DESC
- [ ] Chaque contact affiche : avatar avec initiales, prénom+nom, entreprise (si remplie), email
- [ ] Badge RGPD affiche l'état (C/CT/IL/OL ou ? si non défini)
- [ ] Avatar cliquable ouvre modal d'édition
- [ ] Hover affiche boutons : menu RGPD (shield) + supprimer (trash)

**Composants :** 
- src/frontend/src/components/memory/MemoryPanel.tsx (ContactsList ligne 524)
- src/backend/app/routers/memory.py (GET /contacts)

**data-testid :** `memory-panel`, `memory-add-contact-btn`

---

### US-504 : Rechercher des contacts par keyword
**En tant que** solopreneur/TPE
**Je veux** chercher rapidement un contact par nom, email ou entreprise
**Afin de** retrouver une personne sans scroller la liste

**Critères d'acceptation :**
- [ ] Champ de recherche filtre en temps réel (client-side)
- [ ] Recherche sur : first_name, last_name, company, email (insensible à la casse)
- [ ] Liste mise à jour dynamiquement
- [ ] Placeholder : "Rechercher..."

**Composants :** 
- src/frontend/src/components/memory/MemoryPanel.tsx (ligne 236-243)

**data-testid :** `memory-search-input`

---

### US-505 : Filtrer les contacts par scope (E3-05)
**En tant que** solopreneur/TPE
**Je veux** voir les contacts filtrés par scope (Global, Projet, Conversation)
**Afin de** contextualiser ma mémoire

**Critères d'acceptation :**
- [ ] Pills de filtrage : Tout, Global, Projet, Conv.
- [ ] Si Tout → tous les contacts
- [ ] Si Global → scope=global + include_global=true
- [ ] Si Projet/Conv → scope spécifique + contacts globaux
- [ ] État du filtre persisté en state
- [ ] Chargement des données au changement de scope

**Composants :** 
- src/frontend/src/components/memory/MemoryPanel.tsx (ligne 246-260)
- src/backend/app/routers/memory.py (GET /contacts?scope=...)

**data-testid :** N/A

---

### US-506 : Créer un nouveau projet
**En tant que** solopreneur/TPE
**Je veux** créer un projet lié optionnellement à un contact
**Afin de** suivre mes missions

**Critères d'acceptation :**
- [ ] Modal projet avec : nom (obligatoire), description, contact (dropdown), statut, budget, notes, tags
- [ ] Statuts : Actif, En attente, Terminé, Annulé
- [ ] Budget en € (nombre, optionnel)
- [ ] Tags séparés par virgules
- [ ] Contact lié optionnel (validé en BDD)
- [ ] Embedding généré dans Qdrant
- [ ] Audit log (PROJECT_CREATED)
- [ ] Status=active par défaut

**Composants :** 
- src/frontend/src/components/memory/ProjectModal.tsx
- src/backend/app/routers/memory.py (POST /projects)

**data-testid :** N/A

---

### US-507 : Modifier un projet
**En tant que** solopreneur/TPE
**Je veux** mettre à jour les détails d'un projet
**Afin de** refléter les changements

**Critères d'acceptation :**
- [ ] Tous les champs modifiables
- [ ] Validation : nom requis, budget doit être nombre valide
- [ ] updated_at mis à jour
- [ ] Embedding Qdrant re-généré
- [ ] Audit log (PROJECT_UPDATED)

**Composants :** 
- src/frontend/src/components/memory/ProjectModal.tsx
- src/backend/app/routers/memory.py (PATCH /projects/{project_id})

**data-testid :** N/A

---

### US-508 : Supprimer un projet
**En tant que** solopreneur/TPE
**Je veux** supprimer un projet obsolète
**Afin de** nettoyer ma liste

**Critères d'acceptation :**
- [ ] Modal de confirmation affiche le nom du projet
- [ ] Paramètre cascade=true supprime fichiers associés (scope=project)
- [ ] Embedding supprimé de Qdrant
- [ ] Audit log (PROJECT_DELETED)

**Composants :** 
- src/frontend/src/components/memory/ProjectModal.tsx
- src/backend/app/routers/memory.py (DELETE /projects/{project_id})

**data-testid :** N/A

---

### US-509 : Afficher les projets en vue Kanban
**En tant que** solopreneur/TPE
**Je veux** voir mes projets organisés par statut (Kanban vertical)
**Afin de** visualiser mon pipeline

**Critères d'acceptation :**
- [ ] 4 colonnes : Actif, En attente, Terminé, Annulé
- [ ] Chaque colonne affiche nombre de projets
- [ ] Cartes affichent : nom, description (optionnelle), budget si > 0
- [ ] Drag & drop pour changer de statut
- [ ] Hover : bouton supprimer + icône chevron
- [ ] Clique sur carte : édition
- [ ] Empty state par colonne : "Glisser ici"
- [ ] Statut normalisé : 'pending' → 'on_hold'

**Composants :** 
- src/frontend/src/components/memory/ProjectsKanban.tsx
- @dnd-kit pour drag & drop

**data-testid :** N/A

---

### US-510 : Chercher des contacts/projets via recherche sémantique
**En tant que** solopreneur/TPE
**Je veux** chercher mes contacts et projets par concept (pas juste mots-clés)
**Afin de** retrouver l'info même avec d'autres termes

**Critères d'acceptation :**
- [ ] Endpoint POST /search accepte query + entity_types optionnels
- [ ] Phase 1 : recherche sémantique Qdrant (nomic-embed-text-v1.5, score_threshold=0.5)
- [ ] Phase 2 : fallback keyword search SQL (ILIKE) si sémantique échoue
- [ ] Résultats fusionnés, triés par score DESC
- [ ] Limite configurable (defaut 10)
- [ ] Temps d'exécution mesuré
- [ ] Chaque résultat : id, entity_type, title, content, score, metadata

**Composants :** 
- src/backend/app/routers/memory.py (POST /search ligne 143)
- src/backend/app/services/qdrant.py (async_search)
- src/backend/app/services/embeddings.py (embed_text)

**data-testid :** N/A

---

### US-511 : Ajouter des fichiers à un projet
**En tant que** solopreneur/TPE
**Je veux** attacher des documents (PDF, Excel, Word) à un projet
**Afin de** centraliser les ressources

**Critères d'acceptation :**
- [ ] Bouton upload visible uniquement en mode édition (projet existant)
- [ ] Formats acceptés : .md, .txt, .csv, .xlsx, .pdf, .docx
- [ ] Multiple files supporté
- [ ] Liste des fichiers affiche : nom, extension, taille
- [ ] Bouton supprimer pour chaque fichier
- [ ] Upload indique "Upload en cours..." pendant traitement

**Composants :** 
- src/frontend/src/components/memory/ProjectModal.tsx (ligne 384-434)
- src/backend/app/routers/memory.py (GET /projects/{project_id}/files)

**data-testid :** N/A

---

### US-512 : Exporter les données d'un contact (RGPD Art. 20)
**En tant que** solopreneur/TPE
**Je veux** exporter les données d'un contact au format JSON
**Afin de** respecter le droit de portabilité RGPD

**Critères d'acceptation :**
- [ ] Menu RGPD (shield) → Exporter (Art. 20)
- [ ] Modal de confirmation affiche le nom du contact
- [ ] Export téléchargé : `rgpd-export-{firstname}-{id}.json`
- [ ] Contenu : contact, activities[], projects[], tasks[], exported_at
- [ ] Audit log : DATA_EXPORTED

**Composants :** 
- src/frontend/src/components/memory/MemoryPanel.tsx (ligne 76-95, 377-411)
- src/backend/app/routers/rgpd.py (GET /export/{contact_id} ligne 38)

**data-testid :** N/A

---

### US-513 : Anonymiser un contact (RGPD Art. 17 - Droit à l'oubli)
**En tant que** solopreneur/TPE
**Je veux** anonymiser complètement un contact
**Afin de** respecter le droit à l'oubli RGPD

**Critères d'acceptation :**
- [ ] Menu RGPD → Anonymiser (Art. 17)
- [ ] Modal demande la RAISON (obligatoire)
- [ ] Avertissement : "Action irréversible"
- [ ] À la confirmation :
  - Prénom → [ANONYMISÉ]
  - Nom → null
  - Email, téléphone, notes, tags → null
  - Entreprise → [ANONYMISÉ]
  - Stage → archive
  - Activities supprimées
  - Projects + Tasks supprimées
- [ ] Activity log ajoutée : type=rgpd_anonymization avec raison
- [ ] Embedding supprimé de Qdrant
- [ ] Audit log : DATA_ANONYMIZED (via Activity)

**Composants :** 
- src/frontend/src/components/memory/MemoryPanel.tsx (ligne 97-114, 414-458)
- src/backend/app/routers/rgpd.py (POST /anonymize/{contact_id} ligne 155)

**data-testid :** N/A

---

### US-514 : Renouveler le consentement RGPD
**En tant que** solopreneur/TPE
**Je veux** renouveler le consentement d'un contact pour 3 ans
**Afin de** prolonger la relation commerciale conforme au RGPD

**Critères d'acceptation :**
- [ ] Menu RGPD → Renouveler consentement
- [ ] Modal affiche : nom contact + notice "Prolonger de 3 ans"
- [ ] À la confirmation :
  - rgpd_base_legale → consentement
  - rgpd_date_collecte → today
  - rgpd_date_expiration → today + 3 ans
  - rgpd_consentement → true
  - updated_at → now
- [ ] Activity log : type=rgpd_consent_renewal
- [ ] Audit log
- [ ] Alert de succès affiche nouvelle date d'expiration

**Composants :** 
- src/frontend/src/components/memory/MemoryPanel.tsx (ligne 116-129, 461-496)
- src/backend/app/routers/rgpd.py (POST /renew-consent/{contact_id} ligne 246)

**data-testid :** N/A

---

### US-515 : Afficher le badge RGPD et alertes d'expiration
**En tant que** solopreneur/TPE
**Je veux** voir rapidement l'état RGPD de chaque contact
**Afin de** identifier ceux qui expirent bientôt

**Critères d'acceptation :**
- [ ] Badge par contact affiche : C (Consentement), CT (Contrat), IL (Intérêt légitime), OL (Obligation légale), ? (non défini)
- [ ] Couleurs : consentement=vert, contrat=bleu, IL=purple, OL=gris, expiré=rouge, expireSoon=orange
- [ ] Expiration prochaine = <= 30 jours → badge orange avec ⚠
- [ ] Expiré = < today → badge rouge avec !
- [ ] Hover affiche texte complet + date d'expiration
- [ ] Banner d'alerte en haut du panel : "X contact(s) RGPD expire(nt) bientôt"
- [ ] Lien vers RGPD stats

**Composants :** 
- src/frontend/src/components/memory/MemoryPanel.tsx (RGPDBadge ligne 643-695, Alert ligne 265-274)
- src/backend/app/routers/rgpd.py (GET /stats ligne 476)

**data-testid :** N/A

---

### US-516 : Afficher les statistiques RGPD globales
**En tant que** solopreneur/TPE
**Je veux** voir un dashboard RGPD avec statistiques
**Afin de** gérer ma conformité

**Critères d'acceptation :**
- [ ] Endpoint GET /stats retourne :
  - total_contacts
  - par_base_legale (consentement, contrat, interet_legitime, obligation_legale, non_defini)
  - sans_info_rgpd (count)
  - expires_ou_bientot (count, <= 30 jours)
  - avec_consentement (count)
- [ ] Calcul performant en mémoire (pas de requête par contact)

**Composants :** 
- src/frontend/src/services/api/rgpd.ts (getRGPDStats)
- src/backend/app/routers/rgpd.py (GET /stats ligne 476)

**data-testid :** N/A

---

### US-517 : Mettre à jour manuellement les champs RGPD
**En tant que** solopreneur/TPE
**Je veux** modifier la base légale et le consentement d'un contact
**Afin de** corriger l'état RGPD si nécessaire

**Critères d'acceptation :**
- [ ] Endpoint PATCH /rgpd/{contact_id} accepte :
  - rgpd_base_legale (consentement|contrat|interet_legitime|obligation_legale)
  - rgpd_consentement (bool)
- [ ] Validation : base légale doit être dans la liste valide
- [ ] Auto-set dates si NULL :
  - rgpd_date_collecte → created_at ou now
  - rgpd_date_expiration → rgpd_date_collecte + 3 ans
- [ ] updated_at mis à jour

**Composants :** 
- src/backend/app/routers/rgpd.py (PATCH /{contact_id} ligne 301)

**data-testid :** N/A

---

### US-518 : Inférer automatiquement la base légale RGPD
**En tant que** solopreneur/TPE
**Je veux** que la base légale soit déduite automatiquement du stage du contact
**Afin de** simplifier la conformité

**Critères d'acceptation :**
- [ ] Endpoint POST /infer/{contact_id}
- [ ] Logique :
  - rgpd_consentement=true → consentement
  - stage in [active, signature, delivery] → contrat
  - else → intérêt légitime
- [ ] Expiration :
  - contrat → +5 ans (obligation comptable)
  - other → +3 ans après collecte
- [ ] Dates auto-set si NULL
- [ ] Réponse : success, base_legale, date_expiration

**Composants :** 
- src/backend/app/routers/rgpd.py (POST /infer/{contact_id} ligne 545)

**data-testid :** N/A

---

### US-519 : Exporter TOUTES les données de l'utilisateur
**En tant que** solopreneur/TPE
**Je veux** télécharger un export JSON complet de mes données
**Afin de** sauvegarder ou migrer

**Critères d'acceptation :**
- [ ] Endpoint GET /export
- [ ] Contenu : contacts, projects, conversations, messages, files, preferences (sans API keys), board_decisions, activity_logs (1000 derniers)
- [ ] API keys redactées en [REDACTED]
- [ ] Filename : `therese-export-{timestamp}.json`
- [ ] Audit log : DATA_EXPORTED

**Composants :** 
- src/backend/app/routers/data.py (GET /export ligne 59)

**data-testid :** N/A

---

### US-520 : Supprimer TOUTES les données utilisateur
**En tant que** solopreneur/TPE
**Je veux** supprimer intégralement mes données
**Afin de** exercer mon droit à l'oubli complet

**Critères d'acceptation :**
- [ ] Endpoint DELETE /all?confirm=true (double confirmation requise)
- [ ] Supprime en ordre (FK d'abord) : CodeChange, AgentMessage, AgentTask, InvoiceLine, Invoice, CalendarEvent, Calendar, EmailLabel, EmailMessage, EmailAccount, Task, Deliverable, Activity, PromptTemplate, Message, Conversation, Project, Contact, FileMetadata, BoardDecisionDB
- [ ] Supprime aussi les API keys dans Preferences
- [ ] Conservation volontaire : logs d'audit (trace légale)
- [ ] Purge collection Qdrant
- [ ] Audit log final : DATA_DELETED_ALL
- [ ] Réponse : message "Toutes vos données ont été supprimées conformément au RGPD Art. 17"

**Composants :** 
- src/backend/app/routers/data.py (DELETE /all ligne 312)

**data-testid :** N/A

---

### US-521 : Créer une sauvegarde manuelle des données
**En tant que** solopreneur/TPE
**Je veux** créer une sauvegarde de ma base de données
**Afin de** protéger mes données en cas de problème

**Critères d'acceptation :**
- [ ] Endpoint POST /backup
- [ ] Copies le fichier DB dans ~/.therese/backups/{backup_name}.db
- [ ] Crée metadata JSON : created_at, app_version, db_path, backup_name
- [ ] Réponse : success, backup_name, path, created_at
- [ ] Audit log : DATA_EXPORTED (type=backup)

**Composants :** 
- src/backend/app/routers/data.py (POST /backup ligne 502)

**data-testid :** N/A

---

### US-522 : Lister et restaurer une sauvegarde
**En tant que** solopreneur/TPE
**Je veux** voir mes sauvegardes et en restaurer une
**Afin de** récupérer des données anciennes

**Critères d'acceptation :**
- [ ] GET /backups retourne liste des backups avec : created_at, app_version, db_path, size_bytes, exists
- [ ] POST /restore/{backup_name}?confirm=true
  - Validation du nom (alphanumérique, tirets, underscores, points)
  - Vérification chemin dans /backups (SEC-019)
  - Crée sauvegarde de l'état actuel (pre_restore_*)
  - Restaure DB
  - En cas d'erreur : rollback vers pre_restore_*
- [ ] Réponse : success, restored_from, restored_at, backup_metadata, safety_backup, note="Redémarrez l'application"

**Composants :** 
- src/backend/app/routers/data.py (GET /backups ligne 557, POST /restore/{backup_name} ligne 593)

**data-testid :** N/A

---

### US-523 : Suppression et suppression de sauvegardes
**En tant que** solopreneur/TPE
**Je veux** supprimer une sauvegarde obsolète
**Afin de** économiser de l'espace disque

**Critères d'acceptation :**
- [ ] DELETE /backups/{backup_name}
- [ ] Validation chemin (SEC-019)
- [ ] Supprime .db et .json
- [ ] Réponse : deleted=true

**Composants :** 
- src/backend/app/routers/data.py (DELETE /backups/{backup_name} ligne 665)

**data-testid :** N/A

---

### US-524 : Importer des conversations depuis export
**En tant que** solopreneur/TPE
**Je veux** importer mes conversations depuis un export antérieur
**Afin de** migrer ou restaurer des conversations

**Critères d'acceptation :**
- [ ] Endpoint POST /import/conversations
- [ ] Format attendu : { conversations: [ { id?, title, messages: [ {role, content, created_at?} ] } ] }
- [ ] Skip conversations qui existent déjà (by ID)
- [ ] Crée Conversation + Messages
- [ ] Réponse : success, imported { conversations, messages }

**Composants :** 
- src/backend/app/routers/data.py (POST /import/conversations ligne 698)

**data-testid :** N/A

---

### US-525 : Importer des contacts depuis export
**En tant que** solopreneur/TPE
**Je veux** importer des contacts depuis un export JSON
**Afin de** restaurer ou merger des données

**Critères d'acceptation :**
- [ ] Endpoint POST /import/contacts
- [ ] Format : { contacts: [ { id?, first_name, last_name, company, email, phone, notes, tags } ] }
- [ ] Skip contacts existants (by ID)
- [ ] Crée Contact avec tags JSON-encoded
- [ ] Réponse : success, imported (count)

**Composants :** 
- src/backend/app/routers/data.py (POST /import/contacts ligne 749)

**data-testid :** N/A

---

### US-526 : Afficher le statut des sauvegardes et recommandations
**En tant que** solopreneur/TPE
**Je veux** savoir quand ma dernière sauvegarde date
**Afin de** de ne pas oublier de sauvegarder

**Critères d'acceptation :**
- [ ] Endpoint GET /backup/status
- [ ] Retourne : has_backups, last_backup (metadata), days_since_backup, recommendation
- [ ] Recommandations :
  - > 7 jours : "Pensez à en créer une nouvelle"
  - > 1 jour : "Dernière sauvegarde il y a N jours"
  - Aucune : "Aucune sauvegarde. Créez-en une maintenant."

**Composants :** 
- src/backend/app/routers/data.py (GET /backup/status ligne 788)

**data-testid :** N/A

---

### US-527 : Exporter les conversations en Markdown
**En tant que** solopreneur/TPE
**Je veux** exporter mes conversations en format Markdown
**Afin de** les relire facilement ou les intégrer ailleurs

**Critères d'acceptation :**
- [ ] Endpoint GET /export/conversations?format=markdown
- [ ] Produit `.md` avec : titre, date, messages au format "**Vous** : ... **THÉRÈSE** : ..."
- [ ] Filename : `therese-conversations-{date}.md`
- [ ] JSON par défaut si format!=markdown

**Composants :** 
- src/backend/app/routers/data.py (GET /export/conversations ligne 238)

**data-testid :** N/A

---

### US-528 : Voir les logs d'audit filtrés
**En tant que** solopreneur/TPE
**Je veux** consulter l'historique de mes actions (audit log)
**Afin de** tracer qui a modifié quoi et quand

**Critères d'acceptation :**
- [ ] Endpoint GET /logs?action=...&resource_type=...&limit=100&offset=0
- [ ] Filtre par AuditAction enum (contact_created, api_key_set, etc.)
- [ ] Filtre par resource_type (contact, project, rgpd, etc.)
- [ ] Retourne : logs[], total, limit, offset
- [ ] Chaque log : id, timestamp, action, resource_type, resource_id, details, ip_address, user_agent

**Composants :** 
- src/backend/app/routers/data.py (GET /logs ligne 397)
- src/backend/app/services/audit.py

**data-testid :** N/A

---

### US-529 : Lister les catégories d'actions audit
**En tant que** développeur/admin
**Je veux** voir les types d'actions audit disponibles
**Afin de** construire des filtres

**Critères d'acceptation :**
- [ ] Endpoint GET /logs/actions
- [ ] Retourne : actions (liste), categories { authentication, profile, data, conversations, files, rgpd, config, board, errors }

**Composants :** 
- src/backend/app/routers/data.py (GET /logs/actions ligne 455)

**data-testid :** N/A

---

### US-530 : Nettoyer les logs d'audit anciens
**En tant que** solopreneur/TPE
**Je veux** supprimer les logs datant de plus de N jours
**Afin de** économiser de l'espace disque

**Critères d'acceptation :**
- [ ] Endpoint DELETE /logs?days=90
- [ ] Supprime ActivityLog où timestamp < now - days
- [ ] Retourne : deleted_count, retention_days
- [ ] Par défaut : 90 jours

**Composants :** 
- src/backend/app/routers/data.py (DELETE /logs ligne 477)

**data-testid :** N/A

---

### US-531 : Paramétrer la purge automatique RGPD
**En tant que** solopreneur/TPE
**Je veux** configurer la purge automatique des contacts inactifs
**Afin de** respecter le RGPD sans intervention manuelle

**Critères d'acceptation :**
- [ ] GET /rgpd/purge/settings → { enabled, months (36 défaut) }
- [ ] PUT /rgpd/purge/settings?enabled=true&months=36
  - Validation : 12 <= months <= 60
- [ ] Stockage en Preference (rgpd_purge_enabled, rgpd_purge_months)
- [ ] Scheduler lancé à startup si enabled=true
- [ ] Supprime contacts sans interaction > months (sauf purge_excluded=true)

**Composants :** 
- src/backend/app/routers/rgpd.py (GET/PUT /purge/settings ligne 399-468)
- src/backend/app/main.py (_rgpd_purge_scheduler)

**data-testid :** N/A

---

### US-532 : Exclure un contact de la purge automatique
**En tant que** solopreneur/TPE
**Je veux** marquer un contact pour qu'il ne soit pas supprimé automatiquement
**Afin de** protéger les contacts stratégiques

**Critères d'acceptation :**
- [ ] Endpoint PATCH /rgpd/contacts/{contact_id}/purge-exclude
- [ ] Toggle : purge_excluded = !purge_excluded
- [ ] Réponse : success, purge_excluded, message ("Exclu de la purge" ou "Inclus")

**Composants :** 
- src/backend/app/routers/rgpd.py (PATCH /contacts/{contact_id}/purge-exclude ligne 357)

**data-testid :** N/A

---

### US-533 : Gestion du menu RGPD contextuel
**En tant que** solopreneur/TPE
**Je veux** accéder rapidement aux 3 actions RGPD depuis chaque contact
**Afin de** gérer la conformité directement

**Critères d'acceptation :**
- [ ] Bouton shield sur chaque ligne de contact
- [ ] Menu déroulant (dropdown) affiche :
  - Download : Exporter (Art. 20)
  - RefreshCw : Renouveler consentement
  - Separator
  - UserX : Anonymiser (Art. 17) - rouge
- [ ] Clique ouvre modal correspondant
- [ ] Menu se ferme après action

**Composants :** 
- src/frontend/src/components/memory/MemoryPanel.tsx (ContactsList, ligne 581-626)

**data-testid :** N/A

---

**Fichiers couverts :**

### Frontend:
- `/src/frontend/src/components/memory/MemoryPanel.tsx` - Panel principal, search, RGPD alerts
- `/src/frontend/src/components/memory/ContactModal.tsx` - Formulaire contact
- `/src/frontend/src/components/memory/ProjectModal.tsx` - Formulaire projet + upload fichiers
- `/src/frontend/src/components/memory/ProjectsKanban.tsx` - Vue Kanban drag & drop
- `/src/frontend/src/components/memory/MemoryPanelStandalone.tsx` - Panel projets standalone
- `/src/frontend/src/services/api/rgpd.ts` - API RGPD (export, anonymize, renew, stats)

### Backend:
- `/src/backend/app/routers/memory.py` - CRUD contacts/projets, recherche sémantique
- `/src/backend/app/routers/rgpd.py` - Export, anonymisation, consentement, inférence, purge
- `/src/backend/app/routers/data.py` - Export global, suppression, backup/restore, logs
- `/src/backend/app/services/qdrant.py` - Vector store (embeddings)
- `/src/backend/app/services/embeddings.py` - Sentence transformers (nomic-embed-text-v1.5)