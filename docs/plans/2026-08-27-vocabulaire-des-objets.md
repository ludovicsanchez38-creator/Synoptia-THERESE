# Le vocabulaire des objets — diagnostic et proposition

Signalé par Dr_logic le 27/08 (D6). Il a un projet « site web l'egrenne »
avec plus de mille fichiers indexés. Quand il écrit « les documents
indexés », Thérèse part sur des factures.

Sa proposition : une syntaxe `{label: nom}` sur le modèle des directives
`[action: …]`, pour nommer explicitement ce dont on parle. Son exemple :
« décris-moi la structure de {label: Fichier-index.html}, indexé dans
{label: Dossier synchronisé} du projet {label: SWL} ».

Ce document a été soumis à une relecture adversariale, puis chaque
affirmation contestée a été revérifiée dans le code. Deux de mes constats
initiaux étaient faux et sont corrigés ci-dessous.

## Ce que le code dit

**1. Aucun outil ne permet d'atteindre les fichiers indexés.** La liste
complète de ce que le modèle peut appeler : `create_calendar_event`,
`create_contact`, `create_project`, `generate_document`,
`list_calendar_events`, `read_contact`, `read_emails`, `search_emails`,
`search_invoices`, `send_email`, `summarize_emails`. Rien pour les
documents.

**2. Le seul accès est une injection que le modèle subit.** Le contexte
trouvé lui est bien montré, sous un en-tête « ## Contexte mémoire: »
(`llm.py:757`) — ma première version disait qu'il l'ignorait, c'était faux.
Ce qu'il ne peut pas, c'est la déclencher, la paramétrer ou la relancer
autrement quand elle ne donne rien.

**3. Et quand elle ne donne rien, elle ne dit rien.** À vide,
`_get_memory_context` rend `None`, et le bloc disparaît entièrement du
prompt. Trois situations très différentes produisent alors exactement le
même silence : aucun document ne correspond, aucun document n'est
consultable dans ce périmètre, aucune recherche n'a eu lieu. Le modèle ne
peut pas les distinguer, l'utilisateur non plus.

**4. Un fichier ne peut pas être retrouvé par son nom.** L'indexation
vectorise le fragment de contenu seul ; le nom du fichier vit en métadonnée,
hors du vecteur. « La structure de Fichier-index.html » compare cette phrase
au contenu des fragments, où le nom n'apparaît le plus souvent pas.

**5. Le prompt envoyait activement vers les factures.** Le bloc « capacités »
ordonnait d'utiliser `search_invoices` « AU LIEU de dire que tu ne peux pas
chercher les documents locaux ». La description de l'outil, elle, était
correctement bornée depuis le début. *Corrigé le 27/08.*

## Le même manque, signalé trois fois

Le motif mérite d'être vu en entier, parce qu'il explique comment on en est
arrivé là.

| Quand | Ce que le testeur voit | Ce qu'on a corrigé |
|---|---|---|
| BUG-160, 0.43.1 | « je ne dispose d'aucun outil permettant de lire ce fichier » | les pièces jointes sont rejouées sur 3 tours |
| BUG-148, juillet | « je n'ai pas d'outil de recherche pour les documents locaux » | on ordonne au modèle d'utiliser les factures |
| D6, aujourd'hui | « les documents indexés » mène aux factures | — |

Les trois fois, la phrase du modèle était littéralement vraie. Les deux
premières fois, on a traité le cas particulier qui avait déclenché la
plainte. Le manque, lui, n'a jamais été comblé : rien ne relie le modèle aux
fichiers indexés.

## La cause la plus probable du cas Dr_logic

Elle n'est pas dans le vocabulaire, elle est dans le périmètre.

Un dossier synchronisé indexe ses fichiers avec `scope="project"`
(`project_sync_service.py:501`). Le périmètre d'une conversation, lui, suit
trois régimes : rattachée à un projet, elle voit ce projet ; réglée sur
« Tous les projets », elle les voit tous ; par défaut, elle applique le
moindre privilège et ne voit que les documents généraux. Ce défaut est un
choix délibéré, écrit noir sur blanc dans le code : « une conversation qui
n'a rien demandé ne pioche pas dans les dossiers clients ».

Conséquence pour quelqu'un qui a indexé mille fichiers dans un projet, puis
ouvert une conversation sans la rattacher : aucun de ses fichiers n'est
consultable, et rien ne le lui dit. Le sélecteur existe pourtant, à côté du
titre de la conversation, avec un nom accessible juste — « Documents
consultés par cette conversation ». Deux choses le desservent. Il tient en
une icône et onze rem de large, dans la taille réservée aux mentions
secondaires. Et son libellé par défaut, « Documents généraux », dit ce qui
est inclus sans jamais dire ce qui est exclu.

C'est le même défaut que le reste du chantier : le comportement est correct,
il n'est pas dit.

## Pourquoi `{label: …}` ne réglerait pas cela

La syntaxe proposée lève une ambiguïté de désignation. Or rien n'est
ambigu : il n'y a rien à désigner. Avec le périmètre par défaut, un
`{label: Fichier-index.html}` parfaitement explicite pointerait vers un
fichier que la conversation n'a pas le droit de consulter, et le modèle n'a
de toute façon aucun outil pour aller le chercher.

Le mécanisme aurait un coût propre. Les variables `{nom}` de la 0.32
substituent déjà sur cette forme d'accolades. Ajouter un second registre
oblige à trancher qui lit quoi en premier, et ce qu'il advient d'un
`{label: X}` dans un message où une variable porte le même nom. Ce genre
d'arbitrage se paie longtemps. Ajoutons que « Dossier synchronisé » est un
titre d'écran, pas un objet nommé : il n'y aurait rien à résoudre derrière
ce label sans un cas particulier écrit à la main.

## Ce qui manque vraiment

Quatre pièces, par ordre de rapport valeur sur risque. Chacune vaut seule.

**Dire le périmètre au lieu de le taire.** Quand la conversation ne consulte
que les documents généraux et qu'il existe des fichiers indexés dans des
projets, le dire à l'endroit du sélecteur. Une phrase suffit. C'est la pièce
qui coûte le moins et qui règle peut-être à elle seule le cas signalé.

**Un catalogue, pas une seconde recherche sémantique.** La relecture
adversariale a rejeté ma première formulation, et elle avait raison : « les
documents indexés » et « Fichier-index.html » sont des interrogations de
catalogue, pas des questions de similarité. Un outil qui relancerait Qdrant
avec le même seuil recollerait le symptôme sous un autre nom. Ce qu'il faut
est un `SELECT` sur la table `files`, qui porte déjà `name`, `scope` et
`scope_id` — exactement le chemin de `read_contact`.

**Le périmètre hérité, jamais élevé.** L'outil doit prendre son périmètre de
la conversation, comme le RAG. Un `project_id` passé par le modèle rouvrirait
la cloison posée en 0.43. Quand l'utilisateur demande un projet auquel sa
conversation n'est pas rattachée, la réponse juste est de le dire, pas de
chercher dans le vide ni de forcer la porte.

**Le contenu borné.** Un catalogue paginé et filtré, puis le contenu d'un
fichier nommé. Pas mille chemins disque déversés dans le prompt, sinon on
recrée BUG-160 par l'autre bout.

Une fois ces pièces posées, `{label: …}` redevient ce qu'il aurait dû être :
un paramètre d'outil, pas une syntaxe à apprendre. Si un jour une directive
s'impose, elle prendra la forme déjà en place — `[fichier: Fichier-index.html]`,
déterministe comme `[contact:]` — plutôt qu'un quatrième dialecte.

## Ce qui reste à trancher

- **Le cas « cherche dans SWL » depuis une conversation non rattachée.**
  Refuser en expliquant, ou autoriser quand le projet est nommé par
  l'utilisateur lui-même et le journaliser. À décider avant d'écrire la
  moindre ligne.
- **Le type `file` dans l'injection automatique**, une fois le catalogue en
  place. Le laisser fait double emploi ; le retirer prive les réponses d'un
  contexte qui arrive parfois à propos.

## Constat annexe

`GET /api/files/` liste toute la table sans filtre de périmètre, et
`GET /api/files/{id}/content` ne contrôle que l'identifiant. La cloison de la
0.43 vit dans la recherche, pas dans ces routes. Aucun écran ne les appelle
aujourd'hui — leurs fonctions frontales n'ont aucun consommateur — mais un
futur catalogue devra s'appuyer sur `GET /api/memory/projects/{id}/files`,
qui filtre, et jamais sur elles.

## Ce que cette proposition ne fait pas

Elle ne touche pas à l'injection automatique, qui garde son rôle : donner du
contexte sans qu'on ait à le demander. Les deux chemins se complètent, l'un
pour ce qui vient tout seul, l'autre pour ce qu'on va chercher. À noter que
couper l'injection quand l'outil est appelé serait de toute façon sans
effet : elle a lieu avant, à la préparation du contexte.

Elle ne renomme aucun écran. Le lexique 0.48 a réglé les noms de surfaces ;
celui des objets manipulés commence par rendre ces objets atteignables, et
par dire quand ils ne le sont pas.
