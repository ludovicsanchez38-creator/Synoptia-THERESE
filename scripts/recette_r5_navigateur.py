"""Écran réel sur données fictives : aucune connexion ni serveur HTTP."""
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".recette-r5/playwright-python"))
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / '.recette-r5/ui-dist'
BRANCHES = ['Profil et consignes', 'Fiches et index', 'Journal des actions confirmées et envois', 'Brouillons en cours', 'Notes de rendez-vous']
ATTENDUS = ['Modifier mon profil et mes consignes', 'Acompte décidé', 'Issue indéterminée', 'FACT-2026-FICTIF', 'Rendez-vous supprimé']
# La longue adresse du worktree dépasse la limite des sockets UNIX de
# Chromium. Ce chemin /proc désigne exactement le dossier temporaire local.
repertoire_temp = os.open(ROOT / '.recette-r5/tmp', os.O_RDONLY | os.O_DIRECTORY)
os.environ['TMPDIR'] = f'/proc/{os.getpid()}/fd/{repertoire_temp}'
resultats = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path=str((ROOT / '.recette-r5/navigateur-existant').resolve()),
        args=['--no-sandbox', '--disable-dev-shm-usage'])
    try:
        for width in (390, 1440):
            ctx = browser.new_context(viewport={'width': width, 'height': 900})
            page = ctx.new_page()
            erreurs = []
            page.on('pageerror', lambda e: erreurs.append(str(e)))
            def servir(route):
                from urllib.parse import urlparse
                url = urlparse(route.request.url)
                if url.netloc != 'recette.test':
                    route.abort()
                    return
                fichier = (DIST / (url.path.lstrip('/') or 'index.html')).resolve()
                if not fichier.is_relative_to(DIST.resolve()) or not fichier.is_file():
                    route.abort()
                    return
                content_type = {'.js': 'application/javascript', '.css': 'text/css', '.html': 'text/html'}.get(fichier.suffix, 'application/octet-stream')
                route.fulfill(body=fichier.read_bytes(), content_type=content_type)
            page.route('**/*', servir)
            page.goto('http://recette.test/')
            page.get_by_role('button', name='Acompte décidé', exact=True).wait_for()
            for index, (branche, attendu) in enumerate(zip(BRANCHES, ATTENDUS, strict=True)):
                button = page.get_by_role('navigation', name='Arborescence de Mémoire').get_by_role('button', name=branche, exact=True)
                button.focus()
                page.keyboard.press('Enter')
                assert button.get_attribute('aria-current') == 'page'
                page.get_by_text(attendu, exact=True).wait_for()
                assert page.get_by_text('Non disponible', exact=True).count() == 0
                assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
                page.screenshot(path=str(ROOT / f'.recette-r5/logs/memoire-{width}-{index}.png'), full_page=True)
                resultats.append({'width': width, 'branche': branche, 'clavier': True})
            page.get_by_role('button', name='Fiches et index', exact=True).click()
            page.get_by_label('Rechercher', exact=True).fill('SENTINELLE_DEMO_RECHERCHE')
            page.evaluate('window.recetteDemo(true)')
            for branche in BRANCHES:
                page.get_by_role('button', name=branche, exact=True).click()
                if branche == 'Fiches et index':
                    assert page.get_by_label('Rechercher', exact=True).input_value() == ''
                texte = page.locator('body').inner_text()
                assert not any(t in texte for t in ('Acompte décidé', 'Préparer le devis après la séance.', 'FACT-2026-FICTIF'))
            page.screenshot(path=str(ROOT / f'.recette-r5/logs/memoire-{width}-demo.png'), full_page=True)
            assert not erreurs, erreurs
            ctx.close()
    finally:
        browser.close()
(ROOT / '.recette-r5/logs/navigateur.json').write_text(json.dumps(resultats, ensure_ascii=False, indent=2))
print('Dix parcours clavier des cinq branches : étroit, large et démo vérifiés.')
