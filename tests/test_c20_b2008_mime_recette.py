"""Exercer la route de recette avec Playwright simulé, sans navigateur ni réseau."""

import runpy
import shutil
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest


@pytest.fixture
def serveur_recette(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[1] / "scripts/recette_r5_navigateur.py"
    script = tmp_path / "scripts" / source.name
    script.parent.mkdir()
    shutil.copyfile(source, script)
    dist = tmp_path / ".recette-r5/ui-dist"
    dist.mkdir(parents=True)
    page = Mock()
    navigateur = Mock()
    navigateur.new_context.return_value.new_page.return_value = page
    playwright = MagicMock()
    playwright.return_value.__enter__.return_value.chromium.launch.return_value = navigateur
    paquet = ModuleType("playwright")
    module = ModuleType("playwright.sync_api")
    module.sync_playwright = playwright
    monkeypatch.setitem(sys.modules, "playwright", paquet)
    monkeypatch.setitem(sys.modules, "playwright.sync_api", module)
    monkeypatch.setattr(sys, "path", sys.path.copy())
    monkeypatch.setattr("os.open", lambda *_args: 123)
    monkeypatch.setenv("TMPDIR", str(tmp_path))

    class RouteInstallee(Exception):
        pass

    page.route.side_effect = RouteInstallee
    with pytest.raises(RouteInstallee):
        runpy.run_path(str(script), run_name="__main__")
    navigateur.close.assert_called_once()
    return dist, page.route.call_args.args[1]


@pytest.mark.parametrize(("nom", "mime"), [
    ("police.woff2", "font/woff2"), ("police.woff", "font/woff"),
    ("icone.svg", "image/svg+xml"), ("photo.png", "image/png"),
    ("photo.JPG", "image/jpeg"), ("photo.webp", "image/webp"),
    ("app.js", "application/javascript"), ("style.css", "text/css"),
    ("index.html", "text/html"), ("archive.inconnu", "application/octet-stream"),
])
def test_ressources_statiques_ont_un_type_mime(serveur_recette, nom, mime):
    dist, servir = serveur_recette
    (dist / nom).write_bytes(b"ressource fictive")
    route = Mock(request=SimpleNamespace(url=f"http://recette.test/{nom}"))
    servir(route)
    route.abort.assert_not_called()
    route.fulfill.assert_called_once_with(body=b"ressource fictive", content_type=mime)


@pytest.mark.parametrize("url", [
    "https://externe.invalid/photo.png", "http://recette.test/../hors-dist.png",
    "http://recette.test/absent.png",
])
def test_serveur_refuse_les_ressources_hors_recette(serveur_recette, url):
    _, servir = serveur_recette
    route = Mock(request=SimpleNamespace(url=url))
    servir(route)
    route.abort.assert_called_once()
    route.fulfill.assert_not_called()
