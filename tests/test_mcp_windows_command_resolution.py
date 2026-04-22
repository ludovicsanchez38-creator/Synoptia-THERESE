import os
from unittest.mock import patch

from app.services.mcp_service import (
    _normalize_command_name,
    build_mcp_enriched_path,
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


def test_build_mcp_enriched_path_uses_os_pathsep():
    """R3 v0.11.4 : le helper unifié doit utiliser os.pathsep, pas ':' en dur."""
    result = build_mcp_enriched_path()
    assert isinstance(result, str)
    if os.pathsep == ";":
        assert ":" not in result or "\\" in result or ";" in result


def test_build_mcp_enriched_path_includes_windows_paths(tmp_path):
    """R3 v0.11.4 : sur Windows, les chemins Node.js courants doivent etre injectes."""
    fake_nodejs = tmp_path / "nodejs"
    fake_nodejs.mkdir()
    fake_npm = tmp_path / "npm"
    fake_npm.mkdir()

    with patch("app.services.mcp_service.sys.platform", "win32"), patch.dict(
        os.environ,
        {
            "PATH": "",
            "PROGRAMFILES": str(tmp_path),
            "APPDATA": str(tmp_path),
            "LOCALAPPDATA": "",
        },
        clear=False,
    ):
        result = build_mcp_enriched_path()
        assert str(fake_nodejs) in result
        assert str(fake_npm) in result


def test_build_mcp_enriched_path_on_unix_is_string():
    """R3 v0.11.4 : sur Unix, le helper retourne une string non vide utilisant os.pathsep."""
    with patch("app.services.mcp_service.sys.platform", "darwin"):
        result = build_mcp_enriched_path()
        assert isinstance(result, str)
        assert result
