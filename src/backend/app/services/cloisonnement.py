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

from typing import Any

from app.models.entities import Contact
from sqlalchemy import false, or_
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import col

_mode_cabinet_cache: bool | None = None


def poser_mode_cabinet(actif: bool | None) -> None:
    """Met en cache le réglage. `None` remet le défaut (carnet partagé)."""
    global _mode_cabinet_cache
    _mode_cabinet_cache = actif


async def charger_mode_cabinet_depuis_la_base() -> bool | None:
    """Pose le cache depuis la préférence, ou le défaut si elle est absente.

    Démarrage, et B-1540 après une restauration : la table des préférences
    vient d'être remplacée, le cache gardait le choix d'avant. Rend la valeur
    lue (None : préférence absente)."""
    from app.models.database import get_session_context
    from app.models.entities import Preference
    from sqlalchemy import select

    async with get_session_context() as session:
        resultat = await session.execute(select(Preference).where(Preference.key == "mode_cabinet"))
        preference = resultat.scalar_one_or_none()
    actif = None if preference is None else preference.value.lower() == "true"
    poser_mode_cabinet(actif)
    return actif


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




def cloison_contacts(
    requete: Any,
    scope: str | None,
    scope_id: str | None,
    conversation_id: str | None = None,
) -> Any:
    """Restreint une requête contacts au périmètre de la conversation.

    Les contacts GÉNÉRAUX restent visibles partout, comme les documents
    globaux. `scope` NULL en base (contacts d'avant E3-05) est traité comme
    général : ne pas le faire masquerait des contacts existants.
    """
    # C3 : en mode cabinet, une conversation rattachée à un dossier ne voit
    # plus le carnet général. Sans cette branche, le modèle contournerait la
    # fermeture du RAG en demandant simplement la fiche par son nom.
    # Le type est annoté : sans lui, mypy infère `False_` du premier
    # assignement et refuse le `or_(...)` qui suit.
    generaux: ColumnElement[bool]
    if not souvenirs_globaux_visibles(scope):
        generaux = false()
    else:
        generaux = or_(col(Contact.scope) == "global", col(Contact.scope).is_(None))
    # RÉGRESSION ÉVITÉE (revue de clôture) : l'interface crée les contacts
    # suggérés avec `scope="conversation"` (`EntitySuggestion.tsx`). Sans cette
    # branche, un contact tout juste enregistré depuis la conversation en cours
    # devenait introuvable dans cette même conversation — la fonction cassait
    # sous prétexte de la protéger.
    if conversation_id:
        generaux = or_(
            generaux,
            (col(Contact.scope) == "conversation") & (col(Contact.scope_id) == conversation_id),
        )
    if scope == "project" and scope_id:
        return requete.where(
            or_(
                generaux,
                (col(Contact.scope) == "project") & (col(Contact.scope_id) == scope_id),
            )
        )
    if scope == "global":
        # Le mode global est le DÉFAUT : le laisser sans filtre revenait à
        # n'avoir cloisonné personne. Une conversation libre ne voit que les
        # contacts généraux et ceux de sa propre conversation.
        return requete.where(generaux)
    if scope == "all":
        # « Tous les projets » : le libellé engage. Il donne accès aux
        # dossiers, PAS aux souvenirs privés des autres conversations — un
        # contact enregistré dans une conversation y reste (revue de clôture :
        # ce mode rendait coordonnées et notes de n'importe quelle
        # conversation).
        return requete.where(or_(generaux, col(Contact.scope) == "project"))
    # `scope is None` : appel hors conversation (scripts, tests, chemins
    # historiques). Pas de cloison, comportement d'avant la 0.43.
    return requete

