"""
THÉRÈSE v2 - Agent Configuration

Charge les configurations d'agents au format OpenClaw (agent.json + SOUL.md).
Supporte les overrides utilisateur dans ~/.therese/agents/{agent_id}/.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Chemin des templates livrés avec l'app
_BUILTIN_AGENTS_DIR = Path(__file__).parent.parent.parent / "agents"

# Modèles disponibles pour les agents (flagship de chaque provider)
AVAILABLE_MODELS = [
    # Anthropic
    {"id": "claude-sonnet-4-6", "name": "Claude Sonnet 4.6", "provider": "anthropic", "recommended": True},
    {"id": "claude-opus-4-6", "name": "Claude Opus 4.6", "provider": "anthropic"},
    {"id": "claude-haiku-4-5-20251001", "name": "Claude Haiku 4.5", "provider": "anthropic"},
    # OpenAI
    {"id": "gpt-5.4", "name": "GPT-5.4", "provider": "openai"},
    {"id": "gpt-5.4-pro", "name": "GPT-5.4 Pro", "provider": "openai"},
    # Google
    {"id": "gemini-3.1-pro", "name": "Gemini 3.1 Pro", "provider": "gemini"},
    {"id": "gemini-3.1-flash", "name": "Gemini 3.1 Flash", "provider": "gemini"},
    {"id": "gemini-3.1-flash-lite-preview", "name": "Gemini 3.1 Flash Lite", "provider": "gemini"},
    # xAI
    {"id": "grok-4-1-fast-reasoning", "name": "Grok 4.1 Fast", "provider": "grok"},
    # Mistral
    {"id": "mistral-large-latest", "name": "Mistral Large 3", "provider": "mistral"},
    {"id": "mistral-large-2512", "name": "Mistral Large 3 (fixé)", "provider": "mistral"},
    {"id": "mistral-small-latest", "name": "Mistral Small 3", "provider": "mistral"},
    # OpenRouter (NVIDIA Nemotron 3)
    {"id": "nvidia/nemotron-3-super-120b-a12b", "name": "Nemotron 3 Super 120B", "provider": "openrouter"},
    {"id": "nvidia/nemotron-3-nano-30b-a3b", "name": "Nemotron 3 Nano 30B", "provider": "openrouter"},
    # DeepSeek
    {"id": "deepseek-chat", "name": "DeepSeek Chat", "provider": "deepseek"},
    # Local (Ollama)
    {"id": "qwen3:32b", "name": "Qwen 3 32B (local)", "provider": "ollama"},
    {"id": "mistral-nemo:12b", "name": "Mistral Nemo 12B (local)", "provider": "ollama"},
]


@dataclass
class AgentConfig:
    """Configuration d'un agent."""

    id: str
    name: str
    description: str
    default_model: str = "claude-sonnet-4-6"
    system_prompt: str = ""
    tools: list[str] = field(default_factory=list)
    max_iterations: int = 10


def _resolve_soul_md(agent_id: str, builtin_dir: Path) -> str:
    """Charge le SOUL.md avec priorité : override utilisateur > builtin."""
    from app.config import settings

    # Override utilisateur
    user_soul = Path(settings.data_dir) / "agents" / agent_id / "SOUL.md"
    if user_soul.exists():
        logger.info(f"Agent {agent_id}: SOUL.md override depuis {user_soul}")
        return user_soul.read_text(encoding="utf-8")

    # Builtin
    builtin_soul = builtin_dir / agent_id / "SOUL.md"
    if builtin_soul.exists():
        return builtin_soul.read_text(encoding="utf-8")

    logger.warning(f"Agent {agent_id}: aucun SOUL.md trouvé")
    return ""


def _resolve_agents_dir() -> Path:
    """Trouve le dossier agents/ : builtin, PyInstaller bundle, ou source path."""
    import os
    import sys

    # 1. Builtin (mode dev, __file__ pointe vers le vrai fichier)
    if (_BUILTIN_AGENTS_DIR / "therese" / "agent.json").exists():
        return _BUILTIN_AGENTS_DIR

    # 2. PyInstaller bundle (_MEIPASS)
    if hasattr(sys, "_MEIPASS"):
        meipass_agents = Path(sys._MEIPASS) / "app" / "agents"
        if (meipass_agents / "therese" / "agent.json").exists():
            return meipass_agents

    # 3. Source path (env var ou DB, sans import circulaire)
    source_path = os.environ.get("THERESE_SOURCE_PATH")
    if not source_path:
        # Lire directement en DB sans passer par le router
        try:
            import sqlite3

            from app.config import settings

            db_path = settings.db_path
            if db_path and Path(db_path).exists():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.execute(
                    "SELECT value FROM preferences WHERE key = 'agent_source_path'"
                )
                row = cursor.fetchone()
                conn.close()
                if row and row[0]:
                    source_path = row[0]
        except Exception:
            pass

    if not source_path:
        # Emplacements connus
        home = Path.home()
        for candidate_root in [
            home / "Developer" / "Synoptia-THERESE",
            home / "Desktop" / "Dev Synoptia" / "THERESE V2",
            home / "repos" / "Synoptia-THERESE",
        ]:
            if (candidate_root / "src" / "backend" / "app" / "agents" / "therese" / "agent.json").exists():
                source_path = str(candidate_root)
                break

    if source_path:
        candidate = Path(source_path) / "src" / "backend" / "app" / "agents"
        if (candidate / "therese" / "agent.json").exists():
            return candidate

    # 4. Fallback (lèvera FileNotFoundError plus tard)
    return _BUILTIN_AGENTS_DIR


def load_agent_config(agent_id: str) -> AgentConfig:
    """Charge la configuration complète d'un agent."""
    builtin_dir = _resolve_agents_dir()

    # Charger agent.json
    agent_json_path = builtin_dir / agent_id / "agent.json"
    if not agent_json_path.exists():
        raise FileNotFoundError(f"Agent config introuvable : {agent_json_path}")

    with open(agent_json_path, encoding="utf-8") as f:
        data = json.load(f)

    # Charger SOUL.md
    system_prompt = _resolve_soul_md(agent_id, builtin_dir)

    return AgentConfig(
        id=agent_id,
        name=data.get("name", agent_id),
        description=data.get("description", ""),
        default_model=data.get("default_model", "claude-sonnet-4-6"),
        system_prompt=system_prompt,
        tools=data.get("tools", []),
        max_iterations=data.get("max_iterations", 10),
    )


# Cache global des configs chargées
_agent_configs: dict[str, AgentConfig] = {}


def get_agent_config(agent_id: str) -> AgentConfig:
    """Récupère la config d'un agent (avec cache)."""
    if agent_id not in _agent_configs:
        _agent_configs[agent_id] = load_agent_config(agent_id)
    return _agent_configs[agent_id]


def reload_agent_configs() -> None:
    """Force le rechargement des configs (après modification SOUL.md)."""
    _agent_configs.clear()
