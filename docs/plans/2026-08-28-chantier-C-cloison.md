# Chantier C — Le cloisonnement pour les professions au secret

Design soumis à relecture AVANT code. **Rien n'est codé.**

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
