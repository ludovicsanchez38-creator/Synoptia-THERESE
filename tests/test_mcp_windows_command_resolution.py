from unittest.mock import patch

from app.services.mcp_service import (
    _normalize_command_name,
    resolve_mcp_command,
    validate_mcp_command,
)


def test_validate_mcp_command_accepts_windows_npx_cmd_variant():
    with patch("app.services.mcp_service.resolve_mcp_command", return_value=r"C:\Program Files\nodejs\NPX.CMD"):
        validate_mcp_command("npx", ["-y", "@modelcontextprotocol/server-fetch"])


def test_normalize_command_name_handles_windows_suffixes_and_case():
    assert _normalize_command_name(r"C:\Program Files\nodejs\NPX.CMD") == "npx"
    assert _normalize_command_name("python.EXE") == "python"
    assert _normalize_command_name("uv.BAT") == "uv"


def test_resolve_mcp_command_uses_explicit_path_when_provided():
    with patch("app.services.mcp_service.shutil.which") as which_mock:
        which_mock.return_value = r"C:\Users\nicol\AppData\Roaming\npm\npx.cmd"

        resolved = resolve_mcp_command("npx", r"C:\Users\nicol\AppData\Roaming\npm;C:\Program Files\nodejs")

        assert resolved == r"C:\Users\nicol\AppData\Roaming\npm\npx.cmd"
        which_mock.assert_called_once_with(
            "npx",
            path=r"C:\Users\nicol\AppData\Roaming\npm;C:\Program Files\nodejs",
        )
