"""
THERESE v2 - Performance Router

API endpoints for performance monitoring and optimization.
US-PERF-01 to US-PERF-05.
"""

import logging

from app.models.database import get_session
from app.models.entities import Conversation, Message
from app.services.performance import (
    PowerSettings,
    get_memory_manager,
    get_performance_monitor,
    get_power_settings,
    get_search_index,
    set_power_settings,
)
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# US-PERF-01: Streaming Metrics
# ============================================================


@router.get("/metrics")
async def get_performance_metrics():
    """
    Get performance metrics including first token latency.

    Returns aggregated stats about streaming performance.
    """
    monitor = get_performance_monitor()
    return monitor.get_stats()


@router.get("/metrics/recent")
async def get_recent_metrics(limit: int = 20):
    """
    Get recent streaming metrics.

    Returns the last N streaming request metrics.
    """
    monitor = get_performance_monitor()
    metrics = list(monitor._recent_metrics)[-limit:]
    return {"metrics": metrics, "count": len(metrics)}


# ============================================================
# US-PERF-02: Conversation Pagination & Count
# ============================================================


@router.get("/conversations/count")
async def get_conversations_count(
    session: AsyncSession = Depends(get_session),
):
    """
    Get total conversation count.

    Useful for pagination UI.
    """
    result = await session.execute(
        select(func.count()).select_from(Conversation)
    )
    total = result.scalar() or 0
    return {"total": total}


@router.get("/conversations/search")
async def search_conversations(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    """
    Fast search across conversations (US-PERF-04).

    Uses in-memory index for fast keyword matching.
    Fallback to database if index is empty.
    """
    search_index = get_search_index()
    results = search_index.search(q, limit=limit)

    if results:
        # Return from index
        return {
            "results": [
                {"id": r[0], "title": r[1], "score": r[2]}
                for r in results
            ],
            "source": "index",
            "total": len(results),
        }

    # Fallback to database LIKE search
    logger.info(f"Search index empty, falling back to database for: {q}")
    query = q.lower()

    result = await session.execute(
        select(Conversation)
        .where(Conversation.title.ilike(f"%{query}%"))
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
    )
    conversations = result.scalars().all()

    return {
        "results": [
            {"id": c.id, "title": c.title, "score": 1.0}
            for c in conversations
        ],
        "source": "database",
        "total": len(conversations),
    }


@router.post("/conversations/reindex")
async def reindex_conversations(
    session: AsyncSession = Depends(get_session),
):
    """
    Rebuild the search index from database.

    Call this after importing data or if index is stale.
    """
    search_index = get_search_index()

    # Get all conversations
    result = await session.execute(
        select(Conversation).order_by(Conversation.updated_at.desc())
    )
    conversations = result.scalars().all()

    indexed = 0
    for conv in conversations:
        # Get first user message for content
        msg_result = await session.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .where(Message.role == "user")
            .order_by(Message.created_at)
            .limit(1)
        )
        first_msg = msg_result.scalar_one_or_none()
        content = first_msg.content[:500] if first_msg else ""

        search_index.index_conversation(conv.id, conv.title, content)
        indexed += 1

    stats = search_index.get_stats()
    return {
        "indexed": indexed,
        "stats": stats,
    }


# ============================================================
# US-PERF-03: Memory Management
# ============================================================


@router.get("/memory")
async def get_memory_stats():
    """
    Get memory statistics.

    Shows uptime, GC stats, and cleanup information.
    """
    manager = get_memory_manager()
    return manager.get_memory_stats()


@router.post("/memory/cleanup")
async def trigger_cleanup():
    """
    Trigger memory cleanup.

    Runs registered cleanup callbacks and garbage collection.
    """
    manager = get_memory_manager()
    results = await manager.run_cleanup()
    return {
        "success": True,
        "results": results,
        "stats": manager.get_memory_stats(),
    }


# ============================================================
# US-PERF-05: Power Settings
# ============================================================


@router.get("/power")
async def get_power_config():
    """
    Get current power/battery settings.
    """
    settings = get_power_settings()
    return settings.to_dict()


@router.post("/power")
async def set_power_config(
    health_check_interval: int | None = None,
    conversation_sync_interval: int | None = None,
    battery_saver_mode: bool | None = None,
    reduce_animations: bool | None = None,
):
    """
    Update power/battery settings.

    Pass only the settings you want to change.
    """
    current = get_power_settings()

    new_settings = PowerSettings(
        health_check_interval=health_check_interval or current.health_check_interval,
        conversation_sync_interval=conversation_sync_interval or current.conversation_sync_interval,
        battery_saver_mode=battery_saver_mode if battery_saver_mode is not None else current.battery_saver_mode,
        reduce_animations=reduce_animations if reduce_animations is not None else current.reduce_animations,
    )

    set_power_settings(new_settings)
    return new_settings.to_dict()


@router.post("/power/battery-saver")
async def enable_battery_saver(enabled: bool = True):
    """
    Enable or disable battery saver mode.

    When enabled, reduces polling intervals and animations.
    """
    if enabled:
        settings = PowerSettings.battery_saver()
    else:
        settings = PowerSettings()  # Default settings

    set_power_settings(settings)
    return {
        "battery_saver_enabled": enabled,
        "settings": settings.to_dict(),
    }


# ============================================================
# Combined Status Endpoint
# ============================================================


@router.get("/status")
async def get_performance_status(
    session: AsyncSession = Depends(get_session),
):
    """
    Get combined performance status.

    Returns metrics, memory stats, and power settings.
    """
    monitor = get_performance_monitor()
    manager = get_memory_manager()
    search_index = get_search_index()
    power = get_power_settings()

    # Get conversation count
    result = await session.execute(
        select(func.count()).select_from(Conversation)
    )
    conv_count = result.scalar() or 0

    return {
        "streaming": monitor.get_stats(),
        "memory": manager.get_memory_stats(),
        "search_index": search_index.get_stats(),
        "power": power.to_dict(),
        "conversations_total": conv_count,
    }
