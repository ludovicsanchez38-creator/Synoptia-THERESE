"""Catalogue NEUTRE des modèles LLM - la source unique (jalon 0.48).

Un seul endroit porte : les listes ordonnées par fournisseur (la TÊTE est
le frontier - c'est un choix ÉDITORIAL, relevé dans la documentation
officielle de chaque fournisseur à chaque release, PAS un choix
mécanique), la politique d'effort par modèle, et les recommandations de
sortie. Les quatre tables de llm.py, la liste UI de config.py et les
providers en DÉRIVENT - plus aucun modèle codé en dur ailleurs.

Relevé aux sources le 25/08/2026 (fiches modèles + guides reasoning des
cinq fournisseurs du Board, listes UI reprises du relevé 24/08 de la
0.43.4). N'importe JAMAIS llm.py (cycle) : l'enum vient de providers.base.

Politique d'effort - trois états par modèle :
- ``None`` (non envoyé) : support non vérifié dans la doc du fournisseur ;
- ``TEL_QUEL`` : le fournisseur accepte nos valeurs telles quelles ;
- une table de traduction : la demande logique (low..max) devient la
  valeur propre au modèle (plafond compris).
Un modèle INCONNU du catalogue est transmis tel quel quand le fournisseur
est dynamique (Ollama, ou inconnu) - le provider garde sa dégradation
gracieuse - et n'est PAS envoyé pour un fournisseur déclaré (prudence,
comportement historique conservé, OpenRouter notamment).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.services.providers.base import LLMProvider

# Sentinelle « transmis tel quel ».
TEL_QUEL = "tel_quel"

#: Fournisseurs dont les modèles sont découverts dynamiquement : un modèle
#: inconnu y est transmis tel quel (dégradation gracieuse côté provider).
_FOURNISSEURS_DYNAMIQUES = {"ollama"}


@dataclass(frozen=True)
class FicheModele:
    """La politique d'un modèle précis."""

    #: None = jamais envoyé ; TEL_QUEL = valeurs transmises telles quelles ;
    #: dict = traduction demande logique -> valeur émise (plafond inclus).
    effort: str | dict[str, str] | None = None
    max_tokens_recommande: int | None = None


@dataclass(frozen=True)
class FicheFournisseur:
    provider: LLMProvider
    env_vars: tuple[str, ...]
    context_window: int
    #: Liste ordonnée - la TÊTE est le frontier (l'ordre EST la
    #: recommandation, contrat de la liste UI).
    modeles: tuple[str, ...]
    fiches: dict[str, FicheModele] = field(default_factory=dict)


# Traductions d'effort vérifiées aux sources (25/08/2026).
_EFFORT_ANTHROPIC = {"low": "low", "medium": "medium", "high": "high", "max": "max"}
_EFFORT_GROK_46 = {"low": "low", "medium": "medium", "high": "high", "max": "xhigh"}
_EFFORT_GROK_45 = {"low": "low", "medium": "medium", "high": "high", "max": "high"}
_EFFORT_GEMINI_3 = {"low": "LOW", "medium": "MEDIUM", "high": "HIGH", "max": "HIGH"}
_EFFORT_MISTRAL_MEDIUM = {"low": "high", "medium": "high", "high": "high", "max": "high"}

_ANTHROPIC_EFFORT_OK = FicheModele(effort=_EFFORT_ANTHROPIC)

CATALOGUE: dict[str, FicheFournisseur] = {
    "anthropic": FicheFournisseur(
        provider=LLMProvider.ANTHROPIC,
        env_vars=("ANTHROPIC_API_KEY",),
        context_window=200000,
        modeles=(
            "claude-opus-5",                 # Le plus polyvalent (recommandé)
            "claude-fable-5",                # Puissance maximale, plus lent
            "claude-sonnet-5",               # Équilibre vitesse/intelligence
            "claude-haiku-4-5-20251001",     # Le plus rapide
            "claude-opus-4-8",               # Génération précédente
            "claude-opus-4-7",
            "claude-opus-4-6",
            "claude-sonnet-4-6",
        ),
        fiches={
            # Effort vérifié (ex-_EFFORT_PREFIXES d'anthropic.py + opus-5,
            # doc effort du 25/08 : opus-5 accepte low..max, défaut high).
            "claude-opus-5": FicheModele(
                effort=_EFFORT_ANTHROPIC, max_tokens_recommande=64000
            ),
            "claude-fable-5": _ANTHROPIC_EFFORT_OK,
            "claude-sonnet-5": _ANTHROPIC_EFFORT_OK,
            "claude-sonnet-4-6": _ANTHROPIC_EFFORT_OK,
            "claude-opus-4-8": _ANTHROPIC_EFFORT_OK,
            "claude-opus-4-7": _ANTHROPIC_EFFORT_OK,
            "claude-opus-4-6": _ANTHROPIC_EFFORT_OK,
            # haiku : pas d'effort (contrat 0.31 conservé).
        },
    ),
    "openai": FicheFournisseur(
        provider=LLMProvider.OPENAI,
        env_vars=("OPENAI_API_KEY",),
        context_window=200000,
        modeles=(
            "gpt-5.6-sol",       # Le plus capable (recommandé)
            "gpt-5.6-terra",     # Équilibre intelligence/coût
            "gpt-5.6-luna",      # Le plus économique de la génération
            "gpt-5.5",           # Génération précédente
            "gpt-5.5-pro",       # Réflexion longue
            "gpt-5.4-mini",      # Petit, rapide, bon marché
        ),
        fiches={
            # Fiches 5.6 : none/low/medium/high/xhigh/max, transmis tel quel.
            "gpt-5.6-sol": FicheModele(effort=TEL_QUEL),
            "gpt-5.6-terra": FicheModele(effort=TEL_QUEL),
            "gpt-5.6-luna": FicheModele(effort=TEL_QUEL),
            # 5.5/5.4 : support non vérifié - RIEN n'est envoyé (contrat
            # 0.31, verrouillé par test_provider_effort).
        },
    ),
    "gemini": FicheFournisseur(
        provider=LLMProvider.GEMINI,
        env_vars=("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        context_window=1000000,
        modeles=(
            "gemini-3.7-flash",           # Le plus récent (recommandé)
            "gemini-3.1-pro-preview",     # Le seul Pro récent
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",      # Le plus économique
            "gemini-2.5-pro",             # Ancienne génération
            "gemini-2.5-flash",
        ),
        fiches={
            # thinkingLevel : Gemini 3+ seulement (erreur API sur les 2.x),
            # MAJUSCULES sur generateContent, pas de xhigh sur 3.7-flash.
            "gemini-3.7-flash": FicheModele(effort=_EFFORT_GEMINI_3),
            "gemini-3.6-flash": FicheModele(effort=_EFFORT_GEMINI_3),
            "gemini-3.5-flash": FicheModele(effort=_EFFORT_GEMINI_3),
            "gemini-3.5-flash-lite": FicheModele(effort=_EFFORT_GEMINI_3),
            "gemini-3.1-pro-preview": FicheModele(effort=_EFFORT_GEMINI_3),
            # 2.x : rien (thinkingConfig sur modèle sans thinking = erreur).
        },
    ),
    "mistral": FicheFournisseur(
        provider=LLMProvider.MISTRAL,
        env_vars=("MISTRAL_API_KEY",),
        context_window=256000,
        modeles=(
            # ID ÉPINGLÉ en tête : un alias -latest bouge silencieusement
            # et aveuglerait la sonde de dérive (design 0.48).
            "mistral-medium-3-5",     # Vaisseau amiral (recommandé)
            "mistral-medium-latest",  # Pointeur perpétuel (choix utilisateur)
            "mistral-large-latest",   # Grand modèle, pointeur à jour
            "mistral-large-2512",     # Version figée, Apache 2.0
            "mistral-small-2603",     # Petit modèle
            "codestral-2508",         # Spécialiste du code
            "ministral-8b-2512",      # Léger
            "ministral-3b-2512",      # Le plus petit
        ),
        fiches={
            # Page Reasoning : seuls high/none documentés pour medium-3-5.
            "mistral-medium-3-5": FicheModele(effort=_EFFORT_MISTRAL_MEDIUM),
            "mistral-medium-latest": FicheModele(effort=_EFFORT_MISTRAL_MEDIUM),
            # Les autres : non documenté - rien n'est envoyé.
        },
    ),
    "grok": FicheFournisseur(
        provider=LLMProvider.GROK,
        env_vars=("XAI_API_KEY",),
        context_window=131072,
        modeles=(
            "grok-4.6",                      # Le plus intelligent (recommandé)
            "grok-4.5",                      # Génération précédente
            "grok-4.3",                      # Économique, très grand contexte
            "grok-4.20-0309-reasoning",      # Raisonnement long
            "grok-4.20-0309-non-reasoning",  # Réponse directe
        ),
        fiches={
            # xhigh disponible depuis 4.6 (high = DÉFAUT, pas le max).
            "grok-4.6": FicheModele(effort=_EFFORT_GROK_46),
            # Plafond high sur 4.5 (contrat 0.31 conservé).
            "grok-4.5": FicheModele(effort=_EFFORT_GROK_45),
        },
    ),
    "glm": FicheFournisseur(
        provider=LLMProvider.GLM,
        env_vars=("GLM_API_KEY",),
        context_window=200000,
        modeles=(
            "glm-5.3", "glm-5.2", "glm-5.1", "glm-5",
            "glm-5-turbo", "glm-4.7", "glm-4.7-flashx", "glm-4.7-flash",
        ),
    ),
    "kimi": FicheFournisseur(
        provider=LLMProvider.KIMI,
        env_vars=("KIMI_API_KEY",),
        context_window=1000000,
        modeles=(
            "kimi-k3", "kimi-k2.7-code", "kimi-k2.7-code-highspeed",
            "kimi-k2.6", "kimi-k2.5",
        ),
    ),
    "qwen": FicheFournisseur(
        provider=LLMProvider.QWEN,
        env_vars=("QWEN_API_KEY",),
        context_window=1000000,
        modeles=("qwen3.8-max", "qwen3.7-plus", "qwen3.7-flash", "qwen3-coder-plus"),
    ),
    "minimax": FicheFournisseur(
        provider=LLMProvider.MINIMAX,
        env_vars=("MINIMAX_API_KEY",),
        context_window=200000,
        modeles=(
            "MiniMax-M3", "MiniMax-M2.7", "MiniMax-M2.7-highspeed",
            "MiniMax-M2.5", "MiniMax-M2.5-highspeed",
        ),
    ),
    "deepseek": FicheFournisseur(
        provider=LLMProvider.DEEPSEEK,
        env_vars=("DEEPSEEK_API_KEY",),
        context_window=128000,
        modeles=("deepseek-v4-pro", "deepseek-v4-flash"),
    ),
    "perplexity": FicheFournisseur(
        provider=LLMProvider.PERPLEXITY,
        env_vars=("PERPLEXITY_API_KEY",),
        context_window=200000,
        modeles=("sonar-pro",),
    ),
    "openrouter": FicheFournisseur(
        provider=LLMProvider.OPENROUTER,
        env_vars=("OPENROUTER_API_KEY",),
        context_window=200000,
        # Découverte dynamique - cette liste n'est que le repli.
        modeles=(
            "anthropic/claude-sonnet-4-6", "anthropic/claude-opus-4-8",
            "openai/gpt-5.5", "google/gemini-3.1-pro",
            "google/gemini-3.5-flash", "meta-llama/llama-4-maverick",
        ),
    ),
    "ollama": FicheFournisseur(
        provider=LLMProvider.OLLAMA,
        env_vars=(),
        context_window=32000,
        # Découverte dynamique - tête = repli historique.
        modeles=("mistral-nemo",),
    ),
}

_FICHES_PAR_MODELE: dict[str, FicheModele] = {
    modele: fiche
    for fournisseur in CATALOGUE.values()
    for modele, fiche in fournisseur.fiches.items()
}

_FOURNISSEUR_PAR_MODELE: dict[str, str] = {
    modele: nom
    for nom, fournisseur in CATALOGUE.items()
    for modele in fournisseur.modeles
}


def frontier(fournisseur: str) -> str | None:
    """La tête de liste - le modèle recommandé du fournisseur."""
    fiche = CATALOGUE.get(fournisseur)
    return fiche.modeles[0] if fiche and fiche.modeles else None


def modeles_ordonnes(fournisseur: str) -> list[str]:
    fiche = CATALOGUE.get(fournisseur)
    return list(fiche.modeles) if fiche else []


def resoudre_effort(
    modele: str,
    effort_demande: str | None,
    fournisseur: str | None = None,
) -> str | None:
    """LE résolveur unique : la valeur d'effort à émettre, ou None.

    Appelé par TOUTE création de LLMConfig (design 0.48) - les providers
    émettent le résultat dans leur syntaxe, sans table locale.
    """
    if not effort_demande:
        return None
    fiche = _FICHES_PAR_MODELE.get(modele)
    if fiche is None:
        if modele in _FOURNISSEUR_PAR_MODELE:
            # Modèle CONNU du catalogue mais sans politique vérifiée.
            return None
        origine = fournisseur or _FOURNISSEUR_PAR_MODELE.get(modele)
        if origine is None or origine in _FOURNISSEURS_DYNAMIQUES:
            # Inconnu et dynamique (Ollama) : transmis tel quel, le
            # provider garde sa dégradation gracieuse.
            return effort_demande
        return None
    if fiche.effort is None:
        return None
    if fiche.effort == TEL_QUEL:
        return effort_demande
    return fiche.effort.get(effort_demande)


def max_tokens_recommande(modele: str) -> int | None:
    fiche = _FICHES_PAR_MODELE.get(modele)
    return fiche.max_tokens_recommande if fiche else None
