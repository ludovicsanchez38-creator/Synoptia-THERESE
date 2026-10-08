// C16 : copie préparée, jamais exécutée par le préparateur. Revue root préalable.
import {preparerContexte} from './contexte-v3.mjs';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const ctx=preparerContexte('P157');
const {repo,out}=ctx;
const manifest = ctx.stack;
const { chromium } = await import(pathToFileURL("/private/tmp/therese-c17-full-suite-ps_tgzy5/source/node_modules/playwright/index.mjs").href);
const { verifierPileJetable, installerGardeReseau } = await import(pathToFileURL(ctx.helper).href);
const base = 'http://127.0.0.1:5173/?port=17593';
const back = 'http://127.0.0.1:17593';
const variant='vert';
const width=Number(process.env.C16_WIDTH);assert([800,1440].includes(width));
const preuve = { ...ctx.metadata, variant, actor: ctx.metadata.actor, status: 'running', mesures: [], requests: [], write_attempts: [], console_errors: [], network_errors: [], captures: [], checks: [] };
const check = (name, passed, observed) => preuve.checks.push({ name, passed: Boolean(passed), observed });
let browser;
try {
  preuve.stack = await verifierPileJetable(base, manifest.data_dir);
  const amorcage = await fetch(`${back}/api/auth/token`, { method: 'GET', redirect: 'error' });
  const { token } = await amorcage.json();
  const contacts = async () => {
    const response = await fetch(`${back}/api/memory/contacts?offset=0&limit=200`, {
      method: 'GET', redirect: 'error', headers: { 'X-Therese-Token': token },
    });
    assert(response.ok);
    const rows = await response.json();
    return { count: rows.length, stages: rows.reduce((acc, c) => {
      acc[c.stage ?? 'sans_etape'] = (acc[c.stage ?? 'sans_etape'] ?? 0) + 1; return acc;
    }, {}), sha256: createHash('sha256').update(JSON.stringify(rows)).digest('hex') };
  };
  preuve.contacts_before = await contacts();
  const minimums = { contact: 10, discovery: 5, proposition: 5, signature: 5, delivery: 5, active: 5, lost: 5, archive: 5 };
  preuve.fixture_density = { minimums, observed: preuve.contacts_before.stages };
  for (const [stage, minimum] of Object.entries(minimums)) {
    assert((preuve.contacts_before.stages[stage] ?? 0) >= minimum, `fixture dense : ${stage} contient au moins ${minimum} cartes`);
  }
  browser = await chromium.launch({headless: false, channel: 'chrome', chromiumSandbox: true, args: ['--disable-background-networking','--disable-component-update','--disable-sync']});
  preuve.chromium = browser.version();
  const context = await browser.newContext({ viewport: { width, height: 900 }, colorScheme: 'light', locale: 'fr-FR', timezoneId: 'Europe/Paris', reducedMotion: 'reduce', serviceWorkers: 'block', acceptDownloads: false });
  const guard = { bloquees: [], websockets_bloques: [], telechargements: [], popups: [], portReel: false };
  preuve.guard = guard;
  await installerGardeReseau(context, guard);
  await context.route('**/*', (route) => {
    const request = route.request();
    if (!['GET', 'HEAD', 'OPTIONS'].includes(request.method())) {
      preuve.write_attempts.push({ method: request.method(), path: new URL(request.url()).pathname });
      return route.abort('blockedbyclient');
    }
    return route.fallback();
  });
  await context.addInitScript(() => localStorage.setItem('therese-accessibility', JSON.stringify({ state: { theme: 'light' }, version: 0 })));
  const page = await context.newPage();
  page.on('request', (r) => preuve.requests.push({ method: r.method(), path: new URL(r.url()).pathname }));
  page.on('pageerror',(e)=>preuve.console_errors.push(String(e)));
  page.on('console',m=>{if(m.type()==='error')preuve.console_errors.push(m.text());});
  page.on('response',r=>{if(r.status()>=400)preuve.network_errors.push({path:new URL(r.url()).pathname,status:r.status()});});
  page.on('download', (d) => { guard.telechargements.push('download'); void d.cancel(); });
  page.on('popup', (p) => { guard.popups.push('popup'); void p.close(); });
  await page.goto(base, { waitUntil: 'networkidle' });
  await page.waitForFunction(() => window.__thereseMonte && window.__therese?.runAction);
  await page.evaluate(() => window.__therese.runAction('crm.open'));
  const grid = page.getByRole('region', { name: 'Étapes du pipeline' });
  await grid.waitFor({ state: 'visible' });
  await page.waitForTimeout(1000);
  const right = page.getByRole('button', { name: /étapes? à droite/ });
  const measure = async (label) => {
    const state = await grid.evaluate((e) => {
      const box = (node) => {
        const r = node.getBoundingClientRect();
        return { x: r.x, y: r.y, width: r.width, height: r.height, top: r.top, bottom: r.bottom, left: r.left, right: r.right };
      };
      const ancestors = [];
      const rGrid = e.getBoundingClientRect();
      const clip = { left: rGrid.left + e.clientLeft, top: 0, right: rGrid.left + e.clientLeft + e.clientWidth, bottom: innerHeight };
      for (let a = e.parentElement; a; a = a.parentElement) {
        const css = getComputedStyle(a), r = a.getBoundingClientRect();
        ancestors.push({ tag: a.tagName, id: a.id, role: a.getAttribute('role'), class: a.className, scrollTop: a.scrollTop, scrollLeft: a.scrollLeft, scrollHeight: a.scrollHeight, clientHeight: a.clientHeight, overflowX: css.overflowX, overflowY: css.overflowY, rect: box(a) });
        if (css.overflowX !== 'visible') { clip.left = Math.max(clip.left, r.left + a.clientLeft); clip.right = Math.min(clip.right, r.left + a.clientLeft + a.clientWidth); }
        if (css.overflowY !== 'visible') { clip.top = Math.max(clip.top, r.top + a.clientTop); clip.bottom = Math.min(clip.bottom, r.top + a.clientTop + a.clientHeight); }
      }
      const visible = (node) => {
        if (!node) return null;
        const r = node.getBoundingClientRect();
        const width = Math.max(0, Math.min(clip.right, r.right) - Math.max(clip.left, r.left));
        const height = Math.max(0, Math.min(clip.bottom, r.bottom) - Math.max(clip.top, r.top));
        return { rect: box(node), visibleWidth: width, visibleHeight: height, visible: width > 0 && height > 0, fullyVisible: width >= r.width && height >= r.height };
      };
      const hints = Array.from(e.parentElement.parentElement.querySelectorAll('button')).map((b) => ({ name: b.textContent, rect: box(b) }));
      return {
        viewport: { width: innerWidth, height: innerHeight }, windowScrollY: scrollY,
        grid: { rect: box(e), scrollTop: e.scrollTop, scrollLeft: e.scrollLeft, scrollHeight: e.scrollHeight, clientHeight: e.clientHeight, scrollWidth: e.scrollWidth, clientWidth: e.clientWidth, overflowX: getComputedStyle(e).overflowX, overflowY: getComputedStyle(e).overflowY },
        active: { tag: document.activeElement.tagName, id: document.activeElement.id, role: document.activeElement.getAttribute('role'), text: document.activeElement.textContent.slice(0, 100) },
        ancestors, clip, hints,
        columns: Array.from(e.querySelectorAll('[data-colonne]')).map((c) => ({
          stage: c.dataset.colonne, cards: c.querySelectorAll('[data-carte]').length,
          column: visible(c), paddingLeft: parseFloat(getComputedStyle(c).paddingLeft), paddingRight: parseFloat(getComputedStyle(c).paddingRight),
          header: visible(c.querySelector('h3')), firstCard: visible(c.querySelector('[data-carte]')),
          cardRects: Array.from(c.querySelectorAll('[data-carte]'), (card) => ({
            id: card.dataset.carte, accessibleName: card.getAttribute('aria-label'), rect: box(card),
            content: box(card.querySelector('[data-testid="crm-contact-item"]')),
            text: card.textContent,
          })),
        })),
      };
    });
    preuve.mesures.push({ label, ...state });
  };
  const shot = async (label) => {
    const path = resolve(out, label + '.png'); await page.screenshot({ path, animations: 'disabled' });
    preuve.captures.push({ path, sha256: createHash('sha256').update(await readFile(path)).digest('hex') });
  };
  await measure('avant-focus'); await shot('avant-focus');
  await right.focus(); await measure('apres-focus-sans-entree'); await shot('apres-focus-sans-entree');
  // Tab natif depuis l’indice doit rejoindre la grille avant les cartes.
  await page.keyboard.press('Tab'); await measure('apres-tab-grille');
  for (let i = 0; i < 10 && await right.count(); i++) {
    await right.focus(); await page.keyboard.press('Enter'); await page.waitForTimeout(650);
    await measure(`apres-entree-${i + 1}`);
  }
  const rightEdgeCount=await right.count();
  preuve.right_edge_observation={right_button_count:rightEdgeCount,last_measure:preuve.mesures.at(-1).label};
  await shot('apres-entrees-au-bord');
  // Retour utilisateur réel par la molette, sans fixer scrollTop dans le DOM.
  await page.mouse.move(Math.min(width-20,420), 430); await page.mouse.wheel(0, -5000); await page.waitForTimeout(600);
  await measure('retour-molette-vers-haut'); await shot('retour-molette-vers-haut');
  const left=page.getByRole('button',{name:/étapes? à gauche/});
  for(let i=0;i<16&&await left.count();i++){await left.focus();await page.keyboard.press('Enter');await page.waitForTimeout(650);await measure('retour-gauche-'+(i+1));}
  await measure('bord-gauche');await shot('bord-gauche');
  const leftEdge=preuve.mesures.at(-1);
  check('left-edge-reached',leftEdge.grid.scrollLeft<=1,leftEdge.grid);
  check('left-edge-focus-region',leftEdge.active.role==='region',leftEdge.active);
  for(const m of preuve.mesures)check(m.label+':panel-only-scroll',m.windowScrollY===0&&m.grid.scrollTop===0&&m.ancestors.filter(a=>a.id!=='crm-panel-pipeline').every(a=>a.scrollTop===0),m.ancestors);
  preuve.contacts_after = await contacts();
  preuve.contacts_unchanged = preuve.contacts_before.sha256 === preuve.contacts_after.sha256;
  assert(preuve.contacts_unchanged);
  assert.equal(preuve.write_attempts.length, 0);
  assert.equal(guard.bloquees.length, 0); assert.equal(guard.websockets_bloques.length, 0); assert(!guard.portReel);
  const panel = (m) => m.ancestors.find((a) => a.id === 'crm-panel-pipeline');
  const parcours = preuve.mesures.filter((m) => m.label !== 'retour-molette-vers-haut');
  const tolerance = 1;
  const fullX = (r, clip) => r.left >= clip.left - tolerance && r.right <= clip.right + tolerance;
  const fullY = (r, clip) => r.top >= clip.top - tolerance && r.bottom <= clip.bottom + tolerance;
  preuve.contract = parcours.map((m) => ({
    label: m.label, panelScrollTop: panel(m).scrollTop,
    visibleStages: m.columns.filter((c) => c.column.visibleWidth > tolerance).map((c) => ({
      stage: c.stage, columnFullyX: fullX(c.column.rect, m.clip),
      headerX: fullX(c.header.rect, m.clip), headerY: fullY(c.header.rect, m.clip),
      firstCardX: c.firstCard ? fullX(c.firstCard.rect, m.clip) : null,
      firstCardY: c.firstCard ? fullY(c.firstCard.rect, m.clip) : null,
    })),
  }));
  check('contacts-count', preuve.contacts_after.count === preuve.contacts_before.count, [preuve.contacts_before.count, preuve.contacts_after.count]);
  check('contacts-hash', preuve.contacts_after.sha256 === preuve.contacts_before.sha256, [preuve.contacts_before.sha256, preuve.contacts_after.sha256]);
  check('eight-stages', preuve.mesures[0].columns.length === 8, preuve.mesures[0].columns.length);
  for (const m of preuve.contract) {
    if (m.label !== 'apres-tab-grille') check(m.label + ':panel-top', m.panelScrollTop === 0, m.panelScrollTop);
    check(m.label + ':one-full-column', m.visibleStages.some((c) => c.columnFullyX), m.visibleStages);
    for (const c of m.visibleStages) {
      check(`${m.label}:${c.stage}:header-Y`, c.headerY, c);
      check(`${m.label}:${c.stage}:first-card-Y`, c.firstCardY, c);
      if (c.columnFullyX) {
        check(`${m.label}:${c.stage}:header-X`, c.headerX, c);
        check(`${m.label}:${c.stage}:first-card-X`, c.firstCardX, c);
      }
    }
  }
  // Contrat indépendant : toutes les cartes, même hors viewport, restent
  // dans le contenu de leur propre colonne. Aucun texte n'est tronqué en DB.
  for (const m of preuve.mesures) {
    for (const c of m.columns) {
      const innerLeft = c.column.rect.left + c.paddingLeft;
      const innerRight = c.column.rect.right - c.paddingRight;
      const violations = c.cardRects.filter((a) => a.rect.left < innerLeft - tolerance || a.rect.right > innerRight + tolerance || a.content.left < innerLeft - tolerance || a.content.right > innerRight + tolerance);
      check(`${m.label}:${c.stage}:card-containment`, violations.length === 0, { innerLeft, innerRight, violations });
    }
    const overlaps = [];
    for (let i = 1; i < m.columns.length; i++) {
      for (const a of m.columns[i - 1].cardRects) for (const b of m.columns[i].cardRects) {
        const x = Math.min(a.content.right, b.content.right) - Math.max(a.content.left, b.content.left);
        const y = Math.min(a.content.bottom, b.content.bottom) - Math.max(a.content.top, b.content.top);
        if (x > tolerance && y > tolerance) overlaps.push({ a: a.id, b: b.id, x, y });
      }
    }
    check(m.label + ':no-adjacent-card-overlap', overlaps.length === 0, overlaps);
  }
  check('Tab-joins-region', preuve.mesures.find((m) => m.label === 'apres-tab-grille').active.role === 'region', preuve.mesures.find((m) => m.label === 'apres-tab-grille').active);
  const bord = preuve.mesures.filter((m) => m.label.startsWith('apres-entree-')).at(-1);
  check('B1742-focus-region-at-edge', bord.active.role === 'region', bord.active);
  check('right-edge-reached', rightEdgeCount === 0, rightEdgeCount);
  check('no-network-errors',preuve.network_errors.length===0,preuve.network_errors);
  check('no-console-errors', preuve.console_errors.length === 0, preuve.console_errors);
  const failed = preuve.checks.filter((c) => !c.passed);
  preuve.failures = failed;
  assert.equal(failed.length, 0, failed.map((c) => c.name).join('; '));
  preuve.status = 'passed'; await context.close();
} catch (error) { preuve.status = 'failed'; preuve.error = String(error); }
finally { if (browser) await browser.close(); await writeFile(resolve(out, 'mesures.json'), JSON.stringify(preuve, null, 2) + '\n'); }
console.log(JSON.stringify({ status: preuve.status, error: preuve.error, proof: resolve(out, 'mesures.json') }));
process.exitCode = preuve.status === 'passed' ? 0 : 1;
