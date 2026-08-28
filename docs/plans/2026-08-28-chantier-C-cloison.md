# Chantier C — Le cloisonnement pour les professions au secret

> **NO-GO de la relecture sur la V1 (28/08). Cinq corrections, dont une qui
> touche le livrable d'arbitrage.**
>
> ## 1. Le formateur n'est PAS le même défaut. Je l'ai écrit à tort
>
> J'avais présenté sa convocation « Atelier Martin » portant les dates de la
> Mairie de Manosque comme la seconde preuve de la fuite. C'est faux :
>
> - il travaillait en **conversation libre**, où le cloisonnement ne joue aucun
>   rôle — un mode « cabinet » n'y changerait rien ;
> - ces dates n'apparaissent nulle part ailleurs dans son propre rapport ;
> - il qualifie lui-même la ligne de « prérequis **inventé** ».
>
> Hallucination du modèle local, très probablement. **La synthèse de campagne a
> été corrigée** : la faire porter au chantier C aurait promis une correction
> qu'il n'apporte pas.
>
> ## 2. C3 n'était pas au bon étage — il y a DEUX portes, j'en visais une
>
> | Porte | C3 tel qu'écrit |
> |---|---|
> | RAG (`_get_memory_context` → `include_global`) | fermée |
> | `read_contact` / `_cloison_contacts` | **grande ouverte** |
>
> Au premier tour, le modèle n'a pas d'outil : il répond avec le RAG. Au second,
> `read_contact("Valette")` depuis Rousset rend la fiche. Fermer la recherche
> vectorielle pendant que l'outil SQL recrache le secret ne protège rien.
>
> Le bon étage n'est pas un booléen Qdrant : c'est une **politique de
> conversation**, lue par les deux lecteurs.
>
> ## 3. Le vrai trou de C2 est `ProjectCreate`, pas `ContactUpdate`
>
> `POST /projects` (`memory.py:801-809`) pose une ligne au défaut `global`, sans
> champ `scope`. C'est ainsi que l'avocat lit « Présente dans le projet
> Valette » : l'**entité projet**, pas le fichier — le fichier, lui, est bien
> `scope="project"` à l'upload.
>
> Corriger les contacts sans les projets laisse la fuite.
>
> Vérifié aussi : ajouter `scope` à `ContactUpdate` ne casse rien (VCF, CRM,
> Sheets et `EntitySuggestion` ne passent pas par ce schéma), mais un schéma
> sans écran est un contrôle mort — `ContactCreate.scope` existe déjà et
> `ContactModal` ne l'envoie pas.
>
> ## 4. C3 sans C2 est PIRE que rien
>
> Toute fiche créée depuis l'écran est globale. Mode cabinet allumé, conversation
> Rousset : plus de Valette — **et plus de Mme Rousset non plus**, dont le secret
> médical vit dans sa propre fiche globale.
>
> « Tu vides le dossier de sa propre personne. »
>
> Donc : **pas de migration** (un contact peut servir deux affaires ; le coller
> au premier dossier serait présomptueux), mais à l'activation du mode, un écran
> qui propose de rattacher les fiches liées à un seul projet. Jamais en silence.
>
> ## 5. C1 ne doit pas anticiper une cloison qui n'existe pas
>
> Renommer en « Dossier de cette conversation » pendant que les fiches fuient
> remplace un mensonge étroit par un mensonge large. C1 passe **en dernier**, et
> dit la vérité du moment : fichiers du projet, carnet partagé.
>
> ## L'ordre retenu
>
> **C2** (contacts *et* projets, schéma + écran + promotion réelle) → **C3**
> (politique unique, RAG *et* SQL) → **C1** (renommage, une fois la cloison
> vraie).
>
> ## Les chemins hors périmètre, nommés
>
> `POST /api/memory/search` n'a aucun `scope` (l'avocat s'en est servi, l'écran
> *Retrouver* aussi) ; `GET /api/files/` ne filtre pas ; `list_calendar_events`,
> `search_invoices` et les mails n'ont pas de périmètre. Ce chantier ne les
> ferme pas — il ne prétendra donc pas que le cloisonnement est complet.
>
> ---
>
> La V1 est conservée ci-dessous.

---

# V1 (NO-GO) — design soumis à relecture AVANT code

## Le constat

Deux personas, deux métiers, deux surfaces différentes, **la même fuite** :

- **L'avocat** (persona 04) : dans le dossier Rousset, THÉRÈSE lui ressort la
  lettre de licenciement d'un autre client **et** le traitement anxiolytique de
  sa cliente. « C'est le secret professionnel. Un associé qui ouvre Rousset n'a
  pas à lire Valette. »
- **Le formateur** (persona 06) : une convocation Qualiopi pour « Atelier
  Martin » sort avec un prérequis daté du 8-9 juillet — les dates de la
  **Mairie de Manosque**, un autre client, absent de la conversation. « Un
  papier qui mélange deux clients, je ne le sors pas. »

## Le mécanisme, vérifié

| Étape | Code |
|---|---|
| Tout contact créé depuis l'écran est **global** | `routers/memory.py:401` — `scope=request.scope or "global"` |
| `ContactModal` n'offre **aucun** choix de périmètre | `components/memory/ContactModal.tsx` |
| Ses notes sont indexées **avec la fiche** | `memory_tools.py` — `text_parts.append(f"Notes: {contact.notes}")` |
| La recherche du chat ne passe pas `include_global` | `chat.py:697-706` |
| …donc le défaut s'applique | `qdrant.py:240` — `include_global: bool = True` |

Une conversation rattachée au dossier Rousset reçoit donc les souvenirs de
Rousset **plus tous les souvenirs globaux**, fiches et notes comprises.

## Ce n'est pas un bug, et c'est ce qui le rend difficile

Le code l'assume : « Les contacts GÉNÉRAUX restent visibles partout, comme les
documents globaux. » La cloison 0.43 a été pensée pour un entrepreneur qui a un
carnet d'adresses commun à ses dossiers. Pour lui, c'est le bon comportement.

Le défaut est ailleurs : **l'étendue réelle de la cloison n'est annoncée nulle
part, et le seul libellé qui en parle induit en erreur.**

```tsx
<span className="sr-only">Documents consultés par cette conversation</span>
aria-label="Documents consultés par cette conversation"
```

Le sélecteur parle de **documents**. Les fichiers sont cloisonnés. Les fiches
contacts, non. Personne ne le dit.

## Ce que je propose, en trois gestes séparables

### C1 — Renommer le sélecteur (petit, sûr)

Il ne dit pas ce qu'il fait. Deux options :
- décrire ce qui est réellement cloisonné (« Dossier de cette conversation »),
- ou garder le nom et étendre le cloisonnement à ce qu'il promet (c'est C3).

Je penche pour renommer d'abord : c'est un mensonge en attendant, et le
renommage ne casse rien.

### C2 — Le périmètre d'un contact devient un choix visible

`ContactUpdate` n'a **aucun** champ `scope` (`schemas.py:160`) : le code promet
pourtant de pouvoir « promouvoir » un contact (`memory_tools.py:228`). Ce
contrôle n'existe pas.

Proposition : exposer le périmètre à la création et à l'édition, avec un défaut
explicite (global, comme aujourd'hui — ne pas changer le comportement en
silence), et permettre de rattacher une fiche à un dossier.

### C3 — Un mode « cabinet » (la vraie question produit)

Un réglage qui fait passer `include_global=False` pour la recherche du chat :
aucune fuite entre dossiers, au prix de ressaisir les contacts communs.

**Pour un avocat, c'est un prix qu'il paiera.** Pour l'artisan, ce serait une
punition — d'où un réglage, pas un changement de défaut.

## Questions au relecteur

1. **C3 est-il au bon étage ?** `include_global` est un paramètre de
   `qdrant.async_search`. Le passer depuis `chat.py` couvre le chat. Mais la
   génération de documents (le cas du formateur) passe-t-elle par le même
   chemin, ou par un autre contexte ?
2. **Le cas du formateur est-il vraiment le même mécanisme ?** Son document
   sort avec les dates d'un autre client. Est-ce le RAG global, ou le contexte
   de conversation, ou l'historique du modèle ?
3. **C2 : changer `ContactUpdate` touche-t-il des chemins que je ne vois pas**
   (import VCF, sync CRM, Sheets) ?
4. **Que fait-on des contacts déjà créés** en global ? Une migration serait
   présomptueuse ; ne rien faire laisse la fuite pour l'existant.
5. Y a-t-il un **troisième chemin** de fuite que la campagne n'a pas trouvé ?

## Ce que ce chantier ne fait pas

- Il ne change pas le défaut (global) sans réglage explicite.
- Il ne touche pas au cloisonnement des documents, qui fonctionne.
