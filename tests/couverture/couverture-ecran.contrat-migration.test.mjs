import assert from 'node:assert/strict';
import test from 'node:test';
import { installerGardeReseau, requeteAutorisee } from './couverture-ecran.mjs';

test('passe 3 : la migration du chat est acquittée sans autorisation réseau', async () => {
  const adresse = 'http://127.0.0.1:17393/api/chat/cache-migration';
  let traiter;
  const garde = { bloquees: [], websockets_bloques: [], portReel: false };
  await installerGardeReseau({
    route: async (_motif, handler) => { traiter = handler; },
    routeWebSocket: async () => {},
  }, garde);
  const actions = [];
  await traiter({
    request: () => ({ method: () => 'POST', url: () => adresse }),
    continue: () => actions.push('réseau'),
    abort: () => actions.push('refus'),
    fulfill: (reponse) => actions.push(reponse),
  });
  assert.deepEqual(actions, [{
    status: 200, contentType: 'application/json', body: JSON.stringify({ success: true }),
  }], 'la migration doit être simulée, sans émission réseau');
  assert.equal(requeteAutorisee('POST', adresse), false);
  assert.deepEqual(garde.ecritures_simulees, {
    nombre: 1, requetes: [{ methode: 'POST', url: adresse }],
  });
  assert.deepEqual(garde.bloquees, []);
});
