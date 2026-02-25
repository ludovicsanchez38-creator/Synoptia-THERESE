"""
Tests pour le CommandRegistry V3.
"""

import pytest
from app.models.command import CommandAction, CommandDefinition, CommandSource
from app.services.command_registry import CommandRegistry


@pytest.fixture
def registry():
    """Crée un registre frais pour chaque test."""
    reg = CommandRegistry()
    # Reset singleton pour éviter les interférences entre tests
    CommandRegistry._instance = None
    return reg


class TestCommandDefinition:
    """Tests du modèle CommandDefinition."""

    def test_create_command(self):
        cmd = CommandDefinition(
            id="test-cmd",
            name="Test",
            description="Un test",
            source=CommandSource.BUILTIN,
            action=CommandAction.PROMPT,
            prompt_template="Hello {{name}}",
        )
        assert cmd.id == "test-cmd"
        assert cmd.source == CommandSource.BUILTIN
        assert cmd.action == CommandAction.PROMPT
        assert cmd.show_on_home is False
        assert cmd.show_in_slash is True
        assert cmd.is_editable is False

    def test_command_sources(self):
        assert CommandSource.BUILTIN.value == "builtin"
        assert CommandSource.SKILL.value == "skill"
        assert CommandSource.USER.value == "user"
        assert CommandSource.MCP.value == "mcp"

    def test_command_actions(self):
        assert CommandAction.PROMPT.value == "prompt"
        assert CommandAction.FORM_THEN_PROMPT.value == "form_then_prompt"
        assert CommandAction.FORM_THEN_FILE.value == "form_then_file"
        assert CommandAction.IMAGE.value == "image"
        assert CommandAction.NAVIGATE.value == "navigate"
        assert CommandAction.RFC.value == "rfc"


class TestCommandRegistry:
    """Tests du CommandRegistry."""

    def test_register_builtin_commands(self, registry):
        registry._register_builtin_commands()
        commands = registry.list()
        assert len(commands) > 0

        # Vérifier les slash commands builtins
        contact = registry.get("contact")
        assert contact is not None
        assert contact.source == CommandSource.BUILTIN
        assert contact.action == CommandAction.PROMPT
        assert contact.show_in_slash is True

    def test_register_builtin_images(self, registry):
        registry._register_builtin_commands()

        gpt = registry.get("image-gpt")
        assert gpt is not None
        assert gpt.action == CommandAction.IMAGE
        assert gpt.show_on_home is True
        assert gpt.image_config is not None
        assert gpt.image_config["provider"] == "gpt-image-1.5"

    def test_list_with_category_filter(self, registry):
        registry._register_builtin_commands()

        builtin_cmds = registry.list(category="builtin")
        assert all(c.category == "builtin" for c in builtin_cmds)

        production_cmds = registry.list(category="production")
        assert all(c.category == "production" for c in production_cmds)

    def test_list_with_home_filter(self, registry):
        registry._register_builtin_commands()

        home_cmds = registry.list(show_on_home=True)
        assert all(c.show_on_home for c in home_cmds)

        slash_cmds = registry.list(show_in_slash=True)
        assert all(c.show_in_slash for c in slash_cmds)

    def test_list_sorted_by_category_and_order(self, registry):
        registry._register_builtin_commands()

        commands = registry.list()
        # Vérifier que la liste est triée
        for i in range(1, len(commands)):
            prev = commands[i - 1]
            curr = commands[i]
            if prev.category == curr.category:
                assert prev.sort_order <= curr.sort_order or prev.name <= curr.name

    def test_get_nonexistent(self, registry):
        assert registry.get("inexistant") is None

    @pytest.mark.asyncio
    async def test_create_user_command(self, registry, tmp_path, monkeypatch):
        """Teste la création d'une commande utilisateur."""
        from app.services.user_commands import UserCommandsService

        # Monkeypatch le répertoire de commandes
        service = UserCommandsService.get_instance()
        monkeypatch.setattr(service, "_commands_dir", tmp_path)

        registry._register_builtin_commands()

        cmd = await registry.create_user_command(
            name="mon-test",
            description="Test commande",
            icon="🧪",
            prompt_template="Teste {{sujet}} pour moi",
        )

        assert cmd.id == "user-mon-test"
        assert cmd.source == CommandSource.USER
        assert cmd.is_editable is True
        assert cmd.show_on_home is True

        # Vérifier qu'on peut la retrouver
        found = registry.get("user-mon-test")
        assert found is not None
        assert found.prompt_template == "Teste {{sujet}} pour moi"

    @pytest.mark.asyncio
    async def test_delete_user_command(self, registry, tmp_path, monkeypatch):
        """Teste la suppression d'une commande utilisateur."""
        from app.services.user_commands import UserCommandsService

        service = UserCommandsService.get_instance()
        monkeypatch.setattr(service, "_commands_dir", tmp_path)

        registry._register_builtin_commands()

        await registry.create_user_command(name="a-supprimer", prompt_template="test")
        assert registry.get("user-a-supprimer") is not None

        deleted = await registry.delete_user_command("user-a-supprimer")
        assert deleted is True
        assert registry.get("user-a-supprimer") is None

    @pytest.mark.asyncio
    async def test_delete_builtin_command_fails(self, registry):
        """On ne peut pas supprimer une commande builtin."""
        registry._register_builtin_commands()

        deleted = await registry.delete_user_command("contact")
        assert deleted is False
