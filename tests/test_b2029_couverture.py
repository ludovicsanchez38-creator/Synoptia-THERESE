"""La garde de l'instrument laisse passer la sauvegarde locale du chat."""

import json
import subprocess


def test_garde_autorise_uniquement_la_migration_locale_du_chat(tmp_path):
    # La garde est du JavaScript pur : aucun navigateur n'est nécessaire.
    # Le chargeur interdit son lancement même si Playwright est installé.
    chargeur = tmp_path / "sans_navigateur.mjs"
    chargeur.write_text("""
export async function resolve(nom, contexte, suivant) {
  if (nom === '@playwright/test') return {
    url: 'data:text/javascript,' + encodeURIComponent(
      'export const chromium = { launch() { throw new Error("Navigateur interdit dans ce banc"); } };'
    ), shortCircuit: true,
  };
  return suivant(nom, contexte);
}
""", encoding="utf-8")
    script = """
import { installerGardeReseau } from './tests/couverture/couverture-ecran.mjs';
let handler;
const garde = { bloquees: [], websockets_bloques: [], portReel: false };
await installerGardeReseau({
  route: async (_motif, callback) => { handler = callback; },
  routeWebSocket: async () => {},
}, garde);
const essais = [
  ['POST', 'http://127.0.0.1:17393/api/chat/cache-migration'],
  ['POST', 'http://127.0.0.1:17393/api/chat/cache-migration?autre=1'],
  ['DELETE', 'http://127.0.0.1:17393/api/chat/cache-migration'],
  ['POST', 'http://127.0.0.1:1420/api/chat/cache-migration'],
  ['POST', 'https://example.invalid/api/chat/cache-migration'],
  ['POST', 'http://127.0.0.1:17393/api/config/preferences'],
];
const resultats = [];
for (const [methode, url] of essais) {
  await handler({
    request: () => ({ method: () => methode, url: () => url }),
    continue: () => resultats.push('continue'),
    abort: () => resultats.push('bloquee'),
  });
}
process.stdout.write(JSON.stringify(resultats));
"""
    execution = subprocess.run(
        ["node", "--experimental-loader", str(chargeur), "--input-type=module", "--eval", script],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(execution.stdout) == ["continue"] + ["bloquee"] * 5
