import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, renameSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { basename, join } from 'node:path';
import test from 'node:test';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { chromium } from '@playwright/test';
import {
  choisirGestes, detailRejetRelocalisation, gesteExclu, installerGardeReseau, lesInteractifs,
  memoriserGesteExerce, relocaliserInteractif,
  requeteAutorisee, verifierBaseJetable, verifierPileJetable,
} from './couverture-ecran.mjs';

const BASE = 'http://127.0.0.1:1420/?port=17393';

test('la CLI refuse une base invalide avant même le lancement de Chromium', () => {
  const fichier = fileURLToPath(new URL('./couverture-ecran.mjs', import.meta.url));
  const code = `
    import { chromium } from '@playwright/test';
    import { pathToFileURL } from 'node:url';
    chromium.launch = async () => { throw new Error('CHROMIUM_LAUNCHED'); };
    const fichier = process.argv[1];
    process.argv = [process.execPath, fichier, '--base', 'file:///private/tmp/base-invalide',
      '--expected-data-dir', '/private/tmp/inexistant'];
    await import(pathToFileURL(fichier).href);
  `;
  const resultat = spawnSync(process.execPath, ['--input-type=module', '-e', code, fichier], { encoding: 'utf8' });
  assert.equal(resultat.status, 1);
  assert.match(resultat.stderr, /Base refusée/);
  assert.doesNotMatch(resultat.stderr, /CHROMIUM_LAUNCHED/);
});

test('la base impose la pile jetable avant toute navigation', () => {
  assert.equal(verifierBaseJetable(BASE).href, BASE);
  for (const base of [
    'http://127.0.0.1:17293/',
    'http://127.0.0.1:1420/',
    'http://127.0.0.1:1420/?port=17293',
    'https://example.com/',
    'http://localhost:1420/?port=17393',
  ]) assert.throws(() => verifierBaseJetable(base));
});

test('la preuve de données jetables exige data_dir et db_path dans /private/tmp', async (t) => {
  const dataDir = mkdtempSync('/private/tmp/therese-couverture-test-');
  const dbPath = join(dataDir, 'therese.db');
  writeFileSync(dbPath, 'jetable');
  t.after(() => renameSync(dataDir, join(homedir(), '.Trash', basename(dataDir))));
  let demandes = 0;
  const fetcher = async (url, options) => {
    demandes += 1;
    assert.equal(options.method, 'GET');
    assert.equal(options.redirect, 'error');
    if (demandes === 1) {
      assert.equal(url, 'http://127.0.0.1:17393/__couverture/offline');
      return { ok: true, json: async () => ({ version: 1, network_policy: 'loopback-only', offline: true }) };
    }
    if (demandes === 2) {
      assert.equal(url, 'http://127.0.0.1:17393/api/auth/token');
      assert.equal(options.headers, undefined, 'aucun Origin ni jeton à l’amorçage');
      return { ok: true, json: async () => ({ token: 'jeton-jetable' }) };
    }
    assert.equal(url, 'http://127.0.0.1:17393/api/config/stats');
    assert.deepEqual(options.headers, { 'X-Therese-Token': 'jeton-jetable' });
    return { ok: true, json: async () => ({ data_dir: dataDir, db_path: dbPath }) };
  };
  assert.deepEqual(await verifierPileJetable(BASE, dataDir, fetcher), { data_dir: dataDir, db_path: dbPath });
  assert.equal(demandes, 3);
  await assert.rejects(verifierPileJetable(BASE, '/Users/synoptia', fetcher));
  await assert.rejects(verifierPileJetable(BASE, '', fetcher));
  assert.equal(demandes, 3, 'une destination invalide ne contacte aucun service');
  const mauvaiseBase = () => verifierPileJetable('http://127.0.0.1:17293/', dataDir, fetcher);
  await assert.rejects(mauvaiseBase());
  assert.equal(demandes, 3);
  let appelsIncoherents = 0;
  await assert.rejects(verifierPileJetable(BASE, dataDir, async () => {
    appelsIncoherents += 1;
    return appelsIncoherents === 1
      ? { ok: true, json: async () => ({ version: 1, network_policy: 'loopback-only', offline: true }) }
      : appelsIncoherents === 2
      ? { ok: true, json: async () => ({ token: 'jeton-jetable' }) }
      : { ok: true, json: async () => ({ data_dir: '/private/tmp', db_path: dbPath }) };
  }));
});

test('seules les lectures locales et la prévisualisation sans effet de bord passent', async () => {
  const cas = [
    ['GET', 'http://127.0.0.1:1420/', true],
    ['GET', 'http://127.0.0.1:17393/api/config/stats', true],
    ['POST', 'http://127.0.0.1:17393/api/variables/preview', true],
    ['POST', 'http://127.0.0.1:17393/api/variables/preview?muter=1', false],
    ['POST', 'http://127.0.0.1:17393/api/config/preferences', false],
    ['DELETE', 'http://127.0.0.1:17393/api/config/preferences/working_directory', false],
    ['POST', 'http://127.0.0.1:1420/api/config/preferences', false],
    ['GET', 'http://127.0.0.1:17293/api/config/stats', false],
    ['GET', 'https://example.com/', false],
    ['GET', 'http://localhost:17393/api/config/stats', false],
  ];
  for (const [methode, url, attendu] of cas) assert.equal(requeteAutorisee(methode, url), attendu, `${methode} ${url}`);

  let routeHttp;
  let routeWs;
  const garde = { bloquees: [], websockets_bloques: [], portReel: false };
  await installerGardeReseau({
    route: async (_motif, handler) => { routeHttp = handler; },
    routeWebSocket: async (_motif, handler) => { routeWs = handler; },
  }, garde);
  const emissions = [];
  const simuler = (methode, url) => routeHttp({
    request: () => ({ method: () => methode, url: () => url }),
    continue: () => emissions.push(`${methode} ${url}`),
    abort: (raison) => assert.equal(raison, 'blockedbyclient'),
  });
  simuler('POST', 'http://127.0.0.1:17393/api/config/preferences');
  simuler('GET', 'http://127.0.0.1:17293/api/config/stats');
  simuler('GET', 'https://example.com/');
  simuler('GET', 'https://example.com/prive?jeton=secret');
  simuler('POST', 'http://127.0.0.1:17393/api/variables/preview');
  assert.deepEqual(emissions, ['POST http://127.0.0.1:17393/api/variables/preview']);
  assert.equal(garde.bloquees.length, 4);
  assert.deepEqual(garde.bloquees.at(-1), { methode: 'GET', url: 'https://example.com/prive' });
  assert.equal(garde.portReel, true);
  routeWs({ url: () => 'ws://127.0.0.1:17293/socket', close: () => emissions.push('ws fermé') });
  assert.deepEqual(garde.websockets_bloques, ['ws://127.0.0.1:17293/socket']);
});

test('B-1720 : sans attestation du backend hors ligne, aucun jeton n’est lu', async (t) => {
  const dataDir = mkdtempSync('/private/tmp/therese-couverture-attestation-');
  t.after(() => renameSync(dataDir, join(homedir(), '.Trash', basename(dataDir))));
  const demandes = [];
  await assert.rejects(verifierPileJetable(BASE, dataDir, async (url) => {
    demandes.push(url);
    return { ok: false, status: 404 };
  }), /hors ligne|offline|attestation/i);
  assert.deepEqual(demandes, ['http://127.0.0.1:17393/__couverture/offline']);
  assert.equal(requeteAutorisee('GET', 'http://127.0.0.1:17393/api/crm/sync/callback'), false);
  assert.equal(requeteAutorisee('GET', 'http://127.0.0.1:17393/api/email/auth/callback-redirect'), false);
});

test('B-1719 : une interruption conserve la preuve des requêtes bloquées', async (t) => {
  const { enregistrerInterruption } = await import('./couverture-ecran.mjs');
  assert.equal(typeof enregistrerInterruption, 'function');
  const dossier = mkdtempSync('/private/tmp/therese-couverture-interruption-');
  t.after(() => renameSync(dossier, join(homedir(), '.Trash', basename(dossier))));
  const garde = {
    bloquees: [{ methode: 'GET', url: 'https://example.com/api' }],
    websockets_bloques: [], telechargements: [], popups: [], portReel: false,
  };
  enregistrerInterruption(dossier, new Error('requête bloquée'), garde, 'accueil');
  const preuve = JSON.parse(readFileSync(join(dossier, 'interruption.json'), 'utf8'));
  assert.equal(preuve.ecran, 'accueil');
  assert.equal(preuve.cause, 'requête bloquée');
  assert.deepEqual(preuve.garde.bloquees, garde.bloquees);
});

test('les gestes sortants et installations restent exclus', () => {
  for (const nom of [
    'Installer le modèle', 'Générer le PDF', 'générer le PDF', 'GÉNÉRER LE PDF',
    'Génère un rapport', 'GÉNÈRE UN RAPPORT', 'Generer le PDF', 'generer le PDF',
    'Synchroniser', 'Tester la connexion', 'Publier',
  ]) {
    assert.equal(gesteExclu(nom), true, nom);
  }
  assert.equal(gesteExclu('Ouvrir les réglages'), false);
});

test('B-1715 : les consultations sûres restent exerçables dans leur seul contexte', () => {
  assert.equal(gesteExclu('Envoyée', { ecran: 'invoices.open', role: 'button' }), false);
  assert.equal(gesteExclu('Rafraîchir les tâches', { ecran: 'tasks.open', role: 'button' }), false);
  const fiches = [
    ['rapport-hebdo', 'Ouvrir la fiche Rapport hebdomadaire'],
    ['relance-clients', 'Ouvrir la fiche Relance clients'],
    ['prep-rdv', 'Ouvrir la fiche Préparation RDV'],
    ['onboarding-client', 'Ouvrir la fiche Onboarding client'],
    ['audit-tresorerie', 'Ouvrir la fiche Audit trésorerie'],
    ['veille-concurrent', 'Ouvrir la fiche Veille concurrentielle'],
  ];
  for (const [agentId, nom] of fiches) {
    assert.equal(gesteExclu(nom, { ecran: 'actions.open', role: 'button', agentId }), false, agentId);
  }
  assert.equal(gesteExclu('Envoyée', { ecran: 'tasks.open', role: 'button' }), true);
  assert.equal(gesteExclu('Rafraîchir les tâches', { ecran: 'settings.open', role: 'button' }), true);
  assert.equal(gesteExclu('Envoyer le message', { ecran: 'invoices.open', role: 'button' }), true);
  assert.equal(gesteExclu('Lancer', { ecran: 'actions.open', role: 'button', agentId: 'relance-clients' }), true);
  assert.equal(gesteExclu('Ouvrir la fiche Relance clients', { ecran: 'actions.open', role: 'button', agentId: 'inconnu' }), true);
  assert.equal(gesteExclu('Ouvrir la fiche Rapport hebdomadaire et lancer', { ecran: 'actions.open', role: 'button', agentId: 'rapport-hebdo' }), true);
  assert.equal(gesteExclu('Ouvrir la fiche Marie', { ecran: 'crm.open', role: 'button' }), false);
});

test('le rôle et la signature retrouvent un bouton au nom accessible différent du texte brut',
  { skip: !process.env.COUVERTURE_BROWSER_TEST }, async () => {
    const navigateur = await chromium.launch();
    try {
      const page = await navigateur.newPage();
      const html = '<button aria-label="Rechercher"><span>Rechercher</span><kbd>⌘K</kbd></button>';
      await page.setContent(html);
      const bouton = page.getByRole('button').first();
      const signature = (await bouton.ariaSnapshot()).split('\n')[0];
      assert.equal(await page.getByRole('button', { name: 'Rechercher⌘K', exact: true }).count(), 0);
      await page.setContent(html);
      const frais = await relocaliserInteractif(page, { role: 'button', index: 0, signature });
      assert.ok(frais);
      assert.equal(await frais.getAttribute('aria-label'), 'Rechercher');
    } finally {
      await navigateur.close();
    }
  });

test('B-1718 : un bouton retiré avant le geste ne décale pas sa relocalisation',
  { skip: !process.env.COUVERTURE_BROWSER_TEST }, async () => {
    const navigateur = await chromium.launch();
    try {
      const page = await navigateur.newPage();
      await page.setContent('<button>Connecter ton agenda</button><button>Compléter le profil de facturation</button><button>Voir la suite</button>');
      const initial = page.getByRole('button').nth(1);
      const signature = (await initial.ariaSnapshot()).split('\n')[0];
      await page.setContent('<button>Compléter le profil de facturation</button><button>Voir la suite</button>');
      const frais = await relocaliserInteractif(page, { role: 'button', index: 1, signature });
      assert.ok(frais, 'le geste initial demeure présent malgré le décalage des rangs');
      assert.equal(await frais.textContent(), 'Compléter le profil de facturation');
    } finally {
      await navigateur.close();
    }
  });

test('B-1721 : le retrait d’un doublon ne fait pas cliquer un autre bouton',
  { skip: !process.env.COUVERTURE_BROWSER_TEST }, async () => {
    const navigateur = await chromium.launch();
    try {
      const page = await navigateur.newPage();
      await page.setContent('<button aria-label="Ouvrir" data-id="premier"></button><button aria-label="Ouvrir" data-id="second"></button><button aria-label="Ouvrir" data-id="troisieme"></button>');
      const signature = (await page.getByRole('button').nth(1).ariaSnapshot()).split('\n')[0];
      await page.setContent('<button aria-label="Ouvrir" data-id="second"></button><button aria-label="Ouvrir" data-id="troisieme"></button>');
      const frais = await relocaliserInteractif(page, {
        role: 'button', index: 1, signature, signatureOccurrence: 1, signatureTotal: 3,
      });
      assert.equal(frais === null, true, 'le rang initial est ambigu après le retrait d’un doublon');
    } finally {
      await navigateur.close();
    }
  });

test('B-1722 : deux écrans exercent chacun leur homonyme métier, mais la coque une seule fois',
  { skip: !process.env.COUVERTURE_BROWSER_TEST }, async () => {
    const navigateur = await chromium.launch();
    try {
      const page = await navigateur.newPage();
      const dejaExerces = new Set();
      const ecran = (metier) => `<div data-testid="conversation-canvas-prototype"><div>
        <header><button>Ouvrir</button></header>
        <div><nav aria-label="Navigation principale"><button>Projets</button></nav>
        <main><button data-id="${metier}">Ouvrir</button></main></div>
      </div></div>`;
      await page.setContent(ecran('fiche-a'));
      const accueil = choisirGestes(await lesInteractifs(page), dejaExerces);
      assert.equal(accueil.filter((el) => el.nom === 'Ouvrir').length, 2);
      assert.equal(accueil.find((el) => el.agentId === null && el.zoneGlobale === 'entete')?.nom, 'Ouvrir');
      for (const el of accueil.filter((item) => item.zoneGlobale)) memoriserGesteExerce(dejaExerces, el);

      await page.setContent(ecran('fiche-b'));
      const autreEcran = choisirGestes(await lesInteractifs(page), dejaExerces);
      assert.deepEqual(autreEcran.map((el) => el.nom), ['Ouvrir'],
        'le geste métier homonyme reste présent ; les contrôles de coque déjà exercés sont seuls dédupliqués');
      assert.equal(autreEcran[0].zoneGlobale, null);
    } finally {
      await navigateur.close();
    }
  });

test('B-1722 : un nav métier homonyme ne devient pas le rail de la coque',
  { skip: !process.env.COUVERTURE_BROWSER_TEST }, async () => {
    const navigateur = await chromium.launch();
    try {
      const page = await navigateur.newPage();
      await page.setContent(`<div data-testid="conversation-canvas-prototype"><div>
        <header><button>En-tête</button></header><div>
          <div><nav aria-label="Navigation principale"><button>Navigation métier</button></nav></div>
          <nav aria-label="Navigation principale"><button>Navigation coque</button></nav>
        </div></div></div>`);
      const interactifs = await lesInteractifs(page);
      assert.equal(interactifs.find((el) => el.nom === 'Navigation métier')?.zoneGlobale, null);
      assert.equal(interactifs.find((el) => el.nom === 'Navigation coque')?.zoneGlobale, 'navigation');
    } finally {
      await navigateur.close();
    }
  });

test('B-1722 : un contrôle de coque inactif ne masque pas son exercice ultérieur',
  { skip: !process.env.COUVERTURE_BROWSER_TEST }, async () => {
    const navigateur = await chromium.launch();
    try {
      const page = await navigateur.newPage();
      const dejaExerces = new Set();
      await page.setContent('<div data-testid="conversation-canvas-prototype"><div><header><button disabled>Ouvrir</button></header></div></div>');
      const premier = choisirGestes(await lesInteractifs(page), dejaExerces);
      assert.equal(premier.length, 1);
      assert.equal(premier[0].actif, false);
      assert.equal(dejaExerces.size, 0);
      await page.setContent('<div data-testid="conversation-canvas-prototype"><div><header><button>Ouvrir</button></header></div></div>');
      const second = choisirGestes(await lesInteractifs(page), dejaExerces);
      assert.equal(second.length, 1);
      assert.equal(second[0].actif, true);
    } finally {
      await navigateur.close();
    }
  });

test('B-1724 : le nom d’une checkbox vient aussi de son label englobant',
  { skip: !process.env.COUVERTURE_BROWSER_TEST }, async () => {
    const navigateur = await chromium.launch();
    try {
      const page = await navigateur.newPage();
      await page.setContent('<label><input type="checkbox"> Accepter</label>');
      const checkbox = (await lesInteractifs(page)).find((el) => el.role === 'checkbox');
      assert.ok(checkbox);
      assert.match(checkbox.signature, /checkbox "Accepter"/);
      assert.equal(checkbox.nom, 'Accepter', 'le nom relevé doit rejoindre le nom accessible du navigateur');
      assert.equal(choisirGestes([checkbox], new Set()).length, 1, 'le geste ne doit pas être omis');
    } finally {
      await navigateur.close();
    }
  });

test('B-1723 : un doublon conserve sa cible quand les boutons échangent de rang',
  { skip: !process.env.COUVERTURE_BROWSER_TEST }, async () => {
    const navigateur = await chromium.launch();
    try {
      const page = await navigateur.newPage();
      await page.setContent('<button aria-label="Ouvrir" data-id="premier"></button><button aria-label="Ouvrir" data-id="second"></button>');
      const initial = (await lesInteractifs(page))[1];
      assert.deepEqual(initial.identiteStable, { attribut: 'data-id', valeur: 'second' });
      await page.setContent('<button aria-label="Ouvrir" data-id="second"></button><button aria-label="Ouvrir" data-id="premier"></button>');
      const frais = await relocaliserInteractif(page, initial);
      assert.ok(frais);
      assert.equal(await frais.getAttribute('data-id'), 'second');
    } finally {
      await navigateur.close();
    }
  });

test('B-1723 : les homonymes sans identité stable sont refusés même à effectif constant',
  { skip: !process.env.COUVERTURE_BROWSER_TEST }, async () => {
    const navigateur = await chromium.launch();
    try {
      const page = await navigateur.newPage();
      await page.setContent('<button aria-label="Ouvrir"></button><button aria-label="Ouvrir"></button>');
      const initial = (await lesInteractifs(page))[1];
      assert.equal(initial.identiteStable, null);
      await page.setContent('<button aria-label="Ouvrir"></button><button aria-label="Ouvrir"></button>');
      assert.equal((await relocaliserInteractif(page, initial)) === null, true,
        'le rang ne prouve pas que le second bouton garde la même action');
      assert.match(detailRejetRelocalisation(initial), /homonymes sans identité stable : clic refusé/);
    } finally {
      await navigateur.close();
    }
  });

test('B-1723 : un singleton remplacé sous la même signature est refusé si son identité change',
  { skip: !process.env.COUVERTURE_BROWSER_TEST }, async () => {
    const navigateur = await chromium.launch();
    try {
      const page = await navigateur.newPage();
      await page.setContent('<button aria-label="Ouvrir" data-id="fiche-a"></button>');
      const initial = (await lesInteractifs(page))[0];
      assert.deepEqual(initial.identiteStable, { attribut: 'data-id', valeur: 'fiche-a' });
      await page.setContent('<button aria-label="Ouvrir" data-id="fiche-b"></button>');
      assert.equal((await relocaliserInteractif(page, initial)) === null, true,
        'la même signature et le même effectif ne suffisent pas si l’identité change');
      await page.setContent('<button aria-label="Ouvrir" data-id="fiche-a"></button>');
      const conserve = await relocaliserInteractif(page, initial);
      assert.ok(conserve);
      assert.equal(await conserve.getAttribute('data-id'), 'fiche-a');
    } finally {
      await navigateur.close();
    }
  });

test('B-1723 : un testid constant ne masque pas le changement de cible métier',
  { skip: !process.env.COUVERTURE_BROWSER_TEST }, async () => {
    const navigateur = await chromium.launch();
    try {
      const page = await navigateur.newPage();
      await page.setContent('<button aria-label="Ouvrir" data-testid="ouvrir-fiche" data-id="fiche-a"></button>');
      const initial = (await lesInteractifs(page))[0];
      assert.deepEqual(initial.identiteStable, { attribut: 'data-testid', valeur: 'ouvrir-fiche' });
      await page.setContent('<button aria-label="Ouvrir" data-testid="ouvrir-fiche" data-id="fiche-b"></button>');
      assert.equal((await relocaliserInteractif(page, initial)) === null, true,
        'le testid structurel ne doit pas autoriser un clic sur une autre fiche');
    } finally {
      await navigateur.close();
    }
  });

test('B-1717 : la réouverture restaure seulement les filtres locaux de Factures',
  { skip: !process.env.COUVERTURE_BROWSER_TEST }, async () => {
    const { capturerEtatLocalEcran, restaurerEtatLocalEcran } = await import('./couverture-ecran.mjs');
    assert.equal(typeof capturerEtatLocalEcran, 'function');
    assert.equal(typeof restaurerEtatLocalEcran, 'function');
    const navigateur = await chromium.launch();
    try {
      const page = await navigateur.newPage();
      await page.route('http://127.0.0.1:1420/**', (route) => route.fulfill({
        status: 200,
        contentType: 'text/html; charset=utf-8',
        body: `<!doctype html><body><script>
          const brut = JSON.parse(localStorage.getItem('therese-invoice-storage') || 'null');
          const filtre = brut?.state?.filters?.status;
          document.body.innerHTML = filtre && filtre !== 'all'
            ? '<button>Réinitialiser les filtres</button>'
            : '<button>Créer un devis ou une facture</button>';
        </script></body>`,
      }));
      await page.goto('http://127.0.0.1:1420/');
      await page.evaluate(() => {
        localStorage.setItem('therese-accessibility', 'theme sombre initial');
        localStorage.setItem('therese-onboarding', 'terminé');
      });
      const etatInitial = await capturerEtatLocalEcran(page, 'invoices.open');
      await page.evaluate(() => localStorage.setItem('therese-invoice-storage',
        JSON.stringify({ state: { filters: { status: 'cancelled' } }, version: 1 })));
      await page.reload();
      assert.equal(await page.getByRole('button', { name: 'Réinitialiser les filtres' }).count(), 1);
      await restaurerEtatLocalEcran(page, etatInitial);
      await page.reload();
      assert.equal(await page.getByRole('button', { name: 'Créer un devis ou une facture' }).count(), 1);
      assert.deepEqual(await page.evaluate(() => ({
        invoice: localStorage.getItem('therese-invoice-storage'),
        theme: localStorage.getItem('therese-accessibility'),
        onboarding: localStorage.getItem('therese-onboarding'),
      })), { invoice: null, theme: 'theme sombre initial', onboarding: 'terminé' });
      assert.equal(await capturerEtatLocalEcran(page, 'settings.open'), null);
    } finally {
      await navigateur.close();
    }
  });
