"""
THÉRÈSE v2 - Agent Tools

Outils disponibles pour les agents Thérèse et Zézette.
Chaque outil est une fonction async qui retourne un résultat string.
"""

import asyncio
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Commandes autorisées pour run_command
ALLOWED_COMMANDS = {
    "pytest",
    "python",
    "npm",
    "npx",
    "vitest",
    "ruff",
    "make",
}

# Sous-commandes autorisées pour des commandes spécifiques
ALLOWED_SUBCOMMANDS = {
    "make": {"test", "test-backend", "test-frontend", "lint", "lint-fix", "typecheck"},
    "npm": {"test", "run"},
    "npx": {"vitest"},
}


class BranchGuard:
    """Vérifie qu'on est sur une branche agent avant tout write."""

    def __init__(self, git_service) -> None:
        self._git = git_service

    async def check(self) -> None:
        """Lève une erreur si on n'est pas sur une branche agent/."""
        branch = await self._git.current_branch()
        if not branch.startswith("agent/"):
            raise PermissionError(
                f"Écriture interdite : branche actuelle '{branch}' "
                f"(seules les branches agent/* sont autorisées)"
            )


class AgentToolExecutor:
    """Exécute les outils pour un agent donné."""

    def __init__(self, source_path: str, git_service=None) -> None:
        self.source_path = Path(source_path)
        self._git = git_service
        self._guard = BranchGuard(git_service) if git_service else None

    def _validate_path(self, file_path: str) -> Path:
        """Valide et résout un chemin de fichier dans le source tree."""
        resolved = (self.source_path / file_path).resolve()
        if not str(resolved).startswith(str(self.source_path.resolve())):
            raise PermissionError(f"Chemin hors du source tree : {file_path}")
        return resolved

    # --- Outils de lecture (Thérèse + Zézette) ---

    async def read_file(self, file_path: str, max_lines: int = 500) -> str:
        """Lit un fichier du source tree."""
        resolved = self._validate_path(file_path)
        if not resolved.exists():
            return f"Erreur : fichier introuvable : {file_path}"
        if not resolved.is_file():
            return f"Erreur : {file_path} n'est pas un fichier"

        try:
            content = resolved.read_text(encoding="utf-8", errors="replace")
            lines = content.split("\n")
            if len(lines) > max_lines:
                return (
                    "\n".join(lines[:max_lines])
                    + f"\n\n[... tronqué à {max_lines} lignes, total: {len(lines)}]"
                )
            return content
        except Exception as e:
            return f"Erreur de lecture : {e}"

    async def list_directory(self, dir_path: str = ".", max_entries: int = 100) -> str:
        """Liste le contenu d'un répertoire."""
        resolved = self._validate_path(dir_path)
        if not resolved.exists():
            return f"Erreur : répertoire introuvable : {dir_path}"
        if not resolved.is_dir():
            return f"Erreur : {dir_path} n'est pas un répertoire"

        try:
            entries = sorted(resolved.iterdir(), key=lambda p: (not p.is_dir(), p.name))
            lines = []
            for i, entry in enumerate(entries):
                if i >= max_entries:
                    lines.append(f"... et {len(list(resolved.iterdir())) - max_entries} autres")
                    break
                prefix = "📁 " if entry.is_dir() else "📄 "
                rel = entry.relative_to(self.source_path)
                lines.append(f"{prefix}{rel}")
            return "\n".join(lines)
        except Exception as e:
            return f"Erreur : {e}"

    async def search_codebase(
        self, pattern: str, glob_filter: str = "*.py", max_results: int = 20
    ) -> str:
        """Recherche un pattern dans le code source via grep."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "grep",
                "-rn",
                "--include",
                glob_filter,
                "-m",
                str(max_results),
                pattern,
                str(self.source_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=15.0)
            output = stdout.decode("utf-8", errors="replace").strip()
            if not output:
                return f"Aucun résultat pour '{pattern}' dans {glob_filter}"
            # Rendre les chemins relatifs
            lines = []
            for line in output.split("\n")[:max_results]:
                line = line.replace(str(self.source_path) + "/", "")
                lines.append(line)
            return "\n".join(lines)
        except asyncio.TimeoutError:
            return "Erreur : timeout de recherche"
        except Exception as e:
            return f"Erreur de recherche : {e}"

    # --- Outils d'écriture (Zézette uniquement) ---

    async def write_file(self, file_path: str, content: str) -> str:
        """Écrit ou modifie un fichier (branche agent uniquement)."""
        try:
            if self._guard:
                await self._guard.check()

            resolved = self._validate_path(file_path)
            resolved.parent.mkdir(parents=True, exist_ok=True)
            resolved.write_text(content, encoding="utf-8")
            return f"Fichier écrit : {file_path} ({len(content)} caractères)"
        except PermissionError as e:
            return f"Permission refusée : {e}"
        except Exception as e:
            return f"Erreur d'écriture : {e}"

    async def run_command(self, command: str) -> str:
        """Exécute une commande autorisée (tests, lint)."""
        try:
            if self._guard:
                await self._guard.check()
        except PermissionError as e:
            return f"Permission refusée : {e}"

        parts = command.strip().split()
        if not parts:
            return "Erreur : commande vide"

        base_cmd = parts[0]
        if base_cmd not in ALLOWED_COMMANDS:
            return f"Erreur : commande '{base_cmd}' non autorisée. Autorisées : {', '.join(sorted(ALLOWED_COMMANDS))}"

        # Vérifier les sous-commandes si nécessaire
        if base_cmd in ALLOWED_SUBCOMMANDS and len(parts) > 1:
            sub = parts[1]
            if sub not in ALLOWED_SUBCOMMANDS[base_cmd]:
                return f"Erreur : sous-commande '{base_cmd} {sub}' non autorisée"

        try:
            proc = await asyncio.create_subprocess_exec(
                *parts,
                cwd=str(self.source_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120.0)
            out = stdout.decode("utf-8", errors="replace")
            err = stderr.decode("utf-8", errors="replace")

            # Limiter la sortie
            max_chars = 5000
            if len(out) > max_chars:
                out = out[:max_chars] + f"\n... tronqué ({len(out)} chars total)"
            if len(err) > max_chars:
                err = err[:max_chars] + f"\n... tronqué ({len(err)} chars total)"

            result = f"Code retour : {proc.returncode}\n"
            if out:
                result += f"\nStdout:\n{out}"
            if err:
                result += f"\nStderr:\n{err}"
            return result
        except asyncio.TimeoutError:
            return f"Erreur : timeout (120s) pour '{command}'"
        except Exception as e:
            return f"Erreur d'exécution : {e}"

    # --- Outils git (Zézette) ---

    async def git_status(self) -> str:
        """Affiche le statut git."""
        if not self._git:
            return "Erreur : service git non disponible"
        return await self._git.status() or "Aucun changement"

    async def git_diff(self) -> str:
        """Affiche le diff des changements en cours."""
        if not self._git:
            return "Erreur : service git non disponible"
        diff = await self._git.diff()
        if len(diff) > 10000:
            return diff[:10000] + f"\n\n... diff tronqué ({len(diff)} chars total)"
        return diff or "Aucun diff"

    # --- Outil recherche web (agents preconfigures) ---

    async def web_search(self, query: str, max_results: int = 5) -> str:
        """Recherche sur le web via Brave Search ou DuckDuckGo."""
        try:
            from app.services.web_search import get_web_search_service

            search_service = get_web_search_service()

            response = await search_service.search(query, max_results=max_results)
            if not response.results:
                return f"Aucun resultat pour '{query}'"

            lines = [f"Resultats pour : {query}\n"]
            for i, r in enumerate(response.results, 1):
                lines.append(f"{i}. **{r.title}**")
                lines.append(f"   {r.url}")
                lines.append(f"   {r.snippet}\n")
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Erreur web_search: {e}", exc_info=True)
            return f"Erreur de recherche web : {e}"

    # --- Outils Thérèse ---

    async def clarify(self, question: str) -> str:
        """Pose une question de clarification à l'utilisateur. Retourne un placeholder."""
        # Le swarm intercepte cet appel et le transmet à l'utilisateur via SSE
        return f"[CLARIFY]{question}"

    async def create_spec(
        self, title: str, description: str, files_to_change: str = "", acceptance_criteria: str = ""
    ) -> str:
        """Crée une spécification pour Zézette."""
        spec = f"# Spec : {title}\n\n"
        spec += f"## Description\n{description}\n\n"
        if files_to_change:
            spec += f"## Fichiers à modifier\n{files_to_change}\n\n"
        if acceptance_criteria:
            spec += f"## Critères d'acceptation\n{acceptance_criteria}\n\n"
        return f"[SPEC]{spec}"

    async def explain_change(self, summary: str, details: str = "") -> str:
        """Explique un changement à l'utilisateur en langage simple."""
        explanation = summary
        if details:
            explanation += f"\n\n{details}"
        return f"[EXPLAIN]{explanation}"


# Définitions d'outils au format OpenAI function calling (compatible LLM)
THERESE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "clarify",
            "description": "Pose une question de clarification à l'utilisateur",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "La question à poser"},
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_spec",
            "description": "Crée une spécification technique pour Zézette",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Titre court de la spec"},
                    "description": {
                        "type": "string",
                        "description": "Description détaillée du changement",
                    },
                    "files_to_change": {
                        "type": "string",
                        "description": "Liste des fichiers à modifier",
                    },
                    "acceptance_criteria": {
                        "type": "string",
                        "description": "Critères pour valider le changement",
                    },
                },
                "required": ["title", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "explain_change",
            "description": "Explique un changement à l'utilisateur en langage simple",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Résumé en 1-2 phrases"},
                    "details": {
                        "type": "string",
                        "description": "Détails supplémentaires (optionnel)",
                    },
                },
                "required": ["summary"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Lit un fichier du code source de Thérèse",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Chemin relatif du fichier"},
                    "max_lines": {
                        "type": "integer",
                        "description": "Nombre max de lignes (défaut: 500)",
                    },
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Liste le contenu d'un répertoire du code source",
            "parameters": {
                "type": "object",
                "properties": {
                    "dir_path": {
                        "type": "string",
                        "description": "Chemin relatif du répertoire (défaut: racine)",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_codebase",
            "description": "Recherche un pattern dans le code source",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Pattern à rechercher (regex)"},
                    "glob_filter": {
                        "type": "string",
                        "description": "Filtre de fichiers (défaut: *.py)",
                    },
                },
                "required": ["pattern"],
            },
        },
    },
]

ZEZETTE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Lit un fichier du code source",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Chemin relatif du fichier"},
                    "max_lines": {
                        "type": "integer",
                        "description": "Nombre max de lignes (défaut: 500)",
                    },
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Écrit ou modifie un fichier (branche agent uniquement)",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Chemin relatif du fichier"},
                    "content": {"type": "string", "description": "Contenu complet du fichier"},
                },
                "required": ["file_path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Liste le contenu d'un répertoire",
            "parameters": {
                "type": "object",
                "properties": {
                    "dir_path": {
                        "type": "string",
                        "description": "Chemin relatif (défaut: racine)",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_codebase",
            "description": "Recherche un pattern dans le code source",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Pattern à rechercher (regex)"},
                    "glob_filter": {
                        "type": "string",
                        "description": "Filtre de fichiers (défaut: *.py)",
                    },
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Exécute une commande autorisée (tests, lint)",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Commande à exécuter (ex: make test-backend, pytest tests/)",
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_status",
            "description": "Affiche le statut git actuel",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_diff",
            "description": "Affiche le diff des changements en cours",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]
