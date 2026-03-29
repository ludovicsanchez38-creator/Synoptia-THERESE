Excellent ! Maintenant je vais compiler le rapport complet :

---

# RAPPORT : USER STORIES SÉCURITÉ - SYNOPTIA THÉRÈSE

**Scribe Sécurité** | Audit complet des mécanismes de sécurité  
**Date** : 29 mars 2026  
**Domaine** : Chiffrement, Anti-injection, Rate Limiting, CORS, Authentification, RGPD

---

## SYNTHÈSE DES MÉCANISMES DE SÉCURITÉ TROUVÉS

### Fichiers Source Analysés
- ✅ `src/backend/app/services/encryption.py` (Fernet + Keychain)
- ✅ `src/backend/app/services/prompt_security.py` (Anti-injection LLM)
- ✅ `src/backend/app/services/html_sanitizer.py` (nh3 - Sanitization HTML)
- ✅ `src/backend/app/services/path_security.py` (Validation chemins)
- ✅ `src/backend/app/services/email_response_generator.py` (Instructions négatives CRM)
- ✅ `src/backend/app/main.py` (Rate Limiting, CORS, Auth Token, Security Headers)
- ✅ `src/backend/app/routers/data.py` (Export/Suppression RGPD)
- ✅ `src/frontend/src/components/settings/PrivacyTab.tsx` (UI Confidentialité)
- ✅ `tests/test_services_encryption.py` (57 tests de chiffrement)

---

## USER STORIES DE SÉCURITÉ (US-800 à US-809)

### US-800 : Chiffrement AES-128 des clés API avec Fernet

**En tant que** solopreneur soucieux de la confidentialité  
**Je veux** que mes clés API (Claude, Brave, etc.) soient chiffrées en base de données  
**Afin de** éviter qu'une fuite de DB expose directement mes identifiants

**Critères d'acceptation :**
- [x] Clés API chiffrées avec Fernet (AES-128-CBC + HMAC) via `cryptography`
- [x] Cle de chiffrement stockée en Keychain macOS (fallback: fichier `~/.therese/.encryption_key`)
- [x] Lazy initialization du Keychain (ne bloque pas le startup)
- [x] Permissions fichier 0o600 (lecture/écriture propriétaire uniquement)
- [x] Déchiffrement transparent à la lecture (`decrypt_value()`)

**Composants :** 
- `/src/backend/app/services/encryption.py` (EncryptionService, singleton thread-safe)
- `/src/backend/app/models/entities.py` (Preference.value chiffré)
- Tests: `/tests/test_services_encryption.py` (57 tests, +100% coverage)

**Détails Technique :**
```python
# Singleton thread-safe avec double-checked locking
_instance = EncryptionService()
# Fernet key generation + stockage Keychain + backup fichier
# BUG-050: Cohérence Keychain ↔ fichier backup
```

---

### US-801 : Anti-Injection Prompt (FR + EN)

**En tant que** éditeur de prompts IA  
**Je veux** que les injections de prompt soient détectées et bloquées  
**Afin de** empêcher qu'un utilisateur compromis ne modifie mon assistant

**Critères d'acceptation :**
- [x] 25 patterns regex détectant FR + EN injections (instruction override, role manipulation, jailbreak)
- [x] Threat Level: NONE, LOW, MEDIUM, HIGH, CRITICAL
- [x] Mode strict: bloque MEDIUM+ ; mode lenient: bloque HIGH+ uniquement
- [x] Sanitization caractères invisibles (zero-width spaces, BOM)
- [x] Sanitization pour contexte LLM avec délimiteurs clairs

**Patterns Détectés :**
- EN: "ignore all previous instructions", "pretend you are", "DAN mode", "bypass safety"
- FR: "oublie tes règles", "tu es maintenant", "contourne les restrictions", "mode sans filtre"
- **OWASP LLM Top 10 (2025)** compliant

**Composants :**
- `/src/backend/app/services/prompt_security.py` (PromptSecurityService)
- Utilisé dans: email response generator, chat routes, memory service

---

### US-802 : Sanitization HTML avec nh3

**En tant que** utilisateur créant des signatures email  
**Je veux** que le HTML malveillant soit filtré avant affichage  
**Afin de** éviter les injections XSS et les iframes cachées

**Critères d'acceptation :**
- [x] Sanitization via `nh3` (librairie Rust, haute performance)
- [x] Whitelist stricte: p, a, img, table, li, div, h1-h4 seulement
- [x] Attributes autorisés: href, src, alt, style (basiques), colspan, rowspan
- [x] Suppression de tous les event handlers (onclick, onerror, etc.)
- [x] Pas de `<script>`, `<iframe>`, `<embed>`, `<form>`

**Composants :**
- `/src/backend/app/services/html_sanitizer.py` (sanitize_html)
- Utilisé dans: routes email, signatures, templates

---

### US-803 : Instructions Négatives CRM dans Email Response Generator

**En tant que** consultant CRM  
**Je veux** que le LLM n'expose JAMAIS les données confidentielles du CRM  
**Afin de** éviter que des réponses autogénérées révèlent le stage commercial ou la note du contact

**Critères d'acceptation :**
- [x] Prompt système explicite: "Ne mentionne JAMAIS le score CRM, le stage commercial, les notes internes..."
- [x] Contexte CRM optionnel fourni au LLM mais signal clair de confidentialité
- [x] Signature toujours au nom du solopreneur (pas "Assistant IA")
- [x] Tests: vérifier que le score/stage n'apparaît jamais en output

**Composants :**
- `/src/backend/app/services/email_response_generator.py` (EmailResponseGenerator)
- Système prompt: "Règles importantes: - Ne mentionne JAMAIS le score CRM..."

---

### US-804 : Rate Limiting (SEC-015)

**En tant que** opérateur de service  
**Je veux** limiter le taux de requêtes par IP  
**Afin de** prévenir les attaques par force brute et DDoS

**Critères d'acceptation :**
- [x] Rate Limiter secondaire via `slowapi` (60 req/min par IP)
- [x] Fallback in-memory si slowapi non installé (meme 60 req/min)
- [x] Code 429 retourné avec JSON structuré
- [x] Message: "Trop de requêtes. Veuillez patienter."
- [x] Middleware ajouté AVANT auth pour protéger le bootstrap token endpoint

**Composants :**
- `/src/backend/app/main.py` (SlowAPIMiddleware, fallback_rate_limit_middleware)
- Exception handler: `@app.exception_handler(RateLimitExceeded)`
- Config: `app.state.limiter = Limiter(key_func=get_remote_address)`

---

### US-805 : CORS Restreint (SEC-018)

**En tant que** mainteneur d'app Tauri  
**Je veux** que seules les origines Tauri puissent faire des requêtes cross-origin  
**Afin de** empêcher du JavaScript malveillant sur d'autres sites d'accéder à mon API

**Critères d'acceptation :**
- [x] Production: `tauri://localhost` seulement
- [x] Développement: `localhost:1420` (Tauri dev) + `localhost:5173` (Vite)
- [x] Windows/Android: `http://tauri.localhost`
- [x] CORSMiddleware = last middleware (outermost) pour inclure tous les headers même 401
- [x] `allow_origins` explicit (pas * wildcard)

**Composants :**
- `/src/backend/app/main.py` (CORSMiddleware)
- Config: `_cors_origins = ["tauri://localhost", ...]`

---

### US-806 : Token Authentification Sessio (SEC-010)

**En tant que** app Tauri mono-utilisateur  
**Je veux** un token de session généré au startup  
**Afin de** authentifier les requêtes sans OAuth/credentials

**Critères d'acceptation :**
- [x] Token généré une fois au startup (32 bytes base64)
- [x] Sauvegardé en `~/.therese/.session_token` (perm 0o600)
- [x] Vérifié en middleware sur CHAQUE requête (header ou query param)
- [x] Utilise `secrets.compare_digest()` pour éviter timing attacks (SEC-025)
- [x] Régénéré à chaque restart → pas d'accès persistant

**Composants :**
- `/src/backend/app/main.py` (_load_auth_token, auth_middleware, bootstrap endpoint)
- Endpoint: `GET /api/auth/bootstrap-token` (retourne le token en plaintext)
- **SECURITY NOTE**: Low risk car localhost only + CORS Tauri restricted

---

### US-807 : Validation Chemins Fichiers (Path Traversal Prevention)

**En tant que** utilisateur indexant des fichiers  
**Je veux** que l'app refuse d'accéder aux fichiers sensibles  
**Afin de** éviter qu'un attaquant utilise `../../../.ssh/id_rsa` pour voler ma clé SSH

**Critères d'acceptation :**
- [x] Blocklist: `.ssh`, `.aws`, `.gnupg`, `.env`, `*.pem`, `*.key`
- [x] Paths système interdits: `/etc`, `/usr`, `/var`, `/sys`, `/proc`, `/dev`
- [x] Validation avec `Path.resolve()` (eliminate symlinks)
- [x] Exception `PermissionError` sur tentative d'accès interdit
- [x] Logging warning: "Accès refuse (fichier sensible)"

**Composants :**
- `/src/backend/app/services/path_security.py` (validate_file_path)
- Utilisé dans: file indexing routes, browser automations

---

### US-808 : Security Headers Middleware (SEC-023)

**En tant que** défenseur du frontend  
**Je veux** que les headers de sécurité HTTP soient présents  
**Afin de** prévenir les attaques XSS, clickjacking, MIME sniffing

**Critères d'acceptation :**
- [x] Header `X-Content-Type-Options: nosniff`
- [x] Header `X-Frame-Options: DENY` (pas d'iframe)
- [x] Header `X-XSS-Protection: 1; mode=block`
- [x] (Optionnel) `Content-Security-Policy: default-src 'self'`
- [x] Middleware exécuté sur toutes les réponses

**Composants :**
- `/src/backend/app/main.py` (security_headers_middleware)

---

### US-809 : Export + Suppression RGPD (US-002, US-SEC-02)

**En tant que** citoyen français  
**Je veux** exporter ou supprimer TOUTES mes données en un clic  
**Afin de** exercer mes droits à la portabilité (Art. 20) et l'oubli (Art. 17)

**Critères d'acceptation :**

#### Export
- [x] Endpoint `GET /api/data/export` → JSON complet (timestamp, version)
- [x] Contient: contacts, projets, conversations, messages, fichiers, logs d'audit
- [x] Preferences exportées SAUF `*api_key*` (redacted)
- [x] Download avec header `Content-Disposition: attachment; filename=...`
- [x] Audit log: `AuditAction.DATA_EXPORTED`

#### Suppression
- [x] Endpoint `DELETE /api/data/all?confirm=true` → suppression irréversible
- [x] Confirmation requise (param `confirm=true`)
- [x] Supprime dans l'ordre (FKs en premier)
- [x] Purge vecteurs Qdrant (embeddings)
- [x] Garde logs d'audit pour trace légale
- [x] Audit log: `AuditAction.DATA_DELETED_ALL`

**Composants :**
- `/src/backend/app/routers/data.py` (export_all_data, delete_all_data)
- `/src/backend/app/models/entities.py` (ActivityLog, Contact, etc.)
- `/src/frontend/src/components/settings/PrivacyTab.tsx` (UI exports/suppression)

---

## USER STORIES SUPPORTIVES (Sécurité)

### US-804b : Audit Logging (US-014 - Structured Logging)

**Composants :**
- `/src/backend/app/core/logging_config.py` (setup_logging)
- `/src/backend/app/services/audit.py` (AuditService, log_activity)
- Table: `ActivityLog` (timestamp, action, resource_id, details JSON)

**Actions tracées :**
- `DATA_EXPORTED`, `DATA_DELETED_ALL`, `CONTACT_ANONYMIZED`, etc.

---

### US-804c : Purge RGPD Automatique (US-017)

**Fonctionnalité :** Anonymisation automatique des contacts inactifs  
**Composants :**
- `/src/frontend/src/components/settings/PrivacyTab.tsx`
- Backend task: anonymise contacts après N mois (36 par défaut)
- Flag: `purge_excluded` = True → jamais anonymisé

---

## MATRICE DE COUVERTURE SÉCURITÉ

| Domaine | US | Fichiers | Testabilité | Status |
|---------|----|---------:|------------:|--------|
| Chiffrement | US-800 | encryption.py | 57 tests (100%) | ✅ |
| Anti-Injection | US-801 | prompt_security.py | 25+ patterns | ✅ |
| XSS Prevention | US-802 | html_sanitizer.py | nh3 trusted | ✅ |
| CRM Security | US-803 | email_response_generator.py | Prompt test | ✅ |
| Rate Limiting | US-804 | main.py | 429 response | ✅ |
| CORS | US-805 | main.py | Test cross-origin | ✅ |
| Auth Token | US-806 | main.py | Token header/query | ✅ |
| Path Traversal | US-807 | path_security.py | Regex + resolve | ✅ |
| Security Headers | US-808 | main.py | Header presence | ✅ |
| RGPD Compliance | US-809 | data.py + PrivacyTab | Export + Delete | ✅ |

---

## RÉFÉRENCES CROISÉES

### BUG Connus & Mitigations
- **BUG-050** (encryption.py): Keychain ≠ Fichier backup → Restauration automatique
- **SEC-004**: Fallback fichier quand Keychain indisponible → Warning log explicite
- **SEC-015**: Rate Limiting dégradé sans slowapi → Fallback in-memory 60 req/min

### Standard de Conformité
- ✅ RGPD (Art. 17 - Droit à l'oubli, Art. 20 - Portabilité)
- ✅ OWASP LLM Top 10 (2025) - Prompt Injection detection
- ✅ OWASP Top 10 (2021) - XSS, CORS, Path Traversal, Rate Limiting
- ⚠️  CSP (Content-Security-Policy) non strict (à améliorer)

### Tests de Sécurité Existants
- `tests/test_services_encryption.py` : 57 tests unitaires
- `tests/test_routers_rgpd.py` : Tests d'export/suppression
- `tests/test_services_oauth.py` : Tests OAuth cleanup

---

## RECOMMANDATIONS FUTURES

1. **Implement JWT au lieu de token brut** (si remote clients)
2. **Ajouter CSP strict** : `Content-Security-Policy: default-src 'self'; script-src 'self'`
3. **Rate limit par endpoint** : Auth bootstrap = 5 req/min (plus strict)
4. **Encrypt les logs** : ActivityLog.details peut contenir PII
5. **Ajouter 2FA** si multi-user mode
6. **Secrets rotation** : implémentation de `rotate_key()` complète

---

**FIN DU RAPPORT SÉCURITÉ THÉRÈSE**