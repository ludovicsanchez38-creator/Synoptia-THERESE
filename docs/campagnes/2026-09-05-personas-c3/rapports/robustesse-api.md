# Robustesse et sécurité défensive de l'API - X01

> Persona X01, cycle 3, phase DISCOVER, axe 7 du skill `boucle-amelioration-app`.
> Cible : backend **jetable** de THÉRÈSE **0.66.1** sur `http://127.0.0.1:17393`,
> données de démonstration (Marie Exemple), profil `/tmp/therese-demo-c3`.
> Session du 05/09/2026, 11 h 39 - 11 h 51 UTC.

## Contexte et méthode

**713 requêtes** jouées par un harnais Python (`httpx`) qui, avant chaque envoi,
refuse l'hôte s'il n'est pas exactement `127.0.0.1:17393` et refuse la route si
elle figure dans une liste de blocage. Cette liste couvre les interdictions
explicites de la mission (`POST /api/shutdown`, `DELETE /api/data/all`,
restauration de sauvegarde, `DELETE /api/config/profile`, `POST /api/config/llm`,
clés d'API) **et** leur périmètre implicite : démarrage ou arrêt de processus
(`/api/mcp/servers/*/start|stop|restart`, `/api/mcp/presets/*/install`,
`/api/agents/spawn|dispatch|request`, `/api/browser/*`, `/api/skills/execute/*`,
`/api/tools/install`, `/api/voice/local/setup`, `/api/actions/*/run`), envois
réels (`/api/invoices/*/send`, `POST /api/email/messages`, `/api/email/auth/*`,
`/api/crm/sync*`, `/api/calendar/sync`), génération d'images, sauvegardes, et
`DELETE /api/data/logs` (qui aurait détruit les preuves). La garde a été éprouvée
avant usage : quatre tentatives d'appel interdit et une tentative vers le port
17293 ont toutes été refusées avant émission.

Chaque essai est enregistré avec sa requête exacte, son code HTTP, un extrait de
réponse et le **delta du journal** `/tmp/therese-demo-c3/logs/therese.log`
mesuré entre l'instant qui précède et celui qui suit la requête (769 lignes de
journal capturées et rattachées à leur essai). Le code des routeurs
(`src/backend/app/routers/`) a été lu en dépôt **en lecture seule** pour
comprendre les observations ; aucune écriture dans le dépôt hors ce rapport.

Répartition : angle 1 (entrées hostiles) 172 essais, angle 2 (frontière
d'erreurs) 45, angle 3 (concurrence) 53, angle 4 (session et jeton) 15,
angle 5 (volumes) 385, angle 6 (chemins) 40.

**Bilan brut** : 486 réponses 2xx, 78 × 422, 68 × 404, 32 × 400, 10 × 403,
6 × 401, 6 × 405, 6 × 409, **15 × 500**, 1 × 307, 5 échecs de sérialisation
côté client (valeurs non finies refusées avant émission). Une seule réponse
au-dessus de 2 s.

**Réglage restauré.** Le répertoire de travail valait
`/Users/synoptia/Documents-Atelier-Exemple` avant la campagne ; l'angle 6 l'a
déplacé (jusqu'à la racine du dépôt, cf. X01-13), il a été **remis à sa valeur
d'origine** en fin d'angle et vérifié (`GET /api/config/working-directory` →
`{"path":"/Users/synoptia/Documents-Atelier-Exemple","exists":true}`), avant
toute nouvelle génération de PDF. `git status` du dépôt : propre.

## Constats

Classement appliqué mécaniquement : `bug_candidate` = toute 500, toute fuite
technique dans `detail` (trace, chemin local, message de bibliothèque,
identifiant technique) **à n'importe quel code**, toute incohérence de données
observée. `observation` = surprenant mais non prouvé fautif. `proposal` = piste.
Un message métier français en 4xx passé par `str(e)` est **conforme**, pas un
constat.

### bug_candidate

#### X01-01 - Une facture en franchise de TVA vaut 120 € en base et 100 € sur le PDF envoyé au client

Le plus grave de la campagne : **la donnée enregistrée et le document imprimé se
contredisent de 20 € sur la même facture**.

Requête :

```
POST /api/invoices/
{"contact_id":"84d60db9-ec7e-4351-a013-f2489464c4b8","tva_applicable":false,
 "lines":[{"description":"ROBUSTESSE-franchise","unit_price_ht":100,"tva_rate":20}]}
→ 200, FACT-2026-007
```

Relecture par l'API (ce que voient l'écran, le pipeline et les totaux) :

```
GET /api/invoices/5e710015-0657-4856-be0c-6a9dfaf5bc4d
→ 200  tva_applicable=False  subtotal_ht=100.0  total_tax=20.0  total_ttc=120.0
       ligne : tva_rate=20.0, total_ttc=120.0
```

Le PDF produit pour la même facture (`GET /api/invoices/{id}/pdf` → 200,
`/Users/synoptia/Documents-Atelier-Exemple/factures/FACT-2026-007.pdf`, lu avec
`pdftotext -layout`) :

```
 ROBUSTESSE-franchise      1     100,00 €    0,0%     100,00 €    100,00 €
                                          Total HT        100,00 €
                                          Total TVA         0,00 €
                                          Total TTC       100,00 €
 Mentions légales : TVA non applicable, art. 293 B du CGI.
```

Cause lisible en dépôt : `invoices.py` calcule les totaux par
`_calculate_invoice_totals(db_lines)` (ligne 426) **sans jamais consulter
`invoice.tva_applicable`**, tandis que `services/invoice_pdf.py` l'honore à
trois endroits (lignes 497, 551, 651) et pose la mention 293 B. La route accepte
par ailleurs un `tva_rate` non nul sur une facture déclarée en franchise, sans
le ramener à zéro ni le refuser. Aucune erreur au journal : la contradiction est
silencieuse. Un document légal part chez le client à 100 €, la comptabilité
interne en compte 120.

#### X01-02 - `POST /api/variables` : quatre 500 sur six créations simultanées de même nom

```
6 requêtes simultanées : POST /api/variables {"name":"robustesse_var","value":"v<i>"}
→ codes obtenus : [409, 500, 200, 500, 500, 500]
```

Journal (une ligne par 500) :

```
ERROR main : Unexpected error: (sqlcipher3.dbapi2.IntegrityError)
UNIQUE constraint failed: variables.name
[SQL: INSERT INTO variables (id, name, kind, value, descr...
```

La route vérifie l'existence puis insère, sans transaction verrouillante entre
les deux : le 409 ne couvre que le cas détecté par la lecture, jamais la course
tranchée par la base. Le même défaut a été identifié et corrigé sur les factures
(commentaire **B-160** du 02/09/2026, `invoices.py` lignes 366-399 : « huit
créations simultanées lisaient le même maximum […] six sur huit finissaient en
500 »), et la mesure le confirme : **dix créations de factures simultanées
donnent dix numéros distincts, zéro doublon, zéro 500**. `POST /api/commands/user`
traite correctement la même course (5 × 409, 1 × 201). Les variables sont la
seule des trois à ne pas avoir reçu la leçon.

#### X01-03 - Le PDF d'une facture recopie une exception ReportLab brute, adresses mémoire comprises

Violation directe de la règle 0.48 (`docs/rules/RULES-DESIGN.md` §13 : « seuls
les messages localisés passent - jamais `str(e)` brut »).

```
GET /api/invoices/c003d920-4ebc-48e1-adf3-0d3635b5d37b/pdf   → 500
{"code":"HTTP_ERROR","message":"Erreur lors de la génération du PDF :
Flowable <Table@0x128BC8640 1 rows x 1 cols(tallest row 828)> with cell(0,0) containing
\"<Table@0x128BC88A0 3 rows x 2 cols(tallest row 300)> with cell(0,0) containing
'<Paragraph at 0x129276dd0>Total HT'\"(481.8897637795276 x 828), tallest cell 828.0
points,  too large on page 3 in frame 'normal'(481.228346456693 x 637.1338582677166*)
of template 'Later'"}
```

Le message d'une bibliothèque tierce, trois adresses mémoire et la géométrie de
la page arrivent à l'écran. Site : `invoices.py:832`
(`detail=f"Erreur lors de la génération du PDF : {str(e)}"`). Déclencheur : la
facture porte des montants énormes (X01-15), mais la fuite ne dépend pas de la
cause - toute panne de rendu la produit.

#### X01-04 - L'aperçu d'import CRM tombe en 500 sur un fichier que l'import, lui, digère

```
POST /api/crm/import/contacts/preview   (CSV malformé, 3 lignes, octets nuls)
→ 500  {"code":"unknown_error","message":"Une erreur inattendue s'est produite, réessaie."}
```

Journal :

```
ERROR main : Unexpected error: 1 validation error for CRMImportPreviewSchema
detected_columns.1
  Input should be ...
```

Le **même fichier** posté sur `POST /api/crm/import/contacts` répond 200 avec un
diagnostic ligne à ligne en français (`"Au moins un nom ou une entreprise est
requis"`). L'étape censée protéger l'utilisateur avant l'import est donc la
seule des deux qui casse : celui qui prévisualise pour se rassurer obtient une
panne, celui qui importe directement obtient un rapport propre.

#### X01-05 - L'import vCard renvoie le message anglais brut de la bibliothèque `vobject`

```
POST /api/crm/import/vcf        → 400
POST /api/memory/contacts/import → 400
{"code":"HTTP_ERROR","message":"Fichier VCF invalide :
 At line 3: Failed to parse line: PAS UNE VCARD DU TOUT"}
```

Le préfixe est localisé, la suite est le `str(e)` de la bibliothèque, en anglais,
avec le numéro de ligne interne du parseur. Deux routes concernées. §13 vaut à
tout code HTTP, pas seulement à 500.

#### X01-06 - Un fuseau horaire de 5 000 caractères produit une 500, sur deux routes

```
POST /api/projects/{id}/schedule/calculate  {"timezone":"ROBUSTESSE-ZZZZ…"}  (5011 c.)  → 500
POST /api/calendar/events  {"summary":"…","timezone":"ZZZZ…"}                (5000 c.)  → 500
```

Journal :

```
ERROR main : Unexpected error: [Errno 63] File name too long:
'/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/.venv/lib/python3.13/
site-packages/tzdata/zoneinfo/ROBUSTESSE-ZZZZ…'
```

`services/planning.py:175` n'attrape que `ZoneInfoNotFoundError` ; `ZoneInfo`
transforme la chaîne en **chemin de fichier** et l'`OSError` du système
d'exploitation passe au travers du validateur. Toutes les autres valeurs
absurdes (`Mars/Olympus`, `UTC+99`, espaces) sont correctement refusées en 422 :
c'est la longueur, pas le contenu, qui ouvre la brèche.

#### X01-07 - Un chemin de 5 000 caractères produit une 500, sur deux routes

Même famille, même cause (une `OSError` de syscall qui échappe au garde) :

```
POST /api/config/working-directory  {"path":"AAAA…"}  (5000 c.) → 500
   ERROR main : Unexpected error: [Errno 63] File name too long: 'AAAA…'
POST /api/files/index               {"path":"AAAA…"}  (5000 c.) → 500
   WARNING files : Superviseur d'indexation terminé en échec
   ERROR main : Unexpected error: [Errno 63] File name too long: '/Users/synoptia/…'
```

Toutes les autres entrées hostiles de ces deux routes sont refusées proprement
(`Path does not exist`, `Path is not a directory`, 403 de `path_security`).

#### X01-08 - Le validateur de fuseau laisse passer deux messages CPython bruts, dont un qui renvoie l'entrée en écho

```
POST /api/projects/{id}/schedule/calculate  {"timezone":""}  → 422
  details[0].message = "Value error, ZoneInfo keys must be normalized relative paths, got: "

POST /api/projects/{id}/schedule/calculate  {"timezone":"../../etc/localtime"}  → 422
  details[0].message = "Value error, ZoneInfo keys must refer to subdirectories of TZPATH,
                        got: ../../etc/localtime"
```

Le même validateur produit pourtant, sur les autres branches, un message propre :
`"Fuseau horaire IANA invalide"`. Deux branches sur cinq échappent donc à la
frontière et livrent un message anglais de la bibliothèque standard, un
identifiant technique (`TZPATH`) et, pour la seconde, la chaîne fournie par
l'appelant renvoyée telle quelle.

#### X01-09 - Supprimer un événement inexistant d'un agenda **local** rend 500 au lieu de 404

```
POST   /api/calendar/events {"summary":"ROBUSTESSE-evt-local","calendar_id":"8222efbd-…"} → 200
DELETE /api/calendar/events/a7873aad-…?calendar_id=8222efbd-…                              → 200 (supprimé)
DELETE /api/calendar/events/a7873aad-…?calendar_id=8222efbd-…   (deuxième fois)            → 500
   ERROR main : Unexpected error: Event a7873aad-… not found in calendar 8222efbd-…
DELETE /api/calendar/events/ROBUSTESSE-jamais-existe?calendar_id=8222efbd-…                → 500
   ERROR main : Unexpected error: Event ROBUSTESSE-jamais-existe not found in calendar 8222efbd-…
```

`calendar.py:1529-1532` appelle `provider.delete_event()` sans rattraper le refus
du fournisseur local. Deux clics sur « supprimer », ou un écran resté ouvert sur
un événement déjà effacé ailleurs, suffisent : l'utilisateur voit une panne
générique là où « cet événement n'existe plus » suffirait. La lecture, elle,
répond bien 404 (`GET /api/calendar/events/inexistant`).

#### X01-10 - Sur une base 100 % locale, l'agenda par défaut réclame un compte Google

```
GET    /api/calendar/events                       (sans calendar_id) → 400
DELETE /api/calendar/events/a7873aad-…            (sans calendar_id) → 400
{"code":"HTTP_ERROR","message":"account_id requis pour Google Calendar"}

GET    /api/calendar/events?calendar_id=8222efbd-… → 200 (la liste des événements)
```

Le profil de démonstration ne contient **aucun compte Google** et son calendrier
local porte `primary: true`. Or `calendar_id` vaut `"primary"` par défaut
(`calendar.py:736` et `:1521`) et cet alias est résolu par
`session.get(Calendar, "primary")`, une recherche par clé primaire qui ne peut
jamais le trouver : l'exécution tombe dans la branche Google. Les correctifs
B-236 (lecture) et B-223 (suppression) ont fermé la branche « identifiant
inconnu » en la renvoyant en 404, mais ont explicitement laissé l'alias
`primary` réclamer un compte - c'est justement le cas par défaut. Même famille
que BUG-133 (« chat calendrier sans compte Google = message trompeur ») : le
message désigne un fournisseur hors de cause.

#### X01-11 - Une date d'émission impossible sur une facture donne 500 au lieu de 422

```
POST /api/invoices/  {"contact_id":"84d60db9-…","issue_date":"2026-02-30",
                      "lines":[{"description":"x","unit_price_ht":1}]}     → 500
   ERROR main : Unexpected error: day is out of range for month
```

`invoices.py:355` fait `datetime.fromisoformat(request.issue_date.replace("Z",""))`
sans garde, alors que `issue_date` est déclaré `str` au schéma. Les autres
entités valident cette même famille d'entrée correctement : les contacts
répondent 422 « Une échéance de … », les tâches 400 « Invalid due_date format »,
l'agenda 422 « Format de date ou d'heure invalide », le planning 422 « day value
is outside expected range ». La facturation est la seule à tomber.

#### X01-12 - Un prix unitaire non fini (`Infinity`, `1e400`) traverse la validation et casse la base

```
POST /api/invoices/  corps brut {"contact_id":"…","lines":[{"description":"ROBUSTESSE-Infinity",
                                 "unit_price_ht":Infinity}]}   → 500
POST /api/invoices/  (idem avec 1e400)                          → 500
   ERROR main : Unexpected error: (sqlcipher3.dbapi2.IntegrityError)
   NOT NULL constraint failed: invoices.total_tax
```

`unit_price_ht` porte `minimum: 0.0` : `+inf` satisfait la contrainte, `-inf` et
`NaN` sont refusés en 422. Le calcul des totaux produit ensuite une valeur que
SQLite range en `NULL`, et la contrainte `NOT NULL` tranche. La validation
numérique doit rejeter les valeurs non finies, pas seulement les négatives.

#### X01-13 - Le répertoire de travail accepte `/`, `/etc` et la chaîne vide - qui vaut le répertoire du backend

```
POST /api/config/working-directory {"path":"/etc"} → 200 {"path":"/private/etc","exists":true}
POST /api/config/working-directory {"path":"/"}    → 200 {"path":"/","exists":true}
POST /api/config/working-directory {"path":""}     → 200
     {"path":"/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE","exists":true}
GET  /api/config/working-directory                 → 200 (valeur retenue : la racine du dépôt)
```

`config.py:1227-1233` ne vérifie que l'existence et le caractère « répertoire »,
sans aucun confinement à l'espace de l'utilisateur. Le cas de la chaîne vide est
le plus vicieux : `Path("").resolve()` rend le **répertoire courant du processus**
- ici la racine du code source de l'application. Or ce réglage pilote la sortie
réelle des documents : la génération de PDF y a créé l'arborescence
`<répertoire>/factures/` sans demander confirmation (constaté en début de
campagne : `GET` annonçait `exists:false`, la génération d'un PDF a fait
apparaître `/Users/synoptia/Documents-Atelier-Exemple/factures/`). Un champ vidé
par mégarde dans l'interface enverrait donc les factures du cabinet dans le
dossier d'installation de THÉRÈSE. Valeur d'origine restaurée en fin d'angle.

**Le reste de la défense des chemins tient bien** et mérite d'être dit :
`path_security` refuse en 403 `/etc/passwd`, `/etc/shadow`, `/dev/zero`,
`/dev/null`, `.session_token` (y compris celui du profil réel `~/.therese`),
`.encryption_key` et `therese.db`, **et suit les liens symboliques** (un
`lien-passwd.txt → /etc/passwd` est résolu puis refusé).

#### X01-14 - Un document de l'atelier s'attache à un projet qui n'existe pas

```
POST /api/documents/ {"title":"ROBUSTESSE-p","brief":"b","project_id":"fantome"} → 200
   → document créé avec project_id="fantome"
```

Les deux entités voisines vérifient pourtant la clé sur la même famille
d'entrée : `POST /api/tasks/` rend 404 « Projet non trouvé », `POST
/api/memory/projects` rend 404 « Contact not found ». La note de dette de
l'atelier documentaire évoque des `Document.project_id` **devenus** pendants
après suppression du projet ; ici ils naissent pendants, ce qui est un cran
au-dessus et se referme par une simple vérification à la création.

### observation

#### X01-15 - Montants et taux sans borne haute sur un document comptable

`tva_rate: 10000` accepté (200, FACT-2026-005 : 10 € HT, 1 000 € de TVA,
1 010 € TTC) ; `quantity: 1e150` × `unit_price_ht: 1e150` accepté (200,
FACT-2026-006 : HT ≈ 1e300, TTC ≈ 1,2e300) - et c'est cette facture-là qui fait
ensuite tomber la génération de PDF en 500 (X01-03). Les bornes basses existent
(`minimum: 0` sur le prix et le taux, quantité strictement positive), les hautes
manquent. `validite_jours: -99999` est également accepté sur un devis.

#### X01-16 - Une facture sans aucune ligne consomme un numéro légal

`POST /api/invoices/ {"contact_id":"…","lines":[]}` → 200, **FACT-2026-004**,
totaux à 0, `lines: []`, et le PDF se génère sans broncher. Le garde existe
côté interface (BUG-132 a ajouté la validation « au moins une ligne » dans
`InvoiceForm.tsx`) mais pas côté API : la séquence de numérotation avance sur
un document vide.

#### X01-17 - Cent mille étiquettes sur un contact : 7,9 s d'écriture, seule réponse au-dessus de 2 s

`POST /api/memory/contacts {"first_name":"ROBUSTESSE-tags-100k","tags":["t"]×100000}`
→ 200 en **7 887 ms**. Tous les champs texte sont bornés (`first_name` 200,
`notes` 10 000, refus en 422 à 10 011 caractères), `tags` ne l'est ni en nombre
ni en longueur. SQLite étant mono-écrivain, cette écriture bloque les autres
pendant huit secondes. Les lectures ultérieures restent rapides (13-17 ms), au
prix de 400 Ko supplémentaires dans chaque page de liste.

#### X01-18 - Un contact entièrement `null` est créé et s'affiche « Sans nom »

`POST /api/memory/contacts {"first_name":null,"last_name":null,"email":null,"tags":null}`
→ 200. `GET .../fiche` rend `display_name: "Sans nom"`, l'export vCard rend
`FN:Sans nom` / `N:;;;;`. Le rendu est propre, mais rien n'empêche d'accumuler
des fiches vides indiscernables.

#### X01-19 - La trame d'un document accepte des positions absurdes

Sections créées en 200 avec `order: -999`, `order: 1e308` et `depth: 1000000000`.
`order` est un flottant sans borne : une trame peut contenir une section dont la
position vaut 1e308, ce qui rend tout tri ultérieur arbitraire.

#### X01-20 - Le panneau « Travaux » affiche un libellé de 5 000 caractères

`GET /api/processing-tasks` rend un traitement dont le `label` fait 5 000
caractères (`label = Path(path).name`, hérité du chemin hostile de X01-07). Un
libellé de panneau n'est borné nulle part.

#### X01-21 - « Document vide : rien à exporter » sur un document de soixante sections

`GET /api/documents/{id}/export?format=md` → 400 sur un document dont la trame
compte 60 sections titrées (chacune avec son brief). Le message est vrai au sens
du code (aucune section n'a de `content` rédigé) mais faux au sens de
l'utilisateur, qui vient de construire un plan complet et s'entend dire que son
document est vide. Le plan seul mériterait d'être exportable, ou le message
d'être reformulé.

#### X01-22 - Les chemins résolus renvoyés en clair révèlent le répertoire d'installation

```
POST /api/files/index {"path":"C:\\Windows\\win.ini"} → 404
  "Fichier non trouvé : /Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/C:\\Windows\\win.ini"
POST /api/files/index {"path":"../../../../etc/hosts"} → 404
  "Fichier non trouvé : /Users/etc/hosts"
```

Renvoyer le chemin demandé est légitime pour une application de bureau ; renvoyer
le chemin **résolu** l'est moins : un chemin relatif ou un chemin Windows fait
apparaître le répertoire courant du backend, que l'utilisateur n'a jamais saisi.
Cas particulier de la même racine que X01-13 (le processus travaille dans le
dépôt).

#### X01-23 - Messages de cadriciel en anglais au passage de la frontière

`405` → `"Method Not Allowed"` (`PUT` sur une route POST, `DELETE` sur une
collection, `TRACE`) ; `400` → `"Disallowed CORS origin"` sur un préflight
d'origine étrangère ; `400` → `"Invalid HTTP request received."` sur une méthode
inventée (`BREW`) ; `404` → `"Not Found"` sur `/api/memory/contacts/../../etc/passwd`.
Ces messages viennent de Starlette et d'uvicorn et traversent
`http_exception_handler` (`main.py:620`), qui recopie `str(exc.detail)`. Peu
susceptibles d'atteindre un utilisateur, mais ils échappent au principe de §13.

#### X01-24 - `GET /api/auth/token` sans jeton rend le jeton (assumé et documenté)

`GET /api/auth/token` sans en-tête → 200 `{"token":"…"}`. Avec un
`Origin: http://evil.example` → 403 `ORIGINE_NON_AUTORISEE`, avec la trace au
journal. Le commentaire B-165 (`main.py:700-704`) assume explicitement le
premier cas : « un appel sans Origin (curl, script local) obtient toujours le
jeton : ce processus peut de toute façon lire `~/.therese/.session_token` ».
Consigné pour mémoire, pas comme un défaut.

**Le reste de l'angle 4 est solide** : requête sans jeton, jeton tronqué, jeton
vide, `Authorization: Bearer` à la place de `X-Therese-Token`, jeton en
paramètre d'URL et **jeton d'un autre profil** (celui du backend réel
`~/.therese`) donnent tous 401 avec le même message, sans distinguer les cas.
`OPTIONS` contourne l'authentification par conception (`main.py:750`) mais ne
livre rien : 405 sur une route sans préflight, 400 sur une origine refusée.

#### X01-25 - Contrat et règle métier désaccordés sur le nom d'une variable

Le schéma OpenAPI annonce `maxLength: 64` pour `VariableCreateBody.name`, la
règle appliquée en dit 32 : `"Nom de variable invalide : « ROBUSTESSE-var ».
Attendu : minuscules, chiffres et _ (32 caractères maximum)."` Un client qui
génère son formulaire depuis le contrat proposera 64 caractères et sera refusé à
33. Accessoirement, ce refus part en **422 avec `code: HTTP_ERROR`** là où les
refus de validation portent `code: VALIDATION_ERROR`.

#### X01-26 - Instantané de planning orphelin après suppression du projet

Quatre calculs de planning lancés simultanément à la suppression du projet ont
tous rendu 200, avec le même `snapshot_id`, pour un projet effacé dans la même
fenêtre. Les trois routes de lecture répondent ensuite 404 (« Project not
found », « Projet non trouvé », « Snapshot de planning non trouvé ») : la ligne
subsiste probablement en base mais reste inatteignable par l'API. Non prouvé
fautif, d'où le classement.

**Le reste de l'angle 3 est sain** : dix créations de factures simultanées →
dix numéros distincts sans doublon ni 500 (B-160 tient) ; six commandes
utilisateur de même nom → 1 × 201 et 5 × 409 ; six calculs de planning
identiques → un seul instantané partagé (la déduplication par empreinte tient) ;
huit tâches de même titre → huit tâches distinctes (aucune contrainte
d'unicité, comportement cohérent) ; six lectures concurrentes d'un contact
supprimé au milieu → six 200 puis la suppression en 200, aucune 500, aucune
demi-lecture.

**L'angle 5 ne révèle aucun effondrement** : 300 contacts créés en 33,7 s
(112 ms pièce, aucune création au-dessus de 2 s) ; après quoi la liste de 200
contacts sort en 10 ms / 216 Ko, la page suivante en 7 ms, la recherche en 9 ms,
les statistiques du pipeline en 7 ms, l'accueil en 9 ms, la recherche sémantique
en 65 ms, l'export vCard en 78 ms. Une facture de 200 lignes se crée en 19 ms,
se relit en 7 ms et sort en PDF en 91 ms. Un document de 60 sections se
construit en 0,4 s et se relit en 6 ms. Une seule réponse au-dessus de 2 s sur
713 (X01-17).

### proposal

- **X01-27** - Rejeter les valeurs non finies au niveau du schéma numérique
  partagé (`allow_inf_nan=False` en Pydantic) plutôt qu'au cas par cas : X01-12
  et les montants de X01-15 tombent ensemble.
- **X01-28** - Borner ce qui traverse un appel système avant l'appel : longueur
  maximale sur `timezone` et sur `path`, et rattraper `OSError` là où
  `ZoneInfoNotFoundError` l'est déjà. X01-06 et X01-07 partagent cette racine.
- **X01-29** - Un test de frontière générique : rejouer un jeu d'entrées
  hostiles sur toutes les routes et refuser toute réponse dont le `message`
  contient une adresse mémoire, un chemin absolu, un nom de classe, `Traceback`,
  `constraint failed` ou un mot anglais de bibliothèque. X01-03, X01-05, X01-08
  et X01-23 seraient tombés d'un coup.
- **X01-30** - Faire trancher l'unicité par la base partout où elle est déclarée,
  sur le modèle B-160 (insertion, `IntegrityError` rattrapée, 409) : X01-02
  aujourd'hui, et toute contrainte d'unicité ajoutée demain.
- **X01-31** - Résoudre l'alias `primary` vers le calendrier marqué `primary` du
  fournisseur configuré avant de conclure « Google » (X01-10), et rattraper le
  refus du fournisseur local en 404 (X01-09).
- **X01-32** - Confiner le répertoire de travail (refus de `/`, des répertoires
  système et de la chaîne vide) et le résoudre à partir de `THERESE_DATA_DIR`
  plutôt que du répertoire courant du processus (X01-13, X01-22).

## Angles non couverts, et pourquoi

- **Cycle de dépendances et durées incohérentes du planning** (angle 1, part
  explicite de la mission) : **aucune route d'écriture** n'expose
  `TaskDependency` ni `TaskSchedule` dans les 299 chemins de `openapi.json` -
  seules existent `GET /schedule`, `POST /schedule/calculate` et
  `GET /schedule/snapshots/{id}`. Un cycle ou une durée optimiste supérieure à
  la pessimiste ne sont donc pas fabricables par l'API ; les garde-fous
  existent d'ailleurs en contraintes de table
  (`ck_task_dependency_distinct_tasks`, `ck_task_schedule_duration_*_order`).
  Le projet de démonstration n'ayant par ailleurs **aucune tâche**, les calculs
  joués portent sur un graphe vide : le moteur PERT-CPM lui-même reste non
  éprouvé. À reprendre par un persona ayant le droit d'écrire en base, ou après
  ouverture d'une route de dépendances.
- **Chat, Board, rédaction de section, recherche approfondie** : le service d'IA
  configuré est un Ollama local (`gemma4-tia:latest`) ; ces routes ont été
  écartées pour ne pas consommer plusieurs minutes de génération par essai et
  ne pas fausser les mesures de temps des autres angles. Aucune n'a été
  sollicitée.
- **Connecteurs, agents, navigateur, exécution de skills, installation d'outils,
  voix locale, génération d'images, envois réels, sauvegardes et restauration** :
  écartés par la liste de blocage du harnais - ils lancent un processus,
  appellent l'extérieur ou détruisent des données.
- **`POST /api/mcp/servers`** (création d'une configuration de connecteur) :
  écarté par prudence, faute d'avoir vérifié si la création déclenche un
  démarrage de processus.
- **Rate limiting** : le comportement au-delà du seuil (`RateLimitExceeded`,
  429) n'a pas été provoqué délibérément ; les rafales jouées (10 requêtes
  simultanées maximum) ne l'ont jamais déclenché.
- **`/api/voice/transcribe`** : deux essais joués avec le mauvais nom de champ
  (`file` au lieu d'`audio`), donc arrêtés en 422 avant d'atteindre la logique.
  Le chemin d'erreur du transcripteur reste à éprouver.

## Résidus laissés dans le profil de démonstration

Rien n'a été nettoyé (le préfixe « ROBUSTESSE- » est là pour ça), mais la
persona suivante doit savoir que **les données de démonstration ne sont plus
vierges** :

- **313 contacts** au lieu de 12, dont 300 « ROBUSTESSE-nnn Volume », un
  « ROBUSTESSE-tags-100k » à cent mille étiquettes, un contact entièrement vide
  (« Sans nom ») et une poignée de contacts d'essai. Le pipeline en est
  mécaniquement faussé : `total_contacts: 313`, étape « contact » à 308 avec un
  score moyen de 79,4.
- **17 factures et 1 devis ROBUSTESSE** (FACT-2026-004 à 020, DEV-2026-002), dont
  la facture vide, celle à 1e300, celle à 10 000 % de TVA et celle de 200
  lignes. La séquence de numérotation 2026 a avancé d'autant.
- Une dizaine de **projets**, une dizaine de **tâches**, quelques **documents**
  d'atelier dont un de 60 sections, une **commande utilisateur**
  (`robustesse_course`, `ROBUSTESSE-cmd`), une **variable** (`robustesse_var`),
  des **fichiers indexés** depuis le bac à sable de la persona, des
  **instantanés de planning**.
- Des **PDF de factures** dans `/Users/synoptia/Documents-Atelier-Exemple/factures/`
  (répertoire créé par la génération elle-même, hors du profil jetable).
- Le **répertoire de travail a été restauré** à sa valeur d'origine.

## Table des essais

319 lignes retenues sur 713 : toutes les réponses hors 2xx, plus une ligne par
famille de succès (les 300 créations de volume, les 60 sections et les rafales
de concurrence sont représentées par une ligne chacune).

| Angle | Requête | Attendu | Observé (extrait) | Code | ms |
|---|---|---|---|---|---|
| 0 | `GET /health` | 200 sante | `{"status":"healthy","version":"0.66.1","services":{"database":true,"qdrant":true}}` | 200 | 4 |
| 4 | `GET /api/memory/contacts` | 401 | `{"code":"UNAUTHORIZED","message":"Token de session invalide ou manquant"}` | 401 | 3 |
| 4 | `GET /api/memory/contacts` | 401 | `{"code":"UNAUTHORIZED","message":"Token de session invalide ou manquant"}` | 401 | 1 |
| 4 | `GET /api/memory/contacts` | 401 | `{"code":"UNAUTHORIZED","message":"Token de session invalide ou manquant"}` | 401 | 1 |
| 4 | `GET /api/memory/contacts` | 401 | `{"code":"UNAUTHORIZED","message":"Token de session invalide ou manquant"}` | 401 | 1 |
| 4 | `GET /api/memory/contacts`<br>*jeton du profil ~/.therese (non recopie)* | 401 jeton autre profil | `{"code":"UNAUTHORIZED","message":"Token de session invalide ou manquant"}` | 401 | 1 |
| 4 | `GET /api/memory/contacts` ?`{"token": "<jeton-de-session>` | 401 | `{"code":"UNAUTHORIZED","message":"Token de session invalide ou manquant"}` | 401 | 1 |
| 4 | `GET /api/auth/token` | ? | `{"token":"<jeton-de-session>"}` | 200 | 5 |
| 4 | `GET /api/auth/token` | refus origine | `{"code":"ORIGINE_NON_AUTORISEE","message":"Origine non autorisée pour cette route."}` | 403 | 3 |
| 4 | `OPTIONS /api/memory/contacts` | 204/405 sans fuite | `{"code":"HTTP_ERROR","message":"Method Not Allowed"}` | 405 | 6 |
| 4 | `OPTIONS /api/memory/contacts` | refus CORS | `Disallowed CORS origin` | 400 | 1 |
| 4 | `PUT /api/memory/contacts`<br>corps `{"name": "x"}` | 405 | `{"code":"HTTP_ERROR","message":"Method Not Allowed"}` | 405 | 1 |
| 4 | `PATCH /api/dashboard/today` | 405 | `{"code":"HTTP_ERROR","message":"Method Not Allowed"}` | 405 | 1 |
| 4 | `DELETE /api/memory/contacts` | 405 | `{"code":"HTTP_ERROR","message":"Method Not Allowed"}` | 405 | 1 |
| 4 | `TRACE /api/memory/contacts` | 405 | `{"code":"HTTP_ERROR","message":"Method Not Allowed"}` | 405 | 1 |
| 4 | `BREW /api/memory/contacts` | 405 | `Invalid HTTP request received.` | 400 | 2 |
| 0 | `GET /api/memory/contacts` ?`{"limit": 5}` | inventaire | `[{"id":"84d60db9-ec7e-4351-a013-f2489464c4b8","first_name":"Claire","last_name":"Roux","company":"Cabinet Roux Conseil",` | 200 | 6 |
| 0 | `GET /api/memory/projects` ?`{"limit": 5}` | inventaire | `[{"id":"a83b33c2-fd24-4909-b3c9-d28632683b73","name":"Bilan Petit Paysage","description":"Mission de juin, bilan à faire` | 200 | 7 |
| 1 | `POST /api/memory/contacts`<br>corps `{"first_name": "ROBUSTESSE-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | 422 borne | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"first_name","message":"Str` | 422 | 6 |
| 1 | `POST /api/memory/contacts`<br>corps `{"first_name": "ROBUSTESSE-long-notes", "notes": "ROBUSTESSE-AAAAAAAAAAAAAAAAA` | 422 borne notes | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"notes","message":"String s` | 422 | 2 |
| 1 | `POST /api/memory/contacts`<br>corps `{"first_name": "ROBUSTESSE-💥éèêçñ中文العربية<script>alert(1)</script>", "last_na` | 201 ou refus propre | `{"id":"40972e7e-84b6-4e30-a926-6eeb6d9e1779","first_name":"ROBUSTESSE-💥éèêçñ中文العربية<script>alert(1)</script>","last_na` | 200 | 216 |
| 1 | `POST /api/memory/contacts`<br>corps `{"first_name": null, "last_name": null, "email": null, "tags": null}` | contact vide ? | `{"id":"89a19fb0-fcb7-4e16-96b2-8b22b39ffb20","first_name":null,"last_name":null,"company":null,"email":null,"phone":null` | 200 | 35 |
| 1 | `POST /api/memory/contacts`<br>corps `{"first_name": "ROBUSTESSE-tags-vides", "tags": []}` | 201 | `{"id":"8f58de17-36a9-4279-9187-9d24efeb7357","first_name":"ROBUSTESSE-tags-vides","last_name":null,"company":null,"email` | 200 | 26 |
| 1 | `POST /api/memory/contacts`<br>corps `{"first_name": "ROBUSTESSE-tags-objet", "tags": [{"a": 1}]}` | 422 | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"tags.0","message":"Input s` | 422 | 2 |
| 1 | `POST /api/memory/contacts`<br>corps `{"first_name": "ROBUSTESSE-mail", "email": "pas-un-email"}` | 422 ou 201 | `{"id":"005ff4d9-b723-4a1c-9818-fdb8af4af2e8","first_name":"ROBUSTESSE-mail","last_name":null,"company":null,"email":"pas` | 200 | 24 |
| 1 | `POST /api/memory/contacts`<br>corps `{"first_name": "ROBUSTESSE-stage", "stage": "ROBUSTESSE-inconnu"}` | 422 | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"stage","message":"Input sh` | 422 | 2 |
| 1 | `POST /api/memory/contacts`<br>corps `{"first_name": "ROBUSTESSE-date", "next_follow_up": "2026-02-30"}`<br>*2026-02-30* | 422 date impossible | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"next_follow_up","message":` | 422 | 2 |
| 1 | `POST /api/memory/contacts`<br>corps `{"first_name": "ROBUSTESSE-date", "next_follow_up": "31/09"}`<br>*31/09* | 422 date impossible | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"next_follow_up","message":` | 422 | 2 |
| 1 | `POST /api/memory/contacts`<br>corps `{"first_name": "ROBUSTESSE-date", "next_follow_up": "2026-13-01T00:00:00"}`<br>*2026-13-01T00:00:00* | 422 date impossible | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"next_follow_up","message":` | 422 | 1 |
| 1 | `POST /api/memory/contacts`<br>corps `{"first_name": "ROBUSTESSE-date", "next_follow_up": "0000-00-00"}`<br>*0000-00-00* | 422 date impossible | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"next_follow_up","message":` | 422 | 1 |
| 1 | `POST /api/memory/contacts`<br>corps `{"first_name": "ROBUSTESSE-date", "next_follow_up": "9999-12-31T23:59:59"}`<br>*9999-12-31T23:59:59* | 422 date impossible | `{"id":"551e65cb-ee3e-4b36-b776-0ce572d2292c","first_name":"ROBUSTESSE-date","last_name":null,"company":null,"email":null` | 200 | 25 |
| 1 | `POST /api/memory/contacts`<br>corps `{"first_name": "ROBUSTESSE-inconnu", "score": 999999, "id": "ROBUSTESSE-force"` | ignore ou 422 | `{"id":"80e5ae6d-8579-4870-9071-253bea95bc50","first_name":"ROBUSTESSE-inconnu","last_name":null,"company":null,"email":n` | 200 | 26 |
| 1 | `POST /api/memory/contacts`<br>corps `{"first_name": 12345}` | 422 | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"first_name","message":"Inp` | 422 | 2 |
| 1 | `POST /api/memory/contacts`<br>corps `{"first_name": ["a", "b"]}` | 422 | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"first_name","message":"Inp` | 422 | 2 |
| 1 | `POST /api/memory/contacts`<br>corps `[{"first_name": "x"}]` | 422 corps liste | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"","message":"Input should ` | 422 | 2 |
| 1 | `POST /api/memory/contacts`<br>corps `{"first_name": "ROBUSTESSE-cassure",` | 422/400 | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"36","message":"JSON decode` | 422 | 2 |
| 1 | `POST /api/memory/contacts`<br>corps `pas du tout du json` | 422/400 corps non JSON | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"0","message":"JSON decode ` | 422 | 2 |
| 1 | `POST /api/memory/contacts`<br>corps `first_name=x` | 422/415 mauvais content-type | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"","message":"Input should ` | 422 | 2 |
| 1 | `GET /api/memory/contacts/inexistant`<br>*inexistant* | 404 propre | `{"code":"HTTP_ERROR","message":"Contact not found"}` | 404 | 3 |
| 1 | `GET /api/memory/contacts/00000000-0000-0000-0000-00000000000`<br>*00000000-0000-0000-0000-000000000000* | 404 propre | `{"code":"HTTP_ERROR","message":"Contact not found"}` | 404 | 2 |
| 1 | `GET /api/memory/contacts/-1`<br>*-1* | 404 propre | `{"code":"HTTP_ERROR","message":"Contact not found"}` | 404 | 2 |
| 1 | `GET /api/memory/contacts/0`<br>*0* | 404 propre | `{"code":"HTTP_ERROR","message":"Contact not found"}` | 404 | 2 |
| 1 | `GET /api/memory/contacts/99999999999999999999999999`<br>*99999999999999999999999999* | 404 propre | `{"code":"HTTP_ERROR","message":"Contact not found"}` | 404 | 2 |
| 1 | `GET /api/memory/contacts/../../etc/passwd`<br>*../../etc/passwd* | 404 propre | `{"code":"HTTP_ERROR","message":"Not Found"}` | 404 | 1 |
| 1 | `GET /api/memory/contacts/%2e%2e%2f`<br>*%2e%2e%2f* | 404 propre | `` | 307 | 1 |
| 1 | `GET /api/memory/contacts/a83b33c2-fd24-4909-b3c9-d28632683b7`<br>*id de projet* | 404 | `{"code":"HTTP_ERROR","message":"Contact not found"}` | 404 | 2 |
| 1 | `GET /api/memory/contacts` ?`{"limit": -1}`<br>*{'limit': -1}* | 422 ou borne | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"query.limit","message":"In` | 422 | 1 |
| 1 | `GET /api/memory/contacts` ?`{"limit": 0}`<br>*{'limit': 0}* | 422 ou borne | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"query.limit","message":"In` | 422 | 1 |
| 1 | `GET /api/memory/contacts` ?`{"limit": 1000000000}`<br>*{'limit': 1000000000}* | 422 ou borne | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"query.limit","message":"In` | 422 | 1 |
| 1 | `GET /api/memory/contacts` ?`{"limit": "abc"}`<br>*{'limit': 'abc'}* | 422 ou borne | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"query.limit","message":"In` | 422 | 2 |
| 1 | `GET /api/memory/contacts` ?`{"offset": -5}`<br>*{'offset': -5}* | 422 ou borne | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"query.offset","message":"I` | 422 | 1 |
| 1 | `GET /api/memory/contacts` ?`{"limit": Infinity}`<br>*{'limit': inf}* | 422 ou borne | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"query.limit","message":"In` | 422 | 1 |
| 1 | `POST /api/memory/projects`<br>corps `{"name": "ROBUSTESSE-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | borne ou 200 | `{"id":"fceec575-2d4c-471e-b8ae-eae54459e37d","name":"ROBUSTESSE-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | 200 | 317 |
| 1 | `POST /api/memory/projects`<br>corps `{"name": null}` | 422 | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"name","message":"Input sho` | 422 | 6 |
| 1 | `POST /api/memory/projects`<br>corps `{}` | 422 | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"name","message":"Field req` | 422 | 5 |
| 1 | `POST /api/memory/projects`<br>corps `{"name": "ROBUSTESSE-budget-neg", "budget": -999999}` | budget negatif ? | `{"id":"19eb5b2e-4803-4fb0-afda-260875f840ef","name":"ROBUSTESSE-budget-neg","description":null,"contact_id":null,"scope"` | 200 | 58 |
| 1 | `POST /api/memory/projects`<br>corps `{"name": "ROBUSTESSE-budget-geant", "budget": 1e+308}` | budget geant ? | `{"id":"288a167e-8318-40dd-b58a-b9e43c37e163","name":"ROBUSTESSE-budget-geant","description":null,"contact_id":null,"scop` | 200 | 54 |
| 1 | `POST /api/memory/projects`<br>corps `{"name": "ROBUSTESSE-inf", "budget": Infinity}` | 422 inf | `ValueError: Out of range float values are not JSON compliant: inf` | - | 0 |
| 1 | `POST /api/memory/projects`<br>corps `{"name": "ROBUSTESSE-contact-fantome", "contact_id": "n-existe-pas"}` | 404 contact inconnu ? | `{"code":"HTTP_ERROR","message":"Contact not found"}` | 404 | 8 |
| 1 | `POST /api/memory/projects`<br>corps `{"name": "ROBUSTESSE-status", "status": "ROBUSTESSE-inconnu"}` | 422 status | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"status","message":"Input s` | 422 | 4 |
| 1 | `POST /api/tasks/`<br>corps `{"title": "ROBUSTESSE-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | borne ou 200 | `{"id":"47ac6758-6257-40b0-82f1-ea867c056489","title":"ROBUSTESSE-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | 200 | 8 |
| 1 | `POST /api/tasks/`<br>corps `{"title": ""}` | 422 | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"title","message":"Value er` | 422 | 4 |
| 1 | `POST /api/tasks/`<br>corps `{"title": "ROBUSTESSE-tache-date", "due_date": "2026-02-30"}`<br>*2026-02-30* | 422 date impossible | `{"code":"HTTP_ERROR","message":"Invalid due_date format"}` | 400 | 4 |
| 1 | `POST /api/tasks/`<br>corps `{"title": "ROBUSTESSE-tache-date", "due_date": "31/09"}`<br>*31/09* | 422 date impossible | `{"code":"HTTP_ERROR","message":"Invalid due_date format"}` | 400 | 4 |
| 1 | `POST /api/tasks/`<br>corps `{"title": "ROBUSTESSE-tache-date", "due_date": "demain"}`<br>*demain* | 422 date impossible | `{"code":"HTTP_ERROR","message":"Invalid due_date format"}` | 400 | 4 |
| 1 | `POST /api/tasks/`<br>corps `{"title": "ROBUSTESSE-tache-date", "due_date": "2026-13-45T99:99:99"}`<br>*2026-13-45T99:99:99* | 422 date impossible | `{"code":"HTTP_ERROR","message":"Invalid due_date format"}` | 400 | 3 |
| 1 | `POST /api/tasks/`<br>corps `{"title": "ROBUSTESSE-tache-date", "due_date": "-1"}`<br>*-1* | 422 date impossible | `{"code":"HTTP_ERROR","message":"Invalid due_date format"}` | 400 | 4 |
| 1 | `POST /api/tasks/`<br>corps `{"title": "ROBUSTESSE-tache-date", "due_date": "1e309"}`<br>*1e309* | 422 date impossible | `{"code":"HTTP_ERROR","message":"Invalid due_date format"}` | 400 | 3 |
| 1 | `POST /api/tasks/`<br>corps `{"title": "ROBUSTESSE-projet-fantome", "project_id": "aucun"}` | 404 projet fantome | `{"code":"HTTP_ERROR","message":"Projet non trouvé"}` | 404 | 5 |
| 1 | `GET /api/tasks/inexistant`<br>*inexistant* | 404 | `{"code":"HTTP_ERROR","message":"Task not found"}` | 404 | 5 |
| 1 | `PATCH /api/tasks/inexistant/complete`<br>*inexistant* | 404 | `{"code":"HTTP_ERROR","message":"Task not found"}` | 404 | 4 |
| 1 | `GET /api/tasks/99999999999999999999999999`<br>*99999999999999999999999999* | 404 | `{"code":"HTTP_ERROR","message":"Task not found"}` | 404 | 4 |
| 1 | `PATCH /api/tasks/99999999999999999999999999/complete`<br>*99999999999999999999999999* | 404 | `{"code":"HTTP_ERROR","message":"Task not found"}` | 404 | 5 |
| 1 | `GET /api/tasks/-1`<br>*-1* | 404 | `{"code":"HTTP_ERROR","message":"Task not found"}` | 404 | 4 |
| 1 | `PATCH /api/tasks/-1/complete`<br>*-1* | 404 | `{"code":"HTTP_ERROR","message":"Task not found"}` | 404 | 5 |
| 1 | `POST /api/invoices/`<br>corps `{"contact_id": "84d60db9-ec7e-4351-a013-f2489464c4b8", "lines": []}` | 422 lignes vides | `{"id":"739edd26-5a33-44f7-ad8d-ec7509be20b4","invoice_number":"FACT-2026-004","contact_id":"84d60db9-ec7e-4351-a013-f248` | 200 | 18 |
| 1 | `POST /api/invoices/`<br>corps `{"contact_id": "84d60db9-ec7e-4351-a013-f2489464c4b8", "lines": [{"description` | 422 prix negatif | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"lines.0.unit_price_ht","me` | 422 | 5 |
| 1 | `POST /api/invoices/`<br>corps `{"contact_id": "84d60db9-ec7e-4351-a013-f2489464c4b8", "lines": [{"description` | 422 tva negative | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"lines.0.tva_rate","message` | 422 | 5 |
| 1 | `POST /api/invoices/`<br>corps `{"contact_id": "84d60db9-ec7e-4351-a013-f2489464c4b8", "lines": [{"description` | tva 10000 % ? | `{"id":"e184032f-869d-45b1-9fc3-5bc4e6acd255","invoice_number":"FACT-2026-005","contact_id":"84d60db9-ec7e-4351-a013-f248` | 200 | 17 |
| 1 | `POST /api/invoices/`<br>corps `{"contact_id": "84d60db9-ec7e-4351-a013-f2489464c4b8", "lines": [{"description` | quantite negative ? | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"lines.0.quantity","message` | 422 | 6 |
| 1 | `POST /api/invoices/`<br>corps `{"contact_id": "84d60db9-ec7e-4351-a013-f2489464c4b8", "lines": [{"description` | montant geant ? | `{"id":"c003d920-4ebc-48e1-adf3-0d3635b5d37b","invoice_number":"FACT-2026-006","contact_id":"84d60db9-ec7e-4351-a013-f248` | 200 | 16 |
| 1 | `POST /api/invoices/`<br>corps `{"contact_id": "84d60db9-ec7e-4351-a013-f2489464c4b8", "lines": [{"description` | 422 inf | `ValueError: Out of range float values are not JSON compliant: inf` | - | 0 |
| 1 | `POST /api/invoices/`<br>corps `{"contact_id": "84d60db9-ec7e-4351-a013-f2489464c4b8", "lines": [{"description` | 422 nan | `ValueError: Out of range float values are not JSON compliant: nan` | - | 0 |
| 1 | `POST /api/invoices/`<br>corps `{"contact_id": "fantome", "lines": [{"description": "x", "unit_price_ht": 1}]}` | 404 contact | `{"code":"HTTP_ERROR","message":"Contact not found"}` | 404 | 6 |
| 1 | `POST /api/invoices/`<br>corps `{"contact_id": "84d60db9-ec7e-4351-a013-f2489464c4b8", "currency": "XXX", "lin` | devise hors enum 422 | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"currency","message":"Input` | 422 | 4 |
| 1 | `POST /api/invoices/`<br>corps `{"contact_id": "84d60db9-ec7e-4351-a013-f2489464c4b8", "issue_date": "2026-02-` | date impossible | `{"code":"unknown_error","message":"Une erreur inattendue s'est produite, réessaie.","recoverable":true,"details":{}}` | 500 | 46 |
| 1 | `POST /api/invoices/`<br>corps `{"contact_id": "84d60db9-ec7e-4351-a013-f2489464c4b8", "tva_applicable": false` | franchise TVA | `{"id":"5e710015-0657-4856-be0c-6a9dfaf5bc4d","invoice_number":"FACT-2026-007","contact_id":"84d60db9-ec7e-4351-a013-f248` | 200 | 12 |
| 1 | `POST /api/invoices/`<br>corps `{"contact_id": "84d60db9-ec7e-4351-a013-f2489464c4b8", "lines": [{"description` | montant a virgule | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"lines.0.unit_price_ht","me` | 422 | 4 |
| 1 | `POST /api/invoices/`<br>corps `{"contact_id": "84d60db9-ec7e-4351-a013-f2489464c4b8", "lines": [{"description` | montant texte point | `{"id":"d04cefba-d048-4f25-bf30-b169f2f625a7","invoice_number":"FACT-2026-008","contact_id":"84d60db9-ec7e-4351-a013-f248` | 200 | 9 |
| 1 | `POST /api/invoices/`<br>corps `{"contact_id": "84d60db9-ec7e-4351-a013-f2489464c4b8", "document_type": "devis` | validite negative | `{"id":"21fc2673-174e-4f04-b120-0e4254d611ed","invoice_number":"DEV-2026-002","contact_id":"84d60db9-ec7e-4351-a013-f2489` | 200 | 13 |
| 1 | `GET /api/invoices/inexistant`<br>*inexistant* | 404 | `{"code":"HTTP_ERROR","message":"Invoice not found"}` | 404 | 6 |
| 1 | `GET /api/invoices/inexistant/pdf`<br>*inexistant* | 404 propre | `{"code":"HTTP_ERROR","message":"Invoice not found"}` | 404 | 5 |
| 1 | `GET /api/invoices/-1`<br>*-1* | 404 | `{"code":"HTTP_ERROR","message":"Invoice not found"}` | 404 | 5 |
| 1 | `GET /api/invoices/-1/pdf`<br>*-1* | 404 propre | `{"code":"HTTP_ERROR","message":"Invoice not found"}` | 404 | 5 |
| 1 | `GET /api/invoices/99999999999999999999999999`<br>*99999999999999999999999999* | 404 | `{"code":"HTTP_ERROR","message":"Invoice not found"}` | 404 | 4 |
| 1 | `GET /api/invoices/99999999999999999999999999/pdf`<br>*99999999999999999999999999* | 404 propre | `{"code":"HTTP_ERROR","message":"Invoice not found"}` | 404 | 4 |
| 1 | `POST /api/calc/roi`<br>corps `{"gain": 100, "cost": 0}` | 400 propre | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"investment","message":"Fie` | 422 | 4 |
| 1 | `POST /api/calc/roi`<br>corps `{"gain": 1e+308, "cost": 1e-308}` | ? | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"investment","message":"Fie` | 422 | 3 |
| 1 | `POST /api/calc/npv`<br>corps `{"rate": -1, "cashflows": [1, 2, 3]}` | ? | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"initial_investment","messa` | 422 | 4 |
| 1 | `POST /api/calc/npv`<br>corps `{"rate": -1.0, "cashflows": [], "initial_investment": 0}` | ? | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"cash_flows","message":"Fie` | 422 | 4 |
| 1 | `POST /api/calc/break-even`<br>corps `{"fixed_costs": 100, "price_per_unit": 5, "variable_cost_per_unit": 5}` | ? | `{"code":"HTTP_ERROR","message":"Le prix doit être supérieur au coût variable"}` | 400 | 6 |
| 1 | `POST /api/calc/ice`<br>corps `{"impact": -10, "confidence": Infinity, "ease": 0}` | ? | `ValueError: Out of range float values are not JSON compliant: inf` | - | 0 |
| 1 | `POST /api/calc/rice`<br>corps `{"reach": 1, "impact": 1, "confidence": 1, "effort": 0}` | ? | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"effort","message":"Input s` | 422 | 5 |
| 1 | `POST /api/invoices/`<br>corps `{"contact_id":"84d60db9-ec7e-4351-a013-f2489464c4b8","lines":[{"description":"`<br>*Infinity* | 422 non-fini | `{"code":"unknown_error","message":"Une erreur inattendue s'est produite, réessaie.","recoverable":true,"details":{}}` | 500 | 49 |
| 1 | `POST /api/invoices/`<br>corps `{"contact_id":"84d60db9-ec7e-4351-a013-f2489464c4b8","lines":[{"description":"`<br>*-Infinity* | 422 non-fini | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"lines.0.unit_price_ht","me` | 422 | 5 |
| 1 | `POST /api/invoices/`<br>corps `{"contact_id":"84d60db9-ec7e-4351-a013-f2489464c4b8","lines":[{"description":"`<br>*NaN* | 422 non-fini | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"lines.0.unit_price_ht","me` | 422 | 5 |
| 1 | `POST /api/invoices/`<br>corps `{"contact_id":"84d60db9-ec7e-4351-a013-f2489464c4b8","lines":[{"description":"`<br>*1e400* | 422 non-fini | `{"code":"unknown_error","message":"Une erreur inattendue s'est produite, réessaie.","recoverable":true,"details":{}}` | 500 | 35 |
| 1 | `POST /api/invoices/`<br>corps `{"contact_id":"84d60db9-ec7e-4351-a013-f2489464c4b8","lines":[{"description":"`<br>*1e-400* | 422 non-fini | `{"id":"6b18c82e-397a-46cb-87b4-03de06cdf1d6","invoice_number":"FACT-2026-009","contact_id":"84d60db9-ec7e-4351-a013-f248` | 200 | 13 |
| 1 | `GET /api/invoices/739edd26-5a33-44f7-ad8d-ec7509be20b4/pdf`<br>*lignes vides* | 200 ou erreur sans fuite | `{"pdf_path":"/Users/synoptia/Documents-Atelier-Exemple/factures/FACT-2026-004.pdf","invoice_number":"FACT-2026-004"}` | 200 | 24 |
| 1 | `GET /api/invoices/c003d920-4ebc-48e1-adf3-0d3635b5d37b/pdf`<br>*1e300* | 200 ou erreur sans fuite | `{"code":"HTTP_ERROR","message":"Erreur lors de la génération du PDF : Flowable <Table@0x128BC88A0 1 rows x 1 cols(talles` | 500 | 19 |
| 1 | `GET /api/invoices/e184032f-869d-45b1-9fc3-5bc4e6acd255/pdf`<br>*tva 10000* | 200 ou erreur sans fuite | `{"pdf_path":"/Users/synoptia/Documents-Atelier-Exemple/factures/FACT-2026-005.pdf","invoice_number":"FACT-2026-005"}` | 200 | 10 |
| 1 | `GET /api/invoices/billing/profile-status` | 200 | `{"is_complete":true,"missing":[]}` | 200 | 2 |
| 1 | `GET /api/memory/projects/a83b33c2-fd24-4909-b3c9-d28632683b7` | 200 | `{"id":"a83b33c2-fd24-4909-b3c9-d28632683b73","name":"Bilan Petit Paysage","description":"Mission de juin, bilan à faire ` | 200 | 6 |
| 1 | `POST /api/projects/a83b33c2-fd24-4909-b3c9-d28632683b73/sched`<br>corps `{"timezone": "Europe/Paris"}`<br>*'Europe/Paris'* | 400/422 fuseau invalide | `{"snapshot_id":"719b48ae-ecba-4065-8cb6-8088180fe27d","project_id":"a83b33c2-fd24-4909-b3c9-d28632683b73","engine_versio` | 200 | 11 |
| 1 | `POST /api/projects/a83b33c2-fd24-4909-b3c9-d28632683b73/sched`<br>corps `{"timezone": "Mars/Olympus"}`<br>*'Mars/Olympus'* | 400/422 fuseau invalide | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"","message":"Value error, ` | 422 | 3 |
| 1 | `POST /api/projects/a83b33c2-fd24-4909-b3c9-d28632683b73/sched`<br>corps `{"timezone": ""}`<br>*''* | 400/422 fuseau invalide | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"","message":"Value error, ` | 422 | 2 |
| 1 | `POST /api/projects/a83b33c2-fd24-4909-b3c9-d28632683b73/sched`<br>corps `{"timezone": "   "}`<br>*'   '* | 400/422 fuseau invalide | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"","message":"Value error, ` | 422 | 2 |
| 1 | `POST /api/projects/a83b33c2-fd24-4909-b3c9-d28632683b73/sched`<br>corps `{"timezone": "UTC+99"}`<br>*'UTC+99'* | 400/422 fuseau invalide | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"","message":"Value error, ` | 422 | 2 |
| 1 | `POST /api/projects/a83b33c2-fd24-4909-b3c9-d28632683b73/sched`<br>corps `{"timezone": "../../etc/localtime"}`<br>*'../../etc/localtime'* | 400/422 fuseau invalide | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"","message":"Value error, ` | 422 | 2 |
| 1 | `POST /api/projects/a83b33c2-fd24-4909-b3c9-d28632683b73/sched`<br>corps `{"timezone": "Europe/Paris "}`<br>*'Europe/Paris '* | 400/422 fuseau invalide | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"","message":"Value error, ` | 422 | 3 |
| 1 | `POST /api/projects/a83b33c2-fd24-4909-b3c9-d28632683b73/sched`<br>corps `{"timezone": "ROBUSTESSE-ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ`<br>*'ROBUSTESSE-ZZZZZZZZZZZZZZZZZZZZZZZZZZZZ* | 400/422 fuseau invalide | `{"code":"unknown_error","message":"Une erreur inattendue s'est produite, réessaie.","recoverable":true,"details":{}}` | 500 | 37 |
| 1 | `POST /api/projects/a83b33c2-fd24-4909-b3c9-d28632683b73/sched`<br>corps `{"starts_at": "2026-02-30T00:00:00Z"}`<br>*2026-02-30T00:00:00Z* | 422 date | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"starts_at","message":"Inpu` | 422 | 3 |
| 1 | `POST /api/projects/a83b33c2-fd24-4909-b3c9-d28632683b73/sched`<br>corps `{"starts_at": "pas-une-date"}`<br>*pas-une-date* | 422 date | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"starts_at","message":"Inpu` | 422 | 2 |
| 1 | `POST /api/projects/a83b33c2-fd24-4909-b3c9-d28632683b73/sched`<br>corps `{"starts_at": "9999-12-31T23:59:59+00:00"}`<br>*9999-12-31T23:59:59+00:00* | 422 date | `{"snapshot_id":"f59386ef-bc3b-48e1-836c-f4916b55d790","project_id":"a83b33c2-fd24-4909-b3c9-d28632683b73","engine_versio` | 200 | 5 |
| 1 | `POST /api/projects/a83b33c2-fd24-4909-b3c9-d28632683b73/sched`<br>corps `{"starts_at": "0001-01-01T00:00:00Z"}`<br>*0001-01-01T00:00:00Z* | 422 date | `{"snapshot_id":"223fddd7-11a5-4b1a-98ed-a35abd125df9","project_id":"a83b33c2-fd24-4909-b3c9-d28632683b73","engine_versio` | 200 | 5 |
| 1 | `POST /api/projects/inexistant/schedule/calculate` | 404 | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"","message":"Field require` | 422 | 4 |
| 1 | `GET /api/projects/inexistant/schedule` | 404 | `{"code":"HTTP_ERROR","message":"Projet non trouvé"}` | 404 | 2 |
| 1 | `GET /api/projects/a83b33c2-fd24-4909-b3c9-d28632683b73/sched` | 404 | `{"code":"HTTP_ERROR","message":"Snapshot de planning non trouvé"}` | 404 | 3 |
| 1 | `GET /api/tasks/` ?`{"project_id": "a83b33c2-fd24-4909-b3c9-d28632683b73` | inventaire | `[]` | 200 | 5 |
| 1 | `GET /api/calendar/calendars` | 200 | `[{"id":"8222efbd-6234-4b91-8e8b-442294712278","account_id":null,"summary":"Mon calendrier","description":"Calendrier loc` | 200 | 4 |
| 1 | `POST /api/calendar/events`<br>corps `{"summary": "ROBUSTESSE-fin-avant-debut", "start_datetime": "2026-09-10T15:00:`<br>*fin avant debut* | 400 fin<debut | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"","message":"Value error, ` | 422 | 5 |
| 1 | `POST /api/calendar/events`<br>corps `{"summary": "ROBUSTESSE-date-impossible", "start_datetime": "2026-02-30T10:00:`<br>*2026-02-30* | 422 | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"","message":"Value error, ` | 422 | 4 |
| 1 | `POST /api/calendar/events`<br>corps `{"summary": "ROBUSTESSE-jour-31-09", "start_date": "31/09", "end_date": "31/09`<br>*31/09* | 422 | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"","message":"Value error, ` | 422 | 3 |
| 1 | `POST /api/calendar/events`<br>corps `{"summary": "ROBUSTESSE-tz", "start_datetime": "2026-09-10T09:00:00", "end_dat`<br>*fuseau inconnu* | 400/422 | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"","message":"Value error, ` | 422 | 4 |
| 1 | `POST /api/calendar/events`<br>corps `{"summary": "ROBUSTESSE-tz-long", "start_datetime": "2026-09-10T09:00:00", "en`<br>*fuseau 5000c* | 400/422 | `{"code":"unknown_error","message":"Une erreur inattendue s'est produite, réessaie.","recoverable":true,"details":{}}` | 500 | 37 |
| 1 | `POST /api/calendar/events`<br>corps `{"summary": "ROBUSTESSE-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA`<br>*titre 10011c* | borne ou 200 | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"","message":"Value error, ` | 422 | 5 |
| 1 | `POST /api/calendar/events`<br>corps `{"summary": "ROBUSTESSE-sans-dates"}`<br>*aucune date* | ? | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"","message":"Value error, ` | 422 | 2 |
| 1 | `POST /api/calendar/events`<br>corps `{"summary": "ROBUSTESSE-attendees", "attendees": ["pas-un-email", "", "xxxxxxx`<br>*invites absurdes* | ? | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"","message":"Value error, ` | 422 | 3 |
| 1 | `POST /api/calendar/events`<br>corps `{"summary": "ROBUSTESSE-recur", "recurrence": ["PAS-UNE-RRULE"], "start_dateti`<br>*rrule invalide* | ? | `{"code":"HTTP_ERROR","message":"account_id requis pour Google Calendar"}` | 400 | 3 |
| 1 | `POST /api/calendar/events`<br>corps `{"summary": "ROBUSTESSE-cal-inconnu", "calendar_id": "n-existe-pas", "start_da`<br>*agenda inconnu* | 404 | `{"code":"HTTP_ERROR","message":"Calendrier introuvable : n-existe-pas"}` | 404 | 3 |
| 1 | `GET /api/calendar/events/inexistant`<br>*inexistant* | 404 | `{"code":"HTTP_ERROR","message":"Event not found"}` | 404 | 5 |
| 1 | `DELETE /api/calendar/events/inexistant`<br>*inexistant* | 404 | `{"code":"HTTP_ERROR","message":"account_id requis pour Google Calendar"}` | 400 | 9 |
| 1 | `GET /api/calendar/events/-1`<br>*-1* | 404 | `{"code":"HTTP_ERROR","message":"Event not found"}` | 404 | 4 |
| 1 | `DELETE /api/calendar/events/-1`<br>*-1* | 404 | `{"code":"HTTP_ERROR","message":"account_id requis pour Google Calendar"}` | 400 | 3 |
| 1 | `GET /api/calendar/events/99999999999999999999999999`<br>*99999999999999999999999999* | 404 | `{"code":"HTTP_ERROR","message":"Event not found"}` | 404 | 4 |
| 1 | `DELETE /api/calendar/events/99999999999999999999999999`<br>*99999999999999999999999999* | 404 | `{"code":"HTTP_ERROR","message":"account_id requis pour Google Calendar"}` | 400 | 2 |
| 1 | `GET /api/calendar/events` ?`{"time_min": "2026-02-30T00:00:00", "time_max": "pas`<br>*bornes absurdes* | ? | `{"code":"HTTP_ERROR","message":"account_id requis pour Google Calendar"}` | 400 | 3 |
| 1 | `GET /api/calendar/export-ics` ?`{"calendar_id": "../../etc/passwd"}`<br>*ics traverse* | ? | `{"code":"HTTP_ERROR","message":"Calendrier non trouvé"}` | 404 | 4 |
| 1 | `POST /api/documents/`<br>corps `{"title": "ROBUSTESSE-doc", "brief": "ROBUSTESSE brief court"}` | 200 | `{"id":"30140e53-3fcb-4d01-80d8-171181a00aec","title":"ROBUSTESSE-doc","brief":"ROBUSTESSE brief court","status":"en_cour` | 200 | 7 |
| 1 | `POST /api/documents/`<br>corps `{"title": "ROBUSTESSE-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | borne ou 200 | `{"id":"b166fd52-4548-42c0-b8a4-8272e9103f6b","title":"ROBUSTESSE-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | 200 | 4 |
| 1 | `POST /api/documents/`<br>corps `{"title": "ROBUSTESSE-sans-brief"}` | 422 | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"brief","message":"Field re` | 422 | 3 |
| 1 | `POST /api/documents/`<br>corps `{"title": "ROBUSTESSE-p", "brief": "b", "project_id": "fantome"}` | 404 projet | `{"id":"d3a5dfbe-2bd1-4b63-871c-69af0cd3f6e9","title":"ROBUSTESSE-p","brief":"b","status":"en_cours","project_id":"fantom` | 200 | 4 |
| 1 | `POST /api/documents/30140e53-3fcb-4d01-80d8-171181a00aec/sect`<br>corps `{"title": "ROBUSTESSE-s1", "order": 1}` | 200 | `{"id":"7e29115f-b3d4-45e8-9e24-ee33513fe110","document_id":"30140e53-3fcb-4d01-80d8-171181a00aec","title":"ROBUSTESSE-s1` | 200 | 7 |
| 1 | `POST /api/documents/30140e53-3fcb-4d01-80d8-171181a00aec/sect`<br>corps `{"title": "ROBUSTESSE-neg", "order": -999}` | ordre negatif ? | `{"id":"134b6b90-97f6-4072-aeb7-60ff3ae04d55","document_id":"30140e53-3fcb-4d01-80d8-171181a00aec","title":"ROBUSTESSE-ne` | 200 | 5 |
| 1 | `POST /api/documents/30140e53-3fcb-4d01-80d8-171181a00aec/sect`<br>corps `{"title": "ROBUSTESSE-geant", "order": 1e+308}` | ordre geant ? | `{"id":"28cf5374-9b27-4fa2-acee-c8d649f995e5","document_id":"30140e53-3fcb-4d01-80d8-171181a00aec","title":"ROBUSTESSE-ge` | 200 | 5 |
| 1 | `POST /api/documents/30140e53-3fcb-4d01-80d8-171181a00aec/sect`<br>corps `{"title": "ROBUSTESSE-prof", "order": 2, "depth": 1000000000}` | profondeur geante ? | `{"id":"fc10073d-9937-4d45-b4d2-d397750ea29b","document_id":"30140e53-3fcb-4d01-80d8-171181a00aec","title":"ROBUSTESSE-pr` | 200 | 5 |
| 1 | `POST /api/documents/30140e53-3fcb-4d01-80d8-171181a00aec/sect`<br>corps `{"sections": [{"id": "fantome", "order": 1, "depth": 0}]}` | 422 ids inconnus | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"items","message":"Field re` | 422 | 3 |
| 1 | `POST /api/documents/30140e53-3fcb-4d01-80d8-171181a00aec/sect`<br>corps `{}` | 422 corps vide | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"items","message":"Field re` | 422 | 2 |
| 1 | `GET /api/documents/30140e53-3fcb-4d01-80d8-171181a00aec/expo` ?`{"format": "ROBUSTESSE-inconnu"}`<br>*format inconnu* | ? | `{"code":"HTTP_ERROR","message":"Format non supporté : robustesse-inconnu. Formats disponibles : md, docx."}` | 400 | 5 |
| 1 | `GET /api/documents/30140e53-3fcb-4d01-80d8-171181a00aec/expo` ?`{"format": "md"}` | ? | `{"code":"HTTP_ERROR","message":"Document vide : rien à exporter."}` | 400 | 3 |
| 1 | `GET /api/documents/inexistant` | 404 | `{"code":"HTTP_ERROR","message":"Document introuvable"}` | 404 | 4 |
| 1 | `PATCH /api/documents/sections/inexistant`<br>corps `{"content": "x"}` | 404 | `{"code":"HTTP_ERROR","message":"Section introuvable"}` | 404 | 4 |
| 1 | `PATCH /api/documents/pistes/inexistant`<br>corps `{"status": "done"}` | 404 | `{"code":"HTTP_ERROR","message":"Piste introuvable"}` | 404 | 5 |
| 1 | `POST /api/variables`<br>corps `{"name": "ROBUSTESSE-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | 422 borne 64 | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"name","message":"String sh` | 422 | 3 |
| 1 | `POST /api/variables`<br>corps `{"name": "ROBUSTESSE-var", "kind": "texte-inconnu", "value": "x"}` | ? | `{"code":"HTTP_ERROR","message":"Nom de variable invalide : « ROBUSTESSE-var ». Attendu : minuscules, chiffres et _ (32 c` | 422 | 3 |
| 1 | `POST /api/variables`<br>corps `{"name": "ROBUSTESSE-liste", "kind": "liste", "value": ["a", "a", "a", "a", "a` | liste geante ? | `{"code":"HTTP_ERROR","message":"Nom de variable invalide : « ROBUSTESSE-liste ». Attendu : minuscules, chiffres et _ (32` | 422 | 2 |
| 1 | `POST /api/variables`<br>corps `{"name": "{ROBUSTESSE}", "value": "x"}` | nom avec accolades ? | `{"code":"HTTP_ERROR","message":"Nom de variable invalide : « {ROBUSTESSE} ». Attendu : minuscules, chiffres et _ (32 car` | 422 | 2 |
| 1 | `POST /api/variables`<br>corps `{"name": "../ROBUSTESSE", "value": "x"}` | nom avec / | `{"code":"HTTP_ERROR","message":"Nom de variable invalide : « ../ROBUSTESSE ». Attendu : minuscules, chiffres et _ (32 ca` | 422 | 3 |
| 1 | `POST /api/variables/preview`<br>corps `{"text": "{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a` | boucle ? | `{"resolved":"{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a}{a` | 200 | 5 |
| 1 | `POST /api/variables/preview`<br>corps `{}` | 422 sans texte | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"text","message":"Field req` | 422 | 3 |
| 1 | `DELETE /api/variables/inexistante` | 404 | `{"code":"HTTP_ERROR","message":"Variable « inexistante » introuvable."}` | 404 | 3 |
| 1 | `POST /api/commands/user`<br>corps `{"name": "ROBUSTESSE-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | 422 borne 50 | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"name","message":"String sh` | 422 | 3 |
| 1 | `POST /api/commands/user`<br>corps `{"name": "ROBUSTESSE-cmd", "content": "ROBUSTESSE-AAAAAAAAAAAAAAAAAAAAAAAAAAAA` | ? | `{"name":"ROBUSTESSE-cmd","description":"","category":"general","icon":"","show_on_home":false,"content":"ROBUSTESSE-AAAA` | 201 | 4 |
| 1 | `POST /api/commands/user`<br>corps `{"name": "ROBUSTESSE-icone", "icon": "💥💥💥💥💥💥💥💥💥💥💥💥💥💥💥💥💥💥💥💥"}` | icone 10c | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"icon","message":"String sh` | 422 | 2 |
| 1 | `POST /api/commands/user`<br>corps `{"name": "ROB /../ USTESSE"}` | nom avec espaces/slash | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"name","message":"Value err` | 422 | 2 |
| 1 | `GET /api/commands/user/inexistante` | 404 | `{"code":"HTTP_ERROR","message":"Commande 'inexistante' introuvable"}` | 404 | 1 |
| 1 | `DELETE /api/commands/user/inexistante` | 404 | `{"code":"HTTP_ERROR","message":"Commande 'inexistante' introuvable"}` | 404 | 2 |
| 1 | `POST /api/calendar/events`<br>corps `{"summary": "ROBUSTESSE-evt-local", "calendar_id": "8222efbd-6234-4b91-8e8b-44` | 200 evenement local | `{"id":"a7873aad-9994-41df-a70e-09ef894ab404","calendar_id":"8222efbd-6234-4b91-8e8b-442294712278","summary":"ROBUSTESSE-` | 200 | 9 |
| 1 | `GET /api/calendar/events` ?`{"calendar_id": "8222efbd-6234-4b91-8e8b-44229471227` | 200 | `[{"id":"63b13195-5045-4d96-9ce1-c4fb2f4e18a0","calendar_id":"8222efbd-6234-4b91-8e8b-442294712278","summary":"Rendez-vou` | 200 | 5 |
| 1 | `GET /api/calendar/events`<br>*aucun calendar_id -> defaut 'primary'* | 200 attendu (agenda local primar | `{"code":"HTTP_ERROR","message":"account_id requis pour Google Calendar"}` | 400 | 3 |
| 1 | `DELETE /api/calendar/events/a7873aad-9994-41df-a70e-09ef894ab40`<br>*aucun calendar_id -> defaut 'primary'* | 204/200 attendu | `{"code":"HTTP_ERROR","message":"account_id requis pour Google Calendar"}` | 400 | 3 |
| 1 | `DELETE /api/calendar/events/a7873aad-9994-41df-a70e-09ef894ab40` ?`{"calendar_id": "8222efbd-6234-4b91-8e8b-44229471227` | 200 | `{"success":true,"message":"Evenement supprime"}` | 200 | 5 |
| 1 | `DELETE /api/calendar/events/a7873aad-9994-41df-a70e-09ef894ab40` ?`{"calendar_id": "8222efbd-6234-4b91-8e8b-44229471227`<br>*suppression repetee* | 404 attendu | `{"code":"unknown_error","message":"Une erreur inattendue s'est produite, réessaie.","recoverable":true,"details":{}}` | 500 | 27 |
| 1 | `DELETE /api/calendar/events/ROBUSTESSE-jamais-existe` ?`{"calendar_id": "8222efbd-6234-4b91-8e8b-44229471227` | 404 attendu | `{"code":"unknown_error","message":"Une erreur inattendue s'est produite, réessaie.","recoverable":true,"details":{}}` | 500 | 26 |
| 6 | `POST /api/config/working-directory`<br>corps `{"path": "/etc"}`<br>*racine systeme* | 400 refus propre | `{"path":"/private/etc","exists":true}` | 200 | 8 |
| 6 | `POST /api/config/working-directory`<br>corps `{"path": "~"}`<br>*tilde non developpe* | 400 refus propre | `{"code":"HTTP_ERROR","message":"Path does not exist"}` | 400 | 3 |
| 6 | `POST /api/config/working-directory`<br>corps `{"path": "~/"}`<br>*tilde slash* | 400 refus propre | `{"code":"HTTP_ERROR","message":"Path does not exist"}` | 400 | 2 |
| 6 | `POST /api/config/working-directory`<br>corps `{"path": "../../../../etc"}`<br>*traversee relative* | 400 refus propre | `{"code":"HTTP_ERROR","message":"Path does not exist"}` | 400 | 3 |
| 6 | `POST /api/config/working-directory`<br>corps `{"path": "C:\\Windows\\System32"}`<br>*chemin Windows* | 400 refus propre | `{"code":"HTTP_ERROR","message":"Path does not exist"}` | 400 | 2 |
| 6 | `POST /api/config/working-directory`<br>corps `{"path": "\\\\serveur\\partage"}`<br>*UNC Windows* | 400 refus propre | `{"code":"HTTP_ERROR","message":"Path does not exist"}` | 400 | 2 |
| 6 | `POST /api/config/working-directory`<br>corps `{"path": ""}`<br>*chaine vide* | 400 refus propre | `{"path":"/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE","exists":true}` | 200 | 4 |
| 6 | `POST /api/config/working-directory`<br>corps `{"path": "/chemin/qui/n/existe/pas"}`<br>*inexistant* | 400 refus propre | `{"code":"HTTP_ERROR","message":"Path does not exist"}` | 400 | 2 |
| 6 | `POST /api/config/working-directory`<br>corps `{"path": "/etc/passwd"}`<br>*fichier et non dossier* | 400 refus propre | `{"code":"HTTP_ERROR","message":"Path is not a directory"}` | 400 | 3 |
| 6 | `POST /api/config/working-directory`<br>corps `{"path": "/private/tmp/claude-501/-Users-synoptia/13b06f85-9058-4142-8646-6213`<br>*lien vers un fichier* | 400 refus propre | `{"code":"HTTP_ERROR","message":"Path is not a directory"}` | 400 | 3 |
| 6 | `POST /api/config/working-directory`<br>corps `{"path": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA`<br>*5000 caracteres* | 400 refus propre | `{"code":"unknown_error","message":"Une erreur inattendue s'est produite, réessaie.","recoverable":true,"details":{}}` | 500 | 31 |
| 6 | `POST /api/config/working-directory`<br>corps `{"path": "/tmp/therese-demo-c3\u0000/etc"}`<br>*octet NUL* | 400 refus propre | `{"code":"HTTP_ERROR","message":"Path does not exist"}` | 400 | 3 |
| 6 | `GET /api/config/working-directory`<br>*controle apres refus* | inchange ? | `{"path":"/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE","exists":true}` | 200 | 3 |
| 6 | `POST /api/files/index`<br>corps `{"path": "/etc/passwd"}`<br>*fichier systeme* | 400/404 refus propre | `{"code":"HTTP_ERROR","message":"Acces interdit : les fichiers systeme ne sont pas accessibles"}` | 403 | 12 |
| 6 | `POST /api/files/index`<br>corps `{"path": "/etc/shadow"}`<br>*fichier protege* | 400/404 refus propre | `{"code":"HTTP_ERROR","message":"Acces interdit : les fichiers systeme ne sont pas accessibles"}` | 403 | 8 |
| 6 | `POST /api/files/index`<br>corps `{"path": "~/.therese/.session_token"}`<br>*tilde + jeton du profil reel* | 400/404 refus propre | `{"code":"HTTP_ERROR","message":"Acces interdit : ce type de fichier est protege"}` | 403 | 8 |
| 6 | `POST /api/files/index`<br>corps `{"path": "/tmp/therese-demo-c3/.session_token"}`<br>*jeton de session en clair* | 400/404 refus propre | `{"code":"HTTP_ERROR","message":"Acces interdit : ce type de fichier est protege"}` | 403 | 7 |
| 6 | `POST /api/files/index`<br>corps `{"path": "/tmp/therese-demo-c3/.encryption_key"}`<br>*cle de chiffrement* | 400/404 refus propre | `{"code":"HTTP_ERROR","message":"Acces interdit : ce type de fichier est protege"}` | 403 | 7 |
| 6 | `POST /api/files/index`<br>corps `{"path": "/tmp/therese-demo-c3/therese.db"}`<br>*base de donnees entiere* | 400/404 refus propre | `{"code":"HTTP_ERROR","message":"Acces interdit : ce type de fichier est protege"}` | 403 | 8 |
| 6 | `POST /api/files/index`<br>corps `{"path": "../../../../etc/hosts"}`<br>*traversee relative* | 400/404 refus propre | `{"code":"HTTP_ERROR","message":"Fichier non trouvé : /Users/etc/hosts"}` | 404 | 8 |
| 6 | `POST /api/files/index`<br>corps `{"path": "C:\\Windows\\win.ini"}`<br>*chemin Windows* | 400/404 refus propre | `{"code":"HTTP_ERROR","message":"Fichier non trouvé : /Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/C:\\Windows\\` | 404 | 7 |
| 6 | `POST /api/files/index`<br>corps `{"path": ""}`<br>*chemin vide* | 400/404 refus propre | `{"code":"HTTP_ERROR","message":"Type de fichier non autorisé pour l'indexation : ''. Types autorisés : .bash, .c, .cfg, ` | 400 | 7 |
| 6 | `POST /api/files/index`<br>corps `{"path": "/private/tmp/claude-501/-Users-synoptia/13b06f85-9058-4142-8646-6213`<br>*fichier de 0 octet* | 400/404 refus propre | `{"id":"14a5aa70-a97b-4215-a0a0-87bfff04766f","path":"/private/tmp/claude-501/-Users-synoptia/13b06f85-9058-4142-8646-621` | 200 | 15 |
| 6 | `POST /api/files/index`<br>corps `{"path": "/private/tmp/claude-501/-Users-synoptia/13b06f85-9058-4142-8646-6213`<br>*extension trompeuse* | 400/404 refus propre | `{"id":"0acc99e3-31a1-447e-9744-2c5f7452a31b","path":"/private/tmp/claude-501/-Users-synoptia/13b06f85-9058-4142-8646-621` | 200 | 59 |
| 6 | `POST /api/files/index`<br>corps `{"path": "/private/tmp/claude-501/-Users-synoptia/13b06f85-9058-4142-8646-6213`<br>*binaire deguise en .txt* | 400/404 refus propre | `{"id":"6e176b7a-2885-4226-8e23-c792551b16d7","path":"/private/tmp/claude-501/-Users-synoptia/13b06f85-9058-4142-8646-621` | 200 | 80 |
| 6 | `POST /api/files/index`<br>corps `{"path": "/private/tmp/claude-501/-Users-synoptia/13b06f85-9058-4142-8646-6213`<br>*lien symbolique interne* | 400/404 refus propre | `{"id":"319f2cb5-4a9e-4ca8-9ad4-29ee796d2f02","path":"/private/tmp/claude-501/-Users-synoptia/13b06f85-9058-4142-8646-621` | 200 | 58 |
| 6 | `POST /api/files/index`<br>corps `{"path": "/private/tmp/claude-501/-Users-synoptia/13b06f85-9058-4142-8646-6213`<br>*lien vers /etc/passwd* | 400/404 refus propre | `{"code":"HTTP_ERROR","message":"Acces interdit : les fichiers systeme ne sont pas accessibles"}` | 403 | 8 |
| 6 | `POST /api/files/index`<br>corps `{"path": "/private/tmp/claude-501/-Users-synoptia/13b06f85-9058-4142-8646-6213`<br>*lien circulaire* | 400/404 refus propre | `{"code":"HTTP_ERROR","message":"Fichier non trouvé : /private/tmp/claude-501/-Users-synoptia/13b06f85-9058-4142-8646-621` | 404 | 9 |
| 6 | `POST /api/files/index`<br>corps `{"path": "/dev/zero"}`<br>*peripherique infini* | 400/404 refus propre | `{"code":"HTTP_ERROR","message":"Acces interdit : les fichiers systeme ne sont pas accessibles"}` | 403 | 7 |
| 6 | `POST /api/files/index`<br>corps `{"path": "/dev/null"}`<br>*peripherique vide* | 400/404 refus propre | `{"code":"HTTP_ERROR","message":"Acces interdit : les fichiers systeme ne sont pas accessibles"}` | 403 | 48 |
| 6 | `POST /api/files/index`<br>corps `{"path": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA`<br>*chemin de 5000 caracteres* | 400/404 refus propre | `{"code":"unknown_error","message":"Une erreur inattendue s'est produite, réessaie.","recoverable":true,"details":{}}` | 500 | 132 |
| 6 | `GET /api/files/` | 200 | `[{"id":"151e4a86-d8e6-43a8-8d73-63b8280994a1","path":"/private/tmp/claude-501/-Users-synoptia/13b06f85-9058-4142-8646-62` | 200 | 20 |
| 6 | `GET /api/files/inexistant`<br>*inexistant* | 404 | `{"code":"HTTP_ERROR","message":"File not found"}` | 404 | 4 |
| 6 | `GET /api/files/inexistant/content`<br>*inexistant* | 404 | `{"code":"HTTP_ERROR","message":"File not found"}` | 404 | 3 |
| 6 | `GET /api/files/../../etc/passwd`<br>*../../etc/passwd* | 404 | `{"code":"HTTP_ERROR","message":"Not Found"}` | 404 | 2 |
| 6 | `GET /api/files/../../etc/passwd/content`<br>*../../etc/passwd* | 404 | `{"code":"HTTP_ERROR","message":"Not Found"}` | 404 | 4 |
| 6 | `GET /api/files/-1`<br>*-1* | 404 | `{"code":"HTTP_ERROR","message":"File not found"}` | 404 | 3 |
| 6 | `GET /api/files/-1/content`<br>*-1* | 404 | `{"code":"HTTP_ERROR","message":"File not found"}` | 404 | 3 |
| 3 | `POST /api/invoices/`<br>corps `{"contact_id": "84d60db9-ec7e-4351-a013-f2489464c4b8", "lines": [{"description`<br>*rafale facture 8* | numeros tous distincts | `{"id":"cf04b9fe-1046-4d22-904f-ff14ae2d1cde","invoice_number":"FACT-2026-010","contact_id":"84d60db9-ec7e-4351-a013-f248` | 200 | 36 |
| 3 | `POST /api/tasks/`<br>corps `{"title": "ROBUSTESSE-tache-simultanee"}`<br>*rafale tache 2* | 8 taches ou refus explicite | `{"id":"e53772c1-bd81-4db6-ad08-69e20522a95e","title":"ROBUSTESSE-tache-simultanee","description":null,"status":"todo","p` | 200 | 14 |
| 3 | `POST /api/commands/user`<br>corps `{"name": "robustesse_course"}`<br>*rafale commande 5* | 1 creation + 5 conflits | `{"name":"robustesse_course","description":"","category":"general","icon":"","show_on_home":false,"content":"","created_a` | 201 | 10 |
| 3 | `POST /api/commands/user`<br>corps `{"name": "robustesse_course"}`<br>*rafale commande 4* | 1 creation + 5 conflits | `{"code":"HTTP_ERROR","message":"La commande 'robustesse_course' existe deja"}` | 409 | 9 |
| 3 | `POST /api/commands/user`<br>corps `{"name": "robustesse_course"}`<br>*rafale commande 0* | 1 creation + 5 conflits | `{"code":"HTTP_ERROR","message":"La commande 'robustesse_course' existe deja"}` | 409 | 11 |
| 3 | `POST /api/commands/user`<br>corps `{"name": "robustesse_course"}`<br>*rafale commande 2* | 1 creation + 5 conflits | `{"code":"HTTP_ERROR","message":"La commande 'robustesse_course' existe deja"}` | 409 | 12 |
| 3 | `POST /api/commands/user`<br>corps `{"name": "robustesse_course"}`<br>*rafale commande 3* | 1 creation + 5 conflits | `{"code":"HTTP_ERROR","message":"La commande 'robustesse_course' existe deja"}` | 409 | 13 |
| 3 | `POST /api/commands/user`<br>corps `{"name": "robustesse_course"}`<br>*rafale commande 1* | 1 creation + 5 conflits | `{"code":"HTTP_ERROR","message":"La commande 'robustesse_course' existe deja"}` | 409 | 12 |
| 3 | `POST /api/variables`<br>corps `{"name": "robustesse_var", "value": "v5"}`<br>*rafale variable 5* | 1 creation + 5 conflits | `{"code":"unknown_error","message":"Une erreur inattendue s'est produite, réessaie.","recoverable":true,"details":{}}` | 500 | 45 |
| 3 | `POST /api/variables`<br>corps `{"name": "robustesse_var", "value": "v2"}`<br>*rafale variable 2* | 1 creation + 5 conflits | `{"name":"robustesse_var","kind":"text","value":"v2","description":null,"updated_at":"2026-09-05T11:46:47.229307"}` | 200 | 45 |
| 3 | `POST /api/variables`<br>corps `{"name": "robustesse_var", "value": "v3"}`<br>*rafale variable 3* | 1 creation + 5 conflits | `{"code":"unknown_error","message":"Une erreur inattendue s'est produite, réessaie.","recoverable":true,"details":{}}` | 500 | 67 |
| 3 | `POST /api/variables`<br>corps `{"name": "robustesse_var", "value": "v1"}`<br>*rafale variable 1* | 1 creation + 5 conflits | `{"code":"unknown_error","message":"Une erreur inattendue s'est produite, réessaie.","recoverable":true,"details":{}}` | 500 | 90 |
| 3 | `POST /api/variables`<br>corps `{"name": "robustesse_var", "value": "v4"}`<br>*rafale variable 4* | 1 creation + 5 conflits | `{"code":"unknown_error","message":"Une erreur inattendue s'est produite, réessaie.","recoverable":true,"details":{}}` | 500 | 110 |
| 3 | `POST /api/variables`<br>corps `{"name": "robustesse_var", "value": "v0"}`<br>*rafale variable 0* | 1 creation + 5 conflits | `{"code":"HTTP_ERROR","message":"La variable « robustesse_var » existe déjà. Utilise « remplacer » pour changer sa valeur` | 409 | 112 |
| 3 | `POST /api/projects/a83b33c2-fd24-4909-b3c9-d28632683b73/sched`<br>corps `{"timezone": "Europe/Paris"}`<br>*rafale planning 4* | 6 x 200, un seul instantane par  | `{"snapshot_id":"719b48ae-ecba-4065-8cb6-8088180fe27d","project_id":"a83b33c2-fd24-4909-b3c9-d28632683b73","engine_versio` | 200 | 12 |
| 3 | `POST /api/memory/contacts`<br>corps `{"first_name": "ROBUSTESSE-cible-course", "notes": "xxxxxxxxxxxxxxxxxxxxxxxxxx` | cible | `{"id":"5adb3eee-b0ab-4953-bd65-24a2cd19d856","first_name":"ROBUSTESSE-cible-course","last_name":null,"company":null,"ema` | 200 | 44 |
| 3 | `GET /api/memory/contacts/5adb3eee-b0ab-4953-bd65-24a2cd19d85`<br>*lecture concurrente* | 200 ou 404, jamais 500 | `{"id":"5adb3eee-b0ab-4953-bd65-24a2cd19d856","first_name":"ROBUSTESSE-cible-course","last_name":null,"company":null,"ema` | 200 | 12 |
| 3 | `DELETE /api/memory/contacts/5adb3eee-b0ab-4953-bd65-24a2cd19d85`<br>*suppression concurrente* | 200 puis 404 | `{"deleted":true,"id":"5adb3eee-b0ab-4953-bd65-24a2cd19d856","cascade_deleted":{"activities":0}}` | 200 | 21 |
| 3 | `POST /api/memory/projects`<br>corps `{"name": "ROBUSTESSE-projet-course"}` | cible | `{"id":"b8ce347a-6fec-4db7-9048-d841a59870b0","name":"ROBUSTESSE-projet-course","description":null,"contact_id":null,"sco` | 200 | 51 |
| 3 | `POST /api/projects/b8ce347a-6fec-4db7-9048-d841a59870b0/sched`<br>corps `{"timezone": "Europe/Paris"}` | 200 ou 404, jamais 500 | `{"snapshot_id":"aefce7fb-b780-4e17-ae67-c60e0dbc77b1","project_id":"b8ce347a-6fec-4db7-9048-d841a59870b0","engine_versio` | 200 | 14 |
| 3 | `DELETE /api/memory/projects/b8ce347a-6fec-4db7-9048-d841a59870b` | 200 | `{"deleted":true,"id":"b8ce347a-6fec-4db7-9048-d841a59870b0","cascade_deleted":{"files":0,"conversations_detachees":0,"do` | 200 | 30 |
| 3 | `GET /api/memory/projects/b8ce347a-6fec-4db7-9048-d841a59870b` | 404 (projet supprime) | `{"code":"HTTP_ERROR","message":"Project not found"}` | 404 | 6 |
| 3 | `GET /api/projects/b8ce347a-6fec-4db7-9048-d841a59870b0/sched` | 404 attendu si la cascade nettoi | `{"code":"HTTP_ERROR","message":"Projet non trouvé"}` | 404 | 4 |
| 3 | `GET /api/projects/b8ce347a-6fec-4db7-9048-d841a59870b0/sched` | 404 attendu | `{"code":"HTTP_ERROR","message":"Snapshot de planning non trouvé"}` | 404 | 4 |
| 5 | `GET /api/config/stats` | 200 | `{"entities":{"contacts":12,"projects":7,"conversations":1,"messages":2,"files":10},"uptime_seconds":6774.215553,"data_di` | 200 | 7 |
| 5 | `GET /api/memory/contacts` ?`{"limit": 200}` | reference | `[{"id":"84d60db9-ec7e-4351-a013-f2489464c4b8","first_name":"Claire","last_name":"Roux","company":"Cabinet Roux Conseil",` | 200 | 6 |
| 5 | `POST /api/memory/contacts`<br>corps `{"first_name": "ROBUSTESSE-000", "last_name": "Volume", "company": "ROBUSTESSE`<br>*volume 0* | 200 | `{"id":"756e616a-b11a-43bc-a288-d1c44e78a372","first_name":"ROBUSTESSE-000","last_name":"Volume","company":"ROBUSTESSE So` | 200 | 107 |
| 5 | `GET /api/memory/contacts` ?`{"limit": 200}` | liste 200 | `[{"id":"08b9802e-98a8-42ec-82f4-51ae5de6cd64","first_name":"ROBUSTESSE-299","last_name":"Volume","company":"ROBUSTESSE S` | 200 | 10 |
| 5 | `GET /api/memory/contacts` ?`{"limit": 200, "offset": 200}` | page 2 | `[{"id":"03eb9ad7-dcd5-4b7f-b11e-fdd27bd773c0","first_name":"ROBUSTESSE-099","last_name":"Volume","company":"ROBUSTESSE S` | 200 | 7 |
| 5 | `GET /api/memory/contacts` ?`{"limit": 200, "offset": 100000}` | page hors bornes | `[]` | 200 | 5 |
| 5 | `GET /api/memory/contacts` ?`{"search": "ROBUSTESSE", "limit": 200}` | recherche | `[{"id":"08b9802e-98a8-42ec-82f4-51ae5de6cd64","first_name":"ROBUSTESSE-299","last_name":"Volume","company":"ROBUSTESSE S` | 200 | 9 |
| 5 | `GET /api/memory/contacts` ?`{"search": "Sociéte", "limit": 50}` | recherche accent | `[{"id":"08b9802e-98a8-42ec-82f4-51ae5de6cd64","first_name":"ROBUSTESSE-299","last_name":"Volume","company":"ROBUSTESSE S` | 200 | 5 |
| 5 | `GET /api/crm/pipeline/stats` | pipeline | `{"total_contacts":312,"stages":{"active":{"count":1,"avg_score":130.0},"archive":{"count":1,"avg_score":0.0},"contact":{` | 200 | 7 |
| 5 | `GET /api/dashboard/today` | accueil | `{"date":"2026-09-05","events":[{"id":"c5f096de-b70e-4bf8-aba8-51530e5c0357","summary":"Séance 2 Garage Benali","start_da` | 200 | 9 |
| 5 | `GET /api/config/stats` | statistiques | `{"entities":{"contacts":312,"projects":7,"conversations":1,"messages":2,"files":10},"uptime_seconds":6808.028905,"data_d` | 200 | 5 |
| 5 | `POST /api/memory/search`<br>corps `{"query": "contact de volume", "limit": 20}` | recherche semantique | `{"query":"contact de volume","results":[{"id":"90bbbc4a-846f-450d-b874-f6f715bccab4","entity_type":"contact","title":"RO` | 200 | 65 |
| 5 | `GET /api/memory/contacts/export` | export | `BEGIN:VCARD  VERSION:3.0  FN:Sans nom  N:;;;;  END:VCARD   BEGIN:VCARD  VERSION:3.0  FN:ROBUSTESSE-date  N:;ROBUSTESSE-d` | 200 | 78 |
| 5 | `POST /api/invoices/`<br>corps `{"contact_id": "84d60db9-ec7e-4351-a013-f2489464c4b8", "lines": [{"description` | 200 | `{"id":"cd540079-971a-4922-88c0-48ce78e7bdf3","invoice_number":"FACT-2026-020","contact_id":"84d60db9-ec7e-4351-a013-f248` | 200 | 19 |
| 5 | `GET /api/invoices/cd540079-971a-4922-88c0-48ce78e7bdf3` | relecture | `{"id":"cd540079-971a-4922-88c0-48ce78e7bdf3","invoice_number":"FACT-2026-020","contact_id":"84d60db9-ec7e-4351-a013-f248` | 200 | 7 |
| 5 | `GET /api/invoices/cd540079-971a-4922-88c0-48ce78e7bdf3/pdf` | PDF 200 lignes | `{"pdf_path":"/Users/synoptia/Documents-Atelier-Exemple/factures/FACT-2026-020.pdf","invoice_number":"FACT-2026-020"}` | 200 | 91 |
| 5 | `GET /api/invoices/` | liste des factures | `[{"id":"cd540079-971a-4922-88c0-48ce78e7bdf3","invoice_number":"FACT-2026-020","contact_id":"84d60db9-ec7e-4351-a013-f24` | 200 | 8 |
| 5 | `POST /api/documents/13fe448e-4ed0-44f0-b565-02d675687e81/sect`<br>corps `{"title": "ROBUSTESSE section 00", "order": 0.0, "brief": "Contenu de volume. `<br>*section 0* | 200 | `{"id":"12a9af79-84d4-48d2-b1f7-a170582dd6f0","document_id":"13fe448e-4ed0-44f0-b565-02d675687e81","title":"ROBUSTESSE se` | 200 | 5 |
| 5 | `GET /api/documents/13fe448e-4ed0-44f0-b565-02d675687e81` | relecture du document | `{"id":"13fe448e-4ed0-44f0-b565-02d675687e81","title":"ROBUSTESSE-doc-60","brief":"Document de volume, 60 sections.","sta` | 200 | 6 |
| 5 | `GET /api/documents/13fe448e-4ed0-44f0-b565-02d675687e81/expo` ?`{"format": "md"}` | export md | `{"code":"HTTP_ERROR","message":"Document vide : rien à exporter."}` | 400 | 4 |
| 5 | `GET /api/documents/` | liste des documents | `[{"id":"13fe448e-4ed0-44f0-b565-02d675687e81","title":"ROBUSTESSE-doc-60","brief":"Document de volume, 60 sections.","st` | 200 | 4 |
| 2 | `POST /api/crm/import/contacts`<br>*CSV malforme* | 400/422 message localise | `{"success":false,"created":0,"updated":0,"skipped":2,"errors":[{"row":1,"column":null,"message":"Au moins un nom ou une ` | 200 | 13 |
| 2 | `POST /api/crm/import/contacts/preview`<br>*apercu CSV malforme* | 400/422 message localise | `{"code":"unknown_error","message":"Une erreur inattendue s'est produite, réessaie.","recoverable":true,"details":{}}` | 500 | 31 |
| 2 | `POST /api/crm/import/projects`<br>*CSV malforme* | 400/422 message localise | `{"success":false,"created":0,"updated":0,"skipped":2,"errors":[{"row":1,"column":null,"message":"Le nom du projet est re` | 200 | 3 |
| 2 | `POST /api/crm/import/deliverables`<br>*CSV malforme* | 400/422 message localise | `{"success":false,"created":0,"updated":0,"skipped":2,"errors":[{"row":1,"column":null,"message":"Le titre du livrable es` | 200 | 3 |
| 2 | `POST /api/crm/import/vcf`<br>*vCard malformee* | 400/422 message localise | `{"code":"HTTP_ERROR","message":"Fichier VCF invalide : At line 3: Failed to parse line: PAS UNE VCARD DU TOUT"}` | 400 | 4 |
| 2 | `POST /api/memory/contacts/import`<br>*vCard malformee* | 400/422 message localise | `{"code":"HTTP_ERROR","message":"Fichier VCF invalide : At line 3: Failed to parse line: PAS UNE VCARD DU TOUT"}` | 400 | 3 |
| 2 | `POST /api/data/import/contacts`<br>*CSV malforme* | 400/422 message localise | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"","message":"Input should ` | 422 | 4 |
| 2 | `POST /api/data/import/conversations`<br>*JSON malforme* | 400/422 message localise | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"","message":"Input should ` | 422 | 3 |
| 2 | `POST /api/crm/import/contacts`<br>*fichier de 0 octet* | 400/422 message localise | `{"success":true,"created":0,"updated":0,"skipped":0,"errors":[],"total_rows":0,"message":"Import termine: 0 crees, 0 mis` | 200 | 3 |
| 2 | `POST /api/crm/import/contacts`<br>*extension trompeuse* | 400/422 message localise | `{"success":true,"created":0,"updated":0,"skipped":0,"errors":[],"total_rows":0,"message":"Import termine: 0 crees, 0 mis` | 200 | 3 |
| 2 | `POST /api/voice/transcribe`<br>*faux WAV* | 400/502 message localise | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"audio","message":"Field re` | 422 | 5 |
| 2 | `POST /api/voice/local/transcribe`<br>*faux WAV, voix locale* | 400/502 message localise | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"audio","message":"Field re` | 422 | 3 |
| 2 | `GET /api/voice/local/status` | 200 | `{"enabled":false,"stt_available":false,"tts_available":false,"whisper_models":{"tiny":{"size_mb":75,"ram_mb":1024,"label` | 200 | 4 |
| 2 | `GET /api/skills/info/inexistant`<br>*/api/skills/info/inexistant* | 404 message localise | `{"code":"HTTP_ERROR","message":"Skill 'inexistant' not found"}` | 404 | 3 |
| 2 | `GET /api/skills/schema/inexistant`<br>*/api/skills/schema/inexistant* | 404 message localise | `{"code":"HTTP_ERROR","message":"Skill 'inexistant' not found"}` | 404 | 2 |
| 2 | `GET /api/skills/prompt/inexistant`<br>*/api/skills/prompt/inexistant* | 404 message localise | `{"code":"HTTP_ERROR","message":"Skill 'inexistant' not found"}` | 404 | 2 |
| 2 | `GET /api/skills/download/inexistant`<br>*/api/skills/download/inexistant* | 404 message localise | `{"code":"HTTP_ERROR","message":"File 'inexistant' not found or expired"}` | 404 | 3 |
| 2 | `GET /api/skills/download/../../etc/passwd`<br>*/api/skills/download/../../etc/passwd* | 404 message localise | `{"code":"HTTP_ERROR","message":"Not Found"}` | 404 | 2 |
| 2 | `GET /api/v3/commands/inexistante`<br>*/api/v3/commands/inexistante* | 404 message localise | `{"code":"HTTP_ERROR","message":"Commande 'inexistante' introuvable"}` | 404 | 2 |
| 2 | `GET /api/v3/commands/inexistante/schema`<br>*/api/v3/commands/inexistante/schema* | 404 message localise | `{"code":"HTTP_ERROR","message":"Commande 'inexistante' introuvable"}` | 404 | 2 |
| 2 | `GET /api/actions/inexistant`<br>*/api/actions/inexistant* | 404 message localise | `{"code":"HTTP_ERROR","message":"Agent 'inexistant' introuvable"}` | 404 | 2 |
| 2 | `GET /api/actions/tasks/inexistant`<br>*/api/actions/tasks/inexistant* | 404 message localise | `{"code":"HTTP_ERROR","message":"Tache 'inexistant' introuvable"}` | 404 | 2 |
| 2 | `GET /api/tools/inexistant/manifest`<br>*/api/tools/inexistant/manifest* | 404 message localise | `{"code":"HTTP_ERROR","message":"Outil 'inexistant' non trouvé"}` | 404 | 3 |
| 2 | `GET /api/personalisation/templates/inexistant`<br>*/api/personalisation/templates/inexistan* | 404 message localise | `{"code":"HTTP_ERROR","message":"Template not found"}` | 404 | 6 |
| 2 | `GET /api/board/advisors/inexistant`<br>*/api/board/advisors/inexistant* | 404 message localise | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"path.role","message":"Inpu` | 422 | 3 |
| 2 | `GET /api/board/decisions/inexistant`<br>*/api/board/decisions/inexistant* | 404 message localise | `{"code":"HTTP_ERROR","message":"Decision not found"}` | 404 | 4 |
| 2 | `GET /api/mcp/servers/inexistant`<br>*/api/mcp/servers/inexistant* | 404 message localise | `{"code":"HTTP_ERROR","message":"Server not found"}` | 404 | 3 |
| 2 | `GET /api/agents/sessions/inexistant`<br>*/api/agents/sessions/inexistant* | 404 message localise | `{"code":"HTTP_ERROR","message":"Session introuvable"}` | 404 | 5 |
| 2 | `GET /api/agents/tasks/inexistant`<br>*/api/agents/tasks/inexistant* | 404 message localise | `{"code":"HTTP_ERROR","message":"Tâche introuvable"}` | 404 | 5 |
| 2 | `GET /api/images/download/inexistant`<br>*/api/images/download/inexistant* | 404 message localise | `{"code":"HTTP_ERROR","message":"Image not found"}` | 404 | 2 |
| 2 | `GET /api/processing-tasks`<br>*/api/processing-tasks* | 404 message localise | `{"traitements":[{"id":"a4fb2272-ac7c-449d-b3ad-0572addced2d","type":"indexation","label":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` | 200 | 3 |
| 2 | `POST /api/v3/commands/generate-template`<br>corps `{"name": "ROBUSTESSE-ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ` | 422/400 | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"brief","message":"Field re` | 422 | 3 |
| 2 | `POST /api/escalation/estimate-cost`<br>corps `{"provider": "ROBUSTESSE-inconnu", "model": "x", "input_tokens": -1, "output_t` | ? | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"input_tokens","message":"I` | 422 | 3 |
| 2 | `POST /api/escalation/check-limits`<br>corps `{"estimated_cost": 1e+308}` | ? | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"query.input_tokens","messa` | 422 | 2 |
| 2 | `POST /api/email/setup/detect-provider`<br>corps `{"email": "ROBUSTESSE-ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ` | ? | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"query.email","message":"Fi` | 422 | 3 |
| 2 | `POST /api/email/setup/validate`<br>corps `{"email": "pas-un-email", "password": "x"}` | ? | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"client_id","message":"Fiel` | 422 | 2 |
| 2 | `GET /api/config/llm/models/ROBUSTESSE-inconnu` | 404/422 | `{"code":"HTTP_ERROR","message":"Fournisseur inconnu : ROBUSTESSE-inconnu"}` | 400 | 2 |
| 2 | `PUT /api/config/preferences/../../etc`<br>corps `{"value": "x"}` | 404/422 | `{"code":"HTTP_ERROR","message":"Not Found"}` | 404 | 2 |
| 2 | `POST /api/perf/conversations/search` | 405 | `{"code":"HTTP_ERROR","message":"Method Not Allowed"}` | 405 | 1 |
| 2 | `GET /api/perf/conversations/search` ?`{"q": "ROBUSTESSEROBUSTESSEROBUSTESSEROBUSTESSEROBUS` | ? | `{"results":[],"source":"database","total":0}` | 200 | 8 |
| 2 | `POST /api/rgpd/anonymize/inexistant` | 404 | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"","message":"Field require` | 422 | 3 |
| 2 | `GET /api/rgpd/export/inexistant` | 404 | `{"code":"HTTP_ERROR","message":"Contact non trouvé"}` | 404 | 3 |
| 2 | `POST /api/crm/contacts/inexistant/recalculate-score` | 404 | `{"code":"HTTP_ERROR","message":"Contact not found"}` | 404 | 3 |
| 2 | `PATCH /api/crm/contacts/inexistant/stage`<br>corps `{"stage": "active"}` | 404 | `{"code":"HTTP_ERROR","message":"Contact not found"}` | 404 | 5 |
| 2 | `PATCH /api/crm/contacts/inexistant/stage`<br>corps `{"stage": "ROBUSTESSE-inconnue"}` | 422 etape inconnue | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"stage","message":"Input sh` | 422 | 3 |
| 1 | `GET /api/invoices/d0ca0000-0000-0000-0000-000000000000/pdf` | 404 temoin | `{"code":"HTTP_ERROR","message":"Invoice not found"}` | 404 | 5 |
| 1 | `POST /api/memory/contacts`<br>corps `{"first_name":"ROBUSTESSE-profond","tags":{"a":{"a":{"a":{"a":{"a":{"a":{"a":{`<br>*2000 niveaux* | 422/400 sans 500 | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"tags","message":"Input sho` | 422 | 5 |
| 1 | `POST /api/memory/contacts`<br>corps `{"first_name":"ROBUSTESSE-gros","notes":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA`<br>*corps 10 Mo* | 413/422 | `{"code":"VALIDATION_ERROR","message":"Données invalides dans la requête","details":[{"field":"notes","message":"String s` | 422 | 44 |
| 1 | `POST /api/memory/contacts`<br>corps `{"first_name": "ROBUSTESSE-tags-100k", "tags": ["t", "t", "t", "t", "t", "t", `<br>*100k tags* | ? | `{"id":"d6ce97d0-fbe9-4679-b5ba-ba8caf2991c1","first_name":"ROBUSTESSE-tags-100k","last_name":null,"company":null,"email"` | 200 | 7887 |
| 1 | `POST /api/memory/contacts`<br>corps `{"first_name":"x"}`<br>*Content-Length faux* | 400 | `LocalProtocolError: Too little data for declared Content-Length` | - | 1 |
| 5 | `GET /api/memory/contacts` ?`{"limit": 200}`<br>*mesure 0* | liste apres le contact a 100k et | `[{"id":"d6ce97d0-fbe9-4679-b5ba-ba8caf2991c1","first_name":"ROBUSTESSE-tags-100k","last_name":null,"company":null,"email` | 200 | 17 |
| 5 | `GET /api/memory/contacts/export` | export vCard | `BEGIN:VCARD  VERSION:3.0  FN:Sans nom  N:;;;;  END:VCARD   BEGIN:VCARD  VERSION:3.0  FN:ROBUSTESSE-date  N:;ROBUSTESSE-d` | 200 | 62 |

> Trace brute complète (713 essais, une ligne JSON par essai avec le delta du
> journal serveur) produite par le harnais de la persona ; la table ci-dessus en
> est la restitution.
