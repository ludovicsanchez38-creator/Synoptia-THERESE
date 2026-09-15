"""B-794 (cycle 9) : un identifiant d'outil non normalisé pouvait sortir du dossier
des outils (`shutil.rmtree(tools_dir / tool_id)` avec « ../victime »)."""
from __future__ import annotations

import pytest
from app.services.skills.tool_installer import ToolInstaller


@pytest.mark.asyncio
async def test_uninstall_refuse_un_identifiant_qui_sort_du_dossier(tmp_path, monkeypatch):
    installer = ToolInstaller()
    monkeypatch.setattr(installer, "_tools_dir", tmp_path / "tools")
    installer.tools_dir.mkdir(parents=True, exist_ok=True)
    victime = tmp_path / "victime"
    victime.mkdir()
    (victime / "precieux.txt").write_text("ne pas effacer", encoding="utf-8")

    for identifiant in ("../victime", "..", "/", "a/../../victime", "victime\\..\\.."):
        assert await installer.uninstall_tool(identifiant) is False, identifiant

    assert (victime / "precieux.txt").exists()


@pytest.mark.asyncio
async def test_uninstall_retire_un_outil_legitime(tmp_path, monkeypatch):
    installer = ToolInstaller()
    monkeypatch.setattr(installer, "_tools_dir", tmp_path / "tools")
    outil = installer.tools_dir / "mon-outil"
    outil.mkdir(parents=True)
    (outil / "tool.py").write_text("print('ok')", encoding="utf-8")

    assert await installer.uninstall_tool("mon-outil") is True
    assert not outil.exists()
