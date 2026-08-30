Je vais d’abord recenser ce que les campagnes ont déjà parcouru, puis relire les chemins nominaux (générateurs, actions, formulaires, contrats API) pour chercher des cousines des trois pannes, pas elles.Les campagnes passées me disent ce qui a déjà été parcouru. Je lis ça, puis je lance des lectures parallèles sur les générateurs, le registre d’actions et les contrats API.Je lance des lectures ciblées en parallèle : générateurs et replis, contrats frontend/backend, registre d’actions, et les surfaces que les campagnes n’ont pas encore éprouvées.Les agents tournent. Je relis en parallèle les replis des générateurs, le bac à sable et les contrats de formulaires pour pouvoir vérifier chaque finding.Je commence par cartographier les lectures de corps d'erreur en flux et le chemin des pièces jointes (tableur inclus).Je commence par leJe vais registre d cartJe commence'actions etographier les génér par cro leiserateurs et leurs routage des v les sch replisémues,as Create,/Update du pour suivre puis suivre backend avec les app chaque destination le chemin nominalels frontend, jusqu'à son jusqu en’ handler réel. prioritéau fichier liv surré. prestations, commandes, suivis, variables et factures.Je lis les replis des générateurs, le bac à sable et les points d’émission de `skill_file`.Je lis les schémas et les clients API en parallèle, en commençant par les parcours peu éprouvés.Je commence par cartographier les chemins nominaux (email, fichiers, atelier, tâches, factures, CRM, board, MCP, images, dictée) dans le code, pas dans les docs.Je lis les routes et les gestes UI critiques (envoi mail, 501 facture, indexation, atelier) pour collJeer le chemin réel passe. au bac à sable et aux skills texte/analyse, puis au déclenchement côté chat.Le contrat prestations est déjà clair (`phase` obligatoire). Je cherche maintenant les formulaires UI et les autres Create/Update.Verdict : plusieurs chemins nominaux tiennent (envoi mail panneau, PDF facture, atelier, tâches, Board, dictée, image). Les faux livrables sont surtout email (joindre / fil / IMAP) et indexation `chunk_count: 0`.

---

## 1. Email (panneau, pas le chat)

**Envoi depuis le panneau : oui, le geste part vraiment.** Composeur -> confirmation externe -> `POST /api/email/messages`. Gmail et IMAP/SMTP sont branchés.

```1125:1186:src/backend/app/routers/email.py
@router.post("/messages")
async def send_email(...):
    ...
    if account.provider == "imap":
        ...
        message_id = await provider.send_message(send_req)
        return {"id": message_id, "labelIds": ["SENT"]}
    else:
        gmail = await get_gmail_service_for_account(account_id, session)
        result = await gmail.send_message(...)
```

Wizard : Gmail (4 étapes OAuth) et SMTP/IMAP (2 étapes) existent. `EmailPanel` ouvre le wizard s’il n’y a pas de compte.

**Faux livrable — bouton Joindre.** Visible, toujours `disabled`. Aucun champ PJ dans le contrat HTTP (`SendEmailRequest` : to / subject / body / cc / bcc / html). Le provider IMAP sait attacher, l’API et l’UI ne passent rien.

```323:326:src/frontend/src/components/email/EmailCompose.tsx
          <Button variant="ghost" size="sm" disabled>
            <Paperclip className="w-4 h-4 mr-2" />
            Joindre
          </Button>
```

```97:105:src/backend/app/models/schemas_email.py
class SendEmailRequest(BaseModel):
    to: list[str]
    subject: str
    body: str
    cc: list[str] | None = None
    bcc: list[str] | None = None
    html: bool = False
```

Gmail n’a même pas le paramètre PJ :

```223:231:src/backend/app/services/gmail_service.py
    async def send_message(
        self,
        to: list[str],Je vér
        subject: strifie,
 encore        body: le str branche,
        cc: list[mentstr des] | None = None,
        outils sur bcc: list[ le chemin non-str] | Nonestream et l’ = Noneabsence,
 de sanit        html: bool =isation du False,
    ) texte -> dict:
``` table

**Fur.aux livrable — Répondre / Transférer.** Ça ouvre un nouveau brouillon (`Re:` / `Fwd:`) avec citation texte. Pas de `In-Reply-To`, pas de thread Gmail, pas des PJ d’origine. `EmailDetail` n’affiche jamais les pièces (aucun `has_attachments` dans le composant).

```188:205:src/frontend/src/components/email/EmailDetail.tsx
  function handleReply() {
    ...
    startComposing([message.from_email], `Re: ${message.subject || ''}`, buildQuotedReply());
  }
  ...
  function handleForward() {
    ...
    startComposing([], `Fwd: ${message.subject || ''}`, forwardBody);
  }
```

IMAP côté SMTP gère `in_reply_to` et `attachments` (`imap_smtp_provider.py:409-420`) mais le routeur ne les remplit jamais.

**Échec franc IMAP — « Générer une réponse ».** Lecture IMAP ne cache pas le message en base. La génération lit uniquement `EmailMessage` SQLite -> 404.

```1077:1107:src/backend/app/routers/email.py
    if account.provider == "imap":
        ...
        dto = await provider.get_message(message_id)
        return { ... }   # pas de session.add
```

```1518:1521:src/backend/app/routers/email.py
    message = await session.get(EmailMessage, message_id)
    if not message or message.account_id != account_id:
        raise HTTPException(status_code=404, detail="Message not found")
```

**Faux livrable IMAP — dossier Envoyés.** `send_message` SMTP n’append pas dans `\Sent`. Le JSON ment : `"labelIds": ["SENT"]`. Gmail, lui, range vraiment dans Envoyés.

**Friction.** `sendEmail` front jette `'Failed to send email'` et jette le `detail` SMTP (`email.ts:306`). Répondre à tous recolle `from` + `to` sans retirer ton adresse (`EmailDetail.tsx:195-198`). HTML-only : citation = snippet (`body_plain || snippet`).

---

## 2. Files

**Indexation : le HTTP 200 n’est pas « cherchable ».** Extraction vide -> `chunk_count = 0`, consigné, 200. Le catalogue refuse `chunk_count > 0`. Le FileBrowser n’inspecte pas leFindings compte uniquementur : spinner, off avec chemin d’ =exécution. ` succèsResponseNotRead`.

```434 n’est pas:439 ref:src/backendiché/app/services.

---/indexation.py

##
    Cause else:
        logger visible.warning(f du 400 table"No text extracted for {file_ur (nouveau)

name}")
   Le  indexed400 n_’atest = datetime.now( pas un refusUTC)
    await MIME _consigner_ côtéresultat(
        backend. Le table file_id,ur est lu chunk_count,,Je indexed_at, vér inject figer_perifie encoreé, puis leimet lere parser=fig fournisse Excelur refuse la multier_perimetre
    )
 requête.

**Che-onglets```

```271min d et:277’exécution le formulaire:src/frontend ( «/src/components fichier/files/Filecelui que » desBrowser.tsx
 analyses.    l’UI emprunte)**

1 try. `ChatInput {
      const metadata. = await indexFile(entry.path);
tsx:621-      onFileIndex?.(metadata);
```628` : `

LestreamMessage journal projet`. avecsync a été `stream: true rendu` et `file honnête_paths`.
 (`etat_pour2. `chat_une_index.py:_ation`,do_stream_ `projectresponse` `_sync_service217.py:585-8-2190604` : `_get`). L_file_context’explorateur de( fichiers, nonfp, …)`..

**Upload projet
3. ` : nominalchat.py:305.**-312` : `POST /api `extract_text/files/upload` hors` exige bou `project_idcle.
`, extensions4. `file born_parser.py:ées120, copie atom-121ique,` puis indexation `_. `ProjectModalextract_xlsx`` appelle `259-296 `upload`ProjectFile`.

 : `openpy**Lecture :**xl` `GET /api/files/{id `read_only}/content` ==True, texte extr data_only=ait, **True`, chaque celluletron viaqué à `str(c 10 000)`, joint carure.** `" (`files.py |: "417`, plafond 2000 lignes-423.
`).

5. `chat**Recherche UI.py:388- :** le «398` : tr Filtrer…oncature » du FileBrowser à **15  est un000 caractères**, bloc filtre de `--- FICH nom localIER: … ---,` ** pas `brut**.
6search_files`.. `llm La.py:772 recherche sémantique-773` : est ce côté chat bloc/ part dans **mémoire.

**``system_promptGET /api/`**files/` sans pér (`## Contexteimètre : mémoire`), toujours pas dans le message vrai.** utilisateur.
7. Dette `context assum.py:36-ée, aucun appelant UI (64` : `trim_to_FilefitBrowser n`’ neappelle rogne **jamais pas `listFiles`). Fu** le prompt système. Siite inter le système-proj déets si un client tapeborde la route.

```37 déjà le:49:src/backend/app budget, le commentaire l’assume : «/routers/ un refus propre defiles.py
@ l’API vautrouter.get("/", response mieux qu’une question disparue »._model=list[FileResponse]) Les
async def list sch_files(...):émas d’outils ne
    """List all indexed files.""" sont **pas**
    result = dans await session.execute(
 `        select(Filetotal_tokens()`.Metadata)
        .
8. Fourorder_by(nisseur streamFileMetadata.indexedé_at.desc,())
``` `raise

---

##_for_status 3. Documents` ( → latelier)

**’écran affCheiche `API errormin nominal: 400` tient (`openai.py:.** Créer263` et héritiers (vide)). -> `

DeuxPOST /{id mécanismes}/outline` ( dansLLM, le 409 code si suff sectionisent déjà réd àigée, remplacement si produire ce trame vide) 400, -> `POST / sans hypothsections/{id}/èsedraft` SSE + hors flush 2 s source -> export ` :

md`/`**docx` via `/Aapi/skills/download/{file_. Carid}` (globactères C `*_0 /` NUL dans les + 8 premiers cellules (le chars plus plausible de pour un l tableur et’uuid).

**Export pas vide un : éche PDF)**  
`c franc, message_extract_xlsx honnête:.** Pas278` fait un faux `str(c livrable.

)` sans```802:807 filtre.:src/backend `sanitize/app/rout_for_contexters/documents.py` n’est
    non_orphan_with **jamais** appelé_content = [ sur less for s in pièces joint sections if not ses (.orphan and sseulement.content.strip()]
 fact    if not nonures / workspace_orphan_with)._content:
        `DANGEROUS raise HTTPException(
_CHARS` (`            status_codeprompt_security.py=400,
            detail="Document vide:105-112`) ne retire : rien à exporter que Z.",
        )
WSP/```

**`BOM, **PATCH content=""` flippas** `\pe encore `x00` nivide `\` -> `broux01-\x08`. Openillon`.** L’UI ne PATAI, Anthropic et Gemini refusent unC `\Heu0000` pas le contenu ( dans unréd message paraction un = 400. Un SSELe export Excel /). chemin nominal CSV métier C contient produit’ souvent souvent ces octetsest un défaut ; d un **fichier télé uncharge’API, pas `.docxable** (carte le`/ geste é ``.pdf` beaucoupskill_file`cran.

```262 moins ou bouton:265 de:src/backend.

**B. Le table/app/rout téléur enfers/documents.pychargement)le **même quand le
 prompt    updates = payload.model système, que la_dump(exclude rien_unset=True génération réelle ne borne, exclude_none a échoué**. ensuite=True)

    `registry.execute`**  
15 if "content" ne fabri 000 caractères (~ in updates and sectionque pas un fichier3.status == "vide après 750 tokens)":
        section une exception coll.status = "brou : cés auillon"
```

’ systemUneest `CodeGen + chaîne videSkill.execute` qui identité est **av + capacités «ale + outils dans l’échec. Sur updates et une fenêtre courte ( », rendOllama  donc un parser8 192 le statut de avec change. Dette réserve repl atelieri**, de sortie), déjà not puis le systemée, répond seul toujours dépasse ` `success=Truemax_tokens` vraie`.

 de `ContextComment.

---

##Window` l 4. Tasks ;’utilisateur décl

** `enche vraiment unNominal tienttrim_to_ générateur (intent.** Création `fit` coupe parPOST /api le **message mots-clés ret/tasks/ utilisateur**, pas leiré,`. Kanban : fichier. L BUG-137) drag’API répond :
- bouton 400 ( -> **Procon `updateduire** /texte /Task({ formulaire payload status })` guidé), (`TaskKanban → `POST / pas un message.tsxapi:/75skills/ métier-127execute/{skill_ « fichier trop gros`). Fid}`
- ».

Ceiltres projet ( `{action: produire n’est **API) et tagpas doc**x :|xlsx (client) : `.|pptx "… `xls"}`` ( → `TasksPanel.tsxrefskill_id`:49usé à l’ forindex-,99cé, auto en-exec après le`voi bloqué (BUG-118 stream
- chat,).

** libre → outil `ChatInput.Friction.** É `generate_documenttsx:435`chec de drag` (docx + seulement/ `path `console.error`pptx/xlsx uniquement_security.py: (carte),129 revient contenu-134 au annoncé`), prochain image reload (plus comme markdown dans,
- `{{ ` pas deaction: skill_ACCEPT_FIC toast). Statid}}` encoreHIERS`),ut honor ni `é ;cancelled` hors un colon la 400 MIME détection parnes kan ( mots-clés neban (`le l backend ignoretodo` / `’est plus le MIME,in_progress`

--- il lit / `done`)

### 1 l : la. Re’extension).

 cartepliL disparaît du part’écran reste tableau `API error:agé : l.

---

##’échec sandbox 400` : 5. In le corps du devient unvoices

**501 refus va « aux d logs ( succèsquand »
’envoi :** il est lu), oui, l’API leF jamais à l’ichier :** prometutilisateur (` `srcopenai.py:260 encore/backend/app-263`).

./services/skills** L’UI ne/code_executorÉ le propose.py: pluschec franc**770-908`

.** Déc pour**ision produit document l’utilisateur.Croit **Frictionée.

 obtenir de```918:947 / diagnostic** tant:src/backend obtient que M/app/rout :** un Wordistral / DeepSeekers/invoices / / Perplexity.py
@ Power / Infomaniakrouter.post("/{Point / Excel métier ne lisinvoice_id}/ent. En pas le bodysend")
async ( casci d’absence def send_invoice_by_email-dessous).

 de code---

## , `(...):
    ...
    raise1. Corps dSyntaxError`’ HTTPerreurException HTTP(
        encore non jet status_code= réparé501,
        detailé (, timeoutcousins,="L'en hors, le `CodeExecutionvoiError` de factures correct par email n' (ex. attributif duest pas encore disponible inex jour. "
        "istant), fichier)

LesTélécharge le vide ou « 5 déjà PDF quasi et vide », envoie corrigés (-le manuellement leOpenAI +.",
    )
 hérit skill **écrit```

Testiers GLM quand UI/Kimi/ : même un `queryByQwen/Mini fichier** viaTitle('EnvoyerMax/Grok `_fallback_execute, Gemini, Anthrop par email')``ic, O absent (` et lellama, OpenRouterInvoicesPanel.test présente) :.tsx:136 comme génér non-141é.

**Che refmin`). :** ` `InvoiceFormichésextract` n_python’_a.

Restcode` → `ent pasexecute_sandboxed d des` → `except’envoi. `` / `elseclient.stream` Le` → net gestetoyage option + `raise_for_status()` annoncénel des **sans** ` à fences → `aread()` :return l await’écran self est._ le log n’fallback_execute(...) PDFa que`. Auc + statut le statutune à, l exception la main.

** remont’écran `APIPDF : error: Née. `registry nominal`.**,

.execute` (`| F garderegistry.py:151ichier | L profil-167ignes | Ce émetteur in`) pose quicomplet (`in alors se `success=Truevoices.py:645 passe`-657 + |
|---|---| URL`). Ouverture via---|
| ` de téléchargement plugin shellm.

**Re Taistral.py` |prouri, repl ` :** n105’i cheminimporte quel-114` puis ppt si web.

** `218x/docx/Conversion-220` |xlsx dont devis -> `raise_for le code facture : nominal_status()` Python plante.** ; ` (TRIANGLE Copie des, importlogger.error(… status lignes_,code `)`, timeout ;). LFACT-…`, yield’UI aff devis `API error: `iche unconverted`. UI {code}` |
 fichier, pas ` et API refus| `deepseekskill_file_ent `converted.py` | `error`.

**`/`67-76`Gravité :**cancelled`. Un puis `176- faux livrable178` | idem ( devis |
 **|brou `perillon**mécanplexity.py`isme reste | `stream commun convertible` + `raise aux (commentaire_for_status trois «` puis `167 génér accepted-169` |ateurs Office). ou sent » non idem |
| `

---

### applinfomaniak.py 2. Excel` | `raiseiqué, de repli : co_for_status `invoices.pyquille A` puis `163:797-165` |/-801` idem |

MB/C, + `Invoiceême forme toujoursForm.tsx: à « assez385-388`). plein l’écran que

**L le »
 400 tableurignes :****Fichier :** ` formulaire. Sursrc/backend/ ces libre, pas 4, leapp/services/ **skills/xlsx_ catalogue CRMle motifgenerator.py:187 `prest du-251`ations`  (surtout (suivi400 est  de ill246-251),isible même mission `_ en, autrefallback log objet_execute` **.

`142-185).

---

web_search.py

**Croit## 6.:177-179 obtenir CRM pipeline` ( / obtient

Pas dBrave) et ` :** un table’objet271-273ur avec « opportunité ».` (Duck sesDuckGo) : Le données. Sans tableau `HTTPStatusError pipeline Markdown (`` log = contacts +|`) `stage`gué ni JSON `" au (7 colonheaders"`, le statut, **bodynes). G parser invent ignoreste :e `headers:é**, puis « ["A","B réponse Nouveau contact »","C"]`, vide ( `rows: [] (`CRMPanel.voir §`.tsx:413-5).

--- Une420`) +

## 2 feuille drag de. Pi «èces jointes : phase Données » + ce -> titre + en que `PATCH /contacts-t l’UI laisse/{id}/stageêtes + footer «` + activité Généré par THERE passer vs +SE ».

 ce recal**Che que le backend faitcul score.

**min :** `

- SSheetsgenerate_document`électeur :** ann / pushonce du best markdown `accept` : `formats-effort à (`workspaceIndexables.ts: la création, sync_tools.py:21-70` dédi243 aligné `-POST /246apié sur `INDEXABLE_`) → pas de/crm/sync bloc Python → repl`. AnEXTENSIONS` (xlsxi. Ounon, csv codecé comme open option, pdf, docx,, pptxpyxl qui, code plante pas comme… → même garantie **pas** image.

 parser, **. `SCodeGenSkill`coring : `pas** `.xls ne re`).
- «calculate_base_valide pas le Tous les fichiers »score` à repl reste (` la création,i.

**PourquoiChatInput.tsx ça `:361update_contact_ passe la-366score` au changement garde`). Un `. de phase :**xls `_. (` / `.validate_document_Le score > png` échcontent` (`100 desoue àcode_executor.py campagnes n’ l’index ;:176est pas relu badge d-227 ici’erreur ;`) exige.)

---

 en ## 7.voi **2 lignes *avec une Board (bloDécquéision** tant)

** valeur*. queNominal tient le fichier Tit est.** re + en là-t5 rô (`435`,les distinctêtes A/B `136/C = s (6`).2. Le commentaireAnalyste, Strat ditège, Av
- Dragocat du Diable « hors header » & ; le code ** drop : `usecompte, le PragmatFileDrop.ts:ique, Visionnaire header**. `66-67),skills.py:` connaît providers186-217 encore distincts, ` `` nePOST /api relxls` en/board/delance donciberate` SSE MIME, sans pas.

 filtre (`**Repro :** dadvisor « gén_*` puis’extension synthèseère. un L Excel’index, de refuse `done` ensuite suivi = ».
- Extraction id persist en chat chat (outil)é). UI : et `stream index partDeliberation`. ouagent ` Produire table

**`ur avec un modèleextract_text`.thoughtSignature` Gemini qui n `.’émetxlsx : hors chemin pas` OK de `| Board, col `..**xls Le` Board → n |`.

**’ `envoieNone` (`Gravité :**file faux livrable pas d’_outilsparser LLM.py:.

---

###127 (`-129 3. Excel`).board
.py-` É : :chec d pas plusieurs’extraction **après de `tools`). onglets promis** un Le re, index « Prjeu unêt » : ` `thoughtSignature` seul produitchat est dans `gemini
**.py:2188.py:Fichier :** `-2190`352-353`xlsx_generator.py ( et `::119stream) et-137 `163451-452` pour` vs6 la `157-1639` **-165boucle d’` +outils du (non-stream) : ` `_parselogger_.markdownwarning chat**. Une_table` (` seulement. délibération Gemini Enune liste `  stream3, sans function calling ne rec un statusheaders`/`rowsro `N erreur(`, `wsises)` (`.title = "Don pas ce221nées"`)

** Croit obtenir /4-2224xx.

--- obtient2`) part

## 8 :** « dans l’indicateur. MCP

** Chaque d18 presets, pas tableau sera 19.** Liste’activité (` converti en un `PREChatInput.tsx onglet ».SET_SERVERS:666` Le parser `-668mcp.py:306 ignore`), **-520 les `pas** dans` (## Nom lafilesystem … playwright). d bul Transport’onglet`le. Le message **stdio réel et fusion utilisateur affiche quand** (` même `[Fichmcpneiers_ joints (service:ou ….py prend]`:) (` un210Chat seulInput`, spawn tableau. `tsx:stdin.

533-536`)./stdout`**Che Si `: tous388-min nominal markdown les extra395`) :**its tomb + JSON-RPC modèleent, le modèle initialize non code-capable répond ** + viasans** list tools.

** `/ le fichier.

Installer !=api/skills/` connectéexecute`, ou `extract_text:.** `installgenerate_document`_preset` `131-133` formatenabled : toute=True`, xlsx.

 ` exception d**Gr’openstart_server`,avité :** fauxpyxl ( et livrable (classe **rendfichier prot  réelégé, x200 même si lelsx cor start, structure mensrom échoue** (`ongèrepumcp.py) →:682).

---

-687 `None` → « Impossible d’### 4.`). L Wordextra deire le contenu’UI grise repli : le » (`chat Python la carte.py «:311-312`), devient installé pas » un (` 400 leTools corps fournissePanel.tsx: duur.

Pas102 document
**F dichier :** `docx’image-112_generator.py:`)., pas de base Un249-311`64 vers `npx - + `code_ le LLMexecutor.py:886.y @…` long-908`

** T peutCroit obtenir /aille r obtient disater :** un le rapport handshakeque. Si.  le Files code n50 Mo (`’est pas dansystemfile_parser.py des / Time:14 fences ferm / Fetch peuvent`) marchées ( ; plafonder sans cléGemini brut utile ;, fence Hub pour or le promptpheline),Spot / = chaque Stripe / Notion 15 000 ex ligne Python carigent ` devientenv_required`.. / un paragraphe. Les

Le fichier fences flag + ferm APIées sont bien 40 000 `installed` compare retir car `nameées ; s..lower pour().replace("’il ne le bloc (`chat ", "-")` reste plus.py:453 à rien`).

---

 `preset (`## 3.["cleaned_content` `idstream"]:` false : vide ou` et « ≤ 50), les HubSpot CRM » ** outils : ->le contenu `hubspot- H1 toujours original (crm` vs id vrai

Toujoursle `hubspot` le script)** est r (` cas **envoyémcp.py:528sur au parser-534 l’API**..

Les tableaux Markdown

-`). L’UI, deviennent `chat.py: des lignes tabul elle1548-155ées, (` compare `8301s.name ===` preset stream.name`.-307

---

##`), pas un tableau → 9. Images `_ Word.

**Re

**pro :** `{streamNominal si_response` →action: produire doc unex "… ` clé238 est là"}` (.** `POST /2`api/images/prompt Python inject `stream_responsegenerate` ->é,_with_tools fichier local voir ` + `GET8 /api/images () puisoutils plant).
- `/download/{id}`. Lage sandbox,chat.py:168 ou modèle qui dump’ét9 du` non `python-docx`abli (`CommandExecutor`) confirme-stream → sans ` `stream_response, gén ``` `.(ère, affiche via blob

 authent**ifié,Grav `context, raise_downloadGeneratedImage`ité :** faux livon_error= ourable (cousTrue)` **sansvre le dialogueine exact ` Tae du ppttools=`uri. Messagex qui**. Le colleBubble charge modèle peut aussi le code sur en **affirmer les slides).

 fetch** `---

###  tokencreate_contact`5. HTML :isé ; page ( rienpas un `<img «>` n complète nu’est exécuté » =).. Document prompt

Sans clé : éché : appé `docs/camp400 message dansagnes un/2026 utilisateur-08-29 `<pre>`
,**-personFichieras :**/ pas un fichier `html fantôme.

constats/H---1-

stream##- _generator.py:117-137false10-. Voicesans-

**outils.md`.

` et `_Nominal.** Micro**Frontendwrap_in_ -> Gro :** leq (consenthtml` 174 composeement au-210

**ur n’emprunte clic) ou voixCroit obtenir / pas ce locale obtient :** une chemin. `Chat. ` landing / unInput.tsx:handle mini-site.Transcript` inject Sanse dans621-625` force `<! le composeur (` `stream: trueDOCTYPE` / `<Chat`. `Inputsend.tsxhtml>` (bloc:307-316 ` ```html ``). Bout inMessage` de `chaton dés.tscomplet,: markdown136-activé tant141` (`stream, Python que le plugin n: false`) est), le’est pas prêt **export skill.

é et---

## Synth ** sansèse paréchappe appelant tout le texte gravité

| UI et Grav**. RFCité le | Geste | Rés : metultat réel `stream: true dans |
|---|---|` + `disable `<---|
| F_tools:pre>`** suraux livrable fond | Jo true`. Board / atelier documentsindre sombre un. `execute mail : | leurs Bouton mort propres` ; streams n’éch API sans, `oue jamais PJ |
| Fraise_on_. `getaux livrableerror=True`,_mime_type | Répondre pas `` n / Transférer |POST’ /aapi pas/ ` Nouveauhtml` danschat/send`. mail

 `**baseGr.py`, pas unav ; iciité :** fil ; PJ perdues |
| F faux le MIME est for livrable **aux livrable | IMAP :si** uncé à `text Envoyer client/html`, puis HTTP ong donc le / télélet Envoyéschargement a test | SMTP / futur part l’air lég, `\ éSent` pasitimecran utilise aliment.

**Repro `stream: falseé ; :** Produire →`. Pas un JSON Page web geste dit (` SENTactionData.ts: d |
|’écran Faux actuel.

---

## livrable | 4. Chem128 IMAP :-137ins non-stream`, Générer une réponse qui avalent l | 404, skill `html-’erreur provider

 message jamaisweb`) avec un`llm en modèle b.py base: |
785| F-aux livrable811avard ou | Indexer un Flash` : `raise.

**Grav fichier (_on_errorité :** faux livexplorateur=False` () | 200défaut) **r +able `.

chunk_---

### 6count: 0ignore.` La =** `Stream introEvent(type=" «uvable au validationerror")`. Pas catalogue |
| É » ac dchec franc |cepte les Envoi facture’exception. coqu par mail |  Générilles (501 APIateur vide = ; succèset le fichier bouton vide.

| App illisible)
** retelant | Liré deFichier :** `ignes | Eff l’UI |
code_executor.py|et utilisateur Échec:183-232 |
 franc ||---| Export---| atelier` ; vide | 400---|
| ` `skills.py: « rien à exporterentity_extractor.py186-217` » |
| Fr`iction | MCP ; ppt | `131- «x `_ 132`,add19 `157-159_title_slide presets » / Install` | Exceptioner` + `_add → liste | 18_end_slide vide. Er ; install` (`reur provider peutpptx_generator.py **sans rester mort:204-212 |
| Fr** exception → parseiction | Er`)

- dreur d PPTX repl’une’envoi maili : slide chaîne vide →  | Front titre + «0 contact mas Merci » =. Pasque le **toujours de chip détail SMTP |
| 2 slides**. OK Fr | En = seuil `pptxvoi mail paniction (neau: ( texte2`.extraction Un) man dump Gquante), de code surmail/ pas un les slides passeIMAP | Oui succès aff.
- XLS, après confirmation |
iché. |
|X| OK : titre | Wizard `action_agents + Gmail A + IMAP.py` | ` | Oui |
|/B/C OK | PDF / = 2 lignes692-700 conversion` | Er, devis / lignes | passe.
- HTMLreur provider aval Oui |
| OK : pasée | At → `content de branche="elier créer →"` → `Step / trame / chuteStatus.COMPLETED`. stream / export | sur Synth Oui |
| OK `return True`èse finale | Tâ (lches créer `. 232).727 / kanban /
- Exception filtres | Oui de lecture ( |
-|740 OK` | : tâcheOOXML cassé CRM contact **COMPLETED** avec) : **fail + phase sections vides.-open**, « + score | Oui **Faux liv on accepte le (pas de dealrable.** |
 fichier ».
- sé| `agents/ Aprèsparé) |
| retryruntime.py` | OK | Board  markdown5 conse `219-221` puis, `illers | Oui |
skills.py` **| OK | Image `232-233` |ne re générvalide pas**. Brer + récup

**Canche **érer | Oui siroit obtenirsans** clé |
| OK outils / obtient | Dictée -> :** un document : erreur « assez aval composeur | Oui |

 riche ».ée, puisLe Obt `done` avec 501 dient une contenu co’envoi de vide. Br facture estanche avecquille qui **toujours a outils (` l passé199’API-217**. le compteur.

**Gr`) prop Ceavité :** faux n’est plus livrable ( un pila gardeège qui d’écran : le devait bouton «age empê Envoyer parcher le  email » a été l’erreur. |

Chat non-stream a `raise_on_error=True1).` ret (`iré. Le pi

---

###1689 ège rest7. Bac`). Board etant, à sable : API documents aussi c’est l autor.’emailisée Deep du trop research aussi panneau ( large.

joindre---

## , constantes utiles,5 fil. Images,, IMAP) et l abs voix, MCP,’indexation qui browserentes
** dit, webFichier :** ` « fait_ »code_ sans chunksexecutor.pysearch

:137.**-164` (`Images** : lepptx route.enum.shapesur rem` entieronte HTTP), `_validate_ 400/500 (`imports` 474-503 (imagesseulement.py:113-136 la rac`). Pas de succès silencine `ieux. `_get_api_pptx`), namespace 624-643key_from_db: (`MSO_ANCHOR55`-56` aval / `PP_e uneALIGN` seulement, pan pasne DB `MSO_SHAPE en` / `MSO_AUTO_SHAPE `logger.debug` puis «_TYPE`)

** clé non configurée » :Croit obtenir éche / obtient :** le promptc franc, cause ppt éventuellementx ann fonce `pptxausse.

**Vo.enum.shapesix** : Gro` (`qpptx non_generator.py-:65`)200 lit et ` `response.text`add_shape(1 (`,voice …)`..py:108- Le modèle importe souvent125`) et le `MSO_AUTO_ **recSHAPE_TYPE.TRIANGLE` :opie** dans le l’import passe, `detail l`’ attribut500. Inverse explose, du **re swallow : corpspli silenc fournisseieux** (findingur à l’écran. É 1), pas unechec franc ( erreur visibleparfois.

M trop bême schémaavard docx : le).

**MCP prompt cite** : `call `WD_STYLE_tool:_TYPE` (`731docx_generator.py-739:64`) sans` rend ` lsuccess=False`’injecter dans le namespace (` au607 modèle. En-623`).

 revanche**Gr `_avité :** causelist_tools: du686-687` faux : éche livrable (c →un log, serveur échec franc ici va laudraitissé `RUNNING` mieux).

---

 avec **0 outil**. L### 8.’UI « `{action: produire}` serveur lancé force », le prompt ** aucuncode outil promis Python**, sans. **Friction tenir** (bouton / compte état du qui modèle
**Fichier :** `chat ment à moitié).

**.py:2251Browser-2260`** : indis (`ponget_system_ible →prompt_addition` uniquement message explic) vs `skills.py:125-ite au140` (lui modèle (`web bas_search.py:cule markdown630-634 si`). Pas silenc `get_modelieux.

**Web_capability != " search (code"`)

**Croit obtenirfaux livrable / obtient :** un)**  
 fichierBrave réd `webigé._search.py: Ollama (177-179`,et Gemini Flash, DDG M `271-273istral small`, SearXNG) sont class `397-399` : HTTPés markdown d (`model_capability’erreur → `.py:13-20SearchResponse(results, 47`).=[])`.  
 Sur`execute_web Produ_search:ire UI555, le route-565ur skills` → `format demande du_results_for Markdown. Sur_llm:184 `{action: produire-187 …}` / `{{action: ppt` /x-pro}} `401`, le chat **-404inject` : **e le« Aucun résultat brief Python**. trouvé pour: Le modèle é … »**.  
metLe modèle ( duet donc code fragile → repl l’utilisateur)i ( crofindings 1it à-4).

 une recherche vide,**Repro :** pas à `{ une cléaction: produire ppt Bravex "kickoff / client 429 / instance"}` avec O mortellama.

. `**Gravité :**chat.py faux: liv289rable sur6-2912 le chemin détermin` pose `success=Trueiste.

` sur---

### 9. « ce texte Anal.

---yser un

## Synth Excel / PDF »èse par : champ fichier gravité

** fantFaux livrôme
able**
**Fichier :**- `action_ `analysisagents.py:_skills.py:692-700`19-27 : étape` (`type COMPLETE='file'`,D vide `required=True si le`) ; `DynamicSkillForm.tsx provider é:112met-171 `` (texterror`. / textarea / select
- `web / number **seulement_search`**, pas ` HTTPfile`)

** dCroit obtenir /’erreur obtient :** coller un `. → «xlsx` et une aucun résultat ». analyse. Le formulaire
- `POST n’affiche /api/chat pas le champ requis/send` ` →stream:false bouton` : affirmation Génér der mort’outil sans exéc. Leution (API skill n’ouvre seulement jamais). le fichier (

**ÉcheMarkdownc franc**
Skill écrit- 400 table justeur : extraction OK la → réponse LLM, inject `base.py:251-265ée`).

Analyse dans le system site → 400 opaque (` `AnalyzeAPI error: WebsiteSkill`)400`. Causes : URL en visibles dans le code texte, **aucun fetch** dans le skill : **(.

**ReApro :** Produ)**ire/ `Comprendre → Fstr(c)`ichier Excel.

** sansGravité :** purge friction (Excel C/PDF)0/NUL, ; analyse **(B)** web fichier hors = de contenu `trim_to inventé si_fit`.
 le modèle n’- Mistral /appelle DeepSeek / Per pas laplexity / Inf recherche (omaniak : mêmefaux 400 ** livsans**rable d body en’analyse, pas log un fichier).

.

**Friction**---

### 
- Extraction join10. « Créte ener une skill » échec : n warning’installe rien
**Fichier + status é :** `GuidedphémèrePrompts.tsx, bul:130-133le utilisateur` (` quiP2 stubs`) aff ; `actionDataiche encore.ts:286 le fichier.
--290` ; MCP running l sans outils’installe siur `tools réel est/list` cas `toolse.
- `_installer.py`entity_extractor` + `POST / /api/tools runtime/ sans outilsinstall`, : silence jamais, pas de appelé par cette mens carteonge d.

**Croit’action. obtenir / obtient :** un outil dans `~/.therese/tools/`. Obtient un prompt de chat. `InstalledToolSkill` n’existe que si un `manifest.json` + `tool.py` sont déjà là (`registry.py:51-63`).

**Gravité :** friction / compétence déclarée sans implémentation UI (pas un faux `.docx`, mais un faux geste « skill »).

---

### Ce qui est un échec franc (donc hors liste « coquille »)
- `registry.execute` en exception → `success=False` (`registry.py:169-175`)
- auto-exec chat si skill introuvable / contenu vide → `skill_file_error` (`chat.py:2581-2646`)
- `generate_document` sans contenu ou format hors docx/pptx/xlsx → message d’erreur (`workspace_tools.py:780-788`)
- outil installé qui n’écrit pas de fichier → `RuntimeError` (`installed_tool.py:174-180`)

---

**Synthèse :** sur le nominal Office, l’utilisateur obtient **un fichier ouvrable** (docx/pptx/xlsx/html) presque toujours. Le contenu n’est garanti **que si le code sandbox a vraiment réussi**. Sinon : script collé, grille A/B/C, page `<pre>`, ou deck titre + Merci. Un échec visible (`skill_file_error`) n’arrive que si le repli lui-même lève, ce qu’il ne fait pas.Voici ce que le code montre sur le chemin nominal (coque `ConversationCanvasPrototype` + `window.__therese` + palette ⌘K). Les 10 vues existent et s’affichent. Board, Actions, Paramètres, Raccourcis, Bibliothèque de prompts et Conversations s’ouvrent vraiment. Les écarts ci-dessous sont ceux où l’annonce et l’effet divergent.

---

## Ce qui tient (pour cadrer)

Les 24 ids de `APP_ACTIONS` (`/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/lib/actionRegistry.ts`) ont un `run`. Dans la coque, `runUnifiedAction` (vers 1349) redirige les vues vers `openEmbeddedView`, et `PrototypeUnifiedViewCanvas` rend bien les 9 vues embarquées (memory, crm, email, calendar, tasks, invoices, files, projects, documents). Le chat passe par `PrototypeChatSurface`. Board (`BoardPanel`), Actions (`ActionPanel` monté dans `App.tsx`), Paramètres, Raccourcis, PromptLibrary et le tiroir Conversations sont branchés.

---

## Findings

### 1. Faux livrable — « Effacer la conversation » n’efface rien en base

**Annonce :** `chat.clear`, label « Effacer la conversation », description « Supprimer tous les messages » (`actionRegistry.ts:49`).

**Effet réel :** `clearCurrentConversation` vide seulement le tableau local (`chatStore.ts:330-337`). Aucun appel API. Les messages restent en SQLite.

**Repro :**
1. Conversation déjà synchronisée, quelques messages.
2. ⌘K → « Effacer la conversation » (ou `window.__therese.runAction('chat.clear')`).
3. L’écran se vide.
4. Changer de conversation puis revenir, ou relancer l’app.

**Pourquoi ça revient :** `useConversationSync` recharge depuis le backend dès que la conversation est `synced` et que `messages.length === 0` (`useConversationSync.ts:174-178`). Le premier effet est masqué par `lastLoadedConversationId` tant qu’on ne quitte pas la conversation.

---

### 2. Échec franc — raccourci « Accueil » (H) annoncé, pas géré (sur Mac, Cmd+H masque l’app)

**Annonce :** `home.open` porte `shortcut: 'H'` (`actionRegistry.ts:64`). La palette de la coque affiche ce suffixe tel quel (`ConversationCanvasPrototype.tsx:618`).

**Effet réel :** `useKeyboardShortcuts.ts` n’a aucune branche `key === 'h'`. Le clic palette / le bouton Accueil du rail marchent via `runUnifiedAction` (`ConversationCanvasPrototype.tsx:1371-1380`). Le raccourci, non.

**Repro :** être dans une vue, taper Cmd+H (Mac) ou Ctrl+H. Rien ne ramène à l’accueil. Sur macOS, Cmd+H est le masquage système.

La fiche Raccourcis (`ShortcutsModal.tsx`) ne ment pas : elle ne liste pas H. C’est le registre et la palette ⌘K qui le font.

---

### 3. Friction — « Rechercher dans les Contacts » ouvre la liste, ne cherche pas

**Annonce :** `memory.search`, label « Rechercher dans les Contacts », raccourci `⇧F` (`actionRegistry.ts:56`). La fiche raccourcis dit la même chose (`ShortcutsModal.tsx:56`). Cmd+Shift+F est bien branché (`useKeyboardShortcuts.ts:102-106` → `onSearch` → `openEmbeddedView('memory')` ligne 1145).

**Effet réel :** identique à `memory.open` : `setView('memory')`. Pas de focus sur `#memory-search-input`, pas de query, pas d’appel `/api/memory/search`. Le champ existe (`MemoryPanel.tsx:289-296`) mais sans `autoFocus`.

**Repro :** Cmd+Shift+F, ou ⌘K → « Rechercher dans les Contacts ». La vue Contacts s’ouvre, le curseur n’est pas dans « Rechercher… ».

---

### 4. Faux livrable — « Produire un document » n’ouvre pas la production Office

**Annonce :** `guided.open`, label « Produire un document », description « Générer DOCX, PPTX ou XLSX (Skills Office) » (`actionRegistry.ts:51`).

**Effet réel :** `setView('chat')` + événement `therese:insert-prompt` avec le texte « Aide-moi à produire un document (DOCX, PPTX ou XLSX) : » (`actionRegistry.ts:35-38, 51`). Aucun `skill_id`. `GuidedPrompts` n’est monté nulle part (seulement défini sous `components/guided/`).

Le vrai chemin de génération, lui, existe : conversation vide → `HomeCommands` / `{action: produire docx "…"}` (slash, puces). La commande du registre court-circuite ces portes.

**Repro :** ⌘K → « Produire un document ». Un chat s’ouvre avec une phrase à compléter. Envoyer sans forcer un skill : pas de carte fichier (même famille que le constat campagne `skill_id`, mais ici c’est la commande nommée du registre qui promet la génération).

---

### 5. Échec franc — commandes `/` listées comme `/contact`, sans exécuteur

Menu `/` (`SlashCommandsMenu.tsx:159-191`) et builtins (`command_registry.py:168-231`) :

| Commande | Annonce | Exécuteur |
|---|---|---|
| `/contact`, `/projet`, `/rdv` | créer | `DETERMINISTIC_COMMANDS` (`slash_commands.py:36`) |
| `/fichier` | analyser un fichier | `FILE_COMMAND_PATTERN` (`chat.py:189-192`) |
| `/aide` | capacités | `parse_action_message` (`chat_actions.py:250-251`) |
| **`/recherche`** | « Rechercher dans la mémoire » | **aucun** |
| **`/résumé`** | « Résumer la conversation » | **aucun** |
| **`/tâches`** | « Extraire les tâches » | **aucun** |
| **`/email`** | « Rédiger un email » | **aucun** |

`parse_slash_command` refuse tout nom hors `{contact, projet, rdv}` (`slash_commands.py:125-126`). Ces quatre commandes se contentent d’insérer le préfixe ; l’envoi part au LLM. Le guide alpha les présente pourtant comme des commandes slash au même titre que `/contact` (`docs/USER_GUIDE_ALPHA.md:101-109`).

**Repro :** `/` → « recherche » → Entrée → `Dupont` → envoyer. Pas d’appel déterministe à la mémoire. Comparer avec `/contact Jean Test` qui crée vraiment une fiche.

---

### 6. Friction — `data.export` : deux implémentations selon la porte

**Annonce :** « Exporter les données » / « Sauvegarder ta mémoire (via Réglages) » (`actionRegistry.ts:78`).

- Palette ⌘K de la coque → `runUnifiedAction` → `openSettings('privacy')` (`ConversationCanvasPrototype.tsx:1393`). L’onglet Confidentialité a bien Export / sauvegardes (`PrivacyTab.tsx:295+`).
- `APP_ACTIONS.run` et donc `window.__therese.runAction('data.export')` → `openSettings()` sans onglet (`actionRegistry.ts:78`) → onglet Profil par défaut.

**Repro testeur :** `window.__therese.runAction('data.export')`. Les Réglages s’ouvrent sur Profil, pas sur l’export. Même id, deux atterrissages.

---

## Vérifié, pas un finding

- Les 10 vues du store sont rendues (chat via coque, les 9 autres via `PrototypeUnifiedViewCanvas.tsx:63-71`).
- Board, Actions, Paramètres, Raccourcis, PromptLibrary, Conversations : ouverture + contenu.
- `documents.new` pose `createModalRequested`, consommé par `DocumentsList`.
- Cartes du tiroir : destinations `view` / `action` / panneaux (calculateurs, livrables, images, relances, voix) câblées dans `ouvrirDestination` ; plus de `kind: 'pending'` vivant.
- Navigation slash `ouvrir email|pipeline|contacts|agenda|tâches|documents|devis et factures` : `actionId` + `runNavigationAction`.
- `{action: ouvrir fichiers|projets}` existe côté backend (`chat_actions.py:64-72`) même si le menu `/` ne les propose pas (absence de listing, pas une commande morte).

Je n’ai pas re-fiché `createCalendar` jamais appelé ni `skill_id` hors prompts suggérés, hors le cas distinct `guided.open` (commande du registre qui promet la génération).J’ai recoupé les schémas Create/Update et les formulaires du chemin nominal. L’amorce prestations du 30/08 est déjà corrigée dans le code actuel : je ne la refiche pas.

## Findings vérifiés

### 1. Analyser Excel / PDF : champ fichier obligatoire jamais rendu
**Gravité : faux livrable**

Le backend impose `file_path` (`type: file`, `required: True`) pour `analyze-xlsx` et `analyze-pdf` :

```19:34:/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/skills/analysis_skills.py
    def get_input_schema(self) -> dict[str, InputField]:
        return {
            'file_path': InputField(
                type='file',
                label='Fichier Excel',
                placeholder='Sélectionne un fichier .xlsx',
                required=True,
                help_text='Fichier à analyser'
            ),
```

Ces skills sont des commandes d’accueil (`show_on_home=True`, action `form_then_prompt`) :

```321:333:/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/services/command_registry.py
            cmd = CommandDefinition(
                id=skill_id,
                name=name,
                ...
                action=action,
                skill_id=skill_id,
                show_on_home=True,
```

`CommandExecutor` charge ce schéma et le passe à `DynamicSkillForm`. Le formulaire n’a des branches que pour `text` / `textarea` / `select` / `number` : aucun `<input type="file">`.

```112:171:/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/guided/DynamicSkillForm.tsx
              {field.type === 'text' && (
                <input ... />
              )}
              {field.type === 'textarea' && (
                <textarea ... />
              )}
              {field.type === 'select' && (
                <select ... />
              )}
              {field.type === 'number' && (
                <input type="number" ... />
              )}
```

La validation exige pourtant tous les `required` :

```59:66:/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/guided/DynamicSkillForm.tsx
    return Object.entries(schema).every(([key, field]) => {
      if (!field.required) return true;
      const value = inputs[key];
      return value !== undefined && value !== '' && value !== null;
    });
```

Chemin nominal : Accueil → Comprendre → « Fichier Excel » / « Document PDF ». On voit le libellé « Fichier Excel * » sans champ. « Générer » reste désactivé.

---

### 2. Devis / facture : l’écran refuse une quantité que l’API accepte
**Gravité : friction** (demi-journée de formation impossible à saisir)

Le schéma 0.55 accepte le fractionnaire (`gt=0`) et le commente comme autorisé à l’écran :

```937:956:/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/models/schemas.py
    quantity: float = Field(default=1.0, gt=0)
    ...
    # Et la quantité accepte le fractionnaire
    # (une demi-journée de formation), seulement pas le zéro ni le négatif.
```

Les deux formulaires de création refusent `quantity < 1` :

```235:237:/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/invoices/InvoiceForm.tsx
    if (normalizedLines.some((line) => line.quantity! < 1 || line.unit_price_ht! < 0)) {
      alert('Saisis une quantité supérieure ou égale à 1 et un prix positif ou nul');
```

```43:43:/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/prototype/InvoiceConversationCard.tsx
  if (request.lines.some((line) => line.quantity < 1 || line.unit_price_ht < 0)) return 'Un montant figé est invalide.';
```

Saisir `0,5` ne part jamais. L’API l’accepterait.

---

### 3. Agenda : participants envoyés sans le format e-mail exigé
**Gravité : échec franc** (dès qu’on met un nom plutôt qu’un e-mail)

Le validateur backend refuse tout participant qui n’est pas un e-mail :

```793:796:/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/backend/app/models/schemas.py
        for attendee in self.attendees or []:
            address = attendee.strip()
            if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", address):
                raise ValueError(f"Adresse participant invalide : {attendee}")
```

`EventForm` découpe sur la virgule et envoie tel quel, sans contrôle :

```143:146:/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE/src/frontend/src/components/calendar/EventForm.tsx
    const attendees = attendeesInput
      .split(',')
      .map((e) => e.trim())
      .filter((e) => e);
```

Le placeholder dit des e-mails, le champ accepte « Marie, Jean ». Enregistrement → 422.

Même payload côté `NewEventForm` (`MeetingConversationCard.tsx`, `attendees: parsedAttendees` après split `[;,\n]`).

---

## Cousines visuelles (saisie lisible, pas un 422)

- **CreateCommandForm** champ « Prompt / Contenu * » (`CreateCommandForm.tsx` ~214-231) : l’amorce « tronqué à gauche » ; le CSS local est un `textarea` `px-3` sans icône superposée. Je n’ai pas trouvé dans ce fichier le padding/overflow qui coupe à gauche.
- **FileBrowser** filtre `w-32 pl-7` + icône `absolute left-2` (`FileBrowser.tsx` 344-352) : ~128 px utiles, le début de saisie est collé à l’icône.
- **ContactsMemoryCard** recherche `pl-8` + icône `left-2.5` (`ContactsMemoryCard.tsx` 188-194).

---

## Contrôlé, pas un finding à ficher

- **Prestations « Ajouter » / `phase` obligatoire** : corrigé. `ListeDesPrestations.tsx` 55-61 envoie `phase`. Ne pas reficher.
- **Documents, tâches, variables, suivis, project.sync, contacts/projets mémoire, facture `contact_id` + `lines`** : noms snake_case alignés, routes présentes, champs requis envoyés.
- **`createDeliverable` / `supprimerUnePrestation` / `createCalendar`** : clients API orphelins, aucun bouton du chemin nominal ne les promet.
- **`POST /api/calendar/calendars`** : le client envoie un JSON `{ account_id, summary, ... }` alors que FastAPI lit des query params. Mort côté UI (aucun appelant composant).

Si tu veux un correctif, le plus net est le 1 (champ fichier des analyses) : sans lui, deux commandes d’accueil sont des portes fermées.Les cinq lectures sont rentrées. Je vérifie encore les chemins les plus graves avant de trancher GO ou NO-GO.**NO-GO.**

Les vues tiennent. Facture PDF, atelier, tâches, Board, image (avec clé), dictée, envoi d’un mail texte : le geste nominal aboutit. Ce qui casse, c’est le même motif que tes trois essais : l’application **rend un objet qui a l’air d’un succès**, et le contenu n’est pas celui promis. Un échec franc (bouton mort, 422, 404) vaut mieux. Ici le repli Office, le « Répondre », l’indexation et la recherche web font l’inverse.

Je n’ai pas refiché le PPTX `TRIANGLE`, le `ResponseNotRead`, ni le champ Prompt tronqué.

---

## Faux livrable (pire qu’un échec)

### 1. Le repli Office est commun aux trois formats, pas seulement au PPTX

**Fichiers :** `src/backend/app/services/skills/code_executor.py:770-908`, `docx_generator.py:249-311`, `xlsx_generator.py:187-251`

**Croit obtenir :** un Word / Excel métier après « Produire » ou `{action: produire …}`.

**Obtient :** un fichier téléchargeable, `success: true`, carte de téléchargement. Dedans : le script Python en paragraphes (Word) ou une feuille « Données » avec les colonnes A, B, C et zéro ligne (Excel).

**Chemin :** `extract_python_code` → sandbox → `except CodeExecutionError` → on **ne remonte pas** l’erreur → `_fallback_execute`. Si le contenu nettoyé est vide ou trop court (`len <= 50`), le script original est renvoyé au parser. Word ignore seulement la ligne ```` ``` ```` d’une fence orpheline et **garde les lignes de code**. Excel, sans tableau Markdown `|`, invente `headers: ["A","B","C"]` et `rows: []`.

`registry.execute` (`registry.py:151-167`) pose alors `success=True`. L’UI n’émet pas `skill_file_error`.

**Repro :** `{action: produire docx "compte-rendu client"}` ou `{action: produire xlsx "suivi de chantier"}` avec un modèle qui émet du python-docx / openpyxl (c’est le brief injecté, finding 3). Ouvrir le fichier.

Un échec sandbox visible vaudrait mieux qu’un `.docx` plein de `from docx import Document`.

---

### 2. La garde « document assez riche » compte les coquilles comme du contenu

**Fichier :** `src/backend/app/services/skills/code_executor.py:176-232`

**Croit obtenir :** un fichier rejeté s’il est vide.

**Obtient :** le repli passe. Excel : titre + en-têtes A/B/C = 2 lignes avec une valeur, seuil `xlsx: 2`. PPTX repli : slide titre + « Merci » = toujours 2 slides. Exception de lecture OOXML : `return True` (fail-open). Le repli **n’est jamais revalidé** après `_fallback_execute`.

Le commentaire dit « hors header ». Le code compte le header.

---

### 3. `{action: produire}` force du Python, même aux modèles classés Markdown

**Fichiers :** `src/backend/app/routers/chat.py:2251-2260` vs `src/backend/app/routers/skills.py:125-140` + `model_capability.py:13-20`

**Croit obtenir :** un fichier rédigé. Ollama et Gemini Flash sont classés `markdown` : le bouton Produire de l’accueil demande du Markdown.

**Obtient :** `{action: produire pptx "kickoff"}` (menu `/`) injecte `get_system_prompt_addition()` (brief python-pptx), `disable_tools=True`, puis auto-exec. Le modèle local émet du code fragile → finding 1.

**Repro :** conversation, `/` → « produire pptx », envoyer. Comparer avec Accueil → Produire → Présentation PPT (chemin skills, Markdown si le modèle n’est pas code-capable).

---

### 4. « Page web » : le prompt atterrit dans un `<pre>`

**Fichier :** `src/backend/app/services/skills/html_generator.py:117-210`

**Croit obtenir :** une landing autonome.

**Obtient :** si le HTML n’a ni `<!DOCTYPE` ni `<html>` (bloc incomplet, Markdown, bavardage), `_wrap_in_html` échappe tout et le met dans `<pre>` sur fond sombre. `execute` ne lève jamais. Le MIME est `text/html` : le téléchargement a l’air légitime.

Cousine exacte du PPTX qui colle le code sur une slide.

---

### 5. « Effacer la conversation » n’efface rien

**Fichiers :** `src/frontend/src/lib/actionRegistry.ts:49`, `src/frontend/src/stores/chatStore.ts:330-337`, `src/frontend/src/hooks/useConversationSync.ts:174-178`

**Croit obtenir :** les messages disparaissent pour de bon.

**Obtient :** le tableau local est vidé. SQLite intact. Changer de conversation puis revenir : `useConversationSync` recharge dès que `synced && messages.length === 0`.

**Repro :** ⌘K → « Effacer la conversation ». L’écran se vide. Ouvrir une autre conversation, revenir.

---

### 6. « Répondre » n’est pas une réponse

**Fichiers :** `src/frontend/src/components/email/EmailDetail.tsx:188-205`, `src/backend/app/models/schemas_email.py:97-105`, `src/backend/app/routers/email.py:1166-1174`

**Croit obtenir :** une réponse dans le fil, éventuellement avec les pièces.

**Obtient :** un **nouveau** brouillon `Re:` / `Fwd:` avec une citation texte. Pas de `In-Reply-To`, pas de thread Gmail, pas des pièces d’origine. Le provider IMAP sait attacher et poser `in_reply_to` (`imap_smtp_provider.py:409-420`) ; le routeur ne les remplit jamais. Côté Gmail, `send_message` n’a même pas le paramètre pièces (`gmail_service.py:223-231`).

Le destinataire reçoit un mail neuf, pas une réponse.

**Repro :** Email → ouvrir un message d’un fil → Répondre → envoyer. Vérifier dans Gmail / IMAP que ce n’est pas dans le thread.

---

### 7. IMAP : « Envoyé » est un mensonge JSON

**Fichiers :** `src/backend/app/routers/email.py:1166-1175`, `src/backend/app/services/email/imap_smtp_provider.py:422-453`

**Croit obtenir :** le message dans Envoyés.

**Obtient :** SMTP part vraiment. Aucun `APPEND` IMAP vers `\Sent`. L’API rend `{"labelIds": ["SENT"]}` et un id fabriqué `sent_YYYYMMDDHHMMSS`. L’onglet Envoyés reste vide.

Gmail, lui, range vraiment.

**Repro :** compte IMAP, envoyer un mail texte, ouvrir Envoyés.

---

### 8. Indexer un fichier : 200, `chunk_count: 0`, introuvable ensuite

**Fichiers :** `src/backend/app/services/indexation.py:434-439`, `src/frontend/src/components/files/FileBrowser.tsx:271-277`

**Croit obtenir :** le fichier est cherchable.

**Obtient :** extraction vide → consigné avec `chunk_count = 0`, HTTP 200. L’explorateur coupe le spinner et n’inspecte pas le compteur. `search_files` exige `chunk_count > 0`.

Le journal projet.sync a été rendu honnête. L’explorateur de la vue Fichiers, non.

**Repro :** Fichiers → indexer un PDF image / un xlsx protégé / un fichier sans texte. Spinner off. Demander le fichier dans le chat.

---

### 9. Recherche web en panne = « aucun résultat »

**Fichier :** `src/backend/app/services/web_search.py:177-179, 184-187, 555-565`

**Croit obtenir :** soit des liens, soit « Brave / DuckDuckGo a échoué ».

**Obtient :** HTTP 401/429/5xx → `SearchResponse(results=[])` → le modèle lit « Aucun résultat trouvé pour: … ». `success: true` côté outil.

Cousine du 400 avalé : le corps d’erreur n’arrive jamais à l’utilisateur, et ici on **traduit la panne en absence de résultats**.

---

### 10. Agent Actions : étape « terminée » à vide

**Fichier :** `src/backend/app/services/action_agents.py:692-700`

**Croit obtenir :** un rapport / une relance.

**Obtient :** `stream_response` (défaut `raise_on_error=False`) avale `StreamEvent(type="error")`. `content=""` puis `StepStatus.COMPLETED`. La synthèse assemble des sections vides et marque la tâche faite.

**Repro :** Actions → lancer un agent pendant une panne de clé / un 5xx fournisseur.

---

## Échec franc (mieux, mais le geste nominal est mort)

### 11. Accueil → Comprendre → « Fichier Excel » / « Document PDF » : formulaire incomplétable

**Fichiers :** `src/backend/app/services/skills/analysis_skills.py:19-27` (et le PDF jumelé), `src/frontend/src/components/guided/DynamicSkillForm.tsx:59-66 et 112-171`, `src/frontend/src/components/home/CommandExecutor.tsx:76-99`

**Croit obtenir :** coller un `.xlsx` et une analyse.

**Obtient :** le schéma exige `file_path` `type: file` `required: true`. Le formulaire n’a des branches que pour text / textarea / select / number. Le libellé « Fichier Excel * » s’affiche **sans champ**. « Générer » reste désactivé. Même chose pour le PDF.

Cousine du « Ajouter » prestations sans `phase` : un champ devenu (ici : toujours) obligatoire, l’écran ne l’envoie pas, et ici il ne le laisse même pas saisir.

**Repro :** conversation vide → Comprendre → Fichier Excel.

---

### 12. IMAP : « Générer une réponse » → 404

**Fichiers :** `src/backend/app/routers/email.py:1077-1107` (lecture IMAP, **pas** d’écriture SQLite) et `:1518-1521` (le générateur lit `EmailMessage` en base)

**Croit obtenir :** un brouillon de réponse.

**Obtient :** `Message not found`. Le bouton est bien là (`EmailDetail.tsx:402`).

**Repro :** compte IMAP, ouvrir un mail, « Générer une réponse ».

---

### 13. Menu `/` : quatre commandes listées sans exécuteur

**Fichiers :** `src/frontend/src/components/chat/SlashCommandsMenu.tsx:159-191`, `src/backend/app/services/slash_commands.py:36 et 125-126`

**Croit obtenir :** `/recherche`, `/résumé`, `/tâches`, `/email` comme `/contact` (création réelle).

**Obtient :** le préfixe est inséré. `parse_slash_command` ne connaît que `{contact, projet, rdv}`. Le reste part au LLM, qui peut affirmer une recherche ou un résumé sans les faire.

**Repro :** `/` → recherche → envoyer `Dupont`. Comparer avec `/contact Jean Test`.

---

### 14. Participants d’agenda : un nom fait 422

**Fichiers :** `src/frontend/src/components/calendar/EventForm.tsx:143-146`, `src/backend/app/models/schemas.py:793-796`

**Croit obtenir :** inviter « Marie, Jean ».

**Obtient :** le champ accepte n’importe quoi, l’API exige un e-mail. 422.

**Repro :** Agenda → nouvel événement → Participants `Marie` → enregistrer.

---

### 15. Quatre fournisseurs streamés n’ont toujours pas le corps d’erreur

**Fichiers :** `mistral.py` (~105-114, 218-220), `deepseek.py` (~67-76, 176-178), `perplexity.py` (~167-169), `infomaniak.py` (~163-165)

**Croit obtenir :** après le correctif du jour, savoir *pourquoi* le 400.

**Obtient :** `API error: 400` à l’écran, statut seul dans le journal. OpenAI / Anthropic / Gemini / Ollama / OpenRouter lisent le body. Ces quatre, non.

Sur le tableur : le backend extrait bien (`file_parser.py:259-296`, `str(c)` brut, 15 000 caractères collés dans le **prompt système**, `llm.py:772-773`). `trim_to_fit` ne rogne jamais le système. Je n’affirme pas que c’est *la* cause du 400 d’aujourd’hui. Le chemin qui peut le produire est celui-là, et le motif reste opaque sur Mistral / DeepSeek / Perplexity / Infomaniak.

---

## Friction

### 16. Bouton « Joindre » du composeur mail, toujours `disabled`

`src/frontend/src/components/email/EmailCompose.tsx:323-326`. Aucun champ pièces dans `SendEmailRequest`. Le bouton est visible, jamais cliquable, sans motif.

### 17. « Produire un document » (⌘K) n’ouvre pas Produire

`actionRegistry.ts:51` : insère « Aide-moi à produire un document… » dans le chat, **sans** `skill_id`. `GuidedPrompts` n’est monté nulle part. Le vrai chemin est Accueil vide → HomeCommands, ou `{action: produire docx "…"}`.

### 18. Quantité facture : l’API autorise 0,5 jour, l’écran refuse

`schemas.py:937-956` (`gt=0`, commentaire demi-journée de formation) vs `InvoiceForm.tsx:235-237` (`quantity < 1` → alerte).

### 19. « Rechercher dans les Contacts » (⇧F) ouvre la liste, ne cherche pas

`actionRegistry.ts:56` : même `run` que `memory.open`. Pas de focus sur le champ.

---

## Ce qui tient, pour ne pas tout peindre en rouge

Chat streamé avec outils, devis/facture PDF, conversion devis → facture, atelier (créer, trame, stream, export vide = 400 honnête), tâches kanban, Board 5 conseillers, image si clé, dictée → composeur, envoi d’un mail **texte** Gmail.

Le 501 d’envoi de facture existe encore côté API. L’écran n’a plus le bouton : ce n’est plus un piège utilisateur.

---

Le motif des trois essais à la main se répète : **un fichier, un index, une réponse, une recherche, une action « terminée »**. L’objet existe. Le contenu n’est pas le métier demandé. Tant que le repli Office rend `success` et que « Répondre » n’est pas un fil, un utilisateur qui s’en sert comme d’une appli de production referme.
