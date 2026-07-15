"""
THÉRÈSE v2 - Board de Décision - Service

Service pour la délibération multi-conseillers.
Persistance SQLite pour les décisions.
"""

import asyncio
import json
import logging
from typing import AsyncGenerator
from uuid import uuid4

from app.models.board import (
    ADVISOR_CONFIG,
    AdvisorOpinion,
    AdvisorRole,
    BoardDecision,
    BoardDeliberationChunk,
    BoardMode,
    BoardRequest,
    BoardSynthesis,
)
from app.models.entities import BoardDecisionDB
from app.services.llm import (
    LLMProvider,
    get_llm_service,
    get_llm_service_for_provider,
    load_therese_md,
)
from app.services.llm import Message as LLMMessage
from app.services.user_profile import get_cached_profile
from app.services.web_search import WebSearchService
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

logger = logging.getLogger(__name__)


def validate_advisor_providers() -> bool:
    """
    Vérifie que les 5 conseillers utilisent des providers distincts.

    Returns:
        True si 5 providers distincts, False sinon
    """
    providers_used = set()
    for _role, config in ADVISOR_CONFIG.items():
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
        # format_brief : on omet l'identite legale (SIRET/TVA/NDA), inutile aux
        # conseillers et bruyante dans une deliberation strategique.
        context_parts.append(f"## Utilisateur\n{profile.format_brief()}")

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
        self._last_web_sources: list[dict[str, str]] = []
        self._last_synthesis_usage: dict[str, str | int | float] = {}
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
            self._last_web_sources = []
            logger.info(f"Recherche web pour le Board: {question[:50]}...")
            response = await self._web_search.search(question, max_results=5)

            if not response.results:
                logger.info("Aucun résultat de recherche web")
                return ""

            # Format results for injection
            results_text = "## Recherche Web (informations actualisées)\n\n"
            for i, result in enumerate(response.results, 1):
                self._last_web_sources.append({
                    "title": result.title,
                    "url": result.url,
                    "snippet": result.snippet,
                })
                results_text += f"**{i}. {result.title}**\n"
                results_text += f"{result.snippet}\n"
                results_text += f"Source: {result.url}\n\n"

            logger.info(f"Recherche web: {len(response.results)} résultats trouvés")
            return results_text

        except Exception as e:
            logger.warning(f"Échec recherche web pour Board: {e}")
            return ""

    def _track_usage(
        self,
        llm_service,
        input_text: str,
        output_text: str,
        usage_sink: dict | None = None,
    ) -> dict[str, str | int | float]:
        """BUG-027 : alimente le token tracker global pour les appels LLM du board.

        Sans ça, l'usage quotidien/mensuel sous-comptait les délibérations (le board
        faisait de vrais appels providers sans jamais nourrir le tracker) - rapport
        Syn 14/06. Usage réel (usage_sink, cf llm.py stream_response) quand
        disponible, sinon estimation ~2 tokens/mot en filet (providers pas
        encore migrés, cf CLAUDE.md).
        conversation_id="board" : simple étiquette (le tracker ne pose pas de FK)."""
        usage_sink = usage_sink or {}
        try:
            from app.services.token_tracker import get_token_tracker
            input_tokens = usage_sink.get("input_tokens") or len(input_text.split()) * 2
            output_tokens = usage_sink.get("output_tokens") or len(output_text.split()) * 2
            record = get_token_tracker().record_usage(
                conversation_id="board",
                model=llm_service.config.model,
                provider=llm_service.config.provider.value,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
            return {
                "provider": llm_service.config.provider.value,
                "model": llm_service.config.model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_eur": record.cost_eur,
            }
        except Exception as e:
            logger.debug(f"Board token tracking ignoré: {e}")
            return {
                "provider": llm_service.config.provider.value,
                "model": llm_service.config.model,
                "input_tokens": usage_sink.get("input_tokens") or len(input_text.split()) * 2,
                "output_tokens": usage_sink.get("output_tokens") or len(output_text.split()) * 2,
                "cost_eur": 0.0,
            }

    async def deliberate(
        self,
        request: BoardRequest,
    ) -> AsyncGenerator[BoardDeliberationChunk, None]:
        """
        Lance une délibération du board en streaming.

        Mode cloud : providers multiples en parallèle + recherche web.
        Mode souverain : Ollama séquentiel, pas de recherche web.

        Yields chunks pour chaque conseiller puis la synthèse.
        """
        is_sovereign = request.mode == BoardMode.SOVEREIGN
        # En mode souverain, aucun service cloud ne doit devenir un filet de
        # secours implicite. Le service par défaut n'est donc chargé qu'en mode
        # cloud. Ollama doit être réellement disponible, sinon on échoue.
        default_llm = None if is_sovereign else get_llm_service()
        advisors = request.advisors or list(AdvisorRole)

        # --- Recherche web (cloud uniquement) ---
        web_search_results = ""
        if not is_sovereign:
            yield BoardDeliberationChunk(
                type="web_search_start",
                content="Recherche d'informations actualisées...",
            )
            web_search_results = await self._search_web_for_context(request.question)
            yield BoardDeliberationChunk(
                type="web_search_done",
                content=f"{len(web_search_results)} caractères de contexte web" if web_search_results else "Aucun résultat",
            )

        # --- Contexte commun ---
        context_msg = f"Question stratégique : {request.question}"
        if request.context:
            context_msg += f"\n\nContexte fourni : {request.context}"
        if web_search_results:
            context_msg += f"\n\n{web_search_results}"

        user_context = _get_user_context()
        opinions: list[AdvisorOpinion] = []

        if is_sovereign:
            # --- MODE SOUVERAIN : séquentiel via Ollama ---
            logger.info("Board en mode souverain (Ollama séquentiel)")

            # Déterminer le modèle Ollama par défaut (celui sélectionné par l'utilisateur).
            # BUG-098 : ne plus coder "mistral-nemo:12b" en dur. Si l'utilisateur n'a
            # pas choisi de modèle, détecter le 1er modèle conversationnel installé
            # (en excluant les modèles d'embedding utilisés par Qdrant).
            default_ollama_model = None
            try:
                user_llm = get_llm_service()
                if user_llm and user_llm.config.provider == LLMProvider.OLLAMA:
                    default_ollama_model = user_llm.config.model
            except Exception as e:
                logger.debug("LLM service non disponible pour Board: %s", e)
            if not default_ollama_model:
                from app.services.llm import detect_default_ollama_model
                default_ollama_model = detect_default_ollama_model()

            for role in advisors:
                config = ADVISOR_CONFIG[role]
                ollama_model = (request.ollama_models or {}).get(role.value, default_ollama_model)

                # Obtenir le service Ollama avec le modèle choisi
                ollama_llm = get_llm_service_for_provider("ollama", model_override=ollama_model)
                if not ollama_llm:
                    ollama_llm = get_llm_service_for_provider("ollama")
                if not ollama_llm:
                    raise RuntimeError(
                        "Mode souverain indisponible : aucun service Ollama local utilisable."
                    )
                llm_service = ollama_llm
                actual_provider = f"ollama:{ollama_llm.config.model}"

                yield BoardDeliberationChunk(
                    type="advisor_start",
                    role=role,
                    name=config["name"],
                    emoji=config["emoji"],
                    provider=actual_provider,
                )

                advisor_system = config["system_prompt"]
                if user_context:
                    advisor_system = f"{config['system_prompt']}\n\n{user_context}"

                messages = [LLMMessage(role="user", content=context_msg)]
                context = llm_service.prepare_context(messages, system_prompt=advisor_system)

                full_content = ""
                usage_sink: dict = {}
                try:
                    async for chunk in llm_service.stream_response(context, usage_sink=usage_sink):
                        full_content += chunk
                        yield BoardDeliberationChunk(
                            type="advisor_chunk",
                            role=role,
                            name=config["name"],
                            emoji=config["emoji"],
                            provider=actual_provider,
                            content=chunk,
                        )
                except Exception as e:
                    logger.error(f"Sovereign advisor {config['name']} error: {e}")
                    raise RuntimeError(
                        f"Le conseiller {config['name']} n'a pas pu répondre via Ollama."
                    ) from e

                usage = self._track_usage(
                    llm_service,
                    advisor_system + context_msg,
                    full_content,
                    usage_sink,
                ) or {}
                opinions.append(AdvisorOpinion(
                    role=role,
                    name=config["name"],
                    emoji=config["emoji"],
                    content=full_content,
                    provider=str(usage.get("provider") or llm_service.config.provider.value),
                    model=str(usage.get("model") or llm_service.config.model),
                    input_tokens=int(usage.get("input_tokens") or 0),
                    output_tokens=int(usage.get("output_tokens") or 0),
                    cost_eur=float(usage.get("cost_eur") or 0.0),
                ))

                yield BoardDeliberationChunk(
                    type="advisor_done",
                    role=role,
                    name=config["name"],
                    emoji=config["emoji"],
                    provider=actual_provider,
                    content=full_content,
                )

        else:
            # --- MODE CLOUD : parallèle multi-providers ---
            # PRE-LOAD all LLM services BEFORE parallel execution (avoid SQLite concurrency issues)
            if default_llm is None:
                raise RuntimeError("Aucun service LLM cloud disponible.")
            advisor_services: dict[AdvisorRole, tuple] = {}
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

            chunk_queue: asyncio.Queue[BoardDeliberationChunk | None] = asyncio.Queue()
            opinions_dict: dict[AdvisorRole, AdvisorOpinion] = {}

            # Anti-429 (vérif Syn) : en mono-provider, les 5 conseillers retombent
            # sur le même fournisseur. Lancer 5 appels d'un coup sur une seule clé
            # déclenche un rate-limit (429) et des avis vides. On limite donc la
            # concurrence PAR fournisseur (≤2) : aucune limite en multi-provider
            # (chaque clé a peu d'avis), mais plus de burst sur une clé unique.
            provider_semaphores: dict[str, asyncio.Semaphore] = {
                prov: asyncio.Semaphore(2)
                for _, prov in advisor_services.values()
            }

            async def process_advisor(role: AdvisorRole):
                """Process a single advisor and put chunks in the queue."""
                config = ADVISOR_CONFIG[role]
                llm_service, actual_provider = advisor_services[role]

                await chunk_queue.put(BoardDeliberationChunk(
                    type="advisor_start",
                    role=role,
                    name=config["name"],
                    emoji=config["emoji"],
                    provider=actual_provider,
                ))

                advisor_system = config["system_prompt"]
                if user_context:
                    advisor_system = f"{config['system_prompt']}\n\n{user_context}"

                messages = [LLMMessage(role="user", content=context_msg)]
                context = llm_service.prepare_context(messages, system_prompt=advisor_system)

                full_content = ""
                usage_sink: dict = {}
                try:
                    # Sémaphore par fournisseur : au plus 2 appels simultanés sur
                    # une même clé (anti-429). advisor_start a déjà été émis, donc
                    # l'UI montre tous les conseillers « en réflexion » pendant
                    # que les appels s'étalent.
                    async with provider_semaphores[actual_provider]:
                        async for chunk in llm_service.stream_response(context, usage_sink=usage_sink):
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
                    raise RuntimeError(
                        f"Le conseiller {config['name']} n'a pas pu terminer son avis."
                    ) from e

                usage = self._track_usage(
                    llm_service,
                    advisor_system + context_msg,
                    full_content,
                    usage_sink,
                ) or {}
                opinions_dict[role] = AdvisorOpinion(
                    role=role,
                    name=config["name"],
                    emoji=config["emoji"],
                    content=full_content,
                    provider=str(usage.get("provider") or llm_service.config.provider.value),
                    model=str(usage.get("model") or llm_service.config.model),
                    input_tokens=int(usage.get("input_tokens") or 0),
                    output_tokens=int(usage.get("output_tokens") or 0),
                    cost_eur=float(usage.get("cost_eur") or 0.0),
                )

                await chunk_queue.put(BoardDeliberationChunk(
                    type="advisor_done",
                    role=role,
                    name=config["name"],
                    emoji=config["emoji"],
                    provider=actual_provider,
                    content=full_content,
                ))

            tasks = [asyncio.create_task(process_advisor(role)) for role in advisors]

            task_results: list[object] = []

            async def monitor_tasks():
                try:
                    task_results.extend(await asyncio.gather(*tasks, return_exceptions=True))
                finally:
                    await chunk_queue.put(None)

            monitor = asyncio.create_task(monitor_tasks())

            try:
                while True:
                    chunk = await chunk_queue.get()
                    if chunk is None:
                        break
                    yield chunk

                await monitor
            finally:
                # La fermeture du flux HTTP doit réellement interrompre les
                # appels encore en cours. On attend leur annulation avant de
                # quitter afin d'interdire synthèse et persistance tardives.
                for task in tasks:
                    if not task.done():
                        task.cancel()
                if not monitor.done():
                    monitor.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                await asyncio.gather(monitor, return_exceptions=True)

            advisor_errors = [
                result for result in task_results
                if isinstance(result, BaseException)
            ]
            if advisor_errors:
                raise RuntimeError(
                    "La délibération est incomplète : au moins un conseiller a échoué."
                ) from advisor_errors[0]
            opinions = [opinions_dict[role] for role in advisors if role in opinions_dict]

        # --- Synthèse ---
        yield BoardDeliberationChunk(type="synthesis_start", content="")

        # En mode souverain, utiliser Ollama pour la synthèse aussi
        synthesis_llm = default_llm
        if is_sovereign:
            synth_model = (request.ollama_models or {}).get("synthesis", default_ollama_model)
            ollama_synth = get_llm_service_for_provider("ollama", model_override=synth_model)
            if not ollama_synth:
                raise RuntimeError(
                    "Mode souverain indisponible : la synthèse Ollama locale ne peut pas démarrer."
                )
            synthesis_llm = ollama_synth

        synthesis = await self._generate_synthesis(request.question, opinions, synthesis_llm)

        # --- Persistance SQLite ---
        decision_id = str(uuid4())
        logger.info(f"Saving board decision {decision_id} (mode={request.mode.value}) to SQLite...")
        if not self._session:
            raise RuntimeError("La décision ne peut pas être sauvegardée sans session locale.")

        try:
            db_decision = BoardDecisionDB(
                id=decision_id,
                question=request.question,
                context=request.context,
                opinions=json.dumps([op.model_dump(mode="json") for op in opinions], ensure_ascii=False),
                synthesis=json.dumps(synthesis.model_dump(mode="json"), ensure_ascii=False),
                confidence=synthesis.confidence,
                recommendation=synthesis.recommendation,
                mode=request.mode.value,
                web_sources=json.dumps(self._last_web_sources, ensure_ascii=False),
                synthesis_usage=json.dumps(self._last_synthesis_usage, ensure_ascii=False),
            )
            self._session.add(db_decision)
            await self._session.commit()
            if await self.get_decision(decision_id) is None:
                raise RuntimeError("La décision sauvegardée est introuvable.")
            logger.info(f"Board decision saved: {decision_id}")
        except Exception as e:
            logger.error(f"Failed to save board decision: {e}", exc_info=True)
            try:
                await self._session.rollback()
            except Exception as rollback_error:
                logger.debug("Rollback apres erreur save: %s", rollback_error)
            raise RuntimeError("La décision n'a pas pu être sauvegardée localement.") from e

        yield BoardDeliberationChunk(
            type="synthesis_chunk",
            content=json.dumps(synthesis.model_dump(), ensure_ascii=False),
        )

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
        usage_sink: dict = {}
        async for chunk in llm_service.stream_response(context, usage_sink=usage_sink):
            full_response += chunk
        self._last_synthesis_usage = self._track_usage(
            llm_service,
            synthesis_prompt,
            full_response,
            usage_sink,
        ) or {}

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
        except Exception as e:
            logger.error(f"Failed to parse synthesis JSON: {e}")
            logger.error(f"Raw response: {full_response}")
            raise RuntimeError("La synthèse du Board est invalide et ne sera pas sauvegardée.") from e

    async def get_decision(self, decision_id: str) -> BoardDecision | None:
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
            mode=getattr(db, "mode", "cloud"),
            web_sources=json.loads(getattr(db, "web_sources", "[]") or "[]"),
            synthesis_usage=json.loads(getattr(db, "synthesis_usage", "{}") or "{}"),
            created_at=db.created_at,
        )
