# Politique de sécurité - THÉRÈSE

## Signaler une vulnérabilité

Si vous découvrez une vulnérabilité de sécurité dans THÉRÈSE, **ne créez pas d'issue publique**. Contactez-nous directement :

- **Email** : ludo@synoptia.fr
- **Objet** : `[SÉCURITÉ] Description courte du problème`

Nous nous engageons à :
- Accuser réception sous **48 heures**
- Fournir une évaluation initiale sous **7 jours**
- Corriger les vulnérabilités critiques sous **14 jours**

## Architecture de sécurité

### Données locales

THÉRÈSE est conçu "local-first". Vos données restent sur votre machine :

- **Base de données** : SQLite dans `~/.therese/therese.db`
- **Embeddings vectoriels** : Qdrant local dans `~/.therese/qdrant/`
- **Fichiers** : stockés dans `~/.therese/`

### Chiffrement des clés API

Les clés API des fournisseurs LLM sont chiffrées avec **Fernet** (AES-128-CBC). La clé de chiffrement est stockée dans le Keychain macOS ou le Windows Credential Manager (via `keyring`), jamais sur le disque.

### Chiffrement de la base au repos (US-014)

La base SQLite (`~/.therese/therese.db`) est chiffrée avec **SQLCipher** (AES-256). La clé est dérivée (HKDF-SHA256) de la clé maîtresse du trousseau : un seul secret à protéger, même cycle de vie que les clés API (Keychain + sauvegarde fichier `~/.therese/.encryption_key`, permissions 600). Une base claire existante est migrée automatiquement au premier démarrage (export chiffré, vérification d'intégrité, remplacement atomique - aucune copie claire conservée).

Conséquences à connaître :
- une copie du fichier `therese.db` (vol, sauvegarde cloud, autre machine) est **illisible sans la clé** ;
- restaurer un backup THÉRÈSE sur une autre machine nécessite de transférer aussi la clé (`~/.therese/.encryption_key`) ;
- perdre la clé maîtresse = perdre les clés API ET la base ;
- échappatoire assumée pour le débogage : `THERESE_DB_PLAINTEXT=1` (base en clair, à tes risques).

### Authentification

- Chaque session génère un token unique (SEC-010)
- Protection contre les timing attacks (`secrets.compare_digest`)
- Rate limiting sur toutes les routes API (SEC-015)

### En-têtes de sécurité

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Permissions-Policy` restrictive
- CSP configuré pour Tauri

### Protections actives

- Validation des entrées sur toutes les routes
- Protection contre l'injection de prompts (SEC-021)
- CORS restreint aux origines Tauri (SEC-018)
- Pas de données utilisateur transmises à des tiers (sauf appels LLM explicites)

## Versions supportées

| Version | Supportée |
|---------|-----------|
| Alpha (v0.x) | Oui (programme alpha en cours) |

## Limitations connues (alpha)

- L'application n'est pas signée (macOS Gatekeeper, Windows SmartScreen)
- Le backend écoute sur `127.0.0.1:8000` (localhost uniquement)
- Les communications avec les API LLM transitent par Internet (HTTPS)
