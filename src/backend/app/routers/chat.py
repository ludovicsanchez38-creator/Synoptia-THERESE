"""
THERESE v2 - Chat Router

Endpoints for chat and conversation management.
"""

import asyncio
import json
import logging
import re
import time
from typing import AsyncGenerator

from app.config import settings
from app.models.database import get_session
from app.models.entities import Contact, Conversation, FileMetadata, Message, Project
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationResponse,
    MessageResponse,
    StreamChunk,
)
from app.services.entity_extractor import (
    get_entity_extractor,
)
from app.services.file_parser import chunk_text, extract_text, get_file_metadata
from app.services.llm import (
    ContextWindow,
    LLMService,
    ToolCall,
    ToolResult,
    get_llm_service,
)
from app.services.llm import (
    Message as LLMMessage,
)
from app.services.mcp_service import get_mcp_service
from app.services.memory_tools import MEMORY_TOOL_NAMES, MEMORY_TOOLS, execute_memory_tool
from app.services.path_security import validate_file_path
from app.services.performance import get_performance_monitor, get_search_index
from app.services.qdrant import get_qdrant_service
from app.services.token_tracker import detect_uncertainty, get_token_tracker
from app.services.web_search import WEB_SEARCH_TOOL, execute_web_search
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# Generation Cancellation (US-ERR-04)
# ============================================================

# Track active generations for cancellation
_active_generations: dict[str, bool] = {}
# Timestamps pour detecter les entrees orphelines (client deconnecte)
_generation_timestamps: dict[str, float] = {}
# Duree max avant nettoyage automatique (5 minutes)
_GENERATION_TIMEOUT_S = 300


def _register_generation(conversation_id: str) -> None:
    """Register an active generation."""
    _active_generations[conversation_id] = False
    _generation_timestamps[conversation_id] = time.monotonic()
    # Nettoyage opportuniste des entrees orphelines
    _cleanup_stale_generations()


def _cancel_generation(conversation_id: str) -> bool:
    """Mark a generation for cancellation. Returns True if generation was active."""
    if conversation_id in _active_generations:
        _active_generations[conversation_id] = True
        return True
    return False


def _is_cancelled(conversation_id: str) -> bool:
    """Check if a generation has been cancelled."""
    return _active_generations.get(conversation_id, False)


def _unregister_generation(conversation_id: str) -> None:
    """Remove a generation from tracking."""
    _active_generations.pop(conversation_id, None)
    _generation_timestamps.pop(conversation_id, None)


def _cleanup_stale_generations() -> None:
    """
    Supprime les entrees plus vieilles que _GENERATION_TIMEOUT_S.

    Appele de maniere opportuniste a chaque nouvelle generation
    pour eviter les fuites memoire si un client se deconnecte
    sans que le stream ne se termine proprement.
    """
    now = time.monotonic()
    stale_ids = [
        cid for cid, ts in _generation_timestamps.items()
        if now - ts > _GENERATION_TIMEOUT_S
    ]
    for cid in stale_ids:
        logger.warning(f"Cleanup generation orpheline: {cid} (age > {_GENERATION_TIMEOUT_S}s)")
        _active_generations.pop(cid, None)
        _generation_timestamps.pop(cid, None)


# ============================================================
# Slash Command Patterns
# ============================================================

# Pattern for /fichier [path] or /analyse [path]
FILE_COMMAND_PATTERN = re.compile(
    r'^/(fichier|analyse)\s+(.+)$',
    re.IGNORECASE | re.MULTILINE
)


def _parse_file_commands(message: str) -> list[tuple[str, str]]:
    """
    Parse /fichier and /analyse commands from message.

    Returns list of (command, path) tuples.
    """
    commands = []
    for match in FILE_COMMAND_PATTERN.finditer(message):
        command = match.group(1).lower()
        path = match.group(2).strip()
        # Remove quotes if present
        if (path.startswith('"') and path.endswith('"')) or \
           (path.startswith("'") and path.endswith("'")):
            path = path[1:-1]
        commands.append((command, path))
    return commands


async def _get_file_context(
    file_path: str,
    session: AsyncSession,
    command: str = "fichier"
) -> tuple[str | None, str | None]:
    """
    Get file content for context injection.

    Args:
        file_path: Path to the file
        session: Database session
        command: Command type ('fichier' or 'analyse')

    Returns:
        Tuple of (context_string, error_message)
    """
    # Validation securite du chemin (SEC-002)
    try:
        path = validate_file_path(file_path)
    except PermissionError as e:
        return None, str(e)
    except FileNotFoundError as e:
        return None, str(e)

    if not path.is_file():
        return None, f"Ce n'est pas un fichier: {file_path}"

    try:
        # Extract text content
        text_content = extract_text(path)

        if not text_content:
            return None, f"Impossible d'extraire le contenu de: {path.name}"

        # Check if file is already indexed
        result = await session.execute(
            select(FileMetadata).where(FileMetadata.path == str(path))
        )
        existing = result.scalar_one_or_none()

        # Index if not already done
        if not existing:
            from datetime import UTC, datetime
            metadata = get_file_metadata(path)

            file_meta = FileMetadata(
                path=str(path),
                name=metadata["name"],
                extension=metadata["extension"],
                size=metadata["size"],
                mime_type=metadata["mime_type"],
            )
            session.add(file_meta)

            # Chunk and store in Qdrant
            chunks = list(chunk_text(text_content, chunk_size=settings.chunk_size, overlap=settings.chunk_overlap))
            qdrant = get_qdrant_service()
            items = []

            for i, chunk in enumerate(chunks):
                items.append({
                    "text": chunk,
                    "memory_type": "file",
                    "entity_id": file_meta.id,
                    "metadata": {
                        "name": file_meta.name,
                        "path": str(path),
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    },
                })

            if items:
                await qdrant.async_add_memories(items)
                logger.info(f"Indexed {len(chunks)} chunks for file {path.name}")

            file_meta.chunk_count = len(chunks)
            file_meta.indexed_at = datetime.now(UTC)
            await session.commit()

        # Build context string
        file_name = path.name
        file_size = path.stat().st_size
        size_str = (
            f"{file_size} B" if file_size < 1024
            else f"{file_size / 1024:.1f} KB" if file_size < 1024 * 1024
            else f"{file_size / (1024 * 1024):.1f} MB"
        )

        # Truncate content if too long
        max_chars = 15000
        if len(text_content) > max_chars:
            text_content = text_content[:max_chars] + f"\n\n[... contenu tronque, {len(text_content)} caracteres au total ...]"

        context = f"""--- FICHIER: {file_name} ({size_str}) ---
Chemin: {path}

{text_content}

--- FIN DU FICHIER ---"""

        return context, None

    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        return None, f"Erreur lors de la lecture de {path.name}: {str(e)}"


# ============================================================
# Memory Context Helper
# ============================================================


async def _get_memory_context(user_message: str, limit: int = 8) -> str | None:
    """
    Search memory for context relevant to the user's message.

    Returns formatted context string or None if no relevant memories found.
    """
    try:
        qdrant = get_qdrant_service()
        results = await qdrant.async_search(
            query=user_message,
            limit=limit,
            score_threshold=0.35,  # Lower threshold for broader context
        )

        if not results:
            return None

        # Format results into context string
        context_parts = []
        seen_files = set()  # Track seen files to avoid duplicates

        for hit in results:
            memory_type = hit.get("type", "")
            text = hit.get("text", "")
            metadata = hit.get("metadata", {})
            score = hit.get("score", 0)

            if memory_type == "contact":
                name = metadata.get("name", "Inconnu")
                context_parts.append(f"**Contact**: {name}\n{text}")
            elif memory_type == "project":
                name = metadata.get("name", "Sans nom")
                status = metadata.get("status", "")
                context_parts.append(f"**Projet** ({status}): {name}\n{text}")
            elif memory_type == "file":
                file_name = metadata.get("name", "fichier")
                chunk_index = metadata.get("chunk_index", 0)
                total_chunks = metadata.get("total_chunks", 1)

                # Only include first occurrence per file to avoid too much context
                if file_name not in seen_files:
                    seen_files.add(file_name)
                    if total_chunks > 1:
                        context_parts.append(
                            f"**Fichier**: {file_name} (extrait {chunk_index + 1}/{total_chunks})\n{text}"
                        )
                    else:
                        context_parts.append(f"**Fichier**: {file_name}\n{text}")
            else:
                context_parts.append(text)

            logger.debug(f"Memory context hit: {memory_type} (score={score:.2f})")

        if context_parts:
            return "\n\n".join(context_parts)

    except Exception as e:
        logger.warning(f"Failed to get memory context: {e}")

    return None


# ============================================================
# Entity Extraction Helper
# ============================================================


async def _get_existing_entity_names(session: AsyncSession) -> tuple[list[str], list[str]]:
    """Get names of existing contacts and projects to avoid duplicates."""
    # Get contact names
    contact_result = await session.execute(select(Contact))
    contacts = contact_result.scalars().all()
    contact_names = [c.display_name for c in contacts if c.display_name]

    # Get project names
    project_result = await session.execute(select(Project))
    projects = project_result.scalars().all()
    project_names = [p.name for p in projects if p.name]

    return contact_names, project_names


async def _extract_entities_background(
    user_message: str,
    conversation_id: str,
    message_id: str,
) -> None:
    """
    Extrait les entités en arrière-plan (PERF-001).

    Les résultats ne sont plus envoyés via SSE (le stream est déjà fermé).
    À terme, ils pourront être envoyés via WebSocket ou polling endpoint.

    NOTE: Cette coroutine crée sa propre session DB car la session FastAPI
    est fermée après la réponse HTTP.
    """
    try:
        from app.models.database import get_session_context

        async with get_session_context() as session:
            extractor = get_entity_extractor()
            contact_names, project_names = await _get_existing_entity_names(session)

        extraction_result = await extractor.extract_entities(
            user_message=user_message,
            existing_contacts=contact_names,
            existing_projects=project_names,
        )

        if extraction_result.contacts or extraction_result.projects:
            logger.info(
                f"[Background] Detected {len(extraction_result.contacts)} contacts, "
                f"{len(extraction_result.projects)} projects in message {message_id}"
            )
            # TODO: Envoyer via WebSocket ou stocker pour polling
            # Pour l'instant, les entites sont loggees mais pas envoyees au frontend
            # Le frontend devra interroger un endpoint GET /api/chat/{conv_id}/entities

    except Exception as e:
        logger.warning(f"[Background] Entity extraction failed: {e}")


# ============================================================
# Chat Endpoints
# ============================================================


@router.post("/cancel/{conversation_id}")
async def cancel_generation(conversation_id: str):
    """
    Cancel an active generation (US-ERR-04).

    Returns True if generation was cancelled, False if not active.
    """
    cancelled = _cancel_generation(conversation_id)
    return {
        "cancelled": cancelled,
        "conversation_id": conversation_id,
    }


@router.post("/send")
async def send_message(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Send a message and get a response.

    Supports both streaming (SSE) and non-streaming responses.
    Also handles /fichier and /analyse slash commands.
    """
    # Get or create conversation
    if request.conversation_id:
        result = await session.execute(
            select(Conversation).where(Conversation.id == request.conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(title=request.message[:50])
        session.add(conversation)
        await session.flush()

    # Load conversation history for context
    history_result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
        .limit(50)  # Limit history to last 50 messages
    )
    history_messages = history_result.scalars().all()
    history = [
        LLMMessage(role=msg.role, content=msg.content)
        for msg in history_messages
    ]

    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message,
    )
    session.add(user_message)
    await session.commit()

    # Handle streaming response
    if request.stream:
        return StreamingResponse(
            _stream_response(conversation.id, request.message, session, history),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Non-streaming response using LLM service
    llm_service = get_llm_service()
    messages = history + [LLMMessage(role="user", content=request.message)]

    # Get relevant memory context
    memory_context = await _get_memory_context(request.message)

    # Check for file commands and add file context
    file_commands = _parse_file_commands(request.message)
    file_contexts = []
    for cmd, path in file_commands:
        file_ctx, error = await _get_file_context(path, session, cmd)
        if file_ctx:
            file_contexts.append(file_ctx)
        elif error:
            logger.warning(f"File command error: {error}")

    # Combine memory and file contexts
    if file_contexts:
        file_context_str = "\n\n".join(file_contexts)
        if memory_context:
            memory_context = f"{memory_context}\n\n{file_context_str}"
        else:
            memory_context = file_context_str

    context = llm_service.prepare_context(messages, memory_context=memory_context)

    # Collect full response (non-streaming)
    assistant_content = ""
    try:
        async for chunk in llm_service.stream_response(context):
            assistant_content += chunk
    except Exception as e:
        logger.error(f"LLM error: {e}")
        assistant_content = f"Desolee, une erreur s'est produite: {str(e)}"

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=assistant_content,
        model=llm_service.config.model,
    )
    session.add(assistant_message)
    await session.commit()

    return ChatResponse(
        id=assistant_message.id,
        conversation_id=conversation.id,
        content=assistant_content,
        created_at=assistant_message.created_at,
    )


async def _stream_response(
    conversation_id: str,
    user_message: str,
    session: AsyncSession,
    history: list[LLMMessage] | None = None,
) -> AsyncGenerator[str, None]:
    """Stream response chunks as Server-Sent Events with MCP tool support."""
    # Register generation for cancellation tracking (US-ERR-04)
    _register_generation(conversation_id)

    try:
        async for chunk in _do_stream_response(
            conversation_id, user_message, session, history
        ):
            # Check for cancellation
            if _is_cancelled(conversation_id):
                yield f"data: {json.dumps({'type': 'cancelled', 'content': ''})}\n\n"
                return
            yield chunk
    finally:
        _unregister_generation(conversation_id)


async def _do_stream_response(
    conversation_id: str,
    user_message: str,
    session: AsyncSession,
    history: list[LLMMessage] | None = None,
) -> AsyncGenerator[str, None]:
    """Internal streaming implementation."""
    # Sprint 2 - PERF-2.11: Check for prompt injection
    from app.services.prompt_security import check_prompt_safety
    security_check = check_prompt_safety(user_message)
    if not security_check.is_safe:
        logger.warning(
            f"Blocked message due to {security_check.threat_type}: "
            f"level={security_check.threat_level.value}"
        )
        yield f"data: {json.dumps({'type': 'error', 'content': 'Message bloqué pour raison de sécurité.'})}\n\n"
        return

    llm_service = get_llm_service()
    mcp_service = get_mcp_service()

    # Start performance tracking (US-PERF-01)
    perf_monitor = get_performance_monitor()
    stream_metrics = perf_monitor.start_stream(
        conversation_id,
        provider=llm_service.config.provider.value,
        model=llm_service.config.model,
    )
    first_token_recorded = False

    # Build context with conversation history
    messages = history or []
    messages.append(LLMMessage(role="user", content=user_message))

    # Get relevant memory context for the user's message
    memory_context = await _get_memory_context(user_message)

    # Check for file commands and add file context
    file_commands = _parse_file_commands(user_message)
    file_contexts = []
    file_errors = []

    for cmd, path in file_commands:
        file_ctx, error = await _get_file_context(path, session, cmd)
        if file_ctx:
            file_contexts.append(file_ctx)
        elif error:
            file_errors.append(error)
            logger.warning(f"File command error: {error}")

    # Send file processing status if we had file commands
    if file_commands:
        status_msg = f"Traitement de {len(file_commands)} fichier(s)..."
        if file_contexts:
            status_msg += f" {len(file_contexts)} charge(s)."
        if file_errors:
            status_msg += f" {len(file_errors)} erreur(s)."

        status_data = StreamChunk(
            type="status",
            content=status_msg,
            conversation_id=conversation_id,
        )
        yield f"data: {json.dumps(status_data.model_dump())}\n\n"

    # Combine memory and file contexts
    if file_contexts:
        file_context_str = "\n\n".join(file_contexts)
        if memory_context:
            memory_context = f"{memory_context}\n\n{file_context_str}"
        else:
            memory_context = file_context_str

    context = llm_service.prepare_context(messages, memory_context=memory_context)

    # Check if web search is enabled
    from app.models.entities import Preference
    result = await session.execute(
        select(Preference).where(Preference.key == "web_search_enabled")
    )
    web_search_pref = result.scalar_one_or_none()
    web_search_enabled = web_search_pref.value.lower() == "true" if web_search_pref else True

    # Get available tools: MCP tools + built-in web search + memory tools
    # Note: For Gemini, web search is handled via native grounding (not tool calling)
    tools = mcp_service.get_tools_for_llm() or []

    # Add memory tools (create_contact, create_project)
    tools = MEMORY_TOOLS + tools

    # Add web_search tool for non-Gemini providers (if enabled)
    if web_search_enabled and llm_service.config.provider.value != "gemini":
        tools = [WEB_SEARCH_TOOL] + tools

    if tools:
        logger.info(f"Providing {len(tools)} tools to LLM")

        # Injecter dynamiquement les capacités dans le system prompt
        # uniquement quand des tools sont disponibles (pas pour les petits modèles sans tools)
        tool_names = [t.get("function", {}).get("name", "") for t in tools if t.get("type") == "function"]
        capabilities = "\n\n## Tes capacités (outils)\nTu disposes d'outils que tu DOIS utiliser quand c'est pertinent. Ne dis JAMAIS que tu ne peux pas accéder à internet ou que tu ne peux pas faire quelque chose si un outil le permet.\n"
        if "web_search" in tool_names:
            capabilities += "- **web_search** : Recherche sur internet. Utilise-le pour toute question sur l'actualité, analyser un site web, ou trouver des informations récentes.\n"
        if "create_contact" in tool_names:
            capabilities += "- **create_contact** / **create_project** : Créer des contacts et projets en mémoire.\n"
        mcp_tools = [n for n in tool_names if n not in ("web_search", "create_contact", "create_project")]
        if mcp_tools:
            capabilities += f"- **Outils externes** : {', '.join(mcp_tools[:10])}{'...' if len(mcp_tools) > 10 else ''}\n"
        context.system_prompt += capabilities

    full_content = ""
    tool_calls_collected: list[ToolCall] = []
    max_tool_iterations = 5  # Prevent infinite tool loops

    try:
        # Stream from LLM with tool support
        async for event in llm_service.stream_response_with_tools(context, tools if tools else None):
            if event.type == "text" and event.content:
                # Record first token latency (US-PERF-01)
                if not first_token_recorded:
                    stream_metrics.record_first_token()
                    first_token_recorded = True
                stream_metrics.record_token()

                full_content += event.content
                data = StreamChunk(
                    type="text",
                    content=event.content,
                    conversation_id=conversation_id,
                )
                yield f"data: {json.dumps(data.model_dump())}\n\n"

            elif event.type == "tool_call" and event.tool_call:
                tool_calls_collected.append(event.tool_call)

            elif event.type == "done":
                # Check if we have tool calls to execute
                if tool_calls_collected and event.stop_reason in ("tool_calls", "tool_use"):
                    # Execute tools and continue
                    async for continued_event in _execute_tools_and_continue(
                        llm_service,
                        mcp_service,
                        context,
                        full_content,
                        tool_calls_collected,
                        tools,
                        conversation_id,
                        max_tool_iterations,
                        session=session,
                    ):
                        if continued_event.startswith("data:"):
                            # Parse the content to accumulate full response
                            try:
                                event_data = json.loads(continued_event[6:].strip())
                                if event_data.get("type") == "text":
                                    full_content += event_data.get("content", "")
                            except json.JSONDecodeError:
                                pass
                        yield continued_event

            elif event.type == "error":
                error_data = StreamChunk(
                    type="error",
                    content=event.content or "Unknown error",
                    conversation_id=conversation_id,
                )
                yield f"data: {json.dumps(error_data.model_dump())}\n\n"
                return

    except Exception as e:
        logger.error(f"LLM streaming error: {e}")
        error_data = StreamChunk(
            type="error",
            content=f"Erreur de generation: {str(e)}",
            conversation_id=conversation_id,
        )
        yield f"data: {json.dumps(error_data.model_dump())}\n\n"
        return

    # Save complete assistant message
    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=full_content,
        model=llm_service.config.model,
    )
    session.add(assistant_message)
    await session.commit()

    # Finish performance tracking (US-PERF-01)
    perf_summary = perf_monitor.finish_stream(conversation_id)

    # Track token usage and costs (US-ESC-02, US-ESC-04)
    token_tracker = get_token_tracker()

    # Estimate token counts from content length (rough approximation)
    input_tokens = len(user_message) // 4  # ~4 chars per token
    output_tokens = perf_summary.get("total_tokens", len(full_content) // 4) if perf_summary else len(full_content) // 4

    usage_record = token_tracker.record_usage(
        conversation_id=conversation_id,
        model=llm_service.config.model,
        provider=llm_service.config.provider.value,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

    # Detect uncertainty in response (US-ESC-01)
    uncertainty = detect_uncertainty(full_content)

    # Send done event with usage info
    done_data = StreamChunk(
        type="done",
        content="",
        conversation_id=conversation_id,
        message_id=assistant_message.id,
    )
    done_dict = done_data.model_dump()
    done_dict["usage"] = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_eur": usage_record.cost_eur,
        "model": llm_service.config.model,
    }
    done_dict["uncertainty"] = uncertainty
    yield f"data: {json.dumps(done_dict)}\n\n"

    # Fire-and-forget entity extraction (PERF-001)
    # L'extraction continue en arrière-plan sans bloquer le stream SSE
    # NOTE: On ne passe PAS la session FastAPI car elle sera fermée après la requête.
    # La background task crée sa propre session via get_session_context().
    asyncio.create_task(
        _extract_entities_background(
            user_message=user_message,
            conversation_id=conversation_id,
            message_id=assistant_message.id,
        )
    )


async def _execute_tools_and_continue(
    llm_service: LLMService,
    mcp_service,
    context: ContextWindow,
    assistant_content: str,
    tool_calls: list[ToolCall],
    tools: list[dict],
    conversation_id: str,
    remaining_iterations: int,
    session: AsyncSession | None = None,
) -> AsyncGenerator[str, None]:
    """
    Execute MCP tools and continue the conversation.

    Handles recursive tool calling up to max_iterations.
    """
    if remaining_iterations <= 0:
        logger.warning("Max tool iterations reached, stopping")
        return

    # Send status about tool execution
    tool_names = [tc.name for tc in tool_calls]
    status_data = StreamChunk(
        type="status",
        content=f"Execution des outils: {', '.join(tool_names)}...",
        conversation_id=conversation_id,
    )
    yield f"data: {json.dumps(status_data.model_dump())}\n\n"

    # Execute each tool call
    tool_results: list[ToolResult] = []

    for tc in tool_calls:
        logger.info(f"Executing tool: {tc.name} with args: {tc.arguments}")

        # Execute based on tool type
        if tc.name == "web_search":
            # Built-in web search tool
            import time
            start_time = time.time()
            try:
                search_result = await execute_web_search(tc.arguments)
                execution_time = (time.time() - start_time) * 1000

                # Create result object compatible with MCP format
                class WebSearchResult:
                    def __init__(self, result_text: str, exec_time: float):
                        self.success = True
                        self.result = result_text
                        self.error = None
                        self.execution_time_ms = exec_time

                result = WebSearchResult(search_result, execution_time)
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000

                class WebSearchError:
                    def __init__(self, error_msg: str, exec_time: float):
                        self.success = False
                        self.result = None
                        self.error = error_msg
                        self.execution_time_ms = exec_time

                result = WebSearchError(str(e), execution_time)
        elif tc.name in MEMORY_TOOL_NAMES:
            # Built-in memory tools (create_contact, create_project)
            import time
            start_time = time.time()
            try:
                if session is None:
                    raise RuntimeError("Database session not available for memory tools")
                tool_result_str = await execute_memory_tool(tc.name, tc.arguments, session)
                execution_time = (time.time() - start_time) * 1000

                class MemoryToolResult:
                    def __init__(self, result_text: str, exec_time: float):
                        self.success = True
                        self.result = result_text
                        self.error = None
                        self.execution_time_ms = exec_time

                result = MemoryToolResult(tool_result_str, execution_time)
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000

                class MemoryToolError:
                    def __init__(self, error_msg: str, exec_time: float):
                        self.success = False
                        self.result = None
                        self.error = error_msg
                        self.execution_time_ms = exec_time

                result = MemoryToolError(str(e), execution_time)
        else:
            # Execute via MCP service
            result = await mcp_service.execute_tool_call(tc.name, tc.arguments)

        # Send tool result status
        if result.success:
            result_preview = str(result.result)[:100]
            if len(str(result.result)) > 100:
                result_preview += "..."

            tool_status = StreamChunk(
                type="tool_result",
                content=f"[{tc.name}] OK ({result.execution_time_ms:.0f}ms): {result_preview}",
                conversation_id=conversation_id,
            )
        else:
            tool_status = StreamChunk(
                type="tool_result",
                content=f"[{tc.name}] Erreur: {result.error}",
                conversation_id=conversation_id,
            )

        yield f"data: {json.dumps(tool_status.model_dump())}\n\n"

        # Build ToolResult for LLM
        tool_results.append(ToolResult(
            tool_call_id=tc.id,
            result=result.result if result.success else f"Error: {result.error}",
            is_error=not result.success,
        ))

    # Continue conversation with tool results
    new_tool_calls: list[ToolCall] = []
    continued_content = ""

    async for event in llm_service.continue_with_tool_results(
        context,
        assistant_content,
        tool_calls,
        tool_results,
        tools,
    ):
        if event.type == "text" and event.content:
            continued_content += event.content
            data = StreamChunk(
                type="text",
                content=event.content,
                conversation_id=conversation_id,
            )
            yield f"data: {json.dumps(data.model_dump())}\n\n"

        elif event.type == "tool_call" and event.tool_call:
            new_tool_calls.append(event.tool_call)

        elif event.type == "done":
            # Check if more tools need to be called
            if new_tool_calls and event.stop_reason in ("tool_calls", "tool_use"):
                # Recursive call for chained tools
                async for nested_event in _execute_tools_and_continue(
                    llm_service,
                    mcp_service,
                    context,  # Note: context doesn't include tool results, that's handled in continue_with_tool_results
                    continued_content,
                    new_tool_calls,
                    tools,
                    conversation_id,
                    remaining_iterations - 1,
                    session=session,
                ):
                    yield nested_event

        elif event.type == "error":
            error_data = StreamChunk(
                type="error",
                content=event.content or "Tool continuation error",
                conversation_id=conversation_id,
            )
            yield f"data: {json.dumps(error_data.model_dump())}\n\n"


# ============================================================
# Conversation Endpoints
# ============================================================


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    """
    List all conversations with message counts.

    Sprint 2 - PERF-2.9: Use COUNT(*) with GROUP BY instead of N+1 queries.
    Before: 1 query for conversations + N queries for message counts
    After: 1 query with LEFT JOIN and GROUP BY
    """
    # Single query with COUNT (Sprint 2 - PERF-2.9)
    stmt = (
        select(
            Conversation,
            func.count(Message.id).label("message_count")
        )
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .group_by(Conversation.id)
        .order_by(Conversation.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await session.execute(stmt)
    rows = result.all()

    return [
        ConversationResponse(
            id=conv.id,
            title=conv.title,
            summary=conv.summary,
            message_count=msg_count,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
        )
        for conv, msg_count in rows
    ]


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new conversation."""
    conversation = Conversation(title=request.title)
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)

    # Index for fast search (US-PERF-04)
    search_index = get_search_index()
    search_index.index_conversation(conversation.id, conversation.title)

    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        summary=conversation.summary,
        message_count=0,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get a specific conversation."""
    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Count messages
    count_result = await session.execute(
        select(func.count()).select_from(Message).where(Message.conversation_id == conversation.id)
    )
    message_count = count_result.scalar() or 0

    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        summary=conversation.summary,
        message_count=message_count,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


@router.get(
    "/conversations/{conversation_id}/messages", response_model=list[MessageResponse]
)
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
):
    """Get messages for a conversation."""
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .limit(limit)
    )
    messages = result.scalars().all()

    return [
        MessageResponse(
            id=msg.id,
            conversation_id=msg.conversation_id,
            role=msg.role,
            content=msg.content,
            tokens_in=msg.tokens_in,
            tokens_out=msg.tokens_out,
            model=msg.model,
            created_at=msg.created_at,
        )
        for msg in messages
    ]


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Delete a conversation and all its messages."""
    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await session.delete(conversation)
    await session.commit()

    return {"deleted": True, "id": conversation_id}
