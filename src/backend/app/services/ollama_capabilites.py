"""Ce qu'un modèle local sait faire — et surtout ce qu'il ne sait pas.

BUG-169. Un testeur a choisi `gemma3:1b`. THÉRÈSE lui a envoyé ses douze outils,
Ollama a répondu « does not support tools », et il a attendu 3 min 26 s le
premier mot pour une réponse dégradée. Le repli fonctionnait ; c'est de l'avoir
proposé qui était fautif.

Un modèle sans appel d'outils ne peut ni créer un contact, ni poser un
rendez-vous, ni produire un document, ni lire un email. Ce n'est pas un modèle
moins bon : c'est un modèle qui ne fait pas ce que THÉRÈSE promet. Il n'a donc
rien à faire dans une liste de choix, sauf à dire pourquoi il est écarté.

Source : la bibliothèque Ollama affiche une étiquette « tools » sur les modèles
compatibles (ollama.com/search?c=tools), relevée le 24/08/2026.

Le sens du doute est délibéré : on n'écarte QUE ce qu'on sait incapable. Ollama
accepte n'importe quel modèle, y compris construit ou renommé localement, et
écarter un inconnu priverait l'utilisateur du sien.
"""

# Familles relevées SANS étiquette « tools » sur ollama.com le 24/08/2026.
# La comparaison porte sur la famille, avant les deux-points : une variante
# quantifiée comme `gemma3:1b-instruct-q4_0` reste un gemma3.
FAMILLES_SANS_OUTILS: frozenset[str] = frozenset({
    "gemma3",   # toute la famille, du 1b au 27b — le cas du testeur
    "gemma2",
    "gemma",
    "phi4",     # `phi4-mini` en revanche gère les outils : voir ci-dessous
    "phi3",
    "llama2",
    "codellama",
    "deepseek-coder",
    "starcoder",
    "starcoder2",
    "codegemma",
    "stablelm2",
    "tinyllama",
    "orca-mini",
    "vicuna",
    "wizardlm2",
})

# Exceptions : familles proches par le nom mais réellement outillées. Sans
# elles, `phi4-mini` serait écarté à cause de `phi4`, alors qu'il porte bien
# l'étiquette.
MODELES_OUTILLES_MALGRE_LA_FAMILLE: frozenset[str] = frozenset({
    "phi4-mini",
})


def famille(modele: str) -> str:
    """La famille d'un tag Ollama : `gemma3:1b-q4_0` donne `gemma3`."""
    return modele.split(":", 1)[0].strip().lower()


def gere_les_outils(modele: str) -> bool:
    """Ce modèle peut-il appeler les outils de THÉRÈSE ?

    Renvoie `True` par défaut : on n'écarte que ce dont on est sûr.
    """
    if not modele:
        return True

    nom = famille(modele)
    if nom in MODELES_OUTILLES_MALGRE_LA_FAMILLE:
        return True
    return nom not in FAMILLES_SANS_OUTILS


def motif_d_exclusion(modele: str) -> str | None:
    """Pourquoi ce modèle est écarté, dit à l'utilisateur.

    Un modèle simplement absent de la liste laisse croire à un bug. Le montrer
    désactivé avec son motif respecte le même principe que le reste de cette
    version : l'application sait quelque chose, elle le dit.
    """
    if gere_les_outils(modele):
        return None
    return (
        f"{famille(modele)} ne sait pas déclencher d'actions : ni contact, ni "
        "rendez-vous, ni document. Choisis un modèle comme qwen3.5 ou "
        "ministral-3 pour que THÉRÈSE puisse agir."
    )
