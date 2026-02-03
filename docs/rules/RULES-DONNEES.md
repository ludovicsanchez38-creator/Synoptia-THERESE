# Règles Données et Mémoire - THÉRÈSE V2

## Philosophie
THÉRÈSE est une application local-first. Toutes les données sont stockées sur la machine de l'utilisateur dans `~/.therese/`. Aucune donnée n'est envoyée à des serveurs tiers sauf les appels explicites aux APIs LLM.

## Stockage

### Répertoire de données
```
~/.therese/
├── therese.db              # Base SQLite principale
├── qdrant/                 # Données vectorielles Qdrant
├── mcp_servers.json        # Configuration MCP (chiffré)
├── config.json             # Préférences utilisateur
├── .session_token          # Token de session éphémère
├── .fernet_key             # Clé de chiffrement (fallback)
├── images/                 # Images générées
└── backups/                # Sauvegardes automatiques
```

### Base de données SQLite

#### Tables principales

| Table | Clé primaire | Description |
|-------|-------------|-------------|
| conversation | id (UUID) | Conversations de chat |
| message | id (UUID) | Messages (user/assistant/system) |
| contact | id (UUID) | Contacts avec métadonnées CRM |
| project | id (UUID) | Projets avec suivi |
| file_metadata | id (UUID) | Fichiers indexés pour RAG |
| preference | key (string) | Préférences clé/valeur |
| user_profile | id | Profil utilisateur (unique) |
| activity | id (UUID) | Journal d'audit RGPD |
| task | id (UUID) | Tâches |
| invoice | id (UUID) | Factures |
| email_account | id (UUID) | Comptes email configurés |
| email_message | id (UUID) | Messages email cachés |
| email_label | id (UUID) | Labels email |
| board_decision | id (UUID) | Historique des décisions Board |
| calendar_account | id (UUID) | Comptes calendrier |

#### Conventions de modèles SQLModel
```python
class Contact(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    first_name: str
    last_name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[str] = None  # JSON array stored as string
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    # CRM fields
    stage: Optional[str] = None  # prospect, lead, client, churned
    score: int = 0
    source: Optional[str] = None

    # RGPD fields
    base_legale: Optional[str] = None
    date_collecte: Optional[datetime] = None
    date_expiration: Optional[datetime] = None

    # Scope
    scope: str = "global"  # global | project | conversation
    scope_id: Optional[str] = None
```

#### Règles de modélisation
- UUID v4 comme clé primaire (jamais d'auto-increment)
- Timestamps : created_at (auto), updated_at (manuel)
- Champs JSON : stockés comme string, parsés en Python
- Optional pour tous les champs non-requis
- Cascade : suppression manuelle (pas de ON DELETE CASCADE SQLite)
- Pas d'index custom sauf nécessité prouvée par benchmark

### Base vectorielle Qdrant

#### Collections

| Collection | Dimensions | Distance | Contenu |
|-----------|-----------|----------|---------|
| therese_memory | 768 | Cosine | Contacts, projets, fichiers, web |

#### Modèle d'embeddings
- **Modèle** : nomic-ai/nomic-embed-text-v1.5
- **Dimensions** : 768
- **Framework** : sentence-transformers
- **Préchargement** : Au démarrage (async, fallback si échec)

#### Structure d'un point Qdrant
```json
{
  "id": "uuid-v4",
  "vector": [0.123, -0.456, ...],  // 768 dimensions
  "payload": {
    "entity_type": "contact",       // contact | project | file | web_search
    "entity_id": "uuid-du-contact",
    "text": "Jean Dupont - CEO Acme Corp",
    "metadata": { "tags": ["client"], "score": 85 }
  }
}
```

#### Règles Qdrant
- Embedding généré à chaque création/modification d'entité
- Suppression du point lors de la suppression de l'entité
- Recherche hybride : BM25 (SQLite FTS) + sémantique (Qdrant)
- Maximum 10 résultats par recherche
- Score minimum : 0.3 pour inclusion dans le contexte

## Système de mémoire

### Types de mémoire (taxonomie cognitive)
1. **Mémoire de travail** : Contexte de la conversation en cours (messages récents)
2. **Mémoire épisodique** : Historique des conversations passées
3. **Mémoire sémantique** : Contacts, projets, fichiers indexés (RAG)
4. **Mémoire procédurale** : Préférences utilisateur, templates de prompts

### Flux de recherche hybride
1. Requête utilisateur reçue
2. **Recherche sémantique** (Qdrant) : Embedding de la requête → Top K résultats
3. **Recherche par mots-clés** (SQLite) : FTS sur contacts/projets
4. **Fusion des résultats** : Ranking par score combiné
5. **Injection dans le prompt** : Top 5 résultats ajoutés au system prompt
6. **Le LLM a le contexte** : Répond avec connaissance des entités pertinentes

### Scope des entités
- **global** : Visible partout (défaut)
- **project** : Visible uniquement dans le contexte d'un projet
- **conversation** : Visible uniquement dans une conversation spécifique
- Cascade : Suppression du parent supprime les entités scoped

### Extraction automatique d'entités
1. Après chaque réponse du LLM
2. Analyse du contenu pour détecter contacts et projets
3. Seuil de confiance : 0.6
4. Déduplication contre les entités existantes (nom, email)
5. Suggestion à l'utilisateur via SSE
6. L'utilisateur valide ou ignore

## Fichiers indexés

### Formats supportés
- Texte : txt, md, json
- Code : py, js, ts, html, css
- Documents : pdf, docx
- Taille max : 10 MB

### Pipeline d'indexation
1. Upload ou drag-drop du fichier
2. Validation du chemin (sécurité anti-traversal)
3. Détection MIME type
4. Extraction du texte
5. Découpage en chunks (1000 caractères, 200 chevauchement)
6. Embedding de chaque chunk
7. Stockage dans Qdrant avec référence au fichier
8. Métadonnées en SQLite (FileMetadata)

### Règles de chunking
- Taille de chunk : 1000 caractères
- Chevauchement : 200 caractères
- Séparateurs : paragraphes > phrases > mots
- Métadonnées par chunk : position, fichier source, type

## Sauvegarde et export

### Sauvegarde automatique
- Format : Archive JSON contenant toutes les tables
- Stockage : ~/.therese/backups/
- Rétention : configurable par l'utilisateur

### Export RGPD
- Export complet des données personnelles (droit d'accès)
- Format JSON structuré
- Inclut : profil, contacts, projets, conversations, préférences
- Exclut : embeddings (non lisibles), données techniques

### Import
- Restauration depuis sauvegarde JSON
- Merge intelligent (pas d'écrasement aveugle)
- Validation des données avant import

## CRM et sync Google Sheets

### Architecture de sync
- **Source de vérité** : Google Sheets (CRM du client)
- **Direction** : Sheets → THÉRÈSE (import)
- **Fréquence** : Manuelle (bouton sync)
- **Colonnes mappées** : Nom, Email, Entreprise, Téléphone, Stage, Score, Tags

### Règles de sync
- Matching par email (clé de déduplication)
- Création si nouveau contact
- Mise à jour si contact existant
- Pas de suppression automatique (sécurité)
- Log de chaque opération de sync

## Conformité RGPD

### Principes appliqués
- **Minimisation** : Ne collecter que les données nécessaires
- **Finalité** : Base légale enregistrée par contact
- **Durée** : Date d'expiration configurable
- **Portabilité** : Export en JSON standard
- **Effacement** : Suppression complète (DB + Qdrant + audit)
- **Transparence** : Journal d'audit (table Activity)

### Base légale par contact
- **Consentement** : L'utilisateur a donné son accord
- **Contrat** : Relation contractuelle existante
- **Intérêt légitime** : Prospection commerciale

### Droit à l'oubli
1. Suppression du contact en base SQLite
2. Suppression des embeddings Qdrant associés
3. Suppression des activités liées
4. Log de la suppression dans le journal d'audit
5. Pas de suppression des conversations (anonymisées)

## Anti-patterns données à éviter
- Jamais de données personnelles dans les logs
- Jamais de sauvegarde non chiffrée des clés API
- Jamais de sync automatique sans consentement
- Jamais de suppression sans cascade (orphelins)
- Jamais de requête sans pagination (risque mémoire)
- Jamais de modification directe de la DB (toujours via Alembic)
- Pas de rm sur les fichiers de données - utiliser mv vers ~/.Trash/
- Pas de tirets longs dans les données textuelles
