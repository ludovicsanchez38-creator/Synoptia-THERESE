"""
THÉRÈSE v2 - Board de Décision - Service

Service pour la délibération multi-conseillers.
Persistance SQLite pour les décisions.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.board import (
    AdvisorRole,
    AdvisorOpinion,
    BoardRequest,
    BoardDeliberationChunk,
    BoardSynthesis,
    BoardDecision,
    ADVISOR_CONFIG,
)
from app.models.entities import BoardDecisionDB
from app.services.llm import get_llm_service, get_llm_service_for_provider, Message as LLMMessage, load_therese_md
from app.services.user_profile import get_cached_profile
from app.services.web_search import WebSearchService

logger = logging.getLogger(__name__)


def validate_advisor_providers() -> bool:
    """
    Vérifie que les 5 conseillers utilisent des providers distincts.

    Returns:
        True si 5 providers distincts, False sinon
    """
    providers_used = set()
    for role, config in ADVISOR_CONFIG.items():
        provider = config.get("preferred_provider")
        if provider in providers_used:
            logger.warning(f"Provider {provider} utilisé par plusieurs conseillers!")
            return False
        providers_used.add(provider)

    if len(providers_used) != 5:
        logger.warning(f"Seulement {len(providers_used)} providers distincts au lieu de 5")
        return False

    logger.info(f"Validation OK: 5 providers distincts ({', '.join(providers_used)})")
    return True


def _get_user_context() -> str:
    """
    Récupère le contexte utilisateur (profil + THERESE.md).

    Returns:
        Texte de contexte à injecter dans le system prompt des conseillers
    """
    context_parts = []

    # Profil utilisateur
    profile = get_cached_profile()
    if profile and profile.name:
        context_parts.append(f"## Utilisateur\n{profile.format_for_llm()}")

    # THERESE.md
    therese_md = load_therese_md()
    if therese_md:
        # Limiter à 8000 chars pour ne pas surcharger le contexte des conseillers
        content = therese_md[:8000]
        if len(therese_md) > 8000:
            content += "\n\n[... THERESE.md tronqué ...]"
        context_parts.append(f"## Contexte utilisateur (THERESE.md)\n{content}")

    if context_parts:
        return "\n\n".join(context_parts)
    return ""


class BoardService:
    """Service pour les délibérations du board."""

    _providers_validated: bool = False

    def __init__(self, session: AsyncSession | None = None):
        self._session = session
        self._web_search = WebSearchService()
        # Validation unique au premier usage
        if not BoardService._providers_validated:
            validate_advisor_providers()
            BoardService._providers_validated = True

    async def _search_web_for_context(self, question: str) -> str:
        """
        Effectue une recherche web pour enrichir le contexte des conseillers.

        Args:
            question: La question stratégique posée

        Returns:
            Texte formaté avec les résultats de recherche
        """
        try:
            logger.info(f"Recherche web pour le Board: {question[:50]}...")
            response = await self._web_search.search(question, max_results=5)

            if not response.results:
                logger.info("Aucun résultat de recherche web")
                return ""

            # Format results for injection
            results_text = "## Recherche Web (informations actualisées)\n\n"
            for i, result in enumerate(response.results, 1):
                results_text += f"**{i}. {result.title}**\n"
                results_text += f"{result.snippet}\n"
                results_text += f"Source: {result.url}\n\n"

            logger.info(f"Recherche web: {len(response.results)} résultats trouvés")
            return results_text

        except Exception as e:
            logger.warning(f"Échec recherche web pour Board: {e}")
            return ""

    async def deliberate(
        self,
        request: BoardRequest,
    ) -> AsyncGenerator[BoardDeliberationChunk, None]:
        """
        Lance une délibération du board en streaming.

        Chaque conseiller utilise son provider LLM préféré si configuré,
        sinon tombe sur le provider par défaut.

        Les 5 conseillers sont sollicités EN PARALLÈLE pour plus de rapidité.

        Yields chunks pour chaque conseiller puis la synthèse.
        """
        default_llm = get_llm_service()

        # Determine which advisors to consult
        advisors = request.advisors or list(AdvisorRole)

        # Signal web search start
        yield BoardDeliberationChunk(
            type="web_search_start",
            content="Recherche d'informations actualisées...",
        )

        # Perform web search FIRST to enrich context for all advisors
        web_search_results = await self._search_web_for_context(request.question)

        # Signal web search done
        yield BoardDeliberationChunk(
            type="web_search_done",
            content=f"{len(web_search_results)} caractères de contexte web" if web_search_results else "Aucun résultat",
        )

        # Build context message with web search results
        context_msg = f"Question stratégique : {request.question}"
        if request.context:
            context_msg += f"\n\nContexte fourni : {request.context}"
        if web_search_results:
            context_msg += f"\n\n{web_search_results}"

        # Get user context (profile + THERESE.md)
        user_context = _get_user_context()

        # PRE-LOAD all LLM services BEFORE parallel execution (avoid SQLite concurrency issues)
        advisor_services: dict[AdvisorRole, tuple] = {}  # role -> (llm_service, actual_provider)
        for role in advisors:
            config = ADVISOR_CONFIG[role]
            preferred_provider = config.get("preferred_provider")
            advisor_llm = None
            actual_provider = default_llm.config.provider.value
            if preferred_provider:
                advisor_llm = get_llm_service_for_provider(preferred_provider)
                if advisor_llm:
                    actual_provider = preferred_provider
                    logger.info(f"Advisor {config['name']} using {preferred_provider}")
                else:
                    logger.info(f"Advisor {config['name']} fallback to default")
            llm_service = advisor_llm or default_llm
            advisor_services[role] = (llm_service, actual_provider)

        # Queue for collecting chunks from parallel advisors
        chunk_queue: asyncio.Queue[BoardDeliberationChunk | None] = asyncio.Queue()
        opinions_dict: dict[AdvisorRole, AdvisorOpinion] = {}

        async def process_advisor(role: AdvisorRole):
            """Process a single advisor and put chunks in the queue."""
            config = ADVISOR_CONFIG[role]
            llm_service, actual_provider = advisor_services[role]

            # Signal advisor start
            await chunk_queue.put(BoardDeliberationChunk(
                type="advisor_start",
                role=role,
                name=config["name"],
                emoji=config["emoji"],
                provider=actual_provider,
            ))

            # Build system prompt with user context
            advisor_system = config["system_prompt"]
            if user_context:
                advisor_system = f"{config['system_prompt']}\n\n{user_context}"

            messages = [LLMMessage(role="user", content=context_msg)]
            context = llm_service.prepare_context(messages, system_prompt=advisor_system)

            # Stream response
            full_content = ""
            try:
                async for chunk in llm_service.stream_response(context):
                    full_content += chunk
                    await chunk_queue.put(BoardDeliberationChunk(
                        type="advisor_chunk",
                        role=role,
                        name=config["name"],
                        emoji=config["emoji"],
                        provider=actual_provider,
                        content=chunk,
                    ))
            except Exception as e:
                logger.error(f"Error getting opinion from {config['name']}: {e}")
                full_content = f"Désolé, une erreur s'est produite: {str(e)}"
                await chunk_queue.put(BoardDeliberationChunk(
                    type="advisor_chunk",
                    role=role,
                    provider=actual_provider,
                    content=full_content,
                ))

            # Record opinion
            opinions_dict[role] = AdvisorOpinion(
                role=role,
                name=config["name"],
                emoji=config["emoji"],
                content=full_content,
            )

            # Signal advisor done
            await chunk_queue.put(BoardDeliberationChunk(
                type="advisor_done",
                role=role,
                name=config["name"],
                emoji=config["emoji"],
                provider=actual_provider,
                content=full_content,
            ))

        # Launch all advisors in parallel
        tasks = [asyncio.create_task(process_advisor(role)) for role in advisors]

        # Yield chunks as they arrive
        completed = 0
        total = len(advisors)

        async def monitor_tasks():
            """Signal when all tasks are done."""
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # Log les erreurs individuelles sans crasher la deliberation
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Advisor task {i} failed: {result}")
            await chunk_queue.put(None)  # Sentinel to stop the loop

        monitor = asyncio.create_task(monitor_tasks())

        while True:
            chunk = await chunk_queue.get()
            if chunk is None:
                break
            yield chunk
            if chunk.type == "advisor_done":
                completed += 1

        # Wait for monitor to finish
        await monitor

        # Build opinions list in order
        opinions = [opinions_dict[role] for role in advisors if role in opinions_dict]

        # Generate synthesis (use default LLM for best quality)
        yield BoardDeliberationChunk(type="synthesis_start", content="")

        synthesis = await self._generate_synthesis(request.question, opinions, default_llm)

        # Save decision to SQLite BEFORE sending synthesis chunk
        # (to ensure persistence even if client disconnects after receiving synthesis)
        decision_id = str(uuid4())
        logger.info(f"Saving board decision {decision_id} to SQLite...")
        if self._session:
            try:
                db_decision = BoardDecisionDB(
                    id=decision_id,
                    question=request.question,
                    context=request.context,
                    opinions=json.dumps([op.model_dump(mode="json") for op in opinions], ensure_ascii=False),
                    synthesis=json.dumps(synthesis.model_dump(mode="json"), ensure_ascii=False),
                    confidence=synthesis.confidence,
                    recommendation=synthesis.recommendation,
                )
                self._session.add(db_decision)
                await self._session.commit()
                logger.info(f"Board decision saved: {decision_id}")
            except Exception as e:
                logger.error(f"Failed to save board decision: {e}", exc_info=True)
                try:
                    await self._session.rollback()
                except Exception:
                    pass
        else:
            logger.warning("No session provided, decision not persisted")

        # Stream synthesis as JSON (after saving to ensure persistence)
        yield BoardDeliberationChunk(
            type="synthesis_chunk",
            content=json.dumps(synthesis.model_dump(), ensure_ascii=False),
        )

        # Signal done
        yield BoardDeliberationChunk(
            type="done",
            content=decision_id,
        )

    async def _generate_synthesis(
        self,
        question: str,
        opinions: list[AdvisorOpinion],
        llm_service,
    ) -> BoardSynthesis:
        """Génère une synthèse à partir des avis des conseillers."""

        # Build synthesis prompt
        opinions_text = "\n\n".join([
            f"**{op.emoji} {op.name}:**\n{op.content}"
            for op in opinions
        ])

        synthesis_prompt = f"""Analyse les avis des conseillers et génère une synthèse structurée.

QUESTION STRATÉGIQUE :
{question}

AVIS DES CONSEILLERS :
{opinions_text}

GÉNÈRE UNE SYNTHÈSE AU FORMAT JSON :
{{
  "consensus_points": ["Point 1 sur lequel tous s'accordent", "Point 2..."],
  "divergence_points": ["Point de désaccord 1", "Point de désaccord 2..."],
  "recommendation": "La recommandation finale claire et actionnable",
  "confidence": "high|medium|low",
  "next_steps": ["Étape 1 à faire", "Étape 2...", "Étape 3..."]
}}

RÈGLES :
- consensus_points : 2-4 points maximum
- divergence_points : 1-3 points si pertinent
- recommendation : 1-2 phrases claires
- confidence : "high" si consensus fort, "medium" si quelques divergences, "low" si beaucoup de désaccords
- next_steps : 3-5 étapes concrètes

Réponds UNIQUEMENT avec le JSON, sans texte avant ou après."""

        messages = [
            LLMMessage(role="user", content=synthesis_prompt),
        ]

        context = llm_service.prepare_context(messages)

        # Generate synthesis
        full_response = ""
        async for chunk in llm_service.stream_response(context):
            full_response += chunk

        # Parse JSON response
        try:
            # Clean up response (remove markdown code blocks if present)
            cleaned = full_response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            data = json.loads(cleaned)
            return BoardSynthesis(**data)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to parse synthesis JSON: {e}")
            logger.error(f"Raw response: {full_response}")
            # Return fallback synthesis
            return BoardSynthesis(
                consensus_points=["Analyse en cours..."],
                divergence_points=[],
                recommendation="Veuillez reformuler votre question pour obtenir une meilleure synthèse.",
                confidence="low",
                next_steps=["Reformuler la question", "Consulter le board à nouveau"],
            )

    async def get_decision(self, decision_id: str) -> Optional[BoardDecision]:
        """Récupère une décision par son ID depuis SQLite."""
        if not self._session:
            return None

        result = await self._session.execute(
            select(BoardDecisionDB).where(BoardDecisionDB.id == decision_id)
        )
        db_decision = result.scalar_one_or_none()
        if not db_decision:
            return None

        return self._db_to_model(db_decision)

    async def list_decisions(self, limit: int = 50) -> list[BoardDecision]:
        """Liste les dernières décisions depuis SQLite."""
        if not self._session:
            return []

        result = await self._session.execute(
            select(BoardDecisionDB)
            .order_by(BoardDecisionDB.created_at.desc())
            .limit(limit)
        )
        db_decisions = result.scalars().all()
        return [self._db_to_model(d) for d in db_decisions]

    async def delete_decision(self, decision_id: str) -> bool:
        """Supprime une décision de SQLite."""
        if not self._session:
            return False

        result = await self._session.execute(
            select(BoardDecisionDB).where(BoardDecisionDB.id == decision_id)
        )
        db_decision = result.scalar_one_or_none()
        if not db_decision:
            return False

        await self._session.delete(db_decision)
        await self._session.commit()
        return True

    def _db_to_model(self, db: BoardDecisionDB) -> BoardDecision:
        """Convertit un BoardDecisionDB en BoardDecision."""
        opinions_data = json.loads(db.opinions)
        synthesis_data = json.loads(db.synthesis)

        return BoardDecision(
            id=db.id,
            question=db.question,
            context=db.context,
            opinions=[AdvisorOpinion(**op) for op in opinions_data],
            synthesis=BoardSynthesis(**synthesis_data),
            created_at=db.created_at,
        )
