"""
THÉRÈSE v2 - Swarm Orchestrator

Orchestre le flow : User → Thérèse (PM) → Zézette (Dev) → Review.
Communication via asyncio.Queue (pattern board.py).
"""

import json
import logging
import re
from typing import AsyncGenerator

from app.models.schemas_agents import AgentStreamChunk
from app.services.agents.config import get_agent_config
from app.services.agents.git_service import GitService
from app.services.agents.runtime import AgentRuntime
from app.services.agents.tools import (
    THERESE_TOOLS,
    ZEZETTE_TOOLS,
    AgentToolExecutor,
)

logger = logging.getLogger(__name__)


def _get_agent_model(agent_id: str) -> str | None:
    """Lit le modèle choisi pour un agent depuis la DB."""
    try:
        import sqlite3

        from app.config import settings

        db_path = settings.db_path
        if db_path and db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.execute(
                "SELECT value FROM preferences WHERE key = ?",
                (f"agent_{agent_id}_model",),
            )
            row = cursor.fetchone()
            conn.close()
            if row and row[0]:
                return row[0]
    except Exception:
        pass
    return None


class SwarmOrchestrator:
    """Orchestre les agents Thérèse et Zézette pour traiter une demande utilisateur."""

    def __init__(self, source_path: str) -> None:
        self.source_path = source_path
        self.git = GitService(source_path)

    async def process_request(
        self,
        user_message: str,
        task_id: str,
    ) -> AsyncGenerator[AgentStreamChunk, None]:
        """
        Traite une demande utilisateur en streaming.

        Flow :
        1. Thérèse analyse la demande (guide ou amélioration ?)
        2. Si amélioration → Thérèse rédige une spec
        3. Zézette implémente sur une branche
        4. Thérèse explique les changements
        5. L'utilisateur review dans l'UI
        """
        # --- Phase 1 : Thérèse analyse ---
        yield AgentStreamChunk(
            type="agent_start",
            agent="katia",
            content="Analyse de votre demande...",
            task_id=task_id,
            phase="spec",
        )

        katia_config = get_agent_config("katia")
        katia_tools = AgentToolExecutor(self.source_path)
        katia_model = _get_agent_model("katia")
        katia_runtime = AgentRuntime(katia_config, katia_tools, THERESE_TOOLS, model_override=katia_model)

        # Thérèse traite le message
        spec_content = ""
        is_improvement_request = False
        clarification_question = ""
        explanation_content = ""
        full_response = ""

        async for event in katia_runtime.run(user_message):
            if event.type == "chunk":
                full_response += event.content
                yield AgentStreamChunk(
                    type="agent_chunk",
                    agent="katia",
                    content=event.content,
                    task_id=task_id,
                )
            elif event.type == "tool_call":
                yield AgentStreamChunk(
                    type="tool_use",
                    agent="katia",
                    tool_name=event.tool_name,
                    task_id=task_id,
                )
            elif event.type == "tool_result":
                result = event.tool_result or ""
                if result.startswith("[SPEC]"):
                    spec_content = result[6:]
                    is_improvement_request = True
                elif result.startswith("[CLARIFY]"):
                    clarification_question = result[9:]
                elif result.startswith("[EXPLAIN]"):
                    explanation_content = result[9:]
            elif event.type == "error":
                yield AgentStreamChunk(
                    type="error",
                    agent="katia",
                    content=event.content,
                    task_id=task_id,
                )
                return

        yield AgentStreamChunk(
            type="agent_done",
            agent="katia",
            content=full_response,
            task_id=task_id,
        )

        # Si Thérèse pose une question de clarification, on s'arrête là
        if clarification_question:
            yield AgentStreamChunk(
                type="done",
                task_id=task_id,
                content=clarification_question,
                phase="spec",
            )
            return

        # Si ce n'est pas une demande d'amélioration (juste une question guide), on s'arrête
        if not is_improvement_request:
            yield AgentStreamChunk(
                type="done",
                task_id=task_id,
                content=full_response,
                phase="done",
            )
            return

        # --- Phase 2 : Handoff Thérèse → Zézette ---
        yield AgentStreamChunk(
            type="handoff",
            agent="katia",
            content=spec_content,
            task_id=task_id,
            phase="analysis",
        )

        # --- Phase 3 : Zézette implémente ---
        branch_name = f"agent/{task_id[:8]}-{_slugify(spec_content[:50])}"

        # Préparer git
        if not await self.git.is_repo():
            yield AgentStreamChunk(
                type="error",
                agent="zezette",
                content="Le chemin source n'est pas un dépôt git",
                task_id=task_id,
            )
            return

        # Sauvegarder la branche courante pour y revenir après
        original_branch = await self.git.current_branch()

        # Créer la branche de travail
        yield AgentStreamChunk(
            type="agent_start",
            agent="zezette",
            content=f"Création de la branche {branch_name}...",
            task_id=task_id,
            phase="implementation",
        )

        if not await self.git.create_branch(branch_name):
            yield AgentStreamChunk(
                type="error",
                agent="zezette",
                content=f"Impossible de créer la branche {branch_name}",
                task_id=task_id,
            )
            await self.git.checkout(original_branch)
            return

        # Lancer Zézette avec la spec
        zezette_config = get_agent_config("zezette")
        zezette_tools = AgentToolExecutor(self.source_path, git_service=self.git)
        zezette_model = _get_agent_model("zezette")
        zezette_runtime = AgentRuntime(zezette_config, zezette_tools, ZEZETTE_TOOLS, model_override=zezette_model)

        zezette_prompt = f"""Tu as reçu cette spécification de Thérèse :

{spec_content}

Tu es sur la branche `{branch_name}`. Implémente les changements demandés.

Étapes :
1. Lis les fichiers concernés pour comprendre le code existant
2. Implémente les modifications
3. Lance les tests pour vérifier
4. Résume ce que tu as fait
"""
        zezette_response = ""

        async for event in zezette_runtime.run(zezette_prompt):
            if event.type == "chunk":
                zezette_response += event.content
                yield AgentStreamChunk(
                    type="agent_chunk",
                    agent="zezette",
                    content=event.content,
                    task_id=task_id,
                )
            elif event.type == "tool_call":
                yield AgentStreamChunk(
                    type="tool_use",
                    agent="zezette",
                    tool_name=event.tool_name,
                    task_id=task_id,
                    phase="implementation",
                )
            elif event.type == "tool_result":
                # Signaler les résultats de tests
                if event.tool_name == "run_command":
                    yield AgentStreamChunk(
                        type="test_result",
                        agent="zezette",
                        content=event.tool_result or "",
                        task_id=task_id,
                    )
            elif event.type == "error":
                yield AgentStreamChunk(
                    type="error",
                    agent="zezette",
                    content=event.content,
                    task_id=task_id,
                )
                # Nettoyer : revenir sur la branche originale
                await self.git.checkout(original_branch)
                await self.git.delete_branch(branch_name)
                return

        yield AgentStreamChunk(
            type="agent_done",
            agent="zezette",
            content=zezette_response,
            task_id=task_id,
        )

        # Commit les changements
        await self.git.commit(
            f"[agent] {spec_content.split(chr(10))[0][:80]}"
        )

        # --- Phase 4 : Générer le diff et préparer la review ---
        await self.git.diff(base=original_branch)  # Génère le diff pour review
        files_changed = await self.git.diff_files(base=original_branch)
        additions, deletions = await self.git.count_changes(base=original_branch)
        diff_stat = await self.git.diff_stat(base=original_branch)

        # Revenir sur la branche originale (le diff reste sur la branche agent)
        await self.git.checkout(original_branch)

        yield AgentStreamChunk(
            type="review_ready",
            task_id=task_id,
            branch=branch_name,
            files_changed=[f["file_path"] for f in files_changed],
            diff_summary=diff_stat,
            phase="review",
        )

        # --- Phase 5 : Thérèse explique les changements ---
        yield AgentStreamChunk(
            type="agent_start",
            agent="katia",
            content="Explication des changements...",
            task_id=task_id,
            phase="review",
        )

        explain_prompt = f"""Zézette a implémenté les changements suivants :

## Résumé
{diff_stat}

## Fichiers modifiés
{json.dumps([f['file_path'] for f in files_changed], ensure_ascii=False)}

## Réponse de Zézette
{zezette_response[:3000]}

Explique à l'utilisateur ce qui a changé en langage simple (pas de jargon technique).
Utilise l'outil explain_change pour structurer ton explication.
"""

        explain_response = ""
        async for event in katia_runtime.run(explain_prompt):
            if event.type == "chunk":
                explain_response += event.content
                yield AgentStreamChunk(
                    type="explanation",
                    agent="katia",
                    content=event.content,
                    task_id=task_id,
                )
            elif event.type == "tool_result":
                result = event.tool_result or ""
                if result.startswith("[EXPLAIN]"):
                    explanation_content = result[9:]

        yield AgentStreamChunk(
            type="agent_done",
            agent="katia",
            content=explain_response,
            task_id=task_id,
        )

        # --- Terminé → en attente de review ---
        yield AgentStreamChunk(
            type="done",
            task_id=task_id,
            branch=branch_name,
            phase="review",
            content=explanation_content or explain_response,
        )


def _slugify(text: str) -> str:
    """Convertit un texte en slug pour les noms de branche."""
    text = text.lower().strip()
    text = re.sub(r"[àâä]", "a", text)
    text = re.sub(r"[éèêë]", "e", text)
    text = re.sub(r"[îï]", "i", text)
    text = re.sub(r"[ôö]", "o", text)
    text = re.sub(r"[ùûü]", "u", text)
    text = re.sub(r"[ç]", "c", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text[:40]
