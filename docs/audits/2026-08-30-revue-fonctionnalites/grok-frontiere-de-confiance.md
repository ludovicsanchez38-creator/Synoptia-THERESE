# Revue Grok — la frontière de confiance (30/08/2026, passe 4)

> Angle : ce que l'application accepte de l'extérieur. Injection par le
> contenu, chemins, actions qui partent sans confirmation, secrets dans les
> journaux, échappement à l'affichage.
>
> **C'est la passe la plus grave de la journée.** Le trou n'est pas un défaut
> isolé mais une CHAÎNE : un contenu tiers entre dans le prompt système, et la
> liste des outils qui exigent une confirmation ne compte que deux noms.

### 1. Un fichier, un extrait indexé ou une page web se font passer pour la consigne

**Fichiers.** `src/backend/app/routers/chat.py` ~2112 et ~393 ; `src/backend/app/services/llm.py` ~771.

**Tu crois** joindre un PDF, ou indexer le dossier d'un client, pour que le modèle *consulte* ce contenu.

**Tu obtiens** ce contenu collé dans le prompt système, au même étage que « Tu es THÉRÈSE ».

`check_prompt_safety` ne lit que `user_message` (« Résume ce document » passe). Le fichier est formaté avec des `--- FICHIER ---` / `--- FIN DU FICHIER ---` que le fichier peut refermer lui-même, plus le **chemin absolu**, puis fusionné dans `memory_context`. `prepare_context` l'ajoute au système.

Même collage sans enveloppe pour les extraits Qdrant (`_get_memory_context`), les snippets Brave/DuckDuckGo, le Board, et les 120 caractères de `read_emails`.

`sanitize_for_context` (marqueurs `[Source:]`, cassage des `---`) n'existe qu'à deux endroits : résumé d'e-mails et liste des factures. `read_file` pose un avertissement JSON. La pièce jointe du composeur, non. `BLOC_PIECES_JOINTES` dit même au modèle de traiter ces blocs comme disponibles.

**Reproduire.** Fichier `consigne.txt` qui ferme le délimiteur puis ordonne `send_email` / `web_search`. Joindre, « Résume ce document. » Variante : l'indexer dans un projet, poser une question assez proche pour que Qdrant le ramène.

---

### 2. Sans carte, l'action part. La liste des outils sensibles a deux noms.

**Fichiers.** `src/backend/app/services/tool_confirmations.py` ligne 16 ; `src/backend/app/routers/chat.py` ~2833 et ~2893 ; `src/backend/app/services/contexte_execution.py` ~50.

**Tu crois** que rien de sortant ne part sans carte. C'est vrai pour l'e-mail et le rendez-vous.

**Tu obtiens** un fail-open : pas dans `{send_email, create_calendar_event}`, ça s'exécute. `classe_de()` sait déjà qu'un outil MCP inconnu est une mutation externe, mais ça ne sert qu'à l'annulation, pas à la carte.

| Outil | Effet | Packagée ? |
|---|---|---|
| `web_search` | La requête (donc tes extraits, tes mails) part chez Brave ou DuckDuckGo. Défaut allumé. | Oui |
| `browser_navigate` | Navigation, clic, formulaire. Y compris `http://127.0.0.1:17293/api/auth/token` (exempté, token en clair). CORS n'arrête pas un client HTTP côté serveur. | Non (playwright absent). Présent en `make dev` / preset Playwright. |
| `create_contact` / `create_project` | Écriture locale, sans relecture. | Oui |
| `generate_document` | Écrit un fichier (finding 3). | Oui |
| MCP fetch / Slack / WhatsApp / Brevo / Stripe / filesystem | GET, message, paiement, disque. Le gate ne reconnaît que le *nom* `send_email`. | Si tu as installé le preset |

Les presets le disent eux-mêmes (WhatsApp « en ton nom », Stripe/Playwright « high »). L'installation est un clic. Ensuite plus de carte.

**Reproduire (app telle quelle).** Finding 1 + un fichier qui ordonne `web_search` avec les adresses du contexte. Pas de carte. La requête part.

---

### 3. Le bac à sable des documents laisse pandas et `.save(variable)` hors du dossier de sortie

**Fichiers.** `src/backend/app/services/skills/code_executor.py` ~91 (pandas autorisé), ~459 (`open()` borné), ~813 (rewrite de `.save` **seulement** sur un littéral).

**Tu crois** que générer un tableur exécute du Python borné à `output_path`, dans un sous-processus sans tes secrets.

**Tu obtiens** `generate_document` sans carte, et du code (influencé par le finding 1) qui lit ton disque et écrit ailleurs.

`open()` est borné. `pandas.read_csv` / `to_excel` ne passent pas par `open()` : fichier local (`~/.therese/`, `~/.ssh/`) ou URL HTTP. Le sous-processus ne voit pas la mémoire du backend, il tourne sous **ton** utilisateur OS.

Le rewrite `.save("facture.docx")` → `.save(output_path)` rate :

```
chemin = "/Users/ludo/Documents/facture.xlsx"
wb.save(chemin)
```

`_ensure_save_call` s'arrête dès qu'un `.save(` existe. Le prompt du skill ne propose pas pandas. Le validateur l'accepte quand même.

**Reproduire.** Brief joint qui demande un Excel avec `import pandas` + `read_csv("https://…")` ou un `.save` via variable. « Fais-moi un Excel à partir de ce brief. » Pas de carte.

---

### 4. Les arguments d'outils, y compris un e-mail pas encore envoyé, atterrissent dans les journaux

**Fichiers.** `src/backend/app/routers/chat.py` ~2843 (outil sensible, **avant** la carte) et ~2893 ; `src/backend/app/core/logging_config.py` ~42.

**Tu crois** que les journaux masquent les secrets (correctif du 24/08 sur `sk-proj-`).

**Tu obtiens** le dictionnaire d'arguments en clair. `_mask_secrets` connaît `sk-`, `xai-`, `AIza`, `Bearer`. Pas `ya29.` (jeton Google), pas un mot de passe IMAP, pas le corps d'un mail. Annuler la carte ne retire pas la ligne déjà écrite. Ces fichiers finissent dans les rapports de bugs, le formateur le dit.

**Reproduire.** Demander un envoi, carte affichée, Annuler. Le journal a déjà destinataire, objet, corps.

---

### Confirmations (une ligne)

- **upload_file `../`** : confirme le finding de la passe 3. `files.py` 476 toujours `therese_dir / file.filename`.
- **HTML mail / Markdown chat** : rien de neuf. Sanitizers en place.

### Pas élevé

`requestExternalAction` est fail-open si le provider React manque. En production il enveloppe tout `ConversationCanvasPrototype`. Landmine pour une surface future, pas un trou actuel.

L'injection par un mail *lu* via `read_emails` est limitée à ~120 caractères. Le gros volume passe par la pièce jointe et l'index (finding 1).
