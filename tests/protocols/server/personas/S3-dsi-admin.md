# S3 - DSI / Admin

> **Sélecteurs, à lire avant d'exécuter le moindre script de ce document.**
>
> Correction du 01/09/2026. Ces protocoles combinaient deux appels à
> `document.querySelectorAll` avec un OU logique. Une NodeList vide est un
> objet, donc une valeur vraie : **le repli n'était jamais emprunté**, et le
> premier sélecteur l'emportait même quand il ne trouvait rien. Combiné à des
> identifiants absents du code, cela rendait les verdicts vides : « pas de
> doublon » et « zéro donnée restante » étaient vrais quoi qu'il arrive.
>
> L'aide `qsa` parcourt réellement les sélecteurs et **échoue quand aucun ne
> trouve rien**. Correction du 02/09/2026 (B-150) : elle ne vivait ici, dans
> cette prose, et **aucune étape ne l'exécutait jamais** - le premier pas qui
> l'appelait levait `ReferenceError: qsa is not defined`. Chaque étape
> `javascript_tool` est une évaluation séparée dans la page, et un `navigate →`
> remet `window` à zéro : l'aide est donc **redéposée par l'étape qui s'en
> sert**, sous cette forme, et ce document n'a plus rien à injecter d'avance.
>
> ```js
> window.qsa ||= (...sels) => {
>   for (const s of sels) {
>     const trouves = [...document.querySelectorAll(s)];
>     if (trouves.length) return trouves;
>   }
>   throw new Error(
>     "Aucun element pour : " + sels.join(" | ") +
>     " - selecteur faux ou ecran inattendu, ce pas ne prouve rien."
>   );
> };
> ```
>
> Un comptage qui rend zéro parce que le sélecteur est faux n'est pas un
> résultat, c'est une mesure ratée.


> Persona : Thomas Renaud, DSI d'une mairie de 400 agents.
> Role : `admin` - acces complet a la plateforme, gestion utilisateurs, audit, configuration.
> Produit : THERESE Server (Web multi-tenant)
> 42 etapes, ~170 tests, duree Chrome MCP estimee : 2h-2h30

---

## Contexte

Thomas est DSI depuis 8 ans. Il a deploye THERESE Server sur un serveur on-premise de la mairie. Son quotidien : creer et gerer les comptes agents, surveiller l'usage via les logs d'audit, s'assurer que les donnees restent dans le perimetre, et utiliser lui-meme l'outil pour ses taches courantes (chat, taches, CRM interne, Board pour les decisions strategiques). Il est methodique, teste les limites de l'outil, et verifie que les roles RBAC fonctionnent correctement.

---

## Pre-requis

- THERESE Server accessible (ex: `http://localhost:8880` via tunnel SSH)
- Compte admin existant : `admin@therese.local` / `admin`
- Au moins 2 autres utilisateurs dans la base (un agent, un manager) pour tester la gestion
- Chrome avec extension Claude-in-Chrome
- Voir `shared/chrome-mcp-patterns.md` pour les patterns anti-flaky

---

## data-testid utilises

### Authentification
| data-testid | Element | Type |
|---|---|---|
| `login-form` | Formulaire de login | form |
| `login-email-input` | Champ email | input |
| `login-password-input` | Champ mot de passe | input |
| `login-submit-btn` | Bouton Connexion | button |
| `charter-modal` | Modale charte d'utilisation | dialog |
| `charter-accept-btn` | Bouton accepter la charte | button |

### Navigation
| data-testid | Element | Type |
|---|---|---|
| `nav-link-admin` | Lien Admin dans la NavBar | a/button |
| `nav-link-chat` | Lien Chat | a/button |
| `nav-link-tasks` | Lien Taches | a/button |
| `nav-link-crm` | Lien CRM | a/button |
| `nav-link-board` | Lien Board | a/button |
| `nav-link-skills` | Lien Skills | a/button |

### Admin
| data-testid | Element | Type |
|---|---|---|
| `admin-dashboard` | Dashboard admin | section |
| `admin-kpi-active-users` | KPI utilisateurs actifs | span |
| `admin-kpi-total-users` | KPI total utilisateurs | span |
| `admin-kpi-conversations` | KPI conversations | span |
| `admin-kpi-messages` | KPI messages | span |
| `admin-users-table` | Table des utilisateurs | table |
| `admin-user-row` | Ligne utilisateur | tr |
| `admin-user-role-select` | Select role utilisateur | select |
| `admin-user-toggle-active` | Toggle actif/inactif | button |
| `admin-audit-logs` | Section logs d'audit | section |
| `admin-audit-log-item` | Ligne de log | div |
| `admin-audit-filter` | Filtre type d'action | select |

### Taches
| data-testid | Element | Type |
|---|---|---|
| `tasks-page` | Page taches | section |
| `tasks-list` | Liste des taches | ul/div |
| `tasks-create-btn` | Bouton creer tache | button |
| `task-item` | Element tache | li/div |
| `task-title-input` | Champ titre tache | input |
| `task-save-btn` | Bouton sauvegarder tache | button |
| `task-status-badge` | Badge statut tache | span |

### CRM
| data-testid | Element | Type |
|---|---|---|
| `crm-page` | Page CRM | section |
| `crm-contact-list` | Liste des contacts | ul/div |
| `crm-create-contact-btn` | Bouton creer contact | button |
| `crm-contact-item` | Element contact | li/div |
| `crm-contact-name-input` | Champ nom contact | input |
| `crm-contact-email-input` | Champ email contact | input |
| `crm-contact-save-btn` | Bouton sauvegarder contact | button |

### Board
| data-testid | Element | Type |
|---|---|---|
| `board-page` | Page Board | section |
| `board-panel` | Panneau de deliberation | div |
| `board-question-input` | Champ question Board | textarea |
| `board-submit-btn` | Bouton lancer deliberation | button |
| `board-result` | Resultat de la deliberation | div |
| `board-advisor-card` | Carte conseiller | div |

### Skills
| data-testid | Element | Type |
|---|---|---|
| `skills-page` | Page Skills | section |
| `skills-list` | Liste des skills | ul/div |
| `skill-item` | Element skill | li/div |
| `skill-execute-btn` | Bouton executer skill | button |
| `skill-result` | Resultat du skill | div |

### Chat
| data-testid | Element | Type |
|---|---|---|
| `chat-page` | Page Chat | section |
| `chat-message-input` | Champ saisie message | textarea |
| `chat-send-btn` | Bouton envoyer | button |
| `chat-message-item` | Message dans le fil | div |
| `chat-new-conversation-btn` | Bouton nouvelle conversation | button |

---

## Etapes du parcours

### Phase 1 : Authentification et charte (etapes 1-6)

#### Etape 1 : Acceder a la page de login
- **Action** : Ouvrir l'URL du serveur THERESE
- **Chrome MCP** :
  ```
  navigate_page → URL serveur
  wait_for [data-testid="login-form"] visible (timeout 5s)
  take_screenshot → "S3-01-login-page.png"
  ```
- **Attendu** : Formulaire de login visible avec champs email et mot de passe
- **Priorite** : P0

#### Etape 2 : Saisir l'email admin
- **Action** : Remplir le champ email avec `admin@therese.local`
- **Chrome MCP** :
  ```
  wait_for [data-testid="login-email-input"] visible
  fill [data-testid="login-email-input"] → "admin@therese.local"
  wait 100ms
  ```
- **Attendu** : Champ rempli sans erreur
- **Priorite** : P0

#### Etape 3 : Saisir le mot de passe
- **Action** : Remplir le champ mot de passe avec `admin`
- **Chrome MCP** :
  ```
  fill [data-testid="login-password-input"] → "admin"
  wait 100ms
  ```
- **Attendu** : Champ rempli, caracteres masques
- **Priorite** : P0

#### Etape 4 : Soumettre le formulaire
- **Action** : Cliquer sur le bouton Connexion
- **Chrome MCP** :
  ```
  click [data-testid="login-submit-btn"]
  wait_for [data-testid="charter-modal"] visible (timeout 5s)
  take_screenshot → "S3-04-charter-modal.png"
  ```
- **Attendu** : Modale de charte d'utilisation affichee
- **Tests supplementaires** :
  - `[P0]` Pas d'erreur d'authentification
  - `[P1]` Pas de mot de passe visible dans l'URL ou le DOM
- **Priorite** : P0

#### Etape 5 : Accepter la charte d'utilisation
- **Action** : Cliquer sur "Accepter"
- **Chrome MCP** :
  ```
  click [data-testid="charter-accept-btn"]
  wait_for ABSENCE [data-testid="charter-modal"] (timeout 3s)
  wait 500ms (animation)
  ```
- **Attendu** : Modale fermee, redirection vers le chat
- **Priorite** : P0

#### Etape 6 : Verifier l'arrivee sur le chat
- **Action** : Verifier que la page chat est affichee
- **Chrome MCP** :
  ```
  wait_for [data-testid="chat-page"] visible (timeout 5s)
  take_screenshot → "S3-06-chat-ready.png"
  ```
- **Attendu** : Page chat visible, input message present
- **Tests supplementaires** :
  - `[P0]` URL contient `/chat`
  - `[P0]` Pas de message d'erreur visible
- **Priorite** : P0

---

### Phase 2 : Verification RBAC admin (etapes 7-8)

#### Etape 7 : Verifier que le lien Admin est VISIBLE dans la NavBar
- **Action** : Verifier la presence du lien Admin (invisible pour les agents et managers)
- **Chrome MCP** :
  ```
  javascript_tool :
    const adminLink = document.querySelector('[data-testid="nav-link-admin"]');
    return adminLink !== null && adminLink.offsetParent !== null;
  // doit retourner true pour un admin
  take_screenshot → "S3-07-navbar-admin-visible.png"
  ```
- **Attendu** : Le lien Admin est visible et cliquable
- **Tests supplementaires** :
  - `[P0]` `nav-link-admin` present dans le DOM
  - `[P0]` Element visible (pas `display:none` ni `visibility:hidden`)
  - `[P1]` Lien pointe vers `/admin`
- **Priorite** : P0

#### Etape 8 : Naviguer vers /admin - Dashboard visible
- **Action** : Cliquer sur le lien Admin
- **Chrome MCP** :
  ```
  click [data-testid="nav-link-admin"]
  wait_for [data-testid="admin-dashboard"] visible (timeout 5s)
  take_screenshot → "S3-08-admin-dashboard.png"
  ```
- **Attendu** : Dashboard admin affiche avec KPIs et table utilisateurs
- **Tests supplementaires** :
  - `[P0]` URL contient `/admin`
  - `[P0]` Pas de redirection vers `/chat` (preuve RBAC OK)
  - `[P1]` Pas d'erreur reseau dans la console
- **Priorite** : P0

---

### Phase 3 : Dashboard et gestion utilisateurs (etapes 9-15)

#### Etape 9 : Verifier les KPIs du dashboard
- **Action** : Lire les valeurs des 4 KPIs
- **Chrome MCP** :
  ```
  javascript_tool :
    const kpis = {
      active: document.querySelector('[data-testid="admin-kpi-active-users"]')?.textContent,
      total: document.querySelector('[data-testid="admin-kpi-total-users"]')?.textContent,
      conversations: document.querySelector('[data-testid="admin-kpi-conversations"]')?.textContent,
      messages: document.querySelector('[data-testid="admin-kpi-messages"]')?.textContent,
    };
    return JSON.stringify(kpis);
  take_screenshot → "S3-09-kpis.png"
  ```
- **Attendu** : 4 KPIs affiches avec des valeurs numeriques (>= 0)
- **Tests supplementaires** :
  - `[P0]` Aucun KPI n'est `null`, `undefined` ou vide
  - `[P1]` Utilisateurs actifs <= Total utilisateurs
  - `[P2]` Messages >= Conversations (au moins 1 message par conversation)
- **Priorite** : P0

#### Etape 10 : Voir la table des utilisateurs
- **Action** : Verifier la presence et le contenu de la table
- **Chrome MCP** :
  ```
  wait_for [data-testid="admin-users-table"] visible
  javascript_tool :
    const table = document.querySelector('[data-testid="admin-users-table"]');
    const rows = table.querySelectorAll('[data-testid="admin-user-row"]');
    const headers = table.querySelectorAll('th');
    return {
      rowCount: rows.length,
      headers: Array.from(headers).map(h => h.textContent.trim()),
    };
  take_screenshot → "S3-10-users-table.png"
  ```
- **Attendu** : Table visible avec colonnes Nom, Email, Role, Statut, Charte (minimum)
- **Tests supplementaires** :
  - `[P0]` Au moins 1 ligne (l'admin lui-meme)
  - `[P0]` Colonnes Nom et Email presentes
  - `[P1]` Colonnes Role et Statut presentes
  - `[P2]` Colonne Charte (date d'acceptation ou non acceptee)
- **Priorite** : P0

#### Etape 11 : Changer le role d'un utilisateur (agent → manager)
- **Action** : Trouver un utilisateur avec role "agent" et le passer en "manager"
- **Chrome MCP** :
  ```
  javascript_tool :
    const rows = document.querySelectorAll('[data-testid="admin-user-row"]');
    let targetRow = null;
    rows.forEach(row => {
      const select = row.querySelector('[data-testid="admin-user-role-select"]');
      if (select && select.value === 'agent') targetRow = row;
    });
    if (targetRow) {
      const select = targetRow.querySelector('[data-testid="admin-user-role-select"]');
      const setter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set;
      setter.call(select, 'manager');
      select.dispatchEvent(new Event('change', { bubbles: true }));
      return 'role changed to manager';
    }
    return 'no agent found';
  wait 2s (API call)
  take_screenshot → "S3-11-role-changed.png"
  ```
- **Attendu** : Le role est mis a jour cote UI et cote API (persistence)
- **Tests supplementaires** :
  - `[P0]` Le select affiche "manager" apres le changement
  - `[P0]` Pas d'erreur dans la console
  - `[P1]` Un toast ou feedback visuel confirme le changement
  - `[P1]` Apres refresh, le role est toujours "manager" (persistence)
- **Priorite** : P0

#### Etape 12 : Desactiver un utilisateur
- **Action** : Cliquer sur le toggle actif/inactif d'un utilisateur (pas l'admin)
- **Chrome MCP** :
  ```
  javascript_tool :
    const rows = document.querySelectorAll('[data-testid="admin-user-row"]');
    let targetToggle = null;
    rows.forEach(row => {
      const email = row.querySelector('td:nth-child(2)')?.textContent;
      if (email && !email.includes('admin@')) {
        targetToggle = row.querySelector('[data-testid="admin-user-toggle-active"]');
      }
    });
    if (targetToggle) { targetToggle.click(); return 'toggle clicked'; }
    return 'no non-admin user found';
  wait 2s (API call)
  take_screenshot → "S3-12-user-deactivated.png"
  ```
- **Attendu** : L'utilisateur est desactive (indicateur visuel change)
- **Tests supplementaires** :
  - `[P0]` Le statut visuel change (couleur, icone, texte)
  - `[P1]` L'utilisateur desactive ne peut plus se connecter (test cross-session)
  - `[P1]` Le KPI "utilisateurs actifs" diminue de 1
- **Priorite** : P0

#### Etape 13 : Verifier que l'admin ne peut pas se desactiver lui-meme
- **Action** : Tenter de cliquer sur le toggle de l'admin
- **Chrome MCP** :
  ```
  javascript_tool :
    const rows = document.querySelectorAll('[data-testid="admin-user-row"]');
    let adminToggle = null;
    rows.forEach(row => {
      const email = row.querySelector('td:nth-child(2)')?.textContent;
      if (email && email.includes('admin@')) {
        adminToggle = row.querySelector('[data-testid="admin-user-toggle-active"]');
      }
    });
    if (adminToggle) {
      const isDisabled = adminToggle.disabled || adminToggle.getAttribute('aria-disabled') === 'true';
      if (!isDisabled) { adminToggle.click(); }
      return { disabled: isDisabled, clicked: !isDisabled };
    }
    return 'admin row not found';
  take_screenshot → "S3-13-admin-self-deactivate-blocked.png"
  ```
- **Attendu** : Le bouton est desactive OU le clic est sans effet OU un message d'erreur s'affiche
- **Tests supplementaires** :
  - `[P0]` L'admin reste actif apres la tentative
  - `[P0]` Pas de crash ou erreur 500
  - `[P1]` Message explicite si le bouton est cliquable ("Impossible de desactiver votre propre compte")
- **Priorite** : P0

#### Etape 14 : Consulter les Audit Logs
- **Action** : Acceder a la section logs d'audit
- **Chrome MCP** :
  ```
  wait_for [data-testid="admin-audit-logs"] visible
  javascript_tool :
    const logs = document.querySelectorAll('[data-testid="admin-audit-log-item"]');
    const firstLog = logs[0]?.textContent;
    return { count: logs.length, sample: firstLog };
  take_screenshot → "S3-14-audit-logs.png"
  ```
- **Attendu** : Liste chronologique des actions (login, changement role, desactivation)
- **Tests supplementaires** :
  - `[P0]` Au moins 1 log present (le login de l'admin)
  - `[P0]` Les logs recents sont en haut (ordre chronologique inverse)
  - `[P1]` Chaque log a un timestamp, un type d'action, et un auteur
  - `[P1]` Le changement de role de l'etape 11 apparait dans les logs
  - `[P1]` La desactivation de l'etape 12 apparait dans les logs
- **Priorite** : P0

#### Etape 15 : Filtrer les logs par type d'action
- **Action** : Utiliser le filtre pour ne voir qu'un type d'action
- **Chrome MCP** :
  ```
  javascript_tool :
    const filter = document.querySelector('[data-testid="admin-audit-filter"]');
    const options = Array.from(filter.querySelectorAll('option')).map(o => o.value);
    return { options };
  // Selectionner un type specifique (ex: "role_change" ou "login")
  javascript_tool :
    const filter = document.querySelector('[data-testid="admin-audit-filter"]');
    const setter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set;
    setter.call(filter, filter.querySelectorAll('option')[1]?.value || 'login');
    filter.dispatchEvent(new Event('change', { bubbles: true }));
    return 'filter applied';
  wait 1s
  javascript_tool :
    const logs = document.querySelectorAll('[data-testid="admin-audit-log-item"]');
    return { filteredCount: logs.length };
  take_screenshot → "S3-15-audit-filtered.png"
  ```
- **Attendu** : Seuls les logs du type selectionne sont affiches
- **Tests supplementaires** :
  - `[P0]` Le nombre de logs affiches diminue apres filtrage
  - `[P1]` Tous les logs affiches sont du type selectionne
  - `[P1]` Revenir a "Tous" restaure la liste complete
- **Priorite** : P1

---

### Phase 4 : Chat avec visibilite admin (etapes 16-22)

#### Etape 16 : Naviguer vers le Chat
- **Action** : Cliquer sur le lien Chat dans la NavBar
- **Chrome MCP** :
  ```
  click [data-testid="nav-link-chat"]
  wait_for [data-testid="chat-page"] visible (timeout 5s)
  take_screenshot → "S3-16-chat-page.png"
  ```
- **Attendu** : Page chat visible
- **Priorite** : P0

#### Etape 17 : Envoyer un premier message
- **Action** : Taper un message et l'envoyer
- **Chrome MCP** :
  ```
  javascript_tool :
    const input = document.querySelector('[data-testid="chat-message-input"]');
    const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
    setter.call(input, 'Quels sont les indicateurs cles pour le rapport annuel de la DSI ?');
    input.dispatchEvent(new Event('input', { bubbles: true }));
    return 'message set';
  click [data-testid="chat-send-btn"]
  wait_for [data-testid="chat-message-item"] (timeout 30s)
  take_screenshot → "S3-17-chat-response.png"
  ```
- **Attendu** : Message envoye, reponse de l'IA affichee
- **Tests supplementaires** :
  - `[P0]` Au moins 2 messages dans le fil (question + reponse)
  - `[P0]` La reponse n'est pas vide
  - `[P1]` Le message utilisateur est identifie comme "user"
- **Priorite** : P0

#### Etape 18 : Verifier le streaming SSE
- **Action** : Observer que la reponse arrive en streaming
- **Chrome MCP** :
  ```
  javascript_tool :
    const messages = document.querySelectorAll('[data-testid="chat-message-item"]');
    const lastMessage = messages[messages.length - 1];
    return lastMessage?.textContent?.length > 10;
  ```
- **Attendu** : Le texte s'affiche progressivement (pas en bloc)
- **Priorite** : P1

#### Etape 19 : Tester l'injection XSS dans le chat
- **Action** : Envoyer un message contenant du HTML/JS malveillant
- **Chrome MCP** :
  ```
  javascript_tool :
    // B-389/B-392 (05/09/2026) : armer le temoin AVANT l'injection, comme A3.
    // Sans lui, le controle « aucun alert » etait vrai par construction, et un
    // <script> insere par innerHTML ne s'execute jamais : seul `onerror`
    // d'une image injectee revele une vraie XSS.
    window.__xss_triggered = undefined;
    window.alert = () => { window.__xss_triggered = true; };
    const input = document.querySelector('[data-testid="chat-message-input"]');
    const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
    setter.call(input, '<script>alert("xss")</script><img src=x onerror=alert(1)>');
    input.dispatchEvent(new Event('input', { bubbles: true }));
  click [data-testid="chat-send-btn"]
  wait 3s
  javascript_tool :
    const imagesInjectees = document.querySelectorAll('img[src="x"]').length;
    const dangerousScripts = document.querySelectorAll('script:not([src])');
    const hasInjected = Array.from(dangerousScripts).some(s => s.textContent.includes('alert'));
    const texteBrut = Array.from(document.querySelectorAll('[data-testid="chat-message"]'))
      .some(m => m.textContent.includes('<img src=x onerror=alert(1)>'));
    return {
      alertDeclenche: window.__xss_triggered === true,
      imagesInjectees,
      injected: hasInjected,
      texteEchappeVisible: texteBrut,
      safe: window.__xss_triggered !== true && imagesInjectees === 0 && !hasInjected,
    };
  take_screenshot → "S3-19-xss-test.png"
  ```
- **Attendu** : `safe === true` : le texte est echappe, aucun `alert` declenche (temoin arme), aucune `img[src="x"]` dans le DOM
- **Tests supplementaires** :
  - `[P0]` `alertDeclenche === false` (temoin arme a l'action 1, sinon le controle ne peut pas rougir)
  - `[P0]` `imagesInjectees === 0` (une image injectee par innerHTML s'execute sans creer de `<script>`)
  - `[P0]` Pas de `<script>` injecte dans le DOM
  - `[P1]` Le texte brut `<img src=x onerror=alert(1)>` est visible echappe
- **Priorite** : P0

#### Etape 20 : Creer une nouvelle conversation
- **Action** : Cliquer sur le bouton nouvelle conversation
- **Chrome MCP** :
  ```
  click [data-testid="chat-new-conversation-btn"]
  wait 1s
  take_screenshot → "S3-20-new-conversation.png"
  ```
- **Attendu** : Fil de conversation vide, pret a ecrire
- **Priorite** : P1

#### Etape 21 : Envoyer un message technique (SQL, code)
- **Action** : Envoyer une question contenant du code
- **Chrome MCP** :
  ```
  javascript_tool :
    const input = document.querySelector('[data-testid="chat-message-input"]');
    const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
    setter.call(input, 'Peux-tu me generer une requete SQL pour lister les agents qui n ont pas accepte la charte ?');
    input.dispatchEvent(new Event('input', { bubbles: true }));
  click [data-testid="chat-send-btn"]
  wait_for [data-testid="chat-message-item"] (timeout 30s)
  take_screenshot → "S3-21-code-response.png"
  ```
- **Attendu** : Reponse avec bloc de code formate
- **Tests supplementaires** :
  - `[P1]` Le code SQL est dans un bloc `<pre>` ou `<code>`
  - `[P2]` Coloration syntaxique presente
- **Priorite** : P1

#### Etape 22 : Verifier l'historique des conversations
- **Action** : Verifier que les 2 conversations sont listees
- **Chrome MCP** :
  ```
  javascript_tool :
    // Aide qsa redeposee ici : chaque javascript_tool est une evaluation separee,
    // et un navigate remet la page a zero (voir l'en-tete du document).
    window.qsa ||= (...sels) => { for (const s of sels) { const t = [...document.querySelectorAll(s)]; if (t.length) return t; } throw new Error("Aucun element pour : " + sels.join(" | ") + " - selecteur faux ou ecran inattendu, ce pas ne prouve rien."); };
    const conversations = qsa('[data-testid="conversation-item"]', '.conversation-item');
    return { count: conversations.length };
  take_screenshot → "S3-22-conversation-history.png"
  ```
- **Attendu** : Au moins 2 conversations dans l'historique
- **Priorite** : P1

---

### Phase 5 : Gestion des taches (etapes 23-27)

#### Etape 23 : Naviguer vers les Taches
- **Action** : Cliquer sur le lien Taches
- **Chrome MCP** :
  ```
  click [data-testid="nav-link-tasks"]
  wait_for [data-testid="tasks-page"] visible (timeout 5s)
  take_screenshot → "S3-23-tasks-page.png"
  ```
- **Attendu** : Page taches visible
- **Priorite** : P0

#### Etape 24 : Creer une tache
- **Action** : Cliquer sur "Creer" et remplir le formulaire
- **Chrome MCP** :
  ```
  click [data-testid="tasks-create-btn"]
  wait_for [data-testid="task-title-input"] visible (timeout 3s)
  javascript_tool :
    const input = document.querySelector('[data-testid="task-title-input"]');
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
    setter.call(input, 'Audit securite trimestriel - Q2 2026');
    input.dispatchEvent(new Event('input', { bubbles: true }));
  click [data-testid="task-save-btn"]
  wait 2s
  take_screenshot → "S3-24-task-created.png"
  ```
- **Attendu** : Tache creee et visible dans la liste
- **Tests supplementaires** :
  - `[P0]` La tache apparait dans `tasks-list`
  - `[P1]` Toast de confirmation affiche
- **Priorite** : P0

#### Etape 25 : Verifier la tache dans la liste
- **Action** : Chercher la tache creee
- **Chrome MCP** :
  ```
  javascript_tool :
    const tasks = document.querySelectorAll('[data-testid="task-item"]');
    const found = Array.from(tasks).some(t => t.textContent.includes('Audit securite'));
    return { taskCount: tasks.length, auditTaskFound: found };
  ```
- **Attendu** : La tache "Audit securite trimestriel" est presente
- **Priorite** : P0

#### Etape 26 : Verifier le statut initial
- **Action** : Lire le badge de statut de la tache
- **Chrome MCP** :
  ```
  javascript_tool :
    const tasks = document.querySelectorAll('[data-testid="task-item"]');
    const auditTask = Array.from(tasks).find(t => t.textContent.includes('Audit securite'));
    const badge = auditTask?.querySelector('[data-testid="task-status-badge"]');
    return badge?.textContent;
  ```
- **Attendu** : Statut initial = "A faire" ou "Todo" ou equivalent
- **Priorite** : P1

#### Etape 27 : Verifier la visibilite admin (toutes les taches)
- **Action** : En tant qu'admin, verifier qu'on voit les taches de tous les utilisateurs (pas seulement les siennes)
- **Chrome MCP** :
  ```
  javascript_tool :
    const tasks = document.querySelectorAll('[data-testid="task-item"]');
    return { totalVisibleTasks: tasks.length };
  take_screenshot → "S3-27-tasks-admin-view.png"
  ```
- **Attendu** : L'admin voit potentiellement plus de taches qu'un agent standard
- **Tests supplementaires** :
  - `[P1]` Si des taches d'autres utilisateurs existent, elles sont visibles
  - `[P2]` Un indicateur montre le createur de chaque tache
- **Priorite** : P1

---

### Phase 6 : CRM (etapes 28-32)

#### Etape 28 : Naviguer vers le CRM
- **Action** : Cliquer sur le lien CRM
- **Chrome MCP** :
  ```
  click [data-testid="nav-link-crm"]
  wait_for [data-testid="crm-page"] visible (timeout 5s)
  take_screenshot → "S3-28-crm-page.png"
  ```
- **Attendu** : Page CRM visible avec liste de contacts
- **Priorite** : P0

#### Etape 29 : Creer un contact
- **Action** : Cliquer sur "Creer un contact" et remplir le formulaire
- **Chrome MCP** :
  ```
  click [data-testid="crm-create-contact-btn"]
  wait_for [data-testid="crm-contact-name-input"] visible (timeout 3s)
  javascript_tool :
    const nameInput = document.querySelector('[data-testid="crm-contact-name-input"]');
    const emailInput = document.querySelector('[data-testid="crm-contact-email-input"]');
    const setterInput = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
    setterInput.call(nameInput, 'Jean-Marc Prestataire IT');
    nameInput.dispatchEvent(new Event('input', { bubbles: true }));
    setterInput.call(emailInput, 'jm.presta@example.com');
    emailInput.dispatchEvent(new Event('input', { bubbles: true }));
  wait 100ms
  click [data-testid="crm-contact-save-btn"]
  wait 2s
  take_screenshot → "S3-29-contact-created.png"
  ```
- **Attendu** : Contact cree et visible dans la liste
- **Priorite** : P0

#### Etape 30 : Verifier le contact dans la liste
- **Action** : Chercher le contact cree
- **Chrome MCP** :
  ```
  javascript_tool :
    const contacts = document.querySelectorAll('[data-testid="crm-contact-item"]');
    const found = Array.from(contacts).some(c => c.textContent.includes('Jean-Marc'));
    return { contactCount: contacts.length, found };
  ```
- **Attendu** : Le contact "Jean-Marc Prestataire IT" est present
- **Priorite** : P0

#### Etape 31 : Tester l'isolation multi-tenant
- **Action** : Verifier que l'admin ne voit que les contacts de son organisation
- **Precondition (fixture, B-333/B-384 du 05/09/2026)** : un contact TEMOIN existe dans une
  AUTRE organisation, cree avant la campagne par un compte de l'organisation B :
  `POST /api/crm/contacts` avec `first_name: "Temoin"`, `last_name: "OrgB-ISOLATION"`.
  Sans ce temoin, l'etape ne fait que compter et ne peut jamais rougir.
- **Chrome MCP** :
  ```
  javascript_tool :
    const contacts = Array.from(document.querySelectorAll('[data-testid="crm-contact-item"]'));
    const temoinVisible = contacts.some(c => c.textContent.includes('OrgB-ISOLATION'));
    return { contactCount: contacts.length, temoinVisible, safe: !temoinVisible };
  ```
- **Verdict API** : `GET /api/crm/contacts` (jeton admin de l'org A) ne contient aucun
  contact dont `organisation_id` differe de celle de l'admin, et aucun `OrgB-ISOLATION`.
- **Attendu** : `safe === true` et verdict API vide de l'org B : pas de fuite cross-organisation
- **Priorite** : P0

#### Etape 32 : Verifier la visibilite etendue admin sur le CRM
- **Action** : L'admin doit voir les contacts crees par tous les agents de son organisation
- **Chrome MCP** :
  ```
  javascript_tool :
    const contacts = document.querySelectorAll('[data-testid="crm-contact-item"]');
    return { totalContacts: contacts.length };
  take_screenshot → "S3-32-crm-admin-view.png"
  ```
- **Attendu** : Tous les contacts de l'organisation sont visibles
- **Priorite** : P1

---

### Phase 7 : Board de decision (etapes 33-36)

#### Etape 33 : Naviguer vers le Board
- **Action** : Cliquer sur le lien Board
- **Chrome MCP** :
  ```
  click [data-testid="nav-link-board"]
  wait_for [data-testid="board-page"] visible (timeout 5s)
  take_screenshot → "S3-33-board-page.png"
  ```
- **Attendu** : Page Board visible avec panneau de deliberation
- **Priorite** : P0

#### Etape 34 : Lancer une deliberation strategique
- **Action** : Poser une question au Board (5 conseillers IA)
- **Chrome MCP** :
  ```
  wait_for [data-testid="board-panel"] visible
  javascript_tool :
    const input = document.querySelector('[data-testid="board-question-input"]');
    const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
    setter.call(input, 'Faut-il migrer notre messagerie Exchange vers une solution souveraine ?');
    input.dispatchEvent(new Event('input', { bubbles: true }));
  click [data-testid="board-submit-btn"]
  wait_for [data-testid="board-result"] visible (timeout 60s)
  take_screenshot → "S3-34-board-deliberation.png"
  ```
- **Attendu** : Deliberation lancee, resultats affiches avec avis des conseillers
- **Tests supplementaires** :
  - `[P0]` Le resultat n'est pas vide
  - `[P1]` Plusieurs conseillers ont repondu (cartes visibles)
  - `[P2]` Un resume/synthese est affiche
- **Priorite** : P0

#### Etape 35 : Verifier les cartes conseillers
- **Action** : Compter et lire les avis individuels
- **Chrome MCP** :
  ```
  javascript_tool :
    const cards = document.querySelectorAll('[data-testid="board-advisor-card"]');
    return {
      advisorCount: cards.length,
      advisors: Array.from(cards).map(c => c.textContent.substring(0, 100))
    };
  take_screenshot → "S3-35-board-advisors.png"
  ```
- **Attendu** : 5 cartes conseillers avec des avis distincts
- **Tests supplementaires** :
  - `[P1]` 5 conseillers presents
  - `[P1]` Les avis ne sont pas identiques (diversite des perspectives)
- **Priorite** : P1

#### Etape 36 : Verifier que le Board ne revele pas de donnees cross-org
- **Action** : S'assurer que la deliberation ne fait pas reference a des donnees d'autres organisations
- **Chrome MCP** :
  ```
  javascript_tool :
    // B-384 (05/09/2026) : `board-result` n'existe pas cote Server, les avis
    // vivent dans `board-advisor-card` ; et sans temoin de l'org B (etape 31),
    // aucune fuite ne pouvait etre constatee.
    const cartes = Array.from(document.querySelectorAll('[data-testid="board-advisor-card"]'));
    const texte = cartes.map(c => c.textContent).join(' ');
    const fuite = texte.includes('OrgB-ISOLATION');
    return { cartes: cartes.length, extrait: texte.substring(0, 300), fuite, safe: cartes.length > 0 && !fuite };
  ```
- **Precondition** : le temoin `OrgB-ISOLATION` de l'etape 31 existe, et la question posee a
  l'etape 34 demande explicitement « liste mes contacts et leurs societes ».
- **Attendu** : `safe === true` : des avis sont rendus et aucun ne cite le temoin de l'org B
- **Priorite** : P1

---

### Phase 8 : Skills (etapes 37-39)

#### Etape 37 : Naviguer vers les Skills
- **Action** : Cliquer sur le lien Skills
- **Chrome MCP** :
  ```
  click [data-testid="nav-link-skills"]
  wait_for [data-testid="skills-page"] visible (timeout 5s)
  take_screenshot → "S3-37-skills-page.png"
  ```
- **Attendu** : Page Skills visible avec liste
- **Priorite** : P0

#### Etape 38 : Verifier la liste des skills disponibles
- **Action** : Compter et lister les skills
- **Chrome MCP** :
  ```
  javascript_tool :
    const skills = document.querySelectorAll('[data-testid="skill-item"]');
    return {
      count: skills.length,
      names: Array.from(skills).map(s => s.textContent.substring(0, 50))
    };
  take_screenshot → "S3-38-skills-list.png"
  ```
- **Attendu** : Au moins 1 skill disponible
- **Tests supplementaires** :
  - `[P0]` La liste n'est pas vide
  - `[P1]` Chaque skill a un nom et un bouton d'execution
- **Priorite** : P0

#### Etape 39 : Executer un skill
- **Action** : Cliquer sur le bouton d'execution du premier skill
- **Chrome MCP** :
  ```
  click [data-testid="skill-execute-btn"]:first-of-type
  wait_for [data-testid="skill-result"] visible (timeout 30s)
  take_screenshot → "S3-39-skill-executed.png"
  ```
- **Attendu** : Le skill s'execute et affiche un resultat
- **Tests supplementaires** :
  - `[P0]` Pas d'erreur 500
  - `[P1]` Le resultat n'est pas vide
  - `[P1]` Pas de crash du frontend
- **Priorite** : P1

---

### Phase 9 : Retour admin et verification finale (etapes 40-42)

#### Etape 40 : Retour sur /admin - Verifier les KPIs mis a jour
- **Action** : Revenir au dashboard admin et verifier que les KPIs refletent l'activite
- **Chrome MCP** :
  ```
  click [data-testid="nav-link-admin"]
  wait_for [data-testid="admin-dashboard"] visible (timeout 5s)
  javascript_tool :
    const conversations = document.querySelector('[data-testid="admin-kpi-conversations"]')?.textContent;
    const messages = document.querySelector('[data-testid="admin-kpi-messages"]')?.textContent;
    return { conversations, messages };
  take_screenshot → "S3-40-kpis-updated.png"
  ```
- **Attendu** : Les KPIs ont augmente (conversations et messages)
- **Tests supplementaires** :
  - `[P1]` Le nombre de conversations a augmente par rapport a l'etape 9
  - `[P1]` Le nombre de messages a augmente par rapport a l'etape 9
- **Priorite** : P1

#### Etape 41 : Verifier les logs d'audit pour la session complete
- **Action** : Consulter les logs et verifier que toutes les actions admin sont tracees
- **Chrome MCP** :
  ```
  wait_for [data-testid="admin-audit-logs"] visible
  javascript_tool :
    const logs = document.querySelectorAll('[data-testid="admin-audit-log-item"]');
    const logTexts = Array.from(logs).slice(0, 10).map(l => l.textContent);
    return { recentLogs: logTexts };
  take_screenshot → "S3-41-audit-final.png"
  ```
- **Attendu** : Logs contenant au minimum : login, changement role, desactivation utilisateur
- **Tests supplementaires** :
  - `[P0]` Le login admin est trace
  - `[P1]` Le changement de role (etape 11) est trace
  - `[P1]` La desactivation (etape 12) est tracee
  - `[P2]` Les actions chat/taches/crm sont tracees
- **Priorite** : P1

#### Etape 42 : Reactiver l'utilisateur desactive (nettoyage)
- **Action** : Reactiver l'utilisateur desactive a l'etape 12 pour remettre le systeme en etat
- **Chrome MCP** :
  ```
  javascript_tool :
    const rows = document.querySelectorAll('[data-testid="admin-user-row"]');
    rows.forEach(row => {
      const toggle = row.querySelector('[data-testid="admin-user-toggle-active"]');
      const email = row.querySelector('td:nth-child(2)')?.textContent;
      // Chercher l'utilisateur desactive (pas admin)
      if (email && !email.includes('admin@') && toggle) {
        // Verifier si inactif via un indicateur visuel
        const statusCell = row.querySelector('td:nth-child(4)');
        if (statusCell && statusCell.textContent.toLowerCase().includes('inactif')) {
          toggle.click();
        }
      }
    });
    return 'cleanup attempted';
  wait 2s
  take_screenshot → "S3-42-cleanup-done.png"
  ```
- **Attendu** : L'utilisateur est reactif, systeme remis en etat propre
- **Tests supplementaires** :
  - `[P0]` L'utilisateur est a nouveau actif
  - `[P1]` Le KPI "utilisateurs actifs" revient a la valeur initiale
- **Priorite** : P1

---

## Resume des tests par priorite

| Priorite | Nombre estimatif | Description |
|----------|-----------------|-------------|
| P0 | ~65 | Bloquants release : auth, RBAC, CRUD, XSS, isolation |
| P1 | ~75 | Importants : persistence, audit, feedback UX, KPIs |
| P2 | ~30 | Nice to have : coloration syntaxique, indicateurs croisees |
| **TOTAL** | **~170** | |

## Couverture fonctionnelle

| Module | Etapes | Tests P0 |
|--------|--------|----------|
| Auth + Charte | 1-6 | 6 |
| RBAC Admin | 7-8 | 4 |
| Admin Dashboard | 9-15 | 12 |
| Chat | 16-22 | 8 |
| Taches | 23-27 | 5 |
| CRM | 28-32 | 6 |
| Board | 33-36 | 4 |
| Skills | 37-39 | 3 |
| Verification finale | 40-42 | 3 |

## Notes d'execution

- **Ordre** : Suivre les etapes dans l'ordre (les etapes 40-42 dependent des etapes precedentes)
- **Pre-conditions** : S'assurer qu'au moins 2 autres utilisateurs existent avant de commencer
- **Nettoyage** : L'etape 42 remet le systeme en etat. Si le test est interrompu, penser a reactiver manuellement les utilisateurs desactives
- **Timeout Board** : La deliberation (etape 34) peut prendre jusqu'a 60s. Ne pas interrompre
- **Screenshots** : 15 captures d'ecran prevues. Les stocker dans un dossier dedie pour le rapport
