"""
THÉRÈSE v2 - Deep Research Service

Recherche approfondie multi-sources : décompose une question en sous-requêtes,
lance les recherches en parallèle, puis synthétise un rapport structuré avec citations.
Inspiré de Manus Wide Research.

v0.6 - Rattrapage Manus
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import AsyncGenerator

from app.services.web_search import SearchResponse, get_web_search_service

logger = logging.getLogger(__name__)


@dataclass
class ResearchSource:
    """Une source utilisée dans la recherche."""
    title: str
    url: str
    snippet: str
    query: str


@dataclass
class ResearchProgress:
    """Progression de la recherche."""
    type: str  # "decomposition", "searching", "search_done", "synthesizing", "done", "error"
    step: int = 0
    total_steps: int = 0
    query: str = ""
    content: str = ""
    sources: list[ResearchSource] = field(default_factory=list)


DECOMPOSITION_PROMPT = """Tu es un assistant de recherche. L'utilisateur pose une question qui nécessite une recherche approfondie.

Décompose cette question en 5 à 8 sous-questions de recherche web précises et complémentaires.
Chaque sous-question doit couvrir un angle différent du sujet.
Formule les sous-questions comme des requêtes de moteur de recherche (courtes, mots-clés pertinents).

Réponds UNIQUEMENT avec un tableau JSON de strings, sans aucun autre texte.
Exemple: ["requête 1", "requête 2", "requête 3"]

Question de l'utilisateur: {question}"""


SYNTHESIS_PROMPT = """Tu es un analyste expert. À partir des résultats de recherche ci-dessous, rédige un rapport structuré et complet en français.

**Consignes :**
- Structure le rapport avec des titres et sous-titres Markdown
- Cite tes sources entre crochets [1], [2], etc.
- Sois factuel et précis, pas de spéculation
- Si des informations se contredisent entre sources, mentionne-le
- Termine par une section "Sources" numérotée avec les URLs
- Longueur : 500 à 1500 mots selon la complexité du sujet

**Question initiale :** {question}

**Résultats de recherche :**

{search_results}

**Liste des sources :**
{sources_list}"""


async def decompose_question(
    question: str,
    llm_service: object,
) -> list[str]:
    """Décompose une question en sous-requêtes de recherche via le LLM."""
    from app.services.providers import LLMMessage

    prompt = DECOMPOSITION_PROMPT.format(question=question)
    messages = [LLMMessage(role="user", content=prompt)]

    context = llm_service.prepare_context(messages)

    full_response = ""
    async for chunk in llm_service.stream_response(context, enable_grounding=False):
        full_response += chunk

    # Extraire le JSON du texte
    try:
        # Chercher un tableau JSON dans la réponse
        start = full_response.find("[")
        end = full_response.rfind("]") + 1
        if start >= 0 and end > start:
            queries = json.loads(full_response[start:end])
            if isinstance(queries, list) and all(isinstance(q, str) for q in queries):
                return queries[:8]
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback : utiliser la question originale
    logger.warning("Impossible de décomposer la question, utilisation de la question originale")
    return [question]


async def search_parallel(
    queries: list[str],
    max_results_per_query: int = 5,
) -> tuple[list[SearchResponse], list[ResearchSource]]:
    """Lance les recherches en parallèle et collecte les résultats."""
    service = get_web_search_service()

    tasks = [
        service.search(query, max_results=max_results_per_query)
        for query in queries
    ]

    responses = await asyncio.gather(*tasks, return_exceptions=True)

    all_responses: list[SearchResponse] = []
    all_sources: list[ResearchSource] = []
    seen_urls: set[str] = set()

    for resp in responses:
        if isinstance(resp, Exception):
            logger.error(f"Erreur recherche : {resp}")
            continue

        all_responses.append(resp)
        for result in resp.results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                all_sources.append(ResearchSource(
                    title=result.title,
                    url=result.url,
                    snippet=result.snippet,
                    query=resp.query,
                ))

    return all_responses, all_sources


def format_search_results_for_synthesis(
    sources: list[ResearchSource],
) -> tuple[str, str]:
    """Formate les résultats pour le prompt de synthèse."""
    search_results_parts = []
    sources_list_parts = []

    for i, source in enumerate(sources, 1):
        search_results_parts.append(
            f"[{i}] **{source.title}** (recherche: \"{source.query}\")\n"
            f"   {source.snippet}\n"
        )
        sources_list_parts.append(f"[{i}] {source.title} - {source.url}")

    return "\n".join(search_results_parts), "\n".join(sources_list_parts)


async def deep_research(
    question: str,
    llm_service: object,
    max_queries: int = 6,
    max_results_per_query: int = 5,
) -> AsyncGenerator[ResearchProgress, None]:
    """
    Exécute une recherche approfondie avec progression en temps réel.

    Workflow:
    1. Décomposer la question en sous-requêtes (LLM)
    2. Lancer les recherches en parallèle (Brave/DDG)
    3. Synthétiser les résultats en rapport structuré (LLM)

    Yields des ResearchProgress pour le streaming SSE.
    """
    from app.services.providers import LLMMessage

    # Étape 1 : Décomposition
    yield ResearchProgress(
        type="decomposition",
        content="Analyse de la question et préparation des recherches...",
    )

    try:
        queries = await decompose_question(question, llm_service)
        queries = queries[:max_queries]
    except Exception as e:
        logger.error(f"Erreur décomposition : {e}")
        queries = [question]

    total = len(queries)
    yield ResearchProgress(
        type="decomposition",
        content=f"{total} axes de recherche identifiés",
        total_steps=total,
    )

    # Étape 2 : Recherches parallèles (avec progression)
    service = get_web_search_service()
    all_sources: list[ResearchSource] = []
    seen_urls: set[str] = set()

    for i, query in enumerate(queries, 1):
        yield ResearchProgress(
            type="searching",
            step=i,
            total_steps=total,
            query=query,
            content=f"Recherche {i}/{total} : {query}",
        )

        try:
            resp = await service.search(query, max_results=max_results_per_query)
            for result in resp.results:
                if result.url not in seen_urls:
                    seen_urls.add(result.url)
                    all_sources.append(ResearchSource(
                        title=result.title,
                        url=result.url,
                        snippet=result.snippet,
                        query=query,
                    ))
        except Exception as e:
            logger.error(f"Erreur recherche '{query}': {e}")

        yield ResearchProgress(
            type="search_done",
            step=i,
            total_steps=total,
            query=query,
            content=f"Recherche {i}/{total} terminée ({len(all_sources)} sources)",
        )

    if not all_sources:
        yield ResearchProgress(
            type="error",
            content="Aucun résultat trouvé. Vérifie ta clé Brave Search ou reformule la question.",
        )
        return

    # Étape 3 : Synthèse
    yield ResearchProgress(
        type="synthesizing",
        content=f"Synthèse de {len(all_sources)} sources en cours...",
        sources=all_sources,
    )

    search_results_text, sources_list_text = format_search_results_for_synthesis(all_sources)

    synthesis_prompt = SYNTHESIS_PROMPT.format(
        question=question,
        search_results=search_results_text,
        sources_list=sources_list_text,
    )

    messages = [LLMMessage(role="user", content=synthesis_prompt)]
    context = llm_service.prepare_context(messages)

    # raise_on_error=True : sans ça, une erreur provider (ex: Gemini 400 tool_config)
    # était avalée -> synthesis_content vide -> on émettait un "done" VIDE (échec
    # silencieux). Rapport Syn 14/06. On la remonte désormais en événement "error".
    synthesis_content = ""
    try:
        async for chunk in llm_service.stream_response(
            context, enable_grounding=False, raise_on_error=True
        ):
            synthesis_content += chunk
            yield ResearchProgress(
                type="synthesizing",
                content=chunk,
                sources=all_sources,
            )
    except Exception as e:
        logger.error(f"Erreur synthèse deep-research : {e}")
        yield ResearchProgress(
            type="error",
            content=f"La synthèse a échoué : {e}",
            sources=all_sources,
        )
        return

    yield ResearchProgress(
        type="done",
        content=synthesis_content,
        sources=all_sources,
    )
