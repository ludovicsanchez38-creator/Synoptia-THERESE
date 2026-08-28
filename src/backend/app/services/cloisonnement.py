"""Politique de cloisonnement de la mémoire — chantier C, campagne dix personas.

Un avocat a vu, depuis le dossier Rousset, la lettre de licenciement d'un autre
client et le traitement anxiolytique de sa cliente. Le mécanisme est assumé par
le code depuis la cloison 0.43 : « Les contacts GÉNÉRAUX restent visibles
partout, comme les documents globaux. » Pour un artisan qui a un carnet
d'adresses commun à ses chantiers, c'est le bon comportement. Pour une
profession au secret, c'est éliminatoire.

D'où un RÉGLAGE, et pas un changement de défaut.

Ce module existe pour une raison précise, trouvée par la relecture de design :
**il y a deux lecteurs de la mémoire**, et fermer un seul ne protège rien.

  * la recherche vectorielle répond au premier tour
    (`chat._get_memory_context` → `qdrant.async_search`, `include_global`) ;
  * l'outil `read_contact` répond au second, quand le modèle demande la fiche
    par son nom (`memory_tools._cloison_contacts`, en SQL).

« Tu fermerais le RAG, l'outil SQL recrache le secret. » La décision vit donc
ici, en un seul endroit, et les deux lecteurs la consultent.

Le cache suit le motif de la clé Brave et du garde de recherche web : posé au
démarrage et à chaque changement de réglage, pour rester utilisable sans
session.
"""

_mode_cabinet_cache: bool | None = None


def poser_mode_cabinet(actif: bool | None) -> None:
    """Met en cache le réglage. `None` remet le défaut (carnet partagé)."""
    global _mode_cabinet_cache
    _mode_cabinet_cache = actif


def mode_cabinet_actif() -> bool:
    """Défaut : non.

    Basculer le défaut priverait de son carnet commun un utilisateur qui n'a
    rien demandé — et, sans le préalable C2 (pouvoir rattacher une fiche à un
    dossier), viderait un dossier de sa propre personne : la fiche du client
    est globale, elle aussi.
    """
    return bool(_mode_cabinet_cache)


def souvenirs_globaux_visibles(scope: str | None = "project") -> bool:
    """Les souvenirs généraux doivent-ils remonter dans cette conversation ?

    `scope` est le périmètre de la conversation, tel que
    `_perimetre_de_conversation` le rend :

      * `"project"` — la conversation est rattachée à un dossier. C'est le seul
        cas que le mode cabinet ferme : l'utilisateur a désigné un dossier, il
        attend de ne voir que lui.
      * `None` ou `"global"` — conversation libre. Il n'y a aucun dossier à
        respecter : fermer ne protégerait personne et casserait l'usage
        courant.
      * `"all"` — l'utilisateur a explicitement demandé tous les dossiers.
    """
    if not mode_cabinet_actif():
        return True
    return scope != "project"
