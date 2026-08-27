# Le vocabulaire des objets — diagnostic et proposition

Signalé par Dr_logic le 27/08 (D6). Il a un projet « site web l'egrenne »
avec plus de mille fichiers indexés. Quand il écrit « les documents
indexés », Thérèse part sur des factures.

Sa proposition : une syntaxe `{label: nom}` sur le modèle des directives
`[action: …]`, pour nommer explicitement ce dont on parle. Son exemple :
« décris-moi la structure de {label: Fichier-index.html}, indexé dans
{label: Dossier synchronisé} du projet {label: SWL} ».

## Ce que le code dit

Quatre constats, tous vérifiés à la lecture.

**1. Aucun outil ne permet d'atteindre les fichiers indexés.** La liste
complète de ce que le modèle peut appeler : `create_calendar_event`,
`create_contact`, `create_project`, `generate_document`,
`list_calendar_events`, `read_contact`, `read_emails`, `search_emails`,
`search_invoices`, `send_email`, `summarize_emails`. Rien pour les
documents.

**2. Le seul accès aux documents est une injection automatique et muette.**
`_get_memory_context` interroge Qdrant sur le message brut, avec un seuil de
similarité à 0.35, cloisonné par projet depuis la 0.43. Le modèle ne la
déclenche pas, ne la paramètre pas, ne sait pas qu'elle a eu lieu, et ne
peut pas la relancer autrement s'il ne trouve rien.

**3. Le seul verbe de recherche annoncé au modèle parle de factures.** Le
bloc « capacités » décrit `search_invoices` comme « Retrouver une facture,
un devis ou un avoir LOCAL par sa référence ou par client ». Face à « les
documents indexés », un modèle qui cherche l'outil le plus proche de sa
liste trouve celui-là. Le comportement rapporté n'est pas une erreur de
compréhension, c'est le seul choix disponible.

**4. Un fichier ne peut pas être retrouvé par son nom.** L'indexation
vectorise le fragment de contenu seul ; le nom du fichier vit en métadonnée,
hors du vecteur, et aucun filtre ne cherche dessus. Demander « la structure
de Fichier-index.html » compare cette phrase au contenu des fragments. Le
nom n'y participe pas.

Un cinquième élément mérite d'être noté, parce qu'il déplace la question :
« Dossier synchronisé » est le terme exact de l'interface, posé en 0.45 par
`ProjectSyncSection`. Le testeur emploie le vocabulaire de l'application.
C'est l'application qui ne reconnaît pas le sien.

## Pourquoi `{label: …}` traiterait le symptôme

La syntaxe proposée résout une ambiguïté de désignation. Or l'ambiguïté
n'est pas la cause : même avec un label parfaitement explicite, il n'existe
rien à appeler. `{label: Fichier-index.html}` désignerait sans équivoque un
fichier que le modèle ne peut ni chercher, ni lire, ni citer.

Le mécanisme aurait en plus un coût qui lui est propre. Les variables `{nom}`
de la 0.32 substituent déjà sur cette syntaxe, dans le seul texte destiné au
modèle et après les parseurs déterministes. Ajouter un second registre sur la
même forme d'accolades demande de trancher qui lit quoi en premier, et ce
qu'il advient d'un `{label: …}` dans un message où une variable porte le même
nom. Ce genre d'arbitrage se paie longtemps.

## Ce qui manque vraiment

Trois pièces, dans cet ordre. Chacune a une valeur seule.

**Un outil de recherche documentaire.** Nommé dans le vocabulaire de
l'interface, pas dans celui du moteur : on cherche dans les fichiers d'un
projet ou d'un dossier synchronisé, pas dans « la mémoire vectorielle ».
Cloisonné par périmètre comme l'injection automatique l'est déjà, et par le
même chemin, pour qu'une cloison corrigée le reste des deux côtés. Annoncé
dans les capacités, pour que le modèle sache qu'il existe.

**La recherche par nom de fichier.** Un filtre sur la métadonnée `name`,
qui rend enfin possible « la structure de Fichier-index.html ». C'est la
pièce qui coûte le moins et qui débloque l'exemple exact du testeur.

**Le vocabulaire annoncé.** Les capacités décrivent aujourd'hui des noms
d'outils. Elles gagneraient à nommer les objets tels que l'interface les
nomme, puisque c'est ainsi que l'utilisateur les désigne.

Une fois ces trois pièces posées, `{label: …}` redevient ce qu'il aurait dû
être : une commodité de désambiguïsation quand deux fichiers portent un nom
proche. Utile, secondaire, et sans arbitrage de syntaxe à trancher dans
l'urgence.

## Ce que cette proposition ne fait pas

Elle ne touche pas à l'injection automatique, qui garde son rôle : donner du
contexte sans qu'on ait à le demander. Les deux chemins se complètent, l'un
pour ce qui vient tout seul, l'autre pour ce qu'on va chercher.

Elle ne renomme aucun écran. Le lexique 0.48 a réglé les noms de surfaces ;
celui des objets manipulés est un chantier distinct, et il commence par
rendre ces objets atteignables.
