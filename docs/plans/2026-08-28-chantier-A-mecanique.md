# Chantier A-mécanique — design v1, soumis à relecture AVANT code

Sorti du chantier A après NO-GO des deux relecteurs. Deux sujets : le garde sur
la recherche web, et le rejeu du 401 après relance du moteur.

**Rien n'est codé.**

---

## A2 — La recherche web

### Ce que la V1 proposait, et pourquoi elle est morte

Ajouter `web_search` aux outils soumis à confirmation. Les relecteurs ont montré
que ça casse quatre choses, dont une **démontrée à l'exécution** :

1. `/confirm-tool` route vers `execute_workspace_tool`, qui ne connaît pas
   `web_search` → `Outil inconnu : web_search`. La recherche cesserait de
   fonctionner.
2. `ToolConfirmationCard.tsx:73` est un **binaire** : tout ce qui n'est pas
   `create_calendar_event` s'affiche « Confirmer l'envoi de l'email », avec les
   champs À / Objet / Message (vides) et un bouton **Envoyer**.
3. Après confirmation, le frontend colle `response.result` comme message
   assistant. Pour un envoi, c'est « Email envoyé ». Pour une recherche, ce
   serait le JSON brut, **sans que le modèle l'exploite**.
4. Board (`board.py`), recherche approfondie (`deep_research.py`) et Atelier
   (`agents/tools.py`) appellent le service **directement** : 18 appels, zéro
   lecture du réglage. Ils contourneraient le gate.

### Le constat qui change tout

Le produit a **déjà** la préférence `web_search_enabled`, persistée en base.
Elle n'est lue qu'à un seul endroit : `chat.py:2271`, pour décider si l'outil
est proposé au modèle.

Autrement dit, **le garde est au mauvais étage**. Il est posé sur la liste
d'outils du chat, alors qu'il devrait être posé sur la sortie réseau.

Le consentement cloud existant (`lib/consent.ts`) ne peut pas servir : il vit
dans le `localStorage` du frontend, donc invisible du backend où tournent Board,
la recherche approfondie et les agents.

### Ce que je propose

**Descendre le garde dans le service de recherche.** `web_search.py` vérifie la
préférence avant tout appel réseau et lève une erreur explicite si elle est
refusée.

Conséquence : **tous les appelants sont couverts par construction**, y compris
ceux qu'on n'a pas encore écrits. Aucun routeur de confirmation à créer, aucune
carte à généraliser, aucune reprise de génération à inventer.

C'est aussi ce que les personas demandaient. L'écrivaine : « je voulais de la
recherche, je voulais juste le savoir. » Une carte à chaque recherche serait une
gêne ; un accord une fois donné, non.

### La question que je ne tranche pas seul

Le défaut actuel est **allumé** (`chat.py:2271` : `else True`).

| | Option 1 — garder allumé | Option 2 — éteint tant que non décidé |
|---|---|---|
| Comportement | inchangé ; l'écran le dit désormais (livré dans A-texte) | premier appel refusé, message clair, l'utilisateur autorise une fois |
| Pour l'avocat / la magistrate | insuffisant : ils veulent décider | c'est exactement ce qu'ils demandent |
| Risque | on garde un défaut que trois personas ont jugé éliminatoire | on change le comportement d'une installation existante, sans trace du choix passé |
| Effet sur Board / Deep Research | couverts, mais toujours allumés | couverts, et refusés tant que rien n'est accordé |

**Je penche pour l'option 2**, avec un message d'erreur qui dit exactement où
activer. Mais elle change le comportement au premier usage, et je veux un avis
avant d'y toucher.

**Questions au relecteur :**

1. Le garde dans `web_search.py` couvre-t-il vraiment tous les chemins ? Y
   a-t-il un appelant qui court-circuite le service (client HTTP direct,
   provider avec recherche intégrée) ?
2. **L'ancrage Google de Gemini** (`gemini.py:216`, `enable_grounding=True`) ne
   passe PAS par ce service : c'est le fournisseur qui cherche. Est-ce dans le
   périmètre de ce lot, ou une dette à écrire ? Je penche pour la dette écrite —
   le couper reviendrait à dégrader Gemini sans le dire.
3. Option 1 ou 2 sur le défaut ?
4. Que faire de l'erreur côté chat : le modèle doit-il la voir (et l'expliquer),
   ou faut-il un événement dédié qui affiche une invite à autoriser ?

---

## A6 — Le rejeu du 401 après relance du moteur

### Le fait

`core.ts:93-110` charge le token **une fois**. Aucune ligne ne traite un 401.
Tauri relance pourtant le sidecar (jusqu'à 3 fois, `lib.rs:375`), et chaque
démarrage génère un **nouveau** token. Après relance, tout retourne 401 pendant
que le bandeau annonce que le moteur est reparti. L'écrivaine a fini sa session
ainsi et a cessé d'essayer.

### Ce que la relecture a corrigé dans mon idée initiale

- Je voulais **exclure le SSE** du rejeu. C'est faux : le 401 du middleware
  d'authentification arrive **avant** l'entrée dans la route (`main.py:700`),
  donc aucune génération ni aucun outil n'a démarré. Rejouer est sûr **tant
  qu'aucun octet du flux n'a été lu**.
- Il ne faut **pas** rejouer « tout 401 » : Gmail, Groq et Google Sheets en
  renvoient aussi, pour des raisons métier. Il faut un **marqueur propre au
  middleware** — un en-tête de réponse.
- `sidecar-status: running` est émis dès le `spawn` (`lib.rs:303`), avant que
  FastAPI ne soit prêt : recharger sur cet événement ne sert à rien. Il faut une
  sonde de disponibilité.

### Ce que je propose

1. **Backend** : le middleware d'auth ajoute un en-tête distinctif sur ses 401
   (`X-Therese-Auth: session-token`). C'est lui, et lui seul, qui autorise un
   rejeu.
2. **Frontend, dans `apiFetch`** : si la réponse est 401 **et** porte cet
   en-tête **et** que la requête n'a pas encore été rejouée → vider le token,
   le recharger par un `fetch` **brut** (sinon récursion), rejouer **une fois**.
3. **Concurrence** : mémoriser le token utilisé par chaque requête. Si le token
   global a déjà changé quand le 401 arrive, rejouer **sans** relancer un
   rafraîchissement. Promesse partagée pour le rafraîchissement lui-même.
4. **Ne pas masquer l'échec** : `initializeAuth()` avale aujourd'hui son
   exception (`catch { console.warn }`). Le rejeu doit savoir qu'il a échoué.
5. Respecter l'`AbortSignal`, et **un seul** rejeu par requête.

### Questions au relecteur

1. L'en-tête est-il le bon marqueur, ou faut-il un code d'erreur dans le corps
   (`code: "UNAUTHORIZED"` existe déjà — est-il propre au middleware, ou
   d'autres routes l'émettent-elles ?) ?
2. Le rejeu d'un POST de chat est-il vraiment sans effet de bord ? Le message
   utilisateur a-t-il déjà été persisté au moment du 401 ?
3. Faut-il aussi recharger le token sur une sonde de disponibilité après
   `sidecar-status`, ou le rejeu sur 401 suffit-il comme filet ?

---

## Ce que ce chantier ne fait PAS

- Il ne crée pas le registre `ToolPolicy` proposé par la relecture. C'est la
  bonne cible, mais elle dépasse ce lot : elle touche la carte, le routeur, la
  reprise de génération et les annotations MCP. À écrire comme chantier F.
- Il ne touche pas à l'ancrage Gemini (voir question 2).
- Il ne touche pas au cloisonnement (chantier C).

## Vérification prévue

TDD strict, preuve par sabotage par copie de fichier, six gates dans l'ordre,
puis relecture du diff.
