// C16 : copie préparée, jamais exécutée par le préparateur. Revue root préalable.
import {preparerContexte} from './contexte-v3.mjs';
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
const ctx=preparerContexte('B1755');
const {chromium}=await import(pathToFileURL("/private/tmp/therese-c17-full-suite-ps_tgzy5/source/node_modules/playwright/index.mjs").href);

const instrument=ctx.helper;
const sortie=ctx.out;
const { gesteExclu, installerGardeReseau, lesInteractifs, relocaliserInteractif } = await import(pathToFileURL(instrument).href);
const html = `<!doctype html><html lang="fr"><meta charset="utf-8"><title>B-1755</title>
<body><h1>Garde de génération</h1>
<button data-id="infinitif">Générer le PDF</button>
<button data-id="imperatif">Génère un rapport</button>
<button data-id="sansaccent">Generer le PDF</button>
<button data-id="sur">Ouvrir les réglages</button>
<script>
window.clics = { infinitif: 0, imperatif: 0, sansaccent: 0, sur: 0 };
for (const bouton of document.querySelectorAll('button')) {
  bouton.addEventListener('click', () => { window.clics[bouton.dataset.id] += 1; });
}
</script></body></html>`;
writeFileSync(join(sortie, 'singleton.html'), html);
const navigateur = await chromium.launch({headless: false, channel: 'chrome', chromiumSandbox: true, args: ['--disable-background-networking','--disable-component-update','--disable-sync']});
const garde = { bloquees: [], websockets_bloques: [], portReel: false };
try {
  const contexte = await navigateur.newContext({ serviceWorkers: 'block', acceptDownloads: false });
  await installerGardeReseau(contexte, garde);
  const page=await contexte.newPage();
  const console_errors=[],network_errors=[],downloads=[],popups=[];
  page.on('pageerror',e=>console_errors.push(String(e)));
  page.on('console',m=>{if(m.type()==='error')console_errors.push(m.text());});
  page.on('request',r=>network_errors.push({unexpected_request:new URL(r.url()).origin+new URL(r.url()).pathname}));
  page.on('download',d=>{downloads.push('download');void d.cancel();});
  page.on('popup',p=>{popups.push('popup');void p.close();});
  // Aucun serveur, même local, n'est requis par ce HTML ; toute requête est refusée.
  await page.route('**/*', (route) => route.abort('blockedbyclient'));
  await page.setContent(html);
  const gestes = [];
  for (const element of await lesInteractifs(page)) {
    const exclu = gesteExclu(element.nom, { ecran: 'temoin', role: element.role, agentId: element.agentId });
    if (!exclu) {
      const frais = await relocaliserInteractif(page, element);
      assert.ok(frais, element.nom);
      await frais.click();
    }
    gestes.push({ nom: element.nom, exclu, clic_reel: !exclu });
  }
  const compteurs = await page.evaluate(() => window.clics);
  assert.equal(console_errors.length,0);assert.equal(network_errors.length,0);assert.equal(downloads.length,0);assert.equal(popups.length,0);
  assert.deepEqual(compteurs, { infinitif: 0, imperatif: 0, sansaccent: 0, sur: 1 });
  assert.deepEqual(gestes.map(({ exclu }) => exclu), [true, true, true, false]);
  assert.deepEqual(garde, { bloquees: [], websockets_bloques: [], portReel: false });
  await page.screenshot({ path: join(sortie, 'singleton.png') });
  writeFileSync(join(sortie, 'recette.json'), JSON.stringify({
    ...ctx.metadata, synthetic_html:true, status: 'pass', navigateur: await navigateur.version(),
    source_sha256: createHash('sha256').update(readFileSync(instrument)).digest('hex'),
    page:page.url(),gestes,compteurs,garde,console_errors,network_errors,downloads,popups,serveur_applicatif:false,
  }, null, 2) + '\n');
  console.log(JSON.stringify({ status: 'pass', compteurs, gestes }));
  await contexte.close();
} finally {
  await navigateur.close();
}
