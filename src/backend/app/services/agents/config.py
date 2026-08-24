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
    # Relevé dans la documentation officielle de chaque fournisseur le
    # 24/08/2026. L'Atelier fait travailler des agents qui écrivent du code et
    # ouvrent des branches : seuls des modèles capables d'appeler des outils ont
    # leur place ici. Un modèle sans outils y produirait du texte, jamais un
    # commit.
    # Anthropic
    {"id": "claude-opus-5", "name": "Claude Opus 5", "provider": "anthropic", "recommended": True},
    {"id": "claude-fable-5", "name": "Claude Fable 5", "provider": "anthropic"},
    {"id": "claude-sonnet-5", "name": "Claude Sonnet 5", "provider": "anthropic"},
    {"id": "claude-opus-4-8", "name": "Claude Opus 4.8", "provider": "anthropic"},
    {"id": "claude-sonnet-4-6", "name": "Claude Sonnet 4.6", "provider": "anthropic"},
    {"id": "claude-haiku-4-5-20251001", "name": "Claude Haiku 4.5", "provider": "anthropic"},
    # OpenAI. gpt-5.3-codex est écarté : sa fiche indique qu'il refuse
    # `v1/chat/completions`, le point d'appel utilisé ici.
    {"id": "gpt-5.6-sol", "name": "GPT-5.6 Sol", "provider": "openai"},
    {"id": "gpt-5.6-terra", "name": "GPT-5.6 Terra", "provider": "openai"},
    {"id": "gpt-5.6-luna", "name": "GPT-5.6 Luna", "provider": "openai"},
    {"id": "gpt-5.5", "name": "GPT-5.5", "provider": "openai"},
    # Google
    {"id": "gemini-3.7-flash", "name": "Gemini 3.7 Flash", "provider": "gemini"},
    {"id": "gemini-3.1-pro-preview", "name": "Gemini 3.1 Pro (préversion)", "provider": "gemini"},
    {"id": "gemini-3.5-flash", "name": "Gemini 3.5 Flash", "provider": "gemini"},
    # xAI
    {"id": "grok-4.6", "name": "Grok 4.6", "provider": "grok"},
    {"id": "grok-4.5", "name": "Grok 4.5", "provider": "grok"},
    {"id": "grok-4.3", "name": "Grok 4.3", "provider": "grok"},
    # Mistral
    {"id": "mistral-medium-latest", "name": "Mistral Medium 3.5", "provider": "mistral"},
    {"id": "mistral-large-latest", "name": "Mistral Large", "provider": "mistral"},
    {"id": "codestral-2508", "name": "Codestral", "provider": "mistral"},
    # OpenRouter (repli statique : le sélecteur principal interroge l'API)
    {"id": "anthropic/claude-opus-5", "name": "Claude Opus 5 (OR)", "provider": "openrouter"},
    {"id": "anthropic/claude-sonnet-5", "name": "Claude Sonnet 5 (OR)", "provider": "openrouter"},
    {"id": "openai/gpt-5.6-sol", "name": "GPT-5.6 Sol (OR)", "provider": "openrouter"},
    {"id": "google/gemini-3.7-flash", "name": "Gemini 3.7 Flash (OR)", "provider": "openrouter"},
    # DeepSeek
    {"id": "deepseek-v4-pro", "name": "DeepSeek V4 Pro", "provider": "deepseek"},
    {"id": "deepseek-v4-flash", "name": "DeepSeek V4 Flash", "provider": "deepseek"},
    # Z.ai (GLM)
    {"id": "glm-5.3", "name": "GLM-5.3", "provider": "glm"},
    {"id": "glm-5.2", "name": "GLM-5.2", "provider": "glm"},
    # Moonshot (Kimi) - un million de jetons de contexte sur K3
    {"id": "kimi-k3", "name": "Kimi K3", "provider": "kimi"},
    {"id": "kimi-k2.7-code", "name": "Kimi K2.7 Code", "provider": "kimi"},
    # Alibaba (Qwen) - l'adresse contient l'espace de travail du compte
    {"id": "qwen3.8-max", "name": "Qwen3.8-Max", "provider": "qwen"},
    {"id": "qwen3-coder-plus", "name": "Qwen3-Coder-Plus", "provider": "qwen"},
    # MiniMax - la casse des identifiants compte
    {"id": "MiniMax-M3", "name": "MiniMax M3", "provider": "minimax"},
    # Local (Ollama) - tous porteurs de l'étiquette « tools » d'Ollama, avec la
    # taille du téléchargement, parce que nos testeurs ont des machines modestes.
    {"id": "qwen3.5:9b", "name": "Qwen3.5 9B (local, 6,6 Go)", "provider": "ollama"},
    {"id": "qwen3-coder:30b", "name": "Qwen3-Coder 30B (local, 19 Go)", "provider": "ollama"},
    {"id": "ministral-3:8b", "name": "Ministral 3 8B (local, 6 Go)", "provider": "ollama"},
    {"id": "devstral:24b", "name": "Devstral 24B (local, 14 Go)", "provider": "ollama"},
    {"id": "gpt-oss:20b", "name": "GPT-OSS 20B (local, 14 Go)", "provider": "ollama"},
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
    if (_BUILTIN_AGENTS_DIR / "katia" / "agent.json").exists():
        return _BUILTIN_AGENTS_DIR

    # 2. PyInstaller bundle (_MEIPASS)
    if hasattr(sys, "_MEIPASS"):
        meipass_agents = Path(sys._MEIPASS) / "app" / "agents"
        if (meipass_agents / "katia" / "agent.json").exists():
            return meipass_agents

    # 3. Source path (env var ou DB, sans import circulaire)
    source_path = os.environ.get("THERESE_SOURCE_PATH")
    if not source_path:
        # Lire directement en DB sans passer par le router
        try:

            from app.config import settings

            db_path = settings.db_path
            if db_path and Path(db_path).exists():
                from app.models.database import db_connect

                conn = db_connect(db_path)  # US-014 : clé SQLCipher si chiffrée
                cursor = conn.execute(
                    "SELECT value FROM preferences WHERE key = 'agent_source_path'"
                )
                row = cursor.fetchone()
                conn.close()
                if row and row[0]:
                    raw = row[0].strip().strip('"').strip("'")
                    resolved = Path(raw).expanduser().resolve()
                    if resolved.exists():
                        source_path = str(resolved)
                    else:
                        logger.warning(
                            "agent_source_path DB '%s' (resolu: '%s') n'existe pas",
                            row[0], resolved,
                        )
        except Exception as e:
            logger.debug("Impossible de lire agent_source_path depuis DB: %s", e)

    if not source_path:
        # Emplacements connus
        home = Path.home()
        for candidate_root in [
            # macOS / Linux
            home / "Developer" / "Synoptia-THERESE",
            home / "Desktop" / "Dev Synoptia" / "Synoptia-THERESE",
            home / "Desktop" / "Dev Synoptia" / "THERESE V2",
            home / "repos" / "Synoptia-THERESE",
            home / "Documents" / "Synoptia-THERESE",
            # Windows (Path.home() = C:\Users\<username>)
            home / "Desktop" / "Synoptia-THERESE",
            home / "source" / "repos" / "Synoptia-THERESE",  # Visual Studio default
            home / "Projects" / "Synoptia-THERESE",
            home / "GitHub" / "Synoptia-THERESE",  # GitHub Desktop default
        ]:
            if (candidate_root / "src" / "backend" / "app" / "agents" / "katia" / "agent.json").exists():
                source_path = str(candidate_root)
                break

    if source_path:
        candidate = Path(source_path) / "src" / "backend" / "app" / "agents"
        if (candidate / "katia" / "agent.json").exists():
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
