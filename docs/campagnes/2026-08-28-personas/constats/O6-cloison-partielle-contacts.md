# O6 - La cloison arrête les documents, pas les fiches contacts

**Vécu par le persona 04 (l'avocat)**, finding F5 : « Dans le dossier Rousset,
on m'a ressorti la lettre de licenciement Valette et le traitement anxiolytique
de Mme Rousset dans la même réponse. »

- **Gravité** : bloquant pour les professions au secret ; majeur sinon
- **Nature** : defaut_app (conception + libellé), pas un bug
- **Source** : `routers/memory.py:401`, `services/qdrant.py:240` et `:337-339`,
  `routers/chat.py:697-706`, `components/chat/ConversationProjectPicker.tsx:139-141`

## L'enchaînement, vérifié

1. **Tout contact créé depuis l'écran est GLOBAL, sans le dire.**
   ```python
   scope=request.scope or "global",     # routers/memory.py:401
   ```
   `ContactModal.tsx` n'offre **aucun** choix de périmètre. L'utilisateur ne
   sait pas qu'il vient de ranger une fiche dans un espace visible partout.

2. **Les notes du contact sont indexées avec la fiche.**
   `memory_tools.py` : `text_parts.append(f"Notes: {contact.notes}")`. C'est
   précisément là que l'avocat écrit le secret : « traitement pour anxiété
   prescrit par le Dr Klein ».

3. **La recherche du chat réinjecte le global, même rattachée à un projet.**
   ```python
   results = await qdrant.async_search(          # chat.py:697-706
       query=user_message, scope=scope, scope_id=scope_id,
       conversation_id=conversation_id,
   )                                             # include_global NON passé
   ```
   ```python
   include_global: bool = True,                  # qdrant.py:240 — le défaut
   ```

Une conversation rattachée au dossier Rousset reçoit donc : les souvenirs de
Rousset **plus tous les souvenirs globaux**, fiches contacts et notes comprises.

## Ce n'est pas un bug, et c'est ce qui le rend grave

Le code l'assume, en toutes lettres : « Les contacts GÉNÉRAUX restent visibles
partout, comme les documents globaux. » La cloison 0.43 a été pensée pour un
entrepreneur qui a un carnet d'adresses commun à ses dossiers. C'est un choix
raisonnable pour cet utilisateur.

Le défaut est ailleurs : **l'étendue réelle de la cloison n'est annoncée nulle
part, et le seul libellé qui en parle induit en erreur.**

```tsx
<span className="sr-only">Documents consultés par cette conversation</span>
aria-label="Documents consultés par cette conversation"
```

Le sélecteur parle de **documents**. Un utilisateur qui le règle sur « projet
Rousset » en conclut, légitimement, que la conversation est cloisonnée. Les
fichiers le sont. Les fiches contacts, non. Personne ne le lui dit.

L'avocat l'a formulé exactement : « Le sélecteur du chat cloisonne les
*fichiers* ; les fiches contacts, où j'écris le secret, passent quand même. »

## Pourquoi ça ne peut pas rester tel quel

Deux des dix personas ont le secret professionnel pour ligne rouge, un
troisième (la magistrate) traque précisément les promesses trop larges. Pour
eux, la question n'est pas « est-ce pratique » mais « est-ce que je peux mettre
un dossier là-dedans ». Aujourd'hui : non, et l'écran laisse croire que oui.

## Correctifs, du moins cher au plus structurant

1. **Renommer le sélecteur.** Il ne dit pas ce qu'il fait. « Documents
   consultés » doit devenir ce qui est réellement cloisonné, ou le
   cloisonnement doit s'étendre à ce que le nom promet.
2. **Choix du périmètre à la création d'un contact**, avec un défaut explicite.
   Un contact rangé dans un dossier ne doit pas être un accident.
3. **Un mode « cabinet »** (à décider, mais c'est la vraie question produit) où
   `include_global=False` : aucune fuite entre dossiers, au prix de ressaisir
   les contacts communs. Pour un avocat, c'est un prix qu'il paiera.

## Le test qui manque

Un test d'étanchéité qui écrit un secret dans les notes d'un contact global,
puis interroge une conversation rattachée à un AUTRE projet et échoue si le
secret remonte. Aujourd'hui, la suite ne couvre que les documents.

---

# Corroboration par le persona 06 (le formateur), autre métier, autre chemin

L'avocat avait vu la fuite dans une **réponse de chat**. Le formateur la
retrouve dans un **document produit**, ce qui est pire : le papier part chez le
client.

Il fait générer les pièces d'une session « Atelier Martin ». La convocation
sort avec ce prérequis :

> « Avoir suivi la session Excel débutant (**8-9 juillet 2026**). »

Ces dates sont celles de la **Mairie de Manosque** — un autre client, enregistré
séparément, absent de cette conversation. Elles atterrissent sur un document
Atelier Martin.

## Pourquoi c'est le même défaut

Le mécanisme est identique à celui décrit plus haut : le contexte mémoire
injecté dans la génération contient les souvenirs `global`, et **tout contact
créé depuis l'écran est global par défaut** (`memory.py:401`). Le document est
rédigé avec, sans que rien ne cloisonne.

Deux personas, deux métiers, deux surfaces différentes (réponse de chat vs
document Word), **même fuite**. Ce n'est pas un accident de génération : c'est
la conséquence prévisible d'une cloison qui ne couvre que les fichiers.

## Ce que ça coûte à celui qui le subit

Le formateur est certifié Qualiopi et attend son audit de surveillance. Son
verdict : « Un papier qui mélange deux clients, je ne le sors pas. »

Pour un organisme de formation, une pièce d'audit qui contient les données d'un
autre client n'est pas une gêne : c'est un écart constatable, et un manquement
RGPD.
