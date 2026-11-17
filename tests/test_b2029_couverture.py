"""La garde acquitte la migration exacte sans autoriser l'écriture réseau."""

import json
import subprocess


def test_garde_simule_la_migration_exacte_et_bloque_ses_variantes(tmp_path):
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
import { installerGardeReseau, requeteAutorisee } from './tests/couverture/couverture-ecran.mjs';
let handler;
const garde = { bloquees: [], websockets_bloques: [], portReel: false };
await installerGardeReseau({
  route: async (_motif, callback) => { handler = callback; },
  routeWebSocket: async () => {},
}, garde);
const essais = [
  ['POST', 'http://127.0.0.1:17393/api/chat/cache-migration'],
  ['POST', 'http://127.0.0.1:17393/api/chat/cache-migration?'],
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
    fulfill: (reponse) => resultats.push({
      status: reponse.status, contentType: reponse.contentType, body: JSON.parse(reponse.body),
    }),
    continue: () => resultats.push('continue'),
    abort: () => resultats.push('bloquee'),
  });
}
process.stdout.write(JSON.stringify({
  resultats,
  autorisee: requeteAutorisee(...essais[0]),
  simulations: garde.ecritures_simulees.nombre,
  bloquees: garde.bloquees.length,
}));
"""
    execution = subprocess.run(
        ["node", "--experimental-loader", chargeur.resolve().as_uri(), "--input-type=module", "--eval", script],
        check=True,
        capture_output=True,
        text=True,
    )
    bilan = json.loads(execution.stdout)
    assert bilan["resultats"] == [{
        "status": 200, "contentType": "application/json", "body": {"success": True},
    }] + ["bloquee"] * 6, "la migration avec ? contourne l'acquittement simulé"
    assert bilan["autorisee"] is False, "la simulation ne doit pas autoriser l'écriture réseau"
    assert bilan["simulations"] == 1
    assert bilan["bloquees"] == 6
