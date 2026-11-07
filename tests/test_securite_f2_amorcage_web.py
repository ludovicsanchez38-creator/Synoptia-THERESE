"""F-2, passe 2 : refus visible du navigateur sans canal privé d'amorçage.

Le Node local exécute le vrai TypeScript et le callback de démarrage d'App,
avec des transports et setters simulés, sans serveur ni dépendance npm.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

SCENARIOS = (
    "amorcage-refuse",
    "renouvellement-refuse",
    "harnais-authentifie",
    "interface-arretee",
    "controle-annexe-refuse",
)

SCRIPT = r"""
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { stripTypeScriptTypes } from 'node:module';

const racine = process.cwd() + '/src/frontend/src/';
const moduleUrl = code => 'data:text/javascript;base64,' + Buffer.from(code).toString('base64');
const transformer = code => stripTypeScriptTypes(code, { mode: 'transform' });
const validation = moduleUrl(transformer(readFileSync(racine + 'lib/messageDeValidation.ts', 'utf8')));
const source = readFileSync(racine + 'services/api/core.ts', 'utf8')
  .replaceAll('import.meta.env', '({})')
  .replace("'../../lib/messageDeValidation'", JSON.stringify(validation));
const core = await import(moduleUrl(transformer(source)));
globalThis.window = {};
console.warn = () => {};
console.error = () => {};
const refus = () => new Response(JSON.stringify({ code: 'UNAUTHORIZED' }), { status: 401 });
const succes = corps => new Response(JSON.stringify(corps));
const message = /mode navigateur.*application desktop/i;
const scenario = process.argv[2];

if (scenario === 'amorcage-refuse') {
  globalThis.fetch = async () => refus();
  await assert.rejects(core.initializeAuth(), message);
  assert.equal(core.getSessionToken(), null);
} else if (scenario === 'renouvellement-refuse') {
  let amorce = true;
  globalThis.fetch = async () => {
    if (amorce) { amorce = false; return succes({ token: 'jeton-initial-factice' }); }
    return refus();
  };
  await core.initializeAuth();
  await assert.rejects(core.request('/api/dashboard/today'), message);
} else if (scenario === 'harnais-authentifie') {
  let amorcages = 0;
  const jetons = [];
  globalThis.fetch = async (url, options) => {
    // Le harnais navigateur possède le fichier privé et authentifie cette route.
    if (String(url).endsWith('/api/auth/token')) {
      return succes({ token: ++amorcages === 1 ? 'jeton-initial-factice' : 'jeton-renouvele-factice' });
    }
    jetons.push(new Headers(options.headers).get('X-Therese-Token'));
    return jetons.length === 1 ? refus() : succes({ ok: true });
  };
  await core.initializeAuth();
  assert.deepEqual(await core.request('/api/dashboard/today'), { ok: true });
  assert.deepEqual(jetons, ['jeton-initial-factice', 'jeton-renouvele-factice']);
} else if (scenario === 'interface-arretee') {
  const app = readFileSync(racine + 'App.tsx', 'utf8');
  const debut = app.indexOf('async function initAndCheckOnboarding()');
  const fin = app.indexOf('\n    initAndCheckOnboarding();', debut);
  assert.ok(debut >= 0 && fin > debut, 'Callback réel de démarrage introuvable');
  const callback = transformer(app.slice(debut, fin));
  const Refus = core.AuthentificationNavigateurImpossible ?? class extends Error {};
  const erreur = new Refus('Le mode navigateur est indisponible. Ouvrez l’application desktop.');
  const evenements = [];
  const executer = new Function(
    'api', 'AuthentificationNavigateurImpossible', 'setErreurDAuthentification',
    'setShowOnboarding', 'setCheckingOnboarding',
    callback + '\nreturn initAndCheckOnboarding();',
  );
  await executer(
    { initializeAuth: async () => { throw erreur; } }, Refus,
    texte => evenements.push(['arret', texte]),
    () => evenements.push(['interface-ouverte']),
    () => evenements.push(['demarrage-termine']),
  );
  assert.deepEqual(evenements, [['arret', erreur.message]]);
} else if (scenario === 'controle-annexe-refuse') {
  const app = readFileSync(racine + 'App.tsx', 'utf8');
  const debut = app.indexOf('void (async () => {');
  const fin = app.indexOf('\n  }, [backendReady]);', debut);
  assert.ok(debut >= 0 && fin > debut, 'Contrôle réel de démarrage introuvable');
  const callback = transformer(app.slice(debut, fin)
    .replace("await import('./lib/capacites/generation')", 'await chargerControle()'))
    .replace('void (async', 'return (async');
  const Refus = core.AuthentificationNavigateurImpossible;
  const executer = new Function('AuthentificationNavigateurImpossible', 'chargerControle', callback);
  await assert.doesNotReject(executer(Refus, async () => ({
    controlerGenerationAuDemarrage: async () => { throw new Refus(); },
  })), 'Le contrôle annexe doit laisser le parcours principal afficher le refus.');
} else {
  assert.fail('Scénario inconnu : ' + scenario);
}
console.log('REUSSI : ' + scenario);
"""


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_le_navigateur_ne_demarre_pas_silencieusement_sans_secret(scenario):
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node local absent : le TypeScript ne peut pas être exécuté.")
    resultat = subprocess.run(
        [node, "--input-type=module", "-", scenario],
        input=SCRIPT,
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert resultat.returncode == 0, resultat.stdout + resultat.stderr[-5000:]
