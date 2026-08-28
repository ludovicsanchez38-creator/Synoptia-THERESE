# Vérification des findings personas — version corrigée après contre-expertise

Deux passes :

1. J'ai vérifié chaque finding persona dans le code.
2. **Soso (Codex) a été lancé pour me réfuter.** Verdict : « Un seul finding
   tient tel quel : V6. Le reste mélange absolus faux, causes ratées et
   gravités gonflées. » Il avait raison sur l'essentiel, et il a trouvé un
   défaut que j'avais complètement manqué.

Cette version intègre ses corrections. Les gravités indiquées ici sont les
gravités **après** contre-expertise, pas celles des personas.

---

## V5 — LE FINDING LE PLUS GRAVE, ET J'AVAIS TOUT FAUX DESSUS

**Ce que j'avais écrit** : le médecin s'est fait dire par l'assistante que « la
base SQLite n'est pas chiffrée au repos », c'est faux, donc c'est une
hallucination du modèle local — `limite_modele_local`, classé « infirmé ».

**Ce qui est vrai** : le modèle n'a rien inventé. **Le prompt système le lui
ordonne.**

`services/llm.py`, bloc `SOVEREIGNTY_BLOCK` :

> « IMPORTANT (honnêteté sécurité) : la base SQLite **n'est PAS chiffrée au
> repos**. Ne prétends JAMAIS qu'elle est « chiffrée », « AES-256 » ou
> équivalent : **ce serait faux**. »

Or la base **est** chiffrée : SQLCipher AES-256, US-014 (`database.py:460-505`).
Vérifié aussi à la main sur la base de campagne : son en-tête n'est pas
`SQLite format 3`.

### Et un test verrouille le mensonge

```python
class TestSovereigntyHonesty:
    """Souveraineté : ne plus prétendre la base chiffrée (NO-GO Syn 0.20.0)."""

    def test_prompt_does_not_claim_encrypted_database(self):
        block = LLMService.SOVEREIGNTY_BLOCK
        assert "base SQLite chiffrée" not in block, "ne plus affirmer que la base est chiffrée (faux)"
        assert "n'est PAS chiffrée au repos" in block
```

En 0.20.0, la base n'était pas chiffrée, et une revue a légitimement exigé
qu'on cesse de le prétendre. Puis US-014 a livré SQLCipher. **Le prompt et son
test ne l'ont jamais su.**

### Les deux tests sont verts en même temps — exécuté

```
[VERT] tests.test_db_encryption.TestRuntime.test_la_db_de_l_app_est_chiffree
[VERT] tests.test_regression.TestSovereigntyHonesty.test_prompt_does_not_claim_encrypted_database
=> tests: 2 | echecs: 0 | erreurs: 0
```

L'un garantit que la base est chiffrée. L'autre garantit que l'assistante dira
qu'elle ne l'est pas. La suite de tests protège une contradiction.

- **Gravité** : majeur, et symboliquement le pire de la campagne
- **Nature** : `defaut_app` (j'avais mis `limite_modele_local` : faux)
- **Correctif** : réécrire `SOVEREIGNTY_BLOCK` (la base EST chiffrée ; rester
  honnête sur ce qui ne l'est pas), et retourner le test pour qu'il exige la
  vérité au lieu de l'ancienne. Nuance à conserver, relevée par Soso : Qdrant
  garde coordonnées et notes **en clair**, et les conversations sont
  sérialisées sans chiffrement applicatif dans `localStorage`
  (`chatStore.ts:426`). Le message honnête n'est donc pas « tout est chiffré ».

---

## V6 — CONFIRMÉ sans réserve (le seul)

« Combien me reste-t-il à encaisser ? » n'a aucun chemin dans le chat.
`search_invoices` (`workspace_tools.py:256`, `:359`) exige une `query`, ne
filtre aucun statut, n'agrège rien.

**Deux corrections de Soso, acceptées** :
- Je disais « le chat n'a que huit outils » : faux. Il ajoute les outils
  mémoire, MCP, web et navigateur (`chat.py:2273`). L'argument tient quand même :
  aucun de ces outils ne lit une situation financière.
- L'`INNER JOIN` n'est pas un aggravant réel : `Invoice.contact_id` est
  obligatoire et la création vérifie le contact.

- **Gravité** : majeur

---

## V1 — REQUALIFIÉ : « nulle part » était faux

L'adresse d'un contact **peut** être saisie : par **import VCF** depuis l'écran
Mémoire (`MemoryPanel.tsx:245` → `memory.py:491`, qui écrit bien `address`).

Le vrai défaut est une **dérive entre couches** sur un même champ :

| Couche | Comportement |
|---|---|
| Base (`entities.py:30`) | `address` existe |
| Schéma (`schemas.py:139`) | l'accepte |
| `POST /memory/contacts` (`memory.py:383`) | **la jette** |
| `PATCH` | fonctionne |
| Import VCF (`memory.py:491`) | fonctionne |
| Outil chat `create_contact` | ne l'expose pas |
| Type TS + formulaire (`ContactModal.tsx:19`) | l'ignorent |

- **Gravité** : majeur globalement, **bloquant sur le parcours « premier devis »**
- **Correction de ma justification juridique** : j'avais cité l'art. 242 nonies A
  du CGI, qui concerne les **factures**. Pour un devis du bâtiment, ce sont le
  nom du client et le **lieu d'exécution** qui sont exigés — et le modèle de
  données ne distingue justement pas ce lieu.

---

## V2 — REQUALIFIÉ en mineur, mais Soso a trouvé le vrai défaut à côté

« DRAFT » sur le PDF décrit exactement un devis encore en brouillon, et passer
le statut à « Envoyé » affiche `SENT`. Les libellés sans accents (*EMETTEUR*,
*Date d' emission*, *Validite*) restent réels : c'est une **localisation
médiocre**, sans perte de données.

- **Gravité** : mineur (j'avais dit bloquant)

**Ce que j'avais manqué, et qui est majeur** : `POST /invoices/{id}/send`
répond **501 en toutes circonstances** (`invoices.py:880-884`) :

> « L'envoi de factures par email n'est pas encore disponible. Télécharge le PDF
> et envoie-le manuellement. »

L'artisan a donc fait son devis… et ne peut pas l'envoyer depuis l'application.
Ni lui ni moi ne l'avions vu ; c'est la contre-expertise qui l'a sorti.

---

## V3 — REQUALIFIÉ : une porte que je croyais fermée est ouverte

Le cloisonnement conversationnel est une **décision explicite de moindre
privilège** (`memory_tools.py:297`), pas un bug — je le disais déjà.

Mais mon « trois portes, deux fermées, une que je n'ai pas » est **faux** :
« Gérer mes contacts » ouvre la vue complète, qui utilise la **recherche
sémantique** et retrouve donc les notes (`ContactsMemoryCard.tsx:283`,
`contactsStore.ts:91`).

Le défaut réel, trouvé par Soso : **le code promet de pouvoir « promouvoir » un
contact vers un périmètre plus large, et ce contrôle n'existe pas.** Aucun champ
`scope` dans `ContactUpdate` (`schemas.py:160`), aucune commande de promotion,
alors que `memory_tools.py:228` l'annonce.

- **Gravité** : majeur (j'avais dit bloquant)

---

## V4 — REQUALIFIÉ : majeur, pas bloquant

`chat.py:1137` reprend bien les 50 premiers caractères du message comme titre.
Mais mon « lisible depuis le couloir » n'est pas démontré par le code : le
tiroir doit être **ouvert**, et l'utilisateur peut renommer ou supprimer la
conversation (`PrototypeConversationDrawer.tsx:240`).

Reste **indéfendable** : la justification « Pas de données personnelles
tierces » pour la conservation illimitée des conversations
(`PrivacyTab.tsx:44`).

- **Gravité** : majeur

---

## V7 — inchangé

« Connecté » désigne le moteur local, pas le réseau. `useOnlineStatus` existe et
n'est branché nulle part (seule occurrence : la réexportation `hooks/index.ts:15`).

- **Gravité** : mineur pris seul

---

## La cause commune, formulée par Soso

> « V1, V3, V5, V6 et O2 viennent du même vice d'architecture : une capacité est
> redéclarée à la main dans les schémas Pydantic, mappings de route, types
> TypeScript, formulaires, outils LLM, prompts, libellés et tests. Ces copies
> divergent. O1 est le même problème appliqué aux chemins : `settings.data_dir`
> existe, mais chaque service peut encore inventer son propre fallback. »

C'est la meilleure description de ce que la campagne a mis au jour. Un champ
`address` déclaré à sept endroits, honoré à trois. Un chiffrement livré dans le
code et jamais propagé au prompt. Une classification d'outils en double dont
une moitié seule est branchée.

---

## V8 — Le score annoncé « de 0 à 100 » monte à 145 (persona 07, F6)

La dirigeante d'organisme de formation lit l'infobulle du pipeline :

> « Score de potentiel commercial **de 0 à 100**, calculé depuis le profil et
> l'activité du contact. »
> — `PipelineView.tsx:274`, et à l'identique dans l'`aria-label` (`:281`)

Le calcul, lui, n'est borné qu'en bas :

```python
return max(0, score)   # scoring.py:88 — « Minimum 0 ». Aucun maximum.
```

**Preuve, relevée dans les journaux de la campagne** (contacts créés par
plusieurs personas) :

```
Contact 504bdd27… score updated: 50 → 145 (initial_creation)
Contact 89dabbd3… score updated: 50 → 130 (initial_creation)
```

Un contact **fraîchement créé**, sans aucune activité, sort déjà à 145 sur une
échelle annoncée à 100. Le libellé est lu par les lecteurs d'écran, donc l'écart
est aussi une information fausse donnée à l'accessibilité.

- **Gravité** : mineur techniquement, **majeur en confiance** — c'est le
  troisième endroit de la campagne où un chiffre affiché contredit ce que
  l'écran annonce (avec le score de confiance à 100 % et le « aucune donnée
  n'est envoyée »).
- **Nature** : `defaut_app`
- **Correctif** : `min(100, max(0, score))`, ou corriger le libellé si l'échelle
  n'est délibérément pas bornée. Une ligne dans les deux cas.

---

## V9 — Le choix de messagerie s'appelle « Gmail », et la cible est sur Outlook (persona 08)

Philippe Marchand, responsable administratif d'une PME de 24 salariés, veut
écrire à un fournisseur « comme dans Outlook ». Son constat : « Il m'a parlé de
Gmail et d'IMAP. **Je n'ai pas Outlook dans les choix.** »

Vérification :

- **L'écran ne nomme que Gmail.** Toutes les mentions visibles de fournisseur
  dans les composants sont « Gmail OAuth », « Gmail API », « Gmail (mot de
  passe d'application) », face à un « SMTP/IMAP classique » générique. Aucun
  libellé « Outlook » ni « Microsoft 365 » à l'écran.
- **Le seul OAuth branché est Google** : `oauth.py:51-52` (`GOOGLE_AUTH_URL`,
  `GOOGLE_TOKEN_URL`). Pas d'équivalent Microsoft.
- Le backend **reconnaît** `outlook.com` et `hotmail.com`, mais seulement comme
  domaines SMTP grand public (`email_setup_assistant.py:54-55`).

Autrement dit : une adresse Outlook personnelle passe par le chemin SMTP
générique, à condition que l'utilisateur sache que c'est là qu'il doit aller.
Un responsable de PME de 57 ans ne le saura pas : il cherche le nom de son
logiciel, et lit « Gmail ».

**À vérifier avant de chiffrer l'ampleur** : l'état réel de l'authentification
basique SMTP/IMAP sur Microsoft 365 en entreprise conditionne la gravité — si
elle n'est plus utilisable, le chemin générique ne rattrape rien pour la cible
professionnelle. Ce point demande une vérification à jour, il n'est pas tranché
ici.

- **Gravité** : majeur (nommage et couverture), potentiellement bloquant pour la
  cible PME selon le point ci-dessus
- **Nature** : `defaut_app`

---

## V10 — ARTEFACT DE HARNAIS : le micro du boulanger (persona 09, F6)

Le boulanger classe en **bloquant** le fait que la dictée exige le cloud :
`GET /api/voice/local/status` → `stt_available: false`, et l'écran
*Confidentialité* affiche « La voix locale n'est pas embarquée dans cette
version de THÉRÈSE. Mets l'application à jour pour en profiter. »

**C'est ma campagne qui l'a induit en erreur, pas le produit.**

Le backend de campagne tourne depuis le venv de développement. Or la voix
locale n'est installée que par un extra optionnel, que **le workflow de release
active** :

```yaml
# .github/workflows/release.yml:98
# --extra voice-local : embarque faster-whisper + Piper dans le sidecar
run: pip install uv && uv sync --dev --extra voice-local
```

### Vérifié sur le binaire réellement livré

`strings` et `find` sur le bundle ne prouvaient rien (PyInstaller compresse
tout : `torch` non plus n'apparaissait pas). J'ai donc lancé
`/Applications/THERESE.app/Contents/MacOS/backend` avec un `THERESE_DATA_DIR`
jetable, et interrogé son API :

```json
{"enabled": false, "stt_available": true, "tts_available": true,
 "whisper_models": {"tiny": …, "base": {"size_mb":145, "label":"Base - recommandé…"}, …}}
```

**La voix locale est bien embarquée dans la 0.53.0.** Le message « pas embarquée
dans cette version » ne s'affiche pas chez un vrai utilisateur.

### Ce qui reste vrai, en beaucoup plus léger

`enabled: false` : la voix locale est **présente mais éteinte par défaut**, et
les modèles se téléchargent au premier usage (145 Mo pour le modèle
recommandé). Le boulanger qui veut dicter sa commande pendant que la cliente est
au téléphone doit donc : ouvrir les Paramètres, activer, attendre un
téléchargement. Ce n'est pas « j'appuie, je parle ».

- **Gravité réelle** : mineur (un défaut de premier usage), pas bloquant
- **À retenir sur la méthode** : un harnais qui n'est pas le paquet livré fait
  produire de faux findings. Pour toute campagne future, soit lancer le binaire
  packagé, soit synchroniser le venv avec `--extra voice-local`.
