# Scenarios Catastrophe - THERESE App + Server

> **Sélecteurs, à lire avant d'exécuter le moindre script de ce document.**
>
> Correction du 01/09/2026. Ces protocoles combinaient deux appels à
> `document.querySelectorAll` avec un OU logique. Une NodeList vide est un
> objet, donc une valeur vraie : **le repli n'était jamais emprunté**, et le
> premier sélecteur l'emportait même quand il ne trouvait rien. Combiné à des
> identifiants absents du code, cela rendait les verdicts vides : « pas de
> doublon » et « zéro donnée restante » étaient vrais quoi qu'il arrive.
>
> Utiliser l'aide ci-dessous, qui parcourt réellement les sélecteurs et
> **échoue quand aucun ne trouve rien** :
>
> ```js
> function qsa(...selecteurs) {
>   for (const s of selecteurs) {
>     const trouves = [...document.querySelectorAll(s)];
>     if (trouves.length) return trouves;
>   }
>   throw new Error(
>     "Aucun élément pour : " + selecteurs.join(" | ") +
>     " — le sélecteur est faux ou l'écran n'est pas celui attendu. " +
>     "Ce pas ne prouve rien, corriger avant de conclure."
>   );
> }
> ```
>
> Un comptage qui rend zéro parce que le sélecteur est faux n'est pas un
> résultat, c'est une mesure ratée.


> 10 scenarios que personne ne teste jamais.
> A executer via Chrome MCP apres les parcours personas.
> Concu le 28 mars 2026.

---

## Index

| # | Scenario | Produit | Gravite |
|---|----------|---------|---------|
| 1 | Perte donnees onboarding (reinstall) | App | CRITIQUE |
| 2 | JWT expire mid-session | Server | HAUTE |
| 3 | Cle Fernet perdue | App | CRITIQUE |
| 4 | Double-clic creation facture | App | HAUTE |
| 5 | IDOR cross-org | Server | CRITIQUE |
| 6 | Board sans provider configure | App | MOYENNE |
| 7 | Import VCard volumineux (10 000 contacts) | App | HAUTE |
| 8 | 2 admins modifient le meme user | Server | HAUTE |
| 9 | Backend tombe pendant utilisation | App | HAUTE |
| 10 | RGPD suppression totale | Les deux | CRITIQUE |

---

## Scenario 1 : Perte donnees onboarding (reinstall app)

- **Produit** : App (Desktop Tauri)
- **Gravite** : CRITIQUE
- **Contexte** : Bug historique v0.6.2 - une reinstallation de l'app purgeait localStorage, re-declenchait l'onboarding, et la DB etait ecrasee par les valeurs par defaut. Fixe en v0.6.3 mais a verifier a chaque release.

### Description

L'utilisateur a configure THERESE (onboarding termine, cles API, contacts, conversations). Il reinstalle l'app (mise a jour ou reparation). La nouvelle installation detecte-t-elle la DB existante dans `~/.therese/` sans l'ecraser ?

### Etapes de reproduction

```
1. Lancer THERESE App normalement
2. Completer l'onboarding (nom, provider, cle API)
3. Envoyer au moins 1 message dans le chat
4. Creer 1 contact dans le CRM
5. Fermer l'app completement

6. javascript_tool :
   // Simuler la reinstall en vidant localStorage (comme fait Tauri au reinstall)
   localStorage.clear();
   sessionStorage.clear();
   return 'storage cleared';

7. navigate → http://localhost:1420 (reload complet)
8. wait 5s (chargement app)
9. take_screenshot → "CATA-01-after-reinstall.png"

10. javascript_tool :
    // Verifier : est-on redirige vers l'onboarding ?
    const onboarding = document.querySelector('[data-testid="onboarding-step"]');
    return { onboardingVisible: !!onboarding };

11. Si onboarding visible :
    // Verifier que c'est un "safe default" (pas un ecrasement)
    // Completer l'onboarding avec les memes infos
    // Puis verifier que les donnees existantes sont preservees

12. Naviguer vers le CRM
13. javascript_tool :
    const contacts = qsa('[data-testid="crm-contact-item"]', '.contact-card');
    return { contactCount: contacts.length };

14. take_screenshot → "CATA-01-data-preserved.png"
```

### Resultat attendu

- L'app detecte la DB existante dans `~/.therese/`
- L'onboarding ne s'affiche PAS (ou en mode "bienvenue de retour")
- Toutes les donnees sont preservees : contacts, conversations, cles API, parametres
- Aucune table n'est ecrasee ou reinitialises

### Resultat redoute

- L'onboarding se re-declenche avec les valeurs par defaut
- La DB est ecrasee : contacts, conversations, cles API perdus
- Les cles Fernet sont regenerees et les anciennes cles API deviennent illisibles
- L'utilisateur pense que l'app est cassee et desinstalle definitivement

---

## Scenario 2 : JWT expire mid-session

- **Produit** : Server (Web multi-tenant)
- **Gravite** : HAUTE
- **Contexte** : L'utilisateur redige un long message ou attend le retour d'une deliberation Board (60s+). Son JWT expire pendant ce temps.

### Description

Un agent connecte au Server redige un message complexe pendant 20 minutes. Son JWT a expire. Il clique sur "Envoyer". Que se passe-t-il ?

### Etapes de reproduction

```
1. Se connecter normalement (login → charte → chat)
2. wait_for [data-testid="chat-page"] visible

3. javascript_tool :
   // Simuler l'expiration du JWT en modifiant le token dans le storage
   const token = localStorage.getItem('token') || sessionStorage.getItem('token');
   if (token) {
     // Corrompre le token pour simuler l'expiration
     const parts = token.split('.');
     if (parts.length === 3) {
       // Modifier le payload pour mettre une date d'expiration passee
       const payload = JSON.parse(atob(parts[1]));
       payload.exp = Math.floor(Date.now() / 1000) - 3600; // expire il y a 1h
       parts[1] = btoa(JSON.stringify(payload));
       const expiredToken = parts.join('.');
       localStorage.setItem('token', expiredToken);
       sessionStorage.setItem('token', expiredToken);
       return 'token expired artificially';
     }
   }
   return 'token not found';

4. javascript_tool :
   // Saisir un message (apres expiration)
   const input = document.querySelector('[data-testid="chat-message-input"]');
   const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
   setter.call(input, 'Ce message est envoye avec un JWT expire');
   input.dispatchEvent(new Event('input', { bubbles: true }));

5. click [data-testid="chat-send-btn"]
6. wait 5s
7. take_screenshot → "CATA-02-jwt-expired.png"

8. javascript_tool :
   // Verifier la reaction de l'app
   const errorMsg = document.querySelector('[data-testid="error-message"]') ||
                    document.querySelector('.toast-error') ||
                    document.querySelector('[role="alert"]');
   const loginRedirect = window.location.pathname.includes('/login');
   return {
     errorVisible: !!errorMsg,
     errorText: errorMsg?.textContent,
     redirectedToLogin: loginRedirect,
     currentPath: window.location.pathname
   };
```

### Resultat attendu

- L'API repond 401 Unauthorized
- Le frontend affiche un message clair : "Session expiree, veuillez vous reconnecter"
- L'utilisateur est redirige vers /login SANS perdre le texte saisi (copie dans le clipboard ou sauvegarde locale)
- Apres reconnexion, l'utilisateur retrouve son contexte

### Resultat redoute

- Le message est perdu silencieusement (pas d'erreur visible)
- L'app affiche une erreur technique ("401" ou "Unauthorized") sans explication
- Boucle de redirections infinie /login → /chat → /login
- Le texte en cours de redaction est perdu sans possibilite de recuperation
- L'app freeze completement (streaming SSE bloque sur un 401)

---

## Scenario 3 : Cle Fernet perdue

- **Produit** : App (Desktop Tauri)
- **Gravite** : CRITIQUE
- **Contexte** : BUG-050 historique. La cle Fernet est stockee dans le macOS Keychain. Un changement de Mac, une reinstallation de macOS, ou un changement de signature binaire peut rendre la cle inaccessible.

### Description

L'utilisateur change de Mac ou reinstalle macOS. La cle Fernet dans le Keychain n'existe plus. Les cles API chiffrees dans la DB sont illisibles.

### Etapes de reproduction

```
1. Lancer THERESE App normalement
2. Aller dans Settings → Configurer au moins 1 cle API (ex: Anthropic)
3. Verifier que le chat fonctionne (message + reponse)
4. Fermer l'app

5. # Terminal (pas Chrome MCP) :
   # Supprimer la cle Fernet du Keychain
   # ATTENTION : ne faire qu'en environnement de test
   python3 -c "
   import keyring
   try:
     keyring.delete_password('therese', 'fernet_key')
     print('Fernet key deleted from keychain')
   except:
     print('Key not found or already deleted')
   "

6. Relancer l'app : navigate → http://localhost:1420
7. wait 5s
8. take_screenshot → "CATA-03-fernet-lost.png"

9. javascript_tool :
   // Verifier l'etat de l'app
   const errorElements = document.querySelectorAll('[class*="error"], [role="alert"]');
   return {
     errors: Array.from(errorElements).map(e => e.textContent),
     pageLoaded: !!document.querySelector('[data-testid="chat-page"]') ||
                 !!document.querySelector('[data-testid="onboarding-step"]')
   };

10. Si l'app demarre : tenter d'envoyer un message (qui necessite une cle API)
11. take_screenshot → "CATA-03-api-call-attempt.png"
```

### Resultat attendu

- L'app detecte l'absence de la cle Fernet au demarrage
- Un message clair s'affiche : "Cle de chiffrement introuvable. Vos cles API doivent etre reconfigurees."
- L'utilisateur est guide vers Settings pour re-saisir ses cles API
- Les donnees non chiffrees (contacts, conversations, taches) sont preservees
- Un fichier de backup de la cle existe (cf. BUG-050 : backup fichier cle Fernet)

### Resultat redoute

- L'app crash au demarrage avec une stacktrace Python
- Les cles API chiffrees provoquent des erreurs `InvalidToken` en cascade
- Toutes les fonctionnalites LLM sont cassees sans message explicite
- L'utilisateur doit supprimer manuellement `~/.therese/therese.db` pour redemarrer (perte totale)
- Le backup de cle Fernet n'est pas utilise automatiquement

---

## Scenario 4 : Double-clic creation facture

- **Produit** : App (Desktop Tauri)
- **Gravite** : HAUTE
- **Contexte** : Race condition classique - l'utilisateur clique 2 fois rapidement sur "Creer la facture" avant que la premiere requete ne termine.

### Description

Un utilisateur cree une facture. Il double-clique sur le bouton de creation. Deux factures identiques sont-elles creees ?

### Etapes de reproduction

```
1. Naviguer vers la facturation (panel invoices)
2. navigate → http://localhost:1420/?panel=invoices
3. wait 3s

4. Ouvrir le formulaire de creation de facture
5. Remplir les champs (client, montant, description)

6. javascript_tool :
   // Compter les factures AVANT
   const invoicesBefore = qsa('[data-testid="invoice-item"]', '.invoice-row');
   const countBefore = invoicesBefore.length;

   // Double-cliquer tres rapidement sur le bouton de creation
   const createBtn = document.querySelector('[data-testid="invoice-create-btn"]') ||
                     document.querySelector('button[type="submit"]');
   if (createBtn) {
     createBtn.click();
     setTimeout(() => createBtn.click(), 50); // 2eme clic 50ms apres
     return { countBefore, doubleClicked: true };
   }
   return { error: 'button not found' };

7. wait 5s (attendre que les 2 requetes API terminent)
8. take_screenshot → "CATA-04-double-click.png"

9. javascript_tool :
   // Compter les factures APRES
   const invoicesAfter = qsa('[data-testid="invoice-item"]', '.invoice-row');
   return { countAfter: invoicesAfter.length };

10. // Verifier s'il y a des doublons
11. javascript_tool :
    const invoices = qsa('[data-testid="invoice-item"]', '.invoice-row');
    const texts = Array.from(invoices).map(i => i.textContent);
    const duplicates = texts.filter((t, i) => texts.indexOf(t) !== i);
    return { duplicateCount: duplicates.length, hasDuplicates: duplicates.length > 0 };
```

### Resultat attendu

- Une seule facture est creee (debounce ou desactivation du bouton apres le 1er clic)
- Le bouton passe en etat disabled ou loading apres le premier clic
- Le 2eme clic est ignore silencieusement
- Pas de doublon dans la base de donnees

### Resultat redoute

- 2 factures identiques sont creees avec 2 numeros differents
- Probleme comptable : 2 lignes au lieu d'1 dans l'export
- Le client recoit 2 factures par email (si envoi automatique)
- L'API repond 500 sur la 2eme requete (contrainte d'unicite) mais la 1ere passe
- Etat UI inconsistant : 1 facture affichee mais 2 en base

---

## Scenario 5 : IDOR cross-org (acces donnees d'une autre organisation)

- **Produit** : Server (Web multi-tenant)
- **Gravite** : CRITIQUE
- **Contexte** : Architecture row-level multi-tenancy avec `user_id`/`org_id` en FK. Si un endpoint oublie le filtre org_id, un agent de l'org A peut acceder aux donnees de l'org B en manipulant les IDs dans l'URL.

### Description

Un agent de l'organisation A tente d'acceder aux contacts/taches/conversations de l'organisation B en modifiant les identifiants dans les requetes API.

### Etapes de reproduction

```
1. Se connecter en tant qu'agent de l'org A
2. Naviguer vers le CRM
3. click [data-testid="nav-link-crm"]
4. wait_for [data-testid="crm-page"] visible

5. javascript_tool :
   // Recuperer l'ID d'un contact de notre org
   const myContact = document.querySelector('[data-testid="crm-contact-item"]');
   const myContactId = myContact?.getAttribute('data-contact-id') ||
                       myContact?.querySelector('a')?.href?.match(/\/(\d+)/)?.[1];
   return { myContactId };

6. javascript_tool :
   // Tenter d'acceder a un contact avec un ID different (potentiellement d'une autre org)
   const targetId = 1; // ID generalement du premier contact cree (souvent admin/autre org)
   const token = localStorage.getItem('token') || sessionStorage.getItem('token');
   const response = await fetch('/api/crm/contacts/' + targetId, {
     headers: { 'Authorization': 'Bearer ' + token }
   });
   return {
     status: response.status,
     body: response.status === 200 ? await response.json() : await response.text()
   };

7. take_screenshot → "CATA-05-idor-attempt.png"

8. javascript_tool :
   // Tester aussi les taches
   const token = localStorage.getItem('token') || sessionStorage.getItem('token');
   const resp = await fetch('/api/tasks/1', {
     headers: { 'Authorization': 'Bearer ' + token }
   });
   return { tasksStatus: resp.status };

9. javascript_tool :
   // Tester les conversations
   const token = localStorage.getItem('token') || sessionStorage.getItem('token');
   const resp = await fetch('/api/chat/conversations/1', {
     headers: { 'Authorization': 'Bearer ' + token }
   });
   return { chatStatus: resp.status };

10. javascript_tool :
    // Tester la modification cross-org (PUT/PATCH)
    const token = localStorage.getItem('token') || sessionStorage.getItem('token');
    const resp = await fetch('/api/crm/contacts/1', {
      method: 'PUT',
      headers: {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ name: 'IDOR-HACKED' })
    });
    return { modifyStatus: resp.status };
```

### Resultat attendu

- Toutes les requetes cross-org repondent 403 Forbidden ou 404 Not Found
- Le filtre `org_id` est applique systematiquement sur tous les endpoints CRUD
- Les tentatives de modification cross-org sont bloquees
- Les tentatives sont tracees dans les audit logs

### Resultat redoute

- Un endpoint repond 200 avec les donnees d'une autre org (fuite de donnees)
- La modification (PUT) fonctionne sur un contact d'une autre org
- Les audit logs ne tracent pas les tentatives d'acces cross-org
- Le filtre org_id est manquant sur un endpoint recent (regression)
- Les endpoints de suppression (DELETE) sont aussi vulnerables

---

## Scenario 6 : Board sans provider configure

- **Produit** : App (Desktop Tauri)
- **Gravite** : MOYENNE
- **Contexte** : Le Board utilise 5 conseillers IA qui font chacun un appel LLM. Sans provider configure (pas de cle API), 5 erreurs en cascade sont attendues.

### Description

L'utilisateur n'a pas configure de provider LLM (ou sa cle API est invalide). Il lance une deliberation Board. 5 appels LLM echouent en cascade.

### Etapes de reproduction

```
1. navigate → http://localhost:1420/?panel=settings
2. wait 3s

3. javascript_tool :
   // Sauvegarder le provider actuel puis le desactiver
   // (ou vider la cle API)
   // Note : adapter selon l'implementation exacte des settings
   const providerSelect = document.querySelector('[data-testid="llm-provider-select"]');
   const savedValue = providerSelect?.value;
   return { currentProvider: savedValue };

4. // Naviguer vers le Board sans provider valide
5. navigate → http://localhost:1420/?panel=board
6. wait 3s

7. javascript_tool :
   const input = document.querySelector('[data-testid="board-question-input"]') ||
                 document.querySelector('textarea');
   if (input) {
     const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
     setter.call(input, 'Dois-je investir dans un nouveau serveur ?');
     input.dispatchEvent(new Event('input', { bubbles: true }));
   }

8. click [data-testid="board-submit-btn"] ou equivalent
9. wait 15s (laisser les 5 appels echouer)
10. take_screenshot → "CATA-06-board-no-provider.png"

11. javascript_tool :
    // Verifier l'etat de l'UI
    const errors = document.querySelectorAll('[class*="error"], [role="alert"]');
    const board = document.querySelector('[data-testid="board-result"]');
    return {
      errorCount: errors.length,
      errorTexts: Array.from(errors).map(e => e.textContent),
      boardResult: board?.textContent?.substring(0, 200),
      pageStillResponsive: !!document.querySelector('body')
    };

12. // Verifier que l'app n'est pas bloquee
13. javascript_tool :
    // Cliquer ailleurs pour verifier la reactivite
    const chatLink = document.querySelector('[data-testid="nav-link-chat"]') ||
                     document.querySelector('a[href*="chat"]');
    return { chatLinkClickable: !!chatLink };
```

### Resultat attendu

- Un message d'erreur clair avant meme de lancer la deliberation : "Aucun provider LLM configure"
- OU si la deliberation est lancee : une seule erreur globale (pas 5 erreurs en cascade)
- Le bouton de deliberation est desactive si pas de provider
- L'app reste reactive apres l'erreur (pas de freeze)
- L'utilisateur est guide vers les Settings pour configurer un provider

### Resultat redoute

- 5 toasts d'erreur empiles les uns sur les autres (un par conseiller)
- L'app freeze pendant 30-60s (les timeouts des 5 appels)
- Le Board reste en etat "loading" indefiniment
- Les erreurs API polluent la console avec des stacktraces
- Le backend accumule 5 connexions HTTP pendantes vers un provider inexistant

---

## Scenario 7 : Import VCard volumineux (10 000 contacts)

- **Produit** : App (Desktop Tauri)
- **Gravite** : HAUTE
- **Contexte** : L'import VCard a ete ajoute en v0.8.0-alpha. Un fichier .vcf peut contenir des milliers de contacts (export Google Contacts, Outlook, etc.).

### Description

L'utilisateur importe un fichier VCard contenant 10 000 contacts. L'app gere-t-elle le volume sans freeze ?

### Etapes de reproduction

```
1. # Terminal : generer un gros fichier VCard de test
   python3 -c "
   with open('/tmp/test-10k-contacts.vcf', 'w') as f:
     for i in range(10000):
       f.write(f'''BEGIN:VCARD
VERSION:3.0
FN:Contact Test {i:05d}
N:Test{i:05d};Contact;;;
EMAIL:contact{i:05d}@test.local
TEL:+33600{i:05d}
ORG:Entreprise Test
END:VCARD
''')
   print('Generated 10000 VCards')
   "

2. navigate → http://localhost:1420/?panel=crm
3. wait 3s
4. take_screenshot → "CATA-07-before-import.png"

5. // Cliquer sur le bouton import VCard
6. javascript_tool :
   const importBtn = document.querySelector('[data-testid="crm-import-vcard-btn"]') ||
                     document.querySelector('button[title*="import"]');
   return { importButtonFound: !!importBtn };

7. // Uploader le fichier via l'input file
8. upload_file → input[type="file"] → /tmp/test-10k-contacts.vcf

9. // Chronometrer et observer
10. javascript_tool :
    const start = Date.now();
    // Stocker le timestamp pour mesurer apres
    window.__importStart = start;
    return { importStarted: true, timestamp: start };

11. wait 30s (laisser l'import tourner)
12. take_screenshot → "CATA-07-during-import.png"

13. javascript_tool :
    // Verifier la reactivite de l'UI pendant l'import
    const elapsed = Date.now() - (window.__importStart || 0);
    const contacts = qsa('[data-testid="crm-contact-item"]', '.contact-card');
    const progressBar = document.querySelector('[data-testid="import-progress"]') ||
                        document.querySelector('[role="progressbar"]');
    return {
      elapsedMs: elapsed,
      contactsVisible: contacts.length,
      hasProgressBar: !!progressBar,
      uiResponsive: document.hasFocus() !== undefined // basique mais indicatif
    };

14. // Attendre la fin de l'import (jusqu'a 5 minutes max)
15. wait 60s
16. take_screenshot → "CATA-07-after-import.png"

17. javascript_tool :
    const contacts = qsa('[data-testid="crm-contact-item"]', '.contact-card');
    return { totalContacts: contacts.length };
```

### Resultat attendu

- L'import se fait en arriere-plan avec une barre de progression
- L'UI reste reactive pendant l'import (pas de freeze du thread principal)
- Les contacts sont inseres par batches (pas un INSERT de 10 000 lignes)
- Un toast ou notification a la fin : "10 000 contacts importes"
- Les doublons sont detectes et geres (skip ou merge)
- L'import prend moins de 2 minutes

### Resultat redoute

- L'app freeze completement pendant l'import (UI bloquee)
- Le backend crash (SQLite lock, memoire, timeout)
- L'import echoue silencieusement apres 1 000 contacts (limite non documentee)
- 10 000 INSERT individuels sans transaction = 10 000 ecritures disque = lent + risque corruption
- Le CRM devient inutilisable apres l'import (pagination absente, scroll infini qui charge tout)
- Le fichier Qdrant explose en taille (embeddings pour 10 000 contacts)

---

## Scenario 8 : 2 admins modifient le meme utilisateur simultanement

- **Produit** : Server (Web multi-tenant)
- **Gravite** : HAUTE
- **Contexte** : Race condition - 2 admins sur 2 navigateurs differents changent le role du meme utilisateur au meme moment.

### Description

Admin A change le role de "Pierre" de "agent" a "manager". Simultanement, Admin B change le role de "Pierre" de "agent" a "admin". Quel role gagne ?

### Etapes de reproduction

```
1. # Ouvrir 2 onglets Chrome, connectes chacun en tant qu'admin

2. # Onglet 1 (Admin A)
   tabs_create_mcp → nouvel onglet
   navigate → URL serveur
   // Login admin
   // Naviguer vers /admin

3. # Onglet 2 (Admin B) - simuler un 2eme admin
   tabs_create_mcp → nouvel onglet
   navigate → URL serveur
   // Login admin (meme compte ou 2eme admin si disponible)
   // Naviguer vers /admin

4. # Dans les 2 onglets : trouver le meme utilisateur (ex: Pierre)

5. # Onglet 1 : preparer le changement (agent → manager)
   select_page → onglet 1
   javascript_tool :
     const rows = document.querySelectorAll('[data-testid="admin-user-row"]');
     const pierreRow = Array.from(rows).find(r =>
       r.textContent.includes('agent') && !r.textContent.includes('admin@')
     );
     const select = pierreRow?.querySelector('[data-testid="admin-user-role-select"]');
     // Ne PAS encore changer - juste localiser
     return { found: !!select, currentRole: select?.value };

6. # Onglet 2 : preparer le meme changement (agent → admin)
   select_page → onglet 2
   javascript_tool :
     // Meme logique, localiser le meme utilisateur
     const rows = document.querySelectorAll('[data-testid="admin-user-row"]');
     const pierreRow = Array.from(rows).find(r =>
       r.textContent.includes('agent') && !r.textContent.includes('admin@')
     );
     return { found: !!pierreRow };

7. # Onglet 1 : changer en "manager"
   select_page → onglet 1
   javascript_tool :
     const rows = document.querySelectorAll('[data-testid="admin-user-row"]');
     const pierreRow = Array.from(rows).find(r =>
       r.textContent.includes('agent') && !r.textContent.includes('admin@')
     );
     const select = pierreRow?.querySelector('[data-testid="admin-user-role-select"]');
     const setter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set;
     setter.call(select, 'manager');
     select.dispatchEvent(new Event('change', { bubbles: true }));
     return 'changed to manager';

8. # Onglet 2 : changer en "admin" IMMEDIATEMENT apres
   select_page → onglet 2
   javascript_tool :
     const rows = document.querySelectorAll('[data-testid="admin-user-row"]');
     const pierreRow = Array.from(rows).find(r => !r.textContent.includes('admin@'));
     const select = pierreRow?.querySelector('[data-testid="admin-user-role-select"]');
     const setter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set;
     setter.call(select, 'admin');
     select.dispatchEvent(new Event('change', { bubbles: true }));
     return 'changed to admin';

9. wait 3s

10. # Verifier le resultat dans les 2 onglets
    select_page → onglet 1
    javascript_tool :
      // Rafraichir les donnees
      location.reload();
    wait 3s
    javascript_tool :
      const rows = document.querySelectorAll('[data-testid="admin-user-row"]');
      const pierre = Array.from(rows).find(r => !r.textContent.includes('admin@'));
      const select = pierre?.querySelector('[data-testid="admin-user-role-select"]');
      return { roleOnTab1: select?.value };

11. take_screenshot → "CATA-08-race-condition-result.png"
```

### Resultat attendu

- Le dernier ecrit gagne (last-write-wins) de maniere deterministe
- Les 2 onglets affichent le meme role apres refresh
- Les audit logs montrent les 2 changements dans l'ordre chronologique
- Pas de corruption de donnees (role invalide, champ vide)
- Idealement : un mecanisme d'optimistic locking (version field) detecte le conflit

### Resultat redoute

- Le role est "manager" dans un onglet et "admin" dans l'autre (etat inconsistant)
- L'API crash avec une erreur de concurrence (deadlock SQLite)
- Le role final est une valeur corrompue ou vide
- Les audit logs montrent un seul changement (le 2eme est perdu)
- Les permissions effectives de Pierre ne correspondent pas au role affiche

---

## Scenario 9 : Backend tombe pendant utilisation

- **Produit** : App (Desktop Tauri)
- **Gravite** : HAUTE
- **Contexte** : Le backend Python (FastAPI via sidecar PyInstaller) peut crasher (OOM, segfault, bug Python). L'utilisateur est en train de travailler.

### Description

L'utilisateur utilise l'app normalement. Le backend crash ou devient injoignable. L'app affiche-t-elle un message clair ou freeze-t-elle ?

### Etapes de reproduction

```
1. Lancer THERESE App normalement
2. navigate → http://localhost:1420
3. Envoyer un message dans le chat (verifier que tout fonctionne)
4. take_screenshot → "CATA-09-before-crash.png"

5. # Simuler le crash du backend
   # Option A : tuer le process backend
   # Terminal :
   # lsof -ti :17293 | xargs kill -9

   # Option B (via Chrome MCP, plus propre) :
   javascript_tool :
     // Simuler un backend injoignable en interceptant les requetes
     const originalFetch = window.fetch;
     window.__originalFetch = originalFetch;
     window.fetch = function(...args) {
       const url = args[0]?.toString() || args[0]?.url;
       if (url && url.includes('/api/')) {
         return Promise.reject(new TypeError('Failed to fetch'));
       }
       return originalFetch.apply(this, args);
     };
     return 'backend simulated down';

6. // Tenter d'envoyer un message
7. javascript_tool :
   const input = document.querySelector('[data-testid="chat-message-input"]');
   if (input) {
     const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
     setter.call(input, 'Ce message devrait echouer');
     input.dispatchEvent(new Event('input', { bubbles: true }));
   }

8. click [data-testid="chat-send-btn"]
9. wait 10s
10. take_screenshot → "CATA-09-backend-down.png"

11. javascript_tool :
    // Verifier la reaction de l'app
    const errorBanner = document.querySelector('[data-testid="connection-lost"]') ||
                        document.querySelector('[data-testid="error-banner"]') ||
                        document.querySelector('.connection-error');
    const toasts = document.querySelectorAll('[class*="toast"], [role="alert"]');
    return {
      connectionLostBanner: !!errorBanner,
      bannerText: errorBanner?.textContent,
      toastCount: toasts.length,
      toastTexts: Array.from(toasts).map(t => t.textContent)
    };

12. // Restaurer le backend
13. javascript_tool :
    if (window.__originalFetch) {
      window.fetch = window.__originalFetch;
      delete window.__originalFetch;
      return 'backend restored';
    }
    return 'no backup found';

14. wait 5s
15. // Verifier la reconnexion automatique
16. javascript_tool :
    const input = document.querySelector('[data-testid="chat-message-input"]');
    const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
    setter.call(input, 'Test apres reconnexion');
    input.dispatchEvent(new Event('input', { bubbles: true }));
17. click [data-testid="chat-send-btn"]
18. wait 15s
19. take_screenshot → "CATA-09-after-recovery.png"
```

### Resultat attendu

- Un banner ou toast clair : "Connexion au serveur perdue" ou "Le backend ne repond pas"
- Le message saisi n'est pas perdu (reste dans l'input ou mis en file d'attente)
- L'app ne freeze pas (le frontend reste reactif)
- Apres retour du backend : reconnexion automatique
- Le message en file d'attente est envoye automatiquement ou l'utilisateur est invite a re-envoyer

### Resultat redoute

- L'app freeze completement (aucune interaction possible)
- Pas de message d'erreur, l'utilisateur ne comprend pas pourquoi rien ne fonctionne
- Le message saisi est perdu sans trace
- Apres retour du backend, l'app reste dans un etat casse (necessite un reload complet)
- Le sidecar PyInstaller ne se relance pas automatiquement
- Le spinner de chargement tourne indefiniment

---

## Scenario 10 : RGPD suppression totale

- **Produit** : Les deux (App + Server)
- **Gravite** : CRITIQUE
- **Contexte** : Le RGPD impose le droit a l'effacement (article 17). L'app a un endpoint DELETE /api/data/all (26 tables + Qdrant). Le Server doit supprimer uniquement les donnees de l'utilisateur, pas celles de l'organisation.

### Description

Un utilisateur demande la suppression totale de ses donnees. Dans l'App, TOUT doit etre efface. Dans le Server, seules SES donnees personnelles doivent etre supprimees (pas les donnees partagees de l'org).

### Etapes de reproduction - App

```
1. Lancer THERESE App
2. Verifier qu'il y a des donnees :
   - Au moins 1 conversation avec messages
   - Au moins 1 contact CRM
   - Au moins 1 tache
   - Au moins 1 souvenir en memoire

3. javascript_tool :
   // Inventaire AVANT suppression
   const chatMessages = document.querySelectorAll('[data-testid="chat-message-item"]');
   return { messagesBefore: chatMessages.length };

4. // Naviguer vers RGPD / Data
5. navigate → http://localhost:1420/?panel=data
   // OU via les settings RGPD
6. wait 3s
7. take_screenshot → "CATA-10-app-before-delete.png"

8. // Cliquer sur "Supprimer toutes mes donnees"
9. javascript_tool :
   const deleteBtn = document.querySelector('[data-testid="rgpd-delete-all-btn"]') ||
                     document.querySelector('button[class*="danger"]');
   return { deleteButtonFound: !!deleteBtn };

10. // Cliquer et confirmer
11. click le bouton de suppression
12. // Il devrait y avoir une confirmation ("Etes-vous sur ?")
13. javascript_tool :
    const confirmModal = document.querySelector('[data-testid="confirm-delete-modal"]') ||
                         document.querySelector('[role="alertdialog"]');
    return { confirmationAsked: !!confirmModal };

14. // Confirmer la suppression
15. click le bouton de confirmation
16. wait 10s (suppression 26 tables + Qdrant)
17. take_screenshot → "CATA-10-app-after-delete.png"

18. // Verifier que TOUT est vide
19. navigate → http://localhost:1420/?panel=chat
20. wait 3s
21. javascript_tool :
    const messages = document.querySelectorAll('[data-testid="chat-message-item"]');
    return { messagesAfter: messages.length };

22. navigate → http://localhost:1420/?panel=crm
23. wait 3s
24. javascript_tool :
    const contacts = qsa('[data-testid="crm-contact-item"]', '.contact-card');
    return { contactsAfter: contacts.length };

25. navigate → http://localhost:1420/?panel=tasks
26. wait 3s
27. javascript_tool :
    const tasks = qsa('[data-testid="task-item"]', '.task-card');
    return { tasksAfter: tasks.length };
```

### Etapes de reproduction - Server

```
1. Se connecter en tant qu'agent (pas admin)
2. Creer des donnees : 1 message, 1 contact, 1 tache
3. Se connecter en tant qu'un AUTRE agent de la meme org
4. Creer aussi des donnees

5. Se reconnecter en tant que le premier agent
6. Demander la suppression de ses donnees (profil → RGPD → Supprimer)

7. javascript_tool :
   // Apres suppression, verifier :
   // 1. Les donnees du 1er agent sont effacees
   // 2. Les donnees du 2eme agent sont INTACTES
   // 3. Les donnees partagees de l'org (parametres, etc.) sont intactes
   return { note: 'Verifier manuellement via API et via le 2eme compte' };

8. // Se connecter en tant que le 2eme agent
9. Verifier que ses contacts, taches, messages sont toujours la
10. take_screenshot → "CATA-10-server-other-user-intact.png"
```

### Resultat attendu - App

- Les 26 tables SQLite sont videes (conversations, messages, contacts, taches, factures, memoire, parametres...)
- Les embeddings Qdrant sont supprimes (collection purgee ou supprimee)
- Les fichiers associes (images generees, PDF exportes) sont supprimes
- Les cles API chiffrees sont supprimees
- L'app revient a l'etat "premier lancement" (onboarding)
- Un fichier de confirmation/log de suppression est genere (preuve RGPD)

### Resultat attendu - Server

- Seules les donnees de l'utilisateur demandeur sont supprimees
- Les messages dans les conversations PARTAGEES sont anonymises (auteur = "utilisateur supprime")
- Les contacts, taches, et factures des autres agents sont intacts
- Les donnees de l'organisation (parametres, roles, charte) restent
- Le compte utilisateur est desactive (pas supprime physiquement pour l'audit trail)
- Un log d'audit trace la demande RGPD avec horodatage

### Resultat redoute - App

- Certaines tables ne sont pas videes (donnees orphelines dans des tables oubliees)
- Les embeddings Qdrant restent (donnees fantomes retrouvables par recherche semantique)
- Les fichiers physiques restent sur le disque (`~/.therese/images/`, exports PDF)
- Les cles API restent en memoire (process Python encore actif)
- L'app crash apres la suppression (references a des objets supprimes)
- Pas de confirmation de suppression (l'utilisateur ne sait pas si c'est fait)

### Resultat redoute - Server

- Les donnees des AUTRES utilisateurs de l'org sont aussi supprimees (catastrophe)
- Les conversations partagees sont supprimees au lieu d'etre anonymisees
- Le compte est supprime physiquement au lieu d'etre desactive (perte de l'audit trail)
- Les cles de chiffrement org sont corrompues (impact sur tous les agents)
- L'admin ne peut plus voir l'historique de l'agent supprime dans les audit logs
- La suppression echoue silencieusement (200 OK mais donnees encore la)

---

## Matrice de couverture

| Scenario | Auth | Data | Securite | UX | Performance | RGPD |
|----------|------|------|----------|-----|-------------|------|
| 1. Onboarding | - | X | - | X | - | - |
| 2. JWT expire | X | - | X | X | - | - |
| 3. Fernet | - | X | X | X | - | - |
| 4. Double-clic | - | X | - | X | - | - |
| 5. IDOR | X | X | X | - | - | - |
| 6. Board no-provider | - | - | - | X | X | - |
| 7. VCard 10K | - | X | - | X | X | - |
| 8. Race condition | - | X | - | - | X | - |
| 9. Backend down | - | - | - | X | X | - |
| 10. RGPD | - | X | - | X | - | X |

## Ordre d'execution recommande

1. **Scenario 5** (IDOR) - le plus critique, impact securite immediat
2. **Scenario 10** (RGPD) - obligation legale, consequence financiere
3. **Scenario 1** (Onboarding) - regression connue, deja fixee mais a reverifier
4. **Scenario 3** (Fernet) - perte de donnees irreversible
5. **Scenario 2** (JWT) - experience utilisateur degradee
6. **Scenario 4** (Double-clic) - impact comptable
7. **Scenario 9** (Backend down) - resilience runtime
8. **Scenario 8** (Race condition) - concurrence admin
9. **Scenario 7** (VCard 10K) - performance
10. **Scenario 6** (Board no-provider) - UX degradee
